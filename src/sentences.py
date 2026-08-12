"""영어 지문의 문장 분리(규칙기반).

명세 2장: 마침표/느낌표/물음표로 나누되, 약어(Mr., e.g. 등)·인용부호·소수점은
문장 끝으로 오인하지 않도록 예외 처리한다. 문장마다 순번(1부터, 화면엔 S1…)을 매긴다.
"""
from __future__ import annotations

import re

# 마침표가 있어도 문장 끝이 아닌 흔한 약어들(대소문자 구분 없이 매칭)
_ABBREV = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "mt", "vs", "etc",
    "e.g", "i.e", "cf", "al", "inc", "ltd", "co", "dept", "fig", "no",
    "vol", "p", "pp", "u.s", "u.k", "a.m", "p.m", "b.c", "a.d",
    "ph.d", "m.d", "b.a", "m.a", "gen", "sen", "gov", "rep", "capt",
}

# 문장 종결 후보: . ! ? (연속 가능) + 닫는 따옴표/괄호가 뒤따를 수 있음
_BOUNDARY = re.compile(r'([.!?]+["”’\')\]]?)\s+')


def _is_abbrev_end(text: str, dot_index: int) -> bool:
    """dot_index 위치의 마침표가 약어의 일부인지 판정."""
    # 마침표 앞의 '단어'(영문자·마침표로 이뤄진) 를 뒤로 훑는다: e.g / U.S 등도 포착
    j = dot_index
    start = j
    while start - 1 >= 0 and (text[start - 1].isalpha() or text[start - 1] == "."):
        start -= 1
    token = text[start:dot_index].lower().strip(".")
    if token in _ABBREV:
        return True
    # 이니셜(대문자 한 글자) 뒤 마침표: 'A.' 'J.' → 문장 끝 아님
    if len(token) == 1 and text[dot_index - 1].isupper():
        return True
    return False


def _is_decimal(text: str, dot_index: int) -> bool:
    """3.14 처럼 숫자 사이 소수점인지."""
    return (
        dot_index > 0 and dot_index + 1 < len(text)
        and text[dot_index - 1].isdigit() and text[dot_index + 1].isdigit()
    )


def split_sentences(text: str) -> list[str]:
    """영어 지문 텍스트를 문장 리스트로 분리한다."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []

    sentences: list[str] = []
    start = 0
    for m in _BOUNDARY.finditer(text):
        end = m.end(1)          # 종결부호(따옴표 포함) 다음 위치
        dot = m.start(1)        # 첫 종결부호 위치
        ch = text[dot]
        if ch == "." and (_is_abbrev_end(text, dot) or _is_decimal(text, dot)):
            continue
        sentence = text[start:end].strip()
        if sentence:
            sentences.append(sentence)
        start = m.end()         # 공백 뒤(다음 문장 시작)
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def split_passage(paragraphs: list[str]) -> list[str]:
    """문단 목록 -> 문장 리스트(문단 순서대로 이어 붙임)."""
    out: list[str] = []
    for para in paragraphs:
        out.extend(split_sentences(para))
    return out
