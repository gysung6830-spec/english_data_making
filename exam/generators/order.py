"""① 순서 배열 생성기 — 정본 문장을 덩어리로 쪼개 라벨만 섞는다."""
from __future__ import annotations

from .. import build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, OrderOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '순서 배열' 문제를 만드세요.
지문을 새로 쓰지 말고, 아래 문장들을 '어떻게 나눌지'만 정하세요.

- given_n: 앞에서 몇 문장을 '주어진 글'로 삼을지(>=1). 되도록 1~2문장으로 짧게 두어
  나머지를 네 덩어리로 넉넉히 나눌 수 있게 하세요.
- block_sizes: 나머지 문장을 **(A)(B)(C)(D) 네 덩어리**로 나눌 때 각 덩어리의 문장 수
  (개수 4개, 합 = 나머지 문장 수, 각 덩어리 최소 1문장).
  ※ 문장이 모자라 네 덩어리를 만들 수 없을 때만 세 덩어리(개수 3개)로 하세요.
- display: (A)(B)(C)(D)가 각각 '원래 순서상 몇 번째 덩어리(1~4)'인지. 1~4의 순열입니다.
  **(A)가 1번 덩어리가 되지 않도록** 섞으세요 — (A)가 곧 시작이면 순서를 절반은 그냥 알게 됩니다.
- reason: 연결사·지시어를 근거로 올바른 순서를 한국어로 설명. 덩어리마다 '무엇이 앞을 받는지'
  (지시어·연결사·반복어)를 하나씩 짚어 주세요.

[덩어리 나누는 법] 각 덩어리는 그 자체로 하나의 흐름이어야 하고, 다음 덩어리의 첫 문장에
'앞을 받는 표지'(this·such·however·그 결과 등)가 있어야 순서가 한 가지로 굳습니다.
표지가 없는 자리에서 자르면 두 가지 순서가 다 말이 되어 복수정답이 됩니다.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    def _chk(o: OrderOut) -> None:
        bad = shape.check_order_shuffle(o.display)
        if bad:
            raise ValueError("순서 배열 문항 설계 결함 — " + " ".join(bad))

    out: OrderOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=OrderOut,
        max_tokens=2500,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    flags: list[str] = []
    q, a = B.make_order(analysis.sentences, out.given_n, out.block_sizes,
                        out.display, out.reason, flags=flags)
    return q, a, flags
