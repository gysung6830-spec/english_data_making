"""시험지 생성 파이프라인 (명세서 §5 동작 순서).

지문 입력 → [분석] 1회 → [생성] 6종 고정 순서 → [검증] → [조판] → [출력].
본체는 유형을 몰라도 TYPE_ORDER 대로 생성기를 실행만 하면 된다.
"""
from __future__ import annotations

from pathlib import Path

from . import analyzer, answer_spread, difficulty, renderer, validator
from . import verify as _verify
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
    """한 유형을 생성. 구조 검증 실패 시 재시도, 고위험 유형은 LLM 자기검증까지.

    반환 (q, a, flags), 또는 최종 실패 시 None(그 문항만 건너뛰고 나머지는 살린다).
    자기검증에 두 번 실패하면 문항은 유지하되 '확인 권장' 사유를 단다.
    """
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            q, a, fl = gen.generate(client, analysis, body, max_retries=max_retries, **kwargs)
        except Exception as e:  # noqa: BLE001 — 유형 단위 격리
            last_err = e
            if logger:
                logger.warning("[%s] 생성 실패(시도 %d): %s", t, attempt + 1, e)
            continue
        ok, reason = _verify.verify(client, t, q, a, max_retries=max_retries)
        if not ok:
            if attempt == 0:      # 한 번은 재생성으로 결함을 털어낸다
                if logger:
                    logger.info("[%s] 자기검증 실패 → 재생성: %s", t, reason)
                continue
            fl = list(fl) + [f"자동검증: {reason or '정답 유일성·정오답 재확인'}"]
        return q, a, fl
    # 재시도 소진 — 지문 전체를 버리지 않고 이 유형만 건너뛴다.
    if logger:
        logger.error("[%s] 최종 생성 실패 — 이 문항은 제외합니다: %s", t, last_err)
    return None
    raise RuntimeError(f"'{t}' 유형 생성 실패: {last_err}")


def build_passage(client: ClaudeClient, body: str, max_retries: int = 1,
                  logger=None, vocab_method: str = "synonym",
                  content_difficulty: str = "hard", analysis=None,
                  level: str | None = None, passage_index: int = 0) -> Passage:
    """지문 원문 1개 -> 7종 문제/해설이 채워진 Passage.

    유형 7종은 서로 독립이므로 스레드로 동시에 생성한다(속도).
    analysis 를 주면 분석 호출을 건너뛴다(1회·2회 교차 공유용).
    level(상/중/하)을 주면 난이도와 함께 어휘 방식도 자동 결정한다
    (상=부정어삽입 · 중=유의어 · 하=원문단어).
    passage_index 로 정답 위치를 지문마다 다르게 분산한다(정답 번호 몰림 방지).
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
        # 선지 순서가 자유로운 유형은 정답 위치를 고르게 분산(몰림 방지)
        if t in answer_spread.SLOTS1:
            kwargs["answer_pos"] = answer_spread.pick(
                passage_index, answer_spread.SLOTS1[t], len(answer_spread.SLOTS1),
                seed=answer_spread.seed_of(analysis.title, level))
        return lambda: _gen_one_type(gen, client, analysis, body, t,
                                     max_retries, logger, kwargs)

    results = run_parallel([(t, _task(t)) for t in TYPE_ORDER])
    from . import review as _rv
    for t in TYPE_ORDER:  # 고정 순서로 채워 넣기(수거는 완료순이라도 조립은 순서대로)
        res = results.get(t)
        if res is None:      # 이 유형은 최종 생성 실패 → 건너뛰고 나머지는 살린다
            continue
        q, a, fl = res
        passage.set_qa(t, q, a)
        passage.flag(t, fl)   # '확인 권장'(자동 보정·오답 근거 약함) 사유가 있으면 기록
        # 지문 종류에 부적합한 유형(안내문·도표의 순서/삽입, 서사문의 주제 등)도 검수 표시
        passage.flag(t, _rv.type_fit_flags(getattr(analysis, "passage_type", "prose"), t))

    if not passage.q:     # 한 유형도 못 만들었을 때만 실패로 본다
        raise RuntimeError(f"[{passage.title}] 모든 유형 생성 실패")
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
    if logger:
        logger.info("지문 %d개 생성 중 …", len(bodies))
    # 지문끼리도 동시에 처리한다. 실제 동시 API 호출 수는 클라이언트의 전체 상한으로
    # 묶이므로, 한 지문의 마지막 호출을 기다리며 노는 시간이 사라진다.
    tasks = [(i, (lambda b=body, a=analysis, i=i: build_passage(
        client, b, max_retries=max_retries, logger=logger,
        vocab_method=vocab_method, content_difficulty=content_difficulty,
        analysis=a, level=level, passage_index=i)))
        for i, (body, analysis) in enumerate(zip(bodies, analyses))]
    res = run_parallel(tasks)
    passages: list[Passage] = []
    for i in range(len(bodies)):
        passage = res[i]
        if labels and i < len(labels):
            passage.source_label = labels[i]
        passages.append(passage)
    validator.validate_passages(passages)
    validator.validate_numbering(passages, start=1)
    return passages
