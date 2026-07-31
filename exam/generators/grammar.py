"""⑤ 어법 생성기 (복수정답, 최대 8밑줄) — 정본에서 지정 단어만 오답형으로."""
from __future__ import annotations

from .. import build as B
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, GrammarOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '어법(복수정답)' 문제를 만드세요.
지문을 새로 쓰지 말고, 밑줄 칠 단어와 표시할 형태만 정하세요.

- marks: 밑줄 2~8개(①~⑧). 각 항목은 sent_no(1-based), word(원본 단어),
  shown(문제에 보여줄 형태). '읽는 순서대로' 나열하세요.
- 그중 '여러 개(2~4개)'는 shown 을 어법상 '틀린' 형태로 바꾸고(answer_nos), 나머지는
  shown 을 원본과 동일하게(옳게) 둡니다.
- 타깃 문법: 수 일치 / 시제 / 태 / 준동사 / 관계사 / 병렬 / 대명사.
- reasons: 틀린 각 번호가 왜 틀렸고 무엇으로 고쳐야 하는지 한국어로 설명.

{ctx}
"""


def _extra_validate(out: GrammarOut) -> None:
    out.check()


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    out: GrammarOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=GrammarOut,
        max_tokens=3000,
        max_retries=max_retries,
        extra_validate=_extra_validate,
    )
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    reasons = {r.no: r.text for r in out.reasons}
    q, a = B.make_grammar(analysis.sentences, marks, out.answer_nos, reasons)
    return q, a, []
