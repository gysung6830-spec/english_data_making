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


def _parse_sentences(body: str) -> List[Sentence]:
    """지문 본문 → 문장 리스트.

    원문자로 조각을 나눈 뒤 같은 번호는 병합한다.
    (예: 영어줄 ①… 다음에 한글줄 ①… 이 오면 하나로 합침)
    """
    # 원문자 위치 수집
    marks: List[Tuple[int, int]] = []  # (문자열 위치, 번호)
    for i, ch in enumerate(body):
        n = circled_to_int(ch)
        if n:
            marks.append((i, n))

    if not marks:
        return []

    # 원문자 앞의 서두(헤더 잔여물 등)는 버린다.
    chunks: List[Tuple[int, str]] = []
    for k, (pos, num) in enumerate(marks):
        start = pos + 1
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body)
        chunks.append((num, body[start:end]))

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
        if not en and not ko:
            continue
        sentences.append(Sentence(num=num, en=en, ko=ko))
    return sentences


def split_passages(raw: str) -> List[Passage]:
    """텍스트 전체 → 지문 리스트."""
    if not raw:
        return []

    lines = raw.splitlines()

    # 헤더 줄 위치 찾기
    header_idx: List[Tuple[int, str, str]] = []  # (줄번호, label, title)
    for i, line in enumerate(lines):
        m = HEADER_RE.search(line)
        if m:
            label = m.group(1).strip()
            title = m.group(3).strip()
            header_idx.append((i, label, title))

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
