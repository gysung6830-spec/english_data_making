# YBM 박준언 1과/2과: 새 O/X/△ 오답 + 어법 형광펜 spans 오버레이 적용 → verify → 렌더
import sys, importlib.util, os, glob, json
sys.path.insert(0,"/home/user/english_data_making")
from src.lecture_schemas import Misread
from src.lecture_render import render_lecture_pdf
from verify import verify_passages, print_report
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
BASE="/home/user/english_data_making/batches"
LESSON=os.environ.get("LESSON","1")
if LESSON=="1":
    BD=BASE+"/공통영어2_YBM_박준언_1과"; GENS=["gen_gen%d.py"%i for i in range(1,7)]; OVD=SC+"/ybm/ov1"; stem=SC+"/공통영어2 YBM_박준언_1과_필생보"
else:
    BD=BASE+"/공통영어2_YBM_박준언_2과"; GENS=["gen_gen%d.py"%i for i in range(1,6)]; OVD=SC+"/ybm/ov2"; stem=SC+"/공통영어2 YBM_박준언_2과_필생보"
sys.path.insert(0, BD)
def load(n):
    p=os.path.join(BD,n); s=importlib.util.spec_from_file_location(n[:-3],p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
from _helpers import finalize
ALL=[]
for n in GENS: ALL += list(load(n).PARTS)
for p in ALL: finalize(p)
# 오버레이
MR={}; GS={}
for f in sorted(glob.glob(OVD+"/ox_*.json")):
    d=json.load(open(f)); MR.update(d.get("misreads",{})); GS.update(d.get("spans",{}))
def K(it,sid): return f"{it}||{sid}"
amr=ags=0
for p in ALL:
    it=p.item_no.strip()
    for s in p.analysis.sentences:
        k=K(it,s.id)
        if k in MR:
            s.misreads=[Misread(statement=m["statement"],verdict=m.get("verdict","X"),
                trap_type=m.get("trap_type",""),anchor=m.get("anchor",""),why=m.get("why",""),
                killer=m.get("killer",False),english=m.get("english",False),
                integrative=m.get("integrative",False)) for m in MR[k]]; amr+=1
        if k in GS:
            for gi,g in enumerate(s.grammar):
                if gi < len(GS[k]): g.spans=list(GS[k][gi])
            ags+=1
print(f"L{LESSON} 오버레이: 오답 {amr}문장 · 형광펜 {ags}문장 / 전체 {sum(len(p.analysis.sentences) for p in ALL)}")
only=os.environ.get("ONLY")
RS=[p for p in ALL if (not only or p.item_no.strip()==only)]
ok=print_report(verify_passages(RS, cross_check=(len(RS)>1)))
if os.environ.get("RENDER") and ok:
    FOOT="© 2026. ortica영어. All rights reserved."
    render_lecture_pdf(RS, stem+"_학생용.pdf", teacher=False, footer_note=FOOT)
    render_lecture_pdf(RS, stem+"_강사용.pdf", teacher=True, footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        dd=fitz.open(f"{stem}_{suf}.pdf"); print(f"  {suf}: {dd.page_count}p"); dd.close()
    print("RENDER OK")
