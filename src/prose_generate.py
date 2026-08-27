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
    # 6종 mega-call 이 이따금 degenerate 하게 '1문장'만 반환해 모든 유형 워크시트가 통째로
    # 비는 사고가 있었다. 지문 문장 수의 80% 이상은 반드시 담기게 검증해 부족하면 재요청한다.
    from .textutil import split_sentences
    expected = len(split_sentences(body))
    # 0.7 배: LLM 의 문장 분할이 우리와 조금 달라도(±) 헛재시도가 없게 여유를 두되,
    # '41문장 → 1문장' 같은 붕괴는 확실히 잡히는 선.
    min_sentences = max(1, int(expected * 0.7))
    llm = client.structured(
        system=pp.SYSTEM,
        prompt=pp.prose_prompt(title, body),
        model_cls=pr.LLMProsePack,
        max_tokens=16000,   # 6종×문장×(어법/어휘 2~4개) → 출력이 큼(잘리면 client 가 자동 증량)
        max_retries=max(2, cfg.processing.max_retries),
        extra_validate=lambda p: pr.validate_llm_prose(p, min_sentences=min_sentences),
    )
    _ensure_ref(client, cfg, extraction, llm)
    _ensure_counts(client, cfg, extraction, llm)
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
    # ★ raw 개수가 아니라 'render 가드를 통과해 실제로 출제될' 지칭 수로 판단한다.
    #   mega-call 이 지칭을 냈어도 전부 가주어·오류라 render 에서 버려지면 최종 워크시트가
    #   비므로, 그 경우까지 폴백이 켜지도록 renderable 수를 센다.
    if pr.renderable_ref_count(llm) >= _REF_MIN:
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
        # 그 문장에 '이미 출제 가능한(render 통과) 지칭'이 있으면 덮지 않는다. 비었거나
        # 기존 지칭이 전부 버려질 것(renderable 0)이면 폴백 결과로 채운다.
        if pr.renderable_ref_items(tgt):
            continue
        tgt.ref_template = rs.ref_template or tgt.ref_template
        tgt.ref_items = rs.ref_items


# 어법·어휘(하/상)에서 문장당 최소 개수(2) 미달 문장이 있으면, 부족한 문장만 top-up 재요청으로 채운다.
_COUNT_MIN = 2
_COUNT_ATTRS = {"grammar": ("grammar_template", "grammar_items"),
                "vocab": ("vocab_template", "vocab_items"),
                "vocab_easy": ("vocab_easy_template", "vocab_easy_items")}


def _ensure_counts(client: ClaudeClient, cfg: Config, extraction: Extraction,
                   llm: pr.LLMProsePack) -> None:
    """어법·어휘(하/상)의 '문장당 최소 2개' 미달을 top-up 재요청으로 보강한다(부작용: llm 수정).

    - 억지 생성(코드 조작)이 아니라 LLM 에 한 번 더 요청해 '채울 수 있는' 문장만 채운다.
      진짜 낼 게 없는 짧은 문장은 재요청해도 안 나오므로 그대로 둔다(규칙상 1개 예외 허용).
    - 우리 필터가 '틀린 문제'를 걸러 생긴 빈자리는 top-up 이 더 많은 문항을 줄 때만 교체한다.
    - 실패(예외)해도 기존 결과를 유지(fail-open).
    """
    # 렌더 가드까지 통과한 '실제 출제 수'로 미달 판단(raw 개수가 아님).
    pack = pr.build_prose_pack(llm, "", "", "")
    sf = pr.count_shortfalls(pack, min_per=_COUNT_MIN)
    if not sf:
        return
    need = {(wt, no) for wt, lst in sf.items() for no, _ in lst}
    try:
        top = client.structured(
            system=pp.SYSTEM,
            prompt=pp.prose_prompt(extraction.title, extraction.body),
            model_cls=pr.LLMProsePack,
            max_tokens=16000,
            max_retries=1,
        )
    except Exception:
        return
    by_no = {s.no: s for s in llm.sentences}
    by_en = {s.en.strip(): s for s in llm.sentences}
    for ts in top.sentences:
        tgt = by_no.get(ts.no) or by_en.get(ts.en.strip())
        if tgt is None:
            continue
        for wt, (tkey, ikey) in _COUNT_ATTRS.items():
            if (wt, tgt.no) not in need:
                continue
            new_items = getattr(ts, ikey)
            # top-up 이 '더 많은' 문항을 줄 때만 template+items 를 함께 교체(정합 유지).
            if len(new_items) > len(getattr(tgt, ikey)):
                setattr(tgt, tkey, getattr(ts, tkey) or getattr(tgt, tkey))
                setattr(tgt, ikey, new_items)
