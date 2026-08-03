# -*- coding: utf-8 -*-
"""UNIT 08 관계사 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "08",
    "title": "관계사",
    "subtitle": "Relatives",
    "intro": [
        "**관계사** = 두 문장을 이어 주며 **선행사(명사)를 꾸미는** 절을 이끈다.",
        "**관계대명사**(who·which·that·whose) : 뒤 문장이 **{{불완전}}**(주어·목적어 빠짐).",
        "**관계부사**(when·where·why·how) : 뒤 문장이 **{{완전}}**.",
    ],
    "points": [
        {
            "no": "01",
            "title": "주격 관계대명사",
            "concepts": [
                {
                    "lead": "주격 관계대명사 (+ 동사)",
                    "desc": "「선행사 + 관계대명사 + **{{동사}}**」. 사람 = **{{who}}**, 사물 = **{{which}}**, 공통 = that.",
                    "examples": [
                        {"en": "I know the boy {{who}} lives next door.", "ko": "나는 옆집에 사는 소년을 안다."},
                        {"en": "This is the book {{which}} won the prize.", "ko": "이것이 그 상을 받은 책이다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["관계사절 동사의 **수 = 선행사**에 일치 : the students who {{are}} …"]},
                {"type": "exam", "label": "시험",
                 "lines": ["선행사(사람/사물)에 맞는 **who/which**, 절 동사 **수 일치**."]},
            ],
        },
        {
            "no": "02",
            "title": "목적격 관계대명사",
            "intro": "뒤 문장에 **목적어가 빠진** 절을 이끈다. 생략 가능.",
            "concepts": [
                {
                    "lead": "목적격 관계대명사 (+ 주어+동사)",
                    "desc": "「선행사 + 관계대명사 + **{{주어 + 동사}}**」(목적어 결여). 사람 whom(who), 사물 which, that. "
                            "**{{생략}}** 가능.",
                    "examples": [
                        {"en": "The man (whom) I met {{was}} kind.", "ko": "내가 만난 남자는 친절했다."},
                        {"en": "The book (which) you gave me is great.", "ko": "네가 준 책은 훌륭하다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "생략",
                 "lines": ["목적격 관계대명사는 **생략 가능**. 단, **전치사 + 관계대명사**(in which)는 생략 불가."]},
                {"type": "exam", "label": "시험",
                 "lines": ["목적격 관계사 뒤 **S+V**(목적어 결여), 생략, whom."]},
            ],
        },
        {
            "no": "03",
            "title": "소유격 관계대명사",
            "intro": "선행사의 **소유**를 나타낸다.",
            "concepts": [
                {
                    "lead": "소유격 관계대명사 whose",
                    "desc": "**{{whose}}** + 명사 (사람·사물 공통). whose 뒤엔 **관사 없는 명사**가 바로 온다.",
                    "examples": [
                        {"en": "I have a friend {{whose}} father is a doctor.",
                         "ko": "나는 아버지가 의사인 친구가 있다."},
                        {"en": "a house {{whose}} roof is red", "ko": "지붕이 빨간 집 (= the roof of which)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "전환",
                 "lines": ["whose + 명사 = **the 명사 + of which** (사물)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["소유격 **whose** 자리, of which 전환."]},
            ],
        },
        {
            "no": "04",
            "title": "관계부사",
            "intro": "「전치사 + 관계대명사」 = **관계부사**, 뒤에 **완전한 문장**.",
            "concepts": [
                {
                    "lead": "관계부사 when/where/why/how",
                    "desc": "시간 **{{when}}**·장소 **{{where}}**·이유 why·방법 how. 뒤 문장은 **{{완전}}**.",
                    "examples": [
                        {"en": "the day {{when}} we met", "ko": "우리가 만난 날 (= on which)"},
                        {"en": "the place {{where}} I was born", "ko": "내가 태어난 곳 (= in which)"},
                        {"en": "the reason {{why}} he left", "ko": "그가 떠난 이유"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "관계부사 뒤 = **완전한 문장** / 관계대명사 뒤 = **불완전**.",
                     "**the way** 와 **how** 는 함께 못 씀 (하나만).",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["**관계대명사 vs 관계부사**(뒤 문장 완전성 판단) = 최빈출."]},
            ],
        },
    ],
    "wrapup": {
        "title": "관계사 정리",
        "headers": ["관계사", "선행사", "뒤 문장"],
        "rows": [
            ["who(주격)", "사람", "{{동사}}~ (주어 결여)"],
            ["which(주격)", "사물", "동사~"],
            ["whom(목적격)", "사람", "{{S+V}}~ (목적어 결여)"],
            ["whose(소유격)", "사람·사물", "명사 + S+V"],
            ["관계부사 when/where", "시간·장소", "{{완전한}} 문장"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 관계사를 고르시오.",
            "items": [
                "I have a friend ( who / which ) speaks French.   →  {{who}}",
                "This is the house ( which / where ) I live.   →  {{where}}",
                "The girl ( whose / who ) hair is long is my sister.   →  {{whose}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "The man {{who}} called you is my uncle.", "ko": "너에게 전화한 남자는 내 삼촌이다."},
                {"en": "I remember the day {{when}} we first met.", "ko": "나는 우리가 처음 만난 날을 기억한다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "The book who I read was fun.  →  {{which/that}}",
                "This is the reason which he left.  →  {{why}}",
                "The students who is here are kind.  →  {{are}}",
            ],
        },
    ],
}
