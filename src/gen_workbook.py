#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""유형별 훈련 — 실제 기출을 '대표 카드'와 동일한 3-STEP 펼침면으로 렌더링.

각 문항 = 2쪽 펼침면:
  · STEP 1 (왼쪽) 직접 풀기 — 깨끗한 지문 + 선지 + 셀프체크
  · STEP 2 (오른쪽 상) 훈련(정답 칠) — 🟡형광펜·🔴신호 + 노랑 도출 + 선지 판정 + 공식
  · STEP 3 (오른쪽 하) 해석(직독직해) — 같은 형광펜 색끼리 영↔한 청크 대응

콘텐츠(도출·직독직해·판정)는 corpus/workbook_content.json 에서 읽는다
(subagent가 지문별로 생성). 콘텐츠가 없는 문항은 간이 훈련 카드로 폴백.

사용: python -m src.gen_workbook [개수]   (기본 80)
출력: samples/유형별훈련_워크북.html
"""
import sys, re, json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "corpus" / "passage_bank.jsonl"
CONTENT = ROOT / "corpus" / "workbook_content.json"
OUT = ROOT / "samples" / "유형별훈련_워크북.html"
CIRCLED = "①②③④⑤"

SIGNALS = {
  "역접": r"\b(however|but|yet|nevertheless|nonetheless|in contrast|by contrast|on the contrary|on the other hand|instead|conversely|whereas|unlike|rather than|still|no longer)\b",
  "결론": r"\b(thus|therefore|hence|consequently|as a result|in conclusion|in short|in sum|ultimately)\b",
  "한정": r"\b(only when|only if|only|unless|except|as long as)\b",
  "주장": r"\b(should|must|ought to|need to|have to|important|essential|crucial|vital|critical|the most|the only|the single)\b",
  "인과": r"\b(because|since|due to|owing to|lead to|leads to|result in|results in|give rise to|thereby|in order to)\b",
  "통념": r"\b(many believe|it is thought|it is assumed|contrary to|traditionally|surprisingly|paradoxically)\b",
}
SKIP_PAT = r"\b(for example|for instance|such as|e\.g\.|to illustrate|in spite of)\b"

FORMULA = {
  "함축의미": "밑줄 ±(긍정/부정) 판정 → 뜻을 추상화한 선지",
  "요지": "역접·결론 문장 = 요지 / 예시는 스킵",
  "주제": "반복 키워드 + 주제문 → 추상 선지",
  "제목": "주제문을 압축·비유한 선지",
  "빈칸추론": "역접·한정 문장 추상화 / 지문어 복사 선지 = 함정",
  "무관한 문장": "주제에서 벗어난 소재·논리의 문장 1개",
  "글의 순서": "지시어·연결어(this·however·연대)로 흐름 잇기",
  "문장 삽입": "지시어가 갑자기 튀는 '논리 공백' 지점",
  "요약문": "주제문 압축 → 빈칸 두 개는 추상어",
}
PROMPT = {
  "21": "밑줄 친 부분이 다음 글에서 의미하는 바로 가장 적절한 것은?",
  "22": "다음 글의 요지로 가장 적절한 것은?",
  "23": "다음 글의 주제로 가장 적절한 것은?",
  "24": "다음 글의 제목으로 가장 적절한 것은?",
  "31-34": "빈칸에 들어갈 말로 가장 적절한 것은?",
  "35": "다음 글에서 전체 흐름과 관계 없는 문장은?",
  "36-37": "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?",
  "38-39": "글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?",
  "40": "다음 글의 내용을 한 문장으로 요약하고자 한다. 빈칸에 들어갈 말로 가장 적절한 것은?",
}
REMIND = {
  "21": [("역접 However","y"),("한정 only","y"),("주장 must","y"),("예시 For example ✕","g"),("양보 Despite ✕","g")],
  "22": [("역접 However","y"),("결론 Thus","y"),("주장 should","y"),("예시 For example ✕","g")],
  "23": [("역접 However","y"),("결론 Therefore","y"),("반복 키워드","y"),("예시 such as ✕","g")],
  "24": [("역접 However","y"),("결론 In sum","y"),("주장 must","y"),("예시 e.g. ✕","g")],
  "31-34": [("역접 However","y"),("한정 only when","y"),("결론 Thus","y"),("예시 For example ✕","g"),("양보 Despite ✕","g")],
  "35": [("주제 키워드","y"),("역접 However","y"),("예시 For instance ✕","g")],
  "36-37": [("지시어 this·that","y"),("연결어 However·So","y"),("연대·순서","y")],
  "38-39": [("지시어 they·this","y"),("역접 However","y"),("논리 공백","y")],
}
BAND_TITLE = {
  "21":"함축의미","22":"요지","23":"주제","24":"제목",
  "31-34":"빈칸추론","35":"무관한 문장","36-37":"글의 순서","38-39":"문장 삽입","40":"요약문",
}
BAND_ORDER = ["21","22","23","24","31-34","35","36-37","38-39","40"]
ALLOWED = set(range(21, 25)) | set(range(31, 42))

def esc(s): return html.escape(str(s), quote=False)


def select(bank, n):
    bank = [r for r in bank if r.get("num") in ALLOWED]
    by = {}
    for r in bank:
        by.setdefault(r["band"], []).append(r)
    for b in by:
        by[b].sort(key=lambda x: (1 if x.get("answer") else 0, x.get("signal_score", 0)), reverse=True)
    picked, i = [], 0
    while len(picked) < n:
        added = False
        for b in BAND_ORDER:
            if b in by and i < len(by[b]):
                picked.append(by[b][i]); added = True
                if len(picked) >= n: break
        if not added: break
        i += 1
    return picked


# ---------- 콘텐츠 기반 렌더 (대표 카드 깊이) ----------

def _inline_tags(text, tags):
    """문장 안 신호어를 <tag>+<rk>로 인라인 표시. tags=[{sig,word}]."""
    out = esc(text)
    for t in (tags or []):
        w = t.get("word") or ""
        sig = t.get("sig") or ""
        if not w:
            continue
        m = re.search(re.escape(w), out, re.I)
        if not m:
            # esc 이후 못 찾으면 원문에서 위치 무시하고 접두 태그만
            out = f'<span class="tag hot">{esc(sig)}</span> ' + out
            continue
        s, e = m.span()
        rep = f'<span class="tag hot">{esc(sig)}</span><span class="rk">{out[s:e]}</span>'
        out = out[:s] + rep + out[e:]
    return out


def step2_passage(hl):
    parts = []
    for seg in hl:
        role = seg.get("role", "skip")
        txt = seg.get("t", "")
        if role == "skip":
            parts.append(f'<span class="sk">{esc(txt)}</span>')
        else:
            inner = _inline_tags(txt, seg.get("tags"))
            cls = "m" if role == "yellow" else "g"
            parts.append(f'<mark class="{cls}">{inner}</mark>')
    return " ".join(parts)


def clean_passage(hl, band):
    """STEP1 문제용 깨끗한 지문 = hl 문장들을 그대로 이어붙임(형광펜 없음)."""
    txt = " ".join(seg.get("t", "") for seg in hl).strip()
    e = esc(txt)
    # 밑줄/빈칸 표기 정돈
    e = re.sub(r'_{3,}', '<span class="bk">&nbsp;&nbsp;&nbsp;</span>', e)
    return e


def derive_block(d):
    steps = ""
    for i, s in enumerate(d.get("steps", [])):
        yb = f'노랑{CIRCLED[i]}' if i < 5 else '노랑'
        an = f' <span class="an">— {s.get("an","")}</span>' if s.get("an") else ""
        steps += f'<li><span class="yb">{yb}</span>{s.get("ko","")}{an}</li>'
    concl = f'<div class="concl">{d.get("concl","")}</div>' if d.get("concl") else ""
    gnote = f'<div class="gnote">{esc(d.get("gnote",""))}</div>' if d.get("gnote") else ""
    return f'''<div class="derive">
      <div class="dh">🟡 노란색 문장만으로 정답이 나오는 과정 <span style="font-weight:600;color:#a58a3a;font-size:8.3px">(지문 속 노란 라벨 = 그 문장을 칠한 이유·신호)</span></div>
      <ol>{steps}</ol>{concl}{gnote}</div>'''


def paraphrase_line(p):
    if not p:
        return ""
    frm = esc(p.get("from", "")); to = esc(p.get("to", "")); topt = p.get("to_opt")
    copies = p.get("copies") or []
    cp = " ".join(f'<span class="cp">{esc(c)}</span>' for c in copies)
    tail = f' / 복사 함정 {cp}' if cp else ""
    arw = f'<span class="arw">→</span> {CIRCLED[topt-1] if topt else ""}' if to else ""
    return f'<div class="pline"><span class="lb">패러프레이즈</span> <span class="sw">{frm}</span> {arw} <span class="sw">{to}</span> ✓{tail}</div>'


def opts_block(opts, answer):
    lis = []
    for o in opts:
        n = o.get("n")
        ok = (o.get("verdict") == "ok") or (n == answer)
        cls = "opt ok" if ok else "opt x"
        jd = o.get("jd") or ("✔ 근거" if ok else "✘")
        lis.append(f'<div class="{cls}"><span class="n">{CIRCLED[n-1] if n else "·"}</span>'
                    f'<span class="tx">{o.get("tx","")}</span><span class="jd">{esc(jd)}</span></div>')
    return f'<div class="opts">{"".join(lis)}</div>'


def direct_block(num, typ, direct):
    rows = ""
    for i, r in enumerate(direct):
        en = " ".join(f'<span class="{c[1]}">{esc(c[0])}</span>' for c in r.get("en", []))
        ko = " ".join(f'<span class="{c[1]}">{esc(c[0])}</span>' for c in r.get("ko", []))
        note = f' <span style="color:#8a6a00;font-weight:700">← {esc(r["note"])}</span>' if r.get("note") else ""
        rows += (f'<div class="row"><span class="bn">{i+1}</span>'
                 f'<div class="en">{en}</div><div class="ko">{ko}{note}</div></div>')
    return rows


def opt_line(item):
    return item.get("opt_line", "")


def render_spread(rec, c, idx):
    band = rec["band"]; typ = BAND_TITLE.get(band, rec.get("type", ""))
    num = rec["num"]; pts = f'{rec.get("points")}점' if rec.get("points") else ""
    answer = c.get("answer") or rec.get("answer")
    hl = c.get("hl") or []
    choices = rec.get("choices") or {}
    prompt = PROMPT.get(band, "다음 글을 읽고 물음에 답하시오.")
    # STEP1 선지
    opt_lines = ""
    for k in sorted(int(x) for x in choices):
        opt_lines += f'<span class="o">{CIRCLED[k-1]} {esc(choices[str(k)])}</span>'
    # 신호 리마인더 칩
    chips = "".join(f'<span class="chip {cl}">{esc(tx)}</span>' for tx, cl in REMIND.get(band, REMIND["31-34"]))
    formula = FORMULA.get(typ, "")
    src_ans = c.get("answer_src", "given")
    ans_note = "" if src_ans == "given" else " <span style=\"font-size:8px;color:#a86b00\">(정답 미공개 → 풀이로 확정)</span>"

    left = f'''<div class="qproblem">
    <div class="pbanner"><span class="no">{num}</span><span class="ty">{esc(typ)}</span>
      {'<span class="pt">'+pts+'</span>' if pts else ''}<span class="step">STEP 1 · 직접 풀기 ✍️</span></div>
    <div class="pbody">
      <div class="pmain">
        <div class="how">🖍 신호 사전을 떠올리며 <b>무조건 읽을 문장에 형광펜</b>을 직접 치고, 예시는 넘기며 답을 골라보세요.</div>
        <div class="psg work">{clean_passage(hl, band)}</div>
        <div class="pracopts"><div class="ttl">{esc(prompt)}</div>{opt_lines}</div>
        <div class="pguide"><div class="h">🖍 이렇게 풀어요</div>
          <div class="g3">
            <div class="s"><span class="k">1</span>묻는 문장부터 읽고 '무엇을 묻나' 파악</div>
            <div class="s"><span class="k">2</span>역접·한정·결론 신호 문장만 🟡, 예시는 넘기기</div>
            <div class="s"><span class="k">3</span>지문어 복사 선지 소거 → 바꿔 말한 선지</div>
          </div>
        </div>
      </div>
      <div class="pside">
        <div class="mini"><div class="h">📢 신호 리마인더</div>{chips}</div>
        <div class="mini"><div class="h">✅ 셀프 체크</div>
          <ul class="check">
            <li>근거 신호 문장을 찾아 칠했나?</li>
            <li>예시·양보절은 회색으로 넘겼나?</li>
            <li>지문 단어 그대로 쓴 선지부터 지웠나?</li>
          </ul>
        </div>
        <div class="memo"><div class="h">✍️ 내 풀이</div>
          <div class="row">걸린 시간 <span class="fill"></span></div>
          <div class="row">내가 고른 답 <span class="fill"></span></div>
          <div class="row">근거 문장(내 생각):<span class="big"></span></div>
        </div>
        <div class="ptip"><div class="h">💡 {esc(typ)} 팁</div>{esc(formula)}</div>
      </div>
    </div>
  </div>'''

    right = f'''<div class="qsolution">
    <div class="card">
      <div class="hd"><span class="no">{num}</span><span class="ty">{esc(typ)}</span><span class="kind">STEP 2 · 훈련 (정답 칠)</span><span class="tm">{esc(rec.get("exam_id",""))} · #{idx}{ans_note}</span></div>
      <div class="psg">{step2_passage(hl)}</div>
      {derive_block(c.get("derive", {}))}
      {paraphrase_line(c.get("paraphrase"))}
      {opts_block(c.get("opts", []), answer)}
      <div class="formula"><span class="k">공식</span>{esc(formula)}</div>
    </div>
    <div class="card trans">
      <div class="hd"><span class="no">{num}</span><span class="ty">{esc(typ)}</span><span class="kind" style="color:var(--src-line);border-color:var(--src-line)">STEP 3 · 해석 (직독직해)</span><span class="tm">🟡문장·선지만</span></div>
      <div class="dchl">
        <span class="kt">🟡 무조건 읽는 문장 — 같은 형광펜 색끼리 영↔한 대응</span>
        {direct_block(num, typ, c.get("direct", []))}
        <div class="opt-line">{opt_line(c)}</div>
      </div>
    </div>
  </div>'''
    return f'<div class="spread">{left}{right}</div>'


# ---------- 폴백(콘텐츠 없음): 간이 훈련 카드 ----------

def _fallback_hl(passage):
    sents = re.split(r'(?<=[.!?])\s+', passage.strip())
    out = []
    for s in sents:
        if not s.strip():
            continue
        low = s.lower()
        if re.search(SKIP_PAT, low):
            out.append(f'<span class="sk">{esc(s)}</span>'); continue
        hit = None
        for name, pat in SIGNALS.items():
            m = re.search(pat, s, re.I)
            if m:
                hit = (name, m.group(0)); break
        if hit:
            inner = _inline_tags(s, [{"sig": hit[0], "word": hit[1]}])
            out.append(f'<mark class="m">{inner}</mark>')
        else:
            out.append(esc(s))
    return " ".join(out)


def render_fallback(rec, idx):
    band = rec["band"]; typ = BAND_TITLE.get(band, rec.get("type", ""))
    num = rec["num"]; pts = f'{rec.get("points")}점' if rec.get("points") else ""
    ans = rec.get("answer"); choices = rec.get("choices") or {}
    ch = ""
    for k in sorted(int(x) for x in choices):
        cls = ' class="opt ok"' if ans == k else ' class="opt x"'
        jd = '<span class="jd">✔ 정답</span>' if ans == k else '<span class="jd"></span>'
        ch += f'<div{cls}><span class="n">{CIRCLED[k-1]}</span><span class="tx">{esc(choices[str(k)])}</span>{jd}</div>'
    formula = FORMULA.get(typ, "")
    return f'''<div class="card solo">
      <div class="hd"><span class="no">{num}</span><span class="ty">{esc(typ)}</span>
        {'<span class="pt">'+pts+'</span>' if pts else ''}<span class="kind">훈련(정답 칠)</span>
        <span class="tm">{esc(rec.get("exam_id",""))} · #{idx}</span></div>
      <div class="psg">{_fallback_hl(rec["passage"])}</div>
      <div class="opts">{ch}</div>
      <div class="formula"><span class="k">공식</span>{esc(formula)}</div>
    </div>'''


def build(n=80):
    bank = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines() if l.strip()]
    picked = select(bank, n)
    content = {}
    if CONTENT.exists():
        for c in json.loads(CONTENT.read_text(encoding="utf-8")):
            content[c.get("key")] = c
    groups = {}
    for r in picked:
        groups.setdefault(r["band"], []).append(r)
    body, idx, full = [], 0, 0
    for b in BAND_ORDER:
        if b not in groups:
            continue
        body.append(f'<div class="sec">{BAND_TITLE.get(b,b)} <small>({b}번대 · {len(groups[b])}문항)</small></div>')
        for r in groups[b]:
            idx += 1
            key = f'{r["exam_id"]}|{r["num"]}'
            c = content.get(key)
            if c and c.get("hl"):
                body.append(render_spread(r, c, idx)); full += 1
            else:
                body.append(render_fallback(r, idx))
    doc = TEMPLATE.replace("{{BODY}}", "\n".join(body)).replace("{{N}}", str(idx)).replace("{{FULL}}", str(full))
    OUT.write_text(doc, encoding="utf-8")
    print(f"워크북 생성: {idx}문항(대표형 {full} · 폴백 {idx-full}) → {OUT}")


TEMPLATE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>유형별 훈련</title><style>
@page{ size:A4; margin:10mm 11mm; }
*{ box-sizing:border-box; }
body{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; line-height:1.5; margin:0; background:#fff; }
:root{ --ink:#1f7a5c; --ink-d:#12543d; --src:#e9f4ef; --src-line:#1f7a5c; --trap:#cd5049;
  --must:#ffe9a8; --must-line:#e0b94a; --skip:#9aa0a6; --muted:#6b7280; --line:#e6e8ea; }
.cover{ text-align:center; padding:10px 0 8px; border-bottom:3px solid var(--ink-d); margin-bottom:10px; break-after:avoid; }
.cover .t{ font-size:19px; font-weight:800; color:var(--ink-d); }
.cover .s{ font-size:9.5px; color:var(--muted); }
.sec{ font-size:13px; font-weight:800; color:#fff; background:var(--ink); border-radius:6px; padding:4px 12px; margin:12px 0 8px; break-before:page; break-after:avoid; }
.sec small{ font-weight:600; opacity:.9; font-size:9px; }
@media print{
  .spread{ display:block; }
  .qproblem{ break-before:left; break-inside:avoid; }
  .qsolution{ break-before:right; break-inside:avoid; }
  .card.solo{ break-inside:avoid; }
}
.spread{ margin-bottom:6px; }

/* 카드 공통 */
.card{ background:#fff; border-radius:8px; box-shadow:0 1px 6px rgba(0,0,0,.1); padding:12px 15px; margin-bottom:10px; }
.card.solo{ border:1px solid var(--line); }
.hd{ display:flex; align-items:center; gap:8px; border-bottom:2px solid var(--ink-d); padding-bottom:6px; margin-bottom:8px; }
.hd .no{ background:var(--ink-d); color:#fff; font-weight:800; font-size:12px; padding:2px 9px; border-radius:5px; }
.hd .ty{ font-weight:800; font-size:13px; color:var(--ink-d); }
.hd .kind{ font-size:9px; font-weight:700; color:var(--ink); border:1px solid var(--ink); border-radius:9px; padding:1px 8px; }
.hd .pt{ font-size:9px; font-weight:700; color:#fff; background:var(--trap); padding:1px 7px; border-radius:9px; }
.hd .tm{ margin-left:auto; font-size:9px; font-weight:700; color:var(--muted); }
.psg{ font-size:11px; line-height:1.85; border:1px solid var(--line); border-radius:6px; padding:9px 11px; margin-bottom:8px; }
mark.m{ background:var(--must); padding:0 2px; border-radius:2px; }
mark.g{ background:var(--src); padding:0 2px; border-radius:2px; }
.sk{ color:var(--skip); }
.bk{ display:inline-block; min-width:60px; border-bottom:2px solid #111; }
.tag{ font-size:7.5px; font-weight:800; color:#fff; background:var(--trap); border:1px solid var(--trap); border-radius:3px; padding:0 4px; vertical-align:1px; margin:0 1px; }
.tag.hot{ color:#fff; background:var(--trap); border-color:var(--trap); }
.rk{ background:#f4b8b2; color:#7a1f19; font-weight:700; padding:0 2px; border-radius:2px; box-shadow:inset 0 -2px 0 #d98b84; }

/* 문제 페이지(왼쪽) */
.pbanner{ background:linear-gradient(100deg,var(--ink-d),var(--ink)); color:#fff; border-radius:9px 9px 0 0; padding:11px 15px; display:flex; align-items:center; gap:9px; }
.pbanner .no{ background:#fff; color:var(--ink-d); font-weight:800; font-size:15px; padding:2px 11px; border-radius:6px; }
.pbanner .ty{ font-size:15px; font-weight:800; }
.pbanner .pt{ font-size:9px; font-weight:700; background:var(--trap); padding:1px 8px; border-radius:9px; }
.pbanner .step{ margin-left:auto; font-size:9px; font-weight:800; background:rgba(255,255,255,.18); padding:3px 10px; border-radius:11px; }
.pbody{ border:2px solid var(--ink-d); border-top:none; border-radius:0 0 9px 9px; padding:15px 17px; display:flex; gap:15px; min-height:600px; }
.pmain{ flex:2; display:flex; flex-direction:column; }
.pside{ flex:1; border-left:1.5px dashed var(--line); padding-left:13px; }
.how{ font-size:9px; color:#8a6a00; background:var(--must); border-radius:5px; padding:7px 10px; margin-bottom:10px; font-weight:700; }
.psg.work{ font-size:11.5px; line-height:2.15; border:none; padding:0; }
.pracopts{ font-size:9.6px; line-height:1.85; margin-top:9px; padding:8px 11px; background:#fff; border:1px dashed var(--must-line); border-radius:5px; }
.pracopts .o{ display:block; }
.pracopts .ttl{ font-size:8.7px; font-weight:800; color:#a86b00; margin-bottom:3px; }
.pguide{ margin-top:auto; background:#e9f4ef; border:1px solid var(--ink); border-radius:7px; padding:9px 12px; }
.pguide .h{ font-size:9.5px; font-weight:800; color:var(--ink-d); margin-bottom:5px; }
.pguide .g3{ display:flex; gap:8px; }
.pguide .g3 .s{ flex:1; font-size:8.6px; line-height:1.4; }
.pguide .g3 .k{ display:inline-block; width:15px; height:15px; line-height:15px; text-align:center; background:var(--ink); color:#fff; border-radius:50%; font-size:8.5px; font-weight:800; margin-right:3px; }
.ptip{ margin-top:11px; background:#fff7ed; border:1px solid #f0c48a; border-radius:6px; padding:8px 10px; font-size:8.8px; color:#8a5a1a; }
.ptip .h{ font-weight:800; color:#b3610d; margin-bottom:2px; }
.mini{ margin-bottom:11px; }
.mini .h{ font-size:9px; font-weight:800; color:var(--ink-d); margin-bottom:4px; border-bottom:1px solid var(--line); padding-bottom:2px; }
.chip{ display:inline-block; font-size:8.2px; font-weight:700; border-radius:9px; padding:1px 7px; margin:0 3px 3px 0; border:1px solid; }
.chip.y{ color:#a86b00; border-color:var(--must-line); background:#fffdf3; }
.chip.g{ color:var(--skip); border-color:#d5d9dd; background:#fafafa; }
.check{ list-style:none; margin:0; padding:0; font-size:8.8px; }
.check li{ margin-bottom:4px; padding-left:17px; position:relative; line-height:1.35; }
.check li::before{ content:"☐"; position:absolute; left:0; font-size:11px; color:var(--ink); }
.memo{ margin-top:10px; background:#eef4f1; border:1px solid var(--line); border-radius:6px; padding:8px 10px; }
.memo .h{ font-size:9px; font-weight:800; color:var(--ink-d); margin-bottom:5px; }
.memo .row{ font-size:9px; margin-bottom:6px; color:#4a5560; }
.memo .fill{ display:inline-block; min-width:38px; border-bottom:1.5px solid var(--ink); margin:0 4px; }
.memo .big{ display:block; height:24px; border-bottom:1px dotted #b9cfc6; }

/* 도출/판정 */
.derive{ margin-top:6px; background:#fffdf3; border:1px solid var(--must-line); border-radius:6px; padding:9px 12px; }
.derive .dh{ font-size:9.3px; font-weight:800; color:#8a6a00; margin-bottom:6px; }
.derive ol{ margin:0 0 6px; padding:0; list-style:none; }
.derive li{ font-size:9.5px; line-height:1.55; margin-bottom:4px; padding-left:42px; position:relative; }
.derive li .yb{ position:absolute; left:0; top:1px; font-size:7.5px; font-weight:800; color:#7a5c00; background:var(--must); border:1px solid var(--must-line); border-radius:7px; padding:1px 5px; }
.derive li u{ text-decoration:none; background:var(--must); padding:0 2px; border-radius:2px; font-weight:700; }
.derive li .an{ color:var(--muted); font-size:8.7px; }
.derive .concl{ font-size:9.6px; font-weight:700; color:#23272e; background:#eaf5f0; border-left:3px solid var(--ink); border-radius:0 5px 5px 0; padding:6px 10px; margin-top:2px; }
.derive .concl b{ color:var(--ink-d); }
.derive .gnote{ font-size:8.6px; color:var(--muted); margin-top:5px; padding-left:2px; }
.pline{ margin-top:6px; background:#eef4f1; border-left:3px solid var(--ink); border-radius:0 5px 5px 0; padding:5px 9px; font-size:9.3px; }
.pline .lb{ font-size:8px; font-weight:800; color:#fff; background:var(--ink); border-radius:8px; padding:1px 6px; margin-right:5px; }
.pline .sw{ background:#dbe7e0; border-radius:3px; padding:0 4px; font-weight:700; color:var(--ink-d); }
.pline .cp{ background:#ffe0dd; border-radius:3px; padding:0 4px; font-weight:700; color:#a5342d; }
.pline .arw{ color:var(--ink); font-weight:800; }
.opts{ margin-top:7px; border-top:1px dashed var(--line); padding-top:7px; }
.opt{ display:flex; gap:6px; align-items:baseline; font-size:9.5px; margin-bottom:3px; }
.opt .n{ flex:none; font-weight:800; width:14px; } .opt .tx{ flex:1; } .opt .jd{ flex:none; font-size:8.6px; font-weight:800; }
.opt.ok{ background:var(--src); border-radius:4px; padding:2px 5px; } .opt.ok .jd{ color:var(--src-line); } .opt.x .jd{ color:var(--trap); }
.reuse{ background:#ffe0dd; border-radius:2px; padding:0 2px; font-weight:700; color:#a5342d; }
.formula{ margin-top:8px; background:#e9f4ef; border:1.5px solid var(--ink); border-radius:6px; padding:6px 10px; font-weight:800; color:var(--ink-d); font-size:9.6px; }
.formula .k{ background:var(--ink); color:#fff; font-size:8px; padding:1px 6px; border-radius:8px; margin-right:6px; }

/* 직독직해 */
.card.trans{ border-left:5px solid var(--src-line); }
.dchl .kt{ display:block; font-weight:800; color:var(--src-line); font-size:8.8px; margin:2px 0 5px; }
.dchl .row{ margin-bottom:7px; padding-left:19px; position:relative; }
.dchl .bn{ position:absolute; left:0; top:1px; width:14px; height:14px; line-height:14px; text-align:center; background:var(--src-line); color:#fff; border-radius:50%; font-size:8px; font-weight:800; }
.dchl .en{ font-size:10.2px; line-height:1.95; color:#23272e; }
.dchl .ko{ font-size:9.6px; line-height:1.95; color:#23272e; margin-top:2px; }
.hl0,.hl1,.hl2,.hl3,.hl4{ color:#23272e; padding:1px 4px; border-radius:3px; box-decoration-break:clone; -webkit-box-decoration-break:clone; }
.hl0{ background:#c9e0ec; } .hl1{ background:#c7e0da; } .hl2{ background:#e8dfb2; } .hl3{ background:#e2dac8; } .hl4{ background:#d5ddb9; }
.dchl .opt-line{ margin-top:7px; padding-top:7px; border-top:1px dashed var(--line); font-size:9.3px; }
.dchl .opt-line .co{ color:var(--src-line); font-weight:800; } .dchl .opt-line .xo{ color:var(--trap); font-weight:700; }
</style></head><body>
<div class="cover"><div class="t">PART 1 · 유형별 훈련 <span style="font-size:12px;color:#6b7280">— 실제 기출 {{N}}문항 (대표형 {{FULL}})</span></div>
<div class="s">문항마다 STEP 1 직접 풀기(왼쪽) → STEP 2 훈련·정답 칠 + STEP 3 직독직해(오른쪽). 🟡=읽을 문장 · 🔴=칠한 근거(신호) · 초록=정답.</div></div>
{{BODY}}
</body></html>'''

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    build(n)
