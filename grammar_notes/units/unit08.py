# -*- coding: utf-8 -*-
"""UNIT 08 관계사 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "08",
    "title": "관계사",
    "subtitle": "Relatives",
    "intro": [
        "**관계사가 왜 필요한가?**  같은 명사를 두 번 말하는 두 문장을, 반복을 없애고 **한 문장으로 잇기** 위해서다. "
        "예) I know a boy. + **He** lives next door. → I know a boy **who** lives next door.",
        "**관계사의 역할** = 「**{{접속사}}** + **{{대명사(또는 부사)}}**」 두 가지를 **동시에** 한다. "
        "그래서 접속사(and, but처럼)를 또 쓰지 않는다.",
        "**해석법** : 관계사 자체는 따로 해석하지 않고, **관계사절 전체를 선행사 앞으로 당겨** "
        "‘**~하는/~한 (선행사)**’로 해석한다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "주격 관계대명사",
            "intro": [
                "**언제?**  두 문장의 공통 명사가 **뒤 문장의 주어**일 때 → 그 주어를 관계대명사로 바꿔 연결.",
                "**역할**  「접속사 + **주어**」 이므로, 관계대명사 **바로 뒤에 {{동사}}** 가 온다.",
                "**해석**  ‘**~하는/~인 (선행사)**’.",
            ],
            "concepts": [
                {
                    "lead": "만드는 과정 (두 문장 → 한 문장)",
                    "desc": "두 문장의 공통 명사를 찾고, 그것이 **뒤 문장의 주어**이면 → **{{who/which}}** 로 바꿔 "
                            "문장 앞으로 빼고 두 문장을 잇는다.",
                    "examples": [
                        {"en": "I know the boy.  +  He lives next door.\n"
                               "→ I know the boy {{who}} lives next door.",
                         "ko": "나는 옆집에 사는 그 소년을 안다. (He = the boy → who)"},
                        {"en": "The book {{which}} is on the desk is mine.",
                         "ko": "책상 위에 있는 그 책은 내 것이다. (It is on the desk → which)"},
                    ],
                },
                {
                    "lead": "선행사에 따른 선택",
                    "desc": "사람 = **{{who}}**, 사물·동물 = **{{which}}**, 사람·사물 공통 = **that**. "
                            "주격은 생략할 수 없다.",
                    "examples": [
                        {"en": "the girl {{who}} sings well", "ko": "노래를 잘하는 그 소녀"},
                        {"en": "a car {{which}} runs fast", "ko": "빨리 달리는 자동차"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "해석",
                 "lines": ["관계사절 「who lives next door」를 통째로 선행사 앞에 붙여 "
                           "‘**옆집에 사는** 그 소년’처럼 해석한다."]},
                {"type": "warn", "label": "함정",
                 "lines": ["관계사절 동사의 **수 = 선행사**에 맞춘다 : the students who {{are}} kind."]},
                {"type": "exam", "label": "시험",
                 "lines": ["선행사(사람/사물)에 맞는 **who/which**, 절 동사 **수 일치**."]},
            ],
        },
        {
            "no": "02",
            "title": "목적격 관계대명사",
            "intro": [
                "**언제?**  공통 명사가 **뒤 문장의 목적어**일 때.",
                "**역할**  「접속사 + **목적어**」 → 목적어가 빠져나갔으므로 뒤에 **{{주어 + 동사}}** 가 오고 "
                "**목적어 자리가 비어** 있다.",
                "**해석**  ‘(주어)가 ~하는 (선행사)’.",
            ],
            "concepts": [
                {
                    "lead": "만드는 과정",
                    "desc": "공통 명사가 **뒤 문장의 목적어**이면 → **{{whom/which}}** 로 바꿔 앞으로 뺀다. "
                            "그 결과 관계사 뒤 문장은 **목적어가 빠진 불완전한** 문장이 된다.",
                    "examples": [
                        {"en": "This is the book.  +  You gave it to me.\n"
                               "→ This is the book {{which}} you gave me.",
                         "ko": "이것은 네가 나에게 준 그 책이다. (it = the book → which, 목적어 자리 빔)"},
                        {"en": "The man {{whom}} I met was kind.",
                         "ko": "내가 만난 그 남자는 친절했다. (I met him → whom)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "판별",
                 "lines": ["관계사 뒤 문장에 **목적어가 비어** 있으면 = **목적격** 관계대명사."]},
                {"type": "tip", "label": "생략",
                 "lines": ["목적격 관계대명사는 **생략 가능** (뒤에 S+V가 바로 오면 생략된 것). "
                           "단 **전치사 + 관계대명사**(in which)는 생략 불가."]},
                {"type": "exam", "label": "시험",
                 "lines": ["목적격 관계사 뒤 **S+V**(목적어 결여), 생략 여부, whom."]},
            ],
        },
        {
            "no": "03",
            "title": "소유격 관계대명사",
            "intro": [
                "**언제?**  공통 명사가 뒤 문장에서 **다른 명사의 소유격(~의)**으로 쓰일 때.",
                "**역할**  「접속사 + **소유격(his/her/its)**」 → **{{whose}} + 명사**.",
                "**해석**  ‘그 (선행사)의 ~가 …인’.",
            ],
            "concepts": [
                {
                    "lead": "만드는 과정",
                    "desc": "뒤 문장의 **his/her/its + 명사** 를 → **{{whose}} + 명사** 로 바꾼다. "
                            "whose 뒤에는 **관사 없는 명사**가 바로 온다.",
                    "examples": [
                        {"en": "I have a friend.  +  His father is a doctor.\n"
                               "→ I have a friend {{whose}} father is a doctor.",
                         "ko": "나는 아버지가 의사인 친구가 있다. (His → whose)"},
                        {"en": "a house {{whose}} roof is red",
                         "ko": "지붕이 빨간 집 (= the roof of which is red)"},
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
            "intro": [
                "**언제?**  공통 부분이 명사가 아니라 **시간·장소·이유·방법(부사)**일 때. "
                "즉 「**전치사 + 관계대명사**」를 하나로 줄인 것.",
                "**역할**  「접속사 + **부사**」 → 뒤에 **{{완전한}} 문장**이 온다. (관계대명사는 불완전)",
                "**해석**  ‘~하는 (때·곳·이유·방법)’.",
            ],
            "concepts": [
                {
                    "lead": "관계부사 when / where / why / how",
                    "desc": "시간 **{{when}}**·장소 **{{where}}**·이유 why·방법 how. "
                            "「전치사+which」와 바꿔 쓸 수 있다.",
                    "examples": [
                        {"en": "This is the house.  +  I live in it.\n"
                               "→ This is the house {{where}} I live.",
                         "ko": "여기가 내가 사는 집이다. (in it = in which → where)"},
                        {"en": "I remember the day {{when}} we met.",
                         "ko": "나는 우리가 만난 그 날을 기억한다. (on that day → when)"},
                        {"en": "Tell me the reason {{why}} you were late.",
                         "ko": "네가 늦은 이유를 말해 봐."},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "핵심 판별",
                 "lines": [
                     "관계사 **뒤 문장이 완전** → 관계**부사**(when/where…).",
                     "관계사 **뒤 문장이 불완전**(주어·목적어 결여) → 관계**대명사**(who/which…).",
                 ]},
                {"type": "warn", "label": "함정",
                 "lines": ["**the way** 와 **how** 는 함께 못 쓴다 → 둘 중 하나만."]},
                {"type": "exam", "label": "시험",
                 "lines": ["**관계대명사 vs 관계부사**(뒤 문장 완전성으로 판별) = 최빈출, 전치사+which = 관계부사."]},
            ],
        },
    ],
    "wrapup": {
        "title": "관계사 한눈에 — 격·선행사·뒤 문장",
        "headers": ["관계사", "선행사", "격/역할", "뒤 문장"],
        "rows": [
            ["who", "사람", "{{주격}}", "동사~ (주어 결여)"],
            ["which", "사물·동물", "주격/목적격", "불완전"],
            ["whom", "사람", "{{목적격}}", "S+V~ (목적어 결여)"],
            ["whose", "사람·사물", "{{소유격}}", "명사 + S+V"],
            ["when/where/why", "시간·장소·이유", "관계부사", "{{완전한}} 문장"],
        ],
    },
    "practice": [
        {
            "q": "두 문장을 관계사로 연결하시오.",
            "examples": [
                {"en": "I met a girl {{who}} speaks French. (← She speaks French)",
                 "ko": "나는 프랑스어를 하는 소녀를 만났다."},
                {"en": "This is the town {{where}} I was born. (← I was born in it)",
                 "ko": "여기가 내가 태어난 마을이다."},
            ],
        },
        {
            "q": "괄호에서 알맞은 관계사를 고르시오.",
            "items": [
                "I have a friend ( who / which ) lives in London.   →  {{who}}",
                "This is the house ( which / where ) I live.   →  {{where}}",
                "The girl ( whose / who ) hair is long is my sister.   →  {{whose}}",
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
