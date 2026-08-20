"""AI 연결기 (명세서 §6): 생성기가 Claude API 에 질문하는 통로.

기존 분석 도구의 src.client.ClaudeClient 를 그대로 재사용한다.
- output_config 로 JSON 형식을 강제하고 pydantic 으로 재검증/재시도한다.
"""
from __future__ import annotations

from src.client import ClaudeClient as _BaseClient  # 구조화 JSON + 검증 + 재시도 래퍼 재사용

from ._concurrent import api_slot

__all__ = ["ClaudeClient"]


class ClaudeClient(_BaseClient):
    """API 호출에 '전체 동시 실행 상한'을 씌운 클라이언트.

    지문·유형·회차를 여러 겹으로 병렬 처리해도 실제로 동시에 나가는 호출 수는
    _concurrent.API_CONCURRENCY 로 묶인다. 덕분에 바깥 루프를 마음껏 병렬화해
    유휴 시간(한 지문의 마지막 호출을 기다리며 노는 시간)을 없애면서도
    레이트리밋을 넘지 않는다.
    """

    def structured(self, *args, **kwargs):
        with api_slot():
            return super().structured(*args, **kwargs)

# 시험지 생성 전반에 공통으로 붙이는 시스템 지시
SYSTEM = (
    "당신은 한국 고등학교 영어 내신·모의고사 출제 전문가입니다. "
    "주어진 영어 지문으로 수능형 변형문제를 만듭니다. "
    "원본 문제를 복제하지 말고, 넣은 지문으로 같은 유형의 새 문제를 생성하세요. "
    "반드시 요청된 JSON 스키마에 정확히 맞춰 응답하고, 개수·범위 조건을 지키세요. "
    "해설(reason)은 한국어로, 정답 근거와 오답이 틀린 이유까지 구체적으로 쓰세요."
)
