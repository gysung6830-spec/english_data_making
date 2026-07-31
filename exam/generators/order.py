"""① 순서 배열 생성기 — 정본 문장을 덩어리로 쪼개 라벨만 섞는다."""
from __future__ import annotations

from .. import build as B
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, OrderOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '순서 배열' 문제를 만드세요.
지문을 새로 쓰지 말고, 아래 문장들을 '어떻게 나눌지'만 정하세요.

- given_n: 앞에서 몇 문장을 '주어진 글'로 삼을지(>=1).
- block_sizes: 나머지 문장을 (A)(B)(C) 세 덩어리로 나눌 때 각 덩어리의 문장 수(합=나머지 수).
- display: (A)(B)(C)가 각각 '원래 순서상 몇 번째 덩어리(1~3)'인지. (A)가 1번 덩어리가 되지
  않도록 섞어 실제 순서를 알기 어렵게 하세요.
- reason: 연결사·지시어를 근거로 올바른 순서를 한국어로 설명.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    out: OrderOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=OrderOut,
        max_tokens=2500,
        max_retries=max_retries,
    )
    flags: list[str] = []
    q, a = B.make_order(analysis.sentences, out.given_n, out.block_sizes,
                        out.display, out.reason, flags=flags)
    return q, a, flags
