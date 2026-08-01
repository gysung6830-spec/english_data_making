"""오프라인 테스트: 시험지 생성 파이프라인을 API 없이 검증한다.

- 데모 데이터 검증·번호 연속·조판(HTML)
- 볼드 5곳 규칙
- 단일 지문 공유: 6종이 모두 같은 정본 문장에서 파생되는지
- LLM 경로(생성기)를 가짜 클라이언트로 대체해 스키마→build→검증→조판 배선
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from exam import build as B  # noqa: E402
from exam import pipeline, renderer, validator  # noqa: E402
from exam.demo_data import DNA, demo_passages  # noqa: E402
from exam.schemas import (  # noqa: E402
    Analysis,
    ContentOut,
    GrammarOut,
    GrammarReason,
    InsertOut,
    KeyTerm,
    OrderOut,
    ShortOut,
    TopicOut,
    VocabOut,
    WordMark,
    WrongReason,
)
from exam.gen2 import (  # noqa: E402
    AOut,
    BOut,
    DOut,
    EOut,
    FOut,
    GOut,
    Pair,
)
from exam.set2 import TYPE_ORDER2  # noqa: E402
from exam.types import TYPE_ORDER  # noqa: E402


def test_demo_validation_and_numbering() -> None:
    passages = demo_passages()
    validator.validate_passages(passages)
    numbers = validator.validate_numbering(passages, start=1)
    assert numbers == [[1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14]]
    print("✓ 데모 검증·번호 연속 통과:", numbers)


def test_render_html_bold_rules() -> None:
    html = renderer.render_html(demo_passages(), header_note="○○학원 고3")
    for cls in ("brand-title", "qnum", "passage-label", "answer-title",
                "answer-key", "boki-title", "cue"):
        assert cls in html, f"볼드 클래스 누락: {cls}"
    assert html.index('class="questions') < html.index('class="answers')
    assert "○○학원 고3" in html
    # 4개 섹션(학생용 → 교사용 → 빠른 정답 → 해설지)이 순서대로 존재
    for sec in ("학생용", "교사용", "빠른 정답", "정답 및 해설"):
        assert sec in html, f"섹션 누락: {sec}"
    order = [html.index("학생용 · 문제"), html.index("교사용 · 문제"),
             html.index("빠른 정답"), html.index("정답 및 해설 · 해설지")]
    assert order == sorted(order), "섹션 순서가 어긋납니다."
    assert "teach-exp" in html and "quick-grid" in html
    # 섹션 선택: 학생용만 → 교사용/빠른정답/해설지 배너 없음, 첫 섹션 break 해제
    only_student = renderer.render_html(demo_passages(), sections=["student"])
    assert "학생용 · 문제" in only_student
    assert "교사용 · 문제" not in only_student
    assert "빠른 정답" not in only_student
    assert "해설지" not in only_student
    assert "first-sec" in only_student
    # 교사용만 → 학생용 배너 없이 교사용이 첫 섹션(break 해제)
    only_teacher = renderer.render_html(demo_passages(), sections=["teacher"])
    assert "학생용 · 문제" not in only_teacher
    assert 'class="teacher first-sec"' in only_teacher
    print("✓ 조판 HTML·볼드 5곳·4섹션·섹션선택·머리글 통과")


def test_single_source_shared() -> None:
    """6종이 모두 '같은 정본 문장'을 공유하는지 확인.

    지문의 특징적인 원문 어구가 순서·삽입·주제·서술형 문제 본문에 모두 등장해야 한다.
    (어휘·어법은 지정 단어만 치환되므로 별도 확인.)
    """
    p = demo_passages()[0]  # DNA
    marker = "vanishingly small space"      # 정본에만 있는 특징 어구
    for t in ("order", "insert", "topic", "content", "short_answer"):
        assert marker in p.q[t], f"{t} 본문이 정본을 공유하지 않음"
    # 정본 문장이 실제로 각 유형에 그대로 들어갔는지(어휘는 밑줄 단어만 달라짐)
    assert "millions of ordinary hard drives combined" in p.q["order"]
    assert "millions of ordinary hard drives combined" in p.q["topic"]
    print("✓ 단일 지문 공유(6종이 같은 정본 사용) 통과")


def test_build_and_validators() -> None:
    s = DNA.sentences
    q, a = B.make_order(s, given_n=1, block_sizes=[2, 2, 2], display=[2, 1, 3], reason="r")
    assert "(A)" in q and "answer-key" in a

    # LLM 오류(개수 오산·범위 초과·대소문자)는 예외 대신 '자동 보정'되어야 한다
    q2, _ = B.make_order(s, given_n=99, block_sizes=[9, 9], display=[7, 7, 7], reason="r")
    assert "(A)" in q2                                   # 보정되어 정상 생성
    q3, _ = B.make_insert(s, remove_idx=0, reason="r")   # 첫 문장 → 내부로 보정
    assert "given-sentence" in q3
    q4, _ = B.make_vocab(s, [(1, "REMARKABLE", "notable"), (1, "small", "tiny"),
                             (3, "durable", "fragile"), (4, "efficiency", "eff"),
                             (5, "expensive", "costly")], 3, "r")
    assert "<u>" in q4                                   # 대소문자 달라도 매칭

    # 정말 불가능한 입력만 예외
    for bad in (
        lambda: B.make_vocab(s, [(1, "nonexistentword", "x")] * 5, 1, "r"),  # 없는 단어
        lambda: B.make_order(["only one."], 1, [1, 1, 1], [1, 2, 3], "r"),   # 문장 부족
    ):
        try:
            bad()
        except Exception:
            pass
        else:
            raise AssertionError("검증이 동작하지 않음")
    print("✓ build 변형기·자동 보정·검증 통과")


def test_error_guards() -> None:
    """오류 가드: 약어 문장분리, G 개수 범위, 조판 이스케이프."""
    from exam import build2
    from exam.analyzer import split_sentences
    assert len(split_sentences("Dr. Smith won the U.S. prize. He left. It ended.")) == 3
    try:
        build2.make_G(["s"], ["a", "b", "c", "d", "e"], 0, "r", {})
    except ValueError:
        pass
    else:
        raise AssertionError("G 0개 일치가 차단되지 않음")
    html = renderer.render_html(demo_passages(), header_note="X<b>&Y", doc_title="T<x>")
    assert "X&lt;b&gt;&amp;Y" in html and "<title>T&lt;x&gt;</title>" in html

    # A: 밑줄 중첩 없음 + 같은 단어 중복 지정 차단
    from exam import build2
    s = ["The cat sat on the mat.", "The cat ran fast.", "It ended well now here."]
    q, _ = build2.make_A(s, [(0, "cat", "CAT"), (0, "mat", "MAT"), (1, "ran", "RAN"),
                             (2, "ended", "ENDED"), (2, "well", "WELL")],
                         2, "r", ["1", "2", "3", "4", "5"])
    assert q.count("<u>") == 5 and "<u><span" not in q
    for bad in (
        lambda: build2.make_A(s, [(0, "cat", "x")] * 5, 1, "r", ["1", "2", "3", "4", "5"]),
        lambda: build2.make_F(s, 0, "The cat", ["1", "2", "3", "4", "5"], 1, "r", {}),  # 2회 등장
    ):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("모호성 가드가 동작하지 않음")
    print("✓ 오류 가드(약어분리·G개수·이스케이프·중첩/다중출현) 통과")


def test_set2_demo() -> None:
    """변형문제 2회(A~G) 데모: 검증·번호·조판."""
    from exam.demo2 import demo_passages_2
    from exam.set2 import TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
    ps = demo_passages_2()
    validator.validate_passages(ps, TYPE_ORDER2)
    nums = validator.validate_numbering(ps, 1, TYPE_ORDER2)
    assert nums == [[1, 2, 3, 4, 5, 6, 7]]
    html = renderer.render_html(ps, type_order=TYPE_ORDER2,
                                prompts=TYPE_PROMPTS2, labels=TYPE_LABELS2)
    assert "vanishingly small space" in html          # 정본 공유
    assert "다음 글의 내용과 일치하는 것의 개수는?" in html   # G 발문
    assert "함의추론" in html                            # B 라벨(해설)
    print("✓ 2회(A~G) 데모 검증·조판 통과")


def test_pdf_cleaning() -> None:
    """PDF 정제: 한글·머리글 제거, 영어 지문만 남기기."""
    from exam import ingest
    seg = (
        "[EBS] 올림포스 영어독해 기본1 ­ 한줄해석 (좌지문 우해석)\n"
        "Ch. 04 Unit 10 - 2번: 제목 한글입니다\n"
        "① Although the wish to be alone is often strong, its intensity varies. 혼자 있고\n"
        "② We need other people to confirm that we exist. 우리는 필요로 한다.\n"
        "[Flow Edu] flowedu.tistory.com\n"
    )
    out = ingest._clean_pdf_text(seg)
    assert "Although the wish to be alone" in out
    assert "We need other people" in out
    assert "올림포스" not in out and "Ch." not in out and "flowedu" not in out
    assert not any("가" <= c <= "힣" for c in out)      # 한글 없음
    print("✓ PDF 정제(한글·머리글 제거) 통과")


def test_workbook_noise() -> None:
    """WORKBOOK 워크시트 노이즈(러닝 헤더·각주 번호·문장 일련번호)를 걷어내고,
    문제번호별로 지문을 분리하는지."""
    import re

    from exam import ingest
    raw = (
        "31 2026 6 ┃3 WORKBOOK4 WORKBOOK. 1. Ever since the early Enlightenment, "
        "preservation and conservation have been closely related.1) 2. Taken as near "
        "synonyms, their meaning is to maintain an object insofar as possible in its "
        "present state, to protect it from change, usually for research and display.2) "
        "3. Conservationists who distinguish their activities emphasize restorative "
        "aspects of the whole discipline in careful ways.3) "
        "32 2026 6 ┃3 WORKBOOK4 WORKBOOK. 1. Speakers do not always put everything "
        "important into words.1) 2. Very often you understand meaning by observing "
        "nonverbal behaviors such as tone, eye contact, and gestures every day.2) "
    )
    ps = ingest._passages_from_raw(raw)
    assert len(ps) == 2, ps                              # 문제 31·32 → 2개
    joined = " ".join(ps)
    assert "WORKBOOK" not in joined                       # 러닝 헤더 제거
    assert not re.search(r"\d\)", joined)                 # 각주 번호 제거
    assert not re.search(r"(?<![\w.])\d{1,3}\.\s+[A-Z]", joined)   # 문장 일련번호 제거
    assert ps[0].startswith("Ever since the early Enlightenment")
    assert ps[1].startswith("Speakers do not always put")

    # 실제 원본(EXAM4YOU) 형태: 한글 머리글 + 페이지 번호(- 14 -) + 로고
    raw2 = (
        "31번 2026년 6월 한국교육과정평가원 모의평가┃고3 단계별 WORKBOOK4 해석 연습하기\n"
        "WORKBOOK 문장 전체의 자연스러운 해석을 써 보세요.\n"
        "1. Ever since the early Enlightenment, preservation and conservation have "
        "been closely related.1)\n"
        "2. Conservationists who distinguish their activities from preservation "
        "emphasize restorative aspects of the whole field in careful ways.2)\n"
        "- 14 -\n"
        "EXAM4YOU\n"
        "32번 2026년 6월 한국교육과정평가원 모의평가┃고3 단계별 WORKBOOK4 해석 연습하기\n"
        "WORKBOOK 문장 전체의 자연스러운 해석을 써 보세요.\n"
        "1. Speakers do not always put everything important into words in real life.1)\n"
        "2. Very often you understand meaning by observing nonverbal behaviors and "
        "gestures across many different social settings every day.2)\n"
        "- 15 -\n"
    )
    ps2 = ingest._passages_from_raw(raw2)
    assert len(ps2) == 2, ps2
    j2 = " ".join(ps2)
    assert "EXAM4YOU" not in j2 and "WORKBOOK" not in j2 and "모의평가" not in j2
    assert not re.search(r"[-–]\s*\d+\s*[-–]", j2)        # 페이지 번호 제거
    assert not any("가" <= c <= "힣" for c in j2)          # 한글 없음
    assert ps2[0].startswith("Ever since the early Enlightenment")
    assert ps2[1].startswith("Speakers do not always put")

    # 문항 번호를 보존한다: 워크북은 31·32, [Flow Edu]·통짜는 번호 없음(None)
    numbered = ingest._passages_from_raw_numbered(raw)
    assert [n for n, _ in numbered] == ["31", "32"]
    numbered2 = ingest._passages_from_raw_numbered(raw2)
    assert [n for n, _ in numbered2] == ["31", "32"]
    plain = ingest._passages_from_raw_numbered("Just a single plain English passage. " * 12)
    assert [n for n, _ in plain] == [None]
    print("✓ WORKBOOK 노이즈 제거·문제번호별 분리(문항번호 보존 포함) 통과")


def test_arrangement_answer_snap() -> None:
    """어순배열 정답이 지문 문장과 정확히 일치하지 않아도(축약형·미세 차이) 실패하지 않고
    토큰·답과 가장 잘 맞는 지문 문장으로 스냅되는지. 무관하면 여전히 실패."""
    sents = [
        "People are likely to be more satisfied with a new building.",
        "Understanding how each user reacts inevitably produces a better building.",
    ]
    # produces→produce 처럼 미세하게 어긋난 LLM 답 → 정확한 지문 문장으로 스냅
    snapped = B.resolve_passage_sentence(
        "Understanding how each user reacts inevitably produce a better building",
        ["understanding", "how", "each", "user", "reacts", "inevitably",
         "produce", "a", "better", "building"], sents)
    assert snapped == sents[1]
    # 전혀 무관한 답 → None(진짜 오류는 여전히 걸러냄)
    assert B.resolve_passage_sentence("Totally unrelated text.", ["totally"], sents) is None
    # make_short 이 하드 실패 대신 스냅해 정답에 원래 문장이 들어간다
    _, a = B.make_short(
        sents, q1_prompt="p", q1_answer="한글",
        q2_prompt="p",
        q2_tokens=["understanding", "how", "each", "user", "react", "inevitably",
                   "produce", "a", "better", "building"],
        q2_cues=["react", "produce"],
        q2_answer="Understanding how each user reacts inevitably produce a better building",
        q3_prompt="p", q3_before="A ", q3_mid=" is ", q3_after=" now.",
        q3_cue_a="consult", q3_cue_b="reduce", q3_ans_a="consulted", q3_ans_b="reduced",
        q3_reason="근거.")
    assert "inevitably produces a better building" in a
    print("✓ 어순배열 정답 스냅(미세 불일치 교정·무관은 실패) 통과")


def test_blank_phrase_punctuation() -> None:
    """F(빈칸)·B(함의): LLM 어구가 곧은 따옴표/대시라도 지문(굽은 따옴표)에서 찾아
    지문 실제 표기로 교정되는지. 못 찾으면 (None, None)."""
    from exam import build2
    sents = ["As it is easy to misinterpret nonverbal behavior, effective listeners "
             "verbally confirm their interpretations of someone’s nonverbal "
             "communication."]
    # LLM 은 곧은 따옴표 someone's
    idx, exact = build2.locate_phrase(
        "verbally confirm their interpretations of someone's nonverbal communication",
        sents)
    assert idx == 0
    assert "’" in exact                      # 지문의 굽은 따옴표로 교정됨
    # 교정된 어구로 make_F 가 예외 없이 빈칸을 만든다
    q, _ = build2.make_F(sents, 0, exact, ["c1", "c2", "c3", "c4", "c5"], 2, "r",
                         {1: "x", 3: "x", 4: "x", 5: "x"})
    assert "blank-line" in q or "passage" in q
    # 대시(—↔-)도 무시
    s2 = ["This is a case—a hard one—for testing dashes here."]
    _, ex2 = build2.locate_phrase("a case-a hard one-for testing", s2)
    assert ex2 is not None and "—" in ex2
    # 전혀 없는 어구는 None
    assert build2.locate_phrase("totally absent phrase", sents) == (None, None)
    print("✓ 빈칸/함의 어구 부호(따옴표·대시) 무시 매칭 통과")


def test_hwp_ingest() -> None:
    """HWP 인식: (1) .hwpx(ZIP+XML) 추출·정제, (2) .hwp PARA_TEXT 레코드/제어객체 파싱."""
    import io
    import struct
    import zipfile

    from exam import hwp, ingest

    # (1) .hwpx — OWPML <hp:t> 에서 영어만 뽑고 한글 지시문은 정제로 제거
    xml = (
        '<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
        'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section">'
        '<hp:p><hp:run><hp:t>Involving prospective building users as well as clients '
        'is even more valuable in the long run for any large institution, because the '
        'people who use a space every day understand its practical needs far better '
        'than the client who merely pays for the project.</hp:t>'
        '</hp:run></hp:p>'
        '<hp:p><hp:run><hp:t>다음 글의 순서로 가장 적절한 것은?</hp:t></hp:run></hp:p>'
        '</hs:sec>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Contents/section0.xml", xml)
    hwpx = ROOT / "output" / "test" / "sample.hwpx"
    hwpx.parent.mkdir(parents=True, exist_ok=True)
    hwpx.write_bytes(buf.getvalue())
    passages = ingest.read_hwp_passages(hwpx)
    assert len(passages) == 1
    assert "prospective building users" in passages[0]
    assert "순서로" not in passages[0]                    # 한글 지시문 제거
    hwpx.unlink()

    # (2) .hwp 본문 레코드: PARA_TEXT(UTF-16LE) + 8코드유닛 인라인 제어객체는 건너뛴다
    body = "Hello".encode("utf-16le") + struct.pack("<H", 2) + b"\x00" * 14 \
        + " World".encode("utf-16le")
    header = 0x43 | (len(body) << 20)                     # tag=PARA_TEXT, size
    rec = struct.pack("<I", header) + body
    texts = [hwp._decode_para_text(d) for t, d in hwp._iter_records(rec)
             if t == hwp._HWPTAG_PARA_TEXT]
    assert "".join(texts).strip() == "Hello World"
    print("✓ HWP 인식(.hwpx 추출·정제, .hwp 레코드/제어객체 파싱) 통과")


def test_analyzer_uses_real_passage() -> None:
    """분석기가 엉뚱한 지문을 내놓아도 '넣은 지문'만 쓰는지."""
    from exam import analyzer
    from exam.schemas import Analysis, KeyTerm as _KT

    class _Halluc:
        def structured(self, system, prompt, model_cls, **kw):
            return Analysis(title="X",
                            sentences=["Fake one.", "Fake two.", "Fake three.", "Fake four."],
                            main_idea="x", key_terms=[_KT(word="a", synonym="b")],
                            hardest_sentence="z")

    body = ("The printing press changed how knowledge spread across Europe. "
            "It made books cheaper and far more widely available. "
            "As literacy rose, new ideas travelled faster than before. "
            "This reshaped science and politics for centuries.")
    a = analyzer.analyze(_Halluc(), body)
    joined = " ".join(a.sentences)
    assert "printing press" in joined and "Fake" not in joined
    print("✓ 분석기: 넣은 지문만 사용(환각 무시) 통과")


class _FakeClient:
    def structured(self, system, prompt, model_cls, max_tokens=8000,
                   max_retries=1, extra_validate=None, image_path=None,
                   cache_prefix=None):
        obj = _FAKE[model_cls.__name__]()
        if extra_validate:
            extra_validate(obj)
        return obj


def _fake_analysis() -> Analysis:
    return Analysis(
        title="Test",
        sentences=[
            "The first sentence introduces the topic clearly.",
            "The second sentence adds an important detail.",
            "The third sentence gives a concrete example.",
            "The fourth sentence draws the whole thing together.",
        ],
        main_idea="A test main idea.",
        key_terms=[KeyTerm(word="topic", synonym="subject", antonym="")],
        hardest_sentence="The fourth sentence draws the whole thing together.",
    )


_FAKE = {
    "Analysis": _fake_analysis,
    "OrderOut": lambda: OrderOut(given_n=1, block_sizes=[1, 1, 1], display=[2, 1, 3],
                                 reason="이유."),
    "InsertOut": lambda: InsertOut(remove_no=2, reason="이유."),
    "TopicOut": lambda: TopicOut(
        choices=["c1", "c2", "c3", "c4", "c5"], answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="무관"), WrongReason(no=3, text="모순"),
                       WrongReason(no=4, text="무관"), WrongReason(no=5, text="모순")]),
    "ContentOut": lambda: ContentOut(
        choices=["선지1", "선지2", "선지3", "선지4", "선지5"], answer_no=2, reason="일치 근거.",
        wrong_reasons=[WrongReason(no=1, text="~부분이 틀림"), WrongReason(no=3, text="~부분이 틀림"),
                       WrongReason(no=4, text="~부분이 틀림"), WrongReason(no=5, text="~부분이 틀림")]),
    "VocabOut": lambda: VocabOut(
        marks=[WordMark(sent_no=1, word="first", shown="initial"),
               WordMark(sent_no=2, word="important", shown="crucial"),
               WordMark(sent_no=3, word="concrete", shown="abstract"),
               WordMark(sent_no=4, word="together", shown="jointly"),
               WordMark(sent_no=1, word="clearly", shown="plainly")],
        answer_no=3, reason="이유."),
    "GrammarOut": lambda: GrammarOut(
        marks=[WordMark(sent_no=1, word="introduces", shown="introduce"),
               WordMark(sent_no=2, word="adds", shown="adds"),
               WordMark(sent_no=3, word="gives", shown="give")],
        answer_nos=[1, 3],
        reasons=[GrammarReason(no=1, text="수 일치"), GrammarReason(no=3, text="수 일치")]),
    "ShortOut": lambda: ShortOut(
        q1_prompt="p1", q1_answer="한글답",
        q2_prompt="p2",
        q2_tokens=["the", "first", "sentence", "introduce", "the", "topic", "clearly"],
        q2_cues=["introduce"],
        q2_answer="The first sentence introduces the topic clearly.",  # 지문 문장과 동일
        q3_prompt="p3", q3_before="Info ", q3_mid=" is ", q3_after=" now.",
        q3_cue_a="accumulate", q3_cue_b="govern", q3_ans_a="accumulated", q3_ans_b="governs",
        q3_reason="근거."),
    # --- 2회(A~G) 가짜 출력 -------------------------------------------------
    "AOut": lambda: AOut(
        marks=[WordMark(sent_no=1, word="first", shown="first"),
               WordMark(sent_no=2, word="important", shown="important"),
               WordMark(sent_no=3, word="concrete", shown="abstract"),   # 반의어(오답)
               WordMark(sent_no=4, word="draws", shown="draw"),          # 어법(오답)
               WordMark(sent_no=1, word="clearly", shown="clearly")],
        answer_no=3, reason="이유.",
        choices=["ⓐ, ⓑ", "ⓐ, ⓒ", "ⓒ, ⓓ", "ⓑ, ⓔ", "ⓓ, ⓔ"]),
    "BOut": lambda: BOut(
        phrase="concrete example", choices=["b1", "b2", "b3", "b4", "b5"],
        answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="축자적 오독"), WrongReason(no=3, text="논지 위배"),
                       WrongReason(no=4, text="무관"), WrongReason(no=5, text="모순")]),
    "DOut": lambda: DOut(
        tokens=["the", "third", "sentence", "give", "a", "concrete", "example"],
        cues=["give"],
        answer="The third sentence gives a concrete example.",  # 지문 문장 그대로
        reason="원래 배열."),
    "EOut": lambda: EOut(
        before="The passage presents its ", mid=" through a ", after=" for readers.",
        pairs=[Pair(a="topic", b="example", a_ok=True, b_ok=True),      # 정답(둘 다 맞음)
               Pair(a="topic", b="wrongword", a_ok=True, b_ok=False),
               Pair(a="wrongword", b="example", a_ok=False, b_ok=True),
               Pair(a="wrongword", b="badword", a_ok=False, b_ok=False),
               Pair(a="badword", b="wrongword", a_ok=False, b_ok=False)],
        answer_no=1, reason="이유."),
    "FOut": lambda: FOut(
        blank_phrase="concrete example", choices=["f1", "f2", "f3", "f4", "f5"],
        answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="모순"), WrongReason(no=3, text="무관"),
                       WrongReason(no=4, text="모순"), WrongReason(no=5, text="무관")]),
    "GOut": lambda: GOut(
        statements=["진술1", "진술2", "진술3", "진술4", "진술5"],
        matches=[True, False, True, False, True], reason="이유.",
        per_stmt=["일치", "불일치", "일치", "불일치", "일치"]),
}


def test_llm_path_wiring() -> None:
    passage = pipeline.build_passage(_FakeClient(), "dummy body")
    assert passage.types == set(TYPE_ORDER)
    validator.check_passage(passage)
    # 부정어·원문단어 방식도 배선되는지
    for m in ("negation", "original"):
        p = pipeline.build_passage(_FakeClient(), "dummy body", vocab_method=m)
        validator.check_passage(p)
    # 어휘 방식은 난이도에 연동: 상=부정어 · 중=유의어 · 하=원문단어
    from exam import difficulty
    assert difficulty.vocab_method("상") == "negation"
    assert difficulty.vocab_method("중") == "synonym"
    assert difficulty.vocab_method("하") == "original"
    for lv in ("상", "중", "하"):
        p = pipeline.build_passage(_FakeClient(), "dummy body", level=lv)
        validator.check_passage(p)
    html = renderer.render_html([passage])
    assert "정답 및 해설" in html
    print("✓ LLM 경로(생성기→build→검증→조판) 배선 통과")


def test_pdf_merge(tmp_out: Path = ROOT / "output" / "test") -> None:
    """여러 파트(세트·난이도 조합)를 한 PDF로 합본하는지."""
    from exam.demo2 import demo_passages_2
    from exam.set2 import TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
    tmp_out.mkdir(parents=True, exist_ok=True)
    parts = [
        {"passages": demo_passages(), "header_note": "변형문제 1회 · 난이도 중",
         "sections": ["student", "answers"]},
        {"passages": demo_passages_2(), "header_note": "변형문제 2회 · 난이도 상",
         "sections": ["student", "answers"], "type_order": TYPE_ORDER2,
         "prompts": TYPE_PROMPTS2, "labels": TYPE_LABELS2},
    ]
    out = tmp_out / "merge.pdf"
    renderer.render_pdf_multi(parts, out)
    assert out.exists() and out.stat().st_size > 2000
    print("✓ 여러 파트 PDF 합본 통과")


def test_prompt_cache_request() -> None:
    """cache_prefix 를 주면 지문·분석이 system 캐시 블록으로 올라가고, 사용자 프롬프트에서는
    중복 제거되는지(캐시 효과)."""
    from src.client import build_request

    ctx = "[문장]\n(1) A sentence here.\n(2) Another one.\n" * 3   # 공유 앞부분
    prompt = "이 지시문대로 문제를 만드세요.\n\n" + ctx               # 지시문 + 지문
    req = build_request("claude-opus-4-8", "SYS", prompt, OrderOut,
                        max_tokens=100, cache_prefix=ctx)
    # system 은 [SYS, ctx(cache_control)] 형태
    assert isinstance(req["system"], list) and len(req["system"]) == 2
    assert req["system"][1]["cache_control"] == {"type": "ephemeral"}
    assert req["system"][1]["text"] == ctx
    # 사용자 프롬프트에서 지문은 제거되어 지시문만 남는다(중복 방지)
    assert ctx not in req["messages"][0]["content"]
    assert "지시문대로" in req["messages"][0]["content"]
    # cache_prefix 가 없으면 system 은 문자열 그대로
    req2 = build_request("claude-opus-4-8", "SYS", prompt, OrderOut, max_tokens=100)
    assert req2["system"] == "SYS"
    print("✓ 프롬프트 캐싱 요청 구성(공유 앞부분 캐시·중복 제거) 통과")


def test_parallel_and_shared_analysis(tmp_out: Path = ROOT / "output" / "test") -> None:
    """유형 병렬 생성 + 지문 병렬 분석 + 1회·2회 분석 공유가 정상 배선되는지."""
    from exam import gen2, pipeline
    tmp_out.mkdir(parents=True, exist_ok=True)

    client = _FakeClient()
    bodies = ["dummy body one", "dummy body two"]

    # 1) 지문 여러 개 병렬 분석
    analyses = pipeline.analyze_bodies(client, bodies)
    assert len(analyses) == len(bodies)

    # 2) 1회: 미리 만든 분석을 공유하며 병렬 유형 생성 → 번호 연속(1..14)
    out1 = tmp_out / "p1.pdf"
    pipeline.build_exam(client, bodies, out1, analyses=analyses)
    assert out1.exists()

    # 3) 2회: 같은 분석 공유 → A~G 병렬 생성
    out2 = tmp_out / "p2.pdf"
    gen2.build_exam2(client, bodies, out2, analyses=analyses)
    assert out2.exists()

    # 4) 병렬 build_passage 결과가 순서대로 온전히 채워졌는지(7종)
    p = pipeline.build_passage(client, "dummy", analysis=analyses[0])
    assert p.types == set(TYPE_ORDER)
    p2 = gen2.build_passage2(client, "dummy", analysis=analyses[0])
    assert p2.types == set(TYPE_ORDER2)
    print("✓ 병렬 생성·병렬 분석·1회2회 분석 공유 통과")


def test_difficulty_lever() -> None:
    """상/중/하 레버가 분석에 지침을 심고, 모든 생성기 context 에 실려 가는지."""
    from exam import difficulty, gen2, pipeline
    from exam.generators.base import context

    assert difficulty.normalize(None) == "중"
    assert difficulty.normalize("이상한값") == "중"
    assert difficulty.content_difficulty("하") == "plain"
    assert difficulty.content_difficulty("상") == "hard"

    client = _FakeClient()
    # level 을 주면 build_passage 가 분석에 지침을 심고 → context 에 노출된다
    a = _fake_analysis()
    a.difficulty_note = difficulty.clause("상")
    assert "[난이도: 상]" in context(a)

    # 1회·2회 모두 level 경로가 정상 배선되는지
    p1 = pipeline.build_passage(client, "dummy", level="하")
    assert p1.types == set(TYPE_ORDER)
    p2 = gen2.build_passage2(client, "dummy", level="상")
    assert p2.types == set(TYPE_ORDER2)
    print("✓ 상/중/하 난이도 레버(지침 주입·1회2회 배선) 통과")


def test_error_reduction_settings() -> None:
    """무인 배치 신뢰도 설정: config 기본값과 build_request 의 thinking/effort 반영."""
    from src.client import build_request
    from src.config import ProcessingCfg, load_config

    # 1) 기본값이 '오류 감축' 쪽으로 서 있는지
    dc = ProcessingCfg()
    assert dc.thinking is True and dc.effort == "high"
    assert dc.max_retries == 2 and dc.pdf_vision_fallback is True
    # load_config 도 같은 기본값을 읽어오는지(파일 없거나 미지정 시)
    cfg = load_config()
    assert cfg.processing.thinking is True
    assert cfg.processing.effort == "high"
    assert cfg.processing.max_retries >= 2
    assert cfg.processing.pdf_vision_fallback is True

    # 2) thinking=True → 적응형 사고 + max_tokens 여유 상향
    req = build_request("claude-opus-4-8", "SYS", "P", OrderOut,
                        max_tokens=100, thinking=True, effort="high")
    assert req["thinking"] == {"type": "adaptive"}
    assert req["max_tokens"] >= 9000                      # 사고 토큰 여유
    assert req["output_config"]["effort"] == "high"       # 추론 강도는 output_config

    # 3) 기본(thinking off, effort 없음)이면 thinking 키가 없고 max_tokens 그대로
    req2 = build_request("claude-opus-4-8", "SYS", "P", OrderOut, max_tokens=100)
    assert "thinking" not in req2
    assert req2["max_tokens"] == 100
    assert "effort" not in req2["output_config"]
    print("✓ 오류 감축 설정(적응형 사고·effort·재시도·기본값) 통과")


def test_answer_spread() -> None:
    """정답 위치 분산: 선지 재배열로 정답을 목표 위치로 옮기되 정오·오답근거는 보존."""
    from exam import answer_spread as A

    # place_answer: 정답이 target 위치로 가고, 나머지는 원래 상대순서 유지
    choices = ["c1", "c2", "c3", "c4", "c5"]      # 정답 = 2번(c2)
    wrong = {1: "w1", 3: "w3", 4: "w4", 5: "w5"}  # 오답 근거(정답 2 제외)
    new_c, new_ans, new_wrong = A.place_answer(choices, 2, 5, wrong)
    assert new_c[new_ans - 1] == "c2"             # 정답 내용 불변
    assert new_ans == 5                            # 목표 위치로 이동
    assert new_c == ["c1", "c3", "c4", "c5", "c2"]   # 나머지 상대순서 유지
    # 오답 근거가 '새 위치'로 정확히 재매핑되는지(내용은 원래 선지에 붙어 따라감)
    for pos, text in new_wrong.items():
        assert new_c[pos - 1] == {"w1": "c1", "w3": "c3", "w4": "c4", "w5": "c5"}[text]
    assert new_ans not in new_wrong                # 정답 위치엔 오답근거 없음

    # 정답이 이미 목표면 그대로
    nc, na, _ = A.place_answer(choices, 3, 3, None)
    assert na == 3 and nc == choices

    # pick: 지문마다 같은 유형이라도 위치가 달라져(몰림 방지) 여러 값이 나온다
    p0 = [A.pick(0, s, len(A.SLOTS1)) for s in A.SLOTS1.values()]
    p1 = [A.pick(1, s, len(A.SLOTS1)) for s in A.SLOTS1.values()]
    assert p0 != p1                                # 지문0과 지문1의 정답 위치 패턴이 다름
    assert all(1 <= v <= 5 for v in p0 + p1)

    # 통합: 정답 위치가 실제로 여러 값으로 흩어지는지(FakeClient 4지문×주제·내용일치)
    from exam import renderer
    client = _FakeClient()
    ps = pipeline.build_passages(client, ["b1", "b2", "b3", "b4"])
    keys = []
    for i, p in enumerate(ps):
        _, quick = renderer._blocks([p], start=1)
        for t, cell in zip(TYPE_ORDER, quick):
            if t in ("topic", "content"):
                keys.append(cell["key"])
    assert len(set(keys)) >= 2, keys               # 한 번호로 몰리지 않음
    print("✓ 정답 위치 분산(재배열·오답근거 재매핑·몰림 방지) 통과")


def test_passage_source_label() -> None:
    """지문 라벨: 원본 문항번호가 있으면 '[31번]', 없으면 위치 기준 '[지문 i]'."""
    # 라벨 없음 → 위치 기준
    html0 = renderer.render_html(demo_passages())
    assert "[지문 1]" in html0 and "[지문 2]" in html0

    # source_label 지정 → 문항번호로 표기(위치 라벨은 사라짐)
    ps = demo_passages()
    ps[0].source_label = "31번"
    ps[1].source_label = "32번"
    html = renderer.render_html(ps)
    assert "[31번]" in html and "[32번]" in html
    assert "[지문 1]" not in html and "[지문 2]" not in html

    # 일부만 번호가 있으면, 없는 지문은 위치 기준(i)으로 대체
    ps2 = demo_passages()
    ps2[0].source_label = "31번"          # 1번째만 번호
    html2 = renderer.render_html(ps2)
    assert "[31번]" in html2 and "[지문 2]" in html2

    # 라벨 스레딩: build_passages(labels=…) 가 Passage.source_label 에 실린다
    client = _FakeClient()
    ps3 = pipeline.build_passages(client, ["b1", "b2"], labels=["45번", "46번"])
    assert [p.source_label for p in ps3] == ["45번", "46번"]
    print("✓ 지문 라벨(원본 문항번호·위치 폴백·labels 스레딩) 통과")


def test_review_flags_and_page(tmp_out: Path = ROOT / "output" / "test") -> None:
    """검토 메모: 자동 점검이 필요한 문항을 맨 끝 별도 페이지로 모은다."""
    from pypdf import PdfReader

    from exam import review
    from exam.types import Passage

    # 1) 자동 보정 감지 — flags 싱크에 사유가 담긴다
    s = DNA.sentences
    fl: list[str] = []
    B.make_order(s, given_n=99, block_sizes=[9, 9], display=[7, 7, 7], reason="r", flags=fl)
    assert review.FIX_ORDER in fl                       # 파라미터 재분배 감지
    fl2: list[str] = []
    B.make_insert(s, remove_idx=0, reason="r", flags=fl2)   # 첫 문장 → 내부로 클램프
    assert review.FIX_INSERT in fl2
    # 정상 입력이면 보정 플래그가 없다
    fl3: list[str] = []
    B.make_order(s, given_n=1, block_sizes=[2, 2, 2], display=[2, 1, 3], reason="r", flags=fl3)
    assert fl3 == []

    # 2) 오답 근거 약함 — 짧은 근거는 잡고, 충분한 근거는 통과
    weak = review.weak_distractors([WrongReason(no=1, text="무관"),
                                    WrongReason(no=3, text="모순"),
                                    WrongReason(no=4, text="지문 3문장과 배치되어 사실과 반대됨"),
                                    WrongReason(no=5, text="지문에 언급되지 않은 내용임")])
    assert weak and "2개" in weak[0]                    # 4개 중 2개가 짧음
    assert review.weak_distractors([WrongReason(no=1, text="충분히 길고 구체적인 오답 근거입니다")]) == []

    # 3) collect_review — 문서 연속 번호로 정확히 매긴다(순서=1, 주제=3, 2지문 서술형=14)
    ps = demo_passages()
    ps[0].flag(TYPE_ORDER[0], [review.FIX_ORDER])       # 1번(순서)
    ps[0].flag(TYPE_ORDER[2], ["오답 근거 약함: …"])       # 3번(주제)
    ps[1].flag(TYPE_ORDER[6], [review.FIX_SNAP])        # 14번(서술형)
    items = renderer.collect_review(ps, start=1)
    assert [it["no"] for it in items] == [1, 3, 14]

    # 4) 교사용이면 맨 끝에 '검토 메모' 페이지가 붙고, 학생용만이면 붙지 않는다
    tmp_out.mkdir(parents=True, exist_ok=True)
    out = renderer.render_pdf(ps, tmp_out / "rv_teacher.pdf")
    r = PdfReader(str(out))
    assert "검토 메모" in (r.pages[-1].extract_text() or "")
    out_s = renderer.render_pdf(ps, tmp_out / "rv_student.pdf", sections=["student"])
    rs = PdfReader(str(out_s))
    joined = " ".join((pg.extract_text() or "") for pg in rs.pages)
    assert "검토 메모" not in joined                     # 학생용에는 노출 안 함

    # 5) 플래그가 하나도 없으면 페이지 자체가 없다(정상 문항만 있는 경우)
    clean = demo_passages()
    assert renderer.collect_review(clean, start=1) == []

    # 6) 합본(render_pdf_multi): 여러 파트의 권장 문항을 '단 한 장'으로 모은다
    p1 = demo_passages(); p1[0].flag(TYPE_ORDER[0], [review.FIX_ORDER])
    p2 = demo_passages(); p2[0].flag(TYPE_ORDER[2], ["오답 근거 약함"])
    parts = [
        {"passages": p1, "header_note": "변형문제 1회", "sections": ["teacher", "answers"]},
        {"passages": p2, "header_note": "변형문제 1회 · 난이도 상", "sections": ["teacher", "answers"]},
    ]
    outm = renderer.render_pdf_multi(parts, tmp_out / "rv_multi.pdf")
    rm = PdfReader(str(outm))
    titled = [i for i, pg in enumerate(rm.pages) if "검토 메모" in (pg.extract_text() or "")]
    assert titled == [len(rm.pages) - 1]                # 오직 마지막 한 장
    print("✓ 검토 메모(점검 문항) 수집·맨 끝 페이지·합본 통과")


def test_conditional_vision_fallback(tmp_out: Path = ROOT / "output" / "test") -> None:
    """조건부 Vision OCR: 글자 있는 PDF 는 vision 안 부르고, 빈(스캔) PDF 만 폴백."""
    from exam import ingest

    calls = {"vision": 0}

    def _fake_vision(client, path, **kw):
        calls["vision"] += 1
        return ["Recovered scanned passage body. " * 12]   # 120자↑ 확보

    orig_vision = ingest.read_pdf_passages_vision
    orig_read = ingest.read_pdf_passages_numbered
    ingest.read_pdf_passages_vision = _fake_vision
    tmp_out.mkdir(parents=True, exist_ok=True)
    fake_pdf = tmp_out / "dummy.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 dummy")   # 실제 파싱은 monkeypatch 로 우회
    try:
        # (a) 글자 PDF: 텍스트 지문이 나오면 vision 호출 안 함
        ingest.read_pdf_passages_numbered = lambda p: [(None, "Real text passage body. " * 12)]
        out = ingest.load_bodies([fake_pdf], client=object(), vision_fallback=True)
        assert calls["vision"] == 0 and len(out) == 1

        # (b) 스캔 PDF(텍스트 0) + client·vision_fallback → vision 폴백
        ingest.read_pdf_passages_numbered = lambda p: []
        out = ingest.load_bodies([fake_pdf], client=object(), vision_fallback=True)
        assert calls["vision"] == 1 and len(out) == 1

        # (c) vision_fallback=False 면 폴백 안 하고 안내 오류
        ingest.read_pdf_passages_numbered = lambda p: []
        try:
            ingest.load_bodies([fake_pdf], client=object(), vision_fallback=False)
            assert False, "빈 PDF 는 오류여야 함"
        except ValueError:
            pass
        assert calls["vision"] == 1   # 호출 증가 없음
    finally:
        ingest.read_pdf_passages_vision = orig_vision
        ingest.read_pdf_passages_numbered = orig_read
    print("✓ 조건부 Vision OCR 폴백(글자 PDF 건너뜀·스캔만 OCR) 통과")


if __name__ == "__main__":
    test_demo_validation_and_numbering()
    test_render_html_bold_rules()
    test_single_source_shared()
    test_build_and_validators()
    test_error_guards()
    test_set2_demo()
    test_pdf_cleaning()
    test_workbook_noise()
    test_arrangement_answer_snap()
    test_blank_phrase_punctuation()
    test_hwp_ingest()
    test_analyzer_uses_real_passage()
    test_llm_path_wiring()
    test_prompt_cache_request()
    test_pdf_merge()
    test_parallel_and_shared_analysis()
    test_difficulty_lever()
    test_error_reduction_settings()
    test_answer_spread()
    test_passage_source_label()
    test_review_flags_and_page()
    test_conditional_vision_fallback()
    print("\n모든 오프라인 테스트 통과 ✅")
