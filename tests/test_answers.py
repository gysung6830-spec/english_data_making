"""단일 유형 정답 모음 렌더 + 출처 라벨 오프라인 테스트.

실행: python -m tests.test_answers
"""
from __future__ import annotations

from src import answers_render as ar
from src.textutil import source_label
from samples.prose_mock import mock_prose_pack
from samples.writing_mock import mock_writing_pack
from samples.blanks_mock import mock_blank_set
from src import blanks_schemas as bs


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def test_source_label():
    _check("고1 9월 30번", source_label("고1_9월_30번.pdf") == "[고1] 9월 30번")
    _check("UUID 접두 제거", source_label("a1b2c3d4-고3 6월 21번.pdf") == "[고3] 6월 21번")
    _check("빈 입력 → fallback", source_label("", "X") == "X")


def test_groups_and_render():
    pk = mock_prose_pack(title="T", header="H"); pk.label = "[고1] 9월 30번"
    wp = mock_writing_pack(title="T", header="H"); wp.label = "[고1] 9월 30번"
    st = mock_blank_set(title="T", no=1); st.label = "[고1] 9월 30번"
    blank_wb = bs.build_blank_workbook(bs.LLMBlankWorkbook(sets=[st]), title="T", subtitle="S")

    # compact 스타일: 어형은 인라인 칩(block=False)
    g_form = ar.group_from_prose(pk, "form", "어형 변형", "f", style="compact")
    g_tr = ar.group_from_prose(pk, "translate", "한글 해석 연습", "t", style="compact")
    g_wr = ar.group_from_writing(wp, style="compact")
    g_bl = ar.groups_from_blanks(blank_wb, style="compact")
    _check("어형 그룹 생성(compact=인라인 칩)", g_form and not g_form.block and g_form.items)
    _check("해석 그룹은 block(줄 단위)", g_tr and g_tr.block)
    _check("영작 그룹 생성", g_wr and g_wr.type_name == "영작 워크북")
    _check("빈칸 그룹은 subgroups(지문/요약)", g_bl and g_bl[0].subgroups)
    # gloss 스타일: 어형도 block(정답+해석 한 줄)
    g_form_gloss = ar.group_from_prose(pk, "form", "어형 변형", "f", style="gloss")
    _check("gloss 어형은 block", g_form_gloss and g_form_gloss.block)

    groups = [g for g in [g_form, g_tr, g_wr] if g] + g_bl
    html = ar.render_answers_html(groups)
    _check("유형명·출처 라벨 노출", "어형 변형" in html and "[고1] 9월 30번" in html)
    _check("빈칸 소제목", "지문 빈칸" in html and "요약문 빈칸" in html)
    _check("연속 배치(페이지 강제분할 클래스 없음)", "page-break-before" not in html
           and 'class="ans-page"' not in html)


if __name__ == "__main__":
    test_source_label()
    test_groups_and_render()
    print("\n정답 모음/출처 라벨 오프라인 테스트 통과 ✅")
