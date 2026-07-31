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
from .pipeline import _safe_stem, list_pdfs

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
    client = ClaudeClient(cfg.api_key, model,
                          thinking=cfg.processing.thinking, effort=cfg.processing.effort)

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
                                            prompts.extract_image_prompt(), schemas.Extraction,
                                            image_path=str(pdf)),
                })
            else:
                raw = extract.extract_passage_text(pdf)
                if extract.looks_empty(raw):
                    raise ValueError("텍스트 추출 실패(스캔본 PDF는 사진으로 저장해 주세요)")
                extract_reqs.append({
                    "custom_id": f"{fid}__extract",
                    "params": build_request(model, prompts.EXTRACT_SYSTEM,
                                            prompts.extract_prompt(raw), schemas.Extraction),
                })
        except Exception as e:
            failed[fid] = f"extract-pre: {e}"

    res1 = _submit_and_collect(client, extract_reqs, logger)
    extractions: dict[str, schemas.Extraction] = {}
    for fid in list(files):
        if fid in failed:
            continue
        text = res1.get(f"{fid}__extract")
        try:
            extractions[fid] = parse_response_text(text or "", schemas.Extraction)
        except Exception as e:
            failed[fid] = f"extract: {e}"

    # ---- 2단계: 5개 섹션 ----
    lo, hi = cfg.vocab.min, cfg.vocab.max
    sec_reqs = []
    section_specs = {
        "summary": (schemas.SummarySection, lambda t, b: prompts.summary_prompt(t, b)),
        "literal": (schemas.LiteralSection, lambda t, b: prompts.literal_prompt(t, b)),
        "grammar": (schemas.GrammarSection, lambda t, b: prompts.grammar_prompt(t, b)),
        "vocab": (schemas.VocabSection, lambda t, b: prompts.vocab_prompt(t, b, lo, hi)),
        "structure": (schemas.StructureSection, lambda t, b: prompts.structure_prompt(t, b)),
    }
    for fid, ex in extractions.items():
        for name, (cls, mk) in section_specs.items():
            mt = 12000 if name == "literal" else 8000
            sec_reqs.append({
                "custom_id": f"{fid}__{name}",
                "params": build_request(model, prompts.SYSTEM, mk(ex.title, ex.body), cls, mt),
            })
    res2 = _submit_and_collect(client, sec_reqs, logger)

    parsed: dict[str, dict[str, object]] = {fid: {} for fid in extractions}
    for fid, ex in extractions.items():
        for name, (cls, _mk) in section_specs.items():
            text = res2.get(f"{fid}__{name}")
            try:
                parsed[fid][name] = parse_response_text(text or "", cls)
            except Exception as e:
                failed.setdefault(fid, f"{name}: {e}")

    # ---- 3단계: 출제 포인트 (문법·어휘 참고) ----
    exam_reqs = []
    for fid, ex in extractions.items():
        if fid in failed:
            continue
        g = parsed[fid].get("grammar")
        v = parsed[fid].get("vocab")
        exam_reqs.append({
            "custom_id": f"{fid}__exam",
            "params": build_request(model, prompts.SYSTEM,
                                    prompts.exam_prompt(ex.title, ex.body, g, v),
                                    schemas.ExamSection),
        })
    res3 = _submit_and_collect(client, exam_reqs, logger)

    # ---- 조립 + 렌더 ----
    success = 0
    outputs: list[Path] = []
    for fid, ex in extractions.items():
        if fid in failed:
            continue
        try:
            exam = parse_response_text(res3.get(f"{fid}__exam") or "", schemas.ExamSection)
            report = schemas.Report(
                title=ex.title, source=ex.source,
                summary=parsed[fid]["summary"], literal=parsed[fid]["literal"],
                grammar=parsed[fid]["grammar"], vocab=parsed[fid]["vocab"],
                structure=parsed[fid]["structure"], exam=exam,
            )
            pdf = files[fid]
            out = cfg.output_dir / f"{_safe_stem(pdf)}_analysis.pdf"
            render.render_pdf(report, out, footer_note=cfg.design.footer_note)
            outputs.append(out)
            manifest.record_success(str(pdf), str(out))
            success += 1
        except Exception as e:
            failed.setdefault(fid, f"assemble: {e}")

    for fid, err in failed.items():
        manifest.record_failure(str(files[fid]), err)

    if outputs and not cfg.design.one_pdf_per_passage:
        combined = cfg.output_dir / "ALL_passages_analysis.pdf"
        render.combine_pdfs(outputs, combined)

    logger.info("Batch 처리 요약 — 성공 %d, 실패 %d (총 %d)", success, len(failed), total)
    logger.info("실패 파일은 logs/failed.jsonl 참고. 동기 모드(python run.py)로 재시도 가능.")
    return {"total": total, "success": success, "failed": len(failed),
            "outputs": [str(o) for o in outputs]}
