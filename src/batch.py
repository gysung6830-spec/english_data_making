"""대량 처리용 Batch API 모드 (비용 절감 + 안정성).

한 지문당 6개 섹션이 서로 의존(⑥ 출제는 ③④ 참고)하므로 3단계 배치로 나눈다.
  1단계: 본문 추출(extract)
  2단계: 요약/직독직해/문법/어휘/구조 (5개)
  3단계: 출제 포인트 (문법·어휘 결과 참고)
각 단계 안에서는 파일들을 한 번에 배치로 제출한다.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import extract, prompts, render, schemas
from .client import ClaudeClient, build_request, parse_response_text
from .config import Config
from .logutil import Manifest, setup_logging
from .pipeline import _safe_stem, list_pdfs, render_outputs

POLL_SECONDS = 30


def _submit_and_collect(client: ClaudeClient, reqs: list[dict], logger) -> dict[str, str]:
    """[{custom_id, params}] 를 배치 제출하고 custom_id -> 응답텍스트(성공만) 반환."""
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    if not reqs:
        return {}
    batch = client.raw.messages.batches.create(
        requests=[
            Request(custom_id=r["custom_id"],
                    params=MessageCreateParamsNonStreaming(**r["params"]))
            for r in reqs
        ]
    )
    logger.info("배치 제출: %s (%d건)", batch.id, len(reqs))
    while True:
        b = client.raw.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        logger.info("  처리 중... (%s)", b.request_counts)
        time.sleep(POLL_SECONDS)

    out: dict[str, str] = {}
    for result in client.raw.messages.batches.results(batch.id):
        if result.result.type == "succeeded":
            msg = result.result.message
            text = next((b.text for b in msg.content if b.type == "text"), "")
            out[result.custom_id] = text
    logger.info("배치 완료: 성공 %d / %d", len(out), len(reqs))
    return out


def run_folder_batch(cfg: Config, model: str) -> dict:
    logger = setup_logging(cfg.logs_dir)
    manifest = Manifest(cfg.logs_dir)
    if not cfg.has_api_key:
        raise SystemExit("ANTHROPIC_API_KEY 가 필요합니다.")
    client = ClaudeClient(cfg.api_key, model)

    pdfs = list_pdfs(cfg.input_dir)
    total = len(pdfs)
    if total == 0:
        logger.warning("input 폴더에 PDF 가 없습니다.")
        return {"total": 0, "success": 0, "failed": 0}

    logger.info("Batch 모드: 총 %d개 지문", total)
    files = {f"f{idx}": pdf for idx, pdf in enumerate(pdfs)}
    failed: dict[str, str] = {}

    # ---- 1단계: 추출 ----
    extract_reqs = []
    for fid, pdf in files.items():
        try:
            if extract.is_image(pdf):
                # 사진/캡처 → 비전 추출 요청
                extract_reqs.append({
                    "custom_id": f"{fid}__extract",
                    "params": build_request(model, prompts.EXTRACT_SYSTEM,
                                            prompts.extract_image_prompt(), schemas.PassageSet,
                                            image_path=str(pdf)),
                })
            else:
                raw = extract.extract_passage_text(pdf)
                if extract.looks_empty(raw):
                    raise ValueError("텍스트 추출 실패(스캔본 PDF는 사진으로 저장해 주세요)")
                extract_reqs.append({
                    "custom_id": f"{fid}__extract",
                    "params": build_request(model, prompts.EXTRACT_SYSTEM,
                                            prompts.extract_prompt(raw), schemas.PassageSet),
                })
        except Exception as e:
            failed[fid] = f"extract-pre: {e}"

    res1 = _submit_and_collect(client, extract_reqs, logger)
    # units: (fid, pidx) -> Extraction  (한 파일에 여러 지문 가능)
    units: dict[tuple[str, int], schemas.Extraction] = {}
    file_units: dict[str, list[int]] = {}
    for fid in list(files):
        if fid in failed:
            continue
        text = res1.get(f"{fid}__extract")
        try:
            pset = parse_response_text(text or "", schemas.PassageSet)
            for pidx, ex in enumerate(pset.passages):
                units[(fid, pidx)] = ex
                file_units.setdefault(fid, []).append(pidx)
        except Exception as e:
            failed[fid] = f"extract: {e}"

    # ---- 2단계: 지문별 섹션(분석지용 5개) + 서술형 교재용 6개 유형 ----
    #   분석지/어휘/시험지가 필요하면 5개 섹션을, 서술형 교재가 필요하면 6개 유형을 요청.
    need_report = cfg.outputs.needs_report
    need_ws = cfg.outputs.worksheet
    lo, hi = cfg.vocab.min, cfg.vocab.max
    sec_reqs = []
    section_specs = {
        "summary": (schemas.SummarySection, lambda t, b: prompts.summary_prompt(t, b)),
        "literal": (schemas.LiteralSection, lambda t, b: prompts.literal_prompt(t, b)),
        "grammar": (schemas.GrammarSection, lambda t, b: prompts.grammar_prompt(t, b)),
        "vocab": (schemas.VocabSection, lambda t, b: prompts.vocab_prompt(t, b, lo, hi)),
        "structure": (schemas.StructureSection, lambda t, b: prompts.structure_prompt(t, b)),
    }
    # 서술형 교재 6개 유형: (스키마, 프롬프트, max_tokens)
    ws_specs = {
        "ws_summary": (schemas.WSSummaryType, prompts.ws_summary_prompt, 8000),
        "ws_paraphrase": (schemas.WSParaphraseType, prompts.ws_paraphrase_prompt, 10000),
        "ws_arrange": (schemas.WSArrangeType, prompts.ws_arrange_prompt, 8000),
        "ws_compose": (schemas.WSComposeType, prompts.ws_compose_prompt, 8000),
        "ws_choice": (schemas.WSChoiceType, prompts.ws_choice_prompt, 10000),
        "ws_error": (schemas.WSErrorType, prompts.ws_error_prompt, 8000),
        "ws_qa": (schemas.WSQAType, prompts.ws_qa_prompt, 8000),
    }
    for (fid, pidx), ex in units.items():
        if need_report:
            for name, (cls, mk) in section_specs.items():
                mt = 12000 if name == "literal" else 8000
                sec_reqs.append({
                    "custom_id": f"{fid}__{pidx}__{name}",
                    "params": build_request(model, prompts.SYSTEM, mk(ex.title, ex.body), cls, mt),
                })
        if need_ws:
            for name, (cls, mk, mt) in ws_specs.items():
                sec_reqs.append({
                    "custom_id": f"{fid}__{pidx}__{name}",
                    "params": build_request(model, prompts.WS_SYSTEM, mk(ex.title, ex.body), cls, mt),
                })
    res2 = _submit_and_collect(client, sec_reqs, logger)

    parsed: dict[tuple[str, int], dict[str, object]] = {k: {} for k in units}
    for (fid, pidx), ex in units.items():
        specs = {}
        if need_report:
            specs.update({n: c for n, (c, _m) in section_specs.items()})
        if need_ws:
            specs.update({n: c for n, (c, _m, _t) in ws_specs.items()})
        for name, cls in specs.items():
            text = res2.get(f"{fid}__{pidx}__{name}")
            try:
                parsed[(fid, pidx)][name] = parse_response_text(text or "", cls)
            except Exception as e:
                failed.setdefault(fid, f"p{pidx}/{name}: {e}")

    # ---- 3단계: 지문별 출제 포인트 (분석지가 필요할 때만) ----
    exam_reqs = []
    if need_report:
        for (fid, pidx), ex in units.items():
            if fid in failed:
                continue
            g = parsed[(fid, pidx)].get("grammar")
            v = parsed[(fid, pidx)].get("vocab")
            exam_reqs.append({
                "custom_id": f"{fid}__{pidx}__exam",
                "params": build_request(model, prompts.SYSTEM,
                                        prompts.exam_prompt(ex.title, ex.body, g, v),
                                        schemas.ExamSection),
            })
    res3 = _submit_and_collect(client, exam_reqs, logger)

    # ---- 조립 + 렌더 (파일별로 지문 순서대로, 선택된 종류의 PDF) ----
    success = 0
    outputs: list[Path] = []
    analysis_outputs: list[Path] = []
    for fid in file_units:
        if fid in failed:
            continue
        try:
            reports = []
            worksheets = []
            for pidx in sorted(file_units[fid]):
                ex = units[(fid, pidx)]
                p = parsed[(fid, pidx)]
                if need_report:
                    exam = parse_response_text(
                        res3.get(f"{fid}__{pidx}__exam") or "", schemas.ExamSection)
                    reports.append(schemas.Report(
                        title=ex.title, source=ex.source,
                        summary=p["summary"], literal=p["literal"],
                        grammar=p["grammar"], vocab=p["vocab"],
                        structure=p["structure"], exam=exam,
                    ))
                if need_ws:
                    worksheets.append(schemas.Worksheet(
                        title=ex.title, source=ex.source, passage=ex.body,
                        summary=p["ws_summary"], paraphrase=p["ws_paraphrase"],
                        arrange=p["ws_arrange"], compose=p["ws_compose"],
                        choice=p["ws_choice"], error=p["ws_error"], qa=p["ws_qa"],
                    ))
            pdf = files[fid]
            recs = render_outputs(cfg, reports, _safe_stem(pdf), worksheets=worksheets)
            outputs.extend(r["path"] for r in recs)
            a_paths = [r["path"] for r in recs if r["kind"] == "analysis"]
            analysis_outputs.extend(a_paths)
            manifest.record_success(str(pdf), str(a_paths[0]) if a_paths else "",
                                    {"passages": max(len(reports), len(worksheets)),
                                     "outputs": [r["path"].name for r in recs]})
            success += 1
        except Exception as e:
            failed.setdefault(fid, f"assemble: {e}")

    for fid, err in failed.items():
        manifest.record_failure(str(files[fid]), err)

    if analysis_outputs and not cfg.design.one_pdf_per_passage:
        combined = cfg.output_dir / "ALL_passages_analysis.pdf"
        render.combine_pdfs(analysis_outputs, combined)

    logger.info("Batch 처리 요약 — 성공 %d, 실패 %d (총 %d)", success, len(failed), total)
    logger.info("실패 파일은 logs/failed.jsonl 참고. 동기 모드(python run.py)로 재시도 가능.")
    return {"total": total, "success": success, "failed": len(failed),
            "outputs": [str(o) for o in outputs]}
