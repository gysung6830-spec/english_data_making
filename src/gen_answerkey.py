# -*- coding: utf-8 -*-
"""부록: 정답 일람표 — 회차×문항 한 장짜리 채점표."""
import json, html, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "workbook_content.json")
OUT = os.path.join(ROOT, "samples", "정답일람.html")

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
NUMS = [21, 22, 23, 24, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41]
# 유형 그룹(색 구분용)
GRP = {21: "a", 22: "a", 23: "a", 24: "a", 30: "b", 31: "b", 32: "b", 33: "b",
       34: "b", 35: "c", 36: "c", 37: "c", 38: "c", 39: "c", 40: "c", 41: "c"}
# 평가원 수능 홀/짝 형태(모의평가는 단일 정답표)
FORM = {"2022-수능": "홀수형", "2023-수능": "홀수형",
        "2024-수능": "짝수형", "2025-수능": "짝수형"}


def esc(s):
    return html.escape(str(s or ""))


def exam_label(eid):
    y, m = eid.split("-")
    m = {"06": "6월", "09": "9월", "수능": "수능"}.get(m, m)
    return f"{y}학년도 {m}"


def ekey(e):
    y, m = e.split("-")
    return (int(y), {"06": 1, "09": 2, "수능": 3}.get(m, 9))


def circ(a):
    try:
        return CIRCLED[int(a) - 1]
    except Exception:
        return esc(a)


def build():
    data = json.load(open(SRC, encoding="utf-8"))
    ans = {}
    for c in data:
        eid, num = c["key"].split("|")
        ans.setdefault(eid, {})[int(num)] = c.get("answer")
    exams = sorted(ans, key=ekey)

    head_cells = "".join(f'<th class="g{GRP[n]}">{n}</th>' for n in NUMS)
    rows = ""
    for e in exams:
        form = FORM.get(e)
        formtag = f'<span class="form">{form}</span>' if form else ""
        cells = ""
        for n in NUMS:
            a = ans[e].get(n)
            cells += f'<td class="g{GRP[n]}">{circ(a)}</td>'
        rows += (f'<tr><th class="rh">{esc(exam_label(e))}{formtag}</th>{cells}</tr>')

    doc = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>정답 일람표</title><style>
@page{{ size:A4; margin:14mm 12mm; }}
*{{ box-sizing:border-box; }}
body{{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; margin:0; background:#fff; }}
:root{{ --ink:#1f7a5c; --ink-d:#12543d; --line:#e6e8ea; --muted:#6b7280;
  --ga:#e9f4ef; --gb:#fff4e0; --gc:#eef2fb; }}
.ak-cover{{ background:linear-gradient(160deg,#12543d 0%,#1f7a5c 78%,#2a916d 100%); color:#fff; border-radius:10px; padding:26px 30px; margin-bottom:16px; }}
.ak-cover .kick{{ font-size:11px; font-weight:800; letter-spacing:3px; opacity:.85; }}
.ak-cover .t{{ font-size:30px; font-weight:800; margin:6px 0 4px; }}
.ak-cover .sub{{ font-size:11px; opacity:.92; }}
.guide{{ background:#f3f8f5; border:1px solid #cfe5da; border-radius:8px; padding:8px 12px; font-size:9px; color:#33514a; margin-bottom:12px; }}
.guide b{{ color:var(--ink-d); }}
table{{ border-collapse:collapse; width:100%; table-layout:fixed; }}
th,td{{ border:1px solid #d7dde1; text-align:center; padding:5px 2px; font-size:10.5px; }}
thead th{{ background:var(--ink-d); color:#fff; font-weight:800; font-size:9.5px; }}
thead th.rh{{ background:var(--ink-d); }}
.rh{{ width:96px; text-align:left; padding-left:8px; font-size:9px; font-weight:800; color:var(--ink-d); background:#f4faf7; white-space:nowrap; }}
tbody td{{ font-weight:800; color:#1a1f26; }}
td.ga,th.ga{{ background:var(--ga); }} td.gb,th.gb{{ background:var(--gb); }} td.gc,th.gc{{ background:var(--gc); }}
thead th.ga,thead th.gb,thead th.gc{{ color:#fff; }}
thead th.ga{{ background:#2a7d5f; }} thead th.gb{{ background:#c58a2a; }} thead th.gc{{ background:#3f5fa6; }}
.form{{ display:inline-block; font-size:7px; font-weight:800; color:#fff; background:var(--muted); border-radius:6px; padding:0 5px; margin-left:5px; vertical-align:1px; }}
.legend{{ margin-top:12px; display:flex; gap:14px; flex-wrap:wrap; font-size:8.6px; color:#4a5560; }}
.legend .lg{{ display:flex; align-items:center; gap:5px; }}
.legend .sw{{ width:14px; height:14px; border-radius:3px; border:1px solid #d7dde1; display:inline-block; }}
.sw.ga{{ background:var(--ga); }} .sw.gb{{ background:var(--gb); }} .sw.gc{{ background:var(--gc); }}
.note2{{ margin-top:10px; font-size:8.4px; color:var(--muted); }}
</style></head><body>
<div class="ak-cover">
  <div class="kick">ANSWER KEY · 본책 맨 끝</div>
  <div class="t">정답 일람표</div>
  <div class="sub">14회차 × 16문항 · 빠른 자가 채점용</div>
</div>
<div class="guide">📝 <b>채점법</b> — 회차별 가로줄에서 문항 번호를 찾아 내 답과 대조하세요. 색은 유형 그룹입니다: <b style="color:#2a7d5f">초록=대의 파악(21~24)</b> · <b style="color:#c58a2a">주황=어휘·빈칸(30~34)</b> · <b style="color:#3f5fa6">파랑=논리·구조(35~41)</b>.</div>
<table>
<thead><tr><th class="rh">회차 \\ 문항</th>{head_cells}</tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="legend">
  <span class="lg"><span class="sw ga"></span>대의 파악 · 함축(21)/요지(22)/주제(23)/제목(24)</span>
  <span class="lg"><span class="sw gb"></span>어휘(30) · 빈칸추론(31~34)</span>
  <span class="lg"><span class="sw gc"></span>무관(35)/순서(36·37)/삽입(38·39)/요약(40)/장문제목(41)</span>
</div>
<div class="note2">※ 평가원 수능은 홀수형/짝수형에 따라 선지 배열이 달라 정답 번호가 다를 수 있습니다. 본 표는 교재 수록 형(수능: {esc("2022·2023=홀수형, 2024·2025=짝수형")}) 기준입니다. 모의평가(6·9월)는 단일 정답표.</div>
</body></html>'''
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"정답 일람표 생성: {len(exams)}회차 → {OUT}")


if __name__ == "__main__":
    build()
