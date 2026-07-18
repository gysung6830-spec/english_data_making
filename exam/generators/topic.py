"""③ 주제 생성기 (영어 선지). 주제만 출제(제목 X)."""
from __future__ import annotations

from .. import format as F
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, TopicOut
from .base import context

_PROMPT = """아래 분석을 바탕으로 '주제' 문제를 만드세요. 제목이 아니라 '주제'만 출제합니다.

선지(choices) 5개는 모두 영어이며 다음 규칙을 지킵니다.
- 정답 1개: 지문 핵심어휘의 '유의어'로 바꿔 표현(원문 단어를 그대로 쓰지 않음).
- 무관 2개: 정답과 관련 없는 내용.
- 모순 2개: 정답과 반대·모순되는 내용.
- 오답 함정: 무관·모순 선지에는 '지문에 실제로 나온 단어'를 일부 섞어,
  대충 읽으면 정답처럼 보이게 만듭니다(정답은 유의어로 바뀌어 있으므로).

- answer_no: 정답 선지 번호(1~5).
- reason: 정답 근거(한국어). wrong_reasons: 나머지 4개 각각 무관/모순 여부와 이유(한국어).
- passage: 문제에 그대로 보여줄 지문 원문.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str]:
    out: TopicOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        model_cls=TopicOut,
        max_tokens=3000,
        max_retries=max_retries,
    )
    q = F.topic_q(out.passage or body, out.choices)
    wrong = {w.no: w.text for w in out.wrong_reasons}
    a = F.topic_a(out.answer_no, out.reason, wrong)
    return q, a
