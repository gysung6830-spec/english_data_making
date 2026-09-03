# 고1 모의고사 산문 필생보: passage JSON(에이전트 저작) → LecturePassage → verify → 렌더 + 단어시험
import sys, glob, json, os
sys.path.insert(0,"/home/user/english_data_making")
from src.lecture_schemas import (LecturePassage, LectureSentence, Overview, KeyGrammar,
    GrammarNote, GrammarDrill, RestatementChain, FlowBlock, SentenceAnalysis, SentenceItem,
    Chunk, GrammarChip, Vocab, Misread)
from src.lecture_render import render_lecture_pdf
from src.vocab_test import render_vocab_test
from verify import verify_passages, print_report
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/moui3"
SRC="고2 2026년 9월 모의고사"   # 출처 라벨

def _eng(m):
    e=m.get("english",False)
    if isinstance(e,bool): return e
    st=m.get("statement","") or ""
    asc=sum(1 for c in st if c.isascii() and c.isalpha()); kor=sum(1 for c in st if '가'<=c<='힣')
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
                    sentence=x.get("sentence",""), fix=x.get("fix",""),
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
                killer=bool(m.get("killer",False)), english=_eng(m),
                integrative=bool(m.get("integrative",False))) for m in s["misreads"]],
            mistips=s.get("mistips",[])))
    sents=[LectureSentence(id=s["id"], text=s["english"]) for s in d["sentences"]]
    return LecturePassage(title=d.get("theme",d["item_no"]), source="EBS "+SRC,
        item_no=d["item_no"], sentences=sents, overview=overview, analysis=SentenceAnalysis(sentences=items))

files=sorted(glob.glob(SC+"/passages/*.json"), key=lambda f:os.path.basename(f))
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
            if m.verdict=="O": m.trap_type=""; m.anchor=""; m.why=""
# 정규화 2) 오류찾기 answer에 번호 접두사(①② ) 맞추기 — answer가 options 문자열과 정확히 일치하도록
import re as _re
def _snum(s): return _re.sub(r'^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*', '', s or '').strip()
for p in P:
    for dr in p.overview.key_grammar.drills:
        if dr.kind=="오류찾기" and dr.answer not in dr.options:
            for o in dr.options:
                if _snum(o)==_snum(dr.answer):
                    dr.answer=o; break
# 정규화 3) 빈칸 짝 맞춤 — ko에 [[ ]] 있는데 en에 없으면 en 첫 단어를 [[ ]]로(렌더 시 en의 [[ ]]는 제거되어 무영향)
_wpat=_re.compile(r"[A-Za-z][A-Za-z'’\-]*")
for p in P:
    for s in p.analysis.sentences:
        for c in s.chunks:
            if "[[" in (c.ko or "") and "[[" not in (c.en or ""):
                mm=_wpat.search(c.en or "")
                if mm:
                    c.en=c.en[:mm.start()]+"[["+mm.group(0)+"]]"+c.en[mm.end():]

print(f"지문 조립: {len(P)}/{len(order)}  ({[p.item_no for p in P]})")
if len(P)==0: sys.exit()
ok=print_report(verify_passages(P, cross_check=(len(P)>1)))
if os.environ.get("RENDER") and ok:
    FOOT="© 2026. Ortica영어. All rights reserved."
    stem=SC+"/고2_모의고사_필생보"
    render_lecture_pdf(P, stem+"_학생용.pdf", teacher=False, footer_note=FOOT)
    render_lecture_pdf(P, stem+"_강사용.pdf", teacher=True, footer_note=FOOT)
    render_vocab_test(P, SC+"/고2_모의고사_단어시험", source_title=SRC, footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        dd=fitz.open(f"{stem}_{suf}.pdf"); print(f"  {suf}: {dd.page_count}p"); dd.close()
    for suf in ["학생용","정답"]:
        dd=fitz.open(f"{SC}/고2_모의고사_단어시험_{suf}.pdf"); print(f"  단어시험 {suf}: {dd.page_count}p"); dd.close()
    print("RENDER OK")
