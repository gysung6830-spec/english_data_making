"""'확인 권장 문항' 판정 — 무인 배치에서 사람 검수가 필요한 문항만 골라낸다.

사람이 일일이 검수하지 않는 배치 운영이므로, 다음 두 경우만 '확인 권장'으로 표시해
PDF 맨 끝 별도 페이지에 모아 준다(해설지 문항에는 배지를 달지 않는다):

  ① 자동 보정된 문항 — 파이프라인이 LLM 출력을 고쳐야 했던 문항.
     (순서 파라미터 재분배·삽입 위치 클램프·정답 문장 스냅 등) → build 계열이 사유를 기록.
  ② 오답 근거가 약한 문항 — 4개 오답 근거가 지나치게 짧아 함정이 부실할 수 있는 문항.
     (주제·내용일치·B·F 등 4지 오답형) → 아래 weak_distractors 로 판정.
"""
from __future__ import annotations

# 검토 항목 문구(교사 점검용) — build 계열이 flags 싱크에 append.
# '자동 보정' 같은 티가 아니라, 교사가 스스로 점검하는 체크리스트 어투로 적는다.
FIX_ORDER = "정답 순서 배열 재확인"
FIX_INSERT = "삽입 문장 위치 재확인"
FIX_SNAP = "정답 문장 표기 재확인"

# 지문 종류 × 문항 유형 부적합 조합 — 근거가 약해 사람 검수가 필요하다.
# (안내문·도표는 산문 논리가 없어 순서·삽입·요약·빈칸의 정답 근거가 약하고,
#  서사·심경문은 '주제'보다 심경/분위기가 맞을 수 있다.)
_UNFIT: dict[str, dict[str, str]] = {
    "notice": {
        "order": "안내문(항목 나열): 순서 정답 근거 재확인",
        "insert": "안내문(항목 나열): 삽입 위치 근거 재확인",
        "B": "안내문: 함의추론 성립 여부 재확인",
        "imply": "안내문: 함축의미 성립 여부 재확인",
        "E": "안내문: 요약문 성립 여부 재확인",
    },
    "chart": {
        "order": "도표 지문: 순서 정답 근거 재확인",
        "insert": "도표 지문: 삽입 위치 근거 재확인",
        "topic": "도표 지문: 주제 성립 여부 재확인",
        "E": "도표 지문: 요약문 성립 여부 재확인",
        "F": "도표 지문: 빈칸추론 성립 여부 재확인",
    },
    "narrative": {
        "topic": "서사·심경문: 주제보다 심경·분위기일 수 있음 재확인",
    },
}


def type_fit_flags(passage_type: str | None, type_key: str) -> list[str]:
    """지문 종류에 부적합한 문항 유형이면 '확인 권장' 사유를 돌려준다(아니면 빈 목록).
    3회 슬롯키(topic_1·content_3 …)는 base(topic·content …)로 정규화해 판정한다."""
    import re
    base = re.sub(r"_\d+$", "", type_key or "")
    fit = _UNFIT.get((passage_type or "prose"), {})
    reason = fit.get(type_key) or fit.get(base)
    return [reason] if reason else []

# 오답 근거가 '빈약'하다고 볼 최소 글자수(이하이면 근거가 사실상 비어 있음)
_MIN_REASON = 8


def weak_distractors(wrong_reasons) -> list[str]:
    """4지 오답형의 오답 근거가 너무 짧으면 '확인 권장' 사유를 돌려준다.

    wrong_reasons: [WrongReason(no, text)] — 정답을 제외한 오답들의 '틀린 이유'.
    근거가 비어 있거나 한두 마디뿐이면 함정이 부실할 수 있어 검토 대상으로 표시한다.
    """
    weak = [w for w in wrong_reasons
            if len((getattr(w, "text", "") or "").strip()) < _MIN_REASON]
    if weak:
        return [f"오답 선지 근거 보강 검토 (오답 {len(wrong_reasons)}개 중 {len(weak)}개)"]
    return []
