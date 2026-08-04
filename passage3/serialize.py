"""분석 결과(지문/문장/어휘) ↔ JSON 직렬화.

목적: API로 한 번 분석(번역·어휘 추출)한 결과를 JSON으로 저장해 두고,
나중에 그 JSON을 다시 입력하면 재분석(=API 비용) 없이 제목만 바꿔 PDF를
다시 뽑을 수 있게 한다. (ORTICA 분석지 JSON 재입력 방식)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

try:
    from .parser import Passage, Sentence, Vocab
except ImportError:
    from parser import Passage, Sentence, Vocab

ORTICA_FORMAT = "ORTICA-3form"
ORTICA_VERSION = 1


def passages_to_dict(passages: List[Passage], docname: str = "") -> dict:
    return {
        "format": ORTICA_FORMAT,
        "version": ORTICA_VERSION,
        "docname": docname,
        "passages": [
            {
                # label/title 은 자유롭게 편집 가능(제목 변경용)
                "label": p.label,
                "title": p.title,
                "sentences": [
                    {"num": s.num, "en": s.en, "ko": s.ko} for s in p.sentences
                ],
                "vocab": [
                    {"word": v.word, "meaning": v.meaning} for v in p.vocab
                ],
            }
            for p in passages
        ],
    }


def passages_to_json(passages: List[Passage], docname: str = "") -> str:
    return json.dumps(passages_to_dict(passages, docname),
                      ensure_ascii=False, indent=2)


def passages_from_dict(data: dict) -> List[Passage]:
    out: List[Passage] = []
    for pd in (data.get("passages") or []):
        sents = [
            Sentence(num=int(s.get("num", 0) or 0),
                     en=(s.get("en") or "").strip(),
                     ko=(s.get("ko") or "").strip())
            for s in (pd.get("sentences") or [])
        ]
        voc = [
            Vocab(word=(v.get("word") or "").strip(),
                  meaning=(v.get("meaning") or "").strip())
            for v in (pd.get("vocab") or [])
            if (v.get("word") or "").strip()
        ]
        out.append(Passage(label=(pd.get("label") or "").strip(),
                           title=(pd.get("title") or "").strip(),
                           sentences=sents, vocab=voc))
    return out


def is_ortica_json(data) -> bool:
    return isinstance(data, dict) and "passages" in data


def load_passages_json(path) -> List[Passage]:
    """ORTICA 분석 JSON 파일 → 지문 리스트. 형식이 아니면 빈 리스트."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []
    if not is_ortica_json(data):
        return []
    return passages_from_dict(data)
