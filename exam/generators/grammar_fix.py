"""어법 서술형 생성기 — 틀린 밑줄 4개를 찾아 '번호 + 바르게 고친 형태'를 쓰게 한다.

개수를 세게 하던 문항(grammar_count)을 대신한다. 재료는 같다 — 밑줄 6개, 그중 틀린 것
4개. 다만 답을 고르는 대신 적게 한다. 그래서
  · 찍어서 맞힐 수 없고(개수형은 여섯 중 하나라 17%가 그냥 맞았다),
  · '무엇이 틀렸는지'뿐 아니라 '어떻게 고쳐야 하는지'까지 알아야 하며,
  · 채점할 때 네 자리에 부분 점수를 줄 수 있다.

고쳐야 할 형태는 따로 물을 필요가 없다. 이 유형은 '다시 쓴 지문' 위에 서므로,
다시 쓴 지문의 원래 낱말(word)이 곧 정답이고 보여 준 낱말(shown)이 틀린 형태다.

지문을 다시 쓰는 것은 이제 이 유형뿐이다. 5번 어법(틀린 것 모두 고르기)은 정본 지문
그대로 낸다. 덕분에 두 어법 문항이 서로 다른 지문 위에 서고, 같은 밑줄을 두 번 묻는
일이 구조적으로 일어나지 않는다.
"""
from __future__ import annotations

from .. import build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, GrammarCountOut
from .base import context


# 다시 쓰기 지침 — 이제 이 유형만 쓴다(5번 어법은 정본 그대로 낸다).
from .base import REWRITE_RULES  # noqa: F401 (여기서 쓰고, 어휘도 함께 쓴다)


_PROMPT = """아래 '정본 지문'으로 '어법 서술형' 문제를 만드세요.
발문은 '밑줄 친 부분 중 어법상 틀린 것 4개를 찾아, 번호를 쓰고 바르게 고쳐 쓰시오.' 입니다.
학생은 밑줄 여섯을 하나도 빠짐없이 따져 틀린 넷을 찾아내고, 각각을 바른 형태로 적습니다.

{rules}
[2단계 — 밑줄과 오류 심기] marks / wrong_nos / reasons
- marks: 밑줄 **정확히 6개**(①~⑥). 각 항목은 sent_no(1-based, **다시 쓴 지문 기준**),
  word(다시 쓴 지문에 실제로 있는 **바른** 낱말), shown(문제에 보여줄 형태). 읽는 순서대로.
- wrong_nos: 그중 어법상 '틀린' 밑줄 번호 — **정확히 4개**. 그 넷은 shown 을 틀린 형태로
  바꿉니다. 나머지 **2개**는 옳은 밑줄이므로 shown 을 word 와 똑같이 둡니다.
- 학생이 적을 정답은 'shown → word' 입니다. 그러니 word 는 그 자리에 넣었을 때 **그것
  하나만** 맞는 형태여야 합니다. 고칠 방법이 둘 이상인 자리(예: 시제를 과거로도 현재완료로도
  고칠 수 있는 자리)는 고르지 마세요 — 채점이 갈립니다.
- 고친 형태는 '낱말 한두 개'로 끝나야 합니다(문장을 통째로 다시 쓰게 하는 자리는 금지).
- 어느 4개를 틀리게 할지는 지문마다 달리하세요(늘 앞쪽 넷이면 자리만 보고 찍습니다).

[타깃 문법 — 아래 다섯 항목에서만 고르세요]
{points}
- **네 오류는 저마다 다른 항목이어야 합니다.** 한 항목을 되풀이하면 그것 하나를 아는
  학생이 나머지도 한꺼번에 찾아냅니다. 항목이 다섯이라 겹칠 이유가 없습니다.
- 이 다섯은 모두 '낱말 한두 개'로 고쳐지는 항목입니다 — 이 유형은 학생이 고친 형태를
  직접 적으므로 그래야 합니다. 어순을 되돌려야 하는 항목(도치·부정 등)은 문장을 통째로
  다시 쓰게 되므로 여기서는 쓰지 마세요. 그런 항목은 5번 어법이 맡습니다.

[근거] reasons 는 **밑줄 6개 전부**에 대해 하나씩 씁니다.
- 틀린 밑줄: 무엇이 왜 틀렸고 어떤 형태로 고쳐야 하는지.
- 옳은 밑줄: 왜 옳은지(어떤 규칙에 맞는지). 학생이 헷갈릴 만한 이유까지 짚어 주면 좋습니다.
- 각 항목에 point 를 함께 적으세요 — 위 목록의 이름을 '한 글자도 바꾸지 말고' 그대로.
reason: 전체 총평 한 줄(한국어).

[확실성]
- 틀린 밑줄은 '누가 봐도 확실히' 틀려야 합니다(문체 취향·미묘한 용법 차이는 안 됩니다).
- 옳은 밑줄 2개는 '완전히' 옳아야 합니다. 하나라도 어색하면 정답이 다섯이 됩니다.
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
        # 학생이 적을 답은 'shown → word' 다. 둘이 같으면 고칠 것이 없다.
        by_no = {i: m for i, m in enumerate(out.marks, 1)}
        same = [n for n in out.wrong_nos
                if n in by_no
                and by_no[n].shown.strip().lower() == by_no[n].word.strip().lower()]
        if same:
            raise ValueError(
                f"{', '.join(map(str, same))}번을 틀린 것으로 표시했는데 보여 준 낱말이 "
                "바른 낱말과 같습니다 — 학생이 고칠 것이 없습니다.")
        # 네 오류가 같은 문법 항목이면 하나만 알아도 넷이 다 보인다.
        flaw = shape.check_grammar_points(
            {r.no: shape.normalize_grammar_point(r.point) for r in out.reasons},
            out.wrong_nos)
        if flaw:
            raise ValueError("어법 서술형 설계 결함 — " + " ".join(flaw))

    out: GrammarCountOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(rules=REWRITE_RULES, ctx=context(analysis),
                              points="\n".join(f"  · {p}"
                                               for p in shape.GRAMMAR_POINTS_FIX)),
        cache_prefix=context(analysis),
        model_cls=GrammarCountOut,
        max_tokens=3500,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    sents = [s.strip() for s in out.rewritten]
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    reasons = {r.no: r.text for r in out.reasons}
    points = {r.no: shape.normalize_grammar_point(r.point) for r in out.reasons}
    flags: list[str] = []
    q, a = B.make_grammar_fix(sents, marks, out.wrong_nos, reasons,
                              note=(out.reason or "").strip(), flags=flags,
                              points=points)
    return q, a, flags
