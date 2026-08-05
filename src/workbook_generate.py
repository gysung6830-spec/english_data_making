"""지문 -> 통합 워크북 생성 (LLM 호출 + 검증 + 채번).

spec 4-2 동작 순서 중 3~5단계를 담당한다.
  3. 분석·출제 : 지문을 LLM 에 넣어 LLMWorkbook JSON 을 받는다.
  5. 검증      : 자리표시자 1:1 대응·번호 정합성 검증(실패 시 재요청).
  4. 채번      : 전역 연속 번호 부여 + total 집계 -> 렌더용 Workbook.
"""
from __future__ import annotations

from . import workbook_prompts as wp
from . import workbook_schemas as ws
from .client import ClaudeClient
from .config import Config
from .schemas import Extraction


def generate_workbook(client: ClaudeClient, cfg: Config, extraction: Extraction) -> ws.Workbook:
    """추출된 지문 -> 검증·채번을 마친 렌더용 Workbook."""
    title, body = extraction.title, extraction.body
    llm = client.structured(
        system=wp.SYSTEM,
        prompt=wp.workbook_prompt(title, body),
        model_cls=ws.LLMWorkbook,
        max_tokens=12000,
        max_retries=max(2, cfg.processing.max_retries),
        extra_validate=ws.validate_llm_workbook,   # 자리표시자·questions 개수 검증
    )
    subtitle = extraction.source or "문장별 복합유형 통합 워크북"
    from .textutil import split_sentences
    return ws.build_workbook(llm, title=title, subtitle=subtitle,
                             originals=split_sentences(body))
