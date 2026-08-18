"""어휘 유형 생성기 (§3-C): vocab_odd / vocab_3blank_abc."""
from __future__ import annotations

from .base import build_choice, register


# 어휘 유형의 난이도 연동 방식(부정어 삽입 대신 반의어/연어로 — 발문과 정합).
_VOCAB_METHOD = {
    "low": "정답 밑줄 1개만 문맥상 어색한 '반의어'로 만들고, 나머지 밑줄 4개는 원문 단어를 "
           "그대로 둔다(암기로도 일부 풀리되 문맥 판단을 학습하게).",
    "mid": "정답 밑줄 1개는 문맥상 어색한 '반의어'로, 나머지 4개는 원문 단어를 유의어로 "
           "패러프레이즈해 기억이 아니라 순수 문맥 판단으로만 가려지게 한다.",
    "mid_high": "정답 밑줄 1개는 미묘한 '반의어' 또는 문맥에 맞지 않는 '연어(collocation) 오류'로, "
                "나머지 4개는 원문을 유의어로 바꿔 정밀한 문맥 판단이 필요하게 한다.",
    "high": "정답 밑줄 1개는 아주 미묘한 '반의어'나 '연어(collocation) 오류'로 만들어 정밀 독해 "
            "없이는 못 가리게 하고, 나머지 4개는 원문을 유의어로 바꾼다.",
}


@register("vocab_odd")
def gen_vocab_odd(item, passage, an, ctx):
    stem = ctx.stem("vocab_odd",
                    "다음 글의 밑줄 친 부분 중, 문맥상 낱말의 쓰임이 적절하지 않은 것은?")
    method = _VOCAB_METHOD.get(ctx.difficulty, _VOCAB_METHOD["mid"])
    instr = (f"{item.underlines or 5}개 밑줄 중 정답은 '정확히 1개'만 문맥상 어색하게 하고 나머지는 "
             f"완전히 자연스럽게 하라(정답 2개 방지). 난이도별 방식: {method} "
             "각 밑줄이 왜 자연스러운지/왜 어색한지 해설에 밝혀라.")
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
