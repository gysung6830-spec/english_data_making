"""지문 프로파일링 · 유형별 적합도 · 자동배정 (§3-A).

- 프로파일링은 규칙기반 1차(§3-A-1). 애매한 경우만 LLM 확정 훅을 둔다(선택).
- 적합도는 §3-A-2 공식.
- 배정은 §3-A-3: 형식 유형 하드제약, 재사용 상한 3, 유형 겹침 회피,
  지문 부족 시 새 지문 생성 없이 대체/스킵.
"""
from __future__ import annotations

import re
from typing import Callable

from ..core.models import (
    Assignment, Blueprint, Difficulty, Item, Passage, PassageProfile,
)

# ---------------------------------------------------------------------------
# 규칙기반 지표 측정
# ---------------------------------------------------------------------------
_CONNECTIVES = re.compile(
    r"\b(however|therefore|thus|for instance|for example|in addition|moreover|"
    r"nevertheless|on the other hand|as a result|consequently|in contrast|"
    r"first|second|finally|then|because|although|while|whereas|instead)\b", re.I)
_REFERENTS = re.compile(r"\b(this|that|these|those|such|it|they|its|their)\b", re.I)
_CONCLUSION = re.compile(
    r"\b(in conclusion|in short|to sum up|overall|the key|the point|important|"
    r"should|must|need to|essential|crucial|thus|therefore|lesson|matters)\b", re.I)
_REL = re.compile(r"\b(who|whom|whose|which|that|where|when|why)\b", re.I)
_PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)\s+\w+(ed|en)\b", re.I)
_PARTICIPLE = re.compile(r"\b\w+(ing|ed)\b", re.I)
_SENT_SPLIT = re.compile(r"[.!?]+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")

# 아주 흔한 단어(저빈도 비율 계산용 스톱워드 근사)
_COMMON = set(
    "the a an of to in and or is are was were be been being it its this that these those "
    "for on with as at by from he she they we you i his her their our your my me him them "
    "not but so if then than can could will would may might do does did have has had not no "
    "one two more most some any all each other into out up down over under about".split())


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def profile_passage(p: Passage) -> PassageProfile:
    """규칙기반 1차 프로파일(§3-A-1)."""
    text = p.text
    words = _WORD.findall(text)
    n = max(len(words), 1)
    sents = [s for s in _SENT_SPLIT.split(text) if s.strip()]
    n_sent = max(len(sents), 1)

    conn = len(_CONNECTIVES.findall(text))
    ref = len(_REFERENTS.findall(text))
    concl = len(_CONCLUSION.findall(text))
    rel = len(_REL.findall(text))
    passive = len(_PASSIVE.findall(text))
    part = len(_PARTICIPLE.findall(text))

    lower = [w.lower() for w in words]
    rare = [w for w in lower if len(w) >= 8 and w not in _COMMON]
    content = [w for w in lower if w not in _COMMON and len(w) >= 4]

    logic = _clamp((conn / n) * 18 + (ref / n) * 6)
    conclusion = _clamp((concl / n_sent) * 2.2)
    grammar = _clamp((rel + passive) / n * 20 + (part / n) * 4)
    vocab = _clamp(len(set(content)) / n * 2.2)
    rare_ratio = len(rare) / n
    avg_len = n / n_sent

    # 난이도: 문장길이 + 저빈도 어휘 비율
    diff_score = avg_len / 22 + rare_ratio * 3
    difficulty: Difficulty = "low" if diff_score < 0.7 else ("high" if diff_score > 1.15 else "mid")

    return PassageProfile(
        passage_id=p.id, format_type=p.format_type,
        logic_structure=round(logic, 3), has_conclusion=round(conclusion, 3),
        grammar_diversity=round(grammar, 3), vocab_contrast=round(vocab, 3),
        words=n, avg_sentence_len=round(avg_len, 2), rare_word_ratio=round(rare_ratio, 3),
        difficulty=difficulty,
        raw={"connectives": conn, "referents": ref, "conclusion": concl,
             "relatives": rel, "passive": passive, "rare": len(rare)},
    )


# ---------------------------------------------------------------------------
# 형식 하드제약 + 적합도 (§3-A-2, §3-A-3)
# ---------------------------------------------------------------------------
# 형식 고정 유형 → 요구 지문 형식
FORMAT_REQUIRED = {
    "dialogue_mismatch": "dialogue",
    "dialogue_arrange_inflect": "dialogue",
    "notice_match": "notice",
    "chart_fix_and_arrange": "chart",
}


def _length_fit(prof: PassageProfile, lo: int = 60, hi: int = 220) -> float:
    w = prof.words
    if lo <= w <= hi:
        return 1.0
    if w < lo:
        return _clamp(w / lo)
    return _clamp(hi / w)


def fit_score(item_type: str, prof: PassageProfile) -> float:
    """(유형 × 지문) 적합도 0~1 (§3-A-2)."""
    t = item_type
    L = _length_fit(prof)
    if t in ("order",):
        return _clamp(prof.logic_structure * 0.6 + L * 0.4)
    if t in ("irrelevant_sentence", "blank_single"):
        return _clamp(prof.logic_structure * 0.55 + prof.has_conclusion * 0.25 + L * 0.2)
    if t in ("grammar", "grammar_vocab_mix", "grammar_fix_and_answer"):
        return _clamp(prof.grammar_diversity * 0.8 + L * 0.2)
    if t in ("title", "main_point", "summary_ab", "summary_fill_from_text"):
        return _clamp(prof.has_conclusion * 0.7 + prof.logic_structure * 0.3)
    if t in ("vocab_odd", "vocab_3blank_abc", "blank_choose_no_change"):
        return _clamp(prof.vocab_contrast * 0.7 + L * 0.3)
    if t == "implied_meaning":
        return _clamp(prof.logic_structure * 0.4 + prof.has_conclusion * 0.3 + L * 0.3)
    if t == "inference_mismatch":
        return _clamp(prof.has_conclusion * 0.4 + L * 0.6)
    # 서술형 일반/기타
    return _clamp(prof.grammar_diversity * 0.3 + prof.vocab_contrast * 0.3 + L * 0.4)


def _difficulty_bonus(prof: PassageProfile, want: Difficulty) -> float:
    """난이도 '상' 요청인데 어휘등급 높은 지문을 우선(§3-B-3)."""
    order = {"low": 0, "mid": 1, "high": 2}
    if want == "high":
        return 0.12 if prof.difficulty == "high" else (0.04 if prof.difficulty == "mid" else -0.04)
    if want == "low":
        return 0.12 if prof.difficulty == "low" else (0.04 if prof.difficulty == "mid" else -0.04)
    return 0.0 if order[prof.difficulty] == 1 else -0.02


# ---------------------------------------------------------------------------
# 배정 알고리즘 (§3-A-3) — 기존 지문만으로, 새 지문 생성 안 함
# ---------------------------------------------------------------------------
REUSE_CAP = 2  # 한 지문 최대 2문항(하드 제약). 상한을 넘으면 대체가 아니라 스킵.


def assign_passages(
    blueprint: Blueprint,
    passages: list[Passage],
    profiles: dict[str, PassageProfile] | None = None,
    difficulty: Difficulty = "mid",
    llm_refine: Callable[[str, Passage], float] | None = None,
) -> list[Assignment]:
    """blueprint 슬롯에 지문을 중복 최소화하며 그리디 배정.

    llm_refine: 규칙 점수가 애매할 때 (유형, 지문)→0~1 을 반환하는 선택 훅.
    """
    if profiles is None:
        profiles = {p.id: profile_passage(p) for p in passages}
    by_format: dict[str, list[Passage]] = {}
    for p in passages:
        by_format.setdefault(p.format_type, []).append(p)

    use_count: dict[str, int] = {p.id: 0 for p in passages}
    type_on: dict[str, set[str]] = {p.id: set() for p in passages}  # 지문별 이미 붙은 유형

    assignments: list[Assignment] = []

    # 형식 고정 슬롯을 먼저 배정(하드 제약)
    order = sorted(blueprint.items, key=lambda it: (0 if it.type in FORMAT_REQUIRED else 1, it.no))

    for item in order:
        req_fmt = FORMAT_REQUIRED.get(item.type)
        candidates = by_format.get(req_fmt, []) if req_fmt else passages
        best = _pick(item, candidates, profiles, use_count, type_on, difficulty, llm_refine)

        if best is None and req_fmt:
            # 형식 지문 없음 → 새로 만들지 않는다. 서술문을 변환하거나 스킵.
            narr = by_format.get("narrative", [])
            conv = _pick(item, narr, profiles, use_count, type_on, difficulty, llm_refine)
            if conv is not None:
                pid, score, src = conv
                assignments.append(Assignment(item.no, item.section, item.type, pid,
                                               score, src, note="substituted"))
                use_count[pid] += 1
                type_on[pid].add(item.type)
            else:
                assignments.append(Assignment(item.no, item.section, item.type, None,
                                               0.0, "format", note="skipped_no_passage"))
            continue

        if best is None:
            # 상한(2)은 유지하되, '같은 지문에 같은 유형 금지'만 완화해 차선 배정 시도.
            # 상한을 넘겨야 채울 수 있으면 대체하지 않고 스킵한다(한 지문 최대 2회 하드 보장).
            fallback = _pick(item, candidates, profiles, use_count,
                             {p.id: set() for p in passages}, difficulty, llm_refine)
            if fallback is not None:
                pid, score, src = fallback
                assignments.append(Assignment(item.no, item.section, item.type, pid,
                                               score, src, note="substituted"))
                use_count[pid] += 1
                type_on[pid].add(item.type)
            else:
                assignments.append(Assignment(item.no, item.section, item.type, None,
                                               0.0, "rule", note="skipped_no_passage"))
            continue

        pid, score, src = best
        assignments.append(Assignment(item.no, item.section, item.type, pid, score, src))
        use_count[pid] += 1
        type_on[pid].add(item.type)

    assignments.sort(key=lambda a: (0 if a.section == "choice" else 1, a.no))
    return assignments


def _pick(item: Item, candidates: list[Passage],
          profiles: dict[str, PassageProfile],
          use_count: dict[str, int], type_on: dict[str, set[str]],
          difficulty: Difficulty,
          llm_refine: Callable[[str, Passage], float] | None):
    """상한(3)·유형겹침을 지키며 적합도 최고 지문을 고른다. 없으면 None."""
    scored: list[tuple[float, str, str]] = []
    for p in candidates:
        if use_count.get(p.id, 0) >= REUSE_CAP:
            continue
        if item.type in type_on.get(p.id, set()):   # 같은 지문에 같은 유형 금지
            continue
        prof = profiles[p.id]
        s = fit_score(item.type, prof) + _difficulty_bonus(prof, difficulty)
        src = "format" if item.type in FORMAT_REQUIRED else "rule"
        # 애매 구간(0.35~0.65)에서만 LLM 확정(§3-A-1)
        if llm_refine is not None and 0.35 <= s <= 0.65:
            s = llm_refine(item.type, p)
            src = "llm"
        # 재사용은 페널티(중복 최소화)
        s -= 0.05 * use_count.get(p.id, 0)
        scored.append((s, p.id, src))
    if not scored:
        return None
    scored.sort(reverse=True)
    best_s, best_id, best_src = scored[0]
    return best_id, round(max(best_s, 0.0), 3), best_src
