"""어법 유형 생성기 (§3-C): grammar / grammar_vocab_mix.

정답 유일성이 중요하므로 client 있을 때 LLM 로 오류 위치를 확정하고,
오프라인에선 밑줄 5개를 구조적으로 표시한 mock 을 만든다.
"""
from __future__ import annotations

from .base import GenContext, build_choice, register

_GRAMMAR_STEM = "다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?"


def _grammar_instr(item, ctx) -> str:
    """어법 유형 공통 출제원리: 5곳 밑줄 중 정확히 1곳만 규칙 위반, 나머지는 완전히 맞음."""
    focus = ", ".join(ctx.profile.get("grammar_focus", []) or ["관계사", "태", "분사"])
    return (f"문법 요소가 걸린 {item.underlines or 5}곳을 밑줄. 정확히 1곳만 규칙 위반, "
            f"나머지는 완전히 정답이며 각기 다른 문법 포인트. 이 학교는 {focus}를 자주 출제. "
            "밑줄 위치는 '고쳐야 할 것 같지만 실제로는 맞는' 표현에 두어 함정.")


@register("grammar")
def gen_grammar(item, passage, an, ctx):
    stem = ctx.stem("grammar", _GRAMMAR_STEM)
    return build_choice(item, passage, ctx, stem, _grammar_instr(item, ctx),
                        mock_answer="③", number_only=True)


@register("grammar_vocab_mix")
def gen_grammar_vocab_mix(item, passage, an, ctx):
    # 사용자 확정: 이 유형도 '어법' 유형과 동일하게 순수 어법 오류 1곳 찾기로 출제.
    stem = ctx.stem("grammar_vocab_mix", _GRAMMAR_STEM)
    return build_choice(item, passage, ctx, stem, _grammar_instr(item, ctx),
                        mock_answer="②", number_only=True)


@register("grammar_multi")
def gen_grammar_multi(item, passage, an, ctx):
    """어법 복수정답 — 밑줄 5곳 중 2~3곳을 어법상 틀리게(모두 고르기)."""
    focus = ", ".join(ctx.profile.get("grammar_focus", []) or ["관계사", "태", "분사"])
    stem = ctx.stem("grammar_multi", "다음 글의 밑줄 친 부분 중, 어법상 틀린 것을 모두 고르시오.")
    instr = (f"문법 요소가 걸린 5곳을 읽는 순서로 밑줄(①~⑤)로 표시하라. 그중 '정확히 2~3곳'을 "
             f"어법상 틀린 형태로 만들고(각기 다른 문법 포인트: 수일치·시제·태·준동사·관계사·병렬·"
             f"대명사 중), 나머지는 완전히 맞게 하라. 이 학교는 {focus}를 자주 출제. answer_indices "
             "에 틀린 밑줄 번호를 모두 넣어라(2~4개). explanation 에는 틀린 각 밑줄이 왜 틀렸고 "
             "어떻게 고치는지, 맞는 밑줄은 왜 맞는지 밝혀라.")
    return build_choice(item, passage, ctx, stem, instr, mock_answer="② ④",
                        number_only=True)


@register("pair_odd")
def gen_pair_odd(item, passage, an, ctx):
    """어법·어휘 짝짓기 — 밑줄 5곳 중 정확히 2곳(1 어법+1 어휘)만 부적절, 선지는 짝."""
    stem = ctx.stem("pair_odd", "다음 글의 밑줄 친 부분 중, 어법상 또는 문맥상 쓰임이 "
                    "적절하지 않은 것끼리 짝지어진 것은?")
    instr = ("문법·어휘 요소가 걸린 5곳을 ①~⑤ 밑줄로 표시하라. 그중 '정확히 2곳'만 부적절하게 "
             "하되 하나는 '어법 오류', 다른 하나는 '문맥상 어색한 반의어'로 만들고, 나머지 3곳은 "
             "완전히 자연스럽게 하라(부적절 2곳이 유일하게 확정되도록). 5개 선지는 두 밑줄의 짝을 "
             "'①-③' 같은 형식으로 구성하고, 정답은 부적절한 두 밑줄의 짝이다. explanation 에 두 "
             "오류의 근거와 나머지 3곳이 왜 맞는지 밝혀라.")
    mock_choices = ["①-②", "①-④", "②-④", "③-⑤", "②-⑤"]
    return build_choice(item, passage, ctx, stem, instr, mock_choices=mock_choices,
                        mock_answer="②")


@register("grammar_fix_and_answer")
def gen_grammar_fix_and_answer(item, passage, an, ctx):
    # 서술형이지만 어법 계열이라 여기서 등록.
    from .base import ESSAY_UNIQUE, build_essay
    stem = ctx.stem("grammar_fix_and_answer",
                    "밑줄 친 부분 중 어법상 틀린 3곳을 찾아 바르게 고치고, "
                    "본문에 근거하여 영어 질문에 영어로 답하시오.")
    instr = ("밑줄 3곳을 수일치·시제·태·관계사 등 '명백한 어법 오류'로 만들어 고친 정답이 "
             "각각 하나로 확정되게 하라. 이어 Why/How 등 영어 질문에 본문 근거로 영어 문장 "
             "답을 쓰되, 본문 표현을 활용해 모범답안 1개로 채점 가능하게 하라. '본문에 사용된 "
             "단어만' 조건을 붙일 수 있음. " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)
