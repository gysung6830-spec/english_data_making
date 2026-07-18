"""Workbook -> HTML -> PDF.

- 문제 표기 치환(render_sentence)은 Python 에서 처리한다.
  en_template 안의 {{Qn}} 자리표시자를 Jinja 가 변수로 오해하지 않도록, 렌더 전에 안전한
  HTML(Markup)로 바꿔 템플릿에 넘긴다.
- HTML -> PDF 는 Playwright(Chromium)로 렌더한다. (spec 4-3: WeasyPrint 미설치,
  LibreOffice 는 CSS 지원 부족.)
"""
from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from .workbook_schemas import Question, Sentence, Workbook

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)


def _chunk_html(q: Question) -> str:
    """한 문항의 문제 표기 HTML (spec 4-4).

    <span class="{cls}">{display}</span><span class="lbl {cls}">{label}</span><sup>{num})</sup>
    display 는 이스케이프하여 안전하게 삽입한다.
    """
    cls = q.css
    return (
        f'<span class="q {cls}">{escape(q.display)}</span>'
        f'<span class="lbl {cls}">{escape(q.label)}</span>'
        f'<sup class="qn">{q.num})</sup>'
    )


def render_sentence(s: Sentence) -> Markup:
    """en_template 의 {{Qn}} 자리표시자를 문제 표기 HTML 로 치환한 안전 HTML.

    자리표시자 이외의 문장 텍스트는 이스케이프하여 원문을 그대로 노출한다.
    """
    html = str(escape(s.en_template))   # 브레이스는 escape 대상이 아니므로 {{Qn}} 은 그대로 남는다
    for q in s.questions:
        html = html.replace("{{" + q.id + "}}", _chunk_html(q))
    return Markup(html)


_env.filters["render_sentence"] = render_sentence


def render_workbook_html(wb: Workbook, footer_note: str = "") -> str:
    tmpl = _env.get_template("workbook.html.j2")
    return tmpl.render(wb=wb, footer_note=footer_note)


# ---------------------------------------------------------------------------
# Playwright(Chromium) 렌더
# ---------------------------------------------------------------------------
def _chromium_executable() -> str | None:
    """번들 Chromium 실행 파일을 찾는다. 표준 설치면 None(Playwright 기본값 사용)."""
    # 명시적 지정이 있으면 우선
    env = os.environ.get("CHROMIUM_EXECUTABLE") or os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if env and Path(env).exists():
        return env
    # PLAYWRIGHT_BROWSERS_PATH 아래에 미리 설치된 Chromium 을 탐색(관리형 환경 대응)
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    roots = [Path(base)] if base else []
    roots.append(Path("/opt/pw-browsers"))
    for root in roots:
        if not root.is_dir():
            continue
        for pat in ("chromium-*/chrome-linux/chrome", "chromium_headless_shell-*/chrome-linux/headless_shell"):
            hits = sorted(root.glob(pat))
            if hits:
                return str(hits[-1])
    return None


def render_workbook_pdf(wb: Workbook, out_path: str | Path, footer_note: str = "") -> Path:
    """Workbook -> A4 세로 PDF (Playwright/Chromium). 배경색 인쇄 포함."""
    from playwright.sync_api import sync_playwright  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = render_workbook_html(wb, footer_note)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    exe = _chromium_executable()
    launch_kw = {"executable_path": exe} if exe else {}
    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kw)
        pg = b.new_page()
        pg.goto(f"file://{html_path.resolve()}")
        pg.pdf(
            path=str(out_path),
            format="A4",
            margin={"top": "14mm", "bottom": "14mm", "left": "14mm", "right": "14mm"},
            print_background=True,   # 배경색 반드시 True (spec 4-3)
        )
        b.close()
    return out_path
