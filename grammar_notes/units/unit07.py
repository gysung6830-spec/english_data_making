# -*- coding: utf-8 -*-
"""UNIT 07 비교 표현 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "07",
    "title": "비교 표현",
    "subtitle": "Comparison",
    "intro": [
        "형용사·부사의 형태를 바꿔 정도를 비교한다 : **{{원급}}**(as~as)·**{{비교급}}**(-er/more)·"
        "**{{최상급}}**(-est/most).",
        "비교급·최상급 규칙 : 짧은 말 -er/-est, 긴 말(3음절↑) **more/most**. "
        "불규칙 good–better–best, bad–worse–worst.",
    ],
    "points": [
        {
            "no": "01",
            "title": "원급·비교급 구문",
            "concepts": [
                {
                    "lead": "원급·비교급 기본",
                    "desc": "원급 「as + **{{원급}}** + as」 = ~만큼 …한. 비교급 「비교급 + **{{than}}**」 = ~보다 …한.",
                    "examples": [
                        {"en": "Tom is as {{tall}} as Bill.", "ko": "Tom은 Bill만큼 키가 크다. (동등)"},
                        {"en": "Tom is {{taller}} than Bill.", "ko": "Tom은 Bill보다 키가 크다. (우등)"},
                        {"en": "This room is twice as {{large}} as that one.", "ko": "이 방은 저 방의 두 배 크다. (배수)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["as ~ as 사이엔 **원급(원형)**, than 앞엔 **비교급**. as taller as (X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["as~as 사이 **원급**, than 앞 **비교급**, 배수 표현(twice as ~ as)."]},
            ],
        },
        {
            "no": "02",
            "title": "원급·비교급 표현",
            "intro": "비교를 활용한 다양한 관용 표현.",
            "concepts": [
                {
                    "lead": "주요 비교 표현",
                    "desc": "비교급 강조 = **{{much/far/even/still/a lot}}** + 비교급 (very X). "
                            "「the 비교급 …, the 비교급 …」 = ~할수록 더 ….",
                    "examples": [
                        {"en": "This is {{much}} bigger than that.", "ko": "이것은 저것보다 훨씬 크다. (강조)"},
                        {"en": "The {{harder}} you study, the {{better}} you get.",
                         "ko": "열심히 공부할수록 더 잘하게 된다."},
                        {"en": "It's getting {{colder and colder}}.", "ko": "점점 더 추워지고 있다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["비교급 강조는 **very가 아니라 much/far/even/a lot**."]},
                {"type": "exam", "label": "시험",
                 "lines": ["**비교급 강조어**(much), **the+비교급, the+비교급**, 비교급 and 비교급."]},
            ],
        },
        {
            "no": "03",
            "title": "최상급 구문",
            "intro": "「the + 최상급 + in/of ~」 = 가장 …한.",
            "concepts": [
                {
                    "lead": "최상급 기본",
                    "desc": "「the + **{{최상급}}** + in(단수 범위)/of(복수 전체)」. "
                            "「one of the + 최상급 + **{{복수명사}}**」 = 가장 ~한 것들 중 하나.",
                    "examples": [
                        {"en": "She is the {{tallest}} in her class.", "ko": "그녀는 반에서 가장 키가 크다."},
                        {"en": "It's one of the {{best}} movies.", "ko": "그것은 최고의 영화들 중 하나다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["**in**(단수 장소·집단) / **of**(복수·전체). one of the 최상급 + **복수명사**."]},
                {"type": "exam", "label": "시험",
                 "lines": ["최상급 **the**, in/of 구별, **one of the 최상급 + 복수명사**."]},
            ],
        },
        {
            "no": "04",
            "title": "최상급 표현",
            "intro": "**원급·비교급으로 최상급 의미**를 나타낼 수 있다.",
            "concepts": [
                {
                    "lead": "최상급 = 원급/비교급 전환",
                    "desc": "「No (other) ~ as 원급 as A」 = 「A ~ 비교급 than any other 단수」 = 「the 최상급」.",
                    "examples": [
                        {"en": "Everest is higher than {{any other}} mountain.",
                         "ko": "에베레스트는 다른 어떤 산보다 높다. (= 가장 높다)"},
                        {"en": "No other student is {{as}} smart {{as}} Tom.",
                         "ko": "어떤 학생도 Tom만큼 똑똑하지 않다. (= Tom이 가장 똑똑)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "전환 공식",
                 "lines": [
                     "the 최상급 = No other 단수 ~ as 원급 as = 비교급 than any other 단수 "
                     "= 비교급 than all the other 복수.",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["**최상급 ↔ 원급/비교급 전환**, any other + 단수명사."]},
            ],
        },
    ],
    "wrapup": {
        "title": "비교 표현 정리",
        "headers": ["구문", "형태", "예"],
        "rows": [
            ["원급", "as {{원급}} as", "as tall as"],
            ["비교급", "비교급 {{than}}", "taller than"],
            ["비교급 강조", "{{much}}/far + 비교급", "much bigger"],
            ["the 비교급~", "the 비교급, the 비교급", "the more, the {{better}}"],
            ["최상급", "the {{최상급}} in/of", "the tallest in"],
            ["최상급 전환", "비교급 than {{any other}} 단수", "than any other"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 것을 고르시오.",
            "items": [
                "She is as ( tall / taller ) as her mom.   →  {{tall}}",
                "This bag is ( very / much ) more expensive than that.   →  {{much}}",
                "He is the tallest ( in / of ) his family.   →  {{in}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "The {{more}} you have, the {{more}} you want.", "ko": "많이 가질수록 더 원한다."},
                {"en": "No mountain is higher than {{any other}}… (= Everest is the highest).",
                 "ko": "에베레스트가 가장 높다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "He is more taller than me.  →  {{taller}}",
                "It is one of the best movie.  →  {{movies}}",
                "This is very bigger than that.  →  {{much}}",
            ],
        },
    ],
}
