# -*- coding: utf-8 -*-
"""형광펜 독해 — 빈출 단어장(별책) 생성.
색인(1,898어)에서 큐레이션한 수능 핵심 어휘를 빈출 순 Day별로 묶어 별도 교재 PDF로 출력.
입력: corpus/vocab_core.json  (list of {w,m,pos,f})  · f=교재 내 등장 지문 수(빈출도)
출력: samples/빈출단어장.html
"""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "vocab_core.json")
OUT = os.path.join(ROOT, "samples", "빈출단어장.html")

PER_DAY = 40          # 하루 분량
MAX_WORDS = 600       # 상한(Day 15까지)

POS_KO = {"n": "명", "v": "동", "adj": "형", "adv": "부", "phr": "숙", "": ""}
POS_CLS = {"n": "n", "v": "v", "adj": "a", "adv": "d", "phr": "p", "": "x"}


def esc(s):
    return html.escape(str(s or ""), quote=False)


def load():
    rows = json.load(open(SRC, encoding="utf-8"))
    # 빈출 순: f desc → 알파벳
    rows.sort(key=lambda r: (-int(r.get("f", 1)), r["w"].lower()))
    return rows[:MAX_WORDS]


def word_row(idx, r):
    w = r["w"]; m = r.get("m", ""); pos = (r.get("pos") or "").strip()
    f = int(r.get("f", 1))
    star = '<span class="star">★</span>' if f >= 2 else ''
    fnum = f'<span class="fn">{f}</span>' if f >= 2 else ''
    pk = POS_KO.get(pos, ""); pc = POS_CLS.get(pos, "x")
    pos_html = f'<span class="pos {pc}">{esc(pk)}</span>' if pk else ''
    return (f'<div class="wr">'
            f'<span class="no">{idx}</span>'
            f'<span class="ck"></span>'
            f'<span class="wb"><span class="en">{esc(w)}{star}{pos_html}</span>'
            f'<span class="ko">{esc(m)}{fnum}</span></span>'
            f'</div>')


def day_page(dno, words, start_idx, total_days):
    n = len(words)
    n_star = sum(1 for r in words if int(r.get("f", 1)) >= 2)
    half = (n + 1) // 2
    col1 = "".join(word_row(start_idx + i, r) for i, r in enumerate(words[:half]))
    col2 = "".join(word_row(start_idx + half + i, r) for i, r in enumerate(words[half:]))
    rng = f"{start_idx}–{start_idx + n - 1}"
    return f'''<section class="pg">
  <div class="dtop">
    <div class="dl"><span class="dno">DAY {dno:02d}</span><span class="drange">단어 {rng}</span></div>
    <div class="dmeta"><span class="dstar">★ 빈출 {n_star}</span><span class="dtot">/ {total_days}일</span></div>
  </div>
  <div class="dhint">□에 <b>회독 체크</b> — 1·2·3회독. <span class="star">★</span>=이 교재 <b>2회 이상</b> 나온 빈출어(옆 숫자=등장 지문 수).</div>
  <div class="cols"><div class="col">{col1}</div><div class="col">{col2}</div></div>
  <div class="dfoot">© 2026. 김은아영어연구소 · 형광펜 독해 — 빈출 단어장 · DAY {dno:02d}</div>
</section>'''


def build():
    rows = load()
    days = [rows[i:i + PER_DAY] for i in range(0, len(rows), PER_DAY)]
    total_days = len(days)
    n_total = len(rows)
    n_star = sum(1 for r in rows if int(r.get("f", 1)) >= 2)

    # 표지
    cover = f'''<section class="cover">
  <div class="ckick">형광펜 독해 · 별책부록</div>
  <div class="ctitle">빈출<br>단어장</div>
  <div class="csub">실제 평가원 기출 <b>224문항</b>에서 뽑은 <b>수능 핵심 {n_total}어</b> —<br>빈출 순 <b>{total_days}일</b> 완성. 매일 40단어, 3회독 체크.</div>
  <div class="crule"></div>
  <div class="ctags">★ 빈출어 <b>{n_star}개</b> 별도 표시 · 뜻·품사 병기 · 본책 색인과 연동</div>
  <div class="cfoot">© 김은아영어연구소 · 형광펜 독해 시리즈</div>
</section>'''

    # 목차(Day 안내) + 활용법
    toc_rows = ""
    for d, ws in enumerate(days, 1):
        s = (d - 1) * PER_DAY + 1
        e = s + len(ws) - 1
        ns = sum(1 for r in ws if int(r.get("f", 1)) >= 2)
        toc_rows += (f'<div class="tr"><span class="td">DAY {d:02d}</span>'
                     f'<span class="tw">단어 {s}–{e}</span><span class="tdot"></span>'
                     f'<span class="ts">★{ns}</span></div>')
    intro = f'''<section class="pg">
  <div class="itop"><span class="ikick">별책부록 · 사용법</span><h1>빈출 단어장 200% 활용법</h1></div>
  <div class="ilead">본책 <b>어휘 색인</b>에서 <b>수능 핵심어 {n_total}개</b>만 골라 <b>빈출 순</b>으로 배열했습니다.
    앞 Day일수록 <b>더 자주·더 중요</b>하게 나온 단어입니다.</div>
  <div class="how">
    <div class="hc"><span class="hn">1</span><b>빈출 순 학습</b><span>DAY 01부터 — 앞쪽이 최빈출. 하루 40단어.</span></div>
    <div class="hc"><span class="hn">2</span><b>3회독 체크</b><span>□□□에 회독마다 체크. 세 번 반복이 기본.</span></div>
    <div class="hc"><span class="hn">3</span><b>★ 빈출어 우선</b><span>★는 교재에 2회 이상 나온 단어 — 반드시 암기.</span></div>
  </div>
  <div class="legend"><b>표기</b> — <span class="pos n">명</span>명사 <span class="pos v">동</span>동사
    <span class="pos a">형</span>형용사 <span class="pos d">부</span>부사 <span class="pos p">숙</span>숙어·구 ·
    <span class="star">★</span>빈출(옆 숫자=등장 지문 수)</div>
  <div class="tochead">DAY 구성 — 총 {total_days}일 · {n_total}단어</div>
  <div class="toc">{toc_rows}</div>
  <div class="ifoot">© 2026. 김은아영어연구소 · 형광펜 독해 — 빈출 단어장</div>
</section>'''

    body = cover + intro
    idx = 1
    for d, ws in enumerate(days, 1):
        body += day_page(d, ws, idx, total_days)
        idx += len(ws)

    htmlout = HEAD + body + "\n</body></html>"
    open(OUT, "w", encoding="utf-8").write(htmlout)
    print(f"빈출 단어장 생성: {n_total}어 · {total_days}일(DAY) · ★빈출 {n_star} → {OUT}")


HEAD = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>형광펜 독해 — 빈출 단어장</title>
<style>
@page{ size:A4; margin:0; }
*{ box-sizing:border-box; }
body{ font-family:"NanumSquareRound","Liberation Sans","DejaVu Sans",sans-serif; color:#23272e; margin:0; }
:root{ --deep:#1f7a5c; --deep-d:#12543d; --must:#ffe9a8; --muted:#6b7280; --line:#e6e8ea; }
.pg{ break-before:page; min-height:271mm; padding:15mm 15mm 12mm; }
.pg:first-child{ break-before:auto; }

/* 표지 */
.cover{ height:297mm; padding:36mm 26mm; display:flex; flex-direction:column;
  background:linear-gradient(160deg,#12543d 0%, #1f7a5c 72%, #2a916d 100%); color:#fff; break-after:page; }
.cover .ckick{ font-size:13px; font-weight:800; letter-spacing:2px; opacity:.9; }
.cover .ctitle{ font-size:60px; font-weight:800; line-height:1.08; margin:14px 0 8px; }
.cover .csub{ font-size:14.5px; line-height:1.75; opacity:.96; max-width:150mm; }
.cover .csub b{ color:var(--must); }
.cover .crule{ width:66mm; height:4px; background:var(--must); border-radius:3px; margin:22px 0; }
.cover .ctags{ margin-top:auto; font-size:12px; opacity:.92; } .cover .ctags b{ color:var(--must); }
.cover .cfoot{ margin-top:16px; font-size:11px; opacity:.72; }

/* 활용법/목차 */
.itop{ border-bottom:3px solid var(--deep-d); padding-bottom:8px; margin-bottom:11px; }
.itop .ikick{ font-size:11px; font-weight:800; color:#fff; background:var(--deep); border-radius:5px; padding:2px 9px; }
.itop h1{ font-size:23px; font-weight:800; color:var(--deep-d); margin:8px 0 0; }
.ilead{ font-size:11.5px; color:#4a5560; line-height:1.6; margin-bottom:12px; } .ilead b{ color:var(--deep-d); }
.how{ display:flex; gap:10px; margin-bottom:13px; }
.how .hc{ flex:1; border:1.5px solid var(--line); border-top:4px solid var(--deep); border-radius:10px; padding:9px 12px; font-size:11px; color:#48525c; line-height:1.5; }
.how .hc .hn{ display:inline-block; width:20px; height:20px; line-height:20px; text-align:center; font-weight:800; color:#fff; background:var(--deep-d); border-radius:50%; font-size:11px; margin-bottom:5px; }
.how .hc b{ display:block; color:var(--deep-d); font-size:12.5px; margin-bottom:2px; }
.how .hc span{ display:block; }
.legend{ font-size:10px; color:#5c646d; background:#f2f8f5; border:1px solid #d9ebe2; border-radius:7px; padding:8px 12px; margin-bottom:14px; }
.tochead{ font-size:12px; font-weight:800; color:var(--deep-d); border-left:5px solid var(--deep); padding-left:8px; margin-bottom:8px; }
.toc{ display:grid; grid-template-columns:1fr 1fr; gap:2px 22px; }
.tr{ display:flex; align-items:baseline; font-size:11px; padding:3px 0; }
.tr .td{ flex:none; width:56px; font-weight:800; color:var(--deep); }
.tr .tw{ flex:none; color:#39424b; font-weight:600; }
.tr .tdot{ flex:1; border-bottom:1px dotted #c9d5cf; margin:0 8px; transform:translateY(-3px); }
.tr .ts{ flex:none; font-size:9.5px; font-weight:800; color:#c98a1a; }
.ifoot,.dfoot{ margin-top:14px; padding-top:8px; border-top:1px solid var(--line); font-size:8.5px; color:#9aa2ab; text-align:center; }

/* Day 헤더 */
.dtop{ display:flex; align-items:center; justify-content:space-between; border-bottom:3px solid var(--deep-d); padding-bottom:7px; margin-bottom:5px; }
.dtop .dno{ font-size:22px; font-weight:800; color:var(--deep-d); letter-spacing:.5px; }
.dtop .drange{ font-size:11px; font-weight:700; color:var(--muted); margin-left:11px; }
.dtop .dmeta{ font-size:10px; color:var(--muted); font-weight:700; }
.dtop .dstar{ color:#c98a1a; } .dtop .dtot{ margin-left:7px; }
.dhint{ font-size:9px; color:#7c848d; margin-bottom:9px; line-height:1.5; } .dhint b{ color:#48525c; }
.dhint .star{ color:#e0a52a; }

/* 단어 2단 */
.cols{ display:grid; grid-template-columns:1fr 1fr; gap:0 20px; }
.col{ border-top:2px solid #e6ede9; }
.wr{ display:flex; align-items:flex-start; gap:5px;
  padding:4.4px 0; border-bottom:1px solid #eef1ef; }
.wr .no{ flex:none; width:17px; color:#b5bcc4; font-size:8.5px; font-weight:700; text-align:right; padding-top:1px; }
.wr .ck{ flex:none; width:32px; padding-top:1px; }
.wr .ck::before{ content:"□□□"; letter-spacing:1px; color:#c7d0c9; font-size:9px; }
.wr .wb{ flex:1; min-width:0; }
.wr .en{ display:block; font-weight:800; color:#1c2b25; font-size:11px; line-height:1.3; }
.wr .en .star{ color:#e0a52a; font-size:9px; margin-left:3px; }
.wr .en .pos{ font-size:8px; font-weight:800; border-radius:4px; padding:0 4px; margin-left:4px; vertical-align:1px; }
.wr .ko{ display:block; color:#4a5560; font-size:9.6px; margin-top:1px; line-height:1.35; }
.wr .ko .fn{ font-size:8px; font-weight:800; color:#c98a1a; background:#fff3dd; border-radius:7px; padding:0 5px; margin-left:5px; }
/* 품사색 */
.pos.n{ color:#215788; background:#dbe9f7; } .pos.v{ color:#8a2f27; background:#fbe2e0; }
.pos.a{ color:#12543d; background:#d9efe6; } .pos.d{ color:#6d3fd4; background:#ece4fd; }
.pos.p{ color:#8a5a1a; background:#fbe7d3; } .pos.x{ display:none; }
</style></head><body>
'''


if __name__ == "__main__":
    build()
