"""ORTICA 3형식(한줄해석/좌지문우해석/직독직해/한줄영어) 렌더용 데이터 모델.

passage3 앱(브랜치 claude/english-passage-pdf-generator-snym2i)의 parser.py 에서
렌더에 필요한 순수 dataclass 만 옮겨온 것. 마스터 분석(Analysis)을 이 모델로
어댑터(to_forms.py)가 변환해 동일한 양식으로 렌더한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    en: str          # 영어 청크(의미 단위)
    ko: str          # 그 청크의 우리말 뜻


@dataclass
class Sentence:
    num: int
    en: str
    ko: str = ""
    chunks: List["Chunk"] = field(default_factory=list)


@dataclass
class Vocab:
    word: str
    meaning: str


@dataclass
class Passage:
    label: str
    title: str
    sentences: List["Sentence"] = field(default_factory=list)
    vocab: List["Vocab"] = field(default_factory=list)
