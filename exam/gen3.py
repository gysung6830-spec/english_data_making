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
from .set3 import (BASE_OF, COUNT_OF, TYPE_LABELS3, TYPE_ORDER3, TYPE_PROMPTS3,
                   VARIANT_OF)
from .types import Passage


# 유형별 '변형 각도' — 같은 지문에서 3문항이 겹치지 않도록 변형마다 다른 제약을 준다.
# (병렬 생성이라 서로를 못 보므로, 애초에 갈라지도록 '구조적 각도'를 배정한다.)
_ANGLE: dict[str, list[str]] = {
    "topic": [
        "핵심을 '가장 압축된 명사구'로 — 글의 중심 소재+필자 초점만 담아라.",
        "같은 주제라도 '다른 핵심 측면(결과·의의·대비 등)'을 전면에 내세워, 1번과 초점·어휘를 다르게.",
        "가장 추상적으로 재진술하되, 앞 두 문제에서 쓴 표현을 피하고 다른 유의어로.",
    ],
    "title": [
        "은유·비유를 담은 '명사구형' 제목으로.",
        "'의문형' 제목(Is/Are/Why/How …?)으로 — 1번과 형식을 달리하라.",
        "'콜론 부제형' 제목(A: B)으로 — 앞 두 문제와 형식·어휘를 달리하라.",
    ],
    "content": [
        "정답(일치 선지)의 근거를 지문 '첫 문장~앞부분' 사실에서 잡아라.",
        "정답의 근거를 지문 '중반부'의 '다른 문장'에서 잡아라. 가장 눈에 띄는 핵심 사실(예: 수치·"
        "시간 언급)은 다른 번호가 이미 쓸 가능성이 높으니 피하고, 덜 부각된 세부 사실을 골라라.",
        "정답의 근거를 지문 '마지막 문장~뒷부분'에서 잡아라. 앞 두 문제가 쓸 법한 사실은 피하고 "
        "'서로 다른 문장 3개'가 근거가 되도록 하라.",
    ],
    "imply": [
        "지문 '첫 문장~전반부'의 비유·맥락의존 어구를 밑줄(phrase)로 골라라.",
        "지문 '중반부'의 '다른 문장'에서 어구를 골라라. 글에서 가장 함축적인 한 구절은 다른 번호가 "
        "이미 쓸 수 있으니, 그와 겹치지 않는 별개의 어구를 골라라.",
        "지문 '마지막 문장~후반부'의 어구를 골라라. '서로 다른 문장 3개'에서 밑줄이 나오도록, 앞 "
        "두 어구와 절대 겹치지 않게 하라.",
    ],
}


def _variant_hint(base: str, label: str, i: int) -> str:
    count = COUNT_OF.get(base, 1)
    if count <= 1:
        return ""    # 단일 문항(주제)은 겹침 방지 지시 불필요
    angle = _ANGLE.get(base, ["", "", ""])[(i - 1) % len(_ANGLE.get(base, [""]))]
    return (f"[변형 {i}/{count} · 겹침 방지] 같은 지문의 '{label}' {i}번째 문제. {angle} "
            f"같은 지문의 다른 번호 문제와 정답·오답 선지·밑줄이 겹치지 않게 하라.")


def _answer_pos(title: str, passage_index: int, slot: str, level: str | None = None) -> int:
    """3개 변형이 서로 다른 정답 위치를 받도록 흩는다(1~5). 난이도도 시드에 섞어
    상·중·하를 함께 배포해도 정답 패턴이 겹치지 않게 한다."""
    seed = answer_spread.seed_of(title, level)
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
        apos = _answer_pos(analysis.title, passage_index, slot, level)
        vh = _variant_hint(base, TYPE_LABELS3[slot], VARIANT_OF[slot])
        # _gen_one_type2(gen, ...) 는 gen(client, analysis, body, max_retries, answer_pos) 를 호출.
        # variant_hint 를 앞서 바인딩해 시그니처를 맞춘다.
        bound = lambda c, a, b, max_retries, answer_pos: gen(  # noqa: E731
            c, a, b, max_retries, answer_pos, vh)
        return lambda: _gen_one_type2(bound, client, analysis, body, base,
                                      max_retries, logger, apos)

    results = run_parallel([(slot, _task(slot)) for slot in TYPE_ORDER3])
    for slot in TYPE_ORDER3:
        res = results.get(slot)
        if res is None:      # 이 슬롯은 최종 생성 실패 → 건너뛰고 나머지는 살린다
            continue
        q, a, fl = res
        passage.set_qa(slot, q, a)
        passage.flag(slot, fl)
        passage.flag(slot, _rv.type_fit_flags(getattr(analysis, "passage_type", "prose"), slot))
    if not passage.q:
        raise RuntimeError(f"[{passage.title}] 3회 모든 유형 생성 실패")
    return passage


def build_passages3(client, bodies, max_retries=1, logger=None, analyses=None,
                    level=None, labels=None, progress=None,
                    part_label="변형문제 3회") -> list:
    """3회 여러 지문 -> 검증된 Passage 리스트(조판 없음). 합본용."""
    from .pipeline import analyze_bodies
    if analyses is None:
        analyses = analyze_bodies(client, bodies, max_retries=max_retries, logger=logger)
    if logger:
        logger.info("[3회] 지문 %d개 생성 중 …", len(bodies))
    # 지문끼리도 동시에 처리(실제 동시 API 호출 수는 클라이언트 전체 상한으로 묶임)
    def _one(b, a, i):
        r = build_passage3(client, b, max_retries=max_retries, logger=logger,
                           analysis=a, level=level, passage_index=i)
        if progress:
            progress.step(f"{part_label} · 지문 {i + 1}")
        return r

    tasks = [(i, (lambda b=body, a=analysis, i=i: _one(b, a, i)))
             for i, (body, analysis) in enumerate(zip(bodies, analyses))]
    res = run_parallel(tasks)
    passages = []
    for i in range(len(bodies)):
        p = res[i]
        if labels and i < len(labels):
            p.source_label = labels[i]
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
