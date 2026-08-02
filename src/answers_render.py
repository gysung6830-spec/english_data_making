"""단일 유형 정답을 '한 문서에 모아' 연속 배치하는 렌더 (유형끼리 페이지 안 나눔).

통합 카드 정답은 기존대로 유형/지문별 페이지 분할을 유지하고, 어형·어법·어휘·영작·해석·빈칸
정답은 이 모듈이 하나의 연속 문서로 모은다. 각 묶음에는 '출처 라벨(예: [고1] 9월 30번)'과
유형명을 붙인다. HTML → PDF 는 Playwright(Chromium).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"


@dataclass
class AnsGroup:
    label: str                 # 출처 라벨 (예: "[고1] 9월 30번")
    type_name: str             # 유형명 (예: "어형 변형")
    css: str                   # 색 클래스 (f/g/v/o/t/b)
    items: list[str] = field(default_factory=list)          # "1) answer" 형태
    block: bool = False        # True 면 한 줄에 하나씩(해석·영작), False 면 인라인 칩
    subgroups: list = field(default_factory=list)           # [(소제목, [items…])] (빈칸용)
    note: str = ""             # 부가 해설 (요약문 해석 등)


# ── 그룹 빌더 ────────────────────────────────────────────────────────
# style: "gloss"(정답+문장 해석 한 줄) / "compact"(정답만) / "passage"(정답+지문 전체 해석 첨부)
def group_from_prose(pack, wtype: str, type_name: str, css: str,
                     style: str = "gloss") -> "AnsGroup | None":
    ws = next((w for w in pack.worksheets if w.wtype == wtype), None)
    if ws is None:
        return None
    is_tr = (wtype == "translate")
    is_vocab = wtype in ("vocab", "vocab_easy")
    block = is_tr or style == "gloss"
    items: list[str] = []
    kos: list[str] = []
    for s in ws.sentences:
        if is_tr:
            if s.ko:
                items.append(f"{s.no}) {s.ko}")
            continue
        if not s.items:
            continue
        if is_vocab:
            # 어휘: 각 정답에 한글 '뜻'을 함께 표기 (예: "ample (충분한)")
            parts = []
            for it in s.items:
                g = getattr(it, "gloss", "")
                parts.append(f"{it.answer} ({g})" if g else it.answer)
            ans = " / ".join(parts)
        else:
            ans = " / ".join(it.answer for it in s.items)
        if style == "gloss" and s.ko:
            items.append(f"{s.no}) {ans}  —  {s.ko}")
        else:
            items.append(f"{s.no}) {ans}")
        if s.ko:
            kos.append(f"{s.no}) {s.ko}")
    if not items:
        return None
    note = " ".join(k.split(") ", 1)[-1] for k in kos) if (style == "passage" and not is_tr) else ""
    return AnsGroup(label=pack.label, type_name=type_name, css=css,
                    items=items, block=block, note=note)


def group_from_writing(wpack, css: str = "o", style: str = "gloss") -> "AnsGroup | None":
    items: list[str] = []
    kos: list[str] = []
    for s in wpack.sentences:
        if not s.items:
            continue
        ans = " · ".join(it.answer for it in s.items)
        if style == "gloss" and s.ko:
            items.append(f"{s.no}) {ans}  —  {s.ko}")
        else:
            items.append(f"{s.no}) {ans}")
        if s.ko:
            kos.append(s.ko)
    if not items:
        return None
    note = " ".join(kos) if style == "passage" else ""
    return AnsGroup(label=wpack.label, type_name="영작 워크북", css=css,
                    items=items, block=True, note=note)


def groups_from_blanks(blank_wb, css: str = "b", style: str = "gloss") -> list["AnsGroup"]:
    out: list[AnsGroup] = []
    for st in blank_wb.sets:
        pb = [f"{b.num}) {b.answer}" for b in st.passage_blanks]
        sb = [f"{b.num}) {b.answer}" for b in st.summary_blanks]
        subs = []
        if pb:
            subs.append(("① 지문 빈칸", pb))
        if sb:
            subs.append(("② 요약문 빈칸", sb))
        if not subs:
            continue
        note = st.summary_ko
        # gloss/passage 는 지문 해석도 함께
        if style in ("gloss", "passage"):
            passage_ko = " ".join(s.ko for s in st.sentences if s.ko)
            if passage_ko:
                note = (f"[지문] {passage_ko}  ·  [요약문] {st.summary_ko}"
                        if st.summary_ko else f"[지문] {passage_ko}")
        out.append(AnsGroup(label=st.label, type_name="빈칸 워크북", css=css,
                            subgroups=subs, note=note))
    return out


# ── 렌더 ─────────────────────────────────────────────────────────────
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)),
                   autoescape=select_autoescape(["html", "xml", "j2"]))


def render_answers_html(groups: list[AnsGroup]) -> str:
    from . import branding
    return _env.get_template("answers.html.j2").render(
        groups=groups, font_css=branding.font_face_css())


def render_answers_pdf(groups: list[AnsGroup], out_path: str | Path,
                       footer_note: str = "") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_answers_html(groups)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    footer = footer_note.strip() if footer_note and footer_note.strip() else DEFAULT_FOOTER
    exe = _chromium_executable()
    launch_kw = {"executable_path": exe} if exe else {}
    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kw)
        pg = b.new_page()
        pg.goto(f"file://{html_path.resolve()}")
        try:
            pg.evaluate("async () => { await document.fonts.ready; }")
        except Exception:
            pass
        pg.pdf(path=str(out_path), format="A4",
               margin={"top": "12mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=_footer_template(footer))
        b.close()
    return out_path
