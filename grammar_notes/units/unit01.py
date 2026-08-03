# -*- coding: utf-8 -*-
"""UNIT 01 주어의 형태 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "01",
    "title": "주어의 형태",
    "subtitle": "The Forms of the Subject",
    "intro": [
        "**주어가 왜 중요한가?**  영어 문장의 뼈대는 ‘**무엇이(주어) + 어찌하다(동사)**’. "
        "주어를 못 찾으면 문장 해석의 출발점을 잃는다.",
        "**주어의 역할** = 동사가 나타내는 동작·상태의 **{{주체}}**. 우리말 ‘~은/는/이/가’로 해석.",
        "**무엇이 주어가 되나?**  ‘**명사 노릇**’을 하는 말이면 다 된다 → 명사·대명사, "
        "동명사·to부정사, 명사절(that절·의문사절).",
        "**해석·수 일치**  주어 덩어리를 통째로 ‘~은/는’ 붙여 해석하고, **구·절 주어는 {{단수}}** 취급.",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "intro": [
                "**무엇?**  가장 기본이 되는 주어 — 명사(구)와 대명사.",
                "**핵심**  주어는 명사 하나가 아니라 **수식어까지 붙은 ‘명사 덩어리’** 전체다. "
                "동사는 그 덩어리의 **{{핵심 명사}}** 에 수를 맞춘다.",
                "**해석**  ‘(수식어)한 그 (명사)은/는’.",
            ],
            "concepts": [
                {
                    "lead": "명사(구) — 핵심 명사를 찾아라",
                    "desc": "「(관사·형용사) + **핵심 명사** + (수식어구)」 전체가 주어. 동사의 수는 관사·형용사가 아니라 "
                            "**{{핵심 명사}}** 로 결정된다. 물질·추상명사는 관사 없이 주어가 된다.",
                    "examples": [
                        {"en": "The diligent students in my class {{study}} hard.",
                         "ko": "우리 반의 성실한 학생들은 열심히 공부한다. (핵심 명사=students → 복수동사 study)"},
                        {"en": "{{Honesty}} is the best policy.",
                         "ko": "정직이 최선의 방책이다. (추상명사, 관사 없이 주어)"},
                    ],
                },
                {
                    "lead": "대명사 — 주어 자리엔 주격",
                    "desc": "명사를 대신하는 대명사가 주어면 반드시 **{{주격}}**(I·you·he·she·it·we·they). "
                            "목적격(me·him…)은 주어가 될 수 없다.",
                    "examples": [
                        {"en": "{{She}} teaches English.", "ko": "그녀는 영어를 가르친다."},
                        {"en": "I bought a book. {{It}} is interesting.",
                         "ko": "나는 책을 샀다. 그것은 재미있다. (It = a book)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "찾는 법",
                 "lines": ["동사를 먼저 찾고 그 앞에서 ‘**누가/무엇이**’를 물으면 주어. "
                           "수식어구(in my class 등)는 지우고 **핵심 명사**만 남겨 동사 수를 정한다."]},
                {"type": "warn", "label": "함정",
                 "lines": [
                     "목적격 주어 금지 : Me and Tom …(X) → Tom and {{I}} …(O)",
                     "사이에 낀 수식어에 끌리지 말 것 : The box of apples {{is}} heavy. (주어=box)",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": [
                     "주어–동사 **수 일치**(사이에 전치사구·관계절 끼우기) = 빈출.",
                     "주격 vs 목적격(Tom and I/me).",
                 ]},
            ],
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "intro": [
                "**왜?**  ‘달리다(run)’ 같은 **동사는 그대로 주어가 될 수 없다.** 주어 자리엔 명사가 와야 하므로, "
                "동사를 **명사형으로 바꿔** 쓴다.",
                "**두 방법**  **{{동명사(V-ing)}}** 또는 **{{to부정사(to+동사원형)}}**. 둘 다 ‘~하는 것은’.",
                "**핵심**  아무리 길어도 하나의 덩어리 = **{{단수}}** → 동사는 is/takes 처럼 단수형.",
            ],
            "concepts": [
                {
                    "lead": "동명사(V-ing)가 주어",
                    "desc": "‘~하는 것은/~하기는’. **일반적·습관적** 행위를 나타내며 구어에서 자연스럽다.",
                    "examples": [
                        {"en": "{{Reading}} books {{is}} fun.",
                         "ko": "책을 읽는 것은 재미있다. (동명사구 주어 → 단수동사 is)"},
                        {"en": "{{Exercising}} every day is good for health.",
                         "ko": "매일 운동하는 것은 건강에 좋다."},
                    ],
                },
                {
                    "lead": "to부정사가 주어",
                    "desc": "역시 ‘~하는 것은’. **격식·문어체** 느낌. 실제로는 긴 to부정사 주어를 뒤로 보내고 "
                            "**가주어 {{it}}** 을 쓰는 것이 더 자연스럽다. (→ Point 04)",
                    "examples": [
                        {"en": "{{To master}} a foreign language {{requires}} patience.",
                         "ko": "외국어를 익히는 것은 인내를 요구한다."},
                        {"en": "To exercise regularly is important.\n→ {{It}} is important to exercise regularly.",
                         "ko": "규칙적으로 운동하는 것은 중요하다. (긴 주어 → 가주어 it)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "compare", "label": "비교",
                 "lines": ["**동명사**(일반·구어) ↔ **to부정사**(격식·문어). 뜻·단수 취급은 같다."]},
                {"type": "warn", "label": "함정",
                 "lines": ["동사원형은 주어 불가 : {{Run}} …(X) → {{Running / To run}} …(O)"]},
                {"type": "exam", "label": "시험",
                 "lines": ["동명사·to부정사 주어의 **단수 동사**(is/are 고르기), 동사원형 주어 오류."]},
            ],
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "intro": [
                "**왜?**  하나의 단어가 아니라 **문장(S+V) 전체**를 주어로 삼고 싶을 때. "
                "「S+V」가 통째로 **명사 노릇(명사절)** 을 한다.",
                "**두 종류**  단정적 사실은 **{{that절}}**(‘~라는 것은’), 불확실·의문은 **{{의문사절}}**(‘~인지’).",
                "**핵심**  명사절 주어도 **{{단수}}**.",
            ],
            "concepts": [
                {
                    "lead": "that절이 주어 — ‘~라는 것은’",
                    "desc": "「**{{That}}** + 완전한 문장」이 주어. 사실·단정의 내용. 딱딱해서 보통 "
                            "**가주어 it** 으로 옮긴다.",
                    "examples": [
                        {"en": "{{That}} the earth is round {{is}} true.",
                         "ko": "지구가 둥글다는 것은 사실이다."},
                        {"en": "That he is honest is true.\n→ {{It}} is true {{that}} he is honest.",
                         "ko": "그가 정직하다는 것은 사실이다. (가주어 it으로 전환)"},
                    ],
                },
                {
                    "lead": "의문사절이 주어 — ‘~인지’",
                    "desc": "「**{{의문사}} + 주어 + 동사**」. ‘무엇이/누가/왜 ~인지’. 의문사 : "
                            "what·who·when·where·why·how·whether.",
                    "examples": [
                        {"en": "{{What}} he said {{surprised}} us.",
                         "ko": "그가 말한 것이 우리를 놀라게 했다."},
                        {"en": "{{Why}} she left early is a mystery.",
                         "ko": "그녀가 왜 일찍 떠났는지는 미스터리다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "해석",
                 "lines": ["that절 = ‘~라는 것은’, 의문사절 = ‘~인지가’. 절 전체가 주어이므로 "
                           "**절 끝까지 읽고** 그 뒤의 동사를 찾는다."]},
                {"type": "warn", "label": "어순 함정",
                 "lines": ["간접의문문은 **평서문 어순**「의문사 + 주어 + 동사」. do/does 안 씀, 도치 X : "
                           "What he wants …(O) / What does he want …(X)"]},
                {"type": "exam", "label": "시험",
                 "lines": ["**간접의문문 어순**, 명사절 주어 단수 동사, that↔what 구별."]},
            ],
        },
        {
            "no": "04",
            "title": "가주어와 비인칭 주어",
            "intro": [
                "**왜?**  영어는 **길고 무거운 주어를 앞에 두기 싫어한다(머리 무거움 회피).** "
                "그래서 자리만 채우는 형식상의 **it** 을 쓴다.",
                "**두 쓰임**  ① **가주어 it** — 진짜 주어(진주어)를 뒤로 보냄  ② **비인칭 it** — 시간·날씨 등.",
                "**공통**  이 **it 은 ‘그것’으로 해석하지 {{않는다}}.**",
            ],
            "concepts": [
                {
                    "lead": "가주어 it — 진주어를 뒤로",
                    "desc": "주어가 to부정사구·that절처럼 길면 뒤로 보내고(=**{{진주어}}**), 그 자리에 "
                            "**가주어 {{it}}**. 「It + 동사 + 보어 + 진주어」.",
                    "examples": [
                        {"en": "{{It}} is difficult {{to solve}} this problem.",
                         "ko": "이 문제를 푸는 것은 어렵다. (진주어=to solve this problem)"},
                        {"en": "{{It}} is surprising {{that}} he passed.",
                         "ko": "그가 합격한 것은 놀랍다. (진주어=that절)"},
                    ],
                },
                {
                    "lead": "비인칭 주어 it — 시간·날씨 등",
                    "desc": "**{{시간·날씨·요일·거리·명암}}** 을 나타낼 때 형식상 쓰는 it. 가리키는 대상이 없다.",
                    "examples": [
                        {"en": "{{It}} is raining now.", "ko": "지금 비가 온다. (날씨)"},
                        {"en": "{{It}} is 10 km to the station.", "ko": "역까지 10km이다. (거리)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "구별법",
                 "lines": [
                     "뒤에 **진주어(to부정사·that절)가 있으면 → 가주어**.",
                     "뒤에 진주어가 **없으면 → 비인칭**(날씨·시간·거리).",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["진주어↔가주어 **문장 전환**(To solve…is hard ↔ It is hard to solve…), 밑줄 친 it의 쓰임."]},
            ],
        },
    ],
    "wrapup": {
        "title": "주어 자리에 올 수 있는 것 — 한눈에 정리",
        "headers": ["형태", "예", "해석", "수"],
        "rows": [
            ["명사(구)", "The book is new.", "~은/는/이/가", "핵심 명사에 일치"],
            ["대명사(주격)", "{{They}} are kind.", "그들은 ~", "명사에 일치"],
            ["동명사", "{{Reading}} is fun.", "~하는 것은", "{{단수}}"],
            ["to부정사", "{{To read}} is fun.", "~하는 것은", "{{단수}}"],
            ["that절", "{{That}} he came is true.", "~라는 것은", "{{단수}}"],
            ["의문사절", "{{What}} he said matters.", "~인지가", "{{단수}}"],
            ["가주어 it", "{{It}} is fun to read.", "(해석 X)", "{{단수}}"],
            ["비인칭 it", "{{It}} is sunny.", "(해석 X)", "{{단수}}"],
        ],
    },
    "practice": [
        {
            "q": "주어에 밑줄을 긋고, 괄호에서 알맞은 동사를 고르시오.",
            "items": [
                "Reading comic books ( is / are ) my hobby.   →  {{is}}",
                "The box of chocolates ( was / were ) on the table.   →  {{was}}",
                "That she won the prize ( surprise / surprised ) everyone.   →  {{surprised}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "{{It}} is important {{to}} exercise regularly.", "ko": "규칙적으로 운동하는 것은 중요하다."},
                {"en": "{{Where}} he {{lives}} is unknown.", "ko": "그가 어디에 사는지는 알려져 있지 않다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "Run every day is good.  →  {{Running / To run}}",
                "Me and my sister like music.  →  {{My sister and I}}",
                "What does he want is a secret.  →  {{What he wants}}",
            ],
        },
    ],
}
