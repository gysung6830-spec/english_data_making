"""변형문제 통합본 — 수능 출제 유형을 한 벌로 덮는 17문항 세트.

1회(7유형)와 2회(A~G)를 따로 뽑으면 사실상 같은 문제가 두 번 나온다.
아래 3유형은 다른 유형이 이미 같은 능력을 묻고 있어 통합본에서 뺐다:

  · C(어법 오류 판별)  → '어법'과 발문이 글자 그대로 같다.
  · G(내용일치 개수)   → '내용 일치'와 같은 능력(수능 표준 형식인 5지선다를 남김).
  · A(어법·어휘 짝짓기) → 뒤에 pair_odd 로 다시 들였다(아래 참고).

여기에 내신 출제 빈도가 높은데 비어 있던 두 유형을 더했다:

  · 제목(24번)        → 주제와 짝을 이루는 유형. 함축·비유가 섞여 답이 겹치지 않는다.
  · 무관한 문장(35번)  → 원문에 없던 문장을 새로 써서 끼우므로 '암기로는 못 푸는' 유형.

어휘는 세 방식(원문단어형·유의어형·부정어형)을 모두 낸다. 발문은 같지만 밑줄을 만드는
방식이 달라 서로 다른 문제가 되고, 내신에서 어휘 비중이 큰 점을 감안했다.
쉬운 것부터 늘어놓는다 — 원문단어형(어색한 하나만 찾기) → 유의어형(다섯을 하나하나 대조)
→ 부정어형(낱말은 멀쩡하고 문장이 흐름과 모순).
어법도 두 개 낸다 — '틀린 것 모두 고르기'와 '틀린 것의 개수'. 뒤쪽은 밑줄을 하나하나
따져야 해서 찍기가 통하지 않는다. 두 어법 문항은 각각 '다시 쓴 지문' 위에 서므로
같은 밑줄을 두 번 묻지 않는다.

어법·어휘 짝짓기(pair_odd)는 옛 A 유형을 다시 들인 것이다. 처음에는 '어법과 어휘가
각각 단독으로 있으니 중복'이라고 보고 뺐지만, 이 유형이 묻는 것은 어법도 어휘도 아닌
**둘을 동시에, 짝으로** 짚는 능력이다. 하나만 찾아서는 답이 나오지 않아 찍기가 통하지
않는다. 선지(짝 5개)는 코드가 만들어 정답 짝이 반드시 하나만 들어가게 한다.
결과: 지문당 17문항. 빼고 싶은 유형이 있으면 MERGED_ORDER 한 줄만 고치면 된다.

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
    GRAMMAR_COUNT,
    IRRELEVANT,
    PAIR_ODD,
    TITLE,
    TYPE_LABELS,
    TYPE_PROMPTS,
    VOCAB,
    VOCAB_2,
    VOCAB_3,
    Passage,
)

# 출제 순서 — 수능 문항 배열을 그대로 따른다(괄호 안이 수능 문항번호).
# 뒤로 갈수록 어려워지므로 학생이 앞에서 막히지 않고, 실제 시험과 같은 리듬으로 훈련된다.
# 수능과 다른 점은 하나뿐: 주제(23번)를 함의추론(21번)보다 앞에 둔다. 수능은 앞에
# 목적·심경·주장(18~20번)이 있어 함의추론이 워밍업 뒤에 나오지만, 이 세트에는 그 셋이
# 없어 함의추론이 곧바로 1번이 되어 버리기 때문이다.
MERGED_ORDER: tuple[str, ...] = (
    TOPIC,         # 주제         (23번)
    TITLE,         # 제목         (24번) — 주제와 붙여 대의파악을 한 묶음으로
    B,             # 함의추론      (21번)
    CONTENT,       # 내용 일치     (26번)
    GRAMMAR,       # 어법 — 틀린 것 모두 고르기 (29번)
    GRAMMAR_COUNT, # 어법 — 틀린 것의 개수      (29번 계열·내신)
    PAIR_ODD,      # 어법·어휘 짝짓기 — 어법과 어휘를 잇는 자리
    # 어휘 3종은 쉬운 것부터 — 전체 배열과 같은 원칙(뒤로 갈수록 어려워진다).
    VOCAB_2,       # 어휘 — 원문단어형 (30번) 4개는 원문 그대로 → 어색한 하나만 찾으면 된다
    VOCAB,         # 어휘 — 유의어형   (30번) 5개가 다 바뀌어 하나하나 대조해야 한다
    VOCAB_3,       # 어휘 — 부정어형   (30번) 낱말은 멀쩡하고 '문장'이 글 흐름과 모순된다
    F,             # 빈칸추론      (31~34번)
    IRRELEVANT,    # 무관한 문장    (35번)
    ORDER,         # 순서 배열     (36~37번)
    INSERT,        # 문장 삽입     (38~39번)
    E,             # 요약문 빈칸    (40번)
    D,             # 어순 배열     (내신 서술형)
    SHORT_ANSWER,  # 서술형        (내신 서술형)
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
                         analysis=None, passage_index: int = 0,
                         strong_client=None) -> Passage:
    """지문 원문 1개 → 통합 17문항이 채워진 Passage.

    유형끼리는 서로 독립이므로 스레드로 동시에 생성한다.
    analysis 를 주면 분석 호출을 건너뛴다.
    strong_client 를 주면, 값싼 모델로 다 만든 뒤 **검수에 걸린 문항만** 그 모델로
    다시 만든다(tiering.escalation_targets). 대부분의 문항은 한 번에 통과하므로
    좋은 모델은 몇 문항에만 쓰인다.
    """
    from . import analyzer, answer_spread, difficulty, gen2, pipeline, tiering
    from . import review as _rv
    from ._concurrent import run_parallel
    from .generators import vocab as _vocab

    if analysis is None:
        analysis = analyzer.analyze(client, body, max_retries=max_retries)
    # 공통 출제 지침을 분석 결과에 심어 두면 모든 생성기의 프롬프트에 함께 실려 간다.
    analysis.difficulty_note = difficulty.CLAUSE
    passage = Passage(title=analysis.title)

    slots = answer_spread.SLOTS_MERGED

    def _task(t, cl=None):
        # 유형마다 추론 강도를 달리한다(판단이 걸린 유형만 high) — 사고 토큰 절감.
        c = tiering.EffortClient(cl or client, tiering.effort_for(t))
        # 슬롯키(vocab_2)는 기본 유형키(vocab)로 되돌려 어느 계열인지 가른다.
        if pipeline._base(t) in pipeline.GENERATORS:     # 산문형 계열
            return pipeline.make_task(t, c, analysis, body, max_retries=max_retries,
                                      logger=logger,
                                      content_difficulty=difficulty.CONTENT_DIFFICULTY,
                                      passage_index=passage_index, slots=slots)
        return gen2.make_task2(t, c, analysis, body, max_retries=max_retries,   # 추론형 계열
                               logger=logger, passage_index=passage_index,
                               slots=slots)

    # 어휘 3종은 밑줄이 겹치면 안 되므로 한 덩어리로 '차례로' 만든다(앞 문제가 쓴 낱말을
    # 다음 문제에 피할 낱말로 넘긴다). 나머지 유형과는 여전히 동시에 돈다.
    vslots = {t: pipeline.VOCAB_METHODS[t]
              for t in MERGED_ORDER if t in pipeline.VOCAB_METHODS}
    tasks = [(t, _task(t)) for t in MERGED_ORDER if t not in vslots]
    if vslots:
        vc = tiering.EffortClient(client, tiering.effort_for(VOCAB))
        tasks.append(("__vocab__", lambda: _vocab.generate_group(
            vc, analysis, body, vslots, max_retries=max_retries, logger=logger)))

    results = run_parallel(tasks)
    results.update(results.pop("__vocab__", None) or {})
    for t in MERGED_ORDER:      # 수거는 완료순이라도 조립은 고정 순서대로
        res = results.get(t)
        if res is None:         # 이 유형만 최종 실패 → 건너뛰고 나머지는 살린다
            continue
        q, a, fl = res
        passage.set_qa(t, q, a)
        passage.flag(t, fl)
        passage.flag(t, _rv.type_fit_flags(getattr(analysis, "passage_type", "prose"), t))

    if strong_client is not None:
        _escalate(passage, strong_client, _task, analysis, body, vslots,
                  max_retries=max_retries, logger=logger)

    if not passage.q:
        raise RuntimeError(f"[{passage.title}] 통합본 모든 유형 생성 실패")
    return passage


def _escalate(passage, strong_client, task_of, analysis, body, vslots,
              max_retries: int = 1, logger=None) -> list[str]:
    """검수에 걸린 문항만 좋은 모델로 다시 만든다. 다시 만든 유형 목록을 돌려준다.

    다시 만든 결과가 검수를 통과하면 문항과 사유를 교체하고, 그래도 걸리면 새 사유로
    바꿔 둔다(어느 쪽이든 교사가 보는 검토메모는 최신 상태가 된다).
    """
    from . import tiering
    from ._concurrent import run_parallel
    from .generators import vocab as _vocab

    targets = tiering.escalation_targets(passage, MERGED_ORDER)
    if not targets:
        return []
    if logger:
        logger.info("[승격] 검수에 걸린 %d문항을 상위 모델로 다시 만듭니다: %s",
                    len(targets), ", ".join(targets))

    vt = {t: vslots[t] for t in targets if t in vslots}
    # task_of() 는 '무인자 함수'를 돌려주므로 여기서 곧바로 실행한다.
    tasks = [(t, (lambda t=t: task_of(t, strong_client)()))
             for t in targets if t not in vt]
    if vt:      # 어휘는 밑줄이 겹치면 안 되므로 묶음으로 다시 만든다
        vc = tiering.EffortClient(strong_client, tiering.effort_for(VOCAB))
        tasks.append(("__vocab__", lambda: _vocab.generate_group(
            vc, analysis, body, vt, max_retries=max_retries, logger=logger)))

    res = run_parallel(tasks)
    res.update(res.pop("__vocab__", None) or {})
    fixed = []
    for t in targets:
        got = res.get(t)
        if got is None:            # 상위 모델도 실패 → 원래 상태를 그대로 둔다
            continue
        q, a, fl = got
        passage.set_qa(t, q, a)
        passage.flags.pop(t, None)          # 낡은 사유를 지우고 새 결과의 사유만 남긴다
        passage.flag(t, fl)
        fixed.append(t)
    if logger:
        still = [t for t in targets if tiering.needs_escalation(passage.flags.get(t))]
        logger.info("[승격] 다시 만든 %d문항 · 여전히 검수에 걸리는 문항 %d개",
                    len(fixed), len(still))
    return fixed


def build_passages_merged(client, bodies: list[str], max_retries: int = 1, logger=None,
                          analyses=None, labels: list[str] | None = None, progress=None,
                          part_label: str = "변형문제", strong_client=None) -> list[Passage]:
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
                                 analysis=a, passage_index=i,
                                 strong_client=strong_client)
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
                      max_retries: int = 1, logger=None, analyses=None, sections=None,
                      labels: list[str] | None = None, strong_client=None) -> Path:
    from . import renderer
    passages = build_passages_merged(client, bodies, max_retries=max_retries, logger=logger,
                                     analyses=analyses, labels=labels,
                                     strong_client=strong_client)
    return renderer.render_pdf(passages, out_path, header_note=header_note,
                               type_order=MERGED_ORDER, prompts=MERGED_PROMPTS,
                               labels=MERGED_LABELS, sections=sections)


def demo_passages_merged() -> list[Passage]:
    """데모(무료 미리보기)용 통합본 — 세 곳의 데모 문항을 출제 순서대로 합친다.

    산문형(주제·어법·어휘·순서·삽입·내용일치·서술형)은 demo_data,
    B·D·E·F 는 demo2, 새로 들어온 유형(제목·무관한 문장·어휘 2종)은 demo_new_types.
    지문 수가 다르면 겹치는 만큼만 만든다(유형이 다 갖춰진 지문만 나간다).
    """
    from .demo2 import demo_passages_2
    from .demo_data import demo_passages
    from .demo_new_types import supplement

    extra = supplement()
    out: list[Passage] = []
    for p1, p2 in zip(demo_passages(), demo_passages_2()):
        p = Passage(title=p1.title)
        p.source_label = getattr(p1, "source_label", "") or ""
        p3 = extra.get(p1.title)
        for t in MERGED_ORDER:          # 출제 순서대로 채운다(어느 데모에서 왔든)
            for src in (p3, p2, p1):   # 다시 쓴 어법이 옛 데모를 대신한다
                if src is not None and t in src.q and t in src.a:
                    p.set_qa(t, src.q[t], src.a[t])
                    break
        out.append(p)
    return out
