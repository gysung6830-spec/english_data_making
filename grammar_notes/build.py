# -*- coding: utf-8 -*-
"""특강용 문법 필기 교재 빌드 진입점.

사용:
  python -m grammar_notes.build 01        # UNIT 01 학생용/교사용 PDF 생성
"""
import importlib
import sys
from pathlib import Path

from grammar_notes.generator import build_pdf

OUT = Path(__file__).resolve().parent.parent / "output"


def main(argv):
    unit_no = (argv[0] if argv else "01").zfill(2)
    mod = importlib.import_module(f"grammar_notes.units.unit{unit_no}")
    made = build_pdf(mod.UNIT, OUT)
    for p in made:
        print("생성:", p.name)


if __name__ == "__main__":
    main(sys.argv[1:])
