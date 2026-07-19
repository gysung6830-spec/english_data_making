"""BlankWorkbook -> HTML -> PDF (빈칸형 워크북).

- 지문 빈칸(passage): 첫 글자 + 고정 길이 밑줄 + 번호 (초록).
- 요약문 빈칸(summary): 밑줄 + 번호만 (청색), 하단에 단어뱅크 박스.
- HTML -> PDF 는 Playwright(Chromium). (통합 워크북과 동일 엔진 재사용)
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from .blanks_schemas import BlankSet, BlankWorkbook, BSentence
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER

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


def render_bsentence(s: BSentence) -> Markup:
    html = str(escape(s.en_template))
    for b in s.blanks:
        html = html.replace("{{" + b.id + "}}", _blank_html(b.first, b.num, b.css))
    return Markup(html)


def render_summary(st: BlankSet) -> Markup:
    html = str(escape(st.summary_template))
    for b in st.summary_blanks:
        html = html.replace("{{" + b.id + "}}", _blank_html(b.first, b.num, b.css))
    return Markup(html)


_env.filters["render_bsentence"] = render_bsentence
_env.filters["render_summary"] = render_summary


def render_blanks_html(wb: BlankWorkbook, footer_note: str = "") -> str:
    return _env.get_template("blanks.html.j2").render(wb=wb, footer_note=footer_note)


def render_blanks_pdf(wb: BlankWorkbook, out_path: str | Path, footer_note: str = "") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_blanks_html(wb, footer_note)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    footer = footer_note.strip() if footer_note and footer_note.strip() else DEFAULT_FOOTER
    exe = _chromium_executable()
    launch_kw = {"executable_path": exe} if exe else {}
    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kw)
        pg = b.new_page()
        pg.goto(f"file://{html_path.resolve()}")
        pg.pdf(path=str(out_path), format="A4",
               margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=_footer_template(footer))
        b.close()
    return out_path
