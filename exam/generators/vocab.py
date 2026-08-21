"""④ 어휘 생성기 (문맥상 부적절) — 정본에서 지정 단어만 변형. 세 방식 지원.

세 방식을 한 지문에서 모두 출제한다(pipeline.VOCAB_METHODS). 발문은 같지만 밑줄을
만드는 방식이 달라 서로 다른 문제가 된다:
  method="synonym"  : 밑줄 5개 중 1개=반의어(정답), 나머지=유의어로 패러프레이즈.
  method="original" : 정답 1개만 반의어, 나머지 4개는 '원문 단어 그대로' 노출.
  method="negation" : 밑줄은 원문 그대로, 정답 문장에만 부정어(no/not/neither)를 넣어
      글의 흐름과 모순되게 만든다(override_no/override_text).
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


def _avoid_clause(taken: set[str]) -> str:
    """이미 다른 어휘 문제가 밑줄로 쓴 낱말을 피하라는 지시문."""
    if not taken:
        return ""
    words = ", ".join(sorted(taken))
    return ("\n[겹침 금지] 같은 지문으로 어휘 문제를 여러 개 만드는 중입니다. 아래 낱말은 "
            "다른 문제에서 이미 밑줄로 썼으니 이번 문제에서는 '하나도 쓰지 마세요'. 다른 "
            f"낱말을 고르세요(품사가 달라도 됩니다).\n피할 낱말: {words}\n")


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, method: str = SYNONYM,
             avoid: set[str] | None = None) -> tuple[str, str, list[str]]:
    """avoid: 다른 어휘 문제가 이미 밑줄로 쓴 낱말(소문자). 겹치면 재요청한다."""
    prompt = _PROMPTS.get(method, _PROMPT_SYNONYM)
    taken = {w.lower() for w in (avoid or set())}

    def _extra(o: VocabOut) -> None:
        dup = sorted({m.word.lower() for m in o.marks} & taken)
        if dup:
            raise ValueError(
                f"다른 어휘 문제와 밑줄이 겹칩니다: {', '.join(dup)}. 겹치지 않는 낱말로 다시 고르세요.")

    out: VocabOut = client.structured(
        system=SYSTEM,
        prompt=prompt.format(ctx=context(analysis)) + _avoid_clause(taken),
        cache_prefix=context(analysis),
        model_cls=VocabOut,
        max_tokens=2500,
        max_retries=max_retries,
        extra_validate=_extra if taken else None,
    )
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    overrides = None
    if out.override_no and out.override_text.strip():
        overrides = {out.override_no - 1: out.override_text}
    flags: list[str] = []
    q, a = B.make_vocab(analysis.sentences, marks, out.answer_no, out.reason,
                        overrides=overrides, flags=flags)
    return q, a, flags, {m.word.lower() for m in out.marks}


def generate_group(client: ClaudeClient, analysis: Analysis, body: str,
                   methods: dict[str, str], max_retries: int = 1,
                   logger=None) -> dict[str, tuple[str, str, list[str]]]:
    """어휘 여러 문제를 '차례로' 만들어 밑줄이 겹치지 않게 한다.

    methods: {슬롯키: 방식}. 앞 문제가 쓴 낱말을 다음 문제에 '피할 낱말'로 넘긴다.
    한 슬롯이 실패해도 나머지는 살린다(그 슬롯만 빠지고 검토메모에 남는다).
    """
    used: set[str] = set()
    out: dict[str, tuple[str, str, list[str]]] = {}
    for slot, method in methods.items():
        try:
            q, a, flags, words = generate(client, analysis, body,
                                          max_retries=max_retries, method=method,
                                          avoid=used)
        except Exception as e:      # noqa: BLE001 — 슬롯 단위 격리
            if logger:
                logger.warning("[%s] 어휘 생성 실패: %s", slot, e)
            continue
        used |= words
        out[slot] = (q, a, flags)
    return out
