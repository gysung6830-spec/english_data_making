"""기출 코퍼스 처리 — 사용자가 넣은 기출 PDF/이미지에서 문장을 뽑고,
각 평가원 코드가 등장하는 문장을 '유형별로' 모은다.

핵심 역할(요청사항): 평가원 기출 문장들을 학습해 '비슷한 유형끼리' 모아 준다.
= 코드(기능어)별로 그 코드가 든 문장을 그룹핑.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .. import extract
from .codes import Category, Code

# 영어 문장 분리(약식): 마침표/물음표/느낌표 뒤 공백 기준, 약어 예외 최소 처리.
_ABBR = {"e.g", "i.e", "etc", "vs", "Mr", "Mrs", "Ms", "Dr", "St", "cf"}
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def split_sentences(text: str) -> list[str]:
    """영어 지문 텍스트를 문장 단위로 분리."""
    # 줄바꿈을 공백으로 정규화(문장이 줄을 넘길 수 있음)
    flat = re.sub(r"\s*\n\s*", " ", text)
    flat = re.sub(r"\s{2,}", " ", flat).strip()
    raw = _SENT_SPLIT.split(flat)
    out: list[str] = []
    for s in raw:
        s = s.strip()
        # 약어로 잘못 끊긴 조각을 앞 문장에 다시 붙임
        if out and out[-1].rstrip(".").split()[-1] in _ABBR:
            out[-1] = out[-1] + " " + s
            continue
        if len(re.sub(r"[^A-Za-z]", "", s)) >= 8:   # 알파벳 8자 미만은 잡음 취급
            out.append(s)
    return out


def read_corpus_text(path: str | Path) -> str:
    """PDF/텍스트 파일에서 텍스트를 뽑는다(이미지는 여기선 제외 — API 단계에서 처리)."""
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return extract.extract_raw_text(path)
    if path.suffix.lower() in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def collect_sentences(corpus_dir: str | Path) -> list[str]:
    """corpus_dir 안의 모든 PDF/텍스트에서 문장을 모아 중복 제거."""
    corpus_dir = Path(corpus_dir)
    seen: set[str] = set()
    sentences: list[str] = []
    if not corpus_dir.exists():
        return sentences
    for f in sorted(corpus_dir.iterdir()):
        if not f.is_file():
            continue
        text = read_corpus_text(f)
        for s in split_sentences(text):
            key = re.sub(r"\s+", " ", s.lower()).strip()
            if key not in seen:
                seen.add(key)
                sentences.append(s)
    return sentences


@dataclass
class Match:
    code: Code
    sentence: str
    hit: str        # 문장에서 실제 매칭된 부분


def match_category(category: Category, sentences: list[str],
                   per_code: int = 1) -> list[Match]:
    """한 카테고리의 각 코드에 대해, 그 코드가 든 문장을 per_code 개까지 모은다.

    → 결과가 곧 '유형별로 모인 기출 문장'.
    """
    matches: list[Match] = []
    used: set[str] = set()
    for code in category.codes:
        found = 0
        for s in sentences:
            if s in used:
                continue
            hit = code.matches(s)
            if hit:
                matches.append(Match(code=code, sentence=s, hit=hit))
                used.add(s)
                found += 1
                if found >= per_code:
                    break
    return matches
