"""서술형 유형 생성기 (§3-C 서술형).

grammar_fix_and_answer 는 어법 계열이라 grammar.py 에 등록. 나머지 8종을 여기서.
"""
from __future__ import annotations

from .base import build_essay, register


@register("prep_find_and_translate")
def gen_prep(item, passage, an, ctx):
    stem = ctx.stem("prep_find_and_translate",
                    "빈칸에 공통으로 들어갈 전치사를 쓰고, 밑줄 친 문장을 우리말로 해석하시오.")
    instr = ("같은 전치사가 들어갈 두 빈칸을 만들어 문법 감각을 평가. "
             "해석은 구문(주어·수식어) 파악을 본다.")
    return build_essay(item, passage, ctx, stem, instr)


@register("dialogue_arrange_inflect")
def gen_dialogue_arrange(item, passage, an, ctx):
    stem = ctx.stem("dialogue_arrange_inflect",
                    "[보기]의 단어를 모두 활용하여(어형 변형 가능) 영작하고, "
                    "본문에 근거해 우리말로 답하시오.")
    instr = ("보기 단어를 전부 써야 하므로 어순 설계력을 평가. 동사는 원형으로 제시해 "
             "학생이 시제·수일치·태·품사를 스스로 변형(어형변형 평가).")
    return build_essay(item, passage, ctx, stem, instr)


@register("condition_write_inflect")
def gen_condition_write(item, passage, an, ctx):
    stem = ctx.stem("condition_write_inflect",
                    ctx.profile.get("stem_style", {}).get("essay_condition",
                    "괄호 속 단어를 어형 변형하여 빈칸을 채우고, 본문 단어만으로 영어로 답하시오."))
    instr = ("괄호 단어를 어형변형해 채우게 하고, 본문에 사용된 단어만으로 영어 답. "
             "난이도 상이면 보기·정답을 본문 등장 단어만으로 구성.")
    return build_essay(item, passage, ctx, stem, instr)


@register("summary_fill_from_text")
def gen_summary_fill(item, passage, an, ctx):
    stem = ctx.stem("summary_fill_from_text",
                    "다음 요약문의 빈칸을 본문에 있는 단어로 채우시오.(변형 금지)")
    instr = ("'본문에 실제 나온 단어, 변형 금지'로 제약해 정확한 어휘 회수와 요지 파악을 "
             "동시에 평가.")
    return build_essay(item, passage, ctx, stem, instr)


@register("word_arrange")
def gen_word_arrange(item, passage, an, ctx):
    stem = ctx.stem("word_arrange", "[보기]의 단어를 알맞게 배열하여 빈칸을 완성하시오.")
    instr = ("보기 단어를 배열해 빈칸 완성. 정답 구문에 관계사절·부정사 등 구조가 들어가 "
             "어순 판단이 핵심.")
    return build_essay(item, passage, ctx, stem, instr)


@register("arrange_and_translate")
def gen_arrange_translate(item, passage, an, ctx):
    stem = ctx.stem("arrange_and_translate",
                    "[보기]의 단어를 모두 활용하여(필요시 단어·어구 추가) 밑줄 친 우리말을 "
                    "영작하고, 본문 내용을 우리말로 답하시오.")
    instr = ("(1) 보기 단어를 모두 활용해 밑줄 우리말 영작(필요 시 단어·어구 추가 허용) "
             "(2) 본문 내용을 우리말로 답(1점 소문항).")
    return build_essay(item, passage, ctx, stem, instr)


@register("chart_fix_and_arrange")
def gen_chart_fix(item, passage, an, ctx):
    stem = ctx.stem("chart_fix_and_arrange",
                    "도표와 일치하지 않는 부분 1곳을 찾아 고치고, 우리말에 맞게 [보기]를 "
                    "배열하여 영작하시오.")
    instr = ("도표 수치와 지문 서술을 대조해 틀린 1곳을 찾아 고치게 함(정보 대조력). "
             "이어 배열 영작으로 표현력 평가. "
             "실제 그래프 이미지는 넣을 수 없으므로, 지문 맨 앞에 '[도표]'로 시작하는 "
             "간단한 텍스트 표(항목: 수치 형태)를 만들어 포함하고, 밑줄 친 ①~④ 서술 중 "
             "하나가 그 표와 어긋나게 하라.")
    return build_essay(item, passage, ctx, stem, instr)


@register("blank_choose_no_change")
def gen_blank_choose(item, passage, an, ctx):
    stem = ctx.stem("blank_choose_no_change",
                    "[보기]에서 골라 각 빈칸을 채우시오.(변형 금지, 빈칸당 한 단어)")
    instr = ("보기에 정답보다 많은 단어(함정)를 넣어 어휘 변별을 평가. 변형 금지·빈칸당 한 단어. "
             "정답과 품사·의미가 비슷한 유인어를 섞는다.")
    return build_essay(item, passage, ctx, stem, instr)
