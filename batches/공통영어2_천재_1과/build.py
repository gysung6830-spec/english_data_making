# -*- coding: utf-8 -*-
"""공통영어2 천재 1과 합본 빌드 (본문 7소단원 + 외 지문 2개 = 9지문)."""
import sys; sys.path.insert(0,"/home/user/english_data_making"); sys.path.insert(0,".")
import gen_bon1, gen_bon2
from src.lecture_render import render_lecture_pdf
from verify import verify_passages, print_report
import fitz
ALL = list(gen_bon1.BON1) + list(gen_bon2.BON2) + list(gen_bon2.EXTRA)
FOOT="© 2026. ortica영어. All rights reserved."
if __name__=="__main__":
    print("총 지문:",len(ALL))
    for i,p in enumerate(ALL,1): print(" %2d. %-20s | %s"%(i,p.item_no,p.overview.key_grammar.point[:34]))
    print("\n=== 검증 ==="); ok=print_report(verify_passages(ALL))
    render_lecture_pdf(ALL,"공통영어2 천재_1과_학생용.pdf",teacher=False,footer_note=FOOT)
    render_lecture_pdf(ALL,"공통영어2 천재_1과_강사용.pdf",teacher=True,footer_note=FOOT)
    ds=fitz.open("공통영어2 천재_1과_학생용.pdf"); dt=fitz.open("공통영어2 천재_1과_강사용.pdf")
    print("합본 student",ds.page_count,"/ teacher",dt.page_count,"| verify",("PASS" if ok else "FAIL")); ds.close();dt.close()
