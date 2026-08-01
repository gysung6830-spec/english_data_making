"""지문 -> 영작 워크북 데이터 생성 (LLM 호출 + 검증)."""
from __future__ import annotations

from . import writing_prompts as wp
from . import writing_render as wr
from .client import ClaudeClient
from .config import Config
from .schemas import Extraction


def generate_writing_pack(client: ClaudeClient, cfg: Config, extraction: Extraction,
                          header: str = "") -> wr.WritingPack:
    """추출된 지문 -> 문장별 '영작 포인트 배열'을 담은 렌더용 WritingPack."""
    title, body = extraction.title, extraction.body
    llm = client.structured(
        system=wp.SYSTEM,
        prompt=wp.writing_prompt(title, body),
        model_cls=wr.LLMWritingPack,
        max_tokens=12000,
        max_retries=max(2, cfg.processing.max_retries),
        extra_validate=wr.validate_llm_writing,
    )
    subtitle = extraction.source or "영작 포인트 배열 연습"
    return wr.build_writing_pack(llm, header=header or title,
                                 title=title, subtitle=subtitle)
