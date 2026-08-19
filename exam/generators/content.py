"""내용 일치 생성기 (한글 선지) — 서술형 앞. 지문은 원본 그대로.

난이도 두 단계:
  difficulty="plain"  — 오답을 지문과 명확히 어긋나게(주로 정반대).
  difficulty="hard"   — 오답을 '헷갈리게'. 정반대 대신 아래 함정 기법을 섞는다.
      · 부분 일치 + 한 요소만 왜곡(숫자·범위·조건)
      · 주체 바꿔치기(누가/무엇을만 맞바꿈)
      · 인과 날조·역전(없던 because 를 끼움)
      · 정도·범위 과장(often/may/one → only/always/must/the main)
      · 미언급인데 그럴듯(모순 아님, 단지 지문에 없음)
    또한 정답은 유의어로 '위장'하고, 오답에는 원문 단어를 그대로 노출해 함정으로 쓴다.
"""
from __future__ import annotations

from .. import answer_spread, build as B
from .. import review
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, ContentOut
from .base import context

PLAIN = "plain"
HARD = "hard"

_PROMPT_PLAIN = """아래 '정본 지문'으로 '내용 일치' 문제를 만드세요. 발문은 '위 글의 내용과 일치하는
것은?'이며, 지문은 원본 그대로 쓰입니다. 당신은 한글 선지 5개만 만듭니다.

- choices: 한국어 선지 5개. 정확히 1개(answer_no)만 글과 일치합니다.
- 나머지 4개는 글의 특정 부분과 어긋나게 만듭니다(주체·숫자·긍정/부정·인과 중 한 부분).
- reason: 정답이 지문의 어느 문장과 일치하는지 한국어로 설명.
- wrong_reasons: 오답마다 '지문은 ~라고 했는데 선지의 ~부분이 틀렸다'처럼 콕 집어 설명.

{ctx}
"""

_PROMPT_HARD = """아래 '정본 지문'으로 '내용 일치' 문제를 만드세요. 발문은 '위 글의 내용과 일치하는
것은?'이며, 지문은 원본 그대로 쓰입니다. 당신은 한국어 선지 5개만 만듭니다.
'뻔한' 정반대 오답은 피하고, 최대한 헷갈리게 만드세요.

[정답 1개] answer_no
- 지문의 '눈에 덜 띄는 세부 사실'을 고르고, 원문 단어를 그대로 쓰지 말고 '유의어로 패러프레이즈'
  하여 위장합니다(첫눈에 정답처럼 보이지 않게).

[오답 4개] 아래 네 가지 함정 기법을 '각각 하나씩'(4개 = 4기법) 사용하고, 각 오답에는 지문에
실제로 나온 단어를 일부 그대로 노출해 정답처럼 보이게 하세요.
  (1) 부분 일치 + 한 요소만 왜곡: 문장 대부분은 지문과 맞고, 숫자·대상·긍정/부정 등 '딱 한
      군데'만 지문과 다르게(특히 여러 항목을 나열한 뒤 마지막 한 항목만 반대로 바꾸기 효과적).
  (2) 주체 바꿔치기: 지문의 진짜 관계에서 행위자/대상만 맞바꿈(단어는 다 지문에 있음).
  (3) 인과 날조·역전: 두 사실은 맞되 지문에 없는 인과(~때문에/~하므로)를 끼우거나 원인·결과를
      뒤집음.
  (4) 미언급인데 그럴듯: 지문과 모순은 아니지만 아예 언급되지 않은, 주제상 그럴듯한 상식적 진술
      (반박할 문장이 없어 가장 헷갈림).

- reason: 정답이 지문의 어느 문장(원문 표현 인용)과 일치하는지 한국어로 설명.
- wrong_reasons: 오답마다 어떤 함정인지와 '어느 한 부분'이 왜 틀렸는지(또는 '지문에 언급 없음'
  인지)를 콕 집어 한국어로 설명. 끝에 함정 유형을 괄호로 표기(예: (주체 바꿔치기)).

[확실성] 정답은 지문 내용과 '완전히' 일치해야 하고(과장·축소 없이), 오답 4개는 각각 지문의 특정
문장과 '확실히' 어긋나거나 지문에 없어야 한다. 어느 오답도 정답으로 읽힐 여지가 없어야 한다.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, difficulty: str = HARD,
             answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    prompt = _PROMPT_PLAIN if difficulty == PLAIN else _PROMPT_HARD
    out: ContentOut = client.structured(
        system=SYSTEM,
        prompt=(variant_hint + "\n" if variant_hint else "") + prompt.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=ContentOut,
        max_tokens=2800,
        max_retries=max_retries,
    )
    wrong = {w.no: w.text for w in out.wrong_reasons}
    choices, answer_no = out.choices, out.answer_no
    old_no = answer_no
    if answer_pos:   # 정답 위치 분산(선지 재배열 — 정오 불변)
        choices, answer_no, wrong = answer_spread.place_answer(
            choices, answer_no, answer_pos, wrong)
    reason = answer_spread.relabel_answer_ref(out.reason, old_no, answer_no)
    q, a = B.make_content(analysis.sentences, choices, answer_no, reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)
