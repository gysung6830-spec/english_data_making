"""④ 어휘 생성기 (문맥상 부적절) — 정본에서 지정 단어만 변형. 세 방식 지원.

난이도 연동(상/중/하)으로 자동 선택된다:
  method="negation" (상): 밑줄은 원문 그대로, 정답 문장에만 부정어(no/not/neither)를 넣어
      글의 흐름과 모순되게 만든다(override_no/override_text). — 가장 어려움
  method="synonym"  (중): 밑줄 5개 중 1개=반의어(정답), 나머지=유의어로 패러프레이즈.
  method="original" (하): 정답 1개만 반의어, 나머지 4개는 '원문 단어 그대로' 노출. — 가장 쉬움
"""
from __future__ import annotations

from .. import build as B
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, VocabOut
from .base import context

SYNONYM = "synonym"
NEGATION = "negation"
ORIGINAL = "original"

_PROMPT_SYNONYM = """아래 '정본 지문'으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 반의어]
지문을 새로 쓰지 말고, 밑줄 칠 단어와 표시할 단어만 정하세요.

- marks: 밑줄 5개. 각 항목은 sent_no(문장 번호 1-based), word(그 문장의 원본 단어),
  shown(문제에 보여줄 단어). '형용사·부사·동사' 위주로 고르세요.
- 정확히 1개(answer_no)는 shown 을 '반의어'로 하여 문맥상 어색하게 만듭니다 → 정답.
- 나머지 4개는 shown 을 원본 단어의 '유의어'로 바꿔 둡니다(원문 단어 그대로 노출 금지).
- [확실성] 정답 1개만 확실히 어색해야 한다. 유의어로 바꾼 나머지 4개는 바꾼 뒤에도 문맥이
  '완전히 자연스러워야' 하며 조금이라도 어색하면 안 된다(그러면 정답이 2개가 됨).
- reason: 정답이 왜 문맥에 어긋나는지, 나머지는 왜 적절한지 한국어로 설명.
- override_no 는 0, override_text 는 빈 문자열로 두세요.

{ctx}
"""

_PROMPT_ORIGINAL = """아래 '정본 지문'으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 원문 단어]
지문을 새로 쓰지 말고, 밑줄 칠 단어와 표시할 단어만 정하세요.

- marks: 밑줄 5개. 각 항목은 sent_no(문장 번호 1-based), word(그 문장의 원본 단어),
  shown(문제에 보여줄 단어). '형용사·부사·동사' 위주로 고르세요.
- 정확히 1개(answer_no)는 shown 을 '반의어'로 하여 문맥상 어색하게 만듭니다 → 정답.
- 나머지 4개는 shown 을 'word 와 똑같이'(원문 단어 그대로) 둡니다. 유의어로 바꾸지 마세요.
- [확실성] 정답 1개만 확실히 어색해야 하고, 나머지 4개는 원문 그대로라 당연히 자연스럽습니다.
- reason: 정답이 왜 문맥에 어긋나는지 한국어로 설명.
- override_no 는 0, override_text 는 빈 문자열로 두세요.

{ctx}
"""

_PROMPT_NEGATION = """아래 '정본 지문'으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 부정어 삽입]
지문을 새로 쓰지 말고, 밑줄과 '정답 문장의 부정어 삽입'만 정하세요.

- marks: 밑줄 5개. sent_no·word·shown. 형용사·부사·동사 위주. 이 방식에서는
  shown 을 word 와 '똑같이'(원문 그대로) 둡니다.
- answer_no: 정답 밑줄 번호. override_no: 그 밑줄이 있는 문장 번호(1-based).
  override_text: 그 문장에 부정어(no/not/never/neither 등)를 자연스럽게 넣어 글 전체 흐름과
  '모순'되게 만든 문장. 단, 그 안에 정답 밑줄 단어(word)는 반드시 그대로 남겨 두세요.
- reason: 삽입된 부정어로 인해 그 문장이 글의 흐름과 어떻게 모순되는지 한국어로 설명.

{ctx}
"""


_PROMPTS = {SYNONYM: _PROMPT_SYNONYM, NEGATION: _PROMPT_NEGATION, ORIGINAL: _PROMPT_ORIGINAL}


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, method: str = SYNONYM) -> tuple[str, str]:
    prompt = _PROMPTS.get(method, _PROMPT_SYNONYM)
    out: VocabOut = client.structured(
        system=SYSTEM,
        prompt=prompt.format(ctx=context(analysis)),
        model_cls=VocabOut,
        max_tokens=2500,
        max_retries=max_retries,
    )
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    overrides = None
    if out.override_no and out.override_text.strip():
        overrides = {out.override_no - 1: out.override_text}
    return B.make_vocab(analysis.sentences, marks, out.answer_no, out.reason,
                        overrides=overrides)
