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
        t_en, t_ko, summary, summary_easy, vocab, flow, implicit = overview_builder.build_overview(
            client, analysis, max_retries=max_retries)
        analysis.vocab, analysis.flow, analysis.implicit = vocab, flow, implicit
        # 영문 제목·한글 부제는 자동 생성값 우선(사용자 입력 없음)
        analysis.title_en = t_en or analysis.title_en
        analysis.title_ko = t_ko or analysis.title_ko
        analysis.summary = summary or analysis.summary
        analysis.summary_easy = summary_easy or analysis.summary_easy
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

    smart_labels: list[str] | None = None
    if extract.is_image(src):
        pset = analyze.extract_passages_image(client, cfg, str(src))
    else:
        raw = extract.extract_passage_text_any(src)   # PDF · HWP · HWPX
        empty = extract.looks_empty(raw)
        is_pdf = src.suffix.lower() == ".pdf"

        pset = None
        # 0) (신규) 문제번호 단위 추출: 장문(범위 번호)이 반복 페이지머리글로 쪼개지거나,
        #    지문 수가 많아 일괄 처리 토큰 한도에 걸려 뒤 지문이 통째로 누락되는 것을 막는다.
        #    문제 경계(≥2)를 못 찾으면 아래 기존 단일 호출로 폴백.
        if not empty and client is not None:
            smart = _extract_passages_by_problem(client, cfg, src, max_retries=max_retries)
            if smart is not None:
                pset, smart_labels = smart

        # 1) 텍스트 경로(단일 호출) — 스마트 경로가 적용되지 않았을 때만.
        if pset is None and not empty:
            pset = analyze.extract_passages(client, cfg, raw)

        # 2) 텍스트가 비었거나(스캔) 결과가 조각나 보이면 → PDF는 페이지를 이미지로
        #    렌더해 비전으로 재추출(폰트 subset·2단·스캔 등으로 문장 앞부분이 잘리는 경우).
        #    비전은 '문제 파일에만' 조건부(설정 quality.vision_fallback, 기본 켜짐).
        #    문제 단위 추출이 성공했으면(smart_labels) 그 결과를 신뢰하고 비전 폴백은 건너뛴다.
        vision_on = getattr(getattr(cfg, "quality", None), "vision_fallback", True)
        if (smart_labels is None and is_pdf and client is not None and vision_on
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
    # 문제 단위 추출이 성공했으면 그때 얻은 라벨(지문과 1:1 정렬)을 그대로 쓴다.
    if smart_labels is not None:
        pnums = smart_labels
    else:
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
# 범위 표기('43~45번','40-42번' 장문·순서 유형)도 하나의 번호로 인식한다.
# ⚠️ 물결(~)은 공백이 있어도 범위로 보되, 붙임표(-)는 '공백 없이 붙었을 때만' 범위로 본다.
#    ('Unit 10 - 1번' 처럼 단원-문제 구분의 ' - '를 범위 '10~1'로 오인하지 않도록.)
_NUM = r"\d{1,3}(?:\s*[~∼〜]\s*\d{1,3}|[－\-–—]\d{1,3})?"
_PROBNO_COLON = re.compile(rf"({_NUM})\s*번\s*[:：]")
_PROBNO_LINE = re.compile(rf"(?m)^\s*({_NUM})\s*번(?![가-힣:：])")


def _norm_probno(s: str) -> str:
    """'43 ~ 45' 처럼 공백·구분자가 섞인 범위를 '43~45'로 정규화."""
    import re as _re
    s = _re.sub(r"\s+", "", s)
    return _re.sub(r"[∼〜－\-–—]", "~", s)


def _detect_problem_numbers(src: Path) -> list[str]:
    """원본(PDF/HWP) 머리글에서 '30번'·'43~45번' 같은 실제 문제 번호를 순서대로 뽑는다.

    'N번:'(제목 머리글)을 우선 찾고, 없으면 줄 맨 앞 'N번'을 찾는다.
    장문·순서 유형의 범위 표기('43~45번')는 하나의 라벨로 취급한다.
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
            n = _norm_probno(m.group(1))
            if n not in seen:      # 같은 번호가 여러 번 나와도 한 번만
                seen.append(n)
        if seen:
            return seen
    return []


# 단원형 머리글: '{Unit|Ch|Lesson} N - {M번 | ANALYSIS | 서술형 | 논술형 …}'(교재 워크북).
# 라벨을 지문마다 유일하게: 'N-M'(M번) · 'N-A'(Analysis) · '서술형'/'논술형'(유형 지문).
#   → 유닛마다 1·2·3이 반복돼도 안 겹치고, Analysis·서술형·논술형 지문도 독립 경계가 된다.
_SEC_HDR = re.compile(
    r"(?i)\b(?:Unit|Ch(?:apter)?|Lesson)\.?\s*(\d{1,3})\s*[-–—]"
    r"[^\n:：]*?(?:(\d{1,3})\s*번|(서술형)|(논술형)|(ANALYSIS|분석))")


def _sec_label(num: str, prob, seosul, nonsul, ana) -> str | None:
    """머리글 항목을 지문 라벨로. M번→'N-M', Analysis→'N-A', 서술형/논술형→유형명."""
    if prob:
        return f"{num}-{prob}"
    if seosul:
        return "서술형"
    if nonsul:
        return "논술형"
    if ana:
        return f"{num}-A"
    return None


def _unit_spans(raw: str) -> list[tuple[str, str]]:
    """'{Unit|Ch|Lesson} N - 항목' 머리글로 원문을 지문 단위로 잘라 [(라벨, 청크), …].

    라벨 = 'N-M'(M번) · 'N-A'(Analysis) · '서술형'/'논술형'(유형 지문).
    머리글이 2개 미만이면 빈 리스트.
    """
    marks: list[tuple[int, str]] = []
    for m in _SEC_HDR.finditer(raw):
        label = _sec_label(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5))
        if label:
            marks.append((m.start(), label))
    if len(marks) < 2:
        return []
    bounds: list[tuple[int, str]] = []
    for pos, lbl in marks:
        if bounds and bounds[-1][1] == lbl:
            continue                 # 같은 지문의 반복 페이지 머리글 → 새 경계 아님
        bounds.append((pos, lbl))
    if len(bounds) < 2:
        return []
    spans: list[tuple[str, str]] = []
    for i, (pos, lbl) in enumerate(bounds):
        end = bounds[i + 1][0] if i + 1 < len(bounds) else len(raw)
        chunk = raw[pos:end].strip()
        if chunk:
            spans.append((lbl, chunk))
    return spans if len(spans) >= 2 else []


def _problem_spans(raw: str) -> list[tuple[str, str]]:
    """원문(한글 포함)을 '지문 머리글' 경계로 잘라 [(라벨, 청크텍스트), …] 로.

    ① 단원형('Unit 10 - 1번' / 'Unit 10 - Analysis')이 있으면 '유닛-문항'(10-1/10-A)으로
       우선 분리 — 유닛 간 번호 중복·Analysis 흡수를 막는다.
    ② 없으면 '문제번호(N번)' 머리글로 분리(모의고사형). 장문(예: '43~45번')은 본문 중간에
       페이지 머리글('WORKBOOK4')이 반복돼도 한 덩어리로 남고, 첫 머리글 앞의 번호 없는
       선두 지문도 라벨 없는 조각으로 보존한다. 머리글 2개 미만이면 빈 리스트(→ 단일 처리).
    """
    unit = _unit_spans(raw)
    if unit:
        return unit
    for rex in (_PROBNO_COLON, _PROBNO_LINE):
        marks = [(m.start(), _norm_probno(m.group(1))) for m in rex.finditer(raw)]
        if len(marks) < 2:
            continue
        bounds: list[tuple[int, str]] = []
        for pos, lbl in marks:
            if bounds and bounds[-1][1] == lbl:
                continue              # 같은 문제의 반복 머리글 → 새 경계 아님
            bounds.append((pos, lbl))
        if len(bounds) < 2:
            continue
        # 첫 '번' 머리글 앞에 '번호 없는 지문'(예: ANALYSIS 지문·서두 지문)이 있으면
        # 통째로 버리지 말고 라벨 없는 선두 조각으로 살린다(영문이 충분히 있을 때만).
        lead = raw[:bounds[0][0]]
        if sum(1 for c in lead if c.isascii() and c.isalpha()) >= 80:
            bounds.insert(0, (0, ""))
        spans: list[tuple[str, str]] = []
        for i, (pos, lbl) in enumerate(bounds):
            end = bounds[i + 1][0] if i + 1 < len(bounds) else len(raw)
            chunk = raw[pos:end].strip()
            if chunk:
                spans.append((lbl, chunk))
        if len(spans) >= 2:
            return spans
    return []


def _merge_passages(passages, label: str):
    """한 문제 청크에서 나온 지문 조각들을 '한 지문'으로 병합(문단 이어붙임).

    장문이 페이지 머리글 때문에 여러 개로 쪼개져 나와도 하나로 되돌린다.
    빈 문단만 있으면 None.
    """
    from ..schemas import Extraction
    paras: list[str] = []
    title, source = "", ""
    for p in passages:
        for para in getattr(p, "paragraphs", []) or []:
            if para and para.strip():
                paras.append(para.strip())
        if not title and getattr(p, "title", ""):
            title = p.title
        if not source and getattr(p, "source", ""):
            source = p.source
    if not paras:
        return None
    return Extraction(title=title or "Untitled", source=source, paragraphs=paras)


def _extract_passages_by_problem(client, cfg, src: Path, max_retries: int = 1):
    """문제번호 단위로 나눠 각각 추출 → '문제당 한 지문'으로 병합.

    장문이 쪼개지거나(반복 페이지 머리글) 전체 일괄 처리의 토큰 한도로 뒤 지문이
    누락되는 것을 막는다. 경계를 못 찾거나 실패하면 None(→ 호출부가 기존 단일 호출로 폴백).
    반환: (PassageSet, labels) | None
    """
    from .. import analyze, extract
    from ..schemas import PassageSet
    try:
        rawh = (extract.extract_hwp_text(src) if extract.is_hwp(src)
                else extract.extract_raw_text(src))
    except Exception:
        return None
    spans = _problem_spans(rawh)
    if len(spans) < 2:
        return None                     # 문제 경계가 불명확 → 기존 방식이 안전

    def _one(span):
        _label, chunk = span
        try:
            ps = analyze.extract_passages(client, cfg, chunk)
        except Exception:
            return None
        return _merge_passages(getattr(ps, "passages", []) or [], _label)

    try:
        with ThreadPoolExecutor(max_workers=min(6, len(spans))) as ex:
            merged = list(ex.map(_one, spans))
    except Exception:
        return None
    passages, labels = [], []
    for (label, _chunk), m in zip(spans, merged):
        if m is not None:
            passages.append(m)
            labels.append(label)
    if len(passages) < 2:               # 문제 단위 추출이 의미 있으려면 최소 2개
        return None
    return PassageSet(passages=passages), labels


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
                     include_back: bool = True, only_guide: bool = False,
                     only_front: bool = False, only_source: bool = False,
                     only_summary: bool = False, toc: list | None = None) -> Path:
    return renderer.render_pdf(analyses, out_path, layout=layout, brand=brand,
                               footer_note=footer_note, engine=engine,
                               footer_meta=footer_meta, density=density,
                               student=student, slevel=slevel,
                               include_guide=include_guide, boxmode=boxmode,
                               include_test=include_test, only_answer=only_answer,
                               only_test=only_test, include_back=include_back,
                               only_guide=only_guide, only_front=only_front,
                               only_source=only_source, only_summary=only_summary,
                               toc=toc)


def render_worksheet_pair(analyses, out_path: str | Path, layout: str = "A",
                          footer_note: str = "", density: str = "auto",
                          make_student: bool = True, slevel: str = "blank",
                          boxmode: str = "") -> Path:
    """섹션을 재배치해 '한 PDF'로 합본하고, 활용 가이드에 페이지 목차를 싣는다.

    페이지 순서:
      ① 활용 가이드(+목차)  ② 지문 분석  ③ 정리(논리흐름·함축·어휘)
      ④ 단어 테스트  ⑤ 정답  ⑥ 학습용(빈칸)  ⑦ 원문(지문별 페이지 나눔)

    각 섹션을 개별 렌더해 페이지 수를 세고, 시작 페이지로 목차를 만든 뒤 가이드에 실어
    맨 앞에 붙인다. make_student=False 면 학습용(⑥)을 생략한다.
    """
    import tempfile

    from pypdf import PdfReader, PdfWriter

    out_path = Path(out_path)
    has_test = any(getattr(a, "vocab", None) for a in analyses)
    has_back = any(getattr(a, "has_back", False) for a in analyses)
    has_source = any(getattr(a, "sentences", None) for a in analyses)

    def _pages(p: Path) -> int:
        try:
            return len(PdfReader(str(p)).pages)
        except Exception:
            return 0

    with tempfile.TemporaryDirectory() as d:
        dd = Path(d)
        # ── 콘텐츠 섹션을 개별 렌더(가이드 제외). (라벨, 파일, 렌더러 kwargs) ──
        specs: list[tuple[str, Path, dict]] = []
        specs.append(("지문 분석", dd / "front.pdf",
                      dict(density=density, student=False, only_front=True)))
        if has_back:
            specs.append(("정리 (논리 흐름·함축·어휘)", dd / "summary.pdf",
                          dict(only_summary=True)))
        if has_test:
            specs.append(("단어 테스트", dd / "test.pdf", dict(only_test=True)))
            specs.append(("정답", dd / "answer.pdf", dict(only_answer=True)))
        if make_student:
            specs.append(("학습용", dd / "student.pdf",
                          dict(density=density, student=True, slevel=slevel,
                               only_front=True)))
        if has_source:
            specs.append(("원문", dd / "source.pdf", dict(only_source=True)))

        sections: list[tuple[str, Path, int]] = []
        for label, path, kw in specs:
            render_worksheet(analyses, path, layout=layout, footer_note=footer_note,
                             include_guide=False, boxmode=boxmode, **kw)
            n = _pages(path)
            if n > 0:
                sections.append((label, path, n))

        # ── 목차: 가이드 다음 페이지부터 각 섹션 시작 페이지 계산(가이드 길이 G 반영) ──
        def _build_toc(guide_pages: int) -> list[dict]:
            toc, pg = [], guide_pages + 1
            for label, _p, n in sections:
                toc.append({"label": label, "page": pg})
                pg += n
            return toc

        gp = dd / "guide.pdf"
        # 가이드는 보통 1페이지 — 우선 1페이지 가정으로 목차를 넣어 렌더한 뒤 실제 길이 확인.
        render_worksheet(analyses, gp, layout=layout, footer_note=footer_note,
                         include_guide=True, only_guide=True, toc=_build_toc(1))
        real_g = _pages(gp)
        if real_g != 1:                    # 가이드가 2페이지 이상이면 목차 페이지 재계산
            render_worksheet(analyses, gp, layout=layout, footer_note=footer_note,
                             include_guide=True, only_guide=True,
                             toc=_build_toc(real_g))

        w = PdfWriter()
        w.append(str(gp))
        for _label, path, _n in sections:
            w.append(str(path))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            w.write(f)
    # 교재명·단원(모의고사면 시행연월·학년) — 여러 자료 병행 수업 현장에서 페이지마다 출처 표기.
    meta = next((a.source_name for a in analyses if getattr(a, "source_name", "")), "")
    _stamp_footer(out_path, footer_note, meta)   # 저작권(좌)·교재명(중앙)·페이지번호(우)
    return out_path


def _stamp_footer(path: Path, footer_note: str = "", meta: str = "") -> None:
    """완성된 PDF 하단 여백에 저작권(왼쪽)·교재명·단원(가운데)·페이지 번호(오른쪽)를 찍는다.

    meta 는 '교재명·단원'(모의고사면 시행연월·학년)으로, 여러 자료를 함께 쓰는 수업 현장에서
    페이지마다 출처를 알 수 있게 가운데에 표기한다. 모든 페이지 같은 위치(하단 여백)라
    페이지별 내용 높이와 무관하게 정렬된다. reportlab 이 없으면 조용히 건너뛴다.
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
            if meta:
                c.setFont(kfont, 10)
                c.drawCentredString(w / 2, 16, meta)       # 가운데 하단: 교재명·단원(10pt)
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
