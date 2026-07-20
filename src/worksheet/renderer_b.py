"""레이아웃 B (직독직해형) 렌더러 — 명세서 §10-3, §7.

같은 Analysis 를 공유하고 렌더러만 분기한다. 영어 원문을 의미 단위(청크)로 끊어
직독직해와 대응시키고 문장별 핵심 문법·핵심 단어를 함께 싣는다.
"""
from __future__ import annotations

from pathlib import Path

from .renderer import render_b_html, render_pdf


def render_html(analyses, footer_note: str = "", brand: str = "은아 T") -> str:
    return render_b_html(analyses, footer_note=footer_note, brand=brand)


def render(analyses, out_path: str | Path, footer_note: str = "",
           brand: str = "은아 T", engine: str = "auto") -> Path:
    return render_pdf(analyses, out_path, layout="B", footer_note=footer_note,
                      brand=brand, engine=engine)
