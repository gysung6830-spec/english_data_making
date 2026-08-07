"""Workbook -> HTML -> PDF.

- 문제 표기 치환(render_sentence)은 Python 에서 처리한다.
  en_template 안의 {{Qn}} 자리표시자를 Jinja 가 변수로 오해하지 않도록, 렌더 전에 안전한
  HTML(Markup)로 바꿔 템플릿에 넘긴다.
- HTML -> PDF 는 Playwright(Chromium)로 렌더한다. (spec 4-3: WeasyPrint 미설치,
  LibreOffice 는 CSS 지원 부족.)
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from . import branding
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
    # 짝이 없어 남은 자리표시자({{Qn}})가 그대로 노출되지 않도록 제거
    html = re.sub(r"\{\{\s*Q\w+\s*\}\}", "", html)
    return Markup(html)


_env.filters["render_sentence"] = render_sentence


def render_workbooks_html(books: list[Workbook], footer_note: str = "",
                          show_ko: bool = True, section: str = "all") -> str:
    """여러 지문을 한 문서에 배치 (지문1 → 답1 → 지문2 → 답2 …).

    show_ko=False 이면 문제면의 한국어 해석 줄을 숨긴다(정답·해설면은 그대로).
    section='q' 이면 문제만, 'a' 이면 정답·해설만, 'all' 이면 둘 다 렌더한다.
    """
    tmpl = _env.get_template("workbook.html.j2")
    return tmpl.render(books=list(books), footer_note=footer_note,
                       show_ko=show_ko, section=section, font_css=branding.font_face_css())


def render_workbook_html(wb: Workbook, footer_note: str = "", show_ko: bool = True,
                         section: str = "all") -> str:
    """단일 지문 렌더 (내부적으로 books=[wb])."""
    return render_workbooks_html([wb], footer_note=footer_note, show_ko=show_ko, section=section)


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


_CHROMIUM_INSTALLED = False


def _install_chromium() -> None:
    """Playwright 브라우저(Chromium)를 자동 설치한다(비개발자용 자가치유).

    Windows 등에서 'Executable doesn't exist … playwright install' 오류가 날 때,
    'python -m playwright install chromium' 을 한 번 실행해 브라우저를 내려받는다.
    """
    global _CHROMIUM_INSTALLED
    if _CHROMIUM_INSTALLED:
        return
    import subprocess
    import sys

    _CHROMIUM_INSTALLED = True   # 재귀·반복 설치 방지(성공/실패와 무관하게 1회만)
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       check=False, timeout=600)
    except Exception:
        pass


def _launch_chromium(p, launch_kw: dict):
    """Chromium 실행. 브라우저 미설치로 실패하면 자동 설치 후 한 번 재시도한다."""
    try:
        return p.chromium.launch(**launch_kw)
    except Exception as e:
        msg = str(e)
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            _install_chromium()
            return p.chromium.launch(**launch_kw)   # 재설치 후 재시도
        raise


# 상단 한글 제목(.sh-title)을 '한 줄·한 페이지 안'에 담기 위한 자동 축소 스크립트.
#   폰트 로딩을 기다린 뒤, 제목이 칸을 넘치면 글씨를 조금씩 줄여 한 줄에 맞춘다(생략 금지).
#   최소 크기에서도 넘치면 그때만 줄바꿈을 허용해 '잘림 없이' 모두 보이게 한다.
_PAGE_READY_JS = """async () => {
  await document.fonts.ready;
  const MIN_PX = 12;                         /* 더는 줄이지 않는 하한(px) */
  document.querySelectorAll('.sh-title').forEach(el => {
    el.style.whiteSpace = 'nowrap';
    let px = parseFloat(getComputedStyle(el).fontSize);
    let guard = 0;
    while (el.scrollWidth > el.clientWidth && px > MIN_PX && guard < 60) {
      px -= 0.5; el.style.fontSize = px + 'px'; guard++;
    }
    if (el.scrollWidth > el.clientWidth) {     /* 하한에서도 넘치면 줄바꿈 허용(생략 금지) */
      el.style.whiteSpace = 'normal';
      el.style.lineHeight = '1.15';
    }
  });
}"""


def _page_ready(pg) -> None:
    """폰트 로딩 대기 + 상단 제목 자동 축소(한 줄·한 페이지). 실패해도 무시."""
    try:
        pg.evaluate(_PAGE_READY_JS)
    except Exception:
        pass


# 하단 저작권 기본 문구 (footer_note 가 비어 있어도 항상 표기)
DEFAULT_FOOTER = branding.FOOTER_BRAND


def _footer_template(text: str) -> str:
    """모든 페이지 하단 '왼쪽'에 인쇄될 저작권 푸터(HTML). 저작권 문구만.

    페이지 번호는 병합 후 문서 전체 기준으로 stamp_page_numbers() 가 하단 '오른쪽'에 따로 찍는다
    (부분 PDF 를 합치므로 Chromium 의 pageNumber 는 구간마다 재시작하기 때문).
    """
    return (
        '<div style="width:100%; font-size:11px; color:#9aa3af; text-align:left; '
        "font-family:'NanumSquareRound','Malgun Gothic','Nanum Gothic',sans-serif; "
        'padding:0 14mm;">'
        f'{escape(text)}'
        '</div>'
    )


def stamp_page_numbers(path: str | Path) -> Path:
    """완성된(병합된) PDF 에 문서 전체 기준 'n / N' 페이지 번호를 하단 중앙에 찍는다.

    저작권 문구(가운데)와 겹치지 않도록 그 아래쪽 여백에 회색 소형으로 표기한다.
    숫자·슬래시만 쓰므로 기본 내장 폰트(helv)로 충분하다.
    """
    import fitz  # PyMuPDF

    path = Path(path)
    doc = fitz.open(str(path))
    n = doc.page_count
    for i, page in enumerate(doc, start=1):
        w, h = page.rect.width, page.rect.height
        label = f"{i} / {n}"
        # 저작권 푸터(11px)와 같은 크기: 11px = 8.25pt
        fs = 8.25
        tw = fitz.get_text_length(label, fontname="helv", fontsize=fs)
        # 저작권 문구(왼쪽)와 겹치지 않게 같은 줄 오른쪽에 배치
        page.insert_text((w - 40 - tw, h - 17.5), label,
                         fontsize=fs, fontname="helv", color=(0.62, 0.66, 0.71))
    tmp = path.with_name(path.stem + "__num.pdf")
    doc.save(str(tmp))
    doc.close()
    os.replace(tmp, path)
    return path


def render_workbooks_pdf(books: list[Workbook], out_path: str | Path, footer_note: str = "",
                         show_ko: bool = True, section: str = "all") -> Path:
    """여러 지문을 한 PDF 로 배치 (지문1 → 답1 → 지문2 → 답2 …).

    A4 세로, 배경색 인쇄 + 모든 페이지 저작권 푸터.
    show_ko=False 이면 문제면의 한국어 해석을 숨긴다.
    section='q' 문제만 / 'a' 정답만 / 'all' 둘 다.
    """
    from playwright.sync_api import sync_playwright  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = render_workbooks_html(books, footer_note, show_ko=show_ko, section=section)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    footer = footer_note.strip() if footer_note and footer_note.strip() else DEFAULT_FOOTER

    exe = _chromium_executable()
    launch_kw = {"executable_path": exe} if exe else {}
    with sync_playwright() as p:
        b = _launch_chromium(p, launch_kw)
        pg = b.new_page()
        pg.goto(f"file://{html_path.resolve()}")
        _page_ready(pg)
        pg.pdf(
            path=str(out_path),
            format="A4",
            margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
            print_background=True,          # 배경색 반드시 True (spec 4-3)
            display_header_footer=True,     # 모든 페이지 하단 저작권 푸터
            header_template="<span></span>",
            footer_template=_footer_template(footer),
        )
        b.close()
    return out_path


def render_workbook_pdf(wb: Workbook, out_path: str | Path, footer_note: str = "",
                        show_ko: bool = True, section: str = "all") -> Path:
    """단일 지문 렌더 (내부적으로 books=[wb])."""
    return render_workbooks_pdf([wb], out_path, footer_note=footer_note,
                                show_ko=show_ko, section=section)


def merge_pdfs(parts: list[str | Path], out_path: str | Path) -> Path:
    """여러 PDF 를 순서대로 하나로 합친다. pypdf 우선, 없으면 PyMuPDF(fitz) 사용."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parts = [Path(p) for p in parts if p and Path(p).is_file()]
    if not parts:
        raise ValueError("합칠 PDF 가 없습니다.")
    if len(parts) == 1:
        # 단일이면 그대로 복사(불필요한 재인코딩 방지)
        import shutil
        shutil.copyfile(parts[0], out_path)
        return out_path
    try:
        from pypdf import PdfWriter
        w = PdfWriter()
        for p in parts:
            w.append(str(p))
        with out_path.open("wb") as f:
            w.write(f)
        return out_path
    except Exception:
        pass
    import fitz  # PyMuPDF
    doc = fitz.open()
    for p in parts:
        with fitz.open(str(p)) as src:
            doc.insert_pdf(src)
    doc.save(str(out_path))
    doc.close()
    return out_path
