# -*- coding: utf-8 -*-
"""올림포스 10-14강 '해석 시험지' — 문장별 영어 원문 + 해석 쓰기(학생용) / 모범 해석(정답)."""
import json, os, html, re
from weasyprint import HTML
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/olrw"
_HERE=os.path.dirname(os.path.abspath(__file__))
FONTDIR=(_HERE+"/fonts") if os.path.exists(_HERE+"/fonts/NanumSquareRoundR.ttf") \
    else "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/fonts"
FOOT="© 2026. ortica영어. All rights reserved."
TITLE="올림포스 독해 기본1 (10강-14강) · 해석 시험지"

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
  --indigo:#575495;--indigo-bg:#ecebf4;--line:#d7ddd6;--sub:#5c636b;}
.doc-h{display:flex; align-items:baseline; gap:8px; border-bottom:2.5px solid var(--green); padding-bottom:5px; margin-bottom:6px;}
.doc-h .t{font-size:14pt; font-weight:800; color:var(--green-d); white-space:nowrap;}
.doc-h .badge{margin-left:auto; font-size:8.4pt; font-weight:700; padding:2px 9px; border-radius:20px;}
.badge.stu{background:var(--green-bg); color:var(--green-d);} .badge.ans{background:var(--indigo-bg); color:var(--indigo);}
.hintbar{font-size:8.2pt; color:var(--sub); background:var(--green-soft); border:1px solid var(--line);
  border-radius:7px; padding:5px 9px; margin-bottom:9px; line-height:1.5;}
.hintbar b{color:var(--green-d);}
.card{border:1px solid var(--line); border-radius:9px; padding:8px 11px 9px; margin-bottom:9px; break-inside:avoid;}
.c-h{display:flex; align-items:baseline; gap:7px; margin-bottom:5px;}
.c-no{background:var(--green); color:#fff; font-weight:800; font-size:8.4pt; padding:1px 8px; border-radius:20px; white-space:nowrap;}
.c-ti{font-size:10pt; font-weight:800; color:var(--green-d); line-height:1.35;}
.s{padding:5px 0 6px; border-bottom:1px dotted #e6ebe8; break-inside:avoid;}
.s:last-child{border-bottom:none;}
.en{font-size:9.7pt; line-height:1.5;}
.en .n{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center;
  background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.wr{margin:4px 0 0 21px; border-bottom:1px solid #c7cec8; height:16px;}
.wr+.wr{margin-top:9px;}
.ko{margin:3px 0 0 21px; font-size:9pt; color:var(--indigo); font-weight:600; line-height:1.5;}
.ko::before{content:"↳ "; color:var(--green); font-weight:800;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def card(p, ans):
    no=esc(p["item_no"].strip()); ti=esc(p["overview"]["theme_ko"])
    h=[f'<div class="card"><div class="c-h"><span class="c-no">{no}</span><span class="c-ti">{ti}</span></div>']
    for s in p["sentences"]:
        h.append('<div class="s">')
        h.append(f'<div class="en"><span class="n">{s["id"]}</span>{esc(s["english"])}</div>')
        if ans:
            tr=(s.get("translation") or "").strip()
            h.append(f'<div class="ko">{esc(tr)}</div>')
        else:
            h.append('<div class="wr"></div><div class="wr"></div>')
        h.append('</div>')
    h.append('</div>')
    return "".join(h)

def build(ans, out):
    badge='정답' if ans else '문제(학생용)'; bcls='ans' if ans else 'stu'
    hint=('<div class="hintbar">각 문장을 <b>정확히 해석</b>해 아래 줄에 쓰세요. 구문 구조(주어·동사·수식 관계)를 놓치지 말 것.</div>') if not ans \
         else '<div class="hintbar">아래는 <b>모범 해석</b>입니다(구문 구조가 드러나는 해석).</div>'
    body=[f'<div class="doc-h"><span class="t">{TITLE}</span><span class="badge {bcls}">{badge}</span></div>', hint]
    for p in P: body.append(card(p, ans))
    doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
    HTML(string=doc).write_pdf(out)
    d=fitz.open(out); n=d.page_count; d.close(); return n

for ans,suf in [(False,"학생용"),(True,"정답")]:
    out=f"{SC}/올림포스_10-14강_해석시험지_{suf}.pdf"
    print(f"{suf}: {build(ans,out)}p  ->  {os.path.basename(out)}")
print("TRANSTEST OK")
