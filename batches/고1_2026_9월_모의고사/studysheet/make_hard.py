# -*- coding: utf-8 -*-
"""고1 2026 9월 — 지문별 '가장 까다로운 문장 + 해석법' PDF."""
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
def sent_of(item, sid):
    for s in P[item]["sentences"]:
        if s["id"]==sid: return s
    return None
def chunked_en(s):
    raw=s["english"]; ends=[]; pos=0
    for c in s.get("chunks",[]):
        t=_MK.sub(r"\1", c.get("en","") or "").strip()
        if not t: continue
        m=re.search(re.escape(t), raw[pos:])
        if not m: continue
        pos=pos+m.end(); ends.append(pos)
    ends=ends[:-1]; out=[]; i=0
    for off in ends:
        out.append(esc(raw[i:off])); out.append(' <span class="sl">/</span> '); i=off
    out.append(esc(raw[i:])); return "".join(out)

CSS=("""
__FONTS__
@page{ size:A4; margin:14mm 13mm; @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; } }
*{box-sizing:border-box;}
body{font-family:'NanumSquareRound',"Malgun Gothic",sans-serif; color:#22262b; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--green-soft:#eef5f0;--indigo:#575495;--indigo-bg:#ecebf4;--amber:#a9781f;--line:#d7ddd6;--sub:#5c636b;}
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
.lab.g{background:var(--green);} .lab.a{background:var(--amber);}
.skel{font-size:9.4pt;color:#2b2f6b;font-style:italic;background:#f4f4fb;border-radius:6px;padding:5px 9px;}
.why{font-size:9.4pt;color:#3a4250;line-height:1.55;}
.steps{margin:2px 0 0;padding:0;list-style:none;}
.steps li{font-size:9.3pt;line-height:1.6;color:#2c3138;padding:2px 0 2px 2px;}
.trans{font-size:9.8pt;line-height:1.6;color:var(--green-d);font-weight:700;background:var(--green-bg);border-radius:6px;padding:6px 10px;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def card(h):
    item=h["item_no"]; ov=P[item]["overview"]; s=sent_of(item, h["sentence_id"])
    steps="".join(f"<li>{esc(x)}</li>" for x in h.get("steps",[]))
    parts=[f'<div class="card"><div class="c-h"><span class="c-no">{esc(item)}</span>'
           f'<span class="c-ti">{esc(ov["theme_ko"])}</span><span class="c-sn">{esc(str(h["sentence_id"]))}번 문장</span></div>']
    parts.append(f'<div class="en">{chunked_en(s)}</div>')
    if h.get("difficulty"):
        parts.append(f'<div class="lab a">까다로운 이유</div><div class="why">{esc(h["difficulty"])}</div>')
    if h.get("skeleton"):
        parts.append(f'<div class="lab g">핵심 골격</div><div class="skel">{esc(h["skeleton"])}</div>')
    parts.append(f'<div class="lab">해석 순서</div><ul class="steps">{steps}</ul>')
    parts.append(f'<div class="lab g">해석</div><div class="trans">{esc(h.get("translation",""))}</div>')
    parts.append('</div>')
    return "".join(parts)

items=[json.load(open(PDIR+"/"+fn))["item_no"].strip() for fn in order]
H=[json.load(open(SC+"/hard/"+it+".json")) for it in items if os.path.exists(SC+"/hard/"+it+".json")]
body=[f'<div class="doc-h">{TITLE}</div><div class="doc-d">지문마다 가장 해석이 까다로운 문장 1개 · 끊어읽기 → 골격 → 난구문 처리 → 해석</div>']
for h in H: body.append(card(h))
doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
out=SC+"/고1_2026_9월_최고난도문장_해석법.pdf"
HTML(string=doc).write_pdf(out)
d=fitz.open(out); print("최고난도 문장 해석법:", d.page_count, "p /", len(H), "지문"); d.close()
