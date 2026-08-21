"""문항 생성 공통 뼈대 — 지문 분석과 '유형 1건 생성'.

지문 입력 → [분석] 1회 → [생성] 유형별 → [자기검증] → [조판] → [출력].
어떤 유형을 어떤 순서로 낼지는 merged.py(변형문제 통합본)가 정하고,
여기서는 '유형 하나를 어떻게 만드는가'만 담당한다.
"""
from __future__ import annotations

import re

from . import analyzer, answer_spread
from . import verify as _verify
from ._concurrent import run_parallel
from .generators import (
    content, grammar, grammar_count, insert, irrelevant, order, pair_odd,
    short_answer, title, topic, vocab,
)
from .llm import ClaudeClient
from .types import (
    CONTENT,
    GRAMMAR_COUNT,
    IRRELEVANT,
    PAIR_ODD,
    TITLE,
    VOCAB_2,
    VOCAB_3,
    GRAMMAR,
    INSERT,
    ORDER,
    SHORT_ANSWER,
    TOPIC,
    VOCAB,
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
    TITLE: title,
    IRRELEVANT: irrelevant,
    GRAMMAR_COUNT: grammar_count,
    PAIR_ODD: pair_odd,
}

# 어휘 슬롯키 -> 출제 방식. 한 지문에서 세 방식을 모두 낸다.
VOCAB_METHODS = {VOCAB: "synonym", VOCAB_2: "original", VOCAB_3: "negation"}


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


def _base(t: str) -> str:
    """슬롯키(vocab_2)를 생성기 표의 기본 유형키(vocab)로 되돌린다."""
    return re.sub(r"_\d+$", "", t or "")


def make_task(t, client, analysis, body, max_retries: int = 1, logger=None,
              content_difficulty: str = "hard",
              passage_index: int = 0, slots=None):
    """산문형 유형(주제·내용일치·어법·어휘·순서·삽입·서술형) 하나를 만드는 '무인자 함수'.

    slots 는 정답 위치 분산용 슬롯표. 생략하면 이 계열만 쓰던 옛 슬롯표를 쓴다.
    """
    gen = GENERATORS[_base(t)]
    kwargs: dict = {}
    if t in VOCAB_METHODS:
        kwargs["method"] = VOCAB_METHODS[t]
    elif t == CONTENT:
        kwargs["difficulty"] = content_difficulty
    slots = answer_spread.SLOTS1 if slots is None else slots
    # 선지 순서가 자유로운 유형은 정답 위치를 고르게 분산(몰림 방지)
    if t in slots:
        kwargs["answer_pos"] = answer_spread.pick(
            passage_index, slots[t], len(slots),
            seed=answer_spread.seed_of(analysis.title))
    return lambda: _gen_one_type(gen, client, analysis, body, t,
                                 max_retries, logger, kwargs)


def analyze_bodies(client: ClaudeClient, bodies: list[str], max_retries: int = 1,
                   logger=None) -> list:
    """여러 지문을 동시에 분석한다(모든 유형이 이 분석 하나를 공유한다)."""
    if logger:
        logger.info("지문 %d개 분석 중 …", len(bodies))
    tasks = [(i, (lambda b=b: analyzer.analyze(client, b, max_retries=max_retries)))
             for i, b in enumerate(bodies)]
    res = run_parallel(tasks)
    return [res[i] for i in range(len(bodies))]
