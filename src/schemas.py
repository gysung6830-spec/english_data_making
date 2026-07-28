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


class PassageSet(BaseModel):
    """한 파일 안에 있는 여러 지문(복수 가능)."""
    passages: list[Extraction] = Field(default_factory=list)

    @field_validator("passages")
    @classmethod
    def _non_empty(cls, v: list[Extraction]) -> list[Extraction]:
        if not v:
            raise ValueError("지문을 찾지 못했습니다.")
        return v


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
    def _non_empty(cls, v: list[GrammarItem]) -> list[GrammarItem]:
        if not v:
            raise ValueError("문법 항목이 비어 있습니다.")
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
    english_summary: str = ""      # 핵심 단어들을 충분히 담은 2문장 이내 영어 요약문
    english_summary_ko: str = ""   # 위 영어 요약문의 한국어 해석

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
    question_type: str   # 출제 유형 (지칭추론/함축의미/서술형)
    content: str         # 은아 T tip 내용 (여러 줄 가능, 줄바꿈으로 구분)
    tip: str = ""        # (미사용 - 이전 호환용)


class ExamSection(BaseModel):
    items: list[ExamItem]

    @field_validator("items")
    @classmethod
    def _has_items(cls, v: list[ExamItem]) -> list[ExamItem]:
        if not v:
            raise ValueError("출제 포인트가 비어 있습니다.")
        return v


# ---------------------------------------------------------------------------
# ⑦ 모의고사 훈련서 (모의고사 입문·60점대 학생용 기초 훈련)
#    소재 찾기 → 주제 찾기 → 선지 읽기(유형별 문제) → 구문(직독직해) 훈련
# ---------------------------------------------------------------------------
class TrainClue(BaseModel):
    """소재를 알려주는 '반복되는 핵심 어구' (소재 찾기 단서)."""
    word: str        # 지문에서 반복·강조되는 영어 어구
    meaning: str     # 한글 뜻


class TopicTraining(BaseModel):
    """소재 찾기 · 주제 찾기 훈련 데이터."""
    clues: list[TrainClue] = Field(default_factory=list)  # 반복 어구(소재 단서)
    material: str            # 소재 = '무엇에 관한 글인가' (짧은 한글 한 마디)
    topic: str               # 주제 한 문장 (한글)
    steps: list[str] = Field(default_factory=list)  # 소재→주제로 가는 사고 과정(학생 안내)

    @field_validator("material", "topic")
    @classmethod
    def _non_blank(cls, v: str) -> str:
        if not (v or "").strip():
            raise ValueError("소재/주제가 비어 있습니다.")
        return v


class TrainChoice(BaseModel):
    """유형 문제의 선지 하나 (+ 선지 읽기 훈련용 정오 이유)."""
    symbol: str            # ① ② ③ ④ ⑤
    text: str              # 선지 내용
    correct: bool = False  # 정답 여부
    reason: str = ""       # 왜 정답/오답인지 (선지 읽기 훈련)


class TrainQuestion(BaseModel):
    qtype: str                 # 유형: 주제 / 요지 / 빈칸추론 등
    instruction: str           # 발문 (예: '다음 글의 주제로 가장 적절한 것은?')
    passage_excerpt: str = ""  # 빈칸 유형 등에서 보여줄 지문/빈칸 표시(없으면 공란)
    choices: list[TrainChoice]
    answer: str                # 정답 기호 (①~⑤)
    solution: str = ""         # 풀이: 소재→주제→정답 도출 과정

    @field_validator("choices")
    @classmethod
    def _has_choices(cls, v: list[TrainChoice]) -> list[TrainChoice]:
        if len(v) < 2:
            raise ValueError("선지는 2개 이상이어야 합니다.")
        return v


class TrainSection(BaseModel):
    topic_training: TopicTraining
    questions: list[TrainQuestion]
    reading_tip: str = ""      # 선지 읽는 법 요약 팁

    @field_validator("questions")
    @classmethod
    def _has_questions(cls, v: list[TrainQuestion]) -> list[TrainQuestion]:
        if not v:
            raise ValueError("훈련 문제가 비어 있습니다.")
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
    # 모의고사 훈련서용(선택). train 출력을 켠 경우에만 채워진다.
    train: TrainSection | None = None
