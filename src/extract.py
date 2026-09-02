"""PDF -> 텍스트 추출 및 지문 본문 후보 정리(휴리스틱).

여기서는 스캔본이 아닌 텍스트 PDF 를 가정한다.
문제/정답/해설 등 불필요한 줄을 1차로 걷어내되, 최종적인 '본문만 추출'은
분석 파이프라인의 추출(extraction) API 호출에서 한 번 더 정제한다.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

# 지원하는 이미지 확장자 (사진/캡처 자동 처리용)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# 한글(HWP) 문서 확장자
HWP_EXTS = {".hwp", ".hwpx"}
# 일반 텍스트 확장자(지문을 그대로 붙여넣은 .txt)
TXT_EXTS = {".txt", ".text"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def is_hwp(path: str | Path) -> bool:
    return Path(path).suffix.lower() in HWP_EXTS


def is_txt(path: str | Path) -> bool:
    return Path(path).suffix.lower() in TXT_EXTS


def extract_txt_text(path: str | Path) -> str:
    """.txt 파일 본문을 그대로 읽는다(UTF-8 우선, 실패 시 CP949/Latin-1).

    지문이 '[18번] …' 처럼 문제 머리글과 함께 붙여넣어진 텍스트를 가정한다.
    추가 정제 없이 원문을 돌려주고, 지문 분리·한글 제거는 상위 파이프라인이 처리한다.
    """
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="ignore")

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

# 한글(음절·자모) 문자
_HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def strip_korean_keep_english(raw: str) -> str:
    """어떤 배치의 PDF 든 '영어 원문'만 순서대로 남긴다.

    - 좌 영어 / 우 한글(2단)  : pdfplumber 가 한 줄에 'English … 한글' 로 붙여 읽어도,
      각 줄을 토큰(공백 단위)으로 보고 한글을 지운 뒤 '영문이 남는 토큰'만 유지.
    - 영어 한 줄 / 한글 한 줄  : 한글 전용 줄은 영문 토큰이 없어 빈 줄로 사라짐.
    - 영어만                   : 한글이 없으므로 원본 그대로(무변경).
    토큰에 한글이 붙어 있어도(cat고양이) 한글만 떼어내 영문(cat)은 살린다.
    """
    out_lines: list[str] = []
    for line in raw.splitlines():
        if not _HANGUL_RE.search(line):
            out_lines.append(line)          # 한글 없음 → 그대로(영어만/빈 줄)
            continue
        toks: list[str] = []
        for tok in line.split():
            cleaned = _HANGUL_RE.sub("", tok).strip()
            if _LATIN_RE.search(cleaned):    # 영문이 남는 토큰만 유지
                toks.append(cleaned)
        out_lines.append(" ".join(toks))     # 영문 없으면 빈 줄(한글 전용 줄 제거)
    return "\n".join(out_lines)


def extract_raw_text(pdf_path: str | Path) -> str:
    """PDF(또는 .txt) 전체에서 텍스트를 뽑는다."""
    pdf_path = Path(pdf_path)
    if is_txt(pdf_path):
        return extract_txt_text(pdf_path)     # .txt 는 그대로 원문 반환
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
    """PDF -> (1차 정제된) 지문 후보 텍스트.

    배치 무관(좌영어우한글·영어만·영어줄/한글줄)하게 영어만 남긴 뒤 잡음 줄을 제거한다.
    """
    return clean_text(strip_korean_keep_english(extract_raw_text(pdf_path)))


# 페이지 마커 "- 14 -", 지문 문장 번호 "1. "/"2) ", 각주 표시 "…use.2)"
_PAGE_MARK_RE = re.compile(r"^\s*-+\s*\d{1,4}\s*-+\s*$")
_LEAD_NUM_RE = re.compile(r"^\s*\d{1,3}\s*[.)]\s+")
_FOOTNOTE_RE = re.compile(r"(?<!\()\b\d{1,3}\)")


def clean_passage_text(raw: str) -> str:
    """워크시트용 1차 정제 — '번호 매겨진 지문 문장'을 보존한다.

    6섹션용 clean_text 는 '1. 2.'로 시작하는 줄을 '객관식 문항'으로 보고 통째로
    지운다. 그러나 해석연습 WORKBOOK 처럼 '지문 문장'마다 번호가 붙는 자료에서는
    그 줄이 문장의 앞부분(주어·동사)이라 지우면 안 된다. 여기서는 줄을 지우지 않고
    앞의 문장 번호와 각주 표시(1) 2) …)만 떼어낸다. 실제 문제/보기/해설 제거는
    뒤따르는 LLM 지문 추출이 담당한다.
    """
    kept: list[str] = []
    for line in raw.splitlines():
        s = line.rstrip()
        if not s.strip():
            kept.append("")
            continue
        if _SHORT_NOISE.match(s) or _PAGE_MARK_RE.match(s):
            continue
        s = _LEAD_NUM_RE.sub("", s)     # 문장 앞 번호 "1. " 제거(줄은 보존)
        s = _FOOTNOTE_RE.sub("", s)     # 각주 표시 "2)" 제거
        kept.append(s.rstrip())
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# ---------------------------------------------------------------------------
# HWP / HWPX 텍스트 추출
# ---------------------------------------------------------------------------
def _extract_hwpx(path: Path) -> str:
    """HWPX(신형, XML zip) 본문 텍스트 추출."""
    import zipfile
    from xml.etree import ElementTree as ET

    out: list[str] = []
    with zipfile.ZipFile(str(path)) as z:
        names = sorted(n for n in z.namelist()
                       if n.startswith("Contents/section") and n.endswith(".xml"))
        for n in names:
            try:
                root = ET.fromstring(z.read(n))
            except Exception:
                continue
            for el in root.iter():
                tag = el.tag.rsplit("}", 1)[-1]     # 네임스페이스 제거
                if tag == "p":
                    out.append("\n")                # 문단 경계
                elif tag == "t" and el.text:
                    out.append(el.text)
    return "".join(out)


# HWP 5.0 레코드 태그: 본문 텍스트
_HWPTAG_PARA_TEXT = 67
# 텍스트 내 확장/인라인 컨트롤(8 wchar 차지) 코드
_HWP_EXT_CTRL = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}


def _hwp5_decode_text(rec: bytes) -> str:
    import struct
    m = len(rec) // 2
    if m == 0:
        return ""
    chars = struct.unpack("<%dH" % m, rec[:m * 2])
    out: list[str] = []
    i = 0
    while i < m:
        c = chars[i]
        if c in _HWP_EXT_CTRL:      # 컨트롤(그림·표·주석 등) → 8 wchar 건너뜀
            i += 8
            continue
        if c in (10, 13):           # 줄바꿈·문단 끝
            out.append("\n")
            i += 1
            continue
        if c < 32:                  # 기타 제어문자 무시
            i += 1
            continue
        out.append(chr(c))
        i += 1
    return "".join(out)


def _extract_hwp5(path: Path) -> str:
    """HWP 5.0(구형, OLE 바이너리) 본문 텍스트 추출."""
    import struct
    import zlib

    import olefile  # setup 에서 설치(경량)

    if not olefile.isOleFile(str(path)):
        raise ValueError("HWP 5.0 형식이 아닙니다(손상되었거나 다른 형식).")
    ole = olefile.OleFileIO(str(path))
    try:
        header = ole.openstream("FileHeader").read()
        compressed = bool(header[36] & 1)     # 플래그 bit0 = 압축 여부
        sections = sorted(
            (e for e in ole.listdir()
             if len(e) == 2 and e[0] == "BodyText" and e[1].startswith("Section")),
            key=lambda e: e[1],
        )
        out: list[str] = []
        for entry in sections:
            data = ole.openstream(entry).read()
            if compressed:
                data = zlib.decompress(data, -15)   # raw deflate
            pos, n = 0, len(data)
            while pos + 4 <= n:
                hdr = struct.unpack("<I", data[pos:pos + 4])[0]
                pos += 4
                tag = hdr & 0x3FF
                size = (hdr >> 20) & 0xFFF
                if size == 0xFFF:                    # 확장 크기
                    size = struct.unpack("<I", data[pos:pos + 4])[0]
                    pos += 4
                rec = data[pos:pos + size]
                pos += size
                if tag == _HWPTAG_PARA_TEXT:
                    out.append(_hwp5_decode_text(rec))
        return "\n".join(out)
    finally:
        ole.close()


def extract_hwp_text(path: str | Path) -> str:
    """HWP(.hwp 5.0) / HWPX(.hwpx) 본문 텍스트를 추출한다."""
    path = Path(path)
    head = b""
    try:
        with open(path, "rb") as f:
            head = f.read(4)
    except OSError:
        pass
    if path.suffix.lower() == ".hwpx" or head[:2] == b"PK":
        return _extract_hwpx(path)
    return _extract_hwp5(path)


def extract_passage_text_any(src: str | Path) -> str:
    """PDF·HWP·HWPX 무엇이든 (1차 정제된) 지문 후보 텍스트로.

    배치 무관하게 영어만 남긴 뒤 잡음 줄을 제거한다(이미지는 별도 비전 경로).
    """
    src = Path(src)
    raw = extract_hwp_text(src) if is_hwp(src) else extract_raw_text(src)
    return clean_passage_text(strip_korean_keep_english(raw))


def looks_empty(text: str) -> bool:
    """텍스트가 사실상 비어있는지(스캔본/추출 실패) 판단."""
    letters = re.sub(r"[^A-Za-z]", "", text)
    return len(letters) < 40


# ---------------------------------------------------------------------------
# PDF -> 페이지 이미지 (텍스트 레이어가 깨졌을 때 비전으로 재추출하기 위한 렌더)
# ---------------------------------------------------------------------------
def pdf_to_images(pdf_path: str | Path, out_dir: str | Path,
                  scale: float = 2.0, max_pages: int = 12) -> list[Path]:
    """PDF 각 페이지를 PNG 로 렌더링해 경로 목록을 돌려준다.

    폰트 subset·2단·스캔 등으로 텍스트 추출이 깨진 PDF를, 화면에 '보이는 그대로'
    비전(이미지) 경로로 다시 읽기 위한 준비 단계. pypdfium2 를 사용한다.
    """
    import pypdfium2 as pdfium

    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        n = min(len(pdf), max_pages)
        for i in range(n):
            img = pdf[i].render(scale=scale).to_pil()
            p = out_dir / f"{pdf_path.stem}_p{i + 1}.png"
            img.save(str(p))
            paths.append(p)
    finally:
        pdf.close()
    return paths
