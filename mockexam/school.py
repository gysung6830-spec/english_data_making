"""학교별 프로파일 IO + 학교급 표준 골격 (§8.5).

- 각 학교는 profiles/<school_id>/ 아래로 완전히 분리된다.
- 학습된 학교는 profile.json 의 item_template/type_distribution 을 쓴다.
- 미학습 학교는 진양고를 베끼지 않고 **학교급 표준 골격**(§8.5.6)으로만 생성한다.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "profiles"


# ---------------------------------------------------------------------------
# 학교 인덱스 (§8.5.1)
# ---------------------------------------------------------------------------
def load_schools_index() -> list[dict[str, Any]]:
    idx = PROFILES_DIR / "schools.json"
    if not idx.exists():
        return []
    return json.loads(idx.read_text(encoding="utf-8")).get("schools", [])


def find_school(school_id: str) -> dict[str, Any] | None:
    for s in load_schools_index():
        if s["school_id"] == school_id:
            return s
    return None


def register_school(school_id: str, name: str, level: str,
                    grades: list[int] | None = None) -> dict[str, Any]:
    """새 학교를 인덱스에 추가(§8.5.1). 이미 있으면 그대로 반환."""
    existing = find_school(school_id)
    if existing:
        return existing
    schools = load_schools_index()
    entry = {"school_id": school_id, "name": name, "level": level,
             "grades": grades or [1, 2, 3]}
    schools.append(entry)
    idx = PROFILES_DIR / "schools.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(json.dumps({"schools": schools}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    (PROFILES_DIR / school_id / "exams").mkdir(parents=True, exist_ok=True)
    return entry


# ---------------------------------------------------------------------------
# profile.json IO (§8.5.3)
# ---------------------------------------------------------------------------
def profile_path(school_id: str) -> Path:
    return PROFILES_DIR / school_id / "profile.json"


def load_profile(school_id: str) -> dict[str, Any] | None:
    """학습된 profile.json 로드. 없으면 None(=미학습)."""
    p = profile_path(school_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_profile(school_id: str, profile: dict[str, Any]) -> Path:
    p = profile_path(school_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def archive_exam(school_id: str, exam_name: str, blueprint_dict: dict[str, Any]) -> Path:
    """학습에 쓴 원본 blueprint 를 exams/ 에 아카이브(§8.5.2)."""
    d = PROFILES_DIR / school_id / "exams"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{exam_name}.json"
    path.write_text(json.dumps(blueprint_dict, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 학교급 표준 골격 (§8.5.6) — 진양고 복제 금지, 임시 기본값
# ---------------------------------------------------------------------------
def _normalize_scores(items: list[dict[str, Any]], total: float) -> list[dict[str, Any]]:
    """배점 합이 정확히 total 이 되도록 마지막 항목으로 보정한다(검증기 통과 보장)."""
    if not items:
        return items
    s = round(sum(i["score"] for i in items), 2)
    diff = round(total - s, 2)
    items[-1]["score"] = round(items[-1]["score"] + diff, 2)
    return items


# 중학교 표준: 지문 짧고 어휘 쉬움, 어법 기초, 서술형 단순. 고난도 유형 제외.
_MIDDLE_CHOICE_TYPES = [
    "main_point", "title", "grammar", "vocab_odd", "grammar", "blank_single",
    "order", "irrelevant_sentence", "dialogue_mismatch", "notice_match",
    "main_point", "blank_single", "vocab_odd", "inference_mismatch",
]
_MIDDLE_ESSAY_TYPES = [
    "word_arrange", "summary_fill_from_text", "blank_choose_no_change",
    "prep_find_and_translate",
]

# 고등학교 표준: 수능형 유형을 폭넓게, 난이도 상향. 배치·배점은 임시값.
_HIGH_CHOICE_TYPES = [
    "grammar_vocab_mix", "grammar", "vocab_odd", "main_point", "title",
    "blank_single", "order", "irrelevant_sentence", "implied_meaning",
    "vocab_3blank_abc", "grammar", "inference_mismatch", "dialogue_mismatch",
    "notice_match", "summary_ab", "main_point", "blank_single", "vocab_odd",
]
_HIGH_ESSAY_TYPES = [
    "prep_find_and_translate", "word_arrange", "condition_write_inflect",
    "summary_fill_from_text", "arrange_and_translate", "blank_choose_no_change",
    "grammar_fix_and_answer",
]

_UNDERLINE_TYPES = {"grammar", "grammar_vocab_mix", "vocab_odd"}


def _build_items(choice_types: list[str], essay_types: list[str],
                 choice_total: float, essay_total: float,
                 choice_score: float, essay_score: float) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for i, t in enumerate(choice_types, 1):
        it: dict[str, Any] = {"no": i, "section": "choice", "type": t, "score": choice_score}
        if t in _UNDERLINE_TYPES:
            it["underlines"] = 5
        items.append(it)
    for i, t in enumerate(essay_types, 1):
        items.append({"no": i, "section": "essay", "type": t, "score": essay_score})
    # 합을 정확히 맞춘다.
    choice = _normalize_scores([x for x in items if x["section"] == "choice"], choice_total)
    essay = _normalize_scores([x for x in items if x["section"] == "essay"], essay_total)
    return choice + essay


def standard_skeleton(level: str, grade: int = 1) -> dict[str, Any]:
    """미학습 학교용 학교급 표준 골격(§8.5.6).

    반환값은 profile 유사 dict(learned=False). blueprint.py 가 이걸로 blueprint 를 만든다.
    """
    if level == "middle":
        items = _build_items(_MIDDLE_CHOICE_TYPES, _MIDDLE_ESSAY_TYPES,
                             choice_total=72, essay_total=28,
                             choice_score=5.0, essay_score=7.0)
        trend = "low"
    else:  # high
        items = _build_items(_HIGH_CHOICE_TYPES, _HIGH_ESSAY_TYPES,
                             choice_total=64, essay_total=36,
                             choice_score=3.5, essay_score=5.0)
        trend = "mid"
    return {
        "learned": False,
        "level": level,
        "grade": grade,
        "subject": "영어",
        "time_min": 45 if level == "middle" else 50,
        "counts": {"choice": len([i for i in items if i["section"] == "choice"]),
                   "essay": len([i for i in items if i["section"] == "essay"])},
        "score_pattern": {"total": 100},
        "difficulty_trend": trend,
        "item_template": items,
        "stem_style": {},
        "grammar_focus": ["시제", "수일치", "품사"] if level == "middle"
                          else ["관계사", "태", "분사"],
        "notes": [f"{('중학교' if level=='middle' else '고등학교')} 표준 골격(미학습, 임시 기본값)"],
    }


def resolve_profile(school_id: str, grade: int = 1) -> dict[str, Any]:
    """생성에 쓸 프로파일을 확정한다.

    - 학습된 학교: profile.json 사용.
    - 미학습 학교: 학교급 표준 골격(§8.5.6)으로 대체(진양고 복제 안 함).
    """
    prof = load_profile(school_id)
    if prof and prof.get("learned") and prof.get("item_template"):
        return prof
    school = find_school(school_id)
    level = (school or {}).get("level", "high")
    name = (school or {}).get("name", school_id)
    skel = standard_skeleton(level, grade)
    skel.update({"school_id": school_id, "name": name})
    return skel
