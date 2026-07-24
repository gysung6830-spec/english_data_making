#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""패러프레이징 훈련 생성기 — 두 트랙.

■ 실전편 (corpus/paraphrase_real.json)
  실제 평가원 문항에서 캐낸 문항. 지문 핵심 문장(원문) + **실제 평가원 선지**(정답·오답 전부 기출).
  정답 선지가 지문을 어떻게 바꿨는지(해부)와 오답 함정 유형을 표시.
■ 기초편 (corpus/paraphrase_items.json)
  실제 기출 '문장'에 대한 변환 연습. 문장은 기출이지만 **선지는 학습용 예문**(저자 작성).

출력: samples/패러프레이징_50.html  (파일명 유지)
"""
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL = ROOT / "corpus" / "paraphrase_real.json"
ITEMS = ROOT / "corpus" / "paraphrase_items.json"
EXPLAIN = ROOT / "corpus" / "paraphrase_explain.json"
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

def q_card(qn, typ, ask, src, choices, cite):
    lis = "".join(
        f'<li><span class="num">{CIRCLED[j]}</span>{esc(c.get("t",""))}</li>'
        for j, c in enumerate(choices))
    cite_html = f'<span class="cite">{esc(cite)}</span>' if cite else ""
    return (f'<div class="q"><div class="qhead"><span class="qn">{esc(qn)}</span>'
            f'<span class="tp">{esc(typ)}</span><span class="ask">{esc(ask)}</span>'
            f'{cite_html}</div>'
            f'<div class="src">{esc(src)}</div><ul class="ch">{lis}</ul></div>')

def a_card(qn, typ, a, choices, src, ex=None, extra=""):
    exrows = (ex or {}).get("rows") or []
    rows = ""
    for j, c in enumerate(choices):
        t = c.get("trap", "off"); nm, cls = TRAP.get(t, TRAP["off"])
        okcls = ' class="ok"' if t == "ok" else ""
        ko = esc(exrows[j].get("ko","")) if j < len(exrows) else ""
        why = esc(exrows[j].get("why","")) if j < len(exrows) else ""
        detail = ((f'<div class="rko">{ko}</div>' if ko else "")
                  + (f'<div class="rwhy">{"✓ " if t=="ok" else "✗ "}{why}</div>' if why else ""))
        rows += (f'<tr{okcls}><td class="oc">{CIRCLED[j]}</td>'
                 f'<td><span class="ce">{esc(c.get("t",""))}</span> <span class="badge {cls}">{nm}</span>'
                 f'{detail}</td></tr>')
    srcko = (ex or {}).get("src_ko", "")
    srcline = f'<div class="src-ko">원문 해석 — {esc(srcko)}</div>' if srcko else ""
    return (f'<div class="ak"><span class="qn">{esc(qn)}</span> 정답 '
            f'<span class="cor">{CIRCLED[a-1] if a else "?"}</span> '
            f'<span class="badge b-ok">{esc(typ)}</span> '
            f'<span class="src-mini">{esc(src)}</span>{extra}{srcline}<table>{rows}</table></div>')

def build():
    real = json.loads(REAL.read_text(encoding="utf-8")) if REAL.exists() else []
    items = json.loads(ITEMS.read_text(encoding="utf-8")) if ITEMS.exists() else []
    explain = {}
    if EXPLAIN.exists():
        for e in json.loads(EXPLAIN.read_text(encoding="utf-8")):
            explain[e.get("id")] = e

    # ── 실전편 (실제 평가원 선지) ──
    rprob, rans = [], []
    for i, it in enumerate(real):
        if not it.get("src"):
            continue
        qn = f"실전 {len(rprob)+1}"
        cite = f"평가원 {exam_label(it.get('exam_id',''))} {it.get('num','')}번"
        rprob.append(q_card(qn, it.get("type",""),
            "원문을 바르게 바꿔 말한 선지는? (①~⑤ 모두 실제 평가원 선지)",
            it.get("src",""), it.get("choices",[]), cite))
        dis = it.get("dissect","")
        extra = (f' <span class="badge b-tf">{esc(it.get("answer_transform",""))}</span>'
                 f'<div class="dissect">🔎 {esc(dis)}</div>' if dis else "")
        rans.append(a_card(qn, it.get("type",""), it.get("answer"),
            it.get("choices",[]), it.get("src",""), explain.get(f"real|{i}"), extra))
    rcount = len(rprob)

    # ── 기초편 (문장 변환 연습) ──
    bprob, bans = [], []
    for i, it in enumerate(items):
        qn = f"기초 {i+1}"
        cite = f"문장 출처 · {exam_label(it.get('exam_id',''))}"
        bprob.append(q_card(qn, it.get("type",""),
            "다음 문장을 바르게 바꿔 말한 것은?",
            it.get("src",""), it.get("choices",[]), cite))
        bans.append(a_card(qn, it.get("type",""), it.get("answer"),
            it.get("choices",[]), it.get("src",""), explain.get(f"basic|{i}")))
    bcount = len(bprob)

    doc = (TPL
        .replace("{{RCOUNT}}", str(rcount)).replace("{{BCOUNT}}", str(bcount))
        .replace("{{TOTAL}}", str(rcount + bcount))
        .replace("{{RPROB}}", "\n".join(rprob)).replace("{{RANS}}", "\n".join(rans))
        .replace("{{BPROB}}", "\n".join(bprob)).replace("{{BANS}}", "\n".join(bans)))
    OUT.write_text(doc, encoding="utf-8")
    print(f"패러프레이징 실전편 {rcount} + 기초편 {bcount} = {rcount+bcount}문항 → {OUT}")

TPL = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>패러프레이징 훈련</title><style>
@page{ size:A4; margin:11mm 12mm; } *{ box-sizing:border-box; }
body{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; margin:0; }
.wrap{ max-width:820px; margin:0 auto; }
:root{ --deep:#1f7a5c; --deep-d:#12543d; --amber:#ffe9a8; --trap:#cd5049; --muted:#6b7280; --line:#e6e8ea; }
.cover{ text-align:center; padding:12px 0 8px; border-bottom:3px solid var(--deep-d); margin-bottom:12px; }
.cover .t{ font-size:19px; font-weight:800; color:var(--deep-d); } .cover .s{ font-size:10px; color:var(--muted); }
.band{ font-size:13.5px; font-weight:800; color:#fff; background:var(--deep); border-radius:6px; padding:5px 13px; margin:14px 0 9px; break-after:avoid; }
.band small{ font-weight:600; opacity:.92; font-size:9.5px; }
.band.real{ background:var(--deep-d); } .band.basic{ background:#5a6b64; }
.lead{ font-size:9.6px; color:#2b3a34; background:#eef4f1; border-left:3px solid var(--deep); border-radius:0 5px 5px 0; padding:7px 11px; margin-bottom:10px; }
.lead b{ color:var(--deep-d); }
.q{ border:1px solid var(--line); border-radius:7px; padding:10px 13px; margin-bottom:9px; break-inside:avoid; }
.qhead{ display:flex; align-items:center; gap:6px; }
.q .qn{ background:var(--deep-d); color:#fff; font-weight:800; font-size:9.8px; padding:1px 8px; border-radius:5px; white-space:nowrap; }
.q .tp{ font-size:8.5px; font-weight:800; color:#fff; background:var(--deep); border-radius:8px; padding:1px 7px; white-space:nowrap; }
.q .ask{ font-size:9.5px; font-weight:700; }
.q .cite{ margin-left:auto; font-size:8.1px; font-weight:700; color:var(--muted); border:1px solid var(--line); border-radius:8px; padding:1px 7px; white-space:nowrap; }
.src{ background:#eaf5f0; border:1px solid #cfe6dd; border-radius:6px; padding:7px 10px; margin:6px 0; font-size:10.2px; line-height:1.5; }
.ch{ list-style:none; margin:0; padding:0; } .ch li{ font-size:9.6px; padding:2px 0 2px 3px; line-height:1.45; } .ch .num{ font-weight:800; margin-right:4px; }
.answers{ break-before:page; } .answers h2{ font-size:14px; color:var(--deep-d); border-bottom:2px solid var(--deep); padding-bottom:5px; }
.ak{ font-size:9.3px; margin-bottom:8px; break-inside:avoid; } .ak .qn{ background:var(--deep-d); color:#fff; font-weight:800; font-size:9.2px; padding:1px 6px; border-radius:4px; margin-right:5px; }
.ak .cor{ color:var(--deep); font-weight:800; } .ak .src-mini{ font-size:8.6px; color:var(--muted); font-style:italic; }
.ak table{ width:100%; border-collapse:collapse; margin-top:3px; }
.ak td{ padding:3px 6px; border-bottom:1px solid var(--line); font-size:9px; vertical-align:top; } .ak .oc{ font-weight:800; width:18px; } .ak tr.ok{ background:#eaf5f0; }
.ak .ce{ color:#3a3f45; }
.ak .src-ko{ font-size:8.9px; font-weight:700; color:#12543d; background:#eef4f1; border-radius:4px; padding:3px 8px; margin:3px 0 4px; }
.ak .rko{ font-size:8.6px; color:#4a5560; margin-top:2px; }
.ak .rwhy{ font-size:8.6px; color:#7a1f19; margin-top:1px; } .ak tr.ok .rwhy{ color:#12543d; }
.dissect{ font-size:8.8px; color:var(--deep-d); background:#fffdf3; border:1px solid #e0b94a; border-radius:5px; padding:4px 8px; margin-top:4px; }
.badge{ display:inline-block; font-size:7.8px; font-weight:800; border-radius:8px; padding:0 6px; color:#fff; }
.b-ok{ background:var(--deep); } .b-copy{ background:#c2410c; } .b-rev{ background:var(--trap); } .b-dist{ background:#a5342d; } .b-over{ background:#b8860b; } .b-off{ background:var(--muted); } .b-tf{ background:#12543d; }
</style></head><body><div class="wrap">
<div class="cover"><div class="t">패러프레이징 훈련 — {{TOTAL}}문항</div>
<div class="s">평가원 정답 선지 = 지문을 바꿔 말한 것 / 오답 = 표면어휘 복사·뜻 반대·세부 왜곡·과도한 일반화·초점 이탈.</div></div>

<div class="band real">실전편 · 실제 평가원 선지 <small>({{RCOUNT}}문항 — ①~⑤ 전부 실제 기출 선지, 정답이 지문을 어떻게 바꿨는지 해부)</small></div>
<div class="lead">여기 선지는 <b>모두 실제 평가원 기출 선지</b>입니다. 정답 선지가 지문(원문)을 어떤 방식으로 바꿔 말했는지, 오답은 어떤 함정인지 뒤 해설에서 확인하세요.</div>
{{RPROB}}

<div class="band basic">기초편 · 문장 변환 연습 <small>({{BCOUNT}}문항 — 문장은 실제 기출, 선지는 변환 원리 학습용 예문)</small></div>
<div class="lead">원문 <b>문장은 실제 평가원 기출</b>이지만, 여기 <b>선지는 5대 변환 원리를 익히기 위한 학습용 예문</b>입니다(저자 작성). 바꿔 말하기 감각을 기르는 기초 훈련입니다.</div>
{{BPROB}}

<div class="answers"><h2>정답 &amp; 해설 — 실전편</h2>{{RANS}}
<h2 style="margin-top:14px">정답 &amp; 해설 — 기초편</h2>{{BANS}}</div>
</div></body></html>'''

if __name__ == "__main__":
    build()
