# -*- coding: utf-8 -*-
"""UNIT 01 주어의 형태 — 특강용 '나만의 문법노트'(직접 필기형) 콘텐츠.

컨셉 : 인쇄물은 개념 뼈대 + 빈칸 + 필기줄만 제공한다.
       학생은 강의를 들으며 핵심어(빈칸)와 예문(필기줄)을 직접 손으로 채워 노트를 완성한다.

빈칸/마크업:
  {{정답}} / {{정답||힌트}}   → 학생용 빈칸(밑줄) / 교사용 정답
  **강조**  __밑줄__
콘텐츠 블록:
  point.intro          → 포인트 도입 한 줄
  concept.desc         → 개념 풀이(핵심어는 빈칸)
  concept.items        → 규칙 요약(빈칸)
  concept.examples[]   → {ko, en} : 학생용은 한글 뜻 + 빈 밑줄, 교사용은 밑줄 위 영작 정답
  concept.space        → 자유 필기용 빈 줄 개수
  boxes[].type         → tip(초록)·warn(함정)·compare(비교)
"""

UNIT = {
    "no": "01",
    "title": "주어의 형태",
    "subtitle": "The Forms of the Subject",
    "intro": [
        "**주어(Subject)** = 문장에서 **동사가 나타내는 동작·상태의 주체**. "
        "우리말 ‘**~은/는/이/가**’로 해석하며, 보통 문장 **{{맨 앞||위치}}**(동사 앞)에 온다.",
        "주어 자리에는 반드시 **{{명사 상당어구||명사 역할}}** 가 온다 → "
        "① {{명사·대명사}}  ② {{동명사·to부정사}}  ③ {{명사절||that절·의문사절}}  "
        "( {{형용사·부사||불가}} 는 주어가 될 수 없다. )",
        "주어 찾는 법 : 먼저 **{{동사}}** 를 찾고, 그 앞에서 ‘**누가/무엇이**’를 물으면 그것이 주어다.",
        "대원칙 ㉠ 주어–동사 **{{수 일치}}**    ㉡ 구·절 주어는 아무리 길어도 **{{단수}}** 취급.",
    ],
    "points": [
        {
            "no": "01",
            "title": "명사와 대명사",
            "intro": "주어 자리에는 명사 하나가 아니라 **{{수식어가 붙은 명사 덩어리(명사구)}}** 전체가 온다.",
            "concepts": [
                {
                    "lead": "명사(구)가 주어",
                    "desc": "명사는 사람·사물·개념의 이름. 문장에서는 「(관사·형용사) + **{{핵심 명사||head}}** "
                            "+ (수식어구)」 전체가 주어가 되고, 동사는 **{{핵심 명사}}** 에 수를 맞춘다.",
                    "items": [
                        "물질·추상명사는 **{{관사 없이}}** 그대로 주어가 될 수 있다. (Water, Honesty …)",
                    ],
                    "examples": [
                        {"ko": "그 키 큰 소년은 빨리 달린다.", "en": "The tall boy runs fast."},
                        {"ko": "우리 반의 성실한 학생들은 항상 열심히 공부한다.",
                         "en": "The diligent students in my class always study hard."},
                        {"ko": "정직이 최선의 방책이다.", "en": "Honesty is the best policy."},
                    ],
                },
                {
                    "lead": "대명사가 주어",
                    "desc": "앞의 명사를 대신하거나 사람을 가리킬 때 쓰며, 주어 자리에는 반드시 **{{주격}}** 을 쓴다.",
                    "items": [
                        "주격 : {{I}} · {{you}} · {{he}} · {{she}} · {{it}} · {{we}} · {{they}}",
                    ],
                    "examples": [
                        {"ko": "그녀는 영어를 가르친다.", "en": "She teaches English."},
                        {"ko": "그들은 나의 반 친구들이다.", "en": "They are my classmates."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "tip", "label": "수 일치",
                    "lines": [
                        "주어가 **3인칭 단수**이면 현재형 동사에 **{{-(e)s}}** 를 붙인다.",
                        "My brother {{likes}} soccer.  /  My brothers {{like}} soccer.",
                    ],
                },
                {
                    "type": "warn", "label": "함정",
                    "lines": [
                        "① 주어 자리에 **목적격 금지** : Me and Tom …(X) → Tom and {{I}} …(O)",
                        "② 주어–동사 사이의 **수식어구에 끌리지 말 것.** 동사는 **핵심 명사**에 맞춘다.",
                        "The box of apples {{is}} heavy. ( 주어=box )   ← are (X)",
                    ],
                },
            ],
        },
        {
            "no": "02",
            "title": "동명사와 to부정사",
            "intro": "동사(run, read …)는 그대로 주어가 **{{될 수 없다||불가}}**. "
                     "**{{동명사(V-ing)}}** 또는 **{{to부정사(to+동사원형)}}** 로 바꿔야 주어가 된다.",
            "concepts": [
                {
                    "lead": "동명사(V-ing)가 주어",
                    "desc": "‘**{{~하는 것은}}**’으로 해석. 일반적·습관적 행위를 나타내며 구어에서 자연스럽다. "
                            "하나의 덩어리라 **{{단수}}** 취급한다.",
                    "examples": [
                        {"ko": "책을 읽는 것은 재미있다.", "en": "Reading books is fun."},
                        {"ko": "매일 운동하는 것은 너를 건강하게 유지해 준다.",
                         "en": "Exercising every day keeps you healthy."},
                    ],
                },
                {
                    "lead": "to부정사(to+동사원형)가 주어",
                    "desc": "역시 ‘~하는 것은’으로 해석하고 **{{단수}}** 취급. 동명사보다 **{{격식·문어체}}** 이다.",
                    "items": [
                        "긴 to부정사 주어는 대개 **가주어 {{it}}** 으로 뒤로 보낸다. (→ Point 04)",
                    ],
                    "examples": [
                        {"ko": "외국어를 마스터하는 것은 인내를 요구한다.",
                         "en": "To master a foreign language requires patience."},
                        {"ko": "규칙적으로 운동하는 것은 중요하다. (가주어 it)",
                         "en": "It is important to exercise regularly."},
                    ],
                    "space": 1,
                },
            ],
            "boxes": [
                {
                    "type": "compare", "label": "비교",
                    "lines": [
                        "**동명사** : 일반·습관·구어에서 흔함   /   **to부정사** : 격식·문어·특정 행위",
                        "→ 뜻(‘~하는 것은’)과 **{{단수}}** 취급은 같다. 실사용은 **가주어 it** 선호.",
                    ],
                },
                {
                    "type": "warn", "label": "함정",
                    "lines": [
                        "**동사원형은 주어 불가** : {{Run}} every day is good.(X) → "
                        "{{Running / To run}} every day is good.(O)",
                    ],
                },
            ],
        },
        {
            "no": "03",
            "title": "that절과 의문사절",
            "intro": "「주어+동사」를 갖춘 **{{문장 하나가 통째로 명사 역할(명사절)}}** 을 하며 주어가 된다. "
                     "명사절 주어도 **{{단수}}** 취급.",
            "concepts": [
                {
                    "lead": "that절이 주어",
                    "desc": "「**{{That}} + 완전한 문장**」 = ‘**{{~라는 것은}}**’. 사실·단정의 내용을 담는다. "
                            "딱딱하므로 보통 **가주어 it** 으로 옮긴다.",
                    "examples": [
                        {"ko": "지구가 둥글다는 것은 사실이다.", "en": "That the earth is round is true."},
                        {"ko": "그가 정직하다는 것은 사실이다. (가주어 it)",
                         "en": "It is true that he is honest."},
                    ],
                },
                {
                    "lead": "의문사절(간접의문문)이 주어",
                    "desc": "「**{{의문사}} + {{주어}} + {{동사}}**」 = ‘무엇이/누가/~인지’. "
                            "의문사 : what·who·when·where·why·how·whether(if)",
                    "examples": [
                        {"ko": "그가 말한 것이 우리를 놀라게 했다.", "en": "What he said surprised us."},
                        {"ko": "그녀가 왜 일찍 떠났는지는 미스터리다.", "en": "Why she left early is a mystery."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "warn", "label": "어순 함정",
                    "lines": [
                        "간접의문문은 **의문문 어순이 아니라 {{평서문}} 어순** : 「의문사 + {{주어}} + {{동사}}」",
                        "**{{do/does/did}}** 안 씀, **도치 안 함** : What he wants …(O) / What does he want …(X)",
                    ],
                },
                {
                    "type": "compare", "label": "비교",
                    "lines": [
                        "**that절** = {{사실·단정}} ‘~라는 것’   /   **의문사절** = {{불확실·의문}} ‘~인지’",
                    ],
                },
            ],
        },
        {
            "no": "04",
            "title": "가주어와 비인칭 주어",
            "intro": "영어는 **{{길고 무거운 주어를 앞에 두기 싫어한다||head-heavy 회피}}** → 형식상의 **it** 을 세운다.",
            "concepts": [
                {
                    "lead": "가주어 it (진주어를 뒤로)",
                    "desc": "주어가 to부정사구·that절처럼 길면 뒤로 보내고(=**{{진주어}}**), 그 자리에 "
                            "**가주어 {{it}}** 을 놓는다. 「It + 동사 + 보어 + 진주어」. **it 은 해석하지 {{않는다}}.**",
                    "examples": [
                        {"ko": "이 문제를 푸는 것은 어렵다.", "en": "It is difficult to solve this problem."},
                        {"ko": "그가 시험에 합격한 것은 놀랍다.",
                         "en": "It is surprising that he passed the exam."},
                    ],
                },
                {
                    "lead": "비인칭 주어 it",
                    "desc": "**{{시간·날씨·요일·거리·명암}}** 등을 나타낼 때 쓰는 형식상의 it. "
                            "가리키는 대상이 없어 **해석하지 {{않는다}}.**",
                    "examples": [
                        {"ko": "지금 비가 오고 있다.", "en": "It is raining now."},
                        {"ko": "3시다.", "en": "It is three o'clock."},
                        {"ko": "역까지 10km이다.", "en": "It is 10 km to the station."},
                    ],
                },
            ],
            "boxes": [
                {
                    "type": "compare", "label": "핵심 구별",
                    "lines": [
                        "**가주어 it** → 뒤에 **{{진주어(to부정사·that절)}} 가 있다.**",
                        "**비인칭 it** → 뒤에 **{{진주어가 없다}}.** (날씨·시간·거리 등)",
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
            ["의문사절", "{{What}} he said matters.", "~인지가", "{{단수}}"],
            ["가주어 it", "{{It}} is fun to read.", "(해석 안 함)", "{{단수}}"],
            ["비인칭 it", "{{It}} is sunny.", "(해석 안 함)", "{{단수}}"],
        ],
    },
    "practice": [
        {
            "q": "다음 문장에서 **주어**에 밑줄을 긋고, 괄호 안에서 알맞은 동사를 고르시오.",
            "items": [
                "Reading comic books ( is / are ) my hobby.   →  {{is}}",
                "The box of chocolates ( was / were ) on the table.   →  {{was}}",
                "That she won the prize ( surprise / surprised ) everyone.   →  {{surprised}}",
            ],
        },
        {
            "q": "우리말에 맞게 영작하시오. (직접 써 보기)",
            "items": [],
            "examples": [
                {"ko": "규칙적으로 운동하는 것은 중요하다.", "en": "It is important to exercise regularly."},
                {"ko": "그가 어디에 사는지는 알려져 있지 않다.", "en": "Where he lives is unknown."},
                {"ko": "그가 정직하다는 것은 사실이다.", "en": "It is true that he is honest."},
            ],
        },
        {
            "q": "어법상 **틀린** 부분을 찾아 바르게 고치시오.",
            "items": [
                "Run every day is good for your health.  →  {{Running / To run}}",
                "Me and my sister like music.  →  {{My sister and I}}",
                "What does he want is a secret.  →  {{What he wants}}",
            ],
        },
    ],
}
