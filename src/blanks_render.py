"""BlankWorkbook -> HTML -> PDF (빈칸형 워크북).

- 지문 빈칸(passage): 첫 글자 + 고정 길이 밑줄 + 번호 (초록).
- 요약문 빈칸(summary): 밑줄 + 번호만 (청색), 하단에 단어뱅크 박스.
- HTML -> PDF 는 Playwright(Chromium). (통합 워크북과 동일 엔진 재사용)
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from . import branding
from .blanks_schemas import BlankSet, BlankWorkbook, BSentence
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER, _page_ready

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)


def _blank_html(first: str, num: int, css: str) -> str:
    """첫 글자(있으면) + 고정 길이 밑줄 + 위첨자 번호."""
    head = escape(first) if first else ""
    return (f'<span class="blk {css}">{head}<span class="ul"></span></span>'
            f'<sup class="bn">{num})</sup>')


def _strip_placeholders(html: str) -> str:
    import re
    return re.sub(r"\{\{\s*\w+\s*\}\}", "", html)


def render_bsentence(s: BSentence) -> Markup:
    html = str(escape(s.en_template))
    for b in s.blanks:
        html = html.replace("{{" + b.id + "}}", _blank_html(b.first, b.num, b.css))
    return Markup(_strip_placeholders(html))


def render_summary(st: BlankSet) -> Markup:
    html = str(escape(st.summary_template))
    for b in st.summary_blanks:
        html = html.replace("{{" + b.id + "}}", _blank_html(b.first, b.num, b.css))
    return Markup(_strip_placeholders(html))


_env.filters["render_bsentence"] = render_bsentence
_env.filters["render_summary"] = render_summary


def render_blanks_html(wb: BlankWorkbook, footer_note: str = "", show_ko: bool = True,
                       section: str = "all") -> str:
    return _env.get_template("blanks.html.j2").render(
        wb=wb, footer_note=footer_note, show_ko=show_ko, section=section,
        font_css=branding.font_face_css())


# 한 지문(section.set)이 한 페이지를 살짝 넘겨 워드뱅크만 다음 장으로 밀리는 것을 막는다.
#   지문 블록 높이가 A4 인쇄영역(≈267mm=약 1005px)을 넘으면 zoom 을 줄여 '한 페이지'에 담는다.
#   가독성 하한(0.72)까지만 줄이고, 그래도 넘치면 자연스럽게 페이지가 나뉜다.
_FIT_SETS_JS = """() => {
  const PAGE_H = 1005;   // A4(297mm) - 상단14mm - 하단16mm ≈ 267mm 를 px 로
  const FLOOR = 0.72;
  document.querySelectorAll('section.set').forEach(set => {
    set.style.zoom = '';
    const h = set.scrollHeight;
    if (h > PAGE_H) set.style.zoom = Math.max(FLOOR, (PAGE_H - 6) / h);
  });
}"""


def _fit_sets_to_page(pg) -> None:
    """지문 블록이 한 페이지를 넘기면 축소해 한 장에 담는다(실패해도 무시)."""
    try:
        pg.evaluate(_FIT_SETS_JS)
    except Exception:
        pass


def render_blanks_pdf(wb: BlankWorkbook, out_path: str | Path, footer_note: str = "",
                      show_ko: bool = True, section: str = "all") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_blanks_html(wb, footer_note, show_ko=show_ko, section=section)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    footer = footer_note.strip() if footer_note and footer_note.strip() else DEFAULT_FOOTER
    exe = _chromium_executable()
    launch_kw = {"executable_path": exe} if exe else {}
    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kw)
        # 뷰포트 폭을 'A4 인쇄영역 폭(182mm≈688px)'에 맞춰야 화면 측정값이 실제 인쇄 줄바꿈과
        # 일치한다(그래야 지문 높이 계산이 정확해 한 페이지 맞춤이 제대로 동작한다).
        pg = b.new_page(viewport={"width": 688, "height": 1009})
        pg.emulate_media(media="print")
        pg.goto(f"file://{html_path.resolve()}")
        _page_ready(pg)
        _fit_sets_to_page(pg)          # 지문 블록을 한 페이지에 맞춤(워드뱅크 분리 방지)
        pg.pdf(path=str(out_path), format="A4",
               margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=_footer_template(footer))
        b.close()
    return out_path
