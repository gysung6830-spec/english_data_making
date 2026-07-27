# -*- coding: utf-8 -*-
"""
중학생 수준 영어 회화 교재 콘텐츠 (OPIC 주제 기반 · '내 의견 말하기' 템플릿).

가로(landscape) 2단 구성:
  - 왼쪽: 내 의견 말하기 5단계 템플릿. 각 빈칸(____)마다 '보기 단어'를 5개 이상 제시
  - 오른쪽: 워드뱅크 (중학생 수준 어휘)

대화문은 없습니다. OPIC 질문을 받고 '내 의견/소개'를 스스로 말하는 연습용입니다.

■ 템플릿 문장(line) 형식: (영어, 한글, [빈칸별 보기목록])
  - 영어 문장의 ____ 개수 = 보기목록 개수 (앞 빈칸부터 순서대로 대응)
  - 빈칸이 없는 문장은 보기목록을 [] 로 둔다
콘텐츠만 수정하면 build_textbook.py 가 그대로 PDF 로 만들어 줍니다.
"""

TITLE = "중학 영어 회화 교재"
SUBTITLE = "OPIC 주제로 말하는 나의 의견 · 중학생 수준 · 템플릿 + 워드뱅크"
FOOTER = "중학 영어 회화 교재 · 내 의견 말하기 템플릿 + 워드뱅크"

HOW_TO_USE = [
    ("1. 워드뱅크 익히기", "오른쪽 워드뱅크의 단어와 뜻을 먼저 읽고, 오늘 쓸 단어 2~3개를 골라 둡니다."),
    ("2. 빈칸 채우기", "왼쪽 템플릿의 빈칸(____)마다 아래 '보기' 중 하나를 골라(또는 내 생각으로) 문장을 완성합니다."),
    ("3. 소리 내어 말하기", "①~⑤ 문장을 이어서 한 편의 '내 의견'으로 30초~1분간 말해 봅니다."),
    ("4. 응용하기", "보기에 없는 나만의 표현으로 바꿔 말하면 완성도가 더 올라갑니다."),
]

STEPS_GUIDE = [
    ("① 주제 소개", "무엇에 대해 말할지 밝히기"),
    ("② 내 의견·선호", "내 생각/선호를 한 문장으로 제시"),
    ("③ 이유", "그렇게 생각하는 이유 1~2가지"),
    ("④ 예시·경험", "구체적인 예나 내 경험 들기"),
    ("⑤ 마무리", "핵심을 다시 정리하며 마무리"),
]

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
                ("I'd like to tell you about my family.", "제 가족에 대해 이야기하고 싶어요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, family is one of the most important things in my life.",
                 "제 생각에 가족은 제 인생에서 가장 중요한 것 중 하나예요.", []),
                ("Personally, I think my family is very ____.",
                 "개인적으로 우리 가족은 매우 ____하다고 생각해요.",
                 [["close", "caring", "supportive", "cheerful", "close-knit", "loving"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that we ____.",
                 "가장 큰 이유는 우리가 ____하기 때문이에요.",
                 [["spend a lot of time together", "always help each other", "get along well",
                   "share everything", "eat dinner together every day", "support one another"]]),
                ("In addition, my parents always ____.",
                 "게다가 부모님은 항상 저를 ____해 주세요.",
                 [["support and encourage me", "believe in me", "listen to me",
                   "give me good advice", "cheer me up", "respect my opinion"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, every weekend we ____.",
                 "예를 들어, 주말마다 우리는 ____해요.",
                 [["have dinner and share our stories", "watch movies together", "go for a walk",
                   "cook together", "visit our grandparents", "play board games"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I feel lucky to have such a ____ family.",
                 "전반적으로, 저는 이렇게 ____한 가족이 있어 운이 좋다고 느껴요.",
                 [["supportive", "caring", "loving", "warm", "close-knit", "wonderful"]]),
            ]),
        ],
        "words": [
            ("supportive", "힘이 되어주는 (형)"), ("get along with", "~와 잘 지내다"),
            ("close-knit", "사이가 돈독한 (형)"), ("rely on", "~에게 의지하다"),
            ("sibling", "형제자매 (명)"), ("caring", "배려심 있는 (형)"),
            ("respect", "존중하다 (동)"), ("value", "소중히 여기다 (동)"),
            ("relative", "친척 (명)"), ("encourage", "격려하다 (동)"),
        ],
    },
    {
        "emoji": "🏠", "title_ko": "우리 집", "title_en": "My Home",
        "prompt": "Describe the place where you live.",
        "template": [
            _step("① 주제 소개", [
                ("Let me describe the place where I live.", "제가 사는 곳을 소개할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, my home is very ____.",
                 "제 생각에 우리 집은 매우 ____해요.",
                 [["cozy", "comfortable", "spacious", "warm", "peaceful", "clean"]]),
                ("Personally, my favorite space is ____.",
                 "개인적으로 제가 가장 좋아하는 공간은 ____예요.",
                 [["my own room", "the living room", "the kitchen", "the balcony", "my study", "the rooftop"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [["it's where I can fully relax", "it's quiet and private", "I can be alone there",
                   "it's full of my favorite things", "I can study well there", "it feels comfortable"]]),
                ("In addition, my neighborhood is ____.",
                 "게다가 우리 동네는 ____해요.",
                 [["quiet and convenient", "safe", "friendly", "close to everything",
                   "full of parks", "clean"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, after school I usually ____ there.",
                 "예를 들어, 방과 후에 저는 보통 거기서 ____해요.",
                 [["relax and listen to music", "do my homework", "read books",
                   "play games", "take a short nap", "chat with my family"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, my home is a place where I feel ____.",
                 "전반적으로, 우리 집은 제가 ____하다고 느끼는 곳이에요.",
                 [["safe and relaxed", "comfortable", "at peace", "happy", "free", "calm"]]),
            ]),
        ],
        "words": [
            ("cozy", "아늑한 (형)"), ("spacious", "널찍한 (형)"), ("furniture", "가구 (명)"),
            ("neighborhood", "동네, 이웃 (명)"), ("convenient", "편리한 (형)"),
            ("atmosphere", "분위기 (명)"), ("appliance", "가전제품 (명)"),
            ("surroundings", "주변 환경 (명)"), ("private", "개인적인, 사적인 (형)"),
            ("decorate", "장식하다 (동)"),
        ],
    },
    {
        "emoji": "🏫", "title_ko": "학교 생활", "title_en": "My School Life",
        "prompt": "Talk about your school life.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my school life.", "제 학교 생활에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the best part of school is ____.",
                 "제 생각에 학교에서 가장 좋은 점은 ____예요.",
                 [["being with my friends", "learning new things", "lunch time",
                   "club activities", "sports day", "my favorite classes"]]),
                ("Personally, my favorite subject is ____ because it is ____.",
                 "개인적으로 제가 가장 좋아하는 과목은 ____인데, ____하기 때문이에요.",
                 [["science", "English", "math", "history", "music", "art", "P.E."],
                  ["interesting", "fun", "useful", "easy to understand", "challenging", "practical"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [["it is both fun and challenging", "the teacher makes it fun", "I'm good at it",
                   "I can use it in real life", "it makes me think", "the lessons are interesting"]]),
                ("Also, my teacher ____.",
                 "또한, 선생님이 ____해 주세요.",
                 [["explains things clearly", "is kind and patient", "makes class fun",
                   "always helps us", "encourages us", "gives useful examples"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ class, we often ____.",
                 "예를 들어, ____ 수업에서 우리는 자주 ____해요.",
                 [["science", "English", "art", "music", "P.E.", "math"],
                  ["do interesting experiments", "have group discussions", "play language games",
                   "work on projects", "watch videos", "solve problems together"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, school life is ____ for me.",
                 "전반적으로, 학교 생활은 저에게 ____해요.",
                 [["busy but rewarding", "fun and meaningful", "sometimes hard but worth it",
                   "full of good memories", "a great experience", "better than I expected"]]),
            ]),
        ],
        "words": [
            ("academic", "학업의 (형)"), ("challenging", "어렵지만 해볼 만한 (형)"),
            ("classmate", "반 친구 (명)"), ("extracurricular", "방과 후의, 교외의 (형)"),
            ("assignment", "과제 (명)"), ("concentrate", "집중하다 (동)"),
            ("participate", "참여하다 (동)"), ("achieve", "성취하다 (동)"),
            ("semester", "학기 (명)"), ("rewarding", "보람 있는 (형)"),
        ],
    },
    {
        "emoji": "🎨", "title_ko": "취미", "title_en": "My Hobbies",
        "prompt": "What do you like to do in your free time?",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about what I do in my free time.",
                 "제가 여가 시간에 하는 일에 대해 이야기하고 싶어요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the perfect way to spend my free time.",
                 "제 생각에 ____은(는) 여가를 보내기에 완벽한 방법이에요.",
                 [["drawing", "reading", "playing the guitar", "riding a bike",
                   "playing games", "taking photos"]]),
                ("Personally, I'm really passionate about ____.",
                 "개인적으로 저는 ____에 정말 열정적이에요.",
                 [["drawing", "music", "sports", "reading", "cooking", "photography"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that it helps me ____.",
                 "가장 큰 이유는 그것이 저를 ____하게 도와주기 때문이에요.",
                 [["relieve stress and relax", "forget my worries", "feel refreshed",
                   "express myself", "focus my mind", "enjoy my free time"]]),
                ("In addition, it makes me feel ____.",
                 "게다가 그것은 저를 ____하게 느끼게 해요.",
                 [["creative and productive", "happy and relaxed", "confident",
                   "proud", "energized", "calm"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I usually ____.",
                 "예를 들어, 저는 보통 ____해요.",
                 [["spend a few hours drawing on weekends", "practice every evening",
                   "join an online community", "watch tutorials", "do it with my friends", "try new things"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, this hobby makes my life much more ____.",
                 "전반적으로, 이 취미는 제 삶을 훨씬 더 ____하게 만들어요.",
                 [["enjoyable", "colorful", "exciting", "meaningful", "balanced", "fun"]]),
            ]),
        ],
        "words": [
            ("leisure", "여가 (명)"), ("pastime", "취미, 소일거리 (명)"),
            ("passionate about", "~에 열정적인"), ("relieve stress", "스트레스를 풀다"),
            ("relaxing", "편안하게 해주는 (형)"), ("pursue", "추구하다, 즐기다 (동)"),
            ("creative", "창의적인 (형)"), ("immerse oneself in", "~에 몰입하다"),
            ("productive", "생산적인 (형)"), ("regularly", "규칙적으로 (부)"),
        ],
    },
    {
        "emoji": "⚽", "title_ko": "운동", "title_en": "Sports & Exercise",
        "prompt": "Tell me about a sport or exercise you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about a sport I enjoy.", "제가 즐기는 운동에 대해 말할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most exciting sport.",
                 "제 생각에 ____은(는) 가장 신나는 운동이에요.",
                 [["soccer", "basketball", "badminton", "swimming", "table tennis", "baseball"]]),
                ("Personally, I prefer ____ to other sports.",
                 "개인적으로 저는 다른 운동보다 ____을(를) 더 좋아해요.",
                 [["soccer", "running", "swimming", "basketball", "badminton", "cycling"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that it improves my ____.",
                 "가장 큰 이유는 그것이 제 ____을(를) 향상시키기 때문이에요.",
                 [["fitness and stamina", "health", "strength", "endurance",
                   "concentration", "mood"]]),
                ("Also, it teaches me the importance of ____.",
                 "또한, 그것은 저에게 ____의 중요성을 가르쳐 줘요.",
                 [["teamwork", "patience", "effort", "discipline", "fair play", "never giving up"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I ____.",
                 "예를 들어, 저는 ____해요.",
                 [["play soccer with my friends twice a week", "go swimming every weekend",
                   "jog every morning", "practice after school", "join a local club", "work out at the gym"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, exercising regularly keeps me ____.",
                 "전반적으로, 규칙적인 운동은 저를 ____하게 유지해 줘요.",
                 [["healthy and energetic", "fit", "refreshed", "in a good mood", "strong", "active"]]),
            ]),
        ],
        "words": [
            ("work out", "운동하다"), ("stamina", "체력, 지구력 (명)"),
            ("competitive", "경쟁심이 강한 (형)"), ("teamwork", "팀워크 (명)"),
            ("opponent", "상대 (명)"), ("endurance", "인내력, 지구력 (명)"),
            ("fitness", "건강, 체력 (명)"), ("energetic", "활기찬 (형)"),
            ("warm up", "준비운동을 하다"), ("improve", "향상시키다 (동)"),
        ],
    },
    {
        "emoji": "🍚", "title_ko": "음식", "title_en": "Food & Meals",
        "prompt": "Talk about your favorite food.",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about my favorite food.",
                 "제가 가장 좋아하는 음식에 대해 이야기하고 싶어요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most delicious food.",
                 "제 생각에 ____은(는) 가장 맛있는 음식이에요.",
                 [["pizza", "fried chicken", "tteokbokki", "sushi", "pasta", "bibimbap"]]),
                ("Personally, I prefer ____ food.",
                 "개인적으로 저는 ____한 음식을 더 좋아해요.",
                 [["spicy", "sweet", "salty", "Korean", "Italian", "homemade"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is its ____.",
                 "가장 큰 이유는 그것의 ____ 때문이에요.",
                 [["rich flavor", "delicious taste", "unique flavor", "chewy texture",
                   "spicy kick", "fresh ingredients"]]),
                ("In addition, it is ____.",
                 "게다가 그것은 ____해요.",
                 [["fairly nutritious and filling", "easy to make", "good for sharing",
                   "not too expensive", "healthy", "comforting"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [["order pizza when I hang out with friends", "cook it at home",
                   "eat it on special days", "buy it after school", "make it with my family", "have it for lunch"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, good food always ____.",
                 "전반적으로, 맛있는 음식은 항상 ____.",
                 [["makes me happy", "cheers me up", "brings people together",
                   "relieves my stress", "gives me energy", "makes my day better"]]),
            ]),
        ],
        "words": [
            ("cuisine", "요리, (특정)음식 (명)"), ("flavor", "맛, 풍미 (명)"),
            ("ingredient", "재료 (명)"), ("nutritious", "영양가 있는 (형)"),
            ("spicy", "매운 (형)"), ("recipe", "조리법 (명)"),
            ("appetite", "식욕 (명)"), ("homemade", "집에서 만든 (형)"),
            ("balanced diet", "균형 잡힌 식단"), ("prefer", "선호하다 (동)"),
        ],
    },
    {
        "emoji": "🐶", "title_ko": "반려동물", "title_en": "Pets",
        "prompt": "Do you have a pet, or would you like one?",
        "template": [
            _step("① 주제 소개", [
                ("Let me share my thoughts about pets.", "반려동물에 대한 제 생각을 나눌게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, pets are wonderful ____.",
                 "제 생각에 반려동물은 훌륭한 ____예요.",
                 [["companions", "friends", "family members", "healers",
                   "playmates", "parts of the family"]]),
                ("Personally, I would love to have a ____.",
                 "개인적으로 저는 ____을(를) 키우고 싶어요.",
                 [["dog", "cat", "rabbit", "hamster", "parrot", "turtle"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that they are ____.",
                 "가장 큰 이유는 그들이 ____하기 때문이에요.",
                 [["loyal and affectionate", "cute and friendly", "always by my side",
                   "fun to play with", "good listeners", "full of love"]]),
                ("In addition, taking care of a pet teaches ____.",
                 "게다가 반려동물을 돌보는 것은 ____을(를) 가르쳐 줘요.",
                 [["responsibility", "patience", "kindness", "love",
                   "how to care for others", "respect for life"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, a dog will ____.",
                 "예를 들어, 강아지는 ____해요.",
                 [["happily greet you whenever you come home", "play with you for hours",
                   "comfort you when you're sad", "make you laugh", "go for walks with you",
                   "always stay by your side"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, having a pet can make life much more ____.",
                 "전반적으로, 반려동물을 키우는 것은 삶을 훨씬 더 ____하게 만들 수 있어요.",
                 [["joyful", "fun", "warm", "lively", "meaningful", "happy"]]),
            ]),
        ],
        "words": [
            ("companion", "동반자, 친구 (명)"), ("loyal", "충성스러운 (형)"),
            ("affectionate", "애정 어린 (형)"), ("responsibility", "책임 (명)"),
            ("take care of", "~을 돌보다"), ("adopt", "입양하다 (동)"),
            ("obedient", "순종적인 (형)"), ("be attached to", "~에 정들다"),
            ("breed", "품종 (명)"), ("groom", "손질하다 (동)"),
        ],
    },
    {
        "emoji": "🌈", "title_ko": "날씨와 계절", "title_en": "Weather & Seasons",
        "prompt": "Talk about your favorite season.",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about my favorite season.",
                 "제가 가장 좋아하는 계절에 대해 이야기하고 싶어요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most pleasant season.",
                 "제 생각에 ____은(는) 가장 쾌적한 계절이에요.",
                 [["fall", "spring", "summer", "winter", "early summer", "late autumn"]]),
                ("Personally, I prefer ____ weather.",
                 "개인적으로 저는 ____한 날씨를 더 좋아해요.",
                 [["mild", "warm", "cool", "sunny", "dry", "breezy"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that the ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [["temperature is cool and comfortable", "air is fresh and clean",
                   "weather is not too hot or cold", "sky is clear and blue",
                   "scenery is beautiful", "days are pleasant"]]),
                ("In addition, I can ____.",
                 "게다가 저는 ____할 수 있어요.",
                 [["do many outdoor activities", "go hiking", "ride my bike",
                   "take nice walks", "enjoy festivals", "play sports outside"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ I usually ____.",
                 "예를 들어, ____에 저는 보통 ____해요.",
                 [["fall", "spring", "summer", "winter", "autumn", "the holidays"],
                  ["go hiking to enjoy the scenery", "take pictures of the leaves", "go on a picnic",
                   "ride my bike", "travel with my family", "walk in the park"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, the weather really ____.",
                 "전반적으로, 날씨는 정말 ____.",
                 [["affects my mood", "changes how I feel", "decides my plans",
                   "influences my energy", "matters to me", "cheers me up"]]),
            ]),
        ],
        "words": [
            ("climate", "기후 (명)"), ("forecast", "예보 (명)"), ("humid", "습한 (형)"),
            ("chilly", "쌀쌀한 (형)"), ("mild", "온화한 (형)"), ("temperature", "기온 (명)"),
            ("breeze", "산들바람 (명)"), ("pleasant", "쾌적한 (형)"),
            ("gloomy", "우중충한 (형)"), ("affect", "영향을 주다 (동)"),
        ],
    },
    {
        "emoji": "🎬", "title_ko": "영화와 음악", "title_en": "Movies & Music",
        "prompt": "Talk about the movies or music you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the movies and music I enjoy.",
                 "제가 즐기는 영화와 음악에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ movies are the most entertaining.",
                 "제 생각에 ____ 영화가 가장 재미있어요.",
                 [["action", "comedy", "animation", "fantasy", "adventure", "science-fiction"]]),
                ("Personally, I'm a big fan of ____.",
                 "개인적으로 저는 ____의 열렬한 팬이에요.",
                 [["K-pop", "pop", "hip-hop", "ballads", "rock", "movie soundtracks"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that the ____ is really ____.",
                 "가장 큰 이유는 ____이(가) 정말 ____하기 때문이에요.",
                 [["plot", "melody", "story", "rhythm", "acting", "beat"],
                  ["exciting", "touching", "catchy", "impressive", "fun", "powerful"]]),
                ("Also, the ____ match my mood.",
                 "또한, ____이(가) 제 기분과 잘 맞아요.",
                 [["lyrics", "soundtrack", "melody", "songs", "rhythm", "message"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently enjoyed ____, and it was really ____.",
                 "예를 들어, 저는 최근에 ____을(를) 즐겼는데, 정말 ____했어요.",
                 [["a Marvel movie", "a Disney animation", "an IU song", "a K-drama OST",
                   "a new pop song", "a classic film"],
                  ["touching", "exciting", "funny", "impressive", "relaxing", "unforgettable"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, movies and music help me ____.",
                 "전반적으로, 영화와 음악은 제가 ____하도록 도와줘요.",
                 [["relax and recharge", "forget my stress", "feel happy",
                   "escape from reality", "enjoy my free time", "express my feelings"]]),
            ]),
        ],
        "words": [
            ("genre", "장르 (명)"), ("plot", "줄거리 (명)"), ("soundtrack", "사운드트랙 (명)"),
            ("lyrics", "가사 (명)"), ("touching", "감동적인 (형)"), ("catchy", "기억하기 쉬운 (형)"),
            ("talented", "재능 있는 (형)"), ("entertaining", "재미있는 (형)"),
            ("recommend", "추천하다 (동)"), ("release", "개봉/발매하다 (동)"),
        ],
    },
    {
        "emoji": "✈️", "title_ko": "여행과 방학", "title_en": "Travel & Vacation",
        "prompt": "Talk about a trip or how you spend your vacation.",
        "template": [
            _step("① 주제 소개", [
                ("I'd like to talk about how I spend my vacation.",
                 "제가 방학을 어떻게 보내는지 이야기하고 싶어요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, traveling is the best way to spend a vacation.",
                 "제 생각에 여행은 방학을 보내는 가장 좋은 방법이에요.", []),
                ("Personally, I really want to visit ____.",
                 "개인적으로 저는 ____에 정말 가보고 싶어요.",
                 [["Jeju Island", "Busan", "Tokyo", "Paris", "New York", "a quiet countryside"]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that I can ____.",
                 "가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [["experience new cultures and scenery", "try delicious local food",
                   "see famous places", "meet new people", "relax on the beach", "make great memories"]]),
                ("In addition, traveling helps me ____.",
                 "게다가 여행은 제가 ____하도록 도와줘요.",
                 [["broaden my horizons", "relieve stress", "learn about the world",
                   "refresh my mind", "become more independent", "appreciate my home"]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last vacation I ____.",
                 "예를 들어, 지난 방학에 저는 ____했어요.",
                 [["visited the beach and went sightseeing", "traveled with my family",
                   "stayed at my grandparents' house", "went camping in the mountains",
                   "explored a new city", "took lots of photos"]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a good trip is always ____.",
                 "전반적으로, 좋은 여행은 항상 ____.",
                 [["memorable", "exciting", "refreshing", "worth it", "unforgettable", "special"]]),
            ]),
        ],
        "words": [
            ("destination", "목적지 (명)"), ("sightseeing", "관광 (명)"),
            ("scenery", "경치 (명)"), ("accommodation", "숙소 (명)"),
            ("explore", "탐험하다 (동)"), ("memorable", "기억에 남는 (형)"),
            ("itinerary", "여행 일정 (명)"), ("adventure", "모험 (명)"),
            ("broaden one's horizons", "견문을 넓히다"), ("local", "현지의 (형)"),
        ],
    },
]
