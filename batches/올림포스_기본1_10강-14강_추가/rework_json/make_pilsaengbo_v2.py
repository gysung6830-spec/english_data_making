# -*- coding: utf-8 -*-
"""올림포스 10-14강 필생보 v2 — 5섹션 구조.
① 원문  ② 어휘리스트  (page)  ③ 해석연습(빈칸)+어법 형광펜  (page)  ④ 어법칩 목록  (page)  ⑤ O/X/△ 학습지.
학생용/강사용 각각 출력."""
import json, os, html, re
from weasyprint import HTML
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/olrw"
_HERE=os.path.dirname(os.path.abspath(__file__))
FONTDIR=(_HERE+"/fonts") if os.path.exists(_HERE+"/fonts/NanumSquareRoundR.ttf") \
    else "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/fonts"
FOOT="© 2026. ortica영어. All rights reserved."
TITLE="올림포스 독해 기본1 (10강-14강) · 필생보"
FONTFACE=f"""
@font-face{{ font-family:'NanumSquareRound'; font-weight:400; src:url('file://{FONTDIR}/NanumSquareRoundR.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:700; src:url('file://{FONTDIR}/NanumSquareRoundB.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:800; src:url('file://{FONTDIR}/NanumSquareRoundEB.ttf'); }}
"""
order=json.load(open(SC+"/order.json"))
P=[json.load(open(SC+"/passages/"+fn)) for fn in order]
def esc(s): return html.escape(str(s or ""))
_MK=re.compile(r"\[\[(.+?)\]\]")

# ---- 어법칩 형광펜(영어 원문) ----
def _bpat(e):
    l=r"(?<![A-Za-z])" if e[:1].isalpha() else ""
    r=r"(?![A-Za-z])" if e[-1:].isalpha() else ""
    return l+re.escape(e)+r
def hl_en(s):
    text=esc(s.get("english","")); spans=[]
    for g in s.get("grammar",[]):
        for sp in (g.get("spans") or []):
            e=esc(str(sp)).strip()
            if e: spans.append(e)
    toks={}
    for i,e in enumerate(sorted(set(spans), key=lambda x:-len(x))):
        m=re.search(_bpat(e), text, re.IGNORECASE)
        if not m: continue
        t=f"\x00h{i}\x00"; toks[t]=f'<mark class="hl">{text[m.start():m.end()]}</mark>'
        text=text[:m.start()]+t+text[m.end():]
    for t,htm in toks.items(): text=text.replace(t,htm)
    return text

# ---- ③ 직독직해 빈칸(핵심 부분만) ----
def _blank(m):
    inner=re.sub(r'&[a-zA-Z#0-9]+;','x',m.group(1))
    w=min(240,max(34,round(len(inner)*11)+14))
    return f'<span class="fill" style="min-width:{w}px"></span>'
def ko_line(s, teacher):
    parts=[]
    for c in s.get("chunks",[]):
        ko=c.get("ko","") or ""
        seg=_MK.sub(r'<b class="key">\1</b>', esc(ko)) if teacher else _MK.sub(_blank, esc(ko))
        parts.append(seg)
    return ' <span class="sl">/</span> '.join(parts)

def vcls(v): return "o" if v=="O" else ("t" if v=="△" else "x")

CSS=("""
__FONTS__
@page{ size:A4; margin:13mm 12mm 13mm 12mm;
  @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; } }
*{box-sizing:border-box;}
body{font-family:'NanumSquareRound',"Malgun Gothic",sans-serif; color:#22262b; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--green-soft:#eef5f0;
  --indigo:#575495;--indigo-bg:#ecebf4;--amber:#a9781f;--red:#a83c2c;--line:#d7ddd6;--sub:#5c636b;}
.psg{break-before:page;} .psg:first-of-type{break-before:auto;}
.p-h{display:flex; align-items:baseline; gap:8px; border-bottom:2.5px solid var(--green); padding-bottom:4px; margin-bottom:6px;}
.p-no{background:var(--green); color:#fff; font-weight:800; font-size:8.6pt; padding:1px 9px; border-radius:20px; white-space:nowrap;}
.p-ti{font-size:11pt; font-weight:800; color:var(--green-d); line-height:1.35;}
.p-src{margin-left:auto; font-size:7.8pt; color:var(--sub); white-space:nowrap;}
.sec{break-inside:auto;}
.sec.brk{break-before:page;}
.sec-h{display:flex; align-items:center; gap:7px; margin:2px 0 6px;}
.sec-n{background:var(--green-d); color:#fff; font-weight:800; font-size:8.6pt; width:20px; height:20px; line-height:20px; text-align:center; border-radius:50%;}
.sec-t{font-size:11pt; font-weight:800; color:var(--green-d);} .sec-d{font-size:8pt; color:var(--sub);}
.panel{border:1px solid var(--line); border-radius:9px; padding:8px 11px;}
/* ① 원문 */
.orig{font-size:10.3pt; line-height:1.85; color:#1c2024;}
.orig .sn{font-size:6.8pt; font-weight:800; color:var(--green); vertical-align:0.5em; margin:0 2px 0 1px;}
/* ② 어휘 */
.voc{columns:2; column-gap:22px; font-size:9.3pt; line-height:1.7;}
.voc .w{font-weight:800; color:var(--green-d);} .voc .m{color:#3a4250;}
.voc .row{break-inside:avoid;}
/* ③ 해석연습 */
.s{padding:5px 0 6px; border-bottom:1px dotted #e6ebe8; break-inside:avoid;}
.s:last-child{border-bottom:none;}
.en{font-size:9.7pt; line-height:1.55;}
.en .n{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center; background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.ko{margin:4px 0 0 21px; font-size:9.2pt; color:#3a4250; line-height:1.7;}
.ko::before{content:"↳ "; color:var(--green); font-weight:800;}
.sl{color:#b9c2ba; font-weight:700; padding:0 2px;}
.fill{display:inline-block; min-width:34px; border-bottom:1.4px solid var(--green); vertical-align:-1px;}
.key{color:var(--indigo); font-weight:800; border-bottom:1.4px solid var(--indigo);}
mark.hl{background:#d8d5f0; padding:0 1px; border-radius:2px; color:inherit;}
/* ④ 어법칩 */
.gl{padding:4px 0; border-bottom:1px dotted #e6ebe8; break-inside:avoid; font-size:9.2pt; line-height:1.55;}
.gl:last-child{border-bottom:none;}
.gl .n{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center; background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.chip{display:inline-block; background:var(--indigo-bg); color:var(--indigo); font-weight:800; font-size:8pt; padding:0 7px; border-radius:999px; margin:0 3px 2px 0;}
.gnote{color:#3a4250; font-size:8.6pt;}
/* ⑤ ox */
.k-o{color:var(--green-d);} .k-x{color:var(--red);} .k-t{color:var(--amber);}
.sen{margin:7px 0 2px; padding:3px 0 3px 8px; border-left:3px solid var(--green-bg); font-size:9.5pt; line-height:1.5;}
.sen .sn2{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center; background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.grp{margin-left:8px;}
.ox{padding:4px 0; border-bottom:1px dotted #eef1ee; break-inside:avoid;}
.ox:last-child{border-bottom:none;}
.stx{font-size:9.3pt; line-height:1.5;} .stx::before{content:"·"; color:var(--sub); font-weight:800; margin-right:6px;} .stx .en2{color:#2b2f6b; font-style:italic;}
.pick{margin:3px 0 0 12px; font-size:8.8pt; color:var(--sub);}
.pick .lab{font-weight:700; color:var(--green-d); margin-right:6px;}
.pick b{display:inline-block; width:19px; height:19px; line-height:19px; text-align:center; border:1.4px solid #c7cec8; border-radius:50%; margin-right:4px; font-weight:800;}
.pick .fixline{display:inline-block; border-bottom:1px solid #c7cec8; min-width:230px; margin-left:8px; vertical-align:-2px;}
.vd{display:inline-block; width:19px; height:19px; line-height:19px; text-align:center; border-radius:50%; font-weight:800; color:#fff; margin-left:6px;}
.vd.o{background:var(--green);} .vd.x{background:var(--red);} .vd.t{background:var(--amber);}
.kill{color:var(--red); font-weight:800; font-size:7.6pt; margin-left:5px;}
.why{margin:3px 0 0 12px; font-size:8.6pt; color:#3a4250; line-height:1.5;}
.why .cue{background:var(--green-soft); border-radius:3px; padding:0 3px; color:var(--green-d);} .why .typ{color:var(--indigo); font-weight:700; font-size:7.8pt;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def sec_head(n,t,d=""):
    return f'<div class="sec-h"><span class="sec-n">{n}</span><span class="sec-t">{t}</span><span class="sec-d">{d}</span></div>'

def passage_html(p, teacher):
    ov=p["overview"]; no=esc(p["item_no"].strip()); ti=esc(ov["theme_ko"]); sents=p["sentences"]
    h=[f'<div class="psg"><div class="p-h"><span class="p-no">{no}</span><span class="p-ti">{ti}</span><span class="p-src">올림포스 독해 기본1</span></div>']
    # ① 원문 + ② 어휘 (같은 페이지)
    h.append('<div class="sec">'+sec_head(1,"원문"))
    body=" ".join(f'<span class="sn">{s["id"]}</span>{esc(s["english"])}' for s in sents)
    h.append(f'<div class="panel orig">{body}</div></div>')
    # ② 어휘
    h.append('<div class="sec" style="margin-top:8px;">'+sec_head(2,"어휘 리스트"))
    seen=set(); rows=[]
    for s in sents:
        for v in s.get("vocab",[]):
            w=v.get("word","").strip()
            if not w or w.lower() in seen: continue
            seen.add(w.lower()); rows.append(f'<div class="row"><span class="w">{esc(w)}</span> <span class="m">{esc(v.get("meaning",""))}</span></div>')
    h.append(f'<div class="panel voc">{"".join(rows)}</div></div>')
    # ③ 해석연습 (page break)
    h.append('<div class="sec brk">'+sec_head(3,"해석 연습","직독직해에서 핵심(오역 위험) 부분만 채우기 · 영어에 어법칩 형광펜"))
    h.append('<div class="panel">')
    for s in sents:
        h.append(f'<div class="s"><div class="en"><span class="n">{s["id"]}</span>{hl_en(s)}</div><div class="ko">{ko_line(s, teacher)}</div></div>')
    h.append('</div></div>')
    # ④ 어법칩 (page break)
    h.append('<div class="sec brk">'+sec_head(4,"어법칩","문장별 핵심 어법"))
    h.append('<div class="panel">')
    for s in sents:
        chips=s.get("grammar",[])
        if not chips: continue
        inner=[f'<span class="n">{s["id"]}</span>']
        for g in chips:
            inner.append(f'<span class="chip">{esc(g.get("tag",""))}</span>')
            if teacher and g.get("note"): inner.append(f'<span class="gnote">{esc(g["note"])}</span> ')
        h.append(f'<div class="gl">{"".join(inner)}</div>')
    h.append('</div></div>')
    # ⑤ ox (page break)
    h.append('<div class="sec brk">'+sec_head(5,"O / X / △ 내용 판단","맞으면 O·틀리면 X·결론만 맞으면 △, X·△는 근거 고치기"))
    h.append('<div class="panel">')
    for s in sents:
        ms=s.get("misreads",[])
        if not ms: continue
        h.append(f'<div class="sen"><span class="sn2">{s["id"]}</span>{esc(s["english"])}</div><div class="grp">')
        for m in ms:
            v=m.get("verdict","X"); stmt=esc(m.get("statement",""))
            if m.get("english"): stmt=f'<span class="en2">{stmt}</span>'
            if teacher:
                kill='<span class="kill">🔥킬러</span>' if m.get("killer") else ''
                h.append(f'<div class="ox"><div class="stx">{stmt}<span class="vd {vcls(v)}">{v}</span>{kill}</div>')
                if v!="O" and (m.get("why") or m.get("anchor")):
                    an=f'<span class="cue">본문: {esc(m["anchor"])}</span> — ' if m.get("anchor") else ''
                    typ=f' <span class="typ">[{esc(m.get("trap_type",""))}]</span>' if m.get("trap_type") else ''
                    h.append(f'<div class="why">→ 바르게: {an}{esc(m.get("why",""))}{typ}</div>')
                h.append('</div>')
            else:
                h.append(f'<div class="ox"><div class="stx">{stmt}</div>'
                         '<div class="pick"><span class="lab">내 판단</span><b class="k-o">O</b><b class="k-x">X</b><b class="k-t">△</b><span class="fixline"></span></div></div>')
        h.append('</div>')
    h.append('</div></div>')
    h.append('</div>')
    return "".join(h)

def build(teacher, out):
    badge='강사용' if teacher else '학생용'
    body=[f'<div class="p-h" style="border-bottom:none;margin-bottom:0;"></div>']
    body=[]
    for p in P: body.append(passage_html(p, teacher))
    doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
    HTML(string=doc).write_pdf(out)
    d=fitz.open(out); n=d.page_count; d.close(); return n

for teacher,suf in [(False,"학생용"),(True,"강사용")]:
    out=f"{SC}/올림포스 독해 기본1_10강-14강_필생보v2_{suf}.pdf"
    print(f"{suf}: {build(teacher,out)}p")
print("PILSAENGBO v2 OK")
