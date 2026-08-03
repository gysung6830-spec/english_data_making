# -*- coding: utf-8 -*-
"""UNIT 01 주어의 형태 — 특강용 '나만의 문법노트' (중 수위 빈칸 + 시험 출제 tip).

컨셉 : 핵심어·예문에 '중간 수위'로 빈칸을 뚫어 학생이 채운다.
       예문 = '핵심어에 빈칸 뚫린 인쇄 문장 + 한글 뜻' (필기줄 아님).
       각 Point에 '시험' 박스로 어디가·어떻게 출제되는지 정리.

빈칸/마크업 : {{정답}} / {{정답||힌트}} / **강조** / __밑줄__
블록 : point.intro / concept.desc / concept.items / concept.examples[{en(빈칸포함), ko}]
       boxes[].type = tip(초록)·warn(함정)·compare(비교)·exam(시험)
"""

UNIT = {
    "no": "01",
    "title": "주어의 형태",
    "subtitle": "The Forms of the Subject",
    "intro": [
        "**주어** = 문장에서 **{{동사}}** 가 나타내는 동작·상태의 **{{주체}}**. 우리말 ‘~은/는/이/가’.",
        "주어 자리 = 반드시 **{{명사 상당어구}}** → ① {{명사·대명사}}  ② {{동명사·to부정사}}  "
        "③ {{명사절}}(that절·의문사절)   ( 형용사·부사는 주어 {{불가}} )",
        "대원칙 ㉠ 주어–동사는 **{{수}}** 일치   ㉡ 구·절 주어는 아무리 길어도 **{{단수}}** 취급",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "concepts": [
                {
                    "lead": "명사(구)가 주어",
                    "desc": "「(관사·형용사) + **{{핵심 명사}}** + (수식어구)」 덩어리 전체가 주어. "
                            "동사는 **{{핵심 명사}}** 에 일치. 물질·추상명사는 관사 없이 주어 가능.",
                    "examples": [
                        {"en": "The tall boy {{runs}} fast.", "ko": "그 키 큰 소년은 빨리 달린다."},
                        {"en": "The diligent students in my class {{study}} hard.",
                         "ko": "우리 반의 성실한 학생들은 열심히 공부한다. (주어=students)"},
                        {"en": "{{Honesty}} is the best policy.", "ko": "정직이 최선의 방책이다."},
                    ],
                },
                {
                    "lead": "대명사가 주어",
                    "desc": "주어 자리 = 반드시 **{{주격}}** ( I·you·he·she·it·we·they )",
                    "examples": [
                        {"en": "{{She}} teaches English.", "ko": "그녀는 영어를 가르친다."},
                        {"en": "{{They}} are my classmates.", "ko": "그들은 나의 반 친구들이다."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "tip", "label": "수 일치",
                    "lines": [
                        "3인칭 단수 주어 → 현재형 동사에 **{{-(e)s}}**.",
                        "My brother {{likes}} soccer. / My brothers like soccer.",
                    ],
                },
                {
                    "type": "warn", "label": "함정",
                    "lines": [
                        "목적격 주어 금지 : Me and Tom …(X) → Tom and {{I}} …(O)",
                        "수식어에 끌리지 말 것 : The box of apples {{is}} heavy. (주어=box)",
                    ],
                },
                {
                    "type": "exam", "label": "시험",
                    "lines": [
                        "**주어–동사 수 일치** : 주어와 동사 사이에 **{{전치사구·관계절}}** 을 끼워 넣고 "
                        "동사 형태(is/are, has/have)를 고르게 함. → 반드시 **핵심 명사**를 찾을 것.",
                        "**주격 vs 목적격** : and로 연결된 주어(Tom and I/me) 어법성 판단.",
                    ],
                },
            ],
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "intro": "동사는 그대로 주어가 될 수 없다 → **{{동명사(V-ing)}}** / **{{to부정사}}** 로 바꿈. 둘 다 **{{단수}}**.",
            "concepts": [
                {
                    "lead": "동명사(V-ing)가 주어",
                    "desc": "‘**{{~하는 것은}}**’으로 해석. 일반적·습관적 행위 (구어에서 자연스러움).",
                    "examples": [
                        {"en": "{{Reading}} books {{is}} fun.", "ko": "책을 읽는 것은 재미있다."},
                        {"en": "{{Exercising}} every day is good for health.", "ko": "매일 운동하는 것은 건강에 좋다."},
                    ],
                },
                {
                    "lead": "to부정사(to+동사원형)가 주어",
                    "desc": "역시 ‘~하는 것은’. 격식·문어체. 긴 주어는 보통 **{{가주어 it}}** 으로. (→ Point 04)",
                    "examples": [
                        {"en": "{{To master}} a foreign language {{requires}} patience.",
                         "ko": "외국어를 익히는 것은 인내가 필요하다."},
                        {"en": "{{It}} is important {{to exercise}} regularly.",
                         "ko": "규칙적으로 운동하는 것은 중요하다. (가주어 it)"},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "warn", "label": "함정",
                    "lines": ["동사원형은 주어 불가 : {{Run}} …(X) → {{Running / To run}} …(O)"],
                },
                {
                    "type": "exam", "label": "시험",
                    "lines": [
                        "동명사·to부정사 주어의 동사는 **{{단수}}**(is/was) → 수 일치 문제로 출제.",
                        "**동사원형을 주어로 쓴 오류**(Run…is good) 찾아 고치기.",
                    ],
                },
            ],
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "intro": "「S+V」 문장이 통째로 **{{명사절}}** → 주어. 명사절 주어도 **{{단수}}**.",
            "concepts": [
                {
                    "lead": "that절이 주어",
                    "desc": "「**{{That}}** + 완전한 문장」 = ‘~라는 것은’(사실·단정). 보통 **{{가주어 it}}** 으로 옮김.",
                    "examples": [
                        {"en": "{{That}} the earth is round {{is}} true.", "ko": "지구가 둥글다는 것은 사실이다."},
                        {"en": "{{It}} is true {{that}} he is honest.",
                         "ko": "그가 정직하다는 것은 사실이다. (가주어 it)"},
                    ],
                },
                {
                    "lead": "의문사절(간접의문문)이 주어",
                    "desc": "「**{{의문사}} + 주어 + 동사**」 = ‘~인지’. 의문사 : what·who·when·where·why·how·whether",
                    "examples": [
                        {"en": "{{What}} he said {{surprised}} us.", "ko": "그가 말한 것이 우리를 놀라게 했다."},
                        {"en": "{{Why}} she left early is a mystery.", "ko": "그녀가 왜 일찍 떠났는지는 미스터리다."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "warn", "label": "어순 함정",
                    "lines": [
                        "간접의문문 = **{{평서문}}** 어순 「의문사 + 주어 + 동사」 ( do/does 안 씀, 도치 X )",
                        "What he wants …(O) / What **does he want** …(X)",
                    ],
                },
                {
                    "type": "compare", "label": "비교",
                    "lines": ["that절 = {{사실·단정}} ‘~라는 것’  /  의문사절 = {{불확실·의문}} ‘~인지’"],
                },
                {
                    "type": "exam", "label": "시험",
                    "lines": [
                        "**간접의문문 어순**(의문사+S+V) 어법성 판단 → **최빈출**.",
                        "명사절 주어의 **단수 동사**, **that ↔ what** 구별.",
                    ],
                },
            ],
        },
        {
            "no": "04",
            "title": "가주어와 비인칭 주어",
            "intro": "영어는 길고 무거운 주어를 앞에 두기 싫어함 → 형식상의 **{{it}}** 사용.",
            "concepts": [
                {
                    "lead": "가주어 it (진주어를 뒤로)",
                    "desc": "긴 주어(to부정사·that절)를 뒤로(=**{{진주어}}**), 자리엔 **{{가주어 it}}**. it 해석 **{{안 함}}**.",
                    "examples": [
                        {"en": "{{It}} is difficult {{to solve}} this problem.", "ko": "이 문제를 푸는 것은 어렵다."},
                        {"en": "{{It}} is surprising {{that}} he passed.", "ko": "그가 합격한 것은 놀랍다."},
                    ],
                },
                {
                    "lead": "비인칭 주어 it",
                    "desc": "**{{시간·날씨·요일·거리·명암}}** 등을 나타내는 형식상의 it. 해석 **{{안 함}}**.",
                    "examples": [
                        {"en": "{{It}} is raining now.", "ko": "지금 비가 온다. (날씨)"},
                        {"en": "{{It}} is 10 km to the station.", "ko": "역까지 10km이다. (거리)"},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "compare", "label": "구별",
                    "lines": [
                        "가주어 it → 뒤에 **{{진주어 있음}}** (to부정사·that절)",
                        "비인칭 it → 뒤에 **{{진주어 없음}}** (날씨·시간·거리)",
                    ],
                },
                {
                    "type": "exam", "label": "시험",
                    "lines": [
                        "**진주어 ↔ 가주어 문장 전환**(To solve … is hard ↔ It is hard to solve …) 영작·배열.",
                        "가주어 it 과 비인칭 it **구별**, 밑줄 친 it의 쓰임 고르기.",
                    ],
                },
            ],
        },
    ],
    "wrapup": {
        "title": "주어 자리에 올 수 있는 것 — 한눈에 정리",
        "headers": ["형태", "예", "해석", "수"],
        "rows": [
            ["명사(구)", "The book is new.", "~은/는/이/가", "명사에 일치"],
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
            "q": "괄호에서 알맞은 동사를 고르시오. (수 일치)",
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
                {"en": "{{It}} is true {{that}} he is honest.", "ko": "그가 정직하다는 것은 사실이다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오. (빈출)",
            "items": [
                "Run every day is good.  →  {{Running / To run}}",
                "Me and my sister like music.  →  {{My sister and I}}",
                "What does he want is a secret.  →  {{What he wants}}",
            ],
        },
    ],
}
