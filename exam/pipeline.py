"""시험지 생성 파이프라인 (명세서 §5 동작 순서).

지문 입력 → [분석] 1회 → [생성] 6종 고정 순서 → [검증] → [조판] → [출력].
본체는 유형을 몰라도 TYPE_ORDER 대로 생성기를 실행만 하면 된다.
"""
from __future__ import annotations

from pathlib import Path

from . import analyzer, difficulty, renderer, validator
from ._concurrent import run_parallel
from .generators import content, grammar, insert, order, short_answer, topic, vocab
from .llm import ClaudeClient
from .types import (
    CONTENT,
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
    CONTENT: content,
    SHORT_ANSWER: short_answer,
}


def _gen_one_type(gen, client, analysis, body, t, max_retries, logger, kwargs):
    """한 유형을 생성(검증 실패 시 한 번 더 재시도). (q, a) 반환."""
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            return gen.generate(client, analysis, body, max_retries=max_retries, **kwargs)
        except Exception as e:  # noqa: BLE001 — 유형 단위 격리
            last_err = e
            if logger:
                logger.warning("[%s] 생성 실패(시도 %d): %s", t, attempt + 1, e)
    raise RuntimeError(f"'{t}' 유형 생성 실패: {last_err}")


def build_passage(client: ClaudeClient, body: str, max_retries: int = 1,
                  logger=None, vocab_method: str = "synonym",
                  content_difficulty: str = "hard", analysis=None,
                  level: str | None = None) -> Passage:
    """지문 원문 1개 -> 7종 문제/해설이 채워진 Passage.

    유형 7종은 서로 독립이므로 스레드로 동시에 생성한다(속도).
    analysis 를 주면 분석 호출을 건너뛴다(1회·2회 교차 공유용).
    level(상/중/하)을 주면 난이도와 함께 어휘 방식도 자동 결정한다
    (상=부정어삽입 · 중=유의어 · 하=원문단어).
    """
    if analysis is None:
        analysis = analyzer.analyze(client, body, max_retries=max_retries)
    vm = vocab_method
    if level:  # 난이도 지침을 분석 결과에 심어 모든 생성기에 공통 전달(병렬 팬아웃 전 단일 스레드)
        analysis.difficulty_note = difficulty.clause(level)
        content_difficulty = difficulty.content_difficulty(level)
        vm = difficulty.vocab_method(level)   # 어휘 방식도 난이도에 연동
    passage = Passage(title=analysis.title)

    def _task(t):
        gen = GENERATORS[t]
        kwargs: dict = {}
        if t == VOCAB:
            kwargs["method"] = vm
        elif t == CONTENT:
            kwargs["difficulty"] = content_difficulty
        return lambda: _gen_one_type(gen, client, analysis, body, t,
                                     max_retries, logger, kwargs)

    results = run_parallel([(t, _task(t)) for t in TYPE_ORDER])
    for t in TYPE_ORDER:  # 고정 순서로 채워 넣기(수거는 완료순이라도 조립은 순서대로)
        q, a, fl = results[t]
        passage.set_qa(t, q, a)
        passage.flag(t, fl)   # '확인 권장'(자동 보정·오답 근거 약함) 사유가 있으면 기록

    # 생성 단계 검증(7종 완비 · 유형 집합 일치)
    rep = validator.check_passage(passage)
    if not rep.ok:
        raise RuntimeError(
            f"[{passage.title}] 검증 실패 — 문제누락:{rep.missing_q} 해설누락:{rep.missing_a}"
        )
    return passage


def analyze_bodies(client: ClaudeClient, bodies: list[str], max_retries: int = 1,
                   logger=None) -> list:
    """여러 지문을 동시에 분석한다(1회·2회가 같은 분석을 공유하도록 재사용 가능)."""
    if logger:
        logger.info("지문 %d개 분석 중 …", len(bodies))
    tasks = [(i, (lambda b=b: analyzer.analyze(client, b, max_retries=max_retries)))
             for i, b in enumerate(bodies)]
    res = run_parallel(tasks)
    return [res[i] for i in range(len(bodies))]


def build_exam(
    client: ClaudeClient,
    bodies: list[str],
    out_path: str | Path,
    header_note: str = "",
    max_retries: int = 1,
    logger=None,
    vocab_method: str = "synonym",
    content_difficulty: str = "hard",
    analyses: list | None = None,
    level: str | None = None,
    sections=None,
    labels: list[str] | None = None,
) -> Path:
    """여러 지문 원문 -> 검증 -> 2단 PDF 한 개.

    analyses 를 주면 분석 단계를 건너뛴다(교차 세트 공유).
    지문은 순서대로 조판하되, 각 지문 안의 유형 7종은 병렬로 생성한다.
    level(상/중/하)로 전체 난이도를 조절한다. labels 로 지문 라벨(문항번호)을 지정.
    """
    passages = build_passages(client, bodies, max_retries=max_retries, logger=logger,
                              vocab_method=vocab_method, content_difficulty=content_difficulty,
                              analyses=analyses, level=level, labels=labels)
    return renderer.render_pdf(passages, out_path, header_note=header_note,
                               sections=sections)


def build_passages(
    client: ClaudeClient,
    bodies: list[str],
    max_retries: int = 1,
    logger=None,
    vocab_method: str = "synonym",
    content_difficulty: str = "hard",
    analyses: list | None = None,
    level: str | None = None,
    labels: list[str] | None = None,
) -> list[Passage]:
    """여러 지문 -> 검증된 Passage 리스트(조판은 하지 않음). 합본용.

    labels 를 주면 각 지문의 라벨(원본 PDF 문항번호 등)을 조판 라벨로 쓴다.
    """
    if analyses is None:
        analyses = analyze_bodies(client, bodies, max_retries=max_retries, logger=logger)
    passages: list[Passage] = []
    for i, (body, analysis) in enumerate(zip(bodies, analyses), 1):
        if logger:
            logger.info("[%d/%d] 지문 생성 중 …", i, len(bodies))
        passage = build_passage(client, body, max_retries=max_retries,
                                logger=logger, vocab_method=vocab_method,
                                content_difficulty=content_difficulty,
                                analysis=analysis, level=level)
        if labels and i - 1 < len(labels):
            passage.source_label = labels[i - 1]
        passages.append(passage)
    validator.validate_passages(passages)
    validator.validate_numbering(passages, start=1)
    return passages
