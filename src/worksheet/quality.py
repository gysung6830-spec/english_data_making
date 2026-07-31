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


def raw_text_fragmented(raw_text: str) -> bool:
    """추출된 '원문 텍스트'가 조각나(문장 앞부분 잘림) 보이는지 사전 판단.

    LLM 지문 추출을 부르기 전에, 비전(PDF→이미지) 재추출로 전환할지 결정하는 데 쓴다.
    정식 분할기(splitter)는 마침표 뒤 '대문자'가 있어야 끊으므로, 소문자로 시작하는
    조각은 한 덩어리로 뭉쳐 감지되지 않는다. 여기서는 감지 전용으로 마침표+공백을
    느슨하게 끊어 '소문자로 시작하는 문장' 비율만 본다.
    """
    pieces = re.split(r"(?<=[.!?])\s+", (raw_text or "").strip())
    sents = [p for p in pieces if len(_ALPHA.findall(p)) >= 3]
    if len(sents) < 3:
        return False
    lower = sum(1 for s in sents if _starts_lowercase(s))
    return lower >= 2 and lower / len(sents) >= 0.4


def passages_fragmented(pset) -> bool:
    """추출된 PassageSet(지문 본문들)이 조각나 보이는지 판단.

    None 이거나 본문들을 이어 봤을 때 소문자 시작 문장이 많으면 True.
    텍스트 경로 결과가 나쁜지 확인해 비전 재추출로 전환할지 결정하는 데 쓴다.
    """
    if pset is None:
        return True
    bodies = [getattr(ex, "body", "") or "" for ex in getattr(pset, "passages", []) or []]
    if not bodies:
        return True
    return raw_text_fragmented("\n".join(bodies))


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


def assess(analyses, min_sentences: int = 2) -> dict:
    """무인 처리용 최종 품질 게이트 — 결과가 미심쩍으면 '검수 권장' 사유를 모은다.

    자동 복구(조건부 비전 재추출)까지 끝난 '최종 결과'를 검사한다. 여기서 사유가
    잡히면, 사람이 전수 검수하지 않고 이 소수만 확인하면 된다.
    반환: {'ok': bool, 'reasons': [사유...]}  (ok=True 면 검수 불필요)
    """
    reasons: list[str] = []
    lst = list(analyses or [])
    total_sents = sum(len(getattr(a, "sentences", []) or []) for a in lst)

    if not lst or total_sents == 0:
        return {"ok": False, "reasons": ["추출된 문장이 없습니다(추출/인식 실패)."]}

    # 1) 조각남(문장 앞부분 잘림) — 자동 복구로도 못 고친 경우
    fw = fragment_warning(lst)
    if fw:
        reasons.append(fw)

    # 2) 지문당 문장 수가 비정상적으로 적음(추출 실패 의심)
    thin = [i for i, a in enumerate(lst, 1)
            if 0 < len(getattr(a, "sentences", []) or []) < min_sentences]
    if thin:
        reasons.append(f"지문 {', '.join(map(str, thin))}: 문장 수가 너무 적습니다(추출 실패 의심).")

    # 3) 해석이 비어 있는 문장(LLM 태깅 실패 흔적)
    empty_tr = sum(1 for a in lst for s in (getattr(a, "sentences", []) or [])
                   if not (getattr(s, "translation", "") or "").strip())
    if empty_tr:
        reasons.append(f"해석이 비어 있는 문장 {empty_tr}개(태깅 누락 가능).")

    return {"ok": not reasons, "reasons": reasons}
