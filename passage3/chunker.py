"""직독직해(sense-group) 청크 생성.

각 문장을 '구와 절 사이' 크기의 의미 단위로 끊고, 청크마다 우리말 뜻을 단다.
영어 어순을 그대로 유지(직독직해)한다. ANTHROPIC_API_KEY(또는 폼 키)가
있어야 하며, 이미 청크가 있으면 건너뛴다(JSON 재입력 시 재생성 없음).
"""
from __future__ import annotations

import os
from typing import List

try:
    from .parser import Chunk, Passage
    from .translator import _extract_json
except ImportError:
    from parser import Chunk, Passage
    from translator import _extract_json

DEFAULT_MODEL = "claude-sonnet-5"

_SYSTEM = (
    "You are an English teacher making a 직독직해 (sense-group reading) worksheet "
    "for Korean students. Split an English sentence into sense units IN ENGLISH "
    "ORDER. For each unit give (1) the exact English substring — concatenating the "
    "units with single spaces must reproduce the original sentence verbatim (same "
    "words, punctuation, capitalization) — and (2) its Korean meaning for that unit. "
    "IMPORTANT — chunk size is MODERATE, between a phrase and a clause "
    "(구와 절 중간 정도): NOT word-by-word and NOT whole clauses only. Break at "
    "clause boundaries (relative/that/adverbial clauses, conjunctions joining "
    "clauses) AND at major phrase boundaries — a verb with its object/complement, a "
    "long (4+ word) prepositional phrase, a to-infinitive phrase, a participial "
    "phrase. But keep SHORT (1–3 word) phrases, articles, and single prepositions "
    "attached to their noun; do NOT break off a single word by itself. Aim for about "
    "one break per 4–6 words; a short sentence (≲8 words) gets about 1 break.\n"
    "TONE for the Korean (직독직해 연결형): plain declarative written style "
    "(문어체 평서형, 반말), NEVER 존댓말. Make the units read naturally in sequence — "
    "non-final units end with connective forms so they flow into the next "
    "(예: ~하여/~하고/~한 후/~인데/~것을/~기 위해/~때), and the LAST unit ends in "
    "'~다'. Keep each meaning concise and in English order. Return ONLY JSON."
)


def chunk_sentences(passages: List[Passage], model: str = DEFAULT_MODEL,
                    api_key: str = None, progress=None) -> List[Passage]:
    """각 문장에 직독직해 청크를 채운다. 키 없으면 그대로 둔다."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return passages
    try:
        import anthropic
    except ImportError:
        return passages

    client = anthropic.Anthropic(api_key=api_key)
    total = sum(1 for p in passages for s in p.sentences
                if not s.chunks and s.en.strip())
    done = 0

    for p in passages:
        for s in p.sentences:
            if s.chunks or not s.en.strip():
                continue  # 이미 있음 / 영어 없음
            user_msg = (
                "Split this sentence into 직독직해 sense units (phrase~clause "
                "sized), in English order. Return ONLY JSON: "
                '{"chunks":[{"en":"unit","ko":"그 단위의 뜻"}]}\n\n' + s.en.strip()
            )
            try:
                resp = client.messages.create(
                    model=model, max_tokens=1200, system=_SYSTEM,
                    messages=[{"role": "user", "content": user_msg}],
                )
                text = "".join(b.text for b in resp.content
                               if getattr(b, "type", "") == "text")
                data = _extract_json(text)
                items = data.get("chunks") if isinstance(data, dict) else data
                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, dict):
                            en, ko = it.get("en"), it.get("ko")
                        else:  # 문자열 응답 호환(뜻 없음)
                            en, ko = it, ""
                        en = (en or "").strip()
                        if en:
                            s.chunks.append(Chunk(en=en, ko=(ko or "").strip()))
            except Exception:
                pass  # 한 문장 실패해도 나머지 진행
            done += 1
            if progress:
                progress(done, total)
    return passages
