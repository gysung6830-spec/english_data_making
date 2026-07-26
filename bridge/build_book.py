"""중등 기초 브릿지 '교재' 빌드 — 표지 + 전체요약 + DAY들을 한 권 PDF로.

사용:
    python -m bridge.build_book            # 전체(표지+요약+1~9일차)
    python -m bridge.build_book 1          # 표지+요약+1일차만 (샘플)
"""
from __future__ import annotations

import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
OUT_DIR = ROOT / "output"

_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


def build(which=None, out_name=None):
    from weasyprint import HTML
    from bridge.lesson1_data import COVER, OVERVIEW, DAYS

    days = [d for d in DAYS if not which or d["day_no"] in which]
    if out_name is None:
        out_name = "교재_브릿지_L1_샘플.pdf" if which else "교재_브릿지_L1_전체.pdf"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html = _env.get_template("bridge_book.html.j2").render(cover=COVER, overview=OVERVIEW, days=days)
    out = OUT_DIR / out_name
    doc = HTML(string=html, base_url=str(TEMPLATE_DIR)).render()
    doc.write_pdf(str(out))
    print(f"  → {out.name} ({len(doc.pages)}쪽, DAY {[d['day_no'] for d in days]})")
    return out


if __name__ == "__main__":
    which = {int(a) for a in sys.argv[1:]} or None
    print("교재 생성 중...")
    build(which)
    print("완료. output/ 폴더를 확인하세요.")
