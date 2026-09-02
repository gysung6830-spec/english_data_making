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
    from .hwp import HWP_EXTS, extract_hwp_text
    from .ocr import IMAGE_EXTS, is_scanned_pdf, ocr_file
    from .chunker import chunk_sentences
    from .parser import Passage, split_passages
    from .pdfparse import pdf_to_passages, strip_side_margins
    from .renderer import (render_format_a, render_format_b, render_format_c,
                          render_format_d)
    from .segmenter import segment_passages
    from .serialize import load_passages_json, passages_to_json
    from .translator import translate_missing
    from .vocab import extract_vocab
except ImportError:  # 스크립트로 직접 실행할 때(python main.py)
    from chunker import chunk_sentences
    from hwp import HWP_EXTS, extract_hwp_text
    from ocr import IMAGE_EXTS, is_scanned_pdf, ocr_file
    from parser import Passage, split_passages
    from pdfparse import pdf_to_passages, strip_side_margins
    from renderer import (render_format_a, render_format_b, render_format_c,
                         render_format_d)
    from segmenter import segment_passages
    from serialize import load_passages_json, passages_to_json
    from translator import translate_missing
    from vocab import extract_vocab

# ── auto-fit 상수 ─────────────────────────────────────────────
# A4 @96dpi
A4_W_PX = 794
A4_H_PX = 1123
# 본문 가용 높이 = A4(297mm) - 상하 여백 20mm씩 = 257mm
PAGE_H_PX = 257 * 96 / 25.4          # ≈ 971px
CALIB = 0.90                          # measure ↔ 실제 PDF 오차 흡수(넘침 방지)
# 압축 후 남는 공간을 문장 간격으로 분배해 페이지를 채울 때의 목표 높이 비율
# (측정↔실제 PDF 오차를 감안한 안전값. 넘치면 2페이지가 되므로 보수적으로.)
FILL_CALIB = 0.89                     # 페이지 가용 높이의 이 비율까지 채움
FIT_STEPS = ["", "compact", "compact2", "compact3"]

# 하단 왼쪽 저작권 문구 + 하단 오른쪽 페이지 번호
FOOTER_TEXT = "©2026.Ortica영어.All rights reserved"
_FOOTER_FONT = (
    "'NanumSquareRound','나눔스퀘어라운드','NanumSquare',"
    "'NanumGothic','Malgun Gothic',sans-serif"
)

# 형식 키 → (렌더 함수, 파일명 접미사)
FORMATS = {
    "a": (render_format_a, "한줄해석"),
    "c": (render_format_c, "한줄영어"),
    "b": (render_format_b, "좌지문우해석"),
    "d": (render_format_d, "직독직해"),
}

_FNAME_BAD = re.compile(r'[\\/:*?"<>|]')


def safe_filename(name: str) -> str:
    """파일명 금지문자를 _ 로 치환."""
    return _FNAME_BAD.sub("_", (name or "").strip()) or "지문"


_RANGE_RE = re.compile(r"(\d+)\s*[~∼\-]\s*(\d+)\s*번")
# 라벨 '끝'의 문항번호 토큰('…N번' 또는 '…N~M번'). 앞의 '[고3] 2026년 6월 -'
# 같은 접두어 숫자에 오인되지 않도록 반드시 끝(번으로 종료)만 잡는다.
_QNUM_END_RE = re.compile(r"(\d{1,3})(?:\s*[~∼\-]\s*(\d{1,3}))?\s*번\s*$")


def _label_qspan(label: str):
    """라벨 끝 문항번호에서 (시작, 끝, match) 반환. 없으면 None."""
    m = _QNUM_END_RE.search(label or "")
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return a, b, m


def _label_span(label: str) -> int:
    """라벨이 장문 범위(N~M번)면 문항 수(M-N+1), 아니면 1."""
    q = _label_qspan(label)
    if q and q[1] >= q[0]:
        return q[1] - q[0] + 1
    return 1


def _label_num(label: str):
    """라벨의 (단일) 문항번호 정수. '…N번' → N, 범위나 형식 밖이면 None."""
    q = _label_qspan(label)
    return q[0] if (q and q[0] == q[1]) else None


# 모의고사 판별 키워드(파일명·제목·원문에 등장)
_MOCK_KEYWORDS = re.compile(
    r"(모의고사|모의평가|모평|학력평가|학평|전국연합|수능|수학능력|"
    r"대학수학능력|교육청|평가원)"
)
_RANGE_LABEL_RE = re.compile(r"\d+\s*[~∼]\s*\d+\s*번")


def is_mock_exam(passages: List[Passage], docname: str = "") -> bool:
    """이 자료가 '모의고사'인지 판별.

    모의고사일 때만 27·28번(실용문)을 제외해야 하므로(교재 등은 제외 안 함),
    다음 신호 중 하나라도 있으면 모의고사로 본다:
      1) 파일명/지문 제목/원문에 모의고사 관련 키워드(학력평가·수능·교육청 등)
      2) 장문 범위 라벨(41~42번, 43~45번 등) — 모의고사·수능 고유 구조
    """
    parts = [docname or ""]
    for p in passages:
        parts.append(p.title or "")
        parts.append(getattr(p, "raw", "") or "")
        for s in p.sentences[:2]:  # 앞부분 문장까지만 훑음
            parts.append(s.ko or "")
    if _MOCK_KEYWORDS.search(" ".join(parts)):
        return True
    if any(_RANGE_LABEL_RE.search(p.label or "") for p in passages):
        return True
    return False


def drop_practical_items(passages: List[Passage],
                         nums=(27, 28)) -> List[Passage]:
    """실용문(안내문·광고) 문항을 제외한다(기본 27·28번).

    ※ 호출 전에 is_mock_exam()으로 모의고사인지 반드시 확인할 것.
    문항 번호가 실제 시험 번호와 맞도록 renumber_passages 이후에 호출한다.
    범위(장문) 라벨은 대상이 아니며, 형식 밖 라벨도 건드리지 않는다.
    """
    drop = set(nums)
    return [p for p in passages if _label_num(p.label) not in drop]


def _label_lead(label: str):
    """라벨 끝 문항번호의 시작값(단일 'N번'→N, 범위 'N~M번'→N). 없으면 None.
    '[고3] 2026년 6월 - 18번' 같은 접두어 숫자는 무시하고 문항번호만 본다."""
    q = _label_qspan(label)
    return q[0] if q else None


def _shift_label(label: str, offset: int) -> str:
    """라벨 끝 문항번호만 offset 만큼 이동. 접두어(고3·연도 등)는 건드리지 않는다."""
    q = _label_qspan(label)
    if not q:
        return label
    a, b, m = q
    new = f"{a + offset}~{b + offset}번" if b != a else f"{a + offset}번"
    return label[:m.start()] + new


def renumber_passages(passages: List[Passage], start_no) -> List[Passage]:
    """문항 시작 번호에 맞춰 라벨을 다시 매긴다.

    - 숫자 라벨이 있으면 '오프셋 이동'(첫 지문 기준)으로 기존 간격·범위를 보존한다.
      예) 첫 지문이 18번이고 시작 18 → offset 0 → 그대로.
      이렇게 해야 27·28번이 이미 빠진 자료를 재입력해도 번호가 밀리지 않는다.
    - 숫자 라벨이 전혀 없으면(번호 없는 자료) 시작번호부터 순차 부여한다.
    start_no 가 None/빈값이면 그대로 둔다(파일에서 인식한 번호 유지).
    """
    if start_no in (None, ""):
        return passages
    try:
        start = int(start_no)
    except (TypeError, ValueError):
        return passages

    first = next((_label_lead(p.label) for p in passages
                  if _label_lead(p.label) is not None), None)
    if first is not None:
        offset = start - first
        if offset:
            for p in passages:
                if _label_lead(p.label) is not None:
                    p.label = _shift_label(p.label, offset)
        return passages

    # 숫자 라벨이 전혀 없는 경우에만 순차 부여
    cur = start
    for p in passages:
        span = _label_span(p.label)
        p.label = f"{cur}~{cur + span - 1}번" if span >= 2 else f"{cur}번"
        cur += span
    return passages


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
                page = strip_side_margins(page)
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


def extract_passages(path, api_key: str = None) -> List[Passage]:
    """입력 종류에 맞춰 '깨끗한 지문 리스트'로 정규화.

    어떤 형식이든 결과가 일정하도록:
      - txt / 이미지 / 스캔 PDF → 텍스트(또는 OCR) → 텍스트 파서
      - 디지털 PDF → 표 인식 파서와 텍스트 파서를 모두 돌려 '더 좋은' 결과 선택.
        (테두리 선을 표로 오인해 표 파서가 엉뚱한 결과를 내는 경우 방지)
    api_key 는 OCR(비전)에 쓰인다(스캔·사진일 때).
    """
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".json":
        # 이미 분석된 ORTICA JSON → 재분석 없이 그대로 로드(API 비용 없음)
        return load_passages_json(p)

    if suffix == ".txt":
        return split_passages(p.read_text(encoding="utf-8", errors="replace"))

    if suffix in HWP_EXTS:
        return split_passages(extract_hwp_text(p))

    if suffix in IMAGE_EXTS:
        return split_passages(ocr_file(p, api_key=api_key))

    if suffix == ".pdf":
        if is_scanned_pdf(p):
            return split_passages(ocr_file(p, api_key=api_key))
        # 표 파서(2단 표용)와 텍스트 파서를 모두 돌려 더 나은 결과를 채택
        table_passages = pdf_to_passages(p)
        text_passages = split_passages(extract_text(p))
        return _pick_better(table_passages, text_passages)

    # 알 수 없는 확장자
    return split_passages(extract_text(p))


def _passage_score(passages) -> tuple:
    """파싱 품질 점수. (영어가 든 문장 수, 총 문장 수) — 클수록 좋음."""
    if not passages:
        return (-1, -1)
    n_en = sum(1 for p in passages for s in p.sentences
               if s.en and re.search(r"[A-Za-z]", s.en))
    n_sent = sum(len(p.sentences) for p in passages)
    return (n_en, n_sent)


def _pick_better(table_passages, text_passages):
    """표 파서 vs 텍스트 파서 결과 중 품질 점수가 높은 쪽 선택(동점이면 표)."""
    if _passage_score(table_passages) >= _passage_score(text_passages):
        return table_passages or text_passages or []
    return text_passages


# ── auto-fit PDF 빌더 ─────────────────────────────────────────

def _find_chromium():
    """미리 설치된 Chromium 실행 파일을 탐색(playwright 기본 브라우저 부재 시)."""
    import glob
    roots = [
        os.environ.get("PLAYWRIGHT_BROWSERS_PATH"),
        "/opt/pw-browsers",
        os.path.expanduser("~/.cache/ms-playwright"),
    ]
    patterns = [
        "chromium-*/chrome-linux/chrome",
        "chromium_headless_shell-*/chrome-linux/headless_shell",
        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    ]
    for root in roots:
        if not root:
            continue
        for pat in patterns:
            hits = sorted(glob.glob(os.path.join(root, pat)))
            if hits:
                return hits[-1]
    return None


def _launch_chromium(pw):
    """Chromium 실행. env var 지정 → 기본 실행 → 미리 설치본 자동 탐색 순."""
    args = ["--no-sandbox"]
    exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if exe:
        return pw.chromium.launch(executable_path=exe, args=args)
    try:
        return pw.chromium.launch(args=args)
    except Exception:
        # playwright 기본 브라우저가 없으면(예: 컨테이너) 설치본을 찾아 재시도
        found = _find_chromium()
        if found:
            return pw.chromium.launch(executable_path=found, args=args)
        raise


def html_to_pdf(html_str: str, out_pdf, autofit: bool = True,
                fill_page: bool = False) -> None:
    """Playwright(Chromium)로 HTML 렌더 → auto-fit 축소 → A4 PDF 출력.

    fill_page=False(기본): 한 페이지로 압축만 하고 하단 여백은 그대로 둔다.
    True: 남는 여백을 문장 간격에 나눠 페이지를 꽉 채운다.
    """
    from playwright.sync_api import sync_playwright

    out_pdf = str(out_pdf)

    with sync_playwright() as pw:
        browser = _launch_chromium(pw)
        page = browser.new_page(viewport={"width": A4_W_PX, "height": A4_H_PX})
        page.set_content(html_str, wait_until="networkidle")

        if autofit:
            _apply_autofit(page, fill_page=fill_page)

        # 하단 왼쪽=저작권, 하단 오른쪽=페이지 번호 (모든 페이지 반복)
        # 푸터 템플릿은 본문 CSS를 상속받지 않으므로 폰트를 여기에도 임베드.
        try:
            from .themes import _font_face_css
        except ImportError:
            from themes import _font_face_css
        footer_font_css = f'<style>{_font_face_css()}</style>'
        footer_template = (
            footer_font_css +
            f'<div style="width:100%; box-sizing:border-box; '
            f'padding:0 18mm; font-family:{_FOOTER_FONT}; font-size:11px; '
            f'color:#000000; display:flex; justify-content:space-between; '
            f'align-items:center;">'
            f'<span>{FOOTER_TEXT}</span>'
            f'<span class="pageNumber"></span>'
            f'</div>'
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


def _apply_autofit(page, fill_page: bool = False) -> None:
    """각 지문 블록의 실제 렌더 높이를 재어 알맞은 축소 클래스를 확정한다.

    fill_page=True 이면 압축 후 남는 세로 여백을 문장 사이 간격에 고르게 나눠
    페이지를 위→아래로 꽉 채운다. False(기본)면 문장은 기본 간격 그대로 위쪽에
    모이고 하단에 자연스러운 여백이 남는다. (한 페이지 압축 자체는 항상 적용.)
    """
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
        # 장문(범위 라벨)은 압축 예외 → 자연스러운 2페이지+ 흐름
        is_long = page.eval_on_selector(
            sel, "el => el.classList.contains('long')"
        )
        if is_long:
            _set_passage_class(page, sel, "", keep_long=True)
            continue

        budget = PAGE_H_PX * FILL_CALIB
        if i == 1:
            budget = (PAGE_H_PX - header_h) * FILL_CALIB

        # 1) 한 페이지에 들어가는 가장 약한 축소 단계 선택(안 되면 최대 축소).
        chosen = FIT_STEPS[-1]
        for step in FIT_STEPS:
            _set_passage_class(page, sel, step)
            h = page.eval_on_selector(
                sel, "el => el.getBoundingClientRect().height"
            )
            if h <= budget:
                chosen = step
                break
        _set_passage_class(page, sel, chosen)

        # 2) (옵션) 남는 공간을 문장 사이 간격에 고르게 나눠 페이지를 '채운다'.
        #    기본(fill_page=False)은 채우지 않고 하단 여백을 그대로 둔다.
        if not fill_page:
            continue
        h = page.eval_on_selector(
            sel, "el => el.getBoundingClientRect().height"
        )
        slack = budget - h
        if slack > 8:
            page.eval_on_selector(
                sel,
                "(el, slack) => {"
                "  const items = el.querySelectorAll('.sent');"
                "  if (!items.length) return;"
                "  const extra = slack / items.length;"
                "  items.forEach(s => {"
                "    const m = parseFloat(getComputedStyle(s).marginBottom)||0;"
                "    s.style.marginBottom = (m + extra) + 'px';"
                "  });"
                "}",
                slack,
            )


def _set_passage_class(page, selector: str, step: str,
                       keep_long: bool = False) -> None:
    """지문 요소의 클래스를 '.passage'(+long)(+step) 으로 설정."""
    cls = "passage"
    if keep_long:
        cls += " long"
    if step:
        cls += f" {step}"
    page.eval_on_selector(
        selector, "(el, cls) => { el.className = cls; }", cls
    )


# ── run ───────────────────────────────────────────────────────

def run(input_path, out_dir, header: str = "", formats: str = "abc",
        do_translate: bool = True, theme: str = "modern",
        docname: str = "", api_key: str = None, start_no=None,
        drop_practical: bool = True, fill_page: bool = False) -> List[Path]:
    """입력 → 3형식 PDF 생성. 생성된 파일 경로 리스트 반환."""
    input_path = Path(input_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] 입력 파싱: {input_path.name}")
    passages = extract_passages(input_path, api_key=api_key)

    print("[2/4] 지문 정규화")
    if not passages:
        print("  ⚠ 지문을 찾지 못했습니다. 헤더 형식(…N번: 제목)과 원문자(①②)를 확인하세요.")
        return []

    # 문항 시작 번호 지정 시 라벨 재부여(시작번호부터 자동 증가)
    passages = renumber_passages(passages, start_no)
    # 모의고사일 때만 실용문(27·28번) 제외. 실제 문항번호가 매겨진 뒤 제거.
    if drop_practical and is_mock_exam(passages, docname):
        before = len(passages)
        passages = drop_practical_items(passages)
        if len(passages) < before:
            print(f"  → 모의고사 판정 · 27·28번(실용문) 제외: {before}개 → {len(passages)}개")
    elif drop_practical:
        print("  → 모의고사 아님(또는 미판정) → 27·28번 제외 안 함")
    print(f"  → 지문 {len(passages)}개, 총 문장 {sum(len(p.sentences) for p in passages)}개")

    # 분석 단계는 '이미 있는 항목은 건너뛴다'(각 함수가 idempotent).
    # JSON 재입력이라도 누락분(예: 새로 분리된 장문 문장의 청크)은 채운다.
    #   - 완성된 자료 재입력 + 키 없음 → 모두 no-op(비용 0)
    #   - 일부 누락 + 키 있음 → 누락분만 생성(비용은 그만큼)
    is_json_input = input_path.suffix.lower() == ".json"
    if is_json_input:
        print("[3/4] JSON 재입력 — 이미 분석된 항목 재사용, 누락분만 채움(키 있을 때)")
    # 번호 없는 통짜 지문(지문 연습하기 등)을 AI로 문장 분리(키 있으면)
    if any(not p.sentences and p.raw for p in passages):
        print("      번호 없는 지문 문장 분리(키 있으면)")
        passages = segment_passages(passages, api_key=api_key)
    needs_ko = any(f in formats for f in ("a", "b", "d"))
    if do_translate and needs_ko:
        print("[3/4] 해석 없는 문장 번역(키 있으면)")
        passages = translate_missing(passages, api_key=api_key)
    print("      어휘 리스트 추출(키 있으면)")
    passages = extract_vocab(passages, api_key=api_key)
    if "d" in formats:
        print("      직독직해 청크 생성(키 있으면)")
        passages = chunk_sentences(passages, api_key=api_key)

    disp_name = (docname or input_path.stem).strip()   # 뱃지 표시용(원본 이름)
    doc = safe_filename(docname or input_path.stem)      # 파일 저장용(치환)

    # 재사용용 분석 JSON 저장(제목만 바꿔 재생성할 때 이 파일을 다시 입력)
    json_path = out_dir / f"{doc}_ORTICA.json"
    json_path.write_text(passages_to_json(passages, docname=disp_name),
                         encoding="utf-8")
    print(f"      분석 JSON 저장: {json_path.name} (재편집·재생성용)")

    print("[4/4] PDF 생성")
    produced: List[Path] = []
    for key in formats:
        entry = FORMATS.get(key)
        if not entry:
            continue
        render_fn, suffix = entry
        html_str = render_fn(passages, header_text=header, theme=theme,
                             doc_name=disp_name)
        out_pdf = out_dir / f"{doc}_{suffix}.pdf"
        print(f"  · {out_pdf.name}")
        html_to_pdf(html_str, out_pdf, autofit=True, fill_page=fill_page)
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
                    help="a=한줄해석 c=한줄영어 b=좌지문우해석 d=직독직해 (기본 abc)")
    ap.add_argument("--theme", default="modern",
                    choices=["modern", "textbook", "middle"], help="디자인 테마")
    ap.add_argument("--header", default="", help="상단 머리글(학원명·자료명 등)")
    ap.add_argument("--name", default="", help="출력 파일명(지문명). 미지정 시 입력 파일명")
    ap.add_argument("--no-translate", action="store_true", help="자동 번역 끄기")
    ap.add_argument("--start-no", default="",
                    help="문항 시작 번호. 지정 시 지문마다 시작번호부터 1씩 증가")
    ap.add_argument("--keep-2728", action="store_true",
                    help="모의고사 27·28번(실용문) 제외 안 함(기본은 제외)")
    ap.add_argument("--fill-page", action="store_true",
                    help="남는 여백을 문장 간격에 나눠 페이지를 꽉 채움"
                         "(기본은 꺼짐: 하단 여백 유지)")
    ap.add_argument("--api-key", default="",
                    help="Claude API 키(영어만 있는 자료 자동 번역·비전 OCR용). "
                         "미지정 시 환경변수 ANTHROPIC_API_KEY 사용")
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
        api_key=args.api_key or None,
        start_no=args.start_no or None,
        drop_practical=not args.keep_2728,
        fill_page=args.fill_page,
    )
    return 0 if produced else 1


if __name__ == "__main__":
    sys.exit(main())
