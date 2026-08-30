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
    # 핵심 문법 — 설명 빈칸이 살아 있는 판. 학생이 채우는 자료라는 것이 보인다.
    Shot("pilsaengbo-grammar.png", 1, head=["문장별 끊어읽기"],
         marks=["would rather A than B"], keep=1.0),
    Shot("pilsaengbo-summary2.png", 15, head=["필생보", "강사용"]),
    Shot("pilsaengbo-summary3.png", 9, head=["필생보", "강사용"]),
    # 재진술 사슬이 둘이고 형광펜이 다섯 곳인 지문. 합본 강사용에서 따로 받았다.
    Shot("hapbon-summary.png", 0, head=["글 정리"], marks=["nonlinear"], keep=1.0),
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

    Shot("workbook-integrated-pronoun.png", 6, head=["한글 포함"], keep=0.72),
    Shot("workbook-integrated-order.png", 7, head=["한글 포함"], keep=0.72),
    Shot("workbook-integrated-form.png", 2, head=["한글 포함"], keep=0.72),
    Shot("workbook-integrated-blank.png", 9, head=["한글 포함"], keep=1.0),

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


# ── 포인트별 부분 확대 ────────────────────────────────────────────────────
# 상세페이지에 지면 전체를 넣으면 글자가 작아 아무것도 안 읽힌다. 특징 하나에
# 그 특징이 보이는 자리만 잘라 붙이는 편이 낫다. 좌표는 0~1 비율이라
# dpi 를 바꿔도 그대로 쓴다.
CROPS = [
    # (원본 samples 파일, 저장 이름, (x0, y0, x1, y1))

    # 01 지문자료 — 판형 셋. 지면 위쪽만 봐도 배치 차이가 드러난다
    ("passage.png", "c-pass-plain.png", (0.03, 0.055, 0.97, 0.44)),
    ("one-line.png", "c-pass-stack.png", (0.03, 0.055, 0.97, 0.44)),
    ("one-line-2col.png", "c-pass-2col.png", (0.03, 0.055, 0.97, 0.44)),

    # 각 자료의 '반 페이지' — 지면이 어떻게 생겼는지 보이는 핵심 절반.
    # 조각만 늘어놓으면 부품은 알아도 지면이 안 그려진다.
    ("analysis.png", "h-analysis.png", (0.02, 0.030, 0.98, 0.520)),
    ("pilsaengbo-student.png", "h-psbc.png", (0.03, 0.055, 0.97, 0.470)),
    ("pilsaengbo-summary.png", "h-psbc-restate.png", (0.03, 0.310, 0.97, 0.625)),
    ("pilsaengbo-summary.png", "h-psbc-flow.png", (0.03, 0.628, 0.97, 0.880)),
    ("pilsaengbo-summary2.png", "h-psbc-restate2.png", (0.03, 0.305, 0.97, 0.640)),
    ("pilsaengbo-summary3.png", "h-psbc-restate3.png", (0.03, 0.300, 0.97, 0.600)),
    ("hapbon-summary.png", "h-psbc-restate4.png", (0.055, 0.352, 0.960, 0.660)),
    ("psb-answer.png", "h-psbs-catch.png", (0.02, 0.015, 0.98, 0.450)),
    ("workbook-integrated-pronoun.png", "c-wbi-pron.png", (0.03, 0.288, 0.97, 0.408)),
    ("psb-solve.png", "h-psbs.png", (0.02, 0.020, 0.98, 0.420)),
    ("workbook-integrated.png", "h-wbi.png", (0.02, 0.020, 0.98, 0.560)),
    ("workbook.png", "h-wb.png", (0.02, 0.015, 0.98, 0.450)),
    ("variation.png", "h-var.png", (0.02, 0.040, 0.98, 0.600)),
    ("mock.png", "h-mock.png", (0.02, 0.030, 0.98, 0.560)),

    # 02 지문분석지
    ("analysis.png", "c-analysis-easy.png", (0.05, 0.100, 0.95, 0.170)),
    ("analysis.png", "c-analysis-point.png", (0.66, 0.664, 0.96, 0.730)),
    ("analysis.png", "c-analysis-parse.png", (0.04, 0.170, 0.665, 0.322)),
    ("analysis.png", "c-analysis-gram.png", (0.66, 0.170, 0.96, 0.272)),

    # 03 필생보 강의용 — 학생용 지면이 특징을 더 잘 보여 준다
    ("pilsaengbo-student.png", "c-psbc-blank.png", (0.07, 0.172, 0.93, 0.232)),
    ("pilsaengbo-student.png", "c-psbc-wrong.png", (0.07, 0.232, 0.93, 0.328)),
    ("pilsaengbo-student.png", "c-psbc-circle.png", (0.08, 0.138, 0.70, 0.182)),
    ("pilsaengbo-grammar.png", "h-psbc-gram.png", (0.04, 0.044, 0.96, 0.320)),
    ("pilsaengbo-grammar.png", "c-psbc-gram-write.png", (0.04, 0.610, 0.96, 0.760)),
    ("pilsaengbo.png", "c-psbc-filled.png", (0.07, 0.168, 0.93, 0.228)),

    # 04 필생보 독학용
    ("psb-solve.png", "c-psbs-write.png", (0.05, 0.120, 0.95, 0.202)),
    ("psb-solve.png", "c-psbs-warn.png", (0.05, 0.208, 0.95, 0.252)),
    ("psb-answer.png", "c-psbs-catch.png", (0.05, 0.232, 0.95, 0.316)),
    ("psb-predict.png", "c-psbs-predict.png", (0.04, 0.090, 0.96, 0.330)),
    ("psb-signal.png", "c-psbs-signal.png", (0.04, 0.090, 0.96, 0.330)),

    # 05 통합 워크북
    ("workbook-integrated.png", "c-wbi-ref.png", (0.06, 0.388, 0.95, 0.538)),
    # 영작은 두 판이다. 지시문 띠까지 같이 잘라야 '배열'과 '어형 변화'가
    # 다른 문제라는 것이 보인다. 같은 1번 문장을 두 판으로 나란히 놓는다.
    ("workbook-integrated-order.png", "c-wbi-order.png", (0.03, 0.120, 0.97, 0.281)),
    ("workbook-integrated-form.png", "c-wbi-form.png", (0.03, 0.120, 0.97, 0.281)),
    ("workbook-integrated-order.png", "c-wbi-order2.png", (0.03, 0.292, 0.97, 0.410)),
    ("workbook-integrated-blank.png", "c-wbi-blank.png", (0.03, 0.088, 0.97, 0.335)),
    ("workbook-integrated-blank.png", "c-wbi-blank2.png", (0.03, 0.443, 0.97, 0.630)),
    ("workbook-integrated.png", "c-wbi-ko.png", (0.04, 0.236, 0.96, 0.372)),
    ("workbook-integrated-en.png", "c-wbi-en.png", (0.04, 0.236, 0.96, 0.348)),

    # 06 서술형 대비 교재
    ("workbook.png", "c-wb-types.png", (0.03, 0.030, 0.97, 0.069)),
    ("workbook.png", "c-wb-level.png", (0.04, 0.110, 0.51, 0.408)),
    ("workbook.png", "c-wb-answer.png", (0.51, 0.110, 0.97, 0.352)),

    # 07 변형문제
    ("variation.png", "c-var-choices.png", (0.49, 0.428, 0.96, 0.588)),
    ("variation.png", "c-var-passage.png", (0.04, 0.234, 0.50, 0.462)),
    ("variation.png", "c-var-round.png", (0.26, 0.083, 0.74, 0.113)),
    ("variation-answer.png", "c-var-why.png", (0.04, 0.352, 0.50, 0.530)),

    # 08 동형모의고사
    ("mock.png", "c-mock-head.png", (0.04, 0.045, 0.96, 0.200)),
    ("mock-paper.png", "c-mock-score.png", (0.04, 0.028, 0.51, 0.250)),
    ("mock-answer.png", "c-mock-why.png", (0.04, 0.080, 0.51, 0.300)),
]


def make_crops() -> list[Path]:
    """samples 안의 지면에서 특징이 보이는 자리만 잘라 낸다."""
    from PIL import Image

    made: list[Path] = []
    for src, name, (x0, y0, x1, y1) in CROPS:
        path = OUT / src
        if not path.exists():
            print(f"  · {name} — 원본 {src} 없음, 건너뜀")
            continue
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            w, h = rgb.size
            box = (round(w * x0), round(h * y0), round(w * x1), round(h * y1))
            rgb.crop(box).save(OUT / name)
        made.append(OUT / name)
        print(f"  ✔ samples/{name}  ({box[2] - box[0]}×{box[3] - box[1]})  ← {src}")
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


# ── 여러 조각을 한 장으로 세로로 잇기 ────────────────────────────────────
# 지문 하나만 보여 주면 "이 지문만 그런가" 싶다. 같은 자리를 지문마다 잇대어
# 놓으면 자료 전체가 그렇게 만들어졌다는 것이 한 장으로 보인다.
STACKS = [
    # (저장 이름, [조각들], 사이 여백)
    ("h-psbc-restate-set.png",
     ["h-psbc-restate2.png", "h-psbc-restate3.png", "h-psbc-restate.png"], 18),
]


def make_stacks(bg: str = "#F6F3EC") -> list[Path]:
    from PIL import Image

    made: list[Path] = []
    for name, parts, gap in STACKS:
        imgs = []
        for f in parts:
            path = OUT / f
            if path.exists():
                with Image.open(path) as im:
                    imgs.append(im.convert("RGB").copy())
        if not imgs:
            print(f"  · {name} — 조각이 없어 건너뜀")
            continue
        w = max(i.width for i in imgs)
        h = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
        sheet = Image.new("RGB", (w, h), bg)
        y = 0
        for im in imgs:
            sheet.paste(im, ((w - im.width) // 2, y))
            y += im.height + gap
        sheet.save(OUT / name)
        made.append(OUT / name)
        print(f"  ✔ samples/{name}  ({w}×{h})  ← {len(imgs)}장")
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description="판매 자료 PDF → 예시 이미지")
    ap.add_argument("--src", default="", help="PDF 들이 있는 폴더")
    ap.add_argument("--dpi", type=int, default=130)
    ap.add_argument("--only", default="", help="이 이름 한 장만 다시 뽑는다")
    ap.add_argument("--crops-only", action="store_true",
                    help="PDF 는 건드리지 않고 부분 확대만 다시 자른다")
    args = ap.parse_args()

    if args.crops_only:
        made = make_crops() + make_stacks()
        print(f"\n{len(made)}개 → {OUT}")
        return

    src = Path(args.src).expanduser()
    if not src.is_dir():
        sys.exit(f"폴더가 없습니다: {src}")
    made = shoot(src, args.dpi, args.only)
    if not args.only:
        made += compose_pairs()
        made += make_crops()
        made += make_stacks()
    print(f"\n{len(made)}개 → {OUT}")


if __name__ == "__main__":
    main()
