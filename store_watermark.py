#!/usr/bin/env python3
"""PDF에 구매자 표시를 새겨 넣습니다.

파일을 받는 순간 그 파일에만 **구매자 이름·이메일·주문번호**가 박힙니다.
막을 수는 없지만, 카페나 단톡방에 올리면 누가 올렸는지 바로 드러납니다.
자료 유출을 줄이는 가장 확실한 방법입니다.

- 원본 파일은 건드리지 않습니다. 받으실 때 그 자리에서 새겨 보냅니다.
- PDF 만 새깁니다. ZIP·한글 파일은 그대로 나갑니다.
- 무료 자료실 자료에는 새기지 않습니다. 그건 퍼질수록 좋으니까요.
- 라이브러리가 없거나 파일이 이상하면 조용히 원본을 그대로 보냅니다.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
FONT_WOFF = ROOT / "store_static" / "fonts" / "NanumSquareRoundR.woff"
FONT_CACHE = ROOT / "store_data" / ".cache" / "watermark.ttf"
FONT_NAME = "OrticaWatermark"

try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
    AVAILABLE = True
except ImportError:                                    # 없으면 원본을 그대로 보냅니다
    AVAILABLE = False

_font_ready: bool | None = None


def _korean_font() -> str:
    """한글이 찍히는 글꼴 이름. 준비가 안 되면 Helvetica 로 물러섭니다.

    사이트가 이미 갖고 있는 나눔스퀘어라운드(woff)를 한 번만 ttf 로 바꿔 두고 씁니다.
    """
    global _font_ready
    if _font_ready is False:
        return "Helvetica"
    if _font_ready is True:
        return FONT_NAME
    try:
        if not FONT_CACHE.exists():
            from fontTools.ttLib import TTFont as FTFont
            FONT_CACHE.parent.mkdir(parents=True, exist_ok=True)
            face = FTFont(str(FONT_WOFF))
            face.flavor = None
            face.save(str(FONT_CACHE))
        pdfmetrics.registerFont(RLTTFont(FONT_NAME, str(FONT_CACHE)))
        _font_ready = True
        return FONT_NAME
    except Exception as exc:                           # 글꼴이 없어도 영문으로는 찍힙니다
        log.info("워터마크 한글 글꼴을 준비하지 못했습니다: %s", exc)
        _font_ready = False
        return "Helvetica"


def _ascii_only(text: str) -> str:
    return "".join(ch for ch in text if ord(ch) < 128).strip(" ·")


def _stamp_page(width: float, height: float, footer: str, diagonal: str) -> "PdfReader":
    """한 쪽 크기에 맞는 도장 PDF 를 만듭니다."""
    font = _korean_font()
    if font == "Helvetica":                            # 한글이 안 찍히면 영문만 남깁니다
        footer, diagonal = _ascii_only(footer), _ascii_only(diagonal)

    buf = io.BytesIO()
    page = canvas.Canvas(buf, pagesize=(width, height))

    if diagonal:
        page.saveState()
        page.setFillColorRGB(0.10, 0.42, 0.29)
        page.setFillAlpha(0.07)
        page.setFont(font, min(30, max(14, width / 20)))
        page.translate(width / 2, height / 2)
        page.rotate(32)
        page.drawCentredString(0, 0, diagonal)
        page.restoreState()

    if footer:
        page.setFillColorRGB(0.42, 0.45, 0.43)
        page.setFillAlpha(0.85)
        page.setFont(font, 7)
        page.drawString(26, 15, footer)

    page.showPage()
    page.save()
    buf.seek(0)
    return PdfReader(buf)


def stamp(path: Path, footer: str, diagonal: str = "") -> bytes | None:
    """PDF 모든 쪽에 표시를 새겨 바이트로 돌려줍니다.

    새기지 못하면 None 을 돌려줍니다. 부르는 쪽에서 원본을 그대로 보내면 됩니다.
    """
    if not AVAILABLE or path.suffix.lower() != ".pdf":
        return None
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:                        # 암호가 걸린 PDF 는 건드리지 않습니다
            return None
        writer = PdfWriter()
        cache: dict[tuple, object] = {}
        for page in reader.pages:
            box = page.mediabox
            size = (round(float(box.width), 1), round(float(box.height), 1))
            if size not in cache:
                cache[size] = _stamp_page(size[0], size[1], footer, diagonal).pages[0]
            page.merge_page(cache[size])
            writer.add_page(page)
        # 합치면 내용이 풀린 채로 남습니다. 다시 눌러 담지 않으면 파일이 몇 배로 커집니다.
        # (writer 에 담긴 뒤에만 눌러 담을 수 있습니다)
        for page in writer.pages:
            try:
                page.compress_content_streams()
            except Exception:
                break
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
    except Exception as exc:                           # 이상한 파일이어도 판매는 멈추지 않습니다
        log.warning("워터마크를 넣지 못했습니다 (%s): %s", path.name, exc)
        return None
