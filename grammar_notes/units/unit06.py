# -*- coding: utf-8 -*-
"""UNIT 06 수식어구의 쓰임 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "06",
    "title": "수식어구의 쓰임",
    "subtitle": "The Use of Modifiers",
    "intro": [
        "**수식어** = 다른 말을 꾸며 뜻을 더하는 말. 문장의 필수 성분은 아니다.",
        "**형용사류**(형용사·분사·전치사구·관계절·형용사적 to부정사) → **{{명사}}** 수식.",
        "**부사류**(부사·전치사구·부사적 to부정사) → **{{동사·형용사·부사·문장}}** 수식.",
    ],
    "points": [
        {
            "no": "01",
            "title": "형용사와 부사",
            "concepts": [
                {
                    "lead": "형용사 vs 부사",
                    "desc": "**형용사** = **{{명사 수식·보어}}**. **부사** = **{{동사·형용사·부사·문장}}** 수식.",
                    "examples": [
                        {"en": "a {{beautiful}} flower", "ko": "아름다운 꽃 (형용사→명사)"},
                        {"en": "He runs {{fast}}.", "ko": "그는 빨리 달린다. (부사→동사)"},
                        {"en": "She is very {{kind}}.", "ko": "그녀는 매우 친절하다. (부사→형용사)"},
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
                 "lines": ["형용사/부사 자리 판단, **hardly·lately·nearly** 의미 구별."]},
            ],
        },
        {
            "no": "02",
            "title": "분사와 전치사구",
            "intro": "**분사·전치사구**가 명사를 꾸민다. 길면 명사 **뒤**에서 수식.",
            "concepts": [
                {
                    "lead": "분사의 명사 수식",
                    "desc": "**현재분사(-ing, 능동·진행)** / **과거분사(p.p., 수동·완료)**. "
                            "단독이면 앞, 딸린 말이 있으면 **{{뒤}}**에서.",
                    "examples": [
                        {"en": "the {{sleeping}} baby", "ko": "자고 있는 아기 (능동)"},
                        {"en": "a {{broken}} window", "ko": "깨진 창문 (수동)"},
                        {"en": "the boy {{running}} over there", "ko": "저기서 달리는 소년 (뒤에서 수식)"},
                    ],
                },
                {
                    "lead": "전치사구의 수식",
                    "desc": "「전치사 + 명사」가 명사·동사를 수식.",
                    "examples": [
                        {"en": "the book {{on the desk}}", "ko": "책상 위의 책 (명사 수식)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "compare", "label": "비교",
                 "lines": ["현재분사(**능동** ~하는)  ↔  과거분사(**수동** ~된/당한)"]},
                {"type": "exam", "label": "시험",
                 "lines": ["수식받는 명사와의 관계가 **능동/수동** → 현재분사/과거분사 고르기 = 빈출."]},
            ],
        },
        {
            "no": "03",
            "title": "형용사 역할의 to부정사",
            "intro": "to부정사가 **명사·대명사 뒤**에서 형용사처럼 수식 = ‘~할, ~하는’.",
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
                 "lines": [
                     "수식받는 명사가 전치사의 목적어면 **to V 뒤 전치사** 필요 : "
                     "a house to live {{in}} / a pen to write {{with}}.",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["명사 + to부정사 어순, **to V 뒤 전치사**(live in) 누락 오류."]},
            ],
        },
        {
            "no": "04",
            "title": "부사 역할의 to부정사",
            "intro": "to부정사가 부사처럼 **목적·감정·결과·판단 근거**를 나타낸다.",
            "concepts": [
                {
                    "lead": "to부정사의 부사적 용법",
                    "desc": "**{{목적}}**(~하기 위해, =in order to)·감정의 원인·판단 근거·결과.",
                    "examples": [
                        {"en": "I study hard {{to pass}} the exam.", "ko": "시험에 합격하려고 열심히 공부한다. (목적)"},
                        {"en": "I'm glad {{to see}} you.", "ko": "너를 만나서 기쁘다. (감정의 원인)"},
                        {"en": "He must be smart {{to solve}} it.", "ko": "그것을 풀다니 그는 똑똑함에 틀림없다. (판단)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "목적 강조",
                 "lines": ["목적을 분명히 : **in order to** / **so as to** + 동사원형."]},
                {"type": "exam", "label": "시험",
                 "lines": ["to부정사 부사적 용법의 **의미**(목적/원인/결과) 파악, in order to."]},
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
                "I have hardly time.  →  (‘거의 없다’면 OK, ‘시간이 많다’ 뜻이면) {{little}}",
                "a broke window  →  {{broken}}",
                "a house to live  →  {{to live in}}",
            ],
        },
    ],
}
