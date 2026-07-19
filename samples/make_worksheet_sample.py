"""구문 분석 학습지 디자인 미리보기(목 데이터, API 키 불필요).

실행: python -m samples.make_worksheet_sample
-> output/sample_worksheet_A.pdf (분석 학습지형)
   output/sample_worksheet_B.pdf (대조표형, 태깅 얹기)
   HTML 미리보기도 함께 저장한다.
"""
from __future__ import annotations

from pathlib import Path

from src.worksheet import renderer
from src.worksheet.mock import mock_analysis

ROOT = Path(__file__).resolve().parent.parent
FOOTER = "(C)2026.김은아영어연구소.All rights reserved"


def build(out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or (ROOT / "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    a = mock_analysis()

    made: list[Path] = []
    pa = out_dir / "sample_worksheet_A.pdf"
    renderer.render_pdf([a], pa, layout="A", footer_note=FOOTER)
    made.append(pa)

    pb = out_dir / "sample_worksheet_B.pdf"
    renderer.render_pdf([a], pb, layout="B", tagged=True, footer_note=FOOTER)
    made.append(pb)

    (out_dir / "sample_worksheet_A.html").write_text(
        renderer.render_a_html([a], footer_note=FOOTER), encoding="utf-8")
    (out_dir / "sample_worksheet_B.html").write_text(
        renderer.render_b_html([a], tagged=True, footer_note=FOOTER), encoding="utf-8")
    return made


if __name__ == "__main__":
    for p in build():
        print(f"생성됨: {p}")
