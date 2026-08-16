# -*- coding: utf-8 -*-
"""rechunk(rc_*) 위에 blanks(bl_*) 오버레이를 얹어 적용 → verify → 렌더.

bl_* 는 각 문장의 '최종 조각 세트'(빈칸 보강 완료)를 담으므로 rc_* 와 같은 문장 키가
있으면 bl_* 가 우선한다(bl_* 는 rc_* 결과를 기준으로 빈칸만 추가한 것이므로 안전)."""
import sys, importlib.util, glob, os, re
sys.path.insert(0,"/home/user/english_data_making")
SCRATCH="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
sys.path.insert(0,SCRATCH); sys.path.insert(0,SCRATCH+"/batches/공통영어2_천재_1과")
import gen_ol, gen_u12, gen_u13, apply_chips
from src.lecture_schemas import Chunk
from src.lecture_render import render_lecture_pdf
from verify import verify_passages, print_report, _content_words, _BLANK
import fitz
def load(p,n):
    spec=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
b1=load(SCRATCH+"/batches/공통영어2_천재_1과/gen_bon1.py","gb1")
b2=load(SCRATCH+"/batches/공통영어2_천재_1과/gen_bon2.py","gb2")
OL=[gen_ol.P_u103,gen_ol.P_u11a,gen_ol.P_u111,gen_ol.P_u112,gen_ol.P_u113]+list(gen_u12.U12_ALL)+list(gen_u13.ALL)
apply_chips.apply(OL)
CE=list(b1.BON1)+list(b2.BON2)+list(b2.EXTRA)

RC={}
for f in sorted(glob.glob(SCRATCH+"/rechunk/rc_*.py")):
    m=load(f,os.path.basename(f)[:-3]); RC.update(m.RC)
BL={}
for f in sorted(glob.glob(SCRATCH+"/blanks/bl_*.py")):
    m=load(f,"b_"+os.path.basename(f)[:-3]); BL.update(m.RC)
print("rc 문장:",len(RC),"/ bl 문장:",len(BL))

def norm(s): return re.sub(r"\s+"," ",re.sub(r"\[\[|\]\]","",s)).strip()

def apply(passages, name):
    bad=[]
    for p in passages:
        for s in p.analysis.sentences:
            k=(p.item_no.strip(), s.id)
            new=None
            if k in RC: new=RC[k]
            if k in BL:
                # bl_* 는 rc_* 결과에 빈칸만 추가한 것 → 텍스트(마커제거) 동일해야 정상
                if k in RC and [ (norm(e),norm(o)) for e,o in RC[k]] != [ (norm(e),norm(o)) for e,o in BL[k]]:
                    bad.append((k,"bl≠rc 텍스트"))
                new=BL[k]
            if new is not None:
                s.chunks=[Chunk(en=e,ko=o) for e,o in new]
    if bad: print("  ⚠ 텍스트 불일치:",bad[:5])
    return bad

def stats(passages):
    nc=[len(s.chunks) for p in passages for s in p.analysis.sentences]
    nb=[len(_BLANK.findall(c.ko)) for p in passages for s in p.analysis.sentences for c in s.chunks]
    noblank=sum(1 for p in passages for s in p.analysis.sentences for c in s.chunks
                if "[[" not in c.ko and _content_words(c.en)>=1)
    return sum(nb)/len(nc), noblank  # 문장당 아님, 참고용

FOOT="© 2026. ortica영어. All rights reserved."
allok=True
for name,passages,outdir,stem in [
    ("공통영어2 천재_1과",CE,SCRATCH+"/batches/공통영어2_천재_1과","공통영어2 천재_1과"),
    ("올림포스 독해 기본1_10강-14강",OL,SCRATCH,"올림포스 독해 기본1_10강-14강")]:
    apply(passages,name)
    bpc,nb=stats(passages)
    print("\n===== %s : 빈칸/문장≈%.2f · 내용어무빈칸조각 남은수=%d ====="%(name,bpc,nb))
    ok=print_report(verify_passages(passages)); allok=allok and ok
    if not ok: print("  ✗ ERROR — 렌더 보류"); continue
    render_lecture_pdf(passages,f"{outdir}/{stem}_학생용.pdf",teacher=False,footer_note=FOOT)
    render_lecture_pdf(passages,f"{outdir}/{stem}_강사용.pdf",teacher=True,footer_note=FOOT)
    d=fitz.open(f"{outdir}/{stem}_학생용.pdf"); print("  렌더:",d.page_count,"p"); d.close()
print("\n전체:", "PASS" if allok else "FAIL")
