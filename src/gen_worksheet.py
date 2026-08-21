# -*- coding: utf-8 -*-
"""학습지(worksheet) 렌더러 — 형광펜 3단계 템플릿 대신 '평가원 시험지형' 깔끔한 문제지 + 정답표.
같은 콘텐츠(JSON)를 재사용하며, 지문+발문+선지만 담고 해설/형광펜/사이드패널은 뺀다.

사용: python3 -m src.gen_worksheet [exam_id ...]   (인자 없으면 2025-수능)
"""
import json, os, sys, re
from src import gen_workbook as G

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "workbook_content.json")
BANK = os.path.join(ROOT, "corpus", "passage_bank.jsonl")
OUT = os.path.join(ROOT, "samples", "학습지.html")

esc = G.esc
CIRCLED = G.CIRCLED


def load_bank():
    recs = {}
    for line in open(BANK, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        recs[f"{r.get('exam_id','')}|{r.get('num','')}"] = r
    return recs


def insert_en_of(c):
    sd = c.get("seq_direct") or {}
    p = next((p for p in sd.get("pieces", []) if p.get("label") == "넣을 문장"), None)
    return p.get("en") if p else None


def choice_lines(c, r):
    """①~⑤ 선지 — 원본 choices 우선, 손상 시 검증된 opts로 대체."""
    ch = dict(r.get("choices") or {})
    opts = c.get("opts", [])
    if opts and len(ch) < len(opts):
        ch = {str(o["n"]): (o.get("tx") or "") for o in opts}
    out = ""
    for k in sorted(int(x) for x in ch):
        out += f'<span class="o">{CIRCLED[k-1]} {esc(ch[str(k)])}</span>'
    return out


def render_item(c, r, seq):
    num = int(c["key"].split("|")[1])
    band = r.get("band") or G.num_to_band(num) if hasattr(G, "num_to_band") else _band(num)
    typ = G.BAND_TITLE.get(band, r.get("type", ""))
    pts = r.get("points")
    prompt = G.PROMPT.get(band, "다음 글을 읽고 물음에 답하시오.")
    hl = c.get("hl") or []
    mug = c.get("mugwan") if num == 35 else None
    if mug:
        body = G.mugwan_html(mug, step2=False)
        opts = ('<div class="opts1"><span class="o"><b>①~⑤</b> 중 전체 흐름과 '
                '관계 <b>없는</b> 문장의 번호를 고르시오.</span></div>')
    else:
        body = G.clean_passage(hl, band, insert_en_of(c))
        summ = G.summary_box(c.get("summary")) if num == 40 else ""
        opts = f'{summ}<div class="opts1">{choice_lines(c, r)}</div>'
    return (f'<section class="q">'
            f'<div class="qh"><span class="qno">{seq}</span>'
            f'<span class="qsrc">[{G.exam_src(r.get("exam_id",""))} {num}번]</span>'
            f'<span class="qty">{esc(typ)}</span>'
            f'{f"<span class=chr-pt>{pts}점</span>" if pts else ""}</div>'
            f'<div class="qprompt">{esc(prompt)}</div>'
            f'<div class="psg">{body}</div>{opts}</section>')


def _band(num):
    if 31 <= num <= 34:
        return "31-34"
    if num in (36, 37):
        return "36-37"
    if num in (38, 39):
        return "38-39"
    return str(num)


def ekey(e):
    y, m = e.split("-")
    return (int(y), {"06": 1, "09": 2, "수능": 3}.get(m, 9))


def build(exam_ids):
    data = {c["key"]: c for c in json.load(open(SRC, encoding="utf-8"))}
    bank = load_bank()
    exam_ids = sorted(exam_ids, key=ekey)

    problems = ""
    answers = []
    seq = 0
    for eid in exam_ids:
        nums = sorted(int(k.split("|")[1]) for k in data if k.startswith(eid + "|"))
        problems += f'<h2 class="exh">{esc(G.exam_src(eid))} · 영어 유형별 학습지</h2>'
        for num in nums:
            k = f"{eid}|{num}"
            c = data[k]; r = bank.get(k, {})
            seq += 1
            problems += render_item(c, r, seq)
            answers.append((seq, eid, num, c.get("answer")))

    # 정답표
    rows = "".join(
        f'<tr><td>{s}</td><td>{esc(G.exam_src(e))}</td><td>{n}</td>'
        f'<td class="a">{CIRCLED[(a-1)] if isinstance(a,int) and 1<=a<=5 else esc(a)}</td></tr>'
        for s, e, n, a in answers
    )
    akey = (f'<section class="akey"><h2 class="exh">정답</h2>'
            f'<table><thead><tr><th>번호</th><th>회차</th><th>문항</th><th>정답</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></section>')

    doc = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>학습지</title><style>
@page{{ size:A4; margin:14mm 14mm 16mm; }}
*{{ box-sizing:border-box; }}
body{{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#1a1f26; font-size:10.5px; line-height:1.7; margin:0; }}
.exh{{ font-size:15px; font-weight:800; color:#12543d; border-bottom:2px solid #12543d; padding-bottom:5px; margin:6px 0 14px; break-before:auto; }}
.q{{ break-inside:avoid; margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #e6e8ea; }}
.qh{{ display:flex; align-items:center; gap:8px; margin-bottom:5px; }}
.qno{{ font-size:13px; font-weight:800; color:#fff; background:#1f7a5c; width:24px; height:24px; line-height:24px; text-align:center; border-radius:6px; }}
.qsrc{{ font-size:8.6px; font-weight:700; color:#12543d; background:#e9f4ef; padding:1px 7px; border-radius:8px; }}
.qty{{ font-size:9px; font-weight:800; color:#a86b00; }}
.chr-pt{{ font-size:8.6px; font-weight:800; color:#cd5049; }}
.qprompt{{ font-size:10.5px; font-weight:800; margin-bottom:7px; }}
.psg{{ font-size:10.5px; line-height:1.95; text-align:justify; margin-bottom:8px; }}
.psg .bk{{ display:inline-block; min-width:44px; border-bottom:1.3px solid #1a1f26; }}
.opts1{{ font-size:10px; line-height:1.9; }}
.opts1 .o{{ display:block; }}
/* 무관 번호매김 · 삽입박스 · 요약박스 (gen_workbook 클래스 재사용) */
.mgn{{ display:inline-block; font-size:9.5px; font-weight:800; color:#fff; background:#12543d; border-radius:50%; width:15px; height:15px; line-height:15px; text-align:center; margin:0 3px; }}
.insbox{{ border:1.5px solid #1a1f26; border-radius:6px; padding:6px 10px; margin-bottom:8px; }}
.insbox .inslab{{ font-size:8px; font-weight:800; color:#12543d; margin-right:6px; }}
.insbody{{ }}
.sumbox{{ margin:6px 0; padding:7px 10px; background:#f4faf7; border:1.5px solid #1f7a5c; border-radius:6px; }}
.sumbox .sh{{ font-size:8px; font-weight:800; color:#12543d; margin-bottom:3px; }}
.sumbox .sent{{ font-size:10.5px; line-height:1.8; }}
.sbk{{ display:inline-block; min-width:34px; text-align:center; font-weight:800; color:#a86b00; border-bottom:1.4px solid #e0b94a; background:#fff7e6; border-radius:3px; padding:0 6px; margin:0 2px; }}
.akey{{ break-before:page; }}
.akey table{{ border-collapse:collapse; width:100%; font-size:9.5px; }}
.akey th,.akey td{{ border:1px solid #d7dde1; padding:4px 6px; text-align:center; }}
.akey thead th{{ background:#12543d; color:#fff; }}
.akey td.a{{ font-weight:800; color:#12543d; }}
</style></head><body>
{problems}
{akey}
</body></html>'''
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"학습지 생성: {len(exam_ids)}회차 · {seq}문항 → {OUT}")


if __name__ == "__main__":
    ids = sys.argv[1:] or ["2025-수능"]
    build(ids)
