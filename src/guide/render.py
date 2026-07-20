"""Guide -> HTML -> PDF (Jinja2 + WeasyPrint). 실전서 전용 렌더러."""
from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

_DIR_BADGE = {
    "forward": "정방향 A→B",
    "backward": "역방향 B←A",
}


def _dir_label(d: str | None) -> str:
    return _DIR_BADGE.get(d or "", "")


_env.filters["dir_label"] = _dir_label


def _highlight(sentence: str, hit: str | None) -> Markup:
    """기출 문장에서 코드 어구(hit)를 하이라이트 <span> 으로 감싼다."""
    if not sentence:
        return Markup("")
    if not hit:
        return escape(sentence)
    idx = sentence.lower().find(hit.lower())
    if idx < 0:
        return escape(sentence)
    before, mid, after = sentence[:idx], sentence[idx:idx + len(hit)], sentence[idx + len(hit):]
    return Markup(
        str(escape(before))
        + '<span class="code-hit">' + str(escape(mid)) + "</span>"
        + str(escape(after))
    )


_env.filters["highlight_code"] = _highlight


def render_html(guide, sample: bool = False, footer_note: str = "") -> str:
    tmpl = _env.get_template("guide.html.j2")
    # 챕터 번호 매기기
    return tmpl.render(guide=guide, sample=sample, footer_note=footer_note,
                       enumerate=enumerate)


def render_pdf(guide, out_path: str | Path, sample: bool = False,
               footer_note: str = "") -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(guide, sample=sample, footer_note=footer_note)
    css = CSS(filename=str(TEMPLATE_DIR / "guide.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
    return out_path
