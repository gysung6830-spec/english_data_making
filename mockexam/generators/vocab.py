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
    return build_choice(item, passage, ctx, stem, instr, mock_answer="④", number_only=True)


@register("vocab_3blank_abc")
def gen_vocab_3blank(item, passage, an, ctx):
    stem = ctx.stem("vocab_3blank_abc",
                    "(A), (B), (C)의 각 네모 안에서 문맥에 맞는 낱말로 "
                    "가장 적절한 것끼리 짝지은 것은?")
    instr = ("지문 안 낱말 선택 지점 세 곳을 '(A)', '(B)', '(C)'로 표시하고, 각 지점에 "
             "[정답낱말 / 유의어 함정낱말] 두 낱말을 함께 제시하라. 5개 선지는 '(A)낱말 - "
             "(B)낱말 - (C)낱말' 형식의 세 칸 조합으로 구성하라. 각 칸은 문맥으로만 가려지는 "
             "유의어 함정을 두고, 어느 한 칸만 봐서는 정답이 결정되지 않도록 선지들이 각 칸에서 "
             "서로 갈리게 배치하며, (A)(B)(C) 세 칸을 '모두' 정확히 판단해야 정답 1개로 "
             "좁혀지게 하라(한 칸만 맞혀도 답이 나오면 안 됨).")
    mock_choices = ["(A)-(B)-(C)", "(A)-(B')-(C)", "(A')-(B)-(C)",
                    "(A)-(B)-(C')", "(A')-(B')-(C')"]
    return build_choice(item, passage, ctx, stem, instr, mock_choices=mock_choices,
                        mock_answer="①")
