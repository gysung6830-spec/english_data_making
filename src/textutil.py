"""가벼운 텍스트 유틸 (무거운 의존성 없음).

지문을 '완전한 문장' 단위로 나눠, 프롬프트에 '그대로 쓸 문장 목록'으로 넘기기 위한 것.
LLM 이 문장 앞부분(주어·도입구)을 임의로 잘라내는 문제를 구조적으로 막는다.
"""
from __future__ import annotations

import re

# 마침표가 문장 끝이 아닌 흔한 약어(뒤에 대문자가 와도 문장 분리하면 안 됨)
_ABBR = [
    "e.g.", "i.e.", "etc.", "vs.", "cf.", "al.", "Mr.", "Mrs.", "Ms.",
    "Dr.", "Prof.", "St.", "Fig.", "No.", "U.S.", "U.K.", "a.m.", "p.m.",
]
_SENT_BOUNDARY = re.compile(r'(?<=[.!?])["”’)\]]?\s+(?=[A-Z"“‘(\[])')


def split_sentences(text: str) -> list[str]:
    """영어 지문을 완전한 문장 리스트로 분리(문장 끝부호 유지, 약어 보호)."""
    if not text:
        return []
    t = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    # 약어의 마침표를 임시로 치환해 분리 대상에서 제외
    for ab in _ABBR:
        t = t.replace(ab, ab.replace(".", "\x00"))
    parts = _SENT_BOUNDARY.split(t)
    out = [p.replace("\x00", ".").strip() for p in parts if p.strip()]
    return out


def sentence_list_block(body: str, header: str = "문장 목록") -> str:
    """프롬프트에 붙일 '그대로 쓸 문장 목록' 블록. 문장이 1개 이하면 빈 문자열."""
    sents = split_sentences(body)
    if len(sents) < 2:
        return ""
    lines = "\n".join(f"S{i}) {s}" for i, s in enumerate(sents, start=1))
    return (
        f"[{header} — 아래 문장을 '그대로' 사용하라]\n"
        "아래는 지문을 완전한 문장 단위로 나눈 목록이다. 각 문장을 '하나도 빠뜨리지 말고',\n"
        "'첫 단어부터 끝 문장부호까지 원문 그대로'(자리표시자로 바꾸는 부분만 예외) 순서대로 사용하라.\n"
        "문장의 앞부분(주어·도입구)을 잘라내거나, 한 문장을 여러 조각으로 쪼개지 말 것.\n"
        + lines
    )
