"""조판기 (명세서 §6, §4).

- TYPE_ORDER 대로만 순회하므로 유형 순서가 자동 보장된다.
- 문서 전체에 걸쳐 문항 번호를 연속으로 부여한다(지문2는 7번부터…).
- 배치: [모든 지문의 문제] → [모든 지문의 해설].
- 문제와 해설은 같은 번호로 대응한다.
- 2단(좌/우) 조판, 지문 라벨, 볼드 5곳, 쪽번호는 템플릿/CSS 가 담당한다.
"""
from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from .types import TYPE_LABELS, TYPE_ORDER, TYPE_PROMPTS, Passage

# 서술형 계열(단일 정답 번호가 없는 유형) — 빠른 정답에는 '서술형'으로 표기
SHORT_TYPES = {"short_answer", "D"}
_KEY_RE = re.compile(r'<span class="answer-key">(.*?)</span>', re.S)


def _answer_key(a_html: str, is_short: bool) -> str:
    """해설 HTML 에서 정답 키(①, '③, ④, ⑤' 등)만 뽑아 빠른 정답용으로 돌려준다."""
    if is_short:
        return "서술형"
    m = _KEY_RE.search(a_html)
    if not m:
        return "-"
    txt = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return txt or "-"

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=False,  # 생성기가 만든 HTML 조각을 그대로 삽입한다
)


def _blocks(passages: list[Passage], start: int,
            type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS):
    """지문별 통합 블록 + 빠른 정답 목록을 만들며 문항 번호를 연속 부여한다.

    각 행(row)에 문제(q_body)·해설(a_body)·정답키(key)를 모두 담아,
    한 데이터로 학생용·교사용·빠른정답·해설지 4개 섹션을 조판한다.
    type_order/prompts/labels 를 바꾸면 다른 문제 세트(예: 2회)도 같은 조판을 쓴다.
    """
    blocks: list[dict] = []
    quick: list[dict] = []
    n = start
    for i, p in enumerate(passages, start=1):
        rows: list[dict] = []
        for t in type_order:
            a_html = p.a[t]
            key = _answer_key(a_html, t in SHORT_TYPES)
            rows.append({
                "no": n,
                "type": t,
                "prompt": prompts[t],
                "q_body": Markup(p.q[t]),
                "label": labels[t],
                "a_body": Markup(a_html),
                "key": key,
            })
            quick.append({"no": n, "key": key})
            n += 1
        blocks.append({"label": f"[지문 {i}]", "title": p.title, "rows": rows})
    return blocks, quick


# 자료 하단 저작권 문구 기본값(필요하면 render_pdf(footer_note=...) 로 교체)
DEFAULT_FOOTER = "ⓒ 2026. 김은아영어연구소. All rights reserved."

# 출력 섹션 키(고정 순서). None 이면 4개 모두.
SECTION_KEYS = ["student", "teacher", "quick", "answers"]


def _resolve_sections(sections) -> tuple[set, str | None]:
    """선택 섹션을 정규화하고 '첫 섹션'(페이지 브레이크 억제용)을 찾는다."""
    if not sections:
        active = list(SECTION_KEYS)
    else:
        active = [k for k in SECTION_KEYS if k in sections]
        if not active:                      # 아무것도 안 고르면 전체
            active = list(SECTION_KEYS)
    return set(active), active[0]


def render_html(
    passages: list[Passage],
    header_note: str = "",
    doc_title: str = "영어 영역",
    start: int = 1,
    footer_note: str = DEFAULT_FOOTER,
    type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS,
    sections=None,
) -> str:
    blocks, quick = _blocks(passages, start, type_order, prompts, labels)
    active, first_section = _resolve_sections(sections)
    tmpl = _env.get_template("exam.html.j2")
    return tmpl.render(
        blocks=blocks,
        quick=quick,
        header_note=header_note,
        doc_title=doc_title,
        footer_note=footer_note,
        sections=active,
        first_section=first_section,
    )


def render_pdf(
    passages: list[Passage],
    out_path: str | Path,
    header_note: str = "",
    doc_title: str = "영어 영역",
    start: int = 1,
    footer_note: str = DEFAULT_FOOTER,
    type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS,
    sections=None,
) -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(passages, header_note=header_note, doc_title=doc_title,
                       start=start, footer_note=footer_note,
                       type_order=type_order, prompts=prompts, labels=labels,
                       sections=sections)
    css = CSS(filename=str(TEMPLATE_DIR / "exam.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
    return out_path


def render_pdf_multi(parts: list[dict], out_path: str | Path,
                     footer_note: str = DEFAULT_FOOTER) -> Path:
    """여러 '파트'를 한 PDF로 합본한다(WeasyPrint 페이지 병합, 외부 라이브러리 불필요).

    part = {passages, header_note, type_order, prompts, labels, sections}.
    각 파트는 자체 머리글로 시작하고, 파트 사이는 새 쪽에서 이어진다.
    """
    from weasyprint import CSS, HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    css = CSS(filename=str(TEMPLATE_DIR / "exam.css"))

    docs = []
    for part in parts:
        html = render_html(
            part["passages"],
            header_note=part.get("header_note", ""),
            footer_note=footer_note,
            type_order=part.get("type_order", TYPE_ORDER),
            prompts=part.get("prompts", TYPE_PROMPTS),
            labels=part.get("labels", TYPE_LABELS),
            sections=part.get("sections"),
        )
        docs.append(HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=[css]))

    all_pages = [pg for d in docs for pg in d.pages]
    docs[0].copy(all_pages).write_pdf(str(out_path))
    return out_path
