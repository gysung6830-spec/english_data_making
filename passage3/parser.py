"""텍스트 → 지문/문장 파싱.

지문 구분 = 문제 번호 헤더 한 줄 (예: "[고3] 2026년 5월 - 26번: 제목").
문장 구분 = 원문자 ①②③…⑳.
영어/한글 분리 = 줄 단위 판별(한글 2자 이상 → 해석).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

# ── 데이터 모델 ────────────────────────────────────────────────

@dataclass
class Sentence:
    num: int        # 문장 번호 (①→1)
    en: str         # 영어 원문
    ko: str = ""    # 한글 해석 (없으면 빈 문자열)


@dataclass
class Vocab:
    word: str        # 영어 단어/표현
    meaning: str     # 한글 뜻(문맥상)


@dataclass
class Passage:
    label: str                              # "[고3] 2026년 5월 - 26번"
    title: str                              # 제목/주제
    sentences: List[Sentence] = field(default_factory=list)
    vocab: List[Vocab] = field(default_factory=list)  # 하단 어휘 리스트


# ── 정규식/상수 ───────────────────────────────────────────────

# 원문자 ①(U+2460) … ⑳(U+2473)
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
_CIRCLED_BASE = 0x2460  # ①
CIRCLED_SET = set(CIRCLED)

# 지문 헤더:  [ ... ] ... N번 : 제목
#   그룹1 = 라벨( [고3] 2026년 5월 - 26번 ), 그룹2 = 번호, 그룹3 = 제목
HEADER_RE = re.compile(
    r"(\[[^\]]*\][^:：\n]*?(\d+)\s*번)\s*[:：]\s*(.*)"
)

# 대체 헤더:  '31번 2026년 6월 … 고3 …' 처럼 줄이 'N번'으로 시작하는 형식
#   (EXAM4YOU 워크북 등. 콜론/대괄호 없음)
HEADER_RE2 = re.compile(r"^\s*(\d{1,3})\s*번\b(.*)$")

# 아라비아 숫자 문장 번호:  줄 시작의 'N. ' (원문자 대신 쓰는 자료)
_ARABIC_MARK_RE = re.compile(r"(?m)^[ \t]*(\d{1,2})\.[ \t]+")

# 각주 참조:  문장 끝의 '1)' '2)' 같은 위첨자 표기 제거
_FOOTNOTE_RE = re.compile(r"\s*\d{1,3}\)\s*$")

# 페이지 번호 줄:  '- 14 -', '14' 등
_PAGENUM_RE = re.compile(r"^\s*[-–—]?\s*\d{1,4}\s*[-–—]?\s*$")

# 한글 음절 영역
_HANGUL_RE = re.compile(r"[가-힣]")


def circled_to_int(ch: str) -> int:
    """원문자 → 정수. ①→1 … ⑳→20. 아니면 0."""
    if ch in CIRCLED_SET:
        return ord(ch) - _CIRCLED_BASE + 1
    return 0


def _count_hangul(s: str) -> int:
    return len(_HANGUL_RE.findall(s))


def _is_korean_line(line: str) -> bool:
    """한글이 2자 이상 포함된 줄 → 한글 해석으로 간주."""
    return _count_hangul(line) >= 2


def _split_mixed_line(line: str) -> Tuple[str, str]:
    """한 줄에 영/한이 섞이면 한글 첫 등장 위치에서 분리.

    반환: (영어부분, 한글부분).
    """
    m = _HANGUL_RE.search(line)
    if not m:
        return line.strip(), ""
    idx = m.start()
    return line[:idx].strip(), line[idx:].strip()


def _split_en_ko(chunk: str) -> Tuple[str, str]:
    """문장 조각(원문자 제거된 본문) → (영어, 한글).

    - 한글 없는 줄 → 영어.
    - 한글 있는 줄:
        · 아직 영어를 못 잡았고 앞부분이 영어면 → 같은 줄에 영/한이 섞인
          경우로 보고 한글 첫 등장 위치에서 분리.
        · 이미 영어 줄을 잡았다면 → 그 줄 전체가 한글 해석(영어 고유명사가
          섞여 있어도 통째로 해석으로 둠).
    """
    en_parts: List[str] = []
    ko_parts: List[str] = []
    for raw_line in chunk.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _PAGENUM_RE.match(line):
            continue  # 페이지 번호 줄('- 14 -' 등) 무시
        if _is_korean_line(line):
            if not en_parts:
                # 아직 영어를 못 잡음 → 같은 줄 혼합 가능성. 분리 시도.
                en, ko = _split_mixed_line(line)
                if en:
                    en_parts.append(en)
                if ko:
                    ko_parts.append(ko)
            else:
                # 영어는 이미 별도 줄에서 잡음 → 이 줄은 통째로 해석.
                ko_parts.append(line)
        else:
            en_parts.append(line)
    en = " ".join(p.strip() for p in en_parts if p.strip())
    ko = " ".join(p.strip() for p in ko_parts if p.strip())
    return en.strip(), ko.strip()


def _strip_footnote(s: str) -> str:
    """문장 끝의 각주 참조('...related.1)')를 제거."""
    return _FOOTNOTE_RE.sub("", s).rstrip()


def _parse_sentences(body: str) -> List[Sentence]:
    """지문 본문 → 문장 리스트.

    문장 번호는 원문자(①②)를 우선 인식하고, 없으면 아라비아 숫자('1.' '2.')
    를 인식한다. 같은 번호가 두 번 나오면(영어줄 + 한글줄) 하나로 병합한다.
    """
    # (마커 시작, 본문 시작, 번호)
    marks: List[Tuple[int, int, int]] = []
    for i, ch in enumerate(body):
        n = circled_to_int(ch)
        if n:
            marks.append((i, i + 1, n))

    # 원문자가 없으면 아라비아 숫자 문장번호로 대체
    if not marks:
        for m in _ARABIC_MARK_RE.finditer(body):
            marks.append((m.start(), m.end(), int(m.group(1))))
        marks.sort()

    if not marks:
        return []

    # 마커 앞의 서두(헤더/안내문 잔여물)는 버린다.
    chunks: List[Tuple[int, str]] = []
    for k, (ms, cs, num) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body)
        chunks.append((num, body[cs:end]))

    # 번호 순서대로 병합
    merged: "dict[int, List[str]]" = {}
    order: List[int] = []
    for num, text in chunks:
        if num not in merged:
            merged[num] = []
            order.append(num)
        merged[num].append(text)

    sentences: List[Sentence] = []
    for num in order:
        combined = "\n".join(merged[num])
        en, ko = _split_en_ko(combined)
        en = _strip_footnote(en)
        if not en and not ko:
            continue
        sentences.append(Sentence(num=num, en=en, ko=ko))
    return sentences


def _clean_title(s: str) -> str:
    """제목 문자열 정리(구분자·중복 공백 정돈)."""
    s = s.replace("┃", " · ").replace("|", " · ")
    s = " ".join(s.split())
    return s.strip(" -–—·:：")


def _match_header(line: str):
    """헤더 줄이면 (라벨, 제목) 반환, 아니면 None."""
    m = HEADER_RE.search(line)
    if m:
        return m.group(1).strip(), m.group(3).strip()
    m = HEADER_RE2.match(line)
    if m:
        rest = m.group(2)
        # 'N번' 뒤에 실제 제목/설명이 있어야 헤더로 인정(문장 오인 방지)
        if _count_hangul(rest) >= 2 or len(rest.strip()) >= 4:
            return f"{m.group(1)}번", _clean_title(rest)
    return None


def split_passages(raw: str) -> List[Passage]:
    """텍스트 전체 → 지문 리스트."""
    if not raw:
        return []

    lines = raw.splitlines()

    # 헤더 줄 위치 찾기
    header_idx: List[Tuple[int, str, str]] = []  # (줄번호, label, title)
    for i, line in enumerate(lines):
        hm = _match_header(line)
        if hm:
            header_idx.append((i, hm[0], hm[1]))

    passages: List[Passage] = []

    if not header_idx:
        # 헤더가 전혀 없으면 전체를 한 지문으로 취급(라벨/제목 비움)
        sents = _parse_sentences(raw)
        if sents:
            passages.append(Passage(label="", title="", sentences=sents))
        return passages

    for k, (line_no, label, title) in enumerate(header_idx):
        body_start = line_no + 1
        body_end = header_idx[k + 1][0] if k + 1 < len(header_idx) else len(lines)
        body = "\n".join(lines[body_start:body_end])
        sents = _parse_sentences(body)
        passages.append(Passage(label=label, title=title, sentences=sents))

    return passages
