"""생성 디스패처: 유형 → 등록된 builder. 지문 분석 1회 캐시(§4 BaseGenerator)."""
from __future__ import annotations

from ..core.models import (
    Assignment, Blueprint, Item, MockExam, Passage, Question,
)
# 카테고리 모듈 임포트 → REGISTRY 에 등록 트리거
from . import dialogue, essay, grammar, reading, vocab  # noqa: F401
from .base import (
    GenContext, PassageAnalysis, REGISTRY, generic_question,
)


def generate_question(item: Item, passage: Passage, ctx: GenContext,
                      analysis: PassageAnalysis | None = None) -> Question:
    an = analysis or PassageAnalysis.of(passage)
    builder = REGISTRY.get(item.type)
    if builder is None:
        # 등록 안 된 유형 → 안전망(구조만 갖춘 mock)
        return generic_question(item, passage, ctx, stem=f"({item.type}) 문항")
    return builder(item, passage, an, ctx)


def _placeholder_passage(no: int, type_: str) -> Passage:
    return Passage(id=f"__none_{no}", text="(지문 부족으로 배정되지 않음)",
                   format_type="narrative")


def generate_all(blueprint: Blueprint, assignments: list[Assignment],
                 passages: dict[str, Passage], ctx: GenContext,
                 skip_missing: bool = True) -> tuple[MockExam, list[dict]]:
    """blueprint + 배정 → MockExam. 배정 안 된 슬롯 처리 로그 반환."""
    by_no: dict[tuple[str, int], Assignment] = {
        (a.section, a.no): a for a in assignments}
    analyses: dict[str, PassageAnalysis] = {}
    questions: list[Question | None] = [None] * len(blueprint.items)
    logs: list[dict] = []
    tasks: list[tuple[int, Item, Passage]] = []

    # 1) 지문 배정 정리(지문 없는 슬롯은 즉시 자리표시자) + 분석 준비
    for idx, item in enumerate(blueprint.items):
        a = by_no.get((item.section, item.no))
        pid = a.passage_id if a else None
        if pid is None or pid not in passages:
            logs.append({"no": item.no, "section": item.section, "type": item.type,
                         "note": (a.note if a else None) or "no_passage"})
            if skip_missing:
                q0 = generic_question(
                    item, _placeholder_passage(item.no, item.type), ctx,
                    stem=f"[지문 부족] ({item.type})")
                q0.meta["review_flag"] = "지문 부족으로 미생성 — 확인·재생성 필요"
                questions[idx] = q0
                continue
        passage = passages.get(pid) if pid else _placeholder_passage(item.no, item.type)
        if passage.id not in analyses:
            analyses[passage.id] = PassageAnalysis.of(passage)
        tasks.append((idx, item, passage))

    # 2) 문항 생성 — LLM 이면 병렬(문항끼리 독립), mock 이면 순차.
    def _one(t: tuple[int, Item, Passage]):
        idx, item, passage = t
        try:
            return idx, generate_question(item, passage, ctx, analyses[passage.id]), None
        except Exception as e:  # noqa: BLE001 - 문항 단위 오류 격리
            return idx, None, (item, passage, str(e)[:200])

    for idx, q, err in _run(tasks, _one, ctx):
        if err is not None:
            item, passage, msg = err
            logs.append({"no": item.no, "section": item.section, "type": item.type,
                         "note": "generation_failed", "error": msg})
            q = generic_question(item, passage, ctx,
                                 stem=f"[생성 실패-검토 필요] ({item.type})")
            q.meta["review_flag"] = f"생성 실패 — 재생성 필요 ({msg[:60]})"
        questions[idx] = q

    exam = MockExam(blueprint=blueprint, questions=[q for q in questions if q])
    return exam, logs


def _run(items, fn, ctx):
    """LLM 모드면 스레드풀로 병렬, 아니면 순차 실행."""
    workers = getattr(ctx, "max_workers", 8) if getattr(ctx, "client", None) else 1
    if workers <= 1 or len(items) <= 1:
        return [fn(x) for x in items]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))
