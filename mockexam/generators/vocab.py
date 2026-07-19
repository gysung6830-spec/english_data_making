"""어휘 유형 생성기 (§3-C): vocab_odd / vocab_3blank_abc."""
from __future__ import annotations

from .base import build_choice, register


@register("vocab_odd")
def gen_vocab_odd(item, passage, an, ctx):
    stem = ctx.stem("vocab_odd",
                    "다음 글의 밑줄 친 부분 중, 문맥상 낱말의 쓰임이 적절하지 않은 것은?")
    instr = (f"{item.underlines or 5}개 밑줄 중 정답은 반의어/오용어로 심고, "
             "나머지는 원문 단어를 유의어로 바꿔 기억으로 못 맞히게 해 순수 문맥 판단을 강제. "
             "난이도 상이면 연어(collocation) 오류로.")
    return build_choice(item, passage, ctx, stem, instr, mock_answer="④")


@register("vocab_3blank_abc")
def gen_vocab_3blank(item, passage, an, ctx):
    stem = ctx.stem("vocab_3blank_abc",
                    "(A), (B), (C)의 각 네모 안에서 문맥에 맞는 낱말로 "
                    "가장 적절한 것끼리 짝지은 것은?")
    instr = ("각 칸마다 정답 1 + 유의어 함정 1을 두고 5지선다 조합. "
             "세 칸을 다 판단해야 답이 하나로 좁혀지게 배치.")
    mock_choices = ["(A)-(B)-(C)", "(A)-(B')-(C)", "(A')-(B)-(C)",
                    "(A)-(B)-(C')", "(A')-(B')-(C')"]
    return build_choice(item, passage, ctx, stem, instr, mock_choices=mock_choices,
                        mock_answer="①")
