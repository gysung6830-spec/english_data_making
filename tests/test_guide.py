"""구문해석 실전서(가이드) 모듈 오프라인 테스트.

실행: python -m tests.test_guide
검증 항목:
  - codes.yaml 로드 및 카테고리 구성
  - 문장 분리
  - 코드 매칭(부사 삽입 포함) + 유형별 그룹핑
  - HTML 렌더링(목 데이터)
"""
from __future__ import annotations

from src.guide import render
from src.guide.codes import load_categories
from src.guide.corpus import match_category, split_sentences


def test_load_codes():
    cats = load_categories()
    ids = {c.id for c in cats}
    assert {"causation", "contrast", "equivalence", "comparison", "connective"} <= ids
    # 각 카테고리에 코드가 있어야 함
    for c in cats:
        assert c.codes, f"{c.id} 코드 없음"
    print("PASS  codes.yaml 로드")


def test_split_sentences():
    text = "A leads to B. In other words, C differs from D! Does it work? Yes."
    sents = split_sentences(text)
    assert len(sents) >= 3
    print("PASS  문장 분리")


def test_match_with_adverb():
    # be동사 뒤 부사 삽입(is largely attributable to)도 매칭돼야 함
    sents = [
        "The decline is largely attributable to habitat loss.",
        "A small change can give rise to big effects.",
        "Experts see structure, whereas novices see surface.",
    ]
    cats = {c.id: c for c in load_categories()}
    caus = match_category(cats["causation"], sents, per_code=2)
    hits = {m.code.en for m in caus}
    assert "be attributable to" in hits, "부사 삽입 매칭 실패"
    assert "give rise to" in hits
    contrast = match_category(cats["contrast"], sents, per_code=2)
    assert any(m.code.en == "whereas" for m in contrast)
    print("PASS  코드 매칭(부사 삽입 포함) + 그룹핑")


def test_polarity_codes():
    cats = {c.id: c for c in load_categories()}
    assert "polarity_positive" in cats and "polarity_negative" in cats
    pos = {c.en for c in cats["polarity_positive"].codes}
    neg = {c.en for c in cats["polarity_negative"].codes}
    assert "central" in pos and "essential" in pos
    assert "rarely" in neg and "lack" in neg
    print("PASS  긍정/부정 신호 카테고리")


def test_syntax_types():
    from src.guide.syntax import SYNTAX_TYPES
    ids = {st.id for st in SYNTAX_TYPES}
    assert ids == {"emphasis", "inversion", "parallel", "comparison", "apposition",
                   "what_clause", "insertion_participle", "that_clause", "wh_clause",
                   "negation", "prep_stack"}
    print("PASS  구문 목차(부정·비교·강조·도치·동격·병렬·what·that·wh·삽입분사·전치사구)")


def test_render_html():
    from samples.guide_mock import mock_guide
    html = render.render_html(mock_guide(), sample=True)
    assert "답으로 이어지는 평가원 코드" in html
    assert "오역" in html and "정답" in html
    assert "이런 내용" in html                    # 진짜 의미 층
    assert "긍정·강조 신호" in html and "부정·부재·거부 신호" in html
    assert "모르는 단어" in html                   # 0부 단어 유추법
    print("PASS  실전서 HTML 렌더링(진짜 의미·극성·유추 포함)")


def run_all():
    test_load_codes()
    test_split_sentences()
    test_match_with_adverb()
    test_polarity_codes()
    test_syntax_types()
    test_render_html()
    print("\n실전서 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
