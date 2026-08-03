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
import os
import re
import tempfile
from pathlib import Path

import textbook_data as data

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "중학영어회화교재_OPIC10.pdf"

# 이모지용 흑백 폰트 (컬러 이모지 대체)
EMOJI_FONT = "Symbola"


def _setup_fontconfig() -> None:
    """WeasyPrint + '컬러 이모지(Noto Color Emoji)'는 글리프가 줄 위로 크게 떠올라
    제자리에 배치되지 않는 버그가 있다. 컬러 이모지 폰트를 '거부(reject)'해서
    정상 metrics 의 흑백 이모지 폰트(Symbola)로 그려지도록 fontconfig 를 구성한다.
    (리눅스 + /etc/fonts 환경에서만 적용. 그 외에는 그대로 둔다.)"""
    sys_conf = "/etc/fonts/fonts.conf"
    if not os.path.exists(sys_conf):
        return
    conf = f"""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <include ignore_missing="yes">{sys_conf}</include>
  <selectfont><rejectfont>
    <pattern><patelt name="family"><string>Noto Color Emoji</string></patelt></pattern>
  </rejectfont></selectfont>
  <alias><family>emoji</family><prefer><family>{EMOJI_FONT}</family></prefer></alias>
</fontconfig>
"""
    path = Path(tempfile.gettempdir()) / "textbook_fontconfig.conf"
    path.write_text(conf, encoding="utf-8")
    os.environ["FONTCONFIG_FILE"] = str(path)


_setup_fontconfig()

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
    content: "__TITLE__  ·  " counter(page) " / " counter(pages);
    font-family: "NanumGothic", sans-serif; font-size: 11px; color: #9aa0a6;
  }
  @bottom-right {
    content: "ⓒ 김은아영어연구소";
    font-family: "NanumGothic", sans-serif; font-size: 11px; color: #9aa0a6;
  }
}
* { box-sizing: border-box; }
body {
  font-family: "NanumGothic", "Nanum Gothic", "Malgun Gothic", "Symbola", sans-serif;
  color: #23272e; font-size: 11px; line-height: 1.45; margin: 0;
}
/* 이모지는 흑백 심볼 폰트로 그려 정확히 배치 (컬러 이모지는 WeasyPrint에서 어긋남) */
.emoji, .em, .emojis { font-family: "Symbola", "NanumGothic", sans-serif; }
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
.cover .emojis { font-size:24px; letter-spacing:5px; line-height:1.6; margin-top:26px;
  max-width:80%; margin-left:auto; margin-right:auto; }
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
.toc { columns:2; column-gap:12px; }
.toc .row { break-inside:avoid; display:flex; align-items:center; gap:10px;
  border:1.5px solid var(--line); border-radius:8px; padding:5px 12px; margin-bottom:6px; }
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

/* 암기 체크(빈칸 뚫기) 페이지 */
.memo .mstep { margin:0 0 13px; }
.memo .mslabel { font-weight:800; color:var(--teal); font-size:12px; margin-bottom:4px; }
.memo .ms { font-size:15px; font-weight:600; line-height:2.1; }
.memo .ms .blk { color:var(--red); font-weight:800; letter-spacing:1px;
  border-bottom:1.5px solid var(--red); padding:0 2px; }
.memo .ms .blk.key { color:transparent; border-bottom:2px solid var(--red); }
.memo .mk { color:var(--muted); font-size:11px; margin:1px 0 4px; }
.memo .ansbox { margin-top:10px; padding-top:7px; border-top:1px dashed var(--line);
  color:#b0b4bb; font-size:9px; }
.memo .ansbox b { color:#9aa0a6; }
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
      <div class="kicker">{esc(getattr(data, "KICKER", "ENGLISH"))}</div>
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
    </div>
    <div class="page">
      <h2 class="section-title">목차 (OPIC 주제 {len(data.UNITS)}개)</h2>
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


# 암기 페이지에서 빈칸으로 뚫지 않는 기능어(관사/전치사/대명사 등)
_STOP = set(
    "a an the this that these those and or but so if to of in on at by for with as from into "
    "i you we they he she it my your our their his her its me us them him "
    "is am are was were be been being do does did have has had will would can could should "
    "not no more most much very just also too than then there here".split()
)


def _cloze_light(text: str, n: int):
    """정적 텍스트에서 내용어 n개를 '첫 글자 + 빈칸' 힌트로 뚫는다.
    반환: (HTML, 정답 리스트, 실제로 뚫은 개수)"""
    if n <= 0:
        return esc(text), [], 0
    parts = re.split(r"([A-Za-z][A-Za-z'\-]*)", text)
    cand = [i for i, p in enumerate(parts)
            if re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", p or "")
            and p.lower() not in _STOP and len(p) >= 4]
    if len(cand) > n:
        step = len(cand) / n
        picks = {cand[min(len(cand) - 1, round(k * step))] for k in range(n)}
    else:
        picks = set(cand)
    out, answers = [], []
    for i, p in enumerate(parts):
        if i in picks:
            answers.append(p)
            out.append(f'<span class="blk">{esc(p[0])}{"_" * (len(p) - 1)}</span>')
        else:
            out.append(esc(p))
    return "".join(out), answers, len(picks)


def _memorize_line(en: str, choices):
    """원래 빈칸(____)이던 자리는 '완전 공백'으로, 그 외 몇 단어는 첫 글자 힌트로 뚫는다."""
    parts = en.split("____")
    n_orig = len(parts) - 1
    budget = 2 if n_orig == 0 else (1 if n_orig == 1 else 0)  # 원래 빈칸이 많으면 힌트 빈칸은 줄임
    out, answers = [], []
    for i, seg in enumerate(parts):
        seg_html, seg_ans, used = _cloze_light(seg, budget)
        budget -= used
        out.append(seg_html)
        answers += seg_ans
        if i < n_orig:                       # 원래 빈칸 자리 = 완전 공백
            opt = choices[i][0][0]
            answers.append(opt)
            width = min(26, max(9, len(opt) + 2))
            out.append(f'<span class="blk key">{"_" * width}</span>')
    return "".join(out), answers


def memorize_html(idx: int, u: dict) -> str:
    """단원 뒤에 붙는 '암기 체크' 페이지.
    원래 템플릿 빈칸은 완전 공백, 그 밖의 단어 몇 개는 첫 글자 힌트. 하단에 정답."""
    accent = ACCENTS[(idx - 1) % len(ACCENTS)]
    steps, answers = "", []
    for st in u["template"]:
        lines = ""
        for en, ko, choices in st["lines"]:
            model_ko = ko
            for opts in choices:
                model_ko = model_ko.replace("____", opts[0][1], 1)
            cloze_html, ans = _memorize_line(en, choices)
            answers += ans
            lines += f'<div class="ms">{cloze_html}</div><div class="mk">{esc(model_ko)}</div>'
        steps += f'<div class="mstep"><div class="mslabel">{esc(st["label"])}</div>{lines}</div>'

    ans_html = "  ·  ".join(esc(a) for a in answers)
    return f"""
    <div class="page">
      <div class="unit-head" style="background:{accent};">
        <div class="emoji">{u["emoji"]}</div>
        <div>
          <div class="no">UNIT {idx:02d} · 암기 체크</div>
          <div class="ko">{esc(u["title_ko"])} <span style="font-size:12px; font-weight:600; opacity:.9;">— 빈칸 암기</span></div>
          <div class="en">Fill in the blanks from memory</div>
        </div>
        <div class="prompt"><div class="q">🧠 앞 페이지로 익힌 뒤, 빈칸을 채워 보세요</div>
          <div style="opacity:.9; font-size:9.5px;">첫 글자가 힌트예요</div></div>
      </div>
      <div class="block memo">
        <div class="bar" style="background:var(--teal);">🧠 문장 암기 · Fill from Memory</div>
        <div class="body">
          {steps}
          <div class="ansbox"><b>정답:</b> {ans_html}</div>
        </div>
      </div>
    </div>
    """


def _render(body: str, out_path: Path) -> Path:
    doc = f"<!doctype html><html><head><meta charset='utf-8'></head><body>{body}</body></html>"
    from weasyprint import CSS as WCSS, HTML  # 지연 임포트(무거움)
    css = CSS.replace("__TITLE__", esc(data.TITLE))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=doc).write_pdf(str(out_path), stylesheets=[WCSS(string=css)])
    return out_path


def build(out_path: Path = OUT, with_memorize: bool = False) -> Path:
    body = cover_html() + intro_html() + expressions_html()
    for i, u in enumerate(data.UNITS, 1):
        body += unit_html(i, u)
        if with_memorize:                 # 단원 페이지 뒤에 암기 체크 페이지
            body += memorize_html(i, u)
    body += appendix_html()
    return _render(body, out_path)


def build_sample(out_path: Path, n_units: int = 3) -> Path:
    """앞쪽 몇 개 단원만: [단원 페이지 + 암기 페이지] 를 번갈아 보여 주는 샘플."""
    body = cover_html()
    for i, u in enumerate(data.UNITS[:n_units], 1):
        body += unit_html(i, u) + memorize_html(i, u)
    return _render(body, out_path)


# 만들 버전들: 인자로 'school'(중) / 'mid'(중상) / 'adult'(상) / 'all' / 'sample' 선택 (기본 all)
TARGETS = {
    "school": ("textbook_data", ROOT / "output" / "OPIC회화교재_난이도중.pdf"),
    "mid":    ("textbook_data_mid", ROOT / "output" / "OPIC회화교재_난이도중상.pdf"),
    "adult":  ("textbook_data_adult", ROOT / "output" / "OPIC회화교재_난이도상.pdf"),
}


if __name__ == "__main__":
    import importlib
    import sys

    which = sys.argv[1] if len(sys.argv) > 1 else "all"

    if which == "sample":
        # 암기 페이지 샘플 (난이도 중 앞 3개 단원)
        data = importlib.import_module("textbook_data")  # noqa: F811
        p = build_sample(ROOT / "output" / "샘플_암기페이지_난이도중.pdf", n_units=3)
        print(f"완성(샘플): {p}")
    else:
        names = list(TARGETS) if which == "all" else [which]
        for name in names:
            module_name, out_path = TARGETS[name]
            data = importlib.import_module(module_name)  # noqa: F811 (전역 재지정)
            p = build(out_path)
            print(f"완성: {p}")
