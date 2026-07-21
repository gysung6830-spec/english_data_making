"""실전서 조립 — 코퍼스 매칭 → Claude 카드 생성 → Guide 객체.

- API 키가 있으면 실제 카드를 생성한다.
- 코드에 매칭된 기출 문장이 없으면 그 코드는 건너뛴다(빈 챕터 방지).
- 일부 카드가 실패해도 전체가 멈추지 않는다.
"""
from __future__ import annotations

import logging

from ..client import ClaudeClient
from . import prompts
from .codes import Category, load_categories, load_part0
from .corpus import Match, collect_sourced, match_category
from .schemas import (CardBodyOut, CodeCard, Chapter, Guide, Part2,
                      SyntaxBodyOut, SyntaxCard, SyntaxChapter)
from .syntax import SYNTAX_TYPES, group_by_syntax

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
                    sentence=m.sentence, source=m.source, body=body)


def _make_syntax_card(client: ClaudeClient, st, sm,
                      max_retries: int = 1) -> SyntaxCard | None:
    prompt = prompts.syntax_card_prompt(st.title, st.formula, sm.sentence)
    try:
        body = client.structured(prompts.SYNTAX_SYSTEM, prompt, SyntaxBodyOut,
                                 max_retries=max_retries)
    except Exception as e:
        log.warning("구문 카드 실패 [%s]: %s", st.title, e)
        return None
    return SyntaxCard(sentence=sm.sentence, structure=st.title, source=sm.source, body=body)


def build_part2(client: ClaudeClient, sentences=None, per_type: int = 2,
                max_retries: int = 1) -> Part2:
    """3부 구문해석 — 해석공식 시각화(3 PART 그룹). 개념·공식·예문은 syntax_formula.yaml에서.

    (실전적용 문제 생성은 후속 단계에서 각 챕터에 붙인다.)
    """
    from .codes import load_part2_workbook
    return load_part2_workbook()


def build_guide(client: ClaudeClient, corpus_dir, per_code: int = 1,
                max_retries: int = 1, codes_path=None,
                include_part0: bool = True, include_part2: bool = True,
                per_type: int = 2) -> Guide:
    """코퍼스 폴더 → 실전서 Guide(0부 기본기 + 1부 평가원 코드 + 2부 구문해석)."""
    sentences = collect_sourced(corpus_dir)
    log.info("코퍼스 문장 %d개 수집(출처 포함)", len(sentences))
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
                                    misread=cat.misread, tip=cat.tip, cards=cards,
                                    core_tip=cat.core_tip, infer_tip=cat.infer_tip))

    part0 = load_part0() if include_part0 else None
    part2 = (build_part2(client, sentences, per_type=per_type, max_retries=max_retries)
             if include_part2 else None)
    return Guide(part0=part0, chapters=chapters, part2=part2)
