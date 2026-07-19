"""레이아웃 A (분석 학습지형) 렌더러 — 명세서 §10-2.

공통 렌더링 로직은 renderer.py 에 있고, 여기서는 A 전용 진입점만 노출한다.
"""
from __future__ import annotations

from pathlib import Path

from .renderer import render_a_html, render_pdf


def render_html(analyses, footer_note: str = "") -> str:
    return render_a_html(analyses, footer_note=footer_note)


def render(analyses, out_path: str | Path, footer_note: str = "",
           engine: str = "auto") -> Path:
    return render_pdf(analyses, out_path, layout="A", footer_note=footer_note, engine=engine)
