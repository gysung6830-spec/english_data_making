"""추출 품질 점검 — 조각난(머리 잘린) 지문을 감지해 경고 문구를 만든다.

원본 PDF/HWP 에서 지문을 뽑을 때, 두 단(영어|한글) 배치나 문제지 형식 때문에
문장 앞부분(주어·동사)이 통째로 빠져 '조각'만 남는 경우가 있다. 이때 학습지는
소문자로 시작하는 미완성 문장이 줄줄이 나온다. 이를 사후 감지해 사용자에게
'추출이 이상하다'고 알려 주기 위한 경량 휴리스틱(외부 의존성 없음).
"""
from __future__ import annotations

import re

_ALPHA = re.compile(r"[A-Za-z]")
_FIRST_ALPHA = re.compile(r"[A-Za-z]")
# 소문자로 시작해도 정상인 흔한 예외(고유·관용 표현은 드묾)
_OK_LOWER_START = {"iPhone", "iPad", "eBay", "pH"}


def _starts_lowercase(text: str) -> bool:
    """문장이 (영문 기준) 소문자로 시작하면 True — 머리 잘림 의심."""
    s = text.lstrip(" \t\"'“‘([—–-·")
    m = _FIRST_ALPHA.search(s[:2])       # 앞 1~2글자 안에 영문이 오는지
    if not m:
        return False                     # 숫자·기호로 시작 → 판단 보류(정상 취급)
    first = m.group(0)
    if first.islower():
        for w in _OK_LOWER_START:
            if s.startswith(w):
                return False
        return True
    return False


def _orphan_punct(text: str) -> bool:
    """' .' , 단독 마침표처럼 앞 단어가 사라져 구두점만 뜬 흔적."""
    return bool(re.search(r"\s[.,;:]", text)) or text.strip() in {".", ",", "!", "?"}


def fragment_warning(analyses) -> str | None:
    """여러 Analysis 를 훑어 조각남이 의심되면 사용자용 경고 문구를 반환.

    - 영문 문장 다수가 소문자로 시작하거나 구두점만 남았으면 경고.
    - 정상 지문(대문자로 시작)에서는 None.
    """
    total = 0
    lower = 0
    orphan = 0
    for a in analyses:
        for s in getattr(a, "sentences", []) or []:
            text = (s.text or "").strip()
            if len(_ALPHA.findall(text)) < 2:
                continue                 # 사실상 빈/기호 문장은 분모에서 제외
            total += 1
            if _starts_lowercase(text):
                lower += 1
            if _orphan_punct(text):
                orphan += 1
    if total < 3:
        return None
    ratio = lower / total
    if ratio >= 0.4 and lower >= 2:
        return (f"추출된 영어 문장 {total}개 중 {lower}개가 소문자로 시작합니다. "
                "원본에서 문장 앞부분(주어·동사)이 잘려 들어왔을 수 있습니다. "
                "지문이 표·2단(영어|한글) 배치이거나 문제지 형식이면, 지문 부분만 "
                "사진(JPG/PNG)으로 저장해 올리면 더 정확합니다.")
    if orphan >= 2 and orphan / total >= 0.3:
        return ("추출된 문장 곳곳에 단어가 빠진 흔적(단독 구두점)이 보입니다. "
                "원본 텍스트가 온전히 추출되지 않았을 수 있으니, 해당 지문을 "
                "사진(JPG/PNG)으로 저장해 올려 보세요.")
    return None
