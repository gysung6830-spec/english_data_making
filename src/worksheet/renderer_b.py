"""레이아웃 B (대조표형) 렌더러 — 명세서 §10-3, §7.

같은 Analysis 를 공유하고 렌더러만 분기한다. tagged=True 면 A 의 구문 태깅을
영어칸에 얹을 수 있다(옵션).
"""
from __future__ import annotations

from pathlib import Path

from .renderer import render_b_html, render_pdf


def render_html(analyses, footer_note: str = "", tagged: bool = False) -> str:
    return render_b_html(analyses, footer_note=footer_note, tagged=tagged)


def render(analyses, out_path: str | Path, footer_note: str = "",
           tagged: bool = False, engine: str = "auto") -> Path:
    return render_pdf(analyses, out_path, layout="B", footer_note=footer_note,
                      tagged=tagged, engine=engine)
