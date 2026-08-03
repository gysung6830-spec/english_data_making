# -*- coding: utf-8 -*-
"""UNIT 09 접속사와 분사구문 — 특강용 문법 필기 교재 (개념·역할·해석 상세본)."""

UNIT = {
    "no": "09",
    "title": "접속사와 분사구문",
    "subtitle": "Conjunctions & Participial Constructions",
    "intro": [
        "**접속사가 왜 필요한가?**  두 문장·생각을 **시간·이유·조건·양보** 같은 논리로 이어 하나로 만들기 위해.",
        "**분사구문이 왜 필요한가?**  「접속사 + 주어 + 동사」의 부사절을 **분사 하나로 줄여** 문장을 간결하게 하려고.",
        "**분사구문 만드는 법**  ① 접속사 삭제  ② (주절과 같은) 주어 삭제  ③ 동사 → **{{V-ing}}**.",
    ],
    "points": [
        {
            "no": "01",
            "title": "시간 접속사",
            "intro": [
                "**역할**  시간 관계를 나타내는 부사절을 이끈다 「접속사 + S + V」.",
                "**핵심**  **시간·조건의 부사절**에서는 미래를 **{{현재}}시제**로 쓴다.",
                "**해석**  ‘~할 때/동안/~까지/~하자마자’.",
            ],
            "concepts": [
                {
                    "lead": "시간 부사절 접속사",
                    "desc": "when(~할 때)·while(~하는 동안)·before·after·until(~까지)·"
                            "as soon as(~하자마자) + S + V.",
                    "examples": [
                        {"en": "I'll call you when I {{arrive}}.", "ko": "도착하면 전화할게. (미래 대신 현재)"},
                        {"en": "{{As soon as}} he came, we left.", "ko": "그가 오자마자 우리는 떠났다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "최빈출 함정",
                 "lines": ["시간·조건 부사절에서 미래를 **현재**로 : when I {{arrive}} (will arrive X)."]},
                {"type": "exam", "label": "시험",
                 "lines": ["시간·조건 부사절의 **현재시제(미래 대용)** = 최빈출."]},
            ],
        },
        {
            "no": "02",
            "title": "이유·조건 접속사",
            "intro": [
                "**역할**  이유·조건·양보를 나타내는 부사절을 이끈다.",
                "**해석**  이유 ‘~때문에’ / 조건 ‘~라면’ / 양보 ‘~에도 불구하고’.",
            ],
            "concepts": [
                {
                    "lead": "이유·조건·양보",
                    "desc": "이유 **{{because/since/as}}**, 조건 if / **{{unless}}**(= if ~ not), "
                            "양보 although/though.",
                    "examples": [
                        {"en": "I stayed home {{because}} it rained.", "ko": "비가 와서 집에 있었다. (이유)"},
                        {"en": "{{Unless}} you hurry, you'll be late.", "ko": "서두르지 않으면 늦을 것이다. (조건)"},
                        {"en": "{{Although}} he is rich, he isn't happy.", "ko": "그는 부자지만 행복하지 않다. (양보)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "**because**(+ 절) ↔ **because of**(+ 명사). although(+절) ↔ despite(+명사).",
                     "**unless** 는 이미 부정 → not 을 또 쓰지 않는다.",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["because/because of, although/despite, unless 의미 = 빈출."]},
            ],
        },
        {
            "no": "03",
            "title": "분사구문 _ 동시상황",
            "intro": [
                "**왜?**  두 동작이 동시에 일어남을 ‘**~하면서**’로 간결히 표현하려고.",
                "**만드는 법**  접속사·주어를 지우고 동사를 **{{V-ing}}** 로. 수동은 (Being) p.p.",
                "**해석**  ‘~하면서 / ~한 채로’.",
            ],
            "concepts": [
                {
                    "lead": "동시상황 분사구문 (부사절 → 분사구문)",
                    "desc": "「접속사 + S + V」를 지우고 동사를 **V-ing** 로 바꿔 앞에 둔다. 주절과 동시 동작.",
                    "examples": [
                        {"en": "As she smiled, she waved at me.\n→ {{Smiling}}, she waved at me.",
                         "ko": "웃으면서 그녀는 나에게 손을 흔들었다."},
                        {"en": "{{Listening}} to music, I did my homework.",
                         "ko": "음악을 들으면서 나는 숙제를 했다."},
                    ],
                },
            ],
            "boxes": [
                {"type": "tip", "label": "만드는 법",
                 "lines": ["① 접속사 삭제 ② 주어 삭제(주절과 같을 때) ③ 동사 → **V-ing**."]},
                {"type": "read", "label": "해석",
                 "lines": ["분사구문은 접속사가 없어 의미가 문맥에 열려 있다 → 동시상황이면 ‘**~하면서**’."]},
                {"type": "exam", "label": "시험",
                 "lines": ["분사구문 ↔ 부사절 전환, 능동 V-ing / 수동 p.p."]},
            ],
        },
        {
            "no": "04",
            "title": "분사구문 _ 시간, 이유",
            "intro": [
                "**무엇?**  분사구문이 **시간(when/after)·이유(because)** 의 뜻을 나타낸다.",
                "**핵심**  주절보다 **먼저** 일어난 일은 **{{Having p.p.}}**(완료 분사구문).",
                "**해석**  문맥에 따라 ‘~할 때 / ~하기 때문에’.",
            ],
            "concepts": [
                {
                    "lead": "시간·이유의 분사구문",
                    "desc": "문맥으로 시간·이유를 파악한다. 시점 차이가 있으면 **Having p.p.** 로 ‘먼저 있었던 일’을 표시.",
                    "examples": [
                        {"en": "{{Arriving}} home, I found the door open.",
                         "ko": "집에 도착했을 때 문이 열려 있었다. (시간, = When I arrived)"},
                        {"en": "{{Being}} tired, he went to bed early.",
                         "ko": "피곤했기 때문에 그는 일찍 잤다. (이유, = Because he was tired)"},
                        {"en": "{{Having finished}} the work, she left.",
                         "ko": "일을 끝낸 후에 그녀는 떠났다. (완료)"},
                    ],
                },
            ],
            "boxes": [
                {"type": "warn", "label": "함정",
                 "lines": [
                     "주절과 **주어가 다르면** 분사 앞에 주어를 남긴다(독립분사구문).",
                     "부정은 분사 **앞에 not** : {{Not knowing}} the answer, …",
                 ]},
                {"type": "exam", "label": "시험",
                 "lines": ["분사구문 의미(시간/이유), Having p.p.(완료), 능동/수동 구별."]},
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
                {"en": "Because I felt tired, I went to bed.\n→ {{Feeling}} tired, I went to bed.",
                 "ko": "피곤해서 나는 잤다."},
                {"en": "After I had done my homework, I watched TV.\n→ {{Having done}} my homework, I watched TV.",
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
