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
        # 해설에 스키마 필드명·작업 용어가 새면 그대로 인쇄된다(실제 결과물에서
        # 'override 문장'·'sent_no=6'·'cues' 가 학생 해설에 찍혔다). 어느 생성기를
        # 거치든 한 곳에서 막도록 여기서 검사하고, 걸리면 기존 재시도가 다시 부른다.
        user = kwargs.get("extra_validate")

        def _guard(out) -> None:
            from . import shape           # 순환 임포트 회피(지연 임포트)
            bad = shape.internal_terms_in(out)
            if bad:
                raise ValueError(
                    "해설에 내부 용어가 들어갔습니다: " + ", ".join(bad)
                    + ". 학생과 선생님이 읽을 말로만 쓰세요(스키마 필드명·작업 용어 금지).")
            if user is not None:
                user(out)

        kwargs["extra_validate"] = _guard
        with api_slot():
            return super().structured(*args, **kwargs)

# 시험지 생성 전반에 공통으로 붙이는 시스템 지시
SYSTEM = (
    "당신은 한국 고등학교 영어 내신·모의고사 출제 전문가입니다. "
    "주어진 영어 지문으로 수능형 변형문제를 만듭니다. "
    "원본 문제를 복제하지 말고, 넣은 지문으로 같은 유형의 새 문제를 생성하세요. "
    "반드시 요청된 JSON 스키마에 정확히 맞춰 응답하고, 개수·범위 조건을 지키세요. "
    "해설(reason)은 한국어로, 정답 근거와 오답이 틀린 이유까지 구체적으로 쓰세요.\n"
    "[해설 쓰는 법 — 모든 유형 공통]\n"
    "· 해설은 '학생과 선생님이 읽는 글'입니다. 스키마 필드명(sent_no·answer_no·"
    "override·cues·choices 등)이나 작업 용어(토큰·플레이스홀더·스키마)를 쓰지 마세요.\n"
    "· 출제 과정을 설명하지 마세요('배열을 조정하였다', '무작위로 섞어 제시했다', "
    "'좋은 삽입 문제 지점이다' 같은 말은 해설이 아니라 개발 메모입니다).\n"
    "· 지문 문장을 '(3)에서'처럼 번호로 지칭하지 마세요. 학생용 지문에는 번호가 없습니다. "
    "필요하면 그 문장을 짧게 인용하세요.\n"
    "· 문체는 '-이다/-한다'로 통일하세요('-습니다'와 섞지 마세요)."
)
