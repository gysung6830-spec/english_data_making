"""오프라인 테스트: 시험지 생성 파이프라인을 API 없이 검증한다.

- 데모 데이터 검증·번호 연속·조판(HTML)
- 볼드 5곳 규칙
- 단일 지문 공유: 6종이 모두 같은 정본 문장에서 파생되는지
- LLM 경로(생성기)를 가짜 클라이언트로 대체해 스키마→build→검증→조판 배선
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from exam import build as B  # noqa: E402
from exam import renderer, validator  # noqa: E402
from exam.demo_data import DNA, demo_passages  # noqa: E402
from exam.schemas import (  # noqa: E402
    Analysis,
    ContentOut,
    ContentOXOut,
    OXStatement,
    GrammarCountOut,
    GrammarOut,
    GrammarReason,
    InsertOut,
    IrrelevantOut,
    KeyTerm,
    LinkerOut,
    LinkerPair,
    OrderOut,
    PairOddOut,
    ShortOut,
    TitleOut,
    TopicOut,
    VocabOut,
    WordMark,
    WrongReason,
)
from exam.gen2 import (  # noqa: E402
    BOut,
    DOut,
    EOut,
    FOut,
    Pair,
)
from exam.merged import (  # noqa: E402
    MERGED_LABELS,
    MERGED_ORDER,
    MERGED_PROMPTS,
    build_passage_merged,
    build_passages_merged,
    demo_passages_merged,
)


def test_demo_validation_and_numbering() -> None:
    passages = demo_passages()
    validator.validate_passages(passages)
    numbers = validator.validate_numbering(passages, start=1)
    assert numbers == [[1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14]]
    print("✓ 데모 검증·번호 연속 통과:", numbers)


def test_render_html_bold_rules() -> None:
    html = renderer.render_html(demo_passages(), header_note="○○학원 고3")
    for cls in ("brand-title", "qnum", "type-chip", "answer-title",
                "answer-key", "boki-title", "cue"):
        assert cls in html, f"볼드 클래스 누락: {cls}"
    # 지문별 편성에서는 지문 라벨이 그 자리를 대신한다
    assert "passage-label" in renderer.render_html(demo_passages(), group_by="passage")
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
    # 2단에서 문항이 칸 중간에 잘리면 안 된다 — 통째로 다음 칸으로 넘어가야 한다.
    css = (renderer.TEMPLATE_DIR / "exam.css").read_text(encoding="utf-8")
    assert "break-inside: auto" not in css, "문항이 칸 중간에서 잘릴 수 있습니다."
    print("✓ 조판 HTML·볼드 5곳·4섹션·섹션선택·머리글·칸 넘김 통과")


def test_single_source_shared() -> None:
    """6종이 모두 '같은 정본 문장'을 공유하는지 확인.

    지문의 특징적인 원문 어구가 순서·삽입·주제·서술형 문제 본문에 모두 등장해야 한다.
    (어휘·어법은 지정 단어만 치환되므로 별도 확인.)
    """
    p = demo_passages()[0]  # DNA
    marker = "vanishingly small space"      # 정본에만 있는 특징 어구
    for t in ("order", "insert", "topic", "content"):
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


# 어법 유형이 돌려주는 '다시 쓴 지문' 두 벌 — 원문과 문장 수는 같고 표현만 다르다.
_REWRITE_A = [
    "The first sentence opens the topic in a plain way.",
    "However, the second sentence supplies an important detail.",
    "The third sentence offers a concrete example.",
    "The fourth sentence pulls the whole thing together.",
    "The fifth sentence meets an obvious objection.",
    "The sixth sentence closes with a practical suggestion of its own.",
]
_REWRITE_B = [
    "The opening sentence starts the topic without any fuss.",
    "Even so, the next sentence attaches an important detail.",
    "A third sentence presents one concrete example.",
    "The fourth sentence ties the whole thing together.",
    "A fifth sentence meets the obvious objection readers feel.",
    "The last sentence ends on a practical suggestion.",
]

# 어휘 3종이 서로 다른 낱말에 밑줄을 치는 상황을 흉내 낸다(겹침 금지 검증용).
_VOCAB_SETS = [
    [(1, "first", "initial"), (2, "important", "crucial"), (3, "concrete", "abstract"),
     (4, "together", "jointly"), (5, "obvious", "evident")],
    [(1, "introduces", "presents"), (2, "adds", "appends"), (3, "gives", "offers"),
     (4, "draws", "pulls"), (6, "practical", "useful")],
    [(1, "topic", "subject"), (2, "detail", "particular"), (3, "example", "instance"),
     (4, "whole", "entire"), (5, "answers", "addresses")],
]
_VOCAB_CYCLE = itertools.cycle(_VOCAB_SETS)


def _fake_ox(prefix: str, n: int = 10) -> list:
    """내용 O/X 가짜 출력 — O 둘, 나머지 X 가 축을 하나씩 쓴다."""
    from exam.shape import OX_AXES

    axes = list(OX_AXES)
    out, k = [], 0
    for i in range(1, n + 1):
        if i in (2, n - 3):                   # O 두 개(자리는 조판기가 다시 정한다)
            out.append(OXStatement(text=f"{prefix} {i}", is_true=True,
                                   why=f"근거{i}", axis="일치"))
        else:
            out.append(OXStatement(text=f"{prefix} {i}", is_true=False,
                                   why=f"근거{i}", axis=axes[k]))
            k += 1
    return out


def _fake_vocab_negation():
    """부정어형 어휘의 가짜 출력 — 정답 밑줄이 삽입한 부정어를 품는다."""
    # 낱말은 다른 어휘 문항(_VOCAB_SETS)·짝짓기와 겹치지 않는 것으로 고른다.
    return VocabOut(
        marks=[WordMark(sent_no=2, word="However", shown="However"),
               WordMark(sent_no=4, word="fourth", shown="fourth"),
               WordMark(sent_no=5, word="fifth", shown="fifth"),
               WordMark(sent_no=6, word="suggestion", shown="suggestion"),
               WordMark(sent_no=6, word="never closes", shown="never closes")],
        answer_no=5,
        override_no=6,
        override_text="The sixth sentence never closes with a practical suggestion.",
        reason="이유.")


# analyze() 는 넣은 원문을 직접 나눠 문장 수를 본다(API 를 부르기 전에).
# 그래서 테스트 지문도 문장 4개 이상이어야 한다 — 실제 사용과 같은 조건.
# 낱말이 넉넉해야 밑줄 문항 다섯(어법·짝짓기·어휘 3종)이 겹치지 않고 다 만들어진다 —
# 실제 지문도 그렇다. carefully·briefly 는 어법 밑줄이 쓰는 자리다.
_DUMMY = ("The first sentence introduces the topic clearly. "
          "However, the second sentence adds an important detail. "
          "The third sentence gives a concrete example. "
          "The fourth sentence carefully draws the whole thing together. "
          "The fifth sentence briefly answers an obvious objection. "
          "The sixth sentence closes with a practical suggestion.")
_DUMMY2 = _DUMMY.replace("sentence", "line")


class _FakeClient:
    def __init__(self, *a, **kw):
        self.efforts: list[tuple[str, str | None]] = []   # (스키마, 추론 강도)

    def structured(self, system, prompt, model_cls, max_tokens=8000,
                   max_retries=1, extra_validate=None, image_path=None,
                   cache_prefix=None, effort=None):
        self.efforts.append((model_cls.__name__, effort))
        # 부정어형 어휘는 '정답 밑줄이 부정어를 품어야' 통과한다(shape.check_negation_underline).
        if model_cls.__name__ == "VocabOut" and "부정어 삽입" in prompt:
            obj = _fake_vocab_negation()
        else:
            obj = _FAKE[model_cls.__name__]()
        if extra_validate:
            extra_validate(obj)
        return obj


def _fake_analysis() -> Analysis:
    return Analysis(
        title="Test",
        sentences=[
            "The first sentence introduces the topic clearly.",
            "However, the second sentence adds an important detail.",
            "The third sentence gives a concrete example.",
            "The fourth sentence draws the whole thing together.",
            "The fifth sentence answers an obvious objection.",
            "The sixth sentence closes with a practical suggestion.",
        ],
        main_idea="A test main idea.",
        key_terms=[KeyTerm(word="topic", synonym="subject", antonym="")],
        hardest_sentence="The fourth sentence draws the whole thing together.",
    )


_FAKE = {
    "Analysis": _fake_analysis,
    "VerifyOut": lambda: __import__("exam.verify", fromlist=["VerifyOut"]).VerifyOut(ok=True),
    "OrderOut": lambda: OrderOut(given_n=1, block_sizes=[2, 1, 1, 1], display=[3, 1, 4, 2],
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
    # 내용 O/X — O 는 정확히 2개, 나머지 X 가 축을 하나씩.
    # _DUMMY 는 47낱말이라 schemas.ox_sizes 가 영어판을 8개로 줄인다(총 18개).
    "ContentOXOut": lambda: ContentOXOut(
        korean=_fake_ox("한글 진술", 10),
        english=_fake_ox("English statement", 8)),
    # 연결어 — (A) 2번 문장 · (B) 4번 문장. 원문에 연결어가 없으니 remove 는 비운다.
    # 정답의 (A)·(B) 낱말이 오답에도 한 번씩 더 나온다 — 한 자리만 보고는 못 고른다.
    "LinkerOut": lambda: LinkerOut(
        blank_a_no=2, blank_b_no=4, remove_a="", remove_b="",
        pairs=[LinkerPair(a="However", b="Therefore"),      # 정답
               LinkerPair(a="However", b="Moreover"),       # (A) 겹침
               LinkerPair(a="In addition", b="Therefore"),  # (B) 겹침
               LinkerPair(a="In addition", b="Moreover"),
               LinkerPair(a="For example", b="Instead")],
        answer_no=1, reason="(A) 대조 · (B) 인과.",
        wrong_reasons=[WrongReason(no=2, text="(B)가 어긋남"),
                       WrongReason(no=3, text="(A)가 어긋남"),
                       WrongReason(no=4, text="둘 다 어긋남"),
                       WrongReason(no=5, text="둘 다 어긋남")]),
    # 어휘는 3종을 잇달아 만들므로, 호출마다 '겹치지 않는' 밑줄 묶음을 돌려준다
    # (실제 LLM 이 [겹침 금지] 지시를 따랐을 때의 모습).
    "VocabOut": lambda: VocabOut(
        marks=[WordMark(sent_no=n, word=w, shown=sh)
               for n, w, sh in next(_VOCAB_CYCLE)],
        answer_no=3, reason="이유."),
    # 어법(복수정답)은 '정본 지문 그대로' 위에 낸다 — 밑줄 낱말만 고른다.
    # 짝짓기·어휘 3종과 같은 지문을 쓰므로 그것들과 겹치지 않는 낱말이어야 한다.
    "GrammarOut": lambda: GrammarOut(
        marks=[WordMark(sent_no=4, word="carefully", shown="careful"),
               WordMark(sent_no=5, word="briefly", shown="brief"),
               WordMark(sent_no=6, word="sixth", shown="sixth")],
        answer_nos=[1, 2],
        reasons=[GrammarReason(no=1, text="수 일치"), GrammarReason(no=3, text="수 일치")]),
    # 밑줄 6개 중 정확히 4개가 틀린다(정답은 늘 ④)
    "GrammarCountOut": lambda: GrammarCountOut(
        rewritten=_REWRITE_B,
        marks=[WordMark(sent_no=1, word="starts", shown="start"),      # ① 오류
               WordMark(sent_no=2, word="attaches", shown="attaches"),  # ② 적절
               WordMark(sent_no=3, word="presents", shown="present"),   # ③ 오류
               WordMark(sent_no=4, word="ties", shown="tie"),           # ④ 오류
               WordMark(sent_no=5, word="meets", shown="meet"),         # ⑤ 오류
               WordMark(sent_no=6, word="ends", shown="ends")],         # ⑥ 적절
        wrong_nos=[1, 3, 4, 5],
        reasons=[GrammarReason(no=i, text="근거") for i in range(1, 7)],
        reason="틀린 것은 4개."),
    "ShortOut": lambda: ShortOut(
        q1_prompt="p1", q1_answer="한글답",
        q2_prompt="p2",
        q2_tokens=["the", "first", "sentence", "introduce", "the", "topic", "clearly"],
        q2_cues=["introduce"],
        q2_answer="The first sentence introduces the topic clearly.",  # 지문 문장과 동일
        q3_prompt="p3", q3_before="Info ", q3_mid=" is ", q3_after=" now.",
        q3_cue_a="accumulate", q3_cue_b="govern", q3_ans_a="accumulated", q3_ans_b="governs",
        q3_reason="근거."),
    # --- 추론형(B·D·E·F) 가짜 출력 -----------------------------------------
    "BOut": lambda: BOut(
        phrase="concrete example", choices=["b1", "b2", "b3", "b4", "b5"],
        answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="축자적 오독"), WrongReason(no=3, text="논지 위배"),
                       WrongReason(no=4, text="무관"), WrongReason(no=5, text="모순")]),
    "DOut": lambda: DOut(
        tokens=["the", "third", "sentence", "give", "a", "concrete", "example"],
        cues=["give"],
        answer="The third sentence gives a concrete example.",  # 지문 문장 그대로
        korean="세 번째 문장은 구체적인 예를 제시한다.",       # 이 줄이 정답 어순을 정한다
        reason="원래 배열."),
    "EOut": lambda: EOut(
        before="The passage presents its ", mid=" through a ", after=" for readers.",
        pairs=[Pair(a="topic", b="example", a_ok=True, b_ok=True),      # 정답(둘 다 맞음)
               Pair(a="topic", b="wrongword", a_ok=True, b_ok=False),
               Pair(a="wrongword", b="example", a_ok=False, b_ok=True),
               Pair(a="wrongword", b="badword", a_ok=False, b_ok=False),
               Pair(a="badword", b="wrongword", a_ok=False, b_ok=False)],
        answer_no=1, reason="이유.",
        # 오답 설명은 번호별로 받는다 — 산문에 몰아 쓰면 선지 재배열 때 번호가 밀린다
        wrong_reasons=[WrongReason(no=2, text="(B)가 어긋남"),
                       WrongReason(no=3, text="(A)가 어긋남"),
                       WrongReason(no=4, text="둘 다 어긋남"),
                       WrongReason(no=5, text="둘 다 어긋남")]),
    "PairOddOut": lambda: PairOddOut(
        # 짝짓기는 '정본 지문' 위에 낸다(어법 유형과 달리 다시 쓰지 않는다)
        # 짝짓기는 밑줄 묶음의 '첫' 문항이라, 어휘 3종과 겹치지 않는 낱말을 쓴다
        marks=[WordMark(sent_no=1, word="clearly", shown="clearly"),
               WordMark(sent_no=2, word="second", shown="seconds"),    # ⓑ 어법 오류
               WordMark(sent_no=3, word="third", shown="third"),
               WordMark(sent_no=4, word="thing", shown="nothing"),     # ⓓ 어휘 오류
               WordMark(sent_no=5, word="objection", shown="objection")],
        grammar_no=2, vocab_no=4,
        reasons=[GrammarReason(no=i, text="근거") for i in range(1, 6)],
        reason="부적절한 것은 2개."),
    "TitleOut": lambda: TitleOut(
        choices=["The First Title", "A Second Title", "Third Title Here",
                 "Fourth Title Here", "A Fifth Title"], answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="범위 비틀기"), WrongReason(no=3, text="초점 이동"),
                       WrongReason(no=4, text="근거 없음"), WrongReason(no=5, text="방향 반전")]),
    "IrrelevantOut": lambda: IrrelevantOut(
        start_no=2, answer_no=3,
        # 지문 낱말(sentence·topic·detail)을 쓰되 인과를 날조한 문장
        sentence=("The third sentence gives a detail only because the topic was "
                  "introduced by a concrete example."),
        reason="논지에 기여하지 않음.",
        wrong_reasons=[WrongReason(no=1, text="앞을 받음"), WrongReason(no=2, text="예시로 뒷받침"),
                       WrongReason(no=4, text="연결사로 이어짐"), WrongReason(no=5, text="결론으로 맺음")]),
    # 빈칸추론 정답은 '지문에 없던 표현'이어야 한다 — 가짜 출력도 그 조건을 지킨다
    "FOut": lambda: FOut(
        blank_phrase="concrete example",
        choices=["a broad summary of the argument",
                 "a vivid illustration of the claim",     # 정답 — 유의어로 바꿔 쓴 표현
                 "a formal objection to the thesis",
                 "a passing remark about the details",
                 "a numeric estimate of the total cost"],
        answer_no=2, reason="이유.",
        wrong_reasons=[WrongReason(no=1, text="모순"), WrongReason(no=3, text="무관"),
                       WrongReason(no=4, text="모순"), WrongReason(no=5, text="무관")]),
}


def test_llm_path_wiring() -> None:
    passage = build_passage_merged(_FakeClient(), _DUMMY)
    assert passage.types == set(MERGED_ORDER)
    validator.check_passage(passage, MERGED_ORDER)
    # 어휘 3종(유의어·원문단어·부정어)이 한 지문에 모두 배선된다 — 난이도와 무관하게 고정
    from exam import difficulty, pipeline as _pl
    assert _pl.VOCAB_METHODS == {"vocab": "synonym", "vocab_2": "original",
                                 "vocab_3": "negation"}, _pl.VOCAB_METHODS
    assert not hasattr(difficulty, "vocab_method")   # 난이도 레버 자체가 사라졌다
    html = renderer.render_html([passage], type_order=MERGED_ORDER,
                                prompts=MERGED_PROMPTS, labels=MERGED_LABELS)
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
    """유형 병렬 생성 + 지문 병렬 분석 + 난이도별 분석 공유가 정상 배선되는지."""
    from exam import pipeline
    from exam.merged import build_exam_merged
    tmp_out.mkdir(parents=True, exist_ok=True)

    client = _FakeClient()
    bodies = [_DUMMY, _DUMMY2]

    # 1) 지문 여러 개 병렬 분석
    analyses = pipeline.analyze_bodies(client, bodies)
    assert len(analyses) == len(bodies)

    # 2) 미리 만든 분석을 공유하며 병렬 유형 생성 → 번호 연속(1..22)
    out1 = tmp_out / "p1.pdf"
    build_exam_merged(client, bodies, out1, analyses=analyses)
    assert out1.exists()

    # 3) 같은 분석을 그대로 재사용해도 분석 API 를 다시 부르지 않는다
    out2 = tmp_out / "p2.pdf"
    build_exam_merged(client, bodies, out2, analyses=analyses)
    assert out2.exists()

    # 4) 병렬 생성 결과가 순서대로 온전히 채워졌는지
    p = build_passage_merged(client, _DUMMY, analysis=analyses[0])
    assert p.types == set(MERGED_ORDER)
    print("✓ 병렬 생성·병렬 분석·난이도별 분석 공유 통과")


def test_difficulty_lever() -> None:
    """상/중/하 레버가 분석에 지침을 심고, 모든 생성기 context 에 실려 가는지."""
    from exam import difficulty
    from exam.generators.base import context

    # 상·하는 삭제됐다 — 고를 수 있는 난이도가 없고, 남은 건 고정된 공통 지침 하나뿐
    for gone in ("normalize", "clause", "content_difficulty", "vocab_method",
                 "LEVELS", "HIGH", "LOW", "MID"):
        assert not hasattr(difficulty, gone), gone
    assert difficulty.CONTENT_DIFFICULTY == "hard"
    assert "수능 표준" in difficulty.CLAUSE
    assert "난이도" not in difficulty.CLAUSE          # 등급 표기가 남아 있지 않다

    client = _FakeClient()
    # 공통 지침은 생성 직전에 분석에 심겨 모든 유형의 프롬프트(context)에 노출된다
    a = _fake_analysis()
    a.difficulty_note = difficulty.CLAUSE
    assert "[출제 수준]" in context(a)

    seen = []

    class _Peek(_FakeClient):
        def structured(self, system, prompt, model_cls, **kw):
            seen.append(prompt)
            return super().structured(system, prompt, model_cls, **kw)

    p = build_passage_merged(_Peek(), _DUMMY)
    assert p.types == set(MERGED_ORDER)
    gen_prompts = [x for x in seen if "[문장]" in x]   # 분석·검증 호출은 제외
    assert gen_prompts and all("[출제 수준]" in x for x in gen_prompts), len(gen_prompts)
    print("✓ 출제 수준 고정(수능 표준 하나·전 유형 주입) 통과")


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

    from exam import serialize

    client = _FakeClient()
    ps1 = build_passages_merged(client, [_DUMMY, _DUMMY2], labels=["31번", "32번"])
    ps2 = build_passages_merged(client, [_DUMMY, _DUMMY2], labels=["33번", "34번"])
    ps1[0].flag("topic", ["오답 선지 근거 보강 검토 (…)"])   # 플래그도 보존되는지

    # 파트가 여러 개인 저장본(옛 난이도별 합본 등)도 그대로 왕복되는지 함께 본다
    part_meta = [
        {"set": "M", "tag": "변형문제",
         "sections": ["student", "answers"], "passages": ps1},
        {"set": "M", "tag": "변형문제 (2교시)",
         "sections": ["student", "answers"], "passages": ps2},
    ]
    payload = serialize.dump_parts(part_meta, header="원래학원", doc_name="Unit1")
    # 실제 저장처럼 문자열 왕복
    data = _json.loads(_json.dumps(payload, ensure_ascii=False))

    # 1) 문항 HTML·제목·라벨·플래그가 그대로 보존
    p0 = data["parts"][0]["passages"][0]
    assert set(p0["q"]) == set(MERGED_ORDER) and set(p0["a"]) == set(MERGED_ORDER)
    assert p0["source_label"] == "31번"
    assert p0["flags"]["topic"]                     # 플래그 보존
    assert data["parts"][1]["set"] == "M"

    # 2) 머리글 교체 복원 → header_note 에 새 제목이 실린다(재분석 없음)
    parts, meta = serialize.load_parts(data, header_override="새학원 4월")
    assert len(parts) == 2 and meta["n_parts"] == 2
    assert parts[0]["header_note"] == "변형문제 — 새학원 4월"
    assert tuple(parts[1]["type_order"]) == MERGED_ORDER    # 통합 조판 메타 복원
    assert parts[0]["passages"][0].source_label == "31번"

    # 3) 머리글 미지정이면 저장된 값 유지
    parts_keep, _ = serialize.load_parts(data)
    assert parts_keep[0]["header_note"].endswith("원래학원")

    # 3-b) 옛 '1회/2회'로 저장해 둔 결과 JSON도 그대로 재출력된다(생성은 못 해도 조판은 가능)
    from exam.demo2 import demo_passages_2
    from exam.set2 import TYPE_ORDER2
    from exam.types import TYPE_ORDER
    legacy = serialize.dump_parts(
        [{"set": "1", "tag": "변형문제 1회", "sections": ["student"],
          "passages": demo_passages()},
         {"set": "2", "tag": "변형문제 2회", "sections": ["student"],
          "passages": demo_passages_2()}], header="옛자료")
    lparts, _ = serialize.load_parts(_json.loads(_json.dumps(legacy, ensure_ascii=False)))
    assert len(lparts) == 2
    assert tuple(lparts[0]["type_order"]) == tuple(TYPE_ORDER)
    assert tuple(lparts[1]["type_order"]) == tuple(TYPE_ORDER2)

    # 4) 실제로 재렌더되는지(무API)
    tmp_out.mkdir(parents=True, exist_ok=True)
    out = tmp_out / "rerender.pdf"
    renderer.render_pdf_multi(parts, out)
    assert out.exists() and out.stat().st_size > 2000

    # 5) 손상 검증: 유형 누락이면 친절한 오류
    broken = _json.loads(_json.dumps(payload, ensure_ascii=False))
    broken["parts"][0]["passages"][0]["q"].pop(MERGED_ORDER[0])
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
    """한 유형이 끝내 생성 실패해도(예: 선지 개수 오류) 지문 전체를 버리지 않고
    나머지 문항으로 출력한다(graceful degradation). 번호는 남은 문항 기준 연속."""
    from exam.demo2 import demo_passages_2
    from exam.set2 import TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
    ps = demo_passages_2()
    dropped = TYPE_ORDER2[1]         # 한 슬롯이 생성 실패한 상황
    del ps[0].q[dropped]
    del ps[0].a[dropped]
    n_full = len(TYPE_ORDER2)
    assert len(validator.present_types(ps[0], TYPE_ORDER2)) == n_full - 1
    validator.validate_passages(ps, TYPE_ORDER2)             # 부분 허용 통과
    nums = validator.validate_numbering(ps, 1, TYPE_ORDER2)
    assert nums[0] == list(range(1, n_full)), nums           # 7 → 6, 연속
    html = renderer.render_html(ps, type_order=TYPE_ORDER2, prompts=TYPE_PROMPTS2,
                                labels=TYPE_LABELS2, group_by="type")
    assert "quick-grid" in html
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
    ps = build_passages_merged(client, [_DUMMY, _DUMMY2, _DUMMY, _DUMMY2])
    keys = []
    for i, p in enumerate(ps):
        _, quick = renderer._blocks([p], start=1, group_by="passage")
        cells = quick[0]["cells"]        # 지문별: 머리 없는 한 묶음
        for t, cell in zip(MERGED_ORDER, cells):
            if t in ("topic", "content"):
                keys.append(cell["key"])
    assert len(set(keys)) >= 2, keys               # 한 번호로 몰리지 않음
    print("✓ 정답 위치 분산(재배열·오답근거 재매핑·몰림 방지) 통과")


def test_passage_source_label() -> None:
    """지문 라벨: 원본 문항번호가 있으면 '31번', 없으면 위치 기준 '지문 i'.

    유형별 편성(기본)에서는 지문이 섞이므로 문항마다 출처를 달고,
    지문별 편성에서는 지문 블록 머리에 [ ] 로 단다.
    """
    # 라벨 없음 → 위치 기준
    html0 = renderer.render_html(demo_passages(), group_by="passage")
    assert "[지문 1]" in html0 and "[지문 2]" in html0

    # source_label 지정 → 문항번호로 표기(위치 라벨은 사라짐)
    ps = demo_passages()
    ps[0].source_label = "31번"
    ps[1].source_label = "32번"
    html = renderer.render_html(ps, group_by="passage")
    assert "[31번]" in html and "[32번]" in html
    assert "[지문 1]" not in html and "[지문 2]" not in html

    # 일부만 번호가 있으면, 없는 지문은 위치 기준(i)으로 대체
    ps2 = demo_passages()
    ps2[0].source_label = "31번"          # 1번째만 번호
    html2 = renderer.render_html(ps2, group_by="passage")
    assert "[31번]" in html2 and "[지문 2]" in html2

    # 유형별 편성: 문항마다 출처 알약이 붙는다(문제·해설 양쪽)
    by_type = renderer.render_html(ps)
    assert by_type.count('class="q-src"') >= 2
    assert '<span class="q-src">31번</span>' in by_type
    assert '<span class="q-src">32번</span>' in by_type

    # 라벨 스레딩: build_passages(labels=…) 가 Passage.source_label 에 실린다
    client = _FakeClient()
    ps3 = build_passages_merged(client, [_DUMMY, _DUMMY2], labels=["45번", "46번"])
    assert [p.source_label for p in ps3] == ["45번", "46번"]
    print("✓ 지문 라벨(원본 문항번호·위치 폴백·labels 스레딩) 통과")


def test_review_flags_and_page(tmp_out: Path = ROOT / "output" / "test") -> None:
    """검토 메모: 자동 점검이 필요한 문항을 맨 끝 별도 페이지로 모은다."""
    from pypdf import PdfReader

    from exam import review

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

    # 3) collect_review — 문서 연속 번호로 정확히 매긴다
    #    문항 번호는 지문 경계를 넘어 문서 전체로 이어진다(둘째 지문 = +유형 수).
    def _fresh():
        return build_passages_merged(_FakeClient(), [_DUMMY, _DUMMY2])

    _i = {t: i + 1 for i, t in enumerate(MERGED_ORDER)}   # 유형 → 지문 내 문항 번호
    ps = _fresh()
    ps[0].flag("topic", [review.FIX_ORDER])
    ps[0].flag("grammar", ["오답 근거 약함: …"])
    ps[1].flag("D", [review.FIX_SNAP])                    # 둘째 지문 → +유형 수
    items = renderer.collect_review(ps, start=1, type_order=MERGED_ORDER,
                                    labels=MERGED_LABELS, group_by="passage")
    by_no = {it["no"]: it for it in items}
    assert review.FIX_ORDER in by_no[_i["topic"]]["reasons"]
    assert "오답 근거 약함: …" in by_no[_i["grammar"]]["reasons"]
    assert by_no[_i["grammar"]]["label"] == "어법"
    n_last = _i["D"] + len(MERGED_ORDER)                  # 둘째 지문의 어순 배열
    assert review.FIX_SNAP in by_no[n_last]["reasons"]
    assert by_no[n_last]["label"] == "어순 배열"
    assert max(by_no) == 2 * len(MERGED_ORDER), sorted(by_no)   # 지문 2개 × 유형 수

    #    유형별 편성(기본)에서는 유형마다 1번부터 — 조판 번호와 어긋나면 안 된다
    by_type = renderer.collect_review(ps, start=1, type_order=MERGED_ORDER,
                                      labels=MERGED_LABELS)
    got = {(it["label"], it["no"]) for it in by_type if it["no"] != "-"}
    assert ("주제", 1) in got and ("어순 배열", 2) in got, got

    # 4) 교사용이면 맨 끝에 '검토 메모' 페이지가 붙고, 학생용만이면 붙지 않는다
    tmp_out.mkdir(parents=True, exist_ok=True)
    _M = dict(type_order=MERGED_ORDER, prompts=MERGED_PROMPTS, labels=MERGED_LABELS)
    out = renderer.render_pdf(ps, tmp_out / "rv_teacher.pdf", **_M)
    r = PdfReader(str(out))
    assert "검토 메모" in (r.pages[-1].extract_text() or "")
    out_s = renderer.render_pdf(ps, tmp_out / "rv_student.pdf", sections=["student"], **_M)
    rs = PdfReader(str(out_s))
    joined = " ".join((pg.extract_text() or "") for pg in rs.pages)
    assert "검토 메모" not in joined                     # 학생용에는 노출 안 함

    # 5) 플래그가 하나도 없으면 페이지 자체가 없다(정상 문항만 있는 경우)
    clean = demo_passages_merged()      # 데모는 오답 근거가 충분해 플래그가 없다
    assert renderer.collect_review(clean, start=1, type_order=MERGED_ORDER,
                                   labels=MERGED_LABELS) == []

    # 6) 합본(render_pdf_multi): 여러 파트의 권장 문항을 '단 한 장'으로 모은다
    p1 = _fresh(); p1[0].flag("topic", [review.FIX_ORDER])
    p2 = _fresh(); p2[0].flag("grammar", ["오답 근거 약함"])
    parts = [
        {"passages": p1, "header_note": "변형문제 · 난이도 중",
         "sections": ["teacher", "answers"], **_M},
        {"passages": p2, "header_note": "변형문제 · 난이도 상",
         "sections": ["teacher", "answers"], **_M},
    ]
    outm = tmp_out / "rv_multi.pdf"
    ret = renderer.render_pdf_multi(parts, outm)
    assert ret is None                                  # 별도 파일 아님 → None
    rm = PdfReader(str(outm))
    texts = [pg.extract_text() or "" for pg in rm.pages]
    titled = [i for i, t in enumerate(texts) if "검토 메모" in t]
    assert len(titled) == 1, titled                     # 제목은 한 번만(한 덩어리)
    # 검토 메모가 시작된 뒤로는 본문이 다시 나오지 않는다 — 맨 뒤에 붙는다
    assert not any("교사용" in t or "해설지" in t for t in texts[titled[0]:]), titled

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


def test_progress_output() -> None:
    """진행 상황: 지문이 하나 끝날 때마다 '완료 개수·경과·남은 예상'을 한 줄씩 찍는다."""
    import io as _io

    from exam.progress import NullProgress, Progress, human

    assert human(0) == "0초" and human(75) == "1분 15초" and human(7920) == "2시간 12분"

    buf = _io.StringIO()
    prog = Progress(total=4, stream=buf)
    prog.note("지문 2개 분석 중 …")
    build_passages_merged(_FakeClient(), [_DUMMY, _DUMMY2],
                            progress=prog, part_label="변형문제 1회 · 난이도 중")
    build_passages_merged(_FakeClient(), [_DUMMY, _DUMMY2],
                            progress=prog, part_label="변형문제 1회 · 난이도 상")
    prog.finish()
    out = buf.getvalue()
    lines = [x for x in out.splitlines() if x.strip()]
    assert lines[0].startswith("  ▶") and "분석" in lines[0], lines[0]
    assert len([x for x in lines if x.startswith("  ✓")]) == 4, out
    assert "[1/4]" in out and "[4/4]" in out, out          # 진행률
    assert "난이도 중" in out and "난이도 상" in out, out    # 파트 구분
    assert "경과" in out and "남은 예상" in out, out          # 경과·ETA
    assert lines[-1].startswith("  ★") and "총 소요" in lines[-1], lines[-1]

    # 데모·테스트용 NullProgress 는 아무것도 찍지 않는다
    quiet = _io.StringIO()
    np = NullProgress()
    np._stream = quiet
    np.note("x")
    np.step("y")
    assert quiet.getvalue() == ""
    print("✓ 진행 상황 표시(완료 개수·경과·남은 예상) 통과")


def test_parallel_passages_and_gate() -> None:
    """속도: 지문끼리도 동시에 생성하되(순서·라벨은 보존), 실제 동시 API 호출 수는
    전체 상한으로 묶여 레이트리밋을 넘지 않는다."""
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    from exam import _concurrent

    # ① 지문 병렬 처리 — 순서·라벨이 입력 순서대로 유지된다
    bodies = [_DUMMY.replace("sentence", f"line{i}") for i in range(6)]
    labels = [f"L{i}" for i in range(6)]
    ps = build_passages_merged(_FakeClient(), bodies, labels=labels)
    assert [p.source_label for p in ps] == labels, [p.source_label for p in ps]
    assert len(ps) == len(bodies)

    # ② 전체 동시 호출 상한 — 스레드를 아무리 많이 띄워도 상한을 넘지 않는다
    import src.client as _sc
    orig_structured, orig_init = _sc.ClaudeClient.structured, _sc.ClaudeClient.__init__
    stat = {"cur": 0, "peak": 0}
    lock = threading.Lock()

    def _fake(self, *a, **kw):
        with lock:
            stat["cur"] += 1
            stat["peak"] = max(stat["peak"], stat["cur"])
        time.sleep(0.02)
        with lock:
            stat["cur"] -= 1
        return "ok"

    _sc.ClaudeClient.structured = _fake
    _sc.ClaudeClient.__init__ = lambda self, *a, **kw: None
    saved = _concurrent.API_CONCURRENCY
    try:
        from exam.llm import ClaudeClient
        for want in (3, 9):
            applied = _concurrent.set_concurrency(want)
            stat["peak"] = 0
            c = ClaudeClient()
            with ThreadPoolExecutor(max_workers=40) as ex:
                list(ex.map(lambda _i: c.structured("s", "p", None), range(30)))
            assert applied == want, (applied, want)
            assert 0 < stat["peak"] <= want, (stat["peak"], want)
    finally:
        _sc.ClaudeClient.structured, _sc.ClaudeClient.__init__ = orig_structured, orig_init
        _concurrent.set_concurrency(saved)
    print("✓ 지문 병렬 생성(순서 보존)·동시 호출 상한 통과")


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

    # ② 시드는 지문 내용에만 달렸다 — 난이도는 정답 위치에 영향을 주지 않는다
    t1, t2 = "단일경작과 승자들", "함께하려는 인간의 욕구"
    assert A.seed_of(t1) != A.seed_of(t2), "지문이 다르면 시드도 달라야 한다"
    assert A.seed_of(t1) == A.seed_of(t1), "같은 지문이면 항상 같은 시드(프로세스 무관)"
    import inspect
    assert "level" not in inspect.signature(A.seed_of).parameters   # 난이도 오프셋 제거됨

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
                                  "out_mode": "each", "group_by": "type"},
               content_type="multipart/form-data")
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "생성 전 확인" in html, r.status_code
    m = _re.search(r'name="precheck_ack" value="([0-9a-f]+)"', html)
    assert m, "ack 토큰 없음"
    assert 'name="out_mode" value="each"' in html           # 고른 옵션 보존
    assert 'name="group_by" value="type"' in html
    assert webmod._stash_path(m.group(1)).exists()          # 재업로드 없이 재사용할 지문 저장
    r2 = c.post("/generate", data={"passages": clean, "api_key": "sk-ant-test"},
                content_type="multipart/form-data")
    assert "생성 전 확인" not in r2.get_data(as_text=True)   # 깨끗하면 바로 진행
    print("✓ 사전 점검 하니스(정본 오염 사전 차단·오탐 없음·웹앱 경고) 통과")

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

    # 렌더 PDF 에 실제로 10-A/11-A 출처가 찍히고 기본 '지문 1' 은 사라진다
    parts, _ = serialize.load_parts(d_ok, header_override="h")
    for pt in parts:                      # 지문 라벨은 지문별 편성에서 대괄호로 찍힌다
        pt["group_by"] = "passage"
    tmp_out.mkdir(parents=True, exist_ok=True)
    out = tmp_out / "relabel.pdf"
    renderer.render_pdf_multi(parts, out)
    txt = " ".join((pg.extract_text() or "") for pg in PdfReader(str(out)).pages)
    assert "[10-A]" in txt and "[11-A]" in txt and "[지문 1]" not in txt

    # 유형별 편성(기본)에서는 문항마다 출처가 붙는다
    parts2, _ = serialize.load_parts(d_ok, header_override="h")
    out2 = tmp_out / "relabel_type.pdf"
    renderer.render_pdf_multi(parts2, out2)
    txt2 = " ".join((pg.extract_text() or "") for pg in PdfReader(str(out2)).pages)
    assert "10-A" in txt2 and "11-A" in txt2 and "지문 1" not in txt2
    print("✓ 재출력 지문 번호 다시 넣기(순서대로 라벨 교체·개수검증) 통과")


def test_merged_set(tmp_out: Path = ROOT / "output" / "test") -> None:
    """변형문제(통합본): 수능 출제 유형을 한 벌로 덮는 15문항.

    옛 1회+2회에서 겹치던 3유형(A·C·G)은 빼고, 비어 있던 제목·무관한 문장을 더했다.
    어휘는 세 방식(유의어형·원문단어형·부정어형)을 난이도와 무관하게 모두 낸다.
    빠진 유형은 생성 호출조차 하지 않으므로 비용이 실제로 준다."""
    import threading as _th

    from pypdf import PdfReader

    from exam import gen2, pipeline, serialize, verify as _v
    from exam.merged import EXCLUDED
    from exam.set2 import TYPE_ORDER2
    from exam.types import TYPE_ORDER

    # ① 구성 — 17문항, 중복 3유형 제외, 옛 두 세트의 나머지는 하나도 안 빠졌다
    assert len(MERGED_ORDER) == 17, MERGED_ORDER
    assert len(set(MERGED_ORDER)) == 17                    # 같은 슬롯이 두 번 나오지 않는다
    assert set(EXCLUDED) == {"A", "C", "G"}, EXCLUDED
    # 옛 A(짝짓기)는 pair_odd 로 되살렸다 — 뺐던 3유형 중 유일하게 되돌아온 것
    assert "pair_odd" in MERGED_ORDER
    # 새로 만든 슬롯키(옛 A 는 pair_odd 라는 새 키로 다시 들였다)
    _added = {"title", "linker", "vocab_2", "vocab_3", "grammar_fix", "pair_odd",
              "content_2"}
    _dropped = {"short_answer"}          # 어순 배열·요약문과 겹쳐 뺐다
    assert (set(TYPE_ORDER) | set(TYPE_ORDER2)
            == (set(MERGED_ORDER) - _added) | set(EXCLUDED) | _dropped)
    for t in MERGED_ORDER:                                  # 발문·라벨이 모두 있다
        assert MERGED_PROMPTS.get(t) and MERGED_LABELS.get(t), t
    # 배열은 수능 순서를 따른다(주제만 함의추론 앞으로 당김) — 뒤로 갈수록 어려워진다
    assert MERGED_ORDER == ("topic", "title", "B", "content", "content_2",
                            "grammar", "grammar_fix", "pair_odd",
                            "vocab_2", "vocab", "vocab_3", "F", "linker",
                            "order", "insert", "E", "D"), MERGED_ORDER
    # 어법 두 문항은 발문이 서로 달라야 한다(같은 문제를 두 번 내는 것이 아니다)
    assert MERGED_PROMPTS["grammar"] != MERGED_PROMPTS["grammar_fix"]
    assert "고쳐 쓰시오" in MERGED_PROMPTS["grammar_fix"]
    #    내용 일치는 O/X, 무관한 문장 자리는 연결어가 대신한다
    assert "O, 일치하지 않으면 X" in MERGED_PROMPTS["content"]
    assert "(A), (B)" in MERGED_PROMPTS["linker"]
    #    내용 O/X 는 한글판·영어판 두 문항이고 발문이 서로 다르다
    assert MERGED_PROMPTS["content"] != MERGED_PROMPTS["content_2"]
    assert "Write O" in MERGED_PROMPTS["content_2"]
    assert MERGED_ORDER[-1] == "D"                          # 서술형 계열은 맨 뒤
    # 서술형은 뺐다 — (2)는 어순 배열과, (3)은 요약문과 과제가 똑같았다
    assert "short_answer" not in MERGED_ORDER
    from exam import pipeline as _pl
    assert "short_answer" not in _pl.GENERATORS            # 생성 경로도 없다
    # 어휘 3종은 발문이 같고 라벨도 '어휘'로 같다(문제 만드는 방식만 다르다)
    _v3 = ("vocab_2", "vocab", "vocab_3")
    assert len({MERGED_PROMPTS[t] for t in _v3}) == 1
    assert {MERGED_LABELS[t] for t in _v3} == {"어휘"}
    # 뺀 유형은 '대신할 유형'이 통합본 안에 실제로 있어야 한다(능력 공백 없음)
    for gone, kept in EXCLUDED.items():
        assert kept in MERGED_ORDER, (gone, kept)

    # ② 빠진 유형은 API 호출조차 하지 않는다 — 비용 절감이 실제로 일어나는 지점
    seen, lock = {}, _th.Lock()

    class _Counting(_FakeClient):
        def structured(self, system, prompt, model_cls, **kw):
            with lock:
                seen[model_cls.__name__] = seen.get(model_cls.__name__, 0) + 1
            return super().structured(system, prompt, model_cls, **kw)

    ps = build_passages_merged(_Counting(), [_DUMMY, _DUMMY2], labels=["10-1", "10-2"])
    assert "AOut" not in seen and "GOut" not in seen, seen      # A·G 생성 안 함
    assert seen.get("GrammarOut") == 2, seen                    # 어법(모두 고르기) 지문당 1번
    assert seen.get("GrammarCountOut") == 2, seen               # 어법 서술형 지문당 1번
    assert seen.get("VocabOut") == 6, seen                      # 어휘는 지문당 3번(3종)
    assert seen.get("TitleOut") == 2 and seen.get("LinkerOut") == 2, seen
    #    내용 O/X 는 한 호출로 한글판·영어판 두 문항을 만든다(호출은 지문당 1번)
    assert seen.get("ContentOXOut") == 2, seen
    assert seen.get("VerifyOut") == 22, seen                    # 자기검증 지문당 11회

    # ③ 지문마다 17문항이 순서대로, 라벨도 보존된다
    assert [p.source_label for p in ps] == ["10-1", "10-2"]
    for p in ps:
        assert list(p.q) == list(MERGED_ORDER), list(p.q)

    # ④-a 지문별 조판 — 번호가 지문을 넘어 이어진다(지문 2개 × 16 = 32번까지)
    tmp_out.mkdir(parents=True, exist_ok=True)
    out = tmp_out / "merged.pdf"
    renderer.render_pdf(ps, out, header_note="통합", group_by="passage",
                        type_order=MERGED_ORDER, prompts=MERGED_PROMPTS, labels=MERGED_LABELS)
    txt = " ".join((pg.extract_text() or "") for pg in PdfReader(str(out)).pages)
    assert "[10-1]" in txt and "[10-2]" in txt, txt[:400]
    _last = 2 * len(MERGED_ORDER)
    assert f"{_last}." in txt, f"마지막 문항 번호({_last})가 없다"

    # ④-b 유형별 조판(기본) — 유형마다 새 쪽에서 시작하고 큰 제목이 붙는다
    out_t = tmp_out / "merged_type.pdf"
    renderer.render_pdf(ps, out_t, header_note="통합", sections=["student"],
                        type_order=MERGED_ORDER, prompts=MERGED_PROMPTS, labels=MERGED_LABELS)
    pages = PdfReader(str(out_t)).pages
    #    학생용만 뽑았으므로 쪽 수 = 유형 수(유형마다 한 쪽부터 시작)
    assert len(pages) >= len(MERGED_ORDER), len(pages)
    heads = [(pg.extract_text() or "").strip().splitlines()[:3] for pg in pages]
    #    각 유형의 이름이 그 유형 첫 쪽 머리에 칩으로 찍혀 있다
    for t in MERGED_ORDER:
        name = MERGED_LABELS[t]
        assert any(any(name in ln and "문항" in ln for ln in h) for h in heads), name
    #    출처는 문항마다 붙는다
    txt_t = " ".join((pg.extract_text() or "") for pg in pages)
    assert "10-1" in txt_t and "10-2" in txt_t

    # ⑤ JSON 저장→복원 재출력(무API)에서도 통합 유형표가 그대로 살아난다
    data = serialize.dump_parts([{"set": "M", "tag": "변형문제 · 난이도 중",
                                  "sections": ["student"], "passages": ps}], header="h")
    parts, _ = serialize.load_parts(data, header_override="h")
    assert tuple(parts[0]["type_order"]) == MERGED_ORDER

    # ⑥ 데모(무료 미리보기)도 통합본으로 나온다
    dps = demo_passages_merged()
    assert dps and all(list(p.q) == list(MERGED_ORDER) for p in dps)
    validator.validate_passages(dps, MERGED_ORDER)
    validator.validate_numbering(dps, 1, MERGED_ORDER)

    # ⑦ 뺀 유형은 생성기 자체가 없다 — '실수로 다시 켜지는' 경로가 남지 않았다
    assert set(gen2._GENERATORS2) == {"B", "D", "E", "F"}, sorted(gen2._GENERATORS2)
    assert not hasattr(gen2, "build_passages2") and not hasattr(gen2, "_gen_A")
    assert not hasattr(pipeline, "build_passages")      # 1회 전용 경로도 없다
    _bases = {pipeline._base(t) for t in MERGED_ORDER}
    assert set(pipeline.GENERATORS) | set(gen2._GENERATORS2) == _bases

    # ⑧ 웹앱 — 세트 선택 없이 통합본 하나로만 나온다
    from web import app as webmod
    webmod.app.config["PREVIEW_ONLY"] = True
    cli = webmod.app.test_client()
    home = cli.get("/").get_data(as_text=True)
    assert 'name="sets"' not in home, "세트 선택이 아직 남아 있다"
    assert "17문항" in home
    r = cli.post("/generate", data={"action": "demo",
                                    "sections": ["student", "answers"]})
    assert r.status_code == 200, r.status_code
    page = r.get_data(as_text=True)
    import re as _re
    assert _re.search(r"/pdf/[0-9a-f]+", page)
    assert "변형문제 1회" not in page and "변형문제 2회" not in page

    # 고위험 자기검증 대상도 통합본 유형만 남는다(C·G 몫이 사라짐)
    assert len([t for t in MERGED_ORDER if _v._base_key(t) in _v.HIGH_RISK]) == 11
    # 짝짓기는 '밑줄 묶음' 안에서 만들어지지만 자기검증은 빠뜨리지 않는다
    assert "pair_odd" in _v.HIGH_RISK
    print("✓ 변형문제 통합본(17문항·제목·연결어·어휘3종·어법2종·짝짓기)·조판·재출력 통과")


def test_new_type_guards() -> None:
    """새 유형의 '무너지는 지점'을 코드가 직접 막는지.

    ① 제목 — 선지 5개가 제목 형식으로 통일됐는가(하나만 서술문이면 답이 티 난다)
    ② 어휘 3종 — 세 문제의 밑줄이 겹치지 않는가
    ③ 연결어 — 빈칸 자리와 지울 연결어가 지문과 맞는가
    """
    from exam.generators.title import check_title_form as chk_title

    # ① 제목 형식 통일 -------------------------------------------------------
    good = ["The Molecule That Outlasts Our Machines",
            "Why Cold Storage Beats Every Other Archive",
            "Reading the Genes of Ancient Animals",
            "Cheaper Chips, Shorter Memories",
            "A Warning Against Trusting Digital Records"]
    assert chk_title(good) == [], chk_title(good)
    # 하나만 서술문(마침표로 끝남) → 잡힌다
    assert any("마침표" in b for b in
               chk_title(good[:4] + ["DNA can store a great amount of data in a tiny space."]))
    # 하나만 소문자 → 잡힌다
    assert any("Title Case" in b for b in
               chk_title(good[:4] + ["a warning against trusting digital records"]))
    assert chk_title(good[:4] + ["DNA"])          # 한 낱말짜리
    assert chk_title(good[:4] + [good[0]])        # 같은 선지 두 번
    # 갈래 표지(물음표·콜론)를 섞으면 그 하나가 곧 답으로 보인다
    assert any("물음표" in b for b in chk_title(good[:4] + ["Is Silicon Really the Future?"]))
    assert any("콜론" in b for b in chk_title(good[:4] + ["Monoculture: The Hidden Cost"]))
    # 의문형으로 통일한 경우는 통과해야 한다(오탐 없음)
    q5 = ["Why Do Cells Keep Their Secrets?", "Can a Molecule Outlast a Machine?",
          "What Makes DNA So Durable?", "Where Should We Store Our Memories?",
          "Is Silicon Really the Future?"]
    assert chk_title(q5) == [], chk_title(q5)

    # ② 어휘 3종 밑줄 겹침 금지 ----------------------------------------------
    marks = {}

    class _Watch(_FakeClient):
        def structured(self, system, prompt, model_cls, **kw):
            obj = super().structured(system, prompt, model_cls, **kw)
            if model_cls.__name__ == "VocabOut":
                marks[len(marks)] = ({m.word.lower() for m in obj.marks}, prompt)
            return obj

    p = build_passage_merged(_Watch(), _DUMMY)
    assert {"vocab", "vocab_2", "vocab_3"} <= p.types, sorted(p.types)
    sets = [w for w, _ in marks.values()]
    assert len(sets) == 3, len(sets)
    for i in range(len(sets)):                     # 어느 두 문제도 낱말을 공유하지 않는다
        for j in range(i + 1, len(sets)):
            assert not (sets[i] & sets[j]), (sets[i] & sets[j])
    # 둘째·셋째 요청에는 '피할 낱말'이 실제로 실려 갔다
    later = [pr for _, pr in list(marks.values())[1:]]
    assert all("[겹침 금지]" in pr for pr in later), later
    # 세 문제의 밑줄 표시가 실제로 다르다(같은 문제가 세 번 나오지 않는다)
    assert len({p.q["vocab"], p.q["vocab_2"], p.q["vocab_3"]}) == 3

    # ③ 요약문 — 정답은 긍정형, 부정은 요약문 문장 쪽에 -------------------
    from exam.gen2 import Pair as _Pair
    from exam.shape import check_summary_answer_polarity as chk_pol
    from exam.shape import check_summary_pairs as chk_sum

    def _pair(a, b):
        return _Pair(a=a, b=b, a_ok=True, b_ok=True)

    # 정답이 '그 자체로 부정을 품은 낱말'이면 거절 → 문장에 not 을 넣고 긍정형으로
    for neg in ("unlikely", "impossible", "insufficient", "irrelevant", "useless"):
        assert chk_pol([_pair(neg, "retain")], 1), neg
    # 오답이 부정형인 것은 정상(정답의 자연스러운 짝이다)
    assert chk_pol([_pair("likely", "retain"), _pair("unlikely", "lose")], 1) == []
    # 형태만 비슷한 멀쩡한 낱말은 걸리지 않는다
    assert chk_pol([_pair("unique", "important")], 1) == []
    assert chk_pol([_pair("increase", "distinct")], 1) == []
    assert chk_pol([_pair("invaluable", "indeed")], 1) == []
    # 전체 검사에도 물려 있다
    bad_sum = [_pair("unlikely", "retain"), _pair("unlikely", "lose"),
               _pair("likely", "retain"), _pair("likely", "lose"),
               _pair("likely", "retain")]
    assert any("부정 의미" in b for b in chk_sum(bad_sum, 1)), chk_sum(bad_sum, 1)

    # ④ 어법·어휘 짝짓기 — 짝 선지는 코드가 만든다 ------------------------
    from exam.generators.pair_odd import build_pairs
    from exam.format2 import cletter
    for a, b in ((2, 4), (1, 5), (3, 4)):
        for seed in range(6):
            ch, no = build_pairs(a, b, seed=seed)
            assert len(ch) == 5 and len(set(ch)) == 5, ch     # 짝 5개가 서로 다르다
            want = {cletter(a), cletter(b)}
            hit = [c for c in ch if want <= set(c)]
            assert hit == [ch[no - 1]], (ch, no)              # 정답 짝은 정확히 하나
            # 오답 중 3개는 '정답 둘 중 하나만' 포함 — 하나만 찾아서는 못 고른다
            half = [c for c in ch if len(want & set(c)) == 1]
            assert len(half) == 3, ch

    # ⑤ 연결어 --------------------------------------------------------------
    import re as _re2

    from exam import build2 as _B2
    lsents = ["First sentence sets the scene.", "However, the second turns.",
              "A third adds detail.", "Therefore, the fourth concludes."]
    pairs = [("However", "Therefore"), ("Moreover", "However"), ("Thus", "Moreover"),
             ("In contrast", "Similarly"), ("For example", "Instead")]
    q, _a = _B2.make_linker(lsents, 2, 4, "However,", "Therefore,", pairs, 1, "이유",
                            {2: "a", 3: "b", 4: "c", 5: "d"})
    plain = _re2.sub(r"<[^>]+>", " ", q)
    assert q.count('class="blank"') == 2                    # (A)·(B) 두 자리
    assert "However" not in plain.split("①")[0]             # 지문에서 지워졌다
    assert "Therefore" not in plain.split("①")[0]
    assert "The second turns" in plain                       # 연결어를 뗀 뒤 첫 글자 대문자
    #    지울 연결어가 그 문장에 실제로 없으면 문항이 어긋난 것 — 거절한다
    for args in (("Moreover,", "Therefore,"), ("However,", "Thus,")):
        try:
            _B2.make_linker(lsents, 2, 4, *args, pairs=pairs, answer_no=1,
                            reason="이유", wrong={2: "a", 3: "b", 4: "c", 5: "d"})
        except ValueError:
            pass
        else:
            raise AssertionError(f"{args} 가 통과되면 안 된다")
    #    첫 문장에는 연결어 자리를 두지 않는다(앞에 이어받을 글이 없다)
    try:
        _B2.make_linker(lsents, 1, 3, "", "", pairs, 1, "이유",
                        {2: "a", 3: "b", 4: "c", 5: "d"})
    except ValueError:
        pass
    else:
        raise AssertionError("첫 문장 빈칸이 통과되면 안 된다")
    print("✓ 새 유형 안전장치(제목 형식·어휘 밑줄 겹침·요약문 정답 긍정형·연결어) 통과")


def test_tiering_and_escalation() -> None:
    """비용은 줄이고 판단력은 지키는 두 장치.

    ① 유형별 추론 강도 — 판단이 걸린 유형만 high, 나머지는 medium, 검수는 항상 high
    ② 모델 승격 — 값싼 모델로 다 만들고, 검수에 걸린 문항만 좋은 모델로 다시 만든다
    """
    from exam import tiering
    from exam.merged import MERGED_ORDER, build_passage_merged

    # ① 강도 배분 ------------------------------------------------------------
    assert tiering.effort_for("linker") == "high"         # 두 자리가 바꿔 써지면 복수정답
    assert tiering.effort_for("F") == "high"              # 빈칸 유일성
    assert tiering.effort_for("insert") == "high"
    assert tiering.effort_for("grammar") == "high"        # 다시 쓴 지문 위에 내므로 부담이 크다
    assert tiering.effort_for("grammar_fix") == "high"    # 고칠 방법이 하나뿐이어야 한다
    assert tiering.effort_for("content") == "high"        # O/X 다섯을 모두 확정해야 한다
    assert tiering.effort_for("vocab") == "medium"        # 형식은 코드가 본다
    assert tiering.effort_for("vocab_3") == "medium"      # 슬롯키도 base 로 판정
    assert tiering.effort_for("title") == "medium"
    assert tiering.VERIFY_EFFORT == "high"                # 마지막 문지기

    c = _FakeClient()
    p = build_passage_merged(c, _DUMMY)
    by_schema = dict(c.efforts)
    assert by_schema["LinkerOut"] == "high", c.efforts
    assert by_schema["VocabOut"] == "medium", c.efforts
    assert by_schema["TitleOut"] == "medium", c.efforts
    assert by_schema["VerifyOut"] == "high", c.efforts    # 검수는 강도를 안 낮춘다
    # 분석은 유형 단위가 아니므로 강도를 얹지 않는다(클라이언트 기본값 사용)
    assert by_schema["Analysis"] is None, c.efforts

    # ② 승격 대상 판정 -------------------------------------------------------
    from exam import review as _rv
    assert tiering.needs_escalation(["자동검증: 복수정답 소지"])       # 결함 의심 → 다시
    assert tiering.needs_escalation([_rv.FIX_INSERT])                  # 자동 보정 → 다시
    assert not tiering.needs_escalation(["오답 선지 근거 보강 검토 (4개 중 1개)"])  # 참고용
    assert not tiering.needs_escalation([]) and not tiering.needs_escalation(None)

    p.flags.clear()
    p.flag("F", ["자동검증: 정답이 둘로 읽힌다"])
    del p.q["insert"], p.a["insert"]                       # 아예 못 만든 문항
    p.flag("topic", ["오답 선지 근거 보강 검토 (…)"])        # 참고용 → 승격 대상 아님
    assert set(tiering.escalation_targets(p, MERGED_ORDER)) == {"F", "insert"}

    # ③ 승격이 실제로 상위 모델만 부르는지 -----------------------------------
    weak, strong = _FakeClient(), _FakeClient()

    class _Flaky(_FakeClient):
        """빈칸추론(F)만 자기검증에 걸리는 값싼 모델."""

        def structured(self, system, prompt, model_cls, **kw):
            if model_cls.__name__ == "VerifyOut" and "빈칸" in prompt:
                from exam.verify import VerifyOut
                self.efforts.append((model_cls.__name__, kw.get("effort")))
                return VerifyOut(ok=False, reason="정답이 둘로 읽힌다")
            return super().structured(system, prompt, model_cls, **kw)

    weak = _Flaky()
    p2 = build_passage_merged(weak, _DUMMY, strong_client=strong)
    assert p2.types == set(MERGED_ORDER), sorted(set(MERGED_ORDER) - p2.types)
    # 상위 모델은 '걸린 문항'에만 쓰였다 — 15문항을 전부 다시 만들지 않는다
    used = [n for n, _ in strong.efforts if n not in ("VerifyOut", "Analysis")]
    assert used and len(used) <= 3, used
    assert "FOut" in used, used
    assert "VocabOut" not in used, used        # 멀쩡한 문항은 건드리지 않는다
    print("✓ 유형별 추론 강도·검수 승격(걸린 문항만 상위 모델) 통과")


def test_order_four_blocks() -> None:
    """순서 배열을 (A)(B)(C)(D) 네 덩어리로 낸다.

    가능한 배열이 6가지 → 24가지로 늘어 찍기가 어려워진다. 문장이 모자란 짧은 지문에서는
    세 덩어리로 줄이되, 어느 쪽이든 정답이 '모양'으로 드러나지 않아야 한다.
    """
    import collections
    import re as _re

    from exam.build import _order_options, make_order
    from exam.schemas import OrderOut
    from exam.shape import check_order_shuffle

    labels_of = lambda q: _re.findall(r'seg-label">\((.)\)', q)
    opts_of = lambda q: _re.findall(r'<li>.*?</li>', q)

    # ① 문장이 넉넉하면 네 덩어리 -----------------------------------------
    s8 = [f"Sentence number {i} says something here." for i in range(1, 9)]
    q, a = make_order(s8, 1, [2, 2, 2, 1], [3, 1, 4, 2], "이유.")
    assert labels_of(q) == ["A", "B", "C", "D"], labels_of(q)
    assert len(opts_of(q)) == 5
    # 정답은 display 를 뒤집어 복원한 배열이다
    assert "(B)-(D)-(A)-(C)" in q
    no = int(_re.search(r'answer-key">(.)<', a).group(1)
             .translate({ord(c): str(i + 1) for i, c in enumerate("①②③④⑤")}))
    assert opts_of(q)[no - 1].endswith("(B)-(D)-(A)-(C)</li>"), (no, opts_of(q))

    # ② 문장이 모자라면 세 덩어리로 줄인다(문항을 버리지 않는다) ----------
    s4 = ["First one here.", "Second one here.", "Third one here.", "Fourth one here."]
    fl: list[str] = []
    q3, _ = make_order(s4, 1, [1, 1, 1, 1], [2, 1, 3, 4], "이유.", flags=fl)
    assert labels_of(q3) == ["A", "B", "C"], labels_of(q3)
    assert fl, "덩어리 수를 줄였으면 확인 권장 사유가 남아야 한다"

    # ③ 선지가 '모양'으로 답을 흘리지 않는다 -------------------------------
    for corr in ("BDAC", "CADB", "DBCA"):
        for seed in range(8):
            opts, ansno = _order_options("ABCD", list(corr), seed)
            assert len(opts) == 5 and len(set(opts)) == 5, opts
            assert opts[ansno - 1] == "-".join(f"({c})" for c in corr)
            firsts = collections.Counter(o[1] for o in opts)   # '(X)-...' 의 X
            assert max(firsts.values()) <= 2, (opts, firsts)   # 첫 라벨 몰림 금지

    # ④ 라벨이 안 섞였거나 (A)가 곧 시작이면 거절 --------------------------
    assert check_order_shuffle([1, 2, 3, 4])          # 원문 순서 그대로
    assert check_order_shuffle([1, 3, 2, 4])          # (A)가 첫 덩어리
    assert check_order_shuffle([3, 1, 4, 2]) == []    # 정상
    # 스키마도 덩어리 수에 맞는 순열만 받는다
    OrderOut(given_n=1, block_sizes=[2, 1, 1, 1], display=[3, 1, 4, 2], reason="r")
    for bad in ([1, 2, 3], [1, 2, 3, 5], [2, 2, 1, 3]):
        try:
            OrderOut(given_n=1, block_sizes=[2, 1, 1, 1], display=bad, reason="r")
        except Exception:
            pass
        else:
            raise AssertionError(f"display={bad} 가 통과되면 안 된다")
    print("✓ 순서 배열 4덩어리(A~D)·짧은 지문 3덩어리 축소·선지 모양 통과")


def test_overlap_and_paraphrase_guards() -> None:
    """같은 지문 안에서 문항끼리 겹치는 것을 막는다.

    ① 정본에 밑줄 치는 문항(짝짓기 + 어휘 3종)이 같은 낱말을 쓰지 않는다
    ② 빈칸추론 정답이 '지문에 있던 어구 그대로'가 아니다
    ③ 서술형이 빠져 어순 배열·요약문과의 과제 중복이 사라졌다
    """
    import collections
    import re as _re

    from exam.merged import MERGED_ORDER, build_passage_merged
    from exam.shape import check_blank_answer_paraphrase as chk_para

    # ① 밑줄이 겹치지 않는다 ------------------------------------------------
    p = build_passage_merged(_FakeClient(), _DUMMY)
    marks = {}
    for t in ("pair_odd", "vocab_2", "vocab", "vocab_3"):
        assert t in p.q, t
        marks[t] = [w.lower() for w in _re.findall(r"<u>(.*?)</u>", p.q[t])]
    flat = [w for ws in marks.values() for w in ws]
    dup = [w for w, c in collections.Counter(flat).items() if c > 1]
    assert not dup, (dup, marks)
    # 둘째 문항부터는 '피할 낱말'이 실제로 프롬프트에 실려 간다
    seen_prompts = []

    class _Peek(_FakeClient):
        def structured(self, system, prompt, model_cls, **kw):
            if model_cls.__name__ in ("VocabOut", "PairOddOut"):
                seen_prompts.append((model_cls.__name__, prompt))
            return super().structured(system, prompt, model_cls, **kw)

    build_passage_merged(_Peek(), _DUMMY)
    later = [pr for _, pr in seen_prompts[1:]]
    assert later and all("겹침 금지" in pr for pr in later), len(later)

    # ② 빈칸추론 정답은 패러프레이즈여야 한다 -------------------------------
    sents = ["What makes it remarkable is that it packs an enormous amount into a tiny space.",
             "Researchers have begun to encode digital files into synthetic DNA."]
    blank = "packs an enormous amount into a tiny space"
    assert chk_para(blank, blank, sents)                       # 원문 그대로 → 실격
    assert chk_para("into a tiny space packs an enormous amount", blank, sents)  # 어순만 바꿈
    assert chk_para("encode digital files into synthetic DNA", blank, sents)     # 지문 다른 곳
    ok = "accommodates a vast volume of data within a minuscule area"
    assert chk_para(ok, blank, sents) == [], chk_para(ok, blank, sents)

    # ③ 서술형이 빠졌다 — 어순 배열·요약문과의 중복이 사라졌다 --------------
    assert "short_answer" not in MERGED_ORDER
    assert "D" in MERGED_ORDER and "E" in MERGED_ORDER
    print("✓ 밑줄 겹침 금지(짝짓기+어휘 3종)·빈칸 정답 패러프레이즈 강제 통과")


def test_grammar_count_fixed_four() -> None:
    """어법 개수 — 밑줄 6개(①~⑥) 중 정확히 4개가 틀린다(정답은 늘 ④).

    개수를 고정하는 대신 '어느 4개가 틀렸는지'를 지문마다 달리해, 학생이 밑줄 여섯을
    하나도 빠짐없이 판정하게 만든다.
    """
    import re as _re

    from exam.build import FIXED_WRONG_COUNT, MAX_WRONG_COUNT, N_COUNT_MARKS, make_grammar_count
    from exam.schemas import GrammarCountOut

    assert (N_COUNT_MARKS, FIXED_WRONG_COUNT, MAX_WRONG_COUNT) == (6, 4, 6)

    s6 = [f"The {w} line does its own job here."
          for w in ("first", "second", "third", "fourth", "fifth", "sixth")]
    marks = [(i, w, w if i in (1, 5) else w + "s")     # ②⑥만 옳게
             for i, w in enumerate(
                 ["first", "second", "third", "fourth", "fifth", "sixth"])]
    reasons = {i: "근거" for i in range(1, 7)}
    q, a = make_grammar_count(s6, marks, [1, 3, 4, 5], reasons, note="총평")
    assert len(_re.findall(r'<li>.*?</li>', q)) == 6                  # 선지 ①~⑥
    assert "6개" in q and "5개" in q
    assert _re.search(r'answer-key">(.)<', a).group(1) == "④"          # 정답은 늘 ④
    assert "(4개)" in a

    # 4개가 아니면 만들지 않는다(스키마·빌더 양쪽에서 막는다)
    for bad in ([1], [1, 3], [1, 2, 3, 4, 5]):
        try:
            make_grammar_count(s6, marks, bad, reasons)
        except ValueError:
            pass
        else:
            raise AssertionError(f"wrong_nos={bad} 가 통과되면 안 된다")
    ok = GrammarCountOut(
        rewritten=s6,
        marks=[WordMark(sent_no=i + 1, word=w, shown=w)
               for i, w in enumerate(["first", "second", "third",
                                      "fourth", "fifth", "sixth"])],
        wrong_nos=[1, 3, 4, 5],
        reasons=[GrammarReason(no=i, text="근거") for i in range(1, 7)])
    ok.check()
    ok.wrong_nos = [1, 3]
    try:
        ok.check()
    except ValueError:
        pass
    else:
        raise AssertionError("틀린 것이 2개인데 통과되면 안 된다")

    # 데모(어법 서술형)도 같은 규칙을 따른다 — 밑줄 6개, 고쳐 쓸 것 4개
    from exam.merged import demo_passages_merged
    dq = demo_passages_merged()[0]
    assert len(_re.findall(r'<u>.*?</u>', dq.q["grammar_fix"])) == 6
    key = _re.search(r'answer-key">(.*?)</span>', dq.a["grammar_fix"]).group(1)
    assert len(_re.findall(r"[①-⑥][^,]*?→", key)) == 4, key
    #    답란도 네 줄이어야 한다(학생이 적을 자리)
    assert dq.q["grammar_fix"].count('class="fix-row"') == 4
    print("✓ 어법 서술형(밑줄 6개·고쳐 쓸 것 4개·답란 4줄) 통과")


def test_demo_matches_real_rules() -> None:
    """데모(무료 미리보기)도 실제 생성이 지키는 규칙을 지켜야 한다.

    데모는 손으로 쓴 데이터라 파이프라인 검사를 거치지 않는다. 그래서 실제 생성이라면
    거절당했을 문항이 데모에는 남을 수 있는데, 그러면 미리보기가 제품을 잘못 보여 준다.
    (실제로 정본을 함께 쓰는 네 문항의 밑줄이 preserved·combined 등에서 겹쳐 있었다.)
    """
    import collections
    import re as _re

    from exam.generators.title import check_title_form
    from exam.merged import MERGED_ORDER, demo_passages_merged
    from exam.shape import check_order_shuffle

    for p in demo_passages_merged():
        # ① 정본을 함께 쓰는 문항끼리 밑줄이 겹치지 않는다
        marks: dict[str, list[str]] = {}
        for t in ("pair_odd", "vocab_2", "vocab", "vocab_3"):
            if t in p.q:
                marks[t] = [w.lower() for w in _re.findall(r"<u>(.*?)</u>", p.q[t])]
        flat = [w for ws in marks.values() for w in ws]
        dup = [w for w, c in collections.Counter(flat).items() if c > 1]
        assert not dup, (p.title, dup, marks)

        # ② 제목 선지는 한 갈래로 통일돼 있다
        if "title" in p.q:
            ch = [_re.sub(r"<.*?>", "", x).strip()
                  for x in _re.findall(r"<li>(.*?)</li>", p.q["title"], _re.S)]
            ch = [_re.sub(r"^[①-⑤]\s*", "", c) for c in ch]
            assert check_title_form(ch) == [], (p.title, check_title_form(ch))

        # ③ 어법 서술형은 밑줄 6개·고쳐 쓸 것 4개
        if "grammar_fix" in p.q:
            assert len(_re.findall(r"<u>.*?</u>", p.q["grammar_fix"])) == 6
            k = _re.search(r'answer-key">(.*?)</span>', p.a["grammar_fix"]).group(1)
            assert len(_re.findall(r"[①-⑥][^,]*?→", k)) == 4, (p.title, k)

        # ④ 순서 배열은 네 덩어리이고 (A)가 첫 덩어리가 아니다
        if "order" in p.q:
            labels = _re.findall(r'seg-label">\((.)\)', p.q["order"])
            assert labels == ["A", "B", "C", "D"], (p.title, labels)
            first = _re.findall(r"<li>.*?</li>", p.q["order"])
            assert len(first) == 5

        # ⑤ 모든 문항이 갖춰져 있다
        assert list(p.q) == list(MERGED_ORDER), [t for t in MERGED_ORDER if t not in p.q]
        # ⑥ 내용 O/X — 두 판 각각 열 진술, O 는 정확히 둘이며 세 칸 이상 떨어져 있다
        ox_at = {}
        for t in ("content", "content_2"):
            if t not in p.q:
                continue
            k = _re.search(r'answer-key">(.*?)</span>', p.a[t]).group(1)
            ox = _re.findall(r"[①-⑩]\s*([OX])", k)
            assert len(ox) == 10, (p.title, t, k)
            assert ox.count("O") == 2, (p.title, t, k)
            yes = tuple(i for i, m in enumerate(ox, 1) if m == "O")
            assert yes[1] - yes[0] >= 3, (p.title, t, k)
            assert p.q[t].count('class="ox-box"') == 10
            ox_at[t] = yes
        #    두 판의 O 자리가 같으면 한 판을 풀고 다른 판을 자리만 보고 옮겨 적는다
        if len(ox_at) == 2:
            assert len(set(ox_at.values())) == 2, (p.title, ox_at)

        # ⑦ 연결어는 (A)·(B) 빈칸 하나씩과 짝 선지 5개
        if "linker" in p.q:
            assert p.q["linker"].count('class="blank"') == 2, p.title
            assert len(_re.findall(r"<li>", p.q["linker"])) == 5, p.title

    print("✓ 데모가 실제 생성 규칙(밑줄 겹침·제목 갈래·어법 서술형·O/X·연결어)을 지킴")


def test_output_defect_regressions() -> None:
    """실제 출력물(올림포스 Unit 11, 32문항)에서 나온 결함을 하나씩 못 박는다."""
    import re

    from exam import answer_spread, shape
    from exam.analyzer import split_sentences

    # 1) 이름 가운데 이니셜에서 문장이 갈라졌다 -> 'Paul R. (1) Ehrlich'
    body = ("The reason pessimists often sound smart is that they can avoid being "
            "'wrong' by moving the goalposts. The American biologist Paul R. Ehrlich "
            "\u2500 author of the 1968 book The Population Bomb \u2500 has been doing this "
            "for decades. A pessimistic stance is a safe one.")
    sents = split_sentences(body)
    assert len(sents) == 3, sents
    assert "Paul R. Ehrlich" in sents[1], sents

    # 2) 인용문 한가운데서 갈라져 따옴표 짝이 깨졌다
    quoted = ("In 1970 he said that 'sometime in the next 15 years, the end will come. "
              "And by \"the end\" I mean an utter breakdown of the capacity of the "
              "planet to support humanity.' Wrong again.")
    qs = split_sentences(quoted)
    assert len(qs) == 2, qs
    assert qs[0].count("'") == 2, qs[0]

    # 3) 부정어형 어휘: 정답 근거(부정어)가 밑줄 '밖'이면 정답이 없는 문항이 된다
    outside = shape.check_negation_underline(
        [(4, "perceived", "perceived")], 1,
        "they would never delete the content despite suffering perceived judgement")
    assert outside and "부정어가 없습니다" in " ".join(outside)
    inside = shape.check_negation_underline(
        [(4, "never delete", "never delete")], 1,
        "they would never delete the content despite suffering perceived judgement")
    assert inside == [], inside

    # 4) 선지 재배열 뒤 해설의 오답 번호가 통째로 밀렸다(정답을 오답이라 설명)
    mapping = answer_spread.perm_map(5, 1, 4)
    moved = answer_spread.relabel_choice_refs(
        "정답은 1번이다. 2번은 (B)가 어긋나고, 5번은 둘 다 어긋난다.", mapping)
    assert "정답은 4번이다" in moved, moved
    assert "1번은 (B)가 어긋나고" in moved, moved
    assert "4번은 둘 다" not in moved, moved
    ch, ans, _ = answer_spread.place_answer(["a", "b", "c", "d", "e"], 1, 4)
    assert ans == 4 and ch[mapping[2] - 1] == "b", (ch, mapping)

    # 5) 해설에 내부 용어·출제 메모·문장 번호 지칭이 새어 나왔다
    assert shape.check_explanation("override 문장은 '결코 삭제하지 않는다'고 하여")
    assert shape.check_explanation("정답은 5번(sent_no=6)입니다.")
    assert shape.check_explanation("A가 첫 덩어리로 오지 않도록 배열을 조정하였다.")
    assert shape.check_explanation("지문 (3)에서 10분 이내에 삭제한다고 명시한다.")
    assert shape.check_explanation("정답 ②는 핵심어를 유의어로 바꿔 표현했다.") == []

    class _Out:
        def __init__(self):
            self.reason = "cues 에 별도 표시가 없습니다."
            self.choices = ["consumers face many choices", "a prompt reply"]
    assert shape.internal_terms_in(_Out()) == ["cues"]

    # 6) 요약문 해설도 오답을 번호별로 받는다(산문에 몰아 쓰면 번호가 밀린다)
    from exam.gen2 import EOut
    assert "wrong_reasons" in EOut.model_fields

    # 7) 지시문 조각이 지문에 박혔다 → '… ordinary listeners.output must'
    assert shape.check_clean_sentence(
        "One explanation is that they have never learned to hear music.output must")
    assert shape.check_clean_sentence(
        "It never lasts in bone or ice, disappearing within a few short years.") == []

    # 8) 어순 배열 <보기> 에 원문에 없는 구두점이 붙었다 → 'brain,'
    assert shape.check_tokens_rebuild(["the", "brain,", "that"], "the brain that")
    #    동사를 원형으로 두는 것(cues)은 정상이므로 걸리지 않는다
    assert shape.check_tokens_rebuild(
        ["the", "third", "sentence", "give", "a", "concrete", "example."],
        "The third sentence gives a concrete example.", ["give"]) == []

    # 9) 유의어 치환이 문장 첫 낱말이면 대문자를 지킨다 → '② numerous studies …'
    from exam import build as _B
    kept = _B.keep_sentence_case(["Many studies show the effect."],
                                 [(0, "Many", "numerous")])
    assert kept == [(0, "Many", "Numerous")], kept

    # 10) 짧은 지문에서도 무관한 문장을 낸다(①~④). 삽입은 자리가 모자라면 알린다.
    assert _B.irrelevant_marks(4) == 4 and _B.irrelevant_marks(5) == 5
    five = ["A one here now.", "B two here now.", "C three here now.",
            "D four here now.", "E five here now."]
    q_ir, _ = _B.make_irrelevant(five, 2, 3, "An unrelated sentence about costs.",
                                 "이유", {1: "a", 2: "b", 4: "d", 5: "e"})
    assert re.findall(r"[①-⑤]", q_ir) == ["①", "②", "③", "④", "⑤"], q_ir
    #    원문 문장은 하나도 사라지지 않는다 — 새 문장을 '끼워 넣는다'
    plain = re.sub(r"<[^>]+>", "", q_ir)
    for s in five:
        assert s in plain, (s, plain)
    assert "An unrelated sentence about costs." in plain
    four = five[:4]
    q4, _ = _B.make_irrelevant(four, 2, 2, "Alien.", "이유", {1: "a", 3: "c", 4: "d"})
    p4 = re.sub(r"<[^>]+>", "", q4)
    assert re.findall(r"[①-⑤]", q4) == ["①", "②", "③", "④"], q4
    assert all(s in p4 for s in four), p4
    fl: list[str] = []
    _B.make_insert(five, 2, "근거", flags=fl)
    assert any("선지가 3개뿐" in f for f in fl), fl

    # 11-a) 해설이 '선택지 N'·'세 번째 밑줄'로 불러도 번호가 같이 옮겨져야 한다
    m2 = answer_spread.perm_map(5, 1, 4)
    moved2 = answer_spread.relabel_choice_refs("선택지 1은 이를 재진술한다.", m2)
    assert "선택지 4" in moved2, moved2
    assert answer_spread.relabel_choice_refs("세 번째 밑줄이 정답이다.",
                                             {3: 4, 4: 3}) == "네 번째 밑줄이 정답이다."
    #    어휘는 밑줄을 읽는 순서로 다시 번호 매기므로 해설의 순번도 함께 옮긴다
    five = ["Alpha one runs here.", "Beta two walks here.", "Gamma three sits here.",
            "Delta four stands here.", "Epsilon five waits here."]
    scrambled = [(4, "waits", "waits"), (0, "runs", "runs"), (2, "sits", "sits"),
                 (1, "walks", "walks"), (3, "stands", "stands")]
    _q, _a = _B.make_vocab(five, scrambled, 3, "세 번째 밑줄 sits 가 정답이다.")
    assert "③" in _a and "세 번째" in _a, _a

    # 11-b) 주제 선지 하나만 절이면 모양으로 답이 보인다(제목·빈칸에는 걸지 않는다)
    np_bad = ["the tendency of individuals to overestimate their willingness",
              "how more witnesses improve the chance that someone intervenes",
              "various character defects that prevent people from responding",
              "the discomfort people feel when comparing themselves to bystanders",
              "situational forces, not personal flaws, explain the failure, as duty spreads"]
    assert shape.check_choice_shape(np_bad, 5, noun_phrase=True)
    assert shape.check_choice_shape(np_bad, 5) == []      # 기본은 걸지 않는다
    #    쉼표 하나짜리 제목은 정상이므로 걸리면 안 된다
    titles = ["Cheaper Chips, Shorter Memories", "Bridging Emotion and Reason",
              "The Hidden Cost of Discipline", "A Sign of Weak Parenting",
              "Calming the Storm Through Words"]
    assert shape.check_choice_shape(titles, 1, noun_phrase=True) == []

    # 12) 제목도 오답 4개 근거를 모두 받아야 한다(빠지면 해설에 빈 줄이 찍혔다)
    from exam.schemas import TitleOut, WrongReason as _WR
    try:
        TitleOut(choices=list("abcde"), answer_no=3, reason="x",
                 wrong_reasons=[_WR(no=i, text="t") for i in (1, 2, 3, 4, 5)])
        raise AssertionError("정답 번호가 오답 목록에 있는데 통과했습니다.")
    except ValueError:
        pass
    # ---- 네 번째 출력물 검증(올림포스 영어독해 기본1)에서 나온 것들 ----------
    # 13) 낱말 하나를 갈아 끼우다 구동사·전치사·타동사 목적어가 깨졌다
    assert shape.check_swap_breaks(
        "To help them calm down, and to see reason, the best strategy is a hug.",
        "calm", "upset")
    assert shape.check_swap_breaks(
        "give them the ability to listen to what their parents are saying.",
        "listen", "hear")
    assert shape.check_swap_breaks(
        "A single bystander would usually respond, just as we hope we would.",
        "respond", "ignore")
    #     멀쩡한 유의어 치환은 하나도 걸리면 안 된다(오탐이 나면 문항이 죽는다)
    for sent, w, sh in [
        ("A single bystander would usually respond, just as we hope.", "respond", "react"),
        ("the child is not able to contain their mood.", "contain", "control"),
        ("due to frustration, sadness or any other intense emotion", "intense", "strong"),
        ("the situation constrains their behavior more than we realize.",
         "realize", "recognize"),
        ("defects in their character that prevent them from helping.", "prevent", "stop"),
        ("bystanders in emergency situations are acting normally", "acting", "behaving"),
        ("the best strategy is a hug", "best", "most effective"),
        ("responsibility apparently diffuses among them", "diffuses", "spreads"),
        ("People often ignore the warning signs.", "ignore", "overlook"),
    ]:
        assert shape.check_swap_breaks(sent, w, sh) == [], (w, sh)

    # 14) 어순 배열 <보기> 는 코드가 섞는다(모델이 정답 순서 그대로 돌려준 적이 있다)
    from exam import build2 as _B2
    ans14 = ("A spoken word will form a bridge between the two worlds, allowing "
             "the child's rational brain to help soothe their emotions.")
    toks14 = ans14.split()
    assert shape.check_tokens_shuffled(toks14, ans14)        # 그대로면 잡는다
    mixed = _B2._shuffle_tokens(toks14, ans14)
    assert sorted(mixed) == sorted(toks14) and mixed != toks14
    assert shape.check_tokens_shuffled(mixed, ans14) == []
    assert _B2._shuffle_tokens(toks14, ans14) == mixed       # 같은 지문 → 같은 결과

    # 15) 짝짓기 해설 — 밑줄 기호가 겹쳐 찍히지 않고, 한 줄씩 나뉜다
    from exam.generators.pair_odd import _strip_marker
    assert _strip_marker("ⓐ contain: '억누르다'의 뜻이다.") == "contain: '억누르다'의 뜻이다."
    five15 = ["Alpha one runs here.", "Beta two walks here.", "Gamma three sits here.",
              "Delta four stands here.", "Epsilon five waits here."]
    marks15 = [(0, "runs", "runs"), (1, "walks", "walks"), (2, "sits", "sits"),
               (3, "stands", "stands"), (4, "waits", "waits")]
    _q15, a15 = _B2.make_A(five15, marks15, 2, "총평",
                           ["ⓐ-ⓑ", "ⓒ-ⓓ", "ⓐ-ⓒ", "ⓑ-ⓓ", "ⓓ-ⓔ"],
                           reasons={i: f"사유 {i}" for i in range(1, 6)})
    assert a15.count('class="wrong"') == 5, a15
    assert "ⓐ ⓐ" not in a15 and "사유 1" in a15

    # 16) 밑줄로 '쓴 낱말'에는 보여 준 낱말도 들어간다(짝짓기 ⓒ emotional ↔ 어휘 ①)
    from exam.generators.vocab import _mark_words

    class _M:
        def __init__(self, w, s):
            self.word, self.shown = w, s
    assert "emotional" in _mark_words([_M("rational", "emotional")])
    assert {"never", "delete"} <= _mark_words([_M("never delete", "never delete")])

    print("✓ 실제 출력물 결함 재발 방지(이니셜·인용문·부정어 밑줄·선지 번호·해설 위생·"
          "지문 오염·보기 토큰·대문자·짧은 지문·제목 오답·낱말 치환 파손·보기 섞기·"
          "짝짓기 해설·밑줄 겹침) 통과")


def test_type_group_layout() -> None:
    """유형별 편성 조판: 유형마다 새 쪽 · 큰 칩 · 문항별 출처 · 두 단 고르게."""
    import copy

    from exam.merged import demo_passages_merged

    # 두 단으로 가장 고르게 나뉘는 자리를 고른다(문항 경계에서만 나눈다)
    assert renderer._even_split([10, 10, 10]) == 20      # 20 / 10
    assert renderer._even_split([10, 10, 10, 10]) == 20  # 20 / 20
    assert renderer._even_split([50, 10, 10]) == 50      # 50 / 20 — 쪼갤 수 없다

    ps = demo_passages_merged()
    ps = ps + [copy.deepcopy(ps[0])]
    for i, p in enumerate(ps, 1):
        p.source_label = f"13-{i}"
    M = dict(type_order=MERGED_ORDER, prompts=MERGED_PROMPTS, labels=MERGED_LABELS)
    html = renderer.render_html(ps, sections=["answers"], **M)
    #  유형마다 제 몫의 2단 상자를 갖고, 조판기가 잴 수 있게 id 가 붙는다
    assert html.count('class="type-group') == len(MERGED_ORDER)
    assert html.count('id="tg-a-') == len(MERGED_ORDER)
    assert '<span class="type-chip-name">주제</span>' in html
    assert '<span class="q-src">13-2</span>' in html

    #  1차 조판을 재어 2차 조판에 줄 칸 높이가 실제로 나온다(짧은 묶음은 한 단에만
    #  쌓이므로, 그대로 두면 오른쪽 단이 통째로 빈다)
    from weasyprint import HTML

    doc = HTML(string=html, base_url=str(renderer.TEMPLATE_DIR)).render(
        stylesheets=renderer._stylesheets())
    css = renderer._balance_css(doc)
    assert "#tg-a-0{height:" in css, css[:200]

    #  지문별 편성에는 유형 묶음이 없으므로 2차 조판도 없다(비용 0)
    html_p = renderer.render_html(ps, sections=["answers"], group_by="passage", **M)
    doc_p = HTML(string=html_p, base_url=str(renderer.TEMPLATE_DIR)).render(
        stylesheets=renderer._stylesheets())
    assert renderer._balance_css(doc_p) == ""
    print("✓ 유형별 편성 조판(유형마다 새 쪽·큰 칩·문항별 출처·두 단 고르게) 통과")


def test_ox_axes() -> None:
    """내용 O/X 의 오답 축 — 눈썰미만 재는 두 방식은 쓰지 않는다."""
    import re as _re

    from exam.merged import demo_passages_merged
    from exam.shape import check_ox_axes

    #  ① 뺀 두 축의 이름이 근거에 있으면 걸린다
    assert check_ox_axes(["지문은 '수만 년'이라 했다. (부분 일치 + 한 요소 왜곡)"])
    assert check_ox_axes(["'반드시'라고 하지 않았다. (정도·빈도 과장)"])
    #  ② 남은 여덟 축은 통과한다
    assert check_ox_axes([
        "주체가 뒤바뀌었다. (주체·대상 바꿔치기)",
        "없던 인과를 엮었다. (인과 날조)",
        "원인과 결과가 뒤집혔다. (인과 역전)",
        "'이론상'이라는 단서를 뗐다. (조건 삭제)",
        "앞뒤 순서가 뒤집혔다. (시점 뒤집기)",
        "지문이 못 박아 부정한 대목이다. (부정 뒤집기)",
        "통념을 필자의 주장으로 바꿔치기했다. (논지·화자 뒤집기)",
        "그럴듯하지만 언급되지 않았다. (미언급인데 그럴듯)",
    ]) == []
    #  ③ 데모도 그 두 축을 쓰지 않고, 여덟 축을 하나씩 쓴다
    from exam.shape import OX_AXES, check_ox_axis_coverage
    for p in demo_passages_merged():
        for t in ("content", "content_2"):
            if t not in p.a:
                continue
            plain = _re.sub(r"<[^>]+>", " ", p.a[t])
            assert check_ox_axes([plain]) == [], (p.title, t)
            ax = _re.findall(r'class="ox-axis">(.*?)</span>', p.a[t])
            assert sorted(ax) == sorted(OX_AXES), (p.title, t, ax)
            assert check_ox_axis_coverage(ax) == []

    #  ④ 축이 겹치면 알려 준다 — 다만 다시 만들지는 않는다(가장 비싼 호출이라서)
    dup = list(OX_AXES[:-1]) + [OX_AXES[0]]
    msg = check_ox_axis_coverage(dup)
    assert msg and "겹칩니다" in msg[0] and "미언급인데 그럴듯" in " ".join(msg), msg
    #     생성기는 이것을 검토 메모로만 단다(승격 표시가 붙지 않는다)
    from exam import tiering
    assert not tiering.needs_escalation(msg)
    print("✓ 내용 O/X 오답 축(여덟 축 하나씩·부분 일치·정도 과장 제외) 통과")


def test_ox_short_passage() -> None:
    """짧은 지문에서는 요구를 낮춘다 — 영어판 8진술 · O 근거 겹침 허용 · 없는 축 대체.

    5문장짜리 지문에 '서로 다른 사실 넷 · 여덟 축 하나씩'을 그대로 요구하면 모델이
    없는 재료를 지어낸다. 지어낸 진술은 지문에 근거가 없어 정답 시비가 난다.
    """
    import re as _re

    from exam import answer_spread, build as B, shape
    from exam.generators import content as C
    from exam.schemas import ContentOXOut, OXStatement, ox_sizes
    from exam.types import CONTENT, CONTENT_2

    FILL = shape.OX_AXES[-1]            # '미언급인데 그럴듯' — 재료가 없을 때 채우는 축

    #  ① 진술 수는 '낱말 수'가 정한다 — 문장 수가 아니다.
    #     실제 EBS 지문을 재어 보면 5문장 141낱말(명제 ~13개)과 10문장 132낱말(~13~16개)이
    #     명제 수가 비슷하다. 문장으로 자르면 정보가 더 많은 쪽이 축소 대상이 된다.
    def _sents(n_words: int, n_sents: int) -> list[str]:
        per = max(1, n_words // n_sents)
        return [" ".join(["word"] * per) + "." for _ in range(n_sents)]

    assert ox_sizes(_sents(60, 4)) == (10, 8)        # 짧다 → 영어판 8진술(총 18)
    assert ox_sizes(_sents(90, 5)) == (10, 8)
    assert ox_sizes(_sents(140, 12)) == (10, 10)     # 넉넉하다 → 20진술
    #     문장이 5개뿐이어도 낱말이 넉넉하면 줄이지 않는다(실제 지문1: 5문장 141낱말)
    assert ox_sizes(_sents(140, 5)) == (10, 10)
    #     문장이 10개여도 낱말이 모자라면 줄인다(문장 수로는 못 잡는 경우)
    assert ox_sizes(_sents(80, 10)) == (10, 8)

    #  ② 여덟 칸짜리 O 자리표 — 없는 자리(⑨⑩)가 나오지 않는다
    seen = set()
    for pi in range(6):                              # 지문 6개 × 두 판 = 열두 문항
        for v in (0, 1):
            a, b = answer_spread.ox_positions(pi, v, seed=0, n=8)
            assert 1 <= a < b <= 8, (pi, v, a, b)
            assert b - a >= 3, (pi, v, a, b)         # 두 O 는 세 칸 이상 떨어진다
            assert (a <= 4) != (b <= 4), (pi, v, a, b)   # 앞뒤 한쪽에 몰리지 않는다
            seen.add((a, b))
    assert len(seen) == 12, seen                     # 열두 문항이 저마다 다른 자리 짝

    #  ③ 조판기가 여덟 진술을 받는다(열은 그대로, 아홉은 거절)
    sents = [f"Sentence {i} of the passage." for i in range(1, 6)]
    q8, _ = B.make_content_ox(sents, [f"진술{i}" for i in range(1, 9)],
                              [i in (2, 6) for i in range(1, 9)],
                              [f"근거{i}" for i in range(1, 9)])
    assert q8.count("<li>") == 8
    try:
        B.make_content_ox(sents, ["진술"] * 9, [True, True] + [False] * 7, ["근거"] * 9)
    except ValueError as e:
        assert "8 또는 10" in str(e), e
    else:
        raise AssertionError("진술이 아홉 개인데 통과했습니다.")

    #     검산기도 여덟 진술을 걸고넘어지지 않는다(문제편의 진술 수와 맞춰 센다)
    from exam import audit
    q8b, a8b = B.make_content_ox(sents, [f"진술{i}" for i in range(1, 9)],
                                 [i in (2, 6) for i in range(1, 9)],
                                 [f"근거{i}" for i in range(1, 9)])
    assert audit._check_item(audit._parse("content_2", q8b, a8b)) == []
    #     반대로 판정이 모자라면 잡는다
    short_key = _re.sub(r"⑥O", "", a8b, count=1)
    assert audit._check_item(audit._parse("content_2", q8b, short_key))

    #  ④ 생성기 — 프롬프트가 지문 길이에 맞춰 바뀌고, 결과 개수도 그에 맞는다
    def _fake(prefix: str, n: int) -> list:
        n_x = n - 2
        axes = (list(shape.OX_AXES[:n_x]) if n_x >= 8
                else list(shape.OX_AXES[:n_x - 3]) + [FILL] * 3)
        out, k = [], 0
        for i in range(1, n + 1):
            if i in (1, n):                          # O 둘(자리는 조판기가 다시 정한다)
                out.append(OXStatement(text=f"{prefix} {i}", is_true=True,
                                       why=f"근거{i}", axis="일치"))
            else:
                out.append(OXStatement(text=f"{prefix} {i}", is_true=False,
                                       why=f"근거{i}", axis=axes[k]))
                k += 1
        return out

    class _Cli:
        prompt = ""

        def structured(self, system, prompt, model_cls, max_tokens=8000,
                       max_retries=1, extra_validate=None, image_path=None,
                       cache_prefix=None, effort=None):
            self.prompt = prompt
            n_ko = int(_re.search(r"한국어 진술 \*\*(\d+)개\*\*", prompt).group(1))
            n_en = int(_re.search(r"영어 진술 \*\*(\d+)개\*\*", prompt).group(1))
            obj = ContentOXOut(korean=_fake("한글 진술", n_ko),
                               english=_fake("English statement", n_en))
            if extra_validate:
                extra_validate(obj)
            return obj

    def _analysis(n_words: int, n_sents: int) -> Analysis:
        ss = _sents(n_words, n_sents)
        return Analysis(title="P", main_idea="A main idea.", sentences=ss,
                        key_terms=[KeyTerm(word="fact", synonym="detail", antonym="")],
                        hardest_sentence=ss[0])

    #     낱말 60개 — 세 자리가 모두 낮아진다
    cli = _Cli()
    res = C.generate_pair(cli, _analysis(60, 5), "body", passage_index=0)
    assert "한국어 진술 **10개**" in cli.prompt
    assert "영어 진술 **8개**" in cli.prompt
    assert "이 지문은 낱말이 60개로 짧습니다" in cli.prompt         # O 근거 겹침 허용
    assert f"'{FILL}'으로 채우세요" in cli.prompt                   # 없는 축 대체 허용
    assert "한글판의 X 8개, 영어판의 X 6개" in cli.prompt
    assert res[CONTENT][0].count("<li>") == 10
    assert res[CONTENT_2][0].count("<li>") == 8
    #     시킨 대로 채운 겹침은 검토 메모를 남기지 않는다
    assert res[CONTENT_2][2] == [], res[CONTENT_2][2]
    #     영어판 O 두 자리가 여덟 칸 안에 있다
    ox = _re.findall(r"([OX])</b>", res[CONTENT_2][1])
    assert len(ox) == 8 and ox.count("O") == 2, ox

    #     낱말 140개 — 문장이 5개뿐이어도 요구를 낮추지 않는다(실제 EBS 지문1의 모양)
    cli2 = _Cli()
    res2 = C.generate_pair(cli2, _analysis(140, 5), "body", passage_index=0)
    assert "영어 진술 **10개**" in cli2.prompt
    assert "짧습니다" not in cli2.prompt
    assert f"'{FILL}'으로 채우세요" not in cli2.prompt
    assert res2[CONTENT][0].count("<li>") == 10
    assert res2[CONTENT_2][0].count("<li>") == 10
    #     O 넷만 서로 달라야 하고, X 는 두 판이 같은 대목을 써도 된다
    assert "O 4개(판마다 2개)는 서로 다른 사실" in cli2.prompt
    assert "X 는 두 판이 같은 대목을 써도 됩니다" in cli2.prompt
    assert "한 판 안에서는" in cli2.prompt

    #  ⑤ '채우라고 시킨' 겹침만 봐준다 — 그 밖의 겹침은 그대로 지적한다
    filled = list(shape.OX_AXES[:3]) + [FILL] * 3       # FILL 이 2번 더(허용치와 같음)
    assert shape.check_ox_axis_coverage(filled, allow_repeat=2) == []
    assert shape.check_ox_axis_coverage(filled) != []   # 안 시켰으면 지적한다
    over = list(shape.OX_AXES[:2]) + [FILL] * 4         # 한 번 더 겹쳤다
    assert shape.check_ox_axis_coverage(over, allow_repeat=2) != []
    other = list(shape.OX_AXES[:3]) + [shape.OX_AXES[0]] + [FILL] * 3
    assert shape.check_ox_axis_coverage(other, allow_repeat=2) != []
    #     건너뛰라고 시켜 놓고 '빠진 축이 있다'고 지적하지도 않는다
    skipped = list(shape.OX_AXES[:6]) + [FILL] * 2      # 여덟 자리에 여섯 축 + 채움
    assert shape.check_ox_axis_coverage(skipped, allow_repeat=2) == []
    assert "쓰이지 않은" in " ".join(shape.check_ox_axis_coverage(skipped))
    print("✓ 짧은 지문 내용 O/X(영어판 8진술·O 근거 겹침 허용·없는 축 대체) 통과")


def test_direct_sale_guards() -> None:
    """산출물이 곧바로 판매되는 전제 — 검토메모에 기대지 않고 코드가 끝을 낸다.

    ① 9·11번(원문단어형·부정어형): 정답 아닌 밑줄을 원문 낱말로 '되돌린다'(거부가 아니라).
       거부하면 재시도가 소진됐을 때 문항이 통째로 빠지고, 빠진 문항은 그대로 팔린다.
    ② 17번(어순 배열): 우리말 뜻이 없으면 정답 어순이 정해지지 않는다 → 스키마 필수.
    ③ 10번(유의어형): 오답 자리의 반의어를 분석표로 잡는다. 자기검증은 붙이지 않는다 —
       어휘 3종은 밑줄이 겹치면 안 되어 차례로 도는 직렬 구간이라, 거기 붙인 한 번은
       고스란히 대기 시간에 더해진다. 그래서 추가 호출 0으로 막는다.
    """
    import collections
    import re as _re

    from exam import build2, format2
    from exam.gen2 import DOut
    from exam.generators.vocab import (NEGATION, ORIGINAL, SYNONYM,
                                       _restore_original_marks)
    from exam.merged import MERGED_ORDER, build_passage_merged
    from exam.schemas import VocabOut, WordMark
    from exam.verify import HIGH_RISK

    #  ① 정답 아닌 밑줄만 되돌리고, 정답과 유의어형은 손대지 않는다
    def _mk():
        return VocabOut(
            marks=[WordMark(sent_no=1, word="rapid", shown="rapid"),
                   WordMark(sent_no=2, word="ignore", shown="overlook"),   # 몰래 바뀜
                   WordMark(sent_no=3, word="clear", shown="obvious"),     # 몰래 바뀜
                   WordMark(sent_no=4, word="grow", shown="shrink"),       # 정답(반의어)
                   WordMark(sent_no=5, word="often", shown="often")],
            answer_no=4, reason="이유", override_no=0, override_text="")

    for method in (ORIGINAL, NEGATION):
        o = _mk()
        assert _restore_original_marks(o, method) == [2, 3], method
        assert [m.shown for m in o.marks] == [
            "rapid", "ignore", "clear", "shrink", "often"], method   # 정답은 그대로
    o = _mk()
    assert _restore_original_marks(o, SYNONYM) == []          # 유의어형은 손대지 않는다
    assert o.marks[1].shown == "overlook"

    #  ② 우리말 뜻은 스키마 '필수' — 빠지면 파싱 단계에서 걸린다(재시도 안내에 실린다)
    assert DOut.model_fields["korean"].is_required()
    q = format2.D_q(["a", "b"], [], "우리말 뜻입니다.")
    assert "d-korean" in q and "우리말 뜻입니다." in q
    #     옛 결과 JSON 에는 우리말이 없다 — 그때는 줄이 통째로 빠져 예전 그대로 나온다
    assert "d-korean" not in format2.D_q(["a", "b"], [])
    #     조판기까지 이어진다
    sents = ["One day our libraries may be stored inside molecules."]
    qd, _ = build2.make_D(sents, sents[0].split(), [], sents[0],
                          korean="언젠가 우리의 도서관이 분자 안에 저장될지도 모른다.")
    assert "언젠가 우리의 도서관이" in qd

    #  ③ 유의어형 — 오답 자리의 반의어를 분석표로 잡는다(추가 호출 0)
    from exam.generators.vocab import check_synonym_antonyms
    from exam.schemas import KeyTerm

    an = Analysis(title="T", main_idea="M",
                  sentences=["S1.", "S2.", "S3.", "S4.", "S5."],
                  key_terms=[KeyTerm(word="rapid", synonym="swift", antonym="slow"),
                             KeyTerm(word="clear", synonym="obvious", antonym="vague")],
                  hardest_sentence="S1.")

    def _v(shown_2, shown_3):
        return VocabOut(
            marks=[WordMark(sent_no=1, word="rapid", shown=shown_2),
                   WordMark(sent_no=2, word="clear", shown=shown_3),
                   WordMark(sent_no=3, word="grow", shown="shrink"),   # 정답
                   WordMark(sent_no=4, word="often", shown="frequently"),
                   WordMark(sent_no=5, word="wide", shown="broad")],
            answer_no=3, reason="이유", override_no=0, override_text="")

    assert check_synonym_antonyms(an, _v("swift", "obvious")) == []      # 유의어 — 통과
    msg = check_synonym_antonyms(an, _v("slow", "obvious"))              # 반의어 — 걸린다
    assert msg and "반의어" in msg[0] and "1번" in msg[0], msg
    assert len(check_synonym_antonyms(an, _v("slow", "vague"))) == 1     # 둘 다 한 줄로
    assert "2번" in check_synonym_antonyms(an, _v("slow", "vague"))[0]
    #     정답 자리의 반의어는 당연히 통과한다(그게 정답이다)
    ok = _v("swift", "obvious")
    ok.marks[2] = WordMark(sent_no=3, word="rapid", shown="slow")
    ok.answer_no = 3
    assert check_synonym_antonyms(an, ok) == []

    #     어휘 3종에는 자기검증을 걸지 않는다 — 직렬 구간이라 시간이 그대로 늘어난다
    assert not any(k.startswith("vocab") for k in HIGH_RISK), sorted(HIGH_RISK)

    class _Count(_FakeClient):
        def __init__(self):
            super().__init__()
            self.calls = collections.Counter()

        def structured(self, system, prompt, model_cls, **kw):
            self.calls[model_cls.__name__] += 1
            return super().structured(system, prompt, model_cls, **kw)

    c = _Count()
    p = build_passage_merged(c, _DUMMY)
    assert len(p.q) == len(MERGED_ORDER), f"문항이 빠졌습니다: {len(p.q)}"
    #     비용 회귀 방지 — 지문 1개당 호출 수를 못 박는다(늘면 이 줄이 먼저 깨진다)
    assert sum(c.calls.values()) == 28, dict(c.calls)
    assert c.calls["VerifyOut"] == 11, dict(c.calls)          # 고위험 11유형만
    #     우리말 뜻이 실제 문제편에 실린다
    assert "d-korean" in p.q["D"]
    assert _re.search(r"우리말", _re.sub(r"<[^>]+>", " ", p.q["D"]))
    print("✓ 판매 직행 안전장치(밑줄 자동 복원·어순배열 우리말 뜻·반의어 충돌·추가 호출 0) 통과")


def test_grammar_on_original_passage() -> None:
    """5번 어법은 정본 그대로, 6번 어법 서술형은 다시 쓴 지문 위에 선다."""
    import re as _re

    from exam.merged import build_passage_merged
    from exam.schemas import GrammarOut

    #  스키마에서 rewritten 이 사라졌다 — 다시 쓰라고 시키지 않으므로 받을 것도 없다
    assert "rewritten" not in GrammarOut.model_fields
    assert "rewritten" in GrammarCountOut.model_fields      # 서술형은 그대로 다시 쓴다

    p = build_passage_merged(_FakeClient(), _DUMMY)
    orig = " ".join(_re.sub(r"\s+", " ", s2) for s2 in
                    _re.split(r"(?<=[.!?])\s+", _DUMMY))

    def _body(html):
        t = _re.sub(r"<[^>]+>", " ", _re.search(
            r'<div class="passage[^"]*">(.*?)</div>', html, _re.S).group(1))
        return _re.sub(r"[^a-z ]+", " ", t.lower()).split()

    #  ① 어법 지문은 정본과 같은 낱말로 이루어진다(밑줄 자리만 형태가 다르다)
    g = set(_body(p.q["grammar"]))
    o = set(_re.sub(r"[^a-z ]+", " ", orig.lower()).split())
    assert len(g - o) <= 3, sorted(g - o)     # 틀린 형태로 바꾼 밑줄만 다르다
    #  ② 어법 서술형 지문은 정본과 확실히 다르다(다시 쓴 것)
    f = set(_body(p.q["grammar_fix"]))
    assert len(f - o) > 5, sorted(f - o)

    #  ③ 어법이 정본에 서므로 짝짓기·어휘와 밑줄이 겹치면 안 된다
    import collections
    marks = {t: [w.lower() for w in _re.findall(r"<u>(.*?)</u>", p.q[t])]
             for t in ("grammar", "pair_odd", "vocab_2", "vocab", "vocab_3")}
    flat = [w for ws in marks.values() for w in ws]
    dup = [w for w, c in collections.Counter(flat).items() if c > 1]
    assert not dup, (dup, marks)
    print("✓ 어법은 정본 그대로·어법 서술형은 다시 쓴 지문·밑줄 겹침 없음 통과")


def test_output_checker() -> None:
    """완성된 산출물 검산기(tools/검증.py)가 실제로 나왔던 결함을 잡는가."""
    import copy
    import re

    from exam import audit as V
    from exam.merged import demo_passages_merged

    clean = demo_passages_merged()[0]
    rows, whole = V.check_passage(clean)
    assert len(rows) == len(MERGED_ORDER), len(rows)
    flagged = {r["label"]: r["bad"] for r in rows if r["bad"]}
    assert not flagged and not whole, (flagged, whole)   # 데모는 깨끗해야 한다

    # 실제 출력물에서 나왔던 결함을 하나씩 심고 잡히는지 본다
    bad = copy.deepcopy(clean)
    bad.q["vocab_3"] = bad.q["vocab_3"].replace("</div>", ".output must</div>", 1)
    bad.q["vocab"] = bad.q["vocab"].replace("A single gram", "numerous single gram", 1)
    bad.q["D"] = re.sub(r"(libraries)", r"\1,", bad.q["D"], count=1)
    bad.a["topic"] = bad.a["topic"].replace("</p>", " 지문 (3)에서 확인된다.</p>", 1)
    bad.a["title"] = bad.a["title"].replace(
        "</p>", " 이 문항은 밑줄 넷이 틀리도록 구성한 문제이다.</p>", 1)

    rows, _ = V.check_passage(bad)
    got = {r["type"]: " ".join(r["bad"]) for r in rows if r["bad"]}
    assert "마침표 뒤에 낱말" in got.get("vocab_3", ""), got
    assert "소문자로 시작" in got.get("vocab", ""), got
    assert "구두점" in got.get("D", ""), got
    assert "문장 번호로 지칭" in got.get("topic", ""), got
    assert "출제 과정 메모" in got.get("title", ""), got

    # 네 번째 출력물에서 나온 것들도 검산기가 잡아야 한다
    bad2 = copy.deepcopy(clean)
    #  (가) <보기> 가 정답 문장 순서 그대로 → 베껴 쓰기 문항
    d_ans = re.sub(r"<[^>]+>", "", re.search(
        r'<span class="answer-key">.*?</span>(.*?)</p>', bad2.a["D"], re.S).group(1)).strip()
    bad2.q["D"] = re.sub(r'<div class="boki">.*?</div>',
                         '<div class="boki">&lt;보기&gt; '
                         + " / ".join(d_ans.split()) + "</div>",
                         bad2.q["D"], count=1, flags=re.S)
    #  (나) 해설이 오답 분류 이름을 문장으로 쓴다
    bad2.a["topic"] = bad2.a["topic"].replace("</p>", " 방향 반전 축이다.</p>", 1)
    #  (다) '빼낼 문장은 …' 도 출제 과정 메모다
    bad2.a["insert"] = bad2.a["insert"].replace("</p>", " 빼낼 문장은 이것이다.</p>", 1)
    rows2, _ = V.check_passage(bad2)
    got2 = {r["type"]: " ".join(r["bad"]) for r in rows2 if r["bad"]}
    assert "순서 그대로" in got2.get("D", ""), got2
    assert "오답 분류 이름" in got2.get("topic", ""), got2
    assert "출제 과정 메모" in got2.get("insert", ""), got2

    #  (라) 검토 메모는 같은 지적을 두 번 싣지 않는다(접두어·말끝만 다른 경우)
    dup = copy.deepcopy(clean)
    dup.flag("insert", ["자동검사: 해설에 출제 과정 메모가 있습니다: 빼낸 문장"])
    dup.a["insert"] = dup.a["insert"].replace("</p>", " 빼낸 문장은 이것이다.</p>", 1)
    V.apply_to_flags(dup)
    memos = [m for m in dup.flags["insert"] if "출제 과정 메모" in m]
    assert len(memos) == 1, memos

    # 기계 검사 사유는 검수 승격의 방아쇠가 된다(값싼 모델의 흠을 상위 모델이 고친다)
    from exam import shape, tiering
    assert tiering.needs_escalation([shape.ESCALATE + "해설에 내부 용어"])
    assert not tiering.needs_escalation(["해설에 '-습니다'체와 '-다'체가 섞여 있습니다."])
    assert not tiering.needs_escalation(["선지가 3개뿐입니다 — 지문이 짧아"])
    print("✓ 산출물 검산기(문항 안·문항끼리)·기계 검사 승격 연결 통과")


def test_stress_fixtures() -> None:
    """극단 지문 시험대(tests/test_stress.py)를 본 묶음에서도 돌린다."""
    sys.path.insert(0, str(ROOT / "tests"))
    from test_stress import test_stress_passages

    test_stress_passages()


def test_analysis_sentences_are_ours() -> None:
    """모델이 sentences 를 못 줘도 생성이 죽지 않아야 한다(실제 실패 재발 방지).

    analyze() 는 모델이 준 sentences 를 쓰지 않고 '넣은 원문'을 코드가 나눈 것으로
    덮어쓴다. 그런데 스키마가 그 버려질 값에 '4개 이상'을 요구하고 있어서, 모델이
    빈 배열을 한 번 돌려주자 지문 두 개짜리 작업이 통째로 실패했다.
    """
    from exam import analyzer
    from exam.schemas import Analysis

    # 1) 모델이 sentences 를 아예 안 줘도 스키마가 통과한다
    assert Analysis(title="t", main_idea="m").sentences == []

    body = ("One sentence stands here. Two sentences stand here. "
            "Three sentences stand here. Four sentences stand here.")

    class _Empty:                       # 모델이 빈 배열을 돌려주는 상황
        def structured(self, **kw):
            return Analysis(title="t", sentences=[], main_idea="m")

    got = analyzer.analyze(_Empty(), body)
    assert got.sentences == analyzer.split_sentences(body), got.sentences

    class _Halluc:                      # 모델이 지문을 바꿔 말하는 상황
        def structured(self, **kw):
            return Analysis(title="t", sentences=["Made up.", "Not in the body."],
                            main_idea="m")

    assert analyzer.analyze(_Halluc(), body).sentences == analyzer.split_sentences(body)

    # 2) 짧은 지문은 'API 를 부르기 전에' 사람이 읽는 말로 거절한다
    class _Boom:
        def structured(self, **kw):
            raise AssertionError("짧은 지문인데 API 를 불렀습니다.")

    try:
        analyzer.analyze(_Boom(), "Only one sentence here.")
        raise AssertionError("짧은 지문이 통과했습니다.")
    except ValueError as e:
        assert "너무 짧" in str(e) and "4개" in str(e), e

    # 3) 사용자 화면에는 pydantic 원문이 아니라 읽을 수 있는 안내가 간다
    sys.path.insert(0, str(ROOT))
    from web.app import _readable_error

    raw = ("[0] 생성 실패: 검증 실패(재시도 소진): 1 validation error for Analysis\n"
           "sentences\n  Value error, 문장이 4개 미만입니다(지문이 너무 짧음). "
           "[type=value_error, input_value=[], input_type=list]\n"
           "    For further information visit https://errors.pydantic.dev/2.13/v/value_error")
    msg = _readable_error(Exception(raw))
    assert "지문이 너무 짧거나" in msg, msg
    assert "pydantic" not in msg and "value_error" not in msg, msg
    assert "요청이 잠시 몰렸" in _readable_error(Exception("Error code: 429 rate_limit"))
    assert "API 키가" in _readable_error(Exception("Error code: 401 authentication_error"))
    print("✓ 분석 문장은 코드가 정한다(모델 출력 무관)·짧은 지문 사전 거절·오류 문구 통과")


def test_batch_client() -> None:
    """비용 절반(Batch API): 흩어진 요청을 한 배치로 모아 보내고, 각 호출에
    같은 결과를 돌려준다. 생성기 코드는 그대로다(클라이언트만 교체)."""
    import io as _io
    import threading as _th
    from concurrent.futures import ThreadPoolExecutor

    from exam.batch_client import BatchingClaudeClient
    from exam.progress import Progress

    class _Msg:                                   # 응답 메시지(텍스트 블록 1개)
        def __init__(self, text): self.content = [type("B", (), {"type": "text", "text": text})()]

    class _Res:
        def __init__(self, cid, kind, text=""):
            self.custom_id = cid
            self.result = type("R", (), {"type": kind, "message": _Msg(text)})()

    class _FakeBatches:
        """가짜 Batch API — 제출된 요청 크기를 기록하고 즉시 '완료'로 응답한다."""

        def __init__(self, answer):
            self.answer = answer                  # (req, seq) -> (kind, text)
            self.sizes: list[int] = []
            self._store: dict[str, list] = {}
            self._n = 0
            self._lock = _th.Lock()

        def create(self, requests):
            with self._lock:
                self.sizes.append(len(requests))
                self._n += 1
                bid = f"batch_{self._n}"
                seq = self._n
            self._store[bid] = [_Res(r["custom_id"], *self.answer(r["params"], seq))
                                for r in requests]
            return type("B", (), {"id": bid})()

        def retrieve(self, bid):
            return type("B", (), {"id": bid, "processing_status": "ended"})()

        def results(self, bid):
            return self._store[bid]

    class _Client(BatchingClaudeClient):
        def __init__(self, answer, **kw):        # 상위 __init__ 우회(네트워크 없이 생성)
            self.model, self.thinking, self.effort = "m", False, None
            self._window = kw.pop("window", 0.5)
            self._poll, self._progress, self._logger = 1.0, kw.pop("progress", None), None
            self._lock = _th.Lock()
            self._pending, self._flusher, self._batch_no = [], None, 0
            self._fake = _FakeBatches(answer)

        @property
        def raw(self):
            return type("R", (), {"messages": type("M", (), {"batches": self._fake})()})()

    def _title(params) -> str:
        return params["output_config"]["format"]["schema"]["title"]

    def _demo(params, _seq):                       # 스키마 이름으로 가짜 응답을 고른다
        return "succeeded", _FAKE[_title(params)]().model_dump_json()

    # ① 흩어진 동시 호출이 '한 배치'로 모인다
    c = _Client(_demo)
    with ThreadPoolExecutor(max_workers=30) as ex:
        outs = list(ex.map(lambda _i: c.structured("s", "p", TopicOut), range(30)))
    assert len(outs) == 30 and all(o.answer_no == 2 for o in outs)
    assert c._fake.sizes == [30], c._fake.sizes      # 30건 → 배치 1회

    # ② 검증 실패는 지시문을 덧붙여 다음 배치에서 재시도한다
    def _retry(params, seq):
        return ("succeeded", "{oops" if seq == 1 else _FAKE[_title(params)]().model_dump_json())

    c2 = _Client(_retry)
    assert c2.structured("s", "p", TopicOut).answer_no == 2
    assert c2._fake.sizes == [1, 1], c2._fake.sizes  # 첫 배치 실패 → 두 번째 배치 성공

    # ③ 재시도를 다 써도 실패하면 사람이 읽을 오류로 끝난다
    c3 = _Client(lambda p, s: ("succeeded", "{oops"))
    try:
        c3.structured("s", "p", TopicOut)
        raise AssertionError("검증 실패가 통과했다")
    except RuntimeError as e:
        assert "재시도 소진" in str(e), e

    # ④ 배치 자체가 실패하면 그대로 전달된다(조용히 성공한 척하지 않는다)
    c4 = _Client(lambda p, s: ("errored", ""))
    try:
        c4.structured("s", "p", TopicOut, max_retries=0)
        raise AssertionError("배치 오류가 통과했다")
    except RuntimeError as e:
        assert "배치 요청 실패" in str(e), e

    # ⑤ 실제 파이프라인이 그대로 돈다 — 생성기 수정 없이 배치로만 바뀐다
    buf = _io.StringIO()
    prog = Progress(total=2, stream=buf)
    c5 = _Client(_demo, progress=prog)
    ps = build_passages_merged(c5, [_DUMMY, _DUMMY2], labels=["10-1", "10-2"], progress=prog)
    assert [p.source_label for p in ps] == ["10-1", "10-2"]
    assert len(ps[0].q) >= 7, len(ps[0].q)
    #    요청 수십 건이 배치 열 몇 개로 뭉쳐진다(건건이 나가지 않는다)
    assert sum(c5._fake.sizes) > 10 and len(c5._fake.sizes) <= 12, c5._fake.sizes
    assert "배치 #1 제출" in buf.getvalue() and "정가의 50%" in buf.getvalue()
    print("✓ Batch API 클라이언트(요청 모으기·재시도·오류 전달·파이프라인) 통과")


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
    test_progress_output()
    test_parallel_passages_and_gate()
    test_output_modes()
    test_edge_guards()
    test_precheck_harness()
    test_short_answer_q3_summary_dedup()
    test_rerender_relabel()
    test_new_type_guards()
    test_tiering_and_escalation()
    test_order_four_blocks()
    test_overlap_and_paraphrase_guards()
    test_grammar_count_fixed_four()
    test_demo_matches_real_rules()
    test_output_defect_regressions()
    test_ox_axes()
    test_ox_short_passage()
    test_direct_sale_guards()
    test_grammar_on_original_passage()
    test_type_group_layout()
    test_output_checker()
    test_stress_fixtures()
    test_analysis_sentences_are_ours()
    test_merged_set()
    test_batch_client()
    print("\n모든 오프라인 테스트 통과 ✅")
