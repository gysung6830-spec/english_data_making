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


def _band(num):
    if 31 <= num <= 34:
        return "31-34"
    if num in (36, 37):
        return "36-37"
    if num in (38, 39):
        return "38-39"
    return str(num)


def build_custom(content_path, title, out_path=None, points=None):
    """corpus를 건드리지 않고, 새 문제 content 파일 하나로 형광펜 답지 생성.
    content 각 항목은 key 'ANY|<num>' 형태이며 answer/hl/opts 등 스키마를 갖춘다."""
    points = points or {}
    items = json.load(open(content_path, encoding="utf-8"))
    if isinstance(items, dict):
        items = list(items.values())
    if os.path.exists(CONNECT):
        for cc in json.load(open(CONNECT, encoding="utf-8")):
            G._CONNECT[cc.get("key")] = cc
    items.sort(key=lambda c: int(c["key"].split("|")[1]))
    out = out_path or os.path.join(ROOT, "samples", "형광펜답지_custom.html")
    body = f'<h2 class="exh">{G.esc(title)} · 형광펜 답지(해설)</h2>'
    seq = 0
    for c in items:
        num = int(c["key"].split("|")[1])
        band = _band(num)
        typ = G.BAND_TITLE.get(band, "")
        rec = {"num": num, "band": band, "exam_id": c["key"].split("|")[0],
               "answer": c.get("answer"), "type": typ, "points": points.get(num)}
        # 답지 헤더의 출처 라벨은 title을 쓰도록 exam_src 우회
        G._CONNECT.setdefault(c["key"], G._CONNECT.get(c["key"]))
        seq += 1
        ans = c.get("answer")
        circ = CIRCLED[ans-1] if isinstance(ans, int) and 1 <= ans <= 5 else G.esc(ans)
        note = "" if c.get("answer_src", "given") == "given" else ' <span style="font-size:8px;color:#ffe9a8">(정답 미공개 → 풀이로 확정)</span>'
        head = (f'<div class="ansbar"><span class="aseq">{seq}</span>'
                f'<span class="asrc">{G.esc(title)} {num}번</span>'
                f'<span class="aty">{G.esc(typ)}</span>'
                f'<span class="aans">✅ 정답 <b>{circ}</b>{note}</span></div>')
        # solution_block은 exam_src(rec.exam_id)를 STEP2 헤더에 쓰므로 title을 넣어줌
        rec["exam_id"] = title
        sol = G.solution_block(rec, c, seq)
        voc = G.vocab_block(c.get("vlist", []))
        body += f'<div class="asol">{head}{sol}{voc}</div>'
    extra = _EXTRA_CSS
    doc = (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
           f'<title>형광펜 답지</title><style>{css()}{extra}</style></head><body>'
           f'{body}</body></html>')
    open(out, "w", encoding="utf-8").write(doc)
    print(f"형광펜 답지(custom) 생성: {seq}문항 → {out}")
    return out


_EXTRA_CSS = '''
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


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--content":
        title = sys.argv[3] if len(sys.argv) > 3 else "새 학습지"
        build_custom(sys.argv[2], title)
    else:
        ids = sys.argv[1:] or ["2025-수능"]
        build(ids)
