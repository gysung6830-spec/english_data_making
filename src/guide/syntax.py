"""구문 유형 자동 감지 — 기출 문장을 '구문 유형별로' 그룹핑한다(구문해석 파트).

정규식 휴리스틱으로 후보를 모으는 단계다(완벽한 파싱이 아님).
실제 괄호치기/뼈대 분석은 이후 Claude 카드 생성이 담당한다.

각 유형 = 감지 신호(이런 구조면) + 해석 공식(이렇게 해석) + 실전 팁.
목차: 강조·도치·동격·병렬·what절·that절·wh절·삽입/분사, 그리고 전치사구(별도).
(부정·비교는 2부 '평가원 코드'에서 다루므로 구문해석에서 제외.)
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
    combat: str = ""      # 실전 팁(시험장 요령)
    min_len: int = 45


# 감지 규칙(위에서부터 우선). 한 문장은 가장 먼저 맞는 유형 하나에 배정.
SYNTAX_TYPES: list[SyntaxType] = [
    SyntaxType(
        id="emphasis", title="강조구문",
        signal="It is/was … that/who … (분열문) 또는 do/does/did + 동사원형, 재귀대명사 강조",
        formula="It ~ that 사이(강조 대상)를 먼저 잡는다: '바로 그것이 …이다'. do 강조는 '정말 ~한다'.",
        combat="실전 팁 — It is X that … 에서 X가 '답'인 경우가 많다. It을 가주어로 착각 말고, that절이 완전하면 강조(=X 부각).",
        pattern=re.compile(r"\bIt\s+(is|was)\b[^.]*?\b(that|who)\b|"
                           r"\b(do|does|did)\s+(?=[a-z]{3,}\b)|"
                           r"\b(myself|yourself|itself|himself|herself|themselves)\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="inversion", title="도치구문",
        signal="문두 부정어(Never/Rarely/Not only/Little/Hardly/Only…) 뒤 주어·동사가 뒤집힌다",
        formula="원래 어순(주어+동사)으로 되돌려 읽는다. 문두 부정어는 '거의/결코 ~않다'로.",
        combat="실전 팁 — 원문장으로 되돌리지 마라. 문두 부정어를 '결코/거의 ~않다·~뿐 아니라·오직 ~해서야'로 먼저 받고, 뒤의 '조동사+주어'는 그냥 주어로 이어 읽는다. 도치는 강조라 그 자리가 답 단서일 때가 많다.",
        pattern=re.compile(r"^\s*(Never|Rarely|Seldom|Hardly|Little|Not only|Nor|No sooner|"
                           r"Only|Not until|Neither|Nowhere|Scarcely|No longer)\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="parallel", title="병렬구문",
        signal="not only A but (also) B / both A and B / either…or / neither…nor / A, B, and C",
        formula="접속사 앞뒤로 '같은 급(품사)'을 짝지어 같은 자리에 놓고 대칭으로 읽는다.",
        combat="실전 팁 — and/but/or 앞뒤에 같은 모양(품사)을 손가락으로 짚어 짝 맞추기. 짝이 안 맞으면 병렬 대상을 잘못 잡은 것.",
        pattern=re.compile(r"\bnot only\b.+?\bbut\b|\bboth\b.+?\band\b|"
                           r"\beither\b.+?\bor\b|\bneither\b.+?\bnor\b|"
                           r"\bnot\b.+?\bbut (also|rather)\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="apposition", title="동격구문",
        signal="the fact/idea/belief/notion that … , 또는 'N, (a/the) N,' 콤마 동격 (앞 명사=뒤 설명)",
        formula="동격은 앞 명사를 '즉/다시 말해'로 풀어 뒤가 같은 대상임을 확인한다.",
        combat="실전 팁 — the fact that … 의 that은 관계사가 아니라 동격(=내용). 'fact = that절 내용'으로 등호를 그어라.",
        pattern=re.compile(r"\b(fact|idea|belief|notion|view|claim|conclusion|possibility|"
                           r"assumption|theory|principle|sense|point|question)\s+that\b|"
                           r",\s+(?:a|an|the)\s+\w+(?:\s+\w+){0,2},", re.IGNORECASE),
    ),
    SyntaxType(
        id="what_clause", title="what절",
        signal="what 이 이끄는 명사절 (what S V = '~하는 것')",
        formula="what절은 통째로 하나의 명사(주어·목적어·보어)다: '~하는 것'으로 묶어 읽는다.",
        combat="실전 팁 — what은 선행사를 포함(the thing which). what절 전체를 [ ]로 묶어 한 덩어리 명사로 취급.",
        pattern=re.compile(r"\bwhat\s+\w+", re.IGNORECASE),
    ),
    SyntaxType(
        id="insertion", title="삽입절",
        signal="— … — / , which / 콤마 사이에 부가 설명이 끼어든다",
        formula="대시·콤마 사이는 통째로 괄호(없는 셈)로 뼈대부터 읽고 부가 설명으로 취급한다.",
        combat="실전 팁 — 대시/콤마 삽입을 빼도 문장이 성립하면 제대로 괄호친 것. 삽입을 지우면 뼈대가 선명.",
        pattern=re.compile(r"—[^—]+—|―[^―]+―|,\s+which\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="participle", title="분사구문",
        signal="문두나 콤마 뒤에 V-ing / V-ed 덩어리가 붙는다(부대상황)",
        formula="분사 덩어리를 괄호 → 주절 뼈대부터 읽고 ~하면서/~한 채로/~해서로 붙인다.",
        combat="실전 팁 — 콤마+V-ing/V-ed는 부대상황 신호. 분사의 의미상 주어는 주절 주어와 같다.",
        pattern=re.compile(r"(?:^|,\s)(\w+ing|\w+ed)\b[^,]{6,},", re.IGNORECASE),
    ),
    SyntaxType(
        id="that_clause", title="that절",
        signal="인식·전달 동사 + that S V (think/believe/show/suggest/argue … that)",
        formula="that절은 통째로 목적어인 '한 문장(명사절)'이다: '~라는 것을'로 묶어 뒤로 붙인다.",
        combat="실전 팁 — 동사 뒤 that은 '~라는 것을'. 접속사 that은 뒤에 완전한 문장(S+V)이 온다(관계사 that과 구분).",
        pattern=re.compile(r"\b(believe|think|show|suggest|argue|claim|find|found|know|knew|say|"
                           r"said|reveal|indicate|assume|conclude|note|mean|meant|imply|insist|"
                           r"realize|recognize|prove|demonstrate|report)s?\s+that\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="wh_clause", title="wh절",
        signal="who / whom / whose / which / where / when / why / how 가 이끄는 관계·명사절",
        formula="선행사(앞 명사)를 꾸미면 '~하는'으로, 명사절이면 '누가/어디/언제/왜/어떻게 ~하는지'로.",
        combat="실전 팁 — wh- 앞에 명사가 있으면 관계사(그 명사 수식), 없으면 명사절. 어느 쪽이든 wh~끝까지 [ ]로 묶어라.",
        pattern=re.compile(r"\b(who|whom|whose|which|where|when|why|how)\b", re.IGNORECASE),
    ),
    SyntaxType(
        id="prep_stack", title="전치사구 이어붙기",
        signal="명사 뒤에 of/in/on/for/with 전치사구가 두 개 이상 줄줄이 이어진다",
        formula="전치사구는 뒤에서 앞으로 '~의 / ~에 있는'으로 차례차례 붙여 명사를 완성한다.",
        combat="실전 팁 — 전치사가 연달으면 명사 뒤에서 앞으로 화살표. 진짜 주어는 맨 앞 명사 하나뿐.",
        pattern=re.compile(r"\b\w+\s+(of|in|on|for|with|between|among)\s+(?:\w+\s+){1,4}"
                           r"(of|in|on|for|with|to|between|among)\b", re.IGNORECASE),
        min_len=70,
    ),
    SyntaxType(
        id="as_compare", title="as·비교 구문",
        signal="as + 명사/S V(전치사·접속사), as A as B, 비교급·최상급, not all/not always(부분부정)",
        formula="as 뒤가 명사면 '~로서/처럼', S+V면 '~할 때/때문에'. as A as B는 'B만큼 A한'. not all/always는 '모두/항상 ~인 건 아니다'.",
        combat="실전 팁 — as는 뒤를 보고 판별(명사→전치사, S+V→접속사). 비교표현은 '강조'이니 필자가 무엇을 동등·우열로 보는지 잡아라. not+전체어(all/always/every)는 부분부정.",
        pattern=re.compile(r"\bas\s+\w+\s+as\b|\bnot\s+(all|always|every)\b|"
                           r"\bthe\s+\w+er\b[^.]*\bthe\s+\w+er\b|"
                           r"\bno\s+(more|less)\s+than\b", re.IGNORECASE),
        min_len=40,
    ),
]


@dataclass
class SyntaxMatch:
    type: SyntaxType
    sentence: str
    source: str = ""


def detect_type(sentence: str) -> SyntaxType | None:
    for st in SYNTAX_TYPES:
        if len(sentence) >= st.min_len and st.pattern.search(sentence):
            return st
    return None


def group_by_syntax(sentences, per_type: int = 3) -> dict[str, list[SyntaxMatch]]:
    """문장들을 구문 유형별로 per_type 개까지 그룹핑.

    sentences 는 list[str] 또는 list[SourcedSentence](.text/.source) 둘 다 허용.
    """
    buckets: dict[str, list[SyntaxMatch]] = {st.id: [] for st in SYNTAX_TYPES}
    for item in sentences:
        text = getattr(item, "text", item)
        source = getattr(item, "source", "")
        st = detect_type(text)
        if st and len(buckets[st.id]) < per_type:
            buckets[st.id].append(SyntaxMatch(type=st, sentence=text, source=source))
    return buckets
