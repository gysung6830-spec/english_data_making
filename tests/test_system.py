"""교습소 시스템 층(라이브러리·커리큘럼·운영·자료팩) 오프라인 테스트.

실행: python -m tests.test_system   (또는 pytest)
API 도, PDF 렌더러(weasyprint)도 없이 돌아간다.
실제 `library/`·`school/` 데이터는 건드리지 않고 임시 폴더에서만 검증한다.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from samples.sample_mock import mock_report
from src import packs, render
from src.curriculum import load_curriculum, level_of_passage
from src.library import Library, body_hash
from src.school import School


def _report(title: str, words: list[tuple[str, str]] | None = None):
    """제목과 어휘만 갈아 끼운 목 리포트."""
    rep = mock_report(title=title)
    if words:
        items = []
        for i, (w, m) in enumerate(words, start=1):
            base = rep.vocab.items[0].model_copy(deep=True)
            base.no, base.word, base.meaning = i, w, m
            base.synonyms, base.antonyms = "", ""
            items.append(base)
        rep = rep.model_copy(
            update={"vocab": rep.vocab.model_copy(update={"items": items})})
    # 같은 지문으로 취급되지 않도록 본문을 제목으로 살짝 바꿔 준다
    sents = [s.model_copy(update={"english": f"{title} {s.english}"})
             for s in rep.literal.sentences]
    return rep.model_copy(
        update={"literal": rep.literal.model_copy(update={"sentences": sents})})


# ---- 1. 라이브러리: 등록 · 중복 방지 · 검색 --------------------------------
def test_library_add_and_dedupe():
    with tempfile.TemporaryDirectory() as tmp:
        lib = Library(Path(tmp))
        rep = _report("Curiosity")

        mat, created = lib.add(rep, level="H1", category="mock", source="6월 모평",
                               tags=["과학", "논설문"])
        assert created and mat.id == "H1-MOCK-0001", mat.id
        assert mat.stats.vocab == len(rep.vocab.items)
        assert mat.stats.sentences == len(rep.literal.sentences)
        assert mat.vocab and mat.grammar_points

        # 같은 지문을 또 넣으면 새로 만들지 않고 기존 것을 돌려준다
        again, created2 = lib.add(rep, level="H1", category="mock")
        assert not created2 and again.id == mat.id

        # 다른 지문은 다음 번호를 받는다
        other, created3 = lib.add(_report("Memory"), level="H1", category="mock")
        assert created3 and other.id == "H1-MOCK-0002", other.id

        # 저장한 분석 결과가 그대로 되살아난다(→ API 없이 PDF 재생성 가능)
        back = lib.load_report(mat.id)
        assert back.title == rep.title
        assert len(back.vocab.items) == len(rep.vocab.items)

        # 검색
        assert len(lib.search(level="H1")) == 2
        assert len(lib.search(category="csat")) == 0
        assert len(lib.search(tag="과학")) == 1
        assert len(lib.search(q="memory")) == 1          # 제목으로 검색
        assert len(lib.search(q="curiosity")) == 2       # 핵심 어휘로도 검색된다
        assert len(lib.search(unused=True)) == 2
    print("PASS  라이브러리 등록·중복방지·검색")


def test_body_hash_ignores_formatting():
    # 대소문자·공백·문장부호 차이는 같은 지문으로 본다
    assert body_hash("The Cat, sat!") == body_hash("the   cat sat")
    assert body_hash("cat sat") != body_hash("dog sat")
    # 숫자만 다른 지문(연도·통계 개정판)은 다른 지문으로 봐야 한다
    assert body_hash("grew in 1990") != body_hash("grew in 2020")
    print("PASS  지문 fingerprint(중복 판별)")


def test_library_catalog_and_stats():
    with tempfile.TemporaryDirectory() as tmp:
        lib = Library(Path(tmp))
        lib.add(_report("A"), level="H1", category="mock")
        lib.add(_report("B"), level="M3", category="textbook")
        cj, cm = lib.rebuild_catalog()
        assert cj.exists() and cm.exists()
        md = cm.read_text(encoding="utf-8")
        assert "H1-MOCK-0001" in md and "M3-TXT-0001" in md

        st = lib.stats()
        assert st["total"] == 2
        assert st["by_level"] == {"H1": 1, "M3": 1}
        assert st["vocab_unique"] > 0
    print("PASS  카탈로그 생성·통계")


# ---- 2. 커리큘럼: 진도표 · 갭 리포트 ---------------------------------------
def test_curriculum_plan():
    cur = load_curriculum()
    assert len(cur.levels) >= 9
    rows = cur.plan("H1")
    assert len(rows) == cur.term_weeks
    assert rows[0]["week"] == 1 and rows[0]["grammar"]
    # 4주마다 도는 누적 어휘 시험이 4·8·12·16주차에 잡혀야 한다
    weeks_with_cumulative = [r["week"] for r in rows
                             if "누적 어휘 시험" in r["assessments"]]
    assert weeks_with_cumulative == [4, 8, 12, 16], weeks_with_cumulative
    # 주차별 지문 번호가 끊기지 않고 이어진다
    assert rows[1]["passage_from"] == rows[0]["passage_to"] + 1
    print("PASS  커리큘럼 주차 진도표")


def test_curriculum_gap():
    cur = load_curriculum()
    with tempfile.TemporaryDirectory() as tmp:
        lib = Library(Path(tmp))
        lib.add(_report("A"), level="H1", category="mock")
        rows = {r["level"]: r for r in cur.gap_report(lib)}
        h1 = rows["H1"]
        assert h1["have"] == 1
        assert h1["missing"] == h1["target"] - 1
        # 유형별로도 쪼개진다 (source_mix 비율 × 목표치)
        src = {r["category"]: r for r in cur.source_gap(lib, "H1")}
        assert src["mock"]["have"] == 1
        assert src["mock"]["target"] > 1
        assert sum(r["share"] for r in src.values()) == 100
    print("PASS  자료 부족분(갭) 리포트")


def test_level_suggestion():
    cur = load_curriculum()
    assert level_of_passage(cur, 80, 8) in ("E1", "E2")
    assert level_of_passage(cur, 230, 26) in ("H1", "H2", "H3")
    print("PASS  지문 길이 기반 레벨 추천")


# ---- 3. 운영: 진도 · 성적 · 다음 회차 --------------------------------------
def _school_with_class(tmp: Path) -> School:
    (tmp / "classes.yaml").write_text(
        "classes:\n"
        "  - code: H1A\n    name: 고1 A\n    level: H1\n"
        "    days: [월, 목]\n    time: '19:00'\n    students: [S001]\n"
        "    active: true\n", encoding="utf-8")
    (tmp / "students.yaml").write_text(
        "students:\n  - code: S001\n    name: 학생A\n    level: H1\n"
        "    active: true\n", encoding="utf-8")
    return School(tmp)


def test_progress_and_next_session():
    cur = load_curriculum()
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        lib = Library(Path(t1))
        sc = _school_with_class(Path(t2))
        ids = [lib.add(_report(f"P{i}"), level="H1", category="mock")[0].id
               for i in range(4)]

        # 첫 회차: 아직 기록이 없으니 1회차 · 1주차 · 첫 문법 주제
        plan = sc.next_session("H1A", cur, lib)
        assert plan["session_no"] == 1 and plan["week"] == 1
        assert plan["grammar"] == cur.level("H1").grammar_sequence[0]
        assert plan["need"] == 1                    # 주 2편 ÷ 주 2회 = 회차당 1편
        assert len(plan["candidates"]) == 3         # 후보는 필요 수의 3배까지 보여 준다
        assert plan["shortage"] == 0

        # 수업 기록 → 쓴 자료는 다음 추천에서 빠지고, 자료에 사용 이력이 남는다
        log = sc.log_session("H1A", ids[:2], grammar="테스트", lib=lib)
        assert log.session_no == 1
        assert lib.get(ids[0]).used_in == ["H1A/1회"]
        assert sc.used_materials("H1A") == ids[:2]

        plan2 = sc.next_session("H1A", cur, lib)
        assert plan2["session_no"] == 2
        assert {c["id"] for c in plan2["candidates"]} == set(ids[2:])

        # 2회차까지 하면 2주차로 넘어간다(주 2회 기준)
        sc.log_session("H1A", ids[2:], lib=lib)
        plan3 = sc.next_session("H1A", cur, lib)
        assert plan3["week"] == 2
        assert plan3["grammar"] == cur.level("H1").grammar_sequence[1]
        assert plan3["shortage"] > 0        # 자료가 바닥나면 부족분을 알려준다
    print("PASS  진도 기록·다음 회차 추천")


def test_report_card_and_weak_words():
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        lib = Library(Path(t1))
        sc = _school_with_class(Path(t2))
        mid = lib.add(_report("P"), level="H1", category="mock")[0].id
        sc.log_session("H1A", [mid], absent=["S001"], lib=lib)
        sc.log_session("H1A", [], lib=lib)
        sc.log_score("S001", score=16, total=20, wrong=["vital", "abandon"])
        sc.log_score("S001", score=18, total=20, wrong=["vital"])

        card = sc.report_card("S001")
        assert card["tests"] == 2 and card["score"] == 34 and card["total"] == 40
        assert card["mastery"] == 0.85
        assert card["sessions"] == 2 and card["attendance"] == 0.5
        assert card["weak_words"][0] == ("vital", 2)
    print("PASS  학생 리포트·오답 누적")


# ---- 4. 자료 팩: 어휘 합본 · 문법 묶음 -------------------------------------
def test_merge_vocab_dedupes_and_renumbers():
    a = _report("A", [("vital", "필수적인"), ("abandon", "버리다")])
    b = _report("B", [("vital", "필수적인"), ("shift", "변화")])
    items = packs.merge_vocab([a, b])
    assert [i.word for i in items] == ["vital", "abandon", "shift"]
    assert [i.no for i in items] == [1, 2, 3]

    merged = packs.merged_report([a, b], "4주 누적")
    assert merged.title == "4주 누적"
    assert len(merged.vocab.items) == 3
    # 어휘 외 섹션은 렌더러가 쓰지 않지만, 스키마는 온전해야 한다
    assert merged.literal.sentences and merged.grammar.items
    print("PASS  누적 어휘 합본(중복 제거·번호 재부여)")


def test_grammar_groups():
    a, b = _report("A"), _report("B")
    groups = render.collect_grammar_groups([a, b])
    assert groups, "문법 묶음이 비었습니다"
    # 두 지문에 같은 포인트가 있으므로 count 가 2인 그룹이 나와야 한다
    assert groups[0]["count"] == 2
    # 자주 나온 순으로 정렬된다
    assert all(groups[i]["count"] >= groups[i + 1]["count"]
               for i in range(len(groups) - 1))
    assert groups[0]["examples"] and groups[0]["examples"][0]["english"]
    # 같은 예문이 여러 지문에 겹쳐도 한 번만 실린다
    for g in groups:
        texts = [e["english"].lower() for e in g["examples"]]
        assert len(texts) == len(set(texts)), g["point"]

    key_only = render.collect_grammar_groups([a, b], key_only=True)
    assert len(key_only) <= len(groups)
    print("PASS  문법 누적 시트 묶기")


def test_personal_test_source_lookup():
    """개인 시험지는 라이브러리에 있는 단어만 쓰고, 없는 단어는 걸러 낸다."""
    with tempfile.TemporaryDirectory() as tmp:
        lib = Library(Path(tmp))
        lib.add(_report("A", [("vital", "필수적인"), ("abandon", "버리다")]),
                level="H1", category="mock")
        idx = lib.vocab_index()
        assert "vital" in idx and "abandon" in idx
        assert "nonexistentword" not in idx
    print("PASS  개인 시험지 단어 조회")


def run_all():
    test_library_add_and_dedupe()
    test_body_hash_ignores_formatting()
    test_library_catalog_and_stats()
    test_curriculum_plan()
    test_curriculum_gap()
    test_level_suggestion()
    test_progress_and_next_session()
    test_report_card_and_weak_words()
    test_merge_vocab_dedupes_and_renumbers()
    test_grammar_groups()
    test_personal_test_source_lookup()
    print("\n시스템 층 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
