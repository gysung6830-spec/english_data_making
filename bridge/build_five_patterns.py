# -*- coding: utf-8 -*-
"""문장의 5형식(1~5형식) 완전 정복 — 교재 1권 생성.

    python -m bridge.build_five_patterns  →  output/문장의5형식_교재.pdf
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "문장의5형식_교재.pdf"

CSS = """
@page { size:A4; margin:12mm 12mm 14mm;
  @bottom-center{content:"ⓒ2026.김은아영어연구소.All rights reserved   ·   " counter(page);
    font-family:"NanumGothic","Malgun Gothic",sans-serif;font-size:8px;color:#9aa0a6;} }
@page cover { margin:0; @bottom-center{content:"";} }
*{box-sizing:border-box;}
body{font-family:"NanumGothic","Nanum Gothic","Malgun Gothic",sans-serif;color:#23272e;font-size:10.6px;line-height:1.6;margin:0;}
:root{--green:#2f9e5f;--green-d:#1f7a48;--green-bg:#eef7f1;--teal:#2f877e;--amber:#cf8a2a;
  --purple:#6a54b3;--purple-bg:#f1eefa;--red:#cd5049;--muted:#6b7280;--line:#e2e6ea;}
b{color:#12283f;}

/* 표지 */
.cover{page:cover;break-after:page;height:297mm;position:relative;
  background:linear-gradient(160deg,#2f9e5f 0%,#248a4f 55%,#1b6d3d 100%);color:#fff;}
.cover-in{position:absolute;inset:0;padding:42mm 24mm;display:flex;flex-direction:column;}
.ck{font-size:12px;font-weight:700;letter-spacing:3px;color:#d5f0df;margin-bottom:14px;}
.ct{font-size:40px;font-weight:800;line-height:1.2;letter-spacing:-1px;}
.cs{font-size:15px;font-weight:600;color:#e4f6ea;margin-top:12px;}
.ctag{display:inline-block;margin-top:22px;background:#fff;color:var(--green-d);font-size:14px;font-weight:800;padding:7px 18px;border-radius:24px;}
.cbox{margin-top:auto;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.28);border-radius:12px;padding:16px 20px;}
.cbox h3{margin:0 0 9px;font-size:14px;color:#fff;} .cbox ul{margin:0;padding-left:16px;}
.cbox li{font-size:11.5px;color:#f0faf3;margin-bottom:5px;}

/* 섹션 공통 */
.sec{break-before:page;}
.band{background:var(--green-d);color:#fff;border-radius:9px;padding:10px 15px;margin-bottom:12px;}
.band .no{font-size:12px;font-weight:800;letter-spacing:1px;color:#bfe6cf;}
.band .tt{font-size:20px;font-weight:800;margin-top:1px;}
.band .code{font-size:12px;font-weight:700;color:#d5f0df;margin-top:2px;}
.goal{background:#fdf6ea;border:1.5px solid #ecd9b6;border-radius:9px;padding:8px 13px;margin-bottom:12px;font-size:11px;font-weight:800;color:#7a4a12;}
.goal .l{display:inline-block;background:var(--amber);color:#fff;font-size:9px;font-weight:800;padding:2px 8px;border-radius:9px;margin-right:8px;}
.h{font-size:12.5px;font-weight:800;color:var(--green-d);border-bottom:2px solid var(--amber);padding-bottom:2px;margin:12px 0 7px;}
.p{margin:0 0 8px;} .p b{background:#eef7f1;padding:0 2px;border-radius:3px;}
.form{background:#faf9fe;border:1px solid #d6cdf0;border-left:4px solid var(--purple);border-radius:0 7px 7px 0;
  padding:8px 13px;margin:6px 0 10px;font-size:12px;font-weight:800;color:#4a3a94;text-align:center;letter-spacing:.3px;}

/* 예문 표 */
table.ex{width:100%;border-collapse:collapse;margin:4px 0 10px;}
table.ex th{background:var(--teal);color:#fff;font-size:9.5px;font-weight:700;padding:4px 8px;text-align:left;}
table.ex td{border-bottom:1px solid var(--line);padding:5px 8px;vertical-align:top;font-size:10.3px;}
table.ex tbody tr:nth-child(even) td{background:#f4faf9;}
.ex .en{font-weight:700;color:#12283f;width:34%;}
.ex .st{width:30%;color:#4a3a94;font-size:9.7px;}
.ex .ko{}
.S{color:#1f7a48;font-weight:800;} .V{color:#c85f2a;font-weight:800;} .O{color:#445fb0;font-weight:800;}
.C{color:#6a54b3;font-weight:800;} .M{color:#9aa0a6;font-weight:700;}

/* 동사 리스트 / 팁 */
.verbs{background:var(--green-bg);border-radius:7px;padding:7px 12px;font-size:10px;margin:2px 0 10px;}
.verbs b{color:var(--green-d);}
.tip{background:#fdf6ea;border-radius:7px;padding:7px 12px;font-size:10px;color:#7a4a12;margin:2px 0 10px;}
.tip .l{font-weight:800;color:var(--amber);margin-right:5px;}
.note{background:#f2f0f6;border-radius:7px;padding:7px 12px;font-size:10px;margin:2px 0 10px;}

/* 연습문제 */
.q-h{font-weight:800;font-size:11.5px;color:var(--amber);margin:12px 0 6px;}
.q-h .b{display:inline-block;background:var(--amber);color:#fff;font-size:9px;font-weight:800;padding:1px 8px;border-radius:8px;margin-right:6px;}
.q{margin:0 0 8px;line-height:1.9;} .blank{display:inline-block;min-width:64px;border-bottom:1px solid #333;text-align:center;}
.q .sel{font-weight:700;}
.ans{background:#f6f8f7;border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin-top:8px;}
.ans .t{display:inline-block;background:#111827;color:#fff;font-size:10.5px;font-weight:800;padding:2px 10px;border-radius:5px;margin-bottom:6px;}
.ans p{margin:3px 0;font-size:9.7px;line-height:1.7;} .ans b{color:var(--green-d);}

/* 총정리 표 */
table.sum{width:100%;border-collapse:collapse;margin:6px 0 12px;}
table.sum th{background:var(--green-d);color:#fff;font-size:10px;font-weight:700;padding:6px 8px;text-align:left;}
table.sum td{border:1px solid var(--line);padding:6px 8px;font-size:10px;vertical-align:top;}
table.sum tbody tr:nth-child(even) td{background:var(--green-bg);}
.flow{list-style:none;padding:0;margin:6px 0 12px;}
.flow li{background:var(--green-bg);border-left:4px solid var(--green);border-radius:0 6px 6px 0;padding:6px 12px;margin-bottom:5px;font-size:10.3px;}
.flow li b{color:var(--green-d);}
"""

def band(no, tt, code):
    return f'<div class="band"><div class="no">{no}</div><div class="tt">{tt}</div><div class="code">{code}</div></div>'

def extable(rows):
    body = "".join(f'<tr><td class="en">{r[0]}</td><td class="st">{r[1]}</td><td class="ko">{r[2]}</td></tr>' for r in rows)
    return f'<table class="ex"><thead><tr><th>영어 문장</th><th>문장 성분</th><th>해석</th></tr></thead><tbody>{body}</tbody></table>'


# ============================================================ 표지
COVER = """
<div class="cover"><div class="cover-in">
  <div class="ck">한 권으로 끝내는 영어 문장 구조</div>
  <div class="ct">문장의 5형식<br>완전 정복</div>
  <div class="cs">1형식부터 5형식까지, 동사가 문장을 결정한다</div>
  <div class="ctag">중·고 기초 문법 · 내신 대비</div>
  <div class="cbox"><h3>이 교재는요</h3><ul>
    <li>영어 문장을 <b>구조(형식)</b>로 읽는 힘을 길러 줘요.</li>
    <li>형식마다 <b>개념 → 형태 공식 → 예문 → 대표 동사 → 구별 팁 → 연습문제</b> 순서로 배워요.</li>
    <li>가장 헷갈리는 <b>2형식 보어 / 4형식·5형식 구별</b>을 확실히 잡아요.</li>
    <li>마지막 <b>총정리 비교표 + 형식 판별 연습</b>으로 마무리해요.</li>
  </ul></div>
</div></div>
"""

# ============================================================ 들어가기
INTRO = f"""
<div class="sec">
  {band("들어가기", "문장에도 '형식'이 있다", "왜 5형식을 배울까?")}
  <p class="p">영어 문장은 아무렇게나 나열된 게 아니라, <b>정해진 뼈대(형식)</b> 위에 세워져요.
  그 뼈대를 결정하는 건 바로 <b>동사</b>예요. 같은 자리라도 동사가 무엇이냐에 따라 뒤에
  <b>목적어</b>가 오기도, <b>보어</b>가 오기도 해요. 형식을 알면 <b>긴 문장도 구조로 빠르게</b> 읽혀요.</p>

  <div class="h">먼저 알아 둘 4가지 성분</div>
  <table class="sum">
    <thead><tr><th style="width:70px">성분</th><th>하는 일</th><th>예</th></tr></thead>
    <tbody>
      <tr><td><b>주어 S</b></td><td>누가/무엇이 (동작·상태의 주인)</td><td class="en"><span class="S">Birds</span> sing.</td></tr>
      <tr><td><b>동사 V</b></td><td>~하다 / ~이다 (문장의 엔진)</td><td class="en">Birds <span class="V">sing</span>.</td></tr>
      <tr><td><b>목적어 O</b></td><td>~을/를 (동작을 받는 대상)</td><td class="en">I love <span class="O">you</span>.</td></tr>
      <tr><td><b>보어 C</b></td><td>주어·목적어를 <b>설명</b> (= 관계)</td><td class="en">She is <span class="C">a teacher</span>.</td></tr>
    </tbody>
  </table>
  <div class="note">※ 시간·장소를 나타내는 <b>수식어(M)</b>(in Seoul, every day…)는 형식을 셀 때 <b>빼고</b> 봐요. 형식의 뼈대가 아니라 &lsquo;살&rsquo;이에요.</div>

  <div class="h">5형식 한눈에</div>
  <ul class="flow">
    <li><b>1형식</b> 주어 + 동사 &nbsp;→&nbsp; <span class="en">Birds <span class="V">sing</span>.</span></li>
    <li><b>2형식</b> 주어 + 동사 + <b>보어</b> (주어=보어) &nbsp;→&nbsp; <span class="en">She is <span class="C">a teacher</span>.</span></li>
    <li><b>3형식</b> 주어 + 동사 + <b>목적어</b> &nbsp;→&nbsp; <span class="en">I love <span class="O">you</span>.</span></li>
    <li><b>4형식</b> 주어 + 동사 + <b>간접목적어 + 직접목적어</b> &nbsp;→&nbsp; <span class="en">He gave <span class="O">me</span> <span class="O">a book</span>.</span></li>
    <li><b>5형식</b> 주어 + 동사 + <b>목적어 + 목적격보어</b> (목적어=보어) &nbsp;→&nbsp; <span class="en">We call <span class="O">him</span> <span class="C">a genius</span>.</span></li>
  </ul>
  <div class="tip"><span class="l">핵심</span>보어(C)는 &lsquo;<b>=</b> 관계로 설명&rsquo;, 목적어(O)는 &lsquo;<b>~을/를</b> 받는 대상&rsquo;. 이 둘만 구별하면 5형식이 다 풀려요.</div>
</div>
"""

# ============================================================ 각 형식
def section(no, tt, code, goal, concept, form, ex_rows, verbs, tip, quiz, ans):
    return f"""
<div class="sec">
  {band(no, tt, code)}
  <div class="goal"><span class="l">한 줄 요약</span>{goal}</div>
  <div class="h">개념</div>
  <p class="p">{concept}</p>
  <div class="form">{form}</div>
  <div class="h">예문으로 보기</div>
  {extable(ex_rows)}
  <div class="h">이 형식에 잘 쓰는 동사</div>
  <div class="verbs">{verbs}</div>
  <div class="tip"><span class="l">✔ 헷갈리지 않기</span>{tip}</div>
  <div class="q-h"><span class="b">연습</span>직접 풀어보기</div>
  {quiz}
  <div class="ans"><div class="t">정답 &amp; 해설</div>{ans}</div>
</div>
"""

S1 = section("1형식", "주어 + 동사", "S + V (완전자동사)",
    "동사만으로 뜻이 완성되는 문장. &lsquo;누가 ~한다.&rsquo;",
    "1형식은 <b>주어(S)</b>와 <b>동사(V)</b>만으로 뜻이 완성돼요. 뒤에 시간·장소 같은 "
    "<b>수식어(M)</b>가 붙어도 형식에는 넣지 않아요. 이때 동사는 목적어가 필요 없는 <b>완전자동사</b>예요. "
    "「There is/are + 명사」(~이 있다)도 1형식이에요.",
    "S + V &nbsp;( + 수식어 M )",
    [("<span class='S'>Birds</span> <span class='V'>sing</span>.", "S + V", "새들이 노래한다."),
     ("<span class='S'>The sun</span> <span class='V'>rises</span> <span class='M'>in the east</span>.", "S + V + (M)", "해가 동쪽에서 뜬다."),
     ("<span class='S'>She</span> <span class='V'>lives</span> <span class='M'>in Seoul</span>.", "S + V + (M)", "그녀는 서울에 산다."),
     ("<span class='V'>There is</span> <span class='S'>a book</span> <span class='M'>on the desk</span>.", "There + V + S + (M)", "책상 위에 책이 (한 권) 있다.")],
    "go, come, run, walk, sleep, live, arrive, happen, appear, rise, exist, work, cry, fly …",
    "<b>전치사구</b>(in the east, on the desk)는 <b>수식어(M)</b>예요. 형식을 셀 땐 괄호 치고 빼세요. &lsquo;~을/를&rsquo;로 받는 목적어가 없으면 1형식!",
    """<div class="q">1) 다음에서 <b>S와 V</b>를 찾고, 수식어는 ( )로 묶으세요.<br>
       &nbsp;&nbsp;① The baby cried. &nbsp;② Time flies fast. &nbsp;③ We arrived at the station.</div>
       <div class="q">2) 이 문장은 몇 형식? &nbsp; There are many stars in the sky. → ( <span class="blank"></span> )형식</div>""",
    """<p><b>1.</b> ① S=The baby / V=cried &nbsp; ② S=Time / V=flies / (fast) &nbsp; ③ S=We / V=arrived / (at the station)</p>
       <p><b>2.</b> 1형식 (There are + 명사 = ~이 있다, in the sky는 수식어)</p>""")

S2 = section("2형식", "주어 + 동사 + 보어", "S + V + C (주어 = 보어)",
    "주어를 설명하는 <b>보어</b>가 필요. &lsquo;주어 = 보어.&rsquo;",
    "2형식은 <b>주어(S) + 동사(V) + 주격보어(C)</b>예요. 동사만으로는 부족해서, "
    "<b>주어가 무엇인지·어떠한지</b> 설명하는 <b>보어</b>가 와요. 이때 <b>주어 = 보어</b> 관계가 성립해요. "
    "보어 자리에는 <b>명사</b>(무엇)나 <b>형용사</b>(어떠하다)가 오고, 이런 동사를 <b>불완전자동사</b>라고 해요.",
    "S + V + C(명사 / 형용사) &nbsp;&nbsp;→&nbsp;&nbsp; S = C",
    [("<span class='S'>She</span> <span class='V'>is</span> <span class='C'>a teacher</span>.", "S + V + C(명사)", "그녀는 선생님이다. (She = a teacher)"),
     ("<span class='S'>He</span> <span class='V'>became</span> <span class='C'>famous</span>.", "S + V + C(형용사)", "그는 유명해졌다. (He = famous)"),
     ("<span class='S'>The soup</span> <span class='V'>tastes</span> <span class='C'>good</span>.", "감각동사 + C(형용사)", "그 수프는 맛이 좋다."),
     ("<span class='S'>You</span> <span class='V'>look</span> <span class='C'>tired</span>.", "감각동사 + C(형용사)", "너 피곤해 보인다.")],
    "be(am/are/is), become, get, grow, turn(~해지다), remain, stay &nbsp;·&nbsp; "
    "<b>감각동사</b> look, sound, smell, taste, feel &nbsp;·&nbsp; seem, appear(~인 것 같다)",
    "<b>감각동사</b>(look, feel, sound…) 뒤에는 <b>부사가 아니라 형용사</b>! &nbsp;You look <b>happy</b>(○) / happily(✗). "
    "&lsquo;주어=보어&rsquo;가 성립하면 보어(2형식)예요.",
    """<div class="q">1) 보어에 <u>밑줄</u>을 긋고 &lsquo;주어=보어&rsquo;를 확인하세요.<br>
       &nbsp;&nbsp;① The leaves turned red. &nbsp;② This cake smells sweet.</div>
       <div class="q">2) 괄호에서 알맞은 것: &nbsp; She looks ( <span class="sel">happy</span> / happily ). &nbsp;→ 알맞은 것에 ○</div>""",
    """<p><b>1.</b> ① 보어 red (The leaves = red, 잎이 빨갛게 되었다) &nbsp; ② 보어 sweet (This cake = sweet)</p>
       <p><b>2.</b> happy &nbsp;— 감각동사 look 뒤에는 <b>형용사</b>. (happily는 부사라 ✗)</p>""")

S3 = section("3형식", "주어 + 동사 + 목적어", "S + V + O (완전타동사)",
    "동작을 받는 <b>목적어(~을/를)</b>가 필요.",
    "3형식은 <b>주어(S) + 동사(V) + 목적어(O)</b>예요. 동사의 동작을 <b>받는 대상(~을/를)</b>이 목적어이고, "
    "이런 동사를 <b>완전타동사</b>라고 해요. 목적어 자리에는 <b>명사·대명사·동명사·to부정사·that절</b> 등이 올 수 있어요.",
    "S + V + O (~을/를)",
    [("<span class='S'>I</span> <span class='V'>love</span> <span class='O'>you</span>.", "S + V + O(대명사)", "나는 너를 사랑한다."),
     ("<span class='S'>She</span> <span class='V'>reads</span> <span class='O'>books</span>.", "S + V + O(명사)", "그녀는 책을 읽는다."),
     ("<span class='S'>We</span> <span class='V'>enjoy</span> <span class='O'>playing soccer</span>.", "S + V + O(동명사)", "우리는 축구하는 것을 즐긴다."),
     ("<span class='S'>He</span> <span class='V'>said</span> <span class='O'>that he was tired</span>.", "S + V + O(that절)", "그는 피곤하다고 말했다.")],
    "love, like, have, read, make, eat, want, know, meet, buy, use, find, bring, take …",
    "우리말 &lsquo;~을/를&rsquo;이 있으면 대개 3형식. 단, <b>자동사를 타동사로 착각 주의!</b> "
    "discuss / marry / enter / reach / resemble / answer 는 <b>전치사 없이</b> 목적어를 바로 써요. "
    "(discuss <b>about</b> it ✗ → discuss it ○)",
    """<div class="q">1) 목적어에 <u>밑줄</u>을 그으세요.<br>
       &nbsp;&nbsp;① I finished my homework. &nbsp;② They enjoy watching movies.</div>
       <div class="q">2) 틀린 곳을 고치세요: &nbsp; He entered <span class="sel">into</span> the room. → <span class="blank"></span></div>""",
    """<p><b>1.</b> ① my homework &nbsp; ② watching movies (동명사 목적어)</p>
       <p><b>2.</b> into 삭제 → <b>He entered the room.</b> (enter는 타동사, 전치사 없이 목적어)</p>""")

S4 = section("4형식", "주어 + 동사 + 간접목적어 + 직접목적어", "S + V + IO + DO (수여동사)",
    "&lsquo;~에게(IO) ~을(DO)&rsquo; — 목적어가 <b>둘</b>.",
    "4형식은 <b>주어 + 동사 + 간접목적어(IO, ~에게) + 직접목적어(DO, ~을)</b>예요. "
    "&lsquo;<b>주다</b>&rsquo; 종류의 동사(<b>수여동사</b>)에 쓰이고, 목적어가 <b>사람(에게) + 사물(을)</b> 두 개 와요. "
    "순서는 <b>IO(사람) 먼저, DO(사물) 나중</b>이에요.",
    "S + V + IO(~에게) + DO(~을)",
    [("<span class='S'>He</span> <span class='V'>gave</span> <span class='O'>me</span> <span class='O'>a book</span>.", "V + IO + DO", "그는 나에게 책을 주었다."),
     ("<span class='S'>She</span> <span class='V'>told</span> <span class='O'>us</span> <span class='O'>a story</span>.", "V + IO + DO", "그녀는 우리에게 이야기를 해 줬다."),
     ("<span class='S'>I</span> <span class='V'>bought</span> <span class='O'>him</span> <span class='O'>a gift</span>.", "V + IO + DO", "나는 그에게 선물을 사 줬다."),
     ("<span class='S'>Can you</span> <span class='V'>show</span> <span class='O'>me</span> <span class='O'>the way</span>?", "V + IO + DO", "나에게 길을 알려줄래?")],
    "give, tell, send, show, teach, lend, offer, pass, bring &nbsp;·&nbsp; buy, make, get, cook, find(사물을 위해) &nbsp;·&nbsp; ask(질문을)",
    "4형식은 <b>3형식으로 바꿀 수 있어요</b>: IO를 DO 뒤로 보내고 앞에 전치사! 전치사는 동사에 따라 달라요 — "
    "<b>대부분 to</b>(give/tell/send/show/teach/lend) · <b>buy·make·get·cook → for</b> · <b>ask → of</b>.",
    """<div class="q">1) 4형식을 <b>3형식</b>으로 바꾸고 전치사를 고르세요.<br>
       &nbsp;&nbsp;① He gave me a book. → He gave a book ( <span class="blank"></span> ) me.<br>
       &nbsp;&nbsp;② I bought him a gift. → I bought a gift ( <span class="blank"></span> ) him.<br>
       &nbsp;&nbsp;③ She asked me a question. → She asked a question ( <span class="blank"></span> ) me.</div>""",
    """<p><b>1.</b> ① <b>to</b> (give→to) &nbsp; ② <b>for</b> (buy→for) &nbsp; ③ <b>of</b> (ask→of)</p>
       <p>※ &lsquo;주는 방향&rsquo;이 상대에게 향하면 to, &lsquo;누구를 위해&rsquo; 해 주면 for, 질문을 묻는 ask는 of.</p>""")

S5 = section("5형식", "주어 + 동사 + 목적어 + 목적격보어", "S + V + O + OC (목적어 = 보어)",
    "목적어를 <b>설명</b>하는 보어가 필요. &lsquo;목적어 = 보어.&rsquo;",
    "5형식은 <b>주어 + 동사 + 목적어(O) + 목적격보어(OC)</b>예요. 목적격보어는 <b>목적어의 상태·정체를 설명</b>해서 "
    "<b>목적어 = 보어</b> 관계가 성립해요. 보어 자리에는 <b>명사·형용사·to부정사</b>가 오고, "
    "<b>사역동사(make·have·let)·지각동사(see·hear·feel·watch)</b> 뒤에서는 <b>원형부정사(동사원형)</b>가 와요.",
    "S + V + O + OC(명사 / 형용사 / to부정사 / 원형) &nbsp;→&nbsp; O = OC",
    [("<span class='S'>We</span> <span class='V'>call</span> <span class='O'>him</span> <span class='C'>a genius</span>.", "V + O + OC(명사)", "우리는 그를 천재라고 부른다. (him = a genius)"),
     ("<span class='S'>She</span> <span class='V'>made</span> <span class='O'>me</span> <span class='C'>happy</span>.", "V + O + OC(형용사)", "그녀는 나를 행복하게 했다. (me = happy)"),
     ("<span class='S'>I</span> <span class='V'>want</span> <span class='O'>you</span> <span class='C'>to stay</span>.", "V + O + OC(to부정사)", "나는 네가 머물기를 원한다."),
     ("<span class='S'>He</span> <span class='V'>let</span> <span class='O'>me</span> <span class='C'>go</span>.", "사역동사 + O + 원형", "그는 나를 가게 해 줬다."),
     ("<span class='S'>I</span> <span class='V'>saw</span> <span class='O'>her</span> <span class='C'>cross</span> the street.", "지각동사 + O + 원형", "나는 그녀가 길을 건너는 것을 봤다.")],
    "make, call, name, keep, find, leave(+명사/형용사) &nbsp;·&nbsp; want, ask, tell, allow, expect(+O+to부정사) &nbsp;·&nbsp; "
    "<b>사역</b> make/have/let(+O+원형) &nbsp;·&nbsp; <b>지각</b> see/hear/feel/watch(+O+원형/-ing)",
    "<b>4형식 vs 5형식</b> — 두 말이 &lsquo;~에게 ~을&rsquo;(서로 다른 대상)이면 <b>4형식</b>, "
    "&lsquo;<b>O = 보어</b>&rsquo;(같은 대상)이면 <b>5형식</b>! &nbsp;He made me <u>a cake</u>(나에게 케이크를=4형식) ↔ He made me <u>happy</u>(나=행복=5형식).",
    """<div class="q">1) 목적격보어에 <u>밑줄</u>을 긋고 &lsquo;목적어=보어&rsquo;를 확인하세요.<br>
       &nbsp;&nbsp;① The news made us sad. &nbsp;② They elected him president.</div>
       <div class="q">2) 괄호에서 알맞은 것: &nbsp; My mom let me ( <span class="sel">go</span> / to go ) out. &nbsp;→ ○</div>
       <div class="q">3) 이 문장은 4형식? 5형식? &nbsp; She found the book easy. → ( <span class="blank"></span> )형식</div>""",
    """<p><b>1.</b> ① sad (us = sad) &nbsp; ② president (him = president)</p>
       <p><b>2.</b> go &nbsp;— 사역동사 let 뒤에는 <b>동사원형</b>(to go ✗)</p>
       <p><b>3.</b> 5형식 &nbsp;— the book = easy (목적어=보어). &lsquo;그 책이 쉽다는 걸 알았다&rsquo;</p>""")

# ============================================================ 총정리
SUMMARY = """
<div class="sec">
  <div class="band"><div class="no">총정리</div><div class="tt">5형식 한눈에 & 형식 판별법</div><div class="code">복습 + 종합 연습</div></div>
  <div class="h">한눈에 비교표</div>
  <table class="sum">
    <thead><tr><th style="width:60px">형식</th><th style="width:150px">구성</th><th>핵심</th><th>예문</th></tr></thead>
    <tbody>
      <tr><td><b>1형식</b></td><td>S + V</td><td>동사만으로 완결 (+수식어)</td><td class="en">Birds <span class="V">sing</span>.</td></tr>
      <tr><td><b>2형식</b></td><td>S + V + C</td><td><b>주어 = 보어</b> (명사/형용사)</td><td class="en">She is <span class="C">a teacher</span>.</td></tr>
      <tr><td><b>3형식</b></td><td>S + V + O</td><td>목적어 <b>~을/를</b></td><td class="en">I love <span class="O">you</span>.</td></tr>
      <tr><td><b>4형식</b></td><td>S + V + IO + DO</td><td><b>~에게 ~을</b> (목적어 둘, 서로 다름)</td><td class="en">He gave <span class="O">me</span> <span class="O">a book</span>.</td></tr>
      <tr><td><b>5형식</b></td><td>S + V + O + OC</td><td><b>목적어 = 보어</b></td><td class="en">We call <span class="O">him</span> <span class="C">a genius</span>.</td></tr>
    </tbody>
  </table>

  <div class="h">형식 판별 순서 (동사 뒤를 보세요)</div>
  <ul class="flow">
    <li><b>① 동사 뒤에 아무것도 없다</b>(수식어만) &nbsp;→&nbsp; <b>1형식</b></li>
    <li><b>② 하나 있고, &lsquo;주어 = 그것&rsquo;</b>이 성립 &nbsp;→&nbsp; <b>2형식</b> (보어)</li>
    <li><b>③ 하나 있고, &lsquo;~을/를&rsquo;</b>로 받음 &nbsp;→&nbsp; <b>3형식</b> (목적어)</li>
    <li><b>④ 둘 있고, &lsquo;~에게 ~을&rsquo;</b>(서로 다른 대상) &nbsp;→&nbsp; <b>4형식</b></li>
    <li><b>⑤ 둘 있고, &lsquo;O = 보어&rsquo;</b>(같은 대상) &nbsp;→&nbsp; <b>5형식</b></li>
  </ul>
  <div class="tip"><span class="l">가장 헷갈리는 것</span>
    <b>2형식 vs 3형식</b>: 주어=뒤말이면 2형식(보어), ~을/를이면 3형식(목적어). &nbsp;
    <b>4형식 vs 5형식</b>: 두 목적어가 다른 대상이면 4형식, O=보어면 5형식.</div>

  <div class="q-h"><span class="b">종합 연습</span>각 문장은 몇 형식일까요?</div>
  <div class="q">1) The train arrived late. → ( <span class="blank"></span> )</div>
  <div class="q">2) She is a famous singer. → ( <span class="blank"></span> )</div>
  <div class="q">3) I read a book yesterday. → ( <span class="blank"></span> )</div>
  <div class="q">4) He sent me a letter. → ( <span class="blank"></span> )</div>
  <div class="q">5) We named our dog Coco. → ( <span class="blank"></span> )</div>
  <div class="q">6) The flowers smell nice. → ( <span class="blank"></span> )</div>
  <div class="q">7) My mom made me a sandwich. → ( <span class="blank"></span> )</div>
  <div class="q">8) My mom made me happy. → ( <span class="blank"></span> )</div>
  <div class="q">9) They live in London. → ( <span class="blank"></span> )</div>
  <div class="q">10) I want you to be honest. → ( <span class="blank"></span> )</div>

  <div class="ans"><div class="t">정답 &amp; 해설</div>
    <p><b>1.</b> 1형식 (arrived, late는 수식어) &nbsp; <b>2.</b> 2형식 (She=a singer) &nbsp; <b>3.</b> 3형식 (a book을) &nbsp;
       <b>4.</b> 4형식 (me에게 a letter를) &nbsp; <b>5.</b> 5형식 (our dog=Coco)</p>
    <p><b>6.</b> 2형식 (감각동사 smell + 형용사, flowers=nice) &nbsp; <b>7.</b> 4형식 (me에게 a sandwich를) &nbsp;
       <b>8.</b> 5형식 (me=happy) &nbsp; <b>9.</b> 1형식 (in London은 수식어) &nbsp; <b>10.</b> 5형식 (you+to be honest)</p>
    <p>※ 7번과 8번을 비교하세요. 같은 made라도 &lsquo;나에게 샌드위치를(4형식)&rsquo; vs &lsquo;나를 행복하게(5형식)&rsquo;로 형식이 달라져요.</p>
  </div>
</div>
"""


def build():
    html = ('<meta charset="utf-8"><style>' + CSS + '</style>'
            + COVER + INTRO + S1 + S2 + S3 + S4 + S5 + SUMMARY)
    from weasyprint import HTML
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = HTML(string=html).render()
    doc.write_pdf(str(OUT))
    print(f"생성: {OUT.name} ({len(doc.pages)}쪽)")
    return OUT


if __name__ == "__main__":
    build()
