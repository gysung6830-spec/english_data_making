# -*- coding: utf-8 -*-
"""책 맨 뒤 어휘 색인(index) 생성 — 전 지문 vlist를 알파벳순으로 모아 사전식으로 출력."""
import json, re, html, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "workbook_content.json")
PAGES = os.path.join(ROOT, "corpus", "item_pages.json")
OUT = os.path.join(ROOT, "samples", "어휘index.html")


def esc(s):
    return html.escape(str(s or ""))


def exam_label(eid):
    if not eid or "|" not in eid:
        return ""
    ex, num = eid.split("|", 1)
    y, m = (ex.split("-", 1) + [""])[:2]
    m = {"06": "6월", "09": "9월", "수능": "수능", "11": "수능"}.get(m, m)
    return f"{y}·{m} {num}"


def sort_key(w):
    # 알파벳 우선, 앞의 비알파벳(관사·기호) 무시하고 첫 실단어 기준
    s = re.sub(r"^(a|an|the|to|be)\s+", "", w.strip().lower())
    s = re.sub(r"[^a-z0-9가-힣 ]", "", s)
    return (s or w.strip().lower())


def first_letter(w):
    k = sort_key(w)
    c = k[:1].upper()
    return c if "A" <= c <= "Z" else "#"


def build():
    data = json.load(open(SRC, encoding="utf-8"))
    pages = {}
    if os.path.exists(PAGES):
        pages = json.load(open(PAGES, encoding="utf-8"))
    # dedupe by lowercased word; merge distinct meanings + collect sources
    agg = {}
    for c in data:
        eid = c.get("key", "")
        for v in c.get("vlist", []):
            if not isinstance(v, dict):
                continue
            w = (v.get("w") or "").strip()
            m = (v.get("m") or "").strip()
            if not w:
                continue
            key = w.lower()
            e = agg.setdefault(key, {"w": w, "means": [], "src": {}})
            if m and m not in e["means"]:
                e["means"].append(m)
            lbl = exam_label(eid)
            pg = pages.get(eid)
            if lbl and lbl not in e["src"]:
                e["src"][lbl] = pg  # 회차 라벨 → 페이지
    entries = sorted(agg.values(), key=lambda e: (sort_key(e["w"]), e["w"].lower()))
    total = len(entries)

    # group by first letter
    groups = {}
    for e in entries:
        groups.setdefault(first_letter(e["w"]), []).append(e)
    letters = [L for L in ["#"] + [chr(x) for x in range(ord("A"), ord("Z") + 1)] if L in groups]
    # '#'(비알파벳)은 맨 뒤로
    letters = [L for L in letters if L != "#"] + (["#"] if "#" in groups else [])

    nav = "".join(f'<span class="nl">{esc(L)}</span>' for L in letters)

    sections = ""
    for L in letters:
        rows = ""
        for e in groups[L]:
            mean = " / ".join(e["means"])
            # 회차·페이지 — 페이지 오름차순 정렬
            src_items = sorted(e["src"].items(), key=lambda kv: (kv[1] is None, kv[1] or 0))
            pgtxt = srctxt = ""
            if src_items:
                # 페이지 배지(중복 제거, 오름차순)
                pnums = sorted({p for _, p in src_items if p})
                if pnums:
                    pgtxt = "".join(f'<span class="pg">p.{p}</span>' for p in pnums[:4])
                    if len(pnums) > 4:
                        pgtxt += f'<span class="pgmore">외 {len(pnums)-4}</span>'
                shown = [lbl for lbl, _ in src_items[:3]]
                more = f' 외 {len(src_items)-3}' if len(src_items) > 3 else ""
                srctxt = f'<span class="src">{esc("·".join(shown))}{esc(more)}</span>'
            rows += (f'<div class="ent"><span class="w">{esc(e["w"])}</span>'
                     f'<span class="pgs">{pgtxt}</span>'
                     f'<span class="m">{esc(mean)}</span>{srctxt}</div>')
        sections += (f'<section class="lg"><div class="lh"><span class="lc">{esc(L)}</span>'
                     f'<span class="cnt">{len(groups[L])}개</span></div>'
                     f'<div class="cols">{rows}</div></section>')

    doc = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>어휘 색인</title><style>
@page{{ size:A4; margin:12mm 12mm 14mm; }}
*{{ box-sizing:border-box; }}
body{{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; line-height:1.5; margin:0; background:#fff; }}
:root{{ --ink:#1f7a5c; --ink-d:#12543d; --line:#e6e8ea; --muted:#6b7280; }}
.idx-cover{{ background:linear-gradient(160deg,#12543d 0%,#1f7a5c 78%,#2a916d 100%); color:#fff; border-radius:10px; padding:26px 30px; margin-bottom:16px; break-after:avoid; }}
.idx-cover .kick{{ font-size:11px; font-weight:800; letter-spacing:3px; opacity:.85; }}
.idx-cover .t{{ font-size:30px; font-weight:800; margin:6px 0 4px; }}
.idx-cover .sub{{ font-size:11px; opacity:.92; }}
.idx-cover .meta{{ margin-top:10px; font-size:10px; opacity:.9; }}
.guide{{ background:#f3f8f5; border:1px solid #cfe5da; border-radius:8px; padding:8px 12px; font-size:9px; color:#33514a; margin-bottom:12px; }}
.guide b{{ color:var(--ink-d); }}
.nav{{ display:flex; flex-wrap:wrap; gap:3px; margin-bottom:14px; }}
.nav .nl{{ font-size:9.5px; font-weight:800; color:var(--ink-d); background:#e9f4ef; border:1px solid #cfe5da; border-radius:5px; padding:1px 7px; }}
.lg{{ break-inside:avoid-column; margin-bottom:9px; }}
.lh{{ display:flex; align-items:baseline; gap:8px; border-bottom:2px solid var(--ink); margin:2px 0 5px; padding-bottom:2px; break-after:avoid; }}
.lh .lc{{ font-size:16px; font-weight:800; color:var(--ink-d); }}
.lh .cnt{{ font-size:8.5px; color:var(--muted); }}
.cols{{ column-count:2; column-gap:16px; }}
.ent{{ break-inside:avoid; padding:2px 0 3px; border-bottom:1px dotted #e9ecee; margin-bottom:1px; }}
.ent .w{{ font-weight:800; color:#1a1f26; }}
.ent .pgs{{ float:right; }}
.ent .pgs .pg{{ display:inline-block; font-size:7.8px; font-weight:800; color:var(--ink-d); background:#e9f4ef; border:1px solid #cfe5da; border-radius:4px; padding:0 4px; margin-left:3px; }}
.ent .pgs .pgmore{{ font-size:7.2px; color:#93a0aa; margin-left:3px; }}
.ent .m{{ display:block; font-size:9.2px; color:#33414d; margin-top:1px; clear:both; }}
.ent .src{{ display:block; font-size:7.4px; color:#93a0aa; margin-top:1px; }}
h1,h2{{ margin:0; }}
</style></head><body>
<div class="idx-cover">
  <div class="kick">APPENDIX · 부록</div>
  <div class="t">어휘 색인</div>
  <div class="sub">전 지문 핵심 단어·숙어 알파벳 사전</div>
  <div class="meta">총 <b>{total}</b>개 표제어 · 알파벳순 · 출처 회차 병기</div>
</div>
<div class="guide">📖 <b>보는 법</b> — 표제어(영어) 오른쪽 <b><span style="color:#12543d">p.숫자</span> = 교재 페이지</b>(그 단어가 나온 문항 위치)로 바로 찾아가세요. 아래엔 뜻과 <b>출처 회차·문항</b>(예: 2026·6월 21). 같은 단어가 여러 번 나오면 뜻·페이지를 모았습니다.</div>
<div class="nav">{nav}</div>
{sections}
</body></html>'''
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"어휘 색인 생성: 표제어 {total}개 → {OUT}")


if __name__ == "__main__":
    build()
