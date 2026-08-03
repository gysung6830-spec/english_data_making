# -*- coding: utf-8 -*-
"""UNIT 04 시제와 수동태 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "04",
    "title": "시제와 수동태",
    "subtitle": "Tense & the Passive Voice",
    "intro": [
        "**완료시제가 왜 필요한가?**  과거시제는 ‘그때 있었던 일’로 **딱 끊긴다.** "
        "하지만 ‘과거에 시작해 **지금까지 이어지거나 영향을 주는**’ 일은 과거형으로 못 나타낸다 → 완료시제.",
        "**수동태가 왜 필요한가?**  행위자보다 **당하는 대상**에 초점을 두거나, 행위자를 모를·밝힐 필요 없을 때. "
        "The window {{was broken}}. (누가 깼는지보다 ‘깨졌다’는 사실)",
        "**형태**  완료 = 「have/had + p.p.」, 수동 = 「be + p.p.」. 둘의 공통 재료가 **{{p.p.}}(과거분사)** 다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "현재완료",
            "intro": [
                "**무엇/왜?**  「have/has + p.p.」. 과거의 일을 **현재와 연결**해 말한다 "
                "(과거시제는 현재와 단절).",
                "**4용법**  {{경험}}·{{계속}}·완료·결과.",
                "**해석**  경험 ‘~한 적 있다’ / 계속 ‘~해 왔다’ / 완료 ‘막 ~했다’ / 결과 ‘~해 버렸다’.",
            ],
            "concepts": [
                {
                    "lead": "현재완료의 4용법",
                    "desc": "**경험**(ever·never·before), **계속**(for·since), **완료**(just·already·yet), "
                            "**결과**(gone 등). 함께 오는 부사로 용법을 구별한다.",
                    "examples": [
                        {"en": "I have {{been}} to Paris.", "ko": "나는 파리에 가본 적 있다. (경험)"},
                        {"en": "She has lived here {{for}} 5 years.", "ko": "그녀는 여기 5년째 살고 있다. (계속)"},
                        {"en": "He has {{just}} finished it.", "ko": "그는 방금 그것을 끝냈다. (완료)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "현재완료는 **명백한 과거표현**과 못 쓴다 : ago·yesterday·last~·의문사 when.",
                     "I have seen him yesterday (X) → {{saw}}.",
                 ]},
                {"type": "compare", "label": "비교",
                 "lines": ["have **been** to (~에 가본 적, 경험)  ↔  have **gone** to (~로 가버림, 결과)"]},
                {"type": "exam", "label": "시험",
                 "lines": ["현재완료 vs 과거시제(ago/yesterday 결합 가부), for/since, been/gone to = 빈출."]},
            ],
        },
        {
            "no": "02",
            "title": "과거완료",
            "intro": [
                "**왜?**  과거의 두 사건 중 **더 먼저 일어난 일**을 구별해 표시하려고 (과거형 두 개면 순서가 모호).",
                "**역할**  ‘과거보다 더 과거’ = **대과거**. 형태 「had + p.p.」.",
                "**해석**  ‘(그 전에 이미) ~했었다’.",
            ],
            "concepts": [
                {
                    "lead": "과거완료 = 과거의 기준 시점보다 앞선 일",
                    "desc": "과거 어느 시점(기준)을 정하고, 그보다 **먼저** 일어난 일을 **{{had p.p.}}** 로 표시한다.",
                    "examples": [
                        {"en": "The train had {{left}} when I arrived.",
                         "ko": "내가 도착했을 때 기차는 이미 떠나 있었다. (떠남 < 도착)"},
                        {"en": "I lost the watch that I had {{bought}}.",
                         "ko": "나는 (전에) 샀던 시계를 잃어버렸다. (삼 < 잃어버림)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "기준 잡기",
                 "lines": ["문장 속 **과거 동사**를 기준으로 잡고, 그보다 먼저면 had p.p., 나중이면 그냥 과거."]},
                {"type": "exam", "label": "시험",
                 "lines": ["두 과거 사건의 **선후 관계** → 먼저 일어난 일에 had p.p. 고르기."]},
            ],
        },
        {
            "no": "03",
            "title": "수동태의 개념",
            "intro": [
                "**왜?**  ‘~이 …되다/당하다’처럼 **대상에 초점**을 두거나 행위자가 불분명할 때.",
                "**전환 3단계**  ① 능동의 목적어 → 주어  ② 동사 → **{{be + p.p.}}**  ③ 주어 → **by + 목적격**.",
                "**해석**  ‘~되다/~받다/~당하다’.",
            ],
            "concepts": [
                {
                    "lead": "능동태 → 수동태 만들기",
                    "desc": "목적어를 주어로 올리고, 동사를 시제에 맞춰 **be + p.p.** 로, 원래 주어는 **by + 목적격**으로.",
                    "examples": [
                        {"en": "Tom broke the window.\n→ The window {{was broken}} by Tom.",
                         "ko": "그 창문은 Tom에 의해 깨졌다."},
                        {"en": "English {{is spoken}} in many countries.",
                         "ko": "영어는 많은 나라에서 쓰인다. (행위자 불분명 → by 생략)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["목적어가 없는 **자동사**(appear·happen·occur)는 수동태 **불가**."]},
                {"type": "exam", "label": "시험",
                 "lines": ["능동↔수동 전환, by 행위자, 자동사 수동 오류 찾기."]},
            ],
        },
        {
            "no": "04",
            "title": "수동태의 시제 표현",
            "intro": [
                "**왜?**  수동태도 언제 일어난 일인지 나타내야 한다 → **be동사를 시제에 맞춰** 바꾼다.",
                "**핵심**  바뀌는 것은 **be동사뿐**, **{{p.p.}}** 는 그대로.",
                "**해석**  시제 + ‘~되다’.",
            ],
            "concepts": [
                {
                    "lead": "시제별 수동태",
                    "desc": "현재 is/are · 과거 was/were · 미래 **{{will be}}** · 완료 **{{have been}}** · "
                            "진행 is being · 조동사 **조동사 + be** + p.p.",
                    "examples": [
                        {"en": "The bridge {{was built}} in 1990.", "ko": "그 다리는 1990년에 지어졌다. (과거)"},
                        {"en": "The work {{will be finished}} soon.", "ko": "그 일은 곧 끝날 것이다. (미래)"},
                        {"en": "It {{can be seen}} from here.", "ko": "그것은 여기서 보일 수 있다. (조동사)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["조동사 수동 = **조동사 + be + p.p.** (조동사 + is p.p. X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["시제별 수동태 형태(will be/have been p.p.), 조동사 + be + p.p."]},
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
            "q": "수동태로 바꿔 빈칸을 완성하시오.",
            "examples": [
                {"en": "Many people love this song.\n→ This song {{is loved}} by many people.",
                 "ko": "이 노래는 많은 사람에게 사랑받는다."},
                {"en": "They will clean the room.\n→ The room {{will be cleaned}}.",
                 "ko": "그 방은 청소될 것이다."},
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
