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
                  include_guide: bool = True, only_back: bool = False,
                  student: bool = False, slevel: str = "slash",
                  boxmode: str = "") -> str:
    """레이아웃 A(분석 학습지형) HTML.

    footer_note   : 하단 우측 저작권 문구.
    footer_meta   : 하단 좌측 페이지 라벨(예: '2025년 06월 고2 모의고사 분석서').
    compact       : 압축 밀도(한 지문을 최대한 1페이지에).
    include_back  : 뒷페이지(어휘/흐름) 포함 여부(측정 시 False).
    include_guide : 맨 앞 '활용 가이드' 표지 페이지 포함 여부(측정 시 False).
    only_back     : 뒷면만 렌더(뒷면 페이지 수 측정용).
    """
    tmpl = _env.get_template("worksheet_a.html.j2")
    return tmpl.render(analyses=_as_list(analyses), footer_note=footer_note,
                       footer_meta=footer_meta, compact=compact,
                       include_back=include_back, include_guide=include_guide,
                       only_back=only_back, student=student, slevel=slevel,
                       boxmode=boxmode)


def render_b_html(analyses, footer_note: str = "", brand: str = "은아 T") -> str:
    """레이아웃 B(직독직해형) HTML.

    영어 원문을 의미 단위(청크)로 끊어 직독직해와 대응시키고, 문장별 핵심 문법 태그와
    핵심 단어를 함께 싣는다. brand 는 헤더 'made by …' 문구(빈 문자열이면 생략).
    """
    tmpl = _env.get_template("worksheet_b.html.j2")
    return tmpl.render(analyses=_as_list(analyses), footer_note=footer_note, brand=brand)


def render_html(analyses, layout: str = "A", footer_note: str = "",
                brand: str = "은아 T", footer_meta: str = "", compact: bool = False,
                include_guide: bool = True, student: bool = False,
                slevel: str = "slash", boxmode: str = "") -> str:
    if layout.upper() == "B":
        return render_b_html(analyses, footer_note=footer_note, brand=brand)
    return render_a_html(analyses, footer_note=footer_note, footer_meta=footer_meta,
                         compact=compact, include_guide=include_guide,
                         student=student, slevel=slevel, boxmode=boxmode)


def _measure_pages_chromium(htmls: list[str]) -> list[int] | None:
    """여러 HTML 의 페이지 수를 '실제 렌더 엔진(Chromium)'으로 측정(브라우저 1회 재사용).

    최종 출력이 Chromium 이므로 측정도 같은 엔진으로 해야 1페이지 판정이 실제와
    일치한다(WeasyPrint 와는 경계에서 ±1 어긋날 수 있음). 불가하면 None.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    import tempfile

    import pypdfium2 as pdfium
    counts: list[int] = []
    try:
        with sync_playwright() as p:
            launch_kw: dict = {"args": ["--no-sandbox"]}
            exe = _find_chromium()
            if exe:
                launch_kw["executable_path"] = exe
            browser = p.chromium.launch(**launch_kw)
            page = browser.new_page(viewport=A4_VIEWPORT)
            for html in htmls:
                page.set_content(html, wait_until="networkidle")
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tf:
                    page.pdf(path=tf.name, format="A4", print_background=True,
                             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
                    counts.append(len(pdfium.PdfDocument(tf.name)))
            browser.close()
        return counts
    except Exception:
        return None


def _page_counts(htmls: list[str]) -> list[int]:
    """각 HTML 페이지 수. Chromium(최종 엔진) 우선, 안 되면 WeasyPrint 로 폴백."""
    counts = _measure_pages_chromium(htmls)
    if counts is not None:
        return counts
    from weasyprint import HTML  # dep
    return [len(HTML(string=h).render().pages) for h in htmls]


_FRONT_TIERS = ["normal", "compact", "ultra"]


def _fit_pages(analyses, fit_front: bool = True,
               student: bool = False, slevel: str = "slash",
               boxmode: str = "") -> None:
    """앞면(분석)·뒷면(정리)을 지문마다 최대한 1페이지에 맞춘다(넘치는 장문은 2페이지).

    - 앞면: normal→compact→ultra 중 1페이지가 되는 가장 큰(덜 압축된) 단계.
    - 뒷면: 기본 압축으로 넘치면 btight 로 1페이지가 될 때만 적용.
    모든 후보를 모아 렌더 엔진 측정을 '한 번'에 수행(대량 처리 시 브라우저 1회).
    fit_front=False 면 앞면은 이미 정해진 밀도를 쓰고 뒷면만 맞춘다.
    학생용(student)은 빈칸 공간까지 반영해 측정한다.
    """
    lst = _as_list(analyses)
    jobs: list[tuple[int, str, object]] = []   # (지문 index, 'front'|'back', tier)
    htmls: list[str] = []
    for i, a in enumerate(lst):
        if fit_front:
            for t in _FRONT_TIERS:
                a.front_density = t
                jobs.append((i, "front", t))
                htmls.append(render_a_html([a], include_back=False, include_guide=False,
                                           student=student, slevel=slevel, boxmode=boxmode))
        if getattr(a, "has_back", False):
            for tight in (False, True):
                a.back_tight = tight
                jobs.append((i, "back", tight))
                htmls.append(render_a_html([a], compact=True, include_guide=False,
                                           only_back=True, student=student, slevel=slevel))
    if not htmls:
        return
    try:
        counts = _page_counts(htmls)
    except Exception:
        for a in lst:
            if fit_front:
                a.front_density = "compact"
            a.back_tight = False
        return

    for i, a in enumerate(lst):
        if fit_front:
            chosen = "ultra"
            for (j, kind, t), c in zip(jobs, counts):
                if j == i and kind == "front":
                    if c <= 1:
                        chosen = t
                        break
            a.front_density = chosen
        backs = {t: c for (j, kind, t), c in zip(jobs, counts) if j == i and kind == "back"}
        a.back_tight = bool(backs) and backs.get(False, 2) > 1 and backs.get(True, 2) <= 1


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
               density: str = "auto", student: bool = False,
               slevel: str = "slash", include_guide: bool = True,
               boxmode: str = "") -> Path:
    """Analysis → PDF.

    engine  : 'auto' | 'playwright' | 'weasyprint'.
    brand   : 레이아웃 B 헤더 'made by …' 문구.
    density : 'normal' | 'compact' | 'auto'. 'auto' 는 앞면이 지문당 1페이지를 넘으면
              자동으로 압축 밀도로 다시 맞춘다(레이아웃 A 한정).
    student : True 면 학생용(필기) — 정답/해석을 비워 빈칸으로.
    slevel  : 'slash'(끊어읽기만) | 'blank'(완전백지) | 'interp'(해석만 빈칸).
    include_guide : 맨 앞 '활용 가이드' 표지 포함 여부(합본 시 학생용은 False).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    compact = (density == "compact")
    if layout.upper() == "A":
        if density == "auto":
            _fit_pages(analyses, fit_front=True, student=student, slevel=slevel,
                       boxmode=boxmode)
        else:                                        # 'normal' | 'compact' 고정
            for a in _as_list(analyses):
                a.front_density = density
            _fit_pages(analyses, fit_front=False, student=student, slevel=slevel,
                       boxmode=boxmode)
    html = render_html(analyses, layout=layout, footer_note=footer_note, brand=brand,
                       footer_meta=footer_meta, compact=compact,
                       student=student, slevel=slevel, include_guide=include_guide,
                       boxmode=boxmode)

    if engine in ("auto", "playwright"):
        if _pdf_playwright(html, out_path):
            return out_path
        if engine == "playwright":
            raise RuntimeError("Playwright(Chromium)를 사용할 수 없습니다.")
    _pdf_weasyprint(html, out_path)
    return out_path
