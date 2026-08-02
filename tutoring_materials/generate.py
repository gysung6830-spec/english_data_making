# -*- coding: utf-8 -*-
"""
1과(Lesson 1) 숙제/테스트 PDF 생성기 · 은아쌤 손글씨판 (WeasyPrint).
    python tutoring_materials/generate.py  →  output/*.pdf

설계
  · 은아쌤이 옆에서 말해주는 말투 (AI 티 X)
  · 지문 요약(무슨 내용) + 지칭 찾기(it·they·this가 뭘 가리키나)
  · 단어: 같은 10개를 3가지 유형으로 반복 + 누적 복습 확대
  · 문법: 예문 보며 스스로 규칙 발견 → 은아쌤 정리
  · 문장: 생각하며 외우기(빈칸 사다리) — 그냥 베끼기 금지
  · 정답 별지 분리
"""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import weasyprint

import content_lesson1 as L1

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT.parent / "templates" / "fonts"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)


def _b64(name):
    return base64.b64encode((FONT_DIR / name).read_bytes()).decode()


FONT_R = _b64("NanumSquareRoundR.woff")
FONT_B = _b64("NanumSquareRoundB.woff")

INK = "#243b53"; ACCENT = "#2a9d8f"; ACCENT2 = "#e76f51"
SOFT = "#f2f7f6"; LINE = "#d7e3e1"; WARM = "#fff7f2"; SKY = "#eef6fb"

CSS = f"""
@font-face {{ font-family:'NSR'; font-weight:400; src:url(data:font/woff;base64,{FONT_R}) format('woff'); }}
@font-face {{ font-family:'NSR'; font-weight:800; src:url(data:font/woff;base64,{FONT_B}) format('woff'); }}
@page {{ size:A4; margin:12mm 12mm 13mm 12mm;
  @bottom-center {{ content:"{L1.COPYRIGHT}  ·  " counter(page) " / " counter(pages);
    font-family:'NSR'; font-size:8.3px; color:#9fb3ae; }} }}
* {{ box-sizing:border-box; }}
body {{ font-family:'NSR',sans-serif; color:{INK}; font-size:11px; line-height:1.5; margin:0; }}
b,strong {{ font-weight:800; }}
.en {{ font-weight:800; letter-spacing:.2px; }}

.head {{ border:2px solid {ACCENT}; border-radius:12px; overflow:hidden; margin-bottom:8px; page-break-inside:avoid; }}
.head .top {{ background:{ACCENT}; color:#fff; padding:6px 13px; display:flex; justify-content:space-between; align-items:center; }}
.head .top .badge {{ font-weight:800; font-size:13px; }}
.head .top .src {{ font-size:8.5px; opacity:.92; text-align:right; }}
.head .body {{ padding:8px 13px 9px; }}
.head .title {{ font-weight:800; font-size:15.5px; }}
.head .title .k {{ color:{ACCENT}; }}
.head .part {{ font-size:9px; color:#7d918c; margin-top:1px; }}
/* 오늘의 문법 — 눈에 확 띄는 배너 */
.gbanner {{ display:flex; align-items:center; gap:12px; border:2.5px solid {ACCENT2};
  border-radius:12px; background:{WARM}; padding:9px 13px; margin:9px 0 3px; page-break-inside:avoid; }}
.gbanner .lab {{ flex:0 0 auto; background:{ACCENT2}; color:#fff; font-weight:800; font-size:10px;
  padding:5px 11px; border-radius:9px; text-align:center; line-height:1.35; }}
.gbanner .gt {{ font-size:15px; font-weight:800; color:{INK}; }}
.gbanner .gd {{ font-size:9.6px; color:#9a7060; margin-top:2px; }}
.gbanner .gd b {{ color:{ACCENT2}; }}

/* 은아쌤 말풍선 */
.saem {{ position:relative; background:{WARM}; border:1.5px solid #f3d3c4; border-radius:12px;
  padding:7px 11px 7px 46px; margin:8px 0; font-size:10.2px; color:#6b4a3d; line-height:1.55; page-break-inside:avoid; }}
.saem .tag {{ position:absolute; left:9px; top:8px; width:30px; height:30px; border-radius:50%;
  background:{ACCENT2}; color:#fff; font-weight:800; font-size:9px; display:flex; align-items:center; justify-content:center; text-align:center; line-height:1.1; }}
.saem b {{ color:{ACCENT2}; }}
.saem.rule {{ background:{SKY}; border-color:#cfe3f0; color:#2c4a5e; }}
.saem.rule .tag {{ background:{ACCENT}; }}
.saem.rule b {{ color:{ACCENT}; }}

.summary {{ background:{SOFT}; border-left:4px solid {ACCENT}; border-radius:6px; padding:7px 11px; margin:8px 0; font-size:10.4px; line-height:1.6; page-break-inside:avoid; }}
.summary .st {{ font-weight:800; color:{ACCENT}; font-size:10px; margin-bottom:2px; }}

.sec {{ margin-top:11px; page-break-inside:avoid; }}
.sec>.h {{ display:flex; align-items:center; gap:7px; margin-bottom:5px; flex-wrap:wrap; }}
.sec>.h .n {{ display:inline-flex; width:19px; height:19px; border-radius:50%; background:{ACCENT}; color:#fff; font-weight:800; font-size:10.5px; align-items:center; justify-content:center; flex:0 0 auto; }}
.sec>.h .t {{ font-weight:800; font-size:12px; }}
.sec>.h .tip {{ font-size:8.8px; color:#93a7a2; font-weight:400; }}
.sec>.h .rep {{ background:{ACCENT2}; color:#fff; font-size:8px; font-weight:800; padding:1px 7px; border-radius:20px; }}
.subt {{ font-weight:800; font-size:10px; color:{ACCENT}; margin:7px 0 3px; }}
.subt .badge {{ background:{ACCENT}; color:#fff; border-radius:5px; padding:1px 6px; font-size:8.5px; margin-right:4px; }}

table {{ border-collapse:collapse; width:100%; }}
.vtab td,.vtab th {{ border:1px solid {LINE}; padding:4px 6px; vertical-align:middle; }}
.vtab th {{ background:{SOFT}; font-weight:800; font-size:9.2px; color:#5b6f6b; }}
.vtab td.num {{ width:20px; text-align:center; color:#9fb3ae; font-size:9px; }}
.vtab td.w {{ width:104px; }}
.vtab td.k {{ width:128px; font-size:10px; }}
.writeline {{ border-bottom:1.3px dotted #b9c9c5; display:inline-block; min-width:70px; height:14px; }}
.wl-full {{ border-bottom:1.3px dotted #b9c9c5; display:block; height:16px; margin-top:4px; }}

ol.q {{ margin:0; padding-left:19px; }}
ol.q li {{ margin:4px 0; }}
.blank {{ display:inline-block; min-width:82px; border-bottom:1.5px solid {ACCENT}; height:13px; }}
.blank.sm {{ min-width:52px; }}
.hint {{ color:{ACCENT2}; font-size:9px; font-weight:800; }}
.wordbank {{ background:{SOFT}; border:1px solid {LINE}; border-radius:8px; padding:5px 10px; margin:4px 0 7px; font-weight:800; color:{ACCENT}; font-size:10.2px; }}
.wordbank .lab {{ color:#93a7a2; margin-right:6px; }}
.spell {{ font-weight:800; letter-spacing:2px; }}

.exline {{ font-size:10.5px; margin:2px 0; padding-left:6px; border-left:2px solid {LINE}; }}
.exline b {{ color:{ACCENT2}; }}

/* 지칭 */
.ref {{ border:1px solid {LINE}; border-radius:8px; padding:6px 10px; margin:5px 0; page-break-inside:avoid; }}
.ref .rs {{ font-size:10.3px; }}
.ref .rk {{ font-size:8.8px; color:#93a7a2; margin:1px 0 3px; }}
.ref .rq {{ font-size:10px; }}
.ref .rq .p {{ color:{ACCENT2}; font-weight:800; }}

/* 문장 외우기 사다리 */
.ladder {{ border:1px solid {LINE}; border-radius:9px; padding:8px 11px; margin:6px 0; page-break-inside:avoid; }}
.ladder .u {{ font-size:10.4px; }}
.ladder .u .ko {{ color:#7d918c; font-size:9px; }}
.ladder .lv {{ margin-top:5px; font-size:10px; }}
.ladder .lv .lb {{ display:inline-block; background:{SOFT}; color:{ACCENT}; font-weight:800; border-radius:5px; padding:1px 6px; font-size:8.3px; margin-right:5px; }}
.ladder .sk {{ font-weight:800; letter-spacing:1px; color:{INK}; }}

/* 정답 별지 */
.answers {{ page-break-before:always; }}
.ansrow {{ border:1px solid #f3d3c4; background:{WARM}; border-radius:8px; padding:6px 10px; margin-bottom:6px; page-break-inside:avoid; }}
.ansrow .d {{ font-weight:800; color:{ACCENT2}; font-size:10px; margin-bottom:2px; }}
.ansrow .b {{ font-size:9px; color:#7a5c50; line-height:1.55; }}
.ansrow .b b {{ color:{ACCENT2}; }}

.note {{ font-size:8.8px; color:#93a7a2; margin-top:3px; }}
.pagebreak {{ page-break-before:always; }}
.tearline {{ border-top:1.5px dashed {ACCENT2}; text-align:center; margin:14px 0 10px; }}
.tearline span {{ background:#fff; color:{ACCENT2}; font-weight:800; font-size:9px; padding:0 8px; position:relative; top:-8px; }}

.cover {{ text-align:center; padding-top:44px; }}
.cover .kie {{ display:inline-block; border:2px solid {ACCENT}; color:{ACCENT}; font-weight:800; padding:4px 14px; border-radius:20px; font-size:12px; }}
.cover h1 {{ font-size:26px; margin:16px 0 4px; }}
.cover .sub {{ font-size:12px; color:{ACCENT2}; font-weight:800; }}
.cover .src {{ font-size:10.5px; color:#7d918c; margin-top:5px; }}
.cover .list {{ display:inline-block; text-align:left; margin-top:18px; background:{SOFT}; border:1px solid {LINE}; border-radius:12px; padding:13px 22px; font-size:10.5px; line-height:1.85; }}
.cover .list b {{ color:{ACCENT}; }}
.cover .tip {{ margin-top:16px; font-size:9.8px; color:#7d918c; line-height:1.7; }}

.examtop {{ display:flex; justify-content:space-between; align-items:flex-end; border-bottom:2px solid {ACCENT}; padding-bottom:6px; margin-bottom:9px; }}
.examtop .nm {{ font-size:10px; color:#5b6f6b; }}
.examtop .nm .u {{ display:inline-block; min-width:110px; border-bottom:1.3px solid #b9c9c5; }}
.examtop .score {{ text-align:center; border:2px solid {ACCENT2}; border-radius:9px; padding:3px 12px; }}
.examtop .score .s1 {{ font-size:8px; color:{ACCENT2}; font-weight:800; }}
.examtop .score .s2 {{ font-size:14px; font-weight:800; }}

.plan {{ width:100%; border-collapse:collapse; }}
.plan td,.plan th {{ border:1px solid {LINE}; padding:5px 6px; vertical-align:top; font-size:8.7px; }}
.plan th {{ background:{ACCENT}; color:#fff; font-weight:800; font-size:9.2px; text-align:center; }}
.plan .wk {{ background:{SOFT}; font-weight:800; color:{ACCENT}; text-align:center; width:56px; font-size:9px; vertical-align:middle; }}
.plan .day .dh {{ font-weight:800; color:{INK}; font-size:9px; }}
.plan .day .gm {{ color:{ACCENT2}; font-weight:800; font-size:8.2px; }}
.plan .day .tk {{ color:#5b6f6b; font-size:8.2px; margin-top:1px; }}
.plan .soon {{ color:#9fb3ae; }}
.legend {{ font-size:9px; color:#5b6f6b; margin-top:8px; line-height:1.7; }}
.box {{ background:{SOFT}; border:1px solid {LINE}; border-radius:10px; padding:10px 13px; margin-top:10px; }}
.box .bt {{ font-weight:800; color:{ACCENT}; font-size:11px; margin-bottom:4px; }}
.chip {{ display:inline-block; background:#fff; border:1px solid {LINE}; border-radius:20px; padding:2px 9px; margin:2px 3px 0 0; font-size:9px; font-weight:800; color:{INK}; }}
"""


def esc(s): return html.escape(str(s))


def bold(s):
    """**x** 또는 <b>x</b> 모두 굵게. 그 외 태그는 이스케이프."""
    s = esc(s)
    s = s.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def spell_hint(word):
    out = []
    for i, ch in enumerate(word):
        if ch == " ":
            out.append("&nbsp;&nbsp;")
        elif i == 0 or word[i - 1] == " ":
            out.append(esc(ch))
        else:
            out.append("_")
    return " ".join(out)


def skeleton(sentence):
    """문장을 '첫 글자 + 밑줄'로 (문장 외우기 2단계)."""
    toks = sentence.split(" ")
    out = []
    for t in toks:
        m = re.match(r"^([A-Za-z']+)(.*)$", t)
        if not m:
            out.append(esc(t)); continue
        w, tail = m.group(1), m.group(2)
        sk = esc(w[0]) + " " + " ".join("_" for _ in w[1:]) if len(w) > 1 else esc(w)
        out.append(f"<span class='sk'>{sk}</span>{esc(tail)}")
    return " ".join(out)


def blank_keys(sentence, day_words):
    """지문 문장에서 핵심 단어(그날 단어 or 긴 단어) 몇 개를 빈칸으로 (1단계)."""
    stems = set()
    for en, _ in day_words:
        for part in en.lower().split():
            stems.add(part)
    toks = sentence.split(" ")
    blanked = 0
    out = []
    for t in toks:
        core = re.sub(r"[^A-Za-z']", "", t).lower()
        is_key = core in stems or (len(core) >= 6 and blanked < 2)
        if is_key and blanked < 3 and core:
            tail = re.sub(r"^[A-Za-z']+", "", t)
            out.append("<span class='blank sm'></span>" + esc(tail))
            blanked += 1
        else:
            out.append(esc(t))
    if blanked == 0 and len(toks) > 2:  # 최소 1개는 빈칸
        toks2 = out[:]
        # 가장 긴 단어 빈칸
        longest_i = max(range(len(toks)), key=lambda i: len(re.sub(r"[^A-Za-z]", "", toks[i])))
        tail = re.sub(r"^[A-Za-z']+", "", toks[longest_i])
        toks2[longest_i] = "<span class='blank sm'></span>" + esc(tail)
        out = toks2
    return " ".join(out)


# ── 누적 복습 (확대 12개, 양방향) ────────────────────────────
def cumulative_review(day_idx):
    if day_idx <= 1:
        return []
    picks = []
    prev = L1.DAYS[day_idx - 2]["words"]           # 어제 전부(10) 중 6
    picks += [(en, ko, "e2k") for en, ko in prev[:3]]
    picks += [(en, ko, "k2e") for en, ko in prev[3:6]]
    if day_idx >= 3:
        d2 = L1.DAYS[day_idx - 3]["words"]         # 그제 3
        picks += [(d2[0][0], d2[0][1], "e2k"), (d2[4][0], d2[4][1], "k2e"), (d2[7][0], d2[7][1], "e2k")]
    if day_idx >= 5:
        old = L1.DAYS[(day_idx - 5) % (day_idx - 1)]["words"]  # 오래된 것 회전 3
        picks += [(old[1][0], old[1][1], "k2e"), (old[5][0], old[5][1], "e2k"), (old[8][0], old[8][1], "k2e")]
    # 중복 제거
    seen, out = set(), []
    for en, ko, dr in picks:
        if en not in seen:
            seen.add(en); out.append((en, ko, dr))
    return out


# ── 하루치 학생용 ────────────────────────────────────────────
def render_day_student(d):
    idx = d["day"]
    P = []
    # 헤더
    P.append(f"""
    <div class="head">
      <div class="top"><span class="badge">{idx}일차 · {esc(d['weekday'])}요일 숙제</span>
        <span class="src">{esc(L1.SOURCE)}<br>{esc(d['part'])}</span></div>
      <div class="body">
        <div class="title"><span class="k">{esc(d['title_en'])}</span> — {esc(d['title_ko'])}</div>
      </div>
    </div>""")
    # 오늘의 문법 배너 (눈에 확 띄게)
    P.append(f"""
    <div class="gbanner">
      <div class="lab">🎯 오늘의<br>문법</div>
      <div>
        <div class="gt">{esc(d['goal_title'])}</div>
        <div class="gd">{bold(d['gnote'])}</div>
      </div>
    </div>""")
    # 은아쌤 오프닝
    P.append(f"""<div class="saem"><span class="tag">{esc(L1.TEACHER)}</span>{bold(d['open'])}</div>""")
    # 지문 내용
    P.append(f"""<div class="summary"><div class="st">📖 오늘 지문, 무슨 내용이냐면</div>{bold(d['summary'])}</div>""")

    n = 0
    # 1) 누적 복습 (확대)
    rev = cumulative_review(idx)
    if rev:
        n += 1
        rows = ""
        for en, ko, dr in rev:
            if dr == "e2k":
                rows += (f"<tr><td class='num'>·</td><td class='w'><span class='en'>{esc(en)}</span></td>"
                         f"<td class='k' style='color:#9fb3ae'>뜻?</td><td><span class='writeline' style='min-width:120px'></span></td></tr>")
            else:
                rows += (f"<tr><td class='num'>·</td><td class='w' style='color:#9fb3ae'>영어?</td>"
                         f"<td class='k'>{esc(ko)}</td><td><span class='writeline' style='min-width:120px'></span></td></tr>")
        P.append(f"""
        <div class="sec">
          <div class="h"><span class="n">{n}</span><span class="t">지난 단어 다시보기</span>
            <span class="rep">반복 {len(rev)}개</span><span class="tip">영어면 뜻을, 뜻이면 영어를 쓰기 — 기억 안 나면 넘어가도 돼</span></div>
          <table class="vtab">{rows}</table>
        </div>""")

    # 2) 오늘 단어 3가지 유형
    n += 1
    # 유형1: 3번 쓰기
    r1 = ""
    for i, (en, ko) in enumerate(d["words"], 1):
        r1 += (f"<tr><td class='num'>{i}</td><td class='w'><span class='en'>{esc(en)}</span></td><td class='k'>{esc(ko)}</td>"
               f"<td><span class='writeline'></span></td><td><span class='writeline'></span></td><td><span class='writeline'></span></td></tr>")
    # 유형2: 뜻 보고 영어 (첫 글자)
    r2 = "".join(f"<li>{esc(ko)} → <span class='spell'>{spell_hint(en)}</span></li>" for en, ko in d["words"])
    # 유형3: 영어 보고 뜻 (순서 섞어)
    shuffled = d["words"][1::2] + d["words"][0::2]
    r3 = "".join(f"<li><span class='en'>{esc(en)}</span> → <span class='writeline' style='min-width:96px'></span></li>" for en, ko in shuffled)
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">오늘의 단어 10개 · 3가지로 익히기</span>
        <span class="tip">같은 단어를 방법을 바꿔 세 번! 이게 진짜 암기법이야</span></div>
      <div class="subt"><span class="badge">유형 ①</span> 소리 내어 읽으며 3번 쓰기</div>
      <table class="vtab"><tr><th class="num">#</th><th>영어</th><th>뜻</th><th>쓰기①</th><th>쓰기②</th><th>쓰기③</th></tr>{r1}</table>
      <div class="subt"><span class="badge">유형 ②</span> 뜻만 보고 영어 쓰기 <span style="font-weight:400;color:#93a7a2;font-size:8.5px;">(첫 글자 힌트)</span></div>
      <ol class="q" style="columns:2; column-gap:24px;">{r2}</ol>
      <div class="subt"><span class="badge">유형 ③</span> 영어만 보고 뜻 쓰기 <span style="font-weight:400;color:#93a7a2;font-size:8.5px;">(순서를 섞었어)</span></div>
      <ol class="q" style="columns:2; column-gap:24px;">{r3}</ol>
    </div>""")

    # 3) 문법 스스로 발견
    n += 1
    ex = "".join(f"<div class='exline'>{bold(e)}</div>" for e in d["discovery"]["examples"])
    prac = "".join(f"<li>{esc(q)}</li>" for q, _ in d["practice"])
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">문법, 스스로 찾아보기</span>
        <span class="rep">{esc(d['goal_title'].split(':')[0].split('(')[0].strip())}</span>
        <span class="tip">규칙을 외우지 말고, 문장을 보고 직접 발견해봐</span></div>
      <div style="font-size:9.3px;color:#7d918c;margin-bottom:2px;">▸ 아래 문장에서 굵은 부분을 잘 봐:</div>
      {ex}
      <div style="margin-top:6px;font-size:10.2px;"><b style="color:{ACCENT2};">❓ {bold(d['discovery']['ask'])}</b></div>
      <div style="margin:3px 0;">내가 찾은 답 → <span class="writeline" style="min-width:70%"></span></div>
      <div class="saem rule"><span class="tag">{esc(L1.TEACHER)}</span><b style="color:{ACCENT};">정리!</b> {bold(d['discovery']['rule'])}</div>
      <div style="font-size:9.3px;color:#7d918c;margin:4px 0 2px;">▸ 이제 직접 골라보자 (동그라미):</div>
      <ol class="q">{prac}</ol>
    </div>""")

    # 4) 지칭 찾기
    n += 1
    ri = ""
    for sent, ko, pron, ans in d["refs"]:
        ri += (f"<div class='ref'><div class='rs'>{esc(sent)}</div><div class='rk'>{esc(ko)}</div>"
               f"<div class='rq'><span class='p'>{esc(pron)}</span> 는(은) 무엇을 가리킬까? → <span class='writeline' style='min-width:55%'></span></div></div>")
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">이게 뭘 가리킬까? (지칭 찾기)</span>
        <span class="tip">it·they·this 같은 말이 가리키는 걸 찾으면 독해가 확 쉬워져</span></div>
      {ri}
    </div>""")

    # 5) 문장 외우기 사다리
    n += 1
    li = ""
    for full, chunk, ko in d["memorize"]:
        li += f"""
        <div class="ladder">
          <div class="u"><span class="en">{esc(chunk)}</span><br><span class="ko">{esc(ko)}</span></div>
          <div class="lv"><span class="lb">1단계</span>빈칸을 채우며 읽기 &nbsp; {blank_keys(full, d['words'])}</div>
          <div class="lv"><span class="lb">2단계</span>첫 글자 보고 쓰기 &nbsp; {skeleton(full)}</div>
          <div class="lv"><span class="lb">3단계</span>우리말만 보고 영어로! <span class="wl-full"></span></div>
        </div>"""
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">문장 외우기 (생각하며!)</span>
        <span class="tip">그냥 베끼지 말고, 빈칸을 채우며 → 첫 글자 보고 → 우리말만 보고. 3번이면 외워져</span></div>
      {li}
    </div>""")

    # 은아쌤 마무리
    P.append(f"""<div class="saem"><span class="tag">{esc(L1.TEACHER)}</span>{bold(d['close'])}</div>""")
    return "".join(P)


def render_day_answer(d):
    idx = d["day"]
    rev = cumulative_review(idx)
    rev_ans = ", ".join(f"{esc(en)}=<b>{esc(ko)}</b>" for en, ko, _ in rev) if rev else "—"
    words = "  ·  ".join(f"<b>{esc(en)}</b> {esc(ko)}" for en, ko in d["words"])
    disc = f"{bold(d['discovery']['answer'])}"
    prac = ", ".join(f"<b>{esc(a)}</b>" for _, a in d["practice"])
    refs = " / ".join(f"{esc(p)}=<b>{esc(a)}</b>" for _, _, p, a in d["refs"])
    mem = " · ".join(f"<b>{esc(full)}</b>" for full, _, _ in d["memorize"])
    return f"""
    <div class="ansrow">
      <div class="d">{idx}일차 · {esc(d['title_en'])} — {esc(d['title_ko'])}</div>
      <div class="b">
        <b>지난 단어</b> — {rev_ans}<br>
        <b>오늘 단어</b> — {words}<br>
        <b>문법 발견</b> — {disc} &nbsp;|&nbsp; <b>연습</b> {prac}<br>
        <b>지칭</b> — {refs}<br>
        <b>외울 문장</b> — {mem}
      </div>
    </div>"""


# ── 10일차 총복습 ───────────────────────────────────────────
def render_review_day_student():
    all_words = [(en, ko) for d in L1.DAYS for en, ko in d["words"]]
    ke = all_words[0::3][:30]; ek = all_words[1::3][:30]
    def tbl(items, mode):
        half = (len(items) + 1) // 2
        cols = [items[:half], items[half:]]; tds = ""
        for col in cols:
            rows = "".join(
                f"<tr><td>{(esc(ko) if mode=='ke' else '<span class=en>'+esc(en)+'</span>')}</td>"
                f"<td><span class='writeline' style='min-width:120px'></span></td></tr>" for en, ko in col)
            tds += f"<td style='width:50%;vertical-align:top;padding:0 6px;'><table class='vtab' style='width:100%'>{rows}</table></td>"
        return f"<table style='width:100%'><tr>{tds}</tr></table>"
    gsum = "".join(f"<tr><td class='num'>{i}</td><td class='w'>{esc(day)}</td><td><b>{esc(g)}</b></td>"
                   f"<td class='k' style='width:auto;font-size:9.2px'>{esc(ex)}</td></tr>"
                   for i, (day, g, ex) in enumerate(L1.GRAMMAR_SUMMARY, 1))
    return f"""
    <div class="head"><div class="top"><span class="badge">10일차 · 금요일 · 1과 총복습</span>
        <span class="src">{esc(L1.SOURCE)}<br>Lesson 1 마무리</span></div>
      <div class="body"><div class="title"><span class="k">Lesson 1 총복습</span> — 배운 걸 손으로 정리</div></div></div>
    <div class="saem"><span class="tag">{esc(L1.TEACHER)}</span>이번 주 정말 잘했어! 오늘은 새 단어 없이, 그동안 배운 걸 <b>쓰면서</b> 확실히 굳히는 날이야. 막히면 앞 숙제를 다시 봐도 괜찮아.</div>
    <div class="sec"><div class="h"><span class="n">1</span><span class="t">뜻 보고 영어 쓰기 (30)</span><span class="rep">반복</span></div>{tbl(ke,'ke')}</div>
    <div class="sec pagebreak"><div class="h"><span class="n">2</span><span class="t">영어 보고 뜻 쓰기 (30)</span><span class="rep">반복</span></div>{tbl(ek,'ek')}</div>
    <div class="sec"><div class="h"><span class="n">3</span><span class="t">1과 문법 총정리</span><span class="tip">빈 곳에 예문을 한 번씩 따라 써 보기</span></div>
      <table class="vtab"><tr><th class="num">#</th><th>배운 날</th><th>문법</th><th>핵심 예</th></tr>{gsum}</table></div>"""


def render_cover():
    days_list = "".join(f"<div><b>{d['day']}일차 ({d['weekday']})</b> · {esc(d['title_en'])} — {esc(d['title_ko'])}</div>" for d in L1.DAYS)
    return f"""
    <div class="cover">
      <div class="kie">중등 기초 브릿지</div>
      <h1>Lesson 1 숙제 &amp; 테스트</h1>
      <div class="sub">모기 이야기 &amp; 이로운 벌레 · 은아쌤 손글씨판</div>
      <div class="src">{esc(L1.SOURCE)}</div>
      <div class="list">
        <div style="font-weight:800;color:{ACCENT2};margin-bottom:5px;">▪ 1과 학습 (2주 · 10일)</div>
        {days_list}
        <div><b>10일차 (금)</b> · Lesson 1 총복습</div>
        <div style="margin-top:8px;font-weight:800;color:{ACCENT2};">▪ 테스트</div>
        <div>· 1주차 단어테스트 · 2주차 단어테스트 · 1과 종합테스트</div>
      </div>
      <div class="tip">
        <b>이렇게 공부해요</b> — ① 지문이 무슨 내용인지 읽고 → ② 단어를 3가지로 익히고 →<br>
        ③ 문법을 문장에서 <b>스스로</b> 찾고 → ④ ‘it·they’가 뭘 가리키는지 짚고 → ⑤ 문장을 생각하며 외워요.<br>
        <b>어제 단어는 오늘 또 나와요</b>(반복). 정답은 맨 뒤 ‘선생님용 정답’에 따로 있어요.
      </div>
    </div>"""


def render_month_plan():
    def cell(d):
        return (f"<td class='day'><div class='dh'>{d['day']}일 · {esc(d['weekday'])}</div>"
                f"<div class='gm'>{esc(d['title_en'])}</div>"
                f"<div class='tk'>{esc(d['title_ko'])}<br>문법: {esc(d['goal_title'].split(':')[0].split('(')[0].strip())}</div></td>")
    w1 = "".join(cell(d) for d in L1.DAYS if d["week"] == 1)
    w2 = "".join(cell(d) for d in L1.DAYS if d["week"] == 2)
    w2 += ("<td class='day'><div class='dh'>10일 · 금</div><div class='gm'>Review</div>"
           "<div class='tk'>1과 총복습<br>+ 단어·종합 테스트</div></td>")
    def soon(week_no, items):
        cells = "".join(f"<td class='day'><div class='dh'>{dh}</div><div class='gm soon'>{esc(t)}</div><div class='tk soon'>(다음 제작 예정)</div></td>" for dh, t in items)
        return f"<tr><td class='wk'>{week_no}주차<br><span style='font-size:8px;color:#93a7a2'>2과</span></td>{cells}</tr>"
    w3 = soon("3", [("11일 · 월","3D 점자지도 ①"),("12일 · 화","3D 점자지도 ②"),("13일 · 수","장치 원리"),("14일 · 목","작동·성공"),("15일 · 금","복습·테스트")])
    w4 = soon("4", [("16일 · 월","수어 앱 ①"),("17일 · 화","수어 앱 ②"),("18일 · 수","정확도·미래"),("19일 · 목","자율주행차"),("20일 · 금","2과 총복습·테스트")])
    return f"""
    <div style="text-align:center;margin-bottom:8px;">
      <div style="display:inline-block;border:2px solid {ACCENT};color:{ACCENT};font-weight:800;padding:3px 12px;border-radius:20px;font-size:11px;">중등 기초 브릿지</div>
      <div style="font-size:20px;font-weight:800;margin-top:8px;">한 달 학습 플랜 · 교과서 1과 &amp; 2과</div>
      <div style="font-size:10px;color:#7d918c;margin-top:2px;">{esc(L1.SOURCE.replace(' · Lesson 1',''))}</div>
    </div>
    <table class="plan">
      <tr><th style="width:56px;">주차</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th></tr>
      <tr><td class="wk">1주차<br><span style='font-size:8px;color:#93a7a2'>1과 전반</span></td>{w1}</tr>
      <tr><td class="wk">2주차<br><span style='font-size:8px;color:#93a7a2'>1과 후반</span></td>{w2}</tr>
      {w3}{w4}
    </table>
    <div class="box"><div class="bt">▪ 매일 학습 루틴 (하루 20분 정도)</div>
      <span class="chip">① 지문 내용 읽기</span><span class="chip">② 단어 3가지로 익히기</span>
      <span class="chip">③ 문법 스스로 찾기</span><span class="chip">④ 지칭 찾기</span><span class="chip">⑤ 문장 외우기</span>
      <div class="legend">읽기만으로는 안 외워져요. <b>손으로 쓰고, 스스로 생각하게</b> 만든 구성이에요. 틀린 단어는 그 자리에서 3번 더 쓰기.</div></div>
    <div class="box"><div class="bt">▪ 반복(누적 복습) 시스템</div>
      <div class="legend">· <b>매일</b> : 숙제 맨 위 ‘지난 단어 다시보기’ — 어제·그제 단어가 다시 나옵니다.<br>
        · <b>매주 금요일</b> : 그 주 단어 전체 <b>단어 테스트</b>.<br>
        · <b>2주마다</b> : 한 과가 끝나면 <b>종합 테스트</b>로 총점검.<br>
        · 한 번에 다 외우려 하지 말고, <b>여러 번 마주치며</b> 굳히는 게 목표예요.</div></div>
    <div class="box"><div class="bt">▪ 이번 주 할 일 체크</div>
      <div class="legend">월□ 화□ 수□ 목□ 금□ 숙제 &nbsp;·&nbsp; 금□ 단어 테스트 &nbsp;·&nbsp; (2주차 끝) □ 1과 종합 테스트</div></div>
    <div class="note" style="margin-top:8px;">※ 3~4주차(2과)는 같은 양식으로 이어서 제작합니다. 위 날짜는 예시이며 진도에 맞춰 조정하세요.</div>"""


# ── 단어 테스트 ─────────────────────────────────────────────
def render_vocab_test(day_range, title):
    words = [(en, ko) for d in L1.DAYS if d["day"] in day_range for en, ko in d["words"]]
    total = len(words); half = (total + 1) // 2
    a = words[:half]; b = words[half:]
    def two_col(items, mode, start):
        h = (len(items) + 1) // 2; cols = [items[:h], items[h:]]; tds = ""
        for ci, col in enumerate(cols):
            rows = "".join(
                f"<tr><td class='num'>{start+ci*h+j}</td>"
                f"<td>{('<span class=en>'+esc(en)+'</span>' if mode=='en2ko' else esc(ko))}</td>"
                f"<td><span class='writeline' style='min-width:110px'></span></td></tr>" for j, (en, ko) in enumerate(col))
            tds += f"<td style='width:50%;vertical-align:top;padding:0 6px;'><table class='vtab' style='width:100%'>{rows}</table></td>"
        return f"<table style='width:100%'><tr>{tds}</tr></table>"
    body = f"""
    <div class="examtop"><div class="nm">이름 <span class="u"></span> &nbsp; 날짜 <span class="u" style="min-width:80px"></span></div>
      <div class="score"><div class="s1">SCORE</div><div class="s2">&nbsp; / {total}</div></div></div>
    <div style="font-weight:800;font-size:14.5px;margin-bottom:2px;">{esc(title)}
      <span style="font-size:9.5px;color:#93a7a2;font-weight:400;">단어 {total}개</span></div>
    <div class="note" style="margin-bottom:9px;">A는 뜻을, B는 영어를 정확히 쓰세요. 철자 하나까지! 한 문제 1점.</div>
    <div class="sec"><div class="h"><span class="n">A</span><span class="t">영어 → 우리말 뜻 쓰기</span></div>{two_col(a,'en2ko',1)}</div>
    <div class="sec pagebreak"><div class="h"><span class="n">B</span><span class="t">우리말 → 영어 단어 쓰기</span></div>{two_col(b,'ko2en',half+1)}</div>"""
    ans = f"""
    <div class="answers"><div class="tearline"><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>
      <div style="font-weight:800;font-size:13px;margin-bottom:6px;">✔ {esc(title)} · 정답</div>
      <div style="font-weight:800;color:{ACCENT2};margin:4px 0 2px;">A. 영어 → 뜻</div>
      <div>{''.join(f"<span style='display:inline-block;width:33%;font-size:9px;margin:1.5px 0;'>{i}. <b>{esc(en)}</b> {esc(ko)}</span>" for i,(en,ko) in enumerate(a,1))}</div>
      <div style="font-weight:800;color:{ACCENT2};margin:8px 0 2px;">B. 뜻 → 영어</div>
      <div>{''.join(f"<span style='display:inline-block;width:33%;font-size:9px;margin:1.5px 0;'>{half+i}. {esc(ko)} <b>{esc(en)}</b></span>" for i,(en,ko) in enumerate(b,1))}</div></div>"""
    return body + ans


def render_comp_test():
    e2k = [("mosquito","모기"),("pierce","뚫다, 찌르다"),("release","분비하다"),("attract","유인하다"),
           ("contain","포함하다"),("predator","포식자"),("estimate","추정하다"),("surround","둘러싸다"),
           ("encounter","맞닥뜨리다"),("defend","방어하다")]
    k2e = [("가려운","itchy"),("단백질","protein"),("중력","gravity"),("치명적인","deadly"),
           ("제국","empire"),("결국, 마침내","eventually"),("퍼뜨리다","spread"),("생존자","survivor"),
           ("곤충","insect"),("흙, 토양","soil")]
    grammar = [
        ("A mosquito ( sneak / sneaks ) into the tent.","sneaks","3인칭 -s"),
        ("How ( do / does ) mosquitoes find us?","do","일반동사 의문문"),
        ("certain chemicals ( that / who ) attract them","that","관계대명사"),
        ("If our blood did not contain protein, they ( will / would ) not bite us.","would","가정법 과거"),
        ("Mosquitoes ( have / has ) killed billions of people.","have","현재완료"),
        ("Rome ( surrounded / was surrounded ) by wetland.","was surrounded","수동태"),
        ("No one ( has / had ) ever encountered these diseases before.","had","과거완료"),
        ("If their immune systems ( had been / were ) stronger, they would not have lost lives.","had been","가정법 과거완료"),
        ("Ladybugs are the ( more / most ) well-known bugs.","most","최상급"),
        ("They keep the soil soft by ( dig / digging ) tunnels.","digging","동명사"),
    ]
    translate = [
        ("A mosquito sneaks in and pierces your skin.","모기가 몰래 들어와 너의 피부를 찌른다."),
        ("When you sweat, you release certain chemicals that attract them.","네가 땀을 흘리면, 그들을 유인하는 특정 화학물질을 내보낸다."),
        ("Mosquitoes have killed more people than any other single cause.","모기는 다른 어떤 단일 원인보다도 더 많은 사람을 죽여 왔다."),
        ("Rome was once surrounded by a huge stretch of wetland.","로마는 한때 거대하게 펼쳐진 습지로 둘러싸여 있었다."),
        ("No one had ever encountered these diseases before.","아무도 이전에 이런 질병들을 접해 본 적이 없었다."),
    ]
    reading = ("Mosquitoes are highly sensitive to CO2 and can detect it from far away. "
               "When you sweat, you release certain chemicals that attract them. "
               "Only female mosquitoes bite us; they need protein to produce eggs.")
    rq = [("모기는 무엇을 멀리서도 감지하나요? (우리말)","이산화탄소(CO2)"),
          ("밑줄 친 them 은 무엇을 가리키나요?","모기들 (mosquitoes)"),
          ("우리를 무는 것은 암컷인가요, 수컷인가요?","암컷"),
          ("암컷 모기가 단백질을 필요로 하는 이유는?","알을 낳기 위해서")]
    def vc(items, mode):
        return "".join(f"<tr><td class='num'>{i}</td>"
                       f"<td>{('<span class=en>'+esc(a)+'</span>' if mode=='e2k' else esc(a))}</td>"
                       f"<td><span class='writeline' style='min-width:100px'></span></td></tr>" for i, (a, b) in enumerate(items, 1))
    top = f"""
    <div class="examtop"><div class="nm">이름 <span class="u"></span> &nbsp; 날짜 <span class="u" style="min-width:80px"></span></div>
      <div class="score"><div class="s1">SCORE</div><div class="s2">&nbsp; / 100</div></div></div>
    <div style="font-weight:800;font-size:14.5px;margin-bottom:2px;">Lesson 1 종합 테스트
      <span style="font-size:9.5px;color:#93a7a2;font-weight:400;">단어 · 문법 · 해석 · 독해(지칭)</span></div>
    <div class="note" style="margin-bottom:9px;">아는 것부터 푸세요. 부분 점수도 있어요!</div>"""
    s1 = (f"<div class='sec'><div class='h'><span class='n'>1</span><span class='t'>단어 (20점)</span></div>"
          f"<table style='width:100%'><tr><td style='width:50%;vertical-align:top;padding-right:8px;'><div class='note' style='margin-bottom:3px;'>(1) 영어 → 뜻</div>"
          f"<table class='vtab' style='width:100%'>{vc(e2k,'e2k')}</table></td>"
          f"<td style='width:50%;vertical-align:top;padding-left:8px;'><div class='note' style='margin-bottom:3px;'>(2) 뜻 → 영어</div>"
          f"<table class='vtab' style='width:100%'>{vc(k2e,'k2e')}</table></td></tr></table></div>")
    s2 = ("<div class='sec'><div class='h'><span class='n'>2</span><span class='t'>문법 · 골라 동그라미 (20점)</span><span class='tip'>한 문제 2점</span></div><ol class='q'>"
          + "".join(f"<li>{esc(q)} <span class='hint'>[{esc(t)}]</span></li>" for q, _, t in grammar) + "</ol></div>")
    s3 = ("<div class='sec pagebreak'><div class='h'><span class='n'>3</span><span class='t'>문장 해석 (25점)</span><span class='tip'>밑줄에 우리말 뜻 쓰기 · 한 문제 5점</span></div><ol class='q'>"
          + "".join(f"<li>{esc(s)}<span class='wl-full'></span></li>" for s, _ in translate) + "</ol></div>")
    s4 = (f"<div class='sec'><div class='h'><span class='n'>4</span><span class='t'>짧은 지문 읽고 답하기 (35점)</span></div>"
          f"<div class='wordbank' style='color:{INK};font-weight:400;line-height:1.7;'>{esc(reading)}</div><ol class='q'>"
          + "".join(f"<li>{esc(q)}<span class='wl-full' style='width:70%'></span></li>" for q, _ in rq) + "</ol></div>")
    ans = f"""
    <div class="answers"><div class="tearline"><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>
      <div style="font-weight:800;font-size:13px;margin-bottom:6px;">✔ Lesson 1 종합 테스트 · 정답 &amp; 해설</div>
      <div class="ansrow"><div class="d">1. 단어</div><div class="b">
        (1) 영어→뜻 : {' · '.join(f"{i}.{esc(k)}" for i,(e,k) in enumerate(e2k,1))}<br>
        (2) 뜻→영어 : {' · '.join(f"{i}.{esc(v)}" for i,(k,v) in enumerate(k2e,1))}</div></div>
      <div class="ansrow"><div class="d">2. 문법</div><div class="b">{' · '.join(f"{i}.<b>{esc(a)}</b>" for i,(q,a,t) in enumerate(grammar,1))}</div></div>
      <div class="ansrow"><div class="d">3. 문장 해석</div><div class="b">{''.join(f"<div>{i}. {esc(a)}</div>" for i,(s,a) in enumerate(translate,1))}</div></div>
      <div class="ansrow"><div class="d">4. 독해</div><div class="b">{''.join(f"<div>{i}. {esc(a)}</div>" for i,(q,a) in enumerate(rq,1))}</div></div></div>"""
    return top + s1 + s2 + s3 + s4 + ans


def wrap(inner, title):
    return f"<html><head><meta charset='utf-8'><title>{esc(title)}</title><style>{CSS}</style></head><body>{inner}</body></html>"


def to_pdf(inner, filename, title=""):
    weasyprint.HTML(string=wrap(inner, title or filename)).write_pdf(str(OUT / filename))
    print(f"  ✓ {filename}  ({(OUT/filename).stat().st_size//1024} KB)")


def main():
    print("PDF 생성 중 …")
    to_pdf(render_month_plan(), "00_한달_학습플랜.pdf", "한 달 학습 플랜")
    for d in L1.DAYS:
        inner = render_day_student(d)
        inner += ("<div class='answers'><div class='tearline'><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>"
                  f"<div style='font-weight:800;font-size:12px;margin-bottom:5px;'>✔ {d['day']}일차 정답</div>"
                  + render_day_answer(d) + "</div>")
        to_pdf(inner, f"L1_{d['day']:02d}일차_{d['weekday']}_숙제_{d['title_en'].replace(' ','')}.pdf", f"{d['day']}일차 숙제")
    to_pdf(render_review_day_student(), "L1_10일차_금_1과총복습.pdf", "10일차 총복습")

    inner = render_cover()
    for d in L1.DAYS:
        inner += "<div class='pagebreak'></div>" + render_day_student(d)
    inner += "<div class='pagebreak'></div>" + render_review_day_student()
    inner += "<div class='answers'><div class='tearline'><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>"
    inner += "<div style='font-weight:800;font-size:14px;margin-bottom:7px;'>✔ Lesson 1 숙제 · 선생님용 정답</div>"
    for d in L1.DAYS:
        inner += render_day_answer(d)
    inner += "</div>"
    to_pdf(inner, "L1_숙제_합본_1-2주차.pdf", "Lesson 1 숙제 합본")

    to_pdf(render_vocab_test(range(1, 6), "1주차 단어 테스트 (1~5일차)"), "L1_테스트_1주차_단어.pdf")
    to_pdf(render_vocab_test(range(6, 10), "2주차 단어 테스트 (6~9일차)"), "L1_테스트_2주차_단어.pdf")
    to_pdf(render_comp_test(), "L1_테스트_1과_종합.pdf", "1과 종합 테스트")
    print("완료! → tutoring_materials/output/")


if __name__ == "__main__":
    main()
