# -*- coding: utf-8 -*-
"""부록: 어휘 미니 테스트 — 회차별 핵심 단어·숙어 영→한 빈칸 시험지 (정답은 「어휘 색인」에서 확인)."""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "workbook_content.json")
OUT = os.path.join(ROOT, "samples", "어휘테스트.html")


def esc(s):
    return html.escape(str(s or ""))


def exam_label(eid):
    y, m = eid.split("-")
    m = {"06": "6월", "09": "9월", "수능": "수능"}.get(m, m)
    return f"{y}학년도 {m}"


def ekey(e):
    y, m = e.split("-")
    return (int(y), {"06": 1, "09": 2, "수능": 3}.get(m, 9))


def sort_key(w):
    s = re.sub(r"^(a|an|the|to|be)\s+", "", w.strip().lower())
    s = re.sub(r"[^a-z0-9가-힣 ]", "", s)
    return s or w.strip().lower()


def build():
    data = json.load(open(SRC, encoding="utf-8"))
    by_exam = {}
    for c in data:
        eid = c["key"].split("|")[0]
        seen = by_exam.setdefault(eid, {})
        for v in c.get("vlist", []):
            if isinstance(v, dict) and v.get("w"):
                w = v["w"].strip()
                seen.setdefault(w.lower(), w)  # dedup within exam
    exams = sorted(by_exam, key=ekey)

    sections = ""
    for e in exams:
        words = sorted(by_exam[e].values(), key=lambda w: (sort_key(w), w.lower()))
        items = "".join(
            f'<div class="ti"><span class="tw">{esc(w)}</span>'
            f'<span class="tb"></span></div>' for w in words
        )
        sections += (
            f'<section class="ex"><div class="exh"><span class="ext">{esc(exam_label(e))}</span>'
            f'<span class="exc">{len(words)}단어</span>'
            f'<span class="exs">맞은 개수 <b>____</b> / {len(words)}</span></div>'
            f'<div class="tgrid">{items}</div></section>'
        )

    total = sum(len(by_exam[e]) for e in exams)
    doc = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>어휘 미니 테스트</title><style>
@page{{ size:A4; margin:13mm 12mm 14mm; }}
*{{ box-sizing:border-box; }}
body{{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; margin:0; background:#fff; }}
:root{{ --ink:#1f7a5c; --ink-d:#12543d; --line:#e6e8ea; --muted:#6b7280; }}
.vt-cover{{ background:linear-gradient(160deg,#12543d 0%,#1f7a5c 78%,#2a916d 100%); color:#fff; border-radius:10px; padding:26px 30px; margin-bottom:16px; break-after:avoid; }}
.vt-cover .kick{{ font-size:11px; font-weight:800; letter-spacing:3px; opacity:.85; }}
.vt-cover .t{{ font-size:30px; font-weight:800; margin:6px 0 4px; }}
.vt-cover .sub{{ font-size:11px; opacity:.92; }}
.vt-cover .meta{{ margin-top:10px; font-size:10px; opacity:.9; }}
.guide{{ background:#f3f8f5; border:1px solid #cfe5da; border-radius:8px; padding:8px 12px; font-size:9px; color:#33514a; margin-bottom:14px; }}
.guide b{{ color:var(--ink-d); }}
.ex{{ margin-bottom:14px; break-inside:avoid-column; }}
.exh{{ display:flex; align-items:baseline; gap:9px; border-bottom:2px solid var(--ink); margin:2px 0 6px; padding-bottom:3px; break-after:avoid; }}
.exh .ext{{ font-size:14px; font-weight:800; color:var(--ink-d); }}
.exh .exc{{ font-size:8.5px; color:var(--muted); }}
.exh .exs{{ margin-left:auto; font-size:8.8px; color:#4a5560; }}
.exh .exs b{{ color:var(--ink-d); }}
.tgrid{{ column-count:3; column-gap:14px; }}
.ti{{ break-inside:avoid; display:flex; align-items:baseline; gap:5px; padding:2px 0; border-bottom:1px dotted #e9ecee; margin-bottom:1px; }}
.ti .tw{{ font-size:9px; font-weight:700; color:#1a1f26; flex:none; max-width:52%; }}
.ti .tb{{ flex:1; border-bottom:1px solid #c7d3cd; height:11px; }}
</style></head><body>
<div class="vt-cover">
  <div class="kick">APPENDIX · 부록</div>
  <div class="t">어휘 미니 테스트</div>
  <div class="sub">회차별 핵심 단어·숙어 영 → 한 쓰기</div>
  <div class="meta">총 <b>{total}</b>문항 · 14회차 · 정답은 부록 「어휘 색인」에서 확인</div>
</div>
<div class="guide">✍️ <b>사용법</b> — 회차별로 영어 단어·숙어를 보고 <b>빈칸에 뜻</b>을 쓰세요. 채점은 뒤쪽 <b>「어휘 색인」</b>(알파벳순·뜻·페이지 수록)에서 찾아 확인합니다. 틀린 단어는 해당 <b>교재 페이지</b>로 돌아가 문맥과 함께 복습하세요.</div>
{sections}
</body></html>'''
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"어휘 미니 테스트 생성: {len(exams)}회차 · 총 {total}문항 → {OUT}")


if __name__ == "__main__":
    build()
