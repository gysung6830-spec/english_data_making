# -*- coding: utf-8 -*-
"""고1 2026 9월 'O/X/△ 내용 판단 학습지' — 문장별 misreads만 모아서. 학생용(선택+근거) / 정답."""
import json, os, html
from weasyprint import HTML
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/moui2"
_HERE=os.path.dirname(os.path.abspath(__file__))
FONTDIR=(_HERE+"/fonts") if os.path.exists(_HERE+"/fonts/NanumSquareRoundR.ttf") \
    else "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/fonts"
FOOT="© 2026. Ortica영어. All rights reserved."
TITLE="고1 2026년 9월 모의고사 · O/X/△ 내용 판단 학습지"
FONTFACE=f"""
@font-face{{ font-family:'NanumSquareRound'; font-weight:400; src:url('file://{FONTDIR}/NanumSquareRoundR.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:700; src:url('file://{FONTDIR}/NanumSquareRoundB.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:800; src:url('file://{FONTDIR}/NanumSquareRoundEB.ttf'); }}
"""
order=json.load(open(SC+"/order.json"))
P=[json.load(open(SC+"/passages/"+fn)) for fn in order]
def esc(s): return html.escape(str(s or ""))

CSS=("""
__FONTS__
@page{ size:A4; margin:13mm 12mm 13mm 12mm;
  @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; } }
*{box-sizing:border-box;}
body{font-family:'NanumSquareRound',"Malgun Gothic",sans-serif; color:#22262b; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--green-soft:#eef5f0;
  --indigo:#575495;--indigo-bg:#ecebf4;--amber:#a9781f;--red:#a83c2c;--line:#d7ddd6;--sub:#5c636b;}
.doc-h{display:flex; align-items:baseline; gap:8px; border-bottom:2.5px solid var(--green); padding-bottom:5px; margin-bottom:6px;}
.doc-h .t{font-size:13.5pt; font-weight:800; color:var(--green-d); white-space:nowrap;}
.doc-h .badge{margin-left:auto; font-size:8.4pt; font-weight:700; padding:2px 9px; border-radius:20px;}
.badge.stu{background:var(--green-bg); color:var(--green-d);} .badge.ans{background:var(--indigo-bg); color:var(--indigo);}
.hintbar{font-size:8.2pt; color:var(--sub); background:var(--green-soft); border:1px solid var(--line);
  border-radius:7px; padding:5px 9px; margin-bottom:9px; line-height:1.5;}
.hintbar b{color:var(--green-d);} .k-o{color:var(--green-d);} .k-x{color:var(--red);} .k-t{color:var(--amber);}
.card{border:1px solid var(--line); border-radius:9px; padding:7px 11px 8px; margin-bottom:8px;}
.c-h{display:flex; align-items:baseline; gap:7px; margin-bottom:2px;}
.c-no{background:var(--green); color:#fff; font-weight:800; font-size:8.4pt; padding:1px 8px; border-radius:20px; white-space:nowrap;}
.c-ti{font-size:9.6pt; font-weight:800; color:var(--green-d); line-height:1.35;}
.sen{margin:7px 0 2px; padding:3px 0 3px 8px; border-left:3px solid var(--green-bg); font-size:9.5pt; line-height:1.5; color:#22262b; break-inside:avoid;}
.sen .sn{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center; background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.grp{margin-left:8px;}
.ox{padding:4px 0 4px; border-bottom:1px dotted #eef1ee; break-inside:avoid;}
.ox:last-child{border-bottom:none;}
.st{font-size:9.3pt; line-height:1.5;}
.st::before{content:"·"; color:var(--sub); font-weight:800; margin-right:6px;}
.st .en{color:#2b2f6b; font-style:italic;}
.pick{margin:3px 0 0 12px; font-size:8.8pt; color:var(--sub);}
.pick .lab{font-weight:700; color:var(--green-d); margin-right:6px;}
.pick b{display:inline-block; width:19px; height:19px; line-height:19px; text-align:center; border:1.4px solid #c7cec8;
  border-radius:50%; margin-right:4px; font-weight:800;}
.pick .fixline{display:inline-block; border-bottom:1px solid #c7cec8; min-width:250px; margin-left:8px; vertical-align:-2px;}
.vd{display:inline-block; width:19px; height:19px; line-height:19px; text-align:center; border-radius:50%;
  font-weight:800; color:#fff; margin-left:6px;}
.vd.o{background:var(--green);} .vd.x{background:var(--red);} .vd.t{background:var(--amber);}
.kill{color:var(--red); font-weight:800; font-size:7.6pt; margin-left:5px;}
.why{margin:3px 0 0 12px; font-size:8.6pt; color:#3a4250; line-height:1.5;}
.why .cue{background:var(--green-soft); border-radius:3px; padding:0 3px; color:var(--green-d);}
.why .typ{color:var(--indigo); font-weight:700; font-size:7.8pt;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def vcls(v): return "o" if v=="O" else ("t" if v=="△" else "x")

def card(p, ans):
    no=esc(p["item_no"].strip()); ti=esc(p["overview"]["theme_ko"])
    h=[f'<div class="card"><div class="c-h"><span class="c-no">{no}</span><span class="c-ti">{ti}</span></div>']
    for s in p["sentences"]:
        ms=s.get("misreads",[])
        if not ms: continue
        h.append(f'<div class="sen"><span class="sn">{s["id"]}</span>{esc(s["english"])}</div>')
        h.append('<div class="grp">')
        for m in ms:
            v=m.get("verdict","X"); stmt=esc(m.get("statement",""))
            if m.get("english"): stmt=f'<span class="en">{stmt}</span>'
            if ans:
                kill='<span class="kill">🔥킬러</span>' if m.get("killer") else ''
                h.append('<div class="ox">')
                h.append(f'<div class="st">{stmt}<span class="vd {vcls(v)}">{v}</span>{kill}</div>')
                if v!="O" and (m.get("why") or m.get("anchor")):
                    an=f'<span class="cue">본문: {esc(m["anchor"])}</span> — ' if m.get("anchor") else ''
                    typ=f' <span class="typ">[{esc(m.get("trap_type",""))}]</span>' if m.get("trap_type") else ''
                    h.append(f'<div class="why">→ 바르게: {an}{esc(m.get("why",""))}{typ}</div>')
                h.append('</div>')
            else:
                h.append('<div class="ox">')
                h.append(f'<div class="st">{stmt}</div>')
                h.append('<div class="pick"><span class="lab">내 판단</span>'
                         '<b class="k-o">O</b><b class="k-x">X</b><b class="k-t">△</b>'
                         '<span class="fixline"></span></div>')
                h.append('</div>')
        h.append('</div>')
    h.append('</div>')
    return "".join(h)

def build(ans, out):
    badge='정답' if ans else '문제(학생용)'; bcls='ans' if ans else 'stu'
    hint=('<div class="hintbar">각 진술이 본문과 맞으면 <b class="k-o">O</b>, 틀리면 <b class="k-x">X</b>, '
          '결론은 맞지만 근거가 틀리면 <b class="k-t">△</b>. <b>X·△는 오른쪽 줄에 근거를 바르게 고치기.</b></div>') if not ans \
         else '<div class="hintbar">정답 판단과 근거입니다. <b class="k-x">X</b>·<b class="k-t">△</b>는 본문 대조 근거를 함께 표시했습니다.</div>'
    body=[f'<div class="doc-h"><span class="t">{TITLE}</span><span class="badge {bcls}">{badge}</span></div>', hint]
    for p in P: body.append(card(p, ans))
    doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
    HTML(string=doc).write_pdf(out)
    d=fitz.open(out); n=d.page_count; d.close(); return n

for ans,suf in [(False,"학생용"),(True,"정답")]:
    out=f"{SC}/고1_2026_9월_OX판단학습지_{suf}.pdf"
    print(f"{suf}: {build(ans,out)}p  ->  {os.path.basename(out)}")
print("OXTEST OK")
