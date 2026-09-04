# -*- coding: utf-8 -*-
"""올림포스 10-14강 FINAL passage 객체를 리워크용 JSON(에이전트 스키마)으로 덤프."""
import sys, importlib.util, glob, os, json
sys.path.insert(0,"/home/user/english_data_making")
SCRATCH="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
sys.path.insert(0,SCRATCH); sys.path.insert(0,SCRATCH+"/batches/공통영어2_천재_1과")
import gen_ol, gen_u12, gen_u13, apply_chips
from src.lecture_schemas import Chunk
from _helpers_oladd import finalize
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

OL=[gen_ol.P_u103,gen_ol.P_u11a,gen_ol.P_u111,gen_ol.P_u112,gen_ol.P_u113]+list(gen_u12.U12_ALL)+list(gen_u13.ALL)
apply_chips.apply(OL)
RC={}
for f in sorted(glob.glob(SCRATCH+"/rechunk/rc_*.py"))+sorted(glob.glob(SCRATCH+"/blanks/bl_*.py")):
    m=load(f,"ov_"+os.path.basename(f)[:-3]); RC.update(m.RC)
for p in OL:
    for s in p.analysis.sentences:
        k=(p.item_no.strip(), s.id)
        if k in RC: s.chunks=[Chunk(en=e,ko=o) for e,o in RC[k]]
add1=load(SCRATCH+"/gen_add1.py","gen_add1"); add2=load(SCRATCH+"/gen_add2.py","gen_add2")
U102,U141=add1.PARTS; U142,U143=add2.PARTS
FINAL=[U102]+OL+[U141,U142,U143]
MT={}
for f in sorted(glob.glob(SCRATCH+"/mt_g*.py")):
    m=load(f,"mt_"+os.path.basename(f)[:-3]); MT.update(m.MT)
for p in FINAL:
    for s in p.analysis.sentences:
        k=(p.item_no.strip(), s.id)
        if k in MT: s.mistips=list(MT[k])
for p in FINAL: finalize(p)

OUT=SCRATCH+"/olrw/passages"
order=[]
for i,p in enumerate(FINAL,1):
    d={"item_no":p.item_no, "theme":p.title, "overview":p.overview.model_dump(),
       "sentences":[s.model_dump() for s in p.analysis.sentences]}
    safe=p.item_no.strip().replace("/","-").replace(" ","")
    fn=f"p{i:02d}_{safe}.json"
    json.dump(d, open(OUT+"/"+fn,"w"), ensure_ascii=False, indent=1)
    order.append(fn)
    print(f"{i:2d}. {fn}  문장 {len(p.sentences)}  핵심문법={p.overview.key_grammar.point}")
json.dump(order, open(SCRATCH+"/olrw/order.json","w"), ensure_ascii=False, indent=1)
print("DUMP OK:", len(order), "지문")
