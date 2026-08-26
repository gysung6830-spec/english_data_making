# 고3 2025-09 모의고사 필생보: passage JSON(에이전트 저작) → LecturePassage → verify → 렌더
import sys, glob, json, os
sys.path.insert(0,"/home/user/english_data_making")
from src.lecture_schemas import (LecturePassage, LectureSentence, Overview, KeyGrammar,
    GrammarNote, GrammarDrill, RestatementChain, FlowBlock, SentenceAnalysis, SentenceItem,
    Chunk, GrammarChip, Vocab, Misread)
from src.lecture_render import render_lecture_pdf
from verify import verify_passages, print_report
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"

def _engflag(m):
    """english 필드 강건화: bool 이면 그대로, 문자열이면 statement 가 영어인지로 판정."""
    e=m.get("english",False)
    if isinstance(e,bool): return e
    st=m.get("statement","") or ""
    asc=sum(1 for c in st if c.isascii() and c.isalpha())
    kor=sum(1 for c in st if '\uac00'<=c<='\ud7a3')
    return asc>kor

def mk_passage(d):
    ov=d["overview"]; kg=ov["key_grammar"]
    overview=Overview(
        theme_ko=ov["theme_ko"],
        key_grammar=KeyGrammar(
            point=kg["point"], source_sentence=kg.get("source_sentence",""),
            explanation=[GrammarNote(chip=n["chip"], text=n["text"]) for n in kg["explanation"]],
            example=kg.get("example",""), example_analysis=kg.get("example_analysis",""),
            drills=[GrammarDrill(kind=x["kind"], question=x["question"], answer=x["answer"],
                    options=x.get("options",[]), words=x.get("words",[]),
                    from_passage=x.get("from_passage",False)) for x in kg["drills"]]),
        topic=ov["topic"], stance=ov["stance"], stance_reason=ov["stance_reason"],
        structure=ov["structure"], structure_reason=ov["structure_reason"],
        restatement_chains=[RestatementChain(label=c["label"], expressions=c["expressions"],
                            variation=c.get("variation","")) for c in ov["restatement_chains"]],
        flow_blocks=[FlowBlock(stage=b["stage"], sentence_range=b["sentence_range"],
                    summary=b["summary"], easy_example=b.get("easy_example","")) for b in ov["flow_blocks"]])
    items=[]
    for s in d["sentences"]:
        items.append(SentenceItem(id=s["id"], english=s["english"],
            grammar=[GrammarChip(tag=g["tag"], note=g.get("note",""), spans=g.get("spans",[])) for g in s.get("grammar",[])],
            vocab=[Vocab(word=v["word"], meaning=v["meaning"]) for v in s.get("vocab",[])],
            chunks=[Chunk(en=c["en"], ko=c["ko"]) for c in s["chunks"]],
            misreads=[Misread(statement=m["statement"], verdict=m.get("verdict","X"),
                trap_type=m.get("trap_type",""), anchor=m.get("anchor",""), why=m.get("why",""),
                killer=bool(m.get("killer",False)), english=_engflag(m),
                integrative=bool(m.get("integrative",False))) for m in s["misreads"]],
            mistips=s.get("mistips",[])))
    sents=[LectureSentence(id=s["id"], text=s["english"]) for s in d["sentences"]]
    return LecturePassage(title=d.get("theme",d["item_no"]), source="EBS 고1 2025년 9월 모의고사",
        item_no=d["item_no"], sentences=sents, overview=overview, analysis=SentenceAnalysis(sentences=items))

files=sorted(glob.glob(SC+"/moui1/passages/*.json"), key=lambda f:os.path.basename(f))
order=["20","21","22","23","24","26","29","30","31","32","33","34","35","36","37","38","39","40","41-42","43-45"]
loaded={}
for f in files:
    d=json.load(open(f))
    try: loaded[d["item_no"]]=mk_passage(d)
    except Exception as e: print("BUILD FAIL", os.path.basename(f), "->", repr(e)[:200])
P=[loaded[k] for k in order if k in loaded]

# 정규화 1) O(참) 진술은 trap_type/anchor/why 비우기
for p in P:
    for s in p.analysis.sentences:
        for m in s.misreads:
            if m.verdict=="O":
                m.trap_type=""; m.anchor=""; m.why=""
# 정규화 2) 객관식 정답 위치 분산(결정론적 회전) — answer 를 목표 슬롯으로 이동
_cnt=0
for p in P:
    for d in p.overview.key_grammar.drills:
        if d.kind=="객관식" and d.answer in d.options and len(d.options)>=2:
            opts=list(d.options); opts.remove(d.answer)
            tgt=_cnt % (len(d.options)); _cnt+=1
            opts.insert(tgt, d.answer); d.options=opts

print(f"지문 조립: {len(P)}/{len(order)}  ({[p.item_no for p in P]})")
if len(P)==0: sys.exit()
ok=print_report(verify_passages(P, cross_check=(len(P)>1)))
if os.environ.get("RENDER") and ok:
    FOOT="© 2026. ortica영어. All rights reserved."
    stem=SC+"/고1_2025_9월_모의고사_필생보"
    render_lecture_pdf(P, stem+"_학생용.pdf", teacher=False, footer_note=FOOT)
    render_lecture_pdf(P, stem+"_강사용.pdf", teacher=True, footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        dd=fitz.open(f"{stem}_{suf}.pdf"); print(f"  {suf}: {dd.page_count}p"); dd.close()
    print("RENDER OK")
