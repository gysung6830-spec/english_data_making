"""변형문제 3회 생성 — 지문당 주제3·제목3·내용일치3·함축의미3(=12문항).

각 유형 슬롯(topic_1 …)은 같은 base 생성기를 '서로 다른 변형'으로 호출한다:
  · variant_hint 로 번호별로 다른 각도/오답을 유도(중복 방지),
  · answer_pos 를 변형마다 다르게 흩어 정답 위치도 겹치지 않게.
'함축의미'는 2회 B(함의추론) 생성기를 재사용한다.
검증(자기검증·부적합 플래그)은 base 로 정규화되어 그대로 적용된다.
"""
from __future__ import annotations

from pathlib import Path

from . import answer_spread, difficulty, renderer, validator
from ._concurrent import run_parallel
from .gen2 import _gen_B, _gen_one_type2
from .generators import content as _content
from .generators import title as _title
from .generators import topic as _topic
from .llm import ClaudeClient
from .set3 import (BASE_OF, PER, TYPE_LABELS3, TYPE_ORDER3, TYPE_PROMPTS3,
                   VARIANT_OF)
from .types import Passage


def _variant_hint(label: str, i: int) -> str:
    return (f"[변형 {i}/{PER}] 이것은 같은 지문에 대한 '{label}' 유형의 {i}번째 문제입니다. "
            f"같은 지문의 다른 번호 문제와 정답 표현·오답 선지가 겹치지 않도록 "
            f"서로 다른 각도·세부·어휘로 구성하세요.")


def _answer_pos(title: str, passage_index: int, slot: str) -> int:
    """3개 변형이 서로 다른 정답 위치를 받도록 흩는다(1~5)."""
    seed = answer_spread.seed_of(title)
    i = VARIANT_OF[slot]
    base_off = sum(ord(c) for c in BASE_OF[slot])
    return (seed + passage_index + base_off + (i - 1) * 2) % 5 + 1


def _base_generator(base: str, content_difficulty: str):
    """base 유형키 → gen2 스타일 시그니처 gen(client, analysis, body, max_retries, answer_pos)."""
    if base == "topic":
        return lambda c, a, b, max_retries, answer_pos, vh="": _topic.generate(
            c, a, b, max_retries=max_retries, answer_pos=answer_pos, variant_hint=vh)
    if base == "title":
        return lambda c, a, b, max_retries, answer_pos, vh="": _title.generate(
            c, a, b, max_retries=max_retries, answer_pos=answer_pos, variant_hint=vh)
    if base == "content":
        return lambda c, a, b, max_retries, answer_pos, vh="": _content.generate(
            c, a, b, max_retries=max_retries, difficulty=content_difficulty,
            answer_pos=answer_pos, variant_hint=vh)
    if base == "imply":
        return lambda c, a, b, max_retries, answer_pos, vh="": _gen_B(
            c, a, b, max_retries=max_retries, answer_pos=answer_pos, variant_hint=vh)
    raise ValueError(f"알 수 없는 base 유형: {base}")


def build_passage3(client, body, max_retries=1, logger=None, analysis=None,
                   level=None, passage_index=0) -> Passage:
    """3회 지문 1개 -> 12문항(주제3·제목3·내용일치3·함축의미3)."""
    from . import analyzer
    from . import review as _rv
    if analysis is None:
        analysis = analyzer.analyze(client, body, max_retries=max_retries)
    cdiff = difficulty.content_difficulty(level) if level else "hard"
    if level:
        analysis.difficulty_note = difficulty.clause(level)
    passage = Passage(title=analysis.title)

    def _task(slot):
        base = BASE_OF[slot]
        gen = _base_generator(base, cdiff)
        apos = _answer_pos(analysis.title, passage_index, slot)
        vh = _variant_hint(TYPE_LABELS3[slot], VARIANT_OF[slot])
        # _gen_one_type2(gen, ...) 는 gen(client, analysis, body, max_retries, answer_pos) 를 호출.
        # variant_hint 를 앞서 바인딩해 시그니처를 맞춘다.
        bound = lambda c, a, b, max_retries, answer_pos: gen(  # noqa: E731
            c, a, b, max_retries, answer_pos, vh)
        return lambda: _gen_one_type2(bound, client, analysis, body, base,
                                      max_retries, logger, apos)

    results = run_parallel([(slot, _task(slot)) for slot in TYPE_ORDER3])
    for slot in TYPE_ORDER3:
        q, a, fl = results[slot]
        passage.set_qa(slot, q, a)
        passage.flag(slot, fl)
        passage.flag(slot, _rv.type_fit_flags(getattr(analysis, "passage_type", "prose"), slot))
    validator.check_passage(passage, TYPE_ORDER3)
    return passage


def build_passages3(client, bodies, max_retries=1, logger=None, analyses=None,
                    level=None, labels=None) -> list:
    """3회 여러 지문 -> 검증된 Passage 리스트(조판 없음). 합본용."""
    from .pipeline import analyze_bodies
    if analyses is None:
        analyses = analyze_bodies(client, bodies, max_retries=max_retries, logger=logger)
    passages = []
    for i, (body, analysis) in enumerate(zip(bodies, analyses), 1):
        if logger:
            logger.info("[3회 %d/%d] 지문 생성 중 …", i, len(bodies))
        p = build_passage3(client, body, max_retries=max_retries, logger=logger,
                           analysis=analysis, level=level, passage_index=i - 1)
        if labels and i - 1 < len(labels):
            p.source_label = labels[i - 1]
        passages.append(p)
    validator.validate_passages(passages, TYPE_ORDER3)
    validator.validate_numbering(passages, 1, TYPE_ORDER3)
    return passages


def build_exam3(client, bodies, out_path, header_note="", max_retries=1, logger=None,
                analyses=None, level=None, sections=None, labels=None) -> Path:
    passages = build_passages3(client, bodies, max_retries=max_retries, logger=logger,
                               analyses=analyses, level=level, labels=labels)
    return renderer.render_pdf(passages, out_path, header_note=header_note,
                               type_order=TYPE_ORDER3, prompts=TYPE_PROMPTS3,
                               labels=TYPE_LABELS3, sections=sections)
