"""CLI 진입점 + 입력 라우팅 + auto-fit PDF 빌더.

파이프라인:
  입력파일 → extract_text → split_passages → translate_missing
           → render_format_* → html_to_pdf(auto-fit) → PDF
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List

try:
    from .ocr import IMAGE_EXTS, is_scanned_pdf, ocr_file
    from .parser import Passage, split_passages
    from .renderer import render_format_a, render_format_b, render_format_c
    from .translator import translate_missing
except ImportError:  # 스크립트로 직접 실행할 때(python main.py)
    from ocr import IMAGE_EXTS, is_scanned_pdf, ocr_file
    from parser import Passage, split_passages
    from renderer import render_format_a, render_format_b, render_format_c
    from translator import translate_missing

# ── auto-fit 상수 ─────────────────────────────────────────────
# A4 @96dpi
A4_W_PX = 794
A4_H_PX = 1123
# 본문 가용 높이 = A4(297mm) - 상하 여백 20mm씩 = 257mm
PAGE_H_PX = 257 * 96 / 25.4          # ≈ 971px
CALIB = 0.90                          # measure ↔ 실제 PDF 오차 흡수(넘침 방지)
FIT_STEPS = ["", "compact", "compact2"]

# 모든 페이지 하단 가운데에 들어가는 고정 저작권 문구
FOOTER_TEXT = "본 자료는 은아T영어연구소에서 제작되었습니다"
_FOOTER_FONT = (
    "'NanumMyeongjo','Nanum Myeongjo','나눔명조','Noto Serif CJK KR',serif"
)

# 형식 키 → (렌더 함수, 파일명 접미사)
FORMATS = {
    "a": (render_format_a, "한줄해석"),
    "c": (render_format_c, "한줄영어"),
    "b": (render_format_b, "좌지문우해석"),
}

_FNAME_BAD = re.compile(r'[\\/:*?"<>|]')


def safe_filename(name: str) -> str:
    """파일명 금지문자를 _ 로 치환."""
    return _FNAME_BAD.sub("_", (name or "").strip()) or "지문"


# ── 입력 라우팅 ───────────────────────────────────────────────

def extract_text(path) -> str:
    """입력 종류에 맞춰 텍스트 추출(+필요 시 OCR)."""
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".txt":
        return p.read_text(encoding="utf-8", errors="replace")

    if suffix in IMAGE_EXTS:
        return ocr_file(p)

    if suffix == ".pdf":
        if is_scanned_pdf(p):
            return ocr_file(p)
        # 디지털 PDF
        import pdfplumber
        parts: List[str] = []
        with pdfplumber.open(str(p)) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        text = "\n".join(parts)
        # 추출은 됐지만 실질적으로 비었으면 OCR 재시도
        if len(text.strip()) < 10:
            return ocr_file(p)
        return text

    # 알 수 없는 확장자: 텍스트로 시도
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


# ── auto-fit PDF 빌더 ─────────────────────────────────────────

def html_to_pdf(html_str: str, out_pdf, autofit: bool = True) -> None:
    """Playwright(Chromium)로 HTML 렌더 → auto-fit 축소 → A4 PDF 출력."""
    from playwright.sync_api import sync_playwright

    out_pdf = str(out_pdf)

    # 미리 설치된 Chromium을 쓰는 환경(컨테이너 등)에서는
    # PLAYWRIGHT_CHROMIUM_EXECUTABLE 로 실행 파일 경로를 지정할 수 있다.
    exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    launch_kwargs = {"args": ["--no-sandbox"]}
    if exe:
        launch_kwargs["executable_path"] = exe

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": A4_W_PX, "height": A4_H_PX})
        page.set_content(html_str, wait_until="networkidle")

        if autofit:
            _apply_autofit(page)

        # 페이지마다 하단 가운데에 반복되는 저작권 푸터(하단 여백 안에 배치)
        footer_template = (
            f'<div style="width:100%; text-align:center; '
            f'font-family:{_FOOTER_FONT}; font-size:8px; color:#9a9a9f; '
            f'padding:0; margin:0;">{FOOTER_TEXT}</div>'
        )

        page.pdf(
            path=out_pdf,
            format="A4",
            margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",   # 상단 기본 머리글 숨김
            footer_template=footer_template,
        )
        browser.close()


def _apply_autofit(page) -> None:
    """각 지문 블록의 실제 렌더 높이를 재어 알맞은 축소 클래스를 확정한다."""
    # 지문 개수
    count = page.eval_on_selector_all(".passage", "els => els.length")
    if not count:
        return

    # 머리글 높이(첫 지문 예산에서 차감)
    header_h = page.eval_on_selector_all(
        ".doc-header",
        "els => els.length ? els[0].getBoundingClientRect().height + 10 : 0",
    ) or 0

    for i in range(1, count + 1):
        sel = f"#passage-{i}"
        budget = PAGE_H_PX * CALIB
        if i == 1:
            budget = (PAGE_H_PX - header_h) * CALIB

        chosen = FIT_STEPS[-1]  # 기본은 최대 축소 → 그래도 넘치면 흐름 허용
        for step in FIT_STEPS:
            _set_passage_class(page, sel, step)
            h = page.eval_on_selector(
                sel, "el => el.getBoundingClientRect().height"
            )
            if h <= budget:
                chosen = step
                break
        else:
            # compact2 로도 초과 → 축소를 풀고(빈 클래스) 자연스러운 2페이지+ 흐름
            chosen = ""

        _set_passage_class(page, sel, chosen)


def _set_passage_class(page, selector: str, step: str) -> None:
    """지문 요소의 클래스를 '.passage' + step 으로 설정."""
    cls = "passage" + (f" {step}" if step else "")
    page.eval_on_selector(
        selector, "(el, cls) => { el.className = cls; }", cls
    )


# ── run ───────────────────────────────────────────────────────

def run(input_path, out_dir, header: str = "", formats: str = "abc",
        do_translate: bool = True, theme: str = "modern",
        docname: str = "") -> List[Path]:
    """입력 → 3형식 PDF 생성. 생성된 파일 경로 리스트 반환."""
    input_path = Path(input_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] 텍스트 추출: {input_path.name}")
    raw = extract_text(input_path)

    print("[2/4] 지문 파싱")
    passages = split_passages(raw)
    if not passages:
        print("  ⚠ 지문을 찾지 못했습니다. 헤더 형식(…N번: 제목)과 원문자(①②)를 확인하세요.")
        return []
    print(f"  → 지문 {len(passages)}개, 총 문장 {sum(len(p.sentences) for p in passages)}개")

    # 한줄영어(c)만 요청하면 번역 불필요
    needs_ko = any(f in formats for f in ("a", "b"))
    if do_translate and needs_ko:
        print("[3/4] 해석 없는 문장 번역(있으면)")
        passages = translate_missing(passages)
    else:
        print("[3/4] 번역 생략")

    doc = safe_filename(docname or input_path.stem)

    print("[4/4] PDF 생성")
    produced: List[Path] = []
    for key in formats:
        entry = FORMATS.get(key)
        if not entry:
            continue
        render_fn, suffix = entry
        html_str = render_fn(passages, header_text=header, theme=theme)
        out_pdf = out_dir / f"{doc}_{suffix}.pdf"
        print(f"  · {out_pdf.name}")
        html_to_pdf(html_str, out_pdf, autofit=True)
        produced.append(out_pdf)

    print(f"완료: {len(produced)}개 PDF → {out_dir}")
    return produced


# ── CLI ───────────────────────────────────────────────────────

def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="영어 지문 → 3형식(한줄해석/한줄영어/좌지문우해석) 학습 PDF 생성기"
    )
    ap.add_argument("input", help="입력 파일 (PDF·이미지·txt)")
    ap.add_argument("--out", default="./output", help="출력 폴더 (기본 ./output)")
    ap.add_argument("--formats", default="abc",
                    help="a=한줄해석 c=한줄영어 b=좌지문우해석 (기본 abc)")
    ap.add_argument("--theme", default="modern",
                    choices=["modern", "textbook", "middle"], help="디자인 테마")
    ap.add_argument("--header", default="", help="상단 머리글(학원명·자료명 등)")
    ap.add_argument("--name", default="", help="출력 파일명(지문명). 미지정 시 입력 파일명")
    ap.add_argument("--no-translate", action="store_true", help="자동 번역 끄기")
    return ap


def main(argv=None) -> int:
    args = _build_argparser().parse_args(argv)
    produced = run(
        input_path=args.input,
        out_dir=args.out,
        header=args.header,
        formats=args.formats,
        do_translate=not args.no_translate,
        theme=args.theme,
        docname=args.name,
    )
    return 0 if produced else 1


if __name__ == "__main__":
    sys.exit(main())
