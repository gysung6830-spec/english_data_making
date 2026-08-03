# -*- coding: utf-8 -*-
"""UNIT 03 보어의 형태 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "03",
    "title": "보어의 형태",
    "subtitle": "The Forms of the Complement",
    "intro": [
        "**보어** = 주어·목적어를 **설명**하는 말. 없으면 문장이 불완전하다.",
        "**{{주격보어}}**(2형식 S+V+SC) = 주어를 설명   /   "
        "**{{목적격보어}}**(5형식 S+V+O+OC) = 목적어를 설명.",
        "보어 자리엔 **{{명사·형용사}}**(부사 X), 분사, 동명사·to부정사가 온다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "주격보어 _ 명사, 형용사, 분사",
            "concepts": [
                {
                    "lead": "명사·형용사 보어 (2형식)",
                    "desc": "be·become·get·seem·remain + **명사/형용사**. 감각동사(look·feel·sound·"
                            "taste·smell) + **{{형용사}}**(부사 X).",
                    "examples": [
                        {"en": "She is a {{teacher}}.", "ko": "그녀는 교사다. (명사 보어)"},
                        {"en": "It sounds {{great}}.", "ko": "그거 좋게 들린다. (greatly X)"},
                    ],
                },
                {
                    "lead": "분사 보어 (감정분사)",
                    "desc": "현재분사(-ing, 능동) / 과거분사(p.p., 수동). 감정동사는 사물엔 **{{-ing}}**, "
                            "사람엔 **{{-ed}}**.",
                    "examples": [
                        {"en": "The story is {{interesting}}.", "ko": "그 이야기는 흥미롭다. (사물)"},
                        {"en": "I am {{interested}} in it.", "ko": "나는 그것에 흥미가 있다. (사람)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["감각동사(look/feel/sound…) 뒤 = **형용사** (부사 아님)."]},
                {"type": "exam", "label": "시험",
                 "lines": [
                     "감각동사 + **형용사**, 보어 자리 형용사/부사 구별.",
                     "**감정분사** -ing(사물)/-ed(사람) = 빈출 (exciting/excited).",
                 ]},
            ],
        },
        {
            "no": "02",
            "title": "주격보어 _ 동명사와 to부정사",
            "intro": "be동사 뒤 **동명사·to부정사**가 보어 = ‘~하는 것(이다)’.",
            "concepts": [
                {
                    "lead": "동명사·to부정사가 주격보어",
                    "desc": "주어가 hobby·plan·dream·job이면 보어로 **{{동명사}}** 또는 **{{to부정사}}**.",
                    "examples": [
                        {"en": "My hobby is {{collecting}} stamps.", "ko": "내 취미는 우표 수집이다."},
                        {"en": "My dream is {{to become}} a pilot.", "ko": "내 꿈은 조종사가 되는 것이다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "구별",
                 "lines": ["be + V-ing 가 **진행형**인지 **보어(동명사)**인지 문맥으로 구별."]},
                {"type": "exam", "label": "시험",
                 "lines": ["주어(dream/hobby) + be + **to부정사/동명사** 보어, 진행형과 구별."]},
            ],
        },
        {
            "no": "03",
            "title": "목적격보어 _ 명사와 형용사",
            "intro": "5형식 「S+V+O+**OC**」, OC가 목적어를 설명한다.",
            "concepts": [
                {
                    "lead": "명사·형용사가 목적격보어",
                    "desc": "call·make·find·keep·leave·name·elect + O + **명사/형용사**. OC 자리엔 부사 X.",
                    "examples": [
                        {"en": "They named the baby {{Tom}}.", "ko": "그들은 아기를 Tom이라 이름 지었다. (명사)"},
                        {"en": "The news made me {{happy}}.", "ko": "그 소식은 나를 행복하게 했다. (형용사)"},
                        {"en": "Keep the door {{open}}.", "ko": "문을 열어 둬라."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["OC 자리에 **부사 X → 형용사** : keep it {{clean}} (cleanly X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["make/keep/find + O + **형용사**(부사 아님) 구별 = 빈출."]},
            ],
        },
        {
            "no": "04",
            "title": "목적격보어 _ to부정사와 동사원형",
            "intro": "**동사에 따라** OC가 to부정사냐 동사원형이냐 결정된다.",
            "concepts": [
                {
                    "lead": "to부정사가 목적격보어",
                    "desc": "want·ask·tell·allow·expect·advise + O + **{{to부정사}}**.",
                    "examples": [
                        {"en": "I want you {{to go}}.", "ko": "나는 네가 가기를 원한다."},
                        {"en": "She told me {{to wait}}.", "ko": "그녀는 나에게 기다리라고 했다."},
                    ],
                },
                {
                    "lead": "동사원형이 목적격보어 (사역·지각)",
                    "desc": "**사역동사** make·have·let + O + **{{동사원형}}**. "
                            "**지각동사** see·hear·watch·feel + O + **{{동사원형/V-ing}}**.",
                    "examples": [
                        {"en": "She made me {{clean}} the room.", "ko": "그녀는 나에게 방을 청소하게 했다."},
                        {"en": "I saw him {{run}} (running).", "ko": "나는 그가 달리는 것을 보았다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "사역·지각동사 뒤 = **동사원형** (to V 아님) : make him {{go}} (to go X).",
                     "get은 준사역 → get + O + **to V**.",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": [
                     "**사역/지각동사 + 동사원형** vs **want류 + to부정사** = 최빈출.",
                     "수동 전환 시 지각·사역은 **to V 부활**(He was made **to go**).",
                 ]},
            ],
        },
    ],
    "wrapup": {
        "title": "보어 자리 정리",
        "headers": ["종류", "형태", "예"],
        "rows": [
            ["주격보어", "명사·형용사", "She is {{happy}}."],
            ["주격보어", "분사", "I am {{tired}}."],
            ["주격보어", "동명사·to부정사", "My job is {{to teach}}."],
            ["목적격보어", "명사·형용사", "made me {{happy}}"],
            ["목적격보어", "to부정사", "want you {{to go}}"],
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
