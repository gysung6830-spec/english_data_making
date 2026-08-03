# -*- coding: utf-8 -*-
"""UNIT 03 보어의 형태 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "03",
    "title": "보어의 형태",
    "subtitle": "The Forms of the Complement",
    "intro": [
        "**보어가 왜 필요한가?**  ‘주어+동사’만으로 뜻이 안 끝나는 동사가 있다. "
        "She is ___ / They made him ___. 이 빈자리를 채워 **뜻을 완성**하는 말이 보어다.",
        "**보어의 역할** = 다른 말을 **설명**한다. **{{주격보어}}**(주어를 설명, 2형식) / "
        "**{{목적격보어}}**(목적어를 설명, 5형식).",
        "**핵심**  보어 자리엔 **명사·형용사**(부사 X). 명사보어는 **동격(A=B)**, 형용사보어는 **상태**를 나타낸다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "주격보어 _ 명사, 형용사, 분사",
            "intro": [
                "**무엇?**  2형식「S + V + 주격보어(SC)」. be·become·get·seem·감각동사 뒤.",
                "**역할**  주어를 설명 → 명사(S = C, 동격), 형용사(S의 상태).",
                "**해석**  ‘S는 C이다 / S는 C하다’.",
            ],
            "concepts": [
                {
                    "lead": "명사·형용사 보어",
                    "desc": "be·become·seem + 명사/형용사. **감각동사**(look·feel·sound·taste·smell)는 "
                            "뒤에 **{{형용사}}**(부사 X)를 쓴다.",
                    "examples": [
                        {"en": "She is a {{teacher}}.", "ko": "그녀는 교사다. (she = teacher, 동격)"},
                        {"en": "It sounds {{great}}.", "ko": "그거 좋게 들린다. (sounds greatly X)"},
                    ],
                },
                {
                    "lead": "분사 보어 (감정분사)",
                    "desc": "감정을 나타내는 동사는, **감정을 주는 사물엔 -ing**, **감정을 느끼는 사람엔 -ed**.",
                    "examples": [
                        {"en": "The story is {{interesting}}.", "ko": "그 이야기는 흥미롭다. (사물이 흥미를 줌)"},
                        {"en": "I am {{interested}} in it.", "ko": "나는 그것에 흥미가 있다. (사람이 흥미를 느낌)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "감정분사 원리",
                 "lines": ["-ing = ‘~한 감정을 **주는**’(주로 사물) / -ed = ‘~한 감정을 **느끼는**’(주로 사람). "
                           "exciting game ↔ excited fans."]},
                {"type": "warn", "label": "함정",
                 "lines": ["감각동사(look/feel/sound…) 뒤 = **형용사**(부사 아님)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["감각동사 + 형용사, 감정분사 -ing(사물)/-ed(사람) = 빈출."]},
            ],
        },
        {
            "no": "02",
            "title": "주격보어 _ 동명사와 to부정사",
            "intro": [
                "**왜?**  보어 자리에 ‘**~하는 것**’을 넣고 싶을 때. My hobby is (책 읽는 것).",
                "**역할**  주어 = 보어 (내 취미 = 읽는 것). 동명사·to부정사 둘 다 가능.",
                "**해석**  ‘S는 ~하는 것이다’.",
            ],
            "concepts": [
                {
                    "lead": "동명사·to부정사가 주격보어",
                    "desc": "주어가 hobby·dream·plan·job이면 be동사 뒤 보어로 **{{동명사}}** 또는 **{{to부정사}}**.",
                    "examples": [
                        {"en": "My hobby is {{collecting}} stamps.", "ko": "내 취미는 우표 수집이다."},
                        {"en": "My dream is {{to become}} a pilot.", "ko": "내 꿈은 조종사가 되는 것이다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "진행형과 구별",
                 "lines": ["be + V-ing 가 **진행형**(~하는 중)인지 **보어(동명사)**(~하는 것)인지는 "
                           "**주어와의 의미(S=C 성립 여부)**로 판단."]},
                {"type": "exam", "label": "시험",
                 "lines": ["주어(dream/hobby) + be + to부정사/동명사 보어, 진행형과 구별."]},
            ],
        },
        {
            "no": "03",
            "title": "목적격보어 _ 명사와 형용사",
            "intro": [
                "**무엇?**  5형식「S + V + O + 목적격보어(OC)」.",
                "**역할**  목적어를 설명 → made him **happy**(him이 happy한 상태), named it **Tom**(it = Tom).",
                "**해석**  ‘O를 C하게 / O를 C로’.",
            ],
            "concepts": [
                {
                    "lead": "명사·형용사가 목적격보어",
                    "desc": "call·make·find·keep·leave·name·elect + O + **명사/형용사**. OC 자리엔 **부사 X**.",
                    "examples": [
                        {"en": "They named the baby {{Tom}}.", "ko": "그들은 아기를 Tom이라 지었다. (baby = Tom)"},
                        {"en": "The news made me {{happy}}.", "ko": "그 소식은 나를 행복하게 했다. (me가 happy)"},
                        {"en": "Keep the door {{open}}.", "ko": "문을 열어 둬라. (door가 open한 상태)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["OC 자리에 **부사 X → 형용사** : keep it {{clean}} (cleanly X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["make/keep/find + O + **형용사**(부사 아님) = 빈출."]},
            ],
        },
        {
            "no": "04",
            "title": "목적격보어 _ to부정사와 동사원형",
            "intro": [
                "**왜?**  목적어가 ‘**~하도록 / ~하는 것을**’ 시키거나 지각할 때. I want you (가기를).",
                "**핵심**  **동사가 OC 형태를 결정** : want형 + to V / **사역동사**(make·have·let) + 동사원형 / "
                "**지각동사**(see·hear…) + 동사원형·V-ing.",
                "**해석**  ‘O가 ~하도록/~하는 것을’.",
            ],
            "concepts": [
                {
                    "lead": "to부정사가 목적격보어 (want형)",
                    "desc": "want·ask·tell·allow·expect·advise + O + **{{to부정사}}**.",
                    "examples": [
                        {"en": "I want you {{to go}}.", "ko": "나는 네가 가기를 원한다."},
                        {"en": "She told me {{to wait}}.", "ko": "그녀는 나에게 기다리라고 했다."},
                    ],
                },
                {
                    "lead": "동사원형이 목적격보어 (사역·지각)",
                    "desc": "**사역동사** make·have·let + O + **{{동사원형}}**(직접 시킴). "
                            "**지각동사** see·hear·watch·feel + O + **{{동사원형/V-ing}}**.",
                    "examples": [
                        {"en": "She made me {{clean}} the room.", "ko": "그녀는 나에게 방을 청소하게 했다. (to clean X)"},
                        {"en": "I saw him {{run}} (running).", "ko": "나는 그가 달리는 것을 보았다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "왜 동사원형?",
                 "lines": ["사역·지각동사는 ‘**직접** 시키거나 본다’는 뜻이라 to 없이 동사원형. "
                           "단 **get**(준사역)은 to 필요 : get him **to go**."]},
                {"type": "warn", "label": "함정",
                 "lines": ["사역·지각동사 뒤 = **동사원형** (to V 아님) : make him {{go}} (to go X)."]},
                {"type": "exam", "label": "시험",
                 "lines": [
                     "사역/지각 + 동사원형 vs want류 + to부정사 = 최빈출.",
                     "**수동 전환** 시 지각·사역은 **to V 부활**(He was made **to go**).",
                 ]},
            ],
        },
    ],
    "wrapup": {
        "title": "보어 자리 정리",
        "headers": ["종류", "형태", "예"],
        "rows": [
            ["주격보어", "명사·형용사", "She is {{happy}}."],
            ["주격보어", "분사(감정)", "I am {{tired}}."],
            ["주격보어", "동명사·to부정사", "My job is {{to teach}}."],
            ["목적격보어", "명사·형용사", "made me {{happy}}"],
            ["목적격보어", "to부정사(want형)", "want you {{to go}}"],
            ["목적격보어", "동사원형(사역·지각)", "made me {{go}}"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 것을 고르시오.",
            "items": [
                "The movie was ( boring / bored ).   →  {{boring}}",
                "This soup tastes ( good / well ).   →  {{good}}",
                "My mom made me ( clean / to clean ) my room.   →  {{clean}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "Keep the window {{open}}.", "ko": "창문을 열어 둬라."},
                {"en": "I heard someone {{call}} my name.", "ko": "나는 누군가 내 이름을 부르는 것을 들었다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "I am interesting in music.  →  {{interested}}",
                "She let me to use her phone.  →  {{use}}",
                "He looks happily today.  →  {{happy}}",
            ],
        },
    ],
}
