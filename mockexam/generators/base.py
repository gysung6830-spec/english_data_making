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
# 위 원리(정답=유의어 패러프레이즈)를 적용하는 유형
_PARAPHRASE_TYPES = {"main_point", "title", "implied_meaning"}


def _flag_reason(item: Item, out: Any) -> str:
    """해설지 '⚠ 확인 권장' 배지 사유. 없으면 빈 문자열.

    (1) 모델 자가확신도가 '주의'거나, (2) 유의어 패러프레이즈 유형인데 정답 선지가
    지문 문장과 거의 동일(원리 위반)하면 사람이 한 번 더 볼 것을 권한다.
    """
    conf = (getattr(out, "answer_confidence", "") or "").strip()
    if conf and not conf.startswith("확실"):
        return "정답 유일성 자가점검에서 '주의'로 표시됨"
    if item.type in _PARAPHRASE_TYPES:
        try:
            correct = (out.choices[out.answer_index - 1] or "").strip()
        except Exception:  # noqa: BLE001
            correct = ""
        core = re.sub(r"[^A-Za-z가-힣 ]", "", correct).strip().lower()
        if len(core) >= 12 and core in (out.passage or "").lower():
            return "정답 선지가 지문 문장과 거의 동일(유의어 패러프레이즈 원리 위반 가능)"
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
        prompt = (f"[지문]\n{passage.text}\n\n[유형 출제원리]\n{instruction}{ul}\n\n"
                  f"[발문]\n{stem}\n\n위 지문으로 이 유형의 5지선다 1문항을 만들어라.\n"
                  "[정답 유일성 자가검증] 출력 전에 스스로 다섯 선지를 하나씩 대입해 "
                  "정답이 '오직 1개'만 성립하는지 확인하라. 두 개 이상 정답이 될 여지가 "
                  "있으면 오답 선지를 확실히 틀리도록 고쳐서 유일 정답이 되게 하라.\n"
                  "explanation 에는 정답 근거뿐 아니라 오답 ①~⑤ 각각이 왜 틀렸는지와 "
                  "핵심 문법·어휘·논지 포인트까지 자세히 써라.")
        sysp = system_prompt(ctx.profile, DIFFICULTY_KO_REV.get(ctx.difficulty, "중"))
        out = ctx.client.structured(sysp, prompt, ChoiceQuestionOut, max_retries=2,
                                    extra_validate=lambda o: _validate_choice_out(item, o))
        q.passage_text = out.passage
        q.choices = make_choices(out.choices)
        q.answer = LABELS[out.answer_index - 1]
        q.explanation = out.explanation
        flag = _flag_reason(item, out)
        if flag:
            q.meta["review_flag"] = flag
    else:
        q.choices = make_choices(mock_choices or [f"선택지 {i+1}" for i in range(5)])
        q.answer = mock_answer
        q.explanation = f"(mock) {item.type}: 정답 {mock_answer}."
        q.passage_text = mock_passage if mock_passage is not None else (
            underline_passage(passage.text, item.underlines) if item.underlines else passage.text)
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
        prompt = (f"[지문]\n{passage.text}\n\n[유형 출제원리]\n{instruction}\n\n"
                  f"[소문항]\n{subs}\n\n[발문]\n{stem}\n\n"
                  "위 지문으로 이 서술형 1문항을 만들어라. 반드시:\n"
                  "1) 이 유형이 요구하는 빈칸은 지문(또는 요약문)에 '____'로, 밑줄은 "
                  "<u>...</u>로 실제로 넣어라(빈칸/밑줄 없는 발문은 오류다).\n"
                  "2) <보기> 단어상자를 쓰는 유형이면 bogi 에 단어들을, <조건>을 쓰는 "
                  "유형이면 conditions 에 조건 문구를 채워라. 아니면 빈 리스트.\n"
                  "3) 영작 유형이면 학생이 영작할 한국어를 blank_ko 에 넣어라.\n"
                  "4) 각 소문항 정답을 answers 에 '지시 :: 정답' 형식으로.\n"
                  "5) explanation 에 각 소문항의 정답 근거·어형변형/어순/문법 포인트·본문 "
                  "근거를 자세히 써라.")
        sysp = system_prompt(ctx.profile, DIFFICULTY_KO_REV.get(ctx.difficulty, "중"))
        out = ctx.client.structured(sysp, prompt, EssayQuestionOut, max_retries=2,
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
            q.meta["review_flag"] = "정답 확신도 '주의'로 표시됨"
    else:
        q.passage_text = passage.text
        q.answer = "(mock) 서술형 정답 예시"
        q.answer_notes = [f"{sp}: (mock 정답)" for sp in item.subparts]
        # 디자인 미리보기용 <보기>/<조건> 박스 데이터(오프라인 자리표시자)
        _BOGI = {"dialogue_arrange_inflect", "word_arrange",
                 "arrange_and_translate", "blank_choose_no_change", "chart_fix_and_arrange"}
        _COND = {"condition_write_inflect", "grammar_fix_and_answer",
                 "summary_fill_from_text"}
        if item.type in _BOGI:
            q.meta["bogi"] = ["(mock)", "word1", "word2", "word3", "word4", "can"]
        if item.type in ("dialogue_arrange_inflect", "arrange_and_translate"):
            q.meta["blank_ko"] = "(mock) 밑줄 친 우리말 의미"
        if item.type in _COND:
            q.meta["conditions"] = ["(mock) 주어진 괄호 속 단어를 사용할 것",
                                    "(mock) 필요시 어형을 변형할 것"]
    return q


def generic_question(item: Item, passage: Passage, ctx: GenContext,
                     stem: str) -> Question:
    """어떤 유형이든 최소 구조를 갖춘 mock 문항(등록 안 된 유형 안전망)."""
    q = Question(no=item.no, section=item.section, type=item.type,
                 score=item.score, stem=stem, passage_text=passage.text,
                 passage_id=passage.id, difficulty=ctx.difficulty,
                 underlines=item.underlines)
    if item.section == "choice":
        q.choices = make_choices([f"선택지 {i+1}" for i in range(5)])
        q.answer = "③"
        q.explanation = "(mock) 문맥상 ③이 정답."
    else:
        q.answer = "(mock) 서술형 정답 예시"
        q.answer_notes = [f"소문항: {sp}" for sp in item.subparts]
    if item.underlines:
        q.passage_text = underline_passage(passage.text, item.underlines)
    return q
