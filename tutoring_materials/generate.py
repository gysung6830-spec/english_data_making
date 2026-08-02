# -*- coding: utf-8 -*-
"""
1과(Lesson 1) 한 달 과정 · 쓰기 강화판 PDF 생성기 (WeasyPrint).
    python tutoring_materials/generate.py
결과: tutoring_materials/output/*.pdf

특징
  · 쓰기 학습 강화: 단어 3번 쓰기 + 뜻→영어 쓰기 + 문장 통째로 쓰기
  · 누적 반복: 매일 이전 날 단어를 다시 복습 (분산 학습)
  · 정답 별지 분리: 학생용 페이지엔 정답 없음, 맨 뒤에 '선생님용 정답'
  · 월간 학습 플랜표 포함
"""
from __future__ import annotations

import base64
import html
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
SOFT = "#f2f7f6"; LINE = "#d7e3e1"; WARM = "#fff7f2"

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
.goal {{ background:{SOFT}; border:1px dashed {ACCENT}; border-radius:9px; padding:6px 11px; margin-top:7px; }}
.goal .g1 {{ font-weight:800; color:{ACCENT2}; font-size:11.3px; }}
.goal .g1 .flag {{ color:{ACCENT}; }}
.goal .g2 {{ font-size:9.6px; color:#5b6f6b; margin-top:2px; }}

.sec {{ margin-top:10px; page-break-inside:avoid; }}
.sec>.h {{ display:flex; align-items:center; gap:7px; margin-bottom:5px; }}
.sec>.h .n {{ display:inline-flex; width:19px; height:19px; border-radius:50%; background:{ACCENT}; color:#fff; font-weight:800; font-size:10.5px; align-items:center; justify-content:center; flex:0 0 auto; }}
.sec>.h .t {{ font-weight:800; font-size:12px; }}
.sec>.h .tip {{ font-size:8.8px; color:#93a7a2; font-weight:400; }}
.sec>.h .rep {{ background:{ACCENT2}; color:#fff; font-size:8px; font-weight:800; padding:1px 7px; border-radius:20px; }}

table {{ border-collapse:collapse; width:100%; }}
.vtab td,.vtab th {{ border:1px solid {LINE}; padding:4px 6px; vertical-align:middle; }}
.vtab th {{ background:{SOFT}; font-weight:800; font-size:9.2px; color:#5b6f6b; }}
.vtab td.num {{ width:20px; text-align:center; color:#9fb3ae; font-size:9px; }}
.vtab td.w {{ width:108px; }}
.vtab td.k {{ width:132px; font-size:10px; }}
.writeline {{ border-bottom:1.3px dotted #b9c9c5; display:inline-block; min-width:70px; height:14px; }}
.wl-full {{ border-bottom:1.3px dotted #b9c9c5; display:block; height:16px; margin-top:3px; }}

.match {{ display:flex; gap:20px; }}
.match .col {{ flex:1; }}
.match .row {{ display:flex; justify-content:space-between; padding:4px; border-bottom:1px dotted {LINE}; font-size:10.3px; }}
.match .dot {{ color:{ACCENT}; }}

ol.q {{ margin:0; padding-left:19px; }}
ol.q li {{ margin:4px 0; }}
.blank {{ display:inline-block; min-width:92px; border-bottom:1.5px solid {ACCENT}; height:13px; }}
.hint {{ color:{ACCENT2}; font-size:9px; font-weight:800; }}
.wordbank {{ background:{SOFT}; border:1px solid {LINE}; border-radius:8px; padding:5px 10px; margin:4px 0 7px; font-weight:800; color:{ACCENT}; font-size:10.2px; }}
.wordbank .lab {{ color:#93a7a2; margin-right:6px; }}
.spell {{ font-weight:800; letter-spacing:2px; }}

/* 문장 통째로 쓰기 */
.copybox {{ border:1px solid {LINE}; border-radius:8px; padding:7px 10px; margin:5px 0; page-break-inside:avoid; }}
.copybox .src {{ font-size:10.6px; margin-bottom:2px; }}
.copybox .src .en {{ color:{INK}; }}
.copybox .ko {{ font-size:8.8px; color:#93a7a2; margin-bottom:4px; }}

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

/* 표지 */
.cover {{ text-align:center; padding-top:46px; }}
.cover .kie {{ display:inline-block; border:2px solid {ACCENT}; color:{ACCENT}; font-weight:800; padding:4px 14px; border-radius:20px; font-size:12px; }}
.cover h1 {{ font-size:27px; margin:16px 0 4px; }}
.cover .sub {{ font-size:12.5px; color:{ACCENT2}; font-weight:800; }}
.cover .src {{ font-size:10.5px; color:#7d918c; margin-top:5px; }}
.cover .list {{ display:inline-block; text-align:left; margin-top:20px; background:{SOFT}; border:1px solid {LINE}; border-radius:12px; padding:14px 24px; font-size:11px; line-height:1.9; }}
.cover .list b {{ color:{ACCENT}; }}
.cover .tip {{ margin-top:18px; font-size:10px; color:#7d918c; line-height:1.7; }}

/* 시험 */
.examtop {{ display:flex; justify-content:space-between; align-items:flex-end; border-bottom:2px solid {ACCENT}; padding-bottom:6px; margin-bottom:9px; }}
.examtop .nm {{ font-size:10px; color:#5b6f6b; }}
.examtop .nm .u {{ display:inline-block; min-width:110px; border-bottom:1.3px solid #b9c9c5; }}
.examtop .score {{ text-align:center; border:2px solid {ACCENT2}; border-radius:9px; padding:3px 12px; }}
.examtop .score .s1 {{ font-size:8px; color:{ACCENT2}; font-weight:800; }}
.examtop .score .s2 {{ font-size:14px; font-weight:800; }}

/* 월간 플랜 */
.plan {{ width:100%; border-collapse:collapse; }}
.plan td,.plan th {{ border:1px solid {LINE}; padding:5px 6px; vertical-align:top; font-size:8.7px; }}
.plan th {{ background:{ACCENT}; color:#fff; font-weight:800; font-size:9.2px; text-align:center; }}
.plan .wk {{ background:{SOFT}; font-weight:800; color:{ACCENT}; text-align:center; width:56px; font-size:9px; vertical-align:middle; }}
.plan .day .dh {{ font-weight:800; color:{INK}; font-size:9px; }}
.plan .day .gm {{ color:{ACCENT2}; font-weight:800; font-size:8.2px; }}
.plan .day .tk {{ color:#5b6f6b; font-size:8.2px; margin-top:1px; }}
.plan .soon {{ color:#9fb3ae; font-style:normal; }}
.plan .test td {{ background:{WARM}; }}
.legend {{ font-size:9px; color:#5b6f6b; margin-top:8px; line-height:1.7; }}
.box {{ background:{SOFT}; border:1px solid {LINE}; border-radius:10px; padding:10px 13px; margin-top:10px; }}
.box .bt {{ font-weight:800; color:{ACCENT}; font-size:11px; margin-bottom:4px; }}
.chip {{ display:inline-block; background:#fff; border:1px solid {LINE}; border-radius:20px; padding:2px 9px; margin:2px 3px 0 0; font-size:9px; font-weight:800; color:{INK}; }}
"""


def esc(s): return html.escape(str(s))


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


def cumulative_review(day_idx):
    """day_idx(1-based)의 누적 복습 단어 8개: 어제4 + 그제2 + 이전2(회전)."""
    if day_idx <= 1:
        return []
    prev = L1.DAYS[day_idx - 2]["words"]          # 어제
    picks = list(prev[:4])
    if day_idx >= 3:
        picks += list(L1.DAYS[day_idx - 3]["words"][4:6])   # 그제 2개
    if day_idx >= 4:
        older = L1.DAYS[(day_idx - 4) % (day_idx - 1)]["words"]
        picks += list(older[6:8]) if len(older) >= 8 else list(older[:2])
    # 중복 제거, 8개로
    seen, out = set(), []
    for en, ko in picks:
        if en not in seen:
            seen.add(en); out.append((en, ko))
    return out[:8]


# ── 하루치: 학생용 페이지 ─────────────────────────────────────
def render_day_student(d):
    idx = d["day"]
    P = []
    P.append(f"""
    <div class="head">
      <div class="top">
        <span class="badge">{idx}일차 · {esc(d['weekday'])}요일 숙제</span>
        <span class="src">{esc(L1.SOURCE)}<br>{esc(d['part'])}</span>
      </div>
      <div class="body">
        <div class="title"><span class="k">{esc(d['title_en'])}</span> — {esc(d['title_ko'])}</div>
        <div class="part">읽기만 하지 말고 꼭 <b>손으로 써</b> 보세요. 소리 내어 읽으며 쓰면 두 배로 외워져요.</div>
        <div class="goal">
          <div class="g1"><span class="flag">🎯 오늘의 문법</span> · {esc(d['goal_title'])}</div>
          <div class="g2">{esc(d['goal_desc'])}</div>
        </div>
      </div>
    </div>""")

    n = 0
    # 1) 누적 복습
    rev = cumulative_review(idx)
    if rev:
        rows = ""
        for en, ko in rev:
            rows += (f"<tr><td class='num'>·</td><td class='w'><span class='en'>{esc(en)}</span></td>"
                     f"<td class='k'><span class='writeline' style='min-width:120px'></span></td></tr>")
        n += 1
        P.append(f"""
        <div class="sec">
          <div class="h"><span class="n">{n}</span><span class="t">누적 단어 복습</span>
            <span class="rep">반복</span><span class="tip">전에 배운 단어! 뜻을 우리말로 쓰기</span></div>
          <table class="vtab"><tr><th class="num">#</th><th>영어</th><th>뜻 쓰기</th></tr>{rows}</table>
        </div>""")

    # 2) 오늘의 단어 3번 쓰기
    n += 1
    rows = ""
    for i, (en, ko) in enumerate(d["words"], 1):
        rows += (f"<tr><td class='num'>{i}</td><td class='w'><span class='en'>{esc(en)}</span></td>"
                 f"<td class='k'>{esc(ko)}</td>"
                 f"<td><span class='writeline'></span></td>"
                 f"<td><span class='writeline'></span></td>"
                 f"<td><span class='writeline'></span></td></tr>")
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">오늘의 단어 10개 · 3번 쓰기</span>
        <span class="tip">소리 내어 읽으며 세 번씩 쓰기</span></div>
      <table class="vtab">
        <tr><th class="num">#</th><th>영어</th><th>뜻</th><th>쓰기 ①</th><th>쓰기 ②</th><th>쓰기 ③</th></tr>
        {rows}
      </table>
    </div>""")

    # 3) 뜻 보고 영어 쓰기 (영작, 첫 글자 힌트)
    n += 1
    qi = ""
    for en, ko in d["words"]:
        qi += f"<li>{esc(ko)} &nbsp;→&nbsp; <span class='spell'>{spell_hint(en)}</span></li>"
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">뜻 보고 영어 쓰기</span>
        <span class="tip">첫 글자를 보고 나머지 알파벳을 채워 완성</span></div>
      <ol class="q" style="columns:2; column-gap:26px;">{qi}</ol>
    </div>""")

    # 4) 문장 통째로 쓰기
    n += 1
    ci = ""
    for s in d["copy"]:
        ci += (f"<div class='copybox'><div class='src'><span class='en'>{esc(s)}</span></div>"
               f"<span class='wl-full'></span><span class='wl-full'></span></div>")
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">문장 통째로 쓰기</span>
        <span class="tip">지문에 나온 문장! 밑줄에 그대로 두 번 따라 쓰기</span></div>
      {ci}
    </div>""")

    # 5) 문장 속 빈칸
    n += 1
    bank = " · ".join(sorted({c[1] for c in d["cloze"]}))
    zi = ""
    for sent, ans, hh in d["cloze"]:
        s = esc(sent).replace("______", "<span class='blank'></span>")
        zi += f"<li>{s} <span class='hint'>({esc(hh)})</span></li>"
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">문장 속 빈칸 채우기</span>
        <span class="tip">아래 단어 상자에서 골라 쓰기</span></div>
      <div class="wordbank"><span class="lab">단어 상자</span>{esc(bank)}</div>
      <ol class="q">{zi}</ol>
    </div>""")

    # 6) 문법 한 입
    n += 1
    gi = "".join(f"<li>{esc(q)}</li>" for q, _ in d["grammar_q"])
    P.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">오늘의 문법 한 입 · 골라 동그라미</span>
        <span class="tip">{esc(d['goal_title'])}</span></div>
      <ol class="q">{gi}</ol>
    </div>""")
    return "".join(P)


# ── 하루치: 정답(별지) ────────────────────────────────────────
def render_day_answer(d):
    idx = d["day"]
    rev = cumulative_review(idx)
    rev_ans = ", ".join(f"{esc(en)}=<b>{esc(ko)}</b>" for en, ko in rev) if rev else "—"
    words = "  ·  ".join(f"<b>{esc(en)}</b> {esc(ko)}" for en, ko in d["words"])
    spell = ", ".join(f"{esc(ko)}=<b>{esc(en)}</b>" for en, ko in d["words"])
    cloze = ", ".join(f"<b>{esc(a)}</b>" for _, a, _ in d["cloze"])
    gram = ", ".join(f"<b>{esc(a)}</b>" for _, a in d["grammar_q"])
    return f"""
    <div class="ansrow">
      <div class="d">{idx}일차 · {esc(d['title_en'])} — {esc(d['title_ko'])}</div>
      <div class="b">
        <b>누적 복습</b> — {rev_ans}<br>
        <b>단어 뜻</b> — {words}<br>
        <b>뜻→영어</b> — {spell}<br>
        <b>문장 빈칸</b> — {cloze}<br>
        <b>문법</b> — {gram} <span style="color:#c9b">|</span> {esc(d['gnote'])}
      </div>
    </div>"""


# ── 10일차: 1과 총복습(쓰기) ─────────────────────────────────
def render_review_day_student():
    all_words = [(en, ko) for d in L1.DAYS for en, ko in d["words"]]  # 90개
    # 뜻→영어 쓰기 30개(대표), 영어→뜻 쓰기 30개
    ke = all_words[0::3][:30]
    ek = all_words[1::3][:30]
    def tbl(items, mode):
        half = (len(items) + 1) // 2
        cols = [items[:half], items[half:]]
        tds = ""
        for col in cols:
            rows = ""
            for en, ko in col:
                prompt = esc(ko) if mode == "ke" else f"<span class='en'>{esc(en)}</span>"
                rows += f"<tr><td>{prompt}</td><td><span class='writeline' style='min-width:120px'></span></td></tr>"
            tds += f"<td style='width:50%;vertical-align:top;padding:0 6px;'><table class='vtab' style='width:100%'>{rows}</table></td>"
        return f"<table style='width:100%'><tr>{tds}</tr></table>"

    gsum = "".join(f"<tr><td class='num'>{i}</td><td class='w'>{esc(day)}</td>"
                   f"<td><b>{esc(g)}</b></td><td class='k' style='width:auto;font-size:9.4px'>{esc(ex)}</td></tr>"
                   for i, (day, g, ex) in enumerate(L1.GRAMMAR_SUMMARY, 1))
    return f"""
    <div class="head">
      <div class="top"><span class="badge">10일차 · 금요일 · 1과 총복습</span>
        <span class="src">{esc(L1.SOURCE)}<br>Lesson 1 마무리</span></div>
      <div class="body">
        <div class="title"><span class="k">Lesson 1 총복습</span> — 한 주 동안 배운 것 손으로 정리</div>
        <div class="part">이번 주는 새 단어 없이, 배운 걸 <b>다시 쓰며</b> 굳히는 날이에요.</div>
      </div>
    </div>
    <div class="sec"><div class="h"><span class="n">1</span><span class="t">뜻 보고 영어 쓰기 (30)</span>
      <span class="rep">반복</span></div>{tbl(ke,'ke')}</div>
    <div class="sec pagebreak"><div class="h"><span class="n">2</span><span class="t">영어 보고 뜻 쓰기 (30)</span>
      <span class="rep">반복</span></div>{tbl(ek,'ek')}</div>
    <div class="sec"><div class="h"><span class="n">3</span><span class="t">1과 문법 총정리</span>
      <span class="tip">빈 곳에 예문을 한 번씩 따라 써 보기</span></div>
      <table class="vtab"><tr><th class="num">#</th><th>배운 날</th><th>문법</th><th>핵심 예</th></tr>{gsum}</table>
    </div>"""


# ── 표지 ────────────────────────────────────────────────────
def render_cover():
    days_list = "".join(
        f"<div><b>{d['day']}일차 ({d['weekday']})</b> · {esc(d['title_en'])} — {esc(d['title_ko'])}</div>"
        for d in L1.DAYS)
    return f"""
    <div class="cover">
      <div class="kie">중등 기초 브릿지</div>
      <h1>Lesson 1 숙제 &amp; 테스트</h1>
      <div class="sub">모기 이야기 &amp; 이로운 벌레 (①~⑨) · 쓰기 강화판</div>
      <div class="src">{esc(L1.SOURCE)}</div>
      <div class="list">
        <div style="font-weight:800;color:{ACCENT2};margin-bottom:5px;">▪ 1과 학습 (2주 · 10일)</div>
        {days_list}
        <div><b>10일차 (금)</b> · Lesson 1 총복습 (쓰기)</div>
        <div style="margin-top:9px;font-weight:800;color:{ACCENT2};">▪ 테스트</div>
        <div>· 1주차 단어테스트 · 2주차 단어테스트 · 1과 종합테스트</div>
      </div>
      <div class="tip">
        읽기만으로는 안 외워져요. <b>매일 손으로 쓰기</b>가 핵심!<br>
        ① 소리 내어 읽기 → ② 세 번 쓰기 → ③ 뜻 가리고 영어 쓰기 → ④ 문장 쓰기<br>
        <b>어제 배운 단어는 오늘 또 나와요</b>(누적 복습) — 반복이 암기를 만듭니다.<br>
        <span style="color:{ACCENT2};font-weight:800;">정답은 맨 뒤 '선생님용 정답'에 따로 있어요.</span>
      </div>
    </div>"""


# ── 월간 플랜표 ─────────────────────────────────────────────
def render_month_plan():
    def cell(d):
        return (f"<td class='day'><div class='dh'>{d['day']}일 · {esc(d['weekday'])}</div>"
                f"<div class='gm'>{esc(d['title_en'])}</div>"
                f"<div class='tk'>{esc(d['title_ko'])}<br>문법: {esc(d['goal_title'].split(':')[0].split('(')[0].strip())}</div></td>")
    w1 = "".join(cell(d) for d in L1.DAYS if d["week"] == 1)
    w2days = [d for d in L1.DAYS if d["week"] == 2]
    w2 = "".join(cell(d) for d in w2days)
    w2 += ("<td class='day'><div class='dh'>10일 · 금</div><div class='gm'>Review</div>"
           "<div class='tk'>1과 총복습 (쓰기)<br>+ 단어·종합 테스트</div></td>")

    def soon(week_no, title, items):
        cells = ""
        for i, (dh, t) in enumerate(items):
            cells += (f"<td class='day'><div class='dh'>{dh}</div>"
                      f"<div class='gm soon'>{esc(t)}</div>"
                      f"<div class='tk soon'>(다음 제작 예정)</div></td>")
        return f"<tr><td class='wk'>{week_no}주차<br><span style='font-size:8px;color:#93a7a2'>2과</span></td>{cells}</tr>"

    w3 = soon("3", "", [("11일 · 월", "3D 점자지도 ①"), ("12일 · 화", "3D 점자지도 ②"),
                        ("13일 · 수", "장치 원리"), ("14일 · 목", "작동·성공"), ("15일 · 금", "복습·테스트")])
    w4 = soon("4", "", [("16일 · 월", "수어 앱 ①"), ("17일 · 화", "수어 앱 ②"),
                        ("18일 · 수", "정확도·미래"), ("19일 · 목", "자율주행차"), ("20일 · 금", "2과 총복습·테스트")])

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
      {w3}
      {w4}
    </table>
    <div class="box">
      <div class="bt">▪ 매일 학습 루틴 (하루 15~20분)</div>
      <span class="chip">① 소리 내어 읽기</span><span class="chip">② 단어 3번 쓰기</span>
      <span class="chip">③ 뜻 가리고 영어 쓰기</span><span class="chip">④ 문장 통째로 쓰기</span>
      <span class="chip">⑤ 문법 한 입</span>
      <div class="legend">읽기만으로는 안 외워집니다. <b>쓰기</b>가 핵심이에요. 틀린 단어는 그 자리에서 3번 더 쓰기.</div>
    </div>
    <div class="box">
      <div class="bt">▪ 반복(누적 복습) 시스템</div>
      <div class="legend">
        · <b>매일</b> : 숙제 맨 위 '누적 단어 복습' — 어제·그제 배운 단어가 다시 나옵니다.<br>
        · <b>매주 금요일</b> : 그 주 단어 전체를 모아 <b>단어 테스트</b>.<br>
        · <b>2주마다</b> : 한 과가 끝나면 <b>종합 테스트</b>(단어·문법·해석·독해)로 총점검.<br>
        · 한 번에 다 외우려 하지 말고, <b>여러 번 마주치며</b> 조금씩 굳히는 게 목표입니다.
      </div>
    </div>
    <div class="box">
      <div class="bt">▪ 이번 주 할 일 체크</div>
      <div class="legend">월□ 화□ 수□ 목□ 금□ 숙제 &nbsp;·&nbsp; 금□ 단어 테스트 &nbsp;·&nbsp; (2주차 끝) □ 1과 종합 테스트</div>
    </div>
    <div class="note" style="margin-top:8px;">※ 3~4주차(2과)는 같은 양식으로 이어서 제작합니다. 위 날짜는 예시이며 진도에 맞춰 조정하세요.</div>
    """


# ── 단어 테스트 (주차별) ────────────────────────────────────
def render_vocab_test(day_range, title, half_split=True):
    words = []
    for d in L1.DAYS:
        if d["day"] in day_range:
            for en, ko in d["words"]:
                words.append((en, ko))
    total = len(words)
    half = (total + 1) // 2
    a = words[:half]   # 영어→뜻
    b = words[half:]   # 뜻→영어

    def two_col(items, mode, start):
        h = (len(items) + 1) // 2
        cols = [items[:h], items[h:]]
        tds = ""
        for ci, col in enumerate(cols):
            rows = ""
            for j, (en, ko) in enumerate(col):
                num = start + ci * h + j
                prompt = f"<span class='en'>{esc(en)}</span>" if mode == "en2ko" else esc(ko)
                rows += (f"<tr><td class='num'>{num}</td><td>{prompt}</td>"
                         f"<td><span class='writeline' style='min-width:110px'></span></td></tr>")
            tds += f"<td style='width:50%;vertical-align:top;padding:0 6px;'><table class='vtab' style='width:100%'>{rows}</table></td>"
        return f"<table style='width:100%'><tr>{tds}</tr></table>"

    body = f"""
    <div class="examtop">
      <div class="nm">이름 <span class="u"></span> &nbsp; 날짜 <span class="u" style="min-width:80px"></span></div>
      <div class="score"><div class="s1">SCORE</div><div class="s2">&nbsp; / {total}</div></div>
    </div>
    <div style="font-weight:800;font-size:14.5px;margin-bottom:2px;">{esc(title)}
      <span style="font-size:9.5px;color:#93a7a2;font-weight:400;">단어 {total}개</span></div>
    <div class="note" style="margin-bottom:9px;">A는 뜻을, B는 영어를 정확히 쓰세요. 철자 하나까지! 한 문제 1점.</div>
    <div class="sec"><div class="h"><span class="n">A</span><span class="t">영어 → 우리말 뜻 쓰기</span></div>{two_col(a,'en2ko',1)}</div>
    <div class="sec pagebreak"><div class="h"><span class="n">B</span><span class="t">우리말 → 영어 단어 쓰기</span></div>{two_col(b,'ko2en',half+1)}</div>"""

    ans = f"""
    <div class="answers">
      <div class="tearline"><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>
      <div style="font-weight:800;font-size:13px;margin-bottom:6px;">✔ {esc(title)} · 정답</div>
      <div style="font-weight:800;color:{ACCENT2};margin:4px 0 2px;">A. 영어 → 뜻</div>
      <div>{''.join(f"<span style='display:inline-block;width:33%;font-size:9px;margin:1.5px 0;'>{i}. <b>{esc(en)}</b> {esc(ko)}</span>" for i,(en,ko) in enumerate(a,1))}</div>
      <div style="font-weight:800;color:{ACCENT2};margin:8px 0 2px;">B. 뜻 → 영어</div>
      <div>{''.join(f"<span style='display:inline-block;width:33%;font-size:9px;margin:1.5px 0;'>{half+i}. {esc(ko)} <b>{esc(en)}</b></span>" for i,(en,ko) in enumerate(b,1))}</div>
    </div>"""
    return body + ans


# ── 1과 종합 테스트 ─────────────────────────────────────────
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
        ("A mosquito sneaks in and pierces your skin.","모기가 몰래 들어와 너의 피부를 뚫는다(찌른다)."),
        ("When you sweat, you release certain chemicals that attract them.","네가 땀을 흘리면, 그들을 유인하는 특정한 화학 물질을 내보낸다(분비한다)."),
        ("Mosquitoes have killed more people than any other single cause.","모기는 다른 어떤 단일 원인보다도 더 많은 사람을 죽여 왔다."),
        ("Rome was once surrounded by a huge stretch of wetland.","로마는 한때 거대하게 펼쳐진 습지로 둘러싸여 있었다."),
        ("No one had ever encountered these diseases before.","아무도 이전에 이런 질병들을 접해 본 적이 없었다."),
    ]
    reading = ("Mosquitoes are highly sensitive to CO2 and can detect it from far away. "
               "When you sweat, you release certain chemicals that attract them. "
               "Only female mosquitoes bite us; they need protein to produce eggs. "
               "Long ago, mosquitoes even helped shape the history of the Roman Empire.")
    rq = [("모기는 무엇을 멀리서도 감지하나요? (우리말)","이산화탄소(CO2)"),
          ("우리를 무는 것은 암컷인가요, 수컷인가요?","암컷"),
          ("암컷 모기가 단백질을 필요로 하는 이유는?","알을 낳기 위해서"),
          ("T/F : Mosquitoes helped shape the history of Rome.","T (맞음)")]

    def vc(items, mode):
        rows = ""
        for i, (a, b) in enumerate(items, 1):
            prompt = f"<span class='en'>{esc(a)}</span>" if mode == "e2k" else esc(a)
            rows += (f"<tr><td class='num'>{i}</td><td>{prompt}</td>"
                     f"<td><span class='writeline' style='min-width:100px'></span></td></tr>")
        return rows

    top = f"""
    <div class="examtop">
      <div class="nm">이름 <span class="u"></span> &nbsp; 날짜 <span class="u" style="min-width:80px"></span></div>
      <div class="score"><div class="s1">SCORE</div><div class="s2">&nbsp; / 100</div></div>
    </div>
    <div style="font-weight:800;font-size:14.5px;margin-bottom:2px;">Lesson 1 종합 테스트
      <span style="font-size:9.5px;color:#93a7a2;font-weight:400;">단어 · 문법 · 해석 · 독해</span></div>
    <div class="note" style="margin-bottom:9px;">아는 것부터 푸세요. 부분 점수도 있어요!</div>"""
    s1 = f"""<div class="sec"><div class="h"><span class="n">1</span><span class="t">단어 (20점)</span></div>
      <table style="width:100%"><tr>
        <td style="width:50%;vertical-align:top;padding-right:8px;"><div class="note" style="margin-bottom:3px;">(1) 영어 → 뜻</div>
          <table class="vtab" style="width:100%">{vc(e2k,'e2k')}</table></td>
        <td style="width:50%;vertical-align:top;padding-left:8px;"><div class="note" style="margin-bottom:3px;">(2) 뜻 → 영어</div>
          <table class="vtab" style="width:100%">{vc(k2e,'k2e')}</table></td></tr></table></div>"""
    s2 = ("<div class='sec'><div class='h'><span class='n'>2</span><span class='t'>문법 · 골라 동그라미 (20점)</span>"
          "<span class='tip'>한 문제 2점</span></div><ol class='q'>"
          + "".join(f"<li>{esc(q)} <span class='hint'>[{esc(t)}]</span></li>" for q, _, t in grammar)
          + "</ol></div>")
    s3 = ("<div class='sec pagebreak'><div class='h'><span class='n'>3</span><span class='t'>문장 해석 (25점)</span>"
          "<span class='tip'>밑줄에 우리말 뜻 쓰기 · 한 문제 5점</span></div><ol class='q'>"
          + "".join(f"<li>{esc(s)}<span class='wl-full'></span></li>" for s, _ in translate)
          + "</ol></div>")
    s4 = (f"<div class='sec'><div class='h'><span class='n'>4</span><span class='t'>짧은 지문 읽고 답하기 (35점)</span></div>"
          f"<div class='wordbank' style='color:{INK};font-weight:400;line-height:1.7;'>{esc(reading)}</div><ol class='q'>"
          + "".join(f"<li>{esc(q)}<span class='wl-full' style='width:70%'></span></li>" for q, _ in rq)
          + "</ol></div>")
    ans = f"""
    <div class="answers">
      <div class="tearline"><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>
      <div style="font-weight:800;font-size:13px;margin-bottom:6px;">✔ Lesson 1 종합 테스트 · 정답 &amp; 해설</div>
      <div class="ansrow"><div class="d">1. 단어</div><div class="b">
        (1) 영어→뜻 : {' · '.join(f"{i}.{esc(k)}" for i,(e,k) in enumerate(e2k,1))}<br>
        (2) 뜻→영어 : {' · '.join(f"{i}.{esc(v)}" for i,(k,v) in enumerate(k2e,1))}</div></div>
      <div class="ansrow"><div class="d">2. 문법</div><div class="b">
        {' · '.join(f"{i}.<b>{esc(a)}</b>" for i,(q,a,t) in enumerate(grammar,1))}</div></div>
      <div class="ansrow"><div class="d">3. 문장 해석</div><div class="b">
        {''.join(f"<div>{i}. {esc(a)}</div>" for i,(s,a) in enumerate(translate,1))}</div></div>
      <div class="ansrow"><div class="d">4. 독해</div><div class="b">
        {''.join(f"<div>{i}. {esc(a)}</div>" for i,(q,a) in enumerate(rq,1))}</div></div>
    </div>"""
    return top + s1 + s2 + s3 + s4 + ans


def wrap(inner, title):
    return f"<html><head><meta charset='utf-8'><title>{esc(title)}</title><style>{CSS}</style></head><body>{inner}</body></html>"


def to_pdf(inner, filename, title=""):
    weasyprint.HTML(string=wrap(inner, title or filename)).write_pdf(str(OUT / filename))
    print(f"  ✓ {filename}  ({(OUT/filename).stat().st_size//1024} KB)")


def main():
    print("PDF 생성 중 …")
    # 0) 월간 플랜
    to_pdf(render_month_plan(), "00_한달_학습플랜.pdf", "한 달 학습 플랜")

    # 1) 개별 숙제 9일 (학생용 + 정답 별지)
    for d in L1.DAYS:
        inner = render_day_student(d)
        inner += ("<div class='answers'><div class='tearline'><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>"
                  f"<div style='font-weight:800;font-size:12px;margin-bottom:5px;'>✔ {d['day']}일차 정답</div>"
                  + render_day_answer(d) + "</div>")
        to_pdf(inner, f"L1_{d['day']:02d}일차_{d['weekday']}_숙제_{d['title_en'].replace(' ','')}.pdf",
               f"{d['day']}일차 숙제")

    # 2) 10일차 총복습
    to_pdf(render_review_day_student(), "L1_10일차_금_1과총복습.pdf", "10일차 총복습")

    # 3) 합본 (표지 + 1~10일 학생용, 그다음 정답 전부)
    inner = render_cover()
    for d in L1.DAYS:
        inner += "<div class='pagebreak'></div>" + render_day_student(d)
    inner += "<div class='pagebreak'></div>" + render_review_day_student()
    # 정답 모음
    inner += "<div class='answers'><div class='tearline'><span>✂ 여기부터 선생님용 정답 (학생에게 주기 전 분리)</span></div>"
    inner += "<div style='font-weight:800;font-size:14px;margin-bottom:7px;'>✔ Lesson 1 숙제 · 선생님용 정답</div>"
    for d in L1.DAYS:
        inner += render_day_answer(d)
    inner += "</div>"
    to_pdf(inner, "L1_숙제_합본_1-2주차.pdf", "Lesson 1 숙제 합본")

    # 4) 단어 테스트 (주차별)
    to_pdf(render_vocab_test(range(1, 6), "1주차 단어 테스트 (1~5일차)"), "L1_테스트_1주차_단어.pdf")
    to_pdf(render_vocab_test(range(6, 10), "2주차 단어 테스트 (6~9일차)"), "L1_테스트_2주차_단어.pdf")

    # 5) 1과 종합 테스트
    to_pdf(render_comp_test(), "L1_테스트_1과_종합.pdf", "1과 종합 테스트")
    print("완료! → tutoring_materials/output/")


if __name__ == "__main__":
    main()
