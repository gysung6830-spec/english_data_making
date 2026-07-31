"""③ 주제 생성기 (영어 선지). 지문은 원본 그대로, 주제만 출제(제목 X)."""
from __future__ import annotations

from .. import build as B
from .. import review
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, TopicOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '주제' 문제를 만드세요. 지문은 원본 그대로 쓰이며,
당신은 영어 선지 5개만 만듭니다. 제목이 아니라 '주제'입니다.

선지(choices) 5개 규칙:
- 정답 1개: 지문 핵심어휘의 '유의어'로 바꿔 표현(원문 단어를 그대로 쓰지 않음).
- 무관 2개: 정답과 관련 없는 내용.
- 모순 2개: 정답과 반대·모순되는 내용.
- 오답 함정: 무관·모순 선지에는 '지문에 실제로 나온 단어'를 일부 섞어 정답처럼 보이게.

- answer_no: 정답 선지 번호(1~5).
- reason: 정답 근거(한국어). wrong_reasons: 나머지 4개 각각 무관/모순 여부와 이유(한국어).

[확실성] 정답은 지문 전체를 정확히 포괄해야 하며 과대·과소 일반화가 아니어야 한다.
오답 4개는 각각 지문의 특정 부분과 '확실히' 무관하거나 모순이어야 하고, 조금이라도 정답으로
읽힐 여지가 있으면 안 된다. (정답은 오직 하나)

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    out: TopicOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=TopicOut,
        max_tokens=2500,
        max_retries=max_retries,
    )
    wrong = {w.no: w.text for w in out.wrong_reasons}
    q, a = B.make_topic(analysis.sentences, out.choices, out.answer_no, out.reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)
