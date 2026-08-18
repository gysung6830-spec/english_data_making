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
    passages: list[Passage] | None = None,
    form: str = "A",
    variant: int = 0,
    avoid_pairs: set[tuple[str, str]] | None = None,
    strict_certify: bool = False,
) -> GenResult:
    """§8.5.5 생성 흐름. difficulty 는 '상/중/하' 또는 low/mid/high.

    문항 생성 단계에서 구조·정답 유일성을 자가검증하므로 별도 검수 패스는 두지 않는다.
    passages 를 직접 주면 파일 재로드(비전 재호출)를 건너뛴다 — N회분 생성 시 비용 절감.
    """
    diff: Difficulty = DIFFICULTY_KO.get(difficulty, difficulty)  # type: ignore
    if diff not in ("low", "mid", "mid_high", "high"):
        diff = "mid"

    # [1] 프로파일 로드 (미학습이면 학교급 표준 골격)
    profile = resolve_profile(school_id, grade)
    # [2] blueprint 구성
    blueprint = blueprint_from_profile(profile, grade)

    # [3] 지문 파싱 + 프로파일링 (API 키 있으면 PDF는 비전 추출로 오류 원천 차단)
    #     passages 가 주어지면(N회분) 재로드하지 않는다.
    if passages is None:
        passages = _load_passages(passage_paths, client)
    pmap: dict[str, Passage] = {p.id: p for p in passages}
    profiles = {p.id: profile_passage(p) for p in passages}

    # [4] 지문 자동배정 (avoid_pairs: 회차 간 (지문,유형) 겹침 방지)
    assignments = assign_passages(blueprint, passages, profiles, difficulty=diff,
                                  avoid_pairs=avoid_pairs)

    # [5] 문항 생성
    ctx = GenContext(profile=profile, difficulty=diff, client=client,
                     grammar_focus=profile.get("grammar_focus", []),
                     max_workers=max(1, int(workers)), variant=variant)
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

    # [7] 의심문항(⚠) 2차 검수 — 무인 운영 오류 저감(플래그 붙은 문항만).
    #     strict_certify(판매용)면 반복 인증 후 남은 ⚠ 를 출력물에서 제거한다.
    if client is not None:
        _review_flagged(exam, client, ctx, _regen, logs, strict=strict_certify)

    # [8] 정답 번호 분산 — 한 번호에 쏠리거나 3연속되지 않게 고르게 재배치
    _rebalance_answers(exam)

    exam.form = form
    return GenResult(exam, blueprint, assignments, report, logs,
                     num_passages=len(passages))


_DIFF_KO = {"low": "하", "mid": "중", "mid_high": "중상", "high": "상"}
# N회분 고정 난이도 사다리(사용자 지정): 하 → 중 → 상 → 중상
_DIFF_LADDER = ["low", "mid", "high", "mid_high"]


def difficulty_gradient(base: str, n: int) -> list[str]:
    """N회분 난이도 목록. n>1 이면 고정 사다리(하→중→상→중상)의 앞 n개를 쓴다.

    n=1 이면 사용자가 고른 기준 난이도를 그대로 사용한다.
    """
    if n <= 1:
        b = DIFFICULTY_KO.get(base, base)
        return [b if b in _DIFF_KO else "mid"]
    if n <= len(_DIFF_LADDER):
        return _DIFF_LADDER[:n]
    # 5회 이상이면 사다리를 반복(마지막은 중상 유지)
    return [_DIFF_LADDER[min(i, len(_DIFF_LADDER) - 1)] for i in range(n)]


def generate_mock_forms(
    school_id: str,
    passage_paths: list[str | Path],
    n_forms: int = 1,
    difficulty: str = "중",
    grade: int = 1,
    client: Any = None,
    max_regen: int = 2,
    workers: int = 8,
    strict_certify: bool = False,
) -> list[GenResult]:
    """지문 파일을 한 번만 로드해 N회분(A·B·C…) 완결형 세트를 만든다.

    - '같은 지문 풀'을 모든 회차에 그대로 사용한다(배정 지문 동일).
    - 회차마다 '문항은 다르게'(회차 변형 지시로 묻는 지점·선지 재구성) 만들고,
      난이도를 기준값에서 상까지 회차별로 상향 조정한다.
    각 회차는 학교 blueprint 전체(완결형)를 그대로 생성한다.
    """
    n = max(1, min(int(n_forms), 8))
    passages = _load_passages(passage_paths, client)   # 비전 추출은 한 번만
    diffs = difficulty_gradient(difficulty, n)
    results: list[GenResult] = []
    used_pairs: set[tuple[str, str]] = set()   # 회차 간 (지문id, 유형) 겹침 방지 누적
    for i in range(n):
        res = generate_mock(school_id, [], difficulty=diffs[i], grade=grade,
                            client=client, max_regen=max_regen, workers=workers,
                            passages=passages, form=chr(ord("A") + i),
                            variant=(i + 1 if n > 1 else 0),
                            avoid_pairs=set(used_pairs) if n > 1 else None,
                            strict_certify=strict_certify)
        # 이 회차가 실제로 쓴 (지문,유형) 조합을 누적 → 다음 회차는 이를 피한다.
        for a in res.assignments:
            if a.passage_id:
                used_pairs.add((a.passage_id, a.type))
        # 이 회차의 난이도(한글)를 결과에 기록 → 웹앱 표시용
        res.logs.insert(0, {"note": "form_difficulty", "form": i + 1,
                            "difficulty": _DIFF_KO.get(diffs[i], diffs[i])})
        results.append(res)
    return results


def _rebalance_answers(exam) -> None:
    """선택형 정답 번호(①~⑤)를 고르게 분산한다.

    - 텍스트 선지 유형: 선지 '순서'만 바꿔(내용 불변) 정답을 목표 번호로 이동.
    - 번호형(어법·어휘·무관문장): 정답 위치가 지문에 고정 → 그대로 두고 카운트에만 반영.
    같은 번호가 3연속되지 않고 다섯 번호가 대체로 균등해지도록 배치한다.
    """
    from .core.models import Choice
    from .generators.base import LABELS

    choice_qs = [q for q in exam.questions if q.section == "choice" and q.choices]
    counts = {lb: 0 for lb in LABELS}
    last2: list[str] = []

    def _is_number_only(q) -> bool:
        return bool(q.meta.get("number_only")) or all(not c.text for c in q.choices)

    def _move(q, target: str) -> None:
        labels = [c.label for c in q.choices]
        if q.answer not in labels or target not in labels:
            return
        cur, tgt = labels.index(q.answer), labels.index(target)
        if cur == tgt:
            return
        texts = [c.text for c in q.choices]
        texts[cur], texts[tgt] = texts[tgt], texts[cur]   # 두 선지 위치 교환
        q.choices = [Choice(LABELS[i], t) for i, t in enumerate(texts)]
        q.answer = target

    # 선지 순서 자체가 의미인 유형(개수형 '1개~5개')은 재배치 제외 — 카운트만 반영.
    _fixed_order = {"count_match"}
    for q in choice_qs:
        if _is_number_only(q) or q.type in _fixed_order:
            if q.answer in counts:
                counts[q.answer] += 1
                last2 = (last2 + [q.answer])[-2:]
            continue
        # 가장 적게 쓰인 번호부터, 단 직전 2개와 같아 3연속이 되는 번호는 회피
        for lb in sorted(LABELS, key=lambda x: counts[x]):
            if len(last2) == 2 and last2[0] == last2[1] == lb:
                continue
            target = lb
            break
        else:
            target = min(LABELS, key=lambda x: counts[x])
        _move(q, target)
        counts[target] += 1
        last2 = (last2 + [target])[-2:]


def _review_flagged(exam, client, ctx, regen, logs, strict=False) -> None:
    """review_flag 가 붙은 의심문항을 2차 LLM 으로 재검수(엄격 모드는 반복).

    - 검수 통과 → 플래그 해제(오답경보 해소, 해설지 ⚠ 줄어듦)
    - 검수 실패 → 재생성 후 재검수(엄격 모드는 여러 라운드 반복)
    - strict=True(판매용): 반복 후에도 확실하지 않은 문항은 출력물에서 ⚠ 를 '제거'하고
      (검토페이지·주의표시가 아예 안 나오게) 그 사실은 logs 에 'uncertified' 로만 남겨
      판매자에게 별도 보고한다. → 배부물에는 주의표시가 하나도 없다.
    (이미 재시도로 못 채운 '생성 실패' 문항은 대상에서 제외.)
    """
    from concurrent.futures import ThreadPoolExecutor
    from .verify.review import review_question

    def _flagged():
        return [i for i, q in enumerate(exam.questions)
                if isinstance(q.meta, dict) and q.meta.get("review_flag")
                and not q.meta.get("gen_failed")]

    def _one(i):
        ok, issue = review_question(client, exam.questions[i])
        return i, ok, issue

    rounds = 3 if strict else 1
    for _r in range(rounds):
        idxs = _flagged()
        if not idxs:
            return
        with ThreadPoolExecutor(max_workers=ctx.max_workers) as ex:
            results = list(ex.map(_one, idxs))
        to_regen = [i for i, ok, _ in results if not ok]
        for i, ok, _ in results:
            if ok:                                    # 검수 통과 → 신뢰, 경보 해제
                exam.questions[i].meta.pop("review_flag", None)
        for i, ok, issue in results:
            if not ok:
                q = exam.questions[i]
                logs.append({"no": q.no, "section": q.section, "type": q.type,
                             "note": "review_failed", "issue": issue[:200]})
        if not to_regen:
            break
        with ThreadPoolExecutor(max_workers=ctx.max_workers) as ex:
            list(ex.map(regen, to_regen))

    # 엄격(판매) 모드: 그래도 남은 ⚠ 는 출력물에서 제거하고 판매자에게만 보고.
    if strict:
        for i in _flagged():
            q = exam.questions[i]
            logs.append({"no": q.no, "section": q.section, "type": q.type,
                         "note": "uncertified",
                         "issue": str(q.meta.get("review_flag", ""))[:200]})
            q.meta.pop("review_flag", None)           # 배부물에서 ⚠·검토페이지 제거


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
