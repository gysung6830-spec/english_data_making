# -*- coding: utf-8 -*-
"""
1주차 숙제 & 테스트 PDF 생성기 (WeasyPrint).
    python tutoring_materials/generate.py
결과: tutoring_materials/output/*.pdf
"""
from __future__ import annotations

import base64
import html
from pathlib import Path

import weasyprint

import content_week1 as C

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT.parent / "templates" / "fonts"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)


def _font_b64(name: str) -> str:
    return base64.b64encode((FONT_DIR / name).read_bytes()).decode()


FONT_R = _font_b64("NanumSquareRoundR.woff")
FONT_B = _font_b64("NanumSquareRoundB.woff")

# ── 색상 팔레트 (밝고 친근한 톤) ────────────────────────────────
INK = "#243b53"       # 본문
ACCENT = "#2a9d8f"    # 청록 (제목/포인트)
ACCENT2 = "#e76f51"   # 주황 (강조/정답)
SOFT = "#f2f7f6"      # 연한 배경
LINE = "#d7e3e1"      # 옅은 선
GOLD = "#f4a261"

CSS = f"""
@font-face {{ font-family:'NSR'; font-weight:400;
  src:url(data:font/woff;base64,{FONT_R}) format('woff'); }}
@font-face {{ font-family:'NSR'; font-weight:800;
  src:url(data:font/woff;base64,{FONT_B}) format('woff'); }}

@page {{
  size: A4; margin: 13mm 12mm 14mm 12mm;
  @bottom-center {{
    content: "{C.COPYRIGHT}  ·  " counter(page) " / " counter(pages);
    font-family:'NSR'; font-size:8.5px; color:#9fb3ae;
  }}
}}
* {{ box-sizing:border-box; }}
body {{ font-family:'NSR', sans-serif; color:{INK}; font-size:11.2px;
  line-height:1.5; margin:0; }}
b, strong {{ font-weight:800; }}
.en {{ font-weight:800; letter-spacing:.2px; }}

/* ── 페이지 상단 헤더 밴드 ── */
.head {{ border:2px solid {ACCENT}; border-radius:12px; overflow:hidden;
  margin-bottom:9px; page-break-inside:avoid; }}
.head .top {{ background:{ACCENT}; color:#fff; padding:7px 13px;
  display:flex; justify-content:space-between; align-items:center; }}
.head .top .badge {{ font-weight:800; font-size:13px; }}
.head .top .src {{ font-size:8.7px; opacity:.92; text-align:right; }}
.head .body {{ padding:9px 13px 10px; }}
.head .title {{ font-weight:800; font-size:16px; color:{INK}; }}
.head .title .k {{ color:{ACCENT}; }}
.head .part {{ font-size:9.3px; color:#7d918c; margin-top:1px; }}

.goal {{ background:{SOFT}; border:1px dashed {ACCENT}; border-radius:9px;
  padding:7px 11px; margin-top:8px; }}
.goal .g1 {{ font-weight:800; color:{ACCENT2}; font-size:11.6px; }}
.goal .g1 .flag {{ color:{ACCENT}; }}
.goal .g2 {{ font-size:10px; color:#5b6f6b; margin-top:2px; }}

/* ── 섹션 ── */
.sec {{ margin-top:11px; page-break-inside:avoid; }}
.sec > .h {{ display:flex; align-items:center; gap:7px; margin-bottom:6px; }}
.sec > .h .n {{ display:inline-flex; width:20px; height:20px; border-radius:50%;
  background:{ACCENT}; color:#fff; font-weight:800; font-size:11px;
  align-items:center; justify-content:center; flex:0 0 auto; }}
.sec > .h .t {{ font-weight:800; font-size:12.5px; }}
.sec > .h .tip {{ font-size:9px; color:#93a7a2; font-weight:400; margin-left:2px; }}

/* ── 표 ── */
table {{ border-collapse:collapse; width:100%; }}
.vtab td, .vtab th {{ border:1px solid {LINE}; padding:5px 7px; vertical-align:middle; }}
.vtab th {{ background:{SOFT}; font-weight:800; font-size:9.6px; color:#5b6f6b; }}
.vtab td.num {{ width:22px; text-align:center; color:#9fb3ae; font-size:9.5px; }}
.vtab td.w  {{ width:120px; }}
.vtab td.k  {{ width:150px; font-size:10.4px; }}
.vtab td.trace {{ color:#c9d6d3; }}   /* 흐린 따라쓰기 힌트 자리 */
.writeline {{ border-bottom:1.4px dotted #b9c9c5; display:inline-block;
  min-width:88px; height:15px; }}

/* 매칭 */
.match {{ display:flex; gap:22px; }}
.match .col {{ flex:1; }}
.match .row {{ display:flex; justify-content:space-between; padding:4.5px 4px;
  border-bottom:1px dotted {LINE}; font-size:10.6px; }}
.match .dot {{ color:{ACCENT}; }}

/* 빈칸/문항 리스트 */
ol.q {{ margin:0; padding-left:20px; }}
ol.q li {{ margin:5px 0; }}
.blank {{ display:inline-block; min-width:96px; border-bottom:1.6px solid {ACCENT};
  height:14px; }}
.hint {{ color:{ACCENT2}; font-size:9.3px; font-weight:800; }}
.wordbank {{ background:{SOFT}; border:1px solid {LINE}; border-radius:8px;
  padding:6px 10px; margin:5px 0 8px; font-weight:800; color:{ACCENT};
  font-size:10.5px; letter-spacing:.3px; }}
.wordbank .lab {{ color:#93a7a2; font-weight:800; margin-right:6px; }}

/* 첫 글자 힌트 */
.spell {{ font-family:'NSR'; font-weight:800; letter-spacing:2px; color:{INK}; }}

/* 정답 박스 */
.ans {{ margin-top:11px; background:#fff7f2; border:1px solid #f3d3c4;
  border-radius:9px; padding:8px 11px; page-break-inside:avoid; }}
.ans .h {{ font-weight:800; color:{ACCENT2}; font-size:10.6px; margin-bottom:3px; }}
.ans .b {{ font-size:9.6px; color:#7a5c50; line-height:1.6; }}
.ans .b b {{ color:{ACCENT2}; }}

/* 안내/도움말 */
.note {{ font-size:9px; color:#93a7a2; margin-top:3px; }}

/* 커버/표지 */
.cover {{ text-align:center; padding-top:70px; }}
.cover .kie {{ display:inline-block; border:2px solid {ACCENT}; color:{ACCENT};
  font-weight:800; padding:4px 14px; border-radius:20px; font-size:12px; }}
.cover h1 {{ font-size:30px; margin:20px 0 6px; color:{INK}; }}
.cover .sub {{ font-size:13px; color:{ACCENT2}; font-weight:800; }}
.cover .src {{ font-size:11px; color:#7d918c; margin-top:6px; }}
.cover .list {{ display:inline-block; text-align:left; margin-top:26px;
  background:{SOFT}; border:1px solid {LINE}; border-radius:12px; padding:16px 26px;
  font-size:12px; line-height:2; }}
.cover .list b {{ color:{ACCENT}; }}
.cover .tip {{ margin-top:24px; font-size:10.5px; color:#7d918c; }}

/* 테스트 상단 이름/점수 */
.examtop {{ display:flex; justify-content:space-between; align-items:flex-end;
  border-bottom:2px solid {ACCENT}; padding-bottom:6px; margin-bottom:10px; }}
.examtop .nm {{ font-size:10.5px; color:#5b6f6b; }}
.examtop .nm .u {{ display:inline-block; min-width:120px; border-bottom:1.4px solid #b9c9c5; }}
.examtop .score {{ text-align:center; border:2px solid {ACCENT2}; border-radius:9px;
  padding:4px 12px; }}
.examtop .score .s1 {{ font-size:8.5px; color:{ACCENT2}; font-weight:800; }}
.examtop .score .s2 {{ font-size:15px; font-weight:800; color:{INK}; }}

.pill {{ display:inline-block; background:{ACCENT}; color:#fff; font-weight:800;
  font-size:9px; padding:1.5px 8px; border-radius:20px; margin-right:6px; }}
.pill.o {{ background:{ACCENT2}; }}
.pagebreak {{ page-break-before:always; }}
"""


def esc(s: str) -> str:
    return html.escape(str(s))


def spell_hint(word: str) -> str:
    """첫 글자만 보여주고 나머지는 밑줄. 공백은 유지."""
    out = []
    for i, ch in enumerate(word):
        if ch == " ":
            out.append("&nbsp;&nbsp;")
        elif i == 0 or word[i - 1] == " ":
            out.append(esc(ch))
        else:
            out.append("_")
    return " ".join(out)


def page_footer_removed():
    return ""


# ──────────────────────────────────────────────────────────────
# 하루치 숙제 HTML
# ──────────────────────────────────────────────────────────────
def render_homework_day(d: dict) -> str:
    parts = []
    # 헤더
    parts.append(f"""
    <div class="head">
      <div class="top">
        <span class="badge">{d['day']}일차 · {d['weekday']}요일 숙제</span>
        <span class="src">{esc(C.SOURCE)}<br>{esc(d['part'])}</span>
      </div>
      <div class="body">
        <div class="title"><span class="k">{esc(d['title_en'])}</span> — {esc(d['title_ko'])}</div>
        <div class="part">오늘 배운 지문을 복습하는 숙제예요. 천천히, 소리 내어 하면 더 잘 외워져요.</div>
        <div class="goal">
          <div class="g1"><span class="flag">🎯 오늘의 문법</span> · {esc(d['goal_title'])}</div>
          <div class="g2">{esc(d['goal_desc'])}</div>
        </div>
      </div>
    </div>
    """)

    n = 0
    # STEP: 어제 단어 복습
    if d["review"]:
        n += 1
        rows = ""
        for en, ko in d["review"]:
            rows += (f"<tr><td class='num'>·</td><td class='w'><span class='en'>{esc(en)}</span></td>"
                     f"<td class='k'><span class='writeline'></span></td></tr>")
        parts.append(f"""
        <div class="sec">
          <div class="h"><span class="n">{n}</span><span class="t">어제 단어 복습</span>
            <span class="tip">뜻을 우리말로 써 보기 (기억 안 나면 넘어가도 OK)</span></div>
          <table class="vtab"><tr><th class="num">#</th><th>영어</th><th>뜻 쓰기</th></tr>{rows}</table>
        </div>""")

    # STEP: 오늘의 단어 (따라쓰기)
    n += 1
    rows = ""
    for i, (en, ko) in enumerate(d["words"], 1):
        rows += (
            f"<tr><td class='num'>{i}</td>"
            f"<td class='w'><span class='en'>{esc(en)}</span></td>"
            f"<td class='k'>{esc(ko)}</td>"
            f"<td class='trace'><span class='en'>{esc(en)}</span></td>"
            f"<td><span class='writeline'></span></td></tr>"
        )
    parts.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">오늘의 단어 10개 · 따라 쓰기</span>
        <span class="tip">연한 글씨를 덮어 쓰고 → 빈칸에 한 번 더 쓰기</span></div>
      <table class="vtab">
        <tr><th class="num">#</th><th>영어</th><th>뜻</th><th>따라 쓰기</th><th>한 번 더</th></tr>
        {rows}
      </table>
    </div>""")

    # STEP: 매칭
    n += 1
    import_words = d["words"]
    left = import_words
    # 오른쪽 뜻은 순서를 섞어 (역순) 매칭 난이도 부여
    right = list(reversed(import_words))
    lrows = "".join(
        f"<div class='row'><span class='en'>{esc(en)}</span><span class='dot'>◦</span></div>"
        for en, _ in left)
    rrows = "".join(
        f"<div class='row'><span class='dot'>◦</span><span>{esc(ko)}</span></div>"
        for _, ko in right)
    parts.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">짝 맞추기 · 선으로 잇기</span>
        <span class="tip">영어와 알맞은 뜻을 선으로 연결</span></div>
      <div class="match">
        <div class="col">{lrows}</div>
        <div class="col">{rrows}</div>
      </div>
    </div>""")

    # STEP: 첫 글자 힌트
    n += 1
    qi = ""
    for i, (en, ko) in enumerate(d["words"], 1):
        qi += (f"<li>{esc(ko)} &nbsp;→&nbsp; <span class='spell'>{spell_hint(en)}</span></li>")
    parts.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">첫 글자 보고 완성하기</span>
        <span class="tip">뜻을 보고, 밑줄 위에 알파벳을 채워 단어 완성</span></div>
      <ol class="q">{qi}</ol>
    </div>""")

    # STEP: 문장 빈칸 (word bank)
    n += 1
    bank = " · ".join(sorted({c[1] for c in d["cloze"]}))
    ci = ""
    for sent, ans, hh in d["cloze"]:
        s = esc(sent).replace("______", "<span class='blank'></span>")
        ci += f"<li>{s} <span class='hint'>({esc(hh)})</span></li>"
    parts.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">문장 속 빈칸 채우기</span>
        <span class="tip">지문에 나온 문장! 아래 단어 상자에서 골라 쓰기</span></div>
      <div class="wordbank"><span class="lab">단어 상자</span>{esc(bank)}</div>
      <ol class="q">{ci}</ol>
    </div>""")

    # STEP: 문법 한 입
    n += 1
    gi = ""
    for q, _ in d["grammar_q"]:
        gi += f"<li>{esc(q)}</li>"
    parts.append(f"""
    <div class="sec">
      <div class="h"><span class="n">{n}</span><span class="t">오늘의 문법 한 입 · 골라 동그라미</span>
        <span class="tip">{esc(d['goal_title'])}</span></div>
      <ol class="q">{gi}</ol>
    </div>""")

    # 정답
    ans_words = "  ·  ".join(f"<b>{esc(en)}</b> {esc(ko)}" for en, ko in d["words"])
    ans_spell = ", ".join(f"{esc(ko)}=<b>{esc(en)}</b>" for en, ko in d["words"])
    ans_cloze = ", ".join(f"<b>{esc(a)}</b>" for _, a, _ in d["cloze"])
    ans_gram = ", ".join(f"<b>{esc(a)}</b>" for _, a in d["grammar_q"])
    parts.append(f"""
    <div class="ans">
      <div class="h">✔ 정답 (채점은 부모님·선생님과 함께, 틀린 단어는 3번 더 쓰기)</div>
      <div class="b">
        <b>단어 뜻</b> — {ans_words}<br>
        <b>첫 글자 완성</b> — {ans_spell}<br>
        <b>문장 빈칸</b> — {ans_cloze}<br>
        <b>문법</b> — {ans_gram} <span style="color:#9d8">|</span> {esc(d['grammar_answer_note'])}
      </div>
    </div>""")

    return "".join(parts)


# ──────────────────────────────────────────────────────────────
# 표지
# ──────────────────────────────────────────────────────────────
def render_cover() -> str:
    days_list = "".join(
        f"<div><b>{d['day']}일차 ({d['weekday']})</b> · {esc(d['title_en'])} — {esc(d['title_ko'])}</div>"
        for d in C.DAYS)
    return f"""
    <div class="cover">
      <div class="kie">중등 기초 브릿지</div>
      <h1>1주차 숙제 &amp; 테스트</h1>
      <div class="sub">The Nuisance &amp; The Predator (모기 이야기 ①~⑤)</div>
      <div class="src">{esc(C.SOURCE)}</div>
      <div class="list">
        <div style="font-weight:800;color:{ACCENT2};margin-bottom:6px;">📚 이번 주 숙제 (월~금)</div>
        {days_list}
        <div style="margin-top:12px;font-weight:800;color:{ACCENT2};">📝 주말 테스트</div>
        <div>· 단어 테스트 (핵심 50단어)</div>
        <div>· 종합 테스트 (단어 · 문법 · 해석 · 독해)</div>
      </div>
      <div class="tip">
        하루 숙제는 10~15분이면 충분해요.<br>
        <b>소리 내어 읽기 → 따라 쓰기 → 뜻 말하기</b> 순서로 하면 단어가 오래 남아요.
      </div>
    </div>
    """


# ──────────────────────────────────────────────────────────────
# 주말 단어 테스트
# ──────────────────────────────────────────────────────────────
def render_vocab_test() -> str:
    def two_col(items, mode):
        # mode 'en2ko': 영어 제시, 뜻 쓰기 / 'ko2en': 뜻 제시, 영어 쓰기
        half = (len(items) + 1) // 2
        cols = [items[:half], items[half:]]
        tds = []
        for col in cols:
            rows = ""
            for idx, it in enumerate(col):
                num = it[3]
                if mode == "en2ko":
                    prompt = f"<span class='en'>{esc(it[0])}</span>"
                else:
                    prompt = esc(it[1])
                rows += (f"<tr><td class='num'>{num}</td><td>{prompt}</td>"
                         f"<td><span class='writeline' style='min-width:120px'></span></td></tr>")
            tds.append(f"<td style='vertical-align:top;padding:0 6px;'><table class='vtab' style='width:100%'>{rows}</table></td>")
        return "<table style='width:100%'><tr>" + "".join(tds) + "</tr></table>"

    a = [(en, ko, day, i + 1) for i, (en, ko, day) in enumerate(C.VOCAB_TEST_EN2KO)]
    b = [(en, ko, day, i + 1) for i, (en, ko, day) in enumerate(C.VOCAB_TEST_KO2EN)]

    body = f"""
    <div class="examtop">
      <div class="nm">이름 <span class="u"></span> &nbsp;&nbsp; 날짜 <span class="u" style="min-width:90px"></span></div>
      <div class="score"><div class="s1">SCORE</div><div class="s2">&nbsp; / 50</div></div>
    </div>
    <div style="font-weight:800;font-size:15px;color:{INK};margin-bottom:2px;">
      1주차 단어 테스트 <span style="font-size:10px;color:#93a7a2;font-weight:400;">핵심 50단어</span></div>
    <div class="note" style="margin-bottom:10px;">A는 영어를 보고 <b>뜻</b>을, B는 뜻을 보고 <b>영어</b>를 쓰세요. 한 문제 1점.</div>

    <div class="sec"><div class="h"><span class="n">A</span><span class="t">영어 → 우리말 뜻 쓰기</span>
      <span class="tip">25문</span></div>{two_col(a, "en2ko")}</div>

    <div class="sec pagebreak"><div class="h"><span class="n">B</span><span class="t">우리말 → 영어 단어 쓰기</span>
      <span class="tip">25문 · 철자까지 정확히</span></div>{two_col(b, "ko2en")}</div>
    """

    # 정답지 (별도 페이지)
    def ans_block(items, mode, title):
        rows = ""
        for i, (en, ko, day) in enumerate(items, 1):
            val = ko if mode == "en2ko" else en
            key = en if mode == "en2ko" else ko
            rows += f"<span style='display:inline-block;width:33%;font-size:9.4px;margin:2px 0;'>{i}. <b>{esc(key)}</b> — {esc(val)}</span>"
        return f"<div style='font-weight:800;color:{ACCENT2};margin:8px 0 3px;'>{title}</div><div>{rows}</div>"

    ans = f"""
    <div class="pagebreak">
      <div style="font-weight:800;font-size:14px;color:{INK};margin-bottom:8px;">✔ 1주차 단어 테스트 · 정답</div>
      {ans_block([(e,k,d) for e,k,d in C.VOCAB_TEST_EN2KO], "en2ko", "A. 영어 → 뜻")}
      {ans_block([(e,k,d) for e,k,d in C.VOCAB_TEST_KO2EN], "ko2en", "B. 뜻 → 영어")}
      <div class="note" style="margin-top:12px;">틀린 단어는 다음 주 숙제 '어제 단어 복습'에 다시 넣어 반복하세요.</div>
    </div>
    """
    return body + ans


# ──────────────────────────────────────────────────────────────
# 종합 테스트
# ──────────────────────────────────────────────────────────────
def render_comp_test() -> str:
    # S1 단어
    def vc_rows(items, mode):
        rows = ""
        for i, it in enumerate(items, 1):
            prompt = f"<span class='en'>{esc(it[0])}</span>" if mode == "en2ko" else esc(it[0])
            rows += (f"<tr><td class='num'>{i}</td><td>{prompt}</td>"
                     f"<td><span class='writeline' style='min-width:110px'></span></td></tr>")
        return rows
    s1 = f"""
    <div class="sec"><div class="h"><span class="n">1</span><span class="t">단어 (20점)</span>
      <span class="tip">뜻/영어를 쓰세요</span></div>
      <table style="width:100%"><tr>
        <td style="width:50%;vertical-align:top;padding-right:8px;">
          <div class="note" style="margin-bottom:3px;">(1) 영어 → 뜻</div>
          <table class="vtab" style="width:100%">{vc_rows(C.COMP_VOCAB_EN2KO, "en2ko")}</table></td>
        <td style="width:50%;vertical-align:top;padding-left:8px;">
          <div class="note" style="margin-bottom:3px;">(2) 뜻 → 영어</div>
          <table class="vtab" style="width:100%">{vc_rows(C.COMP_VOCAB_KO2EN, "ko2en")}</table></td>
      </tr></table>
    </div>"""

    # S2 문법
    gi = ""
    for q, _, typ in C.COMP_GRAMMAR:
        gi += f"<li>{esc(q)} <span class='hint'>[{esc(typ)}]</span></li>"
    s2 = f"""
    <div class="sec"><div class="h"><span class="n">2</span><span class="t">문법 · 골라 동그라미 (20점)</span>
      <span class="tip">한 문제 2점</span></div>
      <ol class="q">{gi}</ol>
    </div>"""

    # S3 해석
    ti = "".join(f"<li>{esc(s)}<br><span class='writeline' style='min-width:96%;margin-top:3px;'></span></li>"
                 for s in C.COMP_TRANSLATE)
    s3 = f"""
    <div class="sec pagebreak"><div class="h"><span class="n">3</span><span class="t">문장 해석 (25점)</span>
      <span class="tip">밑줄에 우리말 뜻을 쓰세요 · 한 문제 5점</span></div>
      <ol class="q">{ti}</ol>
    </div>"""

    # S4 독해
    ri = "".join(f"<li>{esc(q)}<br><span class='writeline' style='min-width:70%;margin-top:3px;'></span></li>"
                 for q, _ in C.COMP_READING_Q)
    s4 = f"""
    <div class="sec"><div class="h"><span class="n">4</span><span class="t">짧은 지문 읽고 답하기 (35점)</span>
      <span class="tip">지문을 읽고 우리말로 답하기</span></div>
      <div class="wordbank" style="color:{INK};font-weight:400;line-height:1.7;background:{SOFT};">
        {esc(C.COMP_READING)}</div>
      <ol class="q">{ri}</ol>
    </div>"""

    top = f"""
    <div class="examtop">
      <div class="nm">이름 <span class="u"></span> &nbsp;&nbsp; 날짜 <span class="u" style="min-width:90px"></span></div>
      <div class="score"><div class="s1">SCORE</div><div class="s2">&nbsp; / 100</div></div>
    </div>
    <div style="font-weight:800;font-size:15px;color:{INK};margin-bottom:2px;">
      1주차 종합 테스트 <span style="font-size:10px;color:#93a7a2;font-weight:400;">단어 · 문법 · 해석 · 독해</span></div>
    <div class="note" style="margin-bottom:10px;">모르는 문제는 넘어가고, 아는 것부터 푸세요. 부분 점수도 있어요!</div>
    """

    # 정답 & 해설
    a1 = " · ".join(f"{i}.{esc(k)}" for i, (e, k) in enumerate(C.COMP_VOCAB_EN2KO, 1))
    a1b = " · ".join(f"{i}.{esc(k)}" for i, (kk, k) in enumerate(C.COMP_VOCAB_KO2EN, 1))
    a2 = " · ".join(f"{i}.<b>{esc(a)}</b>" for i, (q, a, t) in enumerate(C.COMP_GRAMMAR, 1))
    a3 = "".join(f"<div>{i}. {esc(t)}</div>" for i, t in enumerate(C.COMP_TRANSLATE_ANS, 1))
    a4 = "".join(f"<div>{i}. {esc(a)}</div>" for i, (q, a) in enumerate(C.COMP_READING_Q, 1))
    ans = f"""
    <div class="pagebreak">
      <div style="font-weight:800;font-size:14px;color:{INK};margin-bottom:8px;">✔ 1주차 종합 테스트 · 정답 &amp; 해설</div>
      <div class="ans"><div class="h">1. 단어</div>
        <div class="b">(1) 영어→뜻 : {a1}<br>(2) 뜻→영어 : {a1b}</div></div>
      <div class="ans"><div class="h">2. 문법</div><div class="b">{a2}</div></div>
      <div class="ans"><div class="h">3. 문장 해석</div><div class="b">{a3}</div></div>
      <div class="ans"><div class="h">4. 독해</div><div class="b">{a4}</div></div>
    </div>
    """
    return top + s1 + s2 + s3 + s4 + ans


def wrap(inner: str, title: str) -> str:
    return f"<html><head><meta charset='utf-8'><title>{esc(title)}</title><style>{CSS}</style></head><body>{inner}</body></html>"


def to_pdf(html_str: str, filename: str):
    path = OUT / filename
    weasyprint.HTML(string=html_str).write_pdf(str(path))
    print(f"  ✓ {filename}  ({path.stat().st_size//1024} KB)")
    return path


def main():
    print("PDF 생성 중 …")
    # 1) 개별 숙제 5장
    for d in C.DAYS:
        h = wrap(render_homework_day(d), f"{d['day']}일차 숙제")
        to_pdf(h, f"1주차_{d['day']}일차_{d['weekday']}_숙제_{d['title_en'].replace(' ','')}.pdf")

    # 2) 숙제 전체 합본 (표지 + 5일)
    inner = render_cover()
    for d in C.DAYS:
        inner += "<div class='pagebreak'></div>" + render_homework_day(d)
    to_pdf(wrap(inner, "1주차 숙제 합본"), "1주차_숙제_합본_월-금.pdf")

    # 3) 단어 테스트
    to_pdf(wrap(render_vocab_test(), "1주차 단어 테스트"), "1주차_단어테스트.pdf")

    # 4) 종합 테스트
    to_pdf(wrap(render_comp_test(), "1주차 종합 테스트"), "1주차_종합테스트.pdf")

    print("완료! → tutoring_materials/output/")


if __name__ == "__main__":
    main()
