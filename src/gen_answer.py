# -*- coding: utf-8 -*-
"""형광펜 답지(해설지) 렌더러 — 학습지(문제지)와 짝을 이루는 상세 해설 책자.
문항마다: 정답 배너 + 형광펜 지문(노랑/회색) + 노란문장 도출 + 직독직해 + 선지 해설(정답·오답 이유) + 재진술 + 어휘.
gen_workbook.solution_block() 을 그대로 재사용한다.

사용: python3 -m src.gen_answer [exam_id ...]   (인자 없으면 2025-수능)
"""
import json, os, sys, re
from src import gen_workbook as G

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "workbook_content.json")
BANK = os.path.join(ROOT, "corpus", "passage_bank.jsonl")
CONNECT = os.path.join(ROOT, "corpus", "workbook_connect.json")
OUT = os.path.join(ROOT, "samples", "형광펜답지.html")

CIRCLED = "①②③④⑤"


def css():
    m = re.search(r"<style>(.*?)</style>", G.TEMPLATE, re.S)
    return m.group(1) if m else ""


def ekey(e):
    y, m = e.split("-")
    return (int(y), {"06": 1, "09": 2, "수능": 3}.get(m, 9))


def build(exam_ids):
    content = {c["key"]: c for c in json.load(open(SRC, encoding="utf-8"))}
    bank = {}
    for line in open(BANK, encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            bank[f"{r['exam_id']}|{r['num']}"] = r
    if os.path.exists(CONNECT):
        for c in json.load(open(CONNECT, encoding="utf-8")):
            G._CONNECT[c.get("key")] = c
    exam_ids = sorted(exam_ids, key=ekey)

    body = ""
    seq = 0
    for eid in exam_ids:
        nums = sorted(int(k.split("|")[1]) for k in content if k.startswith(eid + "|"))
        body += f'<h2 class="exh">{G.esc(G.exam_src(eid))} · 형광펜 답지(해설)</h2>'
        for num in nums:
            k = f"{eid}|{num}"
            c = content[k]; r = bank.get(k, {})
            seq += 1
            ans = c.get("answer")
            circ = CIRCLED[ans - 1] if isinstance(ans, int) and 1 <= ans <= 5 else G.esc(ans)
            head = (f'<div class="ansbar"><span class="aseq">{seq}</span>'
                    f'<span class="asrc">{G.esc(G.exam_src(eid))} {num}번</span>'
                    f'<span class="aty">{G.esc(G.BAND_TITLE.get(r.get("band"), r.get("type","")))}</span>'
                    f'<span class="aans">✅ 정답 <b>{circ}</b></span></div>')
            sol = G.solution_block(r, c, seq)
            voc = G.vocab_block(c.get("vlist", []))
            body += f'<div class="asol">{head}{sol}{voc}</div>'

    extra = '''
/* 답지 전용 */
.exh{ font-size:15px; font-weight:800; color:var(--ink-d); border-bottom:2px solid var(--ink-d); padding-bottom:5px; margin:0 0 4px; break-before:page; }
.asol{ break-before:page; }
.asol .qsolution{ break-before:auto; }
.ansbar{ display:flex; align-items:center; gap:9px; background:linear-gradient(100deg,var(--ink-d),var(--ink)); color:#fff; border-radius:8px; padding:7px 12px; margin:8px 0 6px; }
.ansbar .aseq{ font-size:13px; font-weight:800; background:#fff; color:var(--ink-d); width:24px; height:24px; line-height:24px; text-align:center; border-radius:6px; }
.ansbar .asrc{ font-size:9px; font-weight:700; background:#ffe9a8; color:#12543d; padding:1px 8px; border-radius:9px; }
.ansbar .aty{ font-size:12px; font-weight:800; }
.ansbar .aans{ margin-left:auto; font-size:12px; font-weight:800; }
.ansbar .aans b{ font-size:15px; color:var(--must); }
'''
    doc = (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
           f'<title>형광펜 답지</title><style>{css()}{extra}</style></head><body>'
           f'{body}</body></html>')
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"형광펜 답지 생성: {len(exam_ids)}회차 · {seq}문항 → {OUT}")


if __name__ == "__main__":
    ids = sys.argv[1:] or ["2025-수능"]
    build(ids)
