"""단어장 시험지 PDF(정답본 페이지)에서 '영단어 - 한글뜻' 목록을 뽑아 JSON 으로 저장.

사용 예)
    python tools/extract_wordbook.py "워드마스터_Day_3~4.pdf" --page 2 --day "Day 3~4" \
        --out data/wordbook/day03_04.json

- 시험지 한 페이지가 좌/우 2단(왼쪽 No.1~40 = 영단어→뜻, 오른쪽 No.41~80 = 뜻→영단어)인
  형식을 가정하고, 좌표(x, y)로 행을 묶어 읽는다.
- 결과 JSON: {"title": ..., "source": ..., "words": [{"no":1,"word":"...","meaning":"..."}, ...]}
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _rows(page, x_split: float):
    """페이지의 텍스트 조각을 (행 y) 기준으로 묶고, 좌/우 단으로 나눈다."""
    import pymupdf  # noqa: F401  (pymupdf 는 PyMuPDF 패키지)

    spans = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                text = sp["text"].strip()
                if text:
                    spans.append({"x": sp["bbox"][0], "y": sp["bbox"][1],
                                  "size": sp["size"], "text": text})
    # y 가 가까운 조각들을 한 행으로 묶는다(같은 행이라도 글자 크기 때문에 y 가 1~3pt 어긋남)
    spans.sort(key=lambda s: s["y"])
    rows: list[list[dict]] = []
    for sp in spans:
        if rows and abs(sp["y"] - rows[-1][0]["y"]) <= 6:
            rows[-1].append(sp)
        else:
            rows.append([sp])
    out = []
    for row in rows:
        items = sorted(row, key=lambda s: s["x"])
        left = [s for s in items if s["x"] < x_split]
        right = [s for s in items if s["x"] >= x_split]
        out.append((left, right))
    return out


def _pair(col: list[dict], eng_first: bool) -> tuple[int, str, str] | None:
    """한 단(3조각: 번호 / 제시어 / 답)에서 (번호, 영단어, 한글뜻) 을 뽑는다."""
    if len(col) < 3:
        return None
    no_txt = col[0]["text"]
    if not re.fullmatch(r"\d{1,3}", no_txt):
        return None
    a, b = col[1]["text"], col[2]["text"]
    eng, ko = (a, b) if eng_first else (b, a)
    if not re.search(r"[A-Za-z]", eng) or not re.search(r"[가-힣]", ko):
        return None
    return int(no_txt), eng.strip(), ko.strip()


def extract(pdf: Path, page_no: int, x_split: float = 300.0) -> list[dict]:
    import pymupdf

    doc = pymupdf.open(str(pdf))
    page = doc[page_no - 1]
    words: list[dict] = []
    for left, right in _rows(page, x_split):
        for col, eng_first in ((left, True), (right, False)):
            got = _pair(col, eng_first)
            if got:
                words.append({"no": got[0], "word": got[1], "meaning": got[2]})
    words.sort(key=lambda w: w["no"])
    return words


def main() -> None:
    ap = argparse.ArgumentParser(description="단어 시험지 PDF → 단어 JSON")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--page", type=int, default=2, help="정답이 채워진 페이지 번호(기본 2)")
    ap.add_argument("--day", default="", help="범위 이름 (예: 'Day 3~4')")
    ap.add_argument("--source", default="", help="교재 이름")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--x-split", type=float, default=300.0, help="좌/우 단을 가르는 x 좌표")
    args = ap.parse_args()

    words = extract(args.pdf, args.page, args.x_split)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        {"title": args.day or args.pdf.stem, "source": args.source, "words": words},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.out} : {len(words)}개")


if __name__ == "__main__":
    main()
