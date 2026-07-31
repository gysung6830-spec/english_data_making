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
        t_en, t_ko, vocab, flow = overview_builder.build_overview(
            client, analysis, max_retries=max_retries)
        analysis.vocab, analysis.flow = vocab, flow
        # 영문 제목·한글 부제는 자동 생성값 우선(사용자 입력 없음)
        analysis.title_en = t_en or analysis.title_en
        analysis.title_ko = t_ko or analysis.title_ko
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


# 원본 머리글의 문제 번호: 줄 맨 앞 "31번 …", "32번 …"
_PROBNO_RE = re.compile(r"(?m)^\s*(\d{1,3})\s*번(?![가-힣])")


def _detect_problem_numbers(src: Path) -> list[str]:
    """원본(PDF/HWP) 머리글에서 '31번/32번' 같은 실제 문제 번호를 순서대로 뽑는다.

    한글 제거 전 원문에서 찾는다(제거 후엔 '번'이 사라짐). 못 찾으면 빈 리스트.
    """
    from .. import extract
    try:
        raw = (extract.extract_hwp_text(src) if extract.is_hwp(src)
               else extract.extract_raw_text(src))
    except Exception:
        return []
    seen: list[str] = []
    for m in _PROBNO_RE.finditer(raw):
        n = m.group(1)
        if n not in seen:          # 같은 번호가 여러 줄 반복돼도 한 번만
            seen.append(n)
    return seen


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
                     slevel: str = "slash") -> Path:
    return renderer.render_pdf(analyses, out_path, layout=layout, brand=brand,
                               footer_note=footer_note, engine=engine,
                               footer_meta=footer_meta, density=density,
                               student=student, slevel=slevel)
