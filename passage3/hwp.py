"""HWP / HWPX 파일에서 텍스트를 추출한다.

- .hwpx : 신형(ZIP + XML). Contents/section*.xml 의 <hp:t> 텍스트를 문단
          단위로 뽑는다. (표준 라이브러리만 사용)
- .hwp  : 구형(한글 5.x, OLE 복합 파일). BodyText/Section* 스트림을 (필요 시
          zlib 해제 후) 레코드 파싱해 PARA_TEXT(문단 텍스트)를 뽑는다.
          olefile 필요.

추출 실패 시 빈 문자열을 반환한다(프로그램은 멈추지 않음).
"""
from __future__ import annotations

import re
import struct
import zipfile
import zlib
from html import unescape
from pathlib import Path

HWP_EXTS = {".hwp", ".hwpx"}

# HWP5 레코드 태그
_HWPTAG_BEGIN = 0x10
_HWPTAG_PARA_TEXT = _HWPTAG_BEGIN + 51  # 67

# 문단 텍스트 내 제어문자 분류(단위: wchar 2바이트)
_CTRL_1WCHAR = {0, 10, 13, 24, 25, 26, 27, 28, 29, 30, 31}   # 1 wchar
_CTRL_8WCHAR = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15,
                16, 17, 18, 19, 20, 21, 22, 23}               # 8 wchar(16바이트)


def extract_hwp_text(path) -> str:
    p = Path(path)
    try:
        if p.suffix.lower() == ".hwpx":
            return _extract_hwpx(p)
        return _extract_hwp5(p)
    except Exception:
        return ""


# ── HWPX (신형) ───────────────────────────────────────────────

def _extract_hwpx(path: Path) -> str:
    paras: list[str] = []
    with zipfile.ZipFile(str(path)) as z:
        names = [n for n in z.namelist()
                 if re.search(r"Contents/section\d+\.xml$", n)]
        names.sort()
        for n in names:
            xml = z.read(n).decode("utf-8", "ignore")
            # 문단(<hp:p ...> ... </hp:p>) 단위로 나눠 각 문단의 <hp:t> 합침
            for pblock in re.split(r"</hp:p>", xml):
                texts = re.findall(r"<hp:t[^>]*>(.*?)</hp:t>", pblock, re.S)
                if not texts:
                    continue
                line = "".join(unescape(re.sub(r"<[^>]+>", "", t)) for t in texts)
                line = line.strip()
                if line:
                    paras.append(line)
    return "\n".join(paras)


# ── HWP5 (구형, OLE) ──────────────────────────────────────────

def _extract_hwp5(path: Path) -> str:
    import olefile

    ole = olefile.OleFileIO(str(path))
    try:
        header = ole.openstream("FileHeader").read()
        # 배포(암호화) 문서는 지원하지 않음
        compressed = bool(header[36] & 0x01)

        sections = []
        for entry in ole.listdir():
            if len(entry) == 2 and entry[0] == "BodyText" \
                    and entry[1].startswith("Section"):
                try:
                    idx = int(entry[1][len("Section"):])
                except ValueError:
                    idx = 0
                sections.append((idx, entry))
        sections.sort(key=lambda x: x[0])

        out: list[str] = []
        for _, entry in sections:
            data = ole.openstream(entry).read()
            if compressed:
                try:
                    data = zlib.decompress(data, -15)
                except zlib.error:
                    continue
            out.append(_parse_records(data))
        return "\n".join(out)
    finally:
        ole.close()


def _parse_records(data: bytes) -> str:
    i, n = 0, len(data)
    paras: list[str] = []
    while i + 4 <= n:
        header = struct.unpack_from("<I", data, i)[0]
        i += 4
        tag = header & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if i + 4 > n:
                break
            size = struct.unpack_from("<I", data, i)[0]
            i += 4
        payload = data[i:i + size]
        i += size
        if tag == _HWPTAG_PARA_TEXT:
            paras.append(_decode_para(payload))
    return "\n".join(t for t in paras if t.strip())


def _decode_para(payload: bytes) -> str:
    res = []
    i, L = 0, len(payload)
    while i + 2 <= L:
        code = struct.unpack_from("<H", payload, i)[0]
        if code in _CTRL_8WCHAR:
            i += 16          # 인라인/확장 제어문자는 8 wchar 차지
            continue
        if code in _CTRL_1WCHAR:
            if code in (10, 13):
                res.append(" ")   # 줄바꿈류는 공백으로
            i += 2
            continue
        res.append(chr(code))
        i += 2
    return "".join(res).strip()
