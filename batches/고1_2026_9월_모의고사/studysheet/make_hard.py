# -*- coding: utf-8 -*-
"""고1 2026 9월 — 지문별 '가장 까다로운 문장' 직독직해 + 해석 포인트 + 지문 이해하기 PDF.

한 지문당 한 카드(가독성 위해 4블록으로 압축, 중복 제거):
  ① 직독직해(영어→한글, 청크별 표)      ← 끊어읽기/골격을 이 표 하나로 통합
  ② 해석(자연스러운 번역)
  ③ 해석 포인트(오역 주의 · 동사 병렬구조 · 전치사+관계대명사) — 있는 것만, 한 상자에
  ④ 지문 이해하기(학생에게 설명하는 구어체) — explain/<item>.json

직독직해는 passage 의 chunks 로 자동 생성.
오역/병렬/전치사+관계대명사는 hard2/<item>.json, 지문 이해하기는 explain/<item>.json."""
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

def literal_rows(s):
    """직독직해: 청크별 영어→한글 (passage chunks 에서 자동). 홀짝 줄무늬로 가독성↑."""
    rows=[]; i=0
    for c in s.get("chunks",[]):
        en=strip_mk(c.get("en","")).strip()
        ko=strip_mk(c.get("ko","")).strip()
        if not en: continue
        zc=" z" if i%2 else ""
        rows.append(f'<tr class="lr{zc}"><td class="le">{esc(en)}</td><td class="lk">{esc(ko)}</td></tr>')
        i+=1
    return "".join(rows)

def talk_html(item):
    """지문 이해하기: explain/<item>.json 의 구어체 문단. 없으면 flow_blocks 로 대체."""
    p=SC+"/explain/"+item+".json"
    if os.path.exists(p):
        t=json.load(open(p)).get("talk") or []
        return "".join(f"<p>{esc(x)}</p>" for x in t if str(x).strip())
    out=[]
    for b in P[item]["overview"].get("flow_blocks",[]):
        sm=strip_mk(b.get("summary","")).strip()
        if sm: out.append(f"<p>{esc(sm)}</p>")
    return "".join(out)

CSS=("""
__FONTS__
@page{ size:A4; margin:14mm 13mm; @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; } }
*{box-sizing:border-box;}
body{font-family:'NanumSquareRound',"Malgun Gothic",sans-serif; color:#23272c; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--indigo:#575495;--amber:#a9781f;--rose:#b0434f;--line:#d7ddd6;--sub:#5c636b;--paper:#faf9f6;}
.doc-h{font-size:14pt;font-weight:800;color:var(--green-d);border-bottom:2.5px solid var(--green);padding-bottom:5px;margin-bottom:4px;}
.doc-d{font-size:8.6pt;color:var(--sub);margin-bottom:12px;}
.card{border:1px solid var(--line);border-radius:10px;padding:11px 13px 12px;margin-bottom:12px;break-inside:avoid;}
.c-h{display:flex;align-items:baseline;gap:8px;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #edf0ec;}
.c-no{background:var(--green);color:#fff;font-weight:800;font-size:8.6pt;padding:1px 9px;border-radius:20px;white-space:nowrap;}
.c-ti{font-size:10.5pt;font-weight:800;color:var(--green-d);}
.c-sn{margin-left:auto;font-size:8pt;color:var(--sub);}
.lab{display:inline-block;font-size:8pt;font-weight:800;color:#fff;background:var(--indigo);border-radius:5px;padding:1px 8px;margin:10px 0 4px;}
.lab.g{background:var(--green);} .lab.a{background:var(--amber);}
.lab:first-of-type{margin-top:2px;}
.lit{width:100%;border-collapse:collapse;margin-top:2px;border:1px solid #e8ebe7;border-radius:6px;overflow:hidden;}
.lit td{vertical-align:top;padding:4px 9px;font-size:9.3pt;line-height:1.5;}
.lit .lr.z{background:var(--paper);}
.lit .le{width:52%;color:#2b3036;border-right:1px solid #ecefec;}
.lit .lk{width:48%;color:var(--green-d);font-weight:700;}
.trans{font-size:9.8pt;line-height:1.6;color:var(--green-d);font-weight:700;background:var(--green-bg);border-radius:6px;padding:6px 10px;}
.pts{border:1px solid #ecdcc0;background:#fdf8ef;border-radius:6px;padding:4px 11px;}
.pt{font-size:9.2pt;line-height:1.5;color:#3a4250;padding:5px 0;border-bottom:1px dashed #eadfca;}
.pt:last-child{border-bottom:none;}
.pt .k{display:inline-block;font-size:7.8pt;font-weight:800;color:#fff;background:var(--amber);border-radius:4px;padding:0 6px;margin-right:6px;vertical-align:1px;}
.pt .k.r{background:var(--rose);}
.pt .sp{font-weight:800;color:var(--rose);}
.talk{font-size:9.5pt;line-height:1.62;color:#2c3138;background:#f3f6f3;border-left:3px solid var(--green);border-radius:0 7px 7px 0;padding:7px 12px;}
.talk p{margin:0 0 5px;}
.talk p:last-child{margin-bottom:0;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def card(h, h2):
    item=h["item_no"]; ov=P[item]["overview"]; s=sent_of(item, h["sentence_id"])
    parts=[f'<div class="card"><div class="c-h"><span class="c-no">{esc(item)}</span>'
           f'<span class="c-ti">{esc(ov["theme_ko"])}</span><span class="c-sn">최고난도 · {esc(str(h["sentence_id"]))}번 문장</span></div>']
    # ① 직독직해
    parts.append('<div class="lab g">직독직해</div>')
    parts.append(f'<table class="lit">{literal_rows(s)}</table>')
    # ② 해석
    parts.append('<div class="lab g">해석</div>')
    parts.append(f'<div class="trans">{esc(h.get("translation",""))}</div>')
    # ③ 해석 포인트 (오역 주의 · 병렬 · 전치사+관계대명사) — 있는 것만, 한 상자
    h2=h2 or {}; pts=[]
    mt=h2.get("mistrans") or {}
    if mt.get("span") or mt.get("note"):
        pts.append(f'<div class="pt"><span class="k r">오역 주의</span>'
                   f'<span class="sp">“{esc(mt.get("span",""))}”</span> {esc(mt.get("note",""))}</div>')
    if h2.get("parallel"):
        pts.append(f'<div class="pt"><span class="k">동사 병렬구조</span>{esc(h2["parallel"])}</div>')
    if h2.get("prep_rel"):
        pts.append(f'<div class="pt"><span class="k">전치사+관계대명사</span>{esc(h2["prep_rel"])}</div>')
    if pts:
        parts.append('<div class="lab a">해석 포인트</div>')
        parts.append('<div class="pts">'+"".join(pts)+'</div>')
    # ④ 지문 이해하기 (구어체)
    parts.append('<div class="lab">지문 이해하기</div>')
    parts.append(f'<div class="talk">{talk_html(item)}</div>')
    parts.append('</div>')
    return "".join(parts)

items=[json.load(open(PDIR+"/"+fn))["item_no"].strip() for fn in order]
def load2(it):
    p=SC+"/hard2/"+it+".json"
    return json.load(open(p)) if os.path.exists(p) else None
H=[(json.load(open(SC+"/hard/"+it+".json")), load2(it)) for it in items if os.path.exists(SC+"/hard/"+it+".json")]
body=[f'<div class="doc-h">{TITLE}</div>'
      f'<div class="doc-d">지문마다 가장 해석이 까다로운 문장 1개 · 직독직해 → 해석 → 해석 포인트(오역·병렬·전치사+관계대명사) → 지문 이해하기</div>']
for h,h2 in H: body.append(card(h,h2))
doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
out=SC+"/고1_2026_9월_최고난도문장_해석법.pdf"
HTML(string=doc).write_pdf(out)
d=fitz.open(out); print("최고난도 문장 해석법:", d.page_count, "p /", len(H), "지문"); d.close()
