"""실전서 조립 — 코퍼스 매칭 → Claude 카드 생성 → Guide 객체.

- API 키가 있으면 실제 카드를 생성한다.
- 코드에 매칭된 기출 문장이 없으면 그 코드는 건너뛴다(빈 챕터 방지).
- 일부 카드가 실패해도 전체가 멈추지 않는다.
"""
from __future__ import annotations

import logging

from ..client import ClaudeClient
from . import prompts
from .codes import Category, load_categories
from .corpus import Match, collect_sentences, match_category
from .schemas import CardBodyOut, CodeCard, Chapter, Guide

log = logging.getLogger("guide")


def _make_card(client: ClaudeClient, cat: Category, m: Match,
               max_retries: int = 1) -> CodeCard | None:
    prompt = prompts.card_prompt(cat.title, cat.misread, m.code.en, m.code.ko, m.sentence)
    try:
        body = client.structured(prompts.SYSTEM, prompt, CardBodyOut,
                                  max_retries=max_retries)
    except Exception as e:  # 개별 카드 실패는 건너뜀
        log.warning("카드 생성 실패 [%s] %s: %s", cat.title, m.code.en, e)
        return None
    return CodeCard(code=m.code.en, code_ko=m.code.ko, dir=m.code.dir,
                    sentence=m.sentence, body=body)


def build_guide(client: ClaudeClient, corpus_dir, per_code: int = 1,
                max_retries: int = 1, codes_path=None) -> Guide:
    """코퍼스 폴더 → 실전서 Guide(1부: 평가원 코드 챕터들)."""
    sentences = collect_sentences(corpus_dir)
    log.info("코퍼스 문장 %d개 수집", len(sentences))
    cats = load_categories(codes_path)

    chapters: list[Chapter] = []
    for cat in cats:
        matches = match_category(cat, sentences, per_code=per_code)
        log.info("[%s] 매칭 문장 %d개", cat.title, len(matches))
        cards: list[CodeCard] = []
        for m in matches:
            card = _make_card(client, cat, m, max_retries=max_retries)
            if card:
                cards.append(card)
        if cards:
            chapters.append(Chapter(id=cat.id, title=cat.title, signal=cat.signal,
                                    misread=cat.misread, tip=cat.tip, cards=cards))
    return Guide(chapters=chapters)
