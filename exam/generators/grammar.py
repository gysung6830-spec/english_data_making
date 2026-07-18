"""⑤ 어법 생성기 (복수정답, 최대 8밑줄)."""
from __future__ import annotations

from .. import format as F
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, GrammarOut
from .base import context

_PROMPT = """아래 분석을 바탕으로 '어법(복수정답)' 문제를 만드세요.

- 본문에 밑줄/네모를 최대 8개(words) 표시합니다(①~⑧).
- 그 중 '여러 개(2~4개)'를 어법상 틀리게 바꾸고(answer_nos), 나머지는 옳게 둡니다.
- 타깃 문법: 수 일치 / 시제 / 태 / 준동사 / 관계사 / 병렬 / 대명사.
- chunks 는 밑줄 단어를 뺀 본문 조각으로, 길이는 words+1 이어야 합니다.
- reasons: 틀린 각 번호가 왜 틀렸고 무엇으로 고쳐야 하는지 한국어로 설명.
- 발문은 '어법상 틀린 것을 모두 고르시오'이므로 반드시 복수 정답이 되게 하세요.

{ctx}
"""


def _extra_validate(out: GrammarOut) -> None:
    out.check()


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str]:
    out: GrammarOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        model_cls=GrammarOut,
        max_tokens=3500,
        max_retries=max_retries,
        extra_validate=_extra_validate,
    )
    markers = [F.underline(i, w) for i, w in enumerate(out.words, 1)]
    marked = F.weave(out.chunks, markers)
    q = F.grammar_q(marked)
    reasons = {r.no: r.text for r in out.reasons}
    a = F.grammar_a(out.answer_nos, reasons)
    return q, a
