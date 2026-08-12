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
    # 지문 문장 수에 비해 응답이 너무 적으면(예: mega-call 이 1문장만 반환) 실패 → 재요청
    one = pr.LLMProsePack(sentences=[pr.LLMProseSentence(no=1, en="a", ko="가")])
    raised2 = False
    try:
        pr.validate_llm_prose(one, min_sentences=10)   # 지문 12문장급인데 1문장뿐 → 실패
    except ValueError:
        raised2 = True
    _check("문장 과소(1<최소10) 시 실패", raised2)
    pr.validate_llm_prose(one, min_sentences=1)         # 기본(하위호환)은 통과


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
    # 보기에 한글이 섞이면(오직 '앞 문장'만 예외) 출제오류로 보고 제외
    ko_mixed = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="x", ko="y", ref_template="It {{P1}} matters.",
        ref_items=[pr.LLMProseItem(id="P1", display="= [ Vision / the street / 양쪽 살피기 ]",
                                   answer="양쪽 살피기")])])
    r3 = next(w for w in pr.build_prose_pack(ko_mixed, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "ref")
    _check("한글 보기 혼입 문항 제외", len(r3.sentences[0].items) == 0)
    # 지칭 template 에서 원문 단어가 사라지면(대명사/명사 누락) 원문 복구 + 문항 제외
    en = "Users of these technologies have posted many messages."
    lost = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en=en, ko="라",
        ref_template="Users of these {{P1}} have posted many messages.",   # technologies 소실
        ref_items=[pr.LLMProseItem(id="P1", display="= [ technologies / messages / users ]",
                                   answer="technologies")])])
    r4 = next(w for w in pr.build_prose_pack(lost, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "ref")
    _check("지칭 단어 소실 → 원문 복구+문항 제외",
           r4.sentences[0].template == en and len(r4.sentences[0].items) == 0)
    # 정상 지칭(대명사 유지 + {{Pn}} 삽입)은 유지
    ok2 = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="Designers who resist it repeat the same mistakes.", ko="마",
        ref_template="Designers who resist it {{P1}} repeat the same mistakes.",
        ref_items=[pr.LLMProseItem(id="P1", display="= [ early feedback / mistakes / designers ]",
                                   answer="early feedback")])])
    r5 = next(w for w in pr.build_prose_pack(ok2, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "ref")
    _check("정상 지칭 문항 유지", len(r5.sentences[0].items) == 1)
    # 가주어 it("It turns out that …")은 가리키는 대상이 없으므로 제외
    expl = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="It turns out that a photo played a key role.", ko="바",
        ref_template="It {{P1}} turns out that a photo played a key role.",
        ref_items=[pr.LLMProseItem(id="P1", display="= [ 앞 문장 / a photo / a key role ]",
                                   answer="앞 문장")])])
    r6 = next(w for w in pr.build_prose_pack(expl, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "ref")
    _check("가주어 it 문항 제외", len(r6.sentences[0].items) == 0)
    # 문항 탈락 시 원문 복구: LLM 이 원문에 없던 대명사(they)를 삽입한 잔여를 제거
    en7 = "The reason we understand is that our memories are different."
    ins = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en=en7, ko="사",
        ref_template="The reason we understand is that our memories they {{P1}} are different.",
        ref_items=[pr.LLMProseItem(id="P1", display="= [ a / b / c ]", answer="zzz")])])  # 정답 보기에 없음
    r7 = next(w for w in pr.build_prose_pack(ins, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "ref").sentences[0]
    _check("문항 탈락 시 삽입 대명사 잔여 없이 원문 복구",
           r7.template == en7 and len(r7.items) == 0)


def test_form_dedup_and_empty_sentence():
    # 어형: 자리표시자 옆에 남은 정답 어형("(change) changed", "(end) end") 중복 제거 + 빈 문장 제외
    llm = pr.LLMProsePack(sentences=[
        pr.LLMProseSentence(no=1, en="Traditions may change or appear to end.", ko="가",
            form_template="Traditions may {{P1}} or {{P2}} {{P3}} end.",
            form_items=[pr.LLMProseItem(id="P1", display="(change)", answer="change"),
                        pr.LLMProseItem(id="P2", display="(appear)", answer="appear"),
                        pr.LLMProseItem(id="P3", display="(end)", answer="to end")]),
        pr.LLMProseSentence(no=2, en="Concepts have changed.", ko="나",
            form_template="Concepts {{P1}} changed.",
            form_items=[pr.LLMProseItem(id="P1", display="(change)", answer="have changed")]),
        pr.LLMProseSentence(no=3, en="", ko="다"),   # 빈 문장
    ])
    pack = pr.build_prose_pack(llm, header="H", title="T", subtitle="S")
    f = next(w for w in pack.worksheets if w.wtype == "form")
    _check("빈 문장(en 없음) 제외", len(f.sentences) == 2)
    html = str(pr.render_prose(f.sentences[0], "form"))
    _check("'(end) end' 중복 제거(end 미노출)", "end end" not in html and html.count("end") <= 1)
    html2 = str(pr.render_prose(f.sentences[1], "form"))
    _check("'(change) changed' 중복 제거(changed 미노출)", "changed" not in html2)


def test_duplicate_sentence_dropped():
    # LLM 이 같은 문장을 '평문본 + 보기본'으로 중복 생성 → 문항 많은 쪽만 남긴다
    en = "The reason pessimists sound smart is that they avoid being wrong."
    llm = pr.LLMProsePack(sentences=[
        pr.LLMProseSentence(no=1, en=en, ko="가"),                       # 평문(보기 없음)
        pr.LLMProseSentence(no=2, en=en, ko="가",                        # 보기본
            vocab_easy_template="The reason pessimists sound {{P1}} is that they avoid being wrong.",
            vocab_easy_items=[pr.LLMProseItem(id="P1", display="[ smart / stupid ]",
                                              answer="smart", gloss="똑똑한")]),
        pr.LLMProseSentence(no=3, en="A distinct second sentence.", ko="나"),
    ])
    ve = next(w for w in pr.build_prose_pack(llm, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "vocab_easy")
    _check("중복 문장 1개로 축소(+다른 문장 유지)", len(ve.sentences) == 2)
    _check("보기 있는 본만 유지", ve.sentences[0].no == 2 and len(ve.sentences[0].items) == 1)


def test_grammar_agreement_dropped():
    # 순수 수일치 쌍(is/are·does/do·has/have) 어법 문항은 렌더에서 제외, 다른 어법은 유지
    llm = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="Musicians are left-brained, which shows the point.", ko="가",
        grammar_template="Musicians {{P1}} left-brained, {{P2}} shows the point.",
        grammar_items=[pr.LLMProseItem(id="P1", display="[ is / are ]", answer="are"),
                       pr.LLMProseItem(id="P2", display="[ which / what ]", answer="which")])])
    g = next(w for w in pr.build_prose_pack(llm, header="H", title="T", subtitle="S").worksheets
             if w.wtype == "grammar")
    ids = [it.id for it in g.sentences[0].items]
    _check("수일치(is/are) 문항 제외", "P1" not in ids)
    _check("비수일치(관계사 which/what) 문항 유지", "P2" in ids)
    # 일반동사 3인칭 단수 수일치(happens/happen, varies/vary(y→ies))도 제외
    llm3 = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="This happens and its intensity varies.", ko="다",
        grammar_template="This {{P1}} and its intensity {{P2}}.",
        grammar_items=[pr.LLMProseItem(id="P1", display="[ happens / happen ]", answer="happens"),
                       pr.LLMProseItem(id="P2", display="[ varies / vary ]", answer="varies")])])
    g3 = next(w for w in pr.build_prose_pack(llm3, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "grammar")
    _check("일반동사 수일치(happens·varies) 제외", len(g3.sentences[0].items) == 0)
    # was/were: 가정법 아니면 제거, 가정법(as if/if)이면 유지
    def _one_grammar(en, tmpl, disp, ans):
        llm = pr.LLMProsePack(sentences=[pr.LLMProseSentence(no=1, en=en, ko="라",
            grammar_template=tmpl,
            grammar_items=[pr.LLMProseItem(id="P1", display=disp, answer=ans)])])
        return next(w for w in pr.build_prose_pack(llm, header="H", title="T", subtitle="S").worksheets
                    if w.wtype == "grammar").sentences[0].items
    _check("was/were 순수 수일치 제거",
           len(_one_grammar("Pests were winners.", "Pests {{P1}} winners.", "[ was / were ]", "were")) == 0)
    _check("was/were 가정법(as if) 유지",
           len(_one_grammar("He talks as if it were true.", "He talks as if it {{P1}} true.",
                            "[ was / were ]", "were")) == 1)
    # 수일치 문항을 버릴 때 자리표시자를 '정답'으로 복원해 문장에 구멍(gap)이 없어야 한다
    llm4 = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="Weeds and pests were also winners.", ko="마",
        grammar_template="Weeds and pests {{P1}} also winners.",
        grammar_items=[pr.LLMProseItem(id="P1", display="[ was / were ]", answer="were")])])
    s4 = next(w for w in pr.build_prose_pack(llm4, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "grammar").sentences[0]
    html4 = str(pr.render_prose(s4, "grammar"))
    _check("수일치 드롭 후 정답 복원(gap 없음)", "were" in html4 and "{{" not in html4)
    # 본동사 누락(LLM 이 'appears' 소실) → 원문 복구 + 문항 버림
    llm5 = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="But defining the group appears to be flexible.", ko="바",
        grammar_template="But {{P1}} the group to be {{P2}} flexible.",
        grammar_items=[pr.LLMProseItem(id="P1", display="[ defined / defining ]", answer="defining"),
                       pr.LLMProseItem(id="P2", display="[ rather / rathest ]", answer="rather")])])
    s5 = next(w for w in pr.build_prose_pack(llm5, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "grammar").sentences[0]
    _check("본동사 누락 → 원문 복구+문항 버림",
           "appears" in s5.template and len(s5.items) == 0)
    # has/have, does/do 도 제외
    llm2 = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="Concepts have changed and someone does care.", ko="나",
        grammar_template="Concepts {{P1}} changed and someone {{P2}} care.",
        grammar_items=[pr.LLMProseItem(id="P1", display="[ have / has ]", answer="have"),
                       pr.LLMProseItem(id="P2", display="[ does / do ]", answer="does")])])
    g2 = next(w for w in pr.build_prose_pack(llm2, header="H", title="T", subtitle="S").worksheets
              if w.wtype == "grammar")
    _check("has/have·does/do 수일치 제외", len(g2.sentences[0].items) == 0)


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


def test_vocab_word_loss_guard():
    # 어휘 보기 박스가 엉뚱한 자리에 놓여 원문 단어가 사라지면(예: intense 소실) 원문으로 되돌림
    en = ("When the brain is overexcited due to any other intense emotion, "
          "the child is not able to contain their mood.")
    lossy = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en=en, ko="가",
        vocab_template=("When the brain is {{P1}} due to any other {{P2}} emotion, "
                        "the child is not able to their mood."),
        vocab_items=[pr.LLMProseItem(id="P1", display="[ overexcited / overstimulated / overestimated ]",
                                     answer="overexcited / overstimulated", gloss="흥분한"),
                     pr.LLMProseItem(id="P2", display="[ contain / control / contend ]",
                                     answer="contain / control", gloss="억누르다")])])
    w = next(x for x in pr.build_prose_pack(lossy, header="H", title="T", subtitle="S").worksheets
             if x.wtype == "vocab")
    s = w.sentences[0]
    _check("단어 소실 어휘 문항 → 원문 대체+문항 버림", s.template == en and len(s.items) == 0)
    # 정상 문장(소실 없음)은 박스 유지
    ok = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en="These media have become so prolific.", ko="나",
        vocab_template="These media have become so {{P1}}.",
        vocab_items=[pr.LLMProseItem(id="P1", display="[ prolific / abundant / prolix ]",
                                     answer="prolific / abundant", gloss="많은")])])
    w2 = next(x for x in pr.build_prose_pack(ok, header="H", title="T", subtitle="S").worksheets
              if x.wtype == "vocab")
    _check("정상 어휘 문장은 박스 유지", len(w2.sentences[0].items) == 1)
    # 보기 박스도 없이 단어만 누락된 경우(items 비어 있음)도 원문으로 복구
    en3 = "Literally, the child is outside themselves, outside their rational part."
    drop = pr.LLMProsePack(sentences=[pr.LLMProseSentence(
        no=1, en=en3, ko="다",
        vocab_template="Literally, the child is outside themselves, outside their part.",
        vocab_items=[])])
    w3 = next(x for x in pr.build_prose_pack(drop, header="H", title="T", subtitle="S").worksheets
              if x.wtype == "vocab")
    _check("박스 없이 단어 누락(rational)도 원문 복구", w3.sentences[0].template == en3)


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
    test_form_dedup_and_empty_sentence()
    test_duplicate_sentence_dropped()
    test_grammar_agreement_dropped()
    test_corrupt_template_falls_back_to_en()
    test_vocab_word_loss_guard()
    test_render_html()
    test_show_ko_flag()
    print("\n단일 유형 산문 워크시트 오프라인 테스트 통과 ✅")
