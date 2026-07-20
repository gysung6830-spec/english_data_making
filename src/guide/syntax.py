"""구문 유형 자동 감지 — 기출 문장을 '구문 유형별로' 그룹핑한다(2부용).

정규식 휴리스틱으로 후보를 모으는 단계다(완벽한 파싱이 아님).
실제 괄호치기/뼈대 분석은 이후 Claude 카드 생성이 담당한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SyntaxType:
    id: str
    title: str
    signal: str          # 학생에게 보여줄 감지 신호 설명
    how: str             # 괄호치는 법 한 줄
    pattern: re.Pattern
    min_len: int = 60    # 이 길이 이상이어야 '수식어 많은' 문장으로 취급


# 감지 규칙(위에서부터 우선). 한 문장은 가장 먼저 맞는 유형 하나에 배정.
SYNTAX_TYPES: list[SyntaxType] = [
    SyntaxType(
        id="relative", title="관계사절",
        signal="who / which / that / whose / where 가 명사 뒤에 붙어 길게 꾸민다",
        how="관계사부터 절 끝까지 통째로 괄호 → 꾸밈받는 명사만 뼈대에 남긴다",
        pattern=re.compile(r"\b\w+\s+(who|which|whose|where|whom)\b|"
                           r"\b(?:noun[s]?|the\s+\w+)\s+that\s+\w+", re.IGNORECASE),
    ),
    SyntaxType(
        id="cleft", title="긴 주어·가주어",
        signal="It is/was … that/to … — 진짜 주어가 뒤로 밀려 있다",
        how="가주어 It 은 버리고, 뒤의 that/to 덩어리를 진짜 주어로 앞에 놓는다",
        pattern=re.compile(r"\bIt\s+(is|was|has been|seems|appears)\b[^.]*?\b(that|to)\b",
                           re.IGNORECASE),
    ),
    SyntaxType(
        id="participle", title="분사구문",
        signal="문두나 콤마 뒤에 V-ing / V-ed 덩어리가 붙는다",
        how="분사 덩어리를 통째로 괄호 → ~하면서/~한 채로 로 뼈대에 붙인다",
        pattern=re.compile(r"(?:^|,\s)(\w+ing|\w+ed)\b[^,]{6,},", re.IGNORECASE),
    ),
    SyntaxType(
        id="insertion", title="삽입·동격",
        signal="— … — 또는 , which / 콤마 동격이 문장 중간에 끼어든다",
        how="대시·콤마 사이 삽입을 통째로 괄호 → 없는 셈 치고 뼈대부터 읽는다",
        pattern=re.compile(r"—[^—]+—|,\s+which\b|,\s+(?:a|an|the)\s+\w+,", re.IGNORECASE),
    ),
    SyntaxType(
        id="comparison", title="비교구문",
        signal="more/-er … than, as … as — 비교 기준이 뒤에 온다",
        how="than/as 뒤(비교 기준)를 괄호 → '무엇보다/무엇만큼'을 뼈대 뒤에 붙인다",
        pattern=re.compile(r"\b(more|less)\b[^.]*?\bthan\b|\b\w+er\s+than\b|"
                           r"\bas\s+\w+\s+as\b", re.IGNORECASE),
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
