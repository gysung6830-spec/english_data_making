"""표지 겸 사용 설명서 페이지 렌더.

통합 워크북 맨 앞에 붙는 1페이지 안내: 이 파일에 어떤 유형이 어떤 순서로 들어 있고,
각 유형을 어떻게 푸는지, 기호(( ) [ / ] 〈 〉 = [ ] 등)가 무슨 뜻인지, '한글 포함/제외'
버전을 어떻게 활용하는지를 한눈에 보여준다. HTML → PDF 는 Playwright(Chromium).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"


@dataclass
class CoverSection:
    no: int
    key: str          # workbook/form/grammar/vocab/writing/translate/blanks
    name: str         # "통합 카드"
    css: str          # 색 클래스 (sec-v 등)
    purpose: str      # 목적 한 줄
    how: str          # 푸는 법 한 줄
    mark: str         # 기호 예시


# 유형 카탈로그(워크북 배치 순서와 동일). 있는 것만 골라 표지에 싣는다.
_CATALOG: dict[str, dict] = {
    "workbook": dict(
        name="통합 카드", css="sec-w",
        purpose="한 문장에서 어형·어법·어휘·배열·지칭을 한 번에 점검",
        how="문장에 표시된 기호대로 푼다: ( ) 어형 · [ / ] 선택 · 〈 〉 배열 · 대명사 = [ ] 지칭",
        mark="( ) [ / ] 〈 〉 = [ ]"),
    "form": dict(
        name="어형 변형", css="sec-f",
        purpose="지문의 모든 동사·준동사를 문맥에 맞는 형태로",
        how="( ) 안의 동사원형을 시제·수·태에 맞게 바꿔 밑줄에 쓴다",
        mark="( 원형 ) ____"),
    "grammar": dict(
        name="어법 양자택일", css="sec-g",
        purpose="시험에 나올 만한 어법 포인트 집중 점검",
        how="[ A / B ] 에서 어법상 알맞은 것을 고른다",
        mark="[ A / B ]"),
    "vocab": dict(
        name="어휘 양자택일", css="sec-c",
        purpose="반의어 대비가 뚜렷한 핵심 어휘 확인",
        how="[ 원문 / 반의어 ] 에서 문맥상 알맞은 것을 고른다",
        mark="[ A / B ]"),
    "writing": dict(
        name="영작 워크북", css="sec-o",
        purpose="자주 틀리는 영작 포인트(어순·구문)만 배열 연습",
        how="우리말 뜻에 맞게 〈 〉 안의 어구를 바르게 배열한다",
        mark="〈 a / b / c 〉"),
    "translate": dict(
        name="한글 해석 연습", css="sec-t",
        purpose="문장을 정확히 해석하는 훈련",
        how="영문을 읽고 아래 칸에 우리말 해석을 쓴다",
        mark="(해석 작성칸)"),
    "blanks": dict(
        name="빈칸 워크북", css="sec-b",
        purpose="핵심어 암기 + 요약문으로 글 재구성",
        how="지문 빈칸은 첫 글자 힌트로, 요약문 빈칸은 워드뱅크에서 골라 쓴다",
        mark="s____ · Word Bank"),
}

_ORDER = ["workbook", "form", "grammar", "vocab", "writing", "translate", "blanks"]


def build_cover_sections(present_keys) -> list[CoverSection]:
    keys = [k for k in _ORDER if k in set(present_keys)]
    out: list[CoverSection] = []
    for i, k in enumerate(keys, start=1):
        c = _CATALOG[k]
        out.append(CoverSection(no=i, key=k, name=c["name"], css=c["css"],
                                purpose=c["purpose"], how=c["how"], mark=c["mark"]))
    return out


# ── 렌더 ─────────────────────────────────────────────────────────────
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)),
                   autoescape=select_autoescape(["html", "xml", "j2"]))


def render_cover_html(*, header: str, title: str, subtitle: str = "",
                      version_label: str = "", n_passages: int = 1,
                      sections: list[CoverSection]) -> str:
    from . import branding
    return _env.get_template("cover.html.j2").render(
        header=header, title=title, subtitle=subtitle, version_label=version_label,
        n_passages=n_passages, sections=sections, font_css=branding.font_face_css())


def render_cover_pdf(out_path: str | Path, *, header: str, title: str, subtitle: str = "",
                     version_label: str = "", n_passages: int = 1,
                     section_keys=None, footer_note: str = "") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sections = build_cover_sections(section_keys or _ORDER)
    html = render_cover_html(header=header, title=title, subtitle=subtitle,
                             version_label=version_label, n_passages=n_passages,
                             sections=sections)
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
