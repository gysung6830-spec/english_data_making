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


import re as _re

_NUM_IN_LABEL = _re.compile(r"(\d+(?:\s*[~∼\-]\s*\d+)?)\s*번")


def _short_num(label: str) -> str:
    """라벨에서 '지문번호'만 뽑는다. 'N번' 있으면 'N번', 없으면 라벨 그대로."""
    if not label:
        return ""
    m = _NUM_IN_LABEL.search(label)
    return f"{m.group(1)}번" if m else label.strip()


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


def _is_long_label(label: str) -> bool:
    """장문(범위) 라벨인지: 'N~M번'처럼 번호 범위면 True."""
    return bool(_re.search(r"\d+\s*[~∼\-]\s*\d+", label or ""))


def _passage_head(idx: int, p: Passage, doc_name: str = "") -> str:
    """지문 여는 태그 + 머리(뱃지 '파일명 지문번호' + 지문주제)."""
    cls = "passage long" if _is_long_label(p.label) else "passage"
    parts = [f'<div class="{cls}" id="passage-{idx}">']
    # 뱃지 = 파일명 + 지문번호(라벨)
    bits = []
    if doc_name and doc_name.strip():
        bits.append(doc_name.strip())
    num = _short_num(p.label)
    if num:
        bits.append(num)
    badge = " ".join(bits)
    title = p.title
    if badge or title:
        inner = ""
        if badge:
            inner += f'<span class="p-badge">{escape(badge)}</span>'
        if title:
            inner += f'<span class="p-title">{escape(title)}</span>'
        parts.append(f'<h2 class="p-head">{inner}</h2>')
    return "\n".join(parts)


def _vocab_box(p: Passage) -> str:
    """지문 하단 어휘 리스트 박스. 어휘가 있을 때만 렌더(없으면 박스 없음)."""
    if not p.vocab:
        return ""
    items = []
    for v in p.vocab:
        items.append(
            '<div class="vocab-item">'
            f'<span class="w">{escape(v.word)}</span>'
            f'<span class="m">{escape(v.meaning)}</span>'
            '</div>'
        )
    return (
        '<div class="vocab">'
        '<div class="vocab-title">핵심 어휘</div>'
        f'<div class="vocab-grid">{"".join(items)}</div>'
        '</div>'
    )


def render_format_a(passages: List[Passage], header_text: str = "", theme: str = "", doc_name: str = "") -> str:
    """한줄해석: 영어 문장 + 바로 아래 회색박스 한글해석(같은 번호 표기)."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_head(i, p, doc_name)]
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
        chunk.append(_vocab_box(p))
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)


def render_format_c(passages: List[Passage], header_text: str = "", theme: str = "", doc_name: str = "") -> str:
    """한줄영어: 영어 문장만 (해석 없음)."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_head(i, p, doc_name)]
        for s in p.sentences:
            num = _circled(s.num)
            chunk.append(
                '<div class="sent"><div class="en">'
                f'<span class="num">{num}</span>{escape(s.en)}'
                '</div></div>'
            )
        chunk.append(_vocab_box(p))
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)


def render_format_b(passages: List[Passage], header_text: str = "", theme: str = "", doc_name: str = "") -> str:
    """좌지문 우해석: 좌 영어 / 우 한글 2단 표(우측엔 번호 없음)."""
    css = get_css(theme)
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        chunk = [_passage_head(i, p, doc_name)]
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
        chunk.append(_vocab_box(p))
        chunk.append("</div>")
        blocks.append("\n".join(chunk))
    return _doc("\n".join(blocks), css, header_text)


def render_format_d(passages: List[Passage], header_text: str = "", theme: str = "", doc_name: str = "") -> str:
    """직독직해: 한줄해석 디자인 그대로 + 영어 문장에 ' / '로 의미 단위 표시.

    청크가 있으면 청크 경계마다 ' / '를 넣고, 없으면(키 없이 생성 안 됨)
    그냥 한줄해석과 동일하게 표시(폴백). 해석은 문장 전체 번역(회색박스).
    """
    css = get_css(theme)
    sep = '<span class="slash">/</span>'
    join = f" {sep} "
    blocks: List[str] = []
    for i, p in enumerate(passages, start=1):
        out = [_passage_head(i, p, doc_name)]
        for s in p.sentences:
            num = _circled(s.num)
            if s.chunks:
                en_html = join.join(escape(c.en) for c in s.chunks)
                # 청크별 뜻이 있으면 한글도 / 로 끊어 맞춤, 없으면 문장 전체 해석
                if any(c.ko for c in s.chunks):
                    ko_html = join.join(escape(c.ko) for c in s.chunks)
                else:
                    ko_html = escape(s.ko)
            else:
                en_html = escape(s.en)
                ko_html = escape(s.ko)
            en = f'<div class="en"><span class="num">{num}</span>{en_html}</div>'
            ko = ""
            if ko_html:
                ko = ('<div class="ko-box"><span class="ko">'
                      f'<span class="num">{num}</span>{ko_html}</span></div>')
            out.append(f'<div class="sent">{en}{ko}</div>')
        out.append(_vocab_box(p))
        out.append("</div>")
        blocks.append("\n".join(out))
    return _doc("\n".join(blocks), css, header_text)
