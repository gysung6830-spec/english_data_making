"""조판기 (명세서 §6, §4).

- TYPE_ORDER 대로만 순회하므로 유형 순서가 자동 보장된다.
- 문서 전체에 걸쳐 문항 번호를 연속으로 부여한다(지문2는 7번부터…).
- 배치: [모든 지문의 문제] → [모든 지문의 해설].
- 문제와 해설은 같은 번호로 대응한다.
- 2단(좌/우) 조판, 지문 라벨, 볼드 5곳, 쪽번호는 템플릿/CSS 가 담당한다.
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from .types import TYPE_LABELS, TYPE_ORDER, TYPE_PROMPTS, Passage

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=False,  # 생성기가 만든 HTML 조각을 그대로 삽입한다
)


def _blocks(passages: list[Passage], start: int):
    """지문별 문제/해설 블록을 만들며 문항 번호를 연속 부여한다."""
    qblocks: list[dict] = []
    ablocks: list[dict] = []
    n = start
    for i, p in enumerate(passages, start=1):
        q_items: list[dict] = []
        a_items: list[dict] = []
        for t in TYPE_ORDER:
            q_items.append({
                "no": n,
                "type": t,
                "prompt": TYPE_PROMPTS[t],
                "body": Markup(p.q[t]),
            })
            a_items.append({
                "no": n,
                "type": t,
                "label": TYPE_LABELS[t],
                "body": Markup(p.a[t]),
            })
            n += 1
        label = f"[지문 {i}]"
        qblocks.append({"label": label, "title": p.title, "rows": q_items})
        ablocks.append({"label": label, "title": p.title, "rows": a_items})
    return qblocks, ablocks


# 자료 하단 저작권 문구 기본값(필요하면 render_pdf(footer_note=...) 로 교체)
DEFAULT_FOOTER = "ⓒ 2026. 김은아영어연구소. All rights reserved."


def render_html(
    passages: list[Passage],
    header_note: str = "",
    doc_title: str = "영어 영역",
    start: int = 1,
    footer_note: str = DEFAULT_FOOTER,
) -> str:
    qblocks, ablocks = _blocks(passages, start)
    tmpl = _env.get_template("exam.html.j2")
    return tmpl.render(
        qblocks=qblocks,
        ablocks=ablocks,
        header_note=header_note,
        doc_title=doc_title,
        footer_note=footer_note,
    )


def render_pdf(
    passages: list[Passage],
    out_path: str | Path,
    header_note: str = "",
    doc_title: str = "영어 영역",
    start: int = 1,
    footer_note: str = DEFAULT_FOOTER,
) -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(passages, header_note=header_note, doc_title=doc_title,
                       start=start, footer_note=footer_note)
    css = CSS(filename=str(TEMPLATE_DIR / "exam.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
    return out_path
