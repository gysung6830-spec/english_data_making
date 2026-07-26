"""중등 기초 브릿지 학습지 빌드 스크립트.

lesson1_data.py 의 DAYS 를 읽어, 일차별 PDF + 전체 합본 PDF 를 output/ 에 생성한다.

사용:
    python -m bridge.build_bridge          # 전체(1~9일차) + 합본
    python -m bridge.build_bridge 1 3      # 1,3일차만
"""
from __future__ import annotations

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
OUT_DIR = ROOT / "output"

_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


def render_day(day: dict) -> str:
    tmpl = _env.get_template("bridge_day.html.j2")
    return tmpl.render(d=day)


def build(days, which=None):
    from weasyprint import HTML

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_paths = []
    for day in days:
        if which and day["day_no"] not in which:
            continue
        html = render_day(day)
        name = f"브릿지_L1_{day['day_no']:02d}일차.pdf"
        out = OUT_DIR / name
        HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out))
        pages = len(HTML(string=html, base_url=str(TEMPLATE_DIR)).render().pages)
        print(f"  {day['day_no']}일차 → {name} ({pages}쪽)")
        pdf_paths.append(out)

    # 합본
    if not which and len(pdf_paths) > 1:
        try:
            from pypdf import PdfWriter
            w = PdfWriter()
            for p in pdf_paths:
                w.append(str(p))
            combo = OUT_DIR / "브릿지_L1_전체합본.pdf"
            with combo.open("wb") as f:
                w.write(f)
            print(f"  합본 → {combo.name}")
        except Exception as e:
            print(f"  (합본 생략: {e})")
    return pdf_paths


if __name__ == "__main__":
    from bridge.lesson1_data import DAYS

    which = {int(a) for a in sys.argv[1:]} or None
    print("브릿지 학습지 생성 중...")
    build(DAYS, which)
    print("완료. output/ 폴더를 확인하세요.")
