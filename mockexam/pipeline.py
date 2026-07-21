"""전체 오케스트레이션 (§0 파이프라인 [1]~[7]) + learn 모드 (§8.5.4)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .core.blueprint import blueprint_from_profile
from .core.models import (
    DIFFICULTY_KO, Blueprint, Difficulty, MockExam, Passage,
)
from .corpus.selector import assign_passages, profile_passage
from .generators.base import GenContext
from .generators.engine import generate_all, generate_question
from .ingest.loader import load_passages
from .school import archive_exam, load_profile, resolve_profile, save_profile
from .verify.verifier import VerifyReport, verify


@dataclass
class GenResult:
    exam: MockExam
    blueprint: Blueprint
    assignments: list
    verify_report: VerifyReport
    logs: list[dict] = field(default_factory=list)
    num_passages: int = 0        # 입력에서 추출된 지문 수(0이면 텍스트 인식 실패)


def generate_mock(
    school_id: str,
    passage_paths: list[str | Path],
    difficulty: str = "중",
    grade: int = 1,
    client: Any = None,
    max_regen: int = 2,
    review_pass: bool = True,
    max_review: int = 1,
) -> GenResult:
    """§8.5.5 생성 흐름. difficulty 는 '상/중/하' 또는 low/mid/high.

    review_pass=True 면 생성 후 2차 LLM 검수로 정답 타당성을 점검해 실패 문항 재생성.
    """
    diff: Difficulty = DIFFICULTY_KO.get(difficulty, difficulty)  # type: ignore
    if diff not in ("low", "mid", "high"):
        diff = "mid"

    # [1] 프로파일 로드 (미학습이면 학교급 표준 골격)
    profile = resolve_profile(school_id, grade)
    # [2] blueprint 구성
    blueprint = blueprint_from_profile(profile, grade)

    # [3] 지문 파싱 + 프로파일링
    passages = load_passages(passage_paths)
    pmap: dict[str, Passage] = {p.id: p for p in passages}
    profiles = {p.id: profile_passage(p) for p in passages}

    # [4] 지문 자동배정
    assignments = assign_passages(blueprint, passages, profiles, difficulty=diff)

    # [5] 문항 생성
    ctx = GenContext(profile=profile, difficulty=diff, client=client,
                     grammar_focus=profile.get("grammar_focus", []))
    exam, logs = generate_all(blueprint, assignments, pmap, ctx)

    # 문항 재생성 헬퍼(선택형/서술형 공통)
    a_by = {(a.section, a.no): a for a in assignments}
    item_by = {(it.section, it.no): it for it in blueprint.items}

    def _regen(q_i: int) -> None:
        q = exam.questions[q_i]
        a = a_by.get((q.section, q.no))
        p = pmap.get(a.passage_id) if a and a.passage_id else None
        item = item_by.get((q.section, q.no))
        if p is not None and item is not None:
            exam.questions[q_i] = generate_question(item, p, ctx)

    # [6] 형식·구조 검증 + 실패 문항 재생성
    structural = client is not None
    report = verify(exam, blueprint, requested=diff, structural=structural)
    for _ in range(max_regen):
        if report.ok:
            break
        bad = report.failed_choice_nos()
        if not bad:
            break
        for q_i, q in enumerate(exam.questions):
            if q.section == "choice" and q.no in bad:
                _regen(q_i)
        report = verify(exam, blueprint, requested=diff, structural=structural)

    # [6-2] 2차 LLM 검수 패스 — 정답 타당성 점검 후 실패 문항 재생성
    if review_pass and client is not None:
        from .verify.review import review_question
        for _ in range(max_review):
            failed_idx: list[int] = []
            for q_i, q in enumerate(exam.questions):
                if not (q.passage_text or q.choices):   # 지문 부족/자리표시자 건너뜀
                    continue
                ok, issue = review_question(client, q)
                if not ok:
                    failed_idx.append(q_i)
                    logs.append({"no": q.no, "section": q.section, "type": q.type,
                                 "note": "review_failed", "issue": issue[:200]})
            if not failed_idx:
                break
            for q_i in failed_idx:
                _regen(q_i)
        report = verify(exam, blueprint, requested=diff, structural=structural)

    return GenResult(exam, blueprint, assignments, report, logs,
                     num_passages=len(passages))


# ---------------------------------------------------------------------------
# learn 모드 (§8.5.4) — 학교 시험지 blueprint → profile 누적
# ---------------------------------------------------------------------------
def learn_from_blueprint(school_id: str, exam_name: str,
                         blueprint: Blueprint, name: str = "",
                         level: str = "high") -> dict[str, Any]:
    """추출된 blueprint 로 profile.json 을 누적 갱신한다.

    같은 학교면 누적, 없으면 새로 생성. type_distribution·counts·score_pattern 갱신.
    """
    prof = load_profile(school_id) or {
        "school_id": school_id, "name": name or school_id, "level": level,
        "learned": True, "exams_learned": [], "type_distribution": {},
        "item_template": [], "stem_style": {}, "grammar_focus": [], "notes": [],
    }
    prof["learned"] = True
    if exam_name not in prof.get("exams_learned", []):
        prof.setdefault("exams_learned", []).append(exam_name)

    # type_distribution 누적
    td = prof.setdefault("type_distribution", {})
    for it in blueprint.items:
        td[it.type] = td.get(it.type, 0) + 1

    # counts / score_pattern (최신 우선)
    prof["counts"] = {"choice": len(blueprint.choice_items),
                      "essay": len(blueprint.essay_items)}
    prof["score_pattern"] = {"total": blueprint.total_score}
    prof["subject"] = blueprint.meta.subject or prof.get("subject", "영어")
    prof["time_min"] = blueprint.meta.time_min

    # 최신 시험 구조를 item_template 로(생성 기준). 학교의 최근 스펙을 반영.
    prof["item_template"] = [it.to_dict() for it in blueprint.items]

    archive_exam(school_id, exam_name, blueprint.to_dict())
    save_profile(school_id, prof)
    return prof
