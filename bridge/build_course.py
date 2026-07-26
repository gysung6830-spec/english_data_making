"""'영어, 처음부터 다시' 기초 문법·해석 교재 빌드.

표지 + 전체 요약 + DAY들을 하나의 '교재' PDF로 만든다.

사용:
    python -m bridge.build_course
"""
from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
OUT_DIR = ROOT / "output"

_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


def build(out_name="교재_영어처음부터다시_샘플.pdf"):
    from weasyprint import HTML
    from bridge.course_data import COVER, OVERVIEW, DAYS

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html = _env.get_template("course.html.j2").render(cover=COVER, overview=OVERVIEW, days=DAYS)
    out = OUT_DIR / out_name
    doc = HTML(string=html, base_url=str(TEMPLATE_DIR)).render()
    doc.write_pdf(str(out))
    print(f"  → {out.name} ({len(doc.pages)}쪽)")
    return out


if __name__ == "__main__":
    print("교재 생성 중...")
    build()
    print("완료. output/ 폴더를 확인하세요.")
