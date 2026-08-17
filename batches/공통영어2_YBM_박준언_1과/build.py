# -*- coding: utf-8 -*-
"""YBM 공통영어2 박준언 1과(Fake News) — 소단원 6개 gen 파일을 목차 순서로 모아
finalize→verify→렌더(학생/강사)."""
import sys, importlib.util, os
BD=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,"/home/user/english_data_making"); sys.path.insert(0,BD)
from _helpers import finalize
from src.lecture_render import render_lecture_pdf
from verify import verify_passages, print_report
import fitz
def load(n):
    p=os.path.join(BD,n)
    s=importlib.util.spec_from_file_location(n[:-3],p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ALL=[]
for n in ["gen_gen1.py","gen_gen2.py","gen_gen3.py","gen_gen4.py","gen_gen5.py","gen_gen6.py"]:
    ALL += list(load(n).PARTS)
print("소단원 수:",len(ALL))
for p in ALL: finalize(p)
ok=print_report(verify_passages(ALL))
print("목차:")
for p in ALL: print("  -",p.item_no,"|",len(p.sentences),"문장")
if ok:
    FOOT="© 2026. ortica영어. All rights reserved."
    stem="공통영어2 YBM_박준언_1과"
    render_lecture_pdf(ALL,f"{BD}/{stem}_학생용.pdf",teacher=False,footer_note=FOOT)
    render_lecture_pdf(ALL,f"{BD}/{stem}_강사용.pdf",teacher=True,footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        d=fitz.open(f"{BD}/{stem}_{suf}.pdf"); print(f"  {suf}: {d.page_count}p"); d.close()
    print("RENDER OK")
else:
    print("ERROR 있음 — 렌더 보류")
