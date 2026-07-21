"""문장 분할 (명세서 §5-2, §10-4).

원문자 ①②③… 마커가 있으면 그 경계로 우선 나누고, 없으면 구두점(. ! ?)
기준으로 자동 분할한다. 약어(Mr. 등)·소수점·따옴표 안 마침표에 오분할되지
않도록 최소한의 보호 장치를 둔다.
"""
from __future__ import annotations

import re

# 원문자 ①~⑳ (U+2460~U+2473). 지문에 문장 번호로 흔히 쓰인다.
CIRCLED = "".join(chr(0x2460 + i) for i in range(20))
_CIRCLED_RE = re.compile(f"[{CIRCLED}]")

# 약어: 마침표 뒤에서 문장을 끊으면 안 되는 흔한 경우.
_ABBREV = {
    "mr", "mrs", "ms", "dr", "prof", "st", "vs", "etc", "e.g", "i.e",
    "no", "fig", "inc", "ltd", "co", "jr", "sr", "u.s", "u.k",
}


def _circled_index(ch: str) -> int:
    """원문자 문자를 1-based 번호로. (① → 1)"""
    return ord(ch) - 0x2460 + 1


def split_by_circled(text: str) -> list[str]:
    """원문자 마커(①②…) 경계로 분할. 마커가 2개 미만이면 빈 리스트 반환."""
    marks = list(_CIRCLED_RE.finditer(text))
    if len(marks) < 2:
        return []
    out: list[str] = []
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        seg = text[start:end].strip()
        if seg:
            out.append(seg)
    return out


def split_by_punct(text: str) -> list[str]:
    """구두점(. ! ?) 기준 분할. 약어/소수점은 최대한 보호."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    sentences: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        buf.append(ch)
        if ch in ".!?":
            # 다음 유의미 문자
            j = i + 1
            while j < n and text[j] in ".!?\"')]”’":
                buf.append(text[j])
                j += 1
            rest = text[j:]
            # 소수점(숫자.숫자) 보호
            if ch == "." and i + 1 < n and text[i + 1].isdigit() and text[i - 1:i].isdigit():
                i = j
                continue
            # 약어 보호
            word = re.split(r"[\s]", "".join(buf).strip())[-1].rstrip(".!?\"')]”’").lower()
            if word in _ABBREV:
                i = j
                continue
            # 문장 경계로 인정하려면 뒤에 공백+대문자/따옴표/끝
            if j >= n or (text[j] == " " and (j + 1 >= n or text[j + 1] in "\"“‘([" or text[j + 1].isupper())):
                sentences.append("".join(buf).strip())
                buf = []
            i = j
            continue
        i += 1
    tail = "".join(buf).strip()
    if tail:
        sentences.append(tail)
    return [s for s in sentences if s]


# 문장 끝(. ! ?) 뒤 공백 + 생략부호(...)로 시작하는 다음 조각의 경계.
# 예: "... activities. ...conversational ..." → 두 문장으로 분리.
_ELLIPSIS_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=\.\.\.)")


def split_sentences(text: str) -> list[str]:
    """지문 텍스트 → 문장 목록. 원문자 우선, 없으면 구두점.

    여러 문단(빈 줄로 구분)이 들어와도 하나의 지문으로 이어붙여 분할한다.
    생략부호(…/...)로 시작하는 조각(순서·삽입·요약 유형 지문)은 각각 별도 문장으로 본다.
    """
    text = (text or "").strip().replace("…", "...")   # 생략부호 정규화
    if not text:
        return []
    circled = split_by_circled(text)
    if circled:
        # 원문자로 나눈 각 조각 안에 다시 여러 문장이 있을 수 있으나,
        # 학습지에서는 원문자 = 한 '문장 단위' 로 취급하는 관례를 따른다.
        return circled
    # 원문자가 없으면 문단을 합쳐 구두점 분할
    joined = re.sub(r"\s*\n\s*", " ", text)
    # '문장끝 + 생략부호 시작' 조각을 먼저 경계로 끊고(합쳐짐 방지), 각 조각을 다시 구두점 분할.
    out: list[str] = []
    for part in _ELLIPSIS_BOUNDARY.split(joined):
        out.extend(split_by_punct(part))
    return [s for s in out if s]
