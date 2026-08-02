# -*- coding: utf-8 -*-
"""
1주차(1~5일) 콘텐츠 데이터 — 김은아영어연구소 '중등 기초 브릿지' 숙제/테스트용.
지문 출처: 2022 개정 천재(강상구) 공통영어2 · Lesson 1 (The Nuisance / The Predator)
대상: 영어를 매우 어려워하고 단어 암기조차 힘든 고1 남학생.
설계 원칙:
  - 하루 숙제는 '핵심 10단어'로 가볍게. (수업에서 배운 것을 복습)
  - 따라쓰기 → 매칭 → 첫글자 힌트 → 문장 빈칸 → 문법 한 입 순서로 난이도 계단.
  - 매일 '어제 단어 복습' 5개로 반복 노출(분산 학습).
"""

WEEK_TITLE = "중등 기초 브릿지 · 1주차 숙제 & 테스트"
SOURCE = "2022 개정 천재(강상구) 공통영어2 · Lesson 1 · 고1 2학기 내신 대비"
COPYRIGHT = "ⓒ2026.김은아영어연구소.All rights reserved"

# ─────────────────────────────────────────────────────────────────────────
# 하루치 데이터 구조
#   day, weekday, title_ko, title_en, part, sentences_range
#   goal_title, goal_desc                (오늘의 문법 목표)
#   words: [(영어, 뜻)] 핵심 10개
#   review: [(영어, 뜻)] 어제 단어 5개 (1일차는 없음)
#   cloze: [(빈칸문장, 정답단어, 뜻힌트)]  지문 실제 문장
#   grammar_q: [(문제html, 정답)]         오늘의 문법 골라 동그라미
#   grammar_answer_note                   문법 해설 한 줄
# ─────────────────────────────────────────────────────────────────────────

DAYS = [
    # ===== 1일차 (월) The Nuisance ① =====
    dict(
        day=1, weekday="월", title_ko="모기가 문다", title_en="The Nuisance ①",
        part="PART 1 · 문장 1–9",
        goal_title="be동사(am·are·is) + 일반동사 3인칭 -s",
        goal_desc="주어가 '하나(he/she/it)'면 동사에 -s! 오늘은 이것만 잡으면 성공.",
        words=[
            ("mosquito", "모기"),
            ("skin", "피부"),
            ("blood", "피, 혈액"),
            ("itchy", "가려운"),
            ("escape", "달아나다, 탈출하다"),
            ("annoying", "짜증나는, 성가신"),
            ("victim", "먹잇감, 희생자"),
            ("signal", "신호"),
            ("pierce", "뚫다, 찌르다"),
            ("near", "가까운"),
        ],
        review=[],
        cloze=[
            ("Right at that moment, you hear that ______ buzzing sound.", "annoying", "성가신"),
            ("A mosquito sneaks in and ______s your skin.", "pierce", "뚫다"),
            ("It fills its belly with ______ and then escapes.", "blood", "피"),
            ("The more you scratch, the more it is ______.", "itchy", "가려운"),
        ],
        grammar_q=[
            ("You ( am / are / is ) on a camping trip.", "are"),
            ("A mosquito ( sneak / sneaks ) in.", "sneaks"),
            ("It ( fill / fills ) its belly with blood.", "fills"),
            ("How ( do / does ) mosquitoes find their victims?", "do"),
        ],
        grammar_answer_note="주어가 하나(a mosquito, it)면 동사에 -s. You/여럿(mosquitoes)이면 do·동사원형.",
    ),
    # ===== 2일차 (화) The Nuisance ② =====
    dict(
        day=2, weekday="화", title_ko="모기는 어떻게 찾을까", title_en="The Nuisance ②",
        part="PART 1 · 문장 10–15",
        goal_title="관계대명사 that / which — 명사를 뒤에서 꾸미기",
        goal_desc="명사 + [that/which ~] = '~하는 (명사)'. 이 덩어리를 묶어 읽으면 쉬워요.",
        words=[
            ("detect", "감지하다, 알아차리다"),
            ("sensitive", "민감한"),
            ("release", "내보내다, 분비하다"),
            ("attract", "끌어당기다, 유인하다"),
            ("notice", "알아채다"),
            ("cue", "단서, 신호"),
            ("protein", "단백질"),
            ("female", "암컷, 여성"),
            ("bite", "물다, 깨물다"),
            ("produce", "생산하다, 만들어 내다"),
        ],
        review=[("mosquito", "모기"), ("blood", "피, 혈액"), ("escape", "달아나다"),
                ("victim", "먹잇감"), ("pierce", "뚫다, 찌르다")],
        cloze=[
            ("When you sweat, you ______ certain chemicals.", "release", "분비하다"),
            ("Those chemicals ______ mosquitoes to you.", "attract", "유인하다"),
            ("They are highly ______ to CO2.", "sensitive", "민감한"),
            ("Only females need ______ to produce eggs.", "protein", "단백질"),
        ],
        grammar_q=[
            ("certain chemicals ( that / who ) attract them", "that"),
            ("chemicals that attract them = 그들을 ( 유인하는 / 유인당하는 ) 화학 물질", "유인하는"),
            ("the only cue ( they use / use they ) → 그들이 이용하는 단서", "they use"),
        ],
        grammar_answer_note="사물·동물을 꾸미면 that/which. '명사 + 주어 + 동사'면 관계대명사가 생략된 것.",
    ),
    # ===== 3일차 (수) The Nuisance ③ =====
    dict(
        day=3, weekday="수", title_ko="알을 낳기까지", title_en="The Nuisance ③",
        part="PART 1 · 문장 16–20",
        goal_title="가정법 과거 : If + 과거, 주어 would + 동사원형",
        goal_desc="'만약 (지금) ~라면 ~할 텐데' — 사실은 반대! 동사는 과거지만 뜻은 현재.",
        words=[
            ("contain", "포함하다, 담고 있다"),
            ("bother", "귀찮게 하다"),
            ("surface", "표면, 겉면"),
            ("gravity", "중력"),
            ("land", "내려앉다, 착륙하다"),
            ("develop", "발달·성숙시키다"),
            ("lay", "(알을) 낳다"),
            ("vertical", "수직의"),
            ("roughly", "대략, 약"),
            ("concentrated", "농축된, 진해진"),
        ],
        review=[("detect", "감지하다"), ("attract", "유인하다"), ("protein", "단백질"),
                ("female", "암컷"), ("bite", "물다")],
        cloze=[
            ("If our blood did not ______ protein, they would not bite us.", "contain", "포함하다"),
            ("She quickly ______s on the nearest vertical surface.", "land", "내려앉다"),
            ("With the aid of ______, she drains off the water.", "gravity", "중력"),
            ("She then ______s roughly 200 eggs on the water.", "lay", "(알을) 낳다"),
        ],
        grammar_q=[
            ("If our blood ( did not / does not ) contain protein,", "did not"),
            ("they ( will / would ) not bother us.", "would"),
            ("이 문장은 실제로 피에 단백질이 ( 있다 / 없다 ) 는 뜻.", "있다"),
        ],
        grammar_answer_note="가정법 과거 = 사실의 반대. If+과거동사, 주어 would+동사원형. (실제론 단백질이 있어서 문다.)",
    ),
    # ===== 4일차 (목) The Predator ① =====
    dict(
        day=4, weekday="목", title_ko="가장 위험한 동물", title_en="The Predator ①",
        part="PART 2 · 문장 21–28",
        goal_title="현재완료 : have / has + 과거분사(p.p.)",
        goal_desc="'지금까지 ~해 왔다 / ~한 적이 있다' — 과거가 지금까지 이어지는 느낌.",
        words=[
            ("predator", "포식자, 천적"),
            ("disease", "질병, 병"),
            ("deadly", "치명적인"),
            ("estimate", "추정하다"),
            ("empire", "제국"),
            ("fall", "몰락, 붕괴"),
            ("claim", "주장하다"),
            ("invasion", "침략, 침입"),
            ("corruption", "부패, 타락"),
            ("nearly", "거의"),
        ],
        review=[("contain", "포함하다"), ("bother", "귀찮게 하다"), ("gravity", "중력"),
                ("lay", "(알을) 낳다"), ("surface", "표면")],
        cloze=[
            ("Mosquitoes can pass on ______ diseases like malaria.", "deadly", "치명적인"),
            ("The real ______ in nature is the mosquito.", "predator", "포식자"),
            ("Winegard ______s that mosquitoes have killed billions.", "estimate", "추정하다"),
            ("Mosquitoes shaped the ______ of several countries.", "fall", "몰락"),
        ],
        grammar_q=[
            ("Mosquitoes ( have / has ) killed many people.", "have"),
            ("all humans who ( have / has ) ever lived", "have"),
            ("'have killed' 의 뜻: 지금까지 ( 죽여 왔다 / 죽일 것이다 )", "죽여 왔다"),
        ],
        grammar_answer_note="have/has + p.p. = 지금까지 이어진 일. 주어가 여럿(mosquitoes, humans)이면 have.",
    ),
    # ===== 5일차 (금) The Predator ② =====
    dict(
        day=5, weekday="금", title_ko="로마 제국과 모기", title_en="The Predator ②",
        part="PART 2 · 문장 29–34",
        goal_title="수동태 : be동사 + 과거분사(p.p.)",
        goal_desc="'~되다 / ~당하다' — 주어가 직접 하는 게 아니라 당하는 쪽. by ~ (~에 의해).",
        words=[
            ("capital", "수도; 자본"),
            ("surround", "둘러싸다"),
            ("wetland", "습지"),
            ("ideal", "이상적인"),
            ("eventually", "결국, 마침내"),
            ("spread", "퍼뜨리다, 퍼지다"),
            ("population", "인구, 개체 수"),
            ("contribute", "기여하다, 한몫하다"),
            ("powerful", "강력한"),
            ("attack", "공격하다"),
        ],
        review=[("predator", "포식자"), ("disease", "질병"), ("estimate", "추정하다"),
                ("empire", "제국"), ("claim", "주장하다")],
        cloze=[
            ("Rome, the ______ of the empire, had a huge wetland.", "capital", "수도"),
            ("Rome was once ______ed by a huge stretch of wetland.", "surround", "둘러싸다"),
            ("The wetland was an ______ breeding ground for mosquitoes.", "ideal", "이상적인"),
            ("They ______ the disease throughout the empire.", "spread", "퍼뜨리다"),
        ],
        grammar_q=[
            ("Rome ( surrounded / was surrounded ) by a huge wetland.", "was surrounded"),
            ("주어 Rome은 습지를 ( 둘러쌌다 / 둘러싸였다 )", "둘러싸였다"),
            ("수동태의 형태는 be동사 + ( 동사원형 / 과거분사 )", "과거분사"),
        ],
        grammar_answer_note="수동태 = be(am/are/is/was/were) + p.p. = '~되다/당하다'. 로마가 당한 쪽.",
    ),
]

# ─────────────────────────────────────────────────────────────────────────
# 주말 단어 테스트 (50문) — 5일치 핵심 50단어
# ─────────────────────────────────────────────────────────────────────────
ALL_WORDS = []
for d in DAYS:
    for en, ko in d["words"]:
        ALL_WORDS.append((en, ko, d["day"]))

# 영어→뜻 25 / 뜻→영어 25 로 나눔 (day 순서를 섞어 배치)
VOCAB_TEST_EN2KO = [ALL_WORDS[i] for i in range(0, 50, 2)]   # 25개
VOCAB_TEST_KO2EN = [ALL_WORDS[i] for i in range(1, 50, 2)]   # 25개

# ─────────────────────────────────────────────────────────────────────────
# 종합 테스트 데이터
# ─────────────────────────────────────────────────────────────────────────
COMP_VOCAB_EN2KO = [
    ("mosquito", "모기"), ("pierce", "뚫다, 찌르다"), ("victim", "먹잇감, 희생자"),
    ("release", "분비하다, 내보내다"), ("attract", "유인하다"), ("protein", "단백질"),
    ("contain", "포함하다"), ("gravity", "중력"), ("vertical", "수직의"),
    ("predator", "포식자"),
]
COMP_VOCAB_KO2EN = [
    ("치명적인", "deadly"), ("제국", "empire"), ("주장하다", "claim"),
    ("수도", "capital"), ("둘러싸다", "surround"), ("결국, 마침내", "eventually"),
    ("퍼뜨리다", "spread"), ("인구", "population"), ("감지하다", "detect"),
    ("가려운", "itchy"),
]

COMP_GRAMMAR = [
    # (문제, 정답, 유형)
    ("A mosquito ( sneak / sneaks ) into the tent.", "sneaks", "3인칭 -s"),
    ("You ( am / are / is ) my best friend.", "are", "be동사"),
    ("How ( do / does ) mosquitoes find us?", "do", "일반동사 의문문"),
    ("certain chemicals ( that / who ) attract them", "that", "관계대명사"),
    ("If our blood did not contain protein, they ( will / would ) not bother us.", "would", "가정법 과거"),
    ("Mosquitoes ( have / has ) killed billions of people.", "have", "현재완료"),
    ("all humans who ( have / has ) ever lived", "have", "현재완료"),
    ("Rome ( surrounded / was surrounded ) by wetland.", "was surrounded", "수동태"),
    ("The plan ( brought / was brought ) down by diseases.", "was brought", "수동태"),
    ("She ( land / lands ) on the nearest surface.", "lands", "3인칭 -s"),
]

COMP_TRANSLATE = [
    "A mosquito sneaks in and pierces your skin.",
    "When you sweat, you release certain chemicals that attract them.",
    "If our blood did not contain protein, they would not bother us.",
    "Mosquitoes have killed more people than any other single cause.",
    "Rome was once surrounded by a huge stretch of wetland.",
]
COMP_TRANSLATE_ANS = [
    "모기가 몰래 들어와 너의 피부를 뚫는다(찌른다).",
    "네가 땀을 흘리면, 너는 그들을 유인하는 특정한 화학 물질을 내보낸다(분비한다).",
    "만약 우리 피가 단백질을 담고 있지 않다면, 그들은 우리를 귀찮게 하지 않을 텐데.",
    "모기는 다른 어떤 단일 원인보다도 더 많은 사람을 죽여 왔다.",
    "로마는 한때 거대하게 펼쳐진 습지로 둘러싸여 있었다.",
]

# 미니 독해 (지문 일부를 쉽게 재구성)
COMP_READING = (
    "Mosquitoes are highly sensitive to CO2 and can detect it from far away. "
    "When you sweat, you release certain chemicals that attract them. "
    "Only female mosquitoes bite us; they need protein to produce eggs. "
    "After taking blood, a female lands on a vertical surface and lays about 200 eggs."
)
COMP_READING_Q = [
    ("모기는 무엇을 멀리서도 감지할 수 있나요? (우리말로)", "이산화탄소(CO2)"),
    ("우리를 무는 것은 암컷 모기인가요, 수컷 모기인가요?", "암컷 모기"),
    ("암컷 모기가 단백질을 필요로 하는 이유는?", "알을 낳기(만들기) 위해서"),
    ("T/F : A female mosquito lays about 200 eggs.", "T (맞음)"),
]
