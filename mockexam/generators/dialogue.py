"""대화문·안내문 유형 생성기 (§3-C): dialogue_mismatch / notice_match."""
from __future__ import annotations

from .base import build_choice, register


@register("dialogue_mismatch")
def gen_dialogue_mismatch(item, passage, an, ctx):
    stem = ctx.stem("dialogue_mismatch",
                    "다음 대화의 내용과 일치하지 않는 것은?")
    instr = ("대화문 세부 정보 대조. 선지 5개 중 1개만 불일치, "
             "오답은 대화에 실제 언급된 사실을 정확히 반영해 소거가 어렵게.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 대화 진술 {i+1}" for i in range(5)])


@register("notice_match")
def gen_notice_match(item, passage, an, ctx):
    stem = ctx.stem("notice_match", "다음 안내문의 내용과 일치하는 것은?")
    instr = ("When&Where/Highlights/Notes 구획을 유지. 숫자·시간·조건을 살짝 비튼 "
             "선지를 함정으로. 5개 중 1개만 일치.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 안내 진술 {i+1}" for i in range(5)])
