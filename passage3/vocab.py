"""지문에서 핵심 어휘를 뽑아 (영어 단어 / 한글 뜻) 리스트를 만든다(선택).

ANTHROPIC_API_KEY(또는 폼에서 받은 키)가 있으면 Claude 로 핵심 어휘를
추출한다. 키가 없으면 아무 것도 하지 않고(빈 리스트) 그대로 둔다 →
렌더러는 빈 어휘 박스를 그린다.
"""
from __future__ import annotations

import json
import os
from typing import List

try:
    from .parser import Passage, Vocab
    from .translator import _extract_json
except ImportError:
    from parser import Passage, Vocab
    from translator import _extract_json

DEFAULT_MODEL = "claude-sonnet-5"

_SYSTEM = (
    "You are an English teacher preparing a vocabulary list for Korean "
    "high-school students. From a passage, pick the most useful/difficult "
    "words or short phrases worth studying. Give each word's base form and a "
    "concise Korean meaning as used in the passage's context. Do not include "
    "trivial words (the, is, and, etc.). Return ONLY JSON."
)


def _count_for(passage: Passage) -> int:
    """지문 길이에 비례해 어휘 개수 결정(6~14)."""
    n = len(passage.sentences)
    return max(6, min(14, n + 2))


def extract_vocab(passages: List[Passage], model: str = DEFAULT_MODEL,
                  api_key: str = None) -> List[Passage]:
    """각 지문에 핵심 어휘를 채운다. 키 없으면 그대로(빈 리스트)."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return passages

    try:
        import anthropic
    except ImportError:
        return passages

    client = anthropic.Anthropic(api_key=api_key)

    for p in passages:
        if p.vocab:  # 이미 있으면 건너뜀
            continue
        english = " ".join(s.en for s in p.sentences if s.en).strip()
        if not english:
            continue
        count = _count_for(p)
        user_msg = (
            f"Select {count} key vocabulary items from this passage. "
            'Return ONLY JSON: {"vocab":[{"word":"...","meaning":"한글 뜻"}]}\n\n'
            + english
        )
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=1500,
                system=_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = "".join(
                b.text for b in resp.content if getattr(b, "type", "") == "text"
            )
            data = _extract_json(text)
            items = data.get("vocab") if isinstance(data, dict) else data
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("word"):
                        p.vocab.append(Vocab(
                            word=str(it.get("word", "")).strip(),
                            meaning=str(it.get("meaning", "")).strip(),
                        ))
        except Exception:
            continue  # 한 지문 실패해도 나머지 진행

    return passages
