# -*- coding: utf-8 -*-
"""UNIT 02 목적어의 형태 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "02",
    "title": "목적어의 형태",
    "subtitle": "The Forms of the Object",
    "intro": [
        "**목적어가 왜 필요한가?**  타동사·전치사는 **대상**이 있어야 뜻이 완성된다. "
        "eat(먹다) → 무엇을? / for → 무엇을 위해? — 그 대상이 목적어다.",
        "**목적어의 역할** = 동사·전치사의 **{{대상}}**. ‘~을/를’(직접목적어), ‘~에게’(간접목적어).",
        "**무엇이 목적어가 되나?**  주어처럼 명사 노릇 하는 말 — 명사·대명사(**{{목적격}}**), "
        "동명사·to부정사, 명사절.",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "intro": [
                "**무엇?**  가장 기본 목적어. 타동사·전치사 뒤의 명사·대명사.",
                "**핵심**  대명사는 반드시 **{{목적격}}**(me·him·her·us·them). "
                "4형식은 ‘**~에게(간접) + ~을(직접)**’ 두 개의 목적어.",
                "**해석**  ‘~을/를’, ‘~에게’.",
            ],
            "concepts": [
                {
                    "lead": "명사·대명사가 목적어",
                    "desc": "타동사·전치사 뒤에서 대상을 나타낸다. 대명사는 주격이 아니라 **{{목적격}}**.",
                    "examples": [
                        {"en": "I know {{him}} well.", "ko": "나는 그를 잘 안다. (타동사의 목적어)"},
                        {"en": "Please wait for {{us}}.", "ko": "우리를 기다려 주세요. (전치사 for의 목적어)"},
                    ],
                },
                {
                    "lead": "4형식 — 목적어가 둘",
                    "desc": "give·send·tell·show + **간접목적어(~에게)** + **직접목적어(~을)**. "
                            "순서를 바꾸면 「직접목적어 + **{{to/for}}** + 간접목적어」.",
                    "examples": [
                        {"en": "She gave {{me}} a book.",
                         "ko": "그녀는 나에게 책을 주었다. (= gave a book {{to}} me)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["전치사·and 뒤도 목적격 : between you and {{me}} (I 아님)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["대명사 **격** 판단(전치사 뒤·and 연결), 4형식 ↔ 3형식 전환(to/for)."]},
            ],
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "intro": [
                "**왜?**  동사를 목적어로 쓸 때도 명사형으로 바꾼다. 그런데 **어떤 동사는 동명사만, "
                "어떤 동사는 to부정사만** 목적어로 받는다 — **동사가 결정한다.**",
                "**핵심**  enjoy형(동명사) / want형(to부정사) / like형(둘 다)로 **동사를 분류해 외운다.**",
                "**해석**  ‘~하는 것을/~하기를’.",
            ],
            "concepts": [
                {
                    "lead": "동명사만 받는 동사 (enjoy형)",
                    "desc": "enjoy·finish·mind·avoid·give up·keep·practice + **{{동명사}}**. "
                            "‘이미·현재 하고 있는’ 느낌의 동사들.",
                    "examples": [
                        {"en": "I enjoy {{reading}} books.", "ko": "나는 책 읽는 것을 즐긴다. (enjoy to read X)"},
                        {"en": "He finished {{doing}} his homework.", "ko": "그는 숙제하는 것을 끝냈다."},
                    ],
                },
                {
                    "lead": "to부정사만 받는 동사 (want형)",
                    "desc": "want·hope·decide·plan·promise·expect·agree + **{{to부정사}}**. "
                            "‘앞으로 할·바라는’ 느낌의 동사들.",
                    "examples": [
                        {"en": "She wants {{to go}} home.", "ko": "그녀는 집에 가기를 원한다. (want going X)"},
                        {"en": "They decided {{to leave}}.", "ko": "그들은 떠나기로 결정했다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "의미가 달라지는 동사",
                 "lines": [
                     "remember/forget + **to V**(앞으로 할 일) ↔ **V-ing**(과거에 한 일)",
                     "stop + **to V**(~하려고 멈추다) ↔ **V-ing**(~을 그만두다)",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["동사별 목적어 형태(동명사 vs to부정사), stop/remember to·-ing 의미차 = 빈출."]},
            ],
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "intro": [
                "**왜?**  타동사의 목적어로 **문장 전체**를 넣고 싶을 때. I think + (그가 옳다).",
                "**핵심**  think·know류 뒤 that절은 **that 생략 가능**. 의문사절은 평서문 어순.",
                "**해석**  ‘~라고/~인지를’.",
            ],
            "concepts": [
                {
                    "lead": "that절이 목적어 — ‘~라고’",
                    "desc": "think·believe·know·hope + 「**{{that}}** + 완전한 문장」. 구어에서 that **생략** 가능.",
                    "examples": [
                        {"en": "I think {{that}} he is right.", "ko": "나는 그가 옳다고 생각한다."},
                        {"en": "I hope {{that}} you succeed.", "ko": "나는 네가 성공하길 바란다."},
                    ],
                },
                {
                    "lead": "의문사절이 목적어 — ‘~인지를’",
                    "desc": "「**{{의문사}} + 주어 + 동사**」. whether/if(~인지)도 목적어로 쓴다.",
                    "examples": [
                        {"en": "I don't know {{what}} she wants.", "ko": "나는 그녀가 무엇을 원하는지 모른다."},
                        {"en": "Do you know {{whether}} he will come?", "ko": "너는 그가 올지 아니?"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "어순 함정",
                 "lines": ["간접의문문 = 평서문 어순「의문사 + S + V」(do/does 안 씀)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["that vs what, 간접의문문 어순, if/whether(~인지)."]},
            ],
        },
        {
            "no": "04",
            "title": "가목적어, 전치사의 목적어",
            "intro": [
                "**왜(가목적어)?**  5형식「S+V+O+보어」에서 목적어가 to부정사·that절처럼 길면 보어보다 앞에 두기 "
                "어색하다 → 목적어를 뒤로 보내고 자리에 **가목적어 it**.",
                "**왜(전치사)?**  전치사 뒤엔 명사가 와야 하니, 동사는 **동명사**로 바꾼다.",
                "**해석**  가목적어 it 은 해석 안 함(진목적어를 해석).",
            ],
            "concepts": [
                {
                    "lead": "가목적어 it (5형식)",
                    "desc": "make/find/think/consider + **가목적어 {{it}}** + 형용사(보어) + **진목적어**(to V·that절). "
                            "긴 목적어를 뒤로 보낸 구조.",
                    "examples": [
                        {"en": "I found {{it}} hard {{to solve}} the problem.",
                         "ko": "나는 그 문제를 푸는 것이 어렵다는 걸 알았다. (it=가목적어, to solve…=진목적어)"},
                        {"en": "She made {{it}} clear {{that}} she was angry.",
                         "ko": "그녀는 화났다는 것을 분명히 했다."},
                    ],
                },
                {
                    "lead": "전치사의 목적어",
                    "desc": "전치사 뒤에는 명사·대명사(목적격)·**{{동명사}}**. 전치사 + to부정사는 **불가**.",
                    "examples": [
                        {"en": "He is good at {{swimming}}.", "ko": "그는 수영을 잘한다. (good at to swim X)"},
                        {"en": "Thank you for {{helping}} me.", "ko": "도와줘서 고마워."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["전치사 뒤 동사 → **동명사** : look forward to **-ing**, be used to **-ing**."]},
                {"type": "exam", "label": "시험",
                 "lines": ["가목적어 it 구조(find/make it + 형용사 + to V/that), 전치사 뒤 동명사."]},
            ],
        },
    ],
    "wrapup": {
        "title": "목적어 자리 정리",
        "headers": ["형태", "예", "비고"],
        "rows": [
            ["명사·대명사", "I know {{him}}.", "대명사=목적격"],
            ["동명사", "enjoy {{reading}}", "enjoy·finish·avoid…"],
            ["to부정사", "want {{to go}}", "want·hope·decide…"],
            ["that절", "think {{that}} …", "that 생략 가능"],
            ["의문사절", "know {{what}} S+V", "평서문 어순"],
            ["가목적어 it", "find {{it}} hard to V", "5형식 긴 목적어"],
            ["전치사+동명사", "good at {{swimming}}", "to부정사 불가"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 형태를 고르시오.",
            "items": [
                "I enjoy ( to swim / swimming ).   →  {{swimming}}",
                "She decided ( to move / moving ) to Seoul.   →  {{to move}}",
                "He is interested in ( learn / learning ) Chinese.   →  {{learning}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "I found {{it}} easy {{to}} use this app.", "ko": "나는 이 앱을 쓰는 것이 쉬웠다."},
                {"en": "Do you know {{what}} he {{wants}}?", "ko": "너는 그가 무엇을 원하는지 아니?"},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "Thank you for to help me.  →  {{helping}}",
                "I want going home now.  →  {{to go}}",
                "Between you and I, it's a secret.  →  {{me}}",
            ],
        },
    ],
}
