"""⑤ 어법 생성기 (복수정답, 최대 8밑줄) — '정본 지문 그대로' 위에 낸다.

지문을 손대지 않고 밑줄 칠 낱말과 보여 줄 형태만 정한다. 어휘·짝짓기와 같은 지문
위에 서므로, 학생은 한 지문을 여러 각도로 다시 읽게 된다.

같은 지문에 밑줄 문항이 다섯이 되므로(어법 · 짝짓기 · 어휘 3종) 밑줄이 겹치기 쉽다.
그래서 이 유형이 밑줄 묶음의 '첫 문항'으로 먼저 만들어지고(고를 수 있는 낱말이 가장
좁다 — 문법이 걸린 자리여야 한다), 쓴 낱말을 뒤 문항들에 '피할 낱말'로 넘긴다.

암기 대비는 6번 어법 서술형이 맡는다 — 그쪽은 '다시 쓴 지문' 위에 선다.
"""
from __future__ import annotations

from .. import build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, GrammarOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '어법(복수정답)' 문제를 만드세요.
발문은 '밑줄 친 부분 중, 어법상 틀린 것을 모두 고르시오.' 입니다.
**지문은 원문 그대로 쓰입니다. 지문을 다시 쓰지 마세요.** 당신은 밑줄 칠 낱말과 문제에
보여 줄 형태만 정합니다.

[밑줄과 오류 심기] marks / answer_nos / reasons
- marks: 밑줄 2~8개(①~⑧). 각 항목은 sent_no(1-based, **정본 지문 기준**),
  word(정본 지문에 실제로 있는 낱말), shown(문제에 보여줄 형태). 읽는 순서대로 나열하세요.
- 그중 '여러 개(2~4개)'는 shown 을 어법상 '틀린' 형태로 바꾸고(answer_nos), 나머지는
  shown 을 word 와 똑같이(옳게) 둡니다.
- word 는 지문에 있는 그대로여야 합니다(철자·대소문자 포함). 지문에 없는 낱말을 적으면
  밑줄을 칠 자리를 찾지 못해 문항이 만들어지지 않습니다.
- 틀린 밑줄과 옳은 밑줄을 번갈아 놓아 흩어 두세요(앞쪽에 몰리면 자리만 보고 찍습니다).
- reasons: 틀린 각 번호가 왜 틀렸고 무엇으로 고쳐야 하는지 한국어로 설명.
  각 항목에 point 를 함께 적으세요 — 아래 목록의 이름을 '한 글자도 바꾸지 말고' 그대로.

[타깃 문법 — 아래 여섯 항목에서만 고르세요]
{points}
- **틀린 밑줄은 저마다 다른 항목이어야 합니다.** 한 항목을 되풀이하면 그것 하나를 아는
  학생이 나머지도 한꺼번에 찾아냅니다. 항목이 여섯이라 겹칠 이유가 없습니다.
- 이 여섯은 '판정'만으로 풀리는 항목입니다(어순·구조가 걸린 것도 됩니다). 낱말 하나만
  바꿔 고치는 항목(감정분사·재귀대명사·부사vs형용사 등)은 어법 서술형이 맡으므로
  여기서는 쓰지 마세요 — 두 어법 문항이 같은 것을 두 번 묻게 됩니다.

[확실성] 정답으로 표시한 밑줄만 틀려야 하고, 나머지 밑줄은 모두 어법상 옳아야 합니다.
옳은 밑줄은 '학생이 헷갈릴 만한 자리'(관계절 안의 동사·병렬 구조·준동사)로 고르되,
실제로는 완전히 옳아야 합니다. 하나라도 어긋나면 정답 개수가 달라져 문항이 무너집니다.

{ctx}
"""


def _points_block() -> str:
    """5번 어법이 고를 수 있는 문법 항목 목록(shape 가 원본이다)."""
    return "\n".join(f"  · {p}" for p in shape.GRAMMAR_POINTS_JUDGE)


def _avoid_clause(taken: set[str]) -> str:
    """이미 다른 밑줄 문항이 쓴 낱말을 피하라는 지시문."""
    if not taken:
        return ""
    return ("\n[겹침 금지] 같은 지문에 밑줄 문항이 여럿입니다. 아래 낱말은 다른 문항이 "
            "이미 밑줄로 썼으니 이번에는 하나도 쓰지 마세요.\n"
            f"피할 낱말: {', '.join(sorted(taken))}\n")


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, avoid: set[str] | None = None,
             with_words: bool = False):
    """avoid: 같은 지문의 다른 밑줄 문항이 이미 쓴 낱말(겹치면 재요청).
    with_words=True 면 (q, a, flags, 이 문항이 쓴 낱말들)을 돌려준다(밑줄 묶음용)."""
    from .vocab import _mark_words

    taken = {w.lower() for w in (avoid or set())}

    def _chk(out: GrammarOut) -> None:
        out.check()
        dup = sorted(_mark_words(out.marks) & taken)
        if dup:
            raise ValueError(f"다른 밑줄 문항과 낱말이 겹칩니다: {', '.join(dup)}. "
                             "겹치지 않는 낱말로 다시 고르세요.")
        # 틀린 밑줄이 같은 문법 항목을 되풀이하면 하나만 알아도 나머지가 다 보인다.
        bad = shape.check_grammar_points(
            {r.no: shape.normalize_grammar_point(r.point) for r in out.reasons},
            out.answer_nos)
        if bad:
            raise ValueError("어법 문항 설계 결함 — " + " ".join(bad))

    out: GrammarOut = client.structured(
        system=SYSTEM,
        prompt=(_PROMPT.format(ctx=context(analysis), points=_points_block())
                + _avoid_clause(taken)),
        cache_prefix=context(analysis),
        model_cls=GrammarOut,
        max_tokens=3000,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    reasons = {r.no: r.text for r in out.reasons}
    # 표기 흔들림은 표의 이름으로 되돌린다. 표에 없는 이름은 알약을 달지 않는다
    # (이름표 하나 때문에 문항을 다시 만들지는 않는다 — shape.normalize_grammar_point).
    points = {r.no: shape.normalize_grammar_point(r.point) for r in out.reasons}
    flags: list[str] = []
    q, a = B.make_grammar(analysis.sentences, marks, out.answer_nos, reasons,
                          flags=flags, points=points)
    if with_words:
        return q, a, flags, _mark_words(out.marks)
    return q, a, flags
