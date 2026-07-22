"""독해 유형 생성기 (§3-C): main_point/title/blank_single/order/
irrelevant_sentence/implied_meaning/inference_mismatch/summary_ab."""
from __future__ import annotations

from ..core.models import Item, Passage
from .base import (
    DISTRACTOR_RULE, GenContext, PassageAnalysis, build_choice, make_choices,
    register,
)


@register("main_point")
def gen_main_point(item, passage, an, ctx):
    stem = ctx.stem("main_point", "다음 글의 요지로 가장 적절한 것은?")
    instr = DISTRACTOR_RULE + " 요지 선지는 **한국어**로 작성하라."
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 요지 후보 {i+1}" for i in range(5)])


@register("title")
def gen_title(item, passage, an, ctx):
    stem = ctx.stem("title", "다음 글의 제목으로 가장 적절한 것은?")
    instr = DISTRACTOR_RULE + " 제목 선지는 **영어**로 작성하라."
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) Title Candidate {i+1}" for i in range(5)])


@register("blank_single")
def gen_blank(item, passage, an, ctx):
    stem = ctx.stem("blank_single", "다음 빈칸에 들어갈 말로 가장 적절한 것은?")
    instr = (DISTRACTOR_RULE + " 이 유형은 지문의 핵심 결론부를 '____'로 비우고 그 자리에 "
             "들어갈 말을 5지선다로 고르게 한다. 따라서 '정답'은 빈칸에 들어갈 올바른 말"
             "(지문 논지를 유의어로 표현), '오답 4개'는 위 원리대로 2개는 주제와 무관·"
             "2개는 주제와 모순되게(지문 단어 활용) 구성하라. 지문의 핵심 결론부는 반드시 "
             "'____'로 표시하라. 선지는 지문 언어(영어)로 작성하라.")
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
             "어휘가 겹쳐 관련 있어 보이나 흐름엔 기여하지 않게. "
             "지문의 각 문장 앞에 ①~⑤ 표시를 붙여라(선지는 번호만).")
    return build_choice(item, passage, ctx, stem, instr, mock_answer="③",
                        number_only=True)


@register("implied_meaning")
def gen_implied(item, passage, an, ctx):
    stem = ctx.stem("implied_meaning",
                    "밑줄 친 부분이 다음 글에서 의미하는 바로 가장 적절한 것은?")
    instr = (DISTRACTOR_RULE + " 단, 밑줄 표현은 문맥 전체로 재해석해야 답이 나오게 하고"
             "(직역으로는 못 풀게), '무관·모순' 오답은 표현을 표면적/축자적으로 읽은 "
             "오독으로 구성하라. 선지는 **영어**로 작성하라.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) implied reading {i+1}" for i in range(5)])


@register("inference_mismatch")
def gen_inference_mismatch(item, passage, an, ctx):
    stem = ctx.stem("inference_mismatch", "다음 글의 내용과 일치하지 않는 것은?")
    instr = ("선지 5개 중 1개만 지문과 불일치(=정답). 정답 선지는 지문 내용에서 "
             "'주체(누가/무엇이 했는지)·인과(원인↔결과)·부정↔긍정' 중 하나를 비틀어 "
             "만들어라 — 예: 행위의 주체를 다른 대상으로 바꾸기, 원인과 결과를 뒤집기, "
             "긍정 진술을 부정으로(또는 부정을 긍정으로) 뒤집기. "
             "나머지 오답 4개는 지문에 실제 언급된 사실을 정확히 반영해 소거가 어렵게 하라.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"(mock) 진술 {i+1}" for i in range(5)])


@register("summary_ab")
def gen_summary_ab(item, passage, an, ctx):
    stem = ctx.stem("summary_ab",
                    "다음 글의 내용을 한 문장으로 요약하고자 한다. "
                    "빈칸 (A), (B)에 들어갈 말로 가장 적절한 것은?")
    instr = ("요약문 한 문장에 (A)(B) 두 개념 빈칸. 각 칸에 유의어 함정을 배치해 "
             "지문 논지의 두 축을 정확히 짚어야 조합이 맞게. "
             "각 선지는 반드시 '(A) 낱말 - (B) 낱말' 형식으로 작성. "
             "지문 뒤에 '[요약문]'으로 시작하는 한 문장 요약문을 (A)__, (B)__ 빈칸과 함께 넣어라.")
    mock_choices = [f"(A) word{i} - (B) word{i}b" for i in range(1, 6)]
    return build_choice(item, passage, ctx, stem, instr, mock_choices=mock_choices)
