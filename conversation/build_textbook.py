# -*- coding: utf-8 -*-
"""
초등 영어 회화 교재 PDF 생성기 (HTML + CSS -> WeasyPrint).

사용법:
    python conversation/build_textbook.py
    ->  output/초등영어회화교재_OPIC10.pdf 생성

콘텐츠(단어/문장/대화)는 conversation/textbook_data.py 에서만 고치면 됩니다.
디자인은 기존 저장소의 5색 팔레트(파랑/초록/보라/노랑/빨강+청록)를 따릅니다.
"""
from __future__ import annotations

import html as _html
from pathlib import Path

import textbook_data as data

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "초등영어회화교재_OPIC10.pdf"

# 단원마다 돌아가며 쓰는 헤더 강조색 (시각적 변화용)
ACCENTS = ["#445fb0", "#3d8f58", "#6a54b3", "#cf8a2a", "#cd5049",
           "#2f877e", "#445fb0", "#3d8f58", "#6a54b3", "#cf8a2a"]


def esc(s: str) -> str:
    return _html.escape(str(s))


CSS = """
@page {
  size: A4;
  margin: 11mm 12mm 13mm 12mm;
  @bottom-center {
    content: "초등 영어 회화 교재  ·  " counter(page) " / " counter(pages);
    font-family: "NanumGothic", sans-serif; font-size: 8px; color: #9aa0a6;
  }
}
* { box-sizing: border-box; }
body {
  font-family: "NanumGothic", "Nanum Gothic", "Malgun Gothic", sans-serif;
  color: #23272e; font-size: 10px; line-height: 1.4; margin: 0;
}
:root {
  --blue:#445fb0; --green:#3d8f58; --purple:#6a54b3;
  --amber:#cf8a2a; --red:#cd5049; --teal:#2f877e;
  --line:#e5e7eb; --muted:#6b7280;
}

/* ---------- 표지 ---------- */
.cover { text-align:center; padding-top: 55mm; page-break-after: always; }
.cover .kicker { display:inline-block; background:#111827; color:#fff;
  font-size:12px; font-weight:700; padding:5px 14px; border-radius:6px; letter-spacing:1px; }
.cover h1 { font-size:38px; font-weight:800; margin:20px 0 8px; color:#1a1f2b; }
.cover .sub { font-size:15px; color:var(--muted); margin-bottom:36px; }
.cover .emojis { font-size:34px; letter-spacing:6px; margin-top:30px; }
.cover .band { height:8px; width:70%; margin:26px auto 0;
  background:linear-gradient(90deg,var(--blue),var(--green),var(--purple),var(--amber),var(--red)); border-radius:8px; }

/* ---------- 공통 섹션 ---------- */
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
h2.section-title { font-size:19px; font-weight:800; margin:0 0 12px;
  border-bottom:3px solid #111827; padding-bottom:6px; }

/* ---------- 사용법 / 목차 ---------- */
.howto { border:1.5px solid var(--line); border-radius:10px; padding:12px 16px; margin-bottom:14px; }
.howto .step { margin:8px 0; }
.howto .step b { color:var(--blue); }
.toc { border:1.5px solid var(--line); border-radius:10px; padding:6px 0; }
.toc .row { display:flex; align-items:center; padding:7px 16px; border-bottom:1px solid #f0f0f2; }
.toc .row:last-child { border-bottom:none; }
.toc .num { width:30px; font-weight:800; color:var(--muted); }
.toc .em { width:34px; font-size:18px; }
.toc .ko { font-weight:700; }
.toc .en { color:var(--muted); margin-left:8px; font-size:10px; }

/* ---------- 단원 헤더 ---------- */
.unit-head { display:flex; align-items:center; gap:11px;
  color:#fff; padding:8px 14px; border-radius:11px; margin-bottom:9px; }
.unit-head .emoji { font-size:24px; }
.unit-head .no { font-size:10px; font-weight:700; opacity:.9; letter-spacing:1px; }
.unit-head .ko { font-size:19px; font-weight:800; line-height:1.15; }
.unit-head .en { font-size:11px; opacity:.92; }

/* ---------- 블록 공통 ---------- */
.block { border:1.5px solid var(--line); border-radius:9px; margin-bottom:8px; overflow:hidden;
  page-break-inside: avoid; }
.block > .bar { color:#fff; font-weight:800; font-size:11px; padding:5px 11px; letter-spacing:.3px; }
.block > .body { padding:8px 11px; }

/* 워드뱅크 (2단) */
.wb .body { padding:6px 8px; }
.wb .cols { display:flex; gap:14px; }
.wb table { width:50%; border-collapse:collapse; }
.wb td { padding:3px 6px; border-bottom:1px solid #f0f0f2; vertical-align:top; }
.wb .en { font-weight:700; width:38%; }
.wb .ko { width:34%; }
.wb .read { color:var(--muted); font-size:9px; }
.wb tr:nth-child(odd) td { background:#f7faf8; }

/* 패턴 (Q/A) */
.pat { margin:5px 0; padding-left:9px; border-left:3px solid var(--blue); }
.pat .q { font-weight:700; }
.pat .q .ko, .pat .a .ko { color:var(--muted); font-weight:400; font-size:9px; margin-left:6px; }
.pat .a { margin-top:1px; }
.pat .a::before { content:"→ "; color:var(--blue); font-weight:800; }

/* 대화 */
.dia .line { display:flex; gap:7px; margin:4px 0; }
.dia .who { flex:0 0 20px; height:20px; border-radius:50%; color:#fff; font-weight:800;
  text-align:center; line-height:20px; font-size:10px; }
.dia .who.A { background:var(--amber); }
.dia .who.B { background:var(--teal); }
.dia .txt .en { font-weight:600; }
.dia .txt .ko { color:var(--muted); font-size:9px; }

/* 나만의 대답 */
.tpl .row { margin:7px 0; font-size:12px; font-weight:600; }
.tpl .hint { color:var(--muted); font-size:9px; margin-top:2px; font-weight:400; }

/* 부록 워드뱅크 */
.appendix table { width:100%; border-collapse:collapse; font-size:10px; }
.appendix th { background:#111827; color:#fff; padding:6px; text-align:left; }
.appendix td { padding:4px 6px; border-bottom:1px solid #eee; }
.appendix .cat { font-weight:800; color:#fff; padding:5px 8px; }
"""


def cover_html() -> str:
    emojis = " ".join(u["emoji"] for u in data.UNITS)
    return f"""
    <div class="cover">
      <div class="kicker">ELEMENTARY ENGLISH</div>
      <h1>{esc(data.TITLE)}</h1>
      <div class="sub">{esc(data.SUBTITLE)}</div>
      <div class="band"></div>
      <div class="emojis">{emojis}</div>
    </div>
    """


def intro_html() -> str:
    steps = "".join(
        f'<div class="step"><b>{esc(t)}</b> — {esc(d)}</div>'
        for t, d in data.HOW_TO_USE
    )
    rows = ""
    for i, u in enumerate(data.UNITS, 1):
        rows += (
            f'<div class="row"><div class="num">{i:02d}</div>'
            f'<div class="em">{u["emoji"]}</div>'
            f'<div><span class="ko">{esc(u["title_ko"])}</span>'
            f'<span class="en">{esc(u["title_en"])}</span></div></div>'
        )
    return f"""
    <div class="page">
      <h2 class="section-title">이 교재 사용법</h2>
      <div class="howto">{steps}</div>
      <p style="color:var(--muted); font-size:10px; margin:2px 4px 16px;">
        모든 단원은 <b>워드뱅크 → 핵심 표현 → 대화 예시 → 나만의 대답</b> 순서의 같은 템플릿으로 되어 있어요.
        한 단원에 익숙해지면 다른 단원도 똑같은 방법으로 공부할 수 있어요.
      </p>
      <h2 class="section-title">목차 (OPIC 주제 10개)</h2>
      <div class="toc">{rows}</div>
    </div>
    """


def unit_html(idx: int, u: dict) -> str:
    accent = ACCENTS[(idx - 1) % len(ACCENTS)]

    # 워드뱅크 (2단으로 분할)
    def wb_table(items):
        return "<table>" + "".join(
            f'<tr><td class="en">{esc(en)}</td><td class="ko">{esc(ko)}</td>'
            f'<td class="read">[{esc(rd)}]</td></tr>'
            for en, ko, rd in items
        ) + "</table>"

    words = u["words"]
    half = (len(words) + 1) // 2
    wb_cols = f'<div class="cols">{wb_table(words[:half])}{wb_table(words[half:])}</div>'

    # 패턴
    pats = "".join(
        f'<div class="pat"><div class="q">{esc(q)}<span class="ko">{esc(qk)}</span></div>'
        f'<div class="a">{esc(a)}<span class="ko">{esc(ak)}</span></div></div>'
        for q, qk, a, ak in u["patterns"]
    )

    # 대화
    lines = "".join(
        f'<div class="line"><div class="who {who}">{who}</div>'
        f'<div class="txt"><div class="en">{esc(en)}</div><div class="ko">{esc(ko)}</div></div></div>'
        for who, en, ko in u["dialogue"]
    )

    # 나만의 대답
    tpl = "".join(f'<div class="row">{esc(t)}</div>' for t in u["template"])

    return f"""
    <div class="page">
      <div class="unit-head" style="background:{accent};">
        <div class="emoji">{u["emoji"]}</div>
        <div>
          <div class="no">UNIT {idx:02d}</div>
          <div class="ko">{esc(u["title_ko"])}</div>
          <div class="en">{esc(u["title_en"])}</div>
        </div>
      </div>

      <div class="block wb">
        <div class="bar" style="background:var(--green);">📚 워드뱅크 · Word Bank</div>
        <div class="body">{wb_cols}</div>
      </div>

      <div class="block">
        <div class="bar" style="background:var(--blue);">💬 핵심 표현 · Key Expressions</div>
        <div class="body">{pats}</div>
      </div>

      <div class="block dia">
        <div class="bar" style="background:var(--amber);">🗣️ 대화 예시 · Sample Dialogue</div>
        <div class="body">{lines}</div>
      </div>

      <div class="block tpl">
        <div class="bar" style="background:var(--purple);">✏️ 나만의 대답 만들기 · Make Your Own Answer</div>
        <div class="body">
          {tpl}
          <div class="hint">빈칸에 워드뱅크 단어를 넣어 나만의 문장을 완성하고 소리 내어 말해 보세요.</div>
        </div>
      </div>
    </div>
    """


def appendix_html() -> str:
    rows = ""
    for i, u in enumerate(data.UNITS, 1):
        rows += (f'<tr><td class="cat" colspan="3" style="background:{ACCENTS[(i-1)%len(ACCENTS)]};">'
                 f'{u["emoji"]} UNIT {i:02d}  {esc(u["title_ko"])} · {esc(u["title_en"])}</td></tr>')
        rows += '<tr><th>단어</th><th>뜻</th><th>발음</th></tr>'
        for en, ko, rd in u["words"]:
            rows += f'<tr><td><b>{esc(en)}</b></td><td>{esc(ko)}</td><td>[{esc(rd)}]</td></tr>'
    return f"""
    <div class="page appendix">
      <h2 class="section-title">전체 워드뱅크 모아보기</h2>
      <p style="color:var(--muted); font-size:10px; margin:0 4px 12px;">
        10개 단원의 단어를 한눈에 복습할 수 있어요. 아는 단어에 ✓ 표시해 보세요.
      </p>
      <table>{rows}</table>
    </div>
    """


def build() -> Path:
    body = cover_html() + intro_html()
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
