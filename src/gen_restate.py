#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""재진술 답 부록 — 전 문항의 재진술 지도를 책 맨 끝(색인 앞)에 모아 배치.
각 항목에 유형 순번(요지 1)·교재 페이지·기출 출처를 단다."""
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "corpus" / "workbook_content.json"
META = ROOT / "corpus" / "item_meta.json"
PAGES = ROOT / "corpus" / "item_pages.json"
OUT = ROOT / "samples" / "재진술답.html"
BAND_ORDER = ["21", "22", "23", "24", "30", "31-34", "35", "36-37", "38-39", "40", "41"]
NUM2BAND = {"21": "21", "22": "22", "23": "23", "24": "24", "30": "30",
            "31": "31-34", "32": "31-34", "33": "31-34", "34": "31-34",
            "35": "35", "36": "36-37", "37": "36-37", "38": "38-39", "39": "38-39",
            "40": "40", "41": "41"}


def esc(s):
    return html.escape(str(s), quote=False)


def _valid(rt):
    if not rt or rt.get("has_restate") is False:
        return False
    if rt.get("kind") == "compare":
        subs = rt.get("subjects") or []
        return len(subs) >= 2 and any(len(s.get("trail") or []) >= 2 for s in subs[:2])
    return len(rt.get("chain") or []) >= 2


LBL = ["A", "A′", "A″", "A‴", "A⁗"]


def _chain_rows(chain):
    rows = ""
    for i, c in enumerate(chain or []):
        how = f'<span class="rh">{esc(c.get("how"))}</span>' if c.get("how") and c.get("how") != "—" else ""
        rows += (f'<div class="rrow"><span class="rl">{LBL[i] if i < len(LBL) else "A"}</span>{how}'
                 f'<span class="re">{esc(c.get("en",""))}</span>'
                 f'<span class="rk">— {esc(c.get("ko",""))}</span></div>')
    return rows


def build():
    content = {c["key"]: c for c in json.loads(CONTENT.read_text(encoding="utf-8"))}
    meta = json.loads(META.read_text(encoding="utf-8"))
    pages = json.loads(PAGES.read_text(encoding="utf-8")) if PAGES.exists() else {}
    # 유형→항목 목록
    groups = {}
    for key, m in meta.items():
        c = content.get(key)
        if not c:
            continue
        rt = c.get("restate")
        if not _valid(rt):
            continue
        b = m.get("band") or NUM2BAND.get(m.get("num"), "")
        groups.setdefault(b, []).append((m, c, rt, key))
    for b in groups:
        groups[b].sort(key=lambda x: x[0].get("tno", 0))

    sections = ""
    total = 0
    for b in BAND_ORDER:
        if b not in groups:
            continue
        typ = groups[b][0][0].get("type", b)
        items = ""
        for m, c, rt, key in groups[b]:
            total += 1
            pg = pages.get(key)
            tno = m.get("tno")
            thesis = esc(rt.get("thesis", ""))
            echo = esc(rt.get("echo", ""))
            if rt.get("kind") == "compare":
                body = ""
                for li, s in zip(["A", "B"], (rt.get("subjects") or [])[:2]):
                    body += (f'<div class="rsub"><span class="rsn">{li} · {esc(s.get("name",""))}</span>'
                             f'{_chain_rows(s.get("trail"))}</div>')
            else:
                body = _chain_rows(rt.get("chain"))
            pgb = f'<span class="ripg">p.{pg}</span>' if pg else ""
            items += (f'<div class="ritem"><div class="rhead">'
                      f'<span class="rlbl">{esc(typ)} {tno}</span>{pgb}'
                      f'<span class="rex">{esc(m.get("exam",""))} {esc(m.get("num",""))}번</span></div>'
                      f'<div class="rth">🔁 {thesis}</div>{body}'
                      + (f'<div class="recho"><b>정답</b> {echo}</div>' if echo else "")
                      + '</div>')
        sections += f'<div class="rsec"><h2>{esc(typ)}</h2><div class="rgrid">{items}</div></div>'

    doc = TEMPLATE.replace("{{SECTIONS}}", sections).replace("{{TOTAL}}", str(total))
    OUT.write_text(doc, encoding="utf-8")
    print(f"재진술 답 부록 생성: {total}문항 → {OUT}")


TEMPLATE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>재진술 답</title><style>
@page{ size:A4; margin:12mm 13mm; }
*{ box-sizing:border-box; }
body{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; line-height:1.5; }
:root{ --ink:#1f7a5c; --ink-d:#12543d; --must:#ffe9a8; --must-line:#e0b94a; --muted:#6b7280; --line:#e6e8ea; }
.head{ background:linear-gradient(100deg,#8a5a1a,#c9902f); color:#fff; border-radius:10px; padding:16px 20px; margin-bottom:14px; }
.head .k{ font-size:11px; font-weight:800; letter-spacing:2px; opacity:.9; }
.head h1{ font-size:24px; font-weight:800; margin:4px 0 3px; }
.head .s{ font-size:11px; opacity:.95; }
.rsec{ margin-bottom:12px; }
.rsec h2{ break-after:avoid; }
.rsec h2{ font-size:14px; font-weight:800; color:var(--ink-d); border-left:5px solid var(--ink); padding-left:9px; margin:12px 0 8px; }
.rgrid{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.ritem{ border:1px solid var(--line); border-left:3px solid var(--must-line); border-radius:8px; padding:8px 11px; break-inside:avoid; background:#fffdf7; }
.rhead{ display:flex; align-items:center; gap:7px; margin-bottom:5px; }
.rhead .rlbl{ font-size:10.5px; font-weight:800; color:#fff; background:var(--ink-d); border-radius:5px; padding:1px 9px; }
.rhead .ripg{ font-size:9px; font-weight:800; color:#12543d; background:var(--must); border-radius:9px; padding:1px 8px; }
.rhead .rex{ font-size:8.6px; color:var(--muted); margin-left:auto; }
.rth{ font-size:10.3px; font-weight:800; color:var(--ink-d); background:#f2f8f5; border-radius:5px; padding:4px 8px; margin-bottom:5px; }
.rrow{ font-size:9.4px; line-height:1.6; padding:2px 0; border-bottom:1px dashed #eee6cf; }
.rrow:last-child{ border-bottom:none; }
.rrow .rl{ display:inline-block; font-weight:800; color:#1f4d7a; background:#e2eefa; border-radius:8px; padding:0 6px; margin-right:5px; font-size:8.4px; }
.rrow .rh{ display:inline-block; font-size:8px; font-weight:800; color:#8a3f3a; background:#fdeceb; border-radius:8px; padding:0 6px; margin-right:5px; }
.rrow .re{ font-style:italic; color:#3a4550; } .rrow .rk{ color:#33414d; margin-left:4px; }
.rsub{ margin:3px 0; } .rsub .rsn{ font-size:8.6px; font-weight:800; color:var(--ink-d); }
.recho{ margin-top:5px; font-size:9.4px; font-weight:700; color:#12543d; background:#eaf5f0; border-left:3px solid var(--ink); border-radius:0 5px 5px 0; padding:4px 8px; } .recho b{ color:var(--ink-d); }
</style></head><body>
<div class="head"><div class="k">APPENDIX · 재진술</div><h1>🔁 재진술 답</h1>
<div class="s">전 문항의 <b>재진술 지도</b>를 유형·순번별로 모았습니다. 같은 소재 A가 A→A′→A″로 표현만 바뀌며 되풀이 → 마지막이 정답. &nbsp;<b>{{TOTAL}}문항</b> · 각 항목의 <b>p.번호</b>로 본문을 찾아가세요.</div></div>
{{SECTIONS}}
</body></html>'''

if __name__ == "__main__":
    build()
