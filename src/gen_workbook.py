#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""유형별 훈련 워크북 생성기 — 지문 은행 → 자동 형광펜 훈련 카드(N개).

지문 은행(corpus/passage_bank.jsonl)에서 지문을 골라, 신호를 자동 감지해
🟡 노란 형광펜(신호 문장) + 🔴 빨간 형광펜(신호어=칠한 근거, A안)으로 칠하고,
유형·번호·배점·공식 정답·유형 공식을 붙인 훈련 카드를 만든다.

사용: python -m src.gen_workbook [개수]   (기본 80)
출력: samples/유형별훈련_워크북.html
"""
import sys, re, json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "corpus" / "passage_bank.jsonl"
OUT = ROOT / "samples" / "유형별훈련_워크북.html"
CIRCLED = "①②③④⑤"

# 신호(노랑 근거) — 정답 도출에 쓰는 논리 신호
SIGNALS = {
  "역접": r"\b(however|but|yet|nevertheless|nonetheless|in contrast|by contrast|on the contrary|on the other hand|instead|conversely|whereas|unlike|rather than|still|no longer)\b",
  "결론": r"\b(thus|therefore|hence|consequently|as a result|in conclusion|in short|in sum|ultimately)\b",
  "한정": r"\b(only when|only if|only|unless|except|as long as)\b",
  "주장": r"\b(should|must|ought to|need to|have to|important|essential|crucial|vital|critical|the most|the only|the single)\b",
  "인과": r"\b(because|since|due to|owing to|lead to|leads to|result in|results in|give rise to|thereby|in order to)\b",
  "통념": r"\b(many believe|it is thought|it is assumed|contrary to|traditionally|surprisingly|paradoxically)\b",
}
SKIP_PAT = r"\b(for example|for instance|such as|e\.g\.|to illustrate|in spite of)\b"
CONCESS  = r"^\s*(despite|although|though|even though)\b"

FORMULA = {
  "목적": "첫·끝 문장 + 부탁/공지 표현(please·would like)만 → 목적",
  "심경": "상황 반전(however) 전후의 감정어만 추적",
  "주장": "should·must·need to 문장 = 주장",
  "함축의미": "밑줄 ±(긍정/부정) 판정 → 뜻을 추상화한 선지",
  "요지": "역접·결론 문장 = 요지 / 예시는 스킵",
  "주제": "반복 키워드 + 주제문 → 추상 선지",
  "제목": "주제문을 압축·비유한 선지",
  "빈칸추론": "역접·한정 문장 찾아 추상화 / 지문어 그대로 쓴 선지 = 함정",
  "무관한문장": "주제에서 벗어난 소재·논리의 문장 1개",
  "글의순서": "지시어·연결어(this·however·연대)로 흐름 잇기",
  "문장삽입": "지시어가 갑자기 튀는 '논리 공백' 지점",
  "요약문": "주제문 압축 → 빈칸 두 개는 추상어",
  "지칭추론": "대명사 바로 앞 명사를 추적",
}
BAND_TITLE = {
  "18":"목적","19":"심경","20":"주장","21":"함축의미","22":"요지","23":"주제","24":"제목",
  "31-34":"빈칸추론","35":"무관한 문장","36-37":"글의 순서","38-39":"문장 삽입","40":"요약문",
  "41-45":"장문(제목·지칭)",
}
BAND_ORDER = ["18","19","20","21","22","23","24","31-34","35","36-37","38-39","40","41-45"]

def esc(s): return html.escape(s, quote=False)

def wrap_signals(sent):
    """문장 안 신호어를 빨간 형광펜(.rk)으로. 반환: (html, 신호이름목록)."""
    hits, names = [], []
    for name, pat in SIGNALS.items():
        for m in re.finditer(pat, sent, re.I):
            hits.append((m.start(), m.end())); names.append(name)
    if not hits:
        return esc(sent), []
    hits.sort()
    merged = [list(hits[0])]
    for a, b in hits[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    out, i = [], 0
    for a, b in merged:
        out.append(esc(sent[i:a])); out.append(f'<span class="rk">{esc(sent[a:b])}</span>'); i = b
    out.append(esc(sent[i:]))
    return "".join(out), sorted(set(names))

def highlight(passage):
    sents = re.split(r'(?<=[.!?])\s+', passage.strip())
    out, sig_all = [], []
    for s in sents:
        if not s.strip():
            continue
        low = s.lower()
        if re.search(SKIP_PAT, low) or re.search(CONCESS, low):
            out.append(f'<span class="sk">{esc(s)}</span>'); continue
        h, names = wrap_signals(s)
        if names:
            out.append(f'<mark class="m">{h}</mark>'); sig_all += names
        else:
            out.append(esc(s))
    return " ".join(out), sorted(set(sig_all))

def select(bank, n):
    by = {}
    for r in bank:
        by.setdefault(r["band"], []).append(r)
    for b in by:
        by[b].sort(key=lambda x: (1 if x.get("answer") else 0, x.get("signal_score", 0)), reverse=True)
    picked, i = [], 0
    # 라운드로빈으로 번호대 골고루
    while len(picked) < n:
        added = False
        for b in BAND_ORDER:
            if b in by and i < len(by[b]):
                picked.append(by[b][i]); added = True
                if len(picked) >= n: break
        if not added: break
        i += 1
    return picked

def card(r, idx):
    band = r["band"]; typ = BAND_TITLE.get(band, r.get("type", ""))
    hl, sigs = highlight(r["passage"])
    pts = f'{r.get("points")}점' if r.get("points") else ""
    ans = r.get("answer")
    choices = r.get("choices") or {}
    ch_html = ""
    if choices:
        lis = []
        for k in sorted(int(x) for x in choices):
            mark = ' class="ok"' if ans == k else ""
            tag = ' ← 정답' if ans == k else ""
            lis.append(f'<li{mark}><span class="n">{CIRCLED[k-1]}</span>{esc(str(choices[str(k)]))}<span class="a">{tag}</span></li>')
        ch_html = f'<ul class="ch">{"".join(lis)}</ul>'
    elif ans:
        ch_html = f'<div class="anonly">공식 정답 <b>{CIRCLED[ans-1]}</b></div>'
    sigline = " · ".join(sigs) if sigs else "—"
    formula = FORMULA.get(r.get("type", typ), FORMULA.get(typ, ""))
    return f'''<div class="tc">
  <div class="tch"><span class="no">{r["num"]}</span><span class="ty">{typ}</span>
    {'<span class="pt">'+pts+'</span>' if pts else ''}<span class="src">{r.get("exam_id","")}</span>
    <span class="idx">#{idx}</span></div>
  <div class="psg">{hl}</div>
  <div class="meta">🔴 이 지문의 신호(칠한 근거): <b>{sigline}</b></div>
  {ch_html}
  <div class="fx">📌 {esc(formula)}</div>
</div>'''

def build(n=80):
    bank = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines() if l.strip()]
    picked = select(bank, n)
    # 번호대별 그룹핑
    groups = {}
    for r in picked:
        groups.setdefault(r["band"], []).append(r)
    body, idx = [], 0
    for b in BAND_ORDER:
        if b not in groups: continue
        body.append(f'<div class="sec">{BAND_TITLE.get(b,b)} <small>({b}번대 · {len(groups[b])}문항)</small></div>')
        for r in groups[b]:
            idx += 1
            body.append(card(r, idx))
    doc = TEMPLATE.replace("{{BODY}}", "\n".join(body)).replace("{{N}}", str(idx))
    OUT.write_text(doc, encoding="utf-8")
    print(f"워크북 생성: {idx}문항 → {OUT}")

TEMPLATE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>유형별 훈련 워크북</title><style>
@page{ size:A4; margin:11mm 12mm; }
*{ box-sizing:border-box; }
body{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; margin:0; background:#fff; }
.wrap{ max-width:820px; margin:0 auto; }
:root{ --ink:#1f7a5c; --ink-d:#12543d; --must:#ffe9a8; --trap:#cd5049; --skip:#9aa0a6; --muted:#6b7280; --line:#e6e8ea; }
.cover{ text-align:center; padding:14px 0 8px; border-bottom:3px solid var(--ink-d); margin-bottom:14px; }
.cover .t{ font-size:20px; font-weight:800; color:var(--ink-d); }
.cover .s{ font-size:10px; color:var(--muted); }
.sec{ font-size:13px; font-weight:800; color:#fff; background:var(--ink); border-radius:6px; padding:4px 12px; margin:14px 0 9px; break-after:avoid; }
.sec small{ font-weight:600; opacity:.9; font-size:9px; }
.tc{ border:1px solid var(--line); border-left:4px solid var(--ink); border-radius:7px; padding:10px 13px; margin-bottom:10px; break-inside:avoid; }
.tch{ display:flex; align-items:center; gap:7px; border-bottom:1px solid var(--line); padding-bottom:5px; margin-bottom:7px; }
.tch .no{ background:var(--ink-d); color:#fff; font-weight:800; font-size:11px; padding:1px 8px; border-radius:5px; }
.tch .ty{ font-weight:800; font-size:12px; color:var(--ink-d); }
.tch .pt{ font-size:8.5px; font-weight:700; color:#fff; background:var(--trap); border-radius:9px; padding:1px 7px; }
.tch .src{ font-size:9px; color:var(--muted); }
.tch .idx{ margin-left:auto; font-size:9px; font-weight:800; color:var(--skip); }
.psg{ font-size:11px; line-height:1.85; }
mark.m{ background:var(--must); padding:0 1px; border-radius:2px; }
.rk{ background:#f4b8b2; color:#7a1f19; font-weight:700; padding:0 2px; border-radius:2px; box-shadow:inset 0 -2px 0 #d98b84; }
.sk{ color:var(--skip); }
.meta{ font-size:9px; color:#3a4a44; margin-top:6px; }
.meta b{ color:var(--trap); }
.ch{ list-style:none; margin:6px 0 0; padding:0; }
.ch li{ font-size:9.6px; padding:2px 0; }
.ch li .n{ font-weight:800; margin-right:4px; }
.ch li.ok{ background:#e9f4ef; border-radius:4px; padding:2px 5px; }
.ch li.ok .a{ color:var(--ink); font-weight:800; }
.anonly{ font-size:9.6px; margin-top:6px; color:var(--ink-d); }
.fx{ font-size:9.2px; font-weight:700; color:var(--ink-d); background:#eef4f1; border-radius:5px; padding:5px 9px; margin-top:7px; }
</style></head><body><div class="wrap">
<div class="cover"><div class="t">유형별 훈련 워크북 <span style="font-size:12px;color:#6b7280">— 실제 기출 {{N}}문항</span></div>
<div class="s">🟡 노란 형광펜 = 읽을 문장 / 🔴 빨간 형광펜 = 그 문장을 칠한 근거(신호). 지문 은행 자동 생성.</div></div>
{{BODY}}
</div></body></html>'''

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    build(n)
