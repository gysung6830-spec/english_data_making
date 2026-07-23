"""0부 레이아웃 시안 3종을 각각 PDF/PNG로 렌더(비교용).

시안 A · 가로 3열 스텝 플로우
시안 B · 지그재그 매거진
시안 C · 대시보드 타일 그리드
실행: python scripts/part0_variants.py
"""
from __future__ import annotations

import html
from pathlib import Path

import fitz
from weasyprint import HTML

from src.guide.codes import load_part0

OUT = Path("output")
E = html.escape


def _demo(d) -> str:
    if not d:
        return ""
    return (f'<div class="dm">'
            f'<div class="dm-r"><span class="t1">①</span>{E(d.bracketed or d.sentence)}</div>'
            f'<div class="dm-r"><span class="t2">②</span><b>{E(d.skeleton_ko)}</b></div>'
            f'<div class="dm-r"><span class="t3">③</span>{E(d.full_ko)}</div></div>')


BASE = """
:root{--navy:#0f5c4d;--navy2:#177a63;--gold:#c98a3b;--tint:#eef7f3;--tint2:#dcefe8;
--ink:#2b2f36;--muted:#6b7280;--line:#e6e3ef;
--f:"Georgia","NanumGothic","Malgun Gothic","WenQuanYi Zen Hei",serif;
--fm:"Georgia","NanumMyeongjo","Batang","WenQuanYi Zen Hei",serif;}
@page{size:A4;margin:13mm 14mm;}
*{box-sizing:border-box;}
body{font-family:var(--f);color:var(--ink);font-size:11px;line-height:1.6;margin:0;}
.kick{color:var(--gold);font-weight:800;font-size:10px;letter-spacing:3px;}
.h1{font-family:var(--fm);font-weight:800;color:#fff;font-size:22px;
background:linear-gradient(100deg,#0c4a3d,var(--navy2));padding:14px 18px;border-radius:12px;margin:4px 0 10px;}
.spine{font-family:var(--fm);font-weight:700;color:var(--navy);background:#f6f8fc;
border-left:4px solid var(--gold);padding:9px 14px;border-radius:0 6px 6px 0;margin:0 0 10px;font-size:12px;}
.tag{display:inline-block;font-weight:800;font-size:8.5px;color:#fff;padding:1px 8px;border-radius:4px;}
.badge{color:var(--gold);font-weight:800;}
/* 엔진 배너(공통) */
.flow{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;align-items:center;
background:linear-gradient(100deg,#0c4a3d,var(--navy2));border-radius:12px;padding:10px 12px;margin-bottom:12px;}
.flow .cap{color:#eafaf4;font-weight:800;font-size:10px;border:1.4px dashed rgba(255,255,255,.45);
border-radius:8px;padding:5px 10px;text-align:center;}
.flow .st{background:#eafaf4;color:var(--navy);font-weight:800;font-size:10px;padding:5px 11px;border-radius:8px;}
.flow .st b{color:var(--gold);}
.flow .ar{color:var(--gold);font-weight:900;}
.dm{margin-top:7px;border-top:1px dashed var(--line);padding-top:6px;font-size:9.5px;}
.dm-r{margin:3px 0;line-height:1.5;}
.dm .t1,.dm .t2,.dm .t3{display:inline-block;color:#fff;font-weight:800;font-size:8px;
padding:0 5px;border-radius:3px;margin-right:5px;}
.dm .t1{background:#6b7280;}.dm .t2{background:var(--right,#1f8a54);}.dm .t3{background:var(--navy);}
.idea{font-size:10px;color:#333;margin:3px 0;}
.rule{font-size:9px;color:#555;background:#f7faf9;border-radius:5px;padding:5px 9px;margin-top:4px;}
.extra{border:1px solid var(--tint2);border-radius:10px;background:#fcfefe;padding:10px 13px;margin-top:10px;}
.extra .eh{font-weight:800;color:var(--navy);font-size:12px;}
.extra .eh .b{background:var(--gold);color:#fff;font-size:9px;padding:2px 8px;border-radius:5px;margin-right:6px;}
"""

FLOW = ('<div class="flow"><span class="cap">수능 문장</span><span class="ar">▶</span>'
        '<span class="st"><b>①</b> 괄호치기</span><span class="ar">▶</span>'
        '<span class="st"><b>②</b> 뼈대·관계</span><span class="ar">▶</span>'
        '<span class="st"><b>③</b> 살 붙이기</span><span class="ar">▶</span>'
        '<span class="cap">쉬운 해석</span></div>')


def head(p0, variant):
    return (f'<div class="kick">0부 · 기본기 &nbsp;—&nbsp; 시안 {variant}</div>'
            f'<div class="h1">{E(p0.title)}</div>'
            f'<div class="spine">“{E(p0.spine)}”</div>')


def extras_html(extras):
    out = []
    for m in extras:
        out.append(f'<div class="extra"><div class="eh"><span class="b">{E(m.step)}</span>'
                   f'{E(m.title)}</div><div class="idea">{E(m.idea)}</div></div>')
    return "".join(out)


def variant_A(p0, steps, extras):
    css = BASE + """
.cols{display:flex;gap:0;align-items:stretch;}
.col{flex:1;border:1px solid var(--line);border-radius:12px;padding:11px 12px;background:#fff;}
.col .n{width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;
font-family:var(--fm);font-weight:800;font-size:15px;display:flex;align-items:center;justify-content:center;
margin-bottom:6px;box-shadow:0 0 0 3px #e2f1eb;}
.col .ct{font-weight:800;color:var(--navy);font-size:11.5px;margin-bottom:3px;line-height:1.35;}
.colar{display:flex;align-items:center;color:var(--gold);font-weight:900;font-size:18px;padding:0 4px;}
"""
    cols = []
    for i, m in enumerate(steps, 1):
        cols.append(f'<div class="col"><div class="n">{i}</div>'
                    f'<div class="ct">{E(m.title)}</div>'
                    f'<div class="idea">{E(m.idea)}</div>{_demo(m.demo)}</div>')
        if i < len(steps):
            cols.append('<div class="colar">▶</div>')
    body = (head(p0, "A · 가로 3열 스텝") + FLOW
            + '<div class="cols">' + "".join(cols) + '</div>'
            + extras_html(extras))
    return css, body


def variant_B(p0, steps, extras):
    css = BASE + """
.zz{display:flex;align-items:stretch;gap:12px;margin-bottom:10px;border-radius:12px;
border:1px solid var(--line);overflow:hidden;background:#fff;}
.zz.alt{flex-direction:row-reverse;background:var(--tint);}
.zz .side{flex:0 0 92px;background:var(--navy);color:#fff;display:flex;flex-direction:column;
align-items:center;justify-content:center;padding:10px;}
.zz.alt .side{background:var(--navy2);}
.zz .bn{font-family:var(--fm);font-weight:800;font-size:34px;line-height:1;}
.zz .bl{font-size:9px;color:#cdeee3;margin-top:4px;text-align:center;}
.zz .main{flex:1;padding:11px 14px;}
.zz .zt{font-weight:800;color:var(--navy);font-size:12.5px;margin-bottom:3px;}
"""
    rows = []
    for i, m in enumerate(steps, 1):
        alt = " alt" if i % 2 == 0 else ""
        rows.append(f'<div class="zz{alt}"><div class="side"><div class="bn">{i}</div>'
                    f'<div class="bl">{E(m.step)}</div></div>'
                    f'<div class="main"><div class="zt">{E(m.title)}</div>'
                    f'<div class="idea">{E(m.idea)}</div>{_demo(m.demo)}</div></div>')
    body = head(p0, "B · 지그재그 매거진") + FLOW + "".join(rows) + extras_html(extras)
    return css, body


def variant_C(p0, steps, extras):
    css = BASE + """
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.tile{position:relative;border:1px solid var(--line);border-radius:12px;padding:12px 14px 11px;background:#fff;overflow:hidden;}
.tile .bg{position:absolute;right:6px;top:-10px;font-family:var(--fm);font-weight:800;
font-size:64px;color:#eef7f3;line-height:1;z-index:0;}
.tile .in{position:relative;z-index:1;}
.tile .tt{font-weight:800;color:var(--navy);font-size:12px;margin-bottom:3px;}
.tile.wide{grid-column:1 / span 2;background:var(--tint);}
.tile .st{display:inline-block;background:var(--navy);color:#fff;font-size:9px;font-weight:800;
padding:1px 8px;border-radius:4px;margin-bottom:5px;}
"""
    tiles = []
    for i, m in enumerate(steps, 1):
        tiles.append(f'<div class="tile"><div class="bg">{i}</div><div class="in">'
                     f'<span class="st">STEP {i}</span>'
                     f'<div class="tt">{E(m.title)}</div><div class="idea">{E(m.idea)}</div>'
                     f'{_demo(m.demo)}</div></div>')
    # 마지막 타일: 지원 도구 요약(전폭)
    ex = " · ".join(E(m.title.split("—")[0].strip()) for m in extras)
    tiles.append(f'<div class="tile wide"><div class="in"><span class="st" '
                 f'style="background:var(--gold)">지원 도구</span>'
                 f'<div class="tt">{ex}</div>'
                 f'<div class="idea">읽기 깊이(유형별 형광펜) · 모르는 단어 유추 — STEP 위에 얹어 쓰는 보조 엔진.</div>'
                 f'</div></div>')
    body = head(p0, "C · 대시보드 타일") + FLOW + '<div class="grid">' + "".join(tiles) + '</div>'
    return css, body


def main():
    p0 = load_part0()
    steps = [m for m in p0.methods if m.step.startswith("STEP")]
    extras = [m for m in p0.methods if not m.step.startswith("STEP")]
    for name, fn in [("A", variant_A), ("B", variant_B), ("C", variant_C)]:
        css, body = fn(p0, steps, extras)
        doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"
        pdf = OUT / f"시안_0부_{name}.pdf"
        HTML(string=doc).write_pdf(str(pdf))
        d = fitz.open(str(pdf))
        d[0].get_pixmap(matrix=fitz.Matrix(2, 2)).save(str(OUT / f"시안_0부_{name}.png"))
        print(f"시안 {name} → {pdf.name}, PNG")


if __name__ == "__main__":
    main()
