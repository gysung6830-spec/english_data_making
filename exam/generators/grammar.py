"""⑤ 어법 생성기 (복수정답, 최대 8밑줄) — '다시 쓴 지문' 위에 낸다.

다른 유형과 달리 이 유형만 정본을 그대로 쓰지 않는다. 내신 대비 학습지는 학생이
지문을 통째로 외운 상태에서 푸는 일이 많은데, 정본 그대로 내면 어법을 몰라도
'원문과 달라진 낱말'을 찾아 답을 맞힌다 — 어법 지식이 아니라 암기력을 재게 된다.

그래서 내용은 같고 표현만 바꾼 지문을 새로 쓰게 한 뒤, 그 위에 밑줄을 친다.
다시 쓴 지문은 shape.check_rewrite 로 검사한다(문장 수 유지·실제로 달라졌는지·
원문과 같은 내용인지).
"""
from __future__ import annotations

from .. import build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, GrammarOut
from .base import context

# 다시 쓰기 지침 — 어법 계열 두 유형이 함께 쓴다.
REWRITE_RULES = """[1단계 — 지문 다시 쓰기] rewritten
이 문항의 지문은 원문 그대로가 아니라 '다시 쓴 것'을 씁니다. 학생이 지문을 외운 상태로
원문과 달라진 낱말만 찾아 푸는 것을 막기 위해서입니다.
  · 문장을 합치거나 나누지 말고 '원문과 같은 개수'로, 1:1 대응되게 다시 쓰세요.
  · 각 문장의 '내용·논리·순서'는 그대로 두고 표현만 바꿉니다. 사실을 더하거나 빼지 마세요.
  · 바꾸는 방법: 유의어 교체 / 능동↔수동 / 구를 절로(또는 그 반대) / 어순 조정 /
    분사구문↔접속사절 / 명사구↔that절 등.
  · 최소한 문장의 60% 이상은 원문과 글자 그대로 같지 않아야 합니다.
  · **다시 쓴 지문 자체는 어법상 완전히 옳아야 합니다.** 오류는 2단계에서만 넣습니다.
    다시 쓰다가 실수로 어색한 문장이 되면 밑줄이 아닌 곳에 오류가 생겨 문항이 무너집니다.
    문장을 완성한 뒤 주어-동사 수 일치, 시제, 관계사, 병렬을 스스로 한 번 더 확인하세요.
"""


_PROMPT = """아래 '정본 지문'으로 '어법(복수정답)' 문제를 만드세요.

{rules}
[2단계 — 밑줄과 오류 심기] marks / answer_nos / reasons
- marks: 밑줄 2~8개(①~⑧). 각 항목은 sent_no(1-based, **다시 쓴 지문 기준**),
  word(다시 쓴 지문에 실제로 있는 낱말), shown(문제에 보여줄 형태). 읽는 순서대로.
- 그중 '여러 개(2~4개)'는 shown 을 어법상 '틀린' 형태로 바꾸고(answer_nos), 나머지는
  shown 을 word 와 동일하게(옳게) 둡니다.
- 타깃 문법: 수 일치 / 시제 / 태 / 준동사 / 관계사 / 병렬 / 대명사.
- reasons: 틀린 각 번호가 왜 틀렸고 무엇으로 고쳐야 하는지 한국어로 설명.

[확실성] 정답으로 표시한 밑줄만 틀려야 하고, 나머지 밑줄과 밑줄 아닌 부분은 모두 어법상
옳아야 합니다. 밑줄 밖에 오류가 남아 있으면 정답이 여러 개가 되어 문항이 무너집니다.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    def _chk(out: GrammarOut) -> None:
        out.check()
        bad = shape.check_rewrite(out.rewritten, analysis.sentences)
        if bad:
            raise ValueError("어법 지문 다시 쓰기 실패 — " + " ".join(bad))

    out: GrammarOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(rules=REWRITE_RULES, ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=GrammarOut,
        max_tokens=3500,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    sents = [s.strip() for s in out.rewritten]
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    reasons = {r.no: r.text for r in out.reasons}
    flags: list[str] = []
    q, a = B.make_grammar(sents, marks, out.answer_nos, reasons, flags=flags)
    return q, a, flags
