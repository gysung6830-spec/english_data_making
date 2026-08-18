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


# 지문을 '변형/오류 삽입'하는 유형 — 같은 지문을 다른 유형과 함께 쓰면 학생이
# 대조해 정답을 찾을 수 있으므로(스포일러), 이런 유형은 되도록 단독 지문에 배정.
SPOILER_TYPES = {
    "grammar", "grammar_vocab_mix", "vocab_odd", "irrelevant_sentence",
    "grammar_fix_and_answer", "blank_single", "order", "summary_ab",
}

# 사실상 같은 문항을 만드는 '유형군' — 한 지문에 같은 군을 겹쳐 배정하면
# 중복 문항(예: 어법·어법+어휘가 같은 지문의 같은 오류를 정답으로)이 나온다.
_TYPE_FAMILY = {
    "grammar": "grammar", "grammar_vocab_mix": "grammar",
    "main_point": "main_idea", "title": "main_idea", "summary_ab": "main_idea",
    "summary_fill_from_text": "main_idea",
    "vocab_odd": "vocab", "vocab_3blank_abc": "vocab",
    "inference_mismatch": "factmatch", "dialogue_mismatch": "factmatch",
    "notice_match": "factmatch",
}


def _family(t: str) -> str:
    return _TYPE_FAMILY.get(t, t)


def _spoiler_penalty(item_type: str, existing_types: set[str]) -> float:
    """이미 다른 유형이 붙은 지문에 스포일러 유형을 겹쳐 쓰면 큰 페널티."""
    if not existing_types:
        return 0.0
    if item_type in SPOILER_TYPES or (existing_types & SPOILER_TYPES):
        return 0.45
    return 0.0


# ---------------------------------------------------------------------------
# 배정 알고리즘 (§3-A-3) — 기존 지문만으로, 새 지문 생성 안 함
# ---------------------------------------------------------------------------
# 지문 수 ≥ 문항 수 일 때만 적용되는 한 지문 최대 사용 횟수.
# 지문 수 < 문항 수 이면 상한을 두지 않고(무제한) 모든 문항을 채운다.
REUSE_CAP = 2


def assign_passages(
    blueprint: Blueprint,
    passages: list[Passage],
    profiles: dict[str, PassageProfile] | None = None,
    difficulty: Difficulty = "mid",
    llm_refine: Callable[[str, Passage], float] | None = None,
    avoid_pairs: set[tuple[str, str]] | None = None,
) -> list[Assignment]:
    """blueprint 슬롯에 지문을 중복 최소화하며 그리디 배정.

    llm_refine: 규칙 점수가 애매할 때 (유형, 지문)→0~1 을 반환하는 선택 훅.
    avoid_pairs: (지문id, 유형) 조합을 되도록 피한다 — N회분에서 회차 간 문항 겹침 방지.
                 대안이 없으면(지문 부족) 최후에 허용해 완성은 보장한다.
    """
    avoid_pairs = avoid_pairs or set()
    if not passages:
        # 지문이 하나도 없으면 채울 수 없다(유일한 스킵 경우).
        return [Assignment(it.no, it.section, it.type, None, 0.0, "rule",
                           note="skipped_no_passage") for it in blueprint.items]

    if profiles is None:
        profiles = {p.id: profile_passage(p) for p in passages}
    by_format: dict[str, list[Passage]] = {}
    for p in passages:
        by_format.setdefault(p.format_type, []).append(p)

    # 동적 재사용 상한(사용자 규칙):
    #  - 지문 수 ≥ 문항 수 : 한 지문 최대 REUSE_CAP(2)회
    #  - 지문 수 <  문항 수 : 제한 없음(None) → 모든 문항을 반드시 채운다
    num_slots = len(blueprint.items)
    cap: int | None = REUSE_CAP if len(passages) >= num_slots else None

    use_count: dict[str, int] = {p.id: 0 for p in passages}
    type_on: dict[str, set[str]] = {p.id: set() for p in passages}  # 지문별 이미 붙은 유형

    assignments: list[Assignment] = []
    # 형식 고정 슬롯을 먼저 배정(하드 제약)
    order = sorted(blueprint.items, key=lambda it: (0 if it.type in FORMAT_REQUIRED else 1, it.no))

    for item in order:
        req_fmt = FORMAT_REQUIRED.get(item.type)
        note: str | None = None

        if req_fmt:
            fmt_pool = by_format.get(req_fmt, [])
            pick = _pick(item, fmt_pool, profiles, use_count, type_on, difficulty,
                         llm_refine, cap, avoid_pairs=avoid_pairs)
            if pick is None:
                # 형식 지문이 없거나 소진 → 서술문(없으면 전체)으로 대체(완성 보장)
                pool = by_format.get("narrative") or passages
                pick = _guaranteed_pick(item, pool, profiles, use_count, type_on,
                                        difficulty, llm_refine, cap, avoid_pairs)
                note = "substituted"
        else:
            pick = _guaranteed_pick(item, passages, profiles, use_count, type_on,
                                    difficulty, llm_refine, cap, avoid_pairs)

        if pick is None:  # 지문 pool 이 비어있는 극단(위 not passages 로 사실상 방지)
            assignments.append(Assignment(item.no, item.section, item.type, None,
                                           0.0, "rule", note="skipped_no_passage"))
            continue
        pid, score, src = pick
        assignments.append(Assignment(item.no, item.section, item.type, pid, score,
                                       src, note=note))
        use_count[pid] += 1
        type_on[pid].add(item.type)

    assignments.sort(key=lambda a: (0 if a.section == "choice" else 1, a.no))
    return assignments


def _guaranteed_pick(item, pool, profiles, use_count, type_on, difficulty,
                     llm_refine, cap, avoid_pairs=None):
    """pool 이 비어있지 않으면 반드시 지문을 하나 반환(모든 문항 완성 보장).

    제약을 단계적으로 완화한다: 겹침회피+회차회피 → 유형겹침허용 → 상한무시 →
    (최후) 회차회피(avoid_pairs)까지 무시. 지문이 부족해도 완성은 보장.
    """
    if not pool:
        return None
    r = _pick(item, pool, profiles, use_count, type_on, difficulty, llm_refine,
              cap, allow_type_overlap=False, avoid_pairs=avoid_pairs)
    if r:
        return r
    r = _pick(item, pool, profiles, use_count, type_on, difficulty, llm_refine,
              cap, allow_type_overlap=True, avoid_pairs=avoid_pairs)
    if r:
        return r
    r = _pick(item, pool, profiles, use_count, type_on, difficulty, llm_refine,
              None, allow_type_overlap=True, avoid_pairs=avoid_pairs)
    if r:
        return r
    # 최후: 회차 간 회피(avoid_pairs)도 포기(대안이 전혀 없을 때만) — 완성 우선
    return _pick(item, pool, profiles, use_count, type_on, difficulty, llm_refine,
                 None, allow_type_overlap=True, avoid_pairs=None)


def _pick(item: Item, candidates: list[Passage],
          profiles: dict[str, PassageProfile],
          use_count: dict[str, int], type_on: dict[str, set[str]],
          difficulty: Difficulty,
          llm_refine: Callable[[str, Passage], float] | None,
          cap: int | None,
          allow_type_overlap: bool = False,
          avoid_pairs: set[tuple[str, str]] | None = None):
    """적합도(fit) 최고 지문을 고른다. 없으면 None.

    지문이 충분할 때(cap 有=지문수≥문항수)만 유형군 겹침·스포일러를 회피한다.
    지문이 적을 때(cap None)는 그 회피가 오히려 '적합도 낮은 지문 강제 배정 →
    구조 오류'를 부르므로, 오직 출제원리 적합도로만 최적 지문을 고른다(재사용 허용).
    """
    plentiful = cap is not None       # 지문수 ≥ 문항수 (재사용 상한이 걸린 경우)
    scored: list[tuple[float, str, str]] = []
    for p in candidates:
        if cap is not None and use_count.get(p.id, 0) >= cap:
            continue
        # 회차 간 겹침 방지: 이미 다른 회차에서 쓴 (지문,유형)이면 건너뛴다(대안 있을 때만).
        if avoid_pairs and (p.id, item.type) in avoid_pairs:
            continue
        # (지문 충분할 때만) 같은 유형군이 한 지문에 겹치면 중복 위험 → 회피
        if plentiful and not allow_type_overlap and \
                _family(item.type) in {_family(x) for x in type_on.get(p.id, set())}:
            continue
        prof = profiles[p.id]
        s = fit_score(item.type, prof) + _difficulty_bonus(prof, difficulty)
        src = "format" if item.type in FORMAT_REQUIRED else "rule"
        # 애매 구간(0.35~0.65)에서만 LLM 확정(§3-A-1)
        if llm_refine is not None and 0.35 <= s <= 0.65:
            s = llm_refine(item.type, p)
            src = "llm"
        # 재사용은 소폭 페널티(같은 지문에만 몰리지 않게 고르게 분산)
        s -= 0.08 * use_count.get(p.id, 0)
        # (지문 충분할 때만) 스포일러 유형 겹침 페널티 — 적을 땐 적합도 우선
        if plentiful:
            s -= _spoiler_penalty(item.type, type_on.get(p.id, set()))
        scored.append((s, p.id, src))
    if not scored:
        return None
    scored.sort(reverse=True)
    best_s, best_id, best_src = scored[0]
    return best_id, round(max(best_s, 0.0), 3), best_src
