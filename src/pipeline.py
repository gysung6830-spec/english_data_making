"""폴더 단위 처리 오케스트레이션 (동기 모드 + 목 모드)."""
from __future__ import annotations

import re
from pathlib import Path

from . import analyze, extract, render
from . import workbook_generate, workbook_render
from . import blanks_generate, blanks_render
from . import blanks_schemas
from . import prose_generate, prose_render
from . import writing_generate, writing_render
from .client import ClaudeClient
from .config import Config
from .logutil import Manifest, setup_logging
from .schemas import Report
from .workbook_schemas import Workbook
from .blanks_schemas import BlankWorkbook


INPUT_EXTS = {".pdf"} | extract.IMAGE_EXTS | extract.HWP_EXTS


def list_pdfs(input_dir: Path) -> list[Path]:
    """PDF 와 이미지(사진/캡처) 파일을 모두 처리 대상으로 수집."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in INPUT_EXTS
    )


def _safe_stem(path: Path) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", path.stem).strip() or "passage"


def _try_stamp(path: Path) -> None:
    """완성 PDF 에 문서 전체 기준 페이지 번호를 찍는다(실패해도 무시)."""
    try:
        workbook_render.stamp_page_numbers(path)
    except Exception:
        pass


def _empty_extract_error(src: Path) -> str:
    if extract.is_hwp(src):
        return ("HWP 에서 텍스트를 추출하지 못했습니다(암호화·배포용 문서이거나 그림만 있는 경우). "
                "한글에서 '다른 이름으로 저장 → PDF' 로 바꿔 넣거나, 지문 페이지를 사진(JPG/PNG)으로 저장해 주세요.")
    return ("텍스트를 추출하지 못했습니다(스캔본 PDF일 수 있음). "
            "이 경우 해당 페이지를 사진(JPG/PNG)으로 저장해 넣어 주세요.")


def _extract_for_pdf(client: ClaudeClient, cfg: Config, src: Path):
    """한 파일(PDF/사진/HWP) -> Extraction (지문 본문). 텍스트/이미지 자동 분기."""
    if extract.is_image(src):
        # 사진/캡처 → 비전으로 지문 추출
        return analyze.extract_report_image(client, cfg, str(src))
    raw = extract.extract_passage_text(src)
    if extract.looks_empty(raw):
        raise ValueError(_empty_extract_error(src))
    return analyze.extract_report(client, cfg, raw)


def build_report_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> Report:
    """실제 API 를 사용해 한 파일(PDF/사진) -> Report."""
    extraction = _extract_for_pdf(client, cfg, src)
    return analyze.analyze_passage(client, cfg, extraction)


def build_workbook_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> Workbook:
    """실제 API 를 사용해 한 파일(PDF/사진) -> 통합 워크북."""
    extraction = _extract_for_pdf(client, cfg, src)
    return workbook_generate.generate_workbook(client, cfg, extraction)


def build_blank_set_for_pdf(client: ClaudeClient, cfg: Config, src: Path):
    """실제 API 를 사용해 한 파일(PDF/사진) -> 빈칸형 세트(LLMBlankSet)."""
    extraction = _extract_for_pdf(client, cfg, src)
    return blanks_generate.generate_blank_set(client, cfg, extraction)


def _extract_passages_for_pdf(client: ClaudeClient, cfg: Config, src: Path):
    """한 파일 -> 그 안의 '여러 지문' 목록(Extraction 리스트)."""
    if extract.is_image(src):
        return analyze.extract_passages_image(client, cfg, str(src))
    raw = extract.extract_passage_text(src)
    if extract.looks_empty(raw):
        raise ValueError(_empty_extract_error(src))
    return analyze.extract_passages(client, cfg, raw)


def build_workbooks_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> list[Workbook]:
    """한 파일(여러 지문 가능) -> 지문별 통합 워크북 목록."""
    return [workbook_generate.generate_workbook(client, cfg, ex)
            for ex in _extract_passages_for_pdf(client, cfg, src)]


def build_workbook_bundle_for_pdf(client: ClaudeClient, cfg: Config, src: Path):
    """한 파일(여러 지문 가능) -> (통합 워크북, 산문 워크시트 팩, 빈칸형 세트, 영작 팩) 목록.

    지문 추출을 1회만 수행해 통합 워크북 · 단일 유형 산문 워크시트 · 빈칸형 · 영작을 함께 생성한다.
    """
    wbs: list[Workbook] = []
    packs: list[prose_render.ProsePack] = []
    blank_sets: list = []
    writing_packs: list[writing_render.WritingPack] = []
    for ex in _extract_passages_for_pdf(client, cfg, src):
        wbs.append(workbook_generate.generate_workbook(client, cfg, ex))
        packs.append(prose_generate.generate_prose_pack(client, cfg, ex, header=ex.title))
        blank_sets.append(blanks_generate.generate_blank_set(client, cfg, ex))
        writing_packs.append(writing_generate.generate_writing_pack(client, cfg, ex, header=ex.title))
    return wbs, packs, blank_sets, writing_packs


def _build_blank_workbook(blank_sets: list, title: str = "빈칸 워크북",
                          subtitle: str = "유형 B 지문 빈칸 · 유형 A 요약문 빈칸"):
    """LLMBlankSet 목록 -> 렌더용 BlankWorkbook (번호 재부여)."""
    if not blank_sets:
        return None
    for idx, st in enumerate(blank_sets, start=1):
        st.no = idx
    base_title = blank_sets[0].title if len(blank_sets) == 1 else title
    base_sub = blank_sets[0].subtitle if len(blank_sets) == 1 else subtitle
    return blanks_schemas.build_blank_workbook(
        blanks_schemas.LLMBlankWorkbook(sets=blank_sets), title=base_title, subtitle=base_sub)


def render_workbook_with_prose_pdf(books: list[Workbook], packs: list, out_path: Path,
                                   footer_note: str = "", scratch: Path | None = None,
                                   blank_wb=None, writing_packs: list | None = None) -> Path:
    """통합 워크북(앞) → 단일 유형 산문 → 빈칸 워크북 → 영작 워크북(맨 뒤) 순서로 한 PDF 로 병합.

    각 부분을 개별 PDF 로 렌더한 뒤 순서대로 병합한다.
    blank_wb 가 None 이면 빈칸형은, writing_packs 가 비면 영작형은 생략한다.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scratch = scratch or out_path.parent
    stem = out_path.stem
    parts: list[Path] = []
    if books:
        wb_pdf = scratch / f"{stem}__wb.pdf"
        workbook_render.render_workbooks_pdf(books, wb_pdf, footer_note=footer_note)
        parts.append(wb_pdf)
    for i, pk in enumerate(packs, start=1):
        pr_pdf = scratch / f"{stem}__prose{i}.pdf"
        prose_render.render_prose_pdf(pk, pr_pdf, footer_note=footer_note)
        parts.append(pr_pdf)
    if blank_wb is not None:               # 빈칸 워크북
        bl_pdf = scratch / f"{stem}__blanks.pdf"
        blanks_render.render_blanks_pdf(blank_wb, bl_pdf, footer_note=footer_note)
        parts.append(bl_pdf)
    for i, wpk in enumerate(writing_packs or [], start=1):   # 영작 워크북은 가장 마지막
        wr_pdf = scratch / f"{stem}__writing{i}.pdf"
        writing_render.render_writing_pdf(wpk, wr_pdf, footer_note=footer_note)
        parts.append(wr_pdf)
    workbook_render.merge_pdfs(parts, out_path)
    try:
        workbook_render.stamp_page_numbers(out_path)   # 문서 전체 기준 페이지 번호
    except Exception:
        pass
    for p in parts:                       # 중간 산출물 정리
        try:
            p.unlink(missing_ok=True)
            p.with_suffix(".html").unlink(missing_ok=True)
        except Exception:
            pass
    return out_path


def build_blank_sets_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> list:
    """한 파일(여러 지문 가능) -> 지문별 빈칸형 세트(LLMBlankSet) 목록."""
    return [blanks_generate.generate_blank_set(client, cfg, ex)
            for ex in _extract_passages_for_pdf(client, cfg, src)]


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


def _mock_prose_pack_for_pdf(cfg: Config, pdf: Path):
    from samples.prose_mock import mock_prose_pack

    title = _safe_stem(pdf)
    return mock_prose_pack(title=title, header=title)


def _mock_writing_pack_for_pdf(cfg: Config, pdf: Path):
    from samples.writing_mock import mock_writing_pack

    title = _safe_stem(pdf)
    return mock_writing_pack(title=title, header=title)


def _mock_blank_set_for_pdf(cfg: Config, pdf: Path, no: int):
    from samples.blanks_mock import mock_blank_set

    title = _safe_stem(pdf)
    if not extract.is_image(pdf):
        try:
            raw = extract.extract_passage_text(pdf)
            first = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
            if first and len(first) < 80:
                title = first
        except Exception:
            pass
    return mock_blank_set(title=title, no=no)


def run_folder_blanks(cfg: Config, mock: bool = False) -> dict:
    """input 폴더의 모든 파일을 처리해 output 에 '빈칸형 워크북' PDF 를 생성."""
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
            raise SystemExit("ANTHROPIC_API_KEY 가 설정되지 않았습니다. --mock 로 미리 확인하세요.")
        client = ClaudeClient(cfg.api_key, cfg.model)

    combine = not cfg.design.one_pdf_per_passage
    logger.info("총 %d개 지문으로 빈칸형 워크북 생성 시작 (%s 모드, %s)", total,
                "MOCK" if mock else "API", "합본" if combine else "지문별 개별 PDF")

    outputs: list[Path] = []
    sets: list = []
    success = failed = 0
    for i, pdf in enumerate(pdfs, start=1):
        try:
            file_sets = ([_mock_blank_set_for_pdf(cfg, pdf, no=1)] if mock
                         else build_blank_sets_for_pdf(client, cfg, pdf))
            if combine:
                sets.extend(file_sets)
            else:
                for idx, st in enumerate(file_sets, start=1):
                    st.no = idx
                wb = blanks_schemas.build_blank_workbook(
                    blanks_schemas.LLMBlankWorkbook(sets=file_sets),
                    title=file_sets[0].title, subtitle=file_sets[0].subtitle)
                out = cfg.output_dir / f"{_safe_stem(pdf)}_빈칸워크북.pdf"
                blanks_render.render_blanks_pdf(wb, out, footer_note=cfg.design.footer_note)
                _try_stamp(out)
                outputs.append(out)
                manifest.record_success(str(pdf), str(out))
            success += 1
            logger.info("[%d/%d] 완료: %s (지문 %d편)", i, total, pdf.name, len(file_sets))
        except Exception as e:
            failed += 1
            manifest.record_failure(str(pdf), str(e))
            logger.error("[%d/%d] 실패: %s (%s)", i, total, pdf.name, e)

    if combine and sets:
        for idx, st in enumerate(sets, start=1):
            st.no = idx
        wb = blanks_schemas.build_blank_workbook(
            blanks_schemas.LLMBlankWorkbook(sets=sets),
            title="빈칸 워크북", subtitle="유형 B 지문 빈칸 · 유형 A 요약문 빈칸")
        combined = cfg.output_dir / "빈칸워크북_합본.pdf"
        blanks_render.render_blanks_pdf(wb, combined, footer_note=cfg.design.footer_note)
        _try_stamp(combined)
        outputs.append(combined)
        manifest.record_success("ALL", str(combined))
        logger.info("합본 빈칸 워크북 생성: %s (지문 %d편)", combined.name, len(sets))

    logger.info("처리 요약 — 성공 %d, 실패 %d (총 %d)", success, failed, total)
    return {"total": total, "success": success, "failed": failed,
            "outputs": [str(o) for o in outputs]}


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
    packs: list = []            # 합본 모드에서 모아두는 단일 유형 산문 워크시트
    bsets: list = []            # 합본 모드에서 모아두는 빈칸형 세트(맨 뒤 배치용)
    wpacks: list = []           # 합본 모드에서 모아두는 영작 워크북(가장 마지막 배치용)
    success = failed = 0
    for i, pdf in enumerate(pdfs, start=1):
        try:
            if mock:
                wbs = [_mock_workbook_for_pdf(cfg, pdf)]
                file_packs = [_mock_prose_pack_for_pdf(cfg, pdf)]
                file_bsets = [_mock_blank_set_for_pdf(cfg, pdf, no=1)]
                file_wpacks = [_mock_writing_pack_for_pdf(cfg, pdf)]
            else:
                wbs, file_packs, file_bsets, file_wpacks = build_workbook_bundle_for_pdf(
                    client, cfg, pdf)
            if combine:
                books.extend(wbs)   # 파일 안의 여러 지문을 모두 합본에 포함
                packs.extend(file_packs)
                bsets.extend(file_bsets)
                wpacks.extend(file_wpacks)
                logger.info("[%d/%d] 분석 완료: %s (지문 %d편)", i, total, pdf.name, len(wbs))
            else:
                out = cfg.output_dir / f"{_safe_stem(pdf)}_워크북.pdf"
                # 통합 카드(앞) → 단일 유형 4종 → 빈칸 워크북 → 영작 워크북(맨 뒤)을 한 PDF 로
                render_workbook_with_prose_pdf(
                    wbs, file_packs, out, footer_note=cfg.design.footer_note,
                    blank_wb=_build_blank_workbook(file_bsets), writing_packs=file_wpacks)
                outputs.append(out)
                manifest.record_success(str(pdf), str(out))
                logger.info("[%d/%d] 완료: %s -> %s (지문 %d편)", i, total, pdf.name, out.name, len(wbs))
            success += 1
        except Exception as e:  # 개별 실패가 전체를 멈추지 않게
            failed += 1
            manifest.record_failure(str(pdf), str(e))
            logger.error("[%d/%d] 실패: %s (%s)", i, total, pdf.name, e)

    # 합본 모드: 모은 지문을 한 PDF 로 배치 (통합 → 단일 유형 → 빈칸 → 영작 순서)
    if combine and books:
        combined = cfg.output_dir / "통합워크북_합본.pdf"
        render_workbook_with_prose_pdf(books, packs, combined,
                                       footer_note=cfg.design.footer_note,
                                       blank_wb=_build_blank_workbook(bsets),
                                       writing_packs=wpacks)
        outputs.append(combined)
        manifest.record_success("ALL", str(combined))
        logger.info("합본 워크북 생성: %s (지문 %d편, 통합→단일유형→빈칸→영작 순서)",
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
