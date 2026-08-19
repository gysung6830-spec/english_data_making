"""의심문항(⚠) 전용 2차 검수 — 무인 운영 오류 저감.

전 문항이 아니라 '자가검증에서 의심(review_flag)으로 표시된 문항'만 2차 LLM 으로
정답 타당성을 재확인한다(비용 최소). 검수 실패 문항은 재생성한다.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..core.models import Question

REVIEW_SYSTEM = (
    "당신은 학교 영어 시험 문항을 검수하는 까다로운 검토자다. 표시된 정답이 실제로 옳고, "
    "정답이 유일하며(다른 선지·답은 확실히 틀림), 지문·선지에 사실/문법 오류가 없는지 "
    "엄격히 판정한다. 조금이라도 복수정답이거나 정답이 틀렸으면 ok=false. 반드시 JSON 으로만 답한다."
)


class ReviewVerdict(BaseModel):
    ok: bool = Field(..., description=(
        "정답이 유일하게 옳고 다른 선지/답은 확실히 틀리며 오류가 없으면 true, 아니면 false"))
    issue: str = Field("", description="ok=false 일 때 구체적 문제(복수정답·정답오류·오류). ok=true 면 빈 문자열")


def review_question(client: Any, q: Question) -> tuple[bool, str]:
    """(ok, issue) 반환. 검수 호출 실패 시 (True, '')로 문항을 보존한다."""
    passage = q.passage_text or ""
    multi = q.type == "grammar_multi"    # 복수정답 유형은 '모두 고르기'가 정상
    if q.choices and any(c.text for c in q.choices):
        body = "[선지]\n" + "\n".join(f"{c.label} {c.text}" for c in q.choices)
    elif q.choices and multi:            # 복수정답: 밑줄 ①~⑤ 중 '여러 개'가 정답
        body = "[선지] 지문의 밑줄 ①~⑤ 중 어법상 틀린 것 '모두'(복수정답)"
    elif q.choices:                      # 번호형(어법 등): 지문 안 ①~⑤로 판단
        body = "[선지] 지문의 밑줄/문장 ①~⑤ 중 하나"
    else:                                # 서술형
        body = "[모범답안]\n" + (q.answer or "")
    if multi:
        ask = ("이 문항은 '어법상 틀린 것을 모두 고르는' 복수정답 문항이다. 표시된 정답 집합이 "
               "'틀린 밑줄 전체'와 정확히 일치하면 ok=true. 틀린 것을 빠뜨렸거나 맞는 것을 "
               "포함했으면 ok=false 로 하고 issue 에 이유를 적어라.")
    else:
        ask = ("이 문항의 표시된 정답이 '유일하게' 옳은가? 복수정답이거나 정답이 틀렸거나 "
               "지문·선지에 오류가 있으면 ok=false 로 판정하고 issue 에 이유를 적어라.")
    prompt = (f"[지문]\n{passage}\n\n[발문]\n{q.stem}\n\n{body}\n\n"
              f"[표시된 정답]\n{q.answer}\n\n" + ask)
    try:
        v = client.structured(REVIEW_SYSTEM, prompt, ReviewVerdict, max_retries=1)
        return bool(v.ok), (v.issue or "")
    except Exception:  # noqa: BLE001 - 검수 실패는 문항 보존
        return True, ""
