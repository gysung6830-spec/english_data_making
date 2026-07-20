"""LLM 구조화 응답 스키마 (pydantic).

analyzer / point_builder 가 Claude 에게 요청할 때 강제하는 JSON 형식.
src/client.py 의 structured() 가 이 스키마로 검증한다. 검증을 통과한 객체는
models.py 의 dataclass(Token/Sentence/Point)로 변환된다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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


class LineSpec(BaseModel):
    tokens: list[TokenSpec] = Field(default_factory=list)


class SentenceAnalysis(BaseModel):
    """한 문장의 태깅 + 해석."""

    lines: list[LineSpec] = Field(default_factory=list)
    translation: str = ""
    badge: str = ""         # '빈'(빈출)·'서'(서술형) 등 짧은 뱃지. 없으면 빈 문자열
    gloss_en: str = ""      # 함축 의미 영어 한 줄(맥락 없이 안 풀리는 문장에만). 없으면 빈 문자열


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


class OverviewBundle(BaseModel):
    vocab: list[VocabSpec] = Field(default_factory=list)
    flow: list[FlowSpec] = Field(default_factory=list)
