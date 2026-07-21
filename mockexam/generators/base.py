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

    def stem(self, item_type: str, fallback: str) -> str:
        style = self.profile.get("stem_style", {}) or {}
        return style.get(item_type) or fallback


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


def build_choice(item: Item, passage: Passage, ctx: GenContext,
                 stem: str, instruction: str,
                 mock_choices: list[str] | None = None,
                 mock_answer: str = "③",
                 mock_passage: str | None = None) -> Question:
    """객관식 1문항. client 있으면 LLM, 없으면 mock 구조 문항.

    instruction: 이 유형의 출제원리(§3-C)를 담은 지시문(LLM 프롬프트에 주입).
    """
    q = Question(no=item.no, section="choice", type=item.type, score=item.score,
                 stem=stem, passage_id=passage.id, difficulty=ctx.difficulty,
                 underlines=item.underlines)
    if ctx.client is not None:
        from ..core.llm import ChoiceQuestionOut, system_prompt
        from ..core.models import DIFFICULTY_KO_REV
        ul = (f"\n지문의 밑줄은 정확히 {item.underlines}개를 ①<u>..</u>~ 형식으로 표시하라."
              if item.underlines else "")
        prompt = (f"[지문]\n{passage.text}\n\n[유형 출제원리]\n{instruction}{ul}\n\n"
                  f"[발문]\n{stem}\n\n위 지문으로 이 유형의 5지선다 1문항을 만들어라.")
        sysp = system_prompt(ctx.profile, DIFFICULTY_KO_REV.get(ctx.difficulty, "중"))
        out = ctx.client.structured(sysp, prompt, ChoiceQuestionOut, max_retries=2)
        q.passage_text = out.passage
        q.choices = make_choices(out.choices)
        q.answer = LABELS[out.answer_index - 1]
        q.explanation = out.explanation
    else:
        q.choices = make_choices(mock_choices or [f"선택지 {i+1}" for i in range(5)])
        q.answer = mock_answer
        q.explanation = f"(mock) {item.type}: 정답 {mock_answer}."
        q.passage_text = mock_passage if mock_passage is not None else (
            underline_passage(passage.text, item.underlines) if item.underlines else passage.text)
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
                  "4) 각 소문항 정답을 answers 에 '지시 :: 정답' 형식으로.")
        sysp = system_prompt(ctx.profile, DIFFICULTY_KO_REV.get(ctx.difficulty, "중"))
        out = ctx.client.structured(sysp, prompt, EssayQuestionOut, max_retries=2)
        q.passage_text = out.passage
        if out.bogi:
            q.meta["bogi"] = list(out.bogi)
        if out.conditions:
            q.meta["conditions"] = list(out.conditions)
        if out.blank_ko:
            q.meta["blank_ko"] = out.blank_ko
        if out.prompt_extra:
            q.stem = f"{stem}\n{out.prompt_extra}"
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
