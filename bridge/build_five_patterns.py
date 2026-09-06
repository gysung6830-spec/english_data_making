# -*- coding: utf-8 -*-
"""문장의 5형식(1~5형식) 완전 정복 — 교재 1권 (직관형 슬롯 다이어그램 레이아웃).

    python -m bridge.build_five_patterns  →  output/문장의5형식_교재.pdf
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "문장의5형식_교재.pdf"

# 성분 색 (S 초록 · V 주황 · O 파랑 · C 보라)
COL = {"S": "#1f7a48", "V": "#c85f2a", "O": "#3a5bd0", "C": "#7a4fd0"}
BG = {"S": "#eaf5ee", "V": "#fdeee3", "O": "#eaf0fc", "C": "#f2ecfc"}

CSS = """
@page { size:A4; margin:14mm 12mm 13mm;
  @bottom-center{content:"ⓒ2026.김은아영어연구소.All rights reserved   ·   " counter(page);
    font-family:"NanumGothic","Malgun Gothic",sans-serif;font-size:8px;color:#9aa0a6;}
  @top-right{content:string(chap);font-family:"NanumGothic","Malgun Gothic",sans-serif;font-size:8px;color:#b3b9bf;}
  @top-left{content:"문장의 5형식 완전 정복";font-family:"NanumGothic","Malgun Gothic",sans-serif;font-size:8px;color:#c6ccd1;} }
@page cover { margin:0; @bottom-center{content:"";} @top-right{content:"";} @top-left{content:"";} }
@page front { @top-right{content:"";} @top-left{content:"";} }
*{box-sizing:border-box;}
body{font-family:"NanumGothic","Nanum Gothic","Malgun Gothic",sans-serif;color:#23272e;font-size:10.6px;line-height:1.55;margin:0;}
:root{--green:#2f9e5f;--green-d:#1f7a48;--green-bg:#eef7f1;--amber:#cf8a2a;--muted:#6b7280;--line:#e2e6ea;}
b{color:#12283f;}

/* 표지 */
.cover{page:cover;break-after:page;height:297mm;position:relative;
  background:linear-gradient(160deg,#2f9e5f 0%,#248a4f 55%,#1b6d3d 100%);color:#fff;}
.cover-in{position:absolute;inset:0;padding:42mm 24mm;display:flex;flex-direction:column;}
.ck{font-size:12px;font-weight:700;letter-spacing:3px;color:#d5f0df;margin-bottom:14px;}
.ct{font-size:42px;font-weight:800;line-height:1.15;letter-spacing:-1px;}
.cs{font-size:15px;font-weight:600;color:#e4f6ea;margin-top:12px;}
.ctag{display:inline-block;margin-top:22px;background:#fff;color:var(--green-d);font-size:14px;font-weight:800;padding:7px 18px;border-radius:24px;}
/* 표지 미니 다이어그램 */
.cov-dia{margin-top:24px;display:flex;flex-direction:column;gap:8px;}
.cov-row{display:flex;align-items:center;gap:6px;font-size:11px;}
.cov-row .n{width:40px;font-weight:800;color:#d5f0df;}
.cov-chip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.3);border-radius:7px;padding:3px 9px;font-weight:800;color:#fff;text-align:center;line-height:1.15;}
.cov-chip small{display:block;font-size:8px;font-weight:600;color:#cfeeda;margin-top:1px;}
.cbox{margin-top:auto;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.28);border-radius:12px;padding:14px 18px;}
.cbox h3{margin:0 0 7px;font-size:13px;color:#fff;} .cbox ul{margin:0;padding-left:16px;}
.cbox li{font-size:11px;color:#f0faf3;margin-bottom:4px;}

/* ===== 목차 ===== */
.toc{page:front;break-after:page;padding-top:4mm;}
.toc h1{font-size:24px;font-weight:800;color:var(--green-d);margin:0 0 3px;}
.toc h1 .en{display:block;font-size:11px;font-weight:800;letter-spacing:3px;color:var(--green);margin-bottom:2px;}
.toc .sub{font-size:11px;color:var(--muted);margin:0 0 20px;padding-bottom:12px;border-bottom:2px solid var(--green);}
a.tr{display:flex;align-items:baseline;text-decoration:none;color:#23272e;font-size:12.5px;padding:11px 3px;border-bottom:1px dotted #ccd3d9;}
a.tr .k{font-weight:800;color:var(--green-d);min-width:78px;}
a.tr .tt2{flex:1;}
a.tr .cc{font-size:9.5px;color:var(--muted);font-weight:700;margin:0 10px;}
a.tr::after{content:target-counter(attr(href), page);font-weight:800;color:var(--green-d);min-width:20px;text-align:right;}
.toc .tnote{margin-top:20px;background:var(--green-bg);border-radius:9px;padding:11px 15px;font-size:10.3px;color:#2c5d41;line-height:1.6;}
.toc .tnote b{color:var(--green-d);}

/* 섹션 */
.sec{break-before:page;}
.band{background:var(--green-d);color:#fff;border-radius:10px;padding:11px 16px;margin-bottom:13px;display:flex;align-items:baseline;gap:12px;}
.band .no{font-size:19px;font-weight:800;}
.band .tt{font-size:16px;font-weight:800;string-set:chap content();}
.band .code{font-size:11px;font-weight:700;color:#cdeed9;margin-left:auto;}

/* ===== 단원 도입부 ===== */
.uhead{background:linear-gradient(135deg,#2f9e5f 0%,#1f7a48 100%);color:#fff;border-radius:13px;padding:15px 19px 16px;margin-bottom:15px;break-inside:avoid;}
.ubar{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid rgba(255,255,255,.25);padding-bottom:10px;margin-bottom:11px;}
.unum{font-size:11px;font-weight:800;letter-spacing:2px;background:#fff;color:var(--green-d);padding:3px 11px;border-radius:20px;}
.ut{font-size:18px;font-weight:800;string-set:chap content();}
.ucode{margin-left:auto;font-size:12.5px;font-weight:800;color:#d5f0df;letter-spacing:1px;}
.goals .gh{font-size:10.5px;font-weight:800;color:#eafff2;margin-bottom:6px;}
.goals ul{margin:0;padding:0;list-style:none;}
.goals li{font-size:10.6px;color:#f3fbf6;margin-bottom:4px;padding-left:19px;position:relative;line-height:1.5;}
.goals li:last-child{margin-bottom:0;}
.goals li::before{content:"✔";position:absolute;left:2px;color:#c6f2d6;font-weight:800;}

/* ===== 핵심: 슬롯 다이어그램 ===== */
.diawrap{border:1.5px solid var(--line);border-radius:12px;padding:13px 14px 11px;margin-bottom:12px;background:#fcfdfc;break-inside:avoid;}
.dia{display:flex;gap:7px;align-items:stretch;}
.slot{flex:1 1 auto;min-width:66px;border-radius:9px;overflow:hidden;border:2px solid #ccc;text-align:center;}
.slot .lab{color:#fff;font-size:9px;font-weight:800;padding:3px 2px;line-height:1.2;}
.slot .lab b{color:#fff;font-size:11px;display:block;}
.slot .lab .lt{display:block;font-size:8px;font-weight:700;opacity:.9;margin-top:1px;}
.slot .w{padding:9px 4px;font-size:15px;font-weight:800;background:#fff;}
.op{align-self:center;font-size:15px;font-weight:800;color:#c2c8cf;padding:0 1px;}
.m-chip{align-self:center;font-size:9.5px;color:var(--muted);background:#f1f3f5;border-radius:7px;padding:6px 8px;font-weight:700;}
.rel{margin-top:9px;text-align:center;font-size:11px;font-weight:800;color:#374151;}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;vertical-align:middle;margin:0 2px;}
.eq{color:#c85f2a;font-size:13px;padding:0 4px;}

/* 개념 콜아웃 */
.concept{background:var(--green-bg);border-left:4px solid var(--green);border-radius:0 8px 8px 0;padding:9px 13px;margin-bottom:11px;font-size:10.4px;}
.concept b{background:#fff;padding:0 2px;border-radius:3px;}

.h{font-size:11.5px;font-weight:800;color:var(--green-d);margin:11px 0 6px;}
/* 예문 라인 */
.exl{display:flex;gap:10px;align-items:baseline;padding:5px 2px;border-bottom:1px solid var(--line);}
.exl .en{flex:1.1;font-size:11px;font-weight:700;color:#12283f;}
.exl .ko{flex:1;font-size:10px;color:#4b5563;}
.S{color:#1f7a48;font-weight:800;} .V{color:#c85f2a;font-weight:800;} .O{color:#3a5bd0;font-weight:800;} .C{color:#7a4fd0;font-weight:800;} .M{color:#9aa0a6;font-weight:700;}

/* 동사 칩 */
.verbs{margin:4px 0 10px;font-size:0;}
.vchip{display:inline-block;font-size:9.8px;font-weight:700;color:var(--green-d);background:var(--green-bg);border:1px solid #cfe6d8;border-radius:14px;padding:3px 10px;margin:0 5px 5px 0;}
.vgrp{font-size:9.5px;color:var(--muted);font-weight:800;margin:2px 0 3px;}

.tip{background:#fdf6ea;border-radius:8px;padding:8px 13px;font-size:10px;color:#7a4a12;margin:2px 0 11px;}
.tip .l{font-weight:800;color:var(--amber);margin-right:5px;}
.tip b{color:#7a4a12;background:#fbe6c8;padding:0 2px;border-radius:3px;}

/* 왜 배울까 / 시험 포인트 / 암기 */
.why{background:#eef4fc;border-left:4px solid #3a5bd0;border-radius:0 9px 9px 0;padding:9px 13px;margin:0 0 12px;font-size:10.3px;line-height:1.6;}
.why .l{display:inline-block;font-weight:800;color:#fff;background:#3a5bd0;font-size:9.5px;padding:2px 9px;border-radius:9px;margin-bottom:4px;}
.why .cmp{margin-top:3px;} .why .cmp .en{font-weight:800;color:#12283f;} .why .cmp .a{color:#3a5bd0;font-weight:800;}
.exam{background:#fdeef0;border-left:4px solid #cd5049;border-radius:0 9px 9px 0;padding:8px 13px;font-size:10px;margin:2px 0 8px;line-height:1.6;}
.exam .l{display:inline-block;font-weight:800;color:#fff;background:#cd5049;font-size:9.5px;padding:2px 9px;border-radius:9px;margin-right:6px;}
.exam b{color:#a3352f;background:#fbe0de;padding:0 2px;border-radius:3px;}
.memo{background:#eef7f1;border-left:4px solid var(--green-d);border-radius:0 9px 9px 0;padding:8px 13px;font-size:10px;margin:2px 0 11px;line-height:1.6;}
.memo .l{display:inline-block;font-weight:800;color:#fff;background:var(--green-d);font-size:9.5px;padding:2px 9px;border-radius:9px;margin-right:6px;}
.memo b{color:var(--green-d);background:#dcefe3;padding:0 3px;border-radius:3px;}

/* 연습 */
.q-h{font-weight:800;font-size:11px;color:var(--amber);margin:12px 0 6px;}
.q-h .b{display:inline-block;background:var(--amber);color:#fff;font-size:9px;font-weight:800;padding:1px 8px;border-radius:8px;margin-right:6px;}
.q{margin:0 0 7px;line-height:1.85;} .blank{display:inline-block;min-width:60px;border-bottom:1px solid #333;text-align:center;}
.q .sel{font-weight:800;}
.ans{background:#f6f8f7;border:1px solid var(--line);border-radius:8px;padding:9px 13px;margin-top:8px;break-inside:avoid;}
.ans .t{display:inline-block;background:#111827;color:#fff;font-size:10px;font-weight:800;padding:2px 10px;border-radius:5px;margin-bottom:5px;}
.ans p{margin:3px 0;font-size:9.6px;line-height:1.65;} .ans b{color:var(--green-d);}

/* 들어가기 / 총정리 표 */
.note{background:#f2f0f6;border-radius:8px;padding:8px 13px;font-size:10px;margin:2px 0 12px;}
table.sum{width:100%;border-collapse:collapse;margin:4px 0 12px;}
table.sum th{background:var(--green-d);color:#fff;font-size:10px;font-weight:700;padding:6px 8px;text-align:left;}
table.sum td{border:1px solid var(--line);padding:6px 8px;font-size:10px;vertical-align:middle;}
table.sum tbody tr:nth-child(even) td{background:var(--green-bg);}
"""

# ---------- 슬롯 다이어그램 ----------
# 쉬운 말 → 문법 용어 병기(자동). 필요하면 "쉬운말|용어"로 직접 지정.
TERM = {"누가": "주어", "한다": "동사", "이다": "동사", "준다": "동사",
        "무엇을": "목적어", "어떠하다": "보어", "어떻게": "목적격보어",
        "누구에게": "간접목적어"}

def slot(kind, label, word):
    c = COL[kind]
    if "|" in label:
        main, sub = label.split("|", 1)
    else:
        main, sub = label, TERM.get(label, "")
    lab = f'<b>{main}</b>' + (f'<span class="lt">{sub}</span>' if sub else "")
    return (f'<div class="slot" style="border-color:{c}">'
            f'<div class="lab" style="background:{c}">{lab}</div>'
            f'<div class="w" style="color:{c}">{word}</div></div>')

def dia(items, rel=""):
    """items: (kind, label, word) or ('op','+'/'='/None,'') or ('m','',text)."""
    parts = []
    for it in items:
        if it[0] == "op":
            parts.append(f'<div class="op">{it[1]}</div>')
        elif it[0] == "m":
            parts.append(f'<div class="m-chip">{it[2]}</div>')
        else:
            parts.append(slot(it[0], it[1], it[2]))
    inner = "".join(parts)
    r = f'<div class="rel">{rel}</div>' if rel else ""
    return f'<div class="diawrap"><div class="dia">{inner}</div>{r}</div>'

def dot(kind):
    return f'<span class="dot" style="background:{COL[kind]}"></span>'

def band(no, tt, code):
    return f'<div class="band"><div class="no">{no}</div><div class="tt">{tt}</div><div class="code">{code}</div></div>'

def exlines(rows):
    return "".join(f'<div class="exl"><div class="en">{en}</div><div class="ko">{ko}</div></div>' for en, ko in rows)

def verbs(groups):
    """groups: [(header, [chips])]"""
    out = []
    for hdr, chips in groups:
        if hdr:
            out.append(f'<div class="vgrp">{hdr}</div>')
        out.append('<div class="verbs">' + "".join(f'<span class="vchip">{c}</span>' for c in chips) + '</div>')
    return "".join(out)


# ============================================================ 표지
COVER = f"""
<div class="cover"><div class="cover-in">
  <div class="ck">한 권으로 끝내는 영어 문장 구조</div>
  <div class="ct">문장의 5형식<br>완전 정복</div>
  <div class="cs">색깔 블록으로 한눈에 — 동사가 문장을 결정한다</div>
  <div class="ctag">중·고 기초 문법 · 내신 대비</div>
  <div class="cov-dia">
    <div class="cov-row"><span class="n">1형식</span><span class="cov-chip">누가<small>주어</small></span><span class="cov-chip">한다<small>동사</small></span></div>
    <div class="cov-row"><span class="n">2형식</span><span class="cov-chip">누가<small>주어</small></span><span class="cov-chip">이다<small>동사</small></span><span class="cov-chip">어떠하다<small>보어</small></span></div>
    <div class="cov-row"><span class="n">3형식</span><span class="cov-chip">누가<small>주어</small></span><span class="cov-chip">한다<small>동사</small></span><span class="cov-chip">무엇을<small>목적어</small></span></div>
    <div class="cov-row"><span class="n">4형식</span><span class="cov-chip">누가<small>주어</small></span><span class="cov-chip">준다<small>동사</small></span><span class="cov-chip">누구에게<small>간접목적어</small></span><span class="cov-chip">무엇을<small>직접목적어</small></span></div>
    <div class="cov-row"><span class="n">5형식</span><span class="cov-chip">누가<small>주어</small></span><span class="cov-chip">한다<small>동사</small></span><span class="cov-chip">무엇을<small>목적어</small></span><span class="cov-chip">어떻게<small>목적격보어</small></span></div>
  </div>
  <div class="cbox"><h3>이 교재는요</h3><ul>
    <li>문장을 <b>색깔 블록</b>으로 보여줘 구조가 한눈에 들어와요.</li>
    <li><b>&lsquo;누가·한다·무엇을&rsquo;</b> 쉬운 말과 <b>문법 용어(주어·동사·목적어)</b>를 함께 적어요.</li>
    <li>읽기만 해도 이해되도록 <b>그림과 예문</b> 위주로 담았어요.</li>
  </ul></div>
</div></div>
"""

# ============================================================ 목차
TOC = """
<div class="toc">
  <h1><span class="en">CONTENTS</span>목차</h1>
  <p class="sub">문장의 5형식 완전 정복 — 색깔 블록으로 배우는 영어 문장 구조</p>
  <a class="tr" href="#intro"><span class="k">들어가기</span><span class="tt2">문장에도 &lsquo;형식&rsquo;이 있다</span><span class="cc">개념 · 왜 5형식?</span></a>
  <a class="tr" href="#u1"><span class="k">UNIT 1</span><span class="tt2">1형식 · 누가 + 한다</span><span class="cc">주어 + 동사</span></a>
  <a class="tr" href="#u2"><span class="k">UNIT 2</span><span class="tt2">2형식 · 누가 + 이다 + 어떠하다</span><span class="cc">주어 + 동사 + 보어</span></a>
  <a class="tr" href="#u3"><span class="k">UNIT 3</span><span class="tt2">3형식 · 누가 + 한다 + 무엇을</span><span class="cc">주어 + 동사 + 목적어</span></a>
  <a class="tr" href="#u4"><span class="k">UNIT 4</span><span class="tt2">4형식 · 누가 + 준다 + 누구에게 + 무엇을</span><span class="cc">주어 + 동사 + 목적어 두 개</span></a>
  <a class="tr" href="#u5"><span class="k">UNIT 5</span><span class="tt2">5형식 · 누가 + 한다 + 무엇을 + 어떻게</span><span class="cc">주어 + 동사 + 목적어 + 보어</span></a>
  <a class="tr" href="#summary"><span class="k">총정리</span><span class="tt2">5형식 한눈에 &amp; 구별하는 법</span><span class="cc">복습 + 종합 연습</span></a>
  <div class="tnote"><b>이 교재는 이렇게 공부해요.</b> 각 단원은 <b>학습 목표 → 구조 그림 → 왜 배울까 → 예문(STEP 1) →
    자주 쓰는 동사(STEP 2) → 시험·암기 포인트 → 연습(STEP 3)</b> 순서예요. 하루에 한 단원씩, 순서대로 읽어 오면 됩니다.</div>
</div>
"""

# ============================================================ 들어가기
INTRO = f"""
<div class="sec" id="intro">
  {band("들어가기", "문장에도 '형식'이 있다", "왜 5형식?")}
  <div class="concept">영어 문장은 <b>동사(한다)</b>가 뼈대를 정해요. 동사에 따라 뒤에 <b>&lsquo;무엇을&rsquo;(목적어)</b>가 오기도,
  <b>&lsquo;어떠하다&rsquo;(보어)</b>가 오기도 해요. 문장을 만드는 <b>덩어리 4가지</b>만 색으로 익히면 구조가 바로 보여요.
  <br>※ 이 교재는 <b>쉬운 말</b>과 <b>(문법 용어)</b>를 나란히 적어요. 쉬운 말로 이해하고, 괄호 안 용어는 시험에서 만나요.</div>

  <div class="h">문장을 만드는 4덩어리 — 쉬운 말(문법 용어)로 기억하기</div>
  {dia([("S","누가","Birds 새가"),("V","한다","sing 노래한다"),("O","무엇을","a song 노래를"),("C","어떠하다","= 설명하는 말")],
       rel=f'{dot("S")}누가(주어) {dot("V")}한다(동사) {dot("O")}무엇을(목적어) {dot("C")}어떠하다(보어) &nbsp;·&nbsp; 회색은 <b>꾸미는 말(수식어)</b>')}
  <div class="note"><b>&lsquo;무엇을(목적어)&rsquo;과 &lsquo;어떠하다(보어)&rsquo;의 차이</b> — <b>목적어</b>는 <b>동작을 받는 대상</b>(노래<b>를</b> 부른다),
  <b>보어</b>는 <b>앞말을 = 로 설명</b>(그녀 <b>=</b> 선생님). 이 둘만 구별하면 5형식이 다 풀려요.</div>

  <div class="h">1형식부터 5형식까지, 한눈에</div>
  {dia([("S","누가","Birds"),("op","+"),("V","한다","sing")], rel="① 1형식 — 동사만으로 문장 끝!")}
  {dia([("S","누가","She"),("op","+"),("V","이다","is"),("op","+"),("C","어떠하다","a teacher")], rel=f'② 2형식 — {dot("S")}She(그녀) <span class="eq">=</span> {dot("C")}a teacher(선생님)')}
  {dia([("S","누가","I"),("op","+"),("V","한다","love"),("op","+"),("O","무엇을","you")], rel="③ 3형식 — you(너를) 사랑한다")}
  {dia([("S","누가","He"),("op","+"),("V","준다","gave"),("op","+"),("O","누구에게","me"),("op","+"),("O","무엇을|직접목적어","a book")], rel="④ 4형식 — me(나에게) + a book(책을)")}
  {dia([("S","누가","We"),("op","+"),("V","한다","call"),("op","+"),("O","무엇을","him"),("op","+"),("C","어떻게","a genius")], rel=f'⑤ 5형식 — {dot("O")}him(그를) <span class="eq">=</span> {dot("C")}a genius(천재라고)')}

  <div class="tip"><span class="l">핵심 한 줄</span>동사 뒤에 <b>&lsquo;무엇을&rsquo;(목적어)</b>이 오면 <b>받는 대상</b>, <b>&lsquo;= 설명&rsquo;(보어)</b>이 오면 <b>앞말을 설명하는 말</b>. 이 둘만 나누면 돼요!</div>

  <div style="break-inside:avoid;">
  <div class="h">그런데 왜 굳이 형식을 배울까?</div>
  <div class="why" style="margin-bottom:0;"><span class="l">이유 하나면 충분해요</span>
    <b>같은 동사라도 형식이 바뀌면 뜻이 완전히 달라지기 때문</b>이에요. 형식을 모르면 해석이 틀려요.
    <div class="cmp"><span class="en">She made me a cake.</span> → <span class="a">4형식</span> · 나<b>에게</b> 케이크<b>를</b> 만들어 줬다</div>
    <div class="cmp"><span class="en">She made me happy.</span> → <span class="a">5형식</span> · 나<b>를</b> 행복하<b>게</b> 만들었다</div>
    <div class="cmp"><span class="en">I found the book.</span> → <span class="a">3형식</span> · 그 책<b>을</b> 찾았다 &nbsp;／&nbsp;
      <span class="en">I found the book easy.</span> → <span class="a">5형식</span> · 그 책<b>이</b> 쉽다<b>고</b> 느꼈다</div>
    이렇게 <b>동사에 따라 문장 짜임이 달라져요</b>. 그래서 &lsquo;몇 형식인지&rsquo; 보는 눈이 <b>정확한 해석과 시험 문제</b>의 열쇠예요.</div>
  </div>
</div>
"""

# ============================================================ 단원(형식 섹션)
def uhead(n, num, tt, code, goals):
    lis = "".join(f"<li>{g}</li>" for g in goals)
    return (f'<div class="uhead"><div class="ubar">'
            f'<span class="unum">UNIT {n}</span>'
            f'<span class="ut">{num} · {tt}</span>'
            f'<span class="ucode">{code}</span></div>'
            f'<div class="goals"><div class="gh">이 단원에서 배울 것 — 학습 목표</div>'
            f'<ul>{lis}</ul></div></div>')

def unit(n, num, tt, code, goals, flagship, why, concept, ex_rows, verb_groups, tip, exam, memo, quiz, ans):
    return f"""
<div class="sec" id="u{n}">
  {uhead(n, num, tt, code, goals)}
  {flagship}
  <div class="why"><span class="l">왜 배울까?</span>{why}</div>
  <div class="concept">{concept}</div>
  <div class="h">STEP 1 · 이렇게 읽어요</div>
  {exlines(ex_rows)}
  <div class="h">STEP 2 · 이 형식에 잘 쓰는 동사</div>
  {verbs(verb_groups)}
  <div class="tip"><span class="l">✔ 헷갈리지 않기</span>{tip}</div>
  <div class="exam"><span class="l">시험 포인트</span>{exam}</div>
  <div class="memo"><span class="l">암기!</span>{memo}</div>
  <div class="q-h"><span class="b">STEP 3 · 연습</span>직접 풀어보기</div>
  {quiz}
  <div class="ans"><div class="t">정답 &amp; 해설</div>{ans}</div>
</div>
"""

S1 = unit(1, "1형식", "누가 + 한다", "주어 + 동사",
    ["<b>&lsquo;누가 + 한다&rsquo;(주어 + 동사)</b>만으로 문장이 끝나는 경우를 안다",
     "뒤에 붙은 <b>꾸미는 말(수식어)</b>(in the sky 등 없어도 되는 말)을 가려낸다",
     "「There is/are ~」(~이 있다)도 1형식임을 안다"],
    dia([("S","누가","Birds"),("op","+"),("V","한다","sing"),("op",""),("m","","（in the sky）꾸미는 말")],
        rel="동사(sing)까지만 있어도 문장이 완성돼요. 뒤에 붙은 <b>&lsquo;하늘에서&rsquo;는 꾸미는 말</b>이라 빼고 봐요."),
    "문장을 &lsquo;몇 형식&rsquo;으로 보는 건 <b>어디까지가 진짜 뼈대인지</b> 가려내기 위해서예요. "
    "1형식을 알면 <b>The sun rises in the east</b>(해가 동쪽에서 뜬다)에서 <b>&lsquo;동쪽에서&rsquo;를 지우고</b> "
    "&lsquo;해가 뜬다&rsquo;라는 핵심만 딱 잡을 수 있어요. 긴 문장도 <b>누가·한다부터</b> 찾는 습관이 여기서 시작돼요.",
    "1형식은 <b>&lsquo;누가 + 한다&rsquo;(주어 + 동사)</b>만으로 뜻이 끝나요. 뒤에 &lsquo;무엇을&rsquo;(목적어)이 없어도 되는 동사, "
    "곧 <b>완전자동사</b>예요. 「<b>There is/are ~</b>」(~이 있다)도 1형식이에요.",
    [("<span class='S'>The sun</span> <span class='V'>rises</span> <span class='M'>in the east</span>.", "해가 (동쪽에서) 뜬다."),
     ("<span class='S'>She</span> <span class='V'>lives</span> <span class='M'>in Seoul</span>.", "그녀는 (서울에) 산다."),
     ("<span class='V'>There is</span> <span class='S'>a book</span> <span class='M'>on the desk</span>.", "(책상 위에) 책이 있다.")],
    [("", ["go 가다","come 오다","run 뛰다","walk 걷다","sleep 자다","live 살다","arrive 도착하다","happen 일어나다","rise 뜨다","cry 울다"])],
    "<b>in the east(동쪽에서)</b>처럼 <b>in·on·at</b>으로 시작하는 말은 <b>꾸미는 말(수식어)</b>! 괄호로 묶어 빼세요. 뒤에 &lsquo;무엇을&rsquo;(목적어)이 없으면 1형식.",
    "<b>꾸미는 말(수식어)을 지운 뒤 몇 형식인지 판단</b>하는 문제가 자주 나와요. &lsquo;There is/are ~&rsquo;도 "
    "1형식이라는 걸 <b>꼭</b> 물어봐요. &lsquo;무엇을&rsquo;(목적어)이 없다고 당황하지 않기.",
    "① <b>&lsquo;무엇을&rsquo; 없이 끝나는 동사(완전자동사)</b>: go·come·live·arrive·happen·rise… "
    "② <b>There is/are ~ = 1형식</b>. ③ <b>in·on·at으로 시작하는 말(수식어)</b>은 형식 셀 때 뺀다.",
    """<div class="q">1) &lsquo;누가·한다&rsquo;를 찾고 꾸미는 말은 ( )로 묶으세요. &nbsp;① The baby cried. &nbsp;② We arrived at the station.</div>
       <div class="q">2) 몇 형식? &nbsp; There are many stars in the sky. → ( <span class="blank"></span> )형식</div>""",
    """<p><b>1.</b> ① 누가=The baby / 한다=cried &nbsp; ② 누가=We / 한다=arrived / (at the station)은 꾸미는 말</p>
       <p><b>2.</b> 1형식 (There are ~, in the sky는 꾸미는 말)</p>""")

S2 = unit(2, "2형식", "누가 + 이다 + 어떠하다", "주어 + 동사 + 보어",
    ["동사 뒤 말(<b>보어</b>)이 <b>앞 사람을 &lsquo;= 로 설명&rsquo;</b>한다는 걸 이해한다 (그녀 = 선생님)",
     "<b>look·feel처럼 느낌을 말하는 동사(감각동사)</b> 뒤엔 happy 같은 <b>상태를 나타내는 말(형용사)</b>이 옴을 안다",
     "be(이다)·become(되다) 등 <b>2형식에 자주 쓰는 동사</b>를 익힌다"],
    dia([("S","누가","She"),("op","+"),("V","이다","is"),("op","+"),("C","어떠하다","a teacher")],
        rel=f'{dot("S")}She(그녀) <span class="eq">=</span> {dot("C")}a teacher(선생님) &nbsp;→&nbsp; <b>뒷말이 앞말을 설명</b>해요'),
    "&lsquo;그녀는 이다&rsquo;만 말하면 말이 안 되죠? <b>is(이다)·become(되다)·look(보이다)</b> 같은 동사는 뒤에 "
    "<b>&lsquo;그녀가 어떤 사람/어떤 상태인지&rsquo;</b> 설명하는 말이 꼭 필요해요. 그래서 뒷말을 <b>&lsquo;=&rsquo;</b>로 이어 읽어야 뜻이 통해요. "
    "<b>She looks tired = 그녀는 피곤해 보인다</b>처럼, 이걸 알면 &lsquo;~해 보인다/들린다/느껴진다&rsquo;를 정확히 해석해요.",
    "2형식은 <b>동사 뒤에 &lsquo;어떠하다&rsquo;(보어)</b>가 오는 문장이에요. 이 <b>보어</b>는 <b>앞 사람을 설명</b>해서 "
    "<b>앞 사람과 &lsquo;= 관계&rsquo;</b>가 돼요. (그녀 = 선생님 / 그녀 = 피곤함) 보어 자리엔 <b>이름(명사)·상태말(형용사)</b>이 와요.",
    [("<span class='S'>He</span> <span class='V'>became</span> <span class='C'>famous</span>.", "그는 유명해졌다. (그 = 유명함)"),
     ("<span class='S'>The soup</span> <span class='V'>tastes</span> <span class='C'>good</span>.", "수프는 맛이 좋다. (수프 = 좋은 맛)"),
     ("<span class='S'>You</span> <span class='V'>look</span> <span class='C'>tired</span>.", "너 피곤해 보인다. (너 = 피곤함)")],
    [("~이다 · ~이 되다", ["be(am/are/is) 이다","become 되다","get ~해지다","grow 자라다·되다","turn 변하다","stay 그대로 있다"]),
     ("느낌을 말하는 동사 (감각동사)", ["look 보이다","sound 들리다","smell 냄새나다","taste 맛나다","feel 느껴지다","seem ~같다"])],
    "<b>look·feel처럼 느낌을 말하는 동사(감각동사)</b> 뒤엔 <b>happy</b> 같은 상태말(형용사)이 와요. "
    "<b>happily</b>(-ly 붙은 말, 부사)는 오답! &nbsp;You look <b>happy</b>(○) / happily(✗).",
    "<b>look·feel(감각동사) 뒤에 happy / happily 중 고르기</b>가 단골 문제! <b>-ly 안 붙은 상태말(형용사)</b>이 정답이에요. "
    "&lsquo;앞말 = 뒷말(보어)&rsquo;로 이어지는지 물어 2형식인지도 확인시켜요.",
    "① <b>감각동사(look·sound·smell·taste·feel) 뒤엔 상태말(형용사)</b> — -ly 붙은 말(부사)은 오답! "
    "② 자주 쓰는 동사: <b>be·become·get·grow·turn·stay</b>. ③ 확인법: <b>앞말 = 뒷말(보어)</b>이면 2형식.",
    """<div class="q">1) 앞말을 설명하는 말에 밑줄. &nbsp;① The leaves turned red. &nbsp;② This cake smells sweet.</div>
       <div class="q">2) 알맞은 것에 ○: &nbsp; She looks ( <span class="sel">happy</span> / happily ).</div>""",
    """<p><b>1.</b> ① red (나뭇잎 = 빨감) &nbsp; ② sweet (케이크 = 달콤함)</p>
       <p><b>2.</b> happy — look 뒤엔 -ly 없는 말 (happily ✗)</p>""")

S3 = unit(3, "3형식", "누가 + 한다 + 무엇을", "주어 + 동사 + 목적어",
    ["동사 뒤 <b>&lsquo;무엇을&rsquo;(목적어)</b> — 동작을 받는 대상 — 을 찾을 수 있다",
     "&lsquo;무엇을&rsquo;을 데려오는 동사(<b>타동사</b>)를 안다 (enter·discuss는 into·about 없이 바로!)",
     "<b>-ing(동명사) / to+동사(to부정사)</b> 덩어리도 &lsquo;무엇을&rsquo; 자리에 옴을 안다"],
    dia([("S","누가","I"),("op","+"),("V","한다","love"),("op","+"),("O","무엇을","you")],
        rel=f'{dot("O")}you(너<b>를</b>) = 동작을 받는 대상'),
    "우리가 쓰는 문장의 <b>대부분이 3형식</b>이에요. &lsquo;누가 무엇을 ~한다&rsquo;가 가장 기본이니까요. "
    "3형식을 알면 &lsquo;무엇을&rsquo; 자리에 <b>한 단어뿐 아니라 긴 덩어리</b>도 올 수 있다는 걸 알게 돼요. "
    "그래야 <b>I enjoy playing soccer</b>(나는 축구하는 것을 즐긴다)처럼 긴 부분도 &lsquo;~하는 것을&rsquo;로 묶어 해석해요.",
    "3형식은 <b>동사 뒤에 &lsquo;무엇을&rsquo;(목적어)</b>이 오는 문장이에요. 이 <b>목적어</b>는 <b>동작을 받는 대상</b>이고, "
    "이런 동사를 <b>타동사</b>라고 해요. 목적어 자리엔 <b>한 단어</b>뿐 아니라 <b>-ing(동명사)·to+동사(to부정사)</b> 덩어리도 올 수 있어요.",
    [("<span class='S'>She</span> <span class='V'>reads</span> <span class='O'>books</span>.", "그녀는 책을 읽는다."),
     ("<span class='S'>We</span> <span class='V'>enjoy</span> <span class='O'>playing soccer</span>.", "우리는 축구하는 것을 즐긴다. (-ing = 동명사)"),
     ("<span class='S'>I</span> <span class='V'>want</span> <span class='O'>to sleep</span>.", "나는 자기를 원한다. (to+동사 = to부정사)")],
    [("", ["love 사랑하다","like 좋아하다","have 가지다","read 읽다","make 만들다","eat 먹다","want 원하다","know 알다","meet 만나다","buy 사다"])],
    "동사 뒤에 &lsquo;무엇을&rsquo;(목적어)이 있으면 3형식. 단, <b>enter·discuss·marry·reach·answer·resemble</b>는 "
    "<b>into·about 같은 말 없이 바로</b> 목적어를 붙여요! (enter <b>into</b> the room ✗)",
    "<b>enter·discuss 뒤에 into·about를 넣으면 오답</b>인 걸 자주 물어봐요 "
    "(enter <b>into</b>✗, discuss <b>about</b>✗). 목적어로 쓴 <b>-ing(동명사)/to+동사(to부정사)</b>를 찾는 문제도 나와요.",
    "① <b>바로 목적어를 붙이는 동사(타동사, into·about 금지)</b>: <u>discuss · marry · enter · reach · resemble · answer</u>. "
    "② 목적어 자리 = 한 단어 · <b>-ing(동명사) · to+동사(to부정사)</b>.",
    """<div class="q">1) &lsquo;무엇을&rsquo;에 밑줄. &nbsp;① I finished my homework. &nbsp;② They enjoy watching movies.</div>
       <div class="q">2) 틀린 곳 고치기: &nbsp; He entered <span class="sel">into</span> the room. → <span class="blank"></span></div>""",
    """<p><b>1.</b> ① my homework(숙제를) &nbsp; ② watching movies(영화 보는 것을)</p>
       <p><b>2.</b> into 삭제 → He entered the room. (enter는 바로 &lsquo;무엇을&rsquo;)</p>""")

S4 = unit(4, "4형식", "누가 + 준다 + 누구에게 + 무엇을", "주어 + 동사 + 목적어 두 개",
    ["동사 뒤에 <b>&lsquo;누구에게&rsquo;(간접목적어) + &lsquo;무엇을&rsquo;(직접목적어)</b> 두 개가 오는 문장을 안다",
     "&lsquo;주다&rsquo;류 동사(<b>수여동사</b>)의 순서는 <b>사람 먼저, 물건 나중</b>임을 안다",
     "<b>to·for·of(전치사)</b>를 써서 다르게 쓰는 법을 익힌다"],
    dia([("S","누가","He"),("op","+"),("V","준다","gave"),("op","+"),("O","누구에게","me"),("op","+"),("O","무엇을|직접목적어","a book")],
        rel=f'{dot("O")}me (<b>나에게</b>) &nbsp;+&nbsp; {dot("O")}a book (<b>책을</b>) &nbsp;→&nbsp; 받는 말이 <b>두 개</b> (사람 + 물건)'),
    "&lsquo;주다·말해 주다·보내 주다&rsquo;처럼 <b>누구에게 무엇을</b> 해 주는 동작은 받는 말이 <b>두 개</b> 필요해요. "
    "4형식을 알면 <b>He gave me a book</b>을 &lsquo;나에게 / 책을&rsquo; 두 덩어리로 정확히 끊어 읽어요. "
    "또 이걸 <b>He gave a book to me</b>처럼 <b>순서를 바꿔 쓰는 시험 문제</b>도 풀 수 있어요.",
    "4형식은 <b>동사 뒤에 &lsquo;누구에게&rsquo;(간접목적어) + &lsquo;무엇을&rsquo;(직접목적어)</b> 두 개가 오는 문장이에요. "
    "&lsquo;주다&rsquo;류 동사, 곧 <b>수여동사</b>에 쓰여요. 순서는 <b>사람 먼저, 물건 나중</b>이에요.",
    [("<span class='S'>She</span> <span class='V'>told</span> <span class='O'>us</span> <span class='O'>a story</span>.", "그녀는 우리에게 이야기를 해 줬다."),
     ("<span class='S'>I</span> <span class='V'>bought</span> <span class='O'>him</span> <span class='O'>a gift</span>.", "나는 그에게 선물을 사 줬다."),
     ("<span class='V'>Show</span> <span class='O'>me</span> <span class='O'>the way</span>.", "나에게 길을 알려줘.")],
    [("to를 붙이는 동사", ["give 주다","tell 말하다","send 보내다","show 보여주다","teach 가르치다","lend 빌려주다"]),
     ("for를 붙이는 동사", ["buy 사주다","make 만들어주다","get 가져다주다","cook 요리해주다"]),
     ("of를 붙이는 동사", ["ask 묻다"])],
    "순서를 바꿔 &lsquo;무엇을&rsquo;을 앞으로 보내면(4형식→3형식), 사람 앞에 <b>to·for·of(전치사)</b> 중 하나를 붙여요. "
    "<b>대부분 to</b> · buy·make·get·cook → <b>for</b> · ask → <b>of</b>.",
    "<b>사람 앞에 to·for·of(전치사) 중 무엇을 붙일지 고르기</b>가 가장 많이 나와요! 동사에 맞는 걸 물어봐요. "
    "또 4형식인지 <b>5형식인지 구별</b>(뒷말 두 개가 다른 대상인가?)하는 문제도 나와요.",
    "붙이는 말(전치사) 3그룹 — ① <b>to</b>: give·tell·send·show·teach·lend &nbsp; "
    "② <b>for</b>: buy·make·get·cook &nbsp; ③ <b>of</b>: ask. 순서는 <b>사람 → 물건</b>.",
    """<div class="q">1) &lsquo;무엇을&rsquo;을 앞으로 뺄 때 사람 앞에 붙일 말은?<br>
       &nbsp;&nbsp;① He gave me a book. → a book ( <span class="blank"></span> ) me &nbsp;
       ② I bought him a gift. → a gift ( <span class="blank"></span> ) him &nbsp;
       ③ She asked me a question. → a question ( <span class="blank"></span> ) me</div>""",
    """<p><b>1.</b> ① <b>to</b> (give는 to) &nbsp; ② <b>for</b> (buy는 for) &nbsp; ③ <b>of</b> (ask는 of)</p>""")

S5 = unit(5, "5형식", "누가 + 한다 + 무엇을 + 어떻게", "주어 + 동사 + 목적어 + 보어",
    ["동사 뒤 <b>&lsquo;무엇을&rsquo;(목적어) + &lsquo;어떻게&rsquo;(목적격보어)</b>가 오는 문장을 안다 (그를 = 천재라고)",
     "<b>시키는 동사(사역동사)·보고 듣는 동사(지각동사)</b> 뒤엔 <b>to 없는 동사(동사원형)</b>가 옴을 안다",
     "가장 헷갈리는 <b>4형식과 5형식</b>을 구별한다"],
    dia([("S","누가","We"),("op","+"),("V","한다","call"),("op","+"),("O","무엇을","him"),("op","+"),("C","어떻게","a genius")],
        rel=f'{dot("O")}him(그를) <span class="eq">=</span> {dot("C")}a genius(천재라고) &nbsp;→&nbsp; <b>뒷말이 &lsquo;무엇을&rsquo;을 설명</b>'),
    "5형식은 &lsquo;<b>~을 …하게 / …라고</b>&rsquo;처럼 <b>&lsquo;무엇을&rsquo;이 어떤 상태·행동인지까지</b> 말해요. "
    "이걸 알아야 <b>She made me happy(나를 행복하게)</b>와 <b>She made me a cake(나에게 케이크를 = 4형식)</b>를 헷갈리지 않아요. "
    "특히 <b>시키는 동사 뒤 to 없는 동사</b>(let me go)는 5형식을 모르면 해석·영작이 안 돼서 <b>고등 문법의 핵심</b>이에요.",
    "5형식은 <b>&lsquo;무엇을&rsquo;(목적어) 뒤에 그것을 설명하는 말(목적격보어)</b>이 하나 더 오는 문장이에요. 뒷말이 <b>&lsquo;무엇을&rsquo;과 = 관계</b>가 돼요. "
    "설명하는 말 자리엔 상태말(형용사)·<b>to+동사(to부정사)</b>가 오고, "
    "<b>시키는 동사(사역동사: make·have·let)·보고 듣는 동사(지각동사: see·hear·feel·watch)</b> 뒤엔 <b>to 없는 동사(동사원형)</b>가 와요.",
    [("<span class='S'>She</span> <span class='V'>made</span> <span class='O'>me</span> <span class='C'>happy</span>.", "그녀는 나를 행복하게 했다. (나 = 행복함)"),
     ("<span class='S'>I</span> <span class='V'>want</span> <span class='O'>you</span> <span class='C'>to stay</span>.", "나는 네가 머물기를 원한다. (to+동사 = to부정사)"),
     ("<span class='S'>He</span> <span class='V'>let</span> <span class='O'>me</span> <span class='C'>go</span>.", "그는 나를 가게 해 줬다. (let 뒤 동사원형 go)")],
    [("뒤에 상태말·이름 (형용사·명사)", ["make ~하게 하다","call ~라 부르다","name 이름 짓다","keep ~한 채 두다","find ~라고 느끼다"]),
     ("뒤에 to+동사 (to부정사)", ["want 원하다","ask 부탁하다","tell 시키다","allow 허락하다","expect 기대하다"]),
     ("뒤에 to 없는 동사 (사역·지각동사)", ["make 시키다","have 시키다","let 허락하다","see 보다","hear 듣다","feel 느끼다","watch 보다"])],
    "<b>4형식과 5형식 구별</b> — 뒷말 둘이 &lsquo;누구에게 무엇을&rsquo;(다른 것)이면 4형식, "
    "<b>&lsquo;무엇을&rsquo; = 뒷말(목적격보어)</b>(같은 것)이면 5형식! He made me <u>a cake</u>(4형식) ↔ He made me <u>happy</u>(5형식).",
    "<b>시키는·보는 동사(사역·지각동사) 뒤에 go / to go 중 고르기</b>가 가장 많이 나와요! (let me <b>go</b>○ / to go✗, saw him <b>run</b>○). "
    "반대로 want·tell·ask 뒤엔 <b>to+동사(to부정사)</b>(want you <b>to</b> stay). <b>4형식·5형식 구별</b>도 자주 나와요.",
    "① <b>사역동사 make·have·let + to 없는 동사(동사원형)</b>. ② <b>지각동사 see·hear·feel·watch + 동사원형</b>. "
    "③ <b>want·ask·tell·allow·expect + to+동사(to부정사)</b>. ④ 확인법: <b>&lsquo;무엇을&rsquo; = 뒷말(목적격보어)</b>이면 5형식.",
    """<div class="q">1) &lsquo;무엇을&rsquo;을 설명하는 말에 밑줄. &nbsp;① The news made us sad. &nbsp;② They elected him president.</div>
       <div class="q">2) 알맞은 것에 ○: &nbsp; My mom let me ( <span class="sel">go</span> / to go ) out.</div>
       <div class="q">3) 몇 형식? &nbsp; She found the book easy. → ( <span class="blank"></span> )형식</div>""",
    """<p><b>1.</b> ① sad (우리 = 슬픔) &nbsp; ② president (그 = 회장)</p>
       <p><b>2.</b> go — let(시키는 동사) 뒤엔 to 없는 동사 (to go ✗)</p>
       <p><b>3.</b> 5형식 (그 책 = 쉬움)</p>""")

# ============================================================ 총정리
SUMMARY = f"""
<div class="sec" id="summary">
  {band("총정리", "5형식 한눈에 & 구별하는 법", "복습 + 종합 연습")}
  <div class="h">색으로 보는 5형식</div>
  {dia([("S","누가","Birds"),("op","+"),("V","한다","sing")], rel="1형식 · 누가 + 한다")}
  {dia([("S","누가","She"),("op","+"),("V","이다","is"),("op","+"),("C","어떠하다","a teacher")], rel=f'2형식 · 누가 + 이다 + 어떠하다 ({dot("S")}={dot("C")})')}
  {dia([("S","누가","I"),("op","+"),("V","한다","love"),("op","+"),("O","무엇을","you")], rel="3형식 · 누가 + 한다 + 무엇을")}
  {dia([("S","누가","He"),("op","+"),("V","준다","gave"),("op","+"),("O","누구에게","me"),("op","+"),("O","무엇을|직접목적어","a book")], rel="4형식 · 누가 + 준다 + 누구에게 + 무엇을")}
  {dia([("S","누가","We"),("op","+"),("V","한다","call"),("op","+"),("O","무엇을","him"),("op","+"),("C","어떻게","a genius")], rel=f'5형식 · 누가 + 한다 + 무엇을 + 어떻게 ({dot("O")}={dot("C")})')}

  <div class="h">몇 형식인지 아는 법 — 동사 뒤를 보세요</div>
  <table class="sum">
    <thead><tr><th style="width:44px">순서</th><th>동사 뒤에 …</th><th style="width:70px">→ 형식</th></tr></thead>
    <tbody>
      <tr><td><b>①</b></td><td>아무것도 없다 (꾸미는 말=수식어만)</td><td><b>1형식</b></td></tr>
      <tr><td><b>②</b></td><td>하나 있고 &lsquo;<b>앞말 = 그것</b>&rsquo;로 설명 (보어)</td><td><b>2형식</b></td></tr>
      <tr><td><b>③</b></td><td>하나 있고 &lsquo;<b>무엇을</b>&rsquo; (목적어)</td><td><b>3형식</b></td></tr>
      <tr><td><b>④</b></td><td>둘 있고 &lsquo;<b>누구에게 + 무엇을</b>&rsquo; (목적어 2개)</td><td><b>4형식</b></td></tr>
      <tr><td><b>⑤</b></td><td>둘 있고 &lsquo;<b>무엇을 = 뒷말</b>&rsquo; (목적어 + 목적격보어)</td><td><b>5형식</b></td></tr>
    </tbody>
  </table>
  <div class="tip"><span class="l">가장 헷갈리는 것</span><b>2형식 vs 3형식</b>: 앞말=뒤말이면 2형식, &lsquo;무엇을&rsquo;이면 3형식. &nbsp; <b>4형식 vs 5형식</b>: 뒷말 둘이 다른 것이면 4형식, &lsquo;무엇을&rsquo;=뒷말이면 5형식.</div>

  <div class="h">시험 포인트 총정리 — 이건 꼭 나온다</div>
  <div class="exam"><span class="l">빈출 5선</span>
    ① <b>look·feel(감각동사) 뒤 happy / happily 고르기</b> (형용사 happy○) &nbsp;
    ② <b>enter·discuss(타동사) 뒤 into·about 넣지 않기</b> &nbsp;
    ③ <b>사람 앞에 to / for / of(전치사) 고르기</b> &nbsp;
    ④ <b>make·let·see(사역·지각동사) 뒤 go / to go 고르기</b> (동사원형 go○) &nbsp;
    ⑤ <b>주어진 문장이 몇 형식인지 판단</b> (특히 4 vs 5, 2 vs 3).</div>

  <div class="h">암기 체크리스트 — 다 외웠나요?</div>
  <div class="memo"><span class="l">이것만은 외우기</span>
    □ <b>느낌 말하는 동사(감각동사, 뒤에 형용사)</b>: look·sound·smell·taste·feel &nbsp;
    □ <b>into·about 없이 바로 목적어(타동사)</b>: discuss·marry·enter·reach·resemble·answer &nbsp;
    □ <b>사람 앞에 붙이는 말(전치사)</b>: to(give·tell·send·show·teach·lend) / for(buy·make·get·cook) / of(ask) &nbsp;
    □ <b>시키는 동사(사역동사, 뒤에 동사원형)</b>: make·have·let &nbsp;
    □ <b>보고 듣는 동사(지각동사, 뒤에 동사원형)</b>: see·hear·feel·watch &nbsp;
    □ <b>뒤에 to+동사(to부정사)가 오는 동사</b>: want·ask·tell·allow·expect</div>

  <div class="q-h"><span class="b">종합 연습</span>각 문장은 몇 형식일까요?</div>
  <div class="q">1) The train arrived late. → ( <span class="blank"></span> ) &nbsp;&nbsp; 2) She is a famous singer. → ( <span class="blank"></span> )</div>
  <div class="q">3) I read a book yesterday. → ( <span class="blank"></span> ) &nbsp;&nbsp; 4) He sent me a letter. → ( <span class="blank"></span> )</div>
  <div class="q">5) We named our dog Coco. → ( <span class="blank"></span> ) &nbsp;&nbsp; 6) The flowers smell nice. → ( <span class="blank"></span> )</div>
  <div class="q">7) My mom made me a sandwich. → ( <span class="blank"></span> ) &nbsp;&nbsp; 8) My mom made me happy. → ( <span class="blank"></span> )</div>
  <div class="q">9) They live in London. → ( <span class="blank"></span> ) &nbsp;&nbsp; 10) I want you to be honest. → ( <span class="blank"></span> )</div>
  <div class="ans"><div class="t">정답 &amp; 해설</div>
    <p><b>1.</b> 1형식 &nbsp; <b>2.</b> 2형식(그녀 = 가수) &nbsp; <b>3.</b> 3형식(책을) &nbsp; <b>4.</b> 4형식(나에게 + 편지를) &nbsp; <b>5.</b> 5형식(우리 개 = Coco)</p>
    <p><b>6.</b> 2형식(꽃 = 좋은 냄새) &nbsp; <b>7.</b> 4형식(나에게 + 샌드위치를) &nbsp; <b>8.</b> 5형식(나 = 행복함) &nbsp; <b>9.</b> 1형식 &nbsp; <b>10.</b> 5형식(너 + 정직하기를)</p>
    <p>※ 7·8번 비교: 같은 made라도 &lsquo;나에게 샌드위치를(4형식)&rsquo; vs &lsquo;나를 행복하게(5형식)&rsquo;로 달라져요.</p>
  </div>
</div>
"""


def build():
    html = '<meta charset="utf-8"><style>' + CSS + '</style>' + COVER + TOC + INTRO + S1 + S2 + S3 + S4 + S5 + SUMMARY
    from weasyprint import HTML
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = HTML(string=html).render()
    doc.write_pdf(str(OUT))
    print(f"생성: {OUT.name} ({len(doc.pages)}쪽)")
    return OUT


if __name__ == "__main__":
    build()
