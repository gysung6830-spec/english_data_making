"""LLM 자기검증 — '고위험 유형'만 생성 직후 한 번 더 확인한다.

구조 검증(개수·범위·토큰 완비 등)으로는 못 잡는 '의미 결함'을 잡는다:
  · 복수 정답(순서·삽입·빈칸·요약이 두 가지로 성립)
  · 어법 오탐(정답 아닌 밑줄이 실은 틀림 / 정답 밑줄이 실은 옳음)
  · 내용일치 참·거짓 오판(정답이 실은 불일치 / 오답이 실은 일치)

동작(파이프라인):
  생성 → (고위험 유형이면) 검증 → 실패 시 1회 재생성 → 그래도 실패면
  '확인 권장'으로 표시(문항은 유지하되 교사 검수 페이지에 사유를 남김).

비용 절감: EXAM_NO_VERIFY=1 이면 전체 비활성(구조 검증만).
"""
from __future__ import annotations

import os
import re

from pydantic import BaseModel


class VerifyOut(BaseModel):
    ok: bool
    reason: str = ""


# 고위험 유형 → 그 유형에서 '집중적으로 볼' 결함(검증 프롬프트에 넣는다).
#   1회: order/insert/grammar/content · 2회: B/C/E/F/G
HIGH_RISK: dict[str, str] = {
    # ---- 변형문제 1회 ----
    "order": "순서 배열의 정답 순서가 '유일하게' 성립하는가. 지시어·연결어·시간/논리 흐름상 "
             "다른 순서도 가능하면 결함이다.",
    "insert": "주어진 문장이 '오직 한 곳'에만 자연스럽게 들어가는가. 두 곳 이상 가능하면 결함이다.",
    "grammar": "정답으로 표시된 밑줄들이 '실제로 어법상 틀렸는가', 그리고 정답이 아닌 밑줄은 "
               "'어법상 옳은가'. 하나라도 어긋나면 결함이다.",
    "content": "정답 선지가 지문과 '확실히 일치'하고, 나머지 4개 오답이 '확실히 불일치'인가. "
               "오답 중 하나라도 참이거나 정답이 애매하면 결함이다.",
    # ---- 변형문제 2회 (A~G) ----
    "B": "밑줄 어구의 함의(정답)가 지문 논지상 '유일하게' 맞는가. 다른 선지도 가능하면 결함이다.",
    "C": "정답으로 표시된 밑줄이 실제로 어법상 틀렸고 나머지는 옳은가.",
    "E": "요약문 빈칸 (A)(B) 정답 조합만 성립하고 나머지 선지는 안 되는가.",
    "F": "빈칸 정답이 '유일'하고 나머지 선지는 성립하지 않는가.",
    "G": "일치하는 선지 '개수'(정답)가 정확한가. 각 선지의 참/거짓을 지문으로 하나씩 확인.",
}

_SYS = ("너는 한국 수능식 영어 시험 문항 검수자다. 주어진 문항과 정답이 결함 없이 "
        "'유일 정답'으로 성립하는지 엄격하게 판정한다. 확신이 없으면 결함(ok=false)으로 본다.")


def enabled() -> bool:
    return os.environ.get("EXAM_NO_VERIFY", "") not in ("1", "true", "True")


def _text(html: str) -> str:
    """조판 HTML → 검증용 평문(태그 제거, 공백 정리)."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def verify(client, type_key: str, q_html: str, a_html: str,
           max_retries: int = 1) -> tuple[bool, str]:
    """(ok, reason). 고위험 유형이 아니거나 검증 비활성/실패면 (True, '')로 통과 처리."""
    focus = HIGH_RISK.get(type_key)
    if not focus or not enabled():
        return True, ""
    prompt = (
        f"[이 유형에서 집중 점검할 것]\n{focus}\n\n"
        f"[문제]\n{_text(q_html)}\n\n"
        f"[정답·해설]\n{_text(a_html)}\n\n"
        "위 정답이 유일하고 결함이 없으면 ok=true, reason 은 빈 문자열.\n"
        "복수정답·어법 오탐·내용 참거짓 오판 등 결함이 있으면 ok=false, reason 에 결함을 "
        "한국어 한 줄로 적어라."
    )
    try:
        out: VerifyOut = client.structured(
            system=_SYS, prompt=prompt, model_cls=VerifyOut,
            max_tokens=600, max_retries=max_retries)
    except Exception:       # noqa: BLE001 — 검증 실패가 생성물을 버리게 하지 않는다
        return True, ""
    return bool(out.ok), (out.reason or "").strip()
