"""직독직해(sense-group) 청크 생성.

각 문장을 '구와 절 사이' 크기의 의미 단위로 끊고, 청크마다 우리말 뜻을 단다.
영어 어순을 그대로 유지(직독직해)한다. ANTHROPIC_API_KEY(또는 폼 키)가
있어야 하며, 이미 청크가 있으면 건너뛴다(JSON 재입력 시 재생성 없음).
"""
from __future__ import annotations

import os
from typing import List

try:
    from .parser import Chunk, Passage, realign_chunks, rough_sense_split
    from .translator import _extract_json
except ImportError:
    from parser import Chunk, Passage, realign_chunks, rough_sense_split
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
    "CONSISTENT BREAK POSITION (very important — be uniform across the whole "
    "worksheet): ALWAYS start a new unit AT a subordinating conjunction or relative "
    "word, so that word BEGINS the next unit and never ends the previous one. This "
    "applies to: that, which, who, whom, whose, where, when, why, because, if, "
    "although, though, while, since, unless, so that, as. So write "
    "'they believe / that taste buds…' and 'studies showing / that when people…', "
    "NEVER 'they believe that / …' or 'studies showing that / …'. A unit must never "
    "end with a lone conjunction/relative word. Also break before a long (4+ word) "
    "prepositional phrase and before a to-infinitive phrase.\n"
    "INSERTED PHRASES: a phrase set off by paired dashes (—…—) or paired commas "
    "(,…,) is its OWN separate unit — do not merge it into the words around it.\n"
    "KEEP TOGETHER (do NOT break here): (a) DEMONSTRATIVE that/those pointing to a "
    "noun (that of the motorist, that field, that skill) stays attached — only a "
    "CLAUSE-leading that/relative starts a new unit; (b) a verb with its short "
    "object/complement; (c) an article or single preposition with its noun; "
    "(d) a 1–3 word phrase — never leave one English word alone as a unit.\n"
    "QUOTATIONS: keep quotation marks and punctuation exactly as in the original, "
    "and split the words inside a quote by the same rules.\n"
    "NEVER split a single word across two units (each unit's English must consist of "
    "whole words only). And in the Korean meaning, translate EVERY English word into "
    "Korean — do NOT leave an English word untranslated (예: 'embedded'는 '내재된/파묻힌' "
    "으로), except proper nouns, titles, or a word being discussed as a word.\n"
    "STRICT UNIT↔MEANING ALIGNMENT (핵심): each Korean meaning must translate ONLY "
    "the English words in that same unit — no more, no less. Do NOT pull in a verb, "
    "time-marker, or object that belongs to a later unit, and do NOT leave a unit's "
    "own words untranslated. Every English word is translated in exactly one unit, "
    "and the units' meanings appear in English order.\n"
    "TONE for the Korean — NATURAL 직독직해 (자연스러운 직독직해): plain written "
    "style (문어체 평서형, 반말), NEVER 존댓말, and it must read as NATURAL Korean, "
    "NOT stiff translationese (번역투 금지). Keep English word order across units, "
    "but each unit's Korean should sound like something a Korean would actually say "
    "for that fragment. A noun/prepositional/short phrase stays a natural PHRASE "
    "ending in a natural 조사 or 어미 — do NOT force it into a full predicate by "
    "tacking on '~이다/~것이다/~다'. Non-final units use natural connective endings "
    "that flow onward (~하는데/~하고/~해서/~하며/~하도록/~할 때/~하기 위해/~지만) or "
    "simply the natural phrase itself. The LAST unit should close the sentence "
    "naturally in 평서형 when it is the predicate (~다/~한다/~된다); if the sentence "
    "ends on a trailing phrase, use its natural form — do NOT bolt on an unnatural "
    "'다', and NEVER write '다다'.\n"
    "AVOID these stiff patterns → PREFER natural ones (examples):\n"
    "  'for the students.' → NOT '학생들에게 있어서다' → '학생들에게 (있어)'\n"
    "  'if you could come.' → NOT '만약 당신이 올 수 있다면이다' → '당신이 와 준다면'\n"
    "  'at Crestville High School.' → NOT '크레스트빌 고등학교의 교사다' → "
    "'크레스트빌 고등학교의'\n"
    "  'showing that …' → NOT '그것이 보여주는 것은' → '~을 보여 주는데'\n"
    "  'as the fifth child …' → NOT '다섯째 아이로 태어났다다' → '다섯째 아이로서'\n"
    "Keep each meaning concise and in English order. Return ONLY JSON."
)


def needs_chunks(s) -> bool:
    """이 문장이 직독직해 청크를 (다시) 생성해야 하는 상태인가.

    청크가 아예 없거나, 있어도 '뜻(ko)'이 통째로 비어 있으면(=en 조각만 있고
    청크별 해석이 없는 미완성) 재생성 대상. 뜻이 하나라도 있으면 완료로 본다.
    (webapp의 호출 게이트와 chunk_sentences 내부가 동일 조건을 쓰도록 공유.)
    """
    return bool(s.en.strip()) and (
        not s.chunks or not any(c.ko.strip() for c in s.chunks))


def any_needs_chunks(passages) -> bool:
    return any(needs_chunks(s) for p in passages for s in p.sentences)


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

    _needs_chunks = needs_chunks
    client = anthropic.Anthropic(api_key=api_key)
    total = sum(1 for p in passages for s in p.sentences if _needs_chunks(s))
    done = 0

    for p in passages:
        for s in p.sentences:
            if not _needs_chunks(s):
                continue  # 이미 뜻까지 있음 / 영어 없음
            user_msg = (
                "Split this sentence into 직독직해 sense units (phrase~clause "
                "sized), in English order. Return ONLY JSON: "
                '{"chunks":[{"en":"unit","ko":"그 단위의 뜻"}]}\n\n' + s.en.strip()
            )
            # 긴 문장은 청크가 많아 응답이 길다 → 길이에 비례해 토큰 확보
            # (부족하면 JSON이 잘려 파싱 실패 → 청크 0개가 되던 문제 방지)
            n_words = len(s.en.split())
            max_tokens = min(4096, max(1200, 400 + n_words * 60))
            # 실패(잘림/일시 오류) 시 재시도
            for attempt in range(2):
                try:
                    resp = client.messages.create(
                        model=model, max_tokens=max_tokens, system=_SYSTEM,
                        messages=[{"role": "user", "content": user_msg}],
                    )
                    text = "".join(b.text for b in resp.content
                                   if getattr(b, "type", "") == "text")
                    data = _extract_json(text)
                    items = data.get("chunks") if isinstance(data, dict) else data
                    got = []
                    if isinstance(items, list):
                        for it in items:
                            if isinstance(it, dict):
                                en, ko = it.get("en"), it.get("ko")
                            else:  # 문자열 응답 호환(뜻 없음)
                                en, ko = it, ""
                            en = (en or "").strip()
                            if en:
                                got.append(Chunk(en=en, ko=(ko or "").strip()))
                    # 뜻(ko)이 하나라도 있어야 성공으로 인정(en 조각만 온 응답은
                    # 재시도해서 청크별 해석을 채운다).
                    if got and any(c.ko for c in got):
                        s.chunks = got
                        break  # 성공
                    if got and not s.chunks:
                        s.chunks = got  # 뜻은 없지만 최소한 조각은 보존(폴백 대비)
                except Exception:
                    pass  # 재시도
                max_tokens = min(4096, max_tokens + 1200)  # 다음 시도는 더 넉넉히
            # 그래도 실패하면 규칙 기반으로 대략 끊는다(끊어읽기 누락 방지).
            # 청크별 뜻은 못 달지만(ko 비움), 렌더러가 문장 전체 해석을 보여 준다.
            if not s.chunks:
                pieces = rough_sense_split(s.en)
                s.chunks = [Chunk(en=p, ko="") for p in pieces] or \
                    [Chunk(en=s.en.strip(), ko="")]
            # 조각 텍스트를 원문에서 그대로 다시 잘라 100% 일치시킴
            s.chunks = realign_chunks(s.en, s.chunks)
            done += 1
            if progress:
                progress(done, total)
    return passages
