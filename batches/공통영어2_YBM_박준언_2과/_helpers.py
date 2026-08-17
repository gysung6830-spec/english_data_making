# -*- coding: utf-8 -*-
"""공통영어2 천재 1과 배치 공용 헬퍼."""
import sys, random
sys.path.insert(0, "/home/user/english_data_making")
from src.lecture_schemas import (Chunk, FlowBlock, GrammarChip, GrammarDrill,
    GrammarNote, KeyGrammar, LecturePassage, LectureSentence, Misread,
    Overview, RestatementChain, SentenceAnalysis, SentenceItem, Vocab)
SRC="YBM(박준언) 공통영어2 · Lesson 2 (Dry)"
def mk(r): return [LectureSentence(id=i,text=t) for i,t in enumerate(r,1)]
def S(r,i,g,v,c,m): return SentenceItem(id=i,english=r[i-1],
    grammar=[GrammarChip(tag=a,note=b) for a,b in g],
    vocab=[Vocab(word=w,meaning=k) for w,k in v],
    chunks=[Chunk(en=e,ko=k) for e,k in c],
    misreads=[Misread(statement=s,why=w) for s,w in m])
def GN(c,t): return GrammarNote(chip=c,text=t)
def build(title,no,r,ov,items,src=SRC):
    p=LecturePassage(title=title,source=src,item_no=no,sentences=mk(r),
        overview=ov,analysis=SentenceAnalysis(sentences=items)); p.analysis.validate_all(len(r)); return p
def tok(a):
    ws=[w.strip('.,;:!?\"()“”—') for w in a.split()]; ws=[w for w in ws if w]
    random.Random(len(a)+sum(map(ord,a[:8]))).shuffle(ws); return ws
_MCQ=[0]
def finalize(p):
    for d in p.overview.key_grammar.drills:
        if d.kind=='영작': d.words=tok(d.answer)
        if d.kind=='객관식' and d.options:
            others=[o for o in d.options if o!=d.answer]
            pos=_MCQ[0]%len(d.options); d.options=others[:]; d.options.insert(pos,d.answer)
        _MCQ[0]+=1
    return p
