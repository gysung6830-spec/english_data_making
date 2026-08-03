# -*- coding: utf-8 -*-
"""특강용 문법 필기 교재 렌더러.

콘텐츠(dict) → HTML → PDF(WeasyPrint).
학생용(빈칸)·교사용(정답본) 두 가지 모드를 지원한다.
"""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "templates" / "fonts"

# ── 색상 테마 (원본 교재의 초록 계열) ──────────────────────────────
GREEN_DARK = "#1e5b34"     # UNIT 배지
GREEN = "#2f9e5b"          # 포인트/강조
GREEN_SOFT = "#e8f5ec"     # 옅은 배경
GREEN_LINE = "#bfe3cb"
ANSWER_BG = "#fff3c4"      # 교사용 정답 형광
ANSWER_FG = "#1a6b3a"
INK = "#1f2937"


def _font_b64(name: str) -> str:
    return base64.b64encode((FONT_DIR / name).read_bytes()).decode()


def _est_width_em(answer: str) -> float:
    """정답 길이에 맞춰 빈칸 밑줄 폭(em) 추정 (한글은 약 2배 폭)."""
    w = 1.4
    for ch in answer:
        w += 1.0 if ord(ch) > 0x1100 else 0.56
    return round(max(2.6, w), 2)


# ── 인라인 마크업 파서 ────────────────────────────────────────────
def _emphasize(escaped: str) -> str:
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__(.+?)__", r'<span class="ul">\1</span>', escaped)
    return escaped


def _blank(answer: str, hint: str | None, teacher: bool) -> str:
    if teacher:
        return f'<span class="ans">{html.escape(answer)}</span>'
    w = _est_width_em(answer)
    hint_html = (
        f'<span class="hint">{html.escape(hint)}</span>' if hint else ""
    )
    return f'<span class="blank" style="min-width:{w}em">{hint_html}</span>'


def render_inline(text: str, teacher: bool) -> str:
    # 1) 빈칸을 sentinel(\x00N\x00)로 보호 → 강조(**),밑줄(__)이 빈칸을 감싸도 안전
    tokens: list[str] = []

    def _stash(m: re.Match) -> str:
        seg = m.group(1)
        answer, hint = (seg.split("||", 1) + [None])[:2] if "||" in seg else (seg, None)
        tokens.append(_blank(answer, hint, teacher))
        return f"\x00{len(tokens) - 1}\x00"

    protected = re.sub(r"\{\{(.*?)\}\}", _stash, text)
    # 2) 이스케이프 후 강조 적용 (sentinel은 일반 문자라 그대로 통과)
    result = _emphasize(html.escape(protected))
    # 3) sentinel 복원
    return re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], result)


# ── 블록 빌더 ─────────────────────────────────────────────────────
def _box_html(box: dict, teacher: bool) -> str:
    kind = box.get("type", "tip")  # tip(초록) | warn(함정) | compare(비교)
    lines = "".join(
        f'<div class="box-line">{render_inline(ln, teacher)}</div>' for ln in box["lines"]
    )
    return (
        f'<div class="box box-{kind}">'
        f'  <div class="box-label">{html.escape(box["label"])}</div>'
        f'  <div class="box-body">{lines}</div></div>'
    )


def _point_html(p: dict, teacher: bool) -> str:
    blocks = [
        f'<div class="point">',
        f'  <div class="point-head"><span class="point-badge">Point {p["no"]}</span>'
        f'<span class="point-title">{html.escape(p["title"])}</span></div>',
    ]
    if p.get("intro"):
        blocks.append(f'  <div class="point-intro">{render_inline(p["intro"], teacher)}</div>')
    for c in p["concepts"]:
        blocks.append('<div class="concept">')
        blocks.append(f'  <div class="lead">▪ {render_inline(c["lead"], teacher)}</div>')
        if c.get("desc"):
            blocks.append(f'  <div class="desc">{render_inline(c["desc"], teacher)}</div>')
        blocks.append('  <ul class="items">')
        for it in c["items"]:
            blocks.append(f'    <li>{render_inline(it, teacher)}</li>')
        blocks.append("  </ul>")
        blocks.append("</div>")
    boxes = p.get("boxes") or ([p["tip"]] if p.get("tip") else [])
    for box in boxes:
        blocks.append(_box_html(box, teacher))
    blocks.append("</div>")
    return "\n".join(blocks)


def _wrapup_html(w: dict, teacher: bool) -> str:
    ths = "".join(f"<th>{html.escape(h)}</th>" for h in w["headers"])
    rows = []
    for r in w["rows"]:
        tds = "".join(f"<td>{render_inline(c, teacher)}</td>" for c in r)
        rows.append(f"<tr>{tds}</tr>")
    return (
        '<div class="wrapup">'
        f'<div class="section-bar">Wrap Up · {html.escape(w["title"])}</div>'
        f'<table class="grid"><thead><tr>{ths}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def _practice_html(items: list, teacher: bool) -> str:
    blocks = ['<div class="practice">',
              '<div class="section-bar alt">Unit Practice</div>']
    for i, grp in enumerate(items, 1):
        blocks.append('<div class="pgroup">')
        blocks.append(f'  <div class="pq">{i}. {render_inline(grp["q"], teacher)}</div>')
        blocks.append('  <ol class="plist">')
        for it in grp["items"]:
            blocks.append(f'    <li>{render_inline(it, teacher)}</li>')
        blocks.append("  </ol></div>")
    blocks.append("</div>")
    return "\n".join(blocks)


def _intro_html(intro: list, teacher: bool) -> str:
    lis = "".join(f"<li>{render_inline(x, teacher)}</li>" for x in intro)
    return f'<div class="intro"><ul>{lis}</ul></div>'


def _css(teacher: bool) -> str:
    reg, bold = _font_b64("NanumSquareRoundR.woff"), _font_b64("NanumSquareRoundB.woff")
    tag = "교사용 · 정답본" if teacher else "학생용 · 필기본"
    tag_color = "#b23a48" if teacher else GREEN_DARK
    return f"""
@font-face {{ font-family:'NSR'; font-weight:400;
  src:url(data:font/woff;base64,{reg}) format('woff'); }}
@font-face {{ font-family:'NSR'; font-weight:700;
  src:url(data:font/woff;base64,{bold}) format('woff'); }}

@page {{
  size: A4; margin: 15mm 14mm 16mm 14mm;
  @bottom-center {{ content: "특강 문법 · UNIT 01  |  " counter(page); font-family:'NSR'; font-size:8pt; color:#9aa4ab; }}
  @top-right {{ content: "{tag}"; font-family:'NSR'; font-size:8pt; color:{tag_color}; font-weight:700; }}
}}
* {{ box-sizing:border-box; }}
body {{ font-family:'NSR'; color:{INK}; font-size:10.3pt; line-height:1.5; margin:0; }}
strong {{ font-weight:700; color:{GREEN_DARK}; }}
.ul {{ text-decoration:underline; text-underline-offset:2px; }}

/* 헤더 배너 */
.banner {{ display:flex; align-items:stretch; margin-bottom:10px; page-break-after:avoid; }}
.banner .ubadge {{ background:{GREEN_DARK}; color:#fff; font-weight:700; font-size:11pt;
  padding:8px 14px; border-radius:6px 0 0 6px; display:flex; align-items:center; white-space:nowrap; }}
.banner .utitle {{ background:linear-gradient(90deg,{GREEN} 0%, #7cc794 100%);
  color:#fff; font-weight:700; font-size:15pt; padding:8px 18px; flex:1;
  border-radius:0 18px 18px 0; display:flex; flex-direction:column; justify-content:center; }}
.banner .utitle small {{ font-weight:400; font-size:9pt; opacity:.9; }}

.intro {{ background:{GREEN_SOFT}; border:1px solid {GREEN_LINE}; border-radius:8px;
  padding:8px 14px 8px 8px; margin-bottom:12px; }}
.intro ul {{ margin:0; padding-left:18px; }}
.intro li {{ margin:3px 0; }}

/* 포인트 */
.point {{ margin:0 0 12px; page-break-inside:avoid; }}
.point-head {{ display:flex; align-items:center; gap:8px; border-bottom:2px solid {GREEN};
  padding-bottom:3px; margin-bottom:6px; }}
.point-badge {{ background:{GREEN}; color:#fff; font-weight:700; font-size:9pt;
  padding:2px 8px; border-radius:11px; }}
.point-title {{ font-weight:700; font-size:12pt; color:{GREEN_DARK}; }}
.point-intro {{ background:{GREEN_SOFT}; border-left:3px solid {GREEN};
  padding:5px 10px; border-radius:0 6px 6px 0; margin:2px 0 8px; }}
.concept {{ margin:6px 0 7px; }}
.lead {{ font-weight:700; color:{INK}; margin-bottom:2px; }}
.desc {{ color:#374151; margin:1px 0 3px; padding-left:14px; }}
.items {{ margin:2px 0 4px; padding-left:20px; }}
.items li {{ margin:3px 0; }}

/* 색상별 박스: tip(초록)·warn(함정)·compare(비교) */
.box {{ display:flex; gap:0; border:1px solid {GREEN_LINE}; border-radius:7px;
  overflow:hidden; margin:6px 0 4px; background:#fafffb; page-break-inside:avoid; }}
.box-label {{ color:#fff; font-weight:700; font-size:8.6pt; padding:8px 9px;
  display:flex; align-items:center; min-width:54px; justify-content:center; text-align:center; }}
.box-body {{ padding:6px 10px; flex:1; }}
.box-line {{ margin:2.5px 0; }}
.box-tip {{ border-color:{GREEN_LINE}; background:#fafffb; }}
.box-tip .box-label {{ background:{GREEN_DARK}; }}
.box-warn {{ border-color:#f0c9cf; background:#fff7f8; }}
.box-warn .box-label {{ background:#b23a48; }}
.box-compare {{ border-color:#cfe0f2; background:#f6faff; }}
.box-compare .box-label {{ background:#2f6fb0; }}

/* 빈칸 & 정답 */
.blank {{ display:inline-block; border-bottom:1.4px solid {GREEN}; height:1.05em;
  vertical-align:bottom; margin:0 2px; position:relative; }}
.hint {{ position:absolute; left:0; right:0; top:1px; text-align:center;
  font-size:7.2pt; color:#9aa4ab; }}
.ans {{ background:{ANSWER_BG}; color:{ANSWER_FG}; font-weight:700;
  padding:0 3px; border-radius:3px; }}

/* 섹션 바 */
.section-bar {{ background:{GREEN_DARK}; color:#fff; font-weight:700; font-size:11pt;
  padding:5px 12px; border-radius:6px; margin:14px 0 8px; page-break-after:avoid; }}
.section-bar.alt {{ background:{GREEN}; }}

/* Wrap Up 표 */
table.grid {{ width:100%; border-collapse:collapse; font-size:9.6pt; }}
table.grid th {{ background:{GREEN_DARK}; color:#fff; padding:5px 7px; border:1px solid {GREEN_DARK}; }}
table.grid td {{ padding:5px 7px; border:1px solid {GREEN_LINE}; }}
table.grid tbody tr:nth-child(even) {{ background:{GREEN_SOFT}; }}
table.grid td:first-child {{ font-weight:700; color:{GREEN_DARK}; white-space:nowrap; }}

/* Practice */
.pgroup {{ margin:0 0 8px; page-break-inside:avoid; }}
.pq {{ font-weight:700; margin-bottom:3px; }}
.plist {{ margin:2px 0; padding-left:20px; }}
.plist li {{ margin:3px 0; }}
"""


def build_html(unit: dict, teacher: bool) -> str:
    body = [f"<style>{_css(teacher)}</style>"]
    body.append(
        f'<div class="banner"><div class="ubadge">UNIT {unit["no"]}</div>'
        f'<div class="utitle">{html.escape(unit["title"])}'
        f'<small>{html.escape(unit["subtitle"])}</small></div></div>'
    )
    body.append(_intro_html(unit["intro"], teacher))
    for p in unit["points"]:
        body.append(_point_html(p, teacher))
    body.append(_practice_html(unit["practice"], teacher))
    body.append(_wrapup_html(unit["wrapup"], teacher))
    return "<!doctype html><meta charset='utf-8'>" + "\n".join(body)


def build_pdf(unit: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for teacher, suffix in [(False, "학생용"), (True, "교사용_정답")]:
        html_str = build_html(unit, teacher)
        out = out_dir / f"특강문법_UNIT{unit['no']}_{unit['title']}_{suffix}.pdf"
        HTML(string=html_str, base_url=str(ROOT)).write_pdf(str(out))
        made.append(out)
    return made
