"""지문 -> 단일 유형 산문 워크시트 데이터 생성 (LLM 호출 + 검증)."""
from __future__ import annotations

from . import prose_prompts as pp
from . import prose_render as pr
from .client import ClaudeClient
from .config import Config
from .schemas import Extraction


def generate_prose_pack(client: ClaudeClient, cfg: Config, extraction: Extraction,
                        header: str = "") -> pr.ProsePack:
    """추출된 지문 -> 어법·어형·어휘·한글해석 4종을 담은 렌더용 ProsePack."""
    title, body = extraction.title, extraction.body
    llm = client.structured(
        system=pp.SYSTEM,
        prompt=pp.prose_prompt(title, body),
        model_cls=pr.LLMProsePack,
        max_tokens=12000,
        max_retries=max(2, cfg.processing.max_retries),
        extra_validate=pr.validate_llm_prose,
    )
    subtitle = extraction.source or "단일 유형 산문 워크시트"
    return pr.build_prose_pack(llm, header=header or title,
                               title=title, subtitle=subtitle)
