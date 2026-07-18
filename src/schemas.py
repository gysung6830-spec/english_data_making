"""각 API 호출이 반환해야 하는 구조화된 JSON 스키마 (pydantic).

각 섹션은 자유 텍스트가 아니라 아래 스키마에 맞는 JSON 으로 응답해야 하며,
코드에서 필드 누락/개수 오류를 검증한다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# 0단계: 지문 본문 추출 (전처리)
# ---------------------------------------------------------------------------
class Extraction(BaseModel):
    title: str = Field(default="Untitled")
    source: str = Field(default="")
    paragraphs: list[str] = Field(default_factory=list)

    @field_validator("paragraphs")
    @classmethod
    def _non_empty(cls, v: list[str]) -> list[str]:
        v = [p.strip() for p in v if p and p.strip()]
        if not v:
            raise ValueError("본문 문단이 비어 있습니다.")
        return v

    @property
    def body(self) -> str:
        return "\n\n".join(self.paragraphs)


# ---------------------------------------------------------------------------
# ① 내용 전체 요약 정리  (주제 한 문장)
# ---------------------------------------------------------------------------
class SummarySection(BaseModel):
    overall: str  # 지문의 주제를 담은 한 문장


# ---------------------------------------------------------------------------
# ② 직독직해 (2단 표)
# ---------------------------------------------------------------------------
class KeyWord(BaseModel):
    word: str
    meaning: str


class Chunk(BaseModel):
    english: str            # 원문 chunk (의미 단위)
    syntax: str = ""        # 핵심 구문 분석 (예: "5형식 ask+목+to부정사")
    korean: str             # 직독직해 (한국어)
    words: list[KeyWord] = Field(default_factory=list)


class Sentence(BaseModel):
    no: int
    chunks: list[Chunk]
    note: str = ""   # 문장 내용이 추상적일 때만 붙이는 쉬운 설명(아니면 공란)

    @field_validator("chunks")
    @classmethod
    def _has_chunks(cls, v: list[Chunk]) -> list[Chunk]:
        if not v:
            raise ValueError("문장에 chunk 가 없습니다.")
        return v


class LiteralSection(BaseModel):
    sentences: list[Sentence]

    @field_validator("sentences")
    @classmethod
    def _has_sentences(cls, v: list[Sentence]) -> list[Sentence]:
        if not v:
            raise ValueError("직독직해 문장이 비어 있습니다.")
        return v


# ---------------------------------------------------------------------------
# ③ 핵심 문법 TOP 10 (정확히 10개)
# ---------------------------------------------------------------------------
class GrammarItem(BaseModel):
    no: int
    point: str            # 문법 포인트명
    example: str          # 지문에서 나온 실제 예문
    explanation: str      # 핵심 설명
    key: bool = False     # 핵심 어법(관계사/분사/가정법/비교/도치/강조/5형식) 여부
    sentence_no: int = 0  # 이 문법이 등장하는 지문 문장 번호(직독직해 문장과 매칭)


class GrammarSection(BaseModel):
    items: list[GrammarItem]

    @field_validator("items")
    @classmethod
    def _exactly_10(cls, v: list[GrammarItem]) -> list[GrammarItem]:
        if len(v) != 10:
            raise ValueError(f"핵심 문법은 정확히 10개여야 합니다 (현재 {len(v)}개).")
        return v


# ---------------------------------------------------------------------------
# ④ 핵심 어휘 · 유의어 · 반의어
# ---------------------------------------------------------------------------
class VocabItem(BaseModel):
    no: int
    word: str
    meaning: str            # 한글 의미
    synonyms: str = ""      # 유의어 (없으면 공란)
    antonyms: str = ""      # 반의어 (없으면 공란)
    example: str = ""       # 지문 속 예문


class VocabSection(BaseModel):
    items: list[VocabItem]

    def validate_count(self, lo: int, hi: int) -> None:
        n = len(self.items)
        if not (lo <= n <= hi):
            raise ValueError(f"어휘 개수는 {lo}~{hi}개여야 합니다 (현재 {n}개).")


# ---------------------------------------------------------------------------
# ⑤ 지문 구조 분석 (Logic Flow / Emotional Flow)
# ---------------------------------------------------------------------------
class FlowStage(BaseModel):
    stage: str                 # 단계명 (예: 도입/전개/... 또는 감정명)
    content: str               # 해당 단계 정리
    evidence: str = ""         # 근거 문장 인용 (감정 흐름에서 특히)


class StructureSection(BaseModel):
    flow_type: Literal["logic", "emotional"]
    genre_reason: str = ""              # 왜 이 유형으로 판별했는지
    easy_explanation: str = ""          # 핵심을 확 와닿게 한 문장으로 요약(친근한 구어체)
    examples: list[str] = Field(default_factory=list)  # 실생활에 빗댄 공감형 예시(Killer Examples)
    stages: list[FlowStage]

    @field_validator("stages")
    @classmethod
    def _has_stages(cls, v: list[FlowStage]) -> list[FlowStage]:
        if not v:
            raise ValueError("구조 분석 단계가 비어 있습니다.")
        return v


# ---------------------------------------------------------------------------
# ⑥ 내신 빈출 출제 포인트 체크리스트
# ---------------------------------------------------------------------------
class ExamItem(BaseModel):
    question_type: str   # 출제 유형 (빈칸추론/제목추론/주제파악/순서배열/내용일치/서술형 등)
    content: str         # 출제 내용
    tip: str             # 신샘팁 (변형 대비 포인트)


class ExamSection(BaseModel):
    items: list[ExamItem]

    @field_validator("items")
    @classmethod
    def _has_items(cls, v: list[ExamItem]) -> list[ExamItem]:
        if not v:
            raise ValueError("출제 포인트가 비어 있습니다.")
        return v


# ---------------------------------------------------------------------------
# 최종 조립 결과 (렌더링 입력)
# ---------------------------------------------------------------------------
class Report(BaseModel):
    title: str
    source: str = ""
    summary: SummarySection
    literal: LiteralSection
    grammar: GrammarSection
    vocab: VocabSection
    structure: StructureSection
    exam: ExamSection
