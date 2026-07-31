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


def _load_passages(passage_paths: list[str | Path], client: Any) -> list[Passage]:
    """지문 로드. API 키(client) 있으면 PDF는 Claude 비전으로 추출(텍스트 오류 원천 차단),
    실패하거나 미리보기(client=None)면 기존 텍스트 추출로 폴백."""
    if client is None:
        return load_passages(passage_paths)
    from .ingest.vision import extract_passages_pdf_vision
    out: list[Passage] = []
    for path in passage_paths:
        if str(path).lower().endswith(".pdf"):
            try:
                vp = extract_passages_pdf_vision(client, path)
                if vp:
                    out.extend(vp)
                    continue
            except Exception:  # noqa: BLE001 - 비전 실패 시 텍스트로 폴백
                pass
        out.extend(load_passages([path]))
    # id 재부여(파일 간 충돌 방지)
    ci = di = 0
    for p in out:
        if p.format_type == "dialogue":
            di += 1; p.id = f"d{di}"
        else:
            ci += 1; p.id = f"p{ci}"
    return out


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
    workers: int = 8,
) -> GenResult:
    """§8.5.5 생성 흐름. difficulty 는 '상/중/하' 또는 low/mid/high.

    문항 생성 단계에서 구조·정답 유일성을 자가검증하므로 별도 검수 패스는 두지 않는다.
    """
    diff: Difficulty = DIFFICULTY_KO.get(difficulty, difficulty)  # type: ignore
    if diff not in ("low", "mid", "high"):
        diff = "mid"

    # [1] 프로파일 로드 (미학습이면 학교급 표준 골격)
    profile = resolve_profile(school_id, grade)
    # [2] blueprint 구성
    blueprint = blueprint_from_profile(profile, grade)

    # [3] 지문 파싱 + 프로파일링 (API 키 있으면 PDF는 비전 추출로 오류 원천 차단)
    passages = _load_passages(passage_paths, client)
    pmap: dict[str, Passage] = {p.id: p for p in passages}
    profiles = {p.id: profile_passage(p) for p in passages}

    # [4] 지문 자동배정
    assignments = assign_passages(blueprint, passages, profiles, difficulty=diff)

    # [5] 문항 생성
    ctx = GenContext(profile=profile, difficulty=diff, client=client,
                     grammar_focus=profile.get("grammar_focus", []),
                     max_workers=max(1, int(workers)))
    exam, logs = generate_all(blueprint, assignments, pmap, ctx)

    # 지문 안내(오류 아님): 지문이 문항보다 적으면 각 유형에 가장 적합한 지문으로 재사용 배정한다.
    n_items = len(blueprint.items)
    if 0 < len(passages) < n_items:
        logs.insert(0, {
            "note": "passage_reuse", "passages": len(passages), "items": n_items,
            "msg": (f"지문 {len(passages)}개로 {n_items}문항을 생성했습니다. 각 문항은 "
                    f"유형(출제원리)에 가장 적합한 지문으로 배정했으며, 지문이 적어 일부는 "
                    f"반복 사용되었습니다(정상). 지문을 더 올리면 다양성이 높아집니다.")})

    # 문항 재생성 헬퍼(선택형/서술형 공통)
    a_by = {(a.section, a.no): a for a in assignments}
    item_by = {(it.section, it.no): it for it in blueprint.items}

    def _regen(q_i: int) -> None:
        q = exam.questions[q_i]
        a = a_by.get((q.section, q.no))
        p = pmap.get(a.passage_id) if a and a.passage_id else None
        item = item_by.get((q.section, q.no))
        if p is None or item is None:
            return
        try:
            exam.questions[q_i] = generate_question(item, p, ctx)  # 성공 시 플래그 사라짐
        except Exception:  # noqa: BLE001 - 재시도 실패는 플래그만 유지
            q = exam.questions[q_i]
            q.meta["gen_failed"] = True
            q.meta["review_flag"] = "미완성 — 검토·보완 필요"

    def _failed_idx() -> list[int]:
        return [i for i, q in enumerate(exam.questions)
                if isinstance(q.meta, dict) and q.meta.get("gen_failed")]

    # [5-2] 생성 실패(일시적 오류) 문항 즉시 자동 재시도 — 선택형·서술형 공통
    if client is not None:
        for _ in range(2):
            fidx = _failed_idx()
            if not fidx:
                break
            if len(fidx) > 1:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=ctx.max_workers) as ex:
                    list(ex.map(_regen, fidx))
            else:
                _regen(fidx[0])

    # [6] 형식·구조 검증 + 실패 문항 재생성
    structural = client is not None
    report = verify(exam, blueprint, requested=diff, structural=structural)
    for _ in range(max_regen):
        if report.ok:
            break
        bad = report.failed_choice_nos()
        if not bad:
            break
        regen_idx = [i for i, q in enumerate(exam.questions)
                     if q.section == "choice" and q.no in bad]
        if client is not None and len(regen_idx) > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=ctx.max_workers) as ex:
                list(ex.map(_regen, regen_idx))
        else:
            for q_i in regen_idx:
                _regen(q_i)
        report = verify(exam, blueprint, requested=diff, structural=structural)

    # [7] 의심문항(⚠)만 2차 검수 — 무인 운영 오류 저감(비용 최소: 플래그 붙은 문항만)
    if client is not None:
        _review_flagged(exam, client, ctx, _regen, logs)

    return GenResult(exam, blueprint, assignments, report, logs,
                     num_passages=len(passages))


def _review_flagged(exam, client, ctx, regen, logs) -> None:
    """review_flag 가 붙은 의심문항만 2차 LLM 으로 재검수.

    - 검수 통과 → 플래그 해제(오답경보 해소, 해설지 ⚠ 줄어듦)
    - 검수 실패 → 1회 재생성 후 그래도 의심이면 이유를 플래그에 남김
    (이미 재시도로 못 채운 '생성 실패' 문항은 대상에서 제외.)
    """
    from concurrent.futures import ThreadPoolExecutor
    from .verify.review import review_question

    def _flagged():
        return [i for i, q in enumerate(exam.questions)
                if isinstance(q.meta, dict) and q.meta.get("review_flag")
                and not q.meta.get("gen_failed")]

    idxs = _flagged()
    if not idxs:
        return

    def _one(i):
        ok, issue = review_question(client, exam.questions[i])
        return i, ok, issue

    with ThreadPoolExecutor(max_workers=ctx.max_workers) as ex:
        results = list(ex.map(_one, idxs))

    to_regen = [i for i, ok, _ in results if not ok]
    passed = [i for i, ok, _ in results if ok]
    for i in passed:                      # 검수 통과 → 신뢰, 경보 해제
        exam.questions[i].meta.pop("review_flag", None)
    for i, ok, issue in results:
        if not ok:
            q = exam.questions[i]
            logs.append({"no": q.no, "section": q.section, "type": q.type,
                         "note": "review_failed", "issue": issue[:200]})
    if to_regen:
        with ThreadPoolExecutor(max_workers=ctx.max_workers) as ex:
            list(ex.map(regen, to_regen))


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
