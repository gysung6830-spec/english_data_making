"""LLM 구조화 응답 스키마 (pydantic).

analyzer / point_builder 가 Claude 에게 요청할 때 강제하는 JSON 형식.
src/client.py 의 structured() 가 이 스키마로 검증한다. 검증을 통과한 객체는
models.py 의 dataclass(Token/Sentence/Point)로 변환된다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# analyzer: 문장 1개의 구문 태깅 결과
# ---------------------------------------------------------------------------
class TokenSpec(BaseModel):
    text: str
    role: str = ""          # 'S','V','O','C','S①' ... (성분 라벨). 없으면 빈 문자열
    note: str = ""          # 문법 주석 (예: '현재분사'). 없으면 빈 문자열
    note_kind: Literal["lbl", "red", "gray", "blue"] = "lbl"
    wrong: str = ""         # 오답형 (예: 'direct(X)'). 없으면 빈 문자열
    above: str = ""         # 토큰 위 메모 (예: 'it is 생략', '= infuse', '↔ decline')
    hl: Literal["", "y", "g", "p"] = ""   # 하이라이트: 없음/노랑/연두/라벤더
    underline: bool = False
    color: Literal["", "red", "blue"] = ""
    slash: bool = False     # 이 토큰 뒤에 끊어읽기 경계 '/' 표시


class LineSpec(BaseModel):
    tokens: list[TokenSpec] = Field(default_factory=list)


class SentenceAnalysis(BaseModel):
    """한 문장의 태깅 + 해석."""

    lines: list[LineSpec] = Field(default_factory=list)
    translation: str = ""   # 온전한 해석(자연스러운 한 문장, 박스에 표시)
    # 직독직해(끊어읽기): '영어 slash 조각당 한 개'의 한글 배열(순서 1:1 대응).
    reading_ko: list[str] = Field(default_factory=list)
    badge: str = ""         # '빈'(빈출)·'서'(서술형) 등 짧은 뱃지. 없으면 빈 문자열
    gloss_en: str = ""      # 함축 의미 영어(맥락 없이 안 풀리는 문장에만). 없으면 ""
    gloss_ko: str = ""      # 함축 의미 한글(영어와 병기). 없으면 ""
    refs: list[str] = Field(default_factory=list)  # 대명사 지칭(예: 'it → the teabag'). 없으면 []

    @field_validator("reading_ko", mode="before")
    @classmethod
    def _reading_to_list(cls, v):
        # 구버전 호환: 문자열(' / ' 구분)로 오면 리스트로 변환.
        if isinstance(v, str):
            return [c.strip() for c in v.split("/") if c.strip()]
        return v


# ---------------------------------------------------------------------------
# point_builder: 문장 1개의 독해/어법 포인트
# ---------------------------------------------------------------------------
class PointSpec(BaseModel):
    kind: Literal["reading", "grammar"]
    caption: str
    body_html: str          # 신뢰된 간단 HTML(리스트/표 허용). 굵게=<b>, 목록=<ul><li>


class PointBundle(BaseModel):
    points: list[PointSpec] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# overview_builder: 뒷페이지(어휘 리스트 / 논리 흐름도 / 쉬운 예시 목차)
# ---------------------------------------------------------------------------
class VocabSpec(BaseModel):
    word: str
    meaning: str
    syn: str = ""            # 유의어(쉼표 구분). 없으면 '—'
    ant: str = ""            # 반의어(쉼표 구분). 없으면 '—'
    sent: int = 0            # 등장 문장 번호(없으면 0)


class FlowSpec(BaseModel):
    label: str               # '도입','전개','비유','원리','주장','결론' 등
    text: str                # 개조식 논리 내용
    easy: str = ""           # 학생 눈높이 쉬운 예시 한 줄(같은 단계에 함께)
    sentences: str = ""      # 관련 문장 번호(예: '1~3')


class ImplicitSpec(BaseModel):
    sent: int = 0            # 문장 번호
    phrase: str = ""         # 원문 핵심 함축 표현(영어)
    meaning_ko: str = ""     # 문맥상 의미(한글)
    answer_en: str = ""      # 영어 정답 표현(쉬운 영어 한 문장)
    trap_ko: str = ""        # ⚠️ 직역 함정(한글)


class OverviewBundle(BaseModel):
    # ⚠️ 한글 제목을 '먼저' 정하고, 그것을 영어로 번역 → title_ko 를 앞에 둬 생성 순서 유도.
    title_ko: str = ""       # 지문 내용 기반 한글 제목(먼저 생성)
    title_en: str = ""       # title_ko 를 그대로 옮긴 영문 제목(뒤에 생성)
    summary: str = ""        # 지문 주제 한 문장 — 분석 페이지 상단 박스(첫 줄)
    summary_easy: str = ""   # '쉽게 말하면' 실생활 예시 한 문장 — 상단 박스(둘째 줄)
    vocab: list[VocabSpec] = Field(default_factory=list)
    flow: list[FlowSpec] = Field(default_factory=list)
    implicit: list[ImplicitSpec] = Field(default_factory=list)   # 출제 포인트·함축의미


# ---------------------------------------------------------------------------
# literal_builder: 직독직해(레이아웃 B) — 의미 단위 청크 + 핵심 문법 + 핵심 단어
# ---------------------------------------------------------------------------
class KeyWordSpec(BaseModel):
    word: str
    meaning: str


class ChunkSpec(BaseModel):
    english: str                  # 의미 단위(‘/’로 끊는) 영어 청크
    korean: str                   # 그 청크의 직독직해(한글)
    words: list[KeyWordSpec] = Field(default_factory=list)  # 이 청크의 핵심 단어


class GrammarChipSpec(BaseModel):
    point: str                    # 어법 이름(예: '과거분사 후치수식')
    explanation: str = ""         # 짧은 설명
    key: bool = False             # ★필수 어법 여부


class LiteralSentenceSpec(BaseModel):
    no: int
    chunks: list[ChunkSpec] = Field(default_factory=list)
    grammar: list[GrammarChipSpec] = Field(default_factory=list)
    note: str = ""                # '쉽게' 요약 한 줄(선택)


class LiteralBundle(BaseModel):
    sentences: list[LiteralSentenceSpec] = Field(default_factory=list)
