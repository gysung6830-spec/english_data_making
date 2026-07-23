"""대화문·안내문 유형 생성기 (§3-C): dialogue_mismatch / notice_match."""
from __future__ import annotations

from .base import FACT_TWIST, build_choice, register


@register("dialogue_mismatch")
def gen_dialogue_mismatch(item, passage, an, ctx):
    stem = ctx.stem("dialogue_mismatch",
                    "다음 대화의 내용과 일치하지 않는 것은?")
    instr = ("대화문 세부 정보 대조. 선지 5개 중 1개만 불일치(=정답). 정답 선지는 대화 "
             "내용에서 " + FACT_TWIST +
             " 나머지 오답 4개는 대화에 실제 언급된 사실을 정확히 반영해 소거가 어렵게 하라.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 대화 진술 {i+1}" for i in range(5)])


@register("notice_match")
def gen_notice_match(item, passage, an, ctx):
    stem = ctx.stem("notice_match", "다음 안내문의 내용과 일치하는 것은?")
    # '일치하는 것' 고르기이므로 정답=사실 정확 반영, 오답 4개=비틀기(불일치와 방향 반대).
    instr = ("When&Where/Highlights/Notes 구획을 유지. 선지 5개 중 1개만 안내문과 정확히 "
             "일치(=정답)하고, 정답 선지는 안내문 사실을 그대로 반영하라. 나머지 오답 4개는 "
             "안내문 내용을 " + FACT_TWIST)
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 안내 진술 {i+1}" for i in range(5)])
