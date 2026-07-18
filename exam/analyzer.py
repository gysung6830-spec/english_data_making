"""분석기 (명세서 §6): 지문 1회 분석 — 6종이 나눠 쓴다.

문장 분리 · 핵심어휘+유의어+반의어 · 주제 한 문장 · 문법 밀집 문장을 추출한다.

중요(정확성): 문제의 '바탕 지문'은 AI 출력이 아니라 '사용자가 넣은 원문'을 그대로
쓴다. 즉 sentences 는 입력 지문을 코드가 문장 단위로 나눈 것으로 강제 교체하여,
AI 가 지문을 바꿔 말하더라도 넣은 지문으로만 문제가 만들어지도록 한다.
"""
from __future__ import annotations

import re

from .llm import SYSTEM, ClaudeClient
from .schemas import Analysis

_PROMPT = """다음 영어 지문을 1회 분석하여 JSON 으로 반환하세요.
이 분석 결과는 순서·삽입·주제·어휘·어법·내용일치·서술형 문제 생성에 공용으로 쓰입니다.

- title: 지문에 어울리는 짧은 제목(한국어 가능).
- sentences: 지문을 문장 단위로 순서대로 나눈 배열(원문 그대로, 절대 바꾸지 말 것).
- main_idea: 지문의 주제를 담은 한 문장(영어).
- key_terms: 지문 핵심어 8~14개. 각 항목은 word(원문 형태), synonym(유의어),
  antonym(반의어, 없으면 빈 문자열). word 는 반드시 지문에 실제로 등장하는 단어여야 함.
- hardest_sentence: 문법 요소가 가장 많은(가장 어려운) 문장 1개(원문 그대로).

[지문]
{body}
"""

# 문장 경계: 마침표/물음표/느낌표 뒤 공백 + (대문자/따옴표/괄호) 시작
_SENT_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'(\[])')


def split_sentences(text: str) -> list[str]:
    """지문 원문을 문장 단위로 나눈다(공백 정규화 포함)."""
    norm = " ".join((text or "").split())
    parts = _SENT_BOUNDARY.split(norm)
    return [p.strip() for p in parts if p.strip()]


def analyze(client: ClaudeClient, body: str, max_retries: int = 1) -> Analysis:
    analysis = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(body=body.strip()),
        model_cls=Analysis,
        max_tokens=4000,
        max_retries=max_retries,
    )
    # 바탕 지문은 반드시 '넣은 원문'을 쓴다(AI 가 지문을 바꿔 말해도 무시).
    real = split_sentences(body)
    if len(real) >= 4:
        analysis.sentences = real
    return analysis
