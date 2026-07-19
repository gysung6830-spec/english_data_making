"""어법 유형 생성기 (§3-C): grammar / grammar_vocab_mix.

정답 유일성이 중요하므로 client 있을 때 LLM 로 오류 위치를 확정하고,
오프라인에선 밑줄 5개를 구조적으로 표시한 mock 을 만든다.
"""
from __future__ import annotations

from .base import GenContext, build_choice, register


@register("grammar")
def gen_grammar(item, passage, an, ctx):
    stem = ctx.stem("grammar", "다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?")
    focus = ", ".join(ctx.profile.get("grammar_focus", []) or ["관계사", "태", "분사"])
    instr = (f"문법 요소가 걸린 {item.underlines or 5}곳을 밑줄. 정확히 1곳만 규칙 위반, "
             f"나머지는 완전히 정답이며 각기 다른 문법 포인트. 이 학교는 {focus}를 자주 출제. "
             "밑줄 위치는 '고쳐야 할 것 같지만 실제로는 맞는' 표현에 두어 함정.")
    return build_choice(item, passage, ctx, stem, instr, mock_answer="③")


@register("grammar_vocab_mix")
def gen_grammar_vocab_mix(item, passage, an, ctx):
    stem = ctx.stem("grammar_vocab_mix",
                    "다음 글의 밑줄 친 부분 중, 어법 또는 문맥상 낱말의 쓰임이 "
                    "적절하지 않은 것은?")
    instr = (f"{item.underlines or 5}개 밑줄에 어법 표현과 어휘를 혼합. "
             "정답은 '문맥상 낱말 쓰임'이 어긋난 1개.")
    return build_choice(item, passage, ctx, stem, instr, mock_answer="②")


@register("grammar_fix_and_answer")
def gen_grammar_fix_and_answer(item, passage, an, ctx):
    # 서술형이지만 어법 계열이라 여기서 등록.
    from .base import build_essay
    stem = ctx.stem("grammar_fix_and_answer",
                    "밑줄 친 부분 중 어법상 틀린 3곳을 찾아 바르게 고치고, "
                    "본문에 근거하여 영어 질문에 영어로 답하시오.")
    instr = ("밑줄 3곳의 어법 오류를 고쳐 쓰게 하고(생산적 어법력), "
             "Why/How 등 영어 질문에 본문 근거로 영어 문장 답. "
             "'본문에 사용된 단어만' 조건을 붙일 수 있음.")
    return build_essay(item, passage, ctx, stem, instr)
