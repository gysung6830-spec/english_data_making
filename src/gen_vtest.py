# -*- coding: utf-8 -*-
"""부록: 어휘 미니 테스트 — 「어휘 색인」과 동일한 알파벳 순서·번호로 50개씩 끊은 테스트지.
TEST 01 = 색인 1~50, TEST 02 = 색인 51~100 … (번호가 색인 번호와 일치)."""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "workbook_content.json")
OUT = os.path.join(ROOT, "samples", "어휘테스트.html")

CHUNK = 50


def esc(s):
    return html.escape(str(s or ""))


def sort_key(w):
    s = re.sub(r"^(a|an|the|to|be)\s+", "", w.strip().lower())
    s = re.sub(r"[^a-z0-9가-힣 ]", "", s)
    return s or w.strip().lower()


def first_letter(w):
    c = sort_key(w)[:1].upper()
    return c if "A" <= c <= "Z" else "#"


def build():
    data = json.load(open(SRC, encoding="utf-8"))
    # 전 지문 어휘 → 소문자 기준 중복 제거(색인과 동일 표제어 집합)
    uniq = {}
    for c in data:
        for v in c.get("vlist", []):
            if isinstance(v, dict) and v.get("w"):
                w = v["w"].strip()
                uniq.setdefault(w.lower(), w)
    # 색인과 '완전히 같은' 순서·번호: (sort_key, lower)로 정렬 후, 글자 그룹 A~Z 다음 '#'(비알파벳)
    entries = sorted(uniq.values(), key=lambda w: (sort_key(w), w.lower()))
    groups = {}
    for w in entries:
        groups.setdefault(first_letter(w), []).append(w)
    letters = [L for L in [chr(x) for x in range(ord("A"), ord("Z") + 1)] if L in groups]
    if "#" in groups:
        letters += ["#"]
    words = [w for L in letters for w in groups[L]]  # 색인 표시 순서 = 색인 번호 순
    total = len(words)
    ntests = (total + CHUNK - 1) // CHUNK

    sections = ""
    for t in range(ntests):
        lo = t * CHUNK
        chunk = words[lo:lo + CHUNK]
        items = "".join(
            f'<div class="ti"><span class="tn">{lo + i + 1}</span>'
            f'<span class="tw">{esc(w)}</span><span class="tb"></span></div>'
            for i, w in enumerate(chunk)
        )
        sections += (
            f'<section class="tst"><div class="tsth">'
            f'<span class="tstno">TEST {t + 1:02d}</span>'
            f'<span class="tstrg">No. {lo + 1}–{lo + len(chunk)}</span>'
            f'<span class="tsts">맞은 개수 <b>____</b> / {len(chunk)}</span></div>'
            f'<div class="tgrid">{items}</div></section>'
        )

    doc = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>어휘 미니 테스트</title><style>
@page{{ size:A4; margin:13mm 12mm 14mm; }}
*{{ box-sizing:border-box; }}
body{{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; margin:0; background:#fff; }}
:root{{ --ink:#1f7a5c; --ink-d:#12543d; --line:#e6e8ea; --muted:#6b7280; }}
.vt-cover{{ background:linear-gradient(160deg,#12543d 0%,#1f7a5c 78%,#2a916d 100%); color:#fff; border-radius:10px; padding:26px 30px; margin-bottom:16px; break-after:avoid; }}
.vt-cover .kick{{ font-size:11px; font-weight:800; letter-spacing:3px; opacity:.85; }}
.vt-cover .t{{ font-size:30px; font-weight:800; margin:6px 0 4px; }}
.vt-cover .sub{{ font-size:11px; opacity:.92; }}
.vt-cover .meta{{ margin-top:10px; font-size:10px; opacity:.9; }}
.guide{{ background:#f3f8f5; border:1px solid #cfe5da; border-radius:8px; padding:8px 12px; font-size:9px; color:#33514a; margin-bottom:14px; }}
.guide b{{ color:var(--ink-d); }}
.tst{{ margin-bottom:0; break-before:page; break-inside:avoid; }}
.tsth{{ display:flex; align-items:baseline; gap:9px; border-bottom:2px solid var(--ink); margin:2px 0 6px; padding-bottom:3px; break-after:avoid; }}
.tsth .tstno{{ font-size:16px; font-weight:800; color:var(--ink-d); letter-spacing:.5px; }}
.tsth .tstrg{{ font-size:9.5px; color:var(--muted); }}
.tsth .tsts{{ margin-left:auto; font-size:10px; color:#4a5560; }}
.tsth .tsts b{{ color:var(--ink-d); }}
.tgrid{{ column-count:2; column-gap:18px; }}
.ti{{ break-inside:avoid; display:flex; align-items:baseline; gap:7px; padding:10px 0 3px; border-bottom:1px dotted #e9ecee; margin-bottom:1px; }}
.ti .tn{{ flex:none; min-width:22px; font-size:10px; font-weight:800; color:#9aa7b0; text-align:right; }}
.ti .tw{{ font-size:12.5px; font-weight:700; color:#1a1f26; flex:none; max-width:52%; }}
.ti .tb{{ flex:1; border-bottom:1px solid #c7d3cd; height:15px; }}
</style></head><body>
<div class="vt-cover">
  <div class="kick">APPENDIX · 부록</div>
  <div class="t">어휘 미니 테스트</div>
  <div class="sub">「어휘 색인」과 같은 순서·번호 · 50개씩</div>
  <div class="meta">총 <b>{total}</b>단어 · <b>{ntests}</b>회분(각 {CHUNK}개) · <b>TEST 01 = 색인 1~50</b>, TEST 02 = 색인 51~100 …</div>
</div>
<div class="guide">✍️ <b>사용법</b> — 각 TEST(50단어)의 영어 단어·숙어를 보고 <b>빈칸에 뜻</b>을 쓰세요. <b>번호가 「어휘 색인」의 번호와 그대로 일치</b>하므로, 채점은 색인에서 <b>같은 번호</b>를 찾아 뜻·교재 페이지를 확인하면 됩니다. 틀린 단어는 해당 <b>교재 페이지</b>로 돌아가 문맥과 함께 복습하세요.</div>
{sections}
</body></html>'''
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"어휘 미니 테스트 생성: {total}단어 · {ntests}회분(각 {CHUNK}개) → {OUT}")


if __name__ == "__main__":
    build()
