"""LLM 이 각 단계에서 돌려줘야 하는 구조화 JSON 스키마 (pydantic).

- 자유 텍스트가 아니라 아래 스키마에 맞는 JSON 으로 응답을 강제하고,
  코드가 개수·범위를 검증한다(src.client.output_format 사용).
- 최종 HTML 조립은 코드(exam.format)가 담당하므로, 볼드 규칙 등은
  LLM 이 신경 쓸 필요가 없다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# 공통: 지문 1회 분석 (analyzer) — 6종이 나눠 쓴다
# ---------------------------------------------------------------------------
class KeyTerm(BaseModel):
    word: str                      # 지문 핵심어(원문 형태)
    synonym: str                   # 유의어(주제 정답·어휘 오답 변형에 사용)
    antonym: str = ""              # 반의어(어휘 정답 변형에 사용)


class Analysis(BaseModel):
    title: str
    sentences: list[str]           # 지문을 문장 단위로 분리
    main_idea: str                 # 주제 한 문장(영어)
    key_terms: list[KeyTerm] = Field(default_factory=list)
    hardest_sentence: str = ""     # 문법 요소가 가장 많은 문장(서술형 영작용)

    @field_validator("sentences")
    @classmethod
    def _has_sentences(cls, v: list[str]) -> list[str]:
        v = [s.strip() for s in v if s and s.strip()]
        if len(v) < 3:
            raise ValueError("문장이 3개 미만입니다(지문이 너무 짧음).")
        return v


# ---------------------------------------------------------------------------
# ① 순서 배열
# ---------------------------------------------------------------------------
class OrderOut(BaseModel):
    given: str
    seg_a: str
    seg_b: str
    seg_c: str
    orders: list[str]              # 5개 순서 조합 문자열 [예: "(B)-(A)-(C)"]
    answer_no: int                 # 정답 보기 번호 1..5
    reason: str

    @field_validator("orders")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("순서 보기는 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v


# ---------------------------------------------------------------------------
# ② 문장 삽입
# ---------------------------------------------------------------------------
class InsertOut(BaseModel):
    given_sentence: str
    chunks: list[str]              # 6개 조각(사이에 ①~⑤ 위치가 들어감)
    answer_no: int                 # 원래 위치 번호 1..5
    reason: str

    @field_validator("chunks")
    @classmethod
    def _six(cls, v: list[str]) -> list[str]:
        if len(v) != 6:
            raise ValueError("chunks 는 정확히 6개여야 합니다(위치 5개).")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v


# ---------------------------------------------------------------------------
# ③ 주제 (영어 선지)
# ---------------------------------------------------------------------------
class WrongReason(BaseModel):
    no: int
    text: str


class TopicOut(BaseModel):
    passage: str                   # 보여줄 지문(원문)
    choices: list[str]             # 영어 선지 5개
    answer_no: int                 # 정답 번호 1..5
    reason: str
    wrong_reasons: list[WrongReason]  # 오답 4개가 틀린 이유

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
# ④ 어휘 (문맥상 부적절)
# ---------------------------------------------------------------------------
class VocabOut(BaseModel):
    chunks: list[str]              # 6개 조각(사이에 5개 밑줄 단어가 들어감)
    words: list[str]              # 밑줄 단어 5개(정답 1개는 반의어로 변형, 나머지는 유의어)
    answer_no: int                 # 문맥상 부적절한 밑줄 번호 1..5
    reason: str

    @field_validator("words")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("밑줄 단어는 정확히 5개여야 합니다.")
        return v

    @field_validator("chunks")
    @classmethod
    def _six(cls, v: list[str]) -> list[str]:
        if len(v) != 6:
            raise ValueError("chunks 는 정확히 6개여야 합니다(밑줄 5개).")
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
    chunks: list[str]              # 밑줄 개수 + 1 개 조각
    words: list[str]              # 밑줄 단어들(2~8개), 그중 여러 개는 어법상 틀리게
    answer_nos: list[int]          # 틀린 밑줄 번호들(복수)
    reasons: list[GrammarReason]

    @field_validator("words")
    @classmethod
    def _count(cls, v: list[str]) -> list[str]:
        if not (2 <= len(v) <= 8):
            raise ValueError("밑줄은 2~8개여야 합니다.")
        return v

    def check(self) -> None:
        if len(self.chunks) != len(self.words) + 1:
            raise ValueError("chunks 는 words+1 개여야 합니다.")
        n = len(self.words)
        if not self.answer_nos:
            raise ValueError("복수 정답이 최소 1개는 있어야 합니다.")
        for a in self.answer_nos:
            if not (1 <= a <= n):
                raise ValueError(f"정답 번호 {a} 가 범위를 벗어났습니다(1~{n}).")


# ---------------------------------------------------------------------------
# ⑥ 서술형 (세 소문항)
# ---------------------------------------------------------------------------
class ShortOut(BaseModel):
    passage: str
    # (1) 독해 이해 확인형 — 한글 답
    q1_prompt: str
    q1_answer: str                 # 한글 모범 답안
    # (2) 문법 문장 영작 (동사 원형 제공, 낱개 배열)
    q2_prompt: str
    q2_tokens: list[str]           # 낱개 단어(구 묶음 금지)
    q2_cues: list[str]             # 그 중 학생이 변형할 제시어(동사 원형 등)
    q2_answer: str                 # 원래 문장(어형변화 포함)
    # (3) 영어 요약문 핵심어 빈칸 (어형변화)
    q3_prompt: str
    q3_before: str                 # (A) 앞 텍스트
    q3_mid: str                    # (A)와 (B) 사이 텍스트
    q3_after: str                  # (B) 뒤 텍스트
    q3_cue_a: str                  # (A) 제시어 원형
    q3_cue_b: str                  # (B) 제시어 원형
    q3_ans_a: str                  # (A) 정답 형태
    q3_ans_b: str                  # (B) 정답 형태
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
