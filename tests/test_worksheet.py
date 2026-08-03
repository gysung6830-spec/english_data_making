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


def test_reading_ko_list_alignment():
    # 직독직해를 '영어 조각당 한 개' 리스트로 받아 정렬. 개수 맞으면 / 유지.
    payload = json.dumps({
        "lines": [{"tokens": [
            {"text": "Certain tribes don't have much,", "slash": True},
            {"text": "yet they share", "slash": True},
            {"text": "because it helps them.", "slash": True},
        ]}],
        "translation": "어떤 부족은 가진 게 적지만 나눈다.",
        "reading_ko": ["어떤 부족은 가진 게 많지 않다", "그러나 그들은 나눈다",
                       "왜냐하면 그것이 그들에게 도움이 되기 때문이다"],
    })
    s = analyzer.analyze_sentence(_fake_client([payload]),
                                  "Certain tribes don't have much, yet they share because it helps them.",
                                  3, strength="full")
    assert s.reading_ko.count(" / ") == 2        # 영어 3조각 = 한글 3조각 → / 유지

    # 한글이 영어보다 잘게 쪼개지면(과분할) → 슬래시 제거하고 연속 표기(오정렬 방지)
    payload2 = json.dumps({
        "lines": [{"tokens": [
            {"text": "A,", "slash": True},
            {"text": "B", "slash": True},
            {"text": "C.", "slash": True},
        ]}],
        "translation": "가나다.",
        "reading_ko": ["가", "나", "그러나", "다", "왜냐하면"],   # 5개 vs 영어 3개
    })
    s2 = analyzer.analyze_sentence(_fake_client([payload2]), "A, B C.", 4, strength="full")
    assert " / " not in s2.reading_ko and "가 나 그러나 다 왜냐하면" == s2.reading_ko
    print("PASS  직독직해 리스트 정렬(개수 일치 / 과분할 시 연속 표기)")


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
    assert "어법 Point" in ha and "독해 Point" in ha  # 남은 두 종류 박스
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
    # 끊어읽기: 영어 슬래시(/) + 직독직해(한글) 줄 (앞면 해석 카드는 삭제됨)
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert 'class="rdko"' in ha and "직독직해" in ha        # 직독직해(끊어읽기) 줄
    assert 'class="kobox"' not in ha                        # 온전한 해석 카드는 앞면에서 제거
    assert 'class="sl"' in ha                               # 영어 끊어읽기 경계 /
    # 직독직해 청크가 / 로 나뉘어 렌더되는지
    assert 'class="rc"' in ha
    print("PASS  끊어읽기(직독직해) 줄 — 앞면 해석 카드 제거")


def test_render_guide_cover():
    # 맨 앞 '활용 가이드' 표지: 색·기호 뜻 + 사용법. include_guide 로 토글.
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert "활용법" in ha and "색 · 기호가 뜻하는 것" in ha   # 표지 존재
    assert "오답형 함정" in ha and "독해 Point" in ha    # 색 범례 항목
    assert "이렇게 쓰세요" in ha                              # 사용법 단계
    # 표지 없이도 렌더 가능(측정/옵션용)
    assert "활용법" not in renderer.render_a_html([a], include_guide=False)
    print("PASS  맨 앞 활용 가이드 표지(색·기호 뜻 + 사용법)")


def test_render_back_page():
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert 'class="bhead"' in ha                       # 뒷페이지 존재
    assert "원문 · 전체 해석" in ha and 'class="pcols"' in ha  # 어휘 앞 원문·해석 2단
    assert 'class="pnum"' in ha and "전체 해석" in ha    # 번호 원 + 해석 칸
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
    # 어법·독해 포인트를 문장별 '합친' 박스에, 독해 뱃지(틸 fcap)는 유지
    a = mock_analysis()
    ha = renderer.render_a_html([a])
    assert "pbox merged" in ha and 'class="cap fcap"' in ha and "독해 Point" in ha
    assert "pbox merged even" in ha and "pbox merged odd" in ha  # 문장마다 번갈아
    assert "the teabag" in ha        # 대명사 지칭(refs)
    assert "Even the finest tea" in ha  # 함축(gloss_en) 도 이 박스 안에
    print("PASS  합친 포인트 박스(어법+독해, 뱃지 유지, 번갈아 색)")


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
        "summary": "호기심이 성장의 원동력이다.",
        "summary_easy": "궁금하면 스스로 찾아보게 되는 거랑 같음.",
        "vocab": [{"word": "thrive", "meaning": "번성하다", "syn": "flourish",
                   "ant": "decline", "sent": 6}],
        "flow": [{"label": "도입", "text": "화제 제시",
                  "easy": "궁금하면 스스로 파고드는 거랑 같음", "sentences": "1"}],
    })
    from src.worksheet import overview_builder
    from src.worksheet.models import Analysis, Sentence
    client = _fake_client([payload])
    a = Analysis(title_en="", sentences=[Sentence(index=1, lines=[[Token(text="Hi")]])])
    t_en, t_ko, summary, summary_easy, vocab, flow = overview_builder.build_overview(client, a)
    assert t_en == "The Value of Curiosity" and t_ko == "호기심의 가치"   # 자동 제목
    assert summary.startswith("호기심") and summary_easy.startswith("궁금")  # 주제 + 쉽게
    assert vocab and vocab[0].word == "thrive" and vocab[0].syn == "flourish"
    assert flow and flow[0].label == "도입" and flow[0].easy.startswith("궁금")
    print("PASS  overview_builder LLM 경로(+자동 제목)")


def test_reading_alignment_and_no_false_review():
    """직독직해 정렬: 1개 차이는 슬래시 유지, 2개 이상 차이는 연속 표기.
    두 경우 모두 품질 검수(assess)에서 '끊어읽기 어긋남'으로 잡히지 않아야 한다."""
    from src.worksheet.analyzer import _reading_ko_aligned
    from src.worksheet.models import Analysis, Sentence, Token
    from src.worksheet import quality

    def en_line(nslash):
        toks = [Token(text=f"w{i}", slash=True) for i in range(nslash)]
        toks.append(Token(text="end"))
        return toks

    # 영어 3조각(슬래시 2) 기준
    exact = _reading_ko_aligned([en_line(2)], ["a", "b", "c"])
    off1 = _reading_ko_aligned([en_line(2)], ["a", "b", "c", "d"])     # 1개 차이 → 유지
    off2 = _reading_ko_aligned([en_line(2)], ["a", "b", "c", "d", "e"])  # 2개 차이 → 연속
    inner = _reading_ko_aligned([en_line(2)], ["a / x", "b", "c"])      # 조각 내 '/' 제거
    assert exact == "a / b / c"
    assert off1 == "a / b / c / d"        # 슬래시 유지(가독성)
    assert " / " not in off2 and off2 == "a b c d e"   # 연속 표기(어긋난 '/' 숨김)
    assert inner == "a x / b / c"         # 내부 '/' 제거로 조각 수 부풀지 않음

    a = Analysis(sentences=[
        Sentence(index=1, lines=[en_line(2)], reading_ko=off1, translation="t"),
        Sentence(index=2, lines=[en_line(2)], reading_ko=off2, translation="t"),
        Sentence(index=3, lines=[en_line(2)], reading_ko=inner, translation="t"),
    ])
    assert quality._reading_misaligned([a]) == 0        # 검수 '어긋남' 0건
    print("PASS  직독직해 정렬 + 검수 오탐 없음")


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
    data = {"basename": "t_ws", "start_no": "30", "mock": "1",
            "files": (io.BytesIO(b"x"), "s_ws.pdf")}
    r = c.post("/build", data=data, content_type="multipart/form-data")
    assert r.status_code == 200 and "완료".encode("utf-8") in r.data
    # 교사용+학생용 합본 PDF 가 나온다
    assert "학생용".encode("utf-8") in r.data and "합본".encode("utf-8") in r.data
    # 폼에 '시작 문항 번호(자동 증가)' 입력이 있다
    assert "start_no".encode("utf-8") in c.get("/").data
    print("PASS  웹앱 학습지 플로우(worksheet_app, 목) — 교사용+학생용 합본")


def test_webapp_start_number_autoincrement():
    # 수동 시작 문항 번호 → 지문마다 start, start+1, … 로 리본 라벨 자동 증가.
    import types
    import worksheet_app as wa
    from src.worksheet.models import Analysis, Sentence, Token

    def _mk(n):
        return [Analysis(title_en="T", title_ko="ㅌ", lecture_label="",
                         sentences=[Sentence(index=i + 1,
                                    lines=[[Token(text="x")]], translation="ㅋ")
                                    for i in range(1)])
                for _ in range(n)]

    captured = {}

    def fake_build(client, cfg, tmp, header, **k):
        return _mk(3)                     # 한 파일에 지문 3개

    def fake_pair(analyses, out, **k):
        captured["labels"] = [a.lecture_label for a in analyses]
        out.write_bytes(b"%PDF-1.4\n%%EOF")   # 렌더 생략(가짜 PDF)

    orig_build, orig_pair = wa.ws_pipeline.build_analyses_for_file, wa.ws_pipeline.render_worksheet_pair
    orig_assess = wa.ws_quality.assess
    wa.ws_pipeline.build_analyses_for_file = fake_build
    wa.ws_pipeline.render_worksheet_pair = fake_pair
    wa.ws_quality.assess = lambda *a, **k: {"ok": True, "reasons": []}
    try:
        c = wa.app.test_client()
        # 목이 아니라 실제 경로를 타도록 api_key 를 준다(환경키 없을 때만 필요)
        data = {"start_no": "30", "api_key": "sk-ant-test",
                "files": (io.BytesIO(b"x"), "wb.pdf")}
        c.post("/build", data=data, content_type="multipart/form-data")
    finally:
        wa.ws_pipeline.build_analyses_for_file = orig_build
        wa.ws_pipeline.render_worksheet_pair = orig_pair
        wa.ws_quality.assess = orig_assess
    assert captured.get("labels") == ["30", "31", "32"], captured
    print("PASS  웹앱 수동 시작 문항 번호(30→30·31·32 자동 증가)")


def _make_hwpx(path, paragraphs):
    """테스트용 최소 HWPX(section0.xml 만 있는 zip) 파일 작성."""
    import zipfile
    ns = "http://www.hancom.co.kr/hwpml/2011/paragraph"
    nss = "http://www.hancom.co.kr/hwpml/2011/section"
    body = "".join(
        f"<hp:p><hp:run><hp:t>{p}</hp:t></hp:run></hp:p>"
        for p in paragraphs
    )
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>'
           f'<hs:sec xmlns:hs="{nss}" xmlns:hp="{ns}">{body}</hs:sec>')
    with zipfile.ZipFile(str(path), "w") as z:
        z.writestr("Contents/section0.xml", xml)


def test_hwp_support():
    import tempfile
    from pathlib import Path
    from src import extract

    # 확장자 판별 + 학습지 앱의 허용 목록에 HWP 포함
    assert extract.is_hwp("a.hwp") and extract.is_hwp("b.HWPX")
    assert not extract.is_hwp("c.pdf")
    import worksheet_app
    assert ".hwp" in worksheet_app.ALLOWED_WS and ".hwpx" in worksheet_app.ALLOWED_WS
    # 6섹션 앱 공용 허용 목록은 HWP 를 포함하지 않아야 함(경계 유지)
    from web_common import ALLOWED as SHARED_ALLOWED
    assert ".hwp" not in SHARED_ALLOWED

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "s.hwpx"
        _make_hwpx(p, ["The cat sat on the mat.", "한글 설명 줄", "Boredom sparks creativity."])
        raw = extract.extract_hwp_text(p)
        assert "The cat sat on the mat." in raw
        # 배치 무관 영어만 남기기까지 통과
        cleaned = extract.extract_passage_text_any(p)
        assert "cat" in cleaned and "creativity" in cleaned
        assert not extract.looks_empty(cleaned)
    print("PASS  HWP/HWPX 텍스트 추출 + 학습지 앱 허용")


def _mk_analysis(sent_texts):
    sents = []
    for i, t in enumerate(sent_texts, start=1):
        toks = [Token(text=w) for w in t.split(" ")]
        sents.append(Sentence(index=i, lines=[toks]))
    return Analysis(title_en="T", sentences=sents)


def test_merge_trailing_punct():
    # 문장부호만 있는 토큰은 앞 단어에 붙어 'protectors .' 같은 공백이 사라져야 한다.
    from src.worksheet import analyzer
    lines = [[Token(text="protectors", slash=True), Token(text="."),
              Token(text="would"), Token(text=","), Token(text="for example")]]
    analyzer._merge_trailing_punct(lines)
    texts = [t.text for t in lines[0]]
    assert texts == ["protectors.", "would,", "for example"], texts
    assert lines[0][0].slash is True          # 앞 토큰 슬래시 유지
    # 역할/주석이 달린 부호 토큰은 병합하지 않음(정보 보존)
    keep = [[Token(text="x"), Token(text="?", note="의문")]]
    analyzer._merge_trailing_punct(keep)
    assert [t.text for t in keep[0]] == ["x", "?"]
    print("PASS  문장부호 토큰 병합(부호 앞 공백 제거)")


def test_detect_problem_numbers_regex():
    from src.worksheet.pipeline import _PROBNO_COLON, _PROBNO_LINE
    # 줄 맨 앞 'N번' 형식(모의평가 머리글)
    raw = ("31번 2026년 6월 한국교육과정평가원 모의평가\n"
           "1. Ever since the early Enlightenment...\n"
           "- 14 -\n"
           "32번 2026년 6월 한국교육과정평가원 모의평가\n"
           "1. Speakers don't always...\n")
    nums = [m.group(1) for m in _PROBNO_LINE.finditer(raw)]
    assert nums == ["31", "32"], nums          # 문장번호 '1.' 은 매칭 안 됨
    # 'N번:' 형식(제목 머리글, 예: '– 30번: 소유가 …')
    raw2 = "[고1] 2025 09월 – 30번: 소유가 많아질수록\n[고1] 2025 09월 – 31번: 다른 지문\n"
    nums2 = [m.group(1) for m in _PROBNO_COLON.finditer(raw2)]
    assert nums2 == ["30", "31"], nums2
    print("PASS  실제 문제 번호(N번 / N번:) 인식")


def test_clean_passage_keeps_numbered_sentences():
    # 회귀: 해석연습 WORKBOOK 처럼 지문 문장에 '1. 2.' 번호가 붙으면, 예전엔
    # clean_text 가 그 줄(문장 앞부분)을 통째로 지워 조각만 남았다. 이제 보존해야 함.
    from src import extract
    raw = ("- 14 -\n"
           "1. Ever since the early Enlightenment, preservation and conservation were related.1)\n"
           "2. Taken as near synonyms, their meaning is to maintain an object\n"
           "in its present state, to protect it from change.2)\n")
    out = extract.clean_passage_text(raw)
    # 문장 앞부분(주어·동사)이 보존돼야 함
    assert "Taken as near synonyms, their meaning is to maintain an object" in out
    assert "Ever since the early Enlightenment" in out
    assert "- 14 -" not in out                 # 페이지 마커 제거
    assert "1)" not in out and "2)" not in out  # 각주 표시 제거
    assert not any(ln.strip().startswith(("1.", "2.")) for ln in out.splitlines())  # 문장 번호 제거
    print("PASS  워크시트 정제: 번호 붙은 지문 문장 보존")


def test_fragment_quality_guard():
    from src.worksheet import quality

    # 정상 지문(모두 대문자로 시작) → 경고 없음
    ok = _mk_analysis([
        "Conservation keeps an object in its present state.",
        "Restoration involves restoring a historical instrument.",
        "Conservators see themselves as protectors.",
    ])
    assert quality.fragment_warning([ok]) is None

    # 첨부 PDF 처럼 머리 잘린 조각(소문자로 시작) → 경고
    frag = _mk_analysis([
        "its present state , to protect it from change , usually",
        "restorative aspects —restoring a historical musical instrument ,",
        "as protectors .",
        "use , rather than interfering as minimally as possible",
        "deteriorated state , for study , rather than to restore or repair it",
    ])
    w = quality.fragment_warning([frag])
    assert w and "소문자" in w
    print("PASS  조각난 추출 감지(품질 경고)")


def test_front_density_render_classes():
    # 앞면 밀도 클래스가 실제로 렌더되는지(ultra 는 compact 위에 얹힘)
    from src.worksheet import renderer
    a = mock_analysis(strength="full")
    a.front_density = "ultra"
    assert 'class="page compact ultra"' in renderer.render_a_html(
        [a], include_back=False, include_guide=False)
    a.front_density = "compact"
    html = renderer.render_a_html([a], include_back=False, include_guide=False)
    assert 'class="page compact"' in html and 'class="page compact ultra"' not in html
    a.front_density = "normal"
    assert 'class="page"' in renderer.render_a_html(
        [a], include_back=False, include_guide=False)
    print("PASS  앞면 밀도 클래스 렌더(normal/compact/ultra)")


def test_student_modes_render():
    from src.worksheet import renderer
    a = mock_analysis(strength="full")
    teacher = renderer.render_a_html([a], include_guide=False)
    assert 'class="blk"' not in teacher and 'class="lbl"' in teacher

    slash = renderer.render_a_html([a], student=True, slevel="slash", include_guide=False)
    assert 'class="blk"' in slash              # 해석/어법 빈칸
    assert 'class="lbl"' not in slash          # 성분(SVOC) 라벨 숨김
    assert 'class="tok tsl"' in slash          # 끊어읽기(/) 유지

    blank = renderer.render_a_html([a], student=True, slevel="blank", include_guide=False)
    assert 'class="blk"' in blank and 'class="lbl"' not in blank
    assert 'class="tok tsl"' not in blank      # 완전백지: / 도 없음

    interp = renderer.render_a_html([a], student=True, slevel="interp", include_guide=False)
    assert 'class="lbl"' in interp             # 성분·어법 유지
    assert 'class="blk"' in interp             # 직독직해·해석만 빈칸
    print("PASS  학생용 3모드 렌더(slash/blank/interp)")


def test_reading_alignment_detect():
    from src.worksheet import quality

    def mk(slash_idx, ko):
        toks = [Token(text="w%d" % i, slash=(i in slash_idx)) for i in range(5)]
        return Analysis(sentences=[Sentence(index=1, lines=[toks], reading_ko=ko)])

    ok = mk({1, 3, 4}, "가 / 나 / 다")       # 영어 3조각 · 한글 3조각 → 정렬
    assert quality._reading_misaligned([ok]) == 0
    bad = mk({0, 1, 2, 3, 4}, "가 / 나")     # 영어 5조각 · 한글 2조각 → 불일치
    assert quality._reading_misaligned([bad]) == 1
    print("PASS  끊어읽기(영어/한글) 정렬 불일치 감지")


def test_quality_assess_gate():
    from src.worksheet import quality
    ok = _mk_analysis(["Full sentence one here.", "Full sentence two here.", "Third one here."])
    for s in ok.sentences:
        s.translation = "온전한 해석"
    v = quality.assess([ok])
    assert v["ok"] and not v["reasons"], v

    # 조각(소문자 시작) + 해석 없음 → 검수 사유 잡힘
    bad = _mk_analysis(["its present state, to protect it.", "as protectors here.",
                        "use, rather than interfering here."])
    v2 = quality.assess([bad])
    assert not v2["ok"] and v2["reasons"]

    assert quality.assess([])["ok"] is False       # 빈 결과 → 검수
    print("PASS  무인 품질 게이트(assess: 검수 대상만 플래그)")


def test_config_quality_defaults():
    from src.config import load_config
    cfg = load_config()
    assert cfg.quality.vision_fallback is True and cfg.quality.auto_flag is True
    assert cfg.quality.min_sentences >= 1
    print("PASS  품질 설정 기본값 로드")


def test_raw_text_fragmented():
    from src.worksheet import quality
    ok = "Conservation keeps things. Restoration changes them. Experts protect items."
    assert quality.raw_text_fragmented(ok) is False
    frag = ("its present state, to protect it. restorative aspects, restoring things. "
            "as protectors. use, rather than interfering.")
    assert quality.raw_text_fragmented(frag) is True

    # PassageSet 단위 판정: None/조각 → True, 온전 → False
    from src.schemas import Extraction, PassageSet
    assert quality.passages_fragmented(None) is True
    good = PassageSet(passages=[Extraction(title="T", paragraphs=[ok])])
    bad = PassageSet(passages=[Extraction(title="T", paragraphs=[frag])])
    assert quality.passages_fragmented(good) is False
    assert quality.passages_fragmented(bad) is True
    print("PASS  원문 조각남 사전 감지(비전 전환 판단)")


def test_vision_fallback_pdf():
    import tempfile
    import types as _t
    from pathlib import Path

    from pypdf import PdfWriter

    from src import extract
    from src.schemas import Extraction, PassageSet
    from src.worksheet import pipeline

    def _blank_pdf(path):
        w = PdfWriter()
        w.add_blank_page(width=420, height=595)
        with open(path, "wb") as fh:
            w.write(fh)

    with tempfile.TemporaryDirectory() as d:
        pdf = Path(d) / "blank.pdf"
        _blank_pdf(pdf)
        # (1) pdf_to_images: 페이지 수만큼 PNG 생성
        imgs = extract.pdf_to_images(pdf, Path(d) / "imgs")
        assert len(imgs) == 1 and imgs[0].exists()

    # (2) 비전 폴백: 가짜 client 가 온전한 지문을 돌려주면 병합해 반환
    fake_ps = PassageSet(passages=[Extraction(title="T", paragraphs=[
        "Conservation keeps an object safe. Restoration returns it to an earlier state."])])

    class _C:
        def structured(self, **k):
            return fake_ps

    cfg = _t.SimpleNamespace(processing=_t.SimpleNamespace(max_retries=1))
    with tempfile.TemporaryDirectory() as d:
        pdf = Path(d) / "b.pdf"
        _blank_pdf(pdf)
        out = pipeline._extract_via_vision_pdf(_C(), cfg, pdf)
    assert out is not None and out.passages
    assert "Conservation" in out.passages[0].body
    print("PASS  PDF 텍스트 깨짐 → 비전(이미지) 재추출 폴백")


def test_font_embed_nanumsquareround():
    # 렌더 HTML 에 나눔스퀘어라운드가 base64 로 임베드되어(시스템 글꼴 무관 동일 렌더),
    # 본문 font-family 도 NanumSquareRound 로 지정되는지 확인.
    from src.worksheet import mock, renderer
    a = mock.mock_analysis()
    html = renderer.render_a_html([a])
    assert "@font-face" in html
    assert "'NanumSquareRound'" in html or "NanumSquareRound" in html
    assert "data:font/ttf;base64," in html
    # 요청 문자만 서브셋 → 원본(1MB)보다 훨씬 작아야 함(과대 임베드 방지)
    import re as _re
    b64 = _re.findall(r"base64,([A-Za-z0-9+/=]+)\)", html)
    assert b64, "임베드된 폰트 데이터가 없음"
    assert max(len(x) for x in b64) < 900_000, "서브셋이 지나치게 큼"
    print("PASS  나눔스퀘어라운드 폰트 임베드(서브셋)")


def test_vocab_test_and_answer_key():
    from src.worksheet import mock, renderer
    a = mock.mock_analysis()
    renderer._ensure_vocab_test(a)
    order = [v.word for v in a.vocab_test]
    # (1) 결정적 셔플: 같은 지문이면 항상 같은 순서
    b = mock.mock_analysis()
    renderer._ensure_vocab_test(b)
    assert [v.word for v in b.vocab_test] == order
    # (2) 누락·중복 없이 원본 단어 전부 포함, 순서는 원본과 달라짐(랜덤)
    assert sorted(order) == sorted(v.word for v in a.vocab)
    assert order != [v.word for v in a.vocab]
    # (3) 테스트 페이지: '단어 TEST' 제목 + 영어 단어 등장
    html_t = renderer.render_a_html([a], include_test=True, include_guide=False)
    assert "단어 TEST" in html_t and a.vocab[0].word in html_t
    # (4) 정답장(only_answer): 단어—뜻만, 유의어/반의어 제외
    html_a = renderer.render_a_html([a], only_answer=True)
    assert "정답" in html_a and a.vocab[0].meaning in html_a
    assert a.vocab[0].syn not in html_a          # 유의어는 테스트/정답에서 제외
    print("PASS  단어 TEST(랜덤·결정적) + 정답장(유의어/반의어 제외)")


def run_all():
    test_splitter_circled()
    test_splitter_punct_protects_abbrev_and_decimal()
    test_splitter_ellipsis_fragments()
    test_extract_strip_korean_layouts()
    test_splitter_missing_space_and_paragraphs()
    test_rule_hints()
    test_rule_only_sentence_and_none()
    test_analyze_sentence_llm_path()
    test_reading_ko_list_alignment()
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
    test_vocab_test_and_answer_key()
    test_webapp_worksheet_flow()
    test_webapp_start_number_autoincrement()
    test_hwp_support()
    test_merge_trailing_punct()
    test_detect_problem_numbers_regex()
    test_front_density_render_classes()
    test_student_modes_render()
    test_reading_alignment_detect()
    test_quality_assess_gate()
    test_config_quality_defaults()
    test_clean_passage_keeps_numbered_sentences()
    test_fragment_quality_guard()
    test_raw_text_fragmented()
    test_vision_fallback_pdf()
    test_font_embed_nanumsquareround()
    print("\n구문 분석 학습지 오프라인 테스트 모두 통과 ✅")


if __name__ == "__main__":
    run_all()
