# -*- coding: utf-8 -*-
"""UNIT 01 주어의 형태 — 특강용 문법 필기 교재 콘텐츠.

빈칸 표기 규칙:
  {{정답}}            → 학생용은 빈칸(밑줄), 교사용은 강조된 정답
  {{정답||힌트}}       → 학생용 빈칸 아래 작은 힌트 표시(교사용은 정답만)
  **강조**            → 굵게(빈칸 아님)
  __밑줄__            → 밑줄(빈칸 아님, 구문 표시용)
"""

UNIT = {
    "no": "01",
    "title": "주어의 형태",
    "subtitle": "The Forms of the Subject",
    "intro": [
        "문장에서 **동사의 동작·상태의 주체**가 되는 말을 주어라고 하며, "
        "우리말로 ‘~은/는/이/가’로 해석한다.",
        "주어 자리에는 반드시 **명사 상당어구**(명사 역할을 하는 말)가 와야 한다. "
        "즉 {{명사·대명사}}, {{동명사·to부정사}}, {{that절·의문사절}} 등이 주어가 될 수 있다.",
        "주어와 동사는 **{{수}}**를 일치시켜야 하며, 구·절 주어는 대부분 **{{단수}}** 취급한다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "concepts": [
                {"lead": "명사(구)가 주어", "items": [
                    "「(관사·형용사 등 수식어) + **명사**」 덩어리 전체가 주어가 된다.",
                    "The tall {{boy}} runs fast. → 주어: {{The tall boy}}",
                    "{{Water}} boils at 100°C. (물질명사·추상명사도 주어 가능)",
                ]},
                {"lead": "대명사가 주어", "items": [
                    "주어 자리에는 **{{주격}}** 대명사(I, you, he, she, it, we, they)를 쓴다.",
                    "{{She}} teaches English. / {{They}} are my friends.",
                ]},
            ],
            "tip": {
                "label": "수 일치",
                "lines": [
                    "주어가 **3인칭 단수**이면 현재형 동사에 **{{-(e)s}}** 를 붙인다.",
                    "My brother {{likes}} soccer.  ( brother = 단수 → likes )",
                    "My brothers {{like}} soccer.  ( brothers = 복수 → like )",
                ],
            },
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "concepts": [
                {"lead": "동명사(V-ing)가 주어", "items": [
                    "‘**~하는 것은/~하기는**’으로 해석하며 **{{단수}}** 취급한다.",
                    "{{Reading}} books {{is}} fun. (동명사구 주어 → 단수 동사 is)",
                    "{{Swimming}} is good for your health.",
                ]},
                {"lead": "to부정사(to+동사원형)가 주어", "items": [
                    "역시 ‘~하는 것은’으로 해석하고 **{{단수}}** 취급하며, 다소 **격식체**이다.",
                    "{{To learn}} a language {{takes}} time.",
                ]},
            ],
            "tip": {
                "label": "핵심",
                "lines": [
                    "동명사·to부정사 주어는 아무리 길어도 **하나의 덩어리 = 단수** → 동사는 "
                    "{{is / takes / makes}} 처럼 **단수형**.",
                    "실제 문장에서는 긴 to부정사 주어를 뒤로 보내고 **가주어 {{it}}** 을 자주 쓴다. (Point 04)",
                ],
            },
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "concepts": [
                {"lead": "that절이 주어", "items": [
                    "「**That + 주어 + 동사**」가 ‘**~라는 것은**’의 뜻으로 주어가 된다. **{{단수}}** 취급.",
                    "{{That}} he is honest {{is}} true.",
                    "→ 실제로는 가주어를 써서  {{It}} is true {{that}} he is honest.  로 더 자주 쓴다.",
                ]},
                {"lead": "의문사절(간접의문문)이 주어", "items": [
                    "「**의문사 + 주어 + 동사**」 어순으로 쓰고 ‘~인지/~하는 것이’로 해석. **{{단수}}** 취급.",
                    "{{What}} he said {{surprised}} us. (그가 말한 것이 우리를 놀라게 했다)",
                    "{{Why}} she left early {{is}} a mystery.",
                ]},
            ],
            "tip": {
                "label": "어순 주의",
                "lines": [
                    "간접의문문(명사절)의 어순은 의문문이 아니라 **평서문 어순**:",
                    "「의문사 + {{주어}} + {{동사}}」  (O)   /   「의문사 + 동사 + 주어」  (X)",
                    "Where he lives is unknown. (O)   ↔   Where does he live? (직접의문문)",
                ],
            },
        },
        {
            "no": "04",
            "title": "가주어와 비인칭 주어",
            "concepts": [
                {"lead": "가주어 it (진주어를 뒤로)", "items": [
                    "주어가 **to부정사구·that절**처럼 길면 뒤로 보내고, 그 자리에 **가주어 {{it}}** 을 쓴다.",
                    "{{It}} is important {{to exercise}} regularly.  ( 진주어 = to exercise regularly )",
                    "{{It}} is clear {{that}} she is right.  ( 진주어 = that절 )",
                    "이때 **it 은 해석하지 않는다.**",
                ]},
                {"lead": "비인칭 주어 it", "items": [
                    "**시간·날씨·요일·날짜·거리·명암** 등을 나타낼 때 형식상 주어로 **it** 을 쓴다.",
                    "{{It}} is raining now. (날씨)   /   {{It}} is three o’clock. (시간)",
                    "{{It}} is Monday today. (요일)   /   {{It}} is 10 km to the station. (거리)",
                    "이 **it 도 ‘그것’으로 해석하지 않는다.**",
                ]},
            ],
            "tip": {
                "label": "비교",
                "lines": [
                    "**가주어 it** 은 뒤에 **진주어(to부정사·that절)가 있다.**",
                    "**비인칭 it** 은 뒤에 **진주어가 없다.** (날씨·시간 등)",
                ],
            },
        },
    ],
    "wrapup": {
        "title": "주어 자리에 올 수 있는 것 — 한눈에 정리",
        "headers": ["형태", "예", "해석", "수"],
        "rows": [
            ["명사(구)", "The book is new.", "~은/는/이/가", "명사에 일치"],
            ["대명사(주격)", "{{They}} are kind.", "그들은 ~", "명사에 일치"],
            ["동명사 V-ing", "{{Reading}} is fun.", "~하는 것은", "{{단수}}"],
            ["to부정사", "{{To read}} is fun.", "~하는 것은", "{{단수}}"],
            ["that절", "{{That}} he came is true.", "~라는 것은", "{{단수}}"],
            ["의문사절", "{{What}} he said matters.", "~인 것이/~인지가", "{{단수}}"],
            ["가주어 it", "{{It}} is fun to read.", "(해석 안 함)", "{{단수}}"],
            ["비인칭 it", "{{It}} is sunny.", "(해석 안 함)", "{{단수}}"],
        ],
    },
    "practice": [
        {
            "q": "다음 문장에서 주어에 밑줄을 긋고, 알맞은 동사를 고르시오.",
            "items": [
                "Reading comic books ( is / are ) my hobby.   → {{is}}",
                "That she won the prize ( surprise / surprised ) everyone.   → {{surprised}}",
                "To keep a diary ( help / helps ) you remember things.   → {{helps}}",
            ],
        },
        {
            "q": "우리말에 맞게 빈칸을 채우시오.",
            "items": [
                "규칙적으로 운동하는 것은 중요하다.  →  {{It}} is important {{to}} exercise regularly.",
                "그가 어디에 사는지는 알려져 있지 않다.  →  {{Where}} he {{lives}} is unknown.",
                "밖은 비가 오고 있다.  →  {{It}} is raining outside.",
            ],
        },
    ],
}
