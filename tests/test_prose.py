"""단일 유형 산문 워크시트 오프라인 테스트 (API 없이).

실행: python -m tests.test_prose
검증 항목:
  - 자리표시자 {{Pn}} ↔ items 개수 검증(유형별)
  - build_prose_pack: 어법·어형·어휘·한글해석 4종 생성
  - 어형(form)=쓰는 밑줄, 어법/어휘=선택 박스, 한글해석=작성칸
  - id 불일치시 등장 순서 정렬
  - HTML 렌더(작성칸/정답 페이지 해석)
"""
from __future__ import annotations

from src import prose_render as pr
from samples.prose_mock import mock_llm_prose, mock_prose_pack


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def test_validation_and_mismatch_tolerated():
    # 자리표시자 2개 vs items 1개(불일치)라도 실패시키지 않고 build 가 처리한다.
    llm = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="a x b y", ko="엑스",
        grammar_template="a {{P1}} b {{P2}}",
        grammar_items=[pr.LLMProseItem(id="P1", display="[a/b]", answer="a")])])
    pr.validate_llm_prose(llm)                       # 예외 없어야 함(관용)
    pack = pr.build_prose_pack(llm, header="H", title="T", subtitle="S")
    g = next(w for w in pack.worksheets if w.wtype == "grammar")
    html = str(pr.render_prose(g.sentences[0], "grammar"))
    _check("남은 자리표시자 노출 없음", "{{" not in html)
    # 문장이 아예 없으면 재요청되도록 실패
    raised = False
    try:
        pr.validate_llm_prose(pr.LLMProsePack(sentences=[]))
    except ValueError:
        raised = True
    _check("문장 전무 시 실패", raised)


def test_build_four_worksheets():
    pack = pr.build_prose_pack(mock_llm_prose(), header="H", title="T", subtitle="S")
    types = [w.wtype for w in pack.worksheets]
    _check("6종 워크시트(어법·어형·어휘하·어휘상·지칭·한글해석) 순서",
           types == ["grammar", "form", "vocab_easy", "vocab", "ref", "translate"])


def test_form_write_flag():
    pack = pr.build_prose_pack(mock_llm_prose(), header="H", title="T", subtitle="S")
    form = next(w for w in pack.worksheets if w.wtype == "form")
    grammar = next(w for w in pack.worksheets if w.wtype == "grammar")
    all_form_write = all(it.write for s in form.sentences for it in s.items if s.items)
    no_grammar_write = all(not it.write for s in grammar.sentences for it in s.items if s.items)
    _check("어형=쓰는 밑줄(write), 어법=선택 박스", all_form_write and no_grammar_write)


def test_translate_no_items():
    pack = pr.build_prose_pack(mock_llm_prose(), header="H", title="T", subtitle="S")
    tr = next(w for w in pack.worksheets if w.wtype == "translate")
    _check("한글 해석 연습: items 없음 + 원문/해석 보존",
           all(not s.items and s.template and s.ko for s in tr.sentences))


def test_id_mismatch_order():
    # id 라벨이 어긋나도 등장 순서로 정렬되어야 한다.
    llm = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="A B C", ko="가나다",
        grammar_template="A {{P1}} B {{P2}} C",
        grammar_items=[pr.LLMProseItem(id="P9", display="[x/y]", answer="x"),
                       pr.LLMProseItem(id="P8", display="[m/n]", answer="m")])])
    pr.validate_llm_prose(llm)
    pack = pr.build_prose_pack(llm, header="H", title="T", subtitle="S")
    g = next(w for w in pack.worksheets if w.wtype == "grammar").sentences[0]
    ids = [it.id for it in g.items]
    _check("id 불일치시 등장 순서 정렬(P1,P2)", ids == ["P1", "P2"])


def test_ref_safeguard():
    # 지칭: 정답이 보기에 없으면 출제오류이므로 자동 제외, '앞 문장'은 유지
    bad = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="x", ko="y", ref_template="They {{P1}} go.",
        ref_items=[pr.LLMProseItem(id="P1", display="= [ a / b / c ]", answer="zzz")])])
    r = next(w for w in pr.build_prose_pack(bad, header="H", title="T", subtitle="S").worksheets
             if w.wtype == "ref")
    _check("정답이 보기에 없으면 문항 제외", len(r.sentences[0].items) == 0)
    ok = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="x", ko="y", ref_template="This {{P1}} matters.",
        ref_items=[pr.LLMProseItem(id="P1", display="= [ 앞 문장 / a / b ]", answer="앞 문장")])])
    r2 = next(w for w in pr.build_prose_pack(ok, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "ref")
    _check("앞 문장 정답 유지", r2.sentences[0].items[0].answer == "앞 문장")


def test_corrupt_template_falls_back_to_en():
    # template 이 손상돼('P P1}}') 정상 자리표시자가 없고 items 만 있으면 원문(en)으로 대체하고
    # 문항을 버려 'P P1}}' 같은 조각이 노출되지 않아야 한다.
    llm = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="They will delete the content.", ko="삭제",
        vocab_template="P P1}}",
        vocab_items=[pr.LLMProseItem(id="P1", display="[ a / b / c ]", answer="a / b", gloss="뜻")])])
    w = next(x for x in pr.build_prose_pack(llm, header="H", title="T", subtitle="S").worksheets
             if x.wtype == "vocab")
    s = w.sentences[0]
    html = str(pr.render_prose(s, "vocab"))
    _check("손상 template → 원문(en) 대체", s.template == "They will delete the content.")
    _check("깨진 조각(P1}}) 미노출", "P1}}" not in html and "}}" not in html and "{{" not in html)
    _check("손상 문항 버림", len(s.items) == 0)


def test_render_html():
    pack = mock_prose_pack(title="샘플", header="[샘플]")
    html = pr.render_prose_html(pack)
    _check("한글 해석 연습 작성칸(translate-box) 렌더", "translate-box" in html)
    _check("정답 페이지 존재", "정답" in html)
    _check("자리표시자 누출 없음", "{{P1}}" not in html and "{{P2}}" not in html)


def test_show_ko_flag():
    # show_ko=False 면 어법/어형/어휘 문제면의 문장별 한글(s-ko)을 숨긴다.
    pack = mock_prose_pack(title="샘플", header="[샘플]")
    inc = pr.render_prose_html(pack, show_ko=True)
    exc = pr.render_prose_html(pack, show_ko=False)
    _check("한글 포함 버전엔 s-ko 존재", 'class="s-ko"' in inc)
    _check("한글 제외 버전엔 s-ko 없음", 'class="s-ko"' not in exc)
    _check("한글 제외 버전도 정답 페이지는 유지", "정답" in exc)


if __name__ == "__main__":
    test_validation_and_mismatch_tolerated()
    test_build_four_worksheets()
    test_form_write_flag()
    test_translate_no_items()
    test_id_mismatch_order()
    test_ref_safeguard()
    test_corrupt_template_falls_back_to_en()
    test_render_html()
    test_show_ko_flag()
    print("\n단일 유형 산문 워크시트 오프라인 테스트 통과 ✅")
