"""폴더 단위 처리 오케스트레이션 (동기 모드 + 목 모드)."""
from __future__ import annotations

import re
from pathlib import Path

from . import analyze, extract, render
from .client import ClaudeClient
from .config import Config
from .logutil import Manifest, setup_logging
from .schemas import Report


INPUT_EXTS = {".pdf"} | extract.IMAGE_EXTS


def list_pdfs(input_dir: Path) -> list[Path]:
    """PDF 와 이미지(사진/캡처) 파일을 모두 처리 대상으로 수집."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in INPUT_EXTS
    )


def _safe_stem(path: Path) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", path.stem).strip() or "passage"


def build_reports_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> list[Report]:
    """실제 API 를 사용해 한 파일(PDF/사진) -> 여러 Report(지문 순서대로)."""
    if extract.is_image(src):
        pset = analyze.extract_passages_image(client, cfg, str(src))
    else:
        raw = extract.extract_passage_text(src)
        if extract.looks_empty(raw):
            raise ValueError(
                "텍스트를 추출하지 못했습니다(스캔본 PDF일 수 있음). "
                "이 경우 해당 페이지를 사진(JPG/PNG)으로 저장해 넣어 주세요."
            )
        pset = analyze.extract_passages(client, cfg, raw)
    return [analyze.analyze_passage(client, cfg, ex) for ex in pset.passages]


# 하위 호환용 별칭(단일 Report 반환)
def build_report_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> Report:
    return build_reports_for_pdf(client, cfg, src)[0]


def _mock_reports_for_pdf(cfg: Config, pdf: Path) -> list[Report]:
    """목 모드: 실제 API 없이 샘플 Report(들)를 반환."""
    from samples.sample_mock import mock_report

    title = _safe_stem(pdf)
    if not extract.is_image(pdf):
        try:
            raw = extract.extract_passage_text(pdf)
            first = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
            if first and len(first) < 80:
                title = first
        except Exception:
            pass
    return [mock_report(title=title, source=f"{pdf.name}")]


def _mock_report_for_pdf(cfg: Config, pdf: Path) -> Report:
    return _mock_reports_for_pdf(cfg, pdf)[0]


def run_folder(cfg: Config, mock: bool = False) -> dict:
    """input 폴더의 모든 PDF 를 처리해 output 에 PDF 를 생성."""
    logger = setup_logging(cfg.logs_dir)
    manifest = Manifest(cfg.logs_dir)
    pdfs = list_pdfs(cfg.input_dir)
    total = len(pdfs)

    if total == 0:
        logger.warning("input 폴더에 PDF 가 없습니다: %s", cfg.input_dir)
        return {"total": 0, "success": 0, "failed": 0, "outputs": []}

    client: ClaudeClient | None = None
    if not mock:
        if not cfg.has_api_key:
            raise SystemExit(
                "ANTHROPIC_API_KEY 가 설정되지 않았습니다. .env 파일에 키를 입력하거나 "
                "--mock 옵션으로 디자인만 미리 확인하세요."
            )
        client = ClaudeClient(cfg.api_key, cfg.model)

    logger.info("총 %d개 지문 처리 시작 (%s 모드)", total, "MOCK" if mock else "API")

    outputs: list[Path] = []
    success = failed = 0
    for i, pdf in enumerate(pdfs, start=1):
        try:
            reports = (_mock_reports_for_pdf(cfg, pdf) if mock
                       else build_reports_for_pdf(client, cfg, pdf))
            out = cfg.output_dir / f"{_safe_stem(pdf)}_analysis.pdf"
            render.render_pdf(reports, out, footer_note=cfg.design.footer_note,
                              min_vocab=cfg.vocab.min)
            outputs.append(out)
            manifest.record_success(str(pdf), str(out), {"passages": len(reports)})
            success += 1
            logger.info("[%d/%d] 완료: %s (지문 %d개) -> %s",
                        i, total, pdf.name, len(reports), out.name)
        except Exception as e:  # 개별 실패가 전체를 멈추지 않게
            failed += 1
            manifest.record_failure(str(pdf), str(e))
            logger.error("[%d/%d] 실패: %s (%s)", i, total, pdf.name, e)

    # 하나의 PDF 로 합치기 옵션
    if outputs and not cfg.design.one_pdf_per_passage:
        combined = cfg.output_dir / "ALL_passages_analysis.pdf"
        render.combine_pdfs(outputs, combined)
        logger.info("합본 PDF 생성: %s", combined.name)

    logger.info("처리 요약 — 성공 %d, 실패 %d (총 %d)", success, failed, total)
    return {"total": total, "success": success, "failed": failed,
            "outputs": [str(o) for o in outputs]}
