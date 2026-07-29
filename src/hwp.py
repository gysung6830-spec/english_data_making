"""HWP / HWPX 파일에서 '글자가 살아있는' 본문 텍스트를 추출.

- .hwpx : 내부가 ZIP+XML 이라 정확히 텍스트를 뽑는다.
- .hwp  : OLE 복합 파일. BodyText/Section* 스트림(필요시 zlib 압축 해제)에서
          PARA_TEXT 레코드를 파싱해 UTF-16LE 텍스트를 뽑는다.

지문이 '이미지로 박혀 있는' HWP 는 여기서 뽑히지 않는다(그 경우 vision 필요).
"""
from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

HWP_EXTS = {".hwp", ".hwpx"}


def is_hwp(path: str | Path) -> bool:
    return Path(path).suffix.lower() in HWP_EXTS


# ---------------------------------------------------------------------------
# HWPX (신형, ZIP + XML)
# ---------------------------------------------------------------------------
def _localname(tag: str) -> str:
    return tag.split("}")[-1]


def extract_hwpx_text(path: str | Path) -> str:
    import zipfile

    paras: list[str] = []
    with zipfile.ZipFile(str(path)) as z:
        secs = sorted(n for n in z.namelist()
                      if re.match(r"Contents/section\d+\.xml$", n))
        if not secs:  # 드물게 경로가 다른 경우 대비
            secs = sorted(n for n in z.namelist()
                          if n.lower().endswith(".xml") and "section" in n.lower())
        for name in secs:
            root = ET.fromstring(z.read(name))
            for p in root.iter():
                if _localname(p.tag) != "p":
                    continue
                txt = "".join(t.text or "" for t in p.iter()
                              if _localname(t.tag) == "t")
                if txt.strip():
                    paras.append(txt)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(paras)).strip()


# ---------------------------------------------------------------------------
# HWP 5.x (구형, OLE 복합 파일)
# ---------------------------------------------------------------------------
_HWPTAG_PARA_TEXT = 67  # HWPTAG_BEGIN(16) + 51

# PARA_TEXT 안에서 8개의 코드유닛(16바이트)을 차지하는 제어문자
_CTRL_8UNIT = set(range(1, 10)) | {11, 12} | set(range(14, 24))
# 한 코드유닛만 차지하는 제어문자: 0, 10(줄바꿈), 13(문단끝), 24~31


def _para_text(rec: bytes) -> str:
    m = len(rec) // 2
    if m == 0:
        return ""
    vals = struct.unpack_from("<%dH" % m, rec, 0)
    out: list[str] = []
    j = 0
    while j < m:
        c = vals[j]
        if c == 9:                 # 탭 (inline, 8유닛)
            out.append("\t"); j += 8
        elif c in _CTRL_8UNIT:     # 그 외 inline/extended 제어 → 건너뜀
            j += 8
        elif c in (10, 13):        # 줄바꿈 / 문단끝
            out.append("\n"); j += 1
        elif c < 32:               # 기타 제어문자
            j += 1
        else:
            out.append(chr(c)); j += 1
    return "".join(out)


def _section_text(data: bytes) -> str:
    out: list[str] = []
    i, n = 0, len(data)
    while i + 4 <= n:
        header = struct.unpack_from("<I", data, i)[0]
        i += 4
        tag = header & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:          # 확장 크기
            if i + 4 > n:
                break
            size = struct.unpack_from("<I", data, i)[0]
            i += 4
        rec = data[i:i + size]
        i += size
        if tag == _HWPTAG_PARA_TEXT:
            t = _para_text(rec)
            if t.strip():
                out.append(t)
    return "\n".join(out)


def extract_hwp5_text(path: str | Path) -> str:
    import olefile

    ole = olefile.OleFileIO(str(path))
    try:
        # 압축 여부: FileHeader 의 properties(offset 36) bit0
        compressed = True
        if ole.exists("FileHeader"):
            header = ole.openstream("FileHeader").read()
            if len(header) >= 40:
                flags = struct.unpack_from("<I", header, 36)[0]
                compressed = bool(flags & 0x01)
        # BodyText/Section0,1,... 순서대로
        sections = []
        for entry in ole.listdir():
            if len(entry) == 2 and entry[0] == "BodyText" and entry[1].startswith("Section"):
                try:
                    idx = int(entry[1][len("Section"):])
                except ValueError:
                    idx = 0
                sections.append((idx, entry))
        sections.sort()
        parts: list[str] = []
        for _idx, entry in sections:
            raw = ole.openstream(entry).read()
            if compressed:
                try:
                    raw = zlib.decompress(raw, -15)
                except zlib.error:
                    pass
            parts.append(_section_text(raw))
        return re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()
    finally:
        ole.close()


def extract_hwp_text(path: str | Path) -> str:
    """확장자에 따라 HWPX/HWP 텍스트를 추출."""
    p = Path(path)
    if p.suffix.lower() == ".hwpx":
        return extract_hwpx_text(p)
    return extract_hwp5_text(p)
