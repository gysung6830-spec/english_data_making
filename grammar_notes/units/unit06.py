# -*- coding: utf-8 -*-
"""UNIT 06 수식어구의 쓰임 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "06",
    "title": "수식어구의 쓰임",
    "subtitle": "The Use of Modifiers",
    "intro": [
        "**수식어가 왜 필요한가?**  문장 뼈대(주어·동사·목적어·보어)만으로는 정보가 부족하다. "
        "‘어떤·어떻게·언제·왜’를 덧붙여 **더 구체적으로** 만드는 것이 수식어다.",
        "**두 갈래**  **{{형용사}}류**(명사 꾸밈) ↔ **{{부사}}류**(동사·형용사·부사·문장 꾸밈).",
        "**핵심**  ‘**무엇을 꾸미느냐**’로 형용사인지 부사인지가 결정된다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "형용사와 부사",
            "intro": [
                "**역할**  형용사 = **{{명사}}** 수식·보어 / 부사 = **{{동사·형용사·부사·문장}}** 수식.",
                "**해석**  형용사 ‘~한’ / 부사 ‘~하게·~히’.",
            ],
            "concepts": [
                {
                    "lead": "형용사 vs 부사",
                    "desc": "형용사는 명사 앞이나 보어 자리, 부사는 그 밖(동사·형용사·부사·문장 전체)을 꾸민다.",
                    "examples": [
                        {"en": "a {{beautiful}} flower", "ko": "아름다운 꽃 (형용사 → 명사)"},
                        {"en": "He runs {{fast}}.", "ko": "그는 빨리 달린다. (부사 → 동사)"},
                        {"en": "She is very {{kind}}.", "ko": "그녀는 매우 친절하다. (부사 very → 형용사 kind)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "혼동어",
                 "lines": [
                     "hard(열심히) ↔ **{{hardly}}**(거의 ~않다)",
                     "late(늦게) ↔ **{{lately}}**(최근에)  /  near(가까이) ↔ nearly(거의)",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["형용사/부사 자리 판단, hardly·lately·nearly 의미 구별."]},
            ],
        },
        {
            "no": "02",
            "title": "분사와 전치사구",
            "intro": [
                "**왜?**  명사를 한 단어 형용사로 다 못 꾸밀 때, **분사·전치사구**로 꾸민다.",
                "**핵심**  현재분사(-ing, **능동·진행**) / 과거분사(p.p., **수동·완료**). "
                "딸린 말이 있으면 명사 **{{뒤}}**에서 수식.",
                "**해석**  ‘~하는(능동)/~된(수동) (명사)’.",
            ],
            "concepts": [
                {
                    "lead": "분사의 명사 수식",
                    "desc": "명사가 **직접 하는** 동작이면 현재분사, **당하는** 동작이면 과거분사.",
                    "examples": [
                        {"en": "the {{sleeping}} baby", "ko": "자고 있는 아기 (아기가 잠 → 능동)"},
                        {"en": "a {{broken}} window", "ko": "깨진 창문 (창문이 깨짐 → 수동)"},
                        {"en": "the boy {{running}} over there", "ko": "저기서 달리는 소년 (딸린 말 → 명사 뒤)"},
                    ],
                },
                {
                    "lead": "전치사구의 수식",
                    "desc": "「전치사 + 명사」가 명사·동사를 꾸민다.",
                    "examples": [
                        {"en": "the book {{on the desk}}", "ko": "책상 위의 책 (명사 수식)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "능동/수동 판별",
                 "lines": ["수식받는 명사가 그 동작을 **하면 -ing**, **당하면 p.p.** : "
                           "the exciting movie(흥미를 줌) ↔ the excited crowd(흥분함)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["명사와의 관계(능동/수동) → 현재분사/과거분사 고르기 = 빈출."]},
            ],
        },
        {
            "no": "03",
            "title": "형용사 역할의 to부정사",
            "intro": [
                "**왜?**  ‘**~할 (명사)**’처럼 명사에 ‘앞으로 할 일’의 뜻을 덧붙일 때.",
                "**위치**  명사·대명사 **뒤**에서 수식.",
                "**해석**  ‘~할, ~하는 (명사)’.",
            ],
            "concepts": [
                {
                    "lead": "to부정사의 형용사적 용법",
                    "desc": "「명사 + **{{to부정사}}**」. -thing/-one은 「-thing + 형용사 + to V」 어순.",
                    "examples": [
                        {"en": "I need something {{to eat}}.", "ko": "나는 먹을 것이 필요하다."},
                        {"en": "something {{cold}} to drink", "ko": "마실 차가운 것"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["수식받는 명사가 전치사의 목적어면 **to V 뒤 전치사** 필요 : "
                           "a house to live {{in}} / a pen to write {{with}}."]},
                {"type": "exam", "label": "시험",
                 "lines": ["명사 + to부정사 어순, to V 뒤 전치사(live in) 누락 오류."]},
            ],
        },
        {
            "no": "04",
            "title": "부사 역할의 to부정사",
            "intro": [
                "**왜?**  동작에 **목적·감정의 원인·결과·판단의 근거**를 덧붙일 때.",
                "**해석**  목적 ‘~하기 위해’ / 원인 ‘~해서’ / 판단 ‘~하다니’.",
            ],
            "concepts": [
                {
                    "lead": "to부정사의 부사적 용법",
                    "desc": "**{{목적}}**(~하기 위해, = in order to)·감정의 원인·판단 근거·결과 등을 나타낸다.",
                    "examples": [
                        {"en": "I study hard {{to pass}} the exam.", "ko": "시험에 합격하려고 열심히 공부한다. (목적)"},
                        {"en": "I'm glad {{to see}} you.", "ko": "너를 만나서 기쁘다. (감정의 원인)"},
                        {"en": "He must be smart {{to solve}} it.", "ko": "그것을 풀다니 똑똑함에 틀림없다. (판단 근거)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "목적 강조",
                 "lines": ["목적을 분명히 하려면 **in order to / so as to** + 동사원형."]},
                {"type": "read", "label": "의미 구별",
                 "lines": ["‘~하기 위해(목적)’인지 ‘~해서(원인)’인지 ‘~하다니(판단)’인지 **문맥**으로 구별."]},
                {"type": "exam", "label": "시험",
                 "lines": ["to부정사 부사적 용법의 의미(목적/원인/결과) 파악, in order to."]},
            ],
        },
    ],
    "wrapup": {
        "title": "수식어구 정리",
        "headers": ["수식어", "꾸미는 대상", "예"],
        "rows": [
            ["형용사", "명사", "a {{kind}} man"],
            ["부사", "동사·형용사 등", "runs {{fast}}"],
            ["현재분사", "명사(능동)", "{{sleeping}} baby"],
            ["과거분사", "명사(수동)", "{{broken}} window"],
            ["to부정사(형용사)", "명사 뒤", "something {{to eat}}"],
            ["to부정사(부사)", "동사·문장", "study {{to pass}}"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 것을 고르시오.",
            "items": [
                "He works ( hard / hardly ) every day.   →  {{hard}}",
                "Look at the ( exciting / excited ) game.   →  {{exciting}}",
                "I want something ( to drink / drink ).   →  {{to drink}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "The girl {{singing}} on the stage is my sister.", "ko": "무대에서 노래하는 소녀는 내 여동생이다."},
                {"en": "I have no chair {{to sit}} on.", "ko": "나는 앉을 의자가 없다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "a broke window  →  {{broken}}",
                "a house to live  →  {{to live in}}",
                "She sings beautiful.  →  {{beautifully}}",
            ],
        },
    ],
}
