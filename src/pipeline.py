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
from . import cover_render
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
    from .textutil import qno_label, format_qno

    wbs: list[Workbook] = []
    packs: list[prose_render.ProsePack] = []
    blank_sets: list = []
    writing_packs: list[writing_render.WritingPack] = []
    for i, ex in enumerate(_extract_passages_for_pdf(client, cfg, src)):
        # 헤더 제목 = 지문의 한글 주제, 뱃지 = 지문번호(문항번호)
        #  · 번호는 LLM 추출(q_no) 1순위, 없으면 파일명 파싱, 그래도 없으면 지문 순서(i+1)
        #  · 파일명 접두는 호출부(webapp/CLI)가 apply_q_numbers 로 붙인다
        topic = (ex.topic_ko or "").strip() or ex.title
        #  · 라벨은 '단원-문항' 형식(예: 10-A, 10-1). LLM q_no + 제목/출처의 단원번호로 조합.
        qno = (format_qno(ex.q_no, ex.title, ex.source, ex.topic_ko)
               or qno_label(ex.source) or qno_label(src.name) or f"{i + 1}번")
        wb = workbook_generate.generate_workbook(client, cfg, ex)
        wb.title = topic; wb.label = qno
        pk = prose_generate.generate_prose_pack(client, cfg, ex, header=ex.title)
        pk.title = topic; pk.label = qno
        bs = blanks_generate.generate_blank_set(client, cfg, ex)
        try:
            bs.title = topic; bs.label = qno
        except Exception:
            pass
        wp = writing_generate.generate_writing_pack(client, cfg, ex, header=ex.title)
        wp.title = topic; wp.label = qno
        wbs.append(wb); packs.append(pk); blank_sets.append(bs); writing_packs.append(wp)
    return wbs, packs, blank_sets, writing_packs


def _passage_number(seqs, i: int) -> str:
    """i번째 지문의 현재 번호 라벨을 읽는다(없으면 빈 문자열)."""
    for seq in seqs:
        if seq and i < len(seq):
            v = getattr(seq[i], "label", "") or ""
            if v:
                return v
    return ""


def apply_q_numbers(wbs, packs, blank_sets, writing_packs,
                    start: int | None = None, tag: str = "") -> int | None:
    """모든 유형의 뱃지(label)를 '파일명 + 지문번호' 형태로 맞춘다.

    - start 가 주어지면 지문마다 'start, start+1 …' 로 번호를 새로 부여(수동 입력 우선),
      없으면 각 지문의 현재 번호(자동 추출/지문 순서)를 그대로 사용한다.
    - tag(파일명 식별자)가 있으면 '파일명 · N번' 으로 앞에 붙인다.
    - start 를 준 경우 '다음 시작번호'(start+지문수)를 반환한다(파일 간 누적용).
    """
    seqs = (wbs, packs, blank_sets, writing_packs)
    n = max(len(s or []) for s in seqs)
    for i in range(n):
        num = f"{start + i}번" if start is not None else (_passage_number(seqs, i) or f"{i + 1}번")
        lbl = f"{tag} · {num}" if tag else num
        for seq in seqs:
            if seq and i < len(seq):
                try:
                    seq[i].label = lbl
                except Exception:
                    pass
    return (start + n) if start is not None else None


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


# 유형(파트) 배치 순서: 통합카드 → 어형 → 어법 → 어휘 → 영작 → 해석 → 빈칸
_PROSE_ORDER = ["form", "grammar", "vocab_easy", "vocab", "ref"]  # 어휘 하→상, 이어서 지칭(해석은 영작 뒤로)


def _prose_subpack(pk, wtype: str):
    """ProsePack 에서 한 유형(wtype)만 담은 서브 팩을 만든다(없으면 None)."""
    subs = [w for w in pk.worksheets if w.wtype == wtype]
    if not subs or not any(w.sentences for w in subs):
        return None
    return prose_render.ProsePack(header=pk.header, title=pk.title,
                                  subtitle=pk.subtitle, worksheets=subs, label=pk.label)


def _cover_keys(books, packs, writing_packs, blank_wb) -> list[str]:
    keys: list[str] = []
    if books:
        keys.append("workbook")
    for wtype in ("form", "grammar", "vocab_easy", "vocab", "ref", "translate"):
        if any(_prose_subpack(pk, wtype) is not None for pk in (packs or [])):
            keys.append(wtype)
    if writing_packs:
        keys.append("writing")
    if blank_wb is not None:
        keys.append("blanks")
    return keys


def _render_cover_for(out_path: Path, books, packs, writing_packs, blank_wb,
                      show_ko: bool, footer_note: str,
                      page_map: dict | None = None, answers_page: int = 0,
                      source_name: str = "") -> Path:
    """수록된 유형을 감지해 표지 겸 목차/사용 설명서를 렌더한다."""
    from . import branding

    keys = _cover_keys(books, packs, writing_packs, blank_wb)
    title = (books[0].title if books else
             (packs[0].title if packs else
              (writing_packs[0].title if writing_packs else "통합 워크북")))
    n_passages = max(len(books or []), len(packs or []), len(writing_packs or []), 1)
    version_label = "한글 포함" if show_ko else "한글 제외"
    return cover_render.render_cover_pdf(
        out_path, header=branding.BRAND, title=title or "통합 워크북",
        version_label=version_label, n_passages=n_passages,
        section_keys=keys, footer_note=footer_note,
        page_map=page_map, answers_page=answers_page, source_name=source_name)


def _build_answer_groups(packs, writing_packs, blank_wb, style: str = "compact") -> list:
    """단일 유형(어형·어법·어휘·영작·해석·빈칸) 정답을 '연속 배치용' 그룹 목록으로 만든다.

    style: "gloss"(정답+문장 해석) / "compact"(정답만) / "passage"(정답+지문 전체 해석).
    """
    from . import answers_render as ar
    groups = []
    for wtype, name, css in (("form", "어형 변형", "f"), ("grammar", "어법 양자택일", "g"),
                             ("vocab_easy", "어휘 양자택일 (하)", "v"),
                             ("vocab", "어휘 (상)", "v"),
                             ("ref", "대명사 (지칭 선택)", "b")):
        for pk in packs or []:
            g = ar.group_from_prose(pk, wtype, name, css, style=style)
            if g:
                groups.append(g)
    for wpk in writing_packs or []:
        g = ar.group_from_writing(wpk, style=style)
        if g:
            groups.append(g)
    for pk in packs or []:
        g = ar.group_from_prose(pk, "translate", "한글 해석 연습", "t", style=style)
        if g:
            groups.append(g)
    if blank_wb is not None:
        groups += ar.groups_from_blanks(blank_wb, style=style)
    return groups


def render_workbook_with_prose_pdf(books: list[Workbook], packs: list, out_path: Path,
                                   footer_note: str = "", scratch: Path | None = None,
                                   blank_wb=None, writing_packs: list | None = None,
                                   show_ko: bool = True, source_name: str = "",
                                   answer_style: str = "compact") -> Path:
    """[표지·목차] → 문제(통합카드→어형→어법→어휘→영작→해석→빈칸)
       → [정답·해설 간지] → 통합카드 정답(유형/지문별 페이지 분할)
       → 단일 유형 정답(유형끼리 페이지 안 나누고 연속, 출처 라벨).

    표지에는 각 유형의 시작 페이지(목차)와 정답 시작 페이지를 표시한다.
    blank_wb 가 None 이면 빈칸형은, writing_packs 가 비면 영작형은 생략한다.
    show_ko=False 이면 모든 문제면의 한국어 해석을 숨긴 '한글 제외' 버전으로 렌더한다.
    """
    from . import branding
    import fitz  # 페이지 수 집계(PyMuPDF)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scratch = scratch or out_path.parent
    stem = out_path.stem

    parts: list[Path] = []          # 표지 제외, 본문 순서대로
    toc: dict[str, int] = {}        # 유형 key -> 시작 페이지(문서 전체 기준)
    seen: set[str] = set()
    cover_guess = 1
    cursor = [cover_guess + 1]      # 첫 본문 페이지 번호

    def _count(p: Path) -> int:
        d = fitz.open(str(p)); n = d.page_count; d.close(); return n

    def _emit(tag: str, fn, key: str | None = None):
        p = scratch / f"{stem}__{tag}.pdf"
        fn(p)
        parts.append(p)
        if key and key not in seen:
            toc[key] = cursor[0]; seen.add(key)
        cursor[0] += _count(p)

    # ── 문제 ──
    if books:
        _emit("wb_q", lambda p: workbook_render.render_workbooks_pdf(
            books, p, footer_note=footer_note, show_ko=show_ko, section="q"), key="workbook")
    for wtype in _PROSE_ORDER:                       # 어형 → 어법 → 어휘
        for i, pk in enumerate(packs, start=1):
            sub = _prose_subpack(pk, wtype)
            if sub is not None:
                _emit(f"{wtype}{i}_q", lambda p, s=sub: prose_render.render_prose_pdf(
                    s, p, footer_note=footer_note, show_ko=show_ko, section="q"), key=wtype)
    for i, wpk in enumerate(writing_packs or [], start=1):    # 영작
        _emit(f"writing{i}_q", lambda p, w=wpk: writing_render.render_writing_pdf(
            w, p, footer_note=footer_note, show_ko=show_ko, section="q"), key="writing")
    for i, pk in enumerate(packs, start=1):          # 한글 해석 연습
        sub = _prose_subpack(pk, "translate")
        if sub is not None:
            _emit(f"translate{i}_q", lambda p, s=sub: prose_render.render_prose_pdf(
                s, p, footer_note=footer_note, show_ko=show_ko, section="q"), key="translate")
    if blank_wb is not None:                          # 빈칸
        _emit("blanks_q", lambda p: blanks_render.render_blanks_pdf(
            blank_wb, p, footer_note=footer_note, show_ko=show_ko, section="q"), key="blanks")

    # ── 정답·해설 ──
    _emit("ansdiv", lambda p: cover_render.render_answer_divider_pdf(
        p, header=branding.BRAND, footer_note=footer_note), key="answers")
    if books:                                         # 통합카드 정답(유형/지문별 페이지 분할 유지)
        _emit("wb_a", lambda p: workbook_render.render_workbooks_pdf(
            books, p, footer_note=footer_note, show_ko=show_ko, section="a"))
    groups = _build_answer_groups(packs, writing_packs, blank_wb, style=answer_style)
    if groups:
        from . import answers_render
        _emit("answers", lambda p: answers_render.render_answers_pdf(
            groups, p, footer_note=footer_note))

    # ── 표지·목차 (본문 페이지 수 집계 후 렌더, 표지 페이지 수 보정) ──
    cover_path = scratch / f"{stem}__cover.pdf"
    _render_cover_for(cover_path, books, packs, writing_packs, blank_wb, show_ko, footer_note,
                      page_map=toc, answers_page=toc.get("answers", 0), source_name=source_name)
    cpages = _count(cover_path)
    if cpages != cover_guess:                         # 표지가 여러 장이면 목차 페이지를 보정
        shift = cpages - cover_guess
        toc = {k: v + shift for k, v in toc.items()}
        _render_cover_for(cover_path, books, packs, writing_packs, blank_wb, show_ko, footer_note,
                          page_map=toc, answers_page=toc.get("answers", 0), source_name=source_name)

    workbook_render.merge_pdfs([cover_path] + parts, out_path)
    try:
        workbook_render.stamp_page_numbers(out_path)   # 문서 전체 기준 페이지 번호
    except Exception:
        pass
    for p in [cover_path] + parts:                    # 중간 산출물 정리
        try:
            p.unlink(missing_ok=True)
            p.with_suffix(".html").unlink(missing_ok=True)
        except Exception:
            pass
    return out_path


def render_workbook_two_versions(books: list[Workbook], packs: list, out_dir: Path,
                                 base_name: str, footer_note: str = "",
                                 scratch: Path | None = None, blank_wb=None,
                                 writing_packs: list | None = None,
                                 source_name: str = "", answer_style: str = "compact") -> list[Path]:
    """같은 내용을 '한글 포함'·'한글 제외' 두 개의 별도 PDF 로 출력한다."""
    out_dir = Path(out_dir)
    outs: list[Path] = []
    for suffix, show_ko in (("_한글포함", True), ("_한글제외", False)):
        out = out_dir / f"{base_name}{suffix}.pdf"
        render_workbook_with_prose_pdf(
            books, packs, out, footer_note=footer_note, scratch=scratch,
            blank_wb=blank_wb, writing_packs=writing_packs, show_ko=show_ko,
            source_name=source_name, answer_style=answer_style)
        outs.append(out)
    return outs


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
    wb = mock_workbook()
    wb.title = _MOCK_TOPIC; wb.label = _mock_label(pdf)
    return wb


# 목(mock)은 '초기 피드백' 지문 하나로 통일 — 헤더 제목은 '핵심 키워드 중심의 짧은' 한글 주제
_MOCK_TOPIC = "초기 피드백과 전문적 성공"


def _mock_label(pdf: Path) -> str:
    from .textutil import qno_label
    return qno_label(pdf.name) or "30번"


def _mock_prose_pack_for_pdf(cfg: Config, pdf: Path):
    from samples.prose_mock import mock_prose_pack

    pk = mock_prose_pack()
    pk.title = _MOCK_TOPIC; pk.label = _mock_label(pdf)
    return pk


def _mock_writing_pack_for_pdf(cfg: Config, pdf: Path):
    from samples.writing_mock import mock_writing_pack

    wp = mock_writing_pack()
    wp.title = _MOCK_TOPIC; wp.label = _mock_label(pdf)
    return wp


def _mock_blank_set_for_pdf(cfg: Config, pdf: Path, no: int):
    from samples.blanks_mock import mock_blank_set

    st = mock_blank_set(no=no)
    try:
        st.title = _MOCK_TOPIC; st.label = _mock_label(pdf)
    except Exception:
        pass
    return st


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
            # 뱃지 = 지문번호('단원-문항' 예: 10-1). 파일명 접두는 붙이지 않는다.
            apply_q_numbers(wbs, file_packs, file_bsets, file_wpacks, tag="")
            if combine:
                books.extend(wbs)   # 파일 안의 여러 지문을 모두 합본에 포함
                packs.extend(file_packs)
                bsets.extend(file_bsets)
                wpacks.extend(file_wpacks)
                logger.info("[%d/%d] 분석 완료: %s (지문 %d편)", i, total, pdf.name, len(wbs))
            else:
                # 유형 순서(통합→어형→어법→어휘→영작→해석→빈칸)로 '한글 포함'·'한글 제외' 2개 PDF
                outs = render_workbook_two_versions(
                    wbs, file_packs, cfg.output_dir, f"{_safe_stem(pdf)}_워크북",
                    footer_note=cfg.design.footer_note,
                    blank_wb=_build_blank_workbook(file_bsets), writing_packs=file_wpacks,
                    source_name=pdf.name)
                outputs.extend(outs)
                manifest.record_success(str(pdf), ", ".join(str(o) for o in outs))
                logger.info("[%d/%d] 완료: %s -> %s (지문 %d편)", i, total, pdf.name,
                            " · ".join(o.name for o in outs), len(wbs))
            success += 1
        except Exception as e:  # 개별 실패가 전체를 멈추지 않게
            failed += 1
            manifest.record_failure(str(pdf), str(e))
            logger.error("[%d/%d] 실패: %s (%s)", i, total, pdf.name, e)

    # 합본 모드: 모은 지문을 유형 순서(통합→어형→어법→어휘→영작→해석→빈칸)로,
    # '한글 포함'·'한글 제외' 2개 PDF 로 출력한다.
    if combine and books:
        outs = render_workbook_two_versions(
            books, packs, cfg.output_dir, "통합워크북_합본",
            footer_note=cfg.design.footer_note,
            blank_wb=_build_blank_workbook(bsets), writing_packs=wpacks)
        outputs.extend(outs)
        manifest.record_success("ALL", ", ".join(str(o) for o in outs))
        logger.info("합본 워크북 생성: %s (지문 %d편, 한글 포함/제외 2벌)",
                    " · ".join(o.name for o in outs), len(books))

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
