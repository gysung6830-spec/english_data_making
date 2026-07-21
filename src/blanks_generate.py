"""지문 -> 빈칸형 워크북 생성 (LLM 호출 + 검증 + 채번)."""
from __future__ import annotations

from . import blanks_prompts as bp
from . import blanks_schemas as bs
from .client import ClaudeClient
from .config import Config
from .schemas import Extraction


def generate_blank_set(client: ClaudeClient, cfg: Config, extraction: Extraction) -> bs.LLMBlankSet:
    """추출된 지문 -> 검증된 LLMBlankSet 한 개(한 지문)."""
    title, body = extraction.title, extraction.body
    st = client.structured(
        system=bp.SYSTEM,
        prompt=bp.blanks_prompt(title, body),
        model_cls=bs.LLMBlankSet,
        max_tokens=8000,
        max_retries=max(2, cfg.processing.max_retries),
        extra_validate=lambda s: bs.validate_llm_blank_workbook(bs.LLMBlankWorkbook(sets=[s])),
    )
    st.no = 1
    if not st.title:
        st.title = title
    return st


def generate_blank_workbook(client: ClaudeClient, cfg: Config, extraction: Extraction) -> bs.BlankWorkbook:
    """단일 지문 -> 렌더용 BlankWorkbook."""
    st = generate_blank_set(client, cfg, extraction)
    llm = bs.LLMBlankWorkbook(sets=[st])
    return bs.build_blank_workbook(
        llm, title=extraction.title, subtitle=st.subtitle or (extraction.source or ""))
