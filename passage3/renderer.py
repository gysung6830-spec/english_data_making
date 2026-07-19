"""3형식 HTML 렌더링.

- render_format_a : 한줄해석  (영어 문장 + 바로 아래 회색박스 한글해석)
- render_format_c : 한줄영어  (영어 문장만)
- render_format_b : 좌지문 우해석 (좌 영어 / 우 한글 2단 표)

각 지문은 <div class="passage" id="passage-N"> 로 감싸며, auto-fit(main.py)이
이 id 로 높이를 측정한다. 지문 머리(라벨+제목)는 .p-head 한 줄로 합쳐
왼쪽 세로 강조 막대와 함께 표시한다.
"""
from __future__ import annotations

from html import escape
from typing import List

try:
    from .parser import Passage
    from .themes import get_css
except ImportError:  # 스크립트로 직접 실행할 때(python main.py)
    from parser import Passage
    from themes import get_css


def _circled(num: int) -> str:
    """정수 → 원문자. 범위 밖이면 'N.' 형태."""
    if 1 <= num <= 20:
        return chr(0x2460 + num - 1)
    return f"{num}."


def _doc(body_html: str, css: str, header_text: str) -> str:
    header = ""
    if header_text.strip():
        header = f'<div class="doc-header">{escape(header_text.strip())}</div>'
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
{css}
</style>
</head>
<body>
{header}
{body_html}
</body>
</html>"""


def _passage_head(idx: int, p: Passage) -> str:
    """지문 여는 태그 + 머리(라벨: 제목) 한 줄."""
    parts = [f'<div class="passage" id="passage-{idx}">']
    label = escape(p.label) if p.label else ""
    title = escape(p.title) if p.title else ""
    if label or title:
        # 지문명(라벨)과 지문주제(제목)를 각각 한 줄씩(줄바꿈)으로.
        inner = ""
        if label:
            inner += f'<span class="p-label">{label}</span>'
        if title:
            inner += f'<span class="p-title">{title}</span>'
        parts.append(f'<h2 class="p-head">{inner}</h2>')
    return "\n".join(parts)


def render_format_a(passages: List[Passage], header_text: str = "", theme: str = "") -> str:
    """한줄해석: 영어 문장 + 바로 아래 회색박스 한글해석(같은 번호 표기)."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_head(i, p)]
        for s in p.sentences:
            num = _circled(s.num)
            en = (
                '<div class="en">'
                f'<span class="num">{num}</span>{escape(s.en)}'
                '</div>'
            )
            ko = ""
            if s.ko:
                ko = (
                    '<div class="ko-box"><span class="ko">'
                    f'<span class="num">{num}</span>{escape(s.ko)}'
                    '</span></div>'
                )
            chunk.append(f'<div class="sent">{en}{ko}</div>')
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)


def render_format_c(passages: List[Passage], header_text: str = "", theme: str = "") -> str:
    """한줄영어: 영어 문장만 (해석 없음)."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_head(i, p)]
        for s in p.sentences:
            num = _circled(s.num)
            chunk.append(
                '<div class="sent"><div class="en">'
                f'<span class="num">{num}</span>{escape(s.en)}'
                '</div></div>'
            )
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)


def render_format_b(passages: List[Passage], header_text: str = "", theme: str = "") -> str:
    """좌지문 우해석: 좌 영어 / 우 한글 2단 표(우측엔 번호 없음)."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_head(i, p)]
        chunk.append('<table class="two-col"><tbody>')
        for s in p.sentences:
            num = _circled(s.num)
            chunk.append(
                '<tr class="sent">'
                f'<td class="col-en"><span class="num">{num}</span>{escape(s.en)}</td>'
                f'<td class="col-ko">{escape(s.ko)}</td>'
                '</tr>'
            )
        chunk.append('</tbody></table>')
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)
