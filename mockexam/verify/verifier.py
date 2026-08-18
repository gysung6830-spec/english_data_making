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


_BLANK_RE = re.compile(r"_{3,}|▢|□|\(\s{2,}\)")


def structural_issue(q: Question) -> str | None:
    """유형이 요구하는 구조 요소(빈칸·밑줄·①~⑤·(A)(B)(C))가 있는지 점검.

    LLM 생성 문항이 발문은 맞지만 지문에 정답 근거 구조를 빠뜨리는 오류를 잡는다.
    """
    t = q.type
    p = q.passage_text or ""
    circled = len(re.findall(r"[①②③④⑤]", p))
    has_u = "<u>" in p
    has_blank = bool(_BLANK_RE.search(p)) or "____" in p
    has_abc = all(m in p for m in ("(A)", "(B)", "(C)"))

    if t in ("grammar", "grammar_vocab_mix", "vocab_odd"):
        if circled < 5 and (not has_u):
            return "밑줄 표시(①~⑤) 부족"
    elif t == "irrelevant_sentence":
        if circled < 5:
            return "문장 번호(①~⑤) 부족"
    elif t == "implied_meaning":
        if not has_u:
            return "밑줄(<u>) 없음"
    elif t in ("blank_single",):
        if not has_blank:
            return "빈칸(____) 없음"
    elif t == "summary_ab":
        if not (has_blank or has_abc):
            return "(A)/(B) 빈칸 없음"
        if q.choices and not any(" - " in c.text or "(A)" in c.text for c in q.choices):
            return "선지가 '(A) - (B)' 형식 아님"
    elif t == "vocab_3blank_abc":
        if not (has_abc or (q.choices and any("(A)" in c.text for c in q.choices))):
            return "(A)(B)(C) 표시 없음"
    elif t == "order":
        if not has_abc:
            return "(A)(B)(C) 문단 없음"
    elif t == "summary_fill_from_text":
        if not has_blank:
            return "요약 빈칸 없음"
    elif t == "grammar_fix_and_answer":
        marks = p.count("<u>") + len(re.findall(r"[①②③]", p))
        if marks < 3:
            return "어법 오류 밑줄 3곳 부족"
    return None


def verify(exam: MockExam, blueprint: Blueprint,
           requested: Difficulty = "mid", structural: bool = False) -> VerifyReport:
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
    #    중상(mid_high)은 '중·상 문항을 반반' 배치하는 조합 난이도이므로 mid/high 둘 다 허용.
    allowed = {"mid", "high"} if requested == "mid_high" else {requested}
    bad_diff = [q.no for q in choice if q.difficulty not in allowed]
    # 요청과 다른 난이도가 절반 넘으면 실패로 본다(경미한 편차는 허용).
    ok7 = len(bad_diff) <= len(choice) * 0.5
    rep.checks.append(CheckResult(
        "난이도일관성", ok7,
        f"요청={requested}, 불일치 {len(bad_diff)}/{len(choice)}"))

    # 8) 구조 요건(LLM 생성 시): 유형이 요구하는 빈칸/밑줄/①~⑤/(A)(B)(C) 유무
    if structural:
        bad_struct: list[int] = []
        details: list[str] = []
        for q in qs:
            issue = structural_issue(q)
            if issue:
                details.append(f"{'서술형 ' if q.section=='essay' else ''}{q.no}({issue})")
                if q.section == "choice":
                    bad_struct.append(q.no)
        rep.checks.append(CheckResult(
            "구조요건", not details,
            "정상" if not details else "; ".join(details), bad_items=bad_struct))

    return rep
