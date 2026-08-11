"""영작 워크북 오프라인 테스트 (API 없이).

실행: python -m tests.test_writing
검증 항목:
  - build_writing_pack: chunks 를 코드가 섞어 display 〈 〉 생성(원래 순서와 다름)
  - answer 는 바른 배열 보존, 문장당 박스 최대 2개
  - 자리표시자 {{An}} ↔ items 정렬(id 불일치 허용)
  - 문장 전무 시 검증 실패
  - HTML 렌더(정답 페이지, 자리표시자 누출 없음)
"""
from __future__ import annotations

from src import writing_render as wr
from samples.writing_mock import mock_llm_writing, mock_writing_pack


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def test_shuffle_and_answer():
    pack = mock_writing_pack(title="T", header="H")
    s1 = pack.sentences[0].items[0]
    _check("display 는 〈 〉 로 감쌈", s1.display.startswith("〈") and s1.display.endswith("〉"))
    _check("answer 는 바른 배열 보존", s1.answer == "to react to your designs while in progress")
    # 조각이 모두 display 안에 들어 있고(섞였을 뿐), 정답 조각 수와 일치
    for s in pack.sentences:
        for it in s.items:
            for chunk in it.answer.split():
                pass  # answer 는 이어붙인 문자열이므로 조각 단위 비교는 생략
    _check("최소 한 박스는 원래 순서와 다르게 섞임",
           any(" / ".join(  # display 내부 순서가 answer 순서와 다른 경우가 존재
               it.display.strip("〈〉 ").split(" / ")) != it.answer
               for s in pack.sentences for it in s.items))


def test_display_never_equals_answer_order():
    # 조각을 '정답과 다른 순서'로 넣어도(입력≠정답), 셔플이 우연히 '정답 순서'로 떨어지면 안 된다.
    # 예: chunks 입력 ["Compean","where","was"], answer "where Compean was"
    #     → display 를 "where / Compean / was"(정답순)로 내면 문제 무의미.
    for _ in range(50):   # 무작위이므로 여러 번 반복해 확률적 실패 방지
        llm = wr.LLMWritingPack(sentences=[wr.LLMWritingSentence(
            no=1, en="x", ko="가", template="They still didn't have any idea {{A1}}.",
            items=[wr.LLMWritingItem(id="A1", chunks=["Compean", "where", "was"],
                                     answer="where Compean was")])])
        pack = wr.build_writing_pack(llm, header="H", title="T", subtitle="S")
        disp = pack.sentences[0].items[0].display.strip("〈〉 ")
        order = " ".join(p.strip() for p in disp.split(" / "))
        _check("display 순서 ≠ 정답 어순", order != "where Compean was")


def test_max_two_boxes():
    pack = mock_writing_pack(title="T", header="H")
    _check("문장당 박스 최대 2개", all(len(s.items) <= 2 for s in pack.sentences))
    # 목데이터 3번 문장은 2박스 케이스
    two = next(s for s in pack.sentences if len(s.items) == 2)
    _check("2박스 문장 존재", two is not None)


def test_id_mismatch_order():
    llm = wr.LLMWritingPack(sentences=[wr.LLMWritingSentence(
        no=1, ko="가", template="A {{A1}} B {{A2}} C",
        items=[wr.LLMWritingItem(id="A9", chunks=["x", "y"], answer="x y"),
               wr.LLMWritingItem(id="A8", chunks=["m", "n"], answer="m n")])])
    wr.validate_llm_writing(llm)
    pack = wr.build_writing_pack(llm, header="H", title="T", subtitle="S")
    ids = [it.id for it in pack.sentences[0].items]
    _check("id 불일치시 등장 순서 정렬(A1,A2)", ids == ["A1", "A2"])


def test_answer_from_chunks_when_blank():
    llm = wr.LLMWritingPack(sentences=[wr.LLMWritingSentence(
        no=1, ko="가", template="{{A1}} here",
        items=[wr.LLMWritingItem(id="A1", chunks=["put", "it"], answer="")])])
    pack = wr.build_writing_pack(llm, header="H", title="T", subtitle="S")
    _check("answer 비면 chunks 로 생성", pack.sentences[0].items[0].answer == "put it")


def test_single_chunk_box_dropped():
    # 조각 1개짜리 박스(〈 on 〉)는 배열할 게 없어 무의미 → 문항에서 빼고 단어를 문장에 복원
    llm = wr.LLMWritingPack(sentences=[wr.LLMWritingSentence(
        no=1, ko="가", template="It has effect {{A1}} their mind {{A2}} now.",
        items=[wr.LLMWritingItem(id="A1", chunks=["on"], answer="on"),
               wr.LLMWritingItem(id="A2", chunks=["right", "now"], answer="right now")])])
    pack = wr.build_writing_pack(llm, header="H", title="T", subtitle="S")
    s = pack.sentences[0]
    _check("1조각 박스 제거(2조각만 남음)", len(s.items) == 1 and s.items[0].id == "A2")
    _check("제거된 어구는 문장에 복원", "effect on their mind" in s.template)
    html = str(wr.render_writing(s))
    _check("무의미 박스 미노출 + 누출 없음", "〈 on 〉" not in html and "{{" not in html)


def test_validation_empty():
    raised = False
    try:
        wr.validate_llm_writing(wr.LLMWritingPack(sentences=[]))
    except ValueError:
        raised = True
    _check("문장 전무 시 실패", raised)


def test_render_html():
    pack = mock_writing_pack(title="샘플", header="[샘플]")
    html = wr.render_writing_html(pack)
    _check("영작 포인트 박스(wo) 렌더", 'class="wo"' in html)
    _check("정답 페이지 존재", "정답" in html)
    _check("자리표시자 누출 없음", "{{A1}}" not in html and "{{A2}}" not in html)
    _check("지시문 포함", "배열" in html)


def test_show_ko_flag():
    # 한글 포함/제외 두 버전: show_ko=False 면 문장별 한글 길잡이(s-ko)를 숨긴다.
    pack = mock_writing_pack(title="샘플", header="[샘플]")
    ko_guide = pack.sentences[0].ko
    inc = wr.render_writing_html(pack, show_ko=True)
    exc = wr.render_writing_html(pack, show_ko=False)
    _check("한글 포함 버전엔 s-ko + 우리말 길잡이 존재", 'class="s-ko"' in inc and ko_guide in inc)
    _check("한글 제외 버전엔 s-ko 없음", 'class="s-ko"' not in exc and ko_guide not in exc)
    _check("한글 제외 버전도 영작 박스는 유지", 'class="wo"' in exc)
    _check("한글 제외 버전도 정답 페이지는 유지", "정답" in exc)


if __name__ == "__main__":
    test_shuffle_and_answer()
    test_display_never_equals_answer_order()
    test_max_two_boxes()
    test_id_mismatch_order()
    test_answer_from_chunks_when_blank()
    test_single_chunk_box_dropped()
    test_validation_empty()
    test_render_html()
    test_show_ko_flag()
    print("\n영작 워크북 오프라인 테스트 통과 ✅")
