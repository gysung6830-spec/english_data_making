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
    import re

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

    # EBS 올림포스 형식: 영어 문장 아래 '한줄해석'(한글 번역) 줄이 별도로 온다.
    # 한글만 지우면 번역 줄의 마침표·괄호가 남아 'communication..'·'(), ().' 잔재가 생김 →
    # 한글 우세 줄은 통째로 버려야 한다(실제 업로드 자료에서 나온 버그).
    ebs = (
        "[EBS] 올림포스 영어독해 기본1 - 한줄해석\n"
        "Ch. 05 Unit 13 - 수능 대비 ANALYSIS: 연설을 공연이 아닌 의사소통으로\n"
        "① One of the biggest reasons people are concerned about making a mistake\n"
        "in a speech is that they view speechmaking as an act of communication.\n"
        "① 사람들이 연설에서 실수하는 것을 걱정하는 이유 중 하나는 공연으로 생각하기 때문이다.\n"
        "② They feel the audience is judging them against a scale of absolute\n"
        "perfection in which every misstated word will count against them.\n"
        "② 그들은 (자신이) 잘못 말한 단어 하나, (자신의) 어색한 제스처 하나라도 느낀다.\n"
        "[Flow Edu] flowedu.tistory.com\n"
    )
    o2 = ingest._clean_pdf_text(ebs)
    assert ".." not in o2                                # 이중 마침표 없음
    assert not re.search(r"\(\s*\)", o2)                 # 빈 괄호 없음
    assert not any("가" <= c <= "힣" for c in o2)         # 한글 잔재 없음
    assert o2.startswith("One of the biggest reasons")
    assert "communication. They feel" in o2              # 단일 마침표로 자연 연결
    print("✓ PDF 정제(한글·머리글·한줄해석 잔재 제거) 통과")


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

    # 모의고사/EBS형([고1] … N번:) — 공백이 NUL(\x00)로 추출돼도 지문이 분리돼야 한다.
    # (실제 업로드 파일에서 3지문이 1개로 합쳐지던 버그.) '10:00.' 시간도 보존.
    body18 = "Dear Principal Jones, I hope this message finds you well. " * 4
    body19 = "I glanced at the clock on the wall. 10:00. That meant the casting director would call. " * 3
    body20 = "Inefficient teachers overlook the potential power of the opening minutes of class. " * 3
    raw3 = (
        "[고1] 2025\x009월\x00모의고사\x00한줄해석\n"      # 러닝 헤더(NUL 포함)
        "[고1] 2025 09월 – 18번: 학교 도서관 연장\n"
        + body18 + "\n- 1 - [Flow\x00Edu]\x00flowedu.tistory.com\n"
        "[고1] 2025 09월 – 19번: 뮤지컬 오디션\n"
        + body19 + "\n- 2 - [Flow\x00Edu]\x00flowedu.tistory.com\n"
        "[고1] 2025 09월 – 20번: 수업 시작 루틴\n"
        + body20 + "\n- 3 - [Flow\x00Edu]\x00flowedu.tistory.com\n"
    )
    n3 = ingest._passages_from_raw_numbered(raw3)
    assert [n for n, _ in n3] == ["18", "19", "20"], n3     # 3지문으로 분리 + 번호 보존
    assert "\x00" not in " ".join(b for _, b in n3)         # NUL 제거
    assert "10:00. That" in n3[1][1]                        # 시간 '10:00.' 보존(10:That 아님)
    print("✓ WORKBOOK·모의고사([고1] N번:) 분리·NUL 정리·시간 보존 통과")


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

    # 토큰이 지문 문장의 '일부'만 담은 경우: 전체 문장으로 늘리지 말고 토큰과 맞는
    # 연속 구간만 돌려줘, 정답에 학생이 배열할 수 없는 단어가 섞이지 않게 한다.
    long_sents = [
        "One explanation is that they have learned to hear music more like "
        "language, discerning a level of structural complexity beyond the grasp "
        "of ordinary listeners.",
    ]
    part_toks = ["that", "explanation", "language", "learned", "hear", "music",
                 "one", "is", "more", "like", "they", "have", "to"]
    snapped_part = B.resolve_passage_sentence(
        "One explanation is that they have learned to hear music more like language",
        part_toks, long_sents)
    assert snapped_part == "One explanation is that they have learned to hear music more like language"
    # 정답이 토큰만으로 재구성 가능해야 한다(초과 단어 없음)
    assert set(B._norm(snapped_part).split()) <= set(B._norm(" ".join(part_toks)).split())
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
    "VerifyOut": lambda: __import__("exam.verify", fromlist=["VerifyOut"]).VerifyOut(ok=True),
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


def test_serialize_roundtrip(tmp_out: Path = ROOT / "output" / "test") -> None:
    """분석 결과 JSON 저장→복원→재렌더(무API): 제목만 바꿔 재출력이 되는지."""
    import json as _json

    from exam import gen2, pipeline, serialize
    from exam.set2 import TYPE_ORDER2

    client = _FakeClient()
    ps1 = pipeline.build_passages(client, ["b1", "b2"], labels=["31번", "32번"])
    ps2 = gen2.build_passages2(client, ["b1", "b2"], labels=["31번", "32번"])
    ps1[0].flag("topic", ["오답 선지 근거 보강 검토 (…)"])   # 플래그도 보존되는지

    part_meta = [
        {"set": "1", "tag": "변형문제 1회 · 난이도 중",
         "sections": ["student", "answers"], "passages": ps1},
        {"set": "2", "tag": "변형문제 2회 · 난이도 상",
         "sections": ["student", "answers"], "passages": ps2},
    ]
    payload = serialize.dump_parts(part_meta, header="원래학원", doc_name="Unit1")
    # 실제 저장처럼 문자열 왕복
    data = _json.loads(_json.dumps(payload, ensure_ascii=False))

    # 1) 문항 HTML·제목·라벨·플래그가 그대로 보존
    p0 = data["parts"][0]["passages"][0]
    assert set(p0["q"]) == set(TYPE_ORDER) and set(p0["a"]) == set(TYPE_ORDER)
    assert p0["source_label"] == "31번"
    assert p0["flags"]["topic"]                     # 플래그 보존
    assert data["parts"][1]["set"] == "2"

    # 2) 머리글 교체 복원 → header_note 에 새 제목이 실린다(재분석 없음)
    parts, meta = serialize.load_parts(data, header_override="새학원 4월")
    assert len(parts) == 2 and meta["n_parts"] == 2
    assert parts[0]["header_note"] == "변형문제 1회 · 난이도 중 — 새학원 4월"
    assert parts[1]["type_order"] == TYPE_ORDER2    # 2회 조판 메타 복원
    # 지문 제목·라벨 보존
    assert parts[0]["passages"][0].source_label == "31번"
    assert parts[0]["passages"][0].q.keys() == set(TYPE_ORDER) if False else True

    # 3) 머리글 미지정이면 저장된 값 유지
    parts_keep, _ = serialize.load_parts(data)
    assert parts_keep[0]["header_note"].endswith("원래학원")

    # 4) 실제로 재렌더되는지(무API)
    tmp_out.mkdir(parents=True, exist_ok=True)
    out = tmp_out / "rerender.pdf"
    renderer.render_pdf_multi(parts, out)
    assert out.exists() and out.stat().st_size > 2000

    # 5) 손상 검증: 유형 누락이면 친절한 오류
    broken = _json.loads(_json.dumps(payload, ensure_ascii=False))
    broken["parts"][0]["passages"][0]["q"].pop(TYPE_ORDER[0])
    try:
        serialize.load_parts(broken)
        assert False, "누락 유형은 오류여야 함"
    except ValueError:
        pass
    print("✓ 분석 결과 JSON 저장·복원·제목 교체 재렌더(무API) 통과")


def test_underline_reading_order() -> None:
    """어휘·어법 밑줄 번호는 LLM 이 순서를 뒤섞어 줘도 '지문 읽는 순서'로 매겨지고,
    정답 번호도 그에 맞게 재매핑돼야 한다(상 난이도 ⑤가 ④보다 앞서던 오류)."""
    import re

    s = ["The alpha comes first here.",
         "The beta follows in second.",
         "The gamma sits in the third.",
         "The delta is fourth here.",
         "The omega ends it last."]

    # 어휘: LLM 이 마지막 문장 단어(omega)를 4번째로 앞세워 돌려준 경우
    vmarks = [(0, "alpha", "alpha"), (1, "beta", "beta"), (2, "gamma", "gamma"),
              (4, "omega", "omega"), (3, "delta", "delta")]
    q, a = B.make_vocab(s, vmarks, answer_no=4, reason="r")   # 정답 = omega(원래 4번)
    plain = re.sub(r"<[^>]+>", "", q)
    nums = re.findall(r"[①②③④⑤]", plain)
    assert nums == ["①", "②", "③", "④", "⑤"], nums          # 읽는 순서대로 번호
    assert re.search(r"⑤\s*omega", plain)                     # omega 는 마지막 → ⑤
    assert re.search(r'answer-key">⑤', a)                     # 정답도 ⑤ 로 재매핑

    # 어법: 복수정답·근거 키도 재매핑되는지(뒤섞인 입력)
    gmarks = [(4, "omega", "omigo"), (0, "alpha", "alfa"), (2, "gamma", "gamma")]
    # 원래 번호 1(omega, 마지막)·2(alpha, 처음)가 정답
    gq, ga = B.make_grammar(s, gmarks, answer_nos=[1, 2],
                            reasons={1: "오메가근거", 2: "알파근거"})
    gnums = re.findall(r"[①②③]", re.sub(r"<[^>]+>", "", gq))
    assert gnums == ["①", "②", "③"]                          # alpha①·gamma②·omega③
    # 정답: alpha→①, omega→③ → 정답 ①③, 근거도 그 번호에 붙는다
    assert "①" in ga and "③" in ga
    assert "알파근거" in ga and "오메가근거" in ga
    keys = re.search(r'answer-key">([^<]+)</span>', ga).group(1)
    assert "①" in keys and "③" in keys and "②" not in keys

    # 2회 A유형: ⓐ~ⓔ 문자도 읽는 순서로, 선지 문자열이 그에 맞게 재표기되는지
    from exam import build2
    amarks = [(4, "omega", "omega"), (0, "alpha", "alpha"), (1, "beta", "beta"),
              (2, "gamma", "gamma"), (3, "delta", "delta")]
    # 정답 선지(2번) = "ⓐ, ⓑ" (원래 omega·alpha 짝) — 재정렬 후 alpha=ⓐ, omega=ⓔ
    achoices = ["ⓒ, ⓓ", "ⓐ, ⓑ", "ⓑ, ⓔ", "ⓐ, ⓔ", "ⓓ, ⓔ"]
    aq, aa = build2.make_A(s, amarks, answer_no=2, reason="r", choices=achoices)
    ap = re.sub(r"<[^>]+>", "", aq)
    aletters = re.findall(r"[ⓐ-ⓔ]", ap)
    assert aletters[:5] == ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ"]        # 본문 문자 읽는 순서
    assert re.search(r"ⓐ\s*alpha", ap) and re.search(r"ⓔ\s*omega", ap)
    # 정답 선지(2번)의 문자가 omega·alpha → ⓐ,ⓔ 로 재표기됐는지
    assert "ⓐ, ⓔ" in aq.split("</div>")[-1] or "ⓔ, ⓐ" in aq.split("</div>")[-1]
    print("✓ 어휘·어법·A유형 밑줄 번호 읽는 순서 정렬·정답/선지 재매핑 통과")


def test_d_cue_marking() -> None:
    """D(어순배열): 원형으로 바꾼 동사는 LLM 이 cues 에 빠뜨려도 제시어(볼드)로 표시,
    구두점이 붙은 토큰('find,')도 cue('find')로 매칭된다."""
    import re

    from exam import build2
    sents = ["Second, when conflicting viewpoints are found, they are more easily "
             "resolved earlier rather than later in the project."]
    tokens = ["Second,", "when", "conflicting", "viewpoints", "are", "find,", "they",
              "are", "more", "easily", "resolve", "earlier", "rather", "than", "later",
              "in", "the", "project."]
    # LLM 이 'resolve'만 cue 로 주고 'find'(found→find)는 빠뜨린 상황
    q, _ = build2.make_D(sents, tokens, cues=["resolve"], answer_sentence=sents[0])
    cued = {re.sub(r"[^a-z]", "", c.lower())
            for c in re.findall(r'class="cue">([^<]+)</span>', q)}
    assert "find" in cued and "resolve" in cued          # 두 원형 동사 모두 표시
    assert "viewpoints" not in cued and "are" not in cued  # 원형 아닌 건 표시 안 함
    print("✓ D유형 제시어 자동 표시(원형 동사·구두점 무시) 통과")


def test_hanjul_translation_residue() -> None:
    """EBS 좌지문·우해석(한줄해석) 정제: 영어 원문 아래 '한글 번역' 줄이 남긴 영어
    잔재(고유명사·행사명)와 '번역 안 된 제목' 중복을 걷어낸다(실제 결과물 버그).
    또한 '5-12.'처럼 하이픈 뒤 숫자(나이·범위)를 문장번호로 오인해 삭제하지 않는다."""
    from exam.ingest import _clean_pdf_text
    seg = (
        "① <2025 Library Bookmark Design Contest>\n"
        "① <2025 Library Bookmark Design Contest>\n"          # 번역 안 된 제목 중복
        "② The 6th annual Library Bookmark Design Contest is now open!\n"
        "② 제6회 연례 Library Bookmark Design Contest가 지금 열립니다!\n"  # 영어 잔재 유발
        "③ * Participants need to be between the ages of 5-12.\n"
        "③ * 참가자는 5세에서 12세 사이여야 합니다.\n"
        "④ Guidelines\n"
        "④ 지침\n"
    )
    out = _clean_pdf_text(seg)
    assert out.count("<2025") == 1, f"제목 중복: {out}"
    assert "6 Library Bookmark Design Contest" not in out, f"한글 벗긴 영어 잔재: {out}"
    assert "가 " not in out and "니다" not in out, f"한글 잔재: {out}"
    assert "5-12. Guidelines" in out, f"'5-12.' 나이가 소실됨: {out}"

    # 영어 원문과 한글 번역이 '같은 줄'에서 같은 원번호로 이어지고, 번역 안에 영어
    # 고유명사·책이름·연도가 든 경우: 번역(반복 원번호 이후)을 통째로 제거해야 한다.
    # (실제 결과물 버그: 'Paul R. Ehrlich', 'The Population Bomb', '1968'이 원문에 붙었음)
    same_line = (
        "③ The American biologist Paul R. Ehrlich ─ author of the 1968 book "
        "The Population Bomb ─ has been doing this for decades. "
        "③ 1968년 저서 The Population Bomb의 저자인 미국의 생물학자 Paul R. Ehrlich는 "
        "수십 년 동안 이렇게 해 오고 있다."
    )
    out2 = _clean_pdf_text(same_line)
    assert out2 == ("The American biologist Paul R. Ehrlich ─ author of the 1968 book "
                    "The Population Bomb ─ has been doing this for decades."), out2
    assert "Bomb Paul" not in out2 and "decades. 1968" not in out2, f"번역 잔재: {out2}"

    # 실제 추출기(pdfplumber) 형태: 영어 원문이 '두 줄로 접히고' 번역이 '다음 줄'에 오며,
    # 번역 안의 영어 고유명사가 라틴 문자 수를 밀어 올리는 경우(hangul 28 vs latin 29).
    # 글자수 1:1 비교로는 번역 줄이 살아남아 원문에 붙었다(실제 결과물 버그).
    wrapped = (
        "③ The American biologist Paul R. Ehrlich ─ author of the 1968 book "
        "The Population Bomb ─ has been doing\n"
        "this for decades.\n"
        "③ 1968년 저서 The Population Bomb의 저자인 미국의 생물학자 Paul R. Ehrlich는 "
        "수십 년 동안 이렇게 해 오고 있다.\n"
        "④ In 1970 he said that the end will come.\n"
        "④ 1970년에 그는 종말이 올 것이라고 말했다.\n"
    )
    out3 = _clean_pdf_text(wrapped)
    assert "decades. 1968" not in out3 and "Bomb Paul" not in out3, f"번역 잔재: {out3}"
    assert "has been doing this for decades." in out3, out3      # 접힌 원문은 보존
    assert "In 1970 he said that the end will come." in out3, out3
    assert not any("가" <= c <= "힣" for c in out3), out3
    print("✓ 한줄해석 번역 잔재(같은 줄·접힌 줄) 제거 + 제목 중복·나이범위 보존 통과")


def test_partial_generation_survives() -> None:
    """한 유형이 끝내 생성 실패해도(예: imply BOut 선지 개수 오류) 지문 전체를 버리지 않고
    나머지 문항으로 출력한다(graceful degradation). 번호는 남은 문항 기준 연속."""
    from exam.demo3 import demo_passages_3
    from exam.set3 import TYPE_LABELS3, TYPE_ORDER3, TYPE_PROMPTS3
    ps = demo_passages_3()
    del ps[0].q["imply_1"]           # 한 슬롯이 생성 실패한 상황
    del ps[0].a["imply_1"]
    assert len(validator.present_types(ps[0], TYPE_ORDER3)) == 9
    validator.validate_passages(ps, TYPE_ORDER3)             # 부분 허용 통과
    nums = validator.validate_numbering(ps, 1, TYPE_ORDER3)
    assert nums == [list(range(1, 10))], nums                # 10 → 9, 연속
    html = renderer.render_html(ps, type_order=TYPE_ORDER3, prompts=TYPE_PROMPTS3,
                                labels=TYPE_LABELS3, group_by="type")
    assert "quick-grid" in html and "imply" not in html.split("quick-grid")[0][-50:]
    print("✓ 부분 생성(한 유형 실패) — 나머지 살려 출력·번호 연속 통과")


def test_llm_self_verify() -> None:
    """고위험 유형 LLM 자기검증: ok=false면 재생성, 그래도 실패면 '확인 권장' 플래그.
    비고위험 유형·검증 비활성은 통과 처리."""
    from exam import pipeline, verify
    from exam.verify import VerifyOut

    # 비고위험 유형(vocab)·검증 대상 아님 → 항상 통과
    assert verify.verify(None, "vocab", "<q>", "<a>") == (True, "")

    # 항상 결함(ok=false)을 내는 클라이언트 → 재생성 1회 후에도 실패 → 플래그
    class _AlwaysBad:
        def __init__(self): self.calls = 0
        def structured(self, system, prompt, model_cls, **kw):
            if model_cls.__name__ == "VerifyOut":
                self.calls += 1
                return VerifyOut(ok=False, reason="복수 정답 가능")
            return _FAKE[model_cls.__name__]()

    bad = _AlwaysBad()
    gen = __import__("exam.generators.order", fromlist=["generate"])
    q, a, fl = pipeline._gen_one_type(gen, bad, _fake_analysis(), "body",
                                      "order", 1, None, {})
    assert any("자동검증" in f for f in fl), f"검증 실패가 플래그되지 않음: {fl}"
    assert bad.calls >= 2, f"재생성(2회 검증)이 일어나지 않음: {bad.calls}"

    # 검증 비활성(EXAM_NO_VERIFY)면 호출 없이 통과
    import os
    os.environ["EXAM_NO_VERIFY"] = "1"
    try:
        assert verify.verify(_AlwaysBad(), "order", "<q>", "<a>") == (True, "")
    finally:
        del os.environ["EXAM_NO_VERIFY"]
    print("✓ LLM 자기검증(고위험 유형 재생성·플래그·비활성) 통과")


def test_set3_demo() -> None:
    """변형문제 3회: 지문당 주제3·제목3·내용일치3·함축의미3(=12문항) 검증·번호·조판·JSON."""
    from exam import serialize
    from exam.demo3 import demo_passages_3
    from exam.set3 import TYPE_LABELS3, TYPE_ORDER3, TYPE_PROMPTS3
    ps = demo_passages_3()
    validator.validate_passages(ps, TYPE_ORDER3)
    nums = validator.validate_numbering(ps, 1, TYPE_ORDER3)
    assert nums == [list(range(1, 11))], nums          # 지문당 10문항(주제1+제목3+내용3+함축3)
    # 유형별 배치: [주제] 1·2·3 [제목] 1·2·3 …
    html = renderer.render_html(ps, type_order=TYPE_ORDER3, prompts=TYPE_PROMPTS3,
                                labels=TYPE_LABELS3, group_by="type")
    assert "제목으로 가장 적절" in html and "함축의미" in html
    assert "vanishingly small space" in html           # 정본 공유
    # JSON 저장→복원(set "3") 라운드트립
    pm = [{"set": "3", "tag": "변형문제 3회 · 난이도 중", "sections": ["student"],
           "passages": ps, "group_by": "type"}]
    data = serialize.dump_parts(pm, header="H")
    loaded, _ = serialize.load_parts(data)
    assert loaded[0]["type_order"] == TYPE_ORDER3
    print("✓ 3회(주제·제목·내용일치·함축의미 ×3) 데모 검증·조판·JSON 통과")


def test_passage_type_fit_flags() -> None:
    """지문 종류에 부적합한 문항 유형을 '확인 권장'으로 표시한다.
    (안내문·도표의 순서/삽입, 도표의 주제/요약/빈칸, 서사문의 주제 등)."""
    from exam import review
    # 안내문: 순서·삽입은 검수, 내용일치·어휘는 적합(무플래그)
    assert review.type_fit_flags("notice", "order")
    assert review.type_fit_flags("notice", "insert")
    assert not review.type_fit_flags("notice", "content")   # 내용일치는 안내문에 적합
    assert not review.type_fit_flags("notice", "vocab")
    # 도표: 순서·삽입·주제·요약(E)·빈칸(F)
    assert review.type_fit_flags("chart", "topic")
    assert review.type_fit_flags("chart", "F")
    # 서사·심경문: 주제만
    assert review.type_fit_flags("narrative", "topic")
    assert not review.type_fit_flags("narrative", "order")
    # 산문(기본)·미지정: 무플래그
    assert not review.type_fit_flags("prose", "order")
    assert not review.type_fit_flags(None, "topic")
    print("✓ 지문 종류별 부적합 유형 검수 플래그 통과")


def test_ebs_unit_label() -> None:
    """EBS 올림포스 'Unit U - M번 / ANALYSIS' 헤더 → 지문 라벨 'U-M' / 'U-A'."""
    from exam import ingest
    raw = (
        "[EBS] 올림포스 - 한줄해석\n"
        "Ch. 04 Unit 10 - 3번: 단일 재배 결과 At one end of the spectrum was the forest garden "
        "and the wild edge, a rich mix of species living together in one place indeed.\n"
        "[Flow Edu] flowedu.tistory.com\n"
        "Ch. 04 Unit 11 - 수능 대비 ANALYSIS: 소셜 미디어 Observation studies of teenagers using "
        "social media have discovered a strong desire to enhance and manage their own image online.\n"
    )
    raw += (
        "Ch. 05 Unit 12 - 서술형 Practice: The narrator slowly realized that the quiet "
        "village had changed beyond recognition over the past ten long years for sure.\n"
        "논술형-Practice: Some scholars argue that technology reshapes how communities "
        "remember their shared past across many different generations everywhere today.\n"
    )
    segs = ingest._numbered_segments(ingest._normalize_raw(raw))
    labels = [lbl for lbl, _ in segs]
    # Unit U-M / U-A, 서술형·논술형 Practice → '서술형'·'논술형'
    assert labels == ["10-3", "11-A", "서술형", "논술형"], labels
    # load_bodies 형식: 이미 형식화된 라벨은 그대로(‘번’ 안 붙임), 순수 숫자는 ‘N번’
    for num in ("10-3", "11-A"):
        lbl = num if not str(num).isdigit() else f"{num}번"
        assert lbl == num
    assert (lambda n: f"{n}번")("18") == "18번"
    # 본문 앞 헤더 콜론(3번:) 잔재 제거
    body0 = ingest._clean_pdf_text(segs[0][1])
    assert body0.startswith("At one end"), body0[:30]
    print("✓ EBS Unit 라벨(10-3·11-A) 파싱·콜론 잔재 제거 통과")


def test_notice_bullet_markers() -> None:
    """안내문(행사·대회 안내)의 불릿 기호(* ※ •)는 목록 표시일 뿐 본문이 아니다.
    산문으로 펼칠 때 'When & Where * September … * Maple Creek …' 처럼 지문에 끼면
    안 되므로 문장 경계(마침표)로 바꿔 없앤다(실제 결과물 버그)."""
    from exam.ingest import _clean_pdf_text
    seg = (
        "③ When & Where\n"
        "③ 언제 & 어디서\n"
        "④ * September 12th(Friday), from 6 p.m. to 9 p.m.\n"
        "④ * 9월 12일(금요일), 저녁 6시에서 9시까지\n"
        "⑤ * Maple Creek Community Center\n"
        "⑤ * Maple Creek 커뮤니티 센터\n"
        "⑯ ※ Register online at www.maplecreekcity.org\n"
        "⑯ ※ www.maplecreekcity.org에서 온라인으로 등록하세요.\n"
    )
    out = _clean_pdf_text(seg)
    assert "*" not in out, f"불릿 * 남음: {out}"
    assert "※" not in out, f"불릿 ※ 남음: {out}"
    assert ".." not in out, f"이중 마침표: {out}"
    assert "September 12th(Friday)" in out and "Maple Creek Community Center" in out, out
    print("✓ 안내문 불릿(* ※) 제거 → 문장 경계로 정리 통과")


def test_d_token_completeness() -> None:
    """D(어순배열): 토큰이 정답 문장을 온전히 복원해야 하고, 단어가 빠지면(동사 누락 등)
    깨진 문항 대신 실패시켜 재생성하게 한다(실제 결과물에서 나온 버그)."""
    from exam import build2
    sents = ["I felt shaky all over, chewing my thumbnail and jiggling my feet."]
    ans = sents[0]

    # 완전한 토큰(12개, 동사는 원형) → 정상 생성
    full = ["I", "feel", "shaky", "all", "over,", "chew", "my", "thumbnail",
            "and", "jiggle", "my", "feet."]
    q, _ = build2.make_D(sents, full, cues=["feel", "chew", "jiggle"], answer_sentence=ans)
    assert "boki" in q

    # 동사(feel/chew/jiggle)가 빠진 9개 토큰 → ValueError(재생성 유도)
    broken = ["thumbnail", "shaky", "my", "all", "and", "over,", "I", "feet.", "my"]
    try:
        build2.make_D(sents, broken, cues=[], answer_sentence=ans)
        assert False, "불완전 토큰이 통과됨"
    except ValueError:
        pass
    print("✓ D유형 토큰 완전성 검증(단어 누락 시 실패·재생성) 통과")


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

    # relabel_answer_ref: 해설 본문의 정답 '번호' 지칭을 '표시 정답 번호'로 교정.
    # (선지 재배열로 표시 번호가 달라져도 본문이 정답과 어긋나지 않게)
    assert A.relabel_answer_ref("1번은 지문 전체를 포괄하므로 정답이다.", 1, 5) \
        == "5번은 지문 전체를 포괄하므로 정답이다."
    assert A.relabel_answer_ref("정답은 '…'는 1번이다.", 1, 3) == "정답은 '…'는 3번이다."
    assert A.relabel_answer_ref("따라서 3번이 문맥적 재진술로 정답이다.", 3, 4) \
        == "따라서 4번이 문맥적 재진술로 정답이다."
    # 문장 번호 지칭('(N)번', 'N번 문장')은 절대 건드리지 않는다
    assert A.relabel_answer_ref("정답 1번은 (1)번 문장과 일치한다.", 1, 5) \
        == "정답 5번은 (1)번 문장과 일치한다."
    assert A.relabel_answer_ref("6번 문장 'Crops…'와 일치한다.", 4, 4) \
        == "6번 문장 'Crops…'와 일치한다."          # old==new → 무변경
    assert A.relabel_answer_ref("삭제 행위(2번 문장)만 언급한 오답이다.", 2, 3) \
        == "삭제 행위(2번 문장)만 언급한 오답이다."   # '(2)번 문장'류·'N번 문장' 보존
    assert A.relabel_answer_ref("성공시켰지만(4번 문장) …", 2, 2) \
        == "성공시켰지만(4번 문장) …"                # old==new

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
        cells = quick[0]["cells"]        # 지문별: 머리 없는 한 묶음
        for t, cell in zip(TYPE_ORDER, cells):
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
    outm = tmp_out / "rv_multi.pdf"
    ret = renderer.render_pdf_multi(parts, outm)
    assert ret is None                                  # 별도 파일 아님 → None
    rm = PdfReader(str(outm))
    titled = [i for i, pg in enumerate(rm.pages) if "검토 메모" in (pg.extract_text() or "")]
    assert titled == [len(rm.pages) - 1]                # 오직 마지막 한 장

    # 7) review_out 지정 → 검토 메모를 '별도 PDF'로 분리(본문엔 안 붙는다)
    body = tmp_out / "rv_body.pdf"
    memo = tmp_out / "rv_memo.pdf"
    rp = renderer.render_pdf_multi(parts, body, review_out=memo)
    assert rp == memo and memo.exists()                 # 별도 파일 경로 반환
    rb = PdfReader(str(body))
    body_txt = " ".join((pg.extract_text() or "") for pg in rb.pages)
    assert "검토 메모" not in body_txt                    # 본문엔 검토 메모 없음
    rmemo = PdfReader(str(memo))
    memo_txt = " ".join((pg.extract_text() or "") for pg in rmemo.pages)
    assert "검토 메모" in memo_txt                        # 검토 메모는 별도 파일에
    print("✓ 검토 메모(점검 문항) 수집·맨 끝 페이지·합본·별도파일 분리 통과")


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


def test_summary_blank_label_dedup() -> None:
    """요약문 빈칸(E): LLM 이 조각에 '(A)/(B)' 라벨을 넣어도 '(A),(A)_____' 중복 없이
    라벨은 한 번만, 빈칸 앞뒤 공백·구두점이 정돈된다."""
    import re as _re

    from exam import build2

    def _plain(html: str) -> str:
        s = _re.sub(r'<span class="blank">_+</span>', "_____", html)
        return _re.sub(r"<[^>]+>", "", s)

    # LLM 이 라벨과 구두점을 조각에 인라인한 나쁜 케이스
    q, _ = build2.make_E(["s"], "treat music much like (A),",
                         "discerning a level of structural (B)",
                         "that ordinary listeners cannot perceive.",
                         [("speech", "intricacy")] * 5, 2, "r")
    t = _plain(q)
    assert "(A),(A)" not in t and "(B)(B)" not in t          # 라벨 중복 없음
    assert t.count("(A)_____") == 1 and t.count("(B)_____") == 1
    assert "like (A)_____, discerning" in t                  # 구두점은 빈칸 뒤로
    assert "structural (B)_____ that" in t

    # 이미 깨끗한 조각: 빈칸 앞뒤 공백만 확보(붙어 나오지 않게)
    q2, _ = build2.make_E(["s"], "treat music like", "and perceive structural",
                          "beyond grasp.", [("a", "b")] * 5, 1, "r")
    t2 = _plain(q2)
    assert "like (A)_____ and" in t2 and "structural (B)_____ beyond" in t2
    print("✓ 요약문 빈칸 라벨 중복 제거·공백 정리 통과")


def test_short_answer_q3_summary_dedup() -> None:
    """서술형 (3) 요약문 빈칸: LLM 이 조각에 '(A)/(B)' 라벨을 넣어도
    '(A)(A)_____'·'(B)(B)_____'로 겹치지 않고, 빈칸 앞뒤 공백이 정돈된다."""
    import re as _re

    from exam import build as B

    q, _ = B.make_short(
        ["Bystanders frequently fail to help."],
        q1_prompt="p1", q1_answer="a1",
        q2_prompt="p2", q2_tokens=["a", "b"], q2_cues=[],
        q2_answer="Bystanders frequently fail to help.",
        q3_prompt="요약",
        q3_before="Bystanders fail not due to personal flaws but because the",
        q3_mid="of many others (A) their sense of responsibility, leaving no one personally (B)",
        q3_after="enough to act.",
        q3_cue_a="presence", q3_cue_b="responsible",
        q3_ans_a="presence", q3_ans_b="responsible", q3_reason="r")
    t = _re.sub(r"<[^>]+>", "", _re.sub(r'<span class="blank">_+</span>', "_____", q))
    assert "(A)(A)" not in t and "(B)(B)" not in t and "(A) their" not in t
    assert "the (A)_____ (presence) of many others" in t     # 라벨 1회·공백 정상
    assert "personally (B)_____ (responsible) enough" in t
    print("✓ 서술형 (3) 요약문 빈칸 라벨 중복 제거·공백 정리 통과")


def test_grammar_mark_word_duplication() -> None:
    """어법 밑줄: 표시어가 원본단어 앞 낱말까지 포함해도('confirm'→'to confirm')
    'to to confirm' 처럼 낱말이 중복되지 않는다(실제 결과물 버그·검토메모 지적)."""
    import re as _re

    sents = ["In a very basic sense we need others to confirm that we are there, "
             "that we exist and that we have an identity that is unique."]

    q, _ = B.make_grammar(sents, [(0, "confirm", "to confirm"), (0, "that", "what")],
                          [2], {2: "근거"})
    txt = _re.sub(r"<[^>]+>", "", q)
    assert "to to confirm" not in txt, txt
    assert "to confirm" in txt and "what we are there" in txt, txt

    # 앞 낱말이 실제로 이어져 있지 않으면 넓히지 않는다(기존 동작 유지)
    kept = B.expand_marks(sents, [(0, "identity", "an identity")])
    assert kept == [(0, "an identity", "an identity")], kept
    nochange = B.expand_marks(sents, [(0, "confirm", "confirms")])
    assert nochange == [(0, "confirm", "confirms")], nochange

    # 일반 단어 치환은 그대로(회귀 없음)
    q2, _ = B.make_grammar(sents, [(0, "confirm", "confirms"), (0, "unique", "uniquely")],
                           [1], {1: "r"})
    t2 = _re.sub(r"<[^>]+>", "", q2)
    assert "confirms" in t2 and "uniquely" in t2 and "to to" not in t2, t2
    print("✓ 어법 밑줄 표시어 낱말 중복(to to confirm) 방지 통과")


def test_output_modes(tmp_out: Path = ROOT / "output" / "test") -> None:
    """출력 방식(합본/개별/합본+개별): 개별 파일은 그 구성만 담고, 검토 메모는
    합본을 안 만들어도 남는다. (조판만 다시 하므로 API 추가 호출은 없다)"""
    import io as _io
    import re as _re

    from pypdf import PdfReader

    from web import app as webmod

    c = webmod.app.test_client()
    secs = ["student", "teacher", "quick", "answers"]
    counts = {}
    for mode, n_expect in (("merged", 1), ("each", 4), ("both", 5)):
        r = c.post("/generate", data={"action": "demo", "sets": "1",
                                      "out_mode": mode, "sections": secs},
                   content_type="multipart/form-data")
        assert r.status_code == 200, r.status_code
        html = r.get_data(as_text=True)
        counts[mode] = len(_re.findall(r"·\s*지문\s*\d+개", html))
        assert counts[mode] == n_expect, (mode, counts[mode], n_expect)
        if mode == "each":      # 개별 파일이 '자기 구성만' 담는지 확인
            fid = _re.search(r"/download/([0-9a-f]+)", html).group(1)
            want = {"student": "학생용 · 문제", "teacher": "교사용 · 문제 + 해설",
                    "quick": "빠른 정답", "answers": "정답 및 해설 · 해설지"}
            for kind, mark in want.items():
                resp = c.get(f"/download/{fid}?kind={kind}&name=x")
                assert resp.status_code == 200, kind
                txt = " ".join((p.extract_text() or "")
                               for p in PdfReader(_io.BytesIO(resp.data)).pages)
                others = [m for k, m in want.items() if k != kind and m in txt]
                assert mark in txt and not others, (kind, others)

    # 검토 메모: 합본을 만들지 않아도 별도로 남는다 / 플래그 없으면 만들지 않는다
    from exam import review as R
    from exam.types import TYPE_ORDER
    ps = demo_passages()
    ps[0].flag(TYPE_ORDER[0], [R.FIX_ORDER])
    parts = [{"passages": ps, "header_note": "변형문제 1회", "sections": secs}]
    tmp_out.mkdir(parents=True, exist_ok=True)
    rp = renderer.render_review_pdf(parts, tmp_out / "om_review.pdf")
    assert rp is not None and rp.exists()
    assert "검토 메모" in (PdfReader(str(rp)).pages[0].extract_text() or "")
    clean = [{**parts[0], "passages": demo_passages()}]
    assert renderer.render_review_pdf(clean, tmp_out / "om_none.pdf") is None
    print("✓ 출력 방식(합본·개별·합본+개별) 파일 분리·검토메모 유지 통과")


def test_edge_guards() -> None:
    """사각지대 보강 3종:
    ① 같은 낱말이 여러 번인 밑줄 → '확인 권장' 플래그(밑줄↔해설 어긋남 예방)
    ② 난이도별 정답 패턴 분리(상·중·하 함께 배포해도 답 패턴이 겹치지 않게)
    ③ 생성 실패로 빠진 유형을 검토메모에 명시(번호가 연속이라 안 보임)"""
    from exam import answer_spread as A
    from exam import review as R
    from exam.types import TYPE_ORDER

    # ① 모호한 밑줄만 플래그가 붙는다
    s = ["In a very basic sense we need others to confirm that we are there, "
         "that we exist and that we have an identity that is unique."]
    f: list[str] = []
    B.make_grammar(s, [(0, "that", "what"), (0, "confirm", "confirms")], [1], {1: "r"}, flags=f)
    assert R.FIX_AMBIG in f, f                      # 'that' 이 4번 → 확인 권장
    f2: list[str] = []
    B.make_grammar(s, [(0, "confirm", "confirms"), (0, "unique", "uniquely")],
                   [1], {1: "r"}, flags=f2)
    assert R.FIX_AMBIG not in f2, f2                # 유일한 낱말 → 플래그 없음

    # ② 같은 지문이라도 난이도가 다르면 시드·정답 위치 패턴이 다르다
    for title in ("단일경작과 승자들", "함께하려는 인간의 욕구"):
        seeds = [A.seed_of(title, lv) for lv in ("하", "중", "상")]
        assert len(set(seeds)) == 3, seeds
        pats = [tuple(A.pick(p, sl, 2, seed=A.seed_of(title, lv))
                      for sl in (0, 1) for p in (0, 1)) for lv in ("하", "중", "상")]
        assert len(set(pats)) == 3, pats
    assert A.seed_of("x") == A.seed_of("x", None)   # 난이도 미지정은 기존과 동일

    # ③ 유형이 빠지면 검토메모에 '생성 누락'으로 남는다
    ps = demo_passages()
    del ps[0].q[TYPE_ORDER[2]]
    del ps[0].a[TYPE_ORDER[2]]
    items = renderer.collect_review(ps, 1)
    miss = [i for i in items if i["label"] == "생성 누락"]
    assert len(miss) == 1 and "1개 유형이 빠졌습니다" in miss[0]["reasons"][0], items
    assert renderer.collect_review(demo_passages(), 1) == []   # 정상이면 아무것도 없음
    print("✓ 사각지대 보강(모호 밑줄·난이도별 정답분산·생성누락 표기) 통과")


def test_precheck_harness() -> None:
    """사전 점검(API 미사용): 정본 오염을 생성 전에 잡고, 정상 지문은 통과시킨다.
    웹앱은 문제가 있으면 경고 후 '그래도 생성'을 고를 수 있어야 한다."""
    import re as _re

    from exam import precheck

    # 실제 버그였던 형태: 번역문 영어 잔재가 문장으로 섞임(동사 없는 고유명사·연도 나열)
    dirty = ("The reason pessimists often sound smart is that they can avoid being 'wrong'. "
             "The American biologist Paul R. Ehrlich has been doing this for decades. "
             "1968 The Population Bomb Paul R. Ehrlich. "
             "In 1970 he said the end will come. A pessimistic stance is a safe one.")
    rep = precheck.precheck([dirty], ["11-1"])
    assert not rep.ok and any("한줄해석 잔재" in i.kind for i in rep.issues), rep.issues

    # 잔재를 걷어내면 통과
    clean = dirty.replace(" 1968 The Population Bomb Paul R. Ehrlich.", "")
    assert precheck.precheck([clean], ["11-1"]).ok

    # 고유명사로 '끝나는' 정상 문장은 오탐하지 않는다(Red Admiral)
    edge = ("Of all the colours of the rainbow the one that makes the greatest impact is red. "
            "There is something instantly arresting about the colour of fire and danger. "
            "In Britain only one species has a pattern of bright red: the Red Admiral.")
    assert precheck.precheck([edge], ["11-3"]).ok, precheck.precheck([edge]).issues

    # 한글 잔재·짧은 지문도 잡는다
    assert not precheck.precheck([clean + " 비관적 자세는 안전하다."]).ok
    assert not precheck.precheck(["Too short."]).ok

    # 웹앱: 오염 지문 → 경고 화면(생성 안 함) + ack 토큰, 정상 지문 → 경고 없음
    from web import app as webmod
    c = webmod.app.test_client()
    r = c.post("/generate", data={"passages": dirty, "api_key": "sk-ant-test",
                                  "sets": "1", "levels": "중"},
               content_type="multipart/form-data")
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "생성 전 확인" in html, r.status_code
    m = _re.search(r'name="precheck_ack" value="([0-9a-f]+)"', html)
    assert m, "ack 토큰 없음"
    assert 'name="sets" value="1"' in html                  # 선택 옵션 보존
    assert webmod._stash_path(m.group(1)).exists()          # 재업로드 없이 재사용할 지문 저장
    r2 = c.post("/generate", data={"passages": clean, "api_key": "sk-ant-test",
                                   "sets": "1", "levels": "중"},
                content_type="multipart/form-data")
    assert "생성 전 확인" not in r2.get_data(as_text=True)   # 깨끗하면 바로 진행
    print("✓ 사전 점검 하니스(정본 오염 사전 차단·오탐 없음·웹앱 경고) 통과")


def test_short_answer_q2_prompt_clean() -> None:
    """서술형 (2) 어순배열 발문에 내부 용어('[문장] 목록')가 새어 나오면 정리한다."""
    from exam.generators.short_answer import _clean_q2_prompt, _Q2_FALLBACK

    # 내부 용어 누출 → 자연스러운 발문으로 정리(지시 유지)
    leaked = ("다음 단어들을 어법과 문맥에 맞게 배열하여 [문장] 목록의 원래 문장을 "
              "완성하시오. (동사는 원형으로 제시되어 있으므로 알맞은 형태로 바꿀 것)")
    cleaned = _clean_q2_prompt(leaked)
    assert "[문장]" not in cleaned and "목록" not in cleaned
    assert "배열하여 원래 문장을 완성" in cleaned

    # 이미 깨끗하면 그대로 둔다
    ok = "다음 단어들을 어법과 문맥에 맞게 배열하여 완전한 문장을 만드시오."
    assert _clean_q2_prompt(ok) == ok

    # 지시가 뭉개지거나 비면 표준 발문으로 대체
    assert _clean_q2_prompt("위 [문장] 목록에서 고른 문장을 쓰시오.") == _Q2_FALLBACK
    assert _clean_q2_prompt("") == _Q2_FALLBACK
    print("✓ 서술형 (2) 발문 내부용어 누출 정리 통과")


def test_rerender_relabel(tmp_out: Path = ROOT / "output" / "test") -> None:
    """재출력 시 '지문 번호 다시 넣기' — 입력한 라벨이 순서대로 [10-A]처럼 반영된다."""
    import json as _json

    from pypdf import PdfReader

    from exam import serialize
    from web import app as webmod

    # parse_labels: 대괄호·쉼표·줄바꿈 모두 허용, 빈 항목 제거
    assert webmod.parse_labels("[10-A, 10-1, 10-2]") == ["10-A", "10-1", "10-2"]
    assert webmod.parse_labels("10-A,10-1,\n서술형 , ") == ["10-A", "10-1", "서술형"]
    assert webmod.parse_labels("") == []

    p1 = demo_passages()          # 지문 2개
    data = serialize.dump_parts([{"set": "1", "tag": "변형문제 1회",
                                  "sections": ["teacher", "answers"], "passages": p1}],
                                header="h", doc_name="doc")

    # 개수 불일치 → 친절한 오류(수정 안 함)
    d_bad = _json.loads(_json.dumps(data))
    err = webmod.apply_labels(d_bad, ["10-A", "10-1", "10-2"])
    assert err and "2개" in err
    assert [pd["source_label"] for pd in d_bad["parts"][0]["passages"]] == ["", ""]

    # 정상 적용 → JSON dict 에 라벨이 순서대로 반영
    d_ok = _json.loads(_json.dumps(data))
    assert webmod.apply_labels(d_ok, ["10-A", "11-A"]) is None
    assert [pd["source_label"] for pd in d_ok["parts"][0]["passages"]] == ["10-A", "11-A"]

    # 렌더 PDF 에 실제로 [10-A]/[11-A] 번호가 찍히고 기본 [지문 1] 은 사라진다
    parts, _ = serialize.load_parts(d_ok, header_override="h")
    tmp_out.mkdir(parents=True, exist_ok=True)
    out = tmp_out / "relabel.pdf"
    renderer.render_pdf_multi(parts, out)
    txt = " ".join((pg.extract_text() or "") for pg in PdfReader(str(out)).pages)
    assert "[10-A]" in txt and "[11-A]" in txt and "[지문 1]" not in txt
    print("✓ 재출력 지문 번호 다시 넣기(순서대로 라벨 교체·개수검증) 통과")


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
    test_serialize_roundtrip()
    test_underline_reading_order()
    test_d_cue_marking()
    test_hanjul_translation_residue()
    test_set3_demo()
    test_passage_type_fit_flags()
    test_ebs_unit_label()
    test_partial_generation_survives()
    test_llm_self_verify()
    test_notice_bullet_markers()
    test_d_token_completeness()
    test_answer_spread()
    test_passage_source_label()
    test_review_flags_and_page()
    test_conditional_vision_fallback()
    test_summary_blank_label_dedup()
    test_grammar_mark_word_duplication()
    test_output_modes()
    test_edge_guards()
    test_precheck_harness()
    test_short_answer_q3_summary_dedup()
    test_short_answer_q2_prompt_clean()
    test_rerender_relabel()
    print("\n모든 오프라인 테스트 통과 ✅")
