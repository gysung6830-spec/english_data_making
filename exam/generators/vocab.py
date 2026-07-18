"""④ 어휘 생성기 (문맥상 부적절) — 두 가지 방식 지원.

method="synonym" (기본, 명세서 §3-④):
    - 밑줄 5개 중 1개를 반의어로 바꿔 정답, 나머지는 유의어로 변형.
    - 형용사/부사/동사 위주로 밑줄을 선별한다.

method="negation":
    - 밑줄 5개는 원문 단어를 '그대로' 둔다.
    - 다만 정답이 있는 '문장'에 부정어(no/not/neither 등)를 넣어
      그 문장이 글의 흐름과 모순되게 만든다 → 그 밑줄이 문맥상 부적절(정답).
"""
from __future__ import annotations

from .. import format as F
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, VocabOut
from .base import context

SYNONYM = "synonym"
NEGATION = "negation"

_PROMPT_SYNONYM = """아래 분석을 바탕으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 반의어]

- 본문에서 밑줄 칠 단어 5개(words)를 고릅니다. '형용사·부사·동사' 위주로 선별합니다.
- 그 중 정확히 1개(answer_no)는 문맥상 어색하도록 '반의어'로 바꿉니다 → 정답.
- 나머지 4개는 원문 단어를 그대로 노출하지 말고 '유의어'로 변형해 둡니다.
- chunks(정확히 6조각)는 밑줄 단어를 뺀 본문 조각입니다. 조각 사이 5곳에 밑줄 단어가 들어갑니다.
- answer_no: 문맥상 부적절한(반의어로 바뀐) 밑줄 번호(1~5).
- reason: 왜 그 단어가 문맥에 어긋나는지, 나머지는 왜 적절한지 한국어로 설명.

{ctx}
"""

_PROMPT_NEGATION = """아래 분석을 바탕으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 부정어 삽입]

- 본문에서 밑줄 칠 단어 5개(words)를 고릅니다. 형용사·부사·동사 위주로 선별합니다.
- 5개 밑줄 단어는 모두 '원문 그대로' 둡니다(유의어·반의어로 바꾸지 않음).
- 대신 정답(answer_no)이 들어 있는 '문장'에만 부정어(no/not/never/neither 등)를 자연스럽게
  끼워 넣어, 그 문장이 글 전체 흐름과 '모순'되게 만듭니다. 그러면 그 밑줄 단어가
  문맥상 부적절해집니다. (부정어는 chunks 본문 안에 포함시키고, 밑줄로 표시하지 않습니다.)
- 나머지 4개 문장에는 부정어를 넣지 않습니다.
- chunks(정확히 6조각) 사이 5곳에 밑줄 단어가 들어갑니다.
- answer_no: 부정어 때문에 문맥상 모순이 된 밑줄 번호(1~5).
- reason: 삽입된 부정어로 인해 해당 문장이 글의 흐름과 어떻게 모순되는지 한국어로 설명.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, method: str = SYNONYM) -> tuple[str, str]:
    prompt = _PROMPT_NEGATION if method == NEGATION else _PROMPT_SYNONYM
    out: VocabOut = client.structured(
        system=SYSTEM,
        prompt=prompt.format(ctx=context(analysis)),
        model_cls=VocabOut,
        max_tokens=3000,
        max_retries=max_retries,
    )
    markers = [F.underline(i, w) for i, w in enumerate(out.words, 1)]
    marked = F.weave(out.chunks, markers)
    q = F.vocab_q(marked)
    a = F.vocab_a(out.answer_no, out.reason)
    return q, a
