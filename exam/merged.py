"""변형문제 통합본 — 1회·2회를 합치고 겹치는 유형을 걷어낸 한 세트(11유형).

1회(7유형)와 2회(A~G)를 따로 뽑으면 사실상 같은 문제가 두 번 나온다.
아래 3유형은 다른 유형이 이미 같은 능력을 묻고 있어 통합본에서 뺐다:

  · C(어법 오류 판별)  → '어법'과 발문이 글자 그대로 같다.
  · G(내용일치 개수)   → '내용 일치'와 같은 능력(수능 표준 형식인 5지선다를 남김).
  · A(어법·어휘 짝짓기) → '어법' + '어휘'가 각각 단독으로 이미 있다.

결과: 지문당 14문항 → 11문항(-21%). 자기검증 호출도 9회 → 7회로 준다.
빼고 싶은/되살리고 싶은 유형이 있으면 MERGED_ORDER 한 줄만 고치면 된다.

생성기는 새로 만들지 않는다 — 1회 계열은 pipeline, 2회 계열은 gen2 의 것을
그대로 호출하고, 이 파일은 '어떤 유형을 어떤 순서로 낼지'만 정한다.
"""
from __future__ import annotations

from pathlib import Path

from .set2 import B, D, E, F, TYPE_LABELS2, TYPE_PROMPTS2
from .types import (
    CONTENT,
    GRAMMAR,
    INSERT,
    ORDER,
    SHORT_ANSWER,
    TOPIC,
    TYPE_LABELS,
    TYPE_PROMPTS,
    VOCAB,
    Passage,
)

# 출제 순서 — 수능 문항 배열을 그대로 따른다(괄호 안이 수능 문항번호).
# 뒤로 갈수록 어려워지므로 학생이 앞에서 막히지 않고, 실제 시험과 같은 리듬으로 훈련된다.
# 수능과 다른 점은 하나뿐: 주제(23번)를 함의추론(21번)보다 앞에 둔다. 수능은 앞에
# 목적·심경·주장(18~20번)이 있어 함의추론이 워밍업 뒤에 나오지만, 이 세트에는 그 셋이
# 없어 함의추론이 곧바로 1번이 되어 버리기 때문이다.
MERGED_ORDER: tuple[str, ...] = (
    TOPIC,         # 주제        (23번)
    B,             # 함의추론     (21번)
    CONTENT,       # 내용 일치    (26번)
    GRAMMAR,       # 어법        (29번)
    VOCAB,         # 어휘        (30번)
    F,             # 빈칸추론     (31~34번)
    ORDER,         # 순서 배열    (36~37번)
    INSERT,        # 문장 삽입    (38~39번)
    E,             # 요약문 빈칸   (40번)
    D,             # 어순 배열    (내신 서술형)
    SHORT_ANSWER,  # 서술형       (내신 서술형)
)

# 통합하며 뺀 유형 → 그 자리를 대신하는 유형(검토·설명용).
EXCLUDED: dict[str, str] = {
    "C": GRAMMAR,     # 어법 오류 판별 → 어법
    "G": CONTENT,     # 내용일치 개수 → 내용 일치
    "A": VOCAB,       # 어법·어휘 짝짓기 → 어법 + 어휘
}

# 1회·2회 유형 키는 서로 겹치지 않으므로(소문자 낱말 vs 대문자 한 글자) 그냥 합친다.
MERGED_PROMPTS: dict[str, str] = {**TYPE_PROMPTS, **TYPE_PROMPTS2}
MERGED_LABELS: dict[str, str] = {**TYPE_LABELS, **TYPE_LABELS2}


def build_passage_merged(client, body: str, max_retries: int = 1, logger=None,
                         vocab_method: str = "synonym", content_difficulty: str = "hard",
                         analysis=None, level: str | None = None,
                         passage_index: int = 0) -> Passage:
    """지문 원문 1개 → 통합 11유형이 채워진 Passage.

    유형끼리는 서로 독립이므로 스레드로 동시에 생성한다(1회·2회와 동일).
    analysis 를 주면 분석 호출을 건너뛴다(회차·난이도 조합이 공유).
    """
    from . import analyzer, answer_spread, difficulty, gen2, pipeline
    from . import review as _rv
    from ._concurrent import run_parallel

    if analysis is None:
        analysis = analyzer.analyze(client, body, max_retries=max_retries)
    vm = vocab_method
    if level:   # 난이도 지침을 분석 결과에 심어 모든 생성기에 공통 전달
        analysis.difficulty_note = difficulty.clause(level)
        content_difficulty = difficulty.content_difficulty(level)
        vm = difficulty.vocab_method(level)
    passage = Passage(title=analysis.title)

    slots = answer_spread.SLOTS_MERGED

    def _task(t):
        if t in pipeline.GENERATORS:        # 1회 계열(주제·내용일치·어법·어휘·순서·삽입·서술형)
            return pipeline.make_task(t, client, analysis, body, max_retries=max_retries,
                                      logger=logger, vocab_method=vm,
                                      content_difficulty=content_difficulty,
                                      passage_index=passage_index, level=level, slots=slots)
        return gen2.make_task2(t, client, analysis, body, max_retries=max_retries,   # 2회 계열
                               logger=logger, passage_index=passage_index,
                               level=level, slots=slots)

    results = run_parallel([(t, _task(t)) for t in MERGED_ORDER])
    for t in MERGED_ORDER:      # 수거는 완료순이라도 조립은 고정 순서대로
        res = results.get(t)
        if res is None:         # 이 유형만 최종 실패 → 건너뛰고 나머지는 살린다
            continue
        q, a, fl = res
        passage.set_qa(t, q, a)
        passage.flag(t, fl)
        passage.flag(t, _rv.type_fit_flags(getattr(analysis, "passage_type", "prose"), t))

    if not passage.q:
        raise RuntimeError(f"[{passage.title}] 통합본 모든 유형 생성 실패")
    return passage


def build_passages_merged(client, bodies: list[str], max_retries: int = 1, logger=None,
                          analyses=None, level: str | None = None,
                          vocab_method: str = "synonym", content_difficulty: str = "hard",
                          labels: list[str] | None = None, progress=None,
                          part_label: str = "변형문제") -> list[Passage]:
    """여러 지문 → 검증된 Passage 리스트(조판 없음). 합본용."""
    from . import validator
    from ._concurrent import run_parallel
    from .pipeline import analyze_bodies

    if analyses is None:
        analyses = analyze_bodies(client, bodies, max_retries=max_retries, logger=logger)
    if logger:
        logger.info("[통합] 지문 %d개 생성 중 …", len(bodies))

    def _one(b, a, i):
        r = build_passage_merged(client, b, max_retries=max_retries, logger=logger,
                                 vocab_method=vocab_method,
                                 content_difficulty=content_difficulty,
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
    validator.validate_passages(passages, MERGED_ORDER)
    validator.validate_numbering(passages, 1, MERGED_ORDER)
    return passages


def build_exam_merged(client, bodies: list[str], out_path: str | Path, header_note: str = "",
                      max_retries: int = 1, logger=None, analyses=None,
                      level: str | None = None, sections=None,
                      labels: list[str] | None = None) -> Path:
    from . import renderer
    passages = build_passages_merged(client, bodies, max_retries=max_retries, logger=logger,
                                     analyses=analyses, level=level, labels=labels)
    return renderer.render_pdf(passages, out_path, header_note=header_note,
                               type_order=MERGED_ORDER, prompts=MERGED_PROMPTS,
                               labels=MERGED_LABELS, sections=sections)


def demo_passages_merged() -> list[Passage]:
    """데모(무료 미리보기)용 통합본 — 1회·2회 데모 문항에서 통합 11유형만 골라 합친다.

    두 데모의 지문 수가 다르면 겹치는 만큼만 만든다(11유형이 다 갖춰진 지문만 나간다).
    """
    from .demo2 import demo_passages_2
    from .demo_data import demo_passages

    out: list[Passage] = []
    for p1, p2 in zip(demo_passages(), demo_passages_2()):
        p = Passage(title=p1.title)
        p.source_label = getattr(p1, "source_label", "") or ""
        for t in MERGED_ORDER:          # 출제 순서대로 채운다(어느 회차에서 왔든)
            for src in (p1, p2):
                if t in src.q and t in src.a:
                    p.set_qa(t, src.q[t], src.a[t])
                    break
        out.append(p)
    return out
