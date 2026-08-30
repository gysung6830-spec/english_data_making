"""번호 없는 통짜 지문(좌 영어 / 우 한글)을 문장 단위로 자동 분리.

'지문 연습하기'처럼 ①②③ 번호가 없고 영어·한글이 (2단 추출로) 뒤섞인
원문을 Claude에 주어 (영어문장, 한글해석) 쌍으로 재구성한다. 키가 있어야
하며, 이미 문장이 있는 지문(번호 있는 자료)은 건드리지 않는다.
"""
from __future__ import annotations

import os
from typing import List

try:
    from .parser import Passage, Sentence
    from .translator import _extract_json
except ImportError:
    from parser import Passage, Sentence
    from translator import _extract_json

DEFAULT_MODEL = "claude-sonnet-5"

_SYSTEM = (
    "You are given the text of ONE English reading passage together with its "
    "Korean translation, extracted from a two-column worksheet, so the English and "
    "Korean are interleaved/jumbled and there are no sentence numbers. Reconstruct "
    "the passage as an ORDERED list of sentences. For each sentence give the full, "
    "clean English sentence (join words split across lines; fix broken spacing) and "
    "its full Korean translation. Keep the original wording; do NOT summarize, add, "
    "or drop sentences. Ignore any leftover instruction text or headers.\n"
    "CRITICAL PAIRING RULES (the input is jumbled, so be careful):\n"
    "1. Within each sentence object, the 'en' and 'ko' MUST be translations of each "
    "other — the same sentence. Never pair an English sentence with the Korean of a "
    "different (neighboring) sentence. If a boundary is ambiguous, re-read both "
    "columns and align by meaning, not by position.\n"
    "2. NEVER split a proper noun / leading subject away from its sentence. A name at "
    "a sentence start (e.g. 'Ethan and Sean set off...') stays WITH that sentence; do "
    "not leave it dangling at the end of the previous one or duplicate it.\n"
    "3. Every 'en' must be a complete sentence — NEVER output an empty 'en'. Every "
    "'ko' must be a complete Korean sentence and must NEVER begin with a dangling "
    "particle/조사 (과, 와, 은, 는, 이, 가, 을, 를, 에, 도) — that means a leading noun "
    "was wrongly cut off; restore it.\n"
    "4. The number of sentences, and their order, must match the passage exactly.\n"
    "Return ONLY JSON."
)


def segment_passages(passages: List[Passage], model: str = DEFAULT_MODEL,
                     api_key: str = None, progress=None) -> List[Passage]:
    """번호 없는 지문(raw 있음·문장 없음)을 AI로 문장 분리해 채운다."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return passages
    try:
        import anthropic
    except ImportError:
        return passages

    client = anthropic.Anthropic(api_key=api_key)
    todo = [p for p in passages if not p.sentences and p.raw.strip()]
    total, done = len(todo), 0

    for p in passages:
        if p.sentences or not p.raw.strip():
            continue
        user_msg = (
            'Reconstruct into ordered sentences. Return ONLY JSON: '
            '{"sentences":[{"en":"...","ko":"..."}]}\n\n' + p.raw.strip()
        )
        try:
            resp = client.messages.create(
                model=model, max_tokens=4000, system=_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = "".join(b.text for b in resp.content
                           if getattr(b, "type", "") == "text")
            data = _extract_json(text)
            items = data.get("sentences") if isinstance(data, dict) else data
            if isinstance(items, list):
                n = 0
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    en = (it.get("en") or "").strip()
                    ko = (it.get("ko") or "").strip()
                    if en:
                        n += 1
                        p.sentences.append(Sentence(num=n, en=en, ko=ko))
                if p.sentences:
                    p.raw = ""  # 분리 성공 시 원문 비움
        except Exception:
            pass
        done += 1
        if progress:
            progress(done, total)
    return passages
