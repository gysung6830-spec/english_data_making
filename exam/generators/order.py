"""① 순서 배열 생성기."""
from __future__ import annotations

from .. import format as F
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, OrderOut
from .base import context

_PROMPT = """아래 분석을 바탕으로 '순서 배열' 문제를 만드세요.

- 첫 문단(주어진 글, given) 뒤에 이어질 내용을 세 덩어리 (A)(B)(C) 로 나눕니다.
- 각 덩어리는 논리적으로 자연스럽게 이어지되, 순서를 알 수 있는 단서
  (연결사·지시어·대명사)를 포함하도록 구성합니다.
- orders: 5개의 서로 다른 순서 조합 문자열(예: "(B)-(A)-(C)"). 그 중 하나가 정답.
- answer_no: 올바른 순서가 놓인 보기 번호(1~5).
- reason: 왜 그 순서인지 단서를 들어 한국어로 설명.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str]:
    out: OrderOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        model_cls=OrderOut,
        max_tokens=3000,
        max_retries=max_retries,
    )
    q = F.order_q(out.given, out.seg_a, out.seg_b, out.seg_c, out.orders)
    a = F.order_a(out.answer_no, out.reason)
    return q, a
