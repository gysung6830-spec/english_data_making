# -*- coding: utf-8 -*-
"""2027 9월 모평 학습지 = 본책(형광펜 독해)에서 2027-09 회차 16문항의 페이지만 추출.
STEP1(직접 풀기) + 통합/STEP2·3 카드를 본책 구성 그대로. STEP1은 왼쪽(짝수) 면 유지.
표지 1면 + 추출 페이지 → samples/2027_9월_모평_독해_학습지.pdf
"""
import pymupdf as fitz, re, subprocess, tempfile, os

DIR = "/home/user/english_data_making/samples"
CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BOOK = f"{DIR}/형광펜독해_교재.pdf"
OUT = f"{DIR}/2027_9월_모평_독해_학습지.pdf"

COVER_HTML = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
@page{ size:A4; margin:0; } *{ box-sizing:border-box; }
body{ margin:0; font-family:"NanumSquareRound","Liberation Sans",sans-serif; }
.c{ height:297mm; padding:38mm 28mm; display:flex; flex-direction:column; color:#fff;
  background:linear-gradient(160deg,#12543d 0%, #1f7a5c 72%, #2a916d 100%); }
.k{ font-size:13px; font-weight:800; letter-spacing:2px; opacity:.9; }
.t{ font-size:46px; font-weight:800; line-height:1.12; margin:14px 0 8px; }
.s{ font-size:14px; line-height:1.8; opacity:.96; } .s b{ color:#ffe9a8; }
.r{ width:64mm; height:4px; background:#ffe9a8; border-radius:3px; margin:20px 0; }
.g{ margin-top:auto; font-size:12px; opacity:.92; } .g b{ color:#ffe9a8; }
.f{ margin-top:16px; font-size:11px; opacity:.72; }
</style></head><body><div class="c">
<div class="k">형광펜 독해 · 실전 학습지</div>
<div class="t">2027학년도<br>9월 모의평가</div>
<div class="s">고3 · 영어 <b>독해 16문항</b> — 본책과 동일 구성<br>
①<b>직접 풀기</b>(STEP 1) → ②<b>통합 카드</b>(직독직해·근거·재진술).<br>
순서·삽입은 <b>지시어·연결어 연결고리</b>로 풉니다.</div>
<div class="r"></div>
<div class="g">유형 21~41 · 실제 평가원 9월 모평 기출 · 문항마다 <b>재진술</b> 훈련</div>
<div class="f">© 김은아영어연구소 · 형광펜 독해 시리즈</div>
</div></body></html>'''


def render_cover():
    prof = tempfile.mkdtemp()
    hp = f"{prof}/cover.html"; open(hp, "w", encoding="utf-8").write(COVER_HTML)
    out = f"{prof}/cover.pdf"
    subprocess.run([CH, "--headless", "--no-sandbox", "--disable-gpu",
        f"--user-data-dir={prof}", "--disable-background-networking", "--no-first-run",
        f"--print-to-pdf={out}", "--no-pdf-header-footer", f"file://{hp}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def main():
    d = fitz.open(BOOK); n = d.page_count
    # 전체 STEP1(문제) 페이지 인덱스 — 문항 경계
    step1_pages = []
    for i in range(n):
        t = d[i].get_text()
        if "STEP 1" in t and "직접" in t:
            m = re.search(r'2027학년도 9월 (\d+)번', t)
            step1_pages.append((i, int(m.group(1)) if m else None))
    starts = [p for p, _ in step1_pages]

    def is_boundary(i):
        """유형 구분면·특강(1-PASS)·치트시트 = 문항이 아닌 섹션 페이지."""
        t = d[i].get_text()
        if "1-PASS" in t or "치트시트" in t:
            return True
        if "유형별 훈련" in t and re.search(r'유형\s*\d+\s*/\s*11', t):
            return True
        return False

    # 각 2027-09 문항: 자기 STEP1 ~ 다음 STEP1 직전까지, 단 섹션 경계면에서 멈춤
    items = {}
    for idx, (p, num) in enumerate(step1_pages):
        if num is None:
            continue
        end = starts[idx + 1] if idx + 1 < len(starts) else n
        pages = [p]
        for q in range(p + 1, end):
            if is_boundary(q):
                break
            pages.append(q)
        items[num] = pages
    order = [21,22,23,24,30,31,32,33,34,35,36,37,38,39,40,41]
    out = fitz.open()
    out.insert_pdf(fitz.open(render_cover()))   # p1 표지
    def cur_len(): return out.page_count
    for num in order:
        pgs = sorted(set(items.get(num, [])))
        if not pgs:
            print("!! 페이지 없음:", num); continue
        # STEP1이 왼쪽(짝수 0-index=홀수 1-index? spread: 표지=1(오른쪽), 2=왼쪽) → STEP1을 짝수 1-index(왼쪽)
        # 1-index 왼쪽 = 짝수. 현재 다음 삽입 위치 = cur_len()+1 (1-index). 왼쪽이려면 짝수.
        if (cur_len() + 1) % 2 != 0:
            out.new_page(width=fitz.paper_size("a4")[0], height=fitz.paper_size("a4")[1])  # 패딩 blank
        for p in pgs:
            out.insert_pdf(d, from_page=p, to_page=p)
    out.save(OUT, garbage=4, deflate=True, clean=True); npg = out.page_count; out.close(); d.close()
    print(f"학습지 추출 완료: {npg}면 · 16문항 · {OUT}")
    print("문항별 면수:", {k: len(items.get(k, [])) for k in order})


if __name__ == "__main__":
    main()
