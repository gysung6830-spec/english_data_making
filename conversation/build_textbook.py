# -*- coding: utf-8 -*-
"""
중학 영어 회화 교재 PDF 생성기 (가로 2단: 템플릿 + 워드뱅크).

사용법:
    python conversation/build_textbook.py
    ->  output/중학영어회화교재_OPIC10.pdf 생성

- 가로(landscape) A4, 페이지당 한 단원
- 왼쪽: 내 의견 말하기 5단계 템플릿 / 오른쪽: 워드뱅크
- 대화문 없음. OPIC 주제로 '내 의견'을 말하는 연습용.
콘텐츠(단어/문장)는 conversation/textbook_data.py 에서만 고치면 됩니다.
"""
from __future__ import annotations

import html as _html
from pathlib import Path

import textbook_data as data

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "중학영어회화교재_OPIC10.pdf"

# 단원마다 돌아가며 쓰는 헤더 강조색
ACCENTS = ["#445fb0", "#3d8f58", "#6a54b3", "#cf8a2a", "#cd5049",
           "#2f877e", "#445fb0", "#3d8f58", "#6a54b3", "#cf8a2a"]


def esc(s: str) -> str:
    return _html.escape(str(s))


CSS = """
@page {
  size: A4 landscape;
  margin: 10mm 12mm 12mm 12mm;
  @bottom-center {
    content: "중학 영어 회화 교재  ·  " counter(page) " / " counter(pages);
    font-family: "NanumGothic", sans-serif; font-size: 8px; color: #9aa0a6;
  }
}
* { box-sizing: border-box; }
body {
  font-family: "NanumGothic", "Nanum Gothic", "Malgun Gothic", sans-serif;
  color: #23272e; font-size: 11px; line-height: 1.45; margin: 0;
}
:root {
  --blue:#445fb0; --green:#3d8f58; --purple:#6a54b3;
  --amber:#cf8a2a; --red:#cd5049; --teal:#2f877e;
  --line:#e5e7eb; --muted:#6b7280; --soft:#f7faf8;
}

/* ---------- 표지 ---------- */
.cover { text-align:center; padding-top: 48mm; page-break-after: always; }
.cover .kicker { display:inline-block; background:#111827; color:#fff;
  font-size:12px; font-weight:700; padding:5px 14px; border-radius:6px; letter-spacing:1px; }
.cover h1 { font-size:40px; font-weight:800; margin:18px 0 8px; color:#1a1f2b; }
.cover .sub { font-size:15px; color:var(--muted); margin-bottom:30px; }
.cover .emojis { font-size:32px; letter-spacing:8px; margin-top:26px; }
.cover .band { height:8px; width:60%; margin:22px auto 0;
  background:linear-gradient(90deg,var(--blue),var(--green),var(--purple),var(--amber),var(--red)); border-radius:8px; }

.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
h2.section-title { font-size:18px; font-weight:800; margin:0 0 10px;
  border-bottom:3px solid #111827; padding-bottom:6px; }

/* ---------- 가로 2단 레이아웃 ---------- */
.two { display:flex; gap:14px; align-items:stretch; }
.col-left  { flex:0 0 57%; }
.col-right { flex:1 1 43%; }

/* ---------- 단원 헤더 ---------- */
.unit-head { display:flex; align-items:center; gap:12px;
  color:#fff; padding:7px 16px; border-radius:10px; margin-bottom:8px; }
.unit-head .emoji { font-size:24px; }
.unit-head .no { font-size:9px; font-weight:700; opacity:.9; letter-spacing:1px; }
.unit-head .ko { font-size:18px; font-weight:800; line-height:1.15; }
.unit-head .en { font-size:10px; opacity:.92; }
.unit-head .prompt { margin-left:auto; text-align:right; font-size:11px;
  background:rgba(255,255,255,.18); padding:5px 10px; border-radius:8px; max-width:44%; }
.unit-head .prompt .q { font-weight:700; }

/* ---------- 블록 공통 ---------- */
.block { border:1.5px solid var(--line); border-radius:10px; overflow:hidden; height:100%; }
.block > .bar { color:#fff; font-weight:800; font-size:12px; padding:7px 13px; letter-spacing:.3px; }
.block > .body { padding:11px 14px; }

/* 템플릿(왼쪽) */
.tpl .step { margin:0 0 14px; }
.tpl .slabel { font-weight:800; color:var(--purple); font-size:12px; margin-bottom:3px; }
.tpl .en { font-weight:600; font-size:13px; line-height:1.45; }
.tpl .ko { color:var(--muted); font-size:10.5px; line-height:1.35; margin-bottom:2px; }
.tpl .en .bk { color:var(--red); font-weight:800; }
.tpl .hint { color:var(--muted); font-size:10px; margin-top:8px; border-top:1px dashed var(--line); padding-top:7px; }

/* 빈칸 번호 배지 */
.bn { display:inline-block; min-width:13px; height:13px; line-height:13px; text-align:center;
  background:var(--red); color:#fff; font-size:8.5px; font-weight:800; border-radius:4px;
  padding:0 3px; margin-left:2px; vertical-align:middle; }

/* 워드뱅크(오른쪽) = 빈칸에 넣을 보기 단어 */
.wb .wrow { display:flex; gap:9px; padding:8.5px 6px; border-bottom:1px solid #eef1ee; align-items:baseline; }
.wb .wrow:last-child { border-bottom:none; }
.wb .wrow:nth-child(odd) { background:var(--soft); }
.wb .wrow .bn { flex:0 0 auto; min-width:16px; height:16px; line-height:16px; font-size:10px; }
.wb .wrow .ws { font-size:10.5px; color:#23272e; line-height:1.45; }
.wb .wrow .ws b { color:#111827; font-weight:700; }
.wb .wrow .ws .m { color:#6b7280; }

/* ---------- 사용법/표현 페이지 ---------- */
.card { border:1.5px solid var(--line); border-radius:10px; padding:12px 14px; height:100%; }
.card h3 { margin:0 0 8px; font-size:13px; }
.howto .step { margin:7px 0; }
.howto .step b { color:var(--blue); }
.steps .s { display:flex; gap:8px; margin:6px 0; }
.steps .s .n { font-weight:800; color:var(--purple); flex:0 0 auto; }
.steps .s .d { color:#374151; }
.steps .s .d .t { font-weight:700; }

/* 표현 모음 */
.expr { display:flex; flex-wrap:wrap; gap:10px; }
.expr .grp { flex:1 1 46%; border:1.5px solid var(--line); border-radius:10px; overflow:hidden; }
.expr .grp .h { background:var(--teal); color:#fff; font-weight:800; font-size:11px; padding:5px 10px; }
.expr .grp table { width:100%; border-collapse:collapse; }
.expr .grp td { padding:4px 10px; border-bottom:1px solid #eef1ee; font-size:10px; }
.expr .grp .en { font-weight:700; width:52%; }
.expr .grp .ko { color:var(--muted); }

/* 목차 */
.toc { display:flex; flex-wrap:wrap; gap:8px; }
.toc .row { flex:1 1 46%; display:flex; align-items:center; gap:10px;
  border:1.5px solid var(--line); border-radius:9px; padding:7px 12px; }
.toc .num { font-weight:800; color:var(--muted); }
.toc .em { font-size:18px; }
.toc .ko { font-weight:700; }
.toc .en { color:var(--muted); font-size:10px; margin-left:6px; }

/* 부록 · 단어 사전 (자동 생성) */
.glossary { columns:3; column-gap:14px; }
.appendix .grow { break-inside:avoid; display:flex; justify-content:space-between; gap:8px;
  padding:3.5px 8px; border-bottom:1px solid #eef1ee; font-size:10px; }
.appendix .grow .ge { font-weight:700; color:#111827; }
.appendix .grow .gk { color:#6b7280; text-align:right; }
"""


def bold_blanks(text: str) -> str:
    """빈칸(____)을 빨간 강조로 표시하고 나머지는 이스케이프."""
    parts = text.split("____")
    out = esc(parts[0])
    for p in parts[1:]:
        out += '<span class="bk">____</span>' + esc(p)
    return out


def cover_html() -> str:
    emojis = " ".join(u["emoji"] for u in data.UNITS)
    return f"""
    <div class="cover">
      <div class="kicker">MIDDLE SCHOOL ENGLISH</div>
      <h1>{esc(data.TITLE)}</h1>
      <div class="sub">{esc(data.SUBTITLE)}</div>
      <div class="band"></div>
      <div class="emojis">{emojis}</div>
    </div>
    """


def intro_html() -> str:
    # 왼쪽: 사용법 + 5단계 설명 / 오른쪽: 목차
    steps = "".join(f'<div class="step"><b>{esc(t)}</b> — {esc(d)}</div>' for t, d in data.HOW_TO_USE)
    guide = "".join(
        f'<div class="s"><div class="n">{esc(lbl.split()[0])}</div>'
        f'<div class="d"><span class="t">{esc(lbl[1:].strip())}</span> — {esc(desc)}</div></div>'
        for lbl, desc in data.STEPS_GUIDE
    )
    toc = ""
    for i, u in enumerate(data.UNITS, 1):
        toc += (f'<div class="row"><span class="num">{i:02d}</span>'
                f'<span class="em">{u["emoji"]}</span>'
                f'<span><span class="ko">{esc(u["title_ko"])}</span>'
                f'<span class="en">{esc(u["title_en"])}</span></span></div>')
    return f"""
    <div class="page">
      <h2 class="section-title">이 교재 사용법 & 내 의견 말하기 5단계</h2>
      <div class="two">
        <div class="col-left">
          <div class="card howto">
            <h3>📖 사용법</h3>
            {steps}
          </div>
        </div>
        <div class="col-right">
          <div class="card steps">
            <h3>🗂️ 내 의견 말하기 5단계 (모든 단원 공통)</h3>
            {guide}
          </div>
        </div>
      </div>
      <h2 class="section-title" style="margin-top:14px;">목차 (OPIC 주제 {len(data.UNITS)}개)</h2>
      <div class="toc">{toc}</div>
    </div>
    """


def expressions_html() -> str:
    grps = ""
    for i, (name, rows) in enumerate(data.EXPRESSIONS):
        trs = "".join(f'<tr><td class="en">{esc(en)}</td><td class="ko">{esc(ko)}</td></tr>'
                      for en, ko in rows)
        grps += (f'<div class="grp"><div class="h">{esc(name)}</div>'
                 f'<table>{trs}</table></div>')
    return f"""
    <div class="page">
      <h2 class="section-title">핵심 표현 모음 · 의견을 말할 때 쓰는 연결어</h2>
      <p style="color:var(--muted); font-size:10.5px; margin:0 2px 12px;">
        아래 표현들을 5단계 템플릿의 빈칸을 이어 주는 '접착제'처럼 쓰면 훨씬 자연스러운 말하기가 됩니다.
      </p>
      <div class="expr">{grps}</div>
    </div>
    """


def unit_html(idx: int, u: dict) -> str:
    accent = ACCENTS[(idx - 1) % len(ACCENTS)]

    # 빈칸에 순서대로 번호를 매기고, 왼쪽=번호 붙은 문장 / 오른쪽 워드뱅크=번호별 보기 단어
    n = 0
    steps_html = ""
    bank = []  # (번호, [보기 단어들])
    for st in u["template"]:
        lines = ""
        for en, ko, choices in st["lines"]:
            parts = en.split("____")
            html_en = esc(parts[0])
            for k, tail in enumerate(parts[1:]):
                n += 1
                opts = choices[k] if k < len(choices) else []
                bank.append((n, opts))
                html_en += (f'<span class="bk">____</span><span class="bn">{n}</span>'
                            + esc(tail))
            lines += f'<div class="en">{html_en}</div><div class="ko">{esc(ko)}</div>'
        steps_html += f'<div class="step"><div class="slabel">{esc(st["label"])}</div>{lines}</div>'

    # 오른쪽 워드뱅크: 각 빈칸 번호에 넣을 보기 단어 (영어 + 한글 뜻)
    wb_rows = ""
    for num, opts in bank:
        words = " · ".join(f'<b>{esc(oe)}</b> <span class="m">{esc(ok)}</span>'
                           for oe, ok in opts)
        wb_rows += (f'<div class="wrow"><span class="bn">{num}</span>'
                    f'<span class="ws">{words}</span></div>')

    return f"""
    <div class="page">
      <div class="unit-head" style="background:{accent};">
        <div class="emoji">{u["emoji"]}</div>
        <div>
          <div class="no">UNIT {idx:02d}</div>
          <div class="ko">{esc(u["title_ko"])}</div>
          <div class="en">{esc(u["title_en"])}</div>
        </div>
        <div class="prompt"><div class="q">🎤 {esc(u["prompt"])}</div>
          <div style="opacity:.9; font-size:9.5px;">이 질문에 '내 의견'으로 답해 보세요</div></div>
      </div>
      <div class="two">
        <div class="col-left">
          <div class="block tpl">
            <div class="bar" style="background:var(--purple);">✏️ 내 의견 말하기 템플릿 · Speak Your Opinion</div>
            <div class="body">
              {steps_html}
              <div class="hint">빨간 빈칸 <span class="bn">번호</span> 에 맞춰, 오른쪽 워드뱅크의 같은 번호 보기에서 단어를 골라 넣어 ①~⑤를 이어서 말해 보세요.</div>
            </div>
          </div>
        </div>
        <div class="col-right">
          <div class="block wb">
            <div class="bar" style="background:var(--green);">📚 워드뱅크 · 빈칸에 넣을 말 (번호 = 왼쪽 빈칸)</div>
            <div class="body">{wb_rows}</div>
          </div>
        </div>
      </div>
    </div>
    """


def appendix_html() -> str:
    # 모든 단원의 보기 중 '한 단어' 어휘만 자동 수집해 알파벳순 사전으로 만든다
    # (구/문장 형태의 보기는 각 단원 워드뱅크에서 맥락과 함께 익히므로 제외)
    glossary = {}
    for u in data.UNITS:
        for st in u["template"]:
            for _en, _ko, choices in st["lines"]:
                for opts in choices:
                    for oe, ok in opts:
                        if " " not in oe:  # 한 단어만
                            glossary.setdefault(oe, ok)
    items = sorted(glossary.items(), key=lambda kv: kv[0].lower())

    rows = "".join(
        f'<div class="grow"><span class="ge">{esc(oe)}</span>'
        f'<span class="gk">{esc(ok)}</span></div>'
        for oe, ok in items
    )
    return f"""
    <div class="page appendix">
      <h2 class="section-title">부록 · 핵심 단어 사전 ({len(items)}개)</h2>
      <p style="color:var(--muted); font-size:10px; margin:0 2px 10px;">
        워드뱅크 보기 중 '한 단어' 어휘를 알파벳순으로 모았어요. 아는 단어에 ✓ 표시하며 복습해 보세요.
      </p>
      <div class="glossary">{rows}</div>
    </div>
    """


def build() -> Path:
    body = cover_html() + intro_html() + expressions_html()
    for i, u in enumerate(data.UNITS, 1):
        body += unit_html(i, u)
    body += appendix_html()

    doc = f"<!doctype html><html><head><meta charset='utf-8'></head><body>{body}</body></html>"

    from weasyprint import CSS as WCSS, HTML  # 지연 임포트(무거움)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=doc).write_pdf(str(OUT), stylesheets=[WCSS(string=CSS)])
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"완성: {p}")
