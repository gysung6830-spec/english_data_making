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
    ha = renderer.render_a_html([a], footer_note="(C)2026", footer_meta="분석서")
    assert "ribbon" in ha and "pbox" in ha
    assert "necessity of openness" in ha            # 제목
    assert "what(X)" in ha and "designed(X)" in ha  # 오답형 표시
    assert "내용 TMI" in ha and "어법 Point" in ha    # 두 종류 박스 캡션
    assert "hl-p" in ha                             # 라벤더 하이라이트(담화표지)
    assert "Even the finest tea" in ha             # 함축 gloss 줄
    hb = renderer.render_b_html([a], tagged=False)
    assert "hbar" in hb and "①" in hb and "②" in hb and "③" in hb
    hb_tagged = renderer.render_b_html([a], tagged=True)
    assert "tok" in hb_tagged
    print("PASS  렌더러 A/B HTML")


def test_render_back_page():
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert 'class="bhead"' in ha                       # 뒷페이지 존재
    assert 'class="vtab"' in ha and 'class="flow"' in ha
    assert 'class="ez"' in ha                          # 논리 흐름 + 쉬운 예시 통합
    assert "impermeable" in ha and "flourish" in ha    # 어휘/유의어
    assert "비유 제시" in ha                             # 흐름 단계
    # 뒷페이지 데이터가 없는 Analysis 는 back 페이지를 만들지 않는다
    from src.worksheet.models import Analysis
    plain = Analysis(title_en="x", sentences=a.sentences)
    assert 'class="bhead"' not in renderer.render_a_html([plain])
    print("PASS  뒷페이지(어휘 + 논리흐름·쉬운예시)")


def test_feed_point_box():
    # 대명사 지칭 + 함축 = 파랑 '떠먹여주는 Point' 박스로 렌더
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert 'class="pbox feed"' in ha and "떠먹여주는 Point" in ha
    assert "the teabag" in ha        # 대명사 지칭(refs)
    assert "Even the finest tea" in ha  # 함축(gloss_en) 도 이 박스 안에
    print("PASS  떠먹여주는 Point(대명사+함축) 박스")


def test_pronoun_referent_in_refs():
    # 대명사 지칭 대상이 토큰 주석이 아니라 refs 로 분리됐는지
    a = mock_analysis()
    refs = [r for s in a.sentences for r in s.refs]
    assert any("→" in r for r in refs)
    print("PASS  대명사 지칭 refs 분리")


def test_page_break_per_passage():
    # 지문마다 앞면 .head + 뒷면 .bhead 페이지로 분리되는지 확인.
    a = mock_analysis()
    html = renderer.render_a_html([a, a, a])
    assert html.count('class="head"') == 3      # 앞면 3개
    assert html.count('class="bhead"') == 3     # 뒷면 3개
    print("PASS  지문당 페이지 분리(앞/뒤)")


def test_overview_builder_llm_path():
    payload = json.dumps({
        "vocab": [{"word": "thrive", "meaning": "번성하다", "syn": "flourish",
                   "ant": "decline", "sent": 6}],
        "flow": [{"label": "도입", "text": "화제 제시",
                  "easy": "궁금하면 스스로 파고드는 거랑 같음", "sentences": "1"}],
    })
    from src.worksheet import overview_builder
    from src.worksheet.models import Analysis, Sentence
    client = _fake_client([payload])
    a = Analysis(title_en="x", sentences=[Sentence(index=1, lines=[[Token(text="Hi")]])])
    vocab, flow = overview_builder.build_overview(client, a)
    assert vocab and vocab[0].word == "thrive" and vocab[0].syn == "flourish"
    assert flow and flow[0].label == "도입" and flow[0].easy.startswith("궁금")
    print("PASS  overview_builder LLM 경로")


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
    test_render_back_page()
    test_feed_point_box()
    test_pronoun_referent_in_refs()
    test_page_break_per_passage()
    test_overview_builder_llm_path()
    test_webapp_worksheet_flow()
    print("\n구문 분석 학습지 오프라인 테스트 모두 통과 ✅")


if __name__ == "__main__":
    run_all()
