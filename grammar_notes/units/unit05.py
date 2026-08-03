# -*- coding: utf-8 -*-
"""UNIT 05 조동사의 이해 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "05",
    "title": "조동사의 이해",
    "subtitle": "Understanding Modal Verbs",
    "intro": [
        "**조동사** = 동사에 **의미를 더함**(능력·허가·의무·추측 등). 뒤에는 항상 **{{동사원형}}**.",
        "조동사는 인칭·수에 따라 변하지 않으며, 두 개를 겹쳐 쓸 수 없다 (will can X).",
        "부정은 조동사 + **{{not}}**, 의문은 **조동사 + 주어 + 동사원형**.",
    ],
    "points": [
        {
            "no": "01",
            "title": "can, may",
            "concepts": [
                {
                    "lead": "can / may",
                    "desc": "**can** = **{{능력}}**(=be able to)·허가·가능. **may** = **{{허가}}**·약한 추측.",
                    "examples": [
                        {"en": "I {{can}} swim.", "ko": "나는 수영할 수 있다. (능력)"},
                        {"en": "{{May}} I come in?", "ko": "들어가도 될까요? (허가)"},
                        {"en": "It {{may}} rain tonight.", "ko": "오늘 밤 비가 올지도 모른다. (추측)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "시제",
                 "lines": ["can 과거 = **could**. 미래 = **will be able to** (will can X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["**can = be able to** 전환, may의 허가/추측 의미 구별."]},
            ],
        },
        {
            "no": "02",
            "title": "must / have to / should, had better",
            "intro": "**의무·충고**를 나타내는 조동사.",
            "concepts": [
                {
                    "lead": "의무·충고",
                    "desc": "**must = have to** = **{{의무}}**(~해야 한다). **should = ought to** = 충고. "
                            "**had better** = ~하는 편이 낫다.",
                    "examples": [
                        {"en": "You {{should}} see a doctor.", "ko": "너는 병원에 가봐야 해. (충고)"},
                        {"en": "You {{had better}} hurry.", "ko": "너는 서두르는 게 좋겠다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "최빈출 함정",
                 "lines": [
                     "**must not** = 금지(~하면 안 된다)  ↔  **don't have to** = 불필요(~할 필요 없다)",
                 ]},
                {"type": "tip", "label": "시제",
                 "lines": ["must의 과거·미래는 **had to / will have to** 로."]},
                {"type": "exam", "label": "시험",
                 "lines": ["**mustn't vs don't have to** 의미 구별 = 최빈출, must=have to 전환."]},
            ],
        },
        {
            "no": "03",
            "title": "must, may/might, can/could, cannot (추측)",
            "intro": "**추측의 확신 강도**를 조동사로 표현한다.",
            "concepts": [
                {
                    "lead": "추측 조동사 (확신의 강도)",
                    "desc": "**must**(~임에 {{틀림없다}}) > may/might(~일지도) > **cannot**(~일 리 {{없다}}).",
                    "examples": [
                        {"en": "He {{must}} be tired.", "ko": "그는 틀림없이 피곤하다. (강한 추측)"},
                        {"en": "She {{may}} be at home.", "ko": "그녀는 집에 있을지도 모른다."},
                        {"en": "It {{can't}} be true.", "ko": "그것은 사실일 리 없다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "compare", "label": "비교",
                 "lines": ["**must be**(강한 긍정 추측)  ↔  **can't be**(강한 부정 추측)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["추측 의미 강도별 조동사 고르기, 부정 추측 **can't**(must not 아님)."]},
            ],
        },
        {
            "no": "04",
            "title": "used to, would",
            "intro": "**과거의 습관·상태**를 나타내는 표현.",
            "concepts": [
                {
                    "lead": "used to / would",
                    "desc": "**used to + V** = 과거의 **{{규칙적 습관·상태}}**(지금은 아님). "
                            "**would + V** = 과거의 반복 습관.",
                    "examples": [
                        {"en": "I {{used to}} play soccer.", "ko": "나는 예전에 축구를 하곤 했다. (지금은 아님)"},
                        {"en": "He {{would}} often visit us.", "ko": "그는 자주 우리를 방문하곤 했다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "최빈출 함정",
                 "lines": [
                     "**used to + V**(과거 습관)  ≠  **be used to + V-ing**(~에 익숙하다)  ≠  "
                     "be used to + V(~하는 데 쓰이다)",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["**used to V / be used to V-ing** 구별 = 빈출, would(과거 습관)."]},
            ],
        },
    ],
    "wrapup": {
        "title": "조동사 의미 정리",
        "headers": ["조동사", "의미", "예"],
        "rows": [
            ["can", "능력·허가", "{{can}} swim"],
            ["may", "허가·추측", "{{may}} rain"],
            ["must", "의무·강한 추측", "{{must}} go / must be"],
            ["should", "충고", "{{should}} rest"],
            ["must not", "금지", "{{금지}}"],
            ["don't have to", "불필요", "{{불필요}}"],
            ["used to", "과거 습관·상태", "{{used to}} play"],
        ],
    },
    "practice": [
        {
            "q": "우리말에 맞게 괄호에서 고르시오.",
            "items": [
                "너는 여기서 담배 피우면 안 된다.  →  You ( must not / don't have to ) smoke.   →  {{must not}}",
                "그는 틀림없이 부자다.  →  He ( must / can't ) be rich.   →  {{must}}",
                "나는 일찍 일어나는 데 익숙하다.  →  I am used to ( get / getting ) up early.   →  {{getting}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "You {{had better}} take an umbrella.", "ko": "너는 우산을 챙기는 게 좋겠다."},
                {"en": "There {{used to}} be a tree here.", "ko": "예전엔 여기 나무가 있었다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "He will can finish it.  →  {{will be able to}}",
                "It cannot be true. She must not be lying.  →  (추측 부정) {{can't}}",
                "I used to getting up late.  →  {{used to get}}",
            ],
        },
    ],
}
