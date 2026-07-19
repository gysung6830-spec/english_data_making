"""스캔 PDF·사진 → 텍스트.

우선순위:
  1) Claude 비전 OCR — ANTHROPIC_API_KEY 있을 때. 원문자/영어/한글 정확도 최고.
  2) Tesseract 폴백    — 키 없을 때. kor+eng (없으면 eng).

스캔 여부는 페이지당 추출 글자 수로 판별한다(평균 40자 미만 → 스캔).
"""
from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import List

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

_VISION_MODEL = "claude-sonnet-5"

_VISION_PROMPT = (
    "이 이미지는 영어 지문 학습 자료입니다. 화면에 보이는 텍스트를 있는 그대로 "
    "정확히 옮겨 적으세요. 규칙:\n"
    "1) 문제 번호 헤더가 있으면 '[고3] 2026년 5월 - 26번: 제목' 형태로 한 줄로 적으세요.\n"
    "2) 각 문장은 원문자(①②③…)로 시작하게 하세요. 원문자를 (1),1) 등으로 바꾸지 마세요.\n"
    "3) 영어 원문과 한글 해석이 모두 있으면 둘 다 옮기세요. 한글 해석은 해당 문장 "
    "바로 아래 줄에 같은 원문자로 적으세요.\n"
    "4) 절대 임의로 번역하거나 문장을 지어내지 마세요. 보이는 것만 옮깁니다.\n"
    "5) 설명·머리말 없이 옮긴 텍스트만 출력하세요."
)


# ── 스캔 판별 ─────────────────────────────────────────────────

def is_scanned_pdf(path, min_chars_per_page: int = 40) -> bool:
    """디지털 텍스트가 거의 없으면(페이지 평균 40자 미만) 스캔으로 간주."""
    try:
        import pdfplumber
    except ImportError:
        return False
    total = 0
    pages = 0
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                pages += 1
                txt = page.extract_text() or ""
                total += len(txt.strip())
    except Exception:
        return False
    if pages == 0:
        return False
    return (total / pages) < min_chars_per_page


# ── 이미지 로딩 ───────────────────────────────────────────────

def _pdf_to_images(path) -> List[bytes]:
    """PDF → 페이지별 PNG 바이트."""
    from pdf2image import convert_from_path
    images = convert_from_path(str(path), dpi=200)
    out = []
    import io
    for im in images:
        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="PNG")
        out.append(buf.getvalue())
    return out


def _load_image_bytes(path) -> List[bytes]:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        return _pdf_to_images(p)
    return [p.read_bytes()]


# ── Claude 비전 OCR ───────────────────────────────────────────

def _vision_ocr(images: List[bytes], verbose: bool = True) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    out_pages: List[str] = []
    for i, img in enumerate(images, start=1):
        if verbose:
            print(f"  [vision OCR] page {i}/{len(images)}")
        b64 = base64.standard_b64encode(img).decode()
        resp = client.messages.create(
            model=_VISION_MODEL,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/png", "data": b64}},
                    {"type": "text", "text": _VISION_PROMPT},
                ],
            }],
        )
        text = "".join(
            b.text for b in resp.content if getattr(b, "type", "") == "text"
        )
        out_pages.append(text.strip())
    return "\n\n".join(out_pages)


# ── Tesseract 폴백 ────────────────────────────────────────────

# 원문자 오인식 복원용: (1) / 1) / (1 등 → 원문자
_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def _restore_circled(text: str) -> str:
    def repl(m):
        n = int(m.group(1))
        if 1 <= n <= 20:
            return _CIRCLED[n - 1]
        return m.group(0)
    # 줄 시작의 (1) 1) [1] 1. 형태를 원문자로
    text = re.sub(r"(?m)^\s*[\(\[]?(\d{1,2})[\)\].]\s*", lambda m: _restore_circled_line(m), text)
    return text


def _restore_circled_line(m) -> str:
    n = int(m.group(1))
    if 1 <= n <= 20:
        return _CIRCLED[n - 1] + " "
    return m.group(0)


def _tesseract_langs() -> str:
    try:
        import pytesseract
        langs = pytesseract.get_languages(config="")
        if "kor" in langs:
            return "kor+eng"
    except Exception:
        pass
    return "eng"


def _tesseract_ocr(images: List[bytes], verbose: bool = True) -> str:
    import io

    import pytesseract
    from PIL import Image

    lang = _tesseract_langs()
    if verbose:
        print(f"  [tesseract] lang={lang}")
    out_pages: List[str] = []
    for i, img in enumerate(images, start=1):
        if verbose:
            print(f"  [tesseract OCR] page {i}/{len(images)}")
        im = Image.open(io.BytesIO(img))
        text = pytesseract.image_to_string(im, lang=lang)
        out_pages.append(_restore_circled(text).strip())
    return "\n\n".join(out_pages)


# ── 진입점 ────────────────────────────────────────────────────

def ocr_file(path, verbose: bool = True) -> str:
    """스캔 PDF·사진 → 텍스트. 엔진 자동 선택."""
    images = _load_image_bytes(path)
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _vision_ocr(images, verbose=verbose)
        except Exception as e:  # 비전 실패 시 폴백
            if verbose:
                print(f"  [vision OCR 실패 → tesseract 폴백] {e}")
    return _tesseract_ocr(images, verbose=verbose)
