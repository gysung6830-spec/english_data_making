"""영작 워크북 (문장 속 '영작 포인트' 어구만 곳곳을 배열).

문장 전체를 단어 배열하는 것이 아니라, 한 문장에서 학생이 자주 틀리는 핵심 어구
(부분부정, 비교구문, 관계사절, to부정사 어순, 관용표현 등)만 골라 그 자리에서만
어순을 뒤섞어 〈 … 〉 로 제시한다. 나머지 문장은 그대로 주어 발판을 준다.
우리말 뜻을 보고 각 〈 … 〉 를 바르게 배열하면 문장이 완성된다.
HTML → PDF 는 Playwright(Chromium).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from .blanks_schemas import placeholders_in  # {{An}} 재사용
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"


# ── 데이터 모델 ──────────────────────────────────────────────────────
@dataclass
class WItem:
    id: str            # "A1"
    display: str       # 뒤섞은 어구: "〈 on the surroundings / to / itself / impose 〉"
    answer: str        # 바른 배열: "to impose itself on the surroundings"


@dataclass
class WSentence:
    no: int
    template: str      # {{A1}} 자리표시자 포함(나머지는 원문 그대로)
    ko: str            # 우리말 뜻(영작의 길잡이)
    items: list[WItem] = field(default_factory=list)


@dataclass
class WritingPack:
    header: str
    title: str
    subtitle: str
    instruction: str
    sentences: list[WSentence]


# ── 렌더 ─────────────────────────────────────────────────────────────
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)),
                   autoescape=select_autoescape(["html", "xml", "j2"]))


def _item_html(it: WItem) -> str:
    return f'<span class="wo">{escape(it.display)}</span>'


def render_writing(s: WSentence) -> Markup:
    import re
    html = str(escape(s.template))
    by_id = {it.id: it for it in s.items}
    for aid in placeholders_in(s.template):
        it = by_id.get(aid)
        if it:
            html = html.replace("{{" + aid + "}}", _item_html(it))
    html = re.sub(r"\{\{\s*\w+\s*\}\}", "", html)   # 남은 자리표시자 정리
    return Markup(html)


_env.filters["render_writing"] = render_writing


def render_writing_html(pack: WritingPack, footer_note: str = "") -> str:
    from . import branding
    return _env.get_template("writing.html.j2").render(
        pack=pack, footer_note=footer_note, font_css=branding.font_face_css())


def render_writing_pdf(pack: WritingPack, out_path: str | Path, footer_note: str = "") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_writing_html(pack, footer_note)
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
               margin={"top": "12mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=_footer_template(footer))
        b.close()
    return out_path
