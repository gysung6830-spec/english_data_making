"""구문 유형 자동 감지 — 기출 문장을 '구문 유형별로' 그룹핑한다(2부용).

정규식 휴리스틱으로 후보를 모으는 단계다(완벽한 파싱이 아님).
실제 괄호치기/뼈대 분석은 이후 Claude 카드 생성이 담당한다.

각 유형 = 감지 신호(이런 구조면) + 해석 공식(이렇게 해석).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SyntaxType:
    id: str
    title: str
    signal: str          # 이런 구조면 (감지 신호)
    formula: str         # 이렇게 해석 (해석 공식)
    pattern: re.Pattern
    min_len: int = 55


# 감지 규칙(위에서부터 우선). 한 문장은 가장 먼저 맞는 유형 하나에 배정.
SYNTAX_TYPES: list[SyntaxType] = [
    SyntaxType(
        id="inversion", title="도치·강조",
        signal="문두에 부정어(Never/Rarely/Not only/Little…)나 Only가 나오고 주어·동사가 뒤집힌다",
        formula="원래 어순(주어+동사)으로 되돌려 읽는다. 문두 부정어는 '거의/결코 ~않다'로.",
        pattern=re.compile(r"^\s*(Never|Rarely|Seldom|Hardly|Little|Not only|Nor|"
                           r"No sooner|Only|Not until|Neither|Nowhere)\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="cleft", title="긴 주어·가주어",
        signal="It is / was … that / to … — 진짜 주어가 뒤로 밀려 있다",
        formula="가주어 It은 버리고, 뒤의 that/to 덩어리를 진짜 주어로 앞에 놓는다.",
        pattern=re.compile(r"\bIt\s+(is|was|has been|seems|appears|follows|takes|remains)\b"
                           r"[^.]*?\b(that|to)\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="parallel", title="병렬·상관접속사",
        signal="not only A but (also) B / both A and B / either…or / neither…nor 로 짝을 이룬다",
        formula="A와 B의 '급(단어 종류)'을 맞춰 같은 자리에 놓고 대칭으로 읽는다.",
        pattern=re.compile(r"\bnot only\b.+?\bbut\b|\bboth\b.+?\band\b|"
                           r"\beither\b.+?\bor\b|\bneither\b.+?\bnor\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="comparison", title="비교구문",
        signal="more/-er … than, as … as, the 비교급 … the 비교급 — 비교 기준이 뒤에 온다",
        formula="than/as 뒤(비교 기준)를 괄호 → '무엇보다 / 무엇만큼'을 뼈대 뒤에 붙인다.",
        pattern=re.compile(r"\b(more|less)\b[^.]*?\bthan\b|\b\w+er\s+than\b|"
                           r"\bas\s+\w+\s+as\b|\bthe\s+\w+er\b.+?\bthe\s+\w+er\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="insertion", title="삽입·동격",
        signal="— … — 또는 , which / 콤마 동격(, a/the 명사,)이 문장 중간에 끼어든다",
        formula="대시·콤마 사이는 통째로 괄호(없는 셈) → 뼈대부터 읽고 부가 설명으로 취급한다.",
        pattern=re.compile(r"—[^—]+—|―[^―]+―|,\s+which\b|,\s+(?:a|an|the)\s+\w+,",
                           re.IGNORECASE),
    ),
    SyntaxType(
        id="relative", title="관계사절",
        signal="who / which / that / whose / where 가 명사 뒤에 붙어 길게 꾸민다",
        formula="관계사부터 절 끝까지 괄호 → 앞 명사만 뼈대에 남기고, '~하는'으로 뒤에서 붙인다.",
        pattern=re.compile(r"\b\w+\s+(who|which|whose|where|whom)\b|"
                           r"\bthe\s+\w+\s+that\s+\w+", re.IGNORECASE),
    ),
    SyntaxType(
        id="participle", title="분사·분사구문",
        signal="문두나 콤마 뒤에 V-ing / V-ed 덩어리가 붙는다",
        formula="분사 덩어리를 괄호 → 주절 뼈대부터 읽고 ~하면서 / ~한 채로 / ~해서로 붙인다.",
        pattern=re.compile(r"(?:^|,\s)(\w+ing|\w+ed)\b[^,]{6,},", re.IGNORECASE),
    ),
    SyntaxType(
        id="prep_stack", title="전치사구 후치수식 겹침",
        signal="명사 뒤에 of/in/on/with/for 전치사구가 두 개 이상 줄줄이 이어진다",
        formula="전치사구는 뒤에서 앞으로 '~의 / ~에 있는'으로 차례차례 붙여 명사를 완성한다.",
        pattern=re.compile(r"\b\w+\s+(of|in|on|for|with|between|among)\s+(?:\w+\s+){1,4}"
                           r"(of|in|on|for|with|to|between|among)\b", re.IGNORECASE),
        min_len=70,
    ),
]


@dataclass
class SyntaxMatch:
    type: SyntaxType
    sentence: str


def detect_type(sentence: str) -> SyntaxType | None:
    for st in SYNTAX_TYPES:
        if len(sentence) >= st.min_len and st.pattern.search(sentence):
            return st
    return None


def group_by_syntax(sentences: list[str], per_type: int = 3) -> dict[str, list[SyntaxMatch]]:
    """문장들을 구문 유형별로 per_type 개까지 그룹핑."""
    buckets: dict[str, list[SyntaxMatch]] = {st.id: [] for st in SYNTAX_TYPES}
    for s in sentences:
        st = detect_type(s)
        if st and len(buckets[st.id]) < per_type:
            buckets[st.id].append(SyntaxMatch(type=st, sentence=s))
    return buckets
