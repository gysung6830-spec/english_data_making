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
    above: str = ""         # 토큰 위 메모 (예: 'it is 생략')
    hl: Literal["", "y", "g"] = ""   # 하이라이트: 없음/노랑/연두
    underline: bool = False
    color: Literal["", "red", "blue"] = ""


class LineSpec(BaseModel):
    tokens: list[TokenSpec] = Field(default_factory=list)


class SentenceAnalysis(BaseModel):
    """한 문장의 태깅 + 해석."""

    lines: list[LineSpec] = Field(default_factory=list)
    translation: str = ""
    badge: str = ""         # '순/삽','서','예시','결론' 등. 없으면 빈 문자열


# ---------------------------------------------------------------------------
# point_builder: 문장 1개의 독해/어법 포인트
# ---------------------------------------------------------------------------
class PointSpec(BaseModel):
    kind: Literal["reading", "grammar"]
    caption: str
    body_html: str          # 신뢰된 간단 HTML(리스트/표 허용). 굵게=<b>, 목록=<ul><li>


class PointBundle(BaseModel):
    points: list[PointSpec] = Field(default_factory=list)
