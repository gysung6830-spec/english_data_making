"""LLM 이 각 단계에서 돌려줘야 하는 구조화 JSON 스키마 (pydantic).

핵심 원칙(단일 지문 공유):
- 생성기는 '지문을 다시 쓰지' 않는다. 대신 분석 결과의 문장(sentences)을
  '어떻게 변형할지'(문장 번호·단어·순서)만 돌려준다.
- 실제 HTML 조립은 코드(exam.build)가 정본 문장에서 수행하므로,
  6종이 모두 '같은 지문'을 공유하는 것이 구조적으로 보장된다.
- 문장 번호(sent_no, remove_no 등)는 분석 결과에 표시된 (1),(2)… 와 같은 '1-based'.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# 공통: 지문 1회 분석 (analyzer) — 6종이 나눠 쓴다
# ---------------------------------------------------------------------------
class KeyTerm(BaseModel):
    word: str
    synonym: str
    antonym: str = ""


class Analysis(BaseModel):
    title: str
    sentences: list[str]           # 정본 지문(문장 단위, 원문 그대로·순서 유지)
    main_idea: str
    key_terms: list[KeyTerm] = Field(default_factory=list)
    hardest_sentence: str = ""

    @field_validator("sentences")
    @classmethod
    def _has_sentences(cls, v: list[str]) -> list[str]:
        v = [s.strip() for s in v if s and s.strip()]
        if len(v) < 4:
            raise ValueError("문장이 4개 미만입니다(지문이 너무 짧음).")
        return v


# ---------------------------------------------------------------------------
# ① 순서 배열 — 정본을 덩어리로 쪼개 라벨만 섞음
# ---------------------------------------------------------------------------
class OrderOut(BaseModel):
    given_n: int                   # 앞에서 몇 문장을 '주어진 글'로 (>=1)
    block_sizes: list[int]         # 나머지를 3덩어리로 (len==3)
    display: list[int]             # (A)(B)(C) 가 각각 원래 몇 번째 덩어리(1~3)인지
    reason: str

    @field_validator("block_sizes", "display")
    @classmethod
    def _three(cls, v: list[int]) -> list[int]:
        if len(v) != 3:
            raise ValueError("block_sizes·display 는 3개여야 합니다.")
        return v

    @field_validator("display")
    @classmethod
    def _perm(cls, v: list[int]) -> list[int]:
        if sorted(v) != [1, 2, 3]:
            raise ValueError("display 는 1,2,3 의 순열이어야 합니다.")
        return v


# ---------------------------------------------------------------------------
# ② 문장 삽입 — 정본에서 문장 하나만 빼냄
# ---------------------------------------------------------------------------
class InsertOut(BaseModel):
    remove_no: int                 # 빼낼 문장 번호(1-based, 내부 문장)
    reason: str


# ---------------------------------------------------------------------------
# ③ 주제 (영어 선지, 지문은 원본 그대로)
# ---------------------------------------------------------------------------
class WrongReason(BaseModel):
    no: int
    text: str


class TopicOut(BaseModel):
    choices: list[str]
    answer_no: int
    reason: str
    wrong_reasons: list[WrongReason]

    @field_validator("choices")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("주제 선지는 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v


# ---------------------------------------------------------------------------
# ④ 어휘 — 정본에서 지정 단어만 밑줄/치환
# ---------------------------------------------------------------------------
class WordMark(BaseModel):
    sent_no: int                   # 밑줄 단어가 있는 문장 번호(1-based)
    word: str                      # 정본 문장 속 원본 단어(찾을 대상)
    shown: str                     # 문제에 보여줄 단어(유의어/반의어/원본/오답형)


class VocabOut(BaseModel):
    marks: list[WordMark]          # 밑줄 5개
    answer_no: int                 # 문맥상 부적절한 밑줄 번호(1~5)
    reason: str
    override_no: int = 0           # (방식2) 부정어를 넣을 문장 번호(1-based, 0=없음)
    override_text: str = ""        # (방식2) 그 문장의 교체 텍스트

    @field_validator("marks")
    @classmethod
    def _five(cls, v: list[WordMark]) -> list[WordMark]:
        if len(v) != 5:
            raise ValueError("어휘 밑줄은 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v


# ---------------------------------------------------------------------------
# ⑤ 어법 (복수정답, 최대 8밑줄)
# ---------------------------------------------------------------------------
class GrammarReason(BaseModel):
    no: int
    text: str


class GrammarOut(BaseModel):
    marks: list[WordMark]          # 밑줄 2~8개(틀린 것은 shown 이 오답형)
    answer_nos: list[int]          # 틀린 밑줄 번호들(복수)
    reasons: list[GrammarReason]

    @field_validator("marks")
    @classmethod
    def _count(cls, v: list[WordMark]) -> list[WordMark]:
        if not (2 <= len(v) <= 8):
            raise ValueError("어법 밑줄은 2~8개여야 합니다.")
        return v

    def check(self) -> None:
        n = len(self.marks)
        if not self.answer_nos:
            raise ValueError("복수 정답이 최소 1개는 있어야 합니다.")
        for a in self.answer_nos:
            if not (1 <= a <= n):
                raise ValueError(f"정답 번호 {a} 가 범위를 벗어났습니다(1~{n}).")


# ---------------------------------------------------------------------------
# ⑥ 서술형 (세 소문항, 지문은 원본 그대로)
# ---------------------------------------------------------------------------
class ShortOut(BaseModel):
    q1_prompt: str
    q1_answer: str                 # 한글 모범 답안
    q2_prompt: str
    q2_tokens: list[str]           # 낱개 단어(구 묶음 금지)
    q2_cues: list[str]             # 변형할 제시어(동사 원형 등)
    q2_answer: str
    q3_prompt: str
    q3_before: str
    q3_mid: str
    q3_after: str
    q3_cue_a: str
    q3_cue_b: str
    q3_ans_a: str
    q3_ans_b: str
    q3_reason: str

    @field_validator("q2_tokens")
    @classmethod
    def _tokens(cls, v: list[str]) -> list[str]:
        v = [t.strip() for t in v if t and t.strip()]
        if len(v) < 4:
            raise ValueError("영작 <보기> 낱개 단어는 최소 4개 이상이어야 합니다.")
        for t in v:
            if " " in t:
                raise ValueError(f"낱개 단어여야 합니다(구 묶음 금지): '{t}'")
        return v

    @field_validator("q2_cues")
    @classmethod
    def _cues(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("변형할 제시어(cue)가 최소 1개는 있어야 합니다.")
        return v
