"""연습용 문장 선별 — 1716 기출 문장에서 '구문해석 연습에 적합한' 문장만 골라
챕터(1부 코드 / 2부 구문)별로 배분한다. (API 불필요, 순수 규칙)

2단계:
  1) 필터(통과 못 하면 제외): 자기완결성·적정길이·신호보유·노이즈 제거
  2) 점수(우선순위): 오역위험 + 복잡도 + 난이도, 한 문항 편중 방지
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .codes import Category, load_categories
from .corpus import SourcedSentence, collect_sourced, estimate_difficulty
from .syntax import SYNTAX_TYPES, detect_type

# ── 필터 규칙 ────────────────────────────────────────────────
# 문두 지시어/대명사(앞 문장 참조 위험 → 자기완결성 부족)
_BACKREF = re.compile(r"^(This|These|Those|They|It|Its|Their|His|Her|Such|Here|There|That)\b")
# 인사·안내·초대문(지문 아님)
_NOTICE = re.compile(r"\b(Dear|Hello|Hi there|Please|Thank you|Welcome|Congratulations|"
                     r"Sincerely|RSVP|join us|come and|sign up|admission|We are (happy|pleased))\b",
                     re.IGNORECASE)
# 추출 노이즈: 같은 고유명사 중복(Buckland Buckland), 워크북 머리말
_DUP_PROPER = re.compile(r"\b([A-Z][a-z]{2,})\s+\1\b")
_NEG = re.compile(r"\b(not|no|hardly|rarely|seldom|never|little|few|lack|absence|unlikely|"
                  r"far from|rather than|nothing but|by no means)\b", re.IGNORECASE)
_CLAUSE = re.compile(r"\b(who|which|that|whose|where|when|because|although|while|though|"
                     r"\w+ing|\w+ed)\b", re.IGNORECASE)

MIN_WORDS = 12
MAX_WORDS = 45


def filter_reason(text: str) -> str:
    """통과하면 '' , 제외되면 사유 문자열."""
    n = len(text.split())
    if n < MIN_WORDS:
        return "너무 짧음"
    if n > MAX_WORDS:
        return "너무 김"
    if _BACKREF.match(text):
        return "문두 지시어(자기완결성↓)"
    if _NOTICE.search(text):
        return "인사·안내문"
    if _DUP_PROPER.search(text) or "WORKBOOK" in text:
        return "추출 노이즈"
    if not re.search(r"[a-z]", text):
        return "본문 아님"
    if not text.rstrip().endswith((".", "?", "!", '."', '?"', '!"')):
        return "문장 미완결"
    return ""


def passes(text: str) -> bool:
    return filter_reason(text) == ""


# ── 점수(우선순위) ───────────────────────────────────────────
def score(text: str, direction_type: bool = False) -> float:
    commas = text.count(",")
    clauses = len(_CLAUSE.findall(text))
    neg = 2 if _NEG.search(text) else 0
    direction = 1 if direction_type else 0
    length_bonus = min(len(text.split()) / 20, 2)
    return round(clauses * 0.6 + commas * 0.5 + neg + direction + length_bonus, 2)


@dataclass
class Picked:
    sentence: str
    source: str
    difficulty: str
    score: float
    hit: str = ""


@dataclass
class ChapterPick:
    id: str
    title: str
    kind: str                 # 'code' | 'syntax'
    picks: list[Picked] = field(default_factory=list)
    filtered_out: int = 0     # 신호는 맞지만 필터 탈락 수


_DIRECTION_CATS = {"causation", "comparison"}


def _rank(cands: list[Picked], cap_per_q: int = 2) -> list[Picked]:
    """점수 내림차순 정렬 + 한 문항(source)당 cap_per_q 개로 제한(편중 방지)."""
    cands.sort(key=lambda p: p.score, reverse=True)
    seen: dict[str, int] = {}
    out: list[Picked] = []
    for p in cands:
        q = p.source or "?"
        if seen.get(q, 0) >= cap_per_q:
            continue
        seen[q] = seen.get(q, 0) + 1
        out.append(p)
    return out


def select_code_chapters(sourced: list[SourcedSentence],
                         cats: list[Category]) -> list[ChapterPick]:
    results: list[ChapterPick] = []
    for cat in cats:
        cands: list[Picked] = []
        filtered = 0
        for ss in sourced:
            hit = None
            for code in cat.codes:
                hit = code.matches(ss.text)
                if hit:
                    break
            if not hit:
                continue
            if not passes(ss.text):
                filtered += 1
                continue
            dif = ss.difficulty or estimate_difficulty(ss.text)
            cands.append(Picked(ss.text, ss.source, dif,
                                score(ss.text, cat.id in _DIRECTION_CATS), hit))
        results.append(ChapterPick(cat.id, cat.title, "code", _rank(cands), filtered))
    return results


def select_syntax_chapters(sourced: list[SourcedSentence]) -> list[ChapterPick]:
    tmap = {st.id: st for st in SYNTAX_TYPES}
    buckets: dict[str, list[Picked]] = {st.id: [] for st in SYNTAX_TYPES}
    filtered: dict[str, int] = {st.id: 0 for st in SYNTAX_TYPES}
    for ss in sourced:
        st = detect_type(ss.text)
        if not st:
            continue
        if not passes(ss.text):
            filtered[st.id] += 1
            continue
        dif = ss.difficulty or estimate_difficulty(ss.text)
        buckets[st.id].append(Picked(ss.text, ss.source, dif,
                                     score(ss.text, st.id == "comparison")))
    results: list[ChapterPick] = []
    for st in SYNTAX_TYPES:
        results.append(ChapterPick(st.id, st.title, "syntax",
                                   _rank(buckets[st.id]), filtered[st.id]))
    return results


def split_examples_problems(picks: list[Picked], n_examples: int = 5,
                            n_problems: int = 20):
    """예시(중 절반 + 고 절반) / 문제(나머지, 최대 n_problems)로 나눈다."""
    mids = [p for p in picks if p.difficulty == "중"]
    highs = [p for p in picks if p.difficulty == "고"]
    half = n_examples // 2
    examples = mids[:half] + highs[:n_examples - half]
    ex_set = {id(p) for p in examples}
    problems = [p for p in picks if id(p) not in ex_set][:n_problems]
    return examples, problems


def preview(corpus_dir) -> dict:
    """선별 미리보기 데이터: 챕터별 통과/탈락 수 + 상위 문장."""
    sourced = collect_sourced(corpus_dir)
    cats = load_categories()
    code_ch = select_code_chapters(sourced, cats)
    syn_ch = select_syntax_chapters(sourced)
    return {"total": len(sourced), "code": code_ch, "syntax": syn_ch}
