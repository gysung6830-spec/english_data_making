"""시험지 생성 파이프라인 (명세서 §5 동작 순서).

지문 입력 → [분석] 1회 → [생성] 6종 고정 순서 → [검증] → [조판] → [출력].
본체는 유형을 몰라도 TYPE_ORDER 대로 생성기를 실행만 하면 된다.
"""
from __future__ import annotations

from pathlib import Path

from . import analyzer, renderer, validator
from .generators import grammar, insert, order, short_answer, topic, vocab
from .llm import ClaudeClient
from .types import (
    GRAMMAR,
    INSERT,
    ORDER,
    SHORT_ANSWER,
    TOPIC,
    TYPE_ORDER,
    VOCAB,
    Passage,
)

# 유형 -> 생성기 모듈 (본체는 이 표만 보고 순서대로 실행)
GENERATORS = {
    ORDER: order,
    INSERT: insert,
    TOPIC: topic,
    VOCAB: vocab,
    GRAMMAR: grammar,
    SHORT_ANSWER: short_answer,
}


def build_passage(client: ClaudeClient, body: str, max_retries: int = 1,
                  logger=None) -> Passage:
    """지문 원문 1개 -> 6종 문제/해설이 채워진 Passage."""
    analysis = analyzer.analyze(client, body, max_retries=max_retries)
    passage = Passage(title=analysis.title)

    for t in TYPE_ORDER:  # 고정 순서
        gen = GENERATORS[t]
        # 유형별 재생성: 검증 실패(예외) 시 한 번 더 시도
        last_err: Exception | None = None
        for attempt in range(2):
            try:
                q, a = gen.generate(client, analysis, body, max_retries=max_retries)
                passage.set_qa(t, q, a)
                last_err = None
                break
            except Exception as e:  # noqa: BLE001 — 유형 단위 격리
                last_err = e
                if logger:
                    logger.warning("[%s] 생성 실패(시도 %d): %s", t, attempt + 1, e)
        if last_err is not None:
            raise RuntimeError(f"'{t}' 유형 생성 실패: {last_err}")

    # 생성 단계 검증(6종 완비 · 유형 집합 일치)
    rep = validator.check_passage(passage)
    if not rep.ok:
        raise RuntimeError(
            f"[{passage.title}] 검증 실패 — 문제누락:{rep.missing_q} 해설누락:{rep.missing_a}"
        )
    return passage


def build_exam(
    client: ClaudeClient,
    bodies: list[str],
    out_path: str | Path,
    header_note: str = "",
    max_retries: int = 1,
    logger=None,
) -> Path:
    """여러 지문 원문 -> 검증 -> 2단 PDF 한 개."""
    passages: list[Passage] = []
    for i, body in enumerate(bodies, 1):
        if logger:
            logger.info("[%d/%d] 지문 분석·생성 중 …", i, len(bodies))
        passages.append(build_passage(client, body, max_retries=max_retries, logger=logger))

    # 결과물 단계 검증(번호 연속 · 6종 완비)
    validator.validate_passages(passages)
    validator.validate_numbering(passages, start=1)

    return renderer.render_pdf(passages, out_path, header_note=header_note)
