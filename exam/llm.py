"""AI 연결기 (명세서 §6): 생성기가 Claude API 에 질문하는 통로.

기존 분석 도구의 src.client.ClaudeClient 를 그대로 재사용한다.
- output_config 로 JSON 형식을 강제하고 pydantic 으로 재검증/재시도한다.
"""
from __future__ import annotations

from src.client import ClaudeClient  # 구조화 JSON + 검증 + 재시도 래퍼 재사용

__all__ = ["ClaudeClient"]

# 시험지 생성 전반에 공통으로 붙이는 시스템 지시
SYSTEM = (
    "당신은 한국 고등학교 영어 내신·모의고사 출제 전문가입니다. "
    "주어진 영어 지문으로 수능형 변형문제를 만듭니다. "
    "원본 문제를 복제하지 말고, 넣은 지문으로 같은 유형의 새 문제를 생성하세요. "
    "반드시 요청된 JSON 스키마에 정확히 맞춰 응답하고, 개수·범위 조건을 지키세요. "
    "해설(reason)은 한국어로, 정답 근거와 오답이 틀린 이유까지 구체적으로 쓰세요."
)
