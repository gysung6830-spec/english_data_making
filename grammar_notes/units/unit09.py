# -*- coding: utf-8 -*-
"""UNIT 09 접속사와 분사구문 — 특강용 문법 필기 교재 (중 수위 빈칸 + 시험 tip)."""

UNIT = {
    "no": "09",
    "title": "접속사와 분사구문",
    "subtitle": "Conjunctions & Participial Constructions",
    "intro": [
        "**부사절 접속사** = 「접속사 + 주어 + 동사」로 시간·이유·조건·양보를 나타낸다.",
        "**분사구문** = 부사절을 **분사(V-ing/p.p.)** 로 간결하게 줄인 것.",
        "만드는 법 : ① 접속사 삭제 ② (주절과 같은) 주어 삭제 ③ 동사 → **{{V-ing}}**.",
    ],
    "points": [
        {
            "no": "01",
            "title": "시간 접속사",
            "concepts": [
                {
                    "lead": "시간 부사절 접속사",
                    "desc": "when(~할 때)·while(~하는 동안)·before·after·until(~까지)·"
                            "as soon as(~하자마자) + 주어 + 동사.",
                    "examples": [
                        {"en": "I'll call you when I {{arrive}}.", "ko": "도착하면 전화할게."},
                        {"en": "{{As soon as}} he came, we left.", "ko": "그가 오자마자 우리는 떠났다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "최빈출 함정",
                 "lines": [
                     "**시간·조건의 부사절**에서는 미래를 **{{현재}}시제**로 : "
                     "when I {{arrive}} (will arrive X).",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["시간·조건 부사절의 **현재시제(미래 대용)** = 최빈출."]},
            ],
        },
        {
            "no": "02",
            "title": "이유·조건 접속사",
            "intro": "이유·조건·양보를 나타내는 접속사.",
            "concepts": [
                {
                    "lead": "이유·조건·양보",
                    "desc": "이유 **{{because/since/as}}**, 조건 if / **{{unless}}**(= if ~ not), "
                            "양보 although/though(~에도 불구하고).",
                    "examples": [
                        {"en": "I stayed home {{because}} it rained.", "ko": "비가 와서 집에 있었다."},
                        {"en": "{{Unless}} you hurry, you'll be late.", "ko": "서두르지 않으면 늦을 것이다."},
                        {"en": "{{Although}} he is rich, he isn't happy.", "ko": "그는 부자지만 행복하지 않다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "**because**(+ 절) ↔ **because of**(+ 명사). / although(+절) ↔ despite(+명사).",
                     "**unless** 에는 not 을 또 쓰지 않는다 (이미 부정).",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["**because/because of, although/despite**, unless 의미 = 빈출."]},
            ],
        },
        {
            "no": "03",
            "title": "분사구문 _ 동시상황",
            "intro": "두 동작이 동시에 = ‘~하면서’. 분사구문으로 표현.",
            "concepts": [
                {
                    "lead": "동시상황 분사구문",
                    "desc": "부사절 → **{{분사(V-ing)}}**. ‘~하면서/~한 채로’. 수동은 **{{(Being) p.p.}}**.",
                    "examples": [
                        {"en": "{{Smiling}} brightly, she waved at me.", "ko": "환하게 웃으면서 그녀는 손을 흔들었다."},
                        {"en": "{{Listening}} to music, I did my homework.", "ko": "음악을 들으면서 숙제를 했다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "만드는 법",
                 "lines": ["① 접속사 삭제 ② 주어 삭제(주절과 같을 때) ③ 동사 → **V-ing**."]},
                {"type": "exam", "label": "시험",
                 "lines": ["분사구문 ↔ 부사절 전환, 능동 **V-ing** / 수동 **p.p.**"]},
            ],
        },
        {
            "no": "04",
            "title": "분사구문 _ 시간, 이유",
            "intro": "분사구문이 **시간(when/after)·이유(because)** 의미를 나타낸다.",
            "concepts": [
                {
                    "lead": "시간·이유의 분사구문",
                    "desc": "문맥으로 시간·이유를 파악. 완료는 **{{Having p.p.}}**(주절보다 먼저 일어난 일).",
                    "examples": [
                        {"en": "{{Arriving}} home, I found the door open.",
                         "ko": "집에 도착했을 때, 문이 열려 있는 것을 발견했다. (시간)"},
                        {"en": "{{Being}} tired, he went to bed early.",
                         "ko": "피곤했기 때문에, 그는 일찍 잤다. (이유)"},
                        {"en": "{{Having finished}} the work, she left.",
                         "ko": "일을 끝낸 후에 그녀는 떠났다. (완료)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "주절과 **주어가 다르면** 분사 앞에 주어를 남긴다(독립분사구문).",
                     "부정은 분사 **앞에 not** (Not knowing ~).",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["분사구문 의미(시간/이유), **Having p.p.**(완료), 능동/수동 구별."]},
            ],
        },
    ],
    "wrapup": {
        "title": "접속사·분사구문 정리",
        "headers": ["항목", "형태", "예"],
        "rows": [
            ["시간 접속사", "when/while + S+V", "when I {{arrive}}"],
            ["이유 접속사", "{{because}} + S+V", "because it rained"],
            ["조건", "if / {{unless}}", "unless you hurry"],
            ["분사구문(능동)", "{{V-ing}} ~", "Smiling, she ~"],
            ["분사구문(수동)", "(Being) {{p.p.}}", "Written in ~"],
            ["분사구문(완료)", "{{Having}} p.p.", "Having finished ~"],
        ],
    },
    "practice": [
        {
            "q": "괄호에서 알맞은 것을 고르시오.",
            "items": [
                "I'll wait here until he ( comes / will come ).   →  {{comes}}",
                "( Because / Because of ) the rain, we stayed home.   →  {{Because of}}",
                "( Smiling / Smiled ), she opened the door.   →  {{Smiling}}",
            ],
        },
        {
            "q": "부사절을 분사구문으로 바꾸시오.",
            "examples": [
                {"en": "{{Feeling}} tired, I went to bed. (← Because I felt tired)",
                 "ko": "피곤해서 나는 잤다."},
                {"en": "{{Having done}} my homework, I watched TV. (← After I had done)",
                 "ko": "숙제를 끝낸 후 TV를 봤다."},
            ],
        },
        {
            "q": "어법상 틀린 부분을 고치시오.",
            "items": [
                "When I will arrive, I will call you.  →  {{arrive}}",
                "Unless you don't hurry, you'll be late.  →  {{Unless you hurry}}",
                "Knowing not the answer, he kept silent.  →  {{Not knowing}}",
            ],
        },
    ],
}
