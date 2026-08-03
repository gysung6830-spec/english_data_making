# -*- coding: utf-8 -*-
"""UNIT 02 목적어의 형태 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "02",
    "title": "목적어의 형태",
    "subtitle": "The Forms of the Object",
    "intro": [
        "**목적어** = 타동사·전치사의 **{{대상}}**. 우리말 ‘~을/를’(직접목적어), ‘~에게’(간접목적어).",
        "목적어 자리 = 반드시 **{{명사 상당어구}}** → ① 명사·대명사  ② 동명사·to부정사  ③ 명사절",
        "대명사가 목적어면 반드시 **{{목적격}}**(me·him·her·us·them).",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "concepts": [
                {
                    "lead": "명사·대명사가 목적어",
                    "desc": "타동사·전치사 뒤에서 ‘~을/를/에게’. 대명사는 반드시 **{{목적격}}** "
                            "(me·him·her·us·them·you·it).",
                    "examples": [
                        {"en": "I know {{him}} well.", "ko": "나는 그를 잘 안다."},
                        {"en": "She gave {{me}} a book.", "ko": "그녀는 나에게 책을 주었다. (간접목적어)"},
                        {"en": "Please wait for {{us}}.", "ko": "우리를 기다려 주세요. (전치사의 목적어)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "4형식",
                 "lines": ["give/send/tell + **간접목적어(~에게)** + **직접목적어(~을)**."]},
                {"type": "warn", "label": "함정",
                 "lines": ["전치사·and 뒤도 목적격 : between you and {{me}} (I 아님)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["대명사 **격**(주격/목적격) 판단, 특히 **전치사 뒤·and 연결** 자리."]},
            ],
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "intro": "**동사에 따라** 목적어가 동명사냐 to부정사냐 결정된다.",
            "concepts": [
                {
                    "lead": "동명사만 목적어로 (enjoy형)",
                    "desc": "enjoy·finish·mind·avoid·give up·keep·practice + **{{동명사}}**.",
                    "examples": [
                        {"en": "I enjoy {{reading}} books.", "ko": "나는 책 읽는 것을 즐긴다."},
                        {"en": "He finished {{doing}} his homework.", "ko": "그는 숙제하는 것을 끝냈다."},
                    ],
                },
                {
                    "lead": "to부정사만 목적어로 (want형)",
                    "desc": "want·hope·decide·plan·promise·expect·agree + **{{to부정사}}**.",
                    "examples": [
                        {"en": "She wants {{to go}} home.", "ko": "그녀는 집에 가기를 원한다."},
                        {"en": "They decided {{to leave}}.", "ko": "그들은 떠나기로 결정했다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "의미차",
                 "lines": [
                     "remember/forget + **to V**(앞으로 할 일) ↔ **V-ing**(과거에 한 일)",
                     "stop **to V**(하려고 멈추다) ↔ stop **V-ing**(그만두다)",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": [
                     "동사별 목적어 형태(**동명사 vs to부정사**) 고르기 = 빈출.",
                     "**stop/remember/forget** + to V / V-ing 의미 차이.",
                 ]},
            ],
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "intro": "타동사 뒤 **명사절**이 목적어. that은 생략 가능.",
            "concepts": [
                {
                    "lead": "that절이 목적어",
                    "desc": "think·believe·know·hope + 「**{{that}}** + 완전한 문장」. that **생략 가능**.",
                    "examples": [
                        {"en": "I think {{that}} he is right.", "ko": "나는 그가 옳다고 생각한다."},
                        {"en": "I hope {{that}} you succeed.", "ko": "나는 네가 성공하길 바란다."},
                    ],
                },
                {
                    "lead": "의문사절이 목적어",
                    "desc": "「**{{의문사}} + 주어 + 동사**」 어순. whether/if(~인지)도 가능.",
                    "examples": [
                        {"en": "I don't know {{what}} she wants.", "ko": "나는 그녀가 무엇을 원하는지 모른다."},
                        {"en": "Do you know {{whether}} he will come?", "ko": "그가 올지 아니?"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "어순",
                 "lines": ["간접의문문 = **평서문** 어순 「의문사 + S + V」 ( do/does 안 씀 )."]},
                {"type": "exam", "label": "시험",
                 "lines": ["**that vs what**, 간접의문문 어순, **if/whether**(~인지)."]},
            ],
        },
        {
            "no": "04",
            "title": "가목적어, 전치사의 목적어",
            "intro": "긴 목적어는 **가목적어 it**, 전치사 뒤 동사는 **동명사**.",
            "concepts": [
                {
                    "lead": "가목적어 it (5형식)",
                    "desc": "목적어(to부정사·that절)가 길면 뒤로, 자리엔 **가목적어 {{it}}**. "
                            "make/find/think/consider + **it** + 형용사 + 진목적어.",
                    "examples": [
                        {"en": "I found {{it}} hard {{to solve}} the problem.",
                         "ko": "나는 그 문제를 푸는 것이 어렵다는 것을 알았다."},
                        {"en": "She made {{it}} clear {{that}} she was angry.",
                         "ko": "그녀는 화났다는 것을 분명히 했다."},
                    ],
                },
                {
                    "lead": "전치사의 목적어",
                    "desc": "전치사 뒤에는 명사·대명사(목적격)·**{{동명사}}**. 전치사+to부정사는 **불가**.",
                    "examples": [
                        {"en": "He is good at {{swimming}}.", "ko": "그는 수영을 잘한다."},
                        {"en": "Thank you for {{helping}} me.", "ko": "도와줘서 고마워."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["전치사 뒤 동사 → **{{동명사}}** (to부정사 X). look forward to **-ing**."]},
                {"type": "exam", "label": "시험",
                 "lines": [
                     "**가목적어 it** 구조(find/make it + 형용사 + to V/that).",
                     "**전치사 뒤 동명사**(be good at -ing, be used to -ing).",
                 ]},
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
