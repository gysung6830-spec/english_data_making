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
    assert ids == {"emphasis", "inversion", "parallel", "apposition",
                   "what_clause", "insertion", "participle", "that_clause", "wh_clause",
                   "prep_stack", "as_compare"}
    print("PASS  구문 목차(강조·도치·동격·병렬·what·that·wh·삽입·분사·전치사구·as비교)")


def test_render_html():
    from samples.guide_mock import mock_guide
    html = render.render_html(mock_guide(), sample=True)
    assert "필자가 의도하는 바를 파악하기" in html   # 1부 개칭
    assert "오역" in html and "정답" in html
    assert "이런 내용" in html                    # 진짜 의미 층
    assert "긍정·강조 신호" in html and "부정·부재·거부 신호" in html
    assert "모르는 단어" in html                   # 0부 단어 유추법
    assert "패턴으로 익히는 실전해석" in html         # 3부 개칭
    assert "단계별 트레이닝" in html                # 전치사구 트레이닝
    assert "관계로 읽기" in html                    # 0부 STEP2 관계 원리
    assert "어휘 유추" in html and "유추의 다섯 단서" in html   # 어휘 유추(부록으로 이동)
    assert "명사화" in html and "비유" in html      # 3부 슬림화: 명사화·비유만 유지
    assert "재진술·예시·대비" in html               # 3부 intro — 논리신호는 2부로 이관 명시
    assert 'class="sv-line"' not in html          # '관계'(주체→행위) 줄 삭제됨
    assert "sw-basis" not in html                 # '이런 내용' 근거 라인 삭제
    assert "실전적용 해설" in html                 # 목차별 문제→해설
    assert html.count('class="chapter drill-q"') >= 5    # 문제 묶음(목차별 1섹션)
    assert html.count('class="chapter drill-a"') >= 5    # 해설 묶음(목차별 1섹션)
    assert html.count('class="dq-item"') >= 180           # 문법 검수(오분류 제거) 반영 후 하한
    assert "20번" not in html and "29번" not in html      # 제외 문항(20·25~29번) 출처 없음
    print("PASS  실전서 HTML 렌더링(진짜 의미·극성·유추 포함)")


def test_corpus_store():
    """영구 기출 저장소(data/corpus.jsonl) 조회 계층 스모크 테스트."""
    from src.guide.corpus_store import EXCLUDE_ITEM_NOS, load_corpus, pick, query
    recs = load_corpus()
    if not recs:
        print("SKIP  corpus.jsonl 없음(ingest 전) — 저장소 테스트 생략")
        return
    # 필수 필드
    r = recs[0]
    for k in ("id", "text", "source", "codes", "type", "difficulty", "self_contained"):
        assert k in r, f"레코드에 {k} 없음"
    # 제외 문항은 기본 질의에서 빠져야 함
    picked = query(recs, code="contrast")
    assert all(x.get("item") not in EXCLUDE_ITEM_NOS for x in picked), "제외문항 누출"
    assert all(x["self_contained"] for x in picked), "자기완결 필터 미적용"
    # pick 은 결정적(재현 가능)
    a = [x["id"] for x in pick(3, type="apposition")]
    b = [x["id"] for x in pick(3, type="apposition")]
    assert a == b, "pick 비결정적"
    print(f"PASS  영구 코퍼스 저장소({len(recs)}문장) 조회·필터·재현성")


def run_all():
    test_load_codes()
    test_split_sentences()
    test_match_with_adverb()
    test_polarity_codes()
    test_syntax_types()
    test_corpus_store()
    test_render_html()
    print("\n실전서 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
