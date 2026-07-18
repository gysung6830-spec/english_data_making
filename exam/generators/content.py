"""내용 일치 생성기 (한글 선지) — 서술형 앞. 지문은 원본 그대로."""
from __future__ import annotations

from .. import build as B
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, ContentOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '내용 일치' 문제를 만드세요. 발문은 '위 글의 내용과 일치하는
것은?'이며, 지문은 원본 그대로 쓰입니다. 당신은 한글 선지 5개만 만듭니다.

- choices: 한국어 선지 5개.
- 정확히 1개(answer_no)만 글의 내용과 '일치'합니다(특정 문장으로 근거를 댈 수 있어야 함).
- 나머지 4개는 글의 특정 부분과 '어긋나게' 만듭니다. 대충 읽으면 그럴듯하되, 숫자·주체·
  긍정/부정·인과 등 '어느 한 부분'이 지문과 반대이거나 없는 내용이어야 합니다.
- reason: 정답이 지문의 어느 문장과 일치하는지 한국어로 설명.
- wrong_reasons: 오답 4개 각각에 대해 '지문은 ~라고 했는데 선지의 ~부분이 틀렸다'처럼
  틀린 부분을 콕 집어 한국어로 설명.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str]:
    out: ContentOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        model_cls=ContentOut,
        max_tokens=2500,
        max_retries=max_retries,
    )
    wrong = {w.no: w.text for w in out.wrong_reasons}
    return B.make_content(analysis.sentences, out.choices, out.answer_no, out.reason, wrong)
