"""단일 유형 산문 워크시트 (어법 양자택일 / 어형 변형 / 어휘 양자택일).

지문 전체를 산문(번호 매긴 문장 목록)으로 두고, 한 가지 기능의 표기만 인라인으로 넣는다.
  - 어형 변형(form): (동사원형) + 쓰는 밑줄
  - 어법·어휘 양자택일(choice): [ A / B ] 박스
HTML → PDF 는 Playwright(Chromium).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from .blanks_schemas import placeholders_in  # {{Pn}} 재사용
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"


# ── 데이터 모델 ──────────────────────────────────────────────────────
@dataclass
class PItem:
    id: str            # "P1"
    display: str       # "(understand)" | "[ that / what ]"
    answer: str
    write: bool = False  # 어형 변형이면 쓰는 밑줄 표시


@dataclass
class PSentence:
    no: int
    template: str      # 인라인 {{P1}} 포함
    ko: str
    items: list[PItem] = field(default_factory=list)


@dataclass
class ProseWorksheet:
    wtype: str         # form | grammar | vocab
    label: str         # "어형 변형" 등
    instruction: str
    sentences: list[PSentence]


@dataclass
class ProsePack:
    header: str        # "[2026] 3월 모의고사 3학년 29번" 같은 상단 메타
    title: str
    subtitle: str
    worksheets: list[ProseWorksheet]


# ── 렌더 ─────────────────────────────────────────────────────────────
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)),
                   autoescape=select_autoescape(["html", "xml", "j2"]))

_WCLASS = {"form": "wf", "grammar": "wg", "vocab": "wv"}


def _item_html(it: PItem, wtype: str) -> str:
    if it.write:  # 어형 변형: (원형) + 쓰는 밑줄
        return (f'<span class="pf">{escape(it.display)}</span>'
                f'<span class="pw"></span>')
    # 양자택일: [ A / B ] 박스
    cls = _WCLASS.get(wtype, "wg")
    return f'<span class="pc {cls}">{escape(it.display)}</span>'


def render_prose(s: PSentence, wtype: str) -> Markup:
    html = str(escape(s.template))
    by_id = {it.id: it for it in s.items}
    for pid in placeholders_in(s.template):
        it = by_id.get(pid)
        if it:
            html = html.replace("{{" + pid + "}}", _item_html(it, wtype))
    return Markup(html)


_env.filters["render_prose"] = render_prose


def render_prose_html(pack: ProsePack, footer_note: str = "") -> str:
    return _env.get_template("prose.html.j2").render(pack=pack, footer_note=footer_note)


def render_prose_pdf(pack: ProsePack, out_path: str | Path, footer_note: str = "") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_prose_html(pack, footer_note)
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
