"""구문 분석 학습지 파이프라인 오케스트레이션 (명세서 §5).

    loader → splitter → analyzer(LLM) → point_builder(LLM) → renderer → PDF

기존 입력 로더(src/extract.py)와 지문 분리(src/analyze.py)를 재사용한다.
API 없이 배관을 확인할 수 있는 규칙기반/목 경로도 함께 제공한다.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from . import analyzer, overview_builder, point_builder, renderer, splitter
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
                 parallel: bool = True, with_back: bool = True) -> Analysis:
    """지문 텍스트 하나를 문장 단위로 태깅+포인트 생성하여 Analysis 로.

    with_back=True 면 뒷페이지(어휘 리스트/논리 흐름도/쉬운 예시)도 함께 생성한다.
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
        analysis.vocab, analysis.flow = overview_builder.build_overview(
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
                            header: Header, max_retries: int = 1) -> list[Analysis]:
    """한 파일에서 지문(들)을 추출해 각각 Analysis 로."""
    from .. import analyze, extract  # 지연 임포트(pdfplumber/anthropic 무거움)

    if extract.is_image(src):
        pset = analyze.extract_passages_image(client, cfg, str(src))
    else:
        raw = extract.extract_passage_text(src)
        if extract.looks_empty(raw):
            raise ValueError(
                "텍스트를 추출하지 못했습니다(스캔본 PDF일 수 있음). "
                "해당 페이지를 사진(JPG/PNG)으로 저장해 넣어 주세요."
            )
        pset = analyze.extract_passages(client, cfg, raw)

    total = len(pset.passages)
    out: list[Analysis] = []
    for i, ex in enumerate(pset.passages, start=1):
        h = header.for_passage(ex, i, total)
        out.append(analyze_text(client, ex.body, h, max_retries=max_retries))
    return out


def mock_analyses_for_file(src: Path, header: Header) -> list[Analysis]:
    """API 없이 목 데이터로 Analysis 반환(디자인 미리보기)."""
    from .mock import mock_analysis

    a = mock_analysis(
        title_en=header.title_en or "The Paradox of Choice",
        lecture_label=header.lecture_label or "20",
        date=header.date or "2025년 09월",
    )
    if header.title_ko:
        a.title_ko = header.title_ko
    return [a]


# ---------------------------------------------------------------------------
# 렌더
# ---------------------------------------------------------------------------
def render_worksheet(analyses, out_path: str | Path, layout: str = "A",
                     tagged: bool = False, footer_note: str = "",
                     engine: str = "auto", footer_meta: str = "") -> Path:
    return renderer.render_pdf(analyses, out_path, layout=layout, tagged=tagged,
                               footer_note=footer_note, engine=engine,
                               footer_meta=footer_meta)
