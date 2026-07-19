"""3형식 HTML 렌더링.

- render_format_a : 한줄해석  (영어 문장 + 바로 아래 회색박스 한글해석)
- render_format_c : 한줄영어  (영어 문장만)
- render_format_b : 좌지문 우해석 (좌 영어 / 우 한글 2단 표)

각 지문은 <div class="passage" id="passage-N"> 로 감싸며, auto-fit(main.py)이
이 id 로 높이를 측정한다.
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


def _passage_open(idx: int, p: Passage) -> str:
    parts = [f'<div class="passage" id="passage-{idx}">']
    if p.label:
        parts.append(f'<div class="p-label">{escape(p.label)}</div>')
    if p.title:
        parts.append(f'<div class="p-title">{escape(p.title)}</div>')
    return "\n".join(parts)


def render_format_a(passages: List[Passage], header_text: str = "", theme: str = "") -> str:
    """한줄해석: 영어 문장 + 바로 아래 회색박스 한글해석."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_open(i, p)]
        for s in p.sentences:
            num = _circled(s.num)
            ko = f'<span class="ko">{escape(s.ko)}</span>' if s.ko else ""
            chunk.append(
                '<div class="sent">'
                f'<span class="en"><span class="num">{num}</span>{escape(s.en)}</span>'
                f'{ko}'
                '</div>'
            )
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)


def render_format_c(passages: List[Passage], header_text: str = "", theme: str = "") -> str:
    """한줄영어: 영어 문장만 (해석 없음)."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_open(i, p)]
        for s in p.sentences:
            num = _circled(s.num)
            chunk.append(
                '<div class="sent">'
                f'<span class="en"><span class="num">{num}</span>{escape(s.en)}</span>'
                '</div>'
            )
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)


def render_format_b(passages: List[Passage], header_text: str = "", theme: str = "") -> str:
    """좌지문 우해석: 좌 영어 / 우 한글 2단 표."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_open(i, p)]
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
