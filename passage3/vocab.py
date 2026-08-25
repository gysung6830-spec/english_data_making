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
    "high-school students. From a passage, select the words/phrases most worth "
    "studying, following these rules:\n"
    "1) CORE words first: pick the key content words essential to understanding "
    "the passage (핵심 단어 위주), not incidental ones.\n"
    "2) PRIORITIZE idioms, phrasal verbs, and set collocations "
    "(숙어·구동사·연어 우선) — include these before single common words when both "
    "are candidates.\n"
    "3) HIGH-SCHOOL level (고등학생 수준): choose words a Korean high schooler "
    "should learn — skip trivial basics (the, is, and, go, big…) AND skip "
    "overly obscure/technical terms a high schooler would never need.\n"
    "4) EXCLUDE proper nouns (고유명사 제외): no names of people, places, "
    "organizations, book/brand titles (e.g., Sonya Lyubomirsky, Prague, "
    "University College London).\n"
    "Give each entry's base/dictionary form and a concise Korean meaning as used "
    "in this passage's context. Return ONLY JSON."
)


def _count_for(passage: Passage) -> int:
    """지문 길이에 비례해 어휘 개수 결정(6~14)."""
    n = len(passage.sentences)
    return max(6, min(14, n + 2))


def extract_vocab(passages: List[Passage], model: str = DEFAULT_MODEL,
                  api_key: str = None, progress=None) -> List[Passage]:
    """각 지문에 핵심 어휘를 채운다. 키 없으면 그대로(빈 리스트)."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return passages

    try:
        import anthropic
    except ImportError:
        return passages

    client = anthropic.Anthropic(api_key=api_key)
    todo = [p for p in passages
            if not p.vocab and any(s.en for s in p.sentences)]
    total, done = len(todo), 0

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
            pass  # 한 지문 실패해도 나머지 진행
        done += 1
        if progress:
            progress(done, total)

    return passages
