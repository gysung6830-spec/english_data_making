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
    from .parser import Chunk, Passage, Sentence, Vocab, _JUNK_RE
except ImportError:
    from parser import Chunk, Passage, Sentence, Vocab, _JUNK_RE

ORTICA_FORMAT = "ORTICA-3form"
ORTICA_VERSION = 1

# 제목이 이 길이를 넘으면 지문 본문이 잘못 섞여 들어간 것으로 보고 비운다.
_MAX_TITLE_LEN = 120


def _sane_title(title: str) -> str:
    """재입력 JSON의 오염된 제목 정리.

    (구버전 파서가 만든) 지문 전체가 들어간 긴 제목이나 잡줄(워터마크·안내문)이
    섞인 제목은 비운다. 정상적인 짧은 제목은 그대로 둔다.
    """
    title = (title or "").strip()
    if not title:
        return ""
    if len(title) > _MAX_TITLE_LEN or _JUNK_RE.search(title):
        return ""
    return title


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
                    {
                        "num": s.num, "en": s.en, "ko": s.ko,
                        **({"chunks": [{"en": c.en, "ko": c.ko}
                                       for c in s.chunks]} if s.chunks else {}),
                    }
                    for s in p.sentences
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
        sents = []
        for s in (pd.get("sentences") or []):
            chunks = [
                Chunk(en=(c.get("en") or "").strip(),
                      ko=(c.get("ko") or "").strip())
                for c in (s.get("chunks") or [])
                if (c.get("en") or "").strip()
            ]
            sents.append(Sentence(
                num=int(s.get("num", 0) or 0),
                en=(s.get("en") or "").strip(),
                ko=(s.get("ko") or "").strip(),
                chunks=chunks,
            ))
        voc = [
            Vocab(word=(v.get("word") or "").strip(),
                  meaning=(v.get("meaning") or "").strip())
            for v in (pd.get("vocab") or [])
            if (v.get("word") or "").strip()
        ]
        out.append(Passage(label=(pd.get("label") or "").strip(),
                           title=_sane_title(pd.get("title") or ""),
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
