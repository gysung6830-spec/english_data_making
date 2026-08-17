# -*- coding: utf-8 -*-
"""올림포스 10강-14강 합본 확장: 기존 15개(재분할+빈칸 오버레이 적용) + 신규 4개
(Unit10-2 앞 / Unit14-1·2·3 뒤) → finalize → verify(교차검사) → 렌더."""
import sys, importlib.util, glob, os
sys.path.insert(0,"/home/user/english_data_making")
SCRATCH="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
sys.path.insert(0,SCRATCH); sys.path.insert(0,SCRATCH+"/batches/공통영어2_천재_1과")
import gen_ol, gen_u12, gen_u13, apply_chips
from src.lecture_schemas import Chunk
from src.lecture_render import render_lecture_pdf
from _helpers_oladd import finalize
from verify import verify_passages, print_report
import fitz
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

# 기존 15개
OL=[gen_ol.P_u103,gen_ol.P_u11a,gen_ol.P_u111,gen_ol.P_u112,gen_ol.P_u113]+list(gen_u12.U12_ALL)+list(gen_u13.ALL)
apply_chips.apply(OL)
# 재분할(rc_*) + 빈칸(bl_*) 오버레이 적용
RC={}
for f in sorted(glob.glob(SCRATCH+"/rechunk/rc_*.py"))+sorted(glob.glob(SCRATCH+"/blanks/bl_*.py")):
    m=load(f,"ov_"+os.path.basename(f)[:-3]); RC.update(m.RC)
for p in OL:
    for s in p.analysis.sentences:
        k=(p.item_no.strip(), s.id)
        if k in RC: s.chunks=[Chunk(en=e,ko=o) for e,o in RC[k]]

# 신규 4개
add1=load(SCRATCH+"/gen_add1.py","gen_add1")   # P1=Unit10-2, P2=Unit14-1
add2=load(SCRATCH+"/gen_add2.py","gen_add2")   # P3=Unit14-2, P4=Unit14-3
U102,U141=add1.PARTS
U142,U143=add2.PARTS

# 목차 순서: Unit10-2 → (기존 15) → Unit14-1 → Unit14-2 → Unit14-3
FINAL=[U102]+OL+[U141,U142,U143]
for p in FINAL: finalize(p)
print("확장 합본 소단원 수:",len(FINAL))
ok=print_report(verify_passages(FINAL))   # cross_check=True → 핵심문법 중복 검사 포함
print("목차·핵심문법:")
for i,p in enumerate(FINAL,1):
    print(f"  {i:2d}. {p.item_no:16s} ({len(p.sentences)}) {p.overview.key_grammar.point}")
if ok:
    FOOT="© 2026. ortica영어. All rights reserved."
    stem="올림포스 독해 기본1_10강-14강"
    render_lecture_pdf(FINAL,f"{SCRATCH}/{stem}_학생용.pdf",teacher=False,footer_note=FOOT)
    render_lecture_pdf(FINAL,f"{SCRATCH}/{stem}_강사용.pdf",teacher=True,footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        d=fitz.open(f"{SCRATCH}/{stem}_{suf}.pdf"); print(f"  {suf}: {d.page_count}p"); d.close()
    print("RENDER OK")
else:
    print("ERROR/중복 있음 — 렌더 보류")
