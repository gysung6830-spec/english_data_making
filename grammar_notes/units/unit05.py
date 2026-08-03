# -*- coding: utf-8 -*-
"""UNIT 05 조동사의 이해 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "05",
    "title": "조동사의 이해",
    "subtitle": "Understanding Modal Verbs",
    "intro": [
        "**조동사가 왜 필요한가?**  동사만으로는 ‘사실’만 전달한다. 여기에 "
        "‘~할 수 있다·해야 한다·일지도 모른다’처럼 **능력·의무·추측 같은 화자의 태도**를 얹는 것이 조동사다.",
        "**역할**  본동사에 의미를 더한다. 뒤에는 항상 **{{동사원형}}**.",
        "**규칙**  인칭·수에 따라 변하지 않고(He can → He cans X), **두 개를 겹쳐 쓸 수 없다**(will can X).",
    ],
    "points": [
        {
            "no": "01",
            "title": "can, may",
            "intro": [
                "**무엇?**  **can** = 능력·허가·가능 / **may** = 허가·약한 추측.",
                "**해석**  can ‘~할 수 있다/해도 된다’ / may ‘~해도 된다/~일지도 모른다’.",
            ],
            "concepts": [
                {
                    "lead": "can / may 의 의미",
                    "desc": "**can** = **{{능력}}**(=be able to)·허가·가능. **may** = **{{허가}}**·약한 추측.",
                    "examples": [
                        {"en": "I {{can}} swim.", "ko": "나는 수영할 수 있다. (능력)"},
                        {"en": "{{May}} I come in?", "ko": "들어가도 될까요? (허가)"},
                        {"en": "It {{may}} rain tonight.", "ko": "오늘 밤 비가 올지도 모른다. (추측)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "read", "label": "한 단어 두 얼굴",
                 "lines": ["같은 can도 문맥에 따라 ‘**능력**(할 수 있다)’ / ‘**허가**(해도 된다)’로 갈린다 → 해석은 문맥."]},
                {"type": "tip", "label": "시제",
                 "lines": ["can 과거 = **could**. 미래 = **will be able to** (will can X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["can = be able to 전환, may의 허가/추측 구별."]},
            ],
        },
        {
            "no": "02",
            "title": "must / have to / should, had better",
            "intro": [
                "**무엇?**  의무·충고를 나타내는 조동사.",
                "**핵심**  must = have to(의무). 그러나 **부정은 뜻이 갈린다** — mustn't(금지) ≠ don't have to(불필요).",
                "**해석**  must/have to ‘~해야 한다’ / should ‘~하는 게 좋다’ / had better ‘~하는 편이 낫다’.",
            ],
            "concepts": [
                {
                    "lead": "의무·충고",
                    "desc": "**must = have to** = **{{의무}}**. **should = ought to** = 충고. "
                            "**had better** = (안 하면 안 좋으니) ~하는 편이 낫다.",
                    "examples": [
                        {"en": "You {{should}} see a doctor.", "ko": "너는 병원에 가보는 게 좋겠다. (충고)"},
                        {"en": "You {{had better}} hurry.", "ko": "너는 서두르는 게 좋겠다. (강한 충고)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "최빈출 함정",
                 "lines": ["**must not** = 금지(하면 안 된다)  ↔  **don't have to** = 불필요(할 필요 없다)"]},
                {"type": "tip", "label": "시제",
                 "lines": ["must의 과거·미래는 **had to / will have to** 로 대신."]},
                {"type": "exam", "label": "시험",
                 "lines": ["mustn't vs don't have to 의미 구별 = 최빈출, must = have to 전환."]},
            ],
        },
        {
            "no": "03",
            "title": "must, may/might, can/could, cannot (추측)",
            "intro": [
                "**왜?**  같은 ‘추측’이라도 **얼마나 확신하는가**를 조동사로 나타낸다.",
                "**강도**  **must**(~임에 틀림없다) > may/might(~일지도) > **cannot**(~일 리 없다).",
                "**해석**  확신의 세기에 맞춰 해석.",
            ],
            "concepts": [
                {
                    "lead": "추측 조동사 (확신의 강도)",
                    "desc": "강한 긍정 확신 **must**(틀림없다), 약한 가능성 may/might(일지도), "
                            "강한 부정 확신 **cannot/can't**(일 리 없다).",
                    "examples": [
                        {"en": "He {{must}} be tired.", "ko": "그는 틀림없이 피곤하다. (강한 추측)"},
                        {"en": "She {{may}} be at home.", "ko": "그녀는 집에 있을지도 모른다. (약한 추측)"},
                        {"en": "It {{can't}} be true.", "ko": "그것은 사실일 리 없다. (강한 부정 추측)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "compare", "label": "비교",
                 "lines": ["**must be**(강한 긍정 추측)  ↔  **can't be**(강한 부정 추측). "
                           "‘~아님에 틀림없다’는 must not 이 아니라 **can't**."]},
                {"type": "exam", "label": "시험",
                 "lines": ["추측 강도별 조동사 고르기, 부정 추측 **can't**(must not 아님)."]},
            ],
        },
        {
            "no": "04",
            "title": "used to, would",
            "intro": [
                "**무엇?**  **과거의 습관·상태**를 나타내는 표현 (지금은 그렇지 않음을 함축).",
                "**차이**  used to = 규칙적 습관 **+ 상태** / would = 반복 습관(상태 X).",
                "**해석**  ‘(예전에) ~하곤 했다 / ~였다(지금은 아님)’.",
            ],
            "concepts": [
                {
                    "lead": "used to / would",
                    "desc": "**used to + V** = 과거의 **{{규칙적 습관·상태}}**. **would + V** = 과거의 반복 습관 "
                            "(상태에는 쓰지 않음).",
                    "examples": [
                        {"en": "I {{used to}} play soccer.", "ko": "나는 예전에 축구를 하곤 했다. (지금은 아님)"},
                        {"en": "There {{used to}} be a tree here.", "ko": "예전엔 여기 나무가 있었다. (상태 → would 불가)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "최빈출 함정",
                 "lines": ["**used to + V**(과거 습관) ≠ **be used to + V-ing**(~에 익숙하다) "
                           "≠ be used to + V(~하는 데 쓰이다)"]},
                {"type": "exam", "label": "시험",
                 "lines": ["used to V / be used to V-ing 구별 = 빈출, would(과거 습관)."]},
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
                {"en": "It {{can't}} be true.", "ko": "그것은 사실일 리 없다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "He will can finish it.  →  {{will be able to}}",
                "You must not go now. (‘갈 필요 없다’의 뜻이면)  →  {{don't have to}}",
                "I used to getting up late.  →  {{used to get}}",
            ],
        },
    ],
}
