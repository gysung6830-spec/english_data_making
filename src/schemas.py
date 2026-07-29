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


# ===========================================================================
# 내신 서술형 대비 교재 (Worksheet) — 6개 유형
#   실제 내신 서술형 교재 문항 형식을 따른다(지문 상단 노출, (A)(B) 빈칸 등).
#   각 유형은 '문제 + 정답 + 해설'을 함께 담아, 한 데이터로
#   학생용/교사용/빠른정답/정답및해설 4파트를 만든다.
# ===========================================================================

# 유형 1) 서술형 요약문 완성 -------------------------------------------------
class WSSummaryBlank(BaseModel):
    label: str            # 빈칸 라벨 "A", "B"
    answer: str           # 정답 단어(원문 단어, 필요시 어형 변화)
    meaning: str = ""     # 한글 뜻(교사용 표시)


class WSSummaryItem(BaseModel):
    sentence: str                          # 요약문. 빈칸은 [[A]], [[B]] 로 표시
    blanks: list[WSSummaryBlank]

    @field_validator("blanks")
    @classmethod
    def _has_blanks(cls, v: list[WSSummaryBlank]) -> list[WSSummaryBlank]:
        if not v:
            raise ValueError("요약문 빈칸이 없습니다.")
        return v


class WSSummaryType(BaseModel):
    """유형1: 지문 요약문의 (A)(B) 빈칸을 원문 단어로 채우기(여러 문항)."""
    items: list[WSSummaryItem]

    @field_validator("items")
    @classmethod
    def _min_items(cls, v: list[WSSummaryItem]) -> list[WSSummaryItem]:
        if len(v) < 2:
            raise ValueError("요약문 문항은 2개 이상이어야 합니다.")
        return v


# 유형 2) 문장 변형 대비(paraphrasing) --------------------------------------
class WSParaphraseQ(BaseModel):
    original: str                          # 지문에서 고른 원문 문장
    options: list[str]                     # 5개 변형 선지
    answer: int                            # 정답 선지 번호(1~5)
    explanation: str = ""                  # 정답 근거 + 오답 이유

    @field_validator("options")
    @classmethod
    def _five_options(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("변형 선지는 정확히 5개여야 합니다.")
        return v


class WSParaphraseType(BaseModel):
    questions: list[WSParaphraseQ]

    @field_validator("questions")
    @classmethod
    def _min_q(cls, v: list[WSParaphraseQ]) -> list[WSParaphraseQ]:
        if not v:
            raise ValueError("문장 변형 문항이 비어 있습니다.")
        return v


# 유형 3) 요지/제목 배열 영작 -----------------------------------------------
class WSArrangeItem(BaseModel):
    korean: str                            # 영작할 우리말(요지 또는 제목)
    given_words: list[str] = Field(default_factory=list)   # 보기 단어(모두 사용)
    word_count: str = ""                   # 단어 수(예: "12단어")
    answer: str                            # 정답 영작
    explanation: str = ""

    @field_validator("given_words")
    @classmethod
    def _has_words(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("보기 단어가 비어 있습니다.")
        return v


class WSArrangeType(BaseModel):
    ideas: list[WSArrangeItem]             # 글의 요지
    titles: list[WSArrangeItem]            # 글의 제목

    @field_validator("ideas", "titles")
    @classmethod
    def _non_empty(cls, v: list[WSArrangeItem]) -> list[WSArrangeItem]:
        if not v:
            raise ValueError("배열 영작 문항이 비어 있습니다.")
        return v


# 유형 4) 조건 영작 연습 ----------------------------------------------------
class WSComposeItem(BaseModel):
    korean: str                            # 영작할 우리말
    conditions: list[str] = Field(default_factory=list)    # 어법 조건
    given_words: list[str] = Field(default_factory=list)   # 필수 단어(보기)
    word_count: str = ""                   # 단어 수
    answer: str                            # 정답 영작(원문 문장)
    explanation: str = ""


class WSComposeType(BaseModel):
    items: list[WSComposeItem]

    @field_validator("items")
    @classmethod
    def _min_items(cls, v: list[WSComposeItem]) -> list[WSComposeItem]:
        if not v:
            raise ValueError("조건 영작 문항이 비어 있습니다.")
        return v


# 유형 5) 보기 어휘 빈칸 완성(사용되지 않는 낱말 고르기) --------------------
class WSClozeSentence(BaseModel):
    label: str                             # 빈칸 라벨 "A","B","C","D"
    text: str                              # 빈칸을 [[A]] 로 표시한 문장
    answer: str                            # 그 빈칸에 들어갈 보기 단어


class WSClozeSet(BaseModel):
    choices: list[str]                     # 보기 단어(①~⑤ 순서, 5개)
    sentences: list[WSClozeSentence]       # 빈칸이 있는 문장들(보통 4개)
    unused: str                            # 어디에도 쓰이지 않는 낱말(정답)
    explanation: str = ""

    @field_validator("choices")
    @classmethod
    def _five_choices(cls, v: list[str]) -> list[str]:
        if len(v) < 5:
            raise ValueError("보기 단어는 5개 이상이어야 합니다.")
        return v

    @field_validator("sentences")
    @classmethod
    def _has_sents(cls, v: list[WSClozeSentence]) -> list[WSClozeSentence]:
        if not v:
            raise ValueError("빈칸 문장이 비어 있습니다.")
        return v


class WSChoiceType(BaseModel):
    sets: list[WSClozeSet]

    @field_validator("sets")
    @classmethod
    def _min_sets(cls, v: list[WSClozeSet]) -> list[WSClozeSet]:
        if not v:
            raise ValueError("어휘 빈칸 세트가 비어 있습니다.")
        return v


# 유형 6) 어법 오류 수정 ----------------------------------------------------
class WSErrorItem(BaseModel):
    text: str                              # 어법 오류가 포함된 문장(오류를 그대로 둔 채)
    error: str                             # 틀린 표현(문장 속 그대로)
    correction: str                        # 바르게 고친 표현
    explanation: str = ""                  # 어법 설명(한국어)


class WSErrorType(BaseModel):
    items: list[WSErrorItem]

    @field_validator("items")
    @classmethod
    def _min_items(cls, v: list[WSErrorItem]) -> list[WSErrorItem]:
        if not v:
            raise ValueError("어법 오류 문항이 비어 있습니다.")
        return v


class Worksheet(BaseModel):
    """한 지문에서 만든 서술형 대비 교재(6개 유형)."""
    title: str
    source: str = ""
    passage: str = ""               # 원문 지문(유형1 상단에 노출)
    summary: WSSummaryType          # 유형1
    paraphrase: WSParaphraseType    # 유형2
    arrange: WSArrangeType          # 유형3 (요지/제목 배열 영작)
    compose: WSComposeType          # 유형4 (조건 영작)
    choice: WSChoiceType            # 유형5 (사용되지 않는 낱말)
    error: WSErrorType              # 유형6


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
