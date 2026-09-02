"""커리큘럼 층 — 레벨 정의를 읽어 진도표를 만들고, 자료 부족분을 계산한다.

`curriculum/levels.yaml` 의 문법 시퀀스와 `curriculum/syllabus.yaml` 의 수업
규격을 결합하면 주차별 진도표가 나온다. 진도표는 손으로 쓰지 않는다 —
레벨 정의를 고치면 진도표가 따라 바뀌는 쪽이 몇 년을 버틴다.

또 하나의 역할은 **갭 리포트**다. 개원 전 가장 중요한 질문은
"자료를 얼마나 모았나"가 아니라 "어느 레벨의 무슨 자료가 아직 비어 있나"다.
`gap_report()` 가 그 답을 표로 돌려준다.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import ROOT
from .library import CATEGORIES, Library

CURRICULUM_DIR = ROOT / "curriculum"
LEVELS_PATH = CURRICULUM_DIR / "levels.yaml"
SYLLABUS_PATH = CURRICULUM_DIR / "syllabus.yaml"


@dataclass
class Level:
    code: str
    name: str
    grades: str = ""
    vocab_target: int = 0
    sentence_words: tuple[int, int] = (0, 0)
    passage_words: tuple[int, int] = (0, 0)
    material_target: int = 0
    source_mix: dict[str, int] = None       # type: ignore[assignment]
    focus: str = ""
    grammar_sequence: list[str] = None      # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.source_mix = self.source_mix or {}
        self.grammar_sequence = self.grammar_sequence or []


@dataclass
class Curriculum:
    term_weeks: int
    levels: list[Level]
    syllabus: dict[str, Any]

    # -- 조회 --------------------------------------------------------------
    def level(self, code: str) -> Level:
        code = (code or "").upper()
        for lv in self.levels:
            if lv.code == code:
                return lv
        raise KeyError(
            f"모르는 레벨입니다: {code} (가능: {', '.join(l.code for l in self.levels)})")

    @property
    def codes(self) -> list[str]:
        return [lv.code for lv in self.levels]

    @property
    def passages_per_week(self) -> int:
        return int(self.syllabus.get("schedule", {}).get("passages_per_week", 2))

    # -- 진도표 ------------------------------------------------------------
    def plan(self, code: str) -> list[dict]:
        """레벨 하나의 주차별 진도표를 만든다.

        각 주에 문법 주제 · 필요한 지문 수 · 그 주에 도는 평가가 붙는다.
        """
        lv = self.level(code)
        per_week = self.passages_per_week
        assessments = self.syllabus.get("assessments", []) or []
        reports = self.syllabus.get("reporting", []) or []
        rows: list[dict] = []
        for i, topic in enumerate(lv.grammar_sequence, start=1):
            due = [a["name"] for a in assessments
                   if a.get("every_weeks") and i % int(a["every_weeks"]) == 0]
            memo = [r["name"] for r in reports
                    if r.get("every_weeks") and i % int(r["every_weeks"]) == 0]
            rows.append({
                "week": i,
                "grammar": topic,
                "passages": per_week,
                "passage_from": (i - 1) * per_week + 1,
                "passage_to": i * per_week,
                "assessments": due,
                "reporting": memo,
            })
        return rows

    # -- 갭 리포트 ---------------------------------------------------------
    def gap_report(self, lib: Library, *, status: str = "ready") -> list[dict]:
        """레벨별로 '목표 대비 몇 건이 비어 있는지' 계산한다."""
        rows: list[dict] = []
        for lv in self.levels:
            have = len(lib.search(level=lv.code, status=status))
            target = lv.material_target
            rows.append({
                "level": lv.code,
                "name": lv.name,
                "have": have,
                "target": target,
                "missing": max(target - have, 0),
                "pct": round(have / target * 100, 1) if target else 0.0,
                "weeks_covered": round(have / self.passages_per_week, 1),
            })
        return rows

    def source_gap(self, lib: Library, code: str, *, status: str = "ready") -> list[dict]:
        """한 레벨 안에서 '유형별로' 몇 건이 비었는지 계산한다.

        source_mix 비율 × 목표 자료 수 = 유형별 목표치.
        """
        lv = self.level(code)
        rows: list[dict] = []
        for cat, pct in sorted(lv.source_mix.items(), key=lambda kv: -kv[1]):
            target = math.ceil(lv.material_target * pct / 100)
            have = len(lib.search(level=lv.code, category=cat, status=status))
            rows.append({
                "category": cat,
                "code": CATEGORIES.get(cat, "?"),
                "share": pct,
                "have": have,
                "target": target,
                "missing": max(target - have, 0),
            })
        return rows

    def total_target(self) -> int:
        return sum(lv.material_target for lv in self.levels)


def load_curriculum(levels_path: Path | None = None,
                    syllabus_path: Path | None = None) -> Curriculum:
    lp = Path(levels_path) if levels_path else LEVELS_PATH
    sp = Path(syllabus_path) if syllabus_path else SYLLABUS_PATH
    if not lp.exists():
        raise FileNotFoundError(f"레벨 정의 파일이 없습니다: {lp}")
    data = yaml.safe_load(lp.read_text(encoding="utf-8")) or {}
    syllabus = (yaml.safe_load(sp.read_text(encoding="utf-8")) or {}) if sp.exists() else {}

    levels: list[Level] = []
    for raw in data.get("levels", []) or []:
        levels.append(Level(
            code=str(raw.get("code", "")).upper(),
            name=str(raw.get("name", "")),
            grades=str(raw.get("grades", "")),
            vocab_target=int(raw.get("vocab_target", 0)),
            sentence_words=tuple(raw.get("sentence_words", [0, 0]))[:2],  # type: ignore[arg-type]
            passage_words=tuple(raw.get("passage_words", [0, 0]))[:2],    # type: ignore[arg-type]
            material_target=int(raw.get("material_target", 0)),
            source_mix={k: int(v) for k, v in (raw.get("source_mix") or {}).items()},
            focus=str(raw.get("focus", "")),
            grammar_sequence=list(raw.get("grammar_sequence") or []),
        ))
    if not levels:
        raise ValueError(f"레벨이 하나도 정의되지 않았습니다: {lp}")
    return Curriculum(term_weeks=int(data.get("term_weeks", 16)),
                      levels=levels, syllabus=syllabus)


def level_of_passage(cur: Curriculum, words: int, avg_sentence: float) -> str:
    """지문 길이·문장 길이로 어느 레벨에 어울리는 지문인지 추천한다.

    자동 분류가 아니라 '등록할 때 기본값 제안' 용도다 — 최종 판단은 사람이 한다.
    """
    best, best_score = "", float("inf")
    for lv in cur.levels:
        lo_w, hi_w = lv.passage_words or (0, 0)
        lo_s, hi_s = lv.sentence_words or (0, 0)
        mid_w = (lo_w + hi_w) / 2 or 1
        mid_s = (lo_s + hi_s) / 2 or 1
        score = abs(words - mid_w) / mid_w + abs(avg_sentence - mid_s) / mid_s
        if score < best_score:
            best, best_score = lv.code, score
    return best
