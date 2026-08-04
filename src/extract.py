"""PDF -> 텍스트 추출 및 지문 본문 후보 정리(휴리스틱).

여기서는 스캔본이 아닌 텍스트 PDF 를 가정한다.
문제/정답/해설 등 불필요한 줄을 1차로 걷어내되, 최종적인 '본문만 추출'은
분석 파이프라인의 추출(extraction) API 호출에서 한 번 더 정제한다.
"""
from __future__ import annotations

import html
import re
import struct
import zipfile
import zlib
from pathlib import Path

import pdfplumber

# 지원하는 이미지 확장자 (사진/캡처 자동 처리용)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# 한글 워드프로세서 파일 (.hwp = 바이너리, .hwpx = XML zip)
HWP_EXTS = {".hwp", ".hwpx"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def is_hwp(path: str | Path) -> bool:
    return Path(path).suffix.lower() in HWP_EXTS


# ---------------------------------------------------------------------------
# HWP / HWPX 본문 텍스트 추출
# ---------------------------------------------------------------------------
# PARA_TEXT 레코드 안에서 16바이트(8 wchar)를 차지하는 인라인/확장 컨트롤 코드
_HWP_LONG_CTRL = {1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23}
_HWPTAG_PARA_TEXT = 67  # HWPTAG_BEGIN(0x10) + 51


def _hwp_decode_para(rec: bytes) -> str:
    """PARA_TEXT 레코드(UTF-16LE + 인라인 컨트롤)를 사람이 읽는 텍스트로."""
    out: list[str] = []
    j, n = 0, len(rec)
    while j + 2 <= n:
        code = rec[j] | (rec[j + 1] << 8)
        if code < 32:
            j += 16 if code in _HWP_LONG_CTRL else 2
            if code in (10, 13):
                out.append("\n")
            continue
        out.append(chr(code))
        j += 2
    return "".join(out)


def _hwp_section_text(data: bytes) -> str:
    """섹션 스트림(레코드 나열)에서 문단 텍스트만 뽑는다."""
    out: list[str] = []
    i, n = 0, len(data)
    while i + 4 <= n:
        header = struct.unpack_from("<I", data, i)[0]
        i += 4
        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if i + 4 > n:
                break
            size = struct.unpack_from("<I", data, i)[0]
            i += 4
        rec = data[i:i + size]
        i += size
        if tag_id == _HWPTAG_PARA_TEXT:
            out.append(_hwp_decode_para(rec))
    return "\n".join(t for t in out if t.strip())


def extract_hwp5_text(path: str | Path) -> str:
    """.hwp(HWP 5.0 바이너리) 본문 텍스트 추출 (olefile + zlib)."""
    import olefile

    ole = olefile.OleFileIO(str(path))
    try:
        header = ole.openstream("FileHeader").read()
        compressed = bool(header[36] & 0x01) if len(header) > 36 else True
        sections = sorted(
            (e for e in ole.listdir()
             if len(e) >= 2 and e[0] == "BodyText" and e[1].lower().startswith("section")),
            key=lambda e: int(re.sub(r"\D", "", e[1]) or 0),
        )
        parts: list[str] = []
        for entry in sections:
            raw = ole.openstream(entry).read()
            if compressed:
                try:
                    raw = zlib.decompress(raw, -15)
                except zlib.error:
                    continue
            parts.append(_hwp_section_text(raw))
        return "\n\n".join(p for p in parts if p.strip())
    finally:
        ole.close()


def extract_hwpx_text(path: str | Path) -> str:
    """.hwpx(OWPML XML zip) 본문 텍스트 추출."""
    paras: list[str] = []
    with zipfile.ZipFile(str(path)) as z:
        names = sorted(n for n in z.namelist()
                       if re.search(r"section\d+\.xml$", n, re.IGNORECASE))
        if not names:
            names = sorted(n for n in z.namelist()
                           if n.lower().endswith(".xml") and "content" in n.lower())
        for name in names:
            xml = z.read(name).decode("utf-8", "ignore")
            # 문단(<...:p>) 단위로 텍스트 런(<...:t>)을 모은다
            for block in re.findall(r"<(?:\w+:)?p\b.*?</(?:\w+:)?p>", xml, re.DOTALL):
                runs = re.findall(r"<(?:\w+:)?t\b[^>]*>(.*?)</(?:\w+:)?t>", block, re.DOTALL)
                line = "".join(html.unescape(re.sub(r"<[^>]+>", "", r)) for r in runs)
                if line.strip():
                    paras.append(line)
    return "\n".join(paras)


def extract_hwp_text(path: str | Path) -> str:
    """확장자에 따라 .hwp / .hwpx 본문 텍스트를 추출."""
    p = Path(path)
    if p.suffix.lower() == ".hwpx":
        return extract_hwpx_text(p)
    return extract_hwp5_text(p)

# 문제/보기/정답으로 보이는 줄을 걸러내기 위한 패턴
_NOISE_PATTERNS = [
    re.compile(r"^\s*[①②③④⑤]"),                     # 객관식 보기 마커
    re.compile(r"^\s*\(?[1-9]\d?\)?\s*[.)]\s"),         # 1) 2. 등 번호 문항
    re.compile(r"^\s*(정답|해설|풀이|어휘|해석|출제|답)\s*[:：)]"),
    re.compile(r"^\s*\[?\s*(정답|해설)\s*\]?"),
    re.compile(r"^\s*(문|문제)\s*\d+"),
    re.compile(r"^\s*[A-E]\)\s"),                       # A) B) 보기
]

# 페이지 번호/머리말 같은 짧은 잡음 줄
_SHORT_NOISE = re.compile(r"^\s*[-–—•·\d\s]{0,4}$")


def extract_raw_text(pdf_path: str | Path) -> str:
    """PDF 전체에서 텍스트를 뽑는다."""
    pdf_path = Path(pdf_path)
    parts: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            parts.append(txt)
    return "\n".join(parts)


def clean_text(raw: str) -> str:
    """문제/정답/해설 등으로 보이는 줄을 1차 제거한다."""
    kept: list[str] = []
    for line in raw.splitlines():
        s = line.rstrip()
        if not s.strip():
            kept.append("")
            continue
        if _SHORT_NOISE.match(s):
            continue
        if any(p.search(s) for p in _NOISE_PATTERNS):
            continue
        kept.append(s)
    # 연속 빈 줄 압축
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def extract_passage_text(pdf_path: str | Path) -> str:
    """PDF/HWP/HWPX -> (1차 정제된) 지문 후보 텍스트."""
    if is_hwp(pdf_path):
        return clean_text(extract_hwp_text(pdf_path))
    return clean_text(extract_raw_text(pdf_path))


def looks_empty(text: str) -> bool:
    """텍스트가 사실상 비어있는지(스캔본/추출 실패) 판단."""
    letters = re.sub(r"[^A-Za-z]", "", text)
    return len(letters) < 40


def looks_garbled(text: str) -> bool:
    """2단(영어+한글 병렬)·한줄해석 등으로 지문 문장이 조각났는지 추정.

    다음 중 하나면 True(→ 비전으로 재추출) — 영어 전용 지문은 어디에도 안 걸림:
      (a) 한 줄에 한글+영어가 함께 있는 줄이 많음(좌우 2단 컬럼이 섞임).
      (b) 'EBS ~ 한줄해석/한 줄 해석' 처럼 영어 조각과 한글 해석을 줄 단위로
          번갈아 싣는 포맷 표지가 있음(문장이 조각나 추출됨).
      (c) '한글만 있는 줄'과 '영어만 있는 줄'이 둘 다 여러 개 → 해석이 함께
          실린 자료(직독직해/해설지)로, 영어가 완전한 문장이 아닐 위험이 큼.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 5:
        return False
    # (b) 한줄해석류 포맷 표지
    if re.search(r"한\s*줄\s*해석|한줄\s*해설", text):
        return True
    ko_re = re.compile(r"[가-힣]")
    en_re = re.compile(r"[A-Za-z]")
    mixed = ko_only = en_only = 0
    for ln in lines:
        has_ko, has_en = bool(ko_re.search(ln)), bool(en_re.search(ln))
        if has_ko and has_en:
            mixed += 1
        elif has_ko:
            ko_only += 1
        elif has_en:
            en_only += 1
    # (a) 한 줄에 영/한 혼재가 많음
    if mixed / len(lines) > 0.3:
        return True
    # (c) 한글 해석 줄과 영어 줄이 둘 다 여러 개(해석이 함께 실린 자료)
    if ko_only >= 3 and en_only >= 3:
        return True
    return False


def pdf_pages_to_images(pdf_path: str | Path, out_dir: str | Path | None = None,
                        dpi: int = 170, max_pages: int = 12) -> list[Path]:
    """PDF 각 페이지를 PNG 이미지로 렌더(비전 재추출용). PyMuPDF 필요."""
    import fitz  # PyMuPDF

    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir) if out_dir else pdf_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            p = out_dir / f"{pdf_path.stem}__p{i + 1}.png"
            pix.save(str(p))
            paths.append(p)
    finally:
        doc.close()
    return paths
