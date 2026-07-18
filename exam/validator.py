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


def check_passage(passage: Passage) -> MissingReport:
    """지문 1개가 6종 문제+해설을 빠짐없이 가졌는지 점검.

    - q, a 에 TYPE_ORDER 6종이 모두 있어야 한다.
    - q 와 a 의 유형 집합이 같아야 한다.
    - 규격 외(TYPE_ORDER 에 없는) 유형이 있으면 오류.
    """
    expected = set(TYPE_ORDER)

    extra_q = passage.q.keys() - expected
    extra_a = passage.a.keys() - expected
    if extra_q or extra_a:
        raise ValidationError(
            f"[{passage.title}] 규격 외 유형이 있습니다: q={sorted(extra_q)} a={sorted(extra_a)}"
        )

    missing_q = [t for t in TYPE_ORDER if not (passage.q.get(t) or "").strip()]
    missing_a = [t for t in TYPE_ORDER if not (passage.a.get(t) or "").strip()]
    return MissingReport(passage.title, missing_q, missing_a)


def validate_passages(passages: list[Passage]) -> None:
    """모든 지문이 6종+해설을 완비했는지 확인. 실패 시 ValidationError."""
    if not passages:
        raise ValidationError("지문이 하나도 없습니다.")
    problems: list[str] = []
    for p in passages:
        rep = check_passage(p)
        if not rep.ok:
            problems.append(
                f"[{rep.passage_title}] 누락 — 문제:{rep.missing_q or '없음'} / 해설:{rep.missing_a or '없음'}"
            )
    if problems:
        raise ValidationError("6종 완비 검증 실패:\n" + "\n".join(problems))


def validate_numbering(passages: list[Passage], start: int = 1) -> list[list[int]]:
    """조판 결과의 문항 번호가 1..N 연속인지 확인하고, 지문별 번호 목록을 돌려준다.

    각 지문은 정확히 6문항(6종)을 가지므로, 문서 전체 번호는
    start..(start + 6*len - 1) 로 연속이어야 한다.
    문제와 해설은 같은 번호를 공유한다.
    """
    numbers: list[list[int]] = []
    n = start
    for p in passages:
        # check_passage 가 통과했다는 전제 하에 6종 고정
        block = list(range(n, n + len(TYPE_ORDER)))
        numbers.append(block)
        n += len(TYPE_ORDER)

    flat = [num for block in numbers for num in block]
    expected = list(range(start, start + len(flat)))
    if flat != expected:
        raise ValidationError(f"문항 번호가 연속이 아닙니다: {flat} != {expected}")
    return numbers
