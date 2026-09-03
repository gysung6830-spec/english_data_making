"""단어장 시험지 PDF(정답이 채워진 면)에서 '영단어 - 한글뜻' 목록을 뽑아 JSON 으로 저장.

사용 예)
    python tools/extract_wordbook.py "워드마스터_Day_3~4.pdf" --day "Day 3~4" \
        --source "워드마스터 수능2000" --out data/wordbook/suneung2000/day03_04.json

동작 방식
- 시험지는 좌/우 2단이고, 각 단은 [번호] [제시어] [답] 세 칸이다.
  '제시어'가 영단어인 교재도 있고 한글 뜻인 교재도 있어서, 순서가 아니라
  **글자 종류(한글이 있으면 뜻, 알파벳뿐이면 영단어)** 로 구분한다.
- 정답 면은 PDF 뒤쪽 절반이다(2쪽짜리 → 2쪽 / 4쪽짜리 → 3·4쪽). `--page` 로 지정도 가능.
- 뜻이나 숙어가 다음 줄로 넘어간 항목(예: 'cannot help but' + 'do')은 번호와의
  세로 거리로 같은 항목에 다시 붙인다.
- 결과 JSON: {"title": ..., "source": ..., "words": [{"no":1,"word":"...","meaning":"..."}, ...]}
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NEAR = 13.0          # 한 항목으로 볼 번호와의 세로 거리(pt)
HEADER_GAP = 4.0     # 표 머리글(No./제시어/…) 아래로 이 정도부터 본문


def _spans(page) -> list[dict]:
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                text = sp["text"].strip()
                if text:
                    out.append({"x": sp["bbox"][0], "y": sp["bbox"][1], "text": text})
    return out


def _join_ko(head: str, tail: str) -> str:
    """줄바꿈으로 잘린 한글 뜻을 이어 붙인다.

    '눈부신 빛,' + '노려봄' → '눈부신 빛, 노려봄'   (구두점 뒤에서 끊긴 경우)
    '수치, 계산, 형' + '태'  → '수치, 계산, 형태'    (단어 중간에서 끊긴 경우)
    """
    if not head:
        return tail
    return f"{head} {tail}" if head.endswith((",", ";", ")", "]", ".")) else head + tail


def _join_en(head: str, tail: str) -> str:
    """줄바꿈으로 잘린 영어 표제어(주로 숙어)를 이어 붙인다."""
    if not head:
        return tail
    return head + tail if head.endswith("-") else f"{head} {tail}"


def _extract_page(page, x_split: float) -> list[dict]:
    spans = _spans(page)
    if not spans:
        return []

    # 표 머리글 아래부터 본문으로 본다
    heads = [s["y"] for s in spans if s["text"] in ("No.", "제시어", "한글뜻/영단어")]
    top = max(heads) + HEADER_GAP if heads else 0.0

    body = [s for s in spans if s["y"] > top]
    numbers = [s for s in body if re.fullmatch(r"\d{1,3}", s["text"])]
    if not numbers:
        return []
    bottom = max(s["y"] for s in numbers) + NEAR
    body = [s for s in body if s["y"] <= bottom]

    # 번호마다 항목을 만들고, 나머지 조각을 같은 단에서 가장 가까운 번호에 붙인다
    items: dict[int, dict] = {}
    for n in numbers:
        items[id(n)] = {"no": int(n["text"]), "side": n["x"] < x_split,
                        "y": n["y"], "parts": []}
    for sp in body:
        if sp in numbers:
            continue
        side = sp["x"] < x_split
        near = [n for n in numbers if (n["x"] < x_split) == side
                and abs(n["y"] - sp["y"]) <= NEAR]
        if not near:
            continue
        owner = min(near, key=lambda n: abs(n["y"] - sp["y"]))
        items[id(owner)]["parts"].append(sp)

    words = []
    for it in items.values():
        eng, ko = "", ""
        for sp in sorted(it["parts"], key=lambda s: (round(s["y"], 1), s["x"])):
            text = sp["text"]
            if re.search(r"[가-힣]", text):
                ko = _join_ko(ko, text)
            elif "_" not in text and re.search(r"[A-Za-z]", text):
                eng = _join_en(eng, text)
        if eng and ko:
            words.append({"no": it["no"], "word": eng, "meaning": ko})
    return words


def answer_pages(doc) -> list[int]:
    """정답이 채워진 면의 페이지 번호(1-based).

    시험지 PDF 는 '문제 면 → 같은 시험지의 정답 면' 순서라, 뒤쪽 절반이 정답 면이다.
    (2쪽짜리 → 2쪽 / 4쪽짜리 → 3·4쪽)
    """
    n = doc.page_count
    return list(range(n // 2 + 1, n + 1))


def extract(pdf: Path, page_no: int | None = None, x_split: float = 300.0) -> list[dict]:
    import pymupdf

    doc = pymupdf.open(str(pdf))
    pages = [page_no] if page_no else answer_pages(doc)
    words: list[dict] = []
    for pno in pages:
        words += _extract_page(doc[pno - 1], x_split)
    words.sort(key=lambda w: w["no"])
    return words


def main() -> None:
    ap = argparse.ArgumentParser(description="단어 시험지 PDF → 단어 JSON")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--page", type=int, default=None,
                    help="정답이 채워진 페이지 번호(기본: 자동 — 뒤쪽 절반 페이지 전부)")
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
