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
class Chunk:
    en: str          # 영어 청크(구~절 사이 의미 단위)
    ko: str          # 그 청크의 우리말 뜻


@dataclass
class Sentence:
    num: int        # 문장 번호 (①→1)
    en: str         # 영어 원문
    ko: str = ""    # 한글 해석 (없으면 빈 문자열)
    chunks: List["Chunk"] = field(default_factory=list)  # 직독직해용 청크


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
    raw: str = ""                           # 번호 없는 지문 원문(문장 자동분리용)


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

# 대체 헤더:  '31번 …' / '41~42번 …' / '43~45번 …' 처럼 줄이 'N번' 또는
#   범위 'N~M번'으로 시작하는 형식 (EXAM4YOU 워크북 등. 콜론/대괄호 없음)
HEADER_RE2 = re.compile(r"^\s*(\d{1,3}(?:\s*[~∼\-]\s*\d{1,3})?)\s*번\b(.*)$")

# 대체 헤더:  'Ch. 05 Unit 13 - 1번: 제목' / 'Ch. 05 Unit 13 - 수능 대비 ANALYSIS: 제목'
#   (올림포스 등. Ch/Chapter/Unit/Lesson + 숫자로 시작하고 콜론이 있는 줄)
HEADER_RE3 = re.compile(
    r"(?i)^\s*((?:ch(?:apter)?|unit|lesson)\.?\s*\d[^:：\n]*?)\s*[:：]\s*(.+)$"
)

# 아라비아 숫자 문장 번호:  줄 시작의 'N. ' (원문자 대신 쓰는 자료)
_ARABIC_MARK_RE = re.compile(r"(?m)^[ \t]*(\d{1,2})\.[ \t]+")

# 각주 참조:  문장 끝의 '1)' '2)' 같은 위첨자 표기 제거
_FOOTNOTE_RE = re.compile(r"\s*\d{1,3}\)\s*$")

# 페이지 번호 줄:  '- 14 -', '14' 등
_PAGENUM_RE = re.compile(r"^\s*[-–—]?\s*\d{1,4}\s*[-–—]?\s*$")

# 자료 머리말/꼬리말·안내문(워터마크) 줄
_JUNK_RE = re.compile(
    r"(?i)(flowedu\.tistory|\[\s*flow\s*edu\s*\]|^\s*\[EBS\]|EXAM4YOU|"
    r"영문과\s*해석을\s*읽고|지문\s*연습하기|^\s*WORKBOOK\b)"
)

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
        if _JUNK_RE.search(line):
            continue  # [EBS]/[Flow Edu] 머리말·꼬리말 무시
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
            # 범위(41~42) 정규화: 구분자 주변 공백 제거
            num = re.sub(r"\s*[~∼\-]\s*", "~", m.group(1))
            return f"{num}번", _clean_title(rest)
    m = HEADER_RE3.match(line)
    if m:
        return _clean_title(m.group(1)), _clean_title(m.group(2))
    return None


def _starts_with_marker(line: str) -> bool:
    """줄이 문장 번호(원문자 또는 'N. ')로 시작하는가."""
    s = line.lstrip()
    if not s:
        return False
    if s[0] in CIRCLED_SET:
        return True
    return bool(re.match(r"\d{1,2}\.[ \t]", s))


def split_passages(raw: str) -> List[Passage]:
    """텍스트 전체 → 지문 리스트."""
    if not raw:
        return []

    # PDF 추출에서 섞이는 널문자/소프트하이픈을 공백으로 정규화
    raw = raw.replace("\x00", " ").replace("\xad", " ")

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
        body_lines = lines[body_start:body_end]

        body = "\n".join(body_lines)
        sents = _parse_sentences(body)
        # 번호가 없어 문장을 못 나눈 경우, 원문(잡음 제거)을 남겨 AI 문장분리에 사용
        raw = "" if sents else _clean_raw(body_lines)

        # 제목이 다음 줄로 이어지는 경우: 문장 마커가 있는 자료에서만 이어붙임
        # (번호 없는 통짜 지문은 본문 전체가 제목에 딸려가는 것을 방지)
        if sents:
            extra = []
            for bl in body_lines:
                if _starts_with_marker(bl):
                    break
                s = bl.strip()
                if s and not _JUNK_RE.search(s):
                    extra.append(s)
            if extra:
                title = _clean_title((title + " " + " ".join(extra)).strip())

        # 워크북 안내문 등 보일러플레이트만 있는 제목은 비운다
        if title and _JUNK_RE.search(title):
            title = ""

        # 같은 번호 헤더가 다음 페이지에 반복되면(장문 등) 이전 지문에 이어붙임
        if passages and label and passages[-1].label == label:
            passages[-1].sentences.extend(sents)
            if raw:
                passages[-1].raw = (passages[-1].raw + " " + raw).strip()
            if not passages[-1].title and title:
                passages[-1].title = title
        else:
            passages.append(Passage(label=label, title=title,
                                   sentences=sents, raw=raw))

    return passages


def _clean_raw(body_lines: List[str]) -> str:
    """번호 없는 지문 원문에서 안내문·페이지번호·널문자 등을 제거."""
    out = []
    for ln in body_lines:
        s = ln.replace("\x00", " ").strip()
        if not s or _JUNK_RE.search(s) or _PAGENUM_RE.match(s):
            continue
        out.append(s)
    return " ".join(out).strip()
