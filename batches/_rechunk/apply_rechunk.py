# -*- coding: utf-8 -*-
"""재분할 오버레이(rc_*.py의 RC dict)를 두 배치에 적용 → verify → 렌더."""
import sys, importlib.util, glob, os
sys.path.insert(0,"/home/user/english_data_making")
SCRATCH="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
sys.path.insert(0,SCRATCH); sys.path.insert(0,SCRATCH+"/batches/공통영어2_천재_1과")
import gen_ol, gen_u12, gen_u13, apply_chips
from src.lecture_schemas import Chunk
from src.lecture_render import render_lecture_pdf
from verify import verify_passages, print_report
import fitz
def load(p,n):
    spec=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
b1=load(SCRATCH+"/batches/공통영어2_천재_1과/gen_bon1.py","gb1")
b2=load(SCRATCH+"/batches/공통영어2_천재_1과/gen_bon2.py","gb2")

OL=[gen_ol.P_u103,gen_ol.P_u11a,gen_ol.P_u111,gen_ol.P_u112,gen_ol.P_u113]+list(gen_u12.U12_ALL)+list(gen_u13.ALL)
apply_chips.apply(OL)
CE=list(b1.BON1)+list(b2.BON2)+list(b2.EXTRA)

# 오버레이 병합
RC={}
for f in sorted(glob.glob(SCRATCH+"/rechunk/rc_*.py")):
    m=load(f,os.path.basename(f)[:-3])
    RC.update(m.RC); print("loaded",os.path.basename(f),len(m.RC),"entries")
print("총 오버레이 문장:",len(RC))

def apply(passages):
    hit=0; miss=[]
    keys=set(RC)
    for p in passages:
        for s in p.analysis.sentences:
            k=(p.item_no.strip(), s.id)
            if k in RC:
                s.chunks=[Chunk(en=e,ko=o) for e,o in RC[k]]; hit+=1; keys.discard(k)
    return hit,keys

def stats(passages):
    import re
    nc=[len(s.chunks) for p in passages for s in p.analysis.sentences]
    return sum(nc)/len(nc)

FOOT="© 2026. ortica영어. All rights reserved."
for name,passages,outdir,stem in [
    ("공통영어2 천재_1과",CE,SCRATCH+"/batches/공통영어2_천재_1과","공통영어2 천재_1과"),
    ("올림포스 독해 기본1_10강-14강",OL,SCRATCH,"올림포스 독해 기본1_10강-14강")]:
    before=stats(passages); hit,unused=apply(passages); after=stats(passages)
    print("\n===== %s : %d문장 재분할 · 평균 %.2f→%.2f조각 ====="%(name,hit,before,after))
    if unused: print("  ⚠ 미매칭 키(무시됨):",list(unused)[:5])
    ok=print_report(verify_passages(passages))
    if not ok: print("  ✗ ERROR 있음 — 렌더 중단"); continue
    render_lecture_pdf(passages,f"{outdir}/{stem}_학생용.pdf",teacher=False,footer_note=FOOT)
    render_lecture_pdf(passages,f"{outdir}/{stem}_강사용.pdf",teacher=True,footer_note=FOOT)
    d=fitz.open(f"{outdir}/{stem}_학생용.pdf"); print("  렌더 완료:",d.page_count,"p / verify PASS"); d.close()
