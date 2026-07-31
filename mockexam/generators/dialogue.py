"""대화문·안내문 유형 생성기 (§3-C): dialogue_mismatch / notice_match."""
from __future__ import annotations

from .base import FACT_TWIST, build_choice, register


@register("dialogue_mismatch")
def gen_dialogue_mismatch(item, passage, an, ctx):
    # 대화문 지문이 없어 대체된 경우: 대화를 지어내지 말고 일반 내용불일치로 출제.
    if passage.format_type == "dialogue":
        stem = ctx.stem("dialogue_mismatch", "다음 대화의 내용과 일치하지 않는 것은?")
        src = "대화"
    else:
        stem = "다음 글의 내용과 일치하지 않는 것은?"
        src = "지문"
    instr = (f"{src} 세부 정보를 대조한다. 선지 5개 중 1개만 불일치(=정답). 정답 선지는 "
             f"{src} 내용에서 " + FACT_TWIST +
             f" 나머지 오답 4개는 {src}에 실제 언급된 사실을 정확히 반영해 소거가 어렵게 하라.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"진술 {i+1}" for i in range(5)])


@register("notice_match")
def gen_notice_match(item, passage, an, ctx):
    # '일치하는 것' 고르기: 정답=사실 정확 반영, 오답 4개=비틀기(불일치와 방향 반대).
    # 안내문 지문이 없어 대체된 경우: 안내문을 지어내지 말고 일반 내용일치로 출제.
    if passage.format_type == "notice":
        stem = ctx.stem("notice_match", "다음 안내문의 내용과 일치하는 것은?")
        src, keep = "안내문", "When&Where/Highlights/Notes 구획을 유지. "
    else:
        stem = "다음 글의 내용과 일치하는 것은?"
        src, keep = "지문", ""
    instr = (f"{keep}선지 5개 중 1개만 {src}과 정확히 일치(=정답)하고, 정답 선지는 {src} "
             f"사실을 그대로 반영하라. 나머지 오답 4개는 {src} 내용을 " + FACT_TWIST)
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"진술 {i+1}" for i in range(5)])
