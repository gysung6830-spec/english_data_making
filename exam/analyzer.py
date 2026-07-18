"""분석기 (명세서 §6): 지문 1회 분석 — 6종이 나눠 쓴다.

문장 분리 · 핵심어휘+유의어+반의어 · 주제 한 문장 · 문법 밀집 문장을 추출한다.
"""
from __future__ import annotations

from .llm import SYSTEM, ClaudeClient
from .schemas import Analysis

_PROMPT = """다음 영어 지문을 1회 분석하여 JSON 으로 반환하세요.
이 분석 결과는 순서·삽입·주제·어휘·어법·서술형 6종 문제 생성에 공용으로 쓰입니다.

- title: 지문에 어울리는 짧은 제목(한국어 가능).
- sentences: 지문을 문장 단위로 순서대로 나눈 배열(원문 그대로).
- main_idea: 지문의 주제를 담은 한 문장(영어).
- key_terms: 지문 핵심어 8~14개. 각 항목은 word(원문 형태), synonym(유의어),
  antonym(반의어, 없으면 빈 문자열).
- hardest_sentence: 문법 요소가 가장 많은(가장 어려운) 문장 1개(원문 그대로).

[지문]
{body}
"""


def analyze(client: ClaudeClient, body: str, max_retries: int = 1) -> Analysis:
    return client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(body=body.strip()),
        model_cls=Analysis,
        max_tokens=4000,
        max_retries=max_retries,
    )
