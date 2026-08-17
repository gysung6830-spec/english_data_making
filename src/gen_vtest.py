# -*- coding: utf-8 -*-
"""부록: 어휘 미니 테스트 — 「어휘 색인」 번호 기준 50개씩(TEST 01=색인 1~50 …),
각 50개 '안에서' 순서만 무작위로 섞은 테스트지. 번호는 색인 번호 그대로라 채점은 색인에서 같은 번호 확인."""
import json, html, os, re, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "corpus", "workbook_content.json")
OUT = os.path.join(ROOT, "samples", "어휘테스트.html")

CHUNK = 50
SEED = 20260817  # 고정 시드 — 빌드마다 같은 배열


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
        # (색인번호, 단어) 쌍 — 색인 번호는 그대로 두고, 이 50개 '안에서' 순서만 셔플
        pairs = [(lo + i + 1, w) for i, w in enumerate(chunk)]
        random.Random(SEED + t).shuffle(pairs)
        items = "".join(
            f'<div class="ti"><span class="tn">{n}</span>'
            f'<span class="tw">{esc(w)}</span><span class="tb"></span></div>'
            for n, w in pairs
        )
        sections += (
            f'<section class="tst"><div class="tsth">'
            f'<span class="tstno">TEST {t + 1:02d}</span>'
            f'<span class="tstrg">색인 No. {lo + 1}–{lo + len(chunk)} · 무작위 순서</span>'
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
  <div class="sub">색인 번호 기준 50개씩 · 각 회차 안에서 무작위 배열</div>
  <div class="meta">총 <b>{total}</b>단어 · <b>{ntests}</b>회분 · <b>TEST 01 = 색인 1~50</b>, TEST 02 = 색인 51~100 … (각 50개 안에서 순서만 섞음)</div>
</div>
<div class="guide">✍️ <b>사용법</b> — 각 TEST는 <b>「어휘 색인」의 50개 구간</b>(01=1~50, 02=51~100 …)이며, 그 안에서 <b>순서만 무작위</b>로 섞여 있습니다. 단어 <b>번호는 색인 번호 그대로</b>이므로, 뜻을 쓴 뒤 색인에서 <b>같은 번호</b>를 찾아 채점하고, 틀린 단어는 <b>교재 페이지</b>로 돌아가 복습하세요.</div>
{sections}
</body></html>'''
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"어휘 미니 테스트 생성: {total}단어 · {ntests}회분(각 {CHUNK}개) → {OUT}")


if __name__ == "__main__":
    build()
