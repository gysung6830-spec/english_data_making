"""독해 유형 생성기 (§3-C): main_point/title/blank_single/order/
irrelevant_sentence/implied_meaning/inference_mismatch/summary_ab."""
from __future__ import annotations

from ..core.models import Item, Passage
from .base import (
    DISTRACTOR_RULE, FACT_TWIST, LABELS, STEM_FALLBACK, GenContext,
    PassageAnalysis, build_choice, make_choices, register,
)


@register("insert")
def gen_insert(item, passage, an, ctx):
    """문장 삽입 — 내부 문장 하나를 빼내 '주어진 문장'으로, 나머지에 ①~⑤ 위치."""
    stem = ctx.stem("insert", STEM_FALLBACK["insert"])
    instr = (
        "지문의 '중간' 문장 하나(첫 문장·끝 문장 제외)를 빼내 '주어진 문장'으로 삼고, 남은 "
        "지문의 문장 사이 다섯 곳에 ①~⑤ 위치를 표시한다. 정답은 그 문장이 원래 있던 자리. "
        "그 자리에만 자연스럽게 들어가도록 연결사(however·therefore·for example 등)·지시어"
        "(this·that·such·these)·정관사·대명사 같은 위치 단서를 '2개 이상' 두어 정답 위치가 "
        "유일하게 확정되게 하고, 다른 자리에 넣으면 지시 대상이나 논리 연결이 어긋나게 하라. "
        "출력 지문은 맨 앞에 '[주어진 문장] ...'을 두고, 본문에는 위치마다 ①~⑤ 를 넣어라. "
        "선지는 ①~⑤ 번호만."
    )
    sents = an.sentences or [passage.text]
    gi = 2 if len(sents) > 3 else (len(sents) // 2 if sents else 0)
    given = sents[gi] if sents else "(주어진 문장)"
    rest = [s for j, s in enumerate(sents) if j != gi] or [passage.text]
    kept = rest[:4]                       # 문장 4개 → 사이·양끝 위치 5개(①~⑤)
    parts: list[str] = []
    for i, s in enumerate(kept):
        parts.append(LABELS[i])           # 문장 앞 위치
        parts.append(s)
    parts.append(LABELS[min(len(kept), 4)])   # 마지막 문장 뒤 위치
    body = " ".join(parts)
    mock_p = f"[주어진 문장] {given}\n{body}"
    return build_choice(item, passage, ctx, stem, instr, mock_answer="③",
                        number_only=True, mock_passage=mock_p)


@register("main_point")
def gen_main_point(item, passage, an, ctx):
    stem = ctx.stem("main_point", "다음 글의 요지로 가장 적절한 것은?")
    instr = DISTRACTOR_RULE + " 요지 선지는 **한국어**로 작성하라."
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"요지 후보 {i+1}" for i in range(5)])


@register("title")
def gen_title(item, passage, an, ctx):
    stem = ctx.stem("title", "다음 글의 제목으로 가장 적절한 것은?")
    instr = DISTRACTOR_RULE + " 제목 선지는 **영어**로 작성하라."
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"Title Candidate {i+1}" for i in range(5)])


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
                        mock_choices=[f"빈칸 후보 {i+1}" for i in range(5)])


@register("order")
def gen_order(item, passage, an, ctx):
    stem = ctx.stem("order", "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?")
    instr = ("도입문을 고정하고 (A)(B)(C)를 재배열하는 유형. 지문은 반드시 도입문 뒤에 "
             "'(A)', '(B)', '(C)'로 시작하는 세 문단을 넣어 구성하라. 정답 순서가 '단 "
             "하나'로만 확정되도록, 각 문단에 연결사(however·for example·in addition 등)·지시어"
             "(this·that·such)·정관사(the)·대명사가 '이어질 특정 문단'을 가리키는 결속 "
             "단서를 '2개 이상' 심어라. 한 단서만 무시하면 다른 순서도 그럴듯해 보이되, "
             "모든 단서를 종합하면 정답 순서는 오직 하나뿐이게 하라. 오답 순서는 단서 하나를 "
             "무시했을 때만 성립하도록 배치하라.")
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
    instr = (DISTRACTOR_RULE + " 단, 지문에서 재해석할 표현(구/절) '한 곳'을 반드시 "
             "<u>...</u>로 감싸고, 그 밑줄 표현은 문맥 전체로 재해석해야 답이 나오게 하라"
             "(직역으로는 못 풀게). '무관·모순' 오답은 그 표현을 표면적/축자적으로 읽은 "
             "오독으로 구성하라. 선지는 **영어**로 작성하라.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"implied reading {i+1}" for i in range(5)])


@register("inference_mismatch")
def gen_inference_mismatch(item, passage, an, ctx):
    stem = ctx.stem("inference_mismatch", "다음 글의 내용과 일치하지 않는 것은?")
    instr = ("선지 5개 중 1개만 지문과 불일치(=정답). 정답 선지는 지문 내용에서 " + FACT_TWIST +
             " 나머지 오답 4개는 지문에 실제 언급된 사실을 정확히 반영해 소거가 어렵게 하라.")
    return build_choice(item, passage, ctx, stem, instr,
                        mock_choices=[f"진술 {i+1}" for i in range(5)])


@register("summary_ab")
def gen_summary_ab(item, passage, an, ctx):
    stem = ctx.stem("summary_ab",
                    "다음 글의 내용을 한 문장으로 요약하고자 한다. "
                    "빈칸 (A), (B)에 들어갈 말로 가장 적절한 것은?")
    instr = ("지문을 한 문장으로 요약하되 핵심 두 축을 (A)(B) 빈칸으로 비운다. 각 칸에 "
             "유의어 함정을 배치하고, 5개 선지는 (A)(B) 조합으로 구성하라. 어느 한 칸만 "
             "봐서는 답이 결정되지 않도록 선지들이 두 칸에서 서로 갈리게 배치하고, (A)(B) "
             "두 칸을 '모두' 정확히 판단해야 정답 1개로 좁혀지게 하라(한 칸만 맞혀도 답이 "
             "나오면 안 됨). 각 선지는 반드시 '(A) 낱말 - (B) 낱말' 형식으로 작성. "
             "지문 뒤에 '[요약문]'으로 시작하는 한 문장 요약문을 (A)__, (B)__ 빈칸과 함께 넣어라.")
    mock_choices = [f"(A) word{i} - (B) word{i}b" for i in range(1, 6)]
    return build_choice(item, passage, ctx, stem, instr, mock_choices=mock_choices)
