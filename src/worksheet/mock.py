"""API 없이 레이아웃/디자인을 미리 보기 위한 목(mock) Analysis.

명세서 §11: '목업은 배관만 확인' — 실제 태깅 품질은 API 키로 검증.
지문 20('차·리더십') 재현. 원칙:
- 모든 문장에 성분(S·V·O·OC·C)을 빠짐없이 표기(단어 위).
- 어법은 정확한 어구에만 red + ①(단어 아래), 유의어/반의어는 해당 어휘에만 파란 밑줄.
- 빈출/주제/빈칸용 어구는 노란 형광(hl='y'), 담화표지는 라벤더(hl='p').
- 함축은 영어+한글 병기, 대명사 지칭과 함께 '떠먹여주는 Point'(파랑) 박스로.
"""
from __future__ import annotations

from .models import (Analysis, FlowStep, GrammarChip, KeyWord, LitChunk,
                     LiteralSentence, Sentence, Token, VocabEntry)
from .point_builder import build_grammar_point


def _T(text, role=None, note=None, kind="gray", wrong=None, above=None, hl=None, color=None) -> Token:
    return Token(text=text, role=role, note=note, note_kind=kind, wrong=wrong,
                 above=above, hl=hl, color=color)


def _G(text, name, role=None, wrong=None, hl=None, above=None) -> Token:
    """어법 토큰: 이름은 note(red), 글자 red. 번호/박스는 build_grammar_point 가 처리.
    role(성분)·above(유의어 밑줄)도 함께 가질 수 있다."""
    return Token(text=text, role=role, note=name, note_kind="red", color="red",
                 wrong=wrong, hl=hl, above=above)


def _LC(english, korean, *words) -> LitChunk:
    """직독직해 청크: english/korean + (word, meaning) 쌍들."""
    kws = [KeyWord(word=w, meaning=m) for w, m in words]
    return LitChunk(english=english, korean=korean, words=kws)


def _GC(point, explanation="", key=False, ci=None) -> GrammarChip:
    return GrammarChip(point=point, explanation=explanation, key=key, ci=ci)


def _mock_literal() -> list[LiteralSentence]:
    """지문 20('차·리더십')의 직독직해(청크 + 핵심 문법 + 핵심 단어)."""
    return [
        LiteralSentence(no=1, chunks=[
            _LC("Imagine", "상상해 보라"),
            _LC("(that) you have the best tea in the world", "당신이 세상에서 제일 좋은 차를 가지고 있고",
                ("the best tea", "최고의 차")),
            _LC("and you put it into a bag", "그것을 봉지에 넣는다고"),
            _LC("that's impermeable", "스며들지 않는", ("impermeable", "스며들지 않는, 불투과성의")),
        ], grammar=[
            _GC("주격 관계대명사 that", "선행사 a bag 을 수식 · what(X)", key=True, ci=3),
        ]),
        LiteralSentence(no=2, chunks=[
            _LC("It won't work.", "그것은 작용하지 않을 것이다.", ("work", "(차가) 우러나다(=infuse)")),
        ], note="아무리 좋은 찻잎도 물이 안 통하는 봉지 속에선 무용지물이라는 말"),
        LiteralSentence(no=3, chunks=[
            _LC("You just won't be able to make", "당신은 그저 만들 수 없을 것이다",
                ("be able to", "~할 수 있다")),
            _LC("a cup of tea.", "차 한 잔을."),
        ]),
        LiteralSentence(no=4, chunks=[
            _LC("For the teabag to work,", "티백이 작용하려면,"),
            _LC("it needs to be porous.", "그것은 구멍이 있어야 한다.", ("porous", "구멍이 많은, 투과성의")),
        ], grammar=[
            _GC("to부정사의 의미상 주어", "「for + 목적격」이 to work 의 주어", key=True, ci=0),
            _GC("to부정사(부사적·목적)", "‘~하기 위해’", key=True, ci=2),
        ]),
        LiteralSentence(no=5, chunks=[
            _LC("You need", "당신은 ~해야 한다"),
            _LC("the tea and the water", "차와 물이"),
            _LC("to come in contact with each other.", "서로 접촉하도록.",
                ("come in contact with", "~와 접촉하다")),
        ], grammar=[
            _GC("5형식 need + O + to-v", "목적어(the tea and the water)의 목적격보어로 to-v", key=True, ci=1),
        ]),
        LiteralSentence(no=6, chunks=[
            _LC("In our lives too,", "우리 삶에서도 마찬가지로,"),
            _LC("we cannot survive and thrive", "우리는 살아갈 수도 성장할 수도 없다",
                ("thrive", "번성하다(=flourish)")),
            _LC("in isolation.", "고립된 채로는.", ("isolation", "고립, 격리")),
        ], grammar=[
            _GC("병렬구조 survive and thrive", "조동사 cannot 뒤 동사원형 병렬", key=True, ci=4),
        ], note="사람도 혼자 틀어박히면 못 산다 — 찻잎·물 비유를 삶에 적용"),
        LiteralSentence(no=7, chunks=[
            _LC("Leaders need to be careful", "리더는 주의해야 한다"),
            _LC("not to build walls around themselves", "자기 주변에 벽을 쌓지 않도록"),
            _LC("that prevent people", "사람들이 ~하지 못하게 막는", ("prevent A from ~ing", "A가 ~하지 못하게 막다")),
            _LC("from reaching out to them.", "그들에게 다가오는 것을.", ("reach out", "다가가다, 손 내밀다")),
        ], grammar=[
            _GC("to부정사 부정 not to-v", "부정사 앞에 not", key=True, ci=1),
            _GC("주격 관계대명사 that", "선행사 walls 수식 · who(X)", key=True, ci=2),
            _GC("prevent A from -ing", "‘A가 -하는 것을 막다’", key=True, ci=4),
            _GC("재귀대명사 themselves", "주어 Leaders 와 동일", ci=6),
        ]),
        LiteralSentence(no=8, chunks=[
            _LC("As a leader,", "리더로서,"),
            _LC("you need to be able to touch", "당신은 접촉할 수 있어야 한다", ("touch", "접촉하다, 닿다")),
            _LC("other people.", "다른 사람들과."),
        ], grammar=[
            _GC("to부정사(명사적·목적어)", "need 의 목적어 to be able to touch", key=True, ci=5),
        ]),
        LiteralSentence(no=9, chunks=[
            _LC("The tea", "차는"),
            _LC("was meant to mix", "섞이도록 의도되었다", ("be meant to", "~하도록 의도되다")),
            _LC("with the water.", "물과."),
        ], grammar=[
            _GC("수동태 was meant", "be + p.p. · ‘의도되다’", key=True, ci=0),
        ]),
        LiteralSentence(no=10, chunks=[
            _LC("Similarly,", "마찬가지로,"),
            _LC("all of us were designed", "우리 모두도 설계되었다", ("be designed to", "~하도록 설계되다")),
            _LC("to work with other people, with teams,", "다른 사람들, 팀,"),
            _LC("and with society at large.", "그리고 더 크게는 사회와 함께 일하도록."),
        ], grammar=[
            _GC("수동태 were designed", "be + p.p. · designed(X) 능동 아님", key=True, ci=1),
            _GC("to부정사(부사적)", "‘~하도록’", ci=3),
            _GC("병렬 with A, with B, and with C", "전치사구 3개 대등 연결", key=True, ci=6),
        ], note="찻잎이 물과 섞이도록 만들어졌듯, 사람도 서로 어울리도록 설계됐다는 뜻"),
    ]


def _thin_to_strength(sentences: list[Sentence], strength: str) -> None:
    """목 문장 태깅을 강도에 맞춰 줄인다(build_grammar_point 번호 매기기 '전'에 호출).

    - full : 그대로(성분·모든 어법·유의어/반의어·형광 전부)
    - key  : 성분(S·V·O·C) + '가장 중요한 어법 1개'만. 유의어/반의어·지엽 주석·지칭·함축 생략.
    - none : 성분·문법 주석 전부 제거. 원문+해석만(형광/지칭/함축도 제거).
    """
    if strength == "full":
        return
    for s in sentences:
        if strength == "none":
            for t in s.tokens:
                t.role = t.note = t.wrong = t.above = t.color = None
                t.note_kind, t.hl, t.underline = "lbl", None, False
            s.refs, s.badge = [], None
            s.gloss_en = s.gloss_ko = None
            continue
        # strength == "key": 성분·형광은 유지, 어법은 문장당 1개만, 나머지 주석은 제거
        kept_red = False
        for t in s.tokens:
            t.above = None            # 유의어/반의어(= / ↔) 위 메모 제거
            t.underline = False
            if t.note_kind == "red" and t.note:
                if not kept_red:
                    kept_red = True   # 첫 어법만 남김
                else:
                    t.note, t.color, t.note_kind = None, None, "lbl"
            elif t.note_kind in ("gray", "blue"):
                t.note = None         # 지엽적 해석 힌트 제거
        s.refs = []                   # 지칭(떠먹여주는 Point) 생략
        s.gloss_en = s.gloss_ko = None


def mock_analysis(title_en: str = "A necessity of openness and connection in leadership",
                  lecture_label: str = "20", date: str = "2025년06월",
                  strength: str = "full") -> Analysis:
    s01 = Sentence(
        index=1,
        lines=[[
            _T("Imagine", role="V"), _T("(you", role="S"), _T("have", role="V"),
            _T("the best tea", role="O"), _T("in the world"), _T("and", role="병렬"),
            _T("you", role="S"), _T("put", role="V"), _T("it", role="O"), _T("into a bag"),
            _G("(that's", "주격 관계대명사", wrong="what(X)"),
            _T("impermeable)).", role="C", above="= non-porous", note="↔ permeable"),
        ]],
        translation="당신이 세상에서 제일 좋은 차(茶)를 가지고 있고, 당신이 그것을 스며들지 않는 티백에 넣는다고 상상해 보라.",
        refs=["it → the best tea"],
    )
    s02 = Sentence(
        index=2,
        lines=[[
            _T("It", role="S"), _T("won't"),
            _T("work.", role="V", above="= infuse (우러나다)"),
        ]],
        translation="그것은 작용하지 않을 것이다.",
        refs=["It → 막힌 봉지 속 그 차"],
    )
    s03 = Sentence(
        index=3,
        gloss_en="Even the finest tea is useless if it stays sealed off from water.",
        gloss_ko="아무리 좋은 차라도 물과 닿지 못하면 소용없다는 뜻.",
        lines=[[
            _T("You", role="S", hl="y"), _T("just", hl="y"), _T("won't", hl="y"),
            _T("be able to", hl="y"), _T("make", role="V", hl="y"),
            _T("a cup of tea.", role="O", hl="y"),
        ]],
        translation="당신은 그저 차 한 잔을 만들 수 없을 것이다.",
    )
    s04 = Sentence(
        index=4,
        lines=[[
            _G("(For the teabag", "to부정사의 의미상 주어"),
            _G("to work),", "to부정사(부사적)"),
            _T("it", role="S"), _T("needs to be", role="V"),
            _T("porous.", role="C", above="= permeable", note="↔ non-porous", hl="y"),
        ]],
        translation="티백이 작용하려면, 그것은 구멍이 있어야 한다.",
        refs=["it → the teabag(티백)"],
    )
    s05 = Sentence(
        index=5,
        lines=[[
            _T("You", role="S"), _G("need", "5형식 (need+O+to-v)", role="V"),
            _T("the tea", role="O①"), _T("and", role="병렬"), _T("the water", role="O②"),
            _T("to come in contact with", role="OC", above="= interact with", note="↔ be isolated from"),
            _T("each other."),
        ]],
        translation="당신은 차와 물이 서로 접촉할 수 있도록 해야 한다.",
    )
    s06 = Sentence(
        index=6,
        lines=[[
            _T("(In our lives too),"), _T("we", role="S"), _T("cannot"),
            _T("survive", role="V①", hl="y"), _T("and", role="병렬", hl="y"),
            _T("thrive", role="V②", above="= flourish", note="↔ decline", hl="y"),
            _T("(in isolation).", note="고립된 채로", hl="y"),
        ]],
        translation="우리 삶에서도 마찬가지로, 우리는 고립된 채로는 살아갈 수도 성장할 수도 없다.",
        refs=["we → 우리 인간"],
    )
    s07 = Sentence(
        index=7,
        badge="서",
        lines=[[
            _T("Leaders", role="S"), _T("need", role="V"), _T("to be careful", role="C"),
            _G("(not to build", "to부정사(부사적)", hl="y"),
            _T("walls", role="O", hl="y"), _T("around themselves", hl="y"),
            _G("(that", "주격 관계대명사", wrong="who(X)", hl="y"),
            _G("prevent", "prevent A from -ing", role="V", hl="y"),
            _T("people", role="O", hl="y"),
            _T("from reaching out to", above="= approach", hl="y"),
            _T("them)).", hl="y"),
        ]],
        translation="리더는 사람들이 그들에게 다가오지 못하게 막는 벽을 그들 자신의 주변에 쌓지 않도록 주의해야 한다.",
        refs=["themselves / them → leaders(리더 자신)"],
    )
    s08 = Sentence(
        index=8,
        lines=[[
            _T("(As a leader),"), _T("you", role="S"), _T("need", role="V"),
            _G("(to be able to", "to부정사(명사적)", role="O"),
            _T("touch", above="= come in contact", note="↔ detach"),
            _T("other people)."),
        ]],
        translation="리더로서, 당신은 다른 사람들과 접촉할 수 있어야 한다.",
        refs=["you → 리더(독자)"],
    )
    s09 = Sentence(
        index=9,
        lines=[[
            _T("The tea", role="S"),
            _G("was meant to", "be meant to (= be intended to)", role="V"),
            _T("mix", above="= mingle with"),
            _T("with the water."),
        ]],
        translation="차는 물과 섞이도록 의도되었다.",
    )
    s10 = Sentence(
        index=10,
        lines=[[
            _T("Similarly", hl="p", above="= Likewise"),
            _T("all of us", role="S"),
            _G("were designed", "수동태", wrong="designed(X)", above="= be built to", hl="y"),
            _G("(to work", "to부정사(부사적)", hl="y"),
            _T("with other people,", role="전치사구①", hl="y"),
            _T("with teams,", role="②", hl="y"),
            _T("and with society", role="③", hl="y"),
            _T("(at large)).", note="더 크게는", hl="y"),
        ]],
        translation="마찬가지로 우리 모두도 다른 사람들, 팀, 그리고 더 크게는 사회와 함께 일하도록 설계되었다.",
        refs=["all of us → 우리 모두(사람 전체)"],
    )

    sentences = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10]

    # 끊어읽기: 직독직해(한글, ' / ' 구분) + 영어 슬래시 경계(토큰 index)
    _readings = {
        1: "상상해 보라 / 당신이 세상 최고의 차를 가지고 있고 / 그것을 봉지에 넣는다고 / 스며들지 않는",
        2: "그것은 / 작용하지 않을 것이다",
        3: "당신은 그저 만들 수 없을 것이다 / 차 한 잔을",
        4: "티백이 작용하려면 / 그것은 구멍이 있어야 한다",
        5: "당신은 해야 한다 / 차와 물이 / 서로 접촉하도록",
        6: "우리 삶에서도 마찬가지로 / 우리는 살아갈 수도 성장할 수도 없다 / 고립된 채로는",
        7: "리더는 주의해야 한다 / 벽을 쌓지 않도록 / 자기 주변에 / 사람들이 다가오지 못하게 막는",
        8: "리더로서 / 당신은 접촉할 수 있어야 한다 / 다른 사람들과",
        9: "차는 / 섞이도록 의도되었다 / 물과",
        10: "마찬가지로 / 우리 모두도 설계되었다 / 다른 사람들·팀 / 그리고 더 크게는 사회와 함께 일하도록",
    }
    _slashes = {1: [0, 4, 9], 4: [1], 6: [0, 5], 10: [0, 2]}
    for s in sentences:
        s.reading_ko = _readings.get(s.index, "")
        toks = s.tokens
        for i in _slashes.get(s.index, []):
            if 0 <= i < len(toks):
                toks[i].slash = True

    _thin_to_strength(sentences, strength)   # 태깅 강도 반영(번호 매기기 전)
    for s in sentences:
        gp = build_grammar_point(s)
        s.points = [gp] if gp else []

    vocab = [
        VocabEntry("impermeable", "스며들지 않는, 불투과성의", "non-porous, sealed", "permeable, porous", 1),
        VocabEntry("infuse", "(차가) 우러나다, 스미다", "steep, brew", "—", 2),
        VocabEntry("porous", "구멍이 많은, 투과성의", "permeable, penetrable", "non-porous, impermeable", 4),
        VocabEntry("come in contact with", "~와 접촉하다", "interact with, mix with", "be isolated from", 5),
        VocabEntry("thrive", "번성하다, 잘 자라다", "flourish, prosper", "decline, wither", 6),
        VocabEntry("isolation", "고립, 격리", "seclusion, solitude", "connection, contact", 6),
        VocabEntry("prevent A from ~ing", "A가 ~하지 못하게 막다", "keep, prohibit, stop", "allow, enable", 7),
        VocabEntry("reach out", "다가가다, 손을 내밀다", "connect, approach", "withdraw", 7),
        VocabEntry("be meant to", "~하도록 의도되다", "be intended to", "—", 9),
        VocabEntry("be designed to", "~하도록 설계되다", "be built to", "—", 10),
    ]
    flow = [
        FlowStep("비유 제시", "아무리 좋은 차도 물이 안 통하는 봉지 속에선 무용지물",
                 easy="아무리 좋은 찻잎도 물 안 통하는 봉지에 넣으면 꽝인 거랑 같음", sentences="1~3"),
        FlowStep("원리 설명", "티백은 구멍(porous)이 있어야 물과 찻잎이 접촉함",
                 easy="티백에 구멍 뚫려야 차가 우러나듯, 물·찻잎이 서로 닿아야 됨", sentences="4~5"),
        FlowStep("삶에 적용", "사람도 고립된 채로는 살지도 성장하지도 못함",
                 easy="혼자 방에만 틀어박히면 사람도 시들해지는 거임", sentences="6"),
        FlowStep("주장", "리더는 벽을 쌓지 말고 열려 있어야 함",
                 easy='리더가 벽 치고 "오지 마" 하면 아무도 도와줄 수 없음', sentences="7~8"),
        FlowStep("결론", "우리는 다른 사람·사회와 함께 일하도록 설계된 존재",
                 easy="찻잎+물처럼, 사람도 같이 섞여야 제 실력이 나옴", sentences="9~10"),
    ]

    return Analysis(
        title_en=title_en,
        title_ko="리더의 개방성과 연결의 중요성",
        lecture_label=lecture_label,
        date=date,
        sentences=sentences,
        vocab=vocab, flow=flow,
        literal=_mock_literal(),
    )
