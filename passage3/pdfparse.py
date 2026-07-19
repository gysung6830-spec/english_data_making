"""표 레이아웃을 인식하는 PDF 파서.

교재/워크북 PDF는 대개 '좌 영어 / 우 한글' 2단 표로 되어 있다. 이때
pdfplumber 의 기본 extract_text() 는 표의 좌우 칸을 행 단위로 가로질러
읽어서 영어와 한글이 뒤섞인다. 이 모듈은 표 구조(extract_tables)를 직접
읽어, 어떤 형식이든 항상 '깨끗한 (영어 / 한글) 문장 쌍'으로 정규화한다.

표가 없거나 문장을 못 찾으면 None 을 반환한다(호출부에서 텍스트 파서로
폴백).
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

try:
    from .parser import (CIRCLED_SET, Passage, Sentence, circled_to_int,
                         _count_hangul)
except ImportError:  # 스크립트로 직접 실행할 때
    from parser import (CIRCLED_SET, Passage, Sentence, circled_to_int,
                        _count_hangul)


def _norm(s: str) -> str:
    """개행·중복 공백 정리."""
    return " ".join((s or "").split())


def _first_circled_cell(cells: List[str]) -> Optional[str]:
    """원문자로 시작하는(=영어 문장) 칸을 찾는다."""
    for c in cells:
        cc = c.lstrip()
        if cc and cc[0] in CIRCLED_SET:
            return c
    return None


def _first_hangul_cell(cells: List[str], exclude: str) -> str:
    """한글이 든(=해석) 칸을 찾는다(영어 칸 제외)."""
    for c in cells:
        if c is exclude:
            continue
        if _count_hangul(c) >= 2:
            return c
    return ""


def _split_header(text: str) -> Tuple[str, str]:
    """헤더 문자열 → (라벨, 제목). 첫 콜론 기준 분리."""
    text = _norm(text)
    m = re.search(r"[:：]", text)
    if m:
        return text[:m.start()].strip(), text[m.end():].strip()
    return "", text


def _cell_sentences(en_cell: str, ko_cell: str) -> List[Sentence]:
    """영어 칸(+한글 칸) → 문장 리스트. 보통 한 칸에 한 문장."""
    en_cell = _norm(en_cell)
    ko = _norm(ko_cell)
    marks = [(i, circled_to_int(ch)) for i, ch in enumerate(en_cell)
             if ch in CIRCLED_SET]
    if not marks:
        return [Sentence(num=0, en=en_cell, ko=ko)] if en_cell else []
    out: List[Sentence] = []
    for k, (pos, num) in enumerate(marks):
        start = pos + 1
        end = marks[k + 1][0] if k + 1 < len(marks) else len(en_cell)
        en = en_cell[start:end].strip()
        # 해석은 첫 문장에만 붙인다(한 칸=한 문장이 일반적)
        out.append(Sentence(num=num, en=en, ko=ko if k == 0 else ""))
    return out


def _looks_like_header(cells: List[str]) -> bool:
    """헤더 후보 행인가(원문자 없음 + 제목/번호 형태)."""
    joined = _norm(" ".join(cells))
    if not joined:
        return False
    if any(c.lstrip()[:1] in CIRCLED_SET for c in cells if c.strip()):
        return False
    # 'N번:' 또는 ':' 가 있는 제목 줄, 또는 'ANALYSIS' 등
    return bool(re.search(r"\d+\s*번", joined) or "：" in joined or ":" in joined)


def pdf_to_passages(path) -> Optional[List[Passage]]:
    """표 인식으로 PDF → 지문 리스트. 실패 시 None."""
    try:
        import pdfplumber
    except ImportError:
        return None

    passages: List[Passage] = []
    current: Optional[Passage] = None

    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue
                for table in tables:
                    header_parts: List[str] = []
                    seen_sentence = False
                    for row in table:
                        cells = [_norm(c) for c in row if c and c.strip()]
                        if not cells:
                            continue
                        en_cell = _first_circled_cell(cells)
                        if en_cell is None:
                            # 문장 전이면 헤더 후보로 모은다
                            if not seen_sentence and _looks_like_header(cells):
                                header_parts.extend(cells)
                            elif not seen_sentence:
                                header_parts.extend(
                                    c for c in cells if len(c) > 1)
                            continue
                        # 문장 행
                        if not seen_sentence:
                            seen_sentence = True
                            if header_parts:
                                label, title = _split_header(
                                    " ".join(header_parts))
                                current = Passage(label=label, title=title)
                                passages.append(current)
                            elif current is None:
                                current = Passage(label="", title="")
                                passages.append(current)
                            # header_parts 없고 current 있으면 이어지는 지문으로 간주
                        ko_cell = _first_hangul_cell(cells, en_cell)
                        for s in _cell_sentences(en_cell, ko_cell):
                            current.sentences.append(s)
    except Exception:
        return None

    if passages and any(p.sentences for p in passages):
        # 문장이 하나도 없는 빈 지문은 제거
        return [p for p in passages if p.sentences]
    return None
