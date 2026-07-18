"""Report -> HTML -> PDF (Jinja2 + WeasyPrint)."""
from __future__ import annotations

from pathlib import Path

import re

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from . import schemas

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

# 특히 중요한 핵심 어법 키워드 (부각 표시용)
KEY_GRAMMAR = ["관계", "분사", "가정법", "비교", "도치", "강조", "5형식", "5 형식", "사역", "지각"]


def _is_key_grammar(text: str | None) -> bool:
    if not text:
        return False
    return any(k in text for k in KEY_GRAMMAR)


_env.filters["is_key_grammar"] = _is_key_grammar


def _highlight_words(text: str | None, words) -> Markup:
    """영어 요약문 안에서 핵심 단어(words)를 굵게 표시."""
    if not text:
        return Markup("")
    ws = sorted({w.strip() for w in (words or []) if w and w.strip()}, key=len, reverse=True)
    if not ws:
        return escape(text)
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in ws) + r")\b", re.IGNORECASE)
    out: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        out.append(str(escape(text[last:m.start()])))
        out.append('<b class="kw">' + str(escape(m.group(0))) + "</b>")
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


_env.filters["highlight_words"] = _highlight_words


def _as_list(reports) -> list:
    if isinstance(reports, schemas.Report):
        return [reports]
    return list(reports)


def render_html(reports, footer_note: str = "") -> str:
    """reports: 단일 Report 또는 여러 Report(list). 여러 지문이면 순서대로 출력."""
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(reports=_as_list(reports), footer_note=footer_note)


def _cap_report(report: schemas.Report, cap: int) -> schemas.Report:
    """어휘 개수를 cap 개로 줄인 사본 반환(원본은 건드리지 않음)."""
    if cap >= len(report.vocab.items):
        return report
    new_vocab = report.vocab.model_copy(update={"items": report.vocab.items[:cap]})
    return report.model_copy(update={"vocab": new_vocab})


def _fit_report(report, footer_note, css, min_vocab: int):
    """한 지문이 2페이지에 들어오도록 어휘 개수를 필요한 만큼만 줄인다."""
    from weasyprint import HTML

    def pages(cap):
        r = _cap_report(report, cap)
        html = render_html([r], footer_note)
        doc = HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=[css])
        return len(doc.pages), r

    n = len(report.vocab.items)
    p, r = pages(n)
    if p <= 2:
        return report            # 이미 2페이지 이내면 그대로
    cap = n
    while cap > min_vocab:       # 최소 개수까지 한 개씩 줄이며 재시도
        cap -= 1
        p, r = pages(cap)
        if p <= 2:
            return r
    return r                     # 최소 개수까지 줄여도 넘치면 그 상태로


def render_pdf(reports, out_path: str | Path, footer_note: str = "",
               fit_pages: bool = True, min_vocab: int = 8) -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트 (무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    rlist = _as_list(reports)

    def build(rs):
        html = render_html(rs, footer_note)
        return HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=[css])

    doc = build(rlist)
    # 지문 1개당 2페이지(1p: 요약~어휘, 2p: 직독직해)를 넘기면 어휘를 줄여 다시 렌더
    if fit_pages and len(doc.pages) > 2 * len(rlist):
        rlist = [_fit_report(r, footer_note, css, min_vocab) for r in rlist]
        doc = build(rlist)
    doc.write_pdf(str(out_path))
    return out_path


def combine_pdfs(pdf_paths: list[Path], out_path: Path) -> Path:
    """여러 지문 PDF 를 하나로 합친다 (pypdf 사용, 없으면 개별 유지)."""
    try:
        from pypdf import PdfWriter
    except Exception:
        return out_path  # 병합 라이브러리 없으면 개별 파일 유지
    writer = PdfWriter()
    for p in pdf_paths:
        writer.append(str(p))
    with out_path.open("wb") as f:
        writer.write(f)
    return out_path
