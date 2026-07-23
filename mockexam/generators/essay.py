"""서술형 유형 생성기 (§3-C 서술형).

grammar_fix_and_answer 는 어법 계열이라 grammar.py 에 등록. 나머지 8종을 여기서.
"""
from __future__ import annotations

from .base import ESSAY_ARRANGE_UNIQUE, ESSAY_UNIQUE, build_essay, register


@register("prep_find_and_translate")
def gen_prep(item, passage, an, ctx):
    stem = ctx.stem("prep_find_and_translate",
                    "빈칸에 공통으로 들어갈 전치사를 쓰고, 밑줄 친 문장을 우리말로 해석하시오.")
    instr = ("같은 전치사 1개가 두 빈칸에 '공통으로만' 들어가도록, 각 빈칸을 그 전치사만 쓰는 "
             "연어·구동사 문맥으로 설계하라(다른 전치사로는 성립하지 않게). 밑줄 문장 해석은 "
             "구문(주어·수식어) 파악을 보고 직역 기준 모범답안 1개로. " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)


@register("dialogue_arrange_inflect")
def gen_dialogue_arrange(item, passage, an, ctx):
    stem = ctx.stem("dialogue_arrange_inflect",
                    "[보기]의 단어를 모두 활용하여(어형 변형 가능) 영작하고, "
                    "본문에 근거해 우리말로 답하시오.")
    instr = ("보기 단어를 '전부' 활용해 빈칸을 영작하게 하라. " + ESSAY_ARRANGE_UNIQUE +
             " 변형해야 할 동사는 원형으로만 제시해 학생이 시제·수일치·태·품사를 스스로 "
             "변형하도록(어형변형 평가). " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)


@register("condition_write_inflect")
def gen_condition_write(item, passage, an, ctx):
    stem = ctx.stem("condition_write_inflect",
                    ctx.profile.get("stem_style", {}).get("essay_condition",
                    "괄호 속 단어를 어형 변형하여 빈칸을 채우고, 본문 단어만으로 영어로 답하시오."))
    instr = ("괄호 속 원형 단어를 문맥상 '한 가지 어형'으로만 맞게 변형해 빈칸을 채우게 하라"
             "(다른 어형은 성립하지 않게). '본문에 사용된 단어만으로 영어로 답할 것' 조건을 "
             "명시. 난이도 상이면 보기·정답을 본문 등장 단어만으로 구성. " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)


@register("summary_fill_from_text")
def gen_summary_fill(item, passage, an, ctx):
    stem = ctx.stem("summary_fill_from_text",
                    "다음 요약문의 빈칸을 본문에 있는 단어로 채우시오.(변형 금지)")
    instr = ("요약문 각 빈칸의 정답이 '본문에 실제 등장하는 핵심어 1개'로만 확정되게 하라"
             "(유의어로 대체 불가하도록 그 개념을 지목). '본문에 있는 단어 그대로, 변형 금지' "
             "조건을 명시. " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)


@register("word_arrange")
def gen_word_arrange(item, passage, an, ctx):
    stem = ctx.stem("word_arrange", "[보기]의 단어를 알맞게 배열하여 빈칸을 완성하시오.")
    instr = ("보기 단어를 알맞게 배열해 빈칸을 완성하게 하라. " + ESSAY_ARRANGE_UNIQUE +
             " 정답 구문에 관계사절·부정사 등 구조를 넣어 어순 판단이 핵심이 되게 하라. "
             + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)


@register("arrange_and_translate")
def gen_arrange_translate(item, passage, an, ctx):
    stem = ctx.stem("arrange_and_translate",
                    "[보기]의 단어를 모두 활용하여(필요시 단어·어구 추가) 밑줄 친 우리말을 "
                    "영작하고, 본문 내용을 우리말로 답하시오.")
    instr = ("(1) 보기 단어를 모두 활용해 밑줄 우리말을 영작하되, 추가 허용 단어는 '관사·"
             "전치사 등 기능어'로만 한정하라. " + ESSAY_ARRANGE_UNIQUE +
             " (2) 본문 내용을 우리말로 답(본문 근거로 모범답안 1개, 1점 소문항). " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)


@register("chart_fix_and_arrange")
def gen_chart_fix(item, passage, an, ctx):
    stem = ctx.stem("chart_fix_and_arrange",
                    "도표와 일치하지 않는 부분 1곳을 찾아 고치고, 우리말에 맞게 [보기]를 "
                    "배열하여 영작하시오.")
    # 도표 지문이 아닌(수치 없는) 지문이 배정될 수 있으므로 조건부·날조 금지로 처리.
    instr = ("도표(수치) 대조 + 배열영작 유형이다. "
             "① 지문에 수치·통계 등 도표로 만들 데이터가 있으면, 지문 맨 앞에 '[도표]'로 "
             "시작하는 간단한 텍스트 표(항목: 수치)를 '실제 데이터'로 만들고, 밑줄 친 ①~④ "
             "서술 중 '정확히 1곳'만 그 표와 어긋나게(나머지 ①~④는 표와 정확히 일치) 하라. "
             "어긋난 곳의 수정 정답은 표 수치로 하나로 확정. "
             "② 지문에 도표로 만들 수치 데이터가 없으면 표를 '지어내지 말고'(수치 날조 금지), "
             "대신 본문 서술과 '사실이 어긋난' 밑줄 ①~④ 중 1곳을 만들어 '본문 내용과 일치하지 "
             "않는 부분을 찾아 바르게 고치기'로 출제하라(나머지 ①~④는 본문과 일치). "
             "이어 배열영작으로 표현력을 평가하라. " + ESSAY_ARRANGE_UNIQUE + " " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)


@register("blank_choose_no_change")
def gen_blank_choose(item, passage, an, ctx):
    stem = ctx.stem("blank_choose_no_change",
                    "[보기]에서 골라 각 빈칸을 채우시오.(변형 금지, 빈칸당 한 단어)")
    instr = ("각 빈칸에 들어갈 보기 단어가 '문맥상 하나로만' 확정되게 하라(함정 단어는 품사는 "
             "비슷하되 의미상 확실히 부적합). 보기 개수 = 빈칸 수 + 함정 2~3개. '변형 금지·"
             "빈칸당 한 단어' 조건을 명시. " + ESSAY_UNIQUE)
    return build_essay(item, passage, ctx, stem, instr)
