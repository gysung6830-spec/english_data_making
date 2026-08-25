import sys, importlib.util, glob, os, json
sys.path.insert(0,"/home/user/english_data_making")
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
sys.path.insert(0,SC); sys.path.insert(0,SC+"/batches/공통영어2_천재_1과")
import gen_ol, gen_u12, gen_u13, apply_chips
from src.lecture_schemas import Chunk
from _helpers_oladd import finalize
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
FINAL=[U102]+OL+[U141,U142,U143]
for p in FINAL: finalize(p)

out=[]
for p in FINAL:
    sents=[]
    for s in p.analysis.sentences:
        sents.append({"id":s.id,"english":s.english,
                      "grammar":[{"tag":g.tag,"note":g.note} for g in s.grammar]})
    out.append({"item_no":p.item_no,"title":p.title,
                "theme_ko":p.overview.theme_ko,
                "structure":p.overview.structure,
                "sentences":sents})
json.dump(out, open(SC+"/ol_data.json","w"), ensure_ascii=False, indent=1)
print("passages:",len(out))
print("item_nos:",[p["item_no"] for p in out])
print("total sentences:",sum(len(p["sentences"]) for p in out))
