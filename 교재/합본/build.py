#!/usr/bin/env python3
"""영문법 완전정복 합본 빌더 — parts/*.html 를 순서대로 이어붙여 master.html 생성 후 PDF 렌더링."""
import glob, os, sys
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "parts")
OUT_HTML = os.path.join(HERE, "master.html")
OUT_PDF = os.path.join(os.path.dirname(HERE), "영문법_완전정복_합본.pdf")

order = sorted(glob.glob(os.path.join(PARTS, "*.html")))
buf = []
for p in order:
    with open(p, encoding="utf-8") as f:
        buf.append(f"<!-- ===== {os.path.basename(p)} ===== -->\n" + f.read())
html = "\n".join(buf)

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[build] parts={len(order)}  master.html={len(html)//1024}KB")

HTML(OUT_HTML).write_pdf(OUT_PDF)
size = os.path.getsize(OUT_PDF) // 1024
print(f"[build] PDF -> {OUT_PDF} ({size}KB)")
