"""분석기 (명세서 §6): 지문 1회 분석 — 6종이 나눠 쓴다.

문장 분리 · 핵심어휘+유의어+반의어 · 주제 한 문장 · 문법 밀집 문장을 추출한다.

중요(정확성): 문제의 '바탕 지문'은 AI 출력이 아니라 '사용자가 넣은 원문'을 그대로
쓴다. 즉 sentences 는 입력 지문을 코드가 문장 단위로 나눈 것으로 강제 교체하여,
AI 가 지문을 바꿔 말하더라도 넣은 지문으로만 문제가 만들어지도록 한다.
"""
from __future__ import annotations

import re

from .llm import SYSTEM, ClaudeClient
from .schemas import Analysis

_PROMPT = """다음 영어 지문을 1회 분석하여 JSON 으로 반환하세요.
이 분석 결과는 순서·삽입·주제·어휘·어법·내용일치·서술형 문제 생성에 공용으로 쓰입니다.

- title: 지문에 어울리는 짧은 제목(한국어 가능).
- passage_type: 지문의 종류를 다음 중 하나로 판정.
  prose(설명·논설문) · narrative(이야기·서사·심경 묘사) · notice(행사/대회/모집 안내문,
  항목 나열식) · chart(도표·그래프 설명) · letter(편지·이메일) · dialogue(대화).
  애매하면 prose.
- sentences: 지문을 문장 단위로 순서대로 나눈 배열(원문 그대로, 절대 바꾸지 말 것).
- main_idea: 지문의 주제를 담은 한 문장(영어).
- key_terms: 지문 핵심어 8~14개. 각 항목은 word(원문 형태), synonym(유의어),
  antonym(반의어, 없으면 빈 문자열). word 는 반드시 지문에 실제로 등장하는 단어여야 함.
- hardest_sentence: 문법 요소가 가장 많은(가장 어려운) 문장 1개(원문 그대로).

[지문]
{body}
"""

# 문장 경계: 마침표/물음표/느낌표(뒤에 닫는 따옴표가 와도 됨) + 공백 + 대문자/따옴표/괄호.
# 닫는 따옴표를 허용하지 않으면 "… humanity.' Wrong again." 이 한 문장으로 붙어,
# 순서·삽입의 덩어리가 필요 이상으로 커진다.
_SENT_BOUNDARY = re.compile(
    r'''(?:(?<=[.!?])|(?<=[.!?]['"”’]))\s+(?=[A-Z"'(\[])''')

# 마침표가 문장 끝이 아닌 흔한 약어(뒤에 대문자가 와도 문장을 나누지 않도록 보호)
_ABBR = ["Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Jr", "St", "Mt", "vs", "No",
         "Fig", "Inc", "Ltd", "Co", "Corp", "Gen", "Sen", "Rev", "Gov"]
# 이름 가운데 이니셜(Paul R. Ehrlich) — 대문자 한 글자 + 마침표 뒤에 또 대문자가 오면
# 문장 끝처럼 보이지만 사람 이름이다. 보호하지 않으면 이름 한가운데서 문장이 갈라져
# 밑줄 번호가 'Paul R. ① Ehrlich' 처럼 이름 사이에 박힌다(실제 결과물 버그).
_INITIAL = re.compile(r'(?<![A-Za-z])([A-Z])\.(?=\s+[A-Z])')
# 낱자마다 마침표가 붙은 약어 — U.S. · U.K. · e.g. · i.e. · a.m. · Ph.D.
# 이 마침표들은 문장 끝이 아니다. 'in the U.S. during the 1970s' 가 갈리면
# 뒤 조각이 소문자로 시작하는 반쪽 문장이 된다.
_ACRONYM = re.compile(r'(?<![A-Za-z])(?:[A-Za-z]\.){2,}')
# 마침표를 품은 그 밖의 약어. 'etc.'·'no.' 는 진짜 문장 끝일 수 있어 넣지 않는다.
_DOTTED = re.compile(r'(?<![A-Za-z])(et al|cf|viz|approx)\.', re.IGNORECASE)
_DOT = "\x00"   # 임시 치환용 (본문에 없을 제어문자)

# 따옴표 짝 세기 — 조각이 인용문 한가운데서 끊겼는지 본다.
#   여는 작은따옴표: 낱말 시작 앞      ( he said 'sometime … )
#   닫는 작은따옴표: 낱말·문장부호 뒤  ( … humanity.' )
#   낱말 사이의 ' 는 아포스트로피(don't·planet's)이므로 어느 쪽에도 걸리지 않는다.
_OPEN_Q = re.compile(r"(?<![A-Za-z0-9])['‘](?=[A-Za-z0-9])")
_CLOSE_Q = re.compile(r"(?<=[\w.,;:!?])['’](?![A-Za-z0-9])")


def _quote_open(s: str) -> bool:
    """이 조각이 '따옴표를 연 채로' 끝나는가."""
    if (s.count('"') + s.count("“") + s.count("”")) % 2:
        return True
    return len(_OPEN_Q.findall(s)) > len(_CLOSE_Q.findall(s))


def _join_quoted(parts: list[str]) -> list[str]:
    """인용문 한가운데서 갈라진 조각을 다시 붙인다.

    'sometime in the next 15 years, the end will come. And by "the end" I mean …'
    처럼 인용문 안에 마침표가 있으면 문장 경계 규칙이 그 자리에서 자른다. 그러면 여는
    따옴표만 있는 조각과 닫는 따옴표만 있는 조각이 생겨, 무관한문장·삽입·어순배열이
    '따옴표 짝이 안 맞는 반쪽 문장'을 그대로 내보낸다(실제 결과물 버그).

    전체 지문의 따옴표 짝이 애초에 안 맞으면(세는 규칙이 못 미치는 글) 손대지 않는다.
    """
    if not _quote_open(" ".join(parts)):        # 전체가 균형 → 조각별 판정을 믿을 수 있다
        out: list[str] = []
        for p in parts:
            if out and _quote_open(out[-1]):
                out[-1] = f"{out[-1]} {p}"
            else:
                out.append(p)
        return out
    return parts


def mask_abbrev(text: str) -> str:
    """약어·이니셜의 마침표를 잠시 가린 문자열(공백도 정규화).

    '문장 끝이 아닌 마침표'가 모두 가려지므로, 남은 마침표는 진짜 문장 끝이다.
    문장이 소문자로 시작하는지 같은 검사는 대문자 조건 없이 잘라야 보이므로
    이 함수를 쓴다(split_sentences 는 대문자로 시작하는 문장만 나눈다).
    돌려받은 문자열의 \x00 을 '.' 로 되돌리면 원문이 된다.
    """
    norm = " ".join((text or "").split())
    for ab in _ABBR:
        norm = re.sub(r'\b' + re.escape(ab) + r'\.', ab + _DOT, norm)
    norm = _INITIAL.sub(r'\1' + _DOT, norm)
    norm = _ACRONYM.sub(lambda m: m.group(0).replace(".", _DOT), norm)
    return _DOTTED.sub(lambda m: m.group(1).replace(".", _DOT) + _DOT, norm)


def split_sentences(text: str) -> list[str]:
    """지문 원문을 문장 단위로 나눈다(공백 정규화 + 약어·이니셜·인용문 보호)."""
    norm = mask_abbrev(text)
    parts = [p.strip() for p in _SENT_BOUNDARY.split(norm) if p.strip()]
    parts = _join_quoted(parts)
    return [p.replace(_DOT, ".").strip() for p in parts]


def analyze(client: ClaudeClient, body: str, max_retries: int = 1) -> Analysis:
    analysis = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(body=body.strip()),
        model_cls=Analysis,
        max_tokens=4000,
        max_retries=max_retries,
    )
    # 바탕 지문은 반드시 '넣은 원문'을 쓴다(AI 가 지문을 바꿔 말해도 무시).
    real = split_sentences(body)
    if len(real) >= 4:
        analysis.sentences = real
    return analysis
