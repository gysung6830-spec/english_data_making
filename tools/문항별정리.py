#!/usr/bin/env python3
"""생성 결과를 '문항 번호 순' 한 장짜리 HTML 로 정리한다 (API 미사용).

시험지 PDF 는 2단 조판이라 '몇 번이 어떤 유형이고 정답이 무엇인지'를 훑기 어렵다.
이 도구는 **같은 시험지 디자인 그대로** 한 단으로 다시 편다:
빠른 정답 → 정본 지문 → 문항별(발문·문제·해설).

조판은 새로 만들지 않는다. 문제·해설 HTML 은 생성기가 만든 것을 그대로 쓰고,
스타일은 시험지와 같은 templates/exam.css 를 그대로 끼워 넣는다.
화면용 보정(1단·글자 확대·머리말 표시)만 뒤에 덧붙인다.

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
from exam.renderer import DEFAULT_FOOTER, TEMPLATE_DIR  # noqa: E402

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


def collect(passage) -> list[dict]:
    """Passage → 문항 번호 순 항목 목록(문제·해설 HTML 은 손대지 않고 그대로)."""
    rows = []
    for no, t in enumerate(MERGED_ORDER, 1):
        q, a = (passage.q.get(t) or "").strip(), (passage.a.get(t) or "").strip()
        if not (q and a):
            continue
        ans = _answer_of(a)
        rows.append({
            "no": no, "key": t,
            "label": MERGED_LABELS[t], "prompt": MERGED_PROMPTS[t],
            "q_html": q, "a_html": a,
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
# 디자인은 그대로 두고 '치수'만 화면용으로 키우고, 2단을 1단으로 편다.
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
.sheet {
  max-width: 860px; margin: 0 auto; background: #fff;
  padding: 9mm 9mm 12mm; border-radius: 3px;
  box-shadow: 0 1px 3px rgba(20,40,30,.14), 0 8px 28px rgba(20,40,30,.10);
}
.columns { column-count: 1; column-rule: none; }
.teacher, .quick, .answers, .review { break-before: auto; }

/* 인쇄 때 하단에 반복되던 저작권 줄 — 화면에서는 맨 끝 한 줄로 */
.page-footer {
  position: static; display: block; margin-top: 8mm;
  padding-top: 2.5mm; border-top: 0.6px solid #dbeae2; font-size: 11.5px;
}

/* px 로 못 박힌 치수만 화면 배율에 맞춰 올린다 */
.brand-title { font-size: 25px; }
.badge { font-size: 11.5px; }
.head-note { font-size: 12px; margin-top: 2.5mm; }
.answer-title { font-size: 16.5px; }
.passage-label { font-size: 12.6px; }
.q-prompt, .q-body { font-size: 14.6px; }
.a-type, .teach-tag { font-size: 11.4px; }
.review-intro { font-size: 12.4px; }

.q-item { margin-bottom: 6mm; }
.q-head { margin-bottom: 1.6mm; }
.qnum { margin-right: 1.4mm; }
.teach-exp { margin-top: 2.6mm; padding: 2.4mm 3mm; }

/* 문항 사이 옅은 구분선 — 한 단으로 길게 이어지므로 경계가 필요하다 */
.q-item + .q-item { border-top: 0.6px solid #e4eeE9; padding-top: 5mm; }

/* '확인 권장' 메모를 문항 안에 붙일 때 */
.q-item .review-intro { margin: 2.4mm 0 0; }
.q-item .review-intro b { color: #8a6d1f; }

.src-note { font-size: 12px; color: #666; margin: 0 0 1mm; }
@media (max-width: 640px) {
  body { padding: 0; }
  .sheet { padding: 6mm 5mm 10mm; border-radius: 0; box-shadow: none; }
}
@media print {
  html, body { background: #fff; padding: 0; }
  .sheet { max-width: none; padding: 0; box-shadow: none; }
}
"""


def _quick_grid(rows: list[dict]) -> str:
    cells = "".join(
        f'<div class="quick-cell"><span class="quick-no">{r["no"]}</span>'
        f'<span class="quick-key">{_E(r["quick"])}</span></div>' for r in rows)
    return f'<div class="quick-grid">{cells}</div>'


def _item(row: dict) -> str:
    """교사용 섹션과 같은 마크업 — 문제 밑에 해설(정답 포함)."""
    parts = [
        f'<div class="q-item type-{_E(row["key"])}">',
        '<div class="q-head">',
        f'<span class="qnum">{row["no"]}.</span> ',
        f'<span class="q-prompt">{row["prompt"]}</span>',
        f' <span class="a-type">· {_E(row["label"])}</span>',
        '</div>',
        f'<div class="q-body">{row["q_html"]}</div>',
        '<div class="teach-exp">',
        f'<span class="teach-tag">해설 · 정답 {_E(row["answer"]) or "-"}</span>',
        f'<div class="a-body">{row["a_html"]}</div>',
        '</div>',
    ]
    if row["flags"]:
        why = " / ".join(_E(f) for f in row["flags"])
        parts.append(f'<div class="review-intro"><b>확인 권장</b> — {why}</div>')
    parts.append('</div>')
    return "".join(parts)


def render(title: str, rows: list[dict], source: str, note: str = "",
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

<section class="quick first-sec">
  <h2 class="answer-title section-title">빠른 정답</h2>
  {_quick_grid(rows)}
  {f'<div class="review-intro"><b>확인 권장 {flagged}문항</b> — 아래 해당 문항에 사유를 적어 두었습니다.</div>' if flagged else ''}
</section>

<section class="questions">
  <h2 class="answer-title section-title">정본 지문</h2>
  <p class="src-note">{_E(title)}</p>
  <div class="passage">{_E(source)}</div>
</section>

<section class="teacher">
  <h2 class="answer-title section-title">문항별 · 문제 + 해설</h2>
  <div class="columns">
    <div class="passage-block">
      {"".join(_item(r) for r in rows)}
    </div>
  </div>
</section>

<div class="page-footer">{_E(footer_note)} · 어법 두 문항(5·6번)은 지문을 다시 써서 내므로
위 정본과 문장이 다릅니다.</div>
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
        note = "무료 미리보기(데모 지문) · 16문항 · 수능 배열 — API 를 쓰지 않았습니다."

    if not passages:
        print("지문이 없습니다.", file=sys.stderr)
        return 1
    p = passages[min(args.index, len(passages) - 1)]
    rows = collect(p)
    src = _txt(p.q[MERGED_ORDER[0]].split("</div>")[0])   # 주제 문항의 본문 = 정본
    out = Path(args.out)
    out.write_text(render(p.title, rows, src, note), encoding="utf-8")
    print(f"{out}  ({len(rows)}문항)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
