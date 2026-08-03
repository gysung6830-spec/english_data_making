# -*- coding: utf-8 -*-
"""UNIT 10 가정법 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "10",
    "title": "가정법",
    "subtitle": "The Subjunctive Mood",
    "intro": [
        "**가정법** = **사실의 반대**를 상상·가정. (직설법 = 사실을 그대로 말함)",
        "핵심 : 시제를 **한 칸 과거로** 당겨 ‘사실과 다름’을 표시한다.",
        "**가정법 과거**(현재 반대) / **가정법 과거완료**(과거 반대).",
    ],
    "points": [
        {
            "no": "01",
            "title": "가정법 과거",
            "intro": "**현재 사실의 반대**를 가정 (‘~라면 …할 텐데’).",
            "concepts": [
                {
                    "lead": "가정법 과거",
                    "desc": "「If + S + **{{과거형}}**(be는 **{{were}}**), S + **{{would/could/might}}** + 동사원형」.",
                    "examples": [
                        {"en": "If I {{were}} rich, I {{would}} buy a car.",
                         "ko": "내가 부자라면 차를 살 텐데. (실제론 부자가 아님)"},
                        {"en": "If I {{knew}} her number, I would call her.",
                         "ko": "그녀의 번호를 안다면 전화할 텐데. (모름)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": ["가정법 과거의 be동사는 인칭과 무관하게 **{{were}}** (was 지양)."]},
                {"type": "compare", "label": "직설법 전환",
                 "lines": ["If I were rich … = As I am **not** rich, I **don't** buy … (현재 사실)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["If절 **과거동사·were**, 주절 **would + 동사원형**, 직설법 전환."]},
            ],
        },
        {
            "no": "02",
            "title": "가정법 과거완료",
            "intro": "**과거 사실의 반대**를 가정 (‘~했더라면 …했을 텐데’).",
            "concepts": [
                {
                    "lead": "가정법 과거완료",
                    "desc": "「If + S + **{{had p.p.}}**, S + would/could/might + **{{have p.p.}}**」.",
                    "examples": [
                        {"en": "If I {{had studied}}, I {{would have passed}}.",
                         "ko": "공부했더라면 합격했을 텐데. (실제론 공부 안 함)"},
                        {"en": "If he {{had left}} earlier, he wouldn't have missed the train.",
                         "ko": "더 일찍 떠났더라면 기차를 놓치지 않았을 텐데."},
                    ],
                },
            ],
            "boxes": [
                {"type": "compare", "label": "비교",
                 "lines": [
                     "가정법 과거(**현재** 반대) ↔ 가정법 과거완료(**과거** 반대).",
                     "혼합가정법 : If + had p.p. , S + would + **동사원형**(과거 원인 → 현재 결과).",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["If절 **had p.p.**, 주절 **would have p.p.**, 혼합가정법 = 빈출."]},
            ],
        },
    ],
    "wrapup": {
        "title": "가정법 정리",
        "headers": ["종류", "If절", "주절", "의미"],
        "rows": [
            ["가정법 과거", "If + S + {{과거형/were}}", "would + 동사원형", "현재 반대"],
            ["가정법 과거완료", "If + S + {{had p.p.}}", "would {{have p.p.}}", "과거 반대"],
            ["혼합가정법", "If + S + had p.p.", "would + {{동사원형}}", "과거→현재"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 것을 고르시오.",
            "items": [
                "If I ( were / was ) you, I would accept it.   →  {{were}}",
                "If she had known, she ( would call / would have called ).   →  {{would have called}}",
                "If I had money, I ( would / would have ) buy it.   →  {{would}}",
            ],
        },
        {
            "q": "빈칸을 채워 문장을 완성하시오.",
            "examples": [
                {"en": "If it {{were}} not raining, we {{would}} go out.", "ko": "비가 오지 않는다면 나갈 텐데."},
                {"en": "If you {{had told}} me, I {{would have helped}} you.",
                 "ko": "네가 말했더라면 도와줬을 텐데."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "If I was a bird, I would fly.  →  {{were}}",
                "If he studied harder, he would have passed. (과거 반대)  →  {{had studied}}",
                "If it rained tomorrow, I will stay home.  →  {{would stay}}",
            ],
        },
    ],
}
