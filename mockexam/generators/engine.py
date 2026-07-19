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
    questions: list[Question] = []
    logs: list[dict] = []

    for item in blueprint.items:
        a = by_no.get((item.section, item.no))
        pid = a.passage_id if a else None
        if pid is None or pid not in passages:
            logs.append({"no": item.no, "section": item.section, "type": item.type,
                         "note": (a.note if a else None) or "no_passage"})
            if skip_missing:
                # 지문 없으면 안전망 문항(구조 유지, 지문 부족 표기)
                q = generic_question(item, _placeholder_passage(item.no, item.type),
                                     ctx, stem=f"[지문 부족] ({item.type})")
                questions.append(q)
                continue
        passage = passages.get(pid) if pid else _placeholder_passage(item.no, item.type)
        if passage.id not in analyses:
            analyses[passage.id] = PassageAnalysis.of(passage)
        q = generate_question(item, passage, ctx, analyses[passage.id])
        questions.append(q)

    exam = MockExam(blueprint=blueprint, questions=questions)
    return exam, logs
