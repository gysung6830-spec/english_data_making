# -*- coding: utf-8 -*-
"""올림포스 10-14강 '내용 정리 학습지' — 필생보 overview(글정리) 기반 빈칸 채우기 + 정답본."""
import json, os, html, re
from weasyprint import HTML
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/olrw"
FOOT="© 2026. ortica영어. All rights reserved."
TITLE="올림포스 독해 기본1 (10강-14강) · 내용 정리 학습지"

order=json.load(open(SC+"/order.json"))
P=[json.load(open(SC+"/passages/"+fn)) for fn in order]

def esc(s): return html.escape(str(s or ""))
def keyed(s):  # [[핵심어]] → 강조 표시(정답용)
    return re.sub(r"\[\[(.+?)\]\]", r'<b class="kw">\1</b>', esc(s))
def clean_topic(s):
    s=str(s or "").strip()
    for a,b in [("에 관한 글이야.",""),("에 관한 글이야",""),("글이야.","글이다."),("글이야","글이다"),("이야.","이다.")]:
        s=s.replace(a,b)
    return esc(s.strip())

CSS="""
@page{ size:A4; margin:13mm 12mm 12mm 12mm;
  @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; } }
*{box-sizing:border-box;}
body{font-family:"Noto Sans KR","Malgun Gothic",sans-serif; color:#22262b; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--green-soft:#eef5f0;
  --indigo:#575495;--indigo-bg:#ecebf4;--amber:#a9781f;--red:#a83c2c;--line:#d7ddd6;--sub:#5c636b;}
.doc-h{display:flex; align-items:baseline; gap:8px; border-bottom:2.5px solid var(--green); padding-bottom:5px; margin-bottom:6px;}
.doc-h .t{font-size:14pt; font-weight:800; color:var(--green-d); white-space:nowrap;}
.doc-h .badge{margin-left:auto; font-size:8.4pt; font-weight:700; padding:2px 9px; border-radius:20px;}
.badge.stu{background:var(--green-bg); color:var(--green-d);} .badge.ans{background:var(--indigo-bg); color:var(--indigo);}
.hintbar{font-size:8pt; color:var(--sub); background:var(--green-soft); border:1px solid var(--line);
  border-radius:7px; padding:5px 9px; margin-bottom:9px; line-height:1.5;}
.hintbar b{color:var(--green-d);}
.card{border:1px solid var(--line); border-radius:9px; padding:8px 11px 10px; margin-bottom:9px; break-inside:avoid;}
.c-h{display:flex; align-items:baseline; gap:7px; margin-bottom:5px;}
.c-no{background:var(--green); color:#fff; font-weight:800; font-size:8.4pt; padding:1px 8px; border-radius:20px; white-space:nowrap;}
.c-ti{font-size:10pt; font-weight:800; color:var(--green-d); line-height:1.35;}
.q{font-size:8pt; font-weight:800; color:var(--indigo); background:var(--indigo-bg); border-radius:4px; padding:1px 6px; margin-right:5px;}
.row{margin:4px 0; line-height:1.5;}
.oneline{display:flex; gap:16px; flex-wrap:wrap;}
.blk{display:inline-block; border-bottom:1.5px solid var(--green); min-width:120px; height:15px; vertical-align:-2px;}
.blk.wide{min-width:100%; margin-top:3px;}
.blk.mid{min-width:220px;}
.ans-v{color:var(--red); font-weight:700;}
.ans-v2{color:var(--indigo); font-weight:700;}
table.flow{width:100%; border-collapse:collapse; margin-top:3px;}
table.flow td{border:1px solid var(--line); padding:4px 6px; font-size:9pt; vertical-align:top;}
.flow .st{background:var(--green-soft); font-weight:700; color:var(--green-d); white-space:nowrap; width:74px; text-align:center;}
.flow .rg{color:var(--sub); font-size:8pt; white-space:nowrap; width:40px; text-align:center;}
.flow .sum-blank{height:20px;}
.rest .lab{display:inline-block; font-weight:700; color:var(--green-d); min-width:96px;}
.small{font-size:8pt; color:var(--sub);}
.kw{color:var(--amber);}
""".replace("__FOOT__", FOOT)

STANCES="긍정적 · 부정적·비판적 · 중립적"
STRUCTS="통념→반박(반전) · 주장→근거·예시 · 문제→해결(방안) · 비교·대조 · 시간·순서(나열) · 예시→일반화(결론)"

def card(p, ans):
    ov=p["overview"]; no=esc(p["item_no"].strip()); ti=esc(ov["theme_ko"])
    h=[f'<div class="card"><div class="c-h"><span class="c-no">{no}</span><span class="c-ti">{ti}</span></div>']
    # ① 입장·구조
    if ans:
        st=f'<span class="ans-v">{esc(ov["stance"])}</span>'; sr=f'<span class="ans-v">{esc(ov["structure"])}</span>'
    else:
        st='<span class="blk mid"></span>'; sr='<span class="blk mid"></span>'
    h.append(f'<div class="row oneline"><span><span class="q">①</span>필자 입장 {st}</span><span>글 구조 {sr}</span></div>')
    # ② 흐름 정리
    h.append('<div class="row"><span class="q">②</span>글의 흐름을 단계별로 정리하기</div>')
    h.append('<table class="flow">')
    for b in ov["flow_blocks"]:
        stg=esc(b["stage"]); rg=esc(b["sentence_range"])
        if ans:
            cell=f'<span class="ans-v2">{keyed(b["summary"])}</span>'
        else:
            cell='<div class="sum-blank"></div>'
        h.append(f'<tr><td class="st">{stg}</td><td class="rg">{rg}</td><td>{cell}</td></tr>')
    h.append('</table>')
    # ③ 핵심 반복 표현
    h.append('<div class="row rest"><span class="q">③</span>핵심 반복·재진술 표현 정리')
    for c in ov["restatement_chains"]:
        lab=esc(c["label"])
        if ans:
            val=f'<span class="ans-v">{esc(" / ".join(c["expressions"]))}</span>'
        else:
            val='<span class="blk wide"></span>'
        h.append(f'<div style="margin-top:3px;"><span class="lab">{lab}</span> {val}</div>')
    h.append('</div>')
    # ④ 한 줄 요약
    if ans:
        summ=f'<span class="ans-v">{clean_topic(ov["topic"])}</span>'
        h.append(f'<div class="row"><span class="q">④</span>한 줄 요약 {summ}</div>')
    else:
        h.append('<div class="row"><span class="q">④</span>한 줄 요약<span class="blk wide"></span></div>')
    h.append('</div>')
    return "".join(h)

def build(ans, out):
    badge='정답' if ans else '학생용'
    bcls='ans' if ans else 'stu'
    hint=(f'<div class="hintbar"><b>입장 보기</b> {STANCES} &nbsp;|&nbsp; <b>구조 보기</b> {STRUCTS}<br>'
          '필생보의 ⑤ 글정리를 참고해, 지문마다 <b>흐름 5단계</b>를 스스로 채우며 내용을 정리하세요.</div>') if not ans else \
         '<div class="hintbar">아래는 학습지의 <b>정답·모범 정리</b>입니다.</div>'
    body=[f'<div class="doc-h"><span class="t">{TITLE}</span><span class="badge {bcls}">{badge}</span></div>', hint]
    for p in P: body.append(card(p, ans))
    doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
    HTML(string=doc).write_pdf(out)
    d=fitz.open(out); n=d.page_count; d.close(); return n

for ans,suf in [(False,"학생용"),(True,"정답")]:
    out=f"{SC}/올림포스_10-14강_내용정리학습지_{suf}.pdf"
    n=build(ans, out)
    print(f"{suf}: {n}p  ->  {os.path.basename(out)}")
print("STUDYSHEET OK")
