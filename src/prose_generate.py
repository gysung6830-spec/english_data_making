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
    _ensure_ref(client, cfg, extraction, llm)
    do_verify = cfg.processing.verify_vocab if verify_vocab is None else verify_vocab
    if do_verify:
        from . import vocab_verify
        llm = vocab_verify.verify_vocab_pack(client, cfg, llm)
    subtitle = extraction.source or "단일 유형 산문 워크시트"
    return pr.build_prose_pack(llm, header=header or title,
                               title=title, subtitle=subtitle)


# 지칭(ref) 문항이 너무 적으면(긴 지문에서 6종 통합 호출이 불안정) 별도 집중 호출로 보강한다.
_REF_MIN = 3


def _ensure_ref(client: ClaudeClient, cfg: Config, extraction: Extraction,
                llm: pr.LLMProsePack) -> None:
    """ref_items 총합이 부족하면 '지칭 전용' LLM 호출로 재생성해 병합한다(부작용: llm 수정).

    통합 6종 호출은 41문장급 장문에서 대명사 지칭을 간헐적으로 0개만 내는 불안정성이 있어,
    ref 문항 수가 기준 미만이면 저렴한 별도 호출로 지칭만 다시 뽑아 문장 단위로 채워 넣는다.
    실패(예외)해도 기존 결과를 유지하도록 fail-open 한다.
    """
    ref_count = sum(len(s.ref_items) for s in llm.sentences)
    if ref_count >= _REF_MIN:
        return
    try:
        ref_llm = client.structured(
            system=pp.REF_SYSTEM,
            prompt=pp.ref_only_prompt(extraction.title, extraction.body),
            model_cls=pr.LLMProsePack,
            max_tokens=8000,
            max_retries=1,
        )
    except Exception:
        return
    by_no = {s.no: s for s in llm.sentences}
    by_en = {s.en.strip(): s for s in llm.sentences}
    for rs in ref_llm.sentences:
        if not rs.ref_items:
            continue
        tgt = by_no.get(rs.no) or by_en.get(rs.en.strip())
        if tgt is None:
            continue
        # 기존에 이미 ref 가 있으면 덮어쓰지 않는다(중복 방지). 비어 있을 때만 채운다.
        if tgt.ref_items:
            continue
        tgt.ref_template = rs.ref_template or tgt.ref_template
        tgt.ref_items = rs.ref_items
