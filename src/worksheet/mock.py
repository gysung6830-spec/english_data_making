"""API 없이 레이아웃/디자인을 미리 보기 위한 목(mock) Analysis.

명세서 §11: '목업은 배관만 확인' — 실제 태깅 품질은 API 키로 검증.
참고 학습지(지문 20 '차·리더십')를 재현한다. 각 문장은 '한 덩어리(한 줄)'로 넣어
자연스럽게 이어지고 폭에 맞춰 자동 줄바꿈되게 한다. 뒷페이지(어휘 리스트/논리 흐름도/
쉬운 예시 목차)도 함께 담아 렌더러의 모든 요소를 확인한다.
"""
from __future__ import annotations

from .models import Analysis, FlowStep, Point, Sentence, Token, VocabEntry


def _T(text, role=None, note=None, kind="gray", wrong=None, above=None,
       hl=None, underline=False, color=None) -> Token:
    return Token(text=text, role=role, note=note, note_kind=kind, wrong=wrong,
                 above=above, hl=hl, underline=underline, color=color)


def _hl(words, hl="y"):
    return [_T(w, hl=hl) for w in words]


def mock_analysis(title_en: str = "A necessity of openness and connection in leadership",
                  lecture_label: str = "20", date: str = "2025년06월") -> Analysis:
    s01 = Sentence(
        index=1,
        lines=[[
            _T("Imagine", role="V"),
            _T("(you"), _T("have"), _T("the best tea"), _T("in the world"),
            _T("and", role="병렬"), _T("you"), _T("put"),
            _T("it"), _T("into a bag"),
            _T("(that's", role="주관대", color="red", wrong="what(X)"),
            _T("impermeable)).", color="blue", above="= non-porous", note="↔ permeable, porous"),
        ]],
        translation="당신이 세상에서 제일 좋은 차(茶)를 가지고 있고, 당신이 그것을 스며들지 않는 티백에 넣는다고 상상해 보라.",
        refs=["it → the best tea"],
        points=[Point(kind="reading", caption="1번 문장 내용 TMI",
                      body_html="세상에서 제일 비싼 찻잎이 있어도 물이 아예 안 들어오는 "
                                "꽉 막힌 봉지에 넣어두면 아무짝에도 쓸모없다는 뜻이야.")],
    )
    s02 = Sentence(
        index=2,
        lines=[[
            _T("It"), _T("won't"),
            _T("work.", color="blue", role="V", above="= infuse (우러나다)"),
        ]],
        translation="그것은 작용하지 않을 것이다.",
        refs=["It → 막힌 봉지 속 그 차"],
    )
    s03 = Sentence(
        index=3,
        gloss_en="Even the finest tea is useless if it remains isolated without contact with water.",
        lines=[_hl(["You", "just", "won't", "be able to", "make", "a cup of tea."])],
        translation="당신은 그저 차 한 잔을 만들 수 없을 것이다.",
    )
    s04 = Sentence(
        index=4,
        lines=[[
            _T("(For the teabag", role="to부정사의 의미상 주어"),
            _T("to work),", role="to부정사(부사)"),
            _T("it"), _T("needs to be"),
            _T("porous.", color="blue", above="↔ non-porous", note="= permeable"),
        ]],
        translation="티백이 작용하려면, 그것은 구멍이 있어야 한다.",
        refs=["it → the teabag(티백)"],
        points=[Point(kind="reading", caption="4번 문장 내용 TMI",
                      body_html="맛있는 차를 마시려면 티백에 미세한 구멍이 뚫려 있어서 "
                                "물이랑 찻잎이 서로 만나야만 해.")],
    )
    s05 = Sentence(
        index=5,
        lines=[[
            _T("You"), _T("need", role="5V"),
            _T("the tea", role="O①"), _T("and", role="병렬"), _T("the water", role="O②"),
            _T("to come in contact with", role="OC", color="blue",
               above="= interact with", note="↔ be isolated from"),
            _T("each other."),
        ]],
        translation="당신은 차와 물이 서로 접촉할 수 있도록 해야 한다.",
    )
    s06 = Sentence(
        index=6,
        badge="빈",
        lines=[[
            _T("(In our lives too),"), _T("we"), _T("cannot"),
            _T("survive", role="V①"), _T("and", role="병렬"),
            _T("thrive", role="V②", color="blue", above="↔ decline", note="= flourish"),
            _T("(in isolation).", note="고립된 채로"),
        ]],
        translation="우리 삶에서도 마찬가지로, 우리는 고립된 채로는 살아갈 수도 성장할 수도 없다.",
        refs=["we → 우리(사람)"],
    )
    s07 = Sentence(
        index=7,
        badge="서",
        lines=[[
            _T("Leaders"), _T("need to be careful"),
            _T("(not to build", role="to부정사(부사)", hl="y"),
            _T("walls", hl="y"), _T("around", hl="y"),
            _T("themselves", hl="y", wrong="them(X)"),
            _T("(that", role="주관대", color="red", note="선행사: walls", wrong="who(X)"),
            _T("prevent", hl="y", note="prevent A\nfrom -ing"),
            _T("people", hl="y"),
            _T("from reaching out to", hl="y", note="~에게 다가가다"),
            _T("them)).", hl="y"),
        ]],
        translation="리더는 사람들이 그들에게 다가오지 못하게 막는 벽을 그들 자신의 주변에 쌓지 않도록 주의해야 한다.",
        refs=["themselves / them → leaders(리더 자신)"],
        points=[
            Point(kind="grammar", caption="7번 문장 어법 Point",
                  body_html="① <b>주격 관계대명사 that</b><ul>"
                            "<li>선행사 <b>walls</b> 를 수식</li>"
                            "<li>뒤에 주어 없는 불완전한 절 → 주격</li>"
                            "<li>사물 선행사라 <b>who(X)</b> 는 오답</li></ul>"
                            "= walls <b>which[that]</b> prevent ~"),
            Point(kind="reading", caption="7번 문장 내용 TMI",
                  body_html='리더가 자기 주변에 높은 벽을 쌓고 "아무도 오지 마!"라고 하면, '
                            "아무도 그 리더를 도와줄 수 없게 돼."),
        ],
    )
    s08 = Sentence(
        index=8,
        lines=[[
            _T("(As a leader),"), _T("you"), _T("need"),
            _T("(to be able to", role="to부정사(명사)"),
            _T("touch", color="blue", above="= come in\ncontact with", note="↔ detach"),
            _T("other people).", role="other+복수명사"),
        ]],
        translation="리더로서, 당신은 다른 사람들과 접촉할 수 있어야 한다.",
        refs=["you → 리더(독자)"],
    )
    s09 = Sentence(
        index=9,
        lines=[[
            _T("The tea"),
            _T("was meant to", note="be meant to\n~하도록 의도되다"),
            _T("mix", color="blue", above="= mingle with"),
            _T("with the water."),
        ]],
        translation="차는 물과 섞이도록 의도되었다.",
    )
    s10 = Sentence(
        index=10,
        badge="빈",
        lines=[[
            _T("Similarly", hl="p", color="blue", above="= Likewise"),
            _T("all of us", role="S"),
            _T("were designed", color="red", note="수동태", wrong="designed(X)"),
            _T("(to work", role="to부정사(부사)"),
            _T("with other people,", role="전치사구①"),
            _T("with teams,", role="②"),
            _T("and with society", role="③"),
            _T("(at large)).", note="더 크게는"),
        ]],
        translation="마찬가지로 우리 모두도 다른 사람들, 팀, 그리고 더 크게는 사회와 함께 일하도록 설계되었다.",
        refs=["all of us → 우리 모두(사람 전체)"],
        points=[Point(kind="reading", caption="10번 문장 내용 TMI",
                      body_html="찻잎이 물과 섞여야 차가 되듯, 우리도 동료나 사회와 부대끼며 "
                                "살아가야 제대로 실력 발휘를 할 수 있게 만들어졌어.")],
    )

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
        sentences=[s01, s02, s03, s04, s05, s06, s07, s08, s09, s10],
        vocab=vocab, flow=flow,
    )
