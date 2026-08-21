"""어법 개수 생성기 — '어법상 틀린 것의 개수는?' (수능 29번 계열의 내신 변형).

어느 것이 틀렸는지 고르게 하는 대신 몇 개가 틀렸는지 세게 한다. 학생은 밑줄 하나하나를
빠짐없이 따져야 하고, 하나만 잘못 봐도 개수가 어긋나 답이 틀린다. 찍어서 맞히기 어렵고
어법 지식을 훨씬 촘촘히 확인한다.

어법 계열이므로 지문은 '다시 쓴 것'을 쓴다(generators/grammar.py 머리말 참고).
같은 지문의 어법 문항 두 개가 서로 다른 지문 위에 서게 되는데, 이는 의도된 것이다 —
두 문항이 같은 밑줄을 다시 묻는 일을 막아 준다.

밑줄은 6개, 틀린 것은 늘 4개로 고정한다(정답은 ④). 개수를 매번 다르게 하면 지문마다
난이도가 들쭉날쭉해지고, LLM 이 2~3개로 몰리기도 한다. 개수를 고정하는 대신 **어느 4개가
틀렸는지**를 지문마다 달리해, 학생이 밑줄 여섯을 전부 판정하게 만든다.
"""
from __future__ import annotations

from .. import build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, GrammarCountOut
from .base import context
from .grammar import REWRITE_RULES

_PROMPT = """아래 '정본 지문'으로 '어법상 틀린 것의 개수' 문제를 만드세요.
발문은 '밑줄 친 부분 중, 어법상 틀린 것의 개수는?'이고 선지는 ①1개 ②2개 ③3개 ④4개 ⑤5개 ⑥6개
입니다. 학생은 밑줄 여섯을 하나도 빠짐없이 따져 '몇 개가 틀렸는지'를 셉니다.

{rules}
[2단계 — 밑줄과 오류 심기] marks / wrong_nos / reasons
- marks: 밑줄 **정확히 6개**(①~⑥). 각 항목은 sent_no(1-based, **다시 쓴 지문 기준**),
  word(다시 쓴 지문에 실제로 있는 낱말), shown(문제에 보여줄 형태). 읽는 순서대로 나열하세요.
- wrong_nos: 그중 어법상 '틀린' 밑줄 번호 — **정확히 4개**. shown 을 틀린 형태로 바꿉니다.
  나머지 **2개**는 옳은 밑줄이므로 shown 을 word 와 똑같이 둡니다.
- 어느 4개를 틀리게 할지는 지문마다 달리하세요(늘 앞쪽 넷이면 자리만 보고 셉니다).
  틀린 것과 옳은 것을 번갈아 놓아 흩어 두는 편이 좋습니다.
- 타깃 문법: 수 일치 / 시제 / 태 / 준동사 / 관계사 / 병렬 / 대명사 / 비교.
  네 오류가 서로 다른 문법 항목이면 더 좋습니다(한 항목만 반복하면 하나 알면 넷이 보입니다).

[근거] reasons 는 **밑줄 6개 전부**에 대해 하나씩 씁니다.
- 틀린 밑줄: 무엇이 왜 틀렸고 어떤 형태로 고쳐야 하는지.
- 옳은 밑줄: 왜 옳은지(어떤 규칙에 맞는지). 학생이 헷갈릴 만한 이유까지 짚어 주면 좋습니다.
reason: 전체 총평 한 줄(한국어).

[확실성] 이 유형은 '개수'가 정답이므로 밑줄 하나만 잘못 판정해도 정답이 틀립니다.
- 틀린 밑줄은 '누가 봐도 확실히' 틀려야 합니다(문체 취향·미묘한 용법 차이는 안 됩니다).
- 옳은 밑줄 2개는 '완전히' 옳아야 합니다. 하나라도 어색하면 개수가 5개가 되어 버립니다.
  학생이 헷갈릴 만한 자리(관계절 안의 동사, 병렬 구조, 준동사)를 골라 두면 좋습니다.
- 밑줄 밖의 본문에도 오류가 없어야 합니다.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    def _chk(out: GrammarCountOut) -> None:
        out.check()
        bad = shape.check_rewrite(out.rewritten, analysis.sentences)
        if bad:
            raise ValueError("어법 지문 다시 쓰기 실패 — " + " ".join(bad))

    out: GrammarCountOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(rules=REWRITE_RULES, ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=GrammarCountOut,
        max_tokens=3500,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    sents = [s.strip() for s in out.rewritten]
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    reasons = {r.no: r.text for r in out.reasons}
    flags: list[str] = []
    q, a = B.make_grammar_count(sents, marks, out.wrong_nos, reasons,
                                note=(out.reason or "").strip(), flags=flags)
    return q, a, flags
