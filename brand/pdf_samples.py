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
SCAN_PAGES = 60       # marks 를 찾을 때 훑는 쪽수. 뒷장의 표시도 잡아야 한다


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
    # '지문 자료' 머리말을 셋이 나눠 쓴다. 본문 생김새로 가른다.
    #   원문만        → 해석 문장이 아예 없다
    #   한줄해석 세로형 → 해석에도 같은 번호가 붙는다 ('①미국 시인인')
    #   한줄해석 2단형  → 오른쪽 칸이라 번호 없이 해석만 온다
    Shot("passage.png", 0, head=["지문 자료"], not_marks=["미국 시인인"], keep=0.62),
    Shot("one-line.png", 0, head=["지문 자료"], marks=["①미국 시인인"], keep=0.62),
    Shot("one-line-2col.png", 0, head=["지문 자료"], marks=["미국 시인인"],
         not_marks=["①미국 시인인"], keep=0.78),

    # 지문분석지 — 본문 · 정리 · 학생용 빈칸 · 단어 TEST · 원문해석 · 활용 가이드
    Shot("analysis.png", 1, head=["이 학습지 100% 활용법"], keep=0.9),
    Shot("analysis-point.png", 2, head=["이 학습지 100% 활용법"], keep=0.86),
    Shot("analysis-flow.png", 3, head=["이 학습지 100% 활용법"], keep=0.9),
    Shot("analysis-blank.png", 6, head=["이 학습지 100% 활용법"], keep=0.9),
    Shot("analysis-vocatest.png", 4, head=["이 학습지 100% 활용법"], keep=0.86),
    Shot("analysis-guide.png", 0, head=["이 학습지 100% 활용법"], keep=0.86),

    # 필생보 강의용 — 강사용 / 학생 문제지 / 글 정리
    Shot("pilsaengbo.png", 1, head=["필생보", "강사용"]),
    Shot("pilsaengbo-summary.png", 3, head=["필생보", "강사용"]),
    Shot("pilsaengbo-student.png", 1, head=["학생 문제지"]),

    # 필생보 독학용 — 표지·목차 말고 실제로 푸는 지면 위주
    Shot("psb-solve.png", 15, marks=["한 문장씩 직접 풀기"], keep=0.9),
    Shot("psb-answer.png", 17, marks=["끊어읽기 · 캐치"], keep=0.9),
    Shot("psb-paraphrase.png", 7, marks=["재진술로 정답을 만든다"], keep=0.9),
    Shot("psb-signal.png", 13, marks=["신호 사전"], keep=0.9),
    Shot("psb-pace.png", 3, marks=["완급조절"], keep=0.9),
    Shot("psb-predict.png", 19, marks=["해석 전 예측"], keep=0.9),

    # 통합 영어 워크북 — 한글 포함 / 제외
    Shot("workbook-integrated.png", 1, head=["한글 포함"], keep=0.82),
    Shot("workbook-integrated-en.png", 1, head=["한글 제외"], keep=0.82),

    # 내신 서술형 워크북 — 조건 영작(난이도 3단 제시어)
    Shot("workbook.png", 12, head=["내신 서술형"], keep=0.86),

    # 변형문제 — 1회 문제 · 교사용 · 해설 · 2회 · 3회 · 빠른정답
    Shot("variation.png", 0, head=["변형문제 1회"], keep=0.86),
    Shot("variation-teacher.png", 4, head=["변형문제 1회"], keep=0.86),
    Shot("variation-answer.png", 10, head=["변형문제 1회"], keep=0.86),
    Shot("variation-r2.png", 12, head=["변형문제 1회"], keep=0.86),
    Shot("variation-r3.png", 19, head=["변형문제 1회"], keep=0.86),
    Shot("variation-quick.png", 9, head=["변형문제 1회"], keep=0.7),

    # 동형모의고사 — 시험지 · 문제 · 교사용 · 해설 · 빠른정답
    Shot("mock.png", 0, head=["동형모의고사"], keep=0.9),
    Shot("mock-paper.png", 1, head=["동형모의고사"], keep=0.9),
    Shot("mock-teacher.png", 2, head=["동형모의고사"], keep=0.9),
    Shot("mock-answer.png", 6, head=["동형모의고사"], keep=0.9),
    Shot("mock-quick.png", 5, head=["동형모의고사"], keep=0.6),
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


def shoot(src: Path, dpi: int = 130, only: str = "") -> list[Path]:
    import pymupdf
    from PIL import Image

    OUT.mkdir(parents=True, exist_ok=True)
    index = {p: scan_text(p) for p in sorted(src.glob("*.pdf"))}
    made: list[Path] = []

    for shot in SHOTS:
        if only and shot.name != only:
            continue
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


# ── 두 판본을 나란히 ──────────────────────────────────────────────────────
PAIRS = [
    # (왼쪽 파일, 왼쪽 라벨, 오른쪽 파일, 오른쪽 라벨, 저장 이름, 위에서 남길 비율)
    ("pilsaengbo.png", "강사용 · 정답 표시",
     "pilsaengbo-student.png", "학생용 · 빈칸",
     "pilsaengbo-compare.png", 0.66),
]


def compose_pairs(width: int = 1600) -> list[Path]:
    """같은 쪽의 두 판본을 나란히 붙인다.

    '강사용은 채워져 있고 학생용은 비어 있다'는 한눈에 보여야 팔린다. 글자를
    읽히려는 그림이 아니라 대비를 보여 주는 그림이라, 폭을 넉넉히 잡는다.
    """
    from PIL import Image

    from render import html_to_png, page  # noqa: PLC0415

    made: list[Path] = []
    for left, l_label, right, r_label, name, keep in PAIRS:
        lp, rp = OUT / left, OUT / right
        if not (lp.exists() and rp.exists()):
            print(f"  · {name} — 원본이 없어 건너뜀")
            continue

        crops = []
        for src in (lp, rp):
            with Image.open(src) as im:
                rgb = im.convert("RGB")
                crop = rgb.crop((0, 0, rgb.width, int(rgb.height * keep)))
                out = OUT / f"_pair_{src.name}"
                crop.save(out)
                crops.append((out, crop.width, crop.height))

        gap, pad, label_h = 26, 30, 46
        col = (width - pad * 2 - gap) // 2
        body_h = max(round(h * col / w) for _, w, h in crops)
        total_h = pad * 2 + label_h + body_h

        cells = "".join(f"""<div style="width:{col}px">
          <div style="font-weight:700;font-size:19px;color:#1B5A46;
               margin-bottom:10px">{label}</div>
          <img src="{path.as_uri()}" style="width:100%;display:block;
               border:1px solid #DED9CC;border-radius:6px">
        </div>""" for (path, _, _), label in zip(crops, (l_label, r_label)))

        html = page(
            f'<div style="background:#F6F3EC;padding:{pad}px;display:flex;'
            f'gap:{gap}px;align-items:flex-start">{cells}</div>',
            "body{font-family:'Malgun Gothic',sans-serif}", width, total_h)
        html_to_png(html, OUT / name, width, total_h)
        for path, _, _ in crops:
            path.unlink(missing_ok=True)
        made.append(OUT / name)
        print(f"  ✔ samples/{name}  ({width}×{total_h})")
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description="판매 자료 PDF → 예시 이미지")
    ap.add_argument("--src", required=True, help="PDF 들이 있는 폴더")
    ap.add_argument("--dpi", type=int, default=130)
    ap.add_argument("--only", default="", help="이 이름 한 장만 다시 뽑는다")
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    if not src.is_dir():
        sys.exit(f"폴더가 없습니다: {src}")
    made = shoot(src, args.dpi, args.only)
    if not args.only:
        made += compose_pairs()
    print(f"\n{len(made)}개 → {OUT}")


if __name__ == "__main__":
    main()
