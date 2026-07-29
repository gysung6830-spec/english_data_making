"""HWP/HWPX 텍스트 추출 오프라인 테스트 (외부 파일 없이 합성).

실행: python -m tests.test_hwp
"""
from __future__ import annotations

import struct
import tempfile
import zipfile
from pathlib import Path

from src import hwp_extract as h
from src import extract


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def test_hwpx_roundtrip():
    sec = (
        '<?xml version="1.0"?>\n'
        '<hml:section xmlns:hp="x">\n'
        '<hp:p><hp:run><hp:t>The sun rises in the east.</hp:t></hp:run></hp:p>\n'
        '<hp:p><hp:run><hp:t>It sets in the </hp:t><hp:t>west &amp; glows.</hp:t></hp:run></hp:p>\n'
        '<hp:p><hp:run><hp:t>모기는 이산화탄소를 감지한다.</hp:t></hp:run></hp:p>\n'
        '</hml:section>')
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "s.hwpx"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("Contents/section0.xml", sec)
        txt = h.extract_hwp_text(p)
    _check("HWPX: 문단 3개 추출", txt.count("\n") == 2)
    _check("HWPX: 같은 run 의 <hp:t> 이어붙임 + XML 이스케이프 해제",
           "It sets in the west & glows." in txt)
    _check("HWPX: 한글 보존", "모기는 이산화탄소를 감지한다." in txt)
    _check("HWPX: extract.is_hwp 인식", extract.is_hwp("a.hwpx") and extract.is_hwp("b.HWP"))


def _rec(tag_id, payload):
    header = (tag_id & 0x3FF) | ((len(payload) & 0xFFF) << 20)
    return struct.pack("<I", header) + payload


def test_hwp5_records_and_controls():
    # 'Hi' + 인라인 제어문자(코드4=8글자) + 'Bye'
    payload = "Hi".encode("utf-16-le")
    payload += struct.pack("<H", 4) + b"\x00" * 14      # 8 wchar 제어문자
    payload += "Bye".encode("utf-16-le")
    rec = _rec(h._HWPTAG_PARA_TEXT, payload)
    recs = list(h._iter_records(rec))
    _check("HWP5: 레코드 1개(PARA_TEXT) 파싱", len(recs) == 1 and recs[0][0] == 67)
    _check("HWP5: 인라인 제어문자(8글자) 건너뛰기", h._para_text(recs[0][2]) == "HiBye")

    # 줄바꿈 제어문자(10) 는 개행으로
    p2 = "A".encode("utf-16-le") + struct.pack("<H", 10) + "B".encode("utf-16-le")
    _check("HWP5: 코드10 -> 개행", h._para_text(p2) == "A\nB")

    # 확장 크기(0xFFF) 레코드도 처리
    big = "X".encode("utf-16-le")
    header = (h._HWPTAG_PARA_TEXT & 0x3FF) | (0xFFF << 20)
    ext = struct.pack("<I", header) + struct.pack("<I", len(big)) + big
    recs2 = list(h._iter_records(ext))
    _check("HWP5: 확장 크기(0xFFF) 레코드 처리", len(recs2) == 1 and h._para_text(recs2[0][2]) == "X")


if __name__ == "__main__":
    test_hwpx_roundtrip()
    test_hwp5_records_and_controls()
    print("\nHWP/HWPX 추출 오프라인 테스트 통과 ✅")
