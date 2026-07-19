"""구문 분석 학습지(worksheet) 오프라인 테스트.

실행: python -m tests.test_worksheet   (또는 pytest)
API 없이 splitter/analyzer(규칙+가짜LLM)/point_builder/renderer/webapp 을 검증한다.
"""
from __future__ import annotations

import io
import json
import types

from src.client import ClaudeClient
from src.worksheet import analyzer, point_builder, renderer, splitter
from src.worksheet.llm_schemas import PointBundle, SentenceAnalysis
from src.worksheet.mock import mock_analysis
from src.worksheet.models import Analysis, Point, Sentence, Token
from src.worksheet.pipeline import Header


# ---- 1. splitter -----------------------------------------------------------
def test_splitter_circled():
    segs = splitter.split_sentences("① First one. ② Second here. ③ Third.")
    assert segs == ["First one.", "Second here.", "Third."]
    print("PASS  splitter 원문자 분할")


def test_splitter_punct_protects_abbrev_and_decimal():
    segs = splitter.split_sentences("Dr. Smith found 3.5 kg. It worked! Really?")
    assert segs == ["Dr. Smith found 3.5 kg.", "It worked!", "Really?"], segs
    print("PASS  splitter 약어/소수점 보호")


# ---- 2. analyzer 규칙기반 --------------------------------------------------
def test_rule_hints():
    hints = analyzer.rule_hints("The book which was written by her is loved.")
    joined = " ".join(hints)
    assert "관계사" in joined and "수동태" in joined
    print("PASS  analyzer 규칙 힌트")


def test_rule_only_sentence_and_none():
    s = analyzer.rule_only_sentence("Students studying hard succeed.", 1, tag=True)
    assert any(t.note for t in s.tokens)
    s_none = analyzer.rule_only_sentence("Just plain text here.", 2, tag=False)
    assert all(t.note is None and t.role is None for t in s_none.tokens)
    print("PASS  analyzer 규칙 초안 / 태깅 없음")


# ---- 3. 가짜 LLM 으로 analyzer/point_builder 경로 검증 ----------------------
class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        text = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=text)])


def _fake_client(responses):
    client = ClaudeClient.__new__(ClaudeClient)
    client.model = "test"
    client._client = types.SimpleNamespace(messages=_FakeMessages(responses))
    return client


def test_analyze_sentence_llm_path():
    payload = json.dumps({
        "lines": [{"tokens": [
            {"text": "The cat", "role": "S"},
            {"text": "caught", "role": "V", "note": "과거시제", "note_kind": "gray"},
            {"text": "the mouse", "role": "O", "wrong": "mice(X)"},
        ]}],
        "translation": "그 고양이가 그 쥐를 잡았다.",
        "badge": "예시",
    })
    client = _fake_client([payload])
    s = analyzer.analyze_sentence(client, "The cat caught the mouse.", 3, strength="full")
    assert isinstance(s, Sentence) and s.index == 3 and s.badge == "예시"
    roles = [t.role for t in s.tokens if t.role]
    assert roles == ["S", "V", "O"]
    assert s.translation.startswith("그 고양이")
    assert any(t.wrong == "mice(X)" for t in s.tokens)
    print("PASS  analyzer LLM 경로 → Sentence 변환")


def test_build_points_llm_path():
    payload = json.dumps({"points": [
        {"kind": "grammar", "caption": "3번 문장 어법 Point",
         "body_html": "<b>caught</b> 는 과거시제.<script>bad()</script>"},
        {"kind": "reading", "caption": "3번 문장 독해 Point", "body_html": "핵심은 <b>포식</b>."},
    ]})
    client = _fake_client([payload])
    s = Sentence(index=3, lines=[[Token(text="x")]], translation="")
    pts = point_builder.build_points(client, s, strength="full")
    assert len(pts) == 2
    grammar = [p for p in pts if p.is_grammar][0]
    # 허용 태그(<b>)는 유지, 위험 태그(<script>)는 이스케이프
    assert "<b>caught</b>" in grammar.body_html
    assert "<script>" not in grammar.body_html and "&lt;script&gt;" in grammar.body_html
    print("PASS  point_builder LLM 경로 + HTML 새니타이즈")


def test_build_points_fallback_to_rules():
    # LLM 이 빈 points → analyzer 태그 기반 어법 Point 로 폴백
    client = _fake_client([json.dumps({"points": []})])
    s = Sentence(index=1, lines=[[
        Token(text="which", note="주격 관계대명사", note_kind="red", wrong="that(X)"),
    ]], translation="")
    pts = point_builder.build_points(client, s, strength="full")
    assert len(pts) == 1 and pts[0].is_grammar
    assert "주격 관계대명사" in pts[0].body_html
    print("PASS  point_builder 규칙 폴백")


# ---- 4. 렌더러 A/B ---------------------------------------------------------
def test_render_a_and_b():
    a = mock_analysis()
    ha = renderer.render_a_html([a], footer_note="(C)2026")
    assert "ribbon" in ha and "pbox" in ha and "The Paradox of Choice" in ha
    assert "offering(X)" in ha and "현재완료" in ha  # 오답형/주석 표시
    hb = renderer.render_b_html([a], tagged=False)
    assert "hbar" in hb and "①" in hb and "②" in hb and "③" in hb
    # tagged=False 면 태깅 클래스 대신 원문만
    hb_tagged = renderer.render_b_html([a], tagged=True)
    assert "tok" in hb_tagged
    print("PASS  렌더러 A/B HTML")


def test_page_break_per_passage():
    from weasyprint import HTML
    a = mock_analysis()
    html = renderer.render_a_html([a, a, a])
    pages = len(HTML(string=html).render().pages)
    assert pages == 3, f"지문 3개 → 3페이지 예상, got {pages}"
    print("PASS  지문당 페이지 분리")


# ---- 5. 웹앱 (test_client, 목 미리보기) ------------------------------------
def test_webapp_worksheet_flow():
    import webapp
    c = webapp.app.test_client()
    assert c.get("/worksheet").status_code == 200
    for layout in ("A", "B"):
        data = {"layout": layout, "strength": "full", "basename": f"t_{layout}",
                "lecture_label": "20", "mock": "1",
                "files": (io.BytesIO(b"x"), f"s_{layout}.pdf")}
        r = c.post("/worksheet/build", data=data, content_type="multipart/form-data")
        assert r.status_code == 200 and "완료".encode("utf-8") in r.data
    print("PASS  웹앱 학습지 플로우(A/B, 목)")


def run_all():
    test_splitter_circled()
    test_splitter_punct_protects_abbrev_and_decimal()
    test_rule_hints()
    test_rule_only_sentence_and_none()
    test_analyze_sentence_llm_path()
    test_build_points_llm_path()
    test_build_points_fallback_to_rules()
    test_render_a_and_b()
    test_page_break_per_passage()
    test_webapp_worksheet_flow()
    print("\n구문 분석 학습지 오프라인 테스트 모두 통과 ✅")


if __name__ == "__main__":
    run_all()
