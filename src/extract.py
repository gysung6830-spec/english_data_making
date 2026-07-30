"""PDF -> 텍스트 추출 및 지문 본문 후보 정리(휴리스틱).

여기서는 스캔본이 아닌 텍스트 PDF 를 가정한다.
문제/정답/해설 등 불필요한 줄을 1차로 걷어내되, 최종적인 '본문만 추출'은
분석 파이프라인의 추출(extraction) API 호출에서 한 번 더 정제한다.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from . import hwp_extract

# 지원하는 이미지 확장자 (사진/캡처 자동 처리용)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# 지원하는 한글(HWP) 확장자
HWP_EXTS = {".hwp", ".hwpx"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def is_hwp(path: str | Path) -> bool:
    return Path(path).suffix.lower() in HWP_EXTS

# 문제/보기/정답으로 보이는 줄을 걸러내기 위한 패턴
_NOISE_PATTERNS = [
    re.compile(r"^\s*(정답|해설|풀이|어휘|해석|출제|답)\s*[:：)]"),
    re.compile(r"^\s*\[?\s*(정답|해설)\s*\]?"),
    re.compile(r"^\s*(문|문제)\s*\d+"),
    re.compile(r"^\s*[A-E]\)\s"),                       # A) B) 보기
]

# 줄 앞머리 번호(1. / 2) / (3)): '해석 연습' 워크시트에서는 '문장 번호',
# 객관식에서는 '보기'. 마커 뒤 내용이 짧으면(보기) 제거, 길면(지문 문장) 유지한다.
_LEADING_NUM = re.compile(r"^\s*\(?([1-9]\d{0,2})\)?\s*[.)]\s+(?P<rest>.+)$")

# 원문자 마커(①②③…): 한줄해석 지문에서는 '문장 번호', 객관식에서는 '보기'.
# 마커 뒤 내용이 짧으면(보기) 제거, 길면(지문 문장) 유지한다.
_CIRCLED = re.compile(r"^\s*[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]\s*")

# 문장 끝 위첨자 각주 번호(예: "... for use.2)" 의 "2)")를 떼기 위한 패턴
_FOOTNOTE = re.compile(r'([.!?…”"\'’」])\s*\d{1,3}\)\s*$')


def _strip_footnote(s: str) -> str:
    """문장 끝의 각주 번호(마침표+숫자+")")를 제거한다. 예: 'use.2)' -> 'use.'"""
    return _FOOTNOTE.sub(r"\1", s)

# 페이지 번호/머리말 같은 짧은 잡음 줄
_SHORT_NOISE = re.compile(r"^\s*[-–—•·\d\s]{0,4}$")
# "- 14 -" 같은 페이지 번호 줄
_PAGE_NUM = re.compile(r"^\s*[-–—]\s*\d{1,4}\s*[-–—]\s*$")


def extract_raw_text(pdf_path: str | Path) -> str:
    """PDF 전체에서 텍스트를 뽑는다. 2단(좌지문/우해석) 레이아웃은 칸별로 세로 추출."""
    pdf_path = Path(pdf_path)
    parts: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            parts.append(_extract_page_text(page))
    return "\n".join(parts)


def _is_hangul(s: str) -> bool:
    return any("가" <= c <= "힣" for c in s)


def _extract_page_text(page) -> str:
    """한 페이지 텍스트.

    좌지문/우해석(영어+한글 2단) 페이지는 문자 종류로 분리한다:
    같은 줄에서 라틴 문자(영어)와 한글을 갈라, '영어 전체 → 한글 전체' 순서로 재배열.
    이렇게 하면 pdfplumber 가 좌우를 뒤섞어 문장이 조각나는 문제를 막는다.
    """
    try:
        words = page.extract_words()
    except Exception:
        words = []
    full = page.extract_text() or ""
    if not words:
        return full

    # 한글이 거의 없으면(영어 전용 지문) 원본 추출을 그대로 사용
    n_kor = sum(1 for w in words if _is_hangul(w["text"]))
    if n_kor < 3 or n_kor > len(words) - 3:
        return full

    # 줄(top)로 묶고, 각 줄에서 라틴/한글을 분리
    lines: dict[int, list] = {}
    for w in words:
        lines.setdefault(round(float(w["top"]) / 3.0), []).append(w)

    eng_lines: list[str] = []
    kor_lines: list[str] = []
    for key in sorted(lines):
        row = sorted(lines[key], key=lambda x: float(x["x0"]))
        eng = " ".join(x["text"] for x in row if not _is_hangul(x["text"])).strip()
        kor = " ".join(x["text"] for x in row if _is_hangul(x["text"])).strip()
        if eng:
            eng_lines.append(eng)
        if kor:
            kor_lines.append(kor)

    out = "\n".join(eng_lines)
    if kor_lines:
        out += "\n\n[해석]\n" + "\n".join(kor_lines)
    return out


def clean_text(raw: str) -> str:
    """문제/정답/해설 등으로 보이는 줄을 1차 제거한다."""
    kept: list[str] = []
    for line in raw.splitlines():
        s = line.rstrip()
        if not s.strip():
            kept.append("")
            continue
        if _SHORT_NOISE.match(s) or _PAGE_NUM.match(s):
            continue
        m = _CIRCLED.match(s)
        if m:
            rest = s[m.end():].strip()
            if len(rest) < 25:          # 짧으면 객관식 보기로 보고 제거
                continue
            # 지문 문장이면 마커만 떼고 본문 유지
            kept.append(_strip_footnote(rest))
            continue
        mn = _LEADING_NUM.match(s)
        if mn:
            rest = mn.group("rest").strip()
            if len(rest) < 25:          # 짧으면 객관식 보기/목차로 보고 제거
                continue
            # '해석 연습' 등 번호 매긴 지문 문장이면 번호만 떼고 본문 유지
            kept.append(_strip_footnote(rest))
            continue
        if any(p.search(s) for p in _NOISE_PATTERNS):
            continue
        kept.append(_strip_footnote(s))
    # 연속 빈 줄 압축
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def extract_passage_text(pdf_path: str | Path) -> str:
    """PDF/HWP -> (1차 정제된) 지문 후보 텍스트."""
    if is_hwp(pdf_path):
        return clean_text(hwp_extract.extract_hwp_text(pdf_path))
    return clean_text(extract_raw_text(pdf_path))


def looks_empty(text: str) -> bool:
    """텍스트가 사실상 비어있는지(스캔본/추출 실패) 판단."""
    letters = re.sub(r"[^A-Za-z]", "", text)
    return len(letters) < 40
