"""검증기 (명세서 §6-2).

- 생성 단계: 지문마다 q·a 에 6종이 모두 있는지, 규격 외 유형이 없는지,
  q 와 a 의 유형 집합이 같은지 확인.
- 결과물 단계: 완성 문서에서 문항 번호가 1..N 연속인지,
  [문제 전체 → 해설 전체] 순인지, 두 파트에 같은 번호가 있는지 확인.
- 실패 시 해당 유형만 재생성하도록 어떤 유형이 빠졌는지 돌려준다.
"""
from __future__ import annotations

from dataclasses import dataclass

from .types import TYPE_ORDER, Passage


class ValidationError(Exception):
    """검증 실패."""


@dataclass
class MissingReport:
    """지문별로 어떤 유형의 q/a 가 비었는지."""

    passage_title: str
    missing_q: list[str]
    missing_a: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing_q and not self.missing_a


def check_passage(passage: Passage, type_order=TYPE_ORDER) -> MissingReport:
    """지문 1개가 유형 문제+해설을 빠짐없이 가졌는지 점검.

    - q, a 에 type_order 유형이 모두 있어야 한다.
    - q 와 a 의 유형 집합이 같아야 한다.
    - 규격 외(type_order 에 없는) 유형이 있으면 오류.
    """
    expected = set(type_order)

    extra_q = passage.q.keys() - expected
    extra_a = passage.a.keys() - expected
    if extra_q or extra_a:
        raise ValidationError(
            f"[{passage.title}] 규격 외 유형이 있습니다: q={sorted(extra_q)} a={sorted(extra_a)}"
        )

    missing_q = [t for t in type_order if not (passage.q.get(t) or "").strip()]
    missing_a = [t for t in type_order if not (passage.a.get(t) or "").strip()]
    return MissingReport(passage.title, missing_q, missing_a)


def present_types(passage: Passage, type_order=TYPE_ORDER) -> list[str]:
    """이 지문에 '실제로 생성된' 유형(문제+해설 둘 다 있는)만 type_order 순서로."""
    return [t for t in type_order
            if (passage.q.get(t) or "").strip() and (passage.a.get(t) or "").strip()]


def validate_passages(passages: list[Passage], type_order=TYPE_ORDER) -> None:
    """지문들의 정합성을 확인한다. 일부 유형은 생성 실패로 빠져 있을 수 있으나(부분 허용),
    ① 규격 외 유형이 없어야 하고 ② 문제/해설 유형 집합이 일치해야 하며
    ③ 최소 1문항은 있어야 한다. 실패 시 ValidationError."""
    if not passages:
        raise ValidationError("지문이 하나도 없습니다.")
    expected = set(type_order)
    problems: list[str] = []
    for p in passages:
        extra = (set(p.q) | set(p.a)) - expected
        if extra:
            problems.append(f"[{p.title}] 규격 외 유형: {sorted(extra)}")
        qk = {t for t in type_order if (p.q.get(t) or "").strip()}
        ak = {t for t in type_order if (p.a.get(t) or "").strip()}
        if qk != ak:
            problems.append(f"[{p.title}] 문제/해설 유형 불일치: {sorted(qk ^ ak)}")
        if not qk:
            problems.append(f"[{p.title}] 생성된 문항이 하나도 없습니다.")
    if problems:
        raise ValidationError("검증 실패:\n" + "\n".join(problems))


def validate_numbering(passages: list[Passage], start: int = 1,
                       type_order=TYPE_ORDER) -> list[list[int]]:
    """조판 결과의 문항 번호가 1..N 연속인지 확인하고, 지문별 번호 목록을 돌려준다.

    각 지문은 '실제로 생성된 문항 수'만큼 번호를 가지며(부분 생성 허용), 문서 전체
    번호는 start..(start + 총문항수 - 1) 로 연속이어야 한다. 문제·해설은 같은 번호를 공유.
    """
    numbers: list[list[int]] = []
    n = start
    for p in passages:
        cnt = len(present_types(p, type_order))
        block = list(range(n, n + cnt))
        numbers.append(block)
        n += cnt

    flat = [num for block in numbers for num in block]
    expected = list(range(start, start + len(flat)))
    if flat != expected:
        raise ValidationError(f"문항 번호가 연속이 아닙니다: {flat} != {expected}")
    return numbers
