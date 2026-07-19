"""검증기 (§5) — 그 학교 프로파일 기대값과 비교. 숫자 하드코딩 금지.

7개 항목을 모두 통과해야 출력한다. 실패 항목은 그 문항만 재생성(§5-8).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..core.models import Blueprint, Difficulty, MockExam, Question


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    bad_items: list[int] = field(default_factory=list)   # 재생성 대상(문항 no)


@dataclass
class VerifyReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def failed_choice_nos(self) -> set[int]:
        bad: set[int] = set()
        for c in self.checks:
            bad.update(c.bad_items)
        return bad

    def summary(self) -> str:
        return "\n".join(f"[{'OK ' if c.ok else 'FAIL'}] {c.name}: {c.detail}"
                         for c in self.checks)


_ANSWER_LABELS = ["①", "②", "③", "④", "⑤"]


def _count_underlines(q: Question) -> int:
    """지문 텍스트에서 밑줄 마커 수를 센다(①~⑤ 또는 (A)(B).. 또는 <u> 태그)."""
    text = q.passage_text or ""
    n = len(re.findall(r"[①②③④⑤]", text))
    if n:
        return n
    return len(re.findall(r"<u[ >]", text))


def verify(exam: MockExam, blueprint: Blueprint,
           requested: Difficulty = "mid") -> VerifyReport:
    rep = VerifyReport()
    qs = exam.questions
    choice = exam.choice_questions
    essay = exam.essay_questions

    # 1) 문항수 (§5-1)
    exp_c = len(blueprint.choice_items)
    exp_e = len(blueprint.essay_items)
    ok1 = len(choice) == exp_c and len(essay) == exp_e
    rep.checks.append(CheckResult(
        "문항수", ok1,
        f"choice {len(choice)}/{exp_c}, essay {len(essay)}/{exp_e}"))

    # 2) 배점 합 (§5-2)
    got = round(sum(q.score for q in qs), 2)
    exp = round(blueprint.meta.total_score, 2)
    rep.checks.append(CheckResult(
        "배점합", abs(got - exp) < 0.01, f"{got} / {exp}"))

    # 3) 유형·배치 (§5-3)
    bad_type: list[int] = []
    for section, items in (("choice", blueprint.choice_items),
                           ("essay", blueprint.essay_items)):
        seq_q = [q for q in qs if q.section == section]
        for it, q in zip(items, seq_q):
            if q.type != it.type:
                bad_type.append(q.no if section == "choice" else 100 + q.no)
    exp_seq = blueprint.type_sequence("choice") + blueprint.type_sequence("essay")
    got_seq = [q.type for q in choice] + [q.type for q in essay]
    rep.checks.append(CheckResult(
        "유형·배치", got_seq == exp_seq,
        "일치" if got_seq == exp_seq else f"불일치({len(bad_type)}건)",
        bad_items=[n for n in bad_type if n < 100]))

    # 4) 정답 유일성 (§5-4) — 객관식은 정답 라벨 정확히 1개
    bad_ans: list[int] = []
    for q in choice:
        if not q.choices:
            continue
        labels = [c.label for c in q.choices]
        ans = q.answer.strip()
        # 정답이 라벨 목록 중 정확히 하나를 가리키는가
        hits = [lb for lb in labels if lb and lb == ans]
        if len(hits) != 1:
            bad_ans.append(q.no)
    rep.checks.append(CheckResult(
        "정답유일성", not bad_ans,
        "모두 단일정답" if not bad_ans else f"위반 {bad_ans}", bad_items=bad_ans))

    # 5) 번호 연속 (§5-5)
    c_nos = sorted(q.no for q in choice)
    e_nos = sorted(q.no for q in essay)
    ok5 = c_nos == list(range(1, len(choice) + 1)) and e_nos == list(range(1, len(essay) + 1))
    rep.checks.append(CheckResult(
        "번호연속", ok5, f"choice={c_nos}, essay={e_nos}"))

    # 6) 밑줄 개수 (§5-6)
    bad_ul: list[int] = []
    by_no = {q.no: q for q in choice}
    for it in blueprint.choice_items:
        if it.underlines is None:
            continue
        q = by_no.get(it.no)
        if q is None:
            continue
        if _count_underlines(q) != it.underlines:
            bad_ul.append(it.no)
    rep.checks.append(CheckResult(
        "밑줄개수", not bad_ul,
        "정상" if not bad_ul else f"불일치 {bad_ul}", bad_items=bad_ul))

    # 7) 난이도 일관성 (§5-7)
    bad_diff = [q.no for q in choice if q.difficulty != requested]
    # 요청과 다른 난이도가 절반 넘으면 실패로 본다(경미한 편차는 허용).
    ok7 = len(bad_diff) <= len(choice) * 0.5
    rep.checks.append(CheckResult(
        "난이도일관성", ok7,
        f"요청={requested}, 불일치 {len(bad_diff)}/{len(choice)}"))

    return rep
