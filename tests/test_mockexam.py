"""동형모의고사 오프라인 테스트 (API 키 없이 전 구간 검증)."""
from __future__ import annotations

from pathlib import Path

import pytest

from mockexam.core.blueprint import blueprint_from_profile
from mockexam.ingest.loader import detect_format, load_passages, split_passages
from mockexam.corpus.selector import assign_passages, profile_passage
from mockexam.pipeline import generate_mock
from mockexam.school import (
    resolve_profile, standard_skeleton, load_schools_index,
)
from mockexam.verify.verifier import verify

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "input" / "sample_passages.txt"


# ---------------------------------------------------------------------------
# 학교 프로파일 / blueprint
# ---------------------------------------------------------------------------
def test_schools_index_has_five():
    ids = {s["school_id"] for s in load_schools_index()}
    assert {"munsan_ms", "daegok_ms", "jinyang_hs", "jeil_ghs", "dongmyeong_hs"} <= ids


def test_jinyang_blueprint_matches_spec():
    prof = resolve_profile("jinyang_hs", 1)
    assert prof["learned"] is True
    bp = blueprint_from_profile(prof, 1)
    assert len(bp.choice_items) == 18
    assert len(bp.essay_items) == 9
    assert abs(bp.total_score - 100.0) < 0.01


def test_unlearned_school_uses_standard_skeleton_not_jinyang():
    prof = resolve_profile("munsan_ms", 1)
    assert prof["learned"] is False
    bp = blueprint_from_profile(prof, 1)
    # 진양고(18/9)를 베끼지 않는다.
    assert (len(bp.choice_items), len(bp.essay_items)) != (18, 9)
    assert abs(bp.total_score - 100.0) < 0.01


def test_middle_and_high_skeletons_sum_to_100():
    for level in ("middle", "high"):
        skel = standard_skeleton(level, 1)
        total = sum(i["score"] for i in skel["item_template"])
        assert abs(total - 100.0) < 0.01, (level, total)


# ---------------------------------------------------------------------------
# 입력 파싱 / 형식 판별
# ---------------------------------------------------------------------------
def test_passage_split_and_format_detection():
    passages = load_passages([SAMPLE])
    assert len(passages) == 4
    fmts = {p.format_type for p in passages}
    assert "dialogue" in fmts
    assert "notice" in fmts


def test_detect_format_dialogue():
    txt = "M: Hello there.\nW: Hi, how are you?\nM: Good, thanks."
    fmt, speakers = detect_format(txt)
    assert fmt == "dialogue"


# ---------------------------------------------------------------------------
# 배정 (형식 하드제약)
# ---------------------------------------------------------------------------
def test_assignment_format_hard_constraint():
    passages = load_passages([SAMPLE])
    pmap = {p.id: p for p in passages}
    prof = resolve_profile("jinyang_hs", 1)
    bp = blueprint_from_profile(prof, 1)
    assigns = assign_passages(bp, passages, difficulty="mid")
    for a in assigns:
        if a.type == "dialogue_mismatch" and a.passage_id:
            assert pmap[a.passage_id].format_type == "dialogue"
        if a.type == "notice_match" and a.passage_id:
            assert pmap[a.passage_id].format_type == "notice"


def test_reuse_cap_max_three():
    passages = load_passages([SAMPLE])
    prof = resolve_profile("jinyang_hs", 1)
    bp = blueprint_from_profile(prof, 1)
    assigns = assign_passages(bp, passages, difficulty="mid")
    from collections import Counter
    c = Counter(a.passage_id for a in assigns if a.passage_id
                and not a.passage_id.startswith("__"))
    # 대체(substituted) 슬롯은 상한을 넘을 수 있으나, 정상 배정은 3 이하 지향
    normal = Counter(a.passage_id for a in assigns
                     if a.passage_id and a.note is None)
    assert all(v <= 3 for v in normal.values()), normal


# ---------------------------------------------------------------------------
# 전체 파이프라인 (오프라인) + 검증기
# ---------------------------------------------------------------------------
def test_generate_offline_passes_verifier():
    res = generate_mock("jinyang_hs", [SAMPLE], difficulty="중", grade=1, client=None)
    rep = res.verify_report
    # 핵심 검증(문항수/배점/유형배치/번호연속)은 반드시 통과
    by = {c.name: c for c in rep.checks}
    assert by["문항수"].ok, by["문항수"].detail
    assert by["배점합"].ok, by["배점합"].detail
    assert by["유형·배치"].ok, by["유형·배치"].detail
    assert by["번호연속"].ok, by["번호연속"].detail
    assert by["정답유일성"].ok, by["정답유일성"].detail


def test_generate_offline_high_school_unlearned():
    res = generate_mock("dongmyeong_hs", [SAMPLE], difficulty="상", grade=2, client=None)
    assert res.blueprint.meta.learned is False
    by = {c.name: c for c in res.verify_report.checks}
    assert by["배점합"].ok
    assert by["번호연속"].ok
