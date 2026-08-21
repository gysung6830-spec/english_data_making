"""제목 생성기 (수능 24번) — 영어 선지. 지문은 원본 그대로.

주제(23번)와 짝을 이루는 유형이다. 주제가 '무엇을 다루는 글인가'를 명사구로 묻는다면,
제목은 거기에 '함축·비유·대구'를 더해 글 전체를 한 줄로 압축하게 한다. 그래서 같은
지문에서 나와도 주제 문제와 답이 겹치지 않는다.
"""
from __future__ import annotations

from .. import answer_spread, build as B
from .. import review
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, TitleOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '제목' 문제를 만드세요. 지문은 원본 그대로 쓰이며,
당신은 영어 선지 5개만 만듭니다. 주제가 아니라 '제목'입니다.

[제목과 주제의 차이] 반드시 지키세요.
- 주제는 글의 내용을 '설명'하지만, 제목은 글 전체를 '압축해 내건 간판'입니다.
- 제목은 짧고(대체로 4~9 단어), 함축적이며, 비유·대구·콜론(:)·의문형 같은 장치를 씁니다.
  예) "Small Choices, Large Consequences" / "When Less Turns Out to Be More" /
      "Monoculture: The Hidden Cost of Uniformity"
- 완전한 서술문(주어+동사로 끝나는 평서문)은 제목답지 않습니다. 명사구·대구·의문형으로.

선지(choices) 5개
- 정답 1개: 글 전체(도입~결론)를 포괄하고, 필자의 초점(역접 뒤 주장·반복어구)을 담습니다.
  지문 단어를 그대로 베끼지 말고 다른 말로 재진술하세요.
- 오답 4개는 아래 축에서 골라 설계하고, '매력적 오답' 1개를 반드시 넣습니다.
  1) 범위 비틀기 — 글보다 너무 넓거나(대주제로 확대), 너무 좁게(예시 하나만 제목화).
  2) 방향 반전 — 필자 주장과 반대로 내걺.
  3) 표면 어휘 함정 — 지문의 눈에 띄는 단어를 그대로 써서 익숙해 보이나 논점이 아님.
  4) 근거 없음 — 그럴듯하나 글에 근거가 없음.
  5) 초점 이동 — 소재는 맞지만 필자의 논점이 아닌 곁가지를 제목으로.
- '매력적 오답' 1개는 정답과 비슷하되 '한 끗(범위 또는 방향)'만 어긋나게 합니다.

- answer_no: 정답 선지 번호(1~5).
- reason: 정답 근거(한국어) — 글의 어느 부분이 그 제목을 뒷받침하는지.
- wrong_reasons: 오답 4개 각각 '어느 축인지 + 왜 제목이 될 수 없는지'(한국어).

[확실성] 정답은 글 전체를 정확히 포괄해야 하고(과대·과소 금지), 오답 4개는 각각 위 축으로
'확실히' 어긋나 반박 가능해야 합니다. 정답은 오직 하나입니다.
[형식] 선지 5개 모두 제목 형식(명사구·대구·의문형)으로 통일하세요. 하나만 서술문이면
그 자체로 답이 티가 납니다. 각 선지의 주요 단어는 영어 제목 관례대로 대문자로 시작합니다.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    out: TitleOut = client.structured(
        system=SYSTEM,
        prompt=(variant_hint + "\n" if variant_hint else "") + _PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=TitleOut,
        max_tokens=2500,
        max_retries=max_retries,
    )
    wrong = {w.no: w.text for w in out.wrong_reasons}
    choices, answer_no = out.choices, out.answer_no
    old_no = answer_no
    if answer_pos:   # 정답 위치 분산(선지 재배열 — 정오 불변)
        choices, answer_no, wrong = answer_spread.place_answer(
            choices, answer_no, answer_pos, wrong)
    reason = answer_spread.relabel_answer_ref(out.reason, old_no, answer_no)
    q, a = B.make_title(analysis.sentences, choices, answer_no, reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)
