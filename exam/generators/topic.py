"""③ 주제 생성기 (영어 선지). 지문은 원본 그대로, 주제만 출제(제목 X)."""
from __future__ import annotations

from .. import answer_spread, build as B
from .. import review, shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, TopicOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '주제' 문제를 만드세요. 지문은 원본 그대로 쓰이며,
당신은 영어 선지 5개만 만듭니다. 제목이 아니라 '주제'입니다.

선지(choices) 5개 — 평가원식 대의파악 설계:
- 정답 1개: 주제문·반복어구·역접(But/However) 뒤 '필자의 초점'을 담은 '명사구'.
  지문 단어를 그대로 쓰지 말고 '다른 말(유의어)'로 재진술. 넓지도 좁지도 않게
  (대주제로 확대 X, 예시·일부 세부로 축소 X).
- 오답 4개는 아래 '5개 축'에서 골라 설계하고, 그중 '매력적 오답' 1개를 반드시 넣는다:
  1) 범위 비틀기 — 지문보다 너무 넓게 또는 너무 좁게.
  2) 방향 반전 — 필자 주장과 정반대·왜곡(±어휘, 역접 뒤 주장 뒤집기).
  3) 표면 어휘 함정 — 지문의 눈에 띄는 단어를 그대로 복사해 익숙해 보이나 논점이 아님.
  4) 근거 없음 — 그럴듯하나 지문에 근거가 없는 내용.
  5) 초점 이동 — 소재는 맞지만 필자 논점이 아닌 곁가지.
- '매력적 오답' 1개: 정답과 비슷하나 '한 끗(범위 또는 방향)'만 어긋나게 하여 변별.

- answer_no: 정답 선지 번호(1~5).
- reason: 정답 근거(한국어). wrong_reasons: 오답 4개 각각 '축 이름 — 이유'(한국어).
  '축이다'라는 말은 쓰지 마세요('방향 반전 — 지문은 …' 처럼 이름 뒤에 줄표를 씁니다).

[확실성] 정답은 지문 전체를 정확히 포괄(과대·과소 금지). 오답 4개는 각각 위 축으로 '확실히'
어긋나야 하고, 매력적 오답조차 결국 한 끗이 틀려 반박 가능해야 한다. (정답은 오직 하나)

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    def _chk(o: TopicOut) -> None:
        # 주제 선지는 명사구로 통일해야 한다 — 하나만 절이면 모양으로 답이 보인다.
        bad = shape.check_choice_shape(o.choices, o.answer_no, "선지",
                                       noun_phrase=True)
        if bad:
            raise ValueError("주제 문항 설계 결함 — " + " ".join(bad))

    out: TopicOut = client.structured(
        system=SYSTEM,
        prompt=(variant_hint + "\n" if variant_hint else "") + _PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=TopicOut,
        max_tokens=2500,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    wrong = {w.no: w.text for w in out.wrong_reasons}
    choices, answer_no = out.choices, out.answer_no
    reason = out.reason
    if answer_pos:   # 정답 위치 분산(선지 재배열 — 정오 불변)
        mapping = answer_spread.perm_map(len(choices), answer_no, answer_pos)
        choices, answer_no, wrong = answer_spread.place_answer(
            choices, answer_no, answer_pos, wrong)
        # 해설이 지칭한 선지 번호를 '전부' 새 번호로 옮긴다(정답만 고치면 나머지가 밀린다).
        reason = answer_spread.relabel_choice_refs(reason, mapping)
        wrong = {n: answer_spread.relabel_choice_refs(t, mapping)
                 for n, t in (wrong or {}).items()}
    q, a = B.make_topic(analysis.sentences, choices, answer_no, reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)
