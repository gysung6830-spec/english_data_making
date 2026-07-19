"""독해 유형 생성기 (§3-C): main_point/title/blank_single/order/
irrelevant_sentence/implied_meaning/inference_mismatch/summary_ab."""
from __future__ import annotations

from ..core.models import Item, Passage
from .base import (
    GenContext, PassageAnalysis, build_choice, make_choices, register,
)


@register("main_point")
def gen_main_point(item, passage, an, ctx):
    stem = ctx.stem("main_point", "다음 글의 요지로 가장 적절한 것은?")
    instr = ("전체 요지를 핵심어의 유의어/상위어로 표현(원단어 그대로 X). "
             "오답 5개 중 2개는 지문 실단어를 섞은 함정, 2개는 주제를 벗어난 무관 선지. "
             "요지 선지는 **한국어**로.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 요지 후보 {i+1}" for i in range(5)])


@register("title")
def gen_title(item, passage, an, ctx):
    stem = ctx.stem("title", "다음 글의 제목으로 가장 적절한 것은?")
    instr = ("제목을 핵심어의 유의어/상위어로 표현. 오답에 지문 실단어를 섞은 함정. "
             "제목 선지는 **영어**로.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) Title Candidate {i+1}" for i in range(5)])


@register("blank_single")
def gen_blank(item, passage, an, ctx):
    stem = ctx.stem("blank_single", "다음 빈칸에 들어갈 말로 가장 적절한 것은?")
    instr = ("지문의 핵심 결론부를 빈칸 처리. 오답은 (a)부분일치 (b)정반대 "
             "(c)과잉일반화 (d)지엽적 사실 4종 함정.")
    mock_p = passage.text
    if an.sentences:
        mock_p = passage.text.replace(an.sentences[-1], "____________ (빈칸)")
    return build_choice(item, passage, ctx, stem, instr, mock_passage=mock_p,
                        mock_choices=[f"(mock) 빈칸 후보 {i+1}" for i in range(5)])


@register("order")
def gen_order(item, passage, an, ctx):
    stem = ctx.stem("order", "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?")
    instr = ("도입문을 고정하고 (A)(B)(C)를 재배열. 연결사·지시어·정관사·대명사가 "
             "정답 순서를 하나로만 확정하게. 오답은 단서 하나를 무시했을 때 그럴듯하게.")
    mock_choices = ["(A) - (C) - (B)", "(B) - (A) - (C)", "(B) - (C) - (A)",
                    "(C) - (A) - (B)", "(C) - (B) - (A)"]
    # 도입문 박스 + (A)(B)(C) 구조로 디자인 미리보기
    intro = an.sentences[0] if an.sentences else passage.text[:120]
    a = an.sentences[1] if len(an.sentences) > 1 else "(A) ..."
    b = an.sentences[2] if len(an.sentences) > 2 else "(B) ..."
    c = an.sentences[3] if len(an.sentences) > 3 else "(C) ..."
    mock_p = f"{intro}\n(A) {a}\n(B) {b}\n(C) {c}"
    return build_choice(item, passage, ctx, stem, instr, mock_choices=mock_choices,
                        mock_answer="④", mock_passage=mock_p)


@register("irrelevant_sentence")
def gen_irrelevant(item, passage, an, ctx):
    stem = ctx.stem("irrelevant_sentence", "다음 글에서 전체 흐름과 관계 없는 문장은?")
    instr = ("같은 소재를 쓰되 논지 방향이 살짝 어긋난 문장 1개를 ①~⑤ 중 한 자리에 삽입. "
             "어휘가 겹쳐 관련 있어 보이나 흐름엔 기여하지 않게.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 문장 {L}" for L in "①②③④⑤"])


@register("implied_meaning")
def gen_implied(item, passage, an, ctx):
    stem = ctx.stem("implied_meaning",
                    "밑줄 친 부분이 다음 글에서 의미하는 바로 가장 적절한 것은?")
    instr = ("밑줄 표현을 문맥 전체로 재해석해야 답이 나오게(직역으로는 못 풀게). "
             "오답은 표현을 표면적/축자적으로 읽은 오독 4종. 선지는 영어.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) implied reading {i+1}" for i in range(5)])


@register("inference_mismatch")
def gen_inference_mismatch(item, passage, an, ctx):
    stem = ctx.stem("inference_mismatch", "다음 글의 내용과 일치하지 않는 것은?")
    instr = ("선지 5개 중 1개만 지문과 불일치. 오답은 지문에 실제 언급된 사실을 정확히 반영해 "
             "소거가 어렵게.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 진술 {i+1}" for i in range(5)])


@register("summary_ab")
def gen_summary_ab(item, passage, an, ctx):
    stem = ctx.stem("summary_ab",
                    "다음 글의 내용을 한 문장으로 요약하고자 한다. "
                    "빈칸 (A), (B)에 들어갈 말로 가장 적절한 것은?")
    instr = ("요약문 한 문장에 (A)(B) 두 개념 빈칸. 각 칸에 유의어 함정을 배치해 "
             "지문 논지의 두 축을 정확히 짚어야 조합이 맞게.")
    mock_choices = [f"(A) word{i} … (B) word{i}b" for i in range(1, 6)]
    return build_choice(item, passage, ctx, stem, instr, mock_choices=mock_choices)
