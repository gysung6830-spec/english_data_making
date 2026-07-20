"""구문 분석 학습지 자동 생성기 (지문 분석 학습지).

영어 지문을 문장 단위로 쪼개 '직독직해 + 구문 태깅 + 포인트 박스' 학습지를
HTML/PDF 로 출력한다. 두 가지 레이아웃을 지원한다.

- 레이아웃 A (분석 학습지형) : 벤 리본 + 좌 분석 / 우 포인트 박스
- 레이아웃 B (대조표형)     : 회색 헤더바 + 좌 영어 / 우 한글 2단 표

파이프라인:
    loader → splitter → analyzer(규칙+LLM) → point_builder → renderer → PDF

기존 6개 섹션 분석 도구(src/analyze.py 등)와는 별개의 산출물이며,
입력 로딩(src/extract.py)과 API 클라이언트(src/client.py)만 재사용한다.
"""
from __future__ import annotations

from .models import (Analysis, FlowStep, OutlineItem, Point, Sentence, Token,
                     VocabEntry)

__all__ = ["Analysis", "FlowStep", "OutlineItem", "Point", "Sentence", "Token",
           "VocabEntry"]
