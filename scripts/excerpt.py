"""완성된 교재 PDF에서 '일부 페이지'만 뽑아 발췌본을 만든다.

전체 PDF를 매번 확인하지 않도록, 바뀐 목차/구간만 잘라 보내는 용도.

사용법:
  python scripts/excerpt.py 7-12                 # 7~12쪽
  python scripts/excerpt.py 7-12,20,30-31        # 여러 구간
  python scripts/excerpt.py --find 인과          # '인과'가 나오는 연속 구간 자동 추출
  python scripts/excerpt.py 7-12 -o out/부분.pdf  # 저장 경로 지정
기본 입력: output/구문해석_실전서.pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz  # PyMuPDF

SRC = Path("output/구문해석_실전서.pdf")


def parse_ranges(spec: str, n: int) -> list[int]:
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            pages += list(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return [p - 1 for p in pages if 1 <= p <= n]      # 1-based → 0-based


def find_pages(doc, term: str) -> list[int]:
    hits = [i for i in range(doc.page_count) if term in doc[i].get_text()]
    if not hits:
        return []
    return list(range(min(hits), max(hits) + 1))       # 첫~끝 연속 구간


def main() -> None:
    args = sys.argv[1:]
    src = SRC
    out = None
    if "-o" in args:
        i = args.index("-o"); out = Path(args[i + 1]); del args[i:i + 2]
    doc = fitz.open(src)
    if args and args[0] == "--find":
        idx = find_pages(doc, args[1])
        label = args[1]
    else:
        idx = parse_ranges(args[0], doc.page_count)
        label = args[0].replace(",", "_")
    if not idx:
        print("추출할 페이지가 없습니다."); return
    out = out or Path(f"output/발췌_{label}.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    ex = fitz.open()
    for i in sorted(set(idx)):
        ex.insert_pdf(doc, from_page=i, to_page=i)
    ex.save(out)
    print(f"{len(set(idx))}쪽 → {out}")


if __name__ == "__main__":
    main()
