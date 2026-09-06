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
@page { size:A4; margin:11mm 11mm 13mm;
  @bottom-center{content:"ⓒ2026.김은아영어연구소.All rights reserved   ·   " counter(page);
    font-family:"NanumGothic","Malgun Gothic",sans-serif;font-size:8px;color:#9aa0a6;} }
@page cover { margin:0; @bottom-center{content:"";} }
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
.cov-dia{margin-top:26px;display:flex;flex-direction:column;gap:7px;}
.cov-row{display:flex;align-items:center;gap:6px;font-size:11px;}
.cov-row .n{width:40px;font-weight:800;color:#d5f0df;}
.cov-chip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.3);border-radius:7px;padding:3px 9px;font-weight:800;color:#fff;}
.cbox{margin-top:auto;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.28);border-radius:12px;padding:14px 18px;}
.cbox h3{margin:0 0 7px;font-size:13px;color:#fff;} .cbox ul{margin:0;padding-left:16px;}
.cbox li{font-size:11px;color:#f0faf3;margin-bottom:4px;}

/* 섹션 */
.sec{break-before:page;}
.band{background:var(--green-d);color:#fff;border-radius:10px;padding:11px 16px;margin-bottom:13px;display:flex;align-items:baseline;gap:12px;}
.band .no{font-size:19px;font-weight:800;}
.band .tt{font-size:16px;font-weight:800;}
.band .code{font-size:11px;font-weight:700;color:#cdeed9;margin-left:auto;}

/* ===== 핵심: 슬롯 다이어그램 ===== */
.diawrap{border:1.5px solid var(--line);border-radius:12px;padding:13px 14px 11px;margin-bottom:12px;background:#fcfdfc;}
.dia{display:flex;gap:7px;align-items:stretch;}
.slot{flex:1 1 auto;min-width:66px;border-radius:9px;overflow:hidden;border:2px solid #ccc;text-align:center;}
.slot .lab{color:#fff;font-size:9px;font-weight:800;padding:3px 2px;line-height:1.25;}
.slot .lab b{color:#fff;font-size:11px;display:block;}
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
.ans{background:#f6f8f7;border:1px solid var(--line);border-radius:8px;padding:9px 13px;margin-top:8px;}
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
def slot(kind, label, word):
    c = COL[kind]
    return (f'<div class="slot" style="border-color:{c}">'
            f'<div class="lab" style="background:{c}"><b>{label}</b></div>'
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
    <div class="cov-row"><span class="n">1형식</span><span class="cov-chip">주어</span><span class="cov-chip">동사</span></div>
    <div class="cov-row"><span class="n">2형식</span><span class="cov-chip">주어</span><span class="cov-chip">동사</span><span class="cov-chip">보어</span></div>
    <div class="cov-row"><span class="n">3형식</span><span class="cov-chip">주어</span><span class="cov-chip">동사</span><span class="cov-chip">목적어</span></div>
    <div class="cov-row"><span class="n">4형식</span><span class="cov-chip">주어</span><span class="cov-chip">동사</span><span class="cov-chip">간접목적어</span><span class="cov-chip">직접목적어</span></div>
    <div class="cov-row"><span class="n">5형식</span><span class="cov-chip">주어</span><span class="cov-chip">동사</span><span class="cov-chip">목적어</span><span class="cov-chip">목적격보어</span></div>
  </div>
  <div class="cbox"><h3>이 교재는요</h3><ul>
    <li>문장 성분을 <b>색깔 블록</b>으로 보여줘 구조가 한눈에 들어와요.</li>
    <li>형식마다 <b>구조 그림 → 예문 → 대표 동사 → 구별 팁 → 연습</b> 순서.</li>
    <li>가장 헷갈리는 <b>2형식 보어 / 4형식·5형식 구별</b>을 확실히!</li>
  </ul></div>
</div></div>
"""

# ============================================================ 들어가기
INTRO = f"""
<div class="sec">
  {band("들어가기", "문장에도 '형식'이 있다", "왜 5형식?")}
  <div class="concept">영어 문장은 <b>동사</b>가 뼈대를 정해요. 같은 자리라도 동사에 따라 뒤에
  <b>목적어(~을)</b>가 오기도, <b>보어(=설명)</b>가 오기도 하죠. 성분을 <b>색</b>으로 구분하면 구조가 바로 보여요.</div>

  <div class="h">문장 성분 4가지 — 색으로 기억하기</div>
  {dia([("S","주어","누가"),("V","동사","뭐하다"),("O","목적어","~을/를"),("C","보어","= 설명")],
       rel=f'{dot("S")}주어 {dot("V")}동사 {dot("O")}목적어 {dot("C")}보어 &nbsp;·&nbsp; 회색은 <b>수식어(M)</b>=꾸미는 살(형식에서 제외)')}

  <div class="h">5형식 구조를 블록으로</div>
  {dia([("S","주어","Birds"),("op","+"),("V","동사","sing")], rel="① 1형식 — 동사만으로 끝!")}
  {dia([("S","주어","She"),("op","+"),("V","동사","is"),("op","+"),("C","보어","a teacher")], rel=f'② 2형식 — {dot("S")}She <span class="eq">=</span> {dot("C")}a teacher (주어=보어)')}
  {dia([("S","주어","I"),("op","+"),("V","동사","love"),("op","+"),("O","목적어","you")], rel="③ 3형식 — you(~을)를 받음")}
  {dia([("S","주어","He"),("op","+"),("V","동사","gave"),("op","+"),("O","간접목적어","me"),("op","+"),("O","직접목적어","a book")], rel="④ 4형식 — me(~에게) + a book(~을)")}
  {dia([("S","주어","We"),("op","+"),("V","동사","call"),("op","+"),("O","목적어","him"),("op","+"),("C","목적격보어","a genius")], rel=f'⑤ 5형식 — {dot("O")}him <span class="eq">=</span> {dot("C")}a genius (목적어=보어)')}

  <div class="tip"><span class="l">핵심 한 줄</span>보어(C)는 &lsquo;<b>= 관계로 설명</b>&rsquo;, 목적어(O)는 &lsquo;<b>~을/를 받는 대상</b>&rsquo;. 이 둘만 구별하면 끝!</div>

  <div style="break-inside:avoid;">
  <div class="h">그런데 왜 굳이 형식을 배울까?</div>
  <div class="why" style="margin-bottom:0;"><span class="l">이유 하나면 충분해요</span>
    <b>같은 동사라도 형식이 바뀌면 뜻이 완전히 달라지기 때문</b>이에요. 형식을 모르면 해석이 틀려요.
    <div class="cmp"><span class="en">She made me a cake.</span> → <span class="a">4형식</span> · 나<b>에게</b> 케이크<b>를</b> 만들어 줬다</div>
    <div class="cmp"><span class="en">She made me happy.</span> → <span class="a">5형식</span> · 나<b>를</b> 행복하<b>게</b> 만들었다</div>
    <div class="cmp"><span class="en">I found the book.</span> → <span class="a">3형식</span> · 그 책<b>을</b> 찾았다 &nbsp;／&nbsp;
      <span class="en">I found the book easy.</span> → <span class="a">5형식</span> · 그 책<b>이</b> 쉽다<b>고</b> 느꼈다</div>
    이렇게 <b>동사가 문장 구조를 결정</b>해요. 그래서 &lsquo;몇 형식인지&rsquo; 보는 눈이 <b>정확한 해석과 서술형·어법 문제</b>의 열쇠예요.</div>
  </div>
</div>
"""

# ============================================================ 형식 섹션
def section(no, tt, code, flagship, why, concept, ex_rows, verb_groups, tip, exam, memo, quiz, ans):
    return f"""
<div class="sec">
  {band(no, tt, code)}
  {flagship}
  <div class="why"><span class="l">왜 배울까?</span>{why}</div>
  <div class="concept">{concept}</div>
  <div class="h">이렇게 읽어요</div>
  {exlines(ex_rows)}
  <div class="h">이 형식에 잘 쓰는 동사</div>
  {verbs(verb_groups)}
  <div class="tip"><span class="l">✔ 헷갈리지 않기</span>{tip}</div>
  <div class="exam"><span class="l">시험 포인트</span>{exam}</div>
  <div class="memo"><span class="l">암기!</span>{memo}</div>
  <div class="q-h"><span class="b">연습</span>직접 풀어보기</div>
  {quiz}
  <div class="ans"><div class="t">정답 &amp; 해설</div>{ans}</div>
</div>
"""

S1 = section("1형식", "주어 + 동사", "S + V",
    dia([("S","주어","Birds"),("op","+"),("V","동사","sing"),("op",""),("m","","（in the sky）수식어")],
        rel="동사만으로 문장이 완성돼요. 뒤 전치사구는 <b>꾸미는 살(M)</b>이라 빼고 봐요."),
    "문장을 &lsquo;몇 형식&rsquo;으로 보는 건 <b>어디까지가 진짜 뼈대인지</b> 가려내기 위해서예요. "
    "1형식을 알면 <b>The sun rises in the east</b> 같은 문장에서 <b>in the east(수식어)를 지우고</b> "
    "&lsquo;해가 뜬다&rsquo;라는 핵심만 딱 잡을 수 있어요. 긴 문장도 <b>주어·동사부터</b> 찾는 습관이 여기서 시작돼요.",
    "1형식은 <b>주어 + 동사</b>만으로 뜻이 끝나요. 목적어가 필요 없는 <b>완전자동사</b>이고, "
    "「<b>There is/are + 명사</b>」(~이 있다)도 1형식이에요.",
    [("<span class='S'>The sun</span> <span class='V'>rises</span> <span class='M'>in the east</span>.", "해가 (동쪽에서) 뜬다."),
     ("<span class='S'>She</span> <span class='V'>lives</span> <span class='M'>in Seoul</span>.", "그녀는 (서울에) 산다."),
     ("<span class='V'>There is</span> <span class='S'>a book</span> <span class='M'>on the desk</span>.", "(책상 위에) 책이 있다.")],
    [("", ["go","come","run","walk","sleep","live","arrive","happen","appear","rise","exist","fly","cry"])],
    "<b>전치사구</b>(in the east…)는 수식어! 형식을 셀 땐 괄호 치고 빼세요. &lsquo;~을/를&rsquo;로 받는 목적어가 없으면 1형식.",
    "<b>수식어(전치사구·부사)를 지운 뒤 형식을 판단</b>하는 문제가 자주 나와요. &lsquo;There is/are + 명사&rsquo;도 "
    "1형식이라는 걸 <b>꼭</b> 물어봐요. 목적어가 없는데 1형식이 아니라고 착각하지 않기.",
    "① <b>완전자동사</b>(go, come, live, arrive, happen, rise…)는 목적어 없이 끝난다. "
    "② <b>There is/are + 명사 = 1형식</b>. ③ 전치사구·부사는 <b>수식어(M)</b> → 형식 계산에서 제외.",
    """<div class="q">1) S·V를 찾고 수식어는 ( )로 묶으세요. &nbsp;① The baby cried. &nbsp;② We arrived at the station.</div>
       <div class="q">2) 몇 형식? &nbsp; There are many stars in the sky. → ( <span class="blank"></span> )형식</div>""",
    """<p><b>1.</b> ① S=The baby / V=cried &nbsp; ② S=We / V=arrived / (at the station)</p>
       <p><b>2.</b> 1형식 (There are + 명사, in the sky는 수식어)</p>""")

S2 = section("2형식", "주어 + 동사 + 보어", "S + V + C",
    dia([("S","주어","She"),("op","+"),("V","동사","is"),("op","+"),("C","보어","a teacher")],
        rel=f'{dot("S")}She <span class="eq">=</span> {dot("C")}a teacher &nbsp;→&nbsp; <b>주어 = 보어</b> (보어=명사/형용사)'),
    "&lsquo;그녀는 이다&rsquo;만으로는 말이 안 되죠? <b>be동사·become·look</b> 같은 동사는 <b>주어가 무엇/어떠한지</b> "
    "설명해 주는 말이 꼭 필요해요. 그래서 <b>보어(C)</b>를 &lsquo;<b>=</b>&rsquo;로 읽어야 뜻이 통해요. "
    "<b>She looks tired = 그녀는 피곤한 상태다</b>처럼, 2형식을 알면 감각동사를 &lsquo;~하게 보인다/들린다&rsquo;로 정확히 해석해요.",
    "2형식은 <b>주어 + 동사 + 보어(C)</b>. 동사만으로 부족해서 <b>주어를 설명</b>하는 보어가 와요. "
    "<b>주어 = 보어</b> 관계가 성립하고, 보어 자리엔 <b>명사</b>(무엇)나 <b>형용사</b>(어떠하다)가 와요.",
    [("<span class='S'>He</span> <span class='V'>became</span> <span class='C'>famous</span>.", "그는 유명해졌다. (He = famous)"),
     ("<span class='S'>The soup</span> <span class='V'>tastes</span> <span class='C'>good</span>.", "수프는 맛이 좋다. (감각동사)"),
     ("<span class='S'>You</span> <span class='V'>look</span> <span class='C'>tired</span>.", "너 피곤해 보인다. (You = tired)")],
    [("상태·변화", ["be(am/are/is)","become","get","grow","turn","remain","stay"]),
     ("감각동사 (+형용사)", ["look","sound","smell","taste","feel","seem","appear"])],
    "<b>감각동사</b>(look, feel…) 뒤엔 <b>부사가 아니라 형용사</b>! &nbsp;You look <b>happy</b>(○) / happily(✗). &lsquo;주어=보어&rsquo;면 2형식.",
    "<b>감각동사 뒤 형용사 vs 부사</b> 고르기가 단골 문제! (look happy○ / happily✗) "
    "또 <b>주어=보어</b>인지 물어 2형식과 1·3형식을 구별시켜요. become·get·turn(변하다) 뒤 형용사도 자주 나와요.",
    "① <b>감각동사(look·sound·smell·taste·feel) + 형용사</b> — 부사 쓰면 오답! "
    "② 상태·변화 동사: <b>be·become·get·grow·turn·remain·stay</b>. ③ 판별 열쇠: <b>주어 = 보어</b>.",
    """<div class="q">1) 보어에 밑줄. &nbsp;① The leaves turned red. &nbsp;② This cake smells sweet.</div>
       <div class="q">2) 알맞은 것에 ○: &nbsp; She looks ( <span class="sel">happy</span> / happily ).</div>""",
    """<p><b>1.</b> ① red (The leaves = red) &nbsp; ② sweet (This cake = sweet)</p>
       <p><b>2.</b> happy — 감각동사 look 뒤엔 형용사 (happily ✗)</p>""")

S3 = section("3형식", "주어 + 동사 + 목적어", "S + V + O",
    dia([("S","주어","I"),("op","+"),("V","동사","love"),("op","+"),("O","목적어","you")],
        rel=f'{dot("O")}you = 동작을 받는 대상 (<b>~을/를</b>)'),
    "우리가 쓰는 문장의 <b>대부분이 3형식</b>이에요. &lsquo;누가 무엇을 ~한다&rsquo;가 가장 기본이니까요. "
    "3형식을 알면 목적어 자리에 <b>단어뿐 아니라 동명사·to부정사·that절</b>(덩어리)도 올 수 있다는 걸 이해하게 돼요. "
    "그래야 <b>I enjoy playing soccer</b>처럼 긴 목적어도 &lsquo;~하는 것을&rsquo;로 묶어 해석해요.",
    "3형식은 <b>주어 + 동사 + 목적어(O)</b>. 동작을 <b>받는 대상(~을/를)</b>이 목적어이고, 이런 동사를 <b>타동사</b>라 해요. "
    "목적어 자리엔 명사·대명사·<b>동명사·to부정사·that절</b>도 올 수 있어요.",
    [("<span class='S'>She</span> <span class='V'>reads</span> <span class='O'>books</span>.", "그녀는 책을 읽는다."),
     ("<span class='S'>We</span> <span class='V'>enjoy</span> <span class='O'>playing soccer</span>.", "우리는 축구하는 것을 즐긴다. (동명사)"),
     ("<span class='S'>He</span> <span class='V'>said</span> <span class='O'>that he was tired</span>.", "그는 피곤하다고 말했다. (that절)")],
    [("", ["love","like","have","read","make","eat","want","know","meet","buy","use","find"])],
    "&lsquo;~을/를&rsquo;이 있으면 대개 3형식. 단, <b>discuss·marry·enter·reach·resemble·answer</b>는 전치사 없이 목적어를 바로! (discuss <b>about</b> it ✗)",
    "<b>전치사가 필요 없는 타동사</b>에 전치사를 붙이는 오답을 자주 물어요 "
    "(enter <b>into</b>✗, discuss <b>about</b>✗). 목적어로 쓴 <b>동명사/to부정사</b>를 찾는 문제도 나와요.",
    "① <b>전치사 없이 바로 목적어</b>: <u>discuss · marry · enter · reach · resemble · answer</u> (앞글자 &lsquo;<b>디마엔리리앤</b>&rsquo;). "
    "② 목적어 자리 = 명사·대명사·<b>동명사·to부정사·that절</b>.",
    """<div class="q">1) 목적어에 밑줄. &nbsp;① I finished my homework. &nbsp;② They enjoy watching movies.</div>
       <div class="q">2) 틀린 곳 고치기: &nbsp; He entered <span class="sel">into</span> the room. → <span class="blank"></span></div>""",
    """<p><b>1.</b> ① my homework &nbsp; ② watching movies (동명사)</p>
       <p><b>2.</b> into 삭제 → He entered the room. (enter는 타동사)</p>""")

S4 = section("4형식", "주어 + 동사 + 간접목적어 + 직접목적어", "S + V + IO + DO",
    dia([("S","주어","He"),("op","+"),("V","동사","gave"),("op","+"),("O","간접목적어","me"),("op","+"),("O","직접목적어","a book")],
        rel=f'{dot("O")}me (<b>~에게</b>) &nbsp;+&nbsp; {dot("O")}a book (<b>~을</b>) &nbsp;→&nbsp; 목적어 <b>둘</b> (서로 다른 대상)'),
    "&lsquo;주다·말해주다·보내주다&rsquo;처럼 <b>누구에게 무엇을</b> 해 주는 동작은 목적어가 <b>두 개</b> 필요해요. "
    "4형식을 알면 <b>He gave me a book</b>을 &lsquo;나에게 / 책을&rsquo; 두 덩어리로 정확히 끊어 읽고, "
    "이걸 <b>3형식(gave a book to me)으로 바꾸는 시험 문제</b>까지 풀 수 있어요.",
    "4형식은 <b>주어 + 동사 + 간접목적어(IO, ~에게) + 직접목적어(DO, ~을)</b>. &lsquo;주다&rsquo;류 <b>수여동사</b>에 쓰이고 "
    "목적어가 <b>사람(에게) + 사물(을)</b> 두 개예요. 순서는 <b>사람 먼저, 사물 나중</b>.",
    [("<span class='S'>She</span> <span class='V'>told</span> <span class='O'>us</span> <span class='O'>a story</span>.", "그녀는 우리에게 이야기를 해 줬다."),
     ("<span class='S'>I</span> <span class='V'>bought</span> <span class='O'>him</span> <span class='O'>a gift</span>.", "나는 그에게 선물을 사 줬다."),
     ("<span class='V'>Show</span> <span class='O'>me</span> <span class='O'>the way</span>.", "나에게 길을 알려줘.")],
    [("to로 바꿈", ["give","tell","send","show","teach","lend","offer"]),
     ("for로 바꿈", ["buy","make","get","cook","find"]),
     ("of로 바꿈", ["ask"])],
    "4형식 → <b>3형식</b> 전환: 사물을 앞으로, 사람 앞에 전치사! <b>대부분 to</b> · buy·make·get·cook → <b>for</b> · ask → <b>of</b>.",
    "<b>4형식 → 3형식 전환 시 전치사(to/for/of) 고르기</b>가 최다 빈출! 동사에 맞는 전치사를 물어봐요. "
    "또 4형식 문장을 <b>5형식과 구별</b>(두 목적어가 다른 대상인가?)하는 문제도 나와요.",
    "3형식 전환 전치사 3그룹 — ① <b>to</b>: give·tell·send·show·teach·lend·offer &nbsp; "
    "② <b>for</b>: buy·make·get·cook·find &nbsp; ③ <b>of</b>: ask. 순서는 <b>사람(에게) → 사물(을)</b>.",
    """<div class="q">1) 3형식으로 바꿀 때 전치사는?<br>
       &nbsp;&nbsp;① He gave me a book. → a book ( <span class="blank"></span> ) me &nbsp;
       ② I bought him a gift. → a gift ( <span class="blank"></span> ) him &nbsp;
       ③ She asked me a question. → a question ( <span class="blank"></span> ) me</div>""",
    """<p><b>1.</b> ① <b>to</b> (give→to) &nbsp; ② <b>for</b> (buy→for) &nbsp; ③ <b>of</b> (ask→of)</p>""")

S5 = section("5형식", "주어 + 동사 + 목적어 + 목적격보어", "S + V + O + OC",
    dia([("S","주어","We"),("op","+"),("V","동사","call"),("op","+"),("O","목적어","him"),("op","+"),("C","목적격보어","a genius")],
        rel=f'{dot("O")}him <span class="eq">=</span> {dot("C")}a genius &nbsp;→&nbsp; <b>목적어 = 보어</b> (같은 대상)'),
    "5형식은 &lsquo;<b>~을 …하게/…라고</b>&rsquo;처럼 <b>목적어의 상태·행동까지</b> 말해요. "
    "이걸 알아야 <b>She made me happy(나를 행복하게)</b>와 <b>She made me a cake(나에게 케이크를=4형식)</b>를 헷갈리지 않아요. "
    "특히 <b>사역·지각동사 뒤 동사원형</b>(let me go)은 5형식을 모르면 절대 해석·작문이 안 돼서 <b>고등 문법의 핵심</b>이에요.",
    "5형식은 <b>주어 + 동사 + 목적어(O) + 목적격보어(OC)</b>. 목적격보어가 <b>목적어를 설명</b>해서 <b>목적어 = 보어</b>가 돼요. "
    "보어 자리엔 명사·형용사·<b>to부정사</b>, <b>사역(make·have·let)·지각(see·hear·feel·watch)</b> 동사면 <b>동사원형</b>이 와요.",
    [("<span class='S'>She</span> <span class='V'>made</span> <span class='O'>me</span> <span class='C'>happy</span>.", "그녀는 나를 행복하게 했다. (me = happy)"),
     ("<span class='S'>I</span> <span class='V'>want</span> <span class='O'>you</span> <span class='C'>to stay</span>.", "나는 네가 머물기를 원한다. (to부정사)"),
     ("<span class='S'>He</span> <span class='V'>let</span> <span class='O'>me</span> <span class='C'>go</span>.", "그는 나를 가게 해 줬다. (사역→원형)")],
    [("+ 명사/형용사", ["make","call","name","keep","find","leave"]),
     ("+ O + to부정사", ["want","ask","tell","allow","expect"]),
     ("사역·지각 (+원형)", ["make","have","let","see","hear","feel","watch"])],
    "<b>4형식 vs 5형식</b> — 두 말이 &lsquo;~에게 ~을&rsquo;(다른 대상)이면 4형식, <b>O=보어</b>(같은 대상)면 5형식! "
    "He made me <u>a cake</u>(4형식) ↔ He made me <u>happy</u>(5형식).",
    "<b>사역·지각동사 뒤 동사원형</b> 고르기가 최다 빈출! (let me <b>go</b>○ / to go✗, saw him <b>run</b>○). "
    "want·tell·ask 뒤엔 반대로 <b>to부정사</b>(want you <b>to</b> stay). <b>4형식 vs 5형식</b> 구별도 자주 나와요.",
    "① <b>사역 make·have·let + 동사원형</b>. ② <b>지각 see·hear·feel·watch + 원형/-ing</b>. "
    "③ <b>want·ask·tell·allow·expect + O + to부정사</b>. ④ 판별 열쇠: <b>목적어 = 목적격보어</b>.",
    """<div class="q">1) 목적격보어에 밑줄. &nbsp;① The news made us sad. &nbsp;② They elected him president.</div>
       <div class="q">2) 알맞은 것에 ○: &nbsp; My mom let me ( <span class="sel">go</span> / to go ) out.</div>
       <div class="q">3) 몇 형식? &nbsp; She found the book easy. → ( <span class="blank"></span> )형식</div>""",
    """<p><b>1.</b> ① sad (us=sad) &nbsp; ② president (him=president)</p>
       <p><b>2.</b> go — 사역동사 let 뒤엔 동사원형 (to go ✗)</p>
       <p><b>3.</b> 5형식 (the book = easy)</p>""")

# ============================================================ 총정리
SUMMARY = f"""
<div class="sec">
  {band("총정리", "5형식 한눈에 & 판별법", "복습 + 종합 연습")}
  <div class="h">색으로 보는 5형식</div>
  {dia([("S","주어","Birds"),("op","+"),("V","동사","sing")], rel="1형식 · S + V")}
  {dia([("S","주어","She"),("op","+"),("V","동사","is"),("op","+"),("C","보어","a teacher")], rel=f'2형식 · S + V + C ({dot("S")}={dot("C")})')}
  {dia([("S","주어","I"),("op","+"),("V","동사","love"),("op","+"),("O","목적어","you")], rel="3형식 · S + V + O")}
  {dia([("S","주어","He"),("op","+"),("V","동사","gave"),("op","+"),("O","간접목적어","me"),("op","+"),("O","직접목적어","a book")], rel="4형식 · S + V + IO + DO")}
  {dia([("S","주어","We"),("op","+"),("V","동사","call"),("op","+"),("O","목적어","him"),("op","+"),("C","목적격보어","a genius")], rel=f'5형식 · S + V + O + OC ({dot("O")}={dot("C")})')}

  <div class="h">형식 판별 순서 — 동사 뒤를 보세요</div>
  <table class="sum">
    <thead><tr><th style="width:44px">순서</th><th>동사 뒤에 …</th><th style="width:70px">→ 형식</th></tr></thead>
    <tbody>
      <tr><td><b>①</b></td><td>아무것도 없다 (수식어만)</td><td><b>1형식</b></td></tr>
      <tr><td><b>②</b></td><td>하나 있고 &lsquo;<b>주어 = 그것</b>&rsquo;</td><td><b>2형식</b> (보어)</td></tr>
      <tr><td><b>③</b></td><td>하나 있고 &lsquo;<b>~을/를</b>&rsquo;</td><td><b>3형식</b> (목적어)</td></tr>
      <tr><td><b>④</b></td><td>둘 있고 &lsquo;<b>~에게 ~을</b>&rsquo; (다른 대상)</td><td><b>4형식</b></td></tr>
      <tr><td><b>⑤</b></td><td>둘 있고 &lsquo;<b>O = 보어</b>&rsquo; (같은 대상)</td><td><b>5형식</b></td></tr>
    </tbody>
  </table>
  <div class="tip"><span class="l">가장 헷갈리는 것</span><b>2 vs 3</b>: 주어=뒤말이면 2형식, ~을/를이면 3형식. &nbsp; <b>4 vs 5</b>: 두 목적어가 다르면 4형식, O=보어면 5형식.</div>

  <div class="h">시험 포인트 총정리 — 이건 꼭 나온다</div>
  <div class="exam"><span class="l">빈출 5선</span>
    ① <b>감각동사 + 형용사</b> (look happy○ / happily✗) &nbsp;
    ② <b>enter·discuss·marry…에 전치사 금지</b> &nbsp;
    ③ <b>4형식→3형식 전치사 to/for/of</b> 고르기 &nbsp;
    ④ <b>사역·지각동사 + 동사원형</b> (let me go○ / to go✗) &nbsp;
    ⑤ <b>주어진 문장의 형식 판별</b> (특히 4 vs 5, 2 vs 3).</div>

  <div class="h">암기 체크리스트 — 다 외웠나요?</div>
  <div class="memo"><span class="l">이것만은 외우기</span>
    □ <b>2형식 감각동사</b>: look·sound·smell·taste·feel (+형용사) &nbsp;
    □ <b>3형식 전치사 없는 타동사</b>: discuss·marry·enter·reach·resemble·answer &nbsp;
    □ <b>4형식 전환 전치사</b>: to(give·tell·send·show·teach·lend) / for(buy·make·get·cook) / of(ask) &nbsp;
    □ <b>5형식 사역동사</b>: make·have·let (+원형) &nbsp;
    □ <b>5형식 지각동사</b>: see·hear·feel·watch (+원형/-ing) &nbsp;
    □ <b>5형식 to부정사동사</b>: want·ask·tell·allow·expect (+ O + to부정사)</div>

  <div class="q-h"><span class="b">종합 연습</span>각 문장은 몇 형식일까요?</div>
  <div class="q">1) The train arrived late. → ( <span class="blank"></span> ) &nbsp;&nbsp; 2) She is a famous singer. → ( <span class="blank"></span> )</div>
  <div class="q">3) I read a book yesterday. → ( <span class="blank"></span> ) &nbsp;&nbsp; 4) He sent me a letter. → ( <span class="blank"></span> )</div>
  <div class="q">5) We named our dog Coco. → ( <span class="blank"></span> ) &nbsp;&nbsp; 6) The flowers smell nice. → ( <span class="blank"></span> )</div>
  <div class="q">7) My mom made me a sandwich. → ( <span class="blank"></span> ) &nbsp;&nbsp; 8) My mom made me happy. → ( <span class="blank"></span> )</div>
  <div class="q">9) They live in London. → ( <span class="blank"></span> ) &nbsp;&nbsp; 10) I want you to be honest. → ( <span class="blank"></span> )</div>
  <div class="ans"><div class="t">정답 &amp; 해설</div>
    <p><b>1.</b> 1형식 &nbsp; <b>2.</b> 2형식(She=a singer) &nbsp; <b>3.</b> 3형식 &nbsp; <b>4.</b> 4형식(me에게 a letter를) &nbsp; <b>5.</b> 5형식(our dog=Coco)</p>
    <p><b>6.</b> 2형식(감각동사+형용사) &nbsp; <b>7.</b> 4형식(me에게 a sandwich를) &nbsp; <b>8.</b> 5형식(me=happy) &nbsp; <b>9.</b> 1형식 &nbsp; <b>10.</b> 5형식(you+to be honest)</p>
    <p>※ 7·8번 비교: 같은 made라도 &lsquo;나에게 샌드위치를(4형식)&rsquo; vs &lsquo;나를 행복하게(5형식)&rsquo;로 형식이 달라져요.</p>
  </div>
</div>
"""


def build():
    html = '<meta charset="utf-8"><style>' + CSS + '</style>' + COVER + INTRO + S1 + S2 + S3 + S4 + S5 + SUMMARY
    from weasyprint import HTML
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = HTML(string=html).render()
    doc.write_pdf(str(OUT))
    print(f"생성: {OUT.name} ({len(doc.pages)}쪽)")
    return OUT


if __name__ == "__main__":
    build()
