"""폴더 단위 처리 오케스트레이션 (동기 모드 + 목 모드)."""
from __future__ import annotations

import re
from pathlib import Path

from . import analyze, extract, render
from . import workbook_generate, workbook_render
from .client import ClaudeClient
from .config import Config
from .logutil import Manifest, setup_logging
from .schemas import Report
from .workbook_schemas import Workbook


INPUT_EXTS = {".pdf"} | extract.IMAGE_EXTS


def list_pdfs(input_dir: Path) -> list[Path]:
    """PDF 와 이미지(사진/캡처) 파일을 모두 처리 대상으로 수집."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in INPUT_EXTS
    )


def _safe_stem(path: Path) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", path.stem).strip() or "passage"


def _extract_for_pdf(client: ClaudeClient, cfg: Config, src: Path):
    """한 파일(PDF/사진) -> Extraction (지문 본문). 텍스트/이미지 자동 분기."""
    if extract.is_image(src):
        # 사진/캡처 → 비전으로 지문 추출
        return analyze.extract_report_image(client, cfg, str(src))
    raw = extract.extract_passage_text(src)
    if extract.looks_empty(raw):
        raise ValueError(
            "텍스트를 추출하지 못했습니다(스캔본 PDF일 수 있음). "
            "이 경우 해당 페이지를 사진(JPG/PNG)으로 저장해 넣어 주세요."
        )
    return analyze.extract_report(client, cfg, raw)


def build_report_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> Report:
    """실제 API 를 사용해 한 파일(PDF/사진) -> Report."""
    extraction = _extract_for_pdf(client, cfg, src)
    return analyze.analyze_passage(client, cfg, extraction)


def build_workbook_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> Workbook:
    """실제 API 를 사용해 한 파일(PDF/사진) -> 통합 워크북."""
    extraction = _extract_for_pdf(client, cfg, src)
    return workbook_generate.generate_workbook(client, cfg, extraction)


def _mock_report_for_pdf(cfg: Config, pdf: Path) -> Report:
    from samples.sample_mock import mock_report

    # 추출 단계를 실제로 돌려 제목 후보를 잡아본다(전처리 검증 목적).
    title = _safe_stem(pdf)
    if not extract.is_image(pdf):
        try:
            raw = extract.extract_passage_text(pdf)
            first = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
            if first and len(first) < 80:
                title = first
        except Exception:
            pass
    return mock_report(title=title, source=f"{pdf.name}")


def _mock_workbook_for_pdf(cfg: Config, pdf: Path) -> Workbook:
    from samples.workbook_mock import mock_workbook

    title = _safe_stem(pdf)
    if not extract.is_image(pdf):
        try:
            raw = extract.extract_passage_text(pdf)
            first = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
            if first and len(first) < 80:
                title = first
        except Exception:
            pass
    return mock_workbook(title=title)


def run_folder_workbook(cfg: Config, mock: bool = False) -> dict:
    """input 폴더의 모든 파일을 처리해 output 에 '통합 워크북' PDF 를 생성."""
    logger = setup_logging(cfg.logs_dir)
    manifest = Manifest(cfg.logs_dir)
    pdfs = list_pdfs(cfg.input_dir)
    total = len(pdfs)

    if total == 0:
        logger.warning("input 폴더에 지문 파일이 없습니다: %s", cfg.input_dir)
        return {"total": 0, "success": 0, "failed": 0, "outputs": []}

    client: ClaudeClient | None = None
    if not mock:
        if not cfg.has_api_key:
            raise SystemExit(
                "ANTHROPIC_API_KEY 가 설정되지 않았습니다. .env 파일에 키를 입력하거나 "
                "--mock 옵션으로 디자인만 미리 확인하세요."
            )
        client = ClaudeClient(cfg.api_key, cfg.model)

    # one_pdf_per_passage=False 이면 여러 지문을 한 PDF 에 배치한다:
    #   지문1 → 답1 → 지문2 → 답2 …  (지문별로 문제 다음에 정답이 이어짐)
    combine = not cfg.design.one_pdf_per_passage
    logger.info("총 %d개 지문으로 통합 워크북 생성 시작 (%s 모드, %s)",
                total, "MOCK" if mock else "API",
                "합본: 지문1→답1→지문2→답2" if combine else "지문별 개별 PDF")

    outputs: list[Path] = []
    books: list = []            # 합본 모드에서 모아두는 (지문 순서대로) 워크북
    success = failed = 0
    for i, pdf in enumerate(pdfs, start=1):
        try:
            wb = _mock_workbook_for_pdf(cfg, pdf) if mock else build_workbook_for_pdf(client, cfg, pdf)
            if combine:
                books.append(wb)
                logger.info("[%d/%d] 분석 완료: %s (문항 %d개)", i, total, pdf.name, wb.total)
            else:
                out = cfg.output_dir / f"{_safe_stem(pdf)}_워크북.pdf"
                workbook_render.render_workbook_pdf(wb, out, footer_note=cfg.design.footer_note)
                outputs.append(out)
                manifest.record_success(str(pdf), str(out))
                logger.info("[%d/%d] 완료: %s -> %s (문항 %d개)", i, total, pdf.name, out.name, wb.total)
            success += 1
        except Exception as e:  # 개별 실패가 전체를 멈추지 않게
            failed += 1
            manifest.record_failure(str(pdf), str(e))
            logger.error("[%d/%d] 실패: %s (%s)", i, total, pdf.name, e)

    # 합본 모드: 모은 지문을 한 PDF 로 배치
    if combine and books:
        combined = cfg.output_dir / "통합워크북_합본.pdf"
        workbook_render.render_workbooks_pdf(books, combined, footer_note=cfg.design.footer_note)
        outputs.append(combined)
        manifest.record_success("ALL", str(combined))
        logger.info("합본 워크북 생성: %s (지문 %d편, 지문1→답1→지문2→답2 순서)",
                    combined.name, len(books))

    logger.info("처리 요약 — 성공 %d, 실패 %d (총 %d)", success, failed, total)
    return {"total": total, "success": success, "failed": failed,
            "outputs": [str(o) for o in outputs]}


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
            report = _mock_report_for_pdf(cfg, pdf) if mock else build_report_for_pdf(client, cfg, pdf)
            out = cfg.output_dir / f"{_safe_stem(pdf)}_analysis.pdf"
            render.render_pdf(report, out, footer_note=cfg.design.footer_note)
            outputs.append(out)
            manifest.record_success(str(pdf), str(out))
            success += 1
            logger.info("[%d/%d] 완료: %s -> %s", i, total, pdf.name, out.name)
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
