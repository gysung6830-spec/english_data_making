"""문항 생성 공통 기반 (§4 BaseGenerator 패턴).

- PassageAnalysis: 지문을 1회 분석해 유형별 generate 가 재사용.
- GenContext: 프로파일(stem_style·grammar_focus)·난이도·LLM 클라이언트를 담는다.
- REGISTRY: type → builder. 각 카테고리 파일(reading/grammar/vocab/dialogue/essay)이 등록.
- ctx.client 가 없으면(오프라인/미학습) 구조적으로 유효한 mock 문항을 만든다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from ..core.models import (
    Choice, Difficulty, Item, MockExam, Passage, Question,
)

LABELS = ["①", "②", "③", "④", "⑤"]
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


@dataclass
class PassageAnalysis:
    """지문 1회 분석 결과(유형별로 공유)."""

    passage: Passage
    sentences: list[str]
    words: list[str]
    key_words: list[str] = field(default_factory=list)

    @classmethod
    def of(cls, p: Passage) -> "PassageAnalysis":
        sents = [s.strip() for s in _SENT_SPLIT.split(p.text.strip()) if s.strip()]
        words = _WORD.findall(p.text)
        # 핵심어: 길이 5+ 이면서 대문자 아닌 내용어 상위 빈도
        from collections import Counter
        common = Counter(w.lower() for w in words if len(w) >= 5)
        key = [w for w, _ in common.most_common(8)]
        return cls(passage=p, sentences=sents, words=words, key_words=key)


@dataclass
class GenContext:
    profile: dict[str, Any]
    difficulty: Difficulty = "mid"
    client: Any = None          # ClaudeClient 또는 None(오프라인)
    grammar_focus: list[str] = field(default_factory=list)
    max_workers: int = 8        # LLM 병렬 호출 수(속도↑, 과도하면 rate limit)
    variant: int = 0            # N회분: 같은 지문으로 회차별 다른 문항 (0=단일)

    def stem(self, item_type: str, fallback: str) -> str:
        style = self.profile.get("stem_style", {}) or {}
        return style.get(item_type) or fallback


# 서술형 중 <보기> 단어상자가 반드시 있어야 하는 유형 / 영작(우리말) 유형
_ESSAY_BOGI = {"dialogue_arrange_inflect", "word_arrange",
               "arrange_and_translate", "blank_choose_no_change", "chart_fix_and_arrange"}
_ESSAY_KO = {"dialogue_arrange_inflect", "arrange_and_translate"}

# 의미 이해형(선지가 문장) 선지 구성 원리 — 정답 유일성을 '구조적으로' 보장한다.
#   정답  : 지문 핵심을 유의어로 패러프레이즈(지문 단어 복붙 금지)
#   오답4 : 2개=주제와 무관 / 2개=주제와 모순 (넷 다 지문에 나온 단어를 활용해 그럴듯하게)
DISTRACTOR_RULE = (
    "[선지 구성(오답 출제) 원리] 정답 선지는 지문의 핵심 논지를 '유의어로 바꿔' 표현하라"
    "(지문 단어를 그대로 베끼지 말 것). 나머지 오답 4개는 반드시 2개는 '주제와 무관'하게, "
    "2개는 '주제와 정반대로 모순'되게 만들되, 오답 4개 모두 지문에 실제 등장한 단어를 활용해 "
    "그럴듯하게 보이도록 하라. 그 결과 정답은 오직 1개만 성립하고 오답 4개는 확실히 틀리게 하라."
)
# 위 원리(정답=유의어 패러프레이즈)를 적용하는 유형(모두 '가장 적절한 것' 고르기형)
_PARAPHRASE_TYPES = {"main_point", "title", "implied_meaning", "blank_single"}

# 사실확인형(일치/불일치)에서 '비튼(틀린)' 진술을 만드는 기법 — 복수정답 방지.
#   한 진술에 '한 가지만' 비틀어 명확히 오답이 되게 한다.
FACT_TWIST = (
    "'주체(누가/무엇이 했는지)·인과(원인↔결과)·부정↔긍정·수치/시점' 중 '하나만' 비틀어 "
    "만들어라(예: 행위 주체를 다른 대상으로 바꾸기, 원인과 결과를 뒤집기, 긍정을 부정으로"
    "(또는 부정을 긍정으로), 숫자·시점 바꾸기). 한 진술에 한 가지만 비틀어 확실한 오답이 되게 하라."
)

# 서술형 공통 — 채점 가능한 '유일 정답'을 강제한다(복수정답·채점모호 방지).
ESSAY_UNIQUE = (
    "정답은 채점 가능한 '모범답안 1개'로 확정하고, 무엇을 맞혀야 정답인지(채점 조건)를 "
    "conditions 에 구체적으로 명시하라."
)
# 배열영작 계열 — 가능한 정답 어순이 하나뿐이 되게 한다.
ESSAY_ARRANGE_UNIQUE = (
    "보기 단어로 문법적으로 성립하는 배열이 '정확히 1개'가 되도록 구조(관계사절·부정사·"
    "전치사구 등)로 어순을 고정하고, 출력 전에 다른 배열도 가능한지 스스로 검증하라."
)


def _variant_hint(ctx: GenContext) -> str:
    """N회분에서 '같은 지문·다른 문항'을 만들기 위한 회차 변형 지시(회차>0일 때만)."""
    if not ctx.variant:
        return ""
    return (f"\n[회차 변형 — {ctx.variant}회차] 같은 지문으로 만드는 여러 회차 중 이 회차용이다. "
            "다른 회차와 겹치지 않도록 '묻는 지점'을 달리하라: 빈칸·밑줄 위치, 초점(핵심) 문장, "
            "선지 구성과 오답 함정을 새로 짜고 표현도 바꿔라. (지문·유형·출제원리는 그대로 유지)")


def _flag_reason(item: Item, out: Any) -> str:
    """해설지 '⚠ 확인 권장' 배지 사유. 없으면 빈 문자열.

    (1) 모델 자가확신도가 '주의'거나, (2) 유의어 패러프레이즈 유형인데 정답 선지가
    지문 문장과 거의 동일(원리 위반)하면 사람이 한 번 더 볼 것을 권한다.
    """
    conf = (getattr(out, "answer_confidence", "") or "").strip()
    if conf and not conf.startswith("확실"):
        return "정답이 유일한지 재확인 권장"
    if item.type in _PARAPHRASE_TYPES:
        try:
            correct = (out.choices[out.answer_index - 1] or "").strip()
        except Exception:  # noqa: BLE001
            correct = ""
        core = re.sub(r"[^A-Za-z가-힣 ]", "", correct).strip().lower()
        if len(core) >= 12 and core in (out.passage or "").lower():
            return "정답 선지가 지문 문장과 유사 (재확인 권장)"
    return ""

Builder = Callable[[Item, Passage, PassageAnalysis, GenContext], Question]
REGISTRY: dict[str, Builder] = {}


def register(*types: str):
    def deco(fn: Builder) -> Builder:
        for t in types:
            REGISTRY[t] = fn
        return fn
    return deco


# ---------------------------------------------------------------------------
# mock 헬퍼: 구조적으로 유효한 5지선다/서술형을 만든다
# ---------------------------------------------------------------------------
def make_choices(texts: list[str]) -> list[Choice]:
    return [Choice(LABELS[i], t) for i, t in enumerate(texts[:5])]


_CIRCLED_NUM = re.compile(r"\s*[①-⑳㉑-㉟]\s*")


def strip_passage_numbering(text: str) -> str:
    """지문 문장에 붙은 ①②③ 번호를 제거(내용일치·요지·제목 등은 지문에 번호가 없어야 함)."""
    return re.sub(r"\s{2,}", " ", _CIRCLED_NUM.sub(" ", text or "")).strip()


def number_sentences(text: str, n: int = 5) -> str:
    """앞쪽 n개 문장 앞에 ①~⑤ 번호를 붙인다(무관문장 유형의 미리보기용)."""
    sents = [s for s in _SENT_SPLIT.split(text.strip()) if s.strip()]
    out = []
    for i, s in enumerate(sents):
        out.append(f"{LABELS[i]} {s}" if i < min(n, len(LABELS)) else s)
    return " ".join(out)


def underline_passage(text: str, n: int) -> str:
    """앞쪽 단어 n개를 ①~⑤ 밑줄 마커로 감싼 지문 텍스트를 만든다(구조 검증용)."""
    words = text.split()
    marks = 0
    out: list[str] = []
    for w in words:
        if marks < n and len(w) >= 4 and w.isalpha():
            out.append(f"{LABELS[marks]}<u>{w}</u>")
            marks += 1
        else:
            out.append(w)
    # 부족하면 뒤에서 채운다
    while marks < n:
        out.append(f"{LABELS[marks]}<u>____</u>")
        marks += 1
    return " ".join(out)


def _validate_choice_out(item: Item, out: Any) -> None:
    """생성 직후(같은 호출 안에서) 구조·정답을 자가검증 → 실패 시 자동 재작성.

    별도 검수 패스 없이도 '밑줄/빈칸 누락·정답 개수 이상'을 생성 단계에서 잡는다.
    """
    from ..verify.verifier import structural_issue  # 지연 임포트(순환 방지)
    tmp = Question(no=item.no, section="choice", type=item.type, score=item.score,
                   stem="", passage_id="", difficulty="mid",
                   underlines=item.underlines, passage_text=out.passage,
                   choices=make_choices(out.choices))
    issue = structural_issue(tmp)
    if issue:
        raise ValueError(f"지문 구조 오류: {issue}")


def _validate_essay_out(item: Item, out: Any) -> None:
    """서술형 생성 직후 자가검증(<보기>·우리말·정답·구조 누락)."""
    from ..verify.verifier import structural_issue  # 지연 임포트
    if item.type in _ESSAY_BOGI and not out.bogi:
        raise ValueError("<보기> 단어 상자(bogi)가 비어 있습니다. 유형상 반드시 채워야 합니다.")
    if item.type in _ESSAY_KO and not (out.blank_ko or "").strip():
        raise ValueError("영작할 우리말(blank_ko)이 비어 있습니다.")
    if not out.answers:
        raise ValueError("정답(answers)이 비어 있습니다.")
    tmp = Question(no=item.no, section="essay", type=item.type, score=item.score,
                   stem="", passage_id="", difficulty="mid", passage_text=out.passage)
    issue = structural_issue(tmp)
    if issue:
        raise ValueError(f"지문 구조 오류: {issue}")


def build_choice(item: Item, passage: Passage, ctx: GenContext,
                 stem: str, instruction: str,
                 mock_choices: list[str] | None = None,
                 mock_answer: str = "③",
                 mock_passage: str | None = None,
                 number_only: bool = False) -> Question:
    """객관식 1문항. client 있으면 LLM, 없으면 mock 구조 문항.

    instruction: 이 유형의 출제원리(§3-C)를 담은 지시문(LLM 프롬프트에 주입).
    number_only: 어법·무관문장처럼 선지를 ①~⑤ 번호만 주는 유형.
    """
    q = Question(no=item.no, section="choice", type=item.type, score=item.score,
                 stem=stem, passage_id=passage.id, difficulty=ctx.difficulty,
                 underlines=item.underlines)
    if number_only:
        q.meta["number_only"] = True
    if ctx.client is not None:
        from ..core.llm import ChoiceQuestionOut, system_prompt
        from ..core.models import DIFFICULTY_KO_REV
        ul = (f"\n지문의 밑줄은 정확히 {item.underlines}개를 ①<u>..</u>~ 형식으로 표시하라."
              if item.underlines else "")
        # 무관문장·어법·어휘가 아니면 지문 문장에 ①②③ 번호를 붙이지 않는다(표준 형식).
        nonum = ("" if number_only else
                 "\n지문 문장 앞에 ①②③ 같은 번호를 붙이지 마라(이 유형은 지문에 번호가 없다).")
        prompt = (f"[지문]\n{passage.text}\n\n[유형 출제원리]\n{instruction}{ul}{nonum}"
                  f"{_variant_hint(ctx)}\n\n"
                  f"[발문]\n{stem}\n\n위 지문으로 이 유형의 5지선다 1문항을 만들어라.\n"
                  "[정답 유일성 자가검증] 출력 전에 스스로 다섯 선지를 하나씩 대입해 "
                  "정답이 '오직 1개'만 성립하는지 확인하라. 두 개 이상 정답이 될 여지가 "
                  "있으면 오답 선지를 확실히 틀리도록 고쳐서 유일 정답이 되게 하라.\n"
                  "explanation 에는 정답 근거뿐 아니라 오답 ①~⑤ 각각이 왜 틀렸는지와 "
                  "핵심 문법·어휘·논지 포인트까지 자세히 써라.")
        sysp = system_prompt(ctx.profile, DIFFICULTY_KO_REV.get(ctx.difficulty, "중"))
        out = ctx.client.structured(sysp, prompt, ChoiceQuestionOut, max_retries=2,
                                    extra_validate=lambda o: _validate_choice_out(item, o))
        # 번호 선지 유형이 아니면 지문에 새어든 ①②③ 문장 번호를 제거(안전망).
        q.passage_text = out.passage if number_only else strip_passage_numbering(out.passage)
        q.choices = make_choices(out.choices)
        q.answer = LABELS[out.answer_index - 1]
        q.explanation = out.explanation
        flag = _flag_reason(item, out)
        if flag:
            q.meta["review_flag"] = flag
    else:
        q.choices = make_choices(mock_choices or [f"선택지 {i+1}" for i in range(5)])
        q.answer = mock_answer
        q.explanation = ""
        if mock_passage is not None:
            q.passage_text = mock_passage
        elif item.underlines:                       # 어법·어휘: 밑줄 ①~⑤
            q.passage_text = underline_passage(passage.text, item.underlines)
        elif number_only:                           # 무관문장: 문장 앞 ①~⑤
            q.passage_text = number_sentences(passage.text)
        else:
            q.passage_text = passage.text
    if number_only:
        # 선지는 지문의 ①~⑤(밑줄/문장 위치)에서 고르므로 번호만 남긴다.
        q.choices = [Choice(lb, "") for lb in LABELS]
    return q


def build_essay(item: Item, passage: Passage, ctx: GenContext,
                stem: str, instruction: str) -> Question:
    """서술형 1문항. client 있으면 LLM, 없으면 mock."""
    q = Question(no=item.no, section="essay", type=item.type, score=item.score,
                 stem=stem, passage_id=passage.id, difficulty=ctx.difficulty)
    if ctx.client is not None:
        from ..core.llm import EssayQuestionOut, system_prompt
        from ..core.models import DIFFICULTY_KO_REV
        subs = "\n".join(f"- {s}" for s in item.subparts) or "- 단일 서술형"
        prompt = (f"[지문]\n{passage.text}\n\n[유형 출제원리]\n{instruction}"
                  f"{_variant_hint(ctx)}\n\n"
                  f"[소문항]\n{subs}\n\n[발문]\n{stem}\n\n"
                  "위 지문으로 이 서술형 1문항을 만들어라. 반드시:\n"
                  "1) 이 유형이 요구하는 빈칸은 지문(또는 요약문)에 '____'로, 밑줄은 "
                  "<u>...</u>로 실제로 넣어라(빈칸/밑줄 없는 발문은 오류다).\n"
                  "2) <보기> 단어상자를 쓰는 유형이면 bogi 에 단어들을, <조건>을 쓰는 "
                  "유형이면 conditions 에 조건 문구를 채워라. 아니면 빈 리스트.\n"
                  "3) 영작 유형이면 학생이 영작할 한국어를 blank_ko 에 넣어라.\n"
                  "4) 각 소문항 정답을 answers 에 '지시 :: 정답' 형식으로.\n"
                  "5) explanation 에 각 소문항의 정답 근거·어형변형/어순/문법 포인트·본문 "
                  "근거를 핵심 위주로 '간결히' 써라(600자 이내, 장황하게 늘어놓지 말 것).")
        from ..core.client import ESSAY_MAX_TOKENS
        sysp = system_prompt(ctx.profile, DIFFICULTY_KO_REV.get(ctx.difficulty, "중"))
        out = ctx.client.structured(sysp, prompt, EssayQuestionOut, max_retries=2,
                                    max_tokens=ESSAY_MAX_TOKENS,
                                    extra_validate=lambda o: _validate_essay_out(item, o))
        q.passage_text = out.passage
        if out.bogi:
            q.meta["bogi"] = list(out.bogi)
        if out.conditions:
            q.meta["conditions"] = list(out.conditions)
        if out.blank_ko:
            q.meta["blank_ko"] = out.blank_ko
        notes = []
        answers = []
        for a in out.answers:
            label, sep, ans = a.partition("::")
            if sep:
                notes.append(f"{label.strip()}: {ans.strip()}")
                answers.append(ans.strip())
            else:
                notes.append(a.strip())
                answers.append(a.strip())
        q.answer = " / ".join(answers)
        q.answer_notes = notes
        q.explanation = out.explanation
        conf = (getattr(out, "answer_confidence", "") or "").strip()
        if conf and not conf.startswith("확실"):
            q.meta["review_flag"] = "정답 재확인 권장"
    else:
        q.passage_text = passage.text
        q.answer = ""
        q.answer_notes = list(item.subparts)
        # 디자인 미리보기용 <보기>/<조건> 박스 데이터(자리표시자, 표기 없이)
        _BOGI = {"dialogue_arrange_inflect", "word_arrange",
                 "arrange_and_translate", "blank_choose_no_change", "chart_fix_and_arrange"}
        _COND = {"condition_write_inflect", "grammar_fix_and_answer",
                 "summary_fill_from_text"}
        if item.type in _BOGI:
            q.meta["bogi"] = ["word", "order", "the", "sentence", "correctly", "can"]
        if item.type in ("dialogue_arrange_inflect", "arrange_and_translate"):
            q.meta["blank_ko"] = "밑줄 친 우리말"
        if item.type in _COND:
            q.meta["conditions"] = ["주어진 괄호 속 단어를 사용할 것",
                                    "필요시 어형을 변형할 것"]
    return q


# 유형별 실제 발문(자리표시자·안전망이 시스템 문구 대신 정상 발문을 쓰도록).
STEM_FALLBACK = {
    "grammar": "다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?",
    "grammar_vocab_mix": "다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?",
    "vocab_odd": "다음 글의 밑줄 친 부분 중, 문맥상 낱말의 쓰임이 적절하지 않은 것은?",
    "vocab_3blank_abc": "(A), (B), (C)의 각 네모 안에서 문맥에 맞는 낱말로 "
                        "가장 적절한 것끼리 짝지은 것은?",
    "main_point": "다음 글의 요지로 가장 적절한 것은?",
    "title": "다음 글의 제목으로 가장 적절한 것은?",
    "blank_single": "다음 빈칸에 들어갈 말로 가장 적절한 것은?",
    "order": "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?",
    "irrelevant_sentence": "다음 글에서 전체 흐름과 관계 없는 문장은?",
    "implied_meaning": "밑줄 친 부분이 다음 글에서 의미하는 바로 가장 적절한 것은?",
    "inference_mismatch": "다음 글의 내용과 일치하지 않는 것은?",
    "dialogue_mismatch": "다음 대화의 내용과 일치하지 않는 것은?",
    "notice_match": "다음 안내문의 내용과 일치하는 것은?",
    "summary_ab": "다음 글의 내용을 한 문장으로 요약하고자 한다. "
                  "빈칸 (A), (B)에 들어갈 말로 가장 적절한 것은?",
    "prep_find_and_translate": "빈칸에 공통으로 들어갈 전치사를 쓰고, 밑줄 친 문장을 "
                               "우리말로 해석하시오.",
    "dialogue_arrange_inflect": "[보기]의 단어를 모두 활용하여(어형 변형 가능) 영작하고, "
                                "본문에 근거해 우리말로 답하시오.",
    "condition_write_inflect": "괄호 속 단어를 어형 변형하여 빈칸을 채우고, 본문 단어만으로 "
                               "영어로 답하시오.",
    "summary_fill_from_text": "다음 요약문의 빈칸을 본문에 있는 단어로 채우시오.(변형 금지)",
    "word_arrange": "[보기]의 단어를 알맞게 배열하여 빈칸을 완성하시오.",
    "arrange_and_translate": "[보기]의 단어를 모두 활용하여 밑줄 친 우리말을 영작하고, "
                             "본문 내용을 우리말로 답하시오.",
    "chart_fix_and_arrange": "도표와 일치하지 않는 부분 1곳을 찾아 고치고, 우리말에 맞게 "
                             "[보기]를 배열하여 영작하시오.",
    "blank_choose_no_change": "[보기]에서 골라 각 빈칸을 채우시오.(변형 금지, 빈칸당 한 단어)",
    "grammar_fix_and_answer": "밑줄 친 부분 중 어법상 틀린 곳을 찾아 바르게 고치고, 본문에 "
                              "근거하여 영어 질문에 영어로 답하시오.",
}


def default_stem(ctx: GenContext, item_type: str) -> str:
    """학습된 발문(있으면) 또는 유형 표준 발문. 시스템 문구를 노출하지 않는다."""
    return ctx.stem(item_type, STEM_FALLBACK.get(item_type, "다음 글을 읽고 물음에 답하시오."))


def generic_question(item: Item, passage: Passage, ctx: GenContext,
                     stem: str | None = None) -> Question:
    """등록 안 된 유형·자리표시자용 최소 구조 문항. 시스템 문구 대신 정상 발문을 쓴다."""
    q = Question(no=item.no, section=item.section, type=item.type, score=item.score,
                 stem=stem or default_stem(ctx, item.type), passage_text=passage.text,
                 passage_id=passage.id, difficulty=ctx.difficulty,
                 underlines=item.underlines)
    if item.section == "choice":
        q.choices = make_choices([f"선택지 {i+1}" for i in range(5)])
        q.answer = "③"
        q.explanation = ""
    else:
        q.answer = ""
        q.answer_notes = list(item.subparts)
    if item.underlines:
        q.passage_text = underline_passage(passage.text, item.underlines)
    return q
