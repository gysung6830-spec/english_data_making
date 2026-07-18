"""통합 워크북 오프라인 테스트 (API 없이).

실행: python -m tests.test_workbook   (또는 pytest)
검증 항목:
  - 자리표시자 {{Qn}} ↔ questions 1:1 대응 검증
  - 전역 연속 채번 + total 집계
  - order 유형 표기(〈 … 〉) 검증
  - render_sentence 치환(자리표시자 누출 없음)
  - HTML 렌더(정답 페이지 분리 등)
"""
from __future__ import annotations

from src import workbook_schemas as ws
from src.workbook_render import (render_sentence, render_workbook_html,
                                 render_workbooks_html)


def _q(qid, typ="verb", display="(be)", answer="is", reason="r"):
    return ws.LLMQuestion(id=qid, type=typ, display=display, answer=answer, reason=reason)


# ---- 1. 1:1 대응 검증 ------------------------------------------------------
def test_placeholder_one_to_one():
    # 정상: 자리표시자와 questions 가 정확히 대응
    ok = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="A {{Q1}} B {{Q2}} C", ko="가나다",
                       questions=[_q("Q1"), _q("Q2")]),
    ])
    ws.validate_llm_workbook(ok)  # 예외 없어야 함

    # 비정상: questions 에 있는 Q2 가 템플릿에 없음
    bad = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="A {{Q1}} B", ko="가",
                       questions=[_q("Q1"), _q("Q2")]),
    ])
    try:
        ws.validate_llm_workbook(bad)
        assert False, "1:1 위반인데 통과하면 안 됨"
    except ValueError:
        pass
    print("PASS  자리표시자 ↔ questions 1:1 대응 검증")


# ---- 2. id 전역 유일성 -----------------------------------------------------
def test_unique_ids():
    dup = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="{{Q1}}", ko="가", questions=[_q("Q1")]),
        ws.LLMSentence(no=2, en_template="{{Q1}}", ko="나", questions=[_q("Q1")]),
    ])
    try:
        ws.validate_llm_workbook(dup)
        assert False, "id 중복인데 통과하면 안 됨"
    except ValueError:
        pass
    print("PASS  문항 id 전역 유일성 검증")


# ---- 3. order 표기 검증 ----------------------------------------------------
def test_order_display_format():
    bad = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="{{Q1}}", ko="가",
                       questions=[_q("Q1", typ="order", display="a / b / c", answer="a b c")]),
    ])
    try:
        ws.validate_llm_workbook(bad)
        assert False, "〈 〉 없는 order 표기는 실패해야 함"
    except ValueError:
        pass
    print("PASS  특수구문(order) 표기 〈 … 〉 검증")


# ---- 4. 전역 연속 채번 + total --------------------------------------------
def test_global_numbering():
    llm = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="{{Q1}} x {{Q2}}", ko="가",
                       questions=[_q("Q1"), _q("Q2")]),
        ws.LLMSentence(no=2, en_template="{{Q3}}", ko="나", questions=[_q("Q3")]),
    ])
    wb = ws.build_workbook(llm, title="T", subtitle="S")
    nums = [q.num for q in wb.all_questions]
    assert nums == [1, 2, 3], nums
    assert wb.total == 3
    print("PASS  전역 연속 채번 + total 집계")


# ---- 5. render_sentence 치환 (자리표시자 누출 없음) ------------------------
def test_render_sentence_substitution():
    llm = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="Giving {{Q1}} chance to {{Q2}} now", ko="가",
                       questions=[_q("Q1", typ="adj", display="[ a / b / c ]", answer="a"),
                                  _q("Q2", typ="verb", display="(react)", answer="react")]),
    ])
    wb = ws.build_workbook(llm, title="T", subtitle="S")
    out = str(render_sentence(wb.sentences[0]))
    assert "{{Q1}}" not in out and "{{Q2}}" not in out, "자리표시자 누출"
    assert "[ a / b / c ]" in out and "(react)" in out
    assert 'class="lbl a"' in out and 'class="lbl v"' in out
    assert "1)" in out and "2)" in out  # 위첨자 번호
    print("PASS  render_sentence 치환(누출 없음, 라벨/번호 삽입)")


# ---- 6. HTML 렌더 ----------------------------------------------------------
def test_render_html():
    from samples.workbook_mock import mock_workbook
    wb = mock_workbook()
    html = render_workbook_html(wb, footer_note="테스트")
    assert "SCORE" in html and f"/ {wb.total}" in html
    assert "정답 · 해설" in html               # 정답 페이지 존재
    assert "ans-page" in html                    # page-break-before 대상
    assert "{{Q1}}" not in html                  # 자리표시자 누출 없음
    assert "동사·준동사" in html and "특수구문" in html  # 범례
    print("PASS  HTML 렌더(SCORE·정답 페이지·범례)")


# ---- 7. 복수 지문 배치 (지문1→답1→지문2→답2) ----------------------------
def test_multi_passage_layout():
    from samples.workbook_mock import mock_workbook
    b1 = mock_workbook(title="Passage One", subtitle="첫째 지문")
    b2 = mock_workbook(title="Passage Two", subtitle="둘째 지문")
    html = render_workbooks_html([b1, b2], footer_note="테스트")
    # 두 지문 모두 제목·지문 번호 배지가 있어야 함
    assert "Passage One" in html and "Passage Two" in html
    assert "지문 1" in html and "지문 2" in html
    # 정답 페이지가 지문마다 하나씩(총 2개) 존재 (CSS 정의와 구분하려 class 속성으로 카운트)
    assert html.count('class="ans-page"') == 2
    # 둘째 지문 문제 페이지는 새 페이지에서 시작(unit-break)
    assert 'unit-break' in html
    # 단일 지문은 지문 번호 배지가 없어야 함
    solo = render_workbooks_html([b1])
    assert "지문 1" not in solo and 'class="ans-page"' in solo
    print("PASS  복수 지문 배치(지문1→답1→지문2→답2)")


def run_all():
    test_placeholder_one_to_one()
    test_unique_ids()
    test_order_display_format()
    test_global_numbering()
    test_render_sentence_substitution()
    test_render_html()
    test_multi_passage_layout()
    print("\n통합 워크북 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
