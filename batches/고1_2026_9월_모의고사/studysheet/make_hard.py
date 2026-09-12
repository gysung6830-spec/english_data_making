# -*- coding: utf-8 -*-
"""고1 2026 9월 — 지문별 '가장 까다로운 문장' 직독직해 + 해석 포인트 + 지문 요약 PDF.

한 지문당 한 카드:
  ① 끊어읽기(영어 /)   ② 직독직해(영어→한글, 청크별)
  ③ 핵심 골격          ④ 오역 주의(이 부분 오역 가능성 있음)
  ⑤ 동사 병렬구조(있을 때)  ⑥ 전치사+관계대명사(있을 때)
  ⑦ 해석               ⑧ 지문 한눈에(지문 단어로, 지문 순서대로)

직독직해(②)·지문 한눈에(⑧)는 passage 의 chunks·flow_blocks 에서 자동 생성.
오역 주의·병렬·전치사+관계대명사(④~⑥)는 hard2/<item>.json 에서 읽음."""
import json, os, html, re
from weasyprint import HTML
import fitz
SC=os.path.dirname(os.path.abspath(__file__))
FONTDIR=SC+"/fonts"
FOOT="© 2026. 오르티카잉. All rights reserved."
TITLE="고1 2026년 9월 모의고사 · 지문별 최고난도 문장 해석법"
FONTFACE=f"""
@font-face{{ font-family:'NanumSquareRound'; font-weight:400; src:url('file://{FONTDIR}/NanumSquareRoundR.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:700; src:url('file://{FONTDIR}/NanumSquareRoundB.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:800; src:url('file://{FONTDIR}/NanumSquareRoundEB.ttf'); }}
"""
order=json.load(open(SC+"/order.json"))
PDIR=(SC+"/passages") if os.path.isdir(SC+"/passages") else os.path.normpath(SC+"/../passages")
P={json.load(open(PDIR+"/"+fn))["item_no"].strip(): json.load(open(PDIR+"/"+fn)) for fn in order}
def esc(s): return html.escape(str(s or ""))
_MK=re.compile(r"\[\[(.+?)\]\]")
def strip_mk(s): return _MK.sub(r"\1", s or "")
def sent_of(item, sid):
    for s in P[item]["sentences"]:
        if s["id"]==sid: return s
    return None

def chunked_en(s):
    """끊어읽기: 청크 경계마다 / 표시."""
    raw=s["english"]; ends=[]; pos=0
    for c in s.get("chunks",[]):
        t=strip_mk(c.get("en","")).strip()
        if not t: continue
        m=re.search(re.escape(t), raw[pos:])
        if not m: continue
        pos=pos+m.end(); ends.append(pos)
    ends=ends[:-1]; out=[]; i=0
    for off in ends:
        out.append(esc(raw[i:off])); out.append(' <span class="sl">/</span> '); i=off
    out.append(esc(raw[i:])); return "".join(out)

def literal_rows(s):
    """직독직해: 청크별 영어→한글 (passage chunks 에서 자동)."""
    rows=[]
    for c in s.get("chunks",[]):
        en=strip_mk(c.get("en","")).strip()
        ko=strip_mk(c.get("ko","")).strip()
        if not en: continue
        rows.append(f'<tr><td class="le">{esc(en)}</td><td class="lk">{esc(ko)}</td></tr>')
    return "".join(rows)

def explain_rows(item):
    """지문 한눈에: flow_blocks(stage→summary) 를 지문 순서대로, 지문 단어로."""
    out=[]
    for b in P[item]["overview"].get("flow_blocks",[]):
        stg=esc(b.get("stage","")); sm=esc(strip_mk(b.get("summary","")).strip())
        if not sm: continue
        out.append(f'<li><span class="stg">{stg}</span> {sm}</li>')
    return "".join(out)

CSS=("""
__FONTS__
@page{ size:A4; margin:14mm 13mm; @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; } }
*{box-sizing:border-box;}
body{font-family:'NanumSquareRound',"Malgun Gothic",sans-serif; color:#22262b; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--green-soft:#eef5f0;--indigo:#575495;--indigo-bg:#ecebf4;--amber:#a9781f;--amber-bg:#fbf2de;--rose:#b0434f;--rose-bg:#fbe9ea;--line:#d7ddd6;--sub:#5c636b;}
.doc-h{font-size:14pt;font-weight:800;color:var(--green-d);border-bottom:2.5px solid var(--green);padding-bottom:5px;margin-bottom:4px;}
.doc-d{font-size:8.6pt;color:var(--sub);margin-bottom:12px;}
.card{border:1px solid var(--line);border-radius:10px;padding:11px 13px 12px;margin-bottom:12px;break-inside:avoid;}
.c-h{display:flex;align-items:baseline;gap:8px;margin-bottom:7px;}
.c-no{background:var(--green);color:#fff;font-weight:800;font-size:8.6pt;padding:1px 9px;border-radius:20px;white-space:nowrap;}
.c-ti{font-size:10.5pt;font-weight:800;color:var(--green-d);}
.c-sn{margin-left:auto;font-size:8pt;color:var(--sub);}
.en{font-size:10pt;line-height:1.7;background:var(--green-soft);border-radius:7px;padding:7px 10px;}
.sl{color:#9fb6a6;font-weight:800;padding:0 1px;}
.lab{display:inline-block;font-size:8pt;font-weight:800;color:#fff;background:var(--indigo);border-radius:5px;padding:1px 7px;margin:9px 0 3px;}
.lab.g{background:var(--green);} .lab.a{background:var(--amber);} .lab.r{background:var(--rose);}
.lit{width:100%;border-collapse:collapse;margin-top:2px;}
.lit td{vertical-align:top;padding:3px 7px;border-bottom:1px solid #eef0ed;font-size:9.2pt;line-height:1.5;}
.lit .le{width:54%;color:#2b3036;}
.lit .lk{width:46%;color:var(--green-d);font-weight:700;}
.skel{font-size:9.3pt;color:#2b2f6b;font-style:italic;background:#f4f4fb;border-radius:6px;padding:5px 9px;}
.warn{font-size:9.3pt;line-height:1.55;color:#3a4250;background:var(--rose-bg);border-radius:6px;padding:6px 10px;}
.warn .sp{font-weight:800;color:var(--rose);}
.tip{font-size:9.3pt;line-height:1.55;color:#3a4250;background:var(--amber-bg);border-radius:6px;padding:6px 10px;}
.tip .sp{font-weight:800;color:var(--amber);}
.trans{font-size:9.8pt;line-height:1.6;color:var(--green-d);font-weight:700;background:var(--green-bg);border-radius:6px;padding:6px 10px;}
.flow{margin:2px 0 0;padding:0;list-style:none;}
.flow li{font-size:9.2pt;line-height:1.55;color:#2c3138;padding:3px 0 3px 0;border-bottom:1px dashed #e4e8e3;}
.flow li:last-child{border-bottom:none;}
.flow .stg{display:inline-block;font-weight:800;color:var(--indigo);font-size:8.4pt;background:var(--indigo-bg);border-radius:4px;padding:0 6px;margin-right:5px;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def card(h, h2):
    item=h["item_no"]; ov=P[item]["overview"]; s=sent_of(item, h["sentence_id"])
    parts=[f'<div class="card"><div class="c-h"><span class="c-no">{esc(item)}</span>'
           f'<span class="c-ti">{esc(ov["theme_ko"])}</span><span class="c-sn">{esc(str(h["sentence_id"]))}번 문장</span></div>']
    # ① 끊어읽기
    parts.append('<div class="lab g">끊어읽기</div>')
    parts.append(f'<div class="en">{chunked_en(s)}</div>')
    # ② 직독직해
    parts.append('<div class="lab g">직독직해</div>')
    parts.append(f'<table class="lit">{literal_rows(s)}</table>')
    # ③ 핵심 골격
    if h.get("skeleton"):
        parts.append('<div class="lab">핵심 골격</div>')
        parts.append(f'<div class="skel">{esc(h["skeleton"])}</div>')
    # ④ 오역 주의
    mt=(h2 or {}).get("mistrans") or {}
    if mt.get("span") or mt.get("note"):
        sp=esc(mt.get("span","")); note=esc(mt.get("note",""))
        parts.append('<div class="lab r">오역 주의</div>')
        parts.append(f'<div class="warn"><span class="sp">“{sp}”</span> — 이 부분 오역 가능성 있음. {note}</div>')
    # ⑤ 동사 병렬구조
    par=(h2 or {}).get("parallel")
    if par:
        parts.append('<div class="lab a">동사 병렬구조</div>')
        parts.append(f'<div class="tip">{esc(par)}</div>')
    # ⑥ 전치사+관계대명사
    pr=(h2 or {}).get("prep_rel")
    if pr:
        parts.append('<div class="lab a">전치사+관계대명사</div>')
        parts.append(f'<div class="tip">{esc(pr)}</div>')
    # ⑦ 해석
    parts.append('<div class="lab g">해석</div>')
    parts.append(f'<div class="trans">{esc(h.get("translation",""))}</div>')
    # ⑧ 지문 한눈에
    parts.append('<div class="lab">지문 한눈에</div>')
    parts.append(f'<ul class="flow">{explain_rows(item)}</ul>')
    parts.append('</div>')
    return "".join(parts)

items=[json.load(open(PDIR+"/"+fn))["item_no"].strip() for fn in order]
def load2(it):
    p=SC+"/hard2/"+it+".json"
    return json.load(open(p)) if os.path.exists(p) else None
H=[(json.load(open(SC+"/hard/"+it+".json")), load2(it)) for it in items if os.path.exists(SC+"/hard/"+it+".json")]
body=[f'<div class="doc-h">{TITLE}</div><div class="doc-d">지문마다 가장 해석이 까다로운 문장 1개 · 직독직해 → 오역 주의·병렬·전치사+관계대명사 → 해석 → 지문 한눈에</div>']
for h,h2 in H: body.append(card(h,h2))
doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
out=SC+"/고1_2026_9월_최고난도문장_해석법.pdf"
HTML(string=doc).write_pdf(out)
d=fitz.open(out); print("최고난도 문장 해석법:", d.page_count, "p /", len(H), "지문"); d.close()
