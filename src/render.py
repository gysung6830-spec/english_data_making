"""Report -> HTML -> PDF (Jinja2 + WeasyPrint)."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import schemas

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)


def render_html(report: schemas.Report, footer_note: str = "") -> str:
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(report=report, footer_note=footer_note)


def render_pdf(report: schemas.Report, out_path: str | Path, footer_note: str = "") -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트 (무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(report, footer_note)
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
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
