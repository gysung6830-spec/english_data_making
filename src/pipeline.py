"""폴더 단위 처리 오케스트레이션 (동기 모드 + 목 모드)."""
from __future__ import annotations

import re
from pathlib import Path

from . import analyze, extract, hwp, render
from .client import ClaudeClient
from .config import Config
from .logutil import Manifest, setup_logging
from .schemas import Report


INPUT_EXTS = {".pdf"} | extract.IMAGE_EXTS | hwp.HWP_EXTS


def list_pdfs(input_dir: Path) -> list[Path]:
    """PDF 와 이미지(사진/캡처) 파일을 모두 처리 대상으로 수집."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in INPUT_EXTS
    )


def _safe_stem(path: Path) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", path.stem).strip() or "passage"


def _extract_pdf_passages(client: ClaudeClient, cfg: Config, src: Path,
                          focus_items: str = ""):
    """PDF -> PassageSet. 설정(pdf_mode)에 따라 비전/텍스트로 추출.

    비전 모드인데 PyMuPDF(fitz)가 없으면 텍스트 추출로 자동 폴백한다(중단 방지).
    focus_items: 모의고사 독해에서 뽑을 문항 번호(예: '18-24,29-43').
    """
    mode = cfg.extraction.pdf_mode

    def _text_extract(require: bool):
        if focus_items:
            # 모의고사: 2단 추출 → 듣기 제거 → 문항별 분할·라벨.
            #   (문항 번호를 정확히 매기려면 clean_text 가 'NN.'을 떼기 전에 분할해야 함)
            raw = extract.segment_exam_questions(
                extract.strip_listening(extract.extract_raw_text(src, two_column=True)),
                focus_items,
            )
        else:
            raw = extract.extract_passage_text(src)
        if extract.looks_empty(raw):
            if require:
                raise ValueError(
                    "PDF에서 텍스트를 추출하지 못했습니다(스캔본이거나 이미지 PDF). "
                    "PyMuPDF 설치('pip install PyMuPDF') 후 비전 모드로 읽거나, "
                    "해당 페이지를 사진(JPG/PNG)으로 저장해 넣어 주세요."
                )
            return None
        # auto: 텍스트가 깨져 보이는 '문제 파일'이면 None 을 돌려 아래 vision 으로 보완.
        #   (비전이 불가한 require 상황에서는 깨졌더라도 그대로 사용해 결과는 내보낸다)
        if mode == "auto" and not require and extract.looks_garbled(raw):
            return None
        return analyze.extract_passages(client, cfg, raw, focus_items)

    if mode in ("text", "auto"):
        pset = _text_extract(require=(mode == "text"))
        if pset is not None:
            return pset
        # auto: 비어보이면 아래 vision 으로 보완

    # vision: PDF 페이지를 이미지로 렌더해 비전으로 읽음
    try:
        imgs = extract.render_pdf_to_images(src, dpi=cfg.extraction.dpi)
    except ModuleNotFoundError:
        # PyMuPDF 미설치 → 텍스트 추출로 폴백(그래도 결과는 나오게)
        return _text_extract(require=True)
    try:
        return analyze.extract_passages_image(client, cfg, [str(p) for p in imgs],
                                              focus_items)
    finally:
        for p in imgs:
            p.unlink(missing_ok=True)


def build_reports_for_pdf(client: ClaudeClient, cfg: Config, src: Path,
                          focus_items: str = "") -> list[Report]:
    """실제 API 를 사용해 한 파일(PDF/사진) -> 여러 Report(지문 순서대로).

    focus_items: 모의고사 독해에서 뽑을 문항 번호 범위(예: '18-24,29-43'). 비우면 전체.
    """
    if extract.is_image(src):
        pset = analyze.extract_passages_image(client, cfg, str(src), focus_items)
    elif hwp.is_hwp(src):
        raw = extract.strip_listening(hwp.extract_hwp_text(src))
        if extract.looks_empty(raw):
            raise ValueError(
                "HWP 에서 텍스트를 찾지 못했습니다(지문이 이미지로 들어간 HWP일 수 있음). "
                "그 페이지를 PDF나 사진(JPG/PNG)으로 저장해 넣어 주세요."
            )
        pset = analyze.extract_passages(client, cfg, raw, focus_items)
    else:
        pset = _extract_pdf_passages(client, cfg, src, focus_items)
    return [analyze.analyze_passage(client, cfg, ex) for ex in pset.passages]


# 하위 호환용 별칭(단일 Report 반환)
def build_report_for_pdf(client: ClaudeClient, cfg: Config, src: Path) -> Report:
    return build_reports_for_pdf(client, cfg, src)[0]


def render_outputs(cfg: Config, reports: list[Report], stem: str,
                   which=None, brand: str | None = None,
                   source_label: str | None = None) -> list[dict]:
    """선택된 종류(분석지/어휘 리스트/시험지)의 PDF 를 생성.

    반환: [{"kind": "analysis"|"wordlist"|"quiz", "label": 표시명, "path": Path}, ...]

    - 분석지: 지문이 여러 개여도 한 PDF(지문1→지문2… 순서)로.
    - 어휘 리스트 / 시험지: 지문이 여러 개면 '지문별로 각각' 생성.
    brand: 분석지의 'made by ~' · '~ tip' 문구 이름. None 이면 config 값, ""이면 문구 제거.
    source_label: 지문 번호 뱃지에 함께 표시할 '파일명(지문명)'. None 이면 stem 사용.
    (하단 저작권 footer 는 항상 그대로)
    """
    sel = which or cfg.outputs
    brand = cfg.design.brand if brand is None else brand
    label = stem if source_label is None else source_label
    fn = cfg.design.footer_note
    title = reports[0].title if reports else stem
    recs: list[dict] = []

    want_teacher = sel.analysis
    want_student = getattr(sel, "student", False)
    if want_teacher and want_student:
        # 교사 전체 지문 → 학생 전체 지문 순서로 한 PDF 합본
        p = cfg.output_dir / f"{stem}_지문분석.pdf"
        render.render_analysis_pdf(reports, p, footer_note=fn,
                                   min_vocab=cfg.vocab.min, brand=brand,
                                   variants=[False, True], source_label=label)
        recs.append({"kind": "analysis", "label": "📘 분석지(교사용+학생용)", "path": p})
    elif want_teacher:
        p = cfg.output_dir / f"{stem}_지문분석.pdf"
        render.render_analysis_pdf(reports, p, footer_note=fn,
                                   min_vocab=cfg.vocab.min, brand=brand, variants=[False],
                                   source_label=label)
        recs.append({"kind": "analysis", "label": "📘 분석지(교사용)", "path": p})
    elif want_student:
        p = cfg.output_dir / f"{stem}_지문분석_학생용.pdf"
        render.render_analysis_pdf(reports, p, footer_note=fn,
                                   min_vocab=cfg.vocab.min, brand=brand, variants=[True],
                                   source_label=label)
        recs.append({"kind": "student", "label": "📗 분석지(학생용·빈칸)", "path": p})

    # 핵심 어휘 리스트(유의어·반의어) — 분석지의 어휘 기반, 별도 PDF
    if getattr(sel, "vocablist", False):
        p = cfg.output_dir / f"{stem}_핵심어휘리스트.pdf"
        render.render_vocablist_pdf(reports, p, title=f"{title} — 핵심 어휘", footer_note=fn)
        recs.append({"kind": "vocablist", "label": "📚 핵심 어휘 리스트", "path": p})

    # 핵심 어휘 시험지(뜻쓰기 + 유의어/반의어 줄긋기)
    if getattr(sel, "vocabtest", False):
        p = cfg.output_dir / f"{stem}_핵심어휘test.pdf"
        render.render_vocabtest_pdf(reports, p, title=f"{title} — 핵심 어휘 시험", footer_note=fn,
                                    brand_name=cfg.design.brand_name)
        recs.append({"kind": "vocabtest", "label": "🧩 핵심 어휘 시험지", "path": p})

    return recs


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

    analysis_outputs: list[Path] = []
    outputs: list[Path] = []
    success = failed = 0
    for i, pdf in enumerate(pdfs, start=1):
        try:
            reports = (_mock_reports_for_pdf(cfg, pdf) if mock
                       else build_reports_for_pdf(client, cfg, pdf))
            recs = render_outputs(cfg, reports, _safe_stem(pdf))
            outputs.extend(r["path"] for r in recs)
            a_paths = [r["path"] for r in recs if r["kind"] == "analysis"]
            analysis_outputs.extend(a_paths)
            manifest.record_success(str(pdf), str(a_paths[0]) if a_paths else "",
                                    {"passages": len(reports),
                                     "outputs": [r["path"].name for r in recs]})
            success += 1
            logger.info("[%d/%d] 완료: %s (지문 %d개) -> %s",
                        i, total, pdf.name, len(reports),
                        ", ".join(r["path"].name for r in recs))
        except Exception as e:  # 개별 실패가 전체를 멈추지 않게
            failed += 1
            manifest.record_failure(str(pdf), str(e))
            logger.error("[%d/%d] 실패: %s (%s)", i, total, pdf.name, e)

    # 하나의 PDF 로 합치기 옵션 (분석지에 한함)
    if analysis_outputs and not cfg.design.one_pdf_per_passage:
        combined = cfg.output_dir / "ALL_passages_analysis.pdf"
        render.combine_pdfs(analysis_outputs, combined)
        logger.info("합본 PDF 생성: %s", combined.name)

    logger.info("처리 요약 — 성공 %d, 실패 %d (총 %d)", success, failed, total)
    return {"total": total, "success": success, "failed": failed,
            "outputs": [str(o) for o in outputs]}
