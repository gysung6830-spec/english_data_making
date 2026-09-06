"""ORTICA 3형식(한줄해석/좌지문우해석/직독직해/한줄영어) 양식 렌더.

passage3 앱의 렌더러/테마/모델을 그대로 가져오고, 마스터 분석(Analysis)을 이 양식의
Passage 모델로 변환하는 어댑터(analyses_to_passages)를 제공한다. 마스터 1회 분석 →
동일 양식으로 파생(추가 API 없음).
"""
from __future__ import annotations

import re

from .models import Chunk, Passage, Sentence, Vocab
from . import renderer

# 라벨 접미사: 'NN-A' 의 'A', 'NN-1' 의 '1' 등
_LABEL_SUFFIX = re.compile(r"-\s*([A-Za-z]+|\d+)\s*$")


def _ortica_badge(label: str) -> str:
    """마스터 lecture_label → ORTICA 뱃지 표기.

    - '01-A' → 'A'      (알파벳 접미사는 그대로)
    - '01-1' → '1번'    (숫자 접미사는 'N번')
    - '01-2' → '2번'
    - '서술형 Practice' → '서술형'
    - '논술형 Practice' → '논술형'
    - 그 외(범위 '41~42번' 등 포함)는 라벨 그대로.
    """
    s = (label or "").strip()
    if not s:
        return ""
    # 'xxx Practice' 꼬리 제거 (서술형/논술형 등)
    s = re.sub(r"\s*Practice\s*$", "", s, flags=re.IGNORECASE).strip()
    m = _LABEL_SUFFIX.search(s)
    if m:
        suf = m.group(1)
        return f"{int(suf)}번" if suf.isdigit() else suf
    return s

# 폼 키 → 렌더 함수 (ORTICA 양식 그대로)
FORMS = {
    "한줄해석": renderer.render_format_a,
    "한줄영어": renderer.render_format_c,
    "좌지문우해석": renderer.render_format_b,
    "직독직해": renderer.render_format_d,
}


def _en_chunks(sent) -> list[str]:
    out, cur = [], []
    for line in sent.lines:
        for t in line:
            cur.append(t.text)
            if getattr(t, "slash", False):
                out.append(" ".join(cur)); cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def analyses_to_passages(analyses) -> list[Passage]:
    """마스터 분석 목록 → ORTICA 양식 Passage 목록(재분석 없음).

    - en   : 문장 토큰을 이어 붙인 영어 원문
    - ko   : 문장 전체 해석(translation)
    - chunks: slash 경계 영어 조각 ↔ reading_ko 직독직해 조각(1:1일 때만)
    - vocab: 핵심 어휘(word/meaning)
    """
    passages: list[Passage] = []
    for a in analyses:
        sents: list[Sentence] = []
        for s in a.sentences:
            ecs = _en_chunks(s)
            kcs = [c.strip() for c in (getattr(s, "reading_ko", "") or "").split(" / ") if c.strip()]
            chunks = [Chunk(en=e, ko=k) for e, k in zip(ecs, kcs)] \
                if (kcs and len(kcs) == len(ecs)) else []
            sents.append(Sentence(num=getattr(s, "index", 0),
                                  en=" ".join(ecs).strip(),
                                  ko=getattr(s, "translation", "") or "",
                                  chunks=chunks))
        vocab = [Vocab(word=getattr(v, "word", ""), meaning=getattr(v, "meaning", ""))
                 for v in (getattr(a, "vocab", None) or [])
                 if getattr(v, "word", "")]
        passages.append(Passage(label=_ortica_badge(getattr(a, "lecture_label", "") or ""),
                                title=getattr(a, "title_ko", "") or getattr(a, "title_en", "") or "",
                                sentences=sents, vocab=vocab))
    return passages


def render_form_html(analyses, form_key: str, doc_name: str = "", theme: str = "") -> str:
    """선택한 양식(form_key)의 HTML 문서를 만든다."""
    passages = analyses_to_passages(analyses)
    fn = FORMS[form_key]
    return fn(passages, header_text="", theme=theme, doc_name=doc_name)
