# -*- coding: utf-8 -*-
"""UNIT 01 주어의 형태 — 특강용 '나만의 문법노트'(직접 필기형) · 간결본.

설명은 짧은 핵심 어구·화살표식으로. 예문은 한글 뜻+영작 필기줄.

빈칸/마크업 : {{정답}} / {{정답||힌트}} / **강조** / __밑줄__
블록 : point.intro / concept.desc / concept.items / concept.examples[{ko,en}] / concept.space
       boxes[].type = tip(초록)·warn(함정)·compare(비교)
"""

UNIT = {
    "no": "01",
    "title": "주어의 형태",
    "subtitle": "The Forms of the Subject",
    "intro": [
        "**주어** = 동작·상태의 주체 (‘~은/는/이/가’). 위치 : 문장 **{{맨 앞||동사 앞}}**.",
        "주어 자리 = **{{명사 상당어구}}** → ① {{명사·대명사}}  ② {{동명사·to부정사}}  ③ {{명사절}} "
        "( 형용사·부사 {{불가}} )",
        "대원칙 ㉠ 주어–동사 **{{수 일치}}**   ㉡ 구·절 주어 = **{{단수}}**",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "concepts": [
                {
                    "lead": "명사(구)가 주어",
                    "desc": "「수식어 + **{{핵심 명사}}**」 덩어리 전체. 동사는 **핵심 명사**에 일치.",
                    "examples": [
                        {"ko": "그 키 큰 소년은 빨리 달린다.", "en": "The tall boy runs fast."},
                        {"ko": "우리 반의 성실한 학생들은 열심히 공부한다.",
                         "en": "The diligent students in my class study hard."},
                    ],
                },
                {
                    "lead": "대명사가 주어",
                    "desc": "주어 자리 = **{{주격}}** ( I·you·he·she·it·we·they )",
                    "examples": [
                        {"ko": "그녀는 영어를 가르친다.", "en": "She teaches English."},
                        {"ko": "그들은 나의 반 친구들이다.", "en": "They are my classmates."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "warn", "label": "함정",
                    "lines": [
                        "목적격 주어 금지 : Me and Tom …(X) → Tom and {{I}} …(O)",
                        "수식어에 끌리지 말 것 : The box of apples {{is}} heavy. ( 주어=box )",
                    ],
                },
            ],
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "intro": "동사 → 주어 불가. **{{동명사(V-ing)}}** / **{{to부정사}}** 로 바꿔야 함. 둘 다 **{{단수}}**.",
            "concepts": [
                {
                    "lead": "동명사(V-ing)가 주어",
                    "desc": "‘~하는 것은’. 일반·습관 (구어에서 흔함)",
                    "examples": [
                        {"ko": "책을 읽는 것은 재미있다.", "en": "Reading books is fun."},
                        {"ko": "매일 운동하는 것은 건강에 좋다.", "en": "Exercising every day is good for health."},
                    ],
                },
                {
                    "lead": "to부정사(to+동사원형)가 주어",
                    "desc": "‘~하는 것은’. 격식·문어. 긴 주어는 보통 **가주어 {{it}}** 으로 (→ Point 04)",
                    "examples": [
                        {"ko": "외국어를 익히는 것은 인내가 필요하다.",
                         "en": "To master a foreign language requires patience."},
                        {"ko": "규칙적으로 운동하는 것은 중요하다. (가주어 it)",
                         "en": "It is important to exercise regularly."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "warn", "label": "함정",
                    "lines": ["동사원형 주어 불가 : {{Run}} …(X) → {{Running / To run}} …(O)"],
                },
            ],
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "intro": "「S+V」 문장이 통째로 **{{명사절}}** → 주어 가능. **{{단수}}**.",
            "concepts": [
                {
                    "lead": "that절이 주어",
                    "desc": "「**{{That}}** + 완전한 문장」 = ‘~라는 것은’ (사실·단정). 보통 **가주어 it** 으로.",
                    "examples": [
                        {"ko": "지구가 둥글다는 것은 사실이다.", "en": "That the earth is round is true."},
                        {"ko": "그가 정직하다는 것은 사실이다. (가주어 it)", "en": "It is true that he is honest."},
                    ],
                },
                {
                    "lead": "의문사절이 주어",
                    "desc": "「**{{의문사}} + {{주어}} + {{동사}}**」 = ‘~인지’ (what·who·when·where·why·how·whether)",
                    "examples": [
                        {"ko": "그가 말한 것이 우리를 놀라게 했다.", "en": "What he said surprised us."},
                        {"ko": "그녀가 왜 일찍 떠났는지는 미스터리다.", "en": "Why she left early is a mystery."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "warn", "label": "어순",
                    "lines": [
                        "평서문 어순 : 「의문사 + {{주어}} + {{동사}}」  ( do/does 안 씀, 도치 X )",
                        "What he wants …(O) / What does he want …(X)",
                    ],
                },
            ],
        },
        {
            "no": "04",
            "title": "가주어와 비인칭 주어",
            "intro": "긴 주어를 앞에 두기 싫어함 → 형식상의 **it** 사용.",
            "concepts": [
                {
                    "lead": "가주어 it",
                    "desc": "긴 주어(to부정사·that절)를 뒤로(=**{{진주어}}**), 자리엔 **it**. it 해석 **{{안 함}}**.",
                    "examples": [
                        {"ko": "이 문제를 푸는 것은 어렵다.", "en": "It is difficult to solve this problem."},
                        {"ko": "그가 합격한 것은 놀랍다.", "en": "It is surprising that he passed."},
                    ],
                },
                {
                    "lead": "비인칭 주어 it",
                    "desc": "**{{시간·날씨·요일·거리·명암}}**. 해석 **{{안 함}}**.",
                    "examples": [
                        {"ko": "지금 비가 온다.", "en": "It is raining now."},
                        {"ko": "역까지 10km이다.", "en": "It is 10 km to the station."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "compare", "label": "구별",
                    "lines": [
                        "가주어 it → 뒤에 **{{진주어 있음}}**",
                        "비인칭 it → 뒤에 **{{진주어 없음}}**",
                    ],
                },
            ],
        },
    ],
    "wrapup": {
        "title": "주어 자리 정리",
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
            "q": "괄호에서 알맞은 동사를 고르시오.",
            "items": [
                "Reading comic books ( is / are ) my hobby.   →  {{is}}",
                "The box of chocolates ( was / were ) on the table.   →  {{was}}",
                "That she won the prize ( surprise / surprised ) everyone.   →  {{surprised}}",
            ],
        },
        {
            "q": "우리말에 맞게 영작하시오.",
            "items": [],
            "examples": [
                {"ko": "규칙적으로 운동하는 것은 중요하다.", "en": "It is important to exercise regularly."},
                {"ko": "그가 어디에 사는지는 알려져 있지 않다.", "en": "Where he lives is unknown."},
                {"ko": "그가 정직하다는 것은 사실이다.", "en": "It is true that he is honest."},
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
