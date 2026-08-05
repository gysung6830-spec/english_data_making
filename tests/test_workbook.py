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


# ---- 1. 자리표시자/questions 개수 불일치 관용 처리 -------------------------
def test_placeholder_mismatch_tolerated():
    from src.workbook_render import render_sentence
    # 정상: 자리표시자와 questions 가 정확히 대응
    ok = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="A {{Q1}} B {{Q2}} C", ko="가나다",
                       questions=[_q("Q1"), _q("Q2")]),
    ])
    ws.validate_llm_workbook(ok)  # 예외 없어야 함

    # 불일치(LLM 이 {{Q}} 를 빠뜨림): questions 는 1개인데 자리표시자 0개 → 실패시키지 않음
    miss = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="A {{Q1}} B", ko="가",
                       questions=[_q("Q1")]),
        ws.LLMSentence(no=2, en_template="No placeholder here.", ko="나",
                       questions=[_q("Q2")]),   # 자리표시자 없음(0) vs questions(1)
    ])
    ws.validate_llm_workbook(miss)               # 예외 없어야 함(관용)
    wb = ws.build_workbook(miss, title="T", subtitle="S")
    # 문장2 는 자리표시자가 없어 그 문항은 조용히 생략되고, 문장은 온전히 남는다
    assert wb.sentences[1].en_template == "No placeholder here."
    assert wb.total == 1                          # 짝지어진 문항만 채번

    # 남는 자리표시자({{Q9}})는 렌더에서 노출되지 않는다
    leak = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="A {{Q1}} B {{Q9}} C", ko="가",
                       questions=[_q("Q1")])])
    wb2 = ws.build_workbook(leak, title="T", subtitle="S")
    out = str(render_sentence(wb2.sentences[0]))
    assert "{{Q9}}" not in out and "{{" not in out
    print("PASS  자리표시자/questions 개수 불일치 관용 처리(+누출 없음)")


# ---- 2. id 불일치 자동 정렬(등장 순서) --------------------------------------
def test_id_mismatch_repair():
    # 자리표시자 id와 questions id가 어긋나도 '개수'만 맞으면 등장 순서로 정렬되어야 함
    # (LLM 이 전역 연속번호를 혼동해 문장2 템플릿=Q1, questions=Q3 처럼 어긋나는 경우)
    llm = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="X {{Q1}} Y {{Q2}}", ko="가",
                       questions=[_q("Q1", display="(a)", answer="a"),
                                  _q("Q2", display="(b)", answer="b")]),
        ws.LLMSentence(no=2, en_template="P {{Q1}} Q", ko="나",
                       questions=[_q("Q3", display="(c)", answer="c")]),
    ])
    ws.validate_llm_workbook(llm)                    # 개수만 맞으면 통과(실패 안 함)
    wb = ws.build_workbook(llm, title="T", subtitle="S")
    out = str(render_sentence(wb.sentences[1]))      # 문장2: {{Q1}} → (c) 로 치환돼야
    assert "{{Q1}}" not in out and "(c)" in out
    assert [q.num for q in wb.all_questions] == [1, 2, 3]
    print("PASS  id 불일치 자동 정렬(등장 순서)")


# ---- 2-b. 빈 questions 문장은 거부하지 않고 '읽기용'으로 그대로 싣는다 --------
def test_empty_questions_kept():
    # LLM 이 출제 요소 없는 문장(빈 questions)을 섞어 보내도 전체를 거부하지 않고,
    # 문장 자체는 지문 보존을 위해 그대로 싣는다(문항만 없음).
    llm = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="No blanks here.", ko="가", questions=[]),
        ws.LLMSentence(no=2, en_template="X {{Q1}} Y", ko="나",
                       questions=[_q("Q1", display="(a)", answer="a")]),
        ws.LLMSentence(no=3, en_template="Also nothing.", ko="다", questions=[]),
    ])
    ws.validate_llm_workbook(llm)                    # 빈 문장 있어도 통과
    wb = ws.build_workbook(llm, title="T", subtitle="S")
    # 세 문장 모두 남고(지문 보존), 문항 총계는 1
    assert len(wb.sentences) == 3 and wb.total == 1
    assert wb.sentences[0].en_template == "No blanks here." and not wb.sentences[0].questions
    # 자리표시자만 있고 questions 가 없는 (렌더 불가) 문장은 건너뛴다
    bad = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="Broken {{Q1}}.", ko="가", questions=[]),
        ws.LLMSentence(no=2, en_template="Y {{Q1}}", ko="나",
                       questions=[_q("Q1", display="(a)", answer="a")])])
    wb2 = ws.build_workbook(bad, title="T", subtitle="S")
    assert len(wb2.sentences) == 1
    # 모든 문장이 비면 재요청되도록 실패해야 함
    empty = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="Nothing.", ko="가", questions=[])])
    try:
        ws.validate_llm_workbook(empty)
        raised = False
    except ValueError:
        raised = True
    assert raised
    print("PASS  빈 questions 문장 보존(+렌더불가 건너뛰기 +전부 비면 실패)")


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
    wb.label = "[고1] 9월 30번"
    html = render_workbook_html(wb, footer_note="테스트")
    assert "sh-head" in html and wb.label in html   # 제목 + 출처 뱃지 헤더
    # NAME/SCORE 블록 삭제 (base64 폰트에 우연히 단어가 들어갈 수 있어 마크업 클래스로 확인)
    assert 'class="wb-meta"' not in html and 'class="wb-score"' not in html
    assert "정답 · 해설" in html               # 정답 페이지 존재
    assert "ans-page" in html                    # page-break-before 대상
    assert "{{Q1}}" not in html                  # 자리표시자 누출 없음
    assert "동사·준동사" in html and "특수구문" in html  # 범례
    assert "※ 문제" in html and "(4)" in html    # 지시문(번호 형식 + 지칭 안내)
    assert "지칭" in html                        # 대명사 지칭(ref) 유형 라벨
    print("PASS  HTML 렌더(제목+뱃지·정답 페이지·범례·지시문·지칭)")


# ---- 7. 복수 지문 배치 (지문1→답1→지문2→답2) ----------------------------
def test_multi_passage_layout():
    from samples.workbook_mock import mock_workbook
    b1 = mock_workbook(title="Passage One"); b1.label = "[고1] 9월 30번"
    b2 = mock_workbook(title="Passage Two"); b2.label = "[고1] 9월 31번"
    html = render_workbooks_html([b1, b2], footer_note="테스트")
    # 두 지문 모두 제목·출처 뱃지가 있어야 함
    assert "Passage One" in html and "Passage Two" in html
    assert "[고1] 9월 30번" in html and "[고1] 9월 31번" in html
    # 정답 페이지가 지문마다 하나씩(총 2개) 존재 (CSS 정의와 구분하려 class 속성으로 카운트)
    assert html.count('class="ans-page"') == 2
    # 둘째 지문 문제 페이지는 새 페이지에서 시작(unit-break)
    assert 'unit-break' in html
    print("PASS  복수 지문 배치(지문1→답1→지문2→답2)")


def test_show_ko_flag():
    from samples.workbook_mock import mock_workbook
    wb = mock_workbook()
    inc = render_workbooks_html([wb], show_ko=True)
    exc = render_workbooks_html([wb], show_ko=False)
    assert 'class="c-ko"' in inc
    # 한글 제외: 문장별 한글(c-ko) 숨김
    assert 'class="c-ko"' not in exc
    # 정답·해설(한글)은 유지
    assert "정답 · 해설" in exc
    print("PASS  한글 포함/제외(show_ko) 문제면 한글 숨김")


def test_section_split():
    # 문제/정답 분리: section='q' 는 정답면 없음, 'a' 는 문제 카드 없음
    from samples.workbook_mock import mock_workbook
    wb = mock_workbook()
    q = render_workbooks_html([wb], section="q")
    a = render_workbooks_html([wb], section="a")
    assert 'class="ans-page"' not in q and 'class="wb-cards"' in q   # 문제만
    assert 'class="ans-page"' in a and 'class="wb-cards"' not in a   # 정답만
    print("PASS  문제/정답 분리(section q/a)")


def test_no_verb_cap():
    # 새 출제원리: '어형변형 2개/문장'을 위해 동사 비율 상한을 두지 않는다.
    #   동사 문항이 40%를 넘어도 되돌리지 않고 그대로 채번되어야 한다.
    def Q(i, t):
        return ws.LLMQuestion(id=f"Q{i}", type=t,
                              display=("(x)" if t == "verb" else "[a/b]"),
                              answer=f"W{i}", reason="r")
    s1 = ws.LLMSentence(no=1, en_template="a {{Q1}} b {{Q2}} c {{Q3}} d {{Q4}} e {{Q5}} f {{Q6}}.",
                        ko="k", questions=[Q(1, "verb"), Q(2, "verb"), Q(3, "verb"),
                                           Q(4, "verb"), Q(5, "verb"), Q(6, "rel")])
    s2 = ws.LLMSentence(no=2, en_template="g {{Q7}} h {{Q8}} i {{Q9}} j {{Q10}}.",
                        ko="k", questions=[Q(7, "verb"), Q(8, "verb"), Q(9, "verb"), Q(10, "conj")])
    wb = ws.build_workbook(ws.LLMWorkbook(sentences=[s1, s2]), title="T", subtitle="S")
    nverb = sum(1 for q in wb.all_questions if q.type == "verb")
    assert wb.total == 10 and nverb == 8            # 모든 문항 보존(동사 되돌림 없음)
    for s in wb.sentences:
        ph = set(ws.placeholders_in(s.en_template))
        assert ph == set(q.id for q in s.questions)   # 자리표시자 ↔ 문항 대응 온전(고아 없음)
    print("PASS  동사 비율 상한 제거(어형변형 2개/문장 우선, 문항 보존)")


def test_misplacement_restore():
    # 원문과 대조: 보기 박스가 엉뚱한 자리에 놓여 원문 단어가 사라지면 문항 버리고 원문 복원
    from src.textutil import split_sentences
    body = ("Project leaders should not be surprised when disagreements emerge within the team. "
            "If they remain hidden, the leader may even want to seek them out for two reasons.")
    orig = split_sentences(body)

    def Q(i, t, a):
        return ws.LLMQuestion(id=f"Q{i}", type=t, display="(x)", answer=a, reason="r")

    # 오배치: seek 자리에 remain(정답) 박스 → 원문의 'seek' 소실
    bad = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=1, en_template="Project leaders should not {{Q1}} surprised when disagreements emerge within the team.",
                       ko="k", questions=[Q(1, "verb", "be")]),
        ws.LLMSentence(no=2, en_template="If they remain hidden, the leader may even want {{Q2}} them out for two reasons.",
                       ko="k", questions=[Q(2, "verb", "remain")]),
    ])
    wb = ws.build_workbook(bad, title="T", subtitle="S", originals=orig)
    assert "to seek them out" in wb.sentences[1].en_template and not wb.sentences[1].questions
    assert len(wb.sentences[0].questions) == 1     # 정상 문장은 유지
    # 정상 배치(seek 자리에 seek)는 유지
    good = ws.LLMWorkbook(sentences=[
        ws.LLMSentence(no=2, en_template="If they remain hidden, the leader may even want {{Q1}} them out for two reasons.",
                       ko="k", questions=[Q(1, "verb", "to seek")])])
    wb2 = ws.build_workbook(good, title="T", subtitle="S", originals=orig)
    assert len(wb2.sentences[0].questions) == 1
    print("PASS  의미 오배치 후처리(원문 대조 복원, 정상 유지)")


def run_all():
    test_placeholder_mismatch_tolerated()
    test_misplacement_restore()
    test_id_mismatch_repair()
    test_empty_questions_kept()
    test_order_display_format()
    test_global_numbering()
    test_render_sentence_substitution()
    test_render_html()
    test_multi_passage_layout()
    test_show_ko_flag()
    test_section_split()
    test_no_verb_cap()
    print("\n통합 워크북 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
