# -*- coding: utf-8 -*-
"""UNIT 01 주어의 형태 — 특강용 문법 필기 교재 콘텐츠 (상세본).

빈칸 표기 규칙:
  {{정답}}            → 학생용은 빈칸(밑줄), 교사용은 강조된 정답
  {{정답||힌트}}       → 학생용 빈칸 아래 작은 힌트 표시(교사용은 정답만)
  **강조**            → 굵게(빈칸 아님)
  __밑줄__            → 밑줄(빈칸 아님, 구문 표시용)

블록 종류:
  point.intro        → 포인트 도입 한 줄(개념 큰 그림)
  concept.desc       → 개념을 풀어 쓴 설명 문장
  boxes[].type       → tip(초록)·warn(함정)·compare(비교)
"""

UNIT = {
    "no": "01",
    "title": "주어의 형태",
    "subtitle": "The Forms of the Subject",
    "intro": [
        "**주어(Subject)** 란 문장에서 **동사가 나타내는 동작·상태의 주체**가 되는 말로, "
        "우리말 ‘**~은/는/이/가**’에 해당한다. 보통 문장 **맨 앞**, 동사 앞에 온다.",
        "주어 자리에는 반드시 **{{명사 상당어구||명사 역할}}** 가 와야 한다. "
        "즉 ① {{명사·대명사}}  ② {{동명사·to부정사}}  ③ {{that절·의문사절}}(명사절) 이 주어가 될 수 있다. "
        "(형용사·부사는 주어가 **될 수 없다.**)",
        "주어 찾는 법 : 먼저 **동사**를 찾고, 그 앞에서 ‘**누가 / 무엇이**’ 그 동작을 하는지 물으면 그것이 주어다.",
        "두 가지 대원칙 —  ㉠ 주어와 동사는 **{{수}}** 를 일치시킨다(수 일치).  "
        "㉡ 구·절로 된 주어는 아무리 길어도 **{{단수}}** 취급한다.",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "intro": "가장 기본이 되는 주어. 주어 자리에는 명사 하나만이 아니라 "
                     "**수식어가 붙은 명사 덩어리(명사구) 전체**가 온다.",
            "concepts": [
                {
                    "lead": "명사(구)가 주어",
                    "desc": "명사는 사람·사물·개념의 이름이다. 실제 문장에서는 「(관사·형용사 등) + "
                            "**핵심 명사** + (수식어구)」 전체가 하나의 주어 덩어리를 이룬다.",
                    "items": [
                        "The tall {{boy}} runs fast.  →  주어 = {{The tall boy}} (그 키 큰 소년은)",
                        "The diligent students in my class always {{study||동사}} hard.",
                        "  └ 이 덩어리의 **핵심 명사(주어)** 는 {{students||복수}} → 동사도 복수형 study.",
                        "{{Water||물질명사}} boils at 100°C. / {{Honesty||추상명사}} is the best policy.",
                        "  └ 물질·추상명사는 **관사 없이** 그대로 주어가 될 수 있다.",
                    ],
                },
                {
                    "lead": "대명사가 주어",
                    "desc": "앞에 나온 명사를 대신하거나 사람을 가리킬 때 쓰며, 주어 자리에는 반드시 "
                            "**주격**을 쓴다.",
                    "items": [
                        "주격 대명사 : {{I}} / {{you}} / {{he}} / {{she}} / {{it}} / {{we}} / {{they}}",
                        "{{She}} teaches English. / {{They}} are my classmates.",
                        "I bought a book. {{It}} is very interesting.  (It = a book)",
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "tip", "label": "수 일치",
                    "lines": [
                        "주어가 **3인칭 단수**이면 현재형 동사에 **{{-(e)s}}** 를 붙인다.",
                        "My brother {{likes}} soccer. ( brother=단수 )  /  My brothers {{like}} soccer. ( 복수 )",
                    ],
                },
                {
                    "type": "warn", "label": "함정",
                    "lines": [
                        "① 주어 자리에 **목적격**을 쓰면 안 된다. → {{Me}} and Tom went there. (X)  →  "
                        "Tom and {{I}} went there. (O)",
                        "② 주어와 동사 사이에 낀 **수식어구(전치사구·관계절)에 끌려** 수 일치를 틀리지 말 것. "
                        "동사는 항상 **핵심 명사**에 맞춘다.",
                        "The box of apples {{is}} heavy. ( 주어=box, 단수 )   ← are (X)",
                        "The students who study hard {{succeed}}. ( 주어=students, 복수 )",
                    ],
                },
            ],
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "intro": "동사(run, read …)는 그대로 주어가 **될 수 없다.** 명사형인 "
                     "**동명사(V-ing)** 또는 **to부정사(to+동사원형)** 로 바꿔야 주어가 된다.",
            "concepts": [
                {
                    "lead": "동명사(V-ing)가 주어",
                    "desc": "‘**~하는 것은 / ~하기는**’으로 해석한다. 일반적·습관적인 행위를 나타내며 "
                            "구어에서 특히 자연스럽다. 하나의 덩어리이므로 **단수** 취급한다.",
                    "items": [
                        "{{Reading}} books {{is||단수동사}} fun.  (책을 읽는 것은 재미있다)",
                        "{{Exercising}} every day {{keeps}} you healthy.",
                        "Reading English newspapers every morning {{is}} a good habit.",
                        "  └ 목적어·수식어가 길게 붙어도 주어의 핵심은 동명사 → 동사는 **단수 {{is}}**.",
                    ],
                },
                {
                    "lead": "to부정사(to+동사원형)가 주어",
                    "desc": "역시 ‘~하는 것은’으로 해석하고 **단수** 취급한다. 동명사보다 **격식·문어체**이며 "
                            "특정·구체적 행위의 느낌이 있다.",
                    "items": [
                        "{{To master}} a foreign language {{requires||단수}} patience.",
                        "{{To keep}} a diary {{helps}} you remember things.",
                        "실제로는 긴 to부정사 주어를 뒤로 보내고 **가주어 {{it}}** 을 쓰는 것이 더 자연스럽다. (Point 04)",
                        "  To exercise regularly is important.  →  {{It}} is important **to exercise** regularly.",
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "compare", "label": "비교",
                    "lines": [
                        "**동명사 주어** : 일반적·습관적, 구어에서 흔함.   /   "
                        "**to부정사 주어** : 격식·문어, 특정 행위.",
                        "둘 다 뜻은 ‘~하는 것은’이고 **{{단수}}** 취급이라는 점은 같다. "
                        "실사용에서는 to부정사 주어를 **가주어 it** 으로 옮겨 쓰는 경우가 많다.",
                    ],
                },
                {
                    "type": "warn", "label": "함정",
                    "lines": [
                        "**동사원형**은 주어가 될 수 없다.",
                        "{{Run}} every day is good for health. (X)  →  "
                        "{{Running}} / {{To run}} every day is good for health. (O)",
                    ],
                },
            ],
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "intro": "「주어+동사」를 갖춘 **문장 하나가 통째로 명사 역할(명사절)** 을 하며 주어가 될 수 있다. "
                     "명사절 주어도 **단수** 취급한다.",
            "concepts": [
                {
                    "lead": "that절이 주어",
                    "desc": "「**That + 완전한 문장**」이 ‘**~라는 것은 / ~라는 사실은**’의 뜻으로 주어가 된다. "
                            "사실·단정의 내용을 담는다.",
                    "items": [
                        "{{That}} the earth is round {{is||단수}} true.  (지구가 둥글다는 것은 사실이다)",
                        "{{That}} he passed the exam surprised everyone.",
                        "→ that절 주어는 딱딱하므로 보통 **가주어 it** 으로 옮긴다 :",
                        "  {{It}} is true {{that}} the earth is round.  ( 더 자연스러움 )",
                    ],
                },
                {
                    "lead": "의문사절(간접의문문)이 주어",
                    "desc": "「**의문사 + 주어 + 동사**」가 ‘**무엇이/누가/~인지**’의 뜻으로 주어가 된다. "
                            "불확실하거나 물음을 담은 내용에 쓴다.  의문사 : what·who·when·where·why·how·whether(if)",
                    "items": [
                        "{{What}} he said {{surprised||단수}} us.  (그가 말한 것이 우리를 놀라게 했다)",
                        "{{Why}} she left early {{is}} a mystery.",
                        "{{Whether}} he will come (or not) {{matters}} to us.  (그가 올지 안 올지가 중요하다)",
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "warn", "label": "어순 함정",
                    "lines": [
                        "간접의문문(명사절)은 **의문문 어순이 아니라 평서문 어순**이다.",
                        "「의문사 + {{주어}} + {{동사}}」 (O)   /   「의문사 + 동사 + 주어」 (X)",
                        "**do/does/did** 를 쓰지 않고, 조동사 **도치도 하지 않는다.**",
                        "{{What}} he wants is unclear. (O)   ↔   What **does he want** is unclear. (X)",
                    ],
                },
                {
                    "type": "compare", "label": "비교",
                    "lines": [
                        "**that절** = 이미 **사실·단정**인 내용 ‘~라는 것’.",
                        "**의문사절** = **불확실·의문**인 내용 ‘~인지’.  둘 다 동사는 **단수**.",
                    ],
                },
            ],
        },
        {
            "no": "04",
            "title": "가주어와 비인칭 주어",
            "intro": "영어는 **길고 무거운 주어를 앞에 두는 것을 싫어한다(head-heavy 회피).** "
                     "그래서 형식상의 **it** 을 주어 자리에 세우는 두 가지 쓰임이 있다.",
            "concepts": [
                {
                    "lead": "가주어 it (진짜 주어를 뒤로 보냄)",
                    "desc": "주어가 **to부정사구·that절·의문사절**처럼 길면 뒤로 보내고(=진주어), 그 빈자리에 "
                            "형식상의 **가주어 it** 을 놓는다. 「**It + 동사 + 보어 + 진주어**」 구조.",
                    "items": [
                        "{{It}} is difficult **to solve** this problem.  ( 진주어 = {{to solve this problem}} )",
                        "{{It}} is surprising **that** he passed the exam.  ( 진주어 = {{that절}} )",
                        "{{It}} is unclear **what** he means.  ( 진주어 = 의문사절 )",
                        "가주어 **it 은 해석하지 않고**, 진주어를 ‘~하는 것은/~라는 것은’으로 해석한다.",
                    ],
                },
                {
                    "lead": "비인칭 주어 it",
                    "desc": "**시간·날짜·요일·계절·날씨·거리·명암·막연한 상황**을 나타낼 때 형식상 주어로 쓰는 it. "
                            "가리키는 대상이 없어 **해석하지 않는다.**",
                    "items": [
                        "{{It}} is raining now. (날씨)   /   {{It}} is three o’clock. (시간)",
                        "{{It}} is Monday today. (요일)   /   {{It}} is 10 km to the station. (거리)",
                        "{{It}} is getting dark. (명암)   /   {{It}} is spring. (계절)",
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "compare", "label": "핵심 구별",
                    "lines": [
                        "**가주어 it** → 문장 **뒤에 진주어(to부정사·that절·의문사절)가 있다.**",
                        "**비인칭 it** → 뒤에 **진주어가 없다.** (날씨·시간·거리 등)",
                        "It is important **to be honest**. → {{가주어}}  ┃  It is cold today. → {{비인칭}}",
                    ],
                },
            ],
        },
    ],
    "wrapup": {
        "title": "주어 자리에 올 수 있는 것 — 한눈에 정리",
        "headers": ["형태", "예", "해석", "수"],
        "rows": [
            ["명사(구)", "The book is new.", "~은/는/이/가", "핵심 명사에 일치"],
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
            "q": "다음 문장에서 **주어**에 밑줄을 긋고, 괄호 안에서 알맞은 동사를 고르시오.",
            "items": [
                "Reading comic books ( is / are ) my hobby.   →  {{is}}  ( 동명사 주어=단수 )",
                "The box of chocolates ( was / were ) on the table.   →  {{was}}  ( 주어=box )",
                "That she won the prize ( surprise / surprised ) everyone.   →  {{surprised}}",
                "To keep a diary ( help / helps ) you remember things.   →  {{helps}}",
            ],
        },
        {
            "q": "우리말에 맞게 빈칸을 채우시오.",
            "items": [
                "규칙적으로 운동하는 것은 중요하다.  →  {{It}} is important {{to}} exercise regularly.",
                "그가 어디에 사는지는 알려져 있지 않다.  →  {{Where}} he {{lives}} is unknown.",
                "그가 정직하다는 것은 사실이다.  →  {{It}} is true {{that}} he is honest.",
                "밖은 비가 오고 있다.  →  {{It}} is raining outside.",
            ],
        },
        {
            "q": "어법상 **틀린** 부분을 찾아 바르게 고치시오.",
            "items": [
                "Run every day is good for your health.  →  {{Running / To run}}",
                "Me and my sister like music.  →  {{My sister and I}}",
                "What does he want is a secret.  →  {{What he wants}}  ( 간접의문문 어순 )",
            ],
        },
    ],
}
