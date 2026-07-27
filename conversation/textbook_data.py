# -*- coding: utf-8 -*-
"""
중학생 수준 영어 회화 교재 콘텐츠 (OPIC 주제 기반 · '내 의견 말하기' 템플릿).

가로(landscape) 2단 구성:
  - 왼쪽: 내 의견 말하기 5단계 템플릿 (빈칸 채워 스스로 의견을 구성)
  - 오른쪽: 워드뱅크 (중학생 수준 어휘)

대화문은 없습니다. OPIC 질문을 받고 '내 의견/소개'를 스스로 말하는 연습용입니다.
콘텐츠만 수정하면 build_textbook.py 가 그대로 PDF 로 만들어 줍니다.
"""

TITLE = "중학 영어 회화 교재"
SUBTITLE = "OPIC 주제로 말하는 나의 의견 · 중학생 수준 · 템플릿 + 워드뱅크"
FOOTER = "중학 영어 회화 교재 · 내 의견 말하기 템플릿 + 워드뱅크"

# 교재 사용법
HOW_TO_USE = [
    ("1. 워드뱅크 익히기", "오른쪽 워드뱅크의 단어와 뜻을 먼저 읽고, 오늘 쓸 단어 2~3개를 골라 둡니다."),
    ("2. 5단계 템플릿 채우기", "왼쪽 템플릿의 빈칸(____)에 내 생각과 워드뱅크 단어를 넣어 문장을 완성합니다."),
    ("3. 소리 내어 말하기", "①~⑤ 문장을 이어서 한 편의 '내 의견'으로 30초~1분간 말해 봅니다."),
    ("4. 응용하기", "예시 대신 자신의 진짜 경험·생각으로 바꿔 말하면 완성도가 올라갑니다."),
]

# 5단계 템플릿 골격 설명
STEPS_GUIDE = [
    ("① 주제 소개", "무엇에 대해 말할지 밝히기"),
    ("② 내 의견·선호", "내 생각/선호를 한 문장으로 제시"),
    ("③ 이유", "그렇게 생각하는 이유 1~2가지"),
    ("④ 예시·경험", "구체적인 예나 내 경험 들기"),
    ("⑤ 마무리", "핵심을 다시 정리하며 마무리"),
]

# 공통 '의견 말하기' 표현 모음 (연결어 · 패턴)
EXPRESSIONS = [
    ("의견 제시", [
        ("In my opinion, ~", "제 생각에는 ~"),
        ("Personally, I think (that) ~", "개인적으로 저는 ~라고 생각해요"),
        ("From my point of view, ~", "제 관점에서는 ~"),
        ("I'd say (that) ~", "~라고 말하고 싶어요"),
    ]),
    ("선호 표현", [
        ("I prefer A to B", "저는 B보다 A를 더 좋아해요"),
        ("I'm really into ~", "저는 ~에 푹 빠져 있어요"),
        ("I'm a big fan of ~", "저는 ~의 열렬한 팬이에요"),
        ("What I like most is ~", "제가 가장 좋아하는 것은 ~예요"),
    ]),
    ("이유·연결", [
        ("The main reason is that ~", "가장 큰 이유는 ~이기 때문이에요"),
        ("This is (mainly) because ~", "이는 (주로) ~이기 때문이에요"),
        ("In addition, ~ / Also, ~", "게다가 ~ / 또한 ~"),
        ("What's more, ~", "더욱이 ~"),
    ]),
    ("예시·마무리", [
        ("For example / For instance, ~", "예를 들어 ~"),
        ("Overall, ~ / All in all, ~", "전반적으로 ~"),
        ("That's why ~", "그래서 ~인 거예요"),
        ("However / On the other hand, ~", "하지만 / 반면에 ~"),
    ]),
]


def _step(label, lines):
    return {"label": label, "lines": lines}


UNITS = [
    {
        "emoji": "👪", "title_ko": "나와 가족", "title_en": "Me & My Family",
        "prompt": "Tell me about your family.",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to tell you about my family.", "제 가족에 대해 이야기하고 싶어요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, family is one of the most important things in my life.", "제 생각에 가족은 제 인생에서 가장 중요한 것 중 하나예요."),
                ("Personally, I think my family is very ____ (close / caring).", "개인적으로 우리 가족은 매우 ____하다고 생각해요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that we ____ (spend a lot of time together).", "가장 큰 이유는 우리가 ____하기 때문이에요."),
                ("In addition, my parents always ____ (support and encourage me).", "게다가 부모님은 항상 저를 ____해 주세요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, every weekend we ____ (have dinner and share our stories).", "예를 들어, 주말마다 우리는 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I feel lucky to have such a ____ (supportive) family.", "전반적으로, 저는 이렇게 ____한 가족이 있어 운이 좋다고 느껴요."),
            ]),
        ],
        "words": [
            ("supportive", "힘이 되어주는 (형)"),
            ("get along with", "~와 잘 지내다"),
            ("close-knit", "사이가 돈독한 (형)"),
            ("rely on", "~에게 의지하다"),
            ("sibling", "형제자매 (명)"),
            ("caring", "배려심 있는 (형)"),
            ("respect", "존중하다 (동)"),
            ("value", "소중히 여기다 (동)"),
            ("relative", "친척 (명)"),
            ("encourage", "격려하다 (동)"),
        ],
    },
    {
        "emoji": "🏠", "title_ko": "우리 집", "title_en": "My Home",
        "prompt": "Describe the place where you live.",
        "template": [
            _step("① 주제 소개", [
                ("Let me describe the place where I live.", "제가 사는 곳을 소개할게요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, my home is very ____ (cozy and comfortable).", "제 생각에 우리 집은 매우 ____해요."),
                ("Personally, my favorite space is ____ (my own room).", "개인적으로 제가 가장 좋아하는 공간은 ____예요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____ (it's where I can fully relax).", "가장 큰 이유는 ____이기 때문이에요."),
                ("In addition, my neighborhood is ____ (quiet and convenient).", "게다가 우리 동네는 ____해요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, after school I usually ____ (relax and listen to music there).", "예를 들어, 방과 후에 저는 보통 거기서 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, my home is a place where I feel ____ (safe and relaxed).", "전반적으로, 우리 집은 제가 ____하다고 느끼는 곳이에요."),
            ]),
        ],
        "words": [
            ("cozy", "아늑한 (형)"),
            ("spacious", "널찍한 (형)"),
            ("furniture", "가구 (명)"),
            ("neighborhood", "동네, 이웃 (명)"),
            ("convenient", "편리한 (형)"),
            ("atmosphere", "분위기 (명)"),
            ("appliance", "가전제품 (명)"),
            ("surroundings", "주변 환경 (명)"),
            ("private", "개인적인, 사적인 (형)"),
            ("decorate", "장식하다 (동)"),
        ],
    },
    {
        "emoji": "🏫", "title_ko": "학교 생활", "title_en": "My School Life",
        "prompt": "Talk about your school life.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my school life.", "제 학교 생활에 대해 이야기할게요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the best part of school is ____ (being with my friends).", "제 생각에 학교에서 가장 좋은 점은 ____예요."),
                ("Personally, my favorite subject is ____ because it is ____.", "개인적으로 제가 가장 좋아하는 과목은 ____인데, ____하기 때문이에요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____ (it is both fun and challenging).", "가장 큰 이유는 ____이기 때문이에요."),
                ("Also, my teacher ____ (explains things clearly).", "또한, 선생님이 ____해 주세요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ class, we often ____ (do interesting experiments).", "예를 들어, ____ 수업에서 우리는 자주 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, school life is ____ (busy but rewarding) for me.", "전반적으로, 학교 생활은 저에게 ____해요."),
            ]),
        ],
        "words": [
            ("academic", "학업의 (형)"),
            ("challenging", "어렵지만 해볼 만한 (형)"),
            ("classmate", "반 친구 (명)"),
            ("extracurricular", "방과 후의, 교외의 (형)"),
            ("assignment", "과제 (명)"),
            ("concentrate", "집중하다 (동)"),
            ("participate", "참여하다 (동)"),
            ("achieve", "성취하다 (동)"),
            ("semester", "학기 (명)"),
            ("rewarding", "보람 있는 (형)"),
        ],
    },
    {
        "emoji": "🎨", "title_ko": "취미", "title_en": "My Hobbies",
        "prompt": "What do you like to do in your free time?",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about what I do in my free time.", "제가 여가 시간에 하는 일에 대해 이야기하고 싶어요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ (drawing) is the perfect way to spend my free time.", "제 생각에 ____은(는) 여가를 보내기에 완벽한 방법이에요."),
                ("Personally, I'm really passionate about ____.", "개인적으로 저는 ____에 정말 열정적이에요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that it helps me ____ (relieve stress and relax).", "가장 큰 이유는 그것이 저를 ____하게 도와주기 때문이에요."),
                ("In addition, it makes me feel ____ (creative and productive).", "게다가 그것은 저를 ____하게 느끼게 해요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, I usually ____ (spend a few hours drawing on weekends).", "예를 들어, 저는 보통 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, this hobby makes my life much more ____ (enjoyable).", "전반적으로, 이 취미는 제 삶을 훨씬 더 ____하게 만들어요."),
            ]),
        ],
        "words": [
            ("leisure", "여가 (명)"),
            ("pastime", "취미, 소일거리 (명)"),
            ("passionate about", "~에 열정적인"),
            ("relieve stress", "스트레스를 풀다"),
            ("relaxing", "편안하게 해주는 (형)"),
            ("pursue", "추구하다, 즐기다 (동)"),
            ("creative", "창의적인 (형)"),
            ("immerse oneself in", "~에 몰입하다"),
            ("productive", "생산적인 (형)"),
            ("regularly", "규칙적으로 (부)"),
        ],
    },
    {
        "emoji": "⚽", "title_ko": "운동", "title_en": "Sports & Exercise",
        "prompt": "Tell me about a sport or exercise you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about a sport I enjoy.", "제가 즐기는 운동에 대해 말할게요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ (soccer) is the most exciting sport.", "제 생각에 ____은(는) 가장 신나는 운동이에요."),
                ("Personally, I prefer ____ to other sports.", "개인적으로 저는 다른 운동보다 ____을(를) 더 좋아해요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that it improves my ____ (fitness and stamina).", "가장 큰 이유는 그것이 제 ____을(를) 향상시키기 때문이에요."),
                ("Also, it teaches me the importance of ____ (teamwork).", "또한, 그것은 저에게 ____의 중요성을 가르쳐 줘요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, I ____ (play soccer with my friends twice a week).", "예를 들어, 저는 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, exercising regularly keeps me ____ (healthy and energetic).", "전반적으로, 규칙적인 운동은 저를 ____하게 유지해 줘요."),
            ]),
        ],
        "words": [
            ("work out", "운동하다"),
            ("stamina", "체력, 지구력 (명)"),
            ("competitive", "경쟁심이 강한 (형)"),
            ("teamwork", "팀워크 (명)"),
            ("opponent", "상대 (명)"),
            ("endurance", "인내력, 지구력 (명)"),
            ("fitness", "건강, 체력 (명)"),
            ("energetic", "활기찬 (형)"),
            ("warm up", "준비운동을 하다"),
            ("improve", "향상시키다 (동)"),
        ],
    },
    {
        "emoji": "🍚", "title_ko": "음식", "title_en": "Food & Meals",
        "prompt": "Talk about your favorite food.",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about my favorite food.", "제가 가장 좋아하는 음식에 대해 이야기하고 싶어요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ (pizza) is the most delicious food.", "제 생각에 ____은(는) 가장 맛있는 음식이에요."),
                ("Personally, I prefer ____ (spicy) food.", "개인적으로 저는 ____한 음식을 더 좋아해요."),
            ]),
            _step("③ 이유", [
                ("The main reason is its ____ (rich flavor).", "가장 큰 이유는 그것의 ____ 때문이에요."),
                ("In addition, it is ____ (fairly nutritious and filling).", "게다가 그것은 ____해요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____ (order pizza when I hang out with friends).", "예를 들어, 저는 자주 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, good food always ____ (makes me happy).", "전반적으로, 맛있는 음식은 항상 저를 ____하게 해요."),
            ]),
        ],
        "words": [
            ("cuisine", "요리, (특정)음식 (명)"),
            ("flavor", "맛, 풍미 (명)"),
            ("ingredient", "재료 (명)"),
            ("nutritious", "영양가 있는 (형)"),
            ("spicy", "매운 (형)"),
            ("recipe", "조리법 (명)"),
            ("appetite", "식욕 (명)"),
            ("homemade", "집에서 만든 (형)"),
            ("balanced diet", "균형 잡힌 식단"),
            ("prefer", "선호하다 (동)"),
        ],
    },
    {
        "emoji": "🐶", "title_ko": "반려동물", "title_en": "Pets",
        "prompt": "Do you have a pet, or would you like one?",
        "template": [
            _step("① 주제 소개", [
                ("Let me share my thoughts about pets.", "반려동물에 대한 제 생각을 나눌게요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, pets are wonderful ____ (companions).", "제 생각에 반려동물은 훌륭한 ____예요."),
                ("Personally, I would love to have a ____ (dog).", "개인적으로 저는 ____을(를) 키우고 싶어요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that they are ____ (loyal and affectionate).", "가장 큰 이유는 그들이 ____하기 때문이에요."),
                ("In addition, taking care of a pet teaches ____ (responsibility).", "게다가 반려동물을 돌보는 것은 ____을(를) 가르쳐 줘요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, a dog will ____ (happily greet you whenever you come home).", "예를 들어, 강아지는 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, having a pet can make life much more ____ (joyful).", "전반적으로, 반려동물을 키우는 것은 삶을 훨씬 더 ____하게 만들 수 있어요."),
            ]),
        ],
        "words": [
            ("companion", "동반자, 친구 (명)"),
            ("loyal", "충성스러운 (형)"),
            ("affectionate", "애정 어린 (형)"),
            ("responsibility", "책임 (명)"),
            ("take care of", "~을 돌보다"),
            ("adopt", "입양하다 (동)"),
            ("obedient", "순종적인 (형)"),
            ("be attached to", "~에 정들다"),
            ("breed", "품종 (명)"),
            ("groom", "손질하다 (동)"),
        ],
    },
    {
        "emoji": "🌈", "title_ko": "날씨와 계절", "title_en": "Weather & Seasons",
        "prompt": "Talk about your favorite season.",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about my favorite season.", "제가 가장 좋아하는 계절에 대해 이야기하고 싶어요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ (fall) is the most pleasant season.", "제 생각에 ____은(는) 가장 쾌적한 계절이에요."),
                ("Personally, I prefer ____ (mild) weather.", "개인적으로 저는 ____한 날씨를 더 좋아해요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that the ____ (temperature is cool and comfortable).", "가장 큰 이유는 ____이기 때문이에요."),
                ("In addition, I can ____ (do many outdoor activities).", "게다가 저는 ____할 수 있어요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ (fall) I usually ____ (go hiking to enjoy the scenery).", "예를 들어, ____에 저는 보통 ____해요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, the weather really ____ (affects my mood).", "전반적으로, 날씨는 제 ____에 정말 영향을 줘요."),
            ]),
        ],
        "words": [
            ("climate", "기후 (명)"),
            ("forecast", "예보 (명)"),
            ("humid", "습한 (형)"),
            ("chilly", "쌀쌀한 (형)"),
            ("mild", "온화한 (형)"),
            ("temperature", "기온 (명)"),
            ("breeze", "산들바람 (명)"),
            ("pleasant", "쾌적한 (형)"),
            ("gloomy", "우중충한 (형)"),
            ("affect", "영향을 주다 (동)"),
        ],
    },
    {
        "emoji": "🎬", "title_ko": "영화와 음악", "title_en": "Movies & Music",
        "prompt": "Talk about the movies or music you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the movies and music I enjoy.", "제가 즐기는 영화와 음악에 대해 이야기할게요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ (action) movies are the most entertaining.", "제 생각에 ____ 영화가 가장 재미있어요."),
                ("Personally, I'm a big fan of ____ (K-pop).", "개인적으로 저는 ____의 열렬한 팬이에요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that the ____ (plot / melody) is really ____ (exciting).", "가장 큰 이유는 ____이(가) 정말 ____하기 때문이에요."),
                ("Also, the ____ (lyrics / soundtrack) match my mood.", "또한, ____이(가) 제 기분과 잘 맞아요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently enjoyed ____, and it was really ____ (touching).", "예를 들어, 저는 최근에 ____을(를) 즐겼는데, 정말 ____했어요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, movies and music help me ____ (relax and recharge).", "전반적으로, 영화와 음악은 제가 ____하도록 도와줘요."),
            ]),
        ],
        "words": [
            ("genre", "장르 (명)"),
            ("plot", "줄거리 (명)"),
            ("soundtrack", "사운드트랙 (명)"),
            ("lyrics", "가사 (명)"),
            ("touching", "감동적인 (형)"),
            ("catchy", "기억하기 쉬운 (형)"),
            ("talented", "재능 있는 (형)"),
            ("entertaining", "재미있는 (형)"),
            ("recommend", "추천하다 (동)"),
            ("release", "개봉/발매하다 (동)"),
        ],
    },
    {
        "emoji": "✈️", "title_ko": "여행과 방학", "title_en": "Travel & Vacation",
        "prompt": "Talk about a trip or how you spend your vacation.",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about how I spend my vacation.", "제가 방학을 어떻게 보내는지 이야기하고 싶어요."),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, traveling is the best way to spend a vacation.", "제 생각에 여행은 방학을 보내는 가장 좋은 방법이에요."),
                ("Personally, I really want to visit ____ (Jeju Island).", "개인적으로 저는 ____에 정말 가보고 싶어요."),
            ]),
            _step("③ 이유", [
                ("The main reason is that I can ____ (experience new cultures and scenery).", "가장 큰 이유는 제가 ____할 수 있기 때문이에요."),
                ("In addition, traveling helps me ____ (broaden my horizons).", "게다가 여행은 제가 ____하도록 도와줘요."),
            ]),
            _step("④ 예시·경험", [
                ("For example, last vacation I ____ (visited the beach and went sightseeing).", "예를 들어, 지난 방학에 저는 ____했어요."),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a good trip is always ____ (memorable).", "전반적으로, 좋은 여행은 항상 ____해요."),
            ]),
        ],
        "words": [
            ("destination", "목적지 (명)"),
            ("sightseeing", "관광 (명)"),
            ("scenery", "경치 (명)"),
            ("accommodation", "숙소 (명)"),
            ("explore", "탐험하다 (동)"),
            ("memorable", "기억에 남는 (형)"),
            ("itinerary", "여행 일정 (명)"),
            ("adventure", "모험 (명)"),
            ("broaden one's horizons", "견문을 넓히다"),
            ("local", "현지의 (형)"),
        ],
    },
]
