"""오프라인 테스트: 시험지 생성 파이프라인을 API 없이 검증한다.

- 데모 데이터 검증·번호 연속·조판(HTML)
- 볼드 5곳 규칙
- 단일 지문 공유: 6종이 모두 같은 정본 문장에서 파생되는지
- LLM 경로(생성기)를 가짜 클라이언트로 대체해 스키마→build→검증→조판 배선
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from exam import build as B  # noqa: E402
from exam import pipeline, renderer, validator  # noqa: E402
from exam.demo_data import DNA, demo_passages  # noqa: E402
from exam.schemas import (  # noqa: E402
    Analysis,
    ContentOut,
    GrammarOut,
    GrammarReason,
    InsertOut,
    KeyTerm,
    OrderOut,
    ShortOut,
    TopicOut,
    VocabOut,
    WordMark,
    WrongReason,
)
from exam.gen2 import (  # noqa: E402
    AOut,
    BOut,
    DOut,
    EOut,
    FOut,
    GOut,
    Pair,
)
from exam.set2 import TYPE_ORDER2  # noqa: E402
from exam.types import TYPE_ORDER  # noqa: E402


def test_demo_validation_and_numbering() -> None:
    passages = demo_passages()
    validator.validate_passages(passages)
    numbers = validator.validate_numbering(passages, start=1)
    assert numbers == [[1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14]]
    print("✓ 데모 검증·번호 연속 통과:", numbers)


def test_render_html_bold_rules() -> None:
    html = renderer.render_html(demo_passages(), header_note="○○학원 고3")
    for cls in ("brand-title", "qnum", "passage-label", "answer-title",
                "answer-key", "boki-title", "cue"):
        assert cls in html, f"볼드 클래스 누락: {cls}"
    assert html.index('class="questions') < html.index('class="answers')
    assert "○○학원 고3" in html
    # 4개 섹션(학생용 → 교사용 → 빠른 정답 → 해설지)이 순서대로 존재
    for sec in ("학생용", "교사용", "빠른 정답", "정답 및 해설"):
        assert sec in html, f"섹션 누락: {sec}"
    order = [html.index("학생용 · 문제"), html.index("교사용 · 문제"),
             html.index("빠른 정답"), html.index("정답 및 해설 · 해설지")]
    assert order == sorted(order), "섹션 순서가 어긋납니다."
    assert "teach-exp" in html and "quick-grid" in html
    # 섹션 선택: 학생용만 → 교사용/빠른정답/해설지 배너 없음, 첫 섹션 break 해제
    only_student = renderer.render_html(demo_passages(), sections=["student"])
    assert "학생용 · 문제" in only_student
    assert "교사용 · 문제" not in only_student
    assert "빠른 정답" not in only_student
    assert "해설지" not in only_student
    assert "first-sec" in only_student
    # 교사용만 → 학생용 배너 없이 교사용이 첫 섹션(break 해제)
    only_teacher = renderer.render_html(demo_passages(), sections=["teacher"])
    assert "학생용 · 문제" not in only_teacher
    assert 'class="teacher first-sec"' in only_teacher
    print("✓ 조판 HTML·볼드 5곳·4섹션·섹션선택·머리글 통과")


def test_single_source_shared() -> None:
    """6종이 모두 '같은 정본 문장'을 공유하는지 확인.

    지문의 특징적인 원문 어구가 순서·삽입·주제·서술형 문제 본문에 모두 등장해야 한다.
    (어휘·어법은 지정 단어만 치환되므로 별도 확인.)
    """
    p = demo_passages()[0]  # DNA
    marker = "vanishingly small space"      # 정본에만 있는 특징 어구
    for t in ("order", "insert", "topic", "content", "short_answer"):
        assert marker in p.q[t], f"{t} 본문이 정본을 공유하지 않음"
    # 정본 문장이 실제로 각 유형에 그대로 들어갔는지(어휘는 밑줄 단어만 달라짐)
    assert "millions of ordinary hard drives combined" in p.q["order"]
    assert "millions of ordinary hard drives combined" in p.q["topic"]
    print("✓ 단일 지문 공유(6종이 같은 정본 사용) 통과")


def test_build_and_validators() -> None:
    s = DNA.sentences
    q, a = B.make_order(s, given_n=1, block_sizes=[2, 2, 2], display=[2, 1, 3], reason="r")
    assert "(A)" in q and "answer-key" in a

    # LLM 오류(개수 오산·범위 초과·대소문자)는 예외 대신 '자동 보정'되어야 한다
    q2, _ = B.make_order(s, given_n=99, block_sizes=[9, 9], display=[7, 7, 7], reason="r")
    assert "(A)" in q2                                   # 보정되어 정상 생성
    q3, _ = B.make_insert(s, remove_idx=0, reason="r")   # 첫 문장 → 내부로 보정
    assert "given-sentence" in q3
    q4, _ = B.make_vocab(s, [(1, "REMARKABLE", "notable"), (1, "small", "tiny"),
                             (3, "durable", "fragile"), (4, "efficiency", "eff"),
                             (5, "expensive", "costly")], 3, "r")
    assert "<u>" in q4                                   # 대소문자 달라도 매칭

    # 정말 불가능한 입력만 예외
    for bad in (
        lambda: B.make_vocab(s, [(1, "nonexistentword", "x")] * 5, 1, "r"),  # 없는 단어
        lambda: B.make_order(["only one."], 1, [1, 1, 1], [1, 2, 3], "r"),   # 문장 부족
    ):
        try:
            bad()
        except Exception:
            pass
        else:
            raise AssertionError("검증이 동작하지 않음")
    print("✓ build 변형기·자동 보정·검증 통과")


def test_error_guards() -> None:
    """오류 가드: 약어 문장분리, G 개수 범위, 조판 이스케이프."""
    from exam import build2
    from exam.analyzer import split_sentences
    assert len(split_sentences("Dr. Smith won the U.S. prize. He left. It ended.")) == 3
    try:
        build2.make_G(["s"], ["a", "b", "c", "d", "e"], 0, "r", {})
    except ValueError:
        pass
    else:
        raise AssertionError("G 0개 일치가 차단되지 않음")
    html = renderer.render_html(demo_passages(), header_note="X<b>&Y", doc_title="T<x>")
    assert "X&lt;b&gt;&amp;Y" in html and "<title>T&lt;x&gt;</title>" in html

    # A: 밑줄 중첩 없음 + 같은 단어 중복 지정 차단
    from exam import build2
    s = ["The cat sat on the mat.", "The cat ran fast.", "It ended well now here."]
    q, _ = build2.make_A(s, [(0, "cat", "CAT"), (0, "mat", "MAT"), (1, "ran", "RAN"),
                             (2, "ended", "ENDED"), (2, "well", "WELL")],
                         2, "r", ["1", "2", "3", "4", "5"])
    assert q.count("<u>") == 5 and "<u><span" not in q
    for bad in (
        lambda: build2.make_A(s, [(0, "cat", "x")] * 5, 1, "r", ["1", "2", "3", "4", "5"]),
        lambda: build2.make_F(s, 0, "The cat", ["1", "2", "3", "4", "5"], 1, "r", {}),  # 2회 등장
    ):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("모호성 가드가 동작하지 않음")
    print("✓ 오류 가드(약어분리·G개수·이스케이프·중첩/다중출현) 통과")


def test_set2_demo() -> None:
    """변형문제 2회(A~G) 데모: 검증·번호·조판."""
    from exam.demo2 import demo_passages_2
    from exam.set2 import TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
    ps = demo_passages_2()
    validator.validate_passages(ps, TYPE_ORDER2)
    nums = validator.validate_numbering(ps, 1, TYPE_ORDER2)
    assert nums == [[1, 2, 3, 4, 5, 6, 7]]
    html = renderer.render_html(ps, type_order=TYPE_ORDER2,
                                prompts=TYPE_PROMPTS2, labels=TYPE_LABELS2)
    assert "vanishingly small space" in html          # 정본 공유
    assert "다음 글의 내용과 일치하는 것의 개수는?" in html   # G 발문
    assert "함의추론" in html                            # B 라벨(해설)
    print("✓ 2회(A~G) 데모 검증·조판 통과")


def test_pdf_cleaning() -> None:
    """PDF 정제: 한글·머리글 제거, 영어 지문만 남기기."""
    from exam import ingest
    seg = (
        "[EBS] 올림포스 영어독해 기본1 ­ 한줄해석 (좌지문 우해석)\n"
        "Ch. 04 Unit 10 - 2번: 제목 한글입니다\n"
        "① Although the wish to be alone is often strong, its intensity varies. 혼자 있고\n"
        "② We need other people to confirm that we exist. 우리는 필요로 한다.\n"
        "[Flow Edu] flowedu.tistory.com\n"
    )
    out = ingest._clean_pdf_text(seg)
    assert "Although the wish to be alone" in out
    assert "We need other people" in out
    assert "올림포스" not in out and "Ch." not in out and "flowedu" not in out
    assert not any("가" <= c <= "힣" for c in out)      # 한글 없음
    print("✓ PDF 정제(한글·머리글 제거) 통과")


def test_analyzer_uses_real_passage() -> None:
    """분석기가 엉뚱한 지문을 내놓아도 '넣은 지문'만 쓰는지."""
    from exam import analyzer
    from exam.schemas import Analysis, KeyTerm as _KT

    class _Halluc:
        def structured(self, system, prompt, model_cls, **kw):
            return Analysis(title="X",
                            sentences=["Fake one.", "Fake two.", "Fake three.", "Fake four."],
                            main_idea="x", key_terms=[_KT(word="a", synonym="b")],
                            hardest_sentence="z")

    body = ("The printing press changed how knowledge spread across Europe. "
            "It made books cheaper and far more widely available. "
            "As literacy rose, new ideas travelled faster than before. "
            "This reshaped science and politics for centuries.")
    a = analyzer.analyze(_Halluc(), body)
    joined = " ".join(a.sentences)
    assert "printing press" in joined and "Fake" not in joined
    print("✓ 분석기: 넣은 지문만 사용(환각 무시) 통과")


class _FakeClient:
    def structured(self, system, prompt, model_cls, max_tokens=8000,
                   max_retries=1, extra_validate=None, image_path=None):
        obj = _FAKE[model_cls.__name__]()
        if extra_validate:
            extra_validate(obj)
        return obj


def _fake_analysis() -> Analysis:
    return Analysis(
        title="Test",
        sentences=[
            "The first sentence introduces the topic clearly.",
            "The second sentence adds an important detail.",
            "The third sentence gives a concrete example.",
            "The fourth sentence draws the whole thing together.",
        ],
        main_idea="A test main idea.",
        key_terms=[KeyTerm(word="topic", synonym="subject", antonym="")],
        hardest_sentence="The fourth sentence draws the whole thing together.",
    )


_FAKE = {
    "Analysis": _fake_analysis,
    "OrderOut": lambda: OrderOut(given_n=1, block_sizes=[1, 1, 1], display=[2, 1, 3],
                                 reason="이유."),
    "InsertOut": lambda: InsertOut(remove_no=2, reason="이유."),
    "TopicOut": lambda: TopicOut(
        choices=["c1", "c2", "c3", "c4", "c5"], answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="무관"), WrongReason(no=3, text="모순"),
                       WrongReason(no=4, text="무관"), WrongReason(no=5, text="모순")]),
    "ContentOut": lambda: ContentOut(
        choices=["선지1", "선지2", "선지3", "선지4", "선지5"], answer_no=2, reason="일치 근거.",
        wrong_reasons=[WrongReason(no=1, text="~부분이 틀림"), WrongReason(no=3, text="~부분이 틀림"),
                       WrongReason(no=4, text="~부분이 틀림"), WrongReason(no=5, text="~부분이 틀림")]),
    "VocabOut": lambda: VocabOut(
        marks=[WordMark(sent_no=1, word="first", shown="initial"),
               WordMark(sent_no=2, word="important", shown="crucial"),
               WordMark(sent_no=3, word="concrete", shown="abstract"),
               WordMark(sent_no=4, word="together", shown="jointly"),
               WordMark(sent_no=1, word="clearly", shown="plainly")],
        answer_no=3, reason="이유."),
    "GrammarOut": lambda: GrammarOut(
        marks=[WordMark(sent_no=1, word="introduces", shown="introduce"),
               WordMark(sent_no=2, word="adds", shown="adds"),
               WordMark(sent_no=3, word="gives", shown="give")],
        answer_nos=[1, 3],
        reasons=[GrammarReason(no=1, text="수 일치"), GrammarReason(no=3, text="수 일치")]),
    "ShortOut": lambda: ShortOut(
        q1_prompt="p1", q1_answer="한글답",
        q2_prompt="p2",
        q2_tokens=["the", "first", "sentence", "introduce", "the", "topic", "clearly"],
        q2_cues=["introduce"],
        q2_answer="The first sentence introduces the topic clearly.",  # 지문 문장과 동일
        q3_prompt="p3", q3_before="Info ", q3_mid=" is ", q3_after=" now.",
        q3_cue_a="accumulate", q3_cue_b="govern", q3_ans_a="accumulated", q3_ans_b="governs",
        q3_reason="근거."),
    # --- 2회(A~G) 가짜 출력 -------------------------------------------------
    "AOut": lambda: AOut(
        marks=[WordMark(sent_no=1, word="first", shown="first"),
               WordMark(sent_no=2, word="important", shown="important"),
               WordMark(sent_no=3, word="concrete", shown="abstract"),   # 반의어(오답)
               WordMark(sent_no=4, word="draws", shown="draw"),          # 어법(오답)
               WordMark(sent_no=1, word="clearly", shown="clearly")],
        answer_no=3, reason="이유.",
        choices=["ⓐ, ⓑ", "ⓐ, ⓒ", "ⓒ, ⓓ", "ⓑ, ⓔ", "ⓓ, ⓔ"]),
    "BOut": lambda: BOut(
        phrase="concrete example", choices=["b1", "b2", "b3", "b4", "b5"],
        answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="축자적 오독"), WrongReason(no=3, text="논지 위배"),
                       WrongReason(no=4, text="무관"), WrongReason(no=5, text="모순")]),
    "DOut": lambda: DOut(
        tokens=["the", "third", "sentence", "give", "a", "concrete", "example"],
        cues=["give"],
        answer="The third sentence gives a concrete example.",  # 지문 문장 그대로
        reason="원래 배열."),
    "EOut": lambda: EOut(
        before="The passage presents its ", mid=" through a ", after=" for readers.",
        pairs=[Pair(a="topic", b="example", a_ok=True, b_ok=True),      # 정답(둘 다 맞음)
               Pair(a="topic", b="wrongword", a_ok=True, b_ok=False),
               Pair(a="wrongword", b="example", a_ok=False, b_ok=True),
               Pair(a="wrongword", b="badword", a_ok=False, b_ok=False),
               Pair(a="badword", b="wrongword", a_ok=False, b_ok=False)],
        answer_no=1, reason="이유."),
    "FOut": lambda: FOut(
        blank_phrase="concrete example", choices=["f1", "f2", "f3", "f4", "f5"],
        answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="모순"), WrongReason(no=3, text="무관"),
                       WrongReason(no=4, text="모순"), WrongReason(no=5, text="무관")]),
    "GOut": lambda: GOut(
        statements=["진술1", "진술2", "진술3", "진술4", "진술5"],
        matches=[True, False, True, False, True], reason="이유.",
        per_stmt=["일치", "불일치", "일치", "불일치", "일치"]),
}


def test_llm_path_wiring() -> None:
    passage = pipeline.build_passage(_FakeClient(), "dummy body")
    assert passage.types == set(TYPE_ORDER)
    validator.check_passage(passage)
    # 부정어·원문단어 방식도 배선되는지
    for m in ("negation", "original"):
        p = pipeline.build_passage(_FakeClient(), "dummy body", vocab_method=m)
        validator.check_passage(p)
    # 어휘 방식은 난이도에 연동: 상=부정어 · 중=유의어 · 하=원문단어
    from exam import difficulty
    assert difficulty.vocab_method("상") == "negation"
    assert difficulty.vocab_method("중") == "synonym"
    assert difficulty.vocab_method("하") == "original"
    for lv in ("상", "중", "하"):
        p = pipeline.build_passage(_FakeClient(), "dummy body", level=lv)
        validator.check_passage(p)
    html = renderer.render_html([passage])
    assert "정답 및 해설" in html
    print("✓ LLM 경로(생성기→build→검증→조판) 배선 통과")


def test_pdf_merge(tmp_out: Path = ROOT / "output" / "test") -> None:
    """여러 파트(세트·난이도 조합)를 한 PDF로 합본하는지."""
    from exam.demo2 import demo_passages_2
    from exam.set2 import TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
    tmp_out.mkdir(parents=True, exist_ok=True)
    parts = [
        {"passages": demo_passages(), "header_note": "변형문제 1회 · 난이도 중",
         "sections": ["student", "answers"]},
        {"passages": demo_passages_2(), "header_note": "변형문제 2회 · 난이도 상",
         "sections": ["student", "answers"], "type_order": TYPE_ORDER2,
         "prompts": TYPE_PROMPTS2, "labels": TYPE_LABELS2},
    ]
    out = tmp_out / "merge.pdf"
    renderer.render_pdf_multi(parts, out)
    assert out.exists() and out.stat().st_size > 2000
    print("✓ 여러 파트 PDF 합본 통과")


def test_parallel_and_shared_analysis(tmp_out: Path = ROOT / "output" / "test") -> None:
    """유형 병렬 생성 + 지문 병렬 분석 + 1회·2회 분석 공유가 정상 배선되는지."""
    from exam import gen2, pipeline
    tmp_out.mkdir(parents=True, exist_ok=True)

    client = _FakeClient()
    bodies = ["dummy body one", "dummy body two"]

    # 1) 지문 여러 개 병렬 분석
    analyses = pipeline.analyze_bodies(client, bodies)
    assert len(analyses) == len(bodies)

    # 2) 1회: 미리 만든 분석을 공유하며 병렬 유형 생성 → 번호 연속(1..14)
    out1 = tmp_out / "p1.pdf"
    pipeline.build_exam(client, bodies, out1, analyses=analyses)
    assert out1.exists()

    # 3) 2회: 같은 분석 공유 → A~G 병렬 생성
    out2 = tmp_out / "p2.pdf"
    gen2.build_exam2(client, bodies, out2, analyses=analyses)
    assert out2.exists()

    # 4) 병렬 build_passage 결과가 순서대로 온전히 채워졌는지(7종)
    p = pipeline.build_passage(client, "dummy", analysis=analyses[0])
    assert p.types == set(TYPE_ORDER)
    p2 = gen2.build_passage2(client, "dummy", analysis=analyses[0])
    assert p2.types == set(TYPE_ORDER2)
    print("✓ 병렬 생성·병렬 분석·1회2회 분석 공유 통과")


def test_difficulty_lever() -> None:
    """상/중/하 레버가 분석에 지침을 심고, 모든 생성기 context 에 실려 가는지."""
    from exam import difficulty, gen2, pipeline
    from exam.generators.base import context

    assert difficulty.normalize(None) == "중"
    assert difficulty.normalize("이상한값") == "중"
    assert difficulty.content_difficulty("하") == "plain"
    assert difficulty.content_difficulty("상") == "hard"

    client = _FakeClient()
    # level 을 주면 build_passage 가 분석에 지침을 심고 → context 에 노출된다
    a = _fake_analysis()
    a.difficulty_note = difficulty.clause("상")
    assert "[난이도: 상]" in context(a)

    # 1회·2회 모두 level 경로가 정상 배선되는지
    p1 = pipeline.build_passage(client, "dummy", level="하")
    assert p1.types == set(TYPE_ORDER)
    p2 = gen2.build_passage2(client, "dummy", level="상")
    assert p2.types == set(TYPE_ORDER2)
    print("✓ 상/중/하 난이도 레버(지침 주입·1회2회 배선) 통과")


if __name__ == "__main__":
    test_demo_validation_and_numbering()
    test_render_html_bold_rules()
    test_single_source_shared()
    test_build_and_validators()
    test_error_guards()
    test_set2_demo()
    test_pdf_cleaning()
    test_analyzer_uses_real_passage()
    test_llm_path_wiring()
    test_pdf_merge()
    test_parallel_and_shared_analysis()
    test_difficulty_lever()
    print("\n모든 오프라인 테스트 통과 ✅")
