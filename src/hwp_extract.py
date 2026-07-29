"""HWP(한글) 파일 텍스트 추출 — 외부 도구 없이 순수 파이썬으로 처리.

지원 형식:
  - HWP 5.x 바이너리(.hwp)  : OLE 복합 파일. BodyText/Section* 스트림을
                              (필요 시) raw-deflate 해제한 뒤 레코드를 파싱해
                              문단 텍스트(HWPTAG_PARA_TEXT)만 뽑는다.
  - HWPX(.hwpx)            : ZIP(OWPML). Contents/section*.xml 의 <hp:t> 텍스트를 모은다.

의존성: olefile (바이너리 .hwp 용). .hwpx 는 표준 라이브러리만 사용.
"""
from __future__ import annotations

import html
import re
import struct
import zipfile
import zlib
from pathlib import Path

# ── HWP 5.0 본문 레코드/제어문자 상수 ───────────────────────────────
_HWPTAG_BEGIN = 0x10
_HWPTAG_PARA_TEXT = _HWPTAG_BEGIN + 51   # 67: 문단 텍스트

# 문단 텍스트 안의 제어 문자(유니코드 코드포인트) 폭 분류
_CTRL_CHAR = {0, 10, 13, 24, 25, 26, 27, 28, 29, 30, 31}   # 1글자(2바이트)
_CTRL_INLINE = {4, 5, 6, 7, 8, 9, 19, 20}                  # 8글자(16바이트)
_CTRL_EXTENDED = {1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23}  # 8글자


def is_hwp(path: str | Path) -> bool:
    return Path(path).suffix.lower() in {".hwp", ".hwpx"}


def extract_hwp_text(path: str | Path) -> str:
    """.hwp/.hwpx -> 본문 텍스트. 형식은 파일 시그니처로 자동 판별."""
    path = Path(path)
    with path.open("rb") as f:
        head = f.read(8)
    if head[:2] == b"PK":                       # ZIP => HWPX
        return _extract_hwpx(path)
    if head[:4] == b"\xd0\xcf\x11\xe0":         # OLE => HWP 5.x 바이너리
        return _extract_hwp5(path)
    # 확장자로 한 번 더 시도
    if path.suffix.lower() == ".hwpx":
        return _extract_hwpx(path)
    return _extract_hwp5(path)


# ── HWPX (.hwpx) ────────────────────────────────────────────────────
def _extract_hwpx(path: Path) -> str:
    with zipfile.ZipFile(str(path)) as z:
        names = [n for n in z.namelist()
                 if re.match(r"Contents/section\d+\.xml$", n, re.I)]
        names.sort(key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        paras: list[str] = []
        for n in names:
            xml = z.read(n).decode("utf-8", "ignore")
            # 문단(<hp:p …> … </hp:p>) 단위로 <hp:t> 텍스트를 모은다.
            for pblock in re.findall(r"<hp:p\b.*?</hp:p>", xml, re.S):
                ts = re.findall(r"<hp:t\b[^>]*>(.*?)</hp:t>", pblock, re.S)
                line = "".join(html.unescape(re.sub(r"<[^>]+>", "", t)) for t in ts)
                paras.append(line)
    return "\n".join(paras).strip()


# ── HWP 5.x 바이너리 (.hwp) ─────────────────────────────────────────
def _iter_records(data: bytes):
    """섹션 스트림(압축 해제 후)에서 (tag_id, level, payload) 레코드를 순회."""
    i, n = 0, len(data)
    while i + 4 <= n:
        header = struct.unpack_from("<I", data, i)[0]
        i += 4
        tag_id = header & 0x3FF
        level = (header >> 10) & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:                      # 확장 크기(다음 4바이트)
            if i + 4 > n:
                break
            size = struct.unpack_from("<I", data, i)[0]
            i += 4
        payload = data[i:i + size]
        i += size
        yield tag_id, level, payload


def _para_text(payload: bytes) -> str:
    """HWPTAG_PARA_TEXT 페이로드(UTF-16LE + 제어문자) -> 순수 텍스트."""
    m = len(payload) // 2
    if m == 0:
        return ""
    chars = struct.unpack_from("<%dH" % m, payload, 0)
    out: list[str] = []
    i = 0
    while i < m:
        c = chars[i]
        if c in _CTRL_INLINE or c in _CTRL_EXTENDED:
            i += 8                              # 인라인/확장 제어문자: 8글자 차지
            continue
        if c in _CTRL_CHAR:
            if c in (10, 13):
                out.append("\n")
            i += 1
            continue
        out.append(chr(c))
        i += 1
    return "".join(out)


def _extract_hwp5(path: Path) -> str:
    import olefile

    ole = olefile.OleFileIO(str(path))
    try:
        # 압축 여부: FileHeader 의 properties(오프셋 36, uint32) bit0
        compressed = True
        if ole.exists("FileHeader"):
            fh = ole.openstream("FileHeader").read()
            if len(fh) >= 40:
                props = struct.unpack_from("<I", fh, 36)[0]
                compressed = bool(props & 0x01)
        # BodyText/Section0, Section1 … 순서대로
        sections = []
        for entry in ole.listdir():
            if len(entry) == 2 and entry[0] == "BodyText" and entry[1].lower().startswith("section"):
                num = re.search(r"(\d+)", entry[1])
                sections.append((int(num.group(1)) if num else 0, entry))
        sections.sort(key=lambda x: x[0])

        paras: list[str] = []
        for _, entry in sections:
            raw = ole.openstream(entry).read()
            if compressed:
                try:
                    raw = zlib.decompress(raw, -15)   # raw deflate
                except zlib.error:
                    pass
            for tag_id, _level, payload in _iter_records(raw):
                if tag_id == _HWPTAG_PARA_TEXT:
                    paras.append(_para_text(payload))
        return "\n".join(paras).strip()
    finally:
        ole.close()
