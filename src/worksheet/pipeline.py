"""구문 분석 학습지 파이프라인 오케스트레이션 (명세서 §5).

    loader → splitter → analyzer(LLM) → point_builder(LLM) → renderer → PDF

기존 입력 로더(src/extract.py)와 지문 분리(src/analyze.py)를 재사용한다.
API 없이 배관을 확인할 수 있는 규칙기반/목 경로도 함께 제공한다.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from . import (analyzer, literal_builder, overview_builder, point_builder,
               renderer, splitter)
from .models import Analysis, Sentence

if TYPE_CHECKING:  # 타입 힌트 전용 (런타임 무거운 임포트 회피)
    from ..client import ClaudeClient
    from ..config import Config


@dataclass
class Header:
    """학습지 머리글 (사용자 입력, 기본값 비움)."""

    title_en: str = ""
    title_ko: str = ""
    lecture_label: str = ""
    date: str = ""
    strength: str = analyzer.STRENGTH_FULL   # 'full' | 'key' | 'none'

    def for_passage(self, ex, order: int, total: int) -> "Header":
        """추출된 지문에 맞춰 제목을 채운 사본. 복수 지문이면 강 라벨에 순번 부기."""
        title = self.title_en or getattr(ex, "title", "") or ""
        lec = self.lecture_label
        if total > 1 and lec:
            lec = f"{lec}-{order}"
        return Header(title_en=title, title_ko=self.title_ko, lecture_label=lec,
                      date=self.date, strength=self.strength)


# ---------------------------------------------------------------------------
# 텍스트 1지문 → Analysis
# ---------------------------------------------------------------------------
def analyze_text(client: "ClaudeClient", raw_text: str, header: Header,
                 passage_summary: str = "", max_retries: int = 1,
                 parallel: bool = True, with_back: bool = True,
                 with_literal: bool = False) -> Analysis:
    """지문 텍스트 하나를 문장 단위로 태깅+포인트 생성하여 Analysis 로.

    with_back=True 면 뒷페이지(어휘 리스트/논리 흐름도/쉬운 예시)도 함께 생성한다.
    with_literal=True 면 직독직해(레이아웃 B: 청크·핵심 문법·핵심 단어)도 생성한다.
    """
    texts = splitter.split_sentences(raw_text)

    def one(i_text):
        i, text = i_text
        s = analyzer.analyze_sentence(client, text, i + 1,
                                      strength=header.strength, max_retries=max_retries)
        # 어법 요소를 (1)(2)…로 번호 매겨 오른쪽 '어법 Point' 박스로(내용 TMI 없음).
        gp = point_builder.build_grammar_point(s)
        s.points = [gp] if gp else []
        return s

    items = list(enumerate(texts))
    if parallel and len(items) > 1:
        with ThreadPoolExecutor(max_workers=min(6, len(items))) as ex:
            sentences = list(ex.map(one, items))
    else:
        sentences = [one(it) for it in items]

    analysis = Analysis(
        title_en=header.title_en,
        title_ko=header.title_ko,
        lecture_label=header.lecture_label,
        date=header.date,
        sentences=sentences,
    )
    if with_back:
        t_en, t_ko, summary, vocab, flow = overview_builder.build_overview(
            client, analysis, max_retries=max_retries)
        analysis.vocab, analysis.flow = vocab, flow
        # 영문 제목·한글 부제는 자동 생성값 우선(사용자 입력 없음)
        analysis.title_en = t_en or analysis.title_en
        analysis.title_ko = t_ko or analysis.title_ko
        analysis.summary = summary or analysis.summary
    if with_literal:
        analysis.literal = literal_builder.build_literal(
            client, analysis, max_retries=max_retries)
    return analysis


def analyze_text_rule_only(raw_text: str, header: Header, tag: bool = True) -> Analysis:
    """API 없이 규칙기반 초안만으로 Analysis(해석 없음). 배관/미리보기용."""
    texts = splitter.split_sentences(raw_text)
    sentences: list[Sentence] = []
    for i, text in enumerate(texts):
        s = analyzer.rule_only_sentence(text, i + 1, tag=tag)
        if tag:
            s.points = point_builder.rule_only_points(s)
        sentences.append(s)
    return Analysis(
        title_en=header.title_en, title_ko=header.title_ko,
        lecture_label=header.lecture_label, date=header.date, sentences=sentences,
    )


# ---------------------------------------------------------------------------
# 파일(PDF/사진) → Analysis 목록 (복수 지문 지원)
# ---------------------------------------------------------------------------
def build_analyses_for_file(client: "ClaudeClient", cfg: "Config", src: Path,
                            header: Header, max_retries: int = 1,
                            layout: str = "A") -> list[Analysis]:
    """한 파일에서 지문(들)을 추출해 각각 Analysis 로.

    layout='B' 면 뒷페이지 대신 직독직해(청크·핵심 문법·핵심 단어)를 생성한다.
    """
    from .. import analyze, extract  # 지연 임포트(pdfplumber/anthropic 무거움)
    from . import quality

    if extract.is_image(src):
        pset = analyze.extract_passages_image(client, cfg, str(src))
    else:
        raw = extract.extract_passage_text_any(src)   # PDF · HWP · HWPX
        empty = extract.looks_empty(raw)
        is_pdf = src.suffix.lower() == ".pdf"

        # 1) 텍스트 경로(비어 있지 않을 때)
        pset = None
        if not empty:
            pset = analyze.extract_passages(client, cfg, raw)

        # 2) 텍스트가 비었거나(스캔) 결과가 조각나 보이면 → PDF는 페이지를 이미지로
        #    렌더해 비전으로 재추출(폰트 subset·2단·스캔 등으로 문장 앞부분이 잘리는 경우).
        #    비전은 '문제 파일에만' 조건부(설정 quality.vision_fallback, 기본 켜짐).
        vision_on = getattr(getattr(cfg, "quality", None), "vision_fallback", True)
        if (is_pdf and client is not None and vision_on
                and (empty or quality.passages_fragmented(pset))):
            vpset = _extract_via_vision_pdf(client, cfg, src)
            if vpset is not None and (pset is None or not quality.passages_fragmented(vpset)):
                pset = vpset      # 비전 결과가 더 온전할 때만 채택(둘 다 조각이면 유지)

        if pset is None:
            hint = ("한글(HWP) 문서에서 영어 지문을 찾지 못했습니다. 지문이 이미지로 들어 있으면 "
                    "그 부분을 사진(JPG/PNG)으로 저장해 넣어 주세요."
                    if extract.is_hwp(src) else
                    "텍스트를 추출하지 못했습니다(스캔본 PDF일 수 있음). "
                    "해당 페이지를 사진(JPG/PNG)으로 저장해 넣어 주세요.")
            raise ValueError(hint)

    is_b = layout.upper() == "B"
    total = len(pset.passages)
    # 원본에 '31번/32번'처럼 실제 문제 번호가 있으면 지문별 라벨로 사용(순번 31-1 대신).
    pnums = _detect_problem_numbers(src) if not extract.is_image(src) else []
    out: list[Analysis] = []
    for i, ex in enumerate(pset.passages, start=1):
        h = header.for_passage(ex, i, total)
        if len(pnums) == total and pnums[i - 1]:
            h.lecture_label = pnums[i - 1]      # 실제 문제 번호(예: 31, 32)
        out.append(analyze_text(client, ex.body, h, max_retries=max_retries,
                                with_back=not is_b, with_literal=is_b))
    return out


# 원본 머리글의 문제 번호 패턴(우선순위 순):
#  ① 'N번:' / 'N번 :' — 문제 제목 머리글(예: '… – 30번: 소유가 …')
#  ② 줄 맨 앞 'N번 …'   — (예: '31번 2026년 …')
_PROBNO_COLON = re.compile(r"(\d{1,3})\s*번\s*[:：]")
_PROBNO_LINE = re.compile(r"(?m)^\s*(\d{1,3})\s*번(?![가-힣:：])")


def _detect_problem_numbers(src: Path) -> list[str]:
    """원본(PDF/HWP) 머리글에서 '30번'·'31번' 같은 실제 문제 번호를 순서대로 뽑는다.

    'N번:'(제목 머리글)을 우선 찾고, 없으면 줄 맨 앞 'N번'을 찾는다.
    한글 제거 전 원문에서 찾는다(제거 후엔 '번'이 사라짐). 못 찾으면 빈 리스트.
    """
    from .. import extract
    try:
        raw = (extract.extract_hwp_text(src) if extract.is_hwp(src)
               else extract.extract_raw_text(src))
    except Exception:
        return []
    for rex in (_PROBNO_COLON, _PROBNO_LINE):
        seen: list[str] = []
        for m in rex.finditer(raw):
            n = m.group(1)
            if n not in seen:      # 같은 번호가 여러 번 나와도 한 번만
                seen.append(n)
        if seen:
            return seen
    return []


def _extract_via_vision_pdf(client: "ClaudeClient", cfg: "Config", src: Path):
    """PDF 텍스트가 깨졌을 때: 각 페이지를 이미지로 렌더해 비전으로 지문 재추출.

    실패(렌더 불가·비전 실패·지문 없음)하면 None 을 돌려주어 텍스트 경로로 되돌아간다.
    화면에 '보이는 그대로' 읽으므로 폰트 subset/2단/스캔 PDF 에 강하다.
    """
    import tempfile

    from .. import analyze, extract
    from ..schemas import PassageSet

    tmpdir = tempfile.mkdtemp(prefix="wsvision_")
    imgs: list[Path] = []
    try:
        imgs = extract.pdf_to_images(src, tmpdir)
    except Exception:
        return None
    all_passages = []
    for img in imgs:
        try:
            ps = analyze.extract_passages_image(client, cfg, str(img))
            all_passages.extend(ps.passages)
        except Exception:
            continue          # 지문 없는 페이지 등은 건너뜀
    for img in imgs:
        try:
            img.unlink()
        except OSError:
            pass
    if not all_passages:
        return None
    return PassageSet(passages=all_passages)


def mock_analyses_for_file(src: Path, header: Header) -> list[Analysis]:
    """API 없이 목 데이터로 Analysis 반환(디자인 미리보기)."""
    from .mock import mock_analysis

    a = mock_analysis(
        title_en=header.title_en or "The Paradox of Choice",
        lecture_label=header.lecture_label or "20",
        date=header.date or "2025년 09월",
        strength=header.strength,
    )
    if header.title_ko:
        a.title_ko = header.title_ko
    return [a]


# ---------------------------------------------------------------------------
# 렌더
# ---------------------------------------------------------------------------
def render_worksheet(analyses, out_path: str | Path, layout: str = "A",
                     brand: str = "은아 T", footer_note: str = "",
                     engine: str = "auto", footer_meta: str = "",
                     density: str = "auto", student: bool = False,
                     slevel: str = "slash", include_guide: bool = True,
                     boxmode: str = "", include_test: bool = False,
                     only_answer: bool = False, only_test: bool = False,
                     include_back: bool = True) -> Path:
    return renderer.render_pdf(analyses, out_path, layout=layout, brand=brand,
                               footer_note=footer_note, engine=engine,
                               footer_meta=footer_meta, density=density,
                               student=student, slevel=slevel,
                               include_guide=include_guide, boxmode=boxmode,
                               include_test=include_test, only_answer=only_answer,
                               only_test=only_test, include_back=include_back)


def render_worksheet_pair(analyses, out_path: str | Path, layout: str = "A",
                          footer_note: str = "", density: str = "auto",
                          make_student: bool = True, slevel: str = "blank",
                          boxmode: str = "") -> Path:
    """선생님용 + 학생용을 '한 PDF'로 합본한다(복수 지문 시 교사용 전체 → 학생용 전체).

    페이지 순서: [가이드, 지문1 교사, 지문2 교사, …] 다음에 [지문1 학생, 지문2 학생, …].
    make_student=False 면 교사용만 만든다.
    """
    import tempfile

    out_path = Path(out_path)
    # 단어 TEST 는 교사용 뒤에 '한 번만'(어휘가 있는 지문이 하나라도 있으면).
    has_test = any(getattr(a, "vocab", None) for a in analyses)
    from pypdf import PdfWriter

    def _append_test(w, d):
        if not has_test:
            return
        wt = Path(d) / "w.pdf"             # 단어 TEST(지문별, 1회)
        render_worksheet(analyses, wt, layout=layout, footer_note=footer_note,
                         include_guide=False, only_test=True)
        w.append(str(wt))

    def _append_answer(w, d):
        if not has_test:
            return
        ap = Path(d) / "a.pdf"             # 정답(맨 마지막, 페이지 나눔 없이 연속)
        render_worksheet(analyses, ap, layout=layout, footer_note=footer_note,
                         include_guide=False, only_answer=True)
        w.append(str(ap))

    if not make_student:
        # 순서: [교사용 지문분석(+뒷면)] → [단어 TEST] → [정답]
        with tempfile.TemporaryDirectory() as d:
            tp = Path(d) / "t.pdf"
            render_worksheet(analyses, tp, layout=layout, footer_note=footer_note,
                             density=density, include_guide=True, boxmode=boxmode)
            w = PdfWriter()
            w.append(str(tp))
            _append_test(w, d)
            _append_answer(w, d)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                w.write(f)
        _stamp_footer(out_path, footer_note)
        return out_path
    # 순서: [교사용 지문분석(+뒷면)] → [학생용(뒷면 없음)] → [단어 TEST(1회)] → [정답]
    with tempfile.TemporaryDirectory() as d:
        tp, sp = Path(d) / "t.pdf", Path(d) / "s.pdf"
        render_worksheet(analyses, tp, layout=layout, footer_note=footer_note,
                         density=density, student=False, include_guide=True,
                         boxmode=boxmode)
        # 학생용: 가이드·뒷면(어휘 정리) 없이 지문분석 빈칸만
        render_worksheet(analyses, sp, layout=layout, footer_note=footer_note,
                         density=density, student=True, slevel=slevel,
                         include_guide=False, boxmode=boxmode, include_back=False)
        w = PdfWriter()
        w.append(str(tp))                   # 교사용
        w.append(str(sp))                   # 학생용
        _append_test(w, d)                  # 단어 TEST(학생용 뒤 1회)
        _append_answer(w, d)                # 정답(맨 마지막)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            w.write(f)
    _stamp_footer(out_path, footer_note)   # 합본 완성 후 저작권(좌)·페이지번호(우) 스탬프
    return out_path


def _stamp_footer(path: Path, footer_note: str = "") -> None:
    """완성된 PDF 하단 여백에 저작권(왼쪽)·'현재/전체' 페이지 번호(오른쪽)를 찍는다.

    모든 페이지 같은 위치(하단 여백)라 페이지별 내용 높이와 무관하게 정렬된다.
    reportlab 이 없으면 조용히 건너뛴다.
    """
    path = Path(path)
    try:
        import io

        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
        from reportlab.pdfgen import canvas
    except Exception:
        return
    # 본문과 동일하게 나눔스퀘어라운드로 통일(저작권=Regular, 페이지번호=Bold).
    # 폰트 파일이 없거나 등록 실패 시 CID 명조 → Helvetica 순으로 폴백.
    from .renderer import FONT_DIR
    kfont, pfont = "Helvetica", "Helvetica-Bold"
    try:
        pdfmetrics.registerFont(RLTTFont("NSR", str(FONT_DIR / "NanumSquareRoundR.ttf")))
        pdfmetrics.registerFont(RLTTFont("NSR-B", str(FONT_DIR / "NanumSquareRoundB.ttf")))
        kfont, pfont = "NSR", "NSR-B"
    except Exception:
        try:                               # 폴백: 한글 지원 CID 명조
            pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
            kfont = "HYSMyeongJo-Medium"
        except Exception:
            pass
    try:
        reader = PdfReader(str(path))
        total = len(reader.pages)
        writer = PdfWriter()
        gray = (0.55, 0.58, 0.64)
        for i, page in enumerate(reader.pages, start=1):
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(w, h))
            c.setFillColorRGB(*gray)
            if footer_note:
                c.setFont(kfont, 11)
                c.drawString(26, 16, footer_note)          # 왼쪽 하단: 저작권(11pt)
            c.setFont(pfont, 11)
            c.drawRightString(w - 26, 16, f"{i} / {total}")  # 오른쪽 하단: 현재/전체(11pt)
            c.save()
            buf.seek(0)
            page.merge_page(PdfReader(buf).pages[0])
            writer.add_page(page)
        with open(path, "wb") as f:
            writer.write(f)
    except Exception:
        return
