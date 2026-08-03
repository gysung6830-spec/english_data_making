# -*- coding: utf-8 -*-
"""UNIT 04 시제와 수동태 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "04",
    "title": "시제와 수동태",
    "subtitle": "Tense & the Passive Voice",
    "intro": [
        "**완료시제** = 「have/had + **{{p.p.}}**」, 한 시점의 일이 다른 시점까지 이어짐.",
        "**수동태** = 「be + **{{p.p.}}**」 = ‘~되다/당하다’. 목적어가 주어로 올라감.",
        "시제는 **동사(be동사)의 형태**로 나타낸다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "현재완료",
            "intro": "「have/has + p.p.」 과거의 일이 **현재까지** 영향 (경험·계속·완료·결과).",
            "concepts": [
                {
                    "lead": "현재완료의 4용법",
                    "desc": "**{{경험}}**(ever·never), **{{계속}}**(for·since), **완료**(just·already·yet), 결과.",
                    "examples": [
                        {"en": "I have {{been}} to Paris.", "ko": "나는 파리에 가본 적 있다. (경험)"},
                        {"en": "She has lived here {{for}} 5 years.", "ko": "그녀는 여기 5년째 산다. (계속)"},
                        {"en": "He has {{just}} finished it.", "ko": "그는 방금 그것을 끝냈다. (완료)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "현재완료는 **명백한 과거표현**과 못 씀 : ago·yesterday·last~·의문사 when.",
                     "I have seen him yesterday (X) → {{saw}}.",
                 ]},
                {"type": "compare", "label": "비교",
                 "lines": ["have **been** to (~에 가본 적, 경험)  ↔  have **gone** to (~로 가버림, 결과)"]},
                {"type": "exam", "label": "시험",
                 "lines": [
                     "**현재완료 vs 과거시제** (ago/yesterday와 결합 가부) = 빈출.",
                     "for/since 구별, have been/gone to.",
                 ]},
            ],
        },
        {
            "no": "02",
            "title": "과거완료",
            "intro": "「had + p.p.」 과거 어느 시점보다 **더 이전(대과거)**.",
            "concepts": [
                {
                    "lead": "과거완료 = 과거보다 더 과거",
                    "desc": "과거 두 사건 중 **먼저 일어난 일**을 **{{had p.p.}}** 로 표시.",
                    "examples": [
                        {"en": "The train had {{left}} when I arrived.",
                         "ko": "내가 도착했을 때 기차는 이미 떠나 있었다."},
                        {"en": "I lost the watch that I had {{bought}}.",
                         "ko": "나는 (전에) 샀던 시계를 잃어버렸다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "exam", "label": "시험",
                 "lines": ["두 과거 사건의 **선후 관계** → 먼저 일어난 일에 had p.p. 고르기."]},
            ],
        },
        {
            "no": "03",
            "title": "수동태의 개념",
            "intro": "「be + p.p. (+ by 행위자)」 = ‘~되다’. 능동의 **목적어 → 수동의 주어**.",
            "concepts": [
                {
                    "lead": "능동태 ↔ 수동태 전환",
                    "desc": "① 목적어를 주어로  ② 동사를 **{{be + p.p.}}** 로  ③ 주어를 **{{by + 목적격}}** 으로.",
                    "examples": [
                        {"en": "The window {{was broken}} by Tom.",
                         "ko": "그 창문은 Tom에 의해 깨졌다. (← Tom broke it)"},
                        {"en": "English {{is spoken}} in many countries.",
                         "ko": "영어는 많은 나라에서 쓰인다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["목적어 없는 **자동사**(appear·happen·occur)는 수동태 **불가**."]},
                {"type": "exam", "label": "시험",
                 "lines": ["능동↔수동 전환, by 행위자, **자동사 수동** 오류 찾기."]},
            ],
        },
        {
            "no": "04",
            "title": "수동태의 시제 표현",
            "intro": "**be동사를 시제에 맞춰** 수동태를 만든다.",
            "concepts": [
                {
                    "lead": "시제별 수동태",
                    "desc": "현재 is/are·과거 was/were·미래 **{{will be}}**·완료 **{{have been}}**·"
                            "진행 is being + p.p.·조동사 **{{조동사 be}}** + p.p.",
                    "examples": [
                        {"en": "The work {{will be finished}} soon.", "ko": "그 일은 곧 끝날 것이다. (미래)"},
                        {"en": "It {{can be seen}} from here.", "ko": "그것은 여기서 보일 수 있다. (조동사)"},
                        {"en": "The bridge {{was built}} in 1990.", "ko": "그 다리는 1990년에 지어졌다. (과거)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["조동사 수동은 **조동사 + be + p.p.** (조동사 + is p.p. X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["시제별 수동태 형태(will be/have been p.p.), **조동사+be+p.p.**"]},
            ],
        },
    ],
    "wrapup": {
        "title": "완료시제·수동태 정리",
        "headers": ["항목", "형태", "예"],
        "rows": [
            ["현재완료", "have/has {{p.p.}}", "have finished"],
            ["과거완료", "{{had}} p.p.", "had left"],
            ["수동태(현재)", "is/are {{p.p.}}", "is made"],
            ["수동태(과거)", "was/were p.p.", "{{was made}}"],
            ["수동태(미래)", "{{will be}} p.p.", "will be done"],
            ["수동태(조동사)", "조동사 {{be}} p.p.", "can be seen"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 것을 고르시오.",
            "items": [
                "I ( have lived / lived ) in Seoul since 2015.   →  {{have lived}}",
                "He ( has finished / finished ) his homework an hour ago.   →  {{finished}}",
                "The letter ( wrote / was written ) by her.   →  {{was written}}",
            ],
        },
        {
            "q": "빈칸을 채워 수동태로 완성하시오.",
            "examples": [
                {"en": "This song {{is loved}} by many people.", "ko": "이 노래는 많은 사람에게 사랑받는다."},
                {"en": "The room {{will be cleaned}} tomorrow.", "ko": "그 방은 내일 청소될 것이다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "I have met him yesterday.  →  {{met}}",
                "The problem can solved easily.  →  {{can be solved}}",
                "The accident was happened last night.  →  {{happened}}",
            ],
        },
    ],
}
