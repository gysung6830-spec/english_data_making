"""실제 판매 자료 PDF 에서 라인업·상세페이지용 예시 이미지를 뽑는다.

    pip install pymupdf
    python brand/pdf_samples.py --src ~/Downloads/ortica-pdf

`SHOTS` 에 (파일 이름 조각, 페이지 번호, 저장할 이름) 을 적어 두면 그 페이지를
PNG 로 저장한다. 파일명은 바뀌기 쉬우므로 '조각'으로 찾는다.

주의 — 여기서 뽑은 이미지는 홍보용 미리보기다. EBS·평가원 지문이 들어간
페이지가 있으므로, 블로그에 올릴 때는 한 지문 전체가 그대로 다 보이지 않게
자르거나 일부만 쓰는 편이 안전하다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "samples"

# (파일명 조각, 0부터 세는 페이지, 저장 이름, 아래에서 잘라낼 비율)
SHOTS: list[tuple[str, int, str, float]] = [
    # 지문자료 — 원문만. 문장마다 번호가 붙는다.
    ("2026", 0, "passage.png", 0.62),
    # 한줄해석 — 원문 아래 문장별 해석
    ("2026", 0, "one-line.png", 0.62),
    # 필생보 — 문장별 끊어읽기 & '이렇게 읽으면 오답'
    ("ortica", 1, "pilsaengbo.png", 0.80),
    # 필생보 — 글 정리 · 재진술 사슬
    ("ortica", 3, "pilsaengbo-summary.png", 0.80),
    # 워크북 — 조건 영작(난이도 3단 제시어)
    ("worksheet", 12, "workbook.png", 0.86),
    # 변형문제 — 문제지 첫 장
    ("123", 0, "variation.png", 0.80),
    # 변형문제 — 해설(오답 유형 표시)
    ("123", 10, "variation-answer.png", 0.80),
]

# 한줄해석은 지문자료와 파일 이름이 겹친다. 제목 줄에도 한글이 있어서 특정
# 낱말로는 못 가른다. 한 쪽 전체의 한글 비율로 나눈다(해석이 붙으면 확 올라간다).
_HANGUL_MIX = 0.25


def _hangul_ratio(text: str) -> float:
    letters = [c for c in text if not c.isspace()]
    if not letters:
        return 0.0
    return sum("가" <= c <= "힣" for c in letters) / len(letters)


def find(src: Path, fragment: str) -> list[Path]:
    return sorted(p for p in src.glob("*.pdf") if fragment.lower() in p.name.lower())


def pick(src: Path, fragment: str, name: str) -> Path | None:
    """조각으로 파일을 찾는다. 후보가 둘이면 한줄해석/원문을 내용으로 가른다."""
    import pymupdf

    hits = find(src, fragment)
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    wants_korean = name.startswith("one-line")
    scored = []
    for p in hits:
        with pymupdf.open(p) as d:
            scored.append((_hangul_ratio(d[0].get_text() or ""), p))
    scored.sort()
    return scored[-1][1] if wants_korean else scored[0][1]


def shoot(src: Path, dpi: int = 130) -> list[Path]:
    import pymupdf
    from PIL import Image

    OUT.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    for fragment, pno, name, keep in SHOTS:
        path = pick(src, fragment, name)
        if path is None:
            print(f"  · {name} — '{fragment}' 가 든 PDF 를 못 찾음, 건너뜀")
            continue
        with pymupdf.open(path) as doc:
            if pno >= doc.page_count:
                print(f"  · {name} — {path.name} 은 {doc.page_count}쪽뿐, 건너뜀")
                continue
            pix = doc[pno].get_pixmap(dpi=dpi)
            raw = OUT / f"_raw_{name}"
            pix.save(str(raw))
        with Image.open(raw) as im:
            rgb = im.convert("RGB")
            # 아래 여백(쪽번호·저작권 줄)을 잘라 목록에서 빈칸이 안 생기게 한다
            rgb.crop((0, 0, rgb.width, int(rgb.height * keep))).save(OUT / name)
        raw.unlink(missing_ok=True)
        made.append(OUT / name)
        print(f"  ✔ samples/{name}  ← {path.name} p{pno + 1}")
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description="판매 자료 PDF → 예시 이미지")
    ap.add_argument("--src", required=True, help="PDF 들이 있는 폴더")
    ap.add_argument("--dpi", type=int, default=130)
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    if not src.is_dir():
        sys.exit(f"폴더가 없습니다: {src}")
    made = shoot(src, args.dpi)
    print(f"\n{len(made)}개 → {OUT}")


if __name__ == "__main__":
    main()
