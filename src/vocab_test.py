"""필생보 단어시험지 생성 — 교재 passage 목록 → 단어시험 PDF(학생용/정답).

규칙(표준):
- 지문(item_no)별로 그룹, 지문 내에서 랜덤 셔플(기본 고정 시드 → 재생성 시 동일).
- 어휘는 지문 내 첫 등장 기준 중복 제거. 영어 → 뜻(빈칸) 형식.
- 브랜드 톤(포레스트 그린 + 민트 + 뉴트럴), 이름·점수란 포함.

사용:
    from src.vocab_test import render_vocab_test
    render_vocab_test(passages, out_stem, source_title="올림포스 …", footer_note="© …")
    # → out_stem+"_학생용.pdf", out_stem+"_정답.pdf"
"""
from __future__ import annotations
import html
import random
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_PAL = """
:root{ --green:#2c6444; --green-d:#1f4d33; --green-bg:#e7f0ea; --green-soft:#eef5f0;
  --ink:#262b31; --gray:#7f8790; --line:#e2e6e6; }
*{ box-sizing:border-box; }
body{ font-family:"NanumSquareRound","Malgun Gothic",sans-serif; color:var(--ink);
  font-size:10.5pt; margin:0; }
.doc-head{ border-bottom:2.5px solid var(--green); padding-bottom:9px; margin-bottom:12px; }
.pill{ display:inline-block; background:var(--green); color:#fff; font-weight:800;
  font-size:10.5pt; border-radius:999px; padding:3px 15px; }
.tag{ display:inline-block; margin-left:8px; font-size:8.7pt; font-weight:700; border-radius:999px; padding:2px 11px; }
.tag.stu{ background:#fff; color:var(--green-d); border:1.4px solid #bfe0cc; }
.tag.ans{ background:#8a6d1f; color:#fff; }
.meta{ margin-top:9px; font-size:9.3pt; color:#3c4652; display:flex; gap:22px; }
.meta b{ color:var(--green-d); }
.instr{ font-size:8.9pt; color:var(--gray); margin-top:3px; }
.unit{ break-inside:avoid; margin:0 0 11px; }
.unit-h{ display:flex; align-items:baseline; gap:8px; background:var(--green-soft);
  border:1px solid #d6e9de; border-left:4px solid var(--green); border-radius:7px;
  padding:4px 11px; margin-bottom:6px; }
.unit-h .u-no{ font-weight:800; color:var(--green-d); font-size:10pt; }
.unit-h .u-th{ font-size:8.4pt; color:var(--gray); font-weight:400; }
.unit-h .u-ct{ margin-left:auto; font-size:8pt; color:var(--gray); }
.vlist{ column-count:2; column-gap:20px; }
.vrow{ display:flex; align-items:baseline; gap:6px; break-inside:avoid;
  padding:2.5px 0; border-bottom:1px dotted #e6ebe8; }
.vn{ flex:none; width:19px; text-align:right; color:var(--gray); font-size:8.2pt; font-weight:700; }
.vw{ flex:none; font-weight:700; color:var(--ink); font-size:9.9pt; }
.vm{ flex:1; }
.vm.blank{ border-bottom:1px solid #cfd8d2; min-height:12px; }
.vm.ans{ color:var(--green-d); font-size:9.3pt; }
"""


def _collect(passages, seed):
    """지문별 어휘(지문 내 중복 제거) 수집 + 지문 내 셔플."""
    units, total = [], 0
    for i, p in enumerate(passages):
        seen, words = set(), []
        for s in p.analysis.sentences:
            for v in s.vocab:
                k = (v.word or "").strip().lower()
                if k and k not in seen:
                    seen.add(k)
                    words.append(((v.word or "").strip(), (v.meaning or "").strip()))
        if not words:
            continue
        if seed is not None:
            random.Random(seed + i * 1009 + (abs(hash(p.item_no or "")) % 100000)).shuffle(words)
        units.append(((p.item_no or f"지문{i + 1}").strip(), (p.title or "").strip(), words))
        total += len(words)
    return units, total


def _page_css(footer_note):
    center = (f'@bottom-center{{ content:"{footer_note}"; font-size:8pt; color:#a7adb8; }}'
              if footer_note else "")
    return ('@page{ size:A4; margin:14mm 13mm 15mm; '
            f'{center} @bottom-right{{ content: counter(page) " / " counter(pages); '
            'font-size:8pt; color:#a7adb8; } }')


def _build_html(units, total, source_title, answer, fonts, footer_note):
    e = html.escape
    tag = '<span class="tag ans">정답</span>' if answer else '<span class="tag stu">학생용</span>'
    parts = [
        f'<div class="doc-head"><span class="pill">{e(source_title)} 단어 시험</span>{tag}'
        f'<div class="meta"><span>이름 <b>____________</b></span>'
        f'<span>점수 <b>______ / {total}</b></span><span>필생보 · Ortica영어</span></div>'
        f'<div class="instr">각 영어 단어의 뜻을 쓰시오. (지문별 구성 · 지문 내 순서 무작위)</div></div>'
    ]
    for no, theme, words in units:
        th = e(theme[:28]) + ("…" if len(theme) > 28 else "")
        rows = []
        for i, (w, mean) in enumerate(words, 1):
            cell = f'<span class="vm ans">{e(mean)}</span>' if answer else '<span class="vm blank"></span>'
            rows.append(f'<div class="vrow"><span class="vn">{i}</span>'
                        f'<span class="vw">{e(w)}</span>{cell}</div>')
        parts.append(f'<div class="unit"><div class="unit-h"><span class="u-no">{e(no)}</span>'
                     f'<span class="u-th">{th}</span><span class="u-ct">{len(words)}개</span></div>'
                     f'<div class="vlist">{"".join(rows)}</div></div>')
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>단어시험</title>'
            f'<style>{fonts}\n{_PAL}\n{_page_css(footer_note)}</style></head>'
            f'<body>{"".join(parts)}</body></html>')


def render_vocab_test(passages, out_stem, source_title="", footer_note="", seed=20260902):
    """passages → 단어시험 학생용/정답 PDF. 생성한 Path 목록 반환."""
    from weasyprint import HTML  # 지연 임포트(무거움)
    fonts = (TEMPLATE_DIR / "lecture_fonts.css").read_text(encoding="utf-8")
    units, total = _collect(list(passages), seed)
    outs = []
    for answer, suf in [(False, "학생용"), (True, "정답")]:
        doc = _build_html(units, total, source_title, answer, fonts, footer_note)
        out = Path(f"{out_stem}_{suf}.pdf")
        out.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=doc, base_url=str(TEMPLATE_DIR) + "/").write_pdf(str(out))
        outs.append(out)
    return outs
