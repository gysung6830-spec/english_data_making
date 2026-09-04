# -*- coding: utf-8 -*-
"""올림포스 10-14강 리워크 JSON → LecturePassage → verify → 렌더 + 단어시험."""
import sys, json, os, re as _re
sys.path.insert(0,"/home/user/english_data_making")
from src.lecture_schemas import (LecturePassage, LectureSentence, Overview,
    SentenceAnalysis, SentenceItem)
from src.lecture_render import render_lecture_pdf
from src.vocab_test import render_vocab_test
from verify import verify_passages, print_report
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/olrw"
SRC="올림포스 독해 기본1 (10강-14강)"

def _norm_kind(k):
    k=(k or "").strip()
    if "밑줄" in k: return "밑줄형"
    if "네모" in k: return "네모형"
    if "오류" in k: return "오류찾기"
    if "영작" in k: return "영작"
    if "객관" in k: return "객관식"
    return k

def mk_passage(d):
    for dr in d["overview"]["key_grammar"].get("drills",[]):
        dr["kind"]=_norm_kind(dr.get("kind"))
    overview=Overview(**d["overview"])
    items=[SentenceItem(**s) for s in d["sentences"]]
    sents=[LectureSentence(id=s["id"], text=s["english"]) for s in d["sentences"]]
    return LecturePassage(title=d.get("theme",d["item_no"]), source=SRC,
        item_no=d["item_no"], sentences=sents, overview=overview, analysis=SentenceAnalysis(sentences=items))

order=json.load(open(SC+"/order.json"))
P=[]
for fn in order:
    d=json.load(open(SC+"/passages/"+fn))
    try: P.append(mk_passage(d))
    except Exception as e: print("BUILD FAIL", fn, "->", repr(e)[:300])

# 정규화 1) O(참) 진술 trap 비우기
for p in P:
    for s in p.analysis.sentences:
        for m in s.misreads:
            if m.verdict=="O": m.trap_type=""; m.anchor=""; m.why=""
# 정규화 2) 오류찾기 answer 번호 접두사 맞춤
def _snum(s): return _re.sub(r'^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*', '', s or '').strip()
for p in P:
    for dr in p.overview.key_grammar.drills:
        if dr.kind=="오류찾기" and dr.answer not in dr.options:
            for o in dr.options:
                if _snum(o)==_snum(dr.answer): dr.answer=o; break
# 정규화 3) 빈칸 짝 맞춤 — ko에 [[ ]] 있는데 en에 없으면 en 첫 단어를 [[ ]]로
_wpat=_re.compile(r"[A-Za-z][A-Za-z'’\-]*")
for p in P:
    for s in p.analysis.sentences:
        for c in s.chunks:
            if "[[" in (c.ko or "") and "[[" not in (c.en or ""):
                mm=_wpat.search(c.en or "")
                if mm: c.en=c.en[:mm.start()]+"[["+mm.group(0)+"]]"+c.en[mm.end():]

print(f"지문 조립: {len(P)}/{len(order)}")
if len(P)==0: sys.exit()
ok=print_report(verify_passages(P, cross_check=(len(P)>1)))
if os.environ.get("RENDER") and ok:
    FOOT="© 2026. ortica영어. All rights reserved."
    stem=SC+"/올림포스 독해 기본1_10강-14강"
    render_lecture_pdf(P, stem+"_학생용.pdf", teacher=False, footer_note=FOOT)
    render_lecture_pdf(P, stem+"_강사용.pdf", teacher=True, footer_note=FOOT)
    render_vocab_test(P, SC+"/올림포스_10-14강_단어시험", source_title=SRC, footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        dd=fitz.open(f"{stem}_{suf}.pdf"); print(f"  {suf}: {dd.page_count}p"); dd.close()
    for suf in ["학생용","정답"]:
        dd=fitz.open(f"{SC}/올림포스_10-14강_단어시험_{suf}.pdf"); print(f"  단어시험 {suf}: {dd.page_count}p"); dd.close()
    print("RENDER OK")
