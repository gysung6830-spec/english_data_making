"""④ 어휘 생성기 (문맥상 부적절)."""
from __future__ import annotations

from .. import format as F
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, VocabOut
from .base import context

_PROMPT = """아래 분석을 바탕으로 '어휘(문맥상 부적절)' 문제를 만드세요.

- 본문에서 밑줄 칠 단어 5개(words)를 고릅니다.
- 그 중 정확히 1개(answer_no)는 문맥상 어색하도록 '반의어'로 바꿉니다 → 정답.
- 나머지 4개는 원문 단어를 그대로 노출하지 말고 '유의어'로 변형해 둡니다.
- chunks(정확히 6조각)는 밑줄 단어를 뺀 본문 조각입니다. 조각 사이 5곳에 밑줄 단어가 들어갑니다.
- answer_no: 문맥상 부적절한(반의어로 바뀐) 밑줄 번호(1~5).
- reason: 왜 그 단어가 문맥에 어긋나는지, 나머지는 왜 적절한지 한국어로 설명.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str]:
    out: VocabOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        model_cls=VocabOut,
        max_tokens=3000,
        max_retries=max_retries,
    )
    markers = [F.underline(i, w) for i, w in enumerate(out.words, 1)]
    marked = F.weave(out.chunks, markers)
    q = F.vocab_q(marked)
    a = F.vocab_a(out.answer_no, out.reason)
    return q, a
