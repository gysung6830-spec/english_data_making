"""영작 워크북 (문장 속 '영작 포인트' 어구만 곳곳을 배열).

문장 전체를 단어 배열하는 것이 아니라, 한 문장에서 학생이 자주 틀리는 핵심 어구
(부분부정, 비교구문, 관계사절, to부정사 어순, 관용표현 등)만 골라 그 자리에서만
어순을 뒤섞어 〈 … 〉 로 제시한다. 나머지 문장은 그대로 주어 발판을 준다.
우리말 뜻을 보고 각 〈 … 〉 를 바르게 배열하면 문장이 완성된다.
HTML → PDF 는 Playwright(Chromium).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from pydantic import BaseModel, Field

from .blanks_schemas import placeholders_in  # {{An}} 재사용
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER, _page_ready, _launch_chromium

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
    label: str = ""    # 출처 기반 문항 라벨 (예: "[고1] 9월 30번")


# ── LLM 응답 계층 (pydantic) ─────────────────────────────────────────
class LLMWritingItem(BaseModel):
    id: str                                       # "A1"
    chunks: list[str] = Field(default_factory=list)  # 바른 순서의 조각들
    answer: str = ""                              # 바른 배열(문장부호 포함). 비면 chunks 로 생성


class LLMWritingSentence(BaseModel):
    no: int
    ko: str                                       # 우리말 뜻(길잡이)
    template: str                                 # 원문에서 영작 포인트만 {{An}} 으로 바꾼 문장
    items: list[LLMWritingItem] = Field(default_factory=list)


class LLMWritingPack(BaseModel):
    title: str = ""
    subtitle: str = ""
    sentences: list[LLMWritingSentence] = Field(default_factory=list)


_DEFAULT_INSTRUCTION = "우리말 뜻에 맞게 〈 〉 안의 어구를 바르게 배열하여 문장을 완성하시오."


def _shuffled_display(chunks: list[str]) -> str:
    """조각들을 무작위로 섞어 '〈 a / b / c 〉' 표시 문자열을 만든다.
    조각이 2개 이상이면 원래 순서와 다르게 되도록 몇 번 다시 섞는다."""
    parts = [c.strip() for c in chunks if c and c.strip()]
    if not parts:
        return "〈 〉"
    if len(parts) >= 2:
        shuffled = parts[:]
        for _ in range(8):
            random.shuffle(shuffled)
            if shuffled != parts:
                break
        parts = shuffled
    return "〈 " + " / ".join(parts) + " 〉"


def _item_answer(it: LLMWritingItem) -> str:
    if it.answer and it.answer.strip():
        return it.answer.strip()
    return " ".join(c.strip() for c in it.chunks if c and c.strip())


def build_writing_pack(llm: LLMWritingPack, header: str, title: str, subtitle: str,
                       instruction: str = "") -> WritingPack:
    """검증된 LLM 응답 -> 렌더용 WritingPack. display 는 코드가 조각을 섞어 생성한다."""
    sents: list[WSentence] = []
    for s in llm.sentences:
        by_id = {it.id: it for it in s.items}
        order = placeholders_in(s.template)
        items: list[WItem] = []
        template = s.template
        # 자리표시자 등장 순서로 짝짓되, id 가 안 맞으면 순서대로 매핑한다.
        pairs = ([(pid, by_id[pid]) for pid in order]
                 if set(order) == set(by_id) and len(order) == len(s.items)
                 else list(zip(order, s.items)))
        for pid, src in pairs:
            chunks = [c.strip() for c in src.chunks if c and c.strip()]
            # 배열할 조각이 2개 미만인 박스(예: 〈 on 〉)는 '배열할 게 없어' 무의미하므로
            # 문항으로 내지 않고 그 어구를 문장에 그대로 복원한다.
            if len(chunks) < 2:
                template = template.replace("{{" + pid + "}}", _item_answer(src))
                continue
            items.append(WItem(id=pid, display=_shuffled_display(src.chunks),
                               answer=_item_answer(src)))
        sents.append(WSentence(no=s.no, template=template, ko=s.ko, items=items))
    return WritingPack(header=header, title=title or "", subtitle=subtitle or "",
                       instruction=instruction or _DEFAULT_INSTRUCTION, sentences=sents)


def validate_llm_writing(llm: LLMWritingPack) -> None:
    """영작 워크북 응답 검증. 자리표시자 수와 items 수가 달라도 build 가 등장 순서로
    가능한 만큼만 짝지어 렌더하므로 실패시키지 않는다(문장이 비면 재요청)."""
    if not llm.sentences:
        raise ValueError("영작 워크북 문장이 비어 있습니다.")


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


def render_writing_html(pack: WritingPack, footer_note: str = "", show_ko: bool = True,
                        section: str = "all") -> str:
    from . import branding
    return _env.get_template("writing.html.j2").render(
        pack=pack, footer_note=footer_note, show_ko=show_ko, section=section,
        font_css=branding.font_face_css())


def render_writing_pdf(pack: WritingPack, out_path: str | Path, footer_note: str = "",
                       show_ko: bool = True, section: str = "all") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_writing_html(pack, footer_note, show_ko=show_ko, section=section)
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
        pg.pdf(path=str(out_path), format="A4",
               margin={"top": "12mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=_footer_template(footer))
        b.close()
    return out_path
