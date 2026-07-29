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


def test_splitter_ellipsis_fragments():
    # 생략부호(...)로 시작하는 조각형 지문이 한 문장으로 뭉치지 않고 분리돼야 한다.
    raw = ("...and to spend extended periods of time sharing activities. "
           "...conversational and non-verbal forms (facial expressions, and so on). "
           "...we exist and that we have an identity. "
           "Thus, we cannot exist for too long without seeking companionship.")
    segs = splitter.split_sentences(raw)
    assert len(segs) == 4, segs
    assert segs[0].startswith("...and to spend") and segs[0].endswith("activities.")
    assert segs[1].startswith("...conversational")
    assert segs[3].startswith("Thus,")
    # 유니코드 생략부호(…)도 동일하게 처리
    assert len(splitter.split_sentences("A ends here. …B starts. …C ends.")) == 3
    print("PASS  splitter 생략부호 조각 분리")


def test_extract_strip_korean_layouts():
    # PDF 배치 무관하게 영어 원문만 남는지: 좌영어우한글 / 영어만 / 영어줄·한글줄 교차
    from src import extract
    sk = extract.strip_korean_keep_english
    # (a) 좌 영어 / 우 한글 (한 줄에 섞여 읽힘)
    a = sk("Humans are social.  인간은 사회적이다.\nThey seek others.  그들은 타인을 찾는다.")
    assert "인간" not in a and "그들" not in a
    assert "Humans are social." in a and "They seek others." in a
    # (b) 영어만 → 무변경
    b = "Humans are social.\nThey seek others."
    assert sk(b) == b
    # (c) 영어 줄 / 한글 줄 교차 → 한글 줄 제거
    c = sk("Humans are social.\n인간은 사회적이다.\nThey seek others.\n그들은 타인을 찾는다.")
    assert "인간" not in c and "Humans are social." in c and "They seek others." in c
    # 토큰에 한글이 붙어도 영문은 보존(cat고양이 → cat)
    assert sk("the cat고양이 sat앉다 down") == "the cat sat down"
    print("PASS  PDF 배치 무관 영어 추출(좌우2단/영어만/교차)")


def test_splitter_missing_space_and_paragraphs():
    # 인식 오류 방지: 마침표 뒤 공백이 없어도(비전/OCR) 대문자면 문장을 나눈다.
    segs = splitter.split_sentences("Humans are social.They seek others.We need it.")
    assert segs == ["Humans are social.", "They seek others.", "We need it."], segs
    # 문단(빈 줄)으로만 구분되고 마침표가 없는 조각도 서로 뭉치지 않는다.
    para = splitter.split_sentences("First idea here\n\nSecond follows.\n\nThird wraps up")
    assert len(para) == 3 and para[0] == "First idea here", para
    print("PASS  splitter 공백누락·문단 분리(한 줄 뭉침 방지)")


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
    assert "어법 Point" in ha and "떠먹여주는 Point" in ha  # 남은 두 종류 박스
    assert "내용 TMI" not in ha                       # 내용 TMI 삭제됨
    assert "①" in ha                                # 어법 넘버링(원문자)
    assert "hl-p" in ha                             # 라벤더 하이라이트(담화표지)
    assert "Even the finest tea" in ha             # 함축 gloss 줄
    hb = renderer.render_b_html([a], brand="은아 T")
    # 직독직해형: 주황 헤더 + made by 브랜드 + 2단 표 + 문법 태그 + 핵심 단어
    assert "lbar" in hb and "직독직해" in hb and "made by 은아 T" in hb
    assert "lit2" in hb and 'class="snum"' in hb
    assert "★필수" in hb and "gtag" in hb           # 필수 어법 태그
    assert "주격 관계대명사 that" in hb               # 문법 포인트명
    assert "lit-words" in hb and "impermeable" in hb  # 핵심 단어
    assert "쉽게" in hb                              # '쉽게' 요약 줄
    assert '<span class="sl">/</span>' in hb         # 청크 구분 슬래시
    # brand 를 비우면 made by 문구가 사라진다
    assert 'class="made"' not in renderer.render_b_html([a], brand="")
    print("PASS  렌더러 A/B HTML(직독직해형)")


def test_render_reading_and_box():
    # 끊어읽기: 영어 슬래시(/) + 직독직해(한글) 줄 + 온전한 해석 박스
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert 'class="rdko"' in ha and "직독직해" in ha        # 직독직해(끊어읽기) 줄
    assert 'class="kobox"' in ha and 'class="kblbl"' in ha  # 온전한 해석 박스
    assert 'class="sl"' in ha                               # 영어 끊어읽기 경계 /
    # 직독직해 청크가 / 로 나뉘어 렌더되는지
    assert 'class="rc"' in ha
    print("PASS  끊어읽기(직독직해) + 온전한 해석 박스")


def test_render_guide_cover():
    # 맨 앞 '활용 가이드' 표지: 색·기호 뜻 + 사용법. include_guide 로 토글.
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert "활용법" in ha and "색 · 기호가 뜻하는 것" in ha   # 표지 존재
    assert "오답형 함정" in ha and "떠먹여주는 Point" in ha    # 색 범례 항목
    assert "이렇게 쓰세요" in ha                              # 사용법 단계
    # 표지 없이도 렌더 가능(측정/옵션용)
    assert "활용법" not in renderer.render_a_html([a], include_guide=False)
    print("PASS  맨 앞 활용 가이드 표지(색·기호 뜻 + 사용법)")


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


def test_grammar_numbering():
    from src.worksheet import point_builder
    from src.worksheet.models import Sentence, Token
    s = Sentence(index=3, lines=[[
        Token(text="that", note="주격 관계대명사", note_kind="red", wrong="who(X)"),
        Token(text="cat"),
        Token(text="was seen", note="수동태", note_kind="red"),
    ]])
    gp = point_builder.build_grammar_point(s)
    assert gp is not None and gp.is_grammar
    # 인라인 주석은 원문자 번호로 치환, 글자는 빨강
    toks = s.tokens
    assert toks[0].note == "①" and toks[0].color == "red"
    assert toks[2].note == "②"
    # 박스에는 원문자 번호(빨강 span) + 어법명
    assert 'class="gn"' in gp.body_html
    assert "①" in gp.body_html and "주격 관계대명사" in gp.body_html
    assert "②" in gp.body_html and "수동태" in gp.body_html
    assert "who(X)" in gp.body_html
    print("PASS  어법 넘버링(원문자) + 박스")


def test_grammar_orphan_wrong_boxed():
    # 오답형(X)만 있고 어법 note 가 없어도 반드시 번호+박스로 실려야 한다('고아 (X)' 방지).
    from src.worksheet import point_builder
    from src.worksheet.models import Sentence, Token
    s = Sentence(index=5, lines=[[
        Token(text="are", note="수일치", note_kind="red", wrong="is(X)"),
        Token(text="designed", wrong="designing(X)"),   # 어법 note 없이 (X)만
    ]])
    gp = point_builder.build_grammar_point(s)
    assert gp is not None
    toks = s.tokens
    assert toks[0].note == "①" and toks[1].note == "②"     # 둘 다 번호가 붙음
    assert "is(X)" in gp.body_html and "designing(X)" in gp.body_html  # 둘 다 박스에
    assert "①" in gp.body_html and "②" in gp.body_html
    print("PASS  고아 오답형(X)도 번호+박스에 포함")


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
        "title_en": "The Value of Curiosity", "title_ko": "호기심의 가치",
        "vocab": [{"word": "thrive", "meaning": "번성하다", "syn": "flourish",
                   "ant": "decline", "sent": 6}],
        "flow": [{"label": "도입", "text": "화제 제시",
                  "easy": "궁금하면 스스로 파고드는 거랑 같음", "sentences": "1"}],
    })
    from src.worksheet import overview_builder
    from src.worksheet.models import Analysis, Sentence
    client = _fake_client([payload])
    a = Analysis(title_en="", sentences=[Sentence(index=1, lines=[[Token(text="Hi")]])])
    t_en, t_ko, vocab, flow = overview_builder.build_overview(client, a)
    assert t_en == "The Value of Curiosity" and t_ko == "호기심의 가치"   # 자동 제목
    assert vocab and vocab[0].word == "thrive" and vocab[0].syn == "flourish"
    assert flow and flow[0].label == "도입" and flow[0].easy.startswith("궁금")
    print("PASS  overview_builder LLM 경로(+자동 제목)")


def test_literal_builder_llm_path():
    payload = json.dumps({
        "sentences": [{
            "no": 1,
            "chunks": [
                {"english": "The cat", "korean": "그 고양이가",
                 "words": [{"word": "cat", "meaning": "고양이"}]},
                {"english": "caught the mouse", "korean": "그 쥐를 잡았다", "words": []},
            ],
            "grammar": [{"point": "과거분사 후치수식", "explanation": "명사 뒤에서 수식", "key": True}],
            "note": "고양이가 쥐 잡은 거임",
        }],
    })
    from src.worksheet import literal_builder
    from src.worksheet.models import Analysis, Sentence, Token
    client = _fake_client([payload])
    a = Analysis(title_en="x", sentences=[
        Sentence(index=1, lines=[[Token(text="The cat caught the mouse")]],
                 translation="그 고양이가 그 쥐를 잡았다.")])
    lits = literal_builder.build_literal(client, a)
    assert lits and lits[0].no == 1
    assert lits[0].chunks[0].english == "The cat" and lits[0].chunks[0].korean == "그 고양이가"
    assert lits[0].chunks[0].words[0].word == "cat"
    g = lits[0].grammar[0]
    assert g.point == "과거분사 후치수식" and g.key is True   # ★필수
    assert lits[0].note.startswith("고양이")
    # 핵심 단어는 청크에서 문장 단위로 모인다
    assert lits[0].words and lits[0].words[0].meaning == "고양이"
    print("PASS  literal_builder LLM 경로(직독직해 청크/문법/단어)")


def test_render_b_from_literal():
    a = mock_analysis()
    hb = renderer.render_b_html([a])
    # 목 데이터의 직독직해가 표에 반영되는지
    assert "made by" in hb and "직독직해" in hb
    assert hb.count('class="lit-row"') == len(a.literal)   # 문장 수만큼 행
    assert "5형식 need + O + to-v" in hb                    # 문법 포인트
    assert "come in contact with" in hb                    # 핵심 단어
    print("PASS  직독직해형 렌더(목 literal 반영)")


# ---- 5. 웹앱 (test_client, 목 미리보기) ------------------------------------
def test_webapp_worksheet_flow():
    # 구문 분석 학습지 전용 웹앱(worksheet_app) — 6섹션 도구(webapp)와 분리됨.
    import worksheet_app
    c = worksheet_app.app.test_client()
    assert c.get("/").status_code == 200                      # 학습지 폼이 첫 화면
    data = {"basename": "t_ws", "lecture_label": "20", "mock": "1",
            "files": (io.BytesIO(b"x"), "s_ws.pdf")}
    r = c.post("/build", data=data, content_type="multipart/form-data")
    assert r.status_code == 200 and "완료".encode("utf-8") in r.data
    assert "포인트박스".encode("utf-8") in r.data
    print("PASS  웹앱 학습지 플로우(worksheet_app, 목)")


def run_all():
    test_splitter_circled()
    test_splitter_punct_protects_abbrev_and_decimal()
    test_splitter_ellipsis_fragments()
    test_extract_strip_korean_layouts()
    test_splitter_missing_space_and_paragraphs()
    test_rule_hints()
    test_rule_only_sentence_and_none()
    test_analyze_sentence_llm_path()
    test_build_points_llm_path()
    test_build_points_fallback_to_rules()
    test_render_a_and_b()
    test_render_reading_and_box()
    test_render_guide_cover()
    test_render_back_page()
    test_grammar_numbering()
    test_grammar_orphan_wrong_boxed()
    test_feed_point_box()
    test_pronoun_referent_in_refs()
    test_page_break_per_passage()
    test_overview_builder_llm_path()
    test_literal_builder_llm_path()
    test_render_b_from_literal()
    test_webapp_worksheet_flow()
    print("\n구문 분석 학습지 오프라인 테스트 모두 통과 ✅")


if __name__ == "__main__":
    run_all()
