"""API 없이 돌아가는 오프라인 테스트.

실행: python -m tests.test_offline   (또는 pytest)
검증 항목:
  - PDF 전처리(문제/정답 제거)
  - 스키마 검증 (문법 정확히 10개, 어휘 개수 범위)
  - 검증 실패 시 재시도 로직
  - HTML 렌더링
"""
from __future__ import annotations

import json
import types

from src import extract, prompts, render, schemas
from src.client import ClaudeClient, DEFAULT_MAX_TOKENS


# ---- 1. 전처리: 문제/정답/보기 제거 ----------------------------------------
def test_clean_removes_noise():
    raw = (
        "The Value of Curiosity\n"
        "Curiosity drives us to explore.\n"
        "1. What is the main idea?\n"
        "① Memorizing answers.\n"
        "② Curiosity is valuable.\n"
        "정답: ②\n"
        "해설: 호기심이 핵심이다.\n"
    )
    cleaned = extract.clean_text(raw)
    assert "Curiosity drives us" in cleaned
    assert "정답" not in cleaned
    assert "①" not in cleaned
    assert "What is the main idea" not in cleaned
    print("PASS  전처리(노이즈 제거)")


# ---- 2. 스키마 검증: 문법은 비어있지 않으면 개수 제한 없음 -------------------
def test_grammar_non_empty():
    try:
        schemas.GrammarSection.model_validate({"items": []})
        assert False, "빈 목록은 통과하면 안 됨"
    except Exception:
        pass
    # 개수 제한이 없으므로 3개든 15개든 통과해야 함
    for n in (3, 15):
        items = [{"no": i, "point": "p", "example": "e", "explanation": "x", "sentence_no": i}
                 for i in range(1, n + 1)]
        schemas.GrammarSection.model_validate({"items": items})
    print("PASS  문법 개수 제한 없음(비어있지만 않으면 OK)")


# ---- 3. 어휘 개수 범위 -----------------------------------------------------
def test_vocab_count_range():
    items = [{"no": i, "word": "w", "meaning": "m"} for i in range(1, 6)]  # 5개
    v = schemas.VocabSection.model_validate({"items": items})
    try:
        v.validate_count(12, 20)
        assert False, "범위 밖인데 통과하면 안 됨"
    except ValueError:
        pass
    print("PASS  어휘 개수 범위 검증")


# ---- 4. 재시도 로직 (가짜 클라이언트) --------------------------------------
class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        text = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        block = types.SimpleNamespace(type="text", text=text)
        return types.SimpleNamespace(content=[block])


def test_retry_recovers():
    # 어휘 개수 범위(12~20) 검증으로 재시도를 유도한다.
    def vocab(n):
        return json.dumps({"items": [{"no": i, "word": "w", "meaning": "m"} for i in range(1, n + 1)]})
    bad = vocab(5)     # 5개 -> 범위 밖 -> 실패
    good = vocab(13)   # 13개 -> 통과

    client = ClaudeClient.__new__(ClaudeClient)    # __init__ 우회(가짜 주입)
    client.model = "test"
    client._client = types.SimpleNamespace(messages=_FakeMessages([bad, good]))

    result = client.structured(
        prompts.SYSTEM, "x", schemas.VocabSection, max_retries=1,
        extra_validate=lambda v: v.validate_count(12, 20),
    )
    assert len(result.items) == 13
    assert client._client.messages.calls == 2  # 1회 실패 후 1회 재시도
    print("PASS  검증 실패 후 재시도 복구")


# ---- 5. 렌더링 ------------------------------------------------------------
def test_render_html():
    from samples.sample_mock import mock_report
    html = render.render_html(mock_report(), footer_note="테스트")
    assert "직독직해" in html and "made by 은아 T" in html
    assert "핵심 어휘" in html and "출제 포인트" in html
    assert "The Value of Curiosity" in html
    print("PASS  HTML 렌더링")


# ---- 6. 서술형 교재 스키마 검증 ------------------------------------------
def test_worksheet_schema():
    # 유형2(문장 변형·주관식): 빈칸이 있어야 함
    ok = {"original": "x", "sentence": "a [[A]] b [[B]]",
          "blanks": [{"label": "A", "answer": "x"}, {"label": "B", "answer": "y"}]}
    schemas.WSParaphraseQ.model_validate(ok)
    try:
        schemas.WSParaphraseQ.model_validate({**ok, "blanks": []})
        assert False, "빈칸 0개는 통과하면 안 됨"
    except Exception:
        pass
    # 유형5(보기 어휘): 사용되지 않는 낱말은 정확히 3개
    base_set = {"choices": ["a", "b", "c", "d", "e", "f", "g"],
                "sentences": [{"label": "A", "text": "[[A]]", "answer": "a"}],
                "unused": ["e", "f", "g"]}
    schemas.WSClozeSet.model_validate(base_set)
    try:
        schemas.WSClozeSet.model_validate({**base_set, "unused": ["e"]})
        assert False, "미사용 1개는 통과하면 안 됨"
    except Exception:
        pass
    # 유형6(어법): 오류가 최소 1곳·정상도 최소 1곳(개수 완화) + 마커↔밑줄 일치
    s5 = "".join("{{%d|t}}" % i for i in range(1, 6))  # {{1|t}}..{{5|t}}
    good = [{"no": i, "text": "t", "wrong": i <= 3} for i in range(1, 6)]
    schemas.WSErrorItem.model_validate({"sentence": s5, "underlines": good})
    two = [{"no": i, "text": "t", "wrong": i <= 2} for i in range(1, 6)]
    schemas.WSErrorItem.model_validate({"sentence": s5, "underlines": two})  # 2곳도 통과
    # 오류 0곳(전부 정상)은 여전히 거부되어야 함
    rejected = False
    try:
        none_wrong = [{"no": i, "text": "t", "wrong": False} for i in range(1, 6)]
        schemas.WSErrorItem.model_validate({"sentence": s5, "underlines": none_wrong})
    except Exception:
        rejected = True
    assert rejected, "오류 0곳은 거부되어야 함"
    # 마커 수가 밑줄 수와 다르면 거부(마커↔밑줄 런타임 검증)
    mism = False
    try:
        schemas.WSErrorItem.model_validate({"sentence": "{{1|t}}", "underlines": good})
    except Exception:
        mism = True
    assert mism, "마커/밑줄 불일치는 거부되어야 함"
    print("PASS  서술형 교재 스키마 검증")


# ---- 7. 서술형 교재 렌더링 (4파트 · 6개 유형) -----------------------------
def test_worksheet_render():
    from samples.sample_mock import mock_worksheet
    from src import render
    # 빈칸 치환: 학생용은 빈칸(정답 숨김), 교사용은 정답 노출
    student = render._sub_labeled("stay [[A]] in class", {"A": "motivated"}, False)
    teacher = render._sub_labeled("stay [[A]] in class", {"A": "motivated"}, True)
    assert "ws-blank" in student and "motivated" not in student
    assert "motivated" in teacher and "(A)" in teacher
    # 일련번호가 'type-major'로 매겨지는지(복수 지문이면 유형별로 지문을 모아서)
    passages = render._ws_context([mock_worksheet(), mock_worksheet("Second")])
    # 유형1(cloze)이 가장 먼저(1번부터), 지문1 다음 지문2로 이어짐
    assert passages[0]["cloze"][0]["qno"] == 1
    assert passages[1]["cloze"][0]["qno"] > passages[0]["cloze"][-1]["qno"]
    # 유형2(summary) 번호는 유형1(cloze) 전체 번호보다 뒤
    assert passages[0]["summary"][0]["qno"] > passages[1]["cloze"][-1]["qno"]
    # 전체 PDF 렌더가 예외 없이 되고 파일이 생성되는지
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "ws.pdf"
        render.render_worksheet_pdf([mock_worksheet(), mock_worksheet("Second")],
                                    out, footer_note="테스트")
        assert out.is_file() and out.stat().st_size > 1000
    print("PASS  서술형 교재 렌더링(4파트·2지문)")


# ---- 8. 서술형 교재 내용 정합성(오류 검증) --------------------------------
def test_worksheet_consistency():
    import re
    from samples.sample_mock import mock_worksheet
    ws = mock_worksheet()
    UL = re.compile(r"\{\{(\d+)\|([^}]*)\}\}")
    LBL = re.compile(r"\[\[([A-Z])\]\]")

    # 어법: 밑줄 마커 수=underlines, 오류 정확히 3곳, 마커텍스트 일치, 오류엔 correction
    for it in ws.error.items:
        mm = {int(n): t for n, t in UL.findall(it.sentence)}
        assert len(mm) == len(it.underlines)
        assert sum(u.wrong for u in it.underlines) == 3
        for u in it.underlines:
            assert mm.get(u.no) == u.text
            assert (u.correction != "") == u.wrong

    # 보기어휘: used(4) + unused(3) == choices(7), 서로 배타적
    for s in ws.choice.sets:
        used = [se.answer for se in s.sentences]
        assert len(s.unused) == 3
        assert not (set(used) & set(s.unused))
        assert sorted(set(used) | set(s.unused)) == sorted(set(s.choices))

    # 문장변형: 오답 2개(정답과 배타), 문장 라벨==blanks 라벨
    for q in ws.paraphrase.questions:
        ans = {b.answer for b in q.blanks}
        assert len(q.distractors) == 2 and not (set(q.distractors) & ans)
        assert set(LBL.findall(q.sentence)) == {b.label.upper() for b in q.blanks}

    # 문답: 정답 존재 + 근거(evidence)는 반드시 지문 안의 문장(추론 금지)
    for q in ws.qa.items:
        assert q.answer.strip()
        if q.evidence:
            assert q.evidence.strip().rstrip(".") in ws.passage
    print("PASS  서술형 교재 내용 정합성(오류 검증)")


# ---- 9. HWP/HWPX 텍스트 추출 ---------------------------------------------
def test_hwp_extract():
    import struct, zipfile, tempfile
    from pathlib import Path
    from src import extract
    # (1) .hwpx: 합성 OWPML zip → 문단 텍스트 추출
    sec = ('<hml:sec xmlns:hp="x">'
           '<hp:p><hp:run><hp:t>Curiosity drives us.</hp:t></hp:run></hp:p>'
           '<hp:p><hp:run><hp:t>Ask questions.</hp:t></hp:run></hp:p></hml:sec>')
    with tempfile.TemporaryDirectory() as d:
        hp = Path(d) / "t.hwpx"
        with zipfile.ZipFile(hp, "w") as z:
            z.writestr("Contents/section0.xml", sec)
        out = extract.extract_hwpx_text(hp)
        assert "Curiosity drives us." in out and "Ask questions." in out
        assert extract.is_hwp(hp) and not extract.is_hwp("x.pdf")
    # (2) .hwp 바이너리 레코드 파서: PARA_TEXT + 인라인 컨트롤 무시
    payload = "Hello".encode("utf-16-le") + struct.pack("<H", 3) + b"\x00" * 14
    header = 67 | (len(payload) << 20)
    rec = struct.pack("<I", header) + payload
    assert extract._hwp_section_text(rec) == "Hello"
    # 추출 부실 신호: 영어 전용은 오탐 없음(False), 영한 2단 혼합은 True
    eng = "\n".join(["Curiosity drives us to explore the unknown."] * 8)
    mixed = "\n".join(["Criminals leave traces 범죄자는 흔적을 남긴다."] * 8)
    assert not extract.looks_garbled(eng)
    assert extract.looks_garbled(mixed)
    # 한줄해석(영어 조각 ↔ 한글 해석 세로 스택) 포맷도 감지되어야 함
    hanjul = ("[EBS] 올림포스 영어독해 기본1 한줄해석\n"
              "shoppers a sample of coffee from one of the mugs\n"
              "유쾌함을 포함한 품질을 위한 맛을 평가하도록 요청했다.\n"
              "mug the same drinks tasted up to 27 percent more bitter\n"
              "느껴졌다.\n"
              "go for a round bowl and mug\n"
              "머그잔을 사용하는 것이 좋다.")
    assert extract.looks_garbled(hanjul)
    # 영어 지문 + 한글 헤더 1줄은 오탐 없어야(False)
    mostly_en = "\n".join(["The value of curiosity is well documented."] * 6 + ["출처: 어딘가"])
    assert not extract.looks_garbled(mostly_en)
    print("PASS  HWP/HWPX 텍스트 추출 + 추출부실 감지")


# ---- 10. 서술형 교재 JSON 저장/복원(API 없이 제목만 바꿔 재렌더) ----------
def test_worksheet_json_roundtrip():
    import tempfile
    from pathlib import Path
    from samples.sample_mock import mock_worksheet
    from src import pipeline

    ws = [mock_worksheet(), mock_worksheet("Second")]
    with tempfile.TemporaryDirectory() as d:
        jp = Path(d) / "ws.json"
        pipeline.save_worksheets_json(ws, jp, title="원제목", start_no=3, passage_start_no=2)
        ws2, meta = pipeline.load_worksheets_json(jp)
        # 데이터가 그대로 복원되고 메타(제목·시작번호)도 유지되어야 함
        assert len(ws2) == 2
        assert meta["title"] == "원제목" and meta["start_no"] == 3 and meta["passage_start_no"] == 2
        assert ws2[0].error.items[0].sentence == ws[0].error.items[0].sentence
        # 형식이 아닌 JSON 은 거부
        bad = Path(d) / "bad.json"
        bad.write_text('{"kind":"other"}', encoding="utf-8")
        rejected = False
        try:
            pipeline.load_worksheets_json(bad)
        except Exception:
            rejected = True
        assert rejected, "형식 불일치 JSON 은 거부되어야 함"
    print("PASS  서술형 교재 JSON 저장/복원(무API 재편집)")


# ---- 11. 영작 보기 단어 ↔ 정답 문장 정합성(누락/잉여/어형) -----------------
def test_compose_arrange_word_guard():
    from src import schemas
    # 배열영작: 정답에 없는 보기 제거 + 빠진 단어 보완(어형 흡수: child↔Children)
    a = "Children who are encouraged to ask questions retain their curiosity longer."
    it = schemas.WSArrangeItem(korean="k", answer=a,
                               given_words=["child", "encourage", "BOGUS", "retain"])
    toks = schemas._WORD_RE.findall(a)
    assert "BOGUS" not in it.given_words                       # 잉여 제거
    assert all(any(schemas._word_match(g, t) for g in it.given_words) for t in toks)  # 전부 커버
    # 조건영작: 정답에 없는 힌트 제거, 어형(ask↔Asking)은 유지
    c = schemas.WSComposeItem(korean="k", answer="Asking questions matters in learning.",
                              given_low=["ask", "matter", "FAKE"], given_mid=["ask", "FAKE"])
    assert "ask" in c.given_low and "FAKE" not in c.given_low and "FAKE" not in c.given_mid
    print("PASS  영작 보기 단어↔정답 정합성(누락/잉여/어형)")


# ---- 12. 부분 재생성(누락 유형만 다시 생성) ------------------------------
def test_regenerate_missing_only():
    from samples.sample_mock import mock_worksheet
    from src import analyze, schemas
    from src.config import load_config

    cfg = load_config()
    cfg.processing.parallel_sections = False
    cfg.processing.verify_content = False

    ws = mock_worksheet()
    orig_error = ws.error
    ws = ws.model_copy(update={"paraphrase": None})   # 문장변형 누락 상황

    class _Fake:
        model = "test"
        def structured(self, S, prompt, cls, **kw):
            if cls is schemas.WSParaphraseType:
                return schemas.WSParaphraseType(questions=[schemas.WSParaphraseQ.model_validate(
                    {"original": "o", "sentence": "a [[A]] b [[B]]",
                     "blanks": [{"label": "A", "answer": "x"}, {"label": "B", "answer": "y"}],
                     "distractors": ["p", "q"]})])
            raise AssertionError("누락 아닌 유형까지 호출됨: " + cls.__name__)

    new = analyze.regenerate_worksheet(_Fake(), cfg, ws)
    assert new.paraphrase is not None      # 누락 유형 채워짐
    assert new.error is orig_error         # 나머지 유형 그대로(재호출 없음)
    print("PASS  부분 재생성(누락 유형만·나머지 보존)")


def run_all():
    test_clean_removes_noise()
    test_grammar_non_empty()
    test_vocab_count_range()
    test_retry_recovers()
    test_render_html()
    test_worksheet_schema()
    test_worksheet_render()
    test_worksheet_consistency()
    test_hwp_extract()
    test_worksheet_json_roundtrip()
    test_compose_arrange_word_guard()
    test_regenerate_missing_only()
    print("\n모든 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
