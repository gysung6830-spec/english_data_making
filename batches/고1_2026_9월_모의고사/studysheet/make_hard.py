# -*- coding: utf-8 -*-
"""고1 2026 9월 — 지문별 '가장 까다로운 문장' 직독직해 + 해석 포인트 + 지문 이해하기 PDF.

한 지문당 한 카드:
  ① 직독직해 : 한글만 / 슬래시로 나열(영어 없음)
  ② 해석     : 자연스러운 번역
  ③ 해석 포인트 : 영어 원문에 형광펜(오역=빨강 · 동사 병렬=초록 같은 색 · 전치사+관계사=파랑)
                 + 오역 주의 / 동사 병렬구조 / 전치사+관계대명사(쉬운 바꿔읽기) 설명
  ④ 지문 이해하기 : 학생에게 설명하는 구어체, 핵심어 형광펜([[..]])·영어 병기

자동: 직독직해(passage chunks 의 ko).  데이터: hard2/<item>.json, explain/<item>.json."""
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

def literal_en(s):
    """직독직해 영어: 문장 그대로, 청크 경계마다 / (줄 단위 표가 아니라 흐르는 문장)."""
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

def literal_ko(s):
    """직독직해 한글: 청크 한글을 / 로 이어 붙인 흐르는 문장."""
    parts=[]
    for c in s.get("chunks",[]):
        ko=strip_mk(c.get("ko","")).strip()
        if ko: parts.append(esc(ko))
    return ' <span class="sl">/</span> '.join(parts)

def _find_unique(raw, term):
    """term 의 (start,end) — 단어경계 존중, 첫 매치."""
    t=(term or "").strip()
    if not t: return None
    l=r"(?<![A-Za-z])" if t[:1].isalpha() else ""
    r=r"(?![A-Za-z])" if t[-1:].isalpha() else ""
    m=re.search(l+re.escape(t)+r, raw, re.I)
    return (m.start(), m.end()) if m else None

def hl_english(raw, spans):
    """raw(영어)에 (span,cls) 형광펜. 겹치면 먼저 온 것 우선."""
    ivs=[]
    for term,cls in spans:
        pos=_find_unique(raw, term)
        if not pos: continue
        s,e=pos
        if any(not(e<=a or s>=b) for a,b,_ in ivs): continue  # overlap → skip
        ivs.append((s,e,cls))
    ivs.sort()
    out=[]; i=0
    for s,e,cls in ivs:
        out.append(esc(raw[i:s])); out.append(f'<mark class="hl {cls}">{esc(raw[s:e])}</mark>'); i=e
    out.append(esc(raw[i:])); return "".join(out)

def hl_talk(text):
    """지문 이해하기: [[..]] → 형광펜."""
    out=[]; i=0
    for m in _MK.finditer(text or ""):
        out.append(esc(text[i:m.start()])); out.append(f'<mark class="hl kw">{esc(m.group(1))}</mark>'); i=m.end()
    out.append(esc((text or "")[i:])); return "".join(out)

def talk_paras(item):
    p=SC+"/explain/"+item+".json"
    if os.path.exists(p):
        t=json.load(open(p)).get("talk") or []
        return "".join(f"<p>{hl_talk(x)}</p>" for x in t if str(x).strip())
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
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--indigo:#4b4a8f;--amber:#a9781f;--rose:#b0434f;--line:#d7ddd6;--sub:#5c636b;--paper:#faf9f6;}
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
.lit{background:#f2f6f2;border-radius:7px;padding:7px 11px;}
.lit-en{font-size:9.8pt;line-height:1.8;color:#2b3036;padding-bottom:5px;margin-bottom:5px;border-bottom:1px dashed #d5e0d7;}
.lit-ko{font-size:9.8pt;line-height:1.8;color:var(--green-d);font-weight:700;}
.sl{color:#8fb49c;font-weight:800;padding:0 2px;}
.trans{font-size:9.8pt;line-height:1.6;color:var(--green-d);font-weight:700;background:var(--green-bg);border-radius:6px;padding:6px 10px;}
.pts{border:1px solid #e6e3d6;background:#fbfaf5;border-radius:6px;padding:7px 11px;}
.eng{font-size:9.7pt;line-height:1.85;color:#2b3036;padding-bottom:6px;margin-bottom:4px;border-bottom:1px dashed #e4e2d5;}
.pt{font-size:9.2pt;line-height:1.5;color:#3a4250;padding:5px 0 0;}
.pt+.pt{padding-top:6px;}
.pt .k{display:inline-block;font-size:7.8pt;font-weight:800;color:#fff;border-radius:4px;padding:0 6px;margin-right:6px;vertical-align:1px;}
.k.kr{background:var(--rose);} .k.kg{background:var(--green);} .k.kb{background:var(--indigo);}
mark.hl{border-radius:3px;padding:0 2px;font-weight:800;}
mark.hl.rose{background:#f7d7da;color:#8f2f3a;}
mark.hl.grn{background:#c9e7d3;color:#1f4d33;}
mark.hl.blu{background:#d7d6f0;color:#37356e;}
mark.hl.kw{background:#fdeeb6;color:#6b5312;}
.trans mark.hl,.lit mark.hl{background:transparent;padding:0;}
.talk{font-size:9.5pt;line-height:1.68;color:#2c3138;background:#f3f6f3;border-left:3px solid var(--green);border-radius:0 7px 7px 0;padding:8px 12px;}
.talk p{margin:0 0 6px;}
.talk p:last-child{margin-bottom:0;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def card(h, h2):
    item=h["item_no"]; ov=P[item]["overview"]; s=sent_of(item, h["sentence_id"]); raw=s["english"]
    h2=h2 or {}
    parts=[f'<div class="card"><div class="c-h"><span class="c-no">{esc(item)}</span>'
           f'<span class="c-ti">{esc(ov["theme_ko"])}</span><span class="c-sn">최고난도 · {esc(str(h["sentence_id"]))}번 문장</span></div>']
    # ① 직독직해 (영어 문장 / + 한글 문장 /, 줄 단위 표 아님)
    parts.append('<div class="lab g">직독직해</div>')
    parts.append(f'<div class="lit"><div class="lit-en">{literal_en(s)}</div>'
                 f'<div class="lit-ko">{literal_ko(s)}</div></div>')
    # ② 해석
    parts.append('<div class="lab g">해석</div>')
    parts.append(f'<div class="trans">{esc(h.get("translation",""))}</div>')
    # ③ 해석 포인트
    mt=h2.get("mistrans") or {}
    par=h2.get("parallel"); par_spans=h2.get("parallel_spans") or []
    pr=h2.get("prep_rel"); pr_spans=h2.get("prep_rel_spans") or []
    hlspans=[]
    if mt.get("span"): hlspans.append((mt["span"],"rose"))
    for sp in par_spans: hlspans.append((sp,"grn"))
    for sp in pr_spans: hlspans.append((sp,"blu"))
    pts=[]
    if mt.get("span") or mt.get("note"):
        pts.append(f'<div class="pt"><span class="k kr">오역 주의</span>이 부분 오역 가능성 있음. {esc(mt.get("note",""))}</div>')
    if par:
        pts.append(f'<div class="pt"><span class="k kg">동사 병렬구조</span>{esc(par)} '
                   f'<span style="color:#2c6444;font-weight:800;">(초록 형광펜끼리 병렬)</span></div>')
    if pr:
        pts.append(f'<div class="pt"><span class="k kb">전치사+관계대명사</span>{esc(pr)}</div>')
    if pts:
        parts.append('<div class="lab a">해석 포인트</div>')
        eng=f'<div class="eng">{hl_english(raw, hlspans)}</div>' if hlspans else ''
        parts.append('<div class="pts">'+eng+"".join(pts)+'</div>')
    # ④ 지문 이해하기
    parts.append('<div class="lab">지문 이해하기</div>')
    parts.append(f'<div class="talk">{talk_paras(item)}</div>')
    parts.append('</div>')
    return "".join(parts)

items=[json.load(open(PDIR+"/"+fn))["item_no"].strip() for fn in order]
def load2(it):
    p=SC+"/hard2/"+it+".json"
    return json.load(open(p)) if os.path.exists(p) else None
H=[(json.load(open(SC+"/hard/"+it+".json")), load2(it)) for it in items if os.path.exists(SC+"/hard/"+it+".json")]
body=[f'<div class="doc-h">{TITLE}</div>'
      f'<div class="doc-d">지문마다 가장 해석이 까다로운 문장 1개 · 직독직해(영어·한글 /) → 해석 → 해석 포인트(영어 형광펜) → 지문 이해하기</div>']
for h,h2 in H: body.append(card(h,h2))
doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
out=SC+"/고1_2026_9월_최고난도문장_해석법.pdf"
HTML(string=doc).write_pdf(out)
d=fitz.open(out); print("최고난도 문장 해석법:", d.page_count, "p /", len(H), "지문"); d.close()
