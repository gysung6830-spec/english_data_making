"""실제 판매 자료 PDF 에서 라인업·상세페이지용 예시 이미지를 뽑는다.

    pip install pymupdf
    python brand/pdf_samples.py --src ~/Downloads/ortica-pdf

파일 이름은 내려받을 때마다 바뀌고 한글이 깨져 들어오기도 한다. 그래서
**첫 쪽 본문에 있는 표시 문구**로 자료를 가려낸다.

주의 — 여기서 뽑은 이미지는 홍보용 미리보기다. EBS·평가원 지문이 들어간
페이지가 있으므로, 블로그에 올릴 때는 한 지문 전체가 그대로 다 보이지 않게
자르거나 일부만 쓰는 편이 안전하다. (brand/ANALYSIS.md §6)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "samples"


HEAD_CHARS = 200      # 첫 쪽 머리말로 볼 글자 수
SCAN_PAGES = 8        # 본문 전체 검색에 쓸 앞쪽 쪽수


class Shot:
    """뽑아낼 한 장.

    head : 첫 쪽 **머리말**에 모두 있어야 하는 문구. 자료 이름표가 본문
           설명글에도 나오는 경우가 있어(예: '한글 포함/제외' 안내) 위치까지 본다.
    marks: 앞쪽 여러 쪽 어디에든 모두 있어야 하는 문구
    not_marks: 하나라도 있으면 그 파일은 아니다
    page : 0부터 세는 쪽 번호
    keep : 아래에서 잘라내고 남길 세로 비율
    """

    def __init__(self, name: str, page: int, *, head: list[str] | None = None,
                 marks: list[str] | None = None, keep: float = 0.8,
                 not_marks: list[str] | None = None):
        self.name = name
        self.head = head or []
        self.marks = marks or []
        self.not_marks = not_marks or []
        self.page = page
        self.keep = keep


SHOTS = [
    # 지문자료 — 원문만. 한줄해석과 머리말이 같아 '해석 없음'으로 가른다.
    Shot("passage.png", 0, head=["지문 자료"], not_marks=["미국 시인인"], keep=0.62),
    # 한줄해석 — 문장 아래에 해석이 붙는다.
    Shot("one-line.png", 0, head=["지문 자료"], marks=["미국 시인인"], keep=0.62),
    # 필생보 — 강사용(정답 표시)
    Shot("pilsaengbo.png", 1, head=["필생보", "강사용"]),
    Shot("pilsaengbo-summary.png", 3, head=["필생보", "강사용"]),
    # 필생보 — 학생 문제지(빈칸 상태)
    Shot("pilsaengbo-student.png", 1, head=["학생 문제지"]),
    # 필생보 독학용 교재
    Shot("pilsaengbo-book-cover.png", 0, head=["독해 훈련", "재진술"], keep=1.0),
    Shot("pilsaengbo-book-toc.png", 1, marks=["이 책 사용법"], keep=0.86),
    Shot("pilsaengbo-book-principle.png", 3, marks=["완급조절"], keep=0.86),
    # 형광펜 독해 학습지
    Shot("highlighter-guide.png", 0, head=["이 학습지 100% 활용법"], keep=0.86),
    Shot("highlighter.png", 1, head=["이 학습지 100% 활용법"], keep=0.82),
    # 통합 영어 워크북 — 한글 포함 / 제외
    Shot("workbook-integrated.png", 1, head=["한글 포함"], keep=0.82),
    Shot("workbook-integrated-en.png", 1, head=["한글 제외"], keep=0.82),
    # 내신 서술형 워크북 — 조건 영작(난이도 3단 제시어)
    Shot("workbook.png", 12, head=["내신 서술형"], keep=0.86),
    # 변형문제
    Shot("variation.png", 0, head=["변형문제 1회"]),
    Shot("variation-answer.png", 10, head=["변형문제 1회"]),
    # 동형모의고사 — 학교 시험지 형식
    Shot("mock.png", 0, head=["동형모의고사"], keep=0.86),
    Shot("mock-answer.png", 4, head=["동형모의고사"], keep=0.82),
]


def scan_text(path: Path) -> tuple[str, str]:
    """(첫 쪽 머리말, 앞쪽 여러 쪽 본문)."""
    import pymupdf

    with pymupdf.open(path) as d:
        head = (d[0].get_text() or "")[:HEAD_CHARS]
        body = "".join(d[i].get_text() or "" for i in range(min(SCAN_PAGES, d.page_count)))
    return head, body


def pick(index: dict[Path, tuple[str, str]], shot: Shot) -> Path | None:
    for path, (head, body) in index.items():
        if not all(m in head for m in shot.head):
            continue
        if not all(m in body for m in shot.marks):
            continue
        if any(m in body for m in shot.not_marks):
            continue
        return path
    return None


def shoot(src: Path, dpi: int = 130) -> list[Path]:
    import pymupdf
    from PIL import Image

    OUT.mkdir(parents=True, exist_ok=True)
    index = {p: scan_text(p) for p in sorted(src.glob("*.pdf"))}
    made: list[Path] = []

    for shot in SHOTS:
        path = pick(index, shot)
        if path is None:
            print(f"  · {shot.name} — {shot.head + shot.marks} 가 든 PDF 없음, 건너뜀")
            continue
        with pymupdf.open(path) as doc:
            if shot.page >= doc.page_count:
                print(f"  · {shot.name} — {path.name} 은 {doc.page_count}쪽뿐, 건너뜀")
                continue
            pix = doc[shot.page].get_pixmap(dpi=dpi)
            raw = OUT / f"_raw_{shot.name}"
            pix.save(str(raw))
        with Image.open(raw) as im:
            rgb = im.convert("RGB")
            if shot.keep < 1.0:
                rgb = rgb.crop((0, 0, rgb.width, int(rgb.height * shot.keep)))
            rgb.save(OUT / shot.name)
        raw.unlink(missing_ok=True)
        made.append(OUT / shot.name)
        print(f"  ✔ samples/{shot.name}  ← {path.name[:26]} p{shot.page + 1}")
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
