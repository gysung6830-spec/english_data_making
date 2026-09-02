"""운영 층 — 반·학생·진도·성적을 다루고, '다음 수업에 뭘 쓸지'를 뽑아낸다.

이 층이 있어야 라이브러리와 커리큘럼이 비로소 '시스템'이 된다.
    커리큘럼(무엇을 언제) + 라이브러리(무슨 자료가 있나) + 진도(어디까지 했나)
    → 다음 회차 수업 준비물

개인정보 원칙
    - `school/*.yaml` 과 `school/*.jsonl` 실데이터는 git 에 올리지 않는다(.gitignore).
    - 저장소에는 `*.example.yaml` 만 남긴다.
    - 학생은 이름 대신 **학생코드**로 다룬다. 이름은 한 파일에만 둔다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml

from .config import ROOT
from .library import Library

SCHOOL_DIR = ROOT / "school"
STUDENTS_PATH = SCHOOL_DIR / "students.yaml"
CLASSES_PATH = SCHOOL_DIR / "classes.yaml"
PROGRESS_PATH = SCHOOL_DIR / "progress.jsonl"
SCORES_PATH = SCHOOL_DIR / "scores.jsonl"


@dataclass
class Student:
    code: str
    name: str = ""
    level: str = ""
    school: str = ""
    grade: str = ""
    enrolled: str = ""
    active: bool = True
    note: str = ""


@dataclass
class ClassRoom:
    code: str
    name: str = ""
    level: str = ""
    days: list[str] = field(default_factory=list)
    time: str = ""
    students: list[str] = field(default_factory=list)   # 학생코드
    started: str = ""
    active: bool = True


@dataclass
class SessionLog:
    """한 회차 수업 기록."""
    date: str
    class_code: str
    session_no: int
    material_ids: list[str] = field(default_factory=list)
    grammar: str = ""
    homework: str = ""
    absent: list[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"date": self.date, "class_code": self.class_code,
                "session_no": self.session_no, "material_ids": self.material_ids,
                "grammar": self.grammar, "homework": self.homework,
                "absent": self.absent, "note": self.note}


class School:
    """`school/` 폴더를 다루는 저장소 객체."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else SCHOOL_DIR
        self.root.mkdir(parents=True, exist_ok=True)
        self.students_path = self.root / "students.yaml"
        self.classes_path = self.root / "classes.yaml"
        self.progress_path = self.root / "progress.jsonl"
        self.scores_path = self.root / "scores.jsonl"

    # -- 명단 --------------------------------------------------------------
    def students(self, *, active_only: bool = True) -> list[Student]:
        raw = _read_yaml_list(self.students_path, "students")
        out = [Student(**{k: v for k, v in s.items() if k in Student.__annotations__})
               for s in raw]
        return [s for s in out if s.active] if active_only else out

    def student(self, code: str) -> Student:
        for s in self.students(active_only=False):
            if s.code == code:
                return s
        raise KeyError(f"학생을 찾을 수 없습니다: {code}")

    def classes(self, *, active_only: bool = True) -> list[ClassRoom]:
        raw = _read_yaml_list(self.classes_path, "classes")
        out = [ClassRoom(**{k: v for k, v in c.items()
                            if k in ClassRoom.__annotations__}) for c in raw]
        return [c for c in out if c.active] if active_only else out

    def classroom(self, code: str) -> ClassRoom:
        for c in self.classes(active_only=False):
            if c.code == code:
                return c
        raise KeyError(f"반을 찾을 수 없습니다: {code}")

    # -- 진도 --------------------------------------------------------------
    def progress(self, class_code: str = "") -> list[SessionLog]:
        rows = _read_jsonl(self.progress_path)
        logs = [SessionLog(
            date=r.get("date", ""), class_code=r.get("class_code", ""),
            session_no=int(r.get("session_no", 0)),
            material_ids=list(r.get("material_ids", [])),
            grammar=r.get("grammar", ""), homework=r.get("homework", ""),
            absent=list(r.get("absent", [])), note=r.get("note", ""),
        ) for r in rows]
        if class_code:
            logs = [l for l in logs if l.class_code == class_code]
        return sorted(logs, key=lambda l: (l.date, l.session_no))

    def log_session(self, class_code: str, material_ids: Iterable[str], *,
                    when: str = "", grammar: str = "", homework: str = "",
                    absent: Iterable[str] = (), note: str = "",
                    lib: Library | None = None) -> SessionLog:
        """수업 한 회차를 기록하고, 쓴 자료에 사용 이력을 남긴다."""
        self.classroom(class_code)      # 없는 반이면 여기서 에러
        prev = self.progress(class_code)
        log = SessionLog(
            date=when or date.today().isoformat(),
            class_code=class_code,
            session_no=(prev[-1].session_no + 1) if prev else 1,
            material_ids=[m for m in material_ids],
            grammar=grammar, homework=homework,
            absent=list(absent), note=note,
        )
        _append_jsonl(self.progress_path, log.to_dict())
        lib = lib or Library()
        for mid in log.material_ids:
            try:
                lib.mark_used(mid, f"{class_code}/{log.session_no}회")
            except KeyError:
                pass    # 라이브러리에 없는 ID 라도 진도 기록 자체는 남긴다
        return log

    def used_materials(self, class_code: str) -> list[str]:
        """그 반이 이미 쓴 자료 ID(사용 순서)."""
        seen: list[str] = []
        for log in self.progress(class_code):
            for mid in log.material_ids:
                if mid not in seen:
                    seen.append(mid)
        return seen

    # -- 성적 --------------------------------------------------------------
    def log_score(self, student_code: str, *, kind: str = "vocabtest",
                  score: int = 0, total: int = 0, when: str = "",
                  material_ids: Iterable[str] = (), wrong: Iterable[str] = (),
                  note: str = "") -> dict:
        """테스트 결과를 기록한다. `wrong` 에는 틀린 단어를 넣는다(개인 처방의 재료)."""
        row = {
            "date": when or date.today().isoformat(),
            "student": student_code, "kind": kind,
            "score": int(score), "total": int(total),
            "material_ids": list(material_ids),
            "wrong": [w.strip() for w in wrong if w and w.strip()],
            "note": note,
        }
        _append_jsonl(self.scores_path, row)
        return row

    def scores(self, student_code: str = "") -> list[dict]:
        rows = _read_jsonl(self.scores_path)
        if student_code:
            rows = [r for r in rows if r.get("student") == student_code]
        return sorted(rows, key=lambda r: r.get("date", ""))

    def weak_words(self, student_code: str, *, limit: int = 40) -> list[tuple[str, int]]:
        """그 학생이 자주 틀린 단어 순위 — 개인 맞춤 복습 시험지의 재료."""
        counts: dict[str, int] = {}
        for r in self.scores(student_code):
            for w in r.get("wrong", []):
                key = w.strip().lower()
                if key:
                    counts[key] = counts.get(key, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]

    def report_card(self, student_code: str) -> dict:
        """월간 리포트/상담에 쓰는 요약 숫자."""
        st = self.student(student_code)
        rows = self.scores(student_code)
        got = sum(r.get("score", 0) for r in rows)
        tot = sum(r.get("total", 0) for r in rows)
        my_classes = [c for c in self.classes(active_only=False)
                      if student_code in c.students]
        sessions = absent = 0
        for c in my_classes:
            for log in self.progress(c.code):
                sessions += 1
                if student_code in log.absent:
                    absent += 1
        return {
            "student": st.code, "name": st.name, "level": st.level,
            "classes": [c.code for c in my_classes],
            "tests": len(rows),
            "score": got, "total": tot,
            "mastery": round(got / tot, 3) if tot else 0.0,
            "sessions": sessions,
            "attendance": round((sessions - absent) / sessions, 3) if sessions else 0.0,
            "weak_words": self.weak_words(student_code, limit=10),
        }

    # -- 다음 회차 준비 ----------------------------------------------------
    def next_session(self, class_code: str, cur, lib: Library | None = None) -> dict:
        """다음 회차에 쓸 문법 주제와 후보 자료를 뽑는다.

        진도 기록으로 '몇 주차인지'를 알고, 커리큘럼에서 그 주의 문법 주제를,
        라이브러리에서 그 반이 아직 안 쓴 같은 레벨 자료를 골라 온다.
        """
        lib = lib or Library()
        room = self.classroom(class_code)
        level = room.level or ""
        logs = self.progress(class_code)
        per_week = cur.passages_per_week
        sessions_per_week = int(
            cur.syllabus.get("schedule", {}).get("sessions_per_week", 2)) or 1

        next_no = (logs[-1].session_no + 1) if logs else 1
        week = (next_no - 1) // sessions_per_week + 1
        seq = cur.level(level).grammar_sequence if level else []
        grammar = seq[(week - 1) % len(seq)] if seq else ""

        used = set(self.used_materials(class_code))
        pool = [m for m in lib.search(level=level, status="ready") if m.id not in used]
        # 아직 어느 반에도 안 쓴 자료를 먼저, 그다음 등록 순서대로
        pool.sort(key=lambda m: (bool(m.used_in), m.id))
        need = max(round(per_week / sessions_per_week), 1)   # 한 회차에 쓸 지문 수

        return {
            "class": class_code,
            "level": level,
            "session_no": next_no,
            "week": week,
            "grammar": grammar,
            "need": need,
            "candidates": [{"id": m.id, "title": m.title, "theme": m.theme_ko,
                            "category": m.category, "vocab": m.stats.vocab}
                           for m in pool[:need * 3]],
            "shortage": max(need - len(pool), 0),
        }


# ---------------------------------------------------------------------------
# 파일 입출력
# ---------------------------------------------------------------------------
def _read_yaml_list(path: Path, key: str) -> list[dict]:
    """실데이터가 없으면 같은 이름의 *.example.yaml 로 폴백한다."""
    if not path.exists():
        example = path.with_name(path.stem + ".example" + path.suffix)
        if not example.exists():
            return []
        path = example
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = data.get(key, []) or []
    return [r for r in rows if isinstance(r, dict)]


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue    # 한 줄이 깨져도 나머지 기록은 살린다
    return out


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
