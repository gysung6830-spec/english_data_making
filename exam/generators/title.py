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

'제목'은 '주제의 비유적 재진술'이다(추상화 위계: 요지 < 주제 < 제목).

선지(choices) 5개 — 평가원식 설계:
- 정답 1개: 주제를 함축·매력적으로 — 은유·의문형·콜론 부제 등 수사를 얹어 주제보다 한 겹 더
  추상/비유하고, 필자의 태도(옹호/비판, ±)를 반영. 지문 단어 그대로 쓰지 않음. 간결하게.
- 오답 4개는 '5개 축'으로 설계하고, '매력적 오답' 1개를 반드시 넣는다:
  1) 범위 비틀기(너무 넓거나 좁은 제목)  2) 방향 반전(필자 태도와 반대·왜곡)
  3) 표면 어휘 함정(지문 단어 복사, 논점 아님)  4) 근거 없음(지문에 없는 내용)
  5) 초점 이동/엉뚱한 비유(소재는 맞으나 곁가지이거나 글과 어긋난 은유).
- '매력적 오답' 1개: 정답과 비슷하나 '한 끗(범위 또는 방향)'만 어긋나게.

- answer_no: 정답 선지 번호(1~5).
- reason: 정답 근거(한국어). wrong_reasons: 오답 4개 각각 '어느 축인지 + 이유'(한국어).

[확실성] 정답 제목은 지문 전체를 정확히 대표(과대·과소 금지). 오답은 각각 위 축으로 확실히
어긋나 반박 가능해야 한다. (정답은 오직 하나)
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
