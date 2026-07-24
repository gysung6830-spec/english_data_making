#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""패러프레이징 훈련 생성기 — 실제 평가원 기출 문장 기반 객관식.

지문 은행에서 뽑은 실제 기출 문장으로 '바르게 바꿔 말한 것은?' 5지선다를 만든다.
문항 데이터: corpus/paraphrase_items.json  (지문 은행 문장 → 문항, subagent 생성)
각 문항에 출처(예: 2023 수능)를 달고, 오답마다 함정 유형을 표시한다.
출력: samples/패러프레이징_50.html  (파일명 유지, 문항 수는 {{N}}로 표기)
"""
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "corpus" / "paraphrase_items.json"
OUT = ROOT / "samples" / "패러프레이징_50.html"
CIRCLED = "①②③④⑤"

TRAP = {
  "ok":  ("정답", "b-ok"),
  "copy":("표면어휘 복사", "b-copy"),
  "rev": ("뜻 반대", "b-rev"),
  "dist":("세부 왜곡", "b-dist"),
  "over":("과도한 일반화", "b-over"),
  "off": ("초점 이탈", "b-off"),
}

def esc(s): return html.escape(str(s), quote=False)

def exam_label(eid):
    if not eid or "-" not in eid:
        return esc(eid or "")
    y, m = eid.split("-", 1)
    m = {"06": "6월", "09": "9월", "수능": "수능", "11": "수능"}.get(m, m)
    return f"{y} {m}"

def build():
    items = json.loads(ITEMS.read_text(encoding="utf-8"))
    probs, ans = [], []
    for i, it in enumerate(items, 1):
        typ = it.get("type", "")
        src = it.get("src", "")
        a = it.get("answer")
        chs = it.get("choices", [])
        cite = exam_label(it.get("exam_id", ""))
        lis = "".join(
            f'<li><span class="num">{CIRCLED[j]}</span>{esc(c.get("t",""))}</li>'
            for j, c in enumerate(chs))
        probs.append(
            f'''<div class="q"><div class="qhead"><span class="qn">Q{i}</span><span class="tp">{esc(typ)}</span>'''
            f'''<span class="ask">다음 문장을 바르게 바꿔 말한 것은?</span>'''
            f'''{f'<span class="cite">평가원 {cite}</span>' if cite else ''}</div>'''
            f'''<div class="src">{esc(src)}</div><ul class="ch">{lis}</ul></div>''')
        rows = ""
        for j, c in enumerate(chs):
            t = c.get("trap", "off")
            nm, cls = TRAP.get(t, TRAP["off"])
            okcls = ' class="ok"' if t == "ok" else ""
            rows += (f'<tr{okcls}><td class="oc">{CIRCLED[j]}</td>'
                     f'<td>{esc(c.get("t",""))} <span class="badge {cls}">{nm}</span></td></tr>')
        ans.append(
            f'<div class="ak"><span class="qn">Q{i}</span> 정답 '
            f'<span class="cor">{CIRCLED[a-1] if a else "?"}</span> '
            f'<span class="badge b-ok">{esc(typ)}</span> '
            f'<span class="src-mini">{esc(src)}</span><table>{rows}</table></div>')
    doc = (TPL.replace("{{PROB}}", "\n".join(probs))
              .replace("{{ANS}}", "\n".join(ans))
              .replace("{{N}}", str(len(items))))
    OUT.write_text(doc, encoding="utf-8")
    print(f"패러프레이징 {len(items)}문항(실제 기출 문장) → {OUT}")

TPL = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>패러프레이징 훈련</title><style>
@page{ size:A4; margin:11mm 12mm; } *{ box-sizing:border-box; }
body{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; margin:0; }
.wrap{ max-width:820px; margin:0 auto; }
:root{ --deep:#1f7a5c; --deep-d:#12543d; --amber:#ffe9a8; --trap:#cd5049; --muted:#6b7280; --line:#e6e8ea; }
.cover{ text-align:center; padding:12px 0 8px; border-bottom:3px solid var(--deep-d); margin-bottom:12px; }
.cover .t{ font-size:19px; font-weight:800; color:var(--deep-d); } .cover .s{ font-size:10px; color:var(--muted); }
.q{ border:1px solid var(--line); border-radius:7px; padding:10px 13px; margin-bottom:9px; break-inside:avoid; }
.qhead{ display:flex; align-items:center; gap:6px; }
.q .qn{ background:var(--deep-d); color:#fff; font-weight:800; font-size:10.5px; padding:1px 8px; border-radius:5px; }
.q .tp{ font-size:8.5px; font-weight:800; color:#fff; background:var(--deep); border-radius:8px; padding:1px 7px; }
.q .ask{ font-size:9.8px; font-weight:700; }
.q .cite{ margin-left:auto; font-size:8.3px; font-weight:700; color:var(--muted); border:1px solid var(--line); border-radius:8px; padding:1px 7px; }
.src{ background:#eaf5f0; border:1px solid #cfe6dd; border-radius:6px; padding:7px 10px; margin:6px 0; font-size:10.3px; line-height:1.5; }
.ch{ list-style:none; margin:0; padding:0; } .ch li{ font-size:9.7px; padding:2px 0 2px 3px; line-height:1.45; } .ch .num{ font-weight:800; margin-right:4px; }
.answers{ break-before:page; } .answers h2{ font-size:14px; color:var(--deep-d); border-bottom:2px solid var(--deep); padding-bottom:5px; }
.ak{ font-size:9.4px; margin-bottom:8px; break-inside:avoid; } .ak .qn{ background:var(--deep-d); color:#fff; font-weight:800; font-size:9.5px; padding:1px 6px; border-radius:4px; margin-right:5px; }
.ak .cor{ color:var(--deep); font-weight:800; } .ak .src-mini{ font-size:8.7px; color:var(--muted); font-style:italic; }
.ak table{ width:100%; border-collapse:collapse; margin-top:3px; }
.ak td{ padding:2px 6px; border-bottom:1px solid var(--line); font-size:9px; } .ak .oc{ font-weight:800; width:18px; } .ak tr.ok{ background:#eaf5f0; }
.badge{ display:inline-block; font-size:7.8px; font-weight:800; border-radius:8px; padding:0 6px; color:#fff; }
.b-ok{ background:var(--deep); } .b-copy{ background:#c2410c; } .b-rev{ background:var(--trap); } .b-dist{ background:#a5342d; } .b-over{ background:#b8860b; } .b-off{ background:var(--muted); }
</style></head><body><div class="wrap">
<div class="cover"><div class="t">패러프레이징 훈련 — {{N}}문항</div>
<div class="s">모든 문장은 실제 평가원 기출에서 발췌. 정답=뜻 유지·표현 교체 / 오답=표면어휘 복사·뜻 반대·세부 왜곡·과도한 일반화·초점 이탈.</div></div>
{{PROB}}
<div class="answers"><h2>정답 &amp; 해설 — 오답 함정 유형까지</h2>{{ANS}}</div>
</div></body></html>'''

if __name__ == "__main__":
    build()
