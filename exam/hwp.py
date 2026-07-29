"""HWP(한글) 파일 → 원문 텍스트 추출.

두 형식을 지원한다:
  .hwpx  신형(2010~). ZIP + XML(OWPML) → 표준 라이브러리만으로 텍스트를 뽑는다.
  .hwp   구형 OLE 바이너리(HWP5). olefile 로 BodyText 섹션을 읽어 파싱한다.

여기서는 '원문 텍스트'만 뽑고, 한글 지시문·머리글 제거와 영어 지문 분리는
ingest 의 정제 파이프라인(_clean_pdf_text)이 PDF 와 동일하게 담당한다.
"""
from __future__ import annotations

import re
import struct
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

# ── .hwpx (ZIP+XML) ─────────────────────────────────────────────────────────
# OWPML 본문 텍스트는 <hp:t> 요소에 담긴다. 네임스페이스는 무시하고 로컬명으로 매칭.
def read_hwpx(path: str | Path) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(str(path)) as z:
        names = [n for n in z.namelist()
                 if re.search(r"Contents/section\d+\.xml$", n, re.IGNORECASE)]
        if not names:  # 섹션을 못 찾으면 Contents 하위 xml 전부 시도
            names = [n for n in z.namelist()
                     if n.lower().startswith("contents/") and n.lower().endswith(".xml")]
        for name in sorted(names):
            try:
                root = ET.fromstring(z.read(name))
            except ET.ParseError:
                continue
            for el in root.iter():
                tag = el.tag.rsplit("}", 1)[-1]     # 네임스페이스 제거
                if tag == "t" and el.text:
                    parts.append(el.text)
                elif tag in ("lineBreak", "linesegarray", "p"):
                    parts.append(" ")
    return re.sub(r"[ \t]+", " ", " ".join(parts)).strip()


# ── .hwp (HWP5 OLE 바이너리) ────────────────────────────────────────────────
_HWPTAG_PARA_TEXT = 0x43           # HWPTAG_BEGIN(0x10) + 51 — 문단 텍스트 레코드
# 제어문자 크기: 1코드유닛(문단/줄바꿈 등) vs 8코드유닛(표·그림 등 인라인/확장 제어)
_CTRL_1 = {0, 10, 13, 24, 25, 26, 27, 28, 29, 30, 31}
_CTRL_8 = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}


def _iter_records(buf: bytes):
    """HWP5 레코드 스트림 → (tag_id, data) 반복."""
    i, n = 0, len(buf)
    while i + 4 <= n:
        header = struct.unpack_from("<I", buf, i)[0]
        i += 4
        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:                      # 확장 크기(다음 4바이트)
            size = struct.unpack_from("<I", buf, i)[0]
            i += 4
        yield tag_id, buf[i:i + size]
        i += size


def _decode_para_text(data: bytes) -> str:
    """PARA_TEXT 레코드(UTF-16LE + 인라인 제어문자)에서 실제 글자만 뽑는다."""
    out: list[str] = []
    j, m = 0, len(data) - 1
    while j <= m:
        code = data[j] | (data[j + 1] << 8)
        if code in _CTRL_8:
            j += 16                            # 8코드유닛 × 2바이트
            continue
        if code in _CTRL_1:
            if code in (10, 13):
                out.append(" ")
            j += 2
            continue
        out.append(chr(code))
        j += 2
    return "".join(out)


def read_hwp(path: str | Path) -> str:
    try:
        import olefile
    except ImportError as e:  # pragma: no cover
        raise ValueError("'.hwp' 처리를 위해 olefile 이 필요합니다(pip install olefile).") from e

    if not olefile.isOleFile(str(path)):
        # 구형 .hwp 가 아니면 사실 .hwpx(ZIP)일 수 있음 → 그쪽으로
        if zipfile.is_zipfile(str(path)):
            return read_hwpx(path)
        raise ValueError("HWP 파일 형식을 인식하지 못했습니다(HWP5/HWPX 아님).")

    ole = olefile.OleFileIO(str(path))
    try:
        # 압축 여부: FileHeader 32바이트 뒤 properties 의 bit0
        compressed = True
        if ole.exists("FileHeader"):
            head = ole.openstream("FileHeader").read()
            if len(head) >= 40:
                compressed = bool(struct.unpack_from("<I", head, 36)[0] & 0x01)

        # BodyText/Section0, Section1, … 순서대로
        sections = sorted(
            (e for e in ole.listdir()
             if len(e) == 2 and e[0].lower() == "bodytext"
             and re.match(r"section\d+$", e[1], re.IGNORECASE)),
            key=lambda e: int(re.search(r"\d+", e[1]).group()),
        )
        texts: list[str] = []
        for entry in sections:
            raw = ole.openstream(entry).read()
            if compressed:
                try:
                    raw = zlib.decompress(raw, -15)   # raw deflate
                except zlib.error:
                    pass
            for tag_id, data in _iter_records(raw):
                if tag_id == _HWPTAG_PARA_TEXT:
                    texts.append(_decode_para_text(data))
        return re.sub(r"[ \t]+", " ", " ".join(texts)).strip()
    finally:
        ole.close()


def read_hwp_any(path: str | Path) -> str:
    """확장자로 .hwp/.hwpx 를 구분해 원문 텍스트를 반환."""
    p = Path(path)
    if p.suffix.lower() == ".hwpx":
        return read_hwpx(p)
    return read_hwp(p)
