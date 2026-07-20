"""API 없이 레이아웃/디자인을 미리 보기 위한 목(mock) Analysis.

명세서 §11: '목업은 배관만 확인' — 실제 태깅 품질은 API 키로 검증.
지문 20('차·리더십') 재현. 원칙:
- 모든 문장에 성분(S·V·O·OC·C)을 빠짐없이 표기(단어 위).
- 어법은 정확한 어구에만 red + ①(단어 아래), 유의어/반의어는 해당 어휘에만 파란 밑줄.
- 빈출/주제/빈칸용 어구는 노란 형광(hl='y'), 담화표지는 라벤더(hl='p').
- 함축은 영어+한글 병기, 대명사 지칭과 함께 '떠먹여주는 Point'(파랑) 박스로.
"""
from __future__ import annotations

from .models import Analysis, FlowStep, Sentence, Token, VocabEntry
from .point_builder import build_grammar_point


def _T(text, role=None, note=None, kind="gray", wrong=None, above=None, hl=None, color=None) -> Token:
    return Token(text=text, role=role, note=note, note_kind=kind, wrong=wrong,
                 above=above, hl=hl, color=color)


def _G(text, name, role=None, wrong=None, hl=None, above=None) -> Token:
    """어법 토큰: 이름은 note(red), 글자 red. 번호/박스는 build_grammar_point 가 처리.
    role(성분)·above(유의어 밑줄)도 함께 가질 수 있다."""
    return Token(text=text, role=role, note=name, note_kind="red", color="red",
                 wrong=wrong, hl=hl, above=above)


def mock_analysis(title_en: str = "A necessity of openness and connection in leadership",
                  lecture_label: str = "20", date: str = "2025년06월") -> Analysis:
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
    )
