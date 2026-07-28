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


def render_a_html(analyses, footer_note: str = "", footer_meta: str = "",
                  compact: bool = False, include_back: bool = True,
                  include_guide: bool = True) -> str:
    """레이아웃 A(분석 학습지형) HTML.

    footer_note   : 하단 우측 저작권 문구.
    footer_meta   : 하단 좌측 페이지 라벨(예: '2025년 06월 고2 모의고사 분석서').
    compact       : 압축 밀도(한 지문을 최대한 1페이지에).
    include_back  : 뒷페이지(어휘/흐름) 포함 여부(측정 시 False).
    include_guide : 맨 앞 '활용 가이드' 표지 페이지 포함 여부(측정 시 False).
    """
    tmpl = _env.get_template("worksheet_a.html.j2")
    return tmpl.render(analyses=_as_list(analyses), footer_note=footer_note,
                       footer_meta=footer_meta, compact=compact,
                       include_back=include_back, include_guide=include_guide)


def render_b_html(analyses, footer_note: str = "", brand: str = "은아 T") -> str:
    """레이아웃 B(직독직해형) HTML.

    영어 원문을 의미 단위(청크)로 끊어 직독직해와 대응시키고, 문장별 핵심 문법 태그와
    핵심 단어를 함께 싣는다. brand 는 헤더 'made by …' 문구(빈 문자열이면 생략).
    """
    tmpl = _env.get_template("worksheet_b.html.j2")
    return tmpl.render(analyses=_as_list(analyses), footer_note=footer_note, brand=brand)


def render_html(analyses, layout: str = "A", footer_note: str = "",
                brand: str = "은아 T", footer_meta: str = "", compact: bool = False,
                include_guide: bool = True) -> str:
    if layout.upper() == "B":
        return render_b_html(analyses, footer_note=footer_note, brand=brand)
    return render_a_html(analyses, footer_note=footer_note, footer_meta=footer_meta,
                         compact=compact, include_guide=include_guide)


def _analysis_fits_one_page(analyses, compact: bool) -> bool:
    """각 지문의 '분석 앞면'이 1페이지에 들어가는지 WeasyPrint 로 측정(뒷페이지 제외)."""
    from weasyprint import HTML  # dep

    lst = _as_list(analyses)
    html = render_a_html(lst, compact=compact, include_back=False, include_guide=False)
    pages = len(HTML(string=html).render().pages)
    return pages <= len(lst)   # 지문당 1페이지


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
# A4 96dpi 뷰포트(명세서 §11): 794×1123
A4_VIEWPORT = {"width": 794, "height": 1123}


def _find_chromium() -> str | None:
    """미리 설치된 Chromium 실행 파일 경로(있으면). 버전 불일치 시 이걸로 실행."""
    import glob
    import os

    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    for pat in ("chromium-*/chrome-linux/chrome",
                "chromium-*/chrome-linux64/chrome",
                "chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(os.path.join(base, pat)), reverse=True)
        for h in hits:
            if os.path.exists(h):
                return h
    return None


def _pdf_playwright(html: str, out_path: Path) -> bool:
    """Playwright(Chromium)로 HTML→PDF. 사용 불가하면 False.

    Chromium 은 CSS 를 정확히(특히 폭0 주석) 렌더하므로 단어 간격이 촘촘하다.
    번들 브라우저 버전이 안 맞으면 미리 설치된 Chromium 경로로 실행한다.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False
    try:
        with sync_playwright() as p:
            launch_kw: dict = {"args": ["--no-sandbox"]}
            exe = _find_chromium()
            if exe:
                launch_kw["executable_path"] = exe
            browser = p.chromium.launch(**launch_kw)
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
               footer_note: str = "", brand: str = "은아 T",
               engine: str = "auto", footer_meta: str = "",
               density: str = "auto") -> Path:
    """Analysis → PDF.

    engine  : 'auto' | 'playwright' | 'weasyprint'.
    brand   : 레이아웃 B 헤더 'made by …' 문구.
    density : 'normal' | 'compact' | 'auto'. 'auto' 는 앞면이 지문당 1페이지를 넘으면
              자동으로 압축 밀도로 다시 맞춘다(레이아웃 A 한정).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    compact = (density == "compact")
    if layout.upper() == "A" and density == "auto":
        try:
            compact = not _analysis_fits_one_page(analyses, compact=False)
        except Exception:
            compact = False
    html = render_html(analyses, layout=layout, footer_note=footer_note, brand=brand,
                       footer_meta=footer_meta, compact=compact)

    if engine in ("auto", "playwright"):
        if _pdf_playwright(html, out_path):
            return out_path
        if engine == "playwright":
            raise RuntimeError("Playwright(Chromium)를 사용할 수 없습니다.")
    _pdf_weasyprint(html, out_path)
    return out_path
