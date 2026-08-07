"""지문 -> 단일 유형 산문 워크시트 데이터 생성 (LLM 호출 + 검증)."""
from __future__ import annotations

from . import prose_prompts as pp
from . import prose_render as pr
from .client import ClaudeClient
from .config import Config
from .schemas import Extraction


def generate_prose_pack(client: ClaudeClient, cfg: Config, extraction: Extraction,
                        header: str = "", verify_vocab: bool | None = None) -> pr.ProsePack:
    """추출된 지문 -> 어법·어형·어휘·한글해석 4종을 담은 렌더용 ProsePack.

    verify_vocab 가 True(기본: config 값)면 어휘(상) 문항을 별도 저비용 LLM 으로
    교차검증해 '정답이 정확히 2개가 아닌' 출제오류 소지 문항을 자동 제외한다.
    """
    title, body = extraction.title, extraction.body
    llm = client.structured(
        system=pp.SYSTEM,
        prompt=pp.prose_prompt(title, body),
        model_cls=pr.LLMProsePack,
        max_tokens=16000,   # 6종×문장×(어법/어휘 2~4개) → 출력이 큼(잘리면 client 가 자동 증량)
        max_retries=max(2, cfg.processing.max_retries),
        extra_validate=pr.validate_llm_prose,
    )
    do_verify = cfg.processing.verify_vocab if verify_vocab is None else verify_vocab
    if do_verify:
        from . import vocab_verify
        llm = vocab_verify.verify_vocab_pack(client, cfg, llm)
    subtitle = extraction.source or "단일 유형 산문 워크시트"
    return pr.build_prose_pack(llm, header=header or title,
                               title=title, subtitle=subtitle)
