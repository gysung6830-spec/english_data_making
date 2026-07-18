"""② 문장 삽입 생성기."""
from __future__ import annotations

from .. import format as F
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, InsertOut
from .base import context

_PROMPT = """아래 분석을 바탕으로 '문장 삽입' 문제를 만드세요.

- 넣을 위치가 확정되는 문장만 '주어진 문장(given_sentence)'으로 고릅니다.
  (however/therefore/this/such 등 연결사·지시어로 시작하거나 앞뒤와 같은 소재로 묶이는 문장)
- 나머지 본문을 chunks(정확히 6조각)로 나눕니다. 조각 사이 5곳이 위치 ①~⑤ 가 됩니다.
- answer_no: 주어진 문장이 원래 들어가야 할 위치 번호(1~5).
- reason: 지시어·연결 관계를 근거로 왜 그 위치인지 한국어로 설명.
- 주어진 문장은 chunks 안에 포함하지 마세요(빼낸 문장입니다).

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str]:
    out: InsertOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        model_cls=InsertOut,
        max_tokens=3000,
        max_retries=max_retries,
    )
    markers = [F.pos(i) for i in range(1, 6)]
    marked = F.weave(out.chunks, markers)
    q = F.insert_q(out.given_sentence, marked)
    a = F.insert_a(out.answer_no, out.reason)
    return q, a
