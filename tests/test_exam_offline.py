"""오프라인 테스트: 시험지 생성 파이프라인을 API 없이 검증한다.

- 데모 데이터 검증·번호 연속·조판(HTML) 확인
- 볼드 5곳 규칙이 HTML 에 반영되는지 확인
- LLM 경로(생성기)를 가짜 클라이언트로 대체해 스키마→format→검증→조판 배선 확인
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from exam import format as F  # noqa: E402
from exam import pipeline, renderer, validator  # noqa: E402
from exam.demo_data import demo_passages  # noqa: E402
from exam.schemas import (  # noqa: E402
    Analysis,
    GrammarOut,
    GrammarReason,
    InsertOut,
    KeyTerm,
    OrderOut,
    ShortOut,
    TopicOut,
    VocabOut,
    WrongReason,
)
from exam.types import TYPE_ORDER  # noqa: E402


def test_demo_validation_and_numbering() -> None:
    passages = demo_passages()
    validator.validate_passages(passages)
    numbers = validator.validate_numbering(passages, start=1)
    assert numbers == [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]
    print("✓ 데모 검증·번호 연속 통과:", numbers)


def test_render_html_bold_rules() -> None:
    passages = demo_passages()
    html = renderer.render_html(passages, header_note="○○학원 고3")
    # 5곳 볼드 클래스가 실제로 존재하는지
    for cls in ("brand-title", "qnum", "passage-label", "answer-title",
                "answer-key", "boki-title", "cue"):
        assert cls in html, f"볼드 클래스 누락: {cls}"
    # 배치: 문제 전체 → 해설 전체
    assert html.index('class="questions"') < html.index('class="answers"')
    # 머리글 반영
    assert "○○학원 고3" in html
    print("✓ 조판 HTML·볼드 5곳·배치·머리글 통과")


def test_weave_and_validators() -> None:
    marked = F.weave(["a ", " b ", " c"], [F.pos(1), F.pos(2)])
    assert "①" in marked and "②" in marked
    # 개수 규칙 위반 시 예외
    for bad in (
        lambda: OrderOut(given="g", seg_a="a", seg_b="b", seg_c="c",
                         orders=["1", "2"], answer_no=1, reason="r"),
        lambda: VocabOut(chunks=["1", "2"], words=["a"], answer_no=1, reason="r"),
    ):
        try:
            bad()
        except Exception:
            pass
        else:
            raise AssertionError("개수 검증이 동작하지 않음")
    print("✓ weave·스키마 개수 검증 통과")


class _FakeClient:
    """model_cls 에 따라 미리 만든 구조화 객체를 돌려주는 가짜 클라이언트."""

    def structured(self, system, prompt, model_cls, max_tokens=8000,
                   max_retries=1, extra_validate=None, image_path=None):
        obj = _FAKE[model_cls.__name__]()
        if extra_validate:
            extra_validate(obj)
        return obj


def _fake_analysis() -> Analysis:
    return Analysis(
        title="Test Passage",
        sentences=["Sentence one here.", "Sentence two here.", "Sentence three here.",
                   "Sentence four here."],
        main_idea="A test main idea.",
        key_terms=[KeyTerm(word="data", synonym="information", antonym="noise")],
        hardest_sentence="Sentence four here.",
    )


_FAKE = {
    "Analysis": _fake_analysis,
    "OrderOut": lambda: OrderOut(
        given="Given part.", seg_a="A part.", seg_b="B part.", seg_c="C part.",
        orders=["(A)-(B)-(C)", "(B)-(A)-(C)", "(B)-(C)-(A)", "(C)-(A)-(B)", "(C)-(B)-(A)"],
        answer_no=2, reason="이유."),
    "InsertOut": lambda: InsertOut(
        given_sentence="Given sentence.",
        chunks=["c0 ", " c1 ", " c2 ", " c3 ", " c4 ", " c5"],
        answer_no=3, reason="이유."),
    "TopicOut": lambda: TopicOut(
        passage="Passage text.",
        choices=["c1", "c2", "c3", "c4", "c5"], answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="무관"), WrongReason(no=3, text="모순"),
                       WrongReason(no=4, text="무관"), WrongReason(no=5, text="모순")]),
    "VocabOut": lambda: VocabOut(
        chunks=["c0 ", " c1 ", " c2 ", " c3 ", " c4 ", " c5"],
        words=["w1", "w2", "w3", "w4", "w5"], answer_no=3, reason="이유."),
    "GrammarOut": lambda: GrammarOut(
        chunks=["c0 ", " c1 ", " c2 ", " c3"],
        words=["w1", "w2", "w3"], answer_nos=[1, 3],
        reasons=[GrammarReason(no=1, text="수 일치"), GrammarReason(no=3, text="태")]),
    "ShortOut": lambda: ShortOut(
        passage="Passage.", q1_prompt="p1", q1_answer="한글답",
        q2_prompt="p2", q2_tokens=["she", "decide", "to", "leave"], q2_cues=["decide"],
        q2_answer="She decided to leave.",
        q3_prompt="p3", q3_before="Info ", q3_mid=" is ", q3_after=" now.",
        q3_cue_a="accumulate", q3_cue_b="govern", q3_ans_a="accumulated", q3_ans_b="governs",
        q3_reason="근거."),
}


def test_llm_path_wiring() -> None:
    client = _FakeClient()
    passage = pipeline.build_passage(client, "dummy body text with several sentences.")
    assert passage.types == set(TYPE_ORDER)
    validator.check_passage(passage)
    # 조판까지 되는지
    html = renderer.render_html([passage])
    assert "정답 및 해설" in html
    print("✓ LLM 경로(생성기→format→검증→조판) 배선 통과")


if __name__ == "__main__":
    test_demo_validation_and_numbering()
    test_render_html_bold_rules()
    test_weave_and_validators()
    test_llm_path_wiring()
    print("\n모든 오프라인 테스트 통과 ✅")
