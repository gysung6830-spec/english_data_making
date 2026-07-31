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
