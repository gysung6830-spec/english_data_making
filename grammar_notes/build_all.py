# -*- coding: utf-8 -*-
"""UNIT 01~10 전체 빌드 + 합본 PDF 생성.

사용:
  python -m grammar_notes.build_all
결과 (output/):
  - 유닛별 PDF (특강문법_UNITxx_..._학생용/교사용_정답.pdf)
  - 합본 PDF   (특강문법_전체_학생용.pdf / 특강문법_전체_교사용_정답.pdf)
"""
import importlib
from pathlib import Path

from pypdf import PdfWriter

from grammar_notes.generator import build_pdf

OUT = Path(__file__).resolve().parent.parent / "output"
UNITS = [f"{i:02d}" for i in range(1, 11)]


def main():
    student_pdfs, teacher_pdfs = [], []
    for no in UNITS:
        mod = importlib.import_module(f"grammar_notes.units.unit{no}")
        made = build_pdf(mod.UNIT, OUT)  # [학생용, 교사용]
        student_pdfs.append(made[0])
        teacher_pdfs.append(made[1])
        print("생성:", made[0].name, "/", made[1].name)

    for pdfs, name in [(student_pdfs, "특강문법_전체_학생용.pdf"),
                       (teacher_pdfs, "특강문법_전체_교사용_정답.pdf")]:
        w = PdfWriter()
        for p in pdfs:
            w.append(str(p))
        out = OUT / name
        with open(out, "wb") as f:
            w.write(f)
        w.close()
        print("합본:", out.name)


if __name__ == "__main__":
    main()
