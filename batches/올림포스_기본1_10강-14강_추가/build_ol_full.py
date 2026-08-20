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

# 신규 4지문 easy_example 채우기(지문 주제·내용에서 뽑은 쉬운 풀이 — 무관한 비유 금지)
EX={
 ("Unit10-2","1~2"):"혼자 있고 싶다가도 누군가와 함께 있고 싶어지는 마음.",
 ("Unit10-2","3"):"함께 있는 동안 말과 표정·몸짓으로 마음을 주고받는 것.",
 ("Unit10-2","4~5"):"남이 있어야 내가 '존재하고 나답다'고 확인되는 것.",
 ("Unit10-2","6"):"사람은 결국 혼자로는 오래 못 견디고 어울림을 찾는 것.",
 ("Unit14-1","1~2"):"자기 홍보가 쑥스럽지만 몰래 할 일은 아니라는 것.",
 ("Unit14-1","3~4"):"성공하려면 오히려 드러내야 하고, 미리 알아채고 대비하는 게 핵심인 것.",
 ("Unit14-1","5~6"):"기회를 못 알아보면 좋은 인상 남길 순간을 놓치는 것.",
 ("Unit14-1","7"):"내가 없는 자리에서 사람들이 뭐라 말할지까지 관리하는 것.",
 ("Unit14-2","1"):"움직임을 알아채는 능력이 별을 찾는 데 쓰인 것.",
 ("Unit14-2","2~3"):"같은 하늘을 며칠 간격으로 두 번 찍어 둔 것.",
 ("Unit14-2","4"):"별은 그대로인데 행성만 사진에서 자리를 옮기는 것.",
 ("Unit14-2","5"):"수많은 점 사이 움직인 하나를 골라내야 하는 어려움.",
 ("Unit14-2","6~7"):"두 사진을 번갈아 넘겨 '움직이는 점'을 눈으로 잡아낸 것.",
 ("Unit14-2","8"):"그렇게 찾아낸 점이 바로 명왕성이었던 것.",
 ("Unit14-3","1"):"숲이 자라는 속도보다 베는 속도가 훨씬 빠른 것.",
 ("Unit14-3","2"):"목재를 줄여야 하는 진짜 이유는 숲의 '기능' 때문이라는 것.",
 ("Unit14-3","3~4"):"숲이 탄소를 빨아들여 온난화를 막고 산소를 주는 것.",
 ("Unit14-3","5"):"별로 중요하지 않은 데 나무를 마구 쓰는 일이 많은 것.",
 ("Unit14-3","6~7"):"폭풍 막으려 합판으로 창 막고, 지나면 그냥 버리는 것.",
 ("Unit14-3","8"):"폭풍 막자고 숲을 베는데, 정작 숲이 폭풍을 막아 준다는 반어.",
}
for p in [U102,U141,U142,U143]:
    for fb in p.overview.flow_blocks:
        k=(p.item_no.strip(), fb.sentence_range.strip())
        if k in EX: fb.easy_example=EX[k]

# 목차 순서: Unit10-2 → (기존 15) → Unit14-1 → Unit14-2 → Unit14-3
FINAL=[U102]+OL+[U141,U142,U143]

# 오역 팁(mistips) 오버레이 적용 — 학생용 전용
MT={}
for f in sorted(glob.glob(SCRATCH+"/mt_g*.py")):
    m=load(f,"mt_"+os.path.basename(f)[:-3]); MT.update(m.MT)
n_mt=0
for p in FINAL:
    for s in p.analysis.sentences:
        k=(p.item_no.strip(), s.id)
        if k in MT: s.mistips=list(MT[k]); n_mt+=len(s.mistips)
print("오역 팁 적용:",n_mt,"개 (",len(MT),"문장)")

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
