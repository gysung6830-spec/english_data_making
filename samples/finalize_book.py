#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""교재 PDF 후처리: (1) 문제=왼쪽/해설=오른쪽 펼침면 정렬  (2) 전 페이지 하단 푸터.

- 문제 페이지(STEP 1 · 직접 풀기)는 펼침면 '왼쪽'(짝수 페이지)에 오도록,
  필요하면 바로 앞에 빈 페이지를 끼워 짝을 맞춘다. (해설 STEP 2는 자연히 오른쪽)
- 모든 페이지 하단 중앙에 '페이지 번호 · (c) 2026. 김은아영어연구소. all rights reserved'.

사용: python samples/finalize_book.py <입력.pdf> <출력.pdf>
"""
import sys, fitz

KFONT = "/usr/share/fonts/truetype/nanumsquareround/NanumSquareRoundR.ttf"
FOOT = "(c) 2026. 김은아영어연구소. all rights reserved"

def is_problem(page):
    t = page.get_text()
    return ("STEP 1" in t) and ("직접" in t)

def finalize(src_path, out_path):
    src = fitz.open(src_path)
    out = fitz.open()
    for i in range(src.page_count):
        # 문제 페이지는 짝수 페이지(1-based)=펼침면 왼쪽에 오게. 현재 배치 수가 짝수면
        # 다음 장이 홀수(오른쪽)가 되므로 빈 페이지를 하나 끼워 왼쪽으로 민다.
        if is_problem(src[i]) and out.page_count % 2 == 0:
            r = src[i].rect
            out.new_page(width=r.width, height=r.height)
        out.insert_pdf(src, from_page=i, to_page=i)

    total = out.page_count
    for i in range(total):
        p = out[i]
        r = p.rect
        y = r.height - 22
        p.insert_textbox(
            fitz.Rect(0, y, r.width, y + 15),
            f"{i+1} / {total}   ·   {FOOT}",
            fontfile=KFONT, fontname="nsr", fontsize=7.3,
            color=(0.55, 0.56, 0.57), align=1,
        )
    out.save(out_path, deflate=True)
    print(f"후처리 완료: {total} pages (문제=왼쪽 정렬 + 푸터) → {out_path}")

if __name__ == "__main__":
    finalize(sys.argv[1], sys.argv[2])
