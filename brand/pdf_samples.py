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


# 새 워크북은 표지가 없어 첫 쪽 본문 머리로 가려낸다. 필생보에도 '올림포스
# 영어독해 기본1' 이 출처로 적혀 있어, 단원 번호까지 붙여야 겹치지 않는다.
WB = dict(head=["올림포스 영어독해 기본1 10-2"], marks=["영작①"])

# 필생보 새 판 — 맨 앞에 '사용법'(범례) 쪽이 붙었다. 강사용·학생용의 첫 쪽이
# 똑같아서 머리말로는 못 가른다. 본문에 있는 판본 이름으로 가른다.
PSB_T = dict(head=["필생보 사용법"], marks=["강사용 · 정답 표시"])
PSB_S = dict(head=["필생보 사용법"], marks=["학생 문제지"])

# 변형문제 새 판 — 회차로 나누던 것을 한 지문 17문항 통합본으로 묶었다.
VAR = dict(head=["통합본 17문항"])

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

    # 필생보 강의용 새 판 — 사용법 · 통독+어휘 · 문장별 · 글 정리 · 핵심 문법
    Shot("pilsaengbo-guide.png", 0, **PSB_T, keep=1.0),
    Shot("pilsaengbo.png", 1, **PSB_T, keep=1.0),
    Shot("pilsaengbo-sent.png", 2, **PSB_T, keep=1.0),
    Shot("pilsaengbo-summary.png", 4, **PSB_T, keep=1.0),
    Shot("pilsaengbo-grammar.png", 5, **PSB_T, keep=1.0),
    # 학생용 — 같은 지면이 빈칸으로. 3쪽에 '이렇게 읽으면 안 돼'가 붙는다.
    Shot("pilsaengbo-student.png", 2, **PSB_S, keep=1.0),
    Shot("pilsaengbo-student2.png", 3, **PSB_S, keep=1.0),

    # 필생보 독학용 — 표지·목차 말고 실제로 푸는 지면 위주
    Shot("psb-solve.png", 15, marks=["한 문장씩 직접 풀기"], keep=0.9),
    Shot("psb-answer.png", 17, marks=["끊어읽기 · 캐치"], keep=0.9),
    Shot("psb-paraphrase.png", 7, marks=["재진술로 정답을 만든다"], keep=0.9),
    Shot("psb-signal.png", 13, marks=["신호 사전"], keep=0.9),
    Shot("psb-pace.png", 3, marks=["완급조절"], keep=0.9),
    Shot("psb-predict.png", 19, marks=["해석 전 예측"], keep=0.9),

    # 통합 영어 워크북 — 새 판(올림포스 10-2). 영작이 ①함정 단어 / ②어형 변형
    # 둘로 갈렸고 쪽 순서도 바뀌었다. 표지가 없어 첫 쪽 본문으로 가려낸다.
    Shot("workbook-integrated.png", 8, **WB, keep=0.82),          # 통합 카드
    Shot("workbook-integrated-vocab.png", 3, **WB, keep=0.72),    # 어휘 (상)
    Shot("workbook-integrated-order.png", 4, **WB, keep=0.72),    # 영작① 함정
    Shot("workbook-integrated-form.png", 5, **WB, keep=0.72),     # 영작② 어형
    Shot("workbook-integrated-blank.png", 6, **WB, keep=1.0),     # 지문·요약문 빈칸
    Shot("workbook-integrated-pronoun.png", 7, **WB, keep=0.72),  # 대명사 지칭

    # 한글 포함 / 제외 대비만 이전 판에서 가져온다. 새 판은 아직 한 벌만 받았다.
    Shot("workbook-integrated-ko.png", 1, head=["한글 포함"], keep=0.82),
    Shot("workbook-integrated-en.png", 1, head=["한글 제외"], keep=0.82),

    # 내신 서술형 워크북 — 조건 영작(난이도 3단 제시어)
    Shot("workbook.png", 12, head=["내신 서술형"], keep=0.86),

    # 변형문제 — 1회 문제 · 교사용 · 해설 · 2회 · 3회 · 빠른정답
    Shot("variation.png", 8, **VAR, keep=0.86),            # 어휘 — 원문형
    Shot("variation-gram.png", 5, **VAR, keep=0.86),       # 어법 모두 고르기
    Shot("variation-gramwrite.png", 6, **VAR, keep=0.86),  # 어법 서술형
    Shot("variation-oxen.png", 4, **VAR, keep=0.86),       # 내용 O/X (영어)
    Shot("variation-teacher.png", 17, **VAR, keep=0.86),   # 교사용 문제+해설
    Shot("variation-answer.png", 45, **VAR, keep=0.86),    # 해설지 — 어법 서술형
    Shot("variation-quick.png", 37, **VAR, keep=0.7),      # 빠른 정답

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
    ("analysis.png", "h-analysis.png", (0.02, 0.020, 0.98, 0.412)),
    ("pilsaengbo-student.png", "h-psbc.png", (0.03, 0.040, 0.97, 0.290)),
    ("pilsaengbo-summary.png", "h-psbc-restate.png", (0.05, 0.265, 0.95, 0.492)),
    ("pilsaengbo-summary.png", "h-psbc-flow.png", (0.05, 0.510, 0.95, 0.728)),
    ("psb-answer.png", "h-psbs-catch.png", (0.02, 0.015, 0.98, 0.450)),
    # 지시문 띠 + 실제 지칭 문항. 띠가 없으면 무슨 문제인지 안 보인다.
    ("workbook-integrated-pronoun.png", "c-wbi-pron.png", (0.03, 0.125, 0.97, 0.258)),
    ("workbook-integrated-vocab.png", "c-wbi-vocab.png", (0.03, 0.125, 0.97, 0.258)),
    ("psb-solve.png", "h-psbs.png", (0.02, 0.020, 0.98, 0.420)),
    ("workbook-integrated.png", "h-wbi.png", (0.02, 0.020, 0.98, 0.560)),
    ("workbook.png", "h-wb.png", (0.02, 0.015, 0.98, 0.450)),
    ("variation.png", "h-var.png", (0.02, 0.040, 0.98, 0.600)),
    ("mock.png", "h-mock.png", (0.02, 0.030, 0.98, 0.560)),

    # 02 지문분석지
    ("analysis.png", "c-analysis-easy.png", (0.04, 0.088, 0.96, 0.152)),
    # 반 페이지(h-analysis)가 1~2문장을 이미 보여 준다. 조각은 5문장에서 딴다.
    ("analysis.png", "c-analysis-parse.png", (0.035, 0.700, 0.70, 0.885)),
    ("analysis.png", "c-analysis-gram.png", (0.685, 0.703, 0.96, 0.858)),
    # 지칭은 본문 동그라미와 오른쪽 골드 박스가 짝이다. 한 줄을 통째로 잘라야
    # ⓐ 가 무엇을 가리키는지 보인다.
    ("analysis.png", "c-analysis-point.png", (0.035, 0.535, 0.96, 0.685)),

    # 03 필생보 강의용 — 학생용 지면이 특징을 더 잘 보여 준다
    # 조각은 빈칸 하나만 학생용에서 따고 나머지는 강사용에서 딴다.
    # 학생용은 빈칸이라 무엇을 배우는 자리인지가 사진으로는 안 보인다.
    ("pilsaengbo-sent.png", "c-psbc-circle.png", (0.06, 0.152, 0.94, 0.190)),
    # 강사용 쪽에서 잘라야 △ 판정과 '→ 바르게'가 채워진 채로 보인다
    ("pilsaengbo-sent.png", "c-psbc-ox.png", (0.06, 0.560, 0.94, 0.640)),
    ("pilsaengbo-student2.png", "c-psbc-notread.png", (0.06, 0.573, 0.94, 0.600)),
    ("pilsaengbo.png", "c-psbc-vocab.png", (0.05, 0.437, 0.95, 0.618)),
    ("pilsaengbo-guide.png", "c-psbc-guide.png", (0.05, 0.280, 0.95, 0.464)),
    ("pilsaengbo-grammar.png", "h-psbc-gram.png", (0.05, 0.050, 0.95, 0.315)),
    ("pilsaengbo-grammar.png", "c-psbc-gram-write.png", (0.05, 0.590, 0.95, 0.737)),
    ("pilsaengbo-sent.png", "c-psbc-filled.png", (0.06, 0.120, 0.94, 0.255)),

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
    ("workbook-integrated-order.png", "c-wbi-order.png", (0.03, 0.125, 0.97, 0.368)),
    ("workbook-integrated-form.png", "c-wbi-form.png", (0.03, 0.125, 0.97, 0.368)),
    ("workbook-integrated-blank.png", "c-wbi-blank.png", (0.03, 0.098, 0.97, 0.222)),
    ("workbook-integrated-blank.png", "c-wbi-blank2.png", (0.03, 0.468, 0.97, 0.682)),
    ("workbook-integrated-ko.png", "c-wbi-ko.png", (0.04, 0.236, 0.96, 0.372)),
    ("workbook-integrated-en.png", "c-wbi-en.png", (0.04, 0.236, 0.96, 0.348)),

    # 06 서술형 대비 교재
    ("workbook.png", "c-wb-types.png", (0.03, 0.030, 0.97, 0.069)),
    ("workbook.png", "c-wb-level.png", (0.04, 0.110, 0.51, 0.408)),
    ("workbook.png", "c-wb-answer.png", (0.51, 0.110, 0.97, 0.352)),

    # 07 변형문제
    # 교사용 한 쪽에 지문 · 선지 · 오답 해설이 위아래로 붙어 있다
    ("variation-teacher.png", "c-var-orig.png", (0.05, 0.190, 0.50, 0.425)),
    ("variation-teacher.png", "c-var-choices.png", (0.05, 0.425, 0.50, 0.578)),
    ("variation-teacher.png", "c-var-why.png", (0.05, 0.578, 0.50, 0.872)),
    # 같은 지문을 표현만 바꿔 낸 판. 위 c-var-orig 와 나란히 놓으면 차이가 보인다
    ("variation-gramwrite.png", "c-var-passage.png", (0.05, 0.155, 0.50, 0.398)),
    ("variation-gramwrite.png", "c-var-write.png", (0.05, 0.040, 0.50, 0.159)),
    ("variation-oxen.png", "c-var-oxen.png", (0.05, 0.412, 0.50, 0.540)),

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


# ── 변형문제 유형 한 장씩 ─────────────────────────────────────────────────
# "열일곱 유형이 각각 어떻게 생겼는지"를 목록 글자만으로는 못 보여 준다.
# 학생용 문제지 열일곱 쪽에서 유형칸을 한 장씩 따 온다.
#
# 지문은 열일곱 쪽에 똑같이 실려 있다. 그대로 열일곱 번 붙이면 같은 지문만
# 계속 나오고 세로가 네 배로 길어지므로, **지시문 위쪽과 지문 아래쪽만** 잘라
# 붙인다. 어법·어휘처럼 지문 안에 밑줄로 묻는 유형은 지문이 곧 문제라서
# 통째로 남긴다.
VARIATION_TYPES = [
    "주제", "제목", "함의추론", "내용 O/X", "내용 O/X (영어)",
    "어법 — 모두 고르기", "어법 서술형", "어법·어휘 짝짓기",
    "어휘 — 원문형", "어휘 — 유의어형", "어휘 — 부정어형",
    "빈칸추론", "연결어 (A)·(B)", "순서 배열", "문장 삽입",
    "요약문 빈칸", "어순 배열",
]

# 본문 칸 좌우(포인트). 오른쪽 절반은 늘 비어 있다.
_VAR_X = (30, 292)
_VAR_GAP = 10          # 지시문과 지문 아랫부분을 이어 붙일 때 벌리는 간격(px)


def variation_gallery(src: Path, dpi: int = 130) -> list[Path]:
    """변형문제 학생용 열일곱 쪽 → 유형별 조각 열일곱 장."""
    import pymupdf
    from PIL import Image

    index = {p: scan_text(p) for p in sorted(src.glob("*.pdf"))}
    path = pick(index, Shot("", 0, **VAR))
    if path is None:
        print("  · 변형문제 유형 조각 — 통합본 PDF 없음, 건너뜀")
        return []

    OUT.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    z = dpi / 72
    with pymupdf.open(path) as doc:
        for i, label in enumerate(VARIATION_TYPES):
            page = doc[i]
            blocks = [b for b in page.get_text("blocks")
                      if b[4].strip() and "Ortica" not in b[4]]
            if not blocks:
                continue
            last = max(b[3] for b in blocks)
            # 유형 이름이 든 초록 띠. 표지 띠가 하나 더 있는 첫 쪽은 아래 것을 쓴다.
            bands = sorted((r["rect"] for r in page.get_drawings()
                            if r["rect"].width > 400 and 20 < r["rect"].height < 60),
                           key=lambda r: r.y0)
            top = bands[-1].y0 - 4 if bands else 30
            # 지문 상자 — 본문 칸 폭이고 세로로 긴 사각형
            boxes = sorted((r["rect"] for r in page.get_drawings()
                            if r["rect"].height > 100 and r["rect"].x1 < 300),
                           key=lambda r: r.y0)
            box = boxes[0] if boxes else None

            pix = page.get_pixmap(dpi=dpi)
            raw = OUT / "_raw_var.png"
            pix.save(str(raw))
            with Image.open(raw) as im:
                full = im.convert("RGB")
                x0, x1 = (round(v * z) for v in _VAR_X)

                def band(y0: float, y1: float):
                    return full.crop((x0, round(y0 * z), x1, round(y1 * z)))

                # 지문 아래에 선지·답란이 있으면 지문을 건너뛴다.
                if box is not None and last > box.y1 + 12:
                    a, b = band(top, box.y0 - 3), band(box.y1 + 3, last + 8)
                    out = Image.new("RGB", (a.width, a.height + _VAR_GAP + b.height),
                                    "white")
                    out.paste(a, (0, 0))
                    out.paste(b, (0, a.height + _VAR_GAP))
                else:
                    out = band(top, last + 8)
                name = f"g-var-{i + 1:02d}.png"
                out.save(OUT / name)
            raw.unlink(missing_ok=True)
            made.append(OUT / name)
            print(f"  ✔ samples/{name}  ({out.width}×{out.height})  {label}")
    return made


# ── 두 판본을 나란히 ──────────────────────────────────────────────────────
PAIRS = [
    # (왼쪽 파일, 왼쪽 라벨, 오른쪽 파일, 오른쪽 라벨, 저장 이름, 위에서 남길 비율)
    ("pilsaengbo-sent.png", "강의용 · 정답 표시",
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
STACKS: list[tuple[str, list[str], int]] = [
    # (저장 이름, [조각들], 사이 여백)
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
    ap.add_argument("--gallery-only", action="store_true",
                    help="변형문제 유형 조각만 다시 뽑는다")
    args = ap.parse_args()

    if args.gallery_only:
        made = variation_gallery(Path(args.src).expanduser(), args.dpi)
        print(f"\n{len(made)}개 → {OUT}")
        return

    if args.crops_only:
        made = make_crops() + make_stacks()
        print(f"\n{len(made)}개 → {OUT}")
        return

    src = Path(args.src).expanduser()
    if not src.is_dir():
        sys.exit(f"폴더가 없습니다: {src}")
    made = shoot(src, args.dpi, args.only)
    if not args.only:
        made += variation_gallery(src, args.dpi)
        made += compose_pairs()
        made += make_crops()
        made += make_stacks()
    print(f"\n{len(made)}개 → {OUT}")


if __name__ == "__main__":
    main()
