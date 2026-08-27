"""내용 O/X 생성기 — 진술 5개를 각각 참·거짓으로 판정하게 한다. 지문은 원본 그대로.

5지선다('일치하는 것은?')는 넷을 몰라도 하나만 알면 맞고, 찍어도 20%가 맞는다.
O/X 는 다섯 진술을 모두 판정해야 하므로 지문을 처음부터 끝까지 훑게 되고, 채점할 때
부분 점수도 줄 수 있다(5문항짜리 소묶음처럼 쓸 수 있다).

오답(=X 진술)은 아래 함정 기법으로 만든다 — '정반대'로만 만들면 읽지 않고도 걸러진다.
  · 부분 일치 + 한 요소만 왜곡(숫자·범위·조건)
  · 주체 바꿔치기(누가/무엇을만 맞바꿈)
  · 인과 날조·역전(없던 because 를 끼움)
  · 정도·범위 과장(often/may/one → only/always/must/the main)
  · 미언급인데 그럴듯(모순 아님, 단지 지문에 없음)
그리고 O 진술은 원문 단어를 그대로 쓰지 말고 유의어로 위장한다.
"""
from __future__ import annotations

from .. import build as B
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, ContentOXOut
from .base import context

PLAIN = "plain"
HARD = "hard"

_PROMPT = """아래 '정본 지문'으로 '내용 O/X' 문제를 만드세요. 발문은 '다음 진술이 글의 내용과
일치하면 O, 일치하지 않으면 X 를 쓰시오.' 이며, 지문은 원본 그대로 쓰입니다. 당신은 한국어
진술 5개와 그 판정을 만듭니다.

- statements: 한국어 진술 5개. 읽는 순서는 되도록 지문 흐름을 따라가게 하세요.
- truths: 각 진술이 글과 일치하면 true, 아니면 false.
  **O 는 2개 또는 3개**여야 합니다. 한쪽으로 몰리면 학생이 지문을 읽지 않고 전부 O(또는
  전부 X)로 찍습니다.
- reasons: 진술마다 왜 O 인지(지문의 어느 문장인지) / 어디가 X 인지 콕 집어 한국어로.

[O 진술을 쓰는 법] 눈에 덜 띄는 세부 사실을 고르고, 원문 단어를 그대로 쓰지 말고
'유의어로 패러프레이즈' 하세요(첫눈에 정답처럼 보이지 않게).

[X 진술을 쓰는 법] '뻔한 정반대'는 피하고, 아래 기법을 서로 다르게 골라 쓰세요. 각 X
진술에는 지문에 실제로 나온 단어를 일부 그대로 노출해 그럴듯해 보이게 만드세요.
  (1) 부분 일치 + 한 요소만 왜곡: 문장 대부분은 지문과 맞고 숫자·대상·긍정/부정 등
      '딱 한 군데'만 다르게(여러 항목을 나열한 뒤 마지막 하나만 뒤집으면 특히 효과적).
  (2) 주체 바꿔치기: 지문의 진짜 관계에서 행위자/대상만 맞바꿈(단어는 다 지문에 있음).
  (3) 인과 날조·역전: 두 사실은 맞되 지문에 없는 인과를 끼우거나 원인·결과를 뒤집음.
  (4) 정도·범위 과장: '~하기도 한다'를 '늘·오직·반드시'로 키움.
  (5) 미언급인데 그럴듯: 지문과 모순은 아니지만 아예 언급되지 않은 상식적 진술.

[확실성] O 진술은 지문과 '완전히' 일치해야 하고(과장·축소 없이), X 진술은 지문의 특정
문장과 '확실히' 어긋나거나 지문에 없어야 합니다. 판정이 갈릴 여지가 있으면 안 됩니다.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, difficulty: str = HARD,
             answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    # difficulty·answer_pos 는 O/X 에서 쓰이지 않는다(정답이 한 자리가 아니다).
    out: ContentOXOut = client.structured(
        system=SYSTEM,
        prompt=((variant_hint + "\n" if variant_hint else "")
                + _PROMPT.format(ctx=context(analysis))),
        cache_prefix=context(analysis),
        model_cls=ContentOXOut,
        max_tokens=2800,
        max_retries=max_retries,
    )
    q, a = B.make_content_ox(analysis.sentences, out.statements,
                             list(out.truths), list(out.reasons))
    return q, a, []
