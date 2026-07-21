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


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS

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
    """PDF -> (1차 정제된) 지문 후보 텍스트.

    배치 무관(좌영어우한글·영어만·영어줄/한글줄)하게 영어만 남긴 뒤 잡음 줄을 제거한다.
    """
    return clean_text(strip_korean_keep_english(extract_raw_text(pdf_path)))


def looks_empty(text: str) -> bool:
    """텍스트가 사실상 비어있는지(스캔본/추출 실패) 판단."""
    letters = re.sub(r"[^A-Za-z]", "", text)
    return len(letters) < 40
