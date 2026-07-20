"""Analysis → HTML(레이아웃 A/B) → PDF (명세서 §5-5, §5-6).

- render_a_html / render_b_html : Analysis 목록을 HTML 문자열로.
- render_pdf                    : HTML → PDF. Playwright(Chromium) 우선, 없으면 WeasyPrint.

템플릿은 CSS 를 <style> 에 내장해 자체 완결형이므로 base_url·외부 폰트 로드가 필요 없다.
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Analysis

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

# 원문자 ①~⑳ 변환 (레이아웃 B 번호용). 20 초과는 (n) 으로 폴백.
_CIRCLED = [chr(0x2460 + i) for i in range(20)]


def circled(n: int) -> str:
    return _CIRCLED[n - 1] if 1 <= n <= 20 else f"({n})"


_env.globals["circled"] = circled


def _as_list(analyses) -> list[Analysis]:
    if isinstance(analyses, Analysis):
        return [analyses]
    return list(analyses)


def render_a_html(analyses, footer_note: str = "", footer_meta: str = "") -> str:
    """레이아웃 A(분석 학습지형) HTML.

    footer_note : 하단 우측 저작권 문구.
    footer_meta : 하단 좌측 페이지 라벨(예: '2025년 06월 고2 모의고사 분석서').
    """
    tmpl = _env.get_template("worksheet_a.html.j2")
    return tmpl.render(analyses=_as_list(analyses), footer_note=footer_note,
                       footer_meta=footer_meta)


def render_b_html(analyses, footer_note: str = "", tagged: bool = False) -> str:
    """레이아웃 B(대조표형) HTML. tagged=True 면 A 의 구문 태깅을 영어칸에 얹는다."""
    tmpl = _env.get_template("worksheet_b.html.j2")
    return tmpl.render(analyses=_as_list(analyses), footer_note=footer_note, tagged=tagged)


def render_html(analyses, layout: str = "A", footer_note: str = "",
                tagged: bool = False, footer_meta: str = "") -> str:
    if layout.upper() == "B":
        return render_b_html(analyses, footer_note=footer_note, tagged=tagged)
    return render_a_html(analyses, footer_note=footer_note, footer_meta=footer_meta)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
# A4 96dpi 뷰포트(명세서 §11): 794×1123
A4_VIEWPORT = {"width": 794, "height": 1123}


def _pdf_playwright(html: str, out_path: Path) -> bool:
    """Playwright(Chromium)로 HTML→PDF. 사용 불가하면 False."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport=A4_VIEWPORT)
            page.set_content(html, wait_until="networkidle")
            page.pdf(path=str(out_path), format="A4", print_background=True,
                     margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            browser.close()
        return True
    except Exception:
        return False


def _pdf_weasyprint(html: str, out_path: Path) -> None:
    from weasyprint import HTML  # 지연 임포트(무거움)

    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path))


def render_pdf(analyses, out_path: str | Path, layout: str = "A",
               footer_note: str = "", tagged: bool = False,
               engine: str = "auto", footer_meta: str = "") -> Path:
    """Analysis → PDF. engine: 'auto' | 'playwright' | 'weasyprint'."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(analyses, layout=layout, footer_note=footer_note, tagged=tagged,
                       footer_meta=footer_meta)

    if engine in ("auto", "playwright"):
        if _pdf_playwright(html, out_path):
            return out_path
        if engine == "playwright":
            raise RuntimeError("Playwright(Chromium)를 사용할 수 없습니다.")
    _pdf_weasyprint(html, out_path)
    return out_path
