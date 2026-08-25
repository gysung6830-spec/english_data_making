# 올림포스 19지문: 새 O/X/△ 오답 + 어법 형광펜 spans 오버레이 적용 → verify → 렌더
import sys, importlib.util, glob, os, json
sys.path.insert(0,"/home/user/english_data_making")
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
sys.path.insert(0,SC); sys.path.insert(0,SC+"/batches/공통영어2_천재_1과")
import gen_ol, gen_u12, gen_u13, apply_chips
from src.lecture_schemas import Chunk, Misread
from src.lecture_render import render_lecture_pdf
from _helpers_oladd import finalize
from verify import verify_passages, print_report
import fitz
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
OL=[gen_ol.P_u103,gen_ol.P_u11a,gen_ol.P_u111,gen_ol.P_u112,gen_ol.P_u113]+list(gen_u12.U12_ALL)+list(gen_u13.ALL)
apply_chips.apply(OL)
RC={}
for f in sorted(glob.glob(SC+"/rechunk/rc_*.py"))+sorted(glob.glob(SC+"/blanks/bl_*.py")):
    m=load(f,"ov_"+os.path.basename(f)[:-3]); RC.update(m.RC)
for p in OL:
    for s in p.analysis.sentences:
        k=(p.item_no.strip(), s.id)
        if k in RC: s.chunks=[Chunk(en=e,ko=o) for e,o in RC[k]]
add1=load(SC+"/gen_add1.py","gen_add1"); add2=load(SC+"/gen_add2.py","gen_add2")
U102,U141=add1.PARTS; U142,U143=add2.PARTS
# easy_example (build_ol_full 과 동일)
EXm=load(SC+"/gen_add1.py","x")  # noop to keep pattern
FINAL=[U102]+OL+[U141,U142,U143]
# mistips 유지(학생용 오역팁)
MT={}
for f in sorted(glob.glob(SC+"/mt_g*.py")):
    m=load(f,"mt_"+os.path.basename(f)[:-3]); MT.update(m.MT)
for p in FINAL:
    for s in p.analysis.sentences:
        k=(p.item_no.strip(), s.id)
        if k in MT: s.mistips=list(MT[k])
for p in FINAL: finalize(p)

# ── 오버레이 로드(에이전트 산출 JSON) ──────────────────────────────
MR={}; GS={}
for f in sorted(glob.glob(SC+"/ox_overlays/ox_*.json")):
    d=json.load(open(f))
    MR.update(d.get("misreads",{})); GS.update(d.get("spans",{}))

def K(item,sid): return f"{item}||{sid}"
applied_mr=applied_gs=0
for p in FINAL:
    it=p.item_no.strip()
    for s in p.analysis.sentences:
        k=K(it,s.id)
        if k in MR:
            s.misreads=[Misread(statement=m["statement"], verdict=m.get("verdict","X"),
                trap_type=m.get("trap_type",""), anchor=m.get("anchor",""),
                why=m.get("why",""), killer=m.get("killer",False),
                english=m.get("english",False), integrative=m.get("integrative",False))
                for m in MR[k]]
            applied_mr+=1
        if k in GS:
            spans=GS[k]  # 문장의 grammar 칩 순서에 맞춘 리스트들
            for gi,g in enumerate(s.grammar):
                if gi < len(spans): g.spans=list(spans[gi])
            applied_gs+=1
print(f"오버레이 적용: 오답 {applied_mr}문장 · 형광펜 {applied_gs}문장 (전체 {sum(len(p.analysis.sentences) for p in FINAL)}문장)")

only=os.environ.get("ONLY")   # 특정 item_no 만 렌더(검증용)
render_set=[p for p in FINAL if (not only or p.item_no.strip()==only)]
ok=print_report(verify_passages(render_set))
if os.environ.get("RENDER") and ok:
    FOOT="© 2026. ortica영어. All rights reserved."
    stem=SC+"/올림포스_기본1_10강-14강_NEW"
    render_lecture_pdf(render_set, stem+"_학생용.pdf", teacher=False, footer_note=FOOT)
    render_lecture_pdf(render_set, stem+"_강사용.pdf", teacher=True, footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        d=fitz.open(f"{stem}_{suf}.pdf"); print(f"  {suf}: {d.page_count}p"); d.close()
    print("RENDER OK")
