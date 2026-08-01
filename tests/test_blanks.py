"""빈칸형 워크북 오프라인 테스트.

실행: python -m tests.test_blanks
"""
from __future__ import annotations

from src import blanks_schemas as bs
from src.blanks_render import render_bsentence, render_summary, render_blanks_html


def _set():
    from samples.blanks_mock import mock_blank_set
    return mock_blank_set()


# ---- 1. 자리표시자/blanks 개수 불일치 관용 처리 ---------------------------
def test_placeholder_mismatch_tolerated():
    st = _set()
    bs.validate_llm_blank_workbook(bs.LLMBlankWorkbook(sets=[st]))  # 정상
    # 요약문 자리표시자 하나 제거해도(개수 불일치) 실패시키지 않고 build 가 처리
    bad = _set()
    bad.summary_template = bad.summary_template.replace("{{S5}}", "isolation")
    bs.validate_llm_blank_workbook(bs.LLMBlankWorkbook(sets=[bad]))  # 예외 없어야 함
    wb = bs.build_blank_workbook(bs.LLMBlankWorkbook(sets=[bad]), title="T", subtitle="S")
    html = render_summary(wb.sets[0])
    assert "{{" not in str(html)          # 남은 자리표시자 노출 없음
    # 빈칸이 하나도 없으면 재요청되도록 실패
    empty = _set()
    empty.sentences = []
    empty.summary_template = "no blanks"
    empty.summary_blanks = []
    try:
        bs.validate_llm_blank_workbook(bs.LLMBlankWorkbook(sets=[empty]))
        raised = False
    except ValueError:
        raised = True
    assert raised
    print("PASS  자리표시자/blanks 개수 불일치 관용(+빈칸 전무 시 실패)")


# ---- 2. 전역 연속 채번(지문→요약) + 단어뱅크 --------------------------------
def test_numbering_and_wordbank():
    wb = bs.build_blank_workbook(bs.LLMBlankWorkbook(sets=[_set()]), title="T", subtitle="S")
    st = wb.sets[0]
    nums = [b.num for b in st.passage_blanks] + [b.num for b in st.summary_blanks]
    assert nums == list(range(1, len(nums) + 1)), nums          # 연속
    assert wb.total == len(nums)
    # 지문 빈칸이 요약문 빈칸보다 먼저 번호
    assert max(b.num for b in st.passage_blanks) < min(b.num for b in st.summary_blanks)
    # 단어뱅크 = 요약문 정답만, 개수 일치
    assert sorted(st.wordbank) == sorted(b.answer for b in st.summary_blanks)
    print("PASS  전역 연속 채번 + 단어뱅크(정답만)")


# ---- 3. 빈칸 렌더: 첫 글자 유무 --------------------------------------------
def test_blank_render():
    wb = bs.build_blank_workbook(bs.LLMBlankWorkbook(sets=[_set()]), title="T", subtitle="S")
    st = wb.sets[0]
    # 지문 빈칸: 첫 글자 노출(varies → v), 자리표시자 누출 없음
    s1 = str(render_bsentence(st.sentences[0]))
    assert "{{B1}}" not in s1 and 'class="blk pb"' in s1 and ">v<" in s1
    # 요약문 빈칸: 첫 글자 없음(번호만)
    sm = str(render_summary(st))
    assert "{{S1}}" not in sm and 'class="blk sb"' in sm
    print("PASS  빈칸 렌더(지문=첫글자 / 요약=번호만)")


# ---- 4. HTML 렌더 ---------------------------------------------------------
def test_html():
    wb = bs.build_blank_workbook(bs.LLMBlankWorkbook(sets=[_set()]), title="T", subtitle="S")
    html = render_blanks_html(wb, footer_note="테스트")
    assert "지문 빈칸" in html and "요약문 빈칸" in html and "Word Bank" in html
    assert "정답" in html and "{{B1}}" not in html and "{{S1}}" not in html
    assert "요약문 해석" in html                 # 해설에 요약문 한국어 해석 포함
    print("PASS  HTML 렌더(구획·단어뱅크·정답·요약문 해석)")


def test_show_ko_flag():
    wb = bs.build_blank_workbook(bs.LLMBlankWorkbook(sets=[_set()]), title="T", subtitle="S")
    inc = render_blanks_html(wb, show_ko=True)
    exc = render_blanks_html(wb, show_ko=False)
    assert 'class="c-ko"' in inc            # 지문 빈칸 문장별 한글
    assert 'class="c-ko"' not in exc        # 한글 제외 버전은 숨김
    assert "정답" in exc and "Word Bank" in exc   # 정답·워드뱅크는 유지
    print("PASS  한글 포함/제외(show_ko) 지문 빈칸 한글 숨김")


def run_all():
    test_placeholder_mismatch_tolerated()
    test_numbering_and_wordbank()
    test_blank_render()
    test_html()
    test_show_ko_flag()
    print("\n빈칸형 워크북 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
