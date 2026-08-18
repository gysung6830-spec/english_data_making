"""제목 생성기 (영어 선지). 지문은 원본 그대로, '제목'을 출제(주제문 X).

주제(topic)와 렌더 구조가 같아 TopicOut·make_topic 을 재사용하되, 프롬프트만
'제목'용으로 바꾼다. variant_hint 를 주면 같은 지문의 N번째 제목 문제가 서로
겹치지 않도록 다른 표현·오답으로 만들게 유도한다.
"""
from __future__ import annotations

from .. import answer_spread, build as B
from .. import review
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, TopicOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '제목' 문제를 만드세요. 지문은 원본 그대로 쓰이며,
당신은 영어 선지 5개(제목 후보)만 만듭니다. '주제문'이 아니라 짧고 함축적인 '제목'입니다.

선지(choices) 5개 규칙:
- 정답 1개: 글 전체를 아우르는 제목. 지문 핵심어를 '유의어'로 바꿔 표현(원문 단어 그대로 금지).
  제목답게 간결하고 함축적으로(완전한 설명문 지양).
- 무관 2개: 글과 관련 없는 제목.
- 모순 2개: 글의 논지와 반대·왜곡된 제목.
- 오답 함정: 무관·모순 선지에 '지문에 실제 나온 단어'를 일부 섞어 제목처럼 보이게.

- answer_no: 정답 선지 번호(1~5).
- reason: 정답 근거(한국어). wrong_reasons: 나머지 4개 각각 무관/모순 여부와 이유(한국어).

[확실성] 정답 제목은 지문 전체를 정확히 대표해야 하며 과대·과소가 아니어야 한다.
오답 4개는 각각 확실히 무관하거나 모순이어야 하고, 정답으로 읽힐 여지가 없어야 한다.
{variant}
{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    out: TopicOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis),
                              variant=(("\n" + variant_hint) if variant_hint else "")),
        cache_prefix=context(analysis),
        model_cls=TopicOut,
        max_tokens=2500,
        max_retries=max_retries,
    )
    wrong = {w.no: w.text for w in out.wrong_reasons}
    choices, answer_no = out.choices, out.answer_no
    if answer_pos:
        choices, answer_no, wrong = answer_spread.place_answer(
            choices, answer_no, answer_pos, wrong)
    q, a = B.make_topic(analysis.sentences, choices, answer_no, out.reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)
