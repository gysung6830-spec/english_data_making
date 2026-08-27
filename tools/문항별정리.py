#!/usr/bin/env python3
"""생성 결과를 '문항 번호 순' 한 장짜리 HTML 로 정리한다 (API 미사용).

시험지 PDF 는 학생용·교사용·해설지가 따로 떨어져 있어 '몇 번이 어떤 유형이고
정답이 무엇인지'를 한 번에 훑기 어렵다. 이 도구는 **같은 시험지 디자인 그대로**
문항 번호 순으로 다시 편다: 문항별(발문·문제·해설) 2단 → 쪽 나눔 → 빠른 정답.

조판은 새로 만들지 않는다. 문제·해설 HTML 은 생성기가 만든 것을 그대로 쓰고,
스타일은 시험지와 같은 templates/exam.css 를 그대로 끼워 넣는다(2단 조판 그대로).
화면용 보정(글자 확대·머리말 표시·쪽 나눔을 종이 장으로)만 뒤에 덧붙인다.

사용:
    python tools/문항별정리.py                 # 데모 지문으로 샘플 만들기
    python tools/문항별정리.py 결과.json        # 웹앱이 저장한 분석 결과로 만들기
    python tools/문항별정리.py 결과.json -o 파일.html
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exam.merged import (  # noqa: E402
    MERGED_LABELS,
    MERGED_ORDER,
    MERGED_PROMPTS,
    demo_passages_merged,
)
from exam.renderer import DEFAULT_FOOTER, TEMPLATE_DIR, hang_numbers  # noqa: E402

_E = html.escape
_CIRCLED = "①②③④⑤⑥⑦⑧ⓐⓑⓒⓓⓔ"


def _txt(h: str) -> str:
    """조판 HTML → 평문(태그 제거·공백 정리·엔티티 복원)."""
    h = re.sub(r"<br\s*/?>", " ", h or "")
    t = re.sub(r"<[^>]+>", " ", h)
    t = (t.replace("&#39;", "'").replace("&nbsp;", " ")
          .replace("&quot;", '"').replace("&amp;", "&")
          .replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", t).strip()


def _answer_of(a_html: str) -> dict:
    """해설 HTML 에서 정답을 뽑는다.

    대부분은 원 번호(①·ⓑ)지만, 어순 배열처럼 '정답'이라는 라벨 뒤에 답 문장이 오는
    유형도 있다. 그때는 라벨이 아니라 문장을 정답으로 보여 줘야 한다.
    """
    m = re.search(r'<p>\s*<span class="answer-key">(.*?)</span>(.*?)</p>', a_html, re.S)
    if not m:
        return {"answer": "", "answer_text": ""}
    key, tail = _txt(m.group(1)), _txt(m.group(2))
    if any(c in key for c in _CIRCLED):
        return {"answer": key, "answer_text": tail}     # ①, ⓑ-ⓓ, ④ (4개) …
    return {"answer": tail or key, "answer_text": ""}   # 어순 배열 — 답 문장이 곧 정답


# 해설 첫 줄이 정답 표기뿐인 문단이면 머리(.a-head)로 올리고 본문에선 지운다
# ('④ (4개)'처럼 짧은 꼬리는 정답과 함께 올린다). 어순 배열처럼 정답 문장이
# 뒤따르는 문단은 그대로 둔다 — 문장이 곧 답이라 본문에 있어야 한다.
_KEY_P = re.compile(r'^\s*<p>\s*<span class="answer-key">[^<]*</span>([^<]*)</p>')
_TAIL_MAX = 12


def collect(passage) -> list[dict]:
    """Passage → 문항 번호 순 항목 목록(문제·해설 HTML 은 손대지 않고 그대로)."""
    rows = []
    for no, t in enumerate(MERGED_ORDER, 1):
        q, a = (passage.q.get(t) or "").strip(), (passage.a.get(t) or "").strip()
        if not (q and a):
            continue
        ans = _answer_of(a)
        a = hang_numbers(a)
        head_key = ans["answer"]
        m = _KEY_P.match(a)
        if m and any(c in ans["answer"] for c in _CIRCLED) \
                and len(m.group(1).strip()) <= _TAIL_MAX:
            head_key = f'{ans["answer"]} {m.group(1).strip()}'.strip()
            a = a[m.end():]
        rows.append({
            "no": no, "key": t,
            "label": MERGED_LABELS[t], "prompt": MERGED_PROMPTS[t],
            "q_html": q, "a_html": a, "head_key": head_key,
            "flags": list(passage.flags.get(t, [])),
            **ans,
            # 빠른 정답 칸: 원 번호가 아니면(어순 배열 등) '서술형'으로 줄여 적는다.
            "quick": ans["answer"] if any(c in ans["answer"] for c in _CIRCLED) else "서술형",
        })
    return rows


# ---------------------------------------------------------------------------
# 조판 — 시험지(exam.css) 그대로 + 화면용 보정만 덧붙임
# ---------------------------------------------------------------------------

# 시험지는 A4 인쇄 기준(본문 10.2px)이라 화면에서는 작다.
# 디자인(2단 조판 포함)은 그대로 두고 '치수'만 화면용으로 키운다.
_SCREEN_CSS = """
/* ===== 화면용 보정 (인쇄 디자인은 위 exam.css 그대로) ===== */
html { background: #e9edeb; }
body {
  background: #e9edeb;
  font-family: 'Liberation Serif', 'Tinos', Georgia, 'Times New Roman',
               'NanumSquareRound', 'Noto Sans KR', serif;
  font-size: 13.4px;
  padding: 22px 14px 60px;
}
/* 화면에서는 '쪽'을 종이 장으로 보여 준다 — 인쇄의 break-before: page 자리와 같다 */
.sheet {
  max-width: 880px; margin: 0 auto 22px; background: #fff;
  padding: 9mm 9mm 11mm; border-radius: 3px;
  box-shadow: 0 1px 3px rgba(20,40,30,.14), 0 8px 28px rgba(20,40,30,.10);
}
.quick, .answers { break-before: auto; }   /* 쪽 나눔은 .sheet 가 대신한다 */
/* 인쇄는 쪽 높이가 정해져 있어 column-fill: auto 가 왼쪽 단부터 채우지만,
   화면은 높이가 무한이라 그대로 두면 전부 왼쪽 단에 몰린다. 화면에서만 균등 분배. */
.columns { column-fill: balance; }

/* 인쇄 때 하단에 반복되던 저작권 줄 — 화면에서는 맨 끝 한 줄로 */
.page-footer {
  position: static; display: block; margin-top: 7mm;
  padding-top: 2.5mm; border-top: 0.6px solid #dbeae2; font-size: 11.5px;
}

/* px 로 못 박힌 치수만 화면 배율에 맞춰 올린다 */
.brand-title { font-size: 25px; }
.badge { font-size: 11.5px; }
.head-note { font-size: 12px; margin-top: 2.5mm; }
.answer-title { font-size: 16.5px; }
.passage-label { font-size: 12.6px; }
.q-prompt, .q-body { font-size: 14.2px; }
.a-type, .teach-tag { font-size: 11.2px; }
.review-intro { font-size: 12.2px; }

.q-item { margin-bottom: 5.4mm; }
.a-item { margin-bottom: 5mm; }
.q-head, .a-head { margin-bottom: 1.8mm; }
.qnum { margin-right: 1.2mm; }

/* 해설 — 한글 산문이라 문제보다 크게·넓게 잡아야 읽힌다 */
.a-body { font-size: 13.8px; line-height: 1.85; }
.a-body p { margin: 1.6mm 0; }
.answer-key { padding: 1px 8px; }
.a-head { display: flex; align-items: baseline; gap: 5px; }
.a-key {                                   /* 정답을 문항 머리 오른쪽에 */
  margin-left: auto; font-size: 11.6px; color: #2f7d61;
  background: #eef6f2; border: 0.6px solid #bcd8cc; border-radius: 999px;
  padding: 1px 9px; white-space: nowrap;
}
.a-key b { font-weight: 700; }
.reason + .wrong { margin-top: 3mm; padding-top: 2.4mm; }

/* '확인 권장' 메모를 해설 문항 안에 붙일 때 */
.a-item .review-intro { margin: 1.6mm 0 0; }
.a-item .review-intro b { color: #8a6d1f; }

/* 좁은 화면에서는 2단이 되레 읽기 나쁘다 — 한 단으로 편다 */
@media (max-width: 720px) {
  body { padding: 0; }
  .sheet { padding: 6mm 5mm 10mm; border-radius: 0; box-shadow: none;
           margin-bottom: 10px; }
  .columns { column-count: 1; column-rule: none; }
}
@media print {
  html, body { background: #fff; padding: 0; }
  .sheet { max-width: none; padding: 0; box-shadow: none; margin: 0; }
  .columns { column-fill: auto; }          /* 인쇄는 왼쪽 단부터 채운다(원래대로) */
  .quick-sheet, .ans-sheet { break-before: page; }
}
"""

# 한 '단 묶음'에 넣을 문항 수. 2단이 한없이 길어지면 왼쪽 단을 끝까지 내려간 뒤
# 다시 맨 위로 올라와야 해서 읽기 나쁘다. 묶음으로 끊어 쪽처럼 읽히게 한다.
# 해설은 지문이 없어 훨씬 짧으므로 더 크게 묶는다.
_PER_BLOCK = 4
_PER_BLOCK_A = 8


def _quick_grid(rows: list[dict]) -> str:
    cells = "".join(
        f'<div class="quick-cell"><span class="quick-no">{r["no"]}</span>'
        f'<span class="quick-key">{_E(r["quick"])}</span></div>' for r in rows)
    return f'<div class="quick-grid">{cells}</div>'


def _q_item(row: dict) -> str:
    """문제편 한 문항 — 학생용 섹션과 같은 마크업(정답·해설 없음)."""
    return (
        f'<div class="q-item type-{_E(row["key"])}">'
        f'<div class="q-head">'
        f'<span class="qnum">{row["no"]}.</span> '
        f'<span class="q-prompt">{row["prompt"]}</span>'
        f' <span class="a-type">· {_E(row["label"])}</span>'
        f'</div>'
        f'<div class="q-body">{row["q_html"]}</div>'
        f'</div>'
    )


def _a_item(row: dict) -> str:
    """해설편 한 문항 — 해설지 섹션과 같은 마크업(정답 + 해설)."""
    key = (f'<span class="a-key">정답 <b>{_E(row["head_key"])}</b></span>'
           if row["quick"] != "서술형" else '<span class="a-key">서술형</span>')
    parts = [
        f'<div class="a-item type-{_E(row["key"])}">',
        '<div class="a-head">',
        f'<span class="qnum">{row["no"]}.</span> ',
        f'<span class="a-type">{_E(row["label"])}</span>',
        key,
        '</div>',
        f'<div class="a-body">{row["a_html"]}</div>',
    ]
    if row["flags"]:
        why = " / ".join(_E(f) for f in row["flags"])
        parts.append(f'<div class="review-intro"><b>확인 권장</b> — {why}</div>')
    parts.append('</div>')
    return "".join(parts)


def _blocks(rows: list[dict], item, per: int) -> str:
    """문항을 per 개씩 묶어 2단으로 흘린다."""
    out = []
    for i in range(0, len(rows), per):
        items = "".join(item(r) for r in rows[i:i + per])
        out.append(f'<div class="columns"><div class="passage-block">{items}</div></div>')
    return "".join(out)


def render(title: str, rows: list[dict], note: str = "",
           footer_note: str = DEFAULT_FOOTER) -> str:
    exam_css = (TEMPLATE_DIR / "exam.css").read_text(encoding="utf-8")
    flagged = sum(1 for r in rows if r["flags"])
    head_note = note or f"{title} · {len(rows)}문항 · 수능 배열"
    return f"""<title>변형문제 문항별 정리</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;800&family=Tinos:ital,wght@0,400;0,700;1,400&display=swap">
<style>{exam_css}{_SCREEN_CSS}</style>

<div class="sheet">
<header class="sheet-head">
  <div class="brand">
    <span class="badge">제 3 교시</span>
    <span class="brand-title">영어 영역</span>
  </div>
  <div class="head-note">{_E(head_note)}</div>
</header>

<section class="questions first-sec">
  <h2 class="answer-title section-title">문제편</h2>
  {_blocks(rows, _q_item, _PER_BLOCK)}
</section>
</div>

<div class="sheet quick-sheet">
<section class="quick">
  <h2 class="answer-title section-title">빠른 정답</h2>
  {_quick_grid(rows)}
  {f'<div class="review-intro"><b>확인 권장 {flagged}문항</b> — 해설편의 해당 문항에 사유를 적어 두었습니다.</div>' if flagged else ''}
</section>
</div>

<div class="sheet ans-sheet">
<section class="answers">
  <h2 class="answer-title section-title">해설편 · 정답 및 해설</h2>
  {_blocks(rows, _a_item, _PER_BLOCK_A)}
</section>
<div class="page-footer">{_E(footer_note)} · 어법 두 문항은 지문을 다시 써서 내므로
다른 문항의 지문과 문장이 다릅니다.</div>
</div>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="생성 결과를 문항별 HTML 로 정리")
    ap.add_argument("json", nargs="?", help="웹앱이 저장한 분석 결과(.json). 없으면 데모")
    ap.add_argument("-o", "--out", default="문항별정리.html")
    ap.add_argument("-i", "--index", type=int, default=0, help="여러 지문 중 몇 번째(0부터)")
    args = ap.parse_args()

    if args.json:
        from exam import serialize
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        parts, _ = serialize.load_parts(data)
        passages = parts[0]["passages"]
        note = parts[0].get("header_note", "")
    else:
        passages = demo_passages_merged()
        note = "무료 미리보기(데모 지문) · 17문항 · 수능 배열 — API 를 쓰지 않았습니다."

    if not passages:
        print("지문이 없습니다.", file=sys.stderr)
        return 1
    p = passages[min(args.index, len(passages) - 1)]
    rows = collect(p)
    out = Path(args.out)
    out.write_text(render(p.title, rows, note), encoding="utf-8")
    print(f"{out}  ({len(rows)}문항)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
