# -*- coding: utf-8 -*-
"""
중학생 수준 영어 회화 교재 콘텐츠 (OPIC 주제 기반 · '내 의견 말하기' 템플릿).

가로(landscape) 2단 구성:
  - 왼쪽: 내 의견 말하기 5단계 템플릿. 각 빈칸(____)에 번호 배지(1,2,3…)
  - 오른쪽: 워드뱅크 = 그 빈칸에 넣을 '보기 단어'(영어 + 한글 뜻)를 번호별로 5개 제시

대화문 없음. OPIC 질문을 받고 '내 의견/소개'를 스스로 말하는 연습용.

■ 템플릿 line 형식: (영어문장, 한글해석, [빈칸별 보기목록])
  - 영어문장의 ____ 개수 = 보기목록 개수 (앞 빈칸부터 순서대로 대응)
  - 각 보기목록 = [(영어단어, 한글뜻), ...]  (빈칸당 5개)
  - 빈칸이 없는 문장은 보기목록을 [] 로 둔다
부록의 '단어 사전'은 모든 보기 단어를 자동 수집해 만들어집니다(별도 작성 불필요).
"""

TITLE = "중학 영어 회화 교재"
SUBTITLE = "OPIC 28개 주제로 말하는 나의 의견 · 중학생 수준 · 템플릿 + 워드뱅크"
FOOTER = "중학 영어 회화 교재 · 내 의견 말하기 템플릿 + 워드뱅크"

HOW_TO_USE = [
    ("1. 워드뱅크 보기 익히기", "오른쪽 워드뱅크에서 각 번호에 들어갈 보기 단어와 뜻을 먼저 읽어 봅니다."),
    ("2. 빈칸 채우기", "왼쪽 템플릿의 빈칸 번호에 맞춰, 같은 번호 보기 중 하나를 골라 문장을 완성합니다."),
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
    # ===== UNIT 01 =====
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
                 [[("close", "가까운"), ("caring", "배려심 있는"), ("supportive", "힘이 되는"),
                   ("cheerful", "밝은"), ("loving", "사랑이 많은")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that we ____.",
                 "가장 큰 이유는 우리가 ____하기 때문이에요.",
                 [[("spend a lot of time together", "많은 시간을 함께 보내다"),
                   ("always help each other", "항상 서로 돕다"), ("get along well", "사이좋게 지내다"),
                   ("share everything", "모든 걸 나누다"), ("eat dinner together", "저녁을 함께 먹다")]]),
                ("In addition, my parents always ____.",
                 "게다가 부모님은 항상 저를 ____해 주세요.",
                 [[("support me", "지지하다"), ("believe in me", "믿어주다"),
                   ("listen to me", "말을 들어주다"), ("give me advice", "조언해주다"),
                   ("cheer me up", "응원해주다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, every weekend we ____.",
                 "예를 들어, 주말마다 우리는 ____해요.",
                 [[("watch movies together", "함께 영화를 보다"), ("go for a walk", "산책하러 가다"),
                   ("cook together", "함께 요리하다"), ("visit our grandparents", "조부모님을 뵈러 가다"),
                   ("play board games", "보드게임을 하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I feel lucky to have such a ____ family.",
                 "전반적으로, 저는 이렇게 ____한 가족이 있어 운이 좋다고 느껴요.",
                 [[("supportive", "힘이 되는"), ("caring", "배려심 있는"), ("loving", "사랑이 많은"),
                   ("warm", "따뜻한"), ("wonderful", "멋진")]]),
            ]),
        ],
    },
    # ===== UNIT 02 =====
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
                 [[("cozy", "아늑한"), ("comfortable", "편안한"), ("spacious", "널찍한"),
                   ("warm", "따뜻한"), ("peaceful", "평화로운")]]),
                ("Personally, my favorite space is ____.",
                 "개인적으로 제가 가장 좋아하는 공간은 ____예요.",
                 [[("my own room", "내 방"), ("the living room", "거실"), ("the kitchen", "부엌"),
                   ("the balcony", "발코니"), ("my study", "서재")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [[("I can fully relax there", "거기서 푹 쉴 수 있다"),
                   ("it is quiet and private", "조용하고 개인적이다"), ("it feels comfortable", "편안하다"),
                   ("I can study well there", "공부가 잘 된다"), ("it is full of my things", "내 물건이 가득하다")]]),
                ("In addition, my neighborhood is ____.",
                 "게다가 우리 동네는 ____해요.",
                 [[("quiet and convenient", "조용하고 편리한"), ("safe", "안전한"), ("friendly", "정겨운"),
                   ("clean", "깨끗한"), ("full of parks", "공원이 많은")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, after school I usually ____ there.",
                 "예를 들어, 방과 후에 저는 보통 거기서 ____해요.",
                 [[("relax and listen to music", "쉬면서 음악을 듣다"), ("do my homework", "숙제를 하다"),
                   ("read books", "책을 읽다"), ("take a short nap", "잠깐 낮잠 자다"),
                   ("chat with my family", "가족과 이야기하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, my home is a place where I feel ____.",
                 "전반적으로, 우리 집은 제가 ____하다고 느끼는 곳이에요.",
                 [[("safe and relaxed", "안전하고 편안한"), ("comfortable", "편안한"), ("at peace", "평온한"),
                   ("happy", "행복한"), ("calm", "차분한")]]),
            ]),
        ],
    },
    # ===== UNIT 03 =====
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
                 [[("being with my friends", "친구들과 있는 것"), ("learning new things", "새로운 걸 배우는 것"),
                   ("lunch time", "점심시간"), ("club activities", "동아리 활동"),
                   ("my favorite classes", "좋아하는 수업")]]),
                ("Personally, my favorite subject is ____ because it is ____.",
                 "개인적으로 제가 가장 좋아하는 과목은 ____인데, ____하기 때문이에요.",
                 [[("science", "과학"), ("English", "영어"), ("math", "수학"),
                   ("history", "역사"), ("music", "음악")],
                  [("interesting", "흥미로운"), ("fun", "재미있는"), ("useful", "유용한"),
                   ("easy to understand", "이해하기 쉬운"), ("challenging", "도전적인")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [[("it is fun and challenging", "재미있고 도전적이다"),
                   ("the teacher makes it fun", "선생님이 재밌게 한다"), ("I am good at it", "내가 잘한다"),
                   ("I can use it in real life", "실생활에 쓸 수 있다"), ("it makes me think", "생각하게 한다")]]),
                ("Also, my teacher ____.",
                 "또한, 선생님이 ____해 주세요.",
                 [[("explains things clearly", "명확히 설명한다"), ("is kind and patient", "친절하고 인내심 있다"),
                   ("makes class fun", "수업을 재밌게 한다"), ("always helps us", "늘 도와준다"),
                   ("encourages us", "격려해준다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ class, we often ____.",
                 "예를 들어, ____ 수업에서 우리는 자주 ____해요.",
                 [[("science", "과학"), ("English", "영어"), ("art", "미술"),
                   ("music", "음악"), ("P.E.", "체육")],
                  [("do experiments", "실험을 하다"), ("have discussions", "토론을 하다"),
                   ("play games", "게임을 하다"), ("work on projects", "프로젝트를 하다"),
                   ("watch videos", "영상을 보다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, school life is ____ for me.",
                 "전반적으로, 학교 생활은 저에게 ____해요.",
                 [[("busy but rewarding", "바쁘지만 보람 있는"), ("fun and meaningful", "재미있고 의미 있는"),
                   ("hard but worth it", "힘들지만 가치 있는"), ("full of good memories", "좋은 추억이 가득한"),
                   ("a great experience", "멋진 경험")]]),
            ]),
        ],
    },
    # ===== UNIT 04 =====
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
                 [[("drawing", "그림 그리기"), ("reading", "독서"), ("playing the guitar", "기타 치기"),
                   ("riding a bike", "자전거 타기"), ("taking photos", "사진 찍기")]]),
                ("Personally, I'm really passionate about ____.",
                 "개인적으로 저는 ____에 정말 열정적이에요.",
                 [[("drawing", "그림 그리기"), ("music", "음악"), ("sports", "운동"),
                   ("reading", "독서"), ("photography", "사진")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that it helps me ____.",
                 "가장 큰 이유는 그것이 저를 ____하게 도와주기 때문이에요.",
                 [[("relieve stress", "스트레스를 풀다"), ("forget my worries", "걱정을 잊다"),
                   ("feel refreshed", "상쾌해지다"), ("express myself", "나를 표현하다"),
                   ("focus my mind", "집중하다")]]),
                ("In addition, it makes me feel ____.",
                 "게다가 그것은 저를 ____하게 느끼게 해요.",
                 [[("creative", "창의적인"), ("relaxed", "편안한"), ("confident", "자신감 있는"),
                   ("proud", "뿌듯한"), ("energized", "활력 넘치는")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I usually ____.",
                 "예를 들어, 저는 보통 ____해요.",
                 [[("draw on weekends", "주말에 그림을 그리다"), ("practice every evening", "매일 저녁 연습하다"),
                   ("watch tutorials", "강좌를 보다"), ("do it with friends", "친구들과 하다"),
                   ("try new things", "새로운 걸 시도하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, this hobby makes my life much more ____.",
                 "전반적으로, 이 취미는 제 삶을 훨씬 더 ____하게 만들어요.",
                 [[("enjoyable", "즐거운"), ("colorful", "다채로운"), ("exciting", "신나는"),
                   ("meaningful", "의미 있는"), ("fun", "재미있는")]]),
            ]),
        ],
    },
    # ===== UNIT 05 =====
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
                 [[("soccer", "축구"), ("basketball", "농구"), ("badminton", "배드민턴"),
                   ("swimming", "수영"), ("baseball", "야구")]]),
                ("Personally, I prefer ____ to other sports.",
                 "개인적으로 저는 다른 운동보다 ____을(를) 더 좋아해요.",
                 [[("soccer", "축구"), ("running", "달리기"), ("swimming", "수영"),
                   ("basketball", "농구"), ("cycling", "자전거 타기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that it improves my ____.",
                 "가장 큰 이유는 그것이 제 ____을(를) 향상시키기 때문이에요.",
                 [[("fitness", "체력"), ("health", "건강"), ("strength", "힘"),
                   ("endurance", "지구력"), ("concentration", "집중력")]]),
                ("Also, it teaches me the importance of ____.",
                 "또한, 그것은 저에게 ____의 중요성을 가르쳐 줘요.",
                 [[("teamwork", "팀워크"), ("patience", "인내"), ("effort", "노력"),
                   ("fair play", "정정당당함"), ("never giving up", "포기하지 않기")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I ____.",
                 "예를 들어, 저는 ____해요.",
                 [[("play soccer twice a week", "일주일에 두 번 축구를 하다"),
                   ("go swimming on weekends", "주말에 수영하러 가다"), ("jog every morning", "매일 아침 조깅하다"),
                   ("practice after school", "방과 후 연습하다"), ("work out at the gym", "헬스장에서 운동하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, exercising regularly keeps me ____.",
                 "전반적으로, 규칙적인 운동은 저를 ____하게 유지해 줘요.",
                 [[("healthy and energetic", "건강하고 활기찬"), ("fit", "건강한"), ("refreshed", "상쾌한"),
                   ("in a good mood", "기분 좋은"), ("strong", "튼튼한")]]),
            ]),
        ],
    },
    # ===== UNIT 06 =====
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
                 [[("pizza", "피자"), ("fried chicken", "프라이드치킨"), ("tteokbokki", "떡볶이"),
                   ("sushi", "초밥"), ("pasta", "파스타")]]),
                ("Personally, I prefer ____ food.",
                 "개인적으로 저는 ____한 음식을 더 좋아해요.",
                 [[("spicy", "매운"), ("sweet", "단"), ("salty", "짭짤한"),
                   ("Korean", "한국"), ("homemade", "집에서 만든")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is its ____.",
                 "가장 큰 이유는 그것의 ____ 때문이에요.",
                 [[("rich flavor", "진한 맛"), ("delicious taste", "맛있는 맛"), ("chewy texture", "쫄깃한 식감"),
                   ("spicy kick", "매콤함"), ("fresh ingredients", "신선한 재료")]]),
                ("In addition, it is ____.",
                 "게다가 그것은 ____해요.",
                 [[("nutritious and filling", "영양 있고 든든한"), ("easy to make", "만들기 쉬운"),
                   ("good for sharing", "나눠 먹기 좋은"), ("not expensive", "비싸지 않은"),
                   ("comforting", "위로가 되는")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [[("order pizza with friends", "친구들과 피자를 시키다"), ("cook it at home", "집에서 만들다"),
                   ("eat it on special days", "특별한 날 먹다"), ("buy it after school", "방과 후 사 먹다"),
                   ("make it with my family", "가족과 만들다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, good food always ____.",
                 "전반적으로, 맛있는 음식은 항상 ____.",
                 [[("makes me happy", "나를 행복하게 한다"), ("cheers me up", "기운을 북돋운다"),
                   ("brings people together", "사람들을 모은다"), ("relieves my stress", "스트레스를 풀어준다"),
                   ("gives me energy", "에너지를 준다")]]),
            ]),
        ],
    },
    # ===== UNIT 07 =====
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
                 [[("companions", "친구"), ("family members", "가족"), ("playmates", "놀이 친구"),
                   ("healers", "위로가 되는 존재"), ("friends", "벗")]]),
                ("Personally, I would love to have a ____.",
                 "개인적으로 저는 ____을(를) 키우고 싶어요.",
                 [[("dog", "강아지"), ("cat", "고양이"), ("rabbit", "토끼"),
                   ("hamster", "햄스터"), ("parrot", "앵무새")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that they are ____.",
                 "가장 큰 이유는 그들이 ____하기 때문이에요.",
                 [[("loyal and affectionate", "충성스럽고 다정한"), ("cute and friendly", "귀엽고 친근한"),
                   ("always by my side", "늘 곁에 있는"), ("fun to play with", "놀기 재밌는"),
                   ("full of love", "사랑이 넘치는")]]),
                ("In addition, taking care of a pet teaches ____.",
                 "게다가 반려동물을 돌보는 것은 ____을(를) 가르쳐 줘요.",
                 [[("responsibility", "책임감"), ("patience", "인내심"), ("kindness", "친절함"),
                   ("love", "사랑"), ("respect for life", "생명 존중")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, a dog will ____.",
                 "예를 들어, 강아지는 ____해요.",
                 [[("greet you happily", "반갑게 맞아주다"), ("play with you", "함께 놀아주다"),
                   ("comfort you when sad", "슬플 때 위로해주다"), ("make you laugh", "웃게 해주다"),
                   ("go for walks with you", "함께 산책하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, having a pet can make life much more ____.",
                 "전반적으로, 반려동물을 키우는 것은 삶을 훨씬 더 ____하게 만들 수 있어요.",
                 [[("joyful", "즐거운"), ("fun", "재미있는"), ("warm", "따뜻한"),
                   ("lively", "활기찬"), ("meaningful", "의미 있는")]]),
            ]),
        ],
    },
    # ===== UNIT 08 =====
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
                 [[("fall", "가을"), ("spring", "봄"), ("summer", "여름"),
                   ("winter", "겨울"), ("early summer", "초여름")]]),
                ("Personally, I prefer ____ weather.",
                 "개인적으로 저는 ____한 날씨를 더 좋아해요.",
                 [[("mild", "온화한"), ("warm", "따뜻한"), ("cool", "시원한"),
                   ("sunny", "맑은"), ("dry", "건조한")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [[("the weather is cool and comfortable", "날씨가 시원하고 편안하다"),
                   ("the air is fresh", "공기가 상쾌하다"), ("it is not too hot or cold", "너무 덥지도 춥지도 않다"),
                   ("the sky is clear", "하늘이 맑다"), ("the scenery is beautiful", "경치가 아름답다")]]),
                ("In addition, I can ____.",
                 "게다가 저는 ____할 수 있어요.",
                 [[("do outdoor activities", "야외 활동을 하다"), ("go hiking", "등산을 가다"),
                   ("ride my bike", "자전거를 타다"), ("take nice walks", "산책을 하다"),
                   ("enjoy festivals", "축제를 즐기다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ I usually ____.",
                 "예를 들어, ____에 저는 보통 ____해요.",
                 [[("fall", "가을"), ("spring", "봄"), ("summer", "여름"),
                   ("winter", "겨울"), ("the holidays", "명절")],
                  [("go hiking", "등산을 가다"), ("take pictures", "사진을 찍다"),
                   ("go on a picnic", "소풍을 가다"), ("ride my bike", "자전거를 타다"),
                   ("travel with my family", "가족과 여행하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, the weather really ____.",
                 "전반적으로, 날씨는 정말 ____.",
                 [[("affects my mood", "기분에 영향을 준다"), ("changes how I feel", "감정을 바꾼다"),
                   ("decides my plans", "계획을 정한다"), ("influences my energy", "활력에 영향을 준다"),
                   ("matters to me", "나에게 중요하다")]]),
            ]),
        ],
    },
    # ===== UNIT 09 =====
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
                 [[("action", "액션"), ("comedy", "코미디"), ("animation", "애니메이션"),
                   ("fantasy", "판타지"), ("adventure", "모험")]]),
                ("Personally, I'm a big fan of ____.",
                 "개인적으로 저는 ____의 열렬한 팬이에요.",
                 [[("K-pop", "케이팝"), ("pop", "팝"), ("hip-hop", "힙합"),
                   ("ballads", "발라드"), ("rock", "록")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that the ____ is really ____.",
                 "가장 큰 이유는 ____이(가) 정말 ____하기 때문이에요.",
                 [[("plot", "줄거리"), ("melody", "멜로디"), ("story", "이야기"),
                   ("rhythm", "리듬"), ("acting", "연기")],
                  [("exciting", "흥미진진한"), ("touching", "감동적인"), ("catchy", "중독성 있는"),
                   ("impressive", "인상적인"), ("powerful", "강렬한")]]),
                ("Also, the ____ match my mood.",
                 "또한, ____이(가) 제 기분과 잘 맞아요.",
                 [[("lyrics", "가사"), ("soundtrack", "사운드트랙"), ("melody", "멜로디"),
                   ("songs", "노래"), ("rhythm", "리듬")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently enjoyed ____, and it was really ____.",
                 "예를 들어, 저는 최근에 ____을(를) 즐겼는데, 정말 ____했어요.",
                 [[("a Marvel movie", "마블 영화"), ("a Disney animation", "디즈니 애니메이션"),
                   ("an IU song", "아이유 노래"), ("a K-drama OST", "드라마 OST"), ("a new pop song", "새 팝송")],
                  [("touching", "감동적인"), ("exciting", "신나는"), ("funny", "웃긴"),
                   ("impressive", "인상적인"), ("unforgettable", "잊을 수 없는")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, movies and music help me ____.",
                 "전반적으로, 영화와 음악은 제가 ____하도록 도와줘요.",
                 [[("relax and recharge", "쉬고 재충전하다"), ("forget my stress", "스트레스를 잊다"),
                   ("feel happy", "행복해지다"), ("enjoy my free time", "여가를 즐기다"),
                   ("express my feelings", "감정을 표현하다")]]),
            ]),
        ],
    },
    # ===== UNIT 10 =====
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
                 [[("Jeju Island", "제주도"), ("Busan", "부산"), ("Tokyo", "도쿄"),
                   ("Paris", "파리"), ("New York", "뉴욕")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that I can ____.",
                 "가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("experience new cultures", "새로운 문화를 경험하다"), ("try local food", "현지 음식을 먹다"),
                   ("see famous places", "유명한 곳을 보다"), ("meet new people", "새로운 사람을 만나다"),
                   ("relax on the beach", "해변에서 쉬다")]]),
                ("In addition, traveling helps me ____.",
                 "게다가 여행은 제가 ____하도록 도와줘요.",
                 [[("broaden my horizons", "견문을 넓히다"), ("relieve stress", "스트레스를 풀다"),
                   ("learn about the world", "세상을 배우다"), ("refresh my mind", "마음을 새롭게 하다"),
                   ("become independent", "독립적이 되다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last vacation I ____.",
                 "예를 들어, 지난 방학에 저는 ____했어요.",
                 [[("visited the beach", "해변에 갔다"), ("traveled with my family", "가족과 여행했다"),
                   ("went camping", "캠핑을 갔다"), ("explored a new city", "새 도시를 둘러봤다"),
                   ("took lots of photos", "사진을 많이 찍었다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a good trip is always ____.",
                 "전반적으로, 좋은 여행은 항상 ____.",
                 [[("memorable", "기억에 남는"), ("exciting", "신나는"), ("refreshing", "상쾌한"),
                   ("worth it", "가치 있는"), ("unforgettable", "잊을 수 없는")]]),
            ]),
        ],
    },
    # ===== UNIT 11 =====
    {
        "emoji": "🙋", "title_ko": "자기소개", "title_en": "Self-Introduction",
        "prompt": "Introduce yourself.",
        "template": [
            _step("① 주제 소개", [
                ("Let me introduce myself.", "제 소개를 할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, I am a ____ person.",
                 "제 생각에 저는 ____ 사람이에요.",
                 [[("cheerful", "밝은"), ("friendly", "친근한"), ("curious", "호기심 많은"),
                   ("hard-working", "성실한"), ("positive", "긍정적인")]]),
                ("Personally, I'm interested in ____.",
                 "개인적으로 저는 ____에 관심이 있어요.",
                 [[("music", "음악"), ("sports", "운동"), ("art", "미술"),
                   ("science", "과학"), ("reading", "독서")]]),
            ]),
            _step("③ 이유", [
                ("The main reason people like me is that I am ____.",
                 "사람들이 저를 좋아하는 이유는 제가 ____하기 때문이에요.",
                 [[("kind to everyone", "모두에게 친절한"), ("easy to talk to", "말 붙이기 편한"),
                   ("always honest", "늘 정직한"), ("a good listener", "잘 들어주는"),
                   ("full of energy", "에너지가 넘치는")]]),
                ("In addition, I am good at ____.",
                 "게다가 저는 ____을(를) 잘해요.",
                 [[("making friends", "친구 사귀기"), ("solving problems", "문제 해결"),
                   ("drawing", "그림"), ("playing sports", "운동"), ("singing", "노래")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in my free time I ____.",
                 "예를 들어, 여가 시간에 저는 ____해요.",
                 [[("hang out with friends", "친구들과 놀다"), ("listen to music", "음악을 듣다"),
                   ("play sports", "운동을 하다"), ("read books", "책을 읽다"),
                   ("watch videos", "영상을 보다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I want to become a ____ person.",
                 "전반적으로, 저는 ____ 사람이 되고 싶어요.",
                 [[("confident", "자신감 있는"), ("respected", "존경받는"), ("helpful", "도움이 되는"),
                   ("successful", "성공한"), ("happy", "행복한")]]),
            ]),
        ],
    },
    # ===== UNIT 12 =====
    {
        "emoji": "👫", "title_ko": "친구", "title_en": "Friends",
        "prompt": "Tell me about your best friend.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about my best friend.", "제 가장 친한 친구에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, a good friend should be ____.",
                 "제 생각에 좋은 친구는 ____해야 해요.",
                 [[("honest", "정직한"), ("kind", "친절한"), ("funny", "재미있는"),
                   ("trustworthy", "믿음직한"), ("caring", "배려심 있는")]]),
                ("Personally, my best friend is very ____.",
                 "개인적으로 제 가장 친한 친구는 매우 ____해요.",
                 [[("friendly", "친근한"), ("cheerful", "밝은"), ("thoughtful", "사려 깊은"),
                   ("easygoing", "느긋한"), ("smart", "똑똑한")]]),
            ]),
            _step("③ 이유", [
                ("The main reason we are close is that we ____.",
                 "우리가 친한 가장 큰 이유는 우리가 ____하기 때문이에요.",
                 [[("share the same interests", "같은 관심사를 가지다"), ("understand each other", "서로를 이해하다"),
                   ("always help each other", "늘 서로 돕다"), ("have fun together", "함께 즐겁다"),
                   ("talk about everything", "뭐든 이야기하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, we often ____ together.",
                 "예를 들어, 우리는 자주 함께 ____해요.",
                 [[("play games", "게임을 하다"), ("study", "공부를 하다"), ("go shopping", "쇼핑을 가다"),
                   ("watch movies", "영화를 보다"), ("hang out", "어울려 놀다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a true friend makes my life more ____.",
                 "전반적으로, 진정한 친구는 제 삶을 더 ____하게 만들어요.",
                 [[("enjoyable", "즐거운"), ("meaningful", "의미 있는"), ("fun", "재미있는"),
                   ("colorful", "다채로운"), ("happy", "행복한")]]),
            ]),
        ],
    },
    # ===== UNIT 13 =====
    {
        "emoji": "🛒", "title_ko": "쇼핑", "title_en": "Shopping",
        "prompt": "Talk about your shopping habits.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my shopping habits.", "제 쇼핑 습관에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the best place to shop.",
                 "제 생각에 ____이(가) 쇼핑하기에 가장 좋아요.",
                 [[("the mall", "쇼핑몰"), ("an online store", "온라인 상점"), ("a department store", "백화점"),
                   ("a market", "시장"), ("a convenience store", "편의점")]]),
                ("Personally, I usually shop for ____.",
                 "개인적으로 저는 보통 ____을(를) 사요.",
                 [[("clothes", "옷"), ("shoes", "신발"), ("snacks", "간식"),
                   ("books", "책"), ("games", "게임")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like shopping is that it is ____.",
                 "제가 쇼핑을 좋아하는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("fun and exciting", "재미있고 신나는"), ("a good way to relax", "좋은 휴식"),
                   ("a nice time with friends", "친구와 좋은 시간"), ("easy online", "온라인이라 편한"),
                   ("full of good deals", "좋은 할인이 많은")]]),
                ("In addition, I try to ____.",
                 "게다가 저는 ____하려고 해요.",
                 [[("save my money", "돈을 아끼다"), ("compare prices", "가격을 비교하다"),
                   ("buy only what I need", "필요한 것만 사다"), ("look for discounts", "할인을 찾다"),
                   ("make a shopping list", "쇼핑 목록을 만들다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last weekend I ____.",
                 "예를 들어, 지난 주말에 저는 ____했어요.",
                 [[("bought a new shirt", "새 셔츠를 샀다"), ("went to the mall with friends", "친구들과 몰에 갔다"),
                   ("ordered shoes online", "신발을 온라인 주문했다"), ("got some snacks", "간식을 샀다"),
                   ("just window-shopped", "아이쇼핑만 했다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, shopping is a ____ activity for me.",
                 "전반적으로, 쇼핑은 저에게 ____ 활동이에요.",
                 [[("fun", "재미있는"), ("relaxing", "편안한"), ("exciting", "신나는"),
                   ("useful", "유용한"), ("enjoyable", "즐거운")]]),
            ]),
        ],
    },
    # ===== UNIT 14 =====
    {
        "emoji": "☕", "title_ko": "카페 가기", "title_en": "Going to Cafés",
        "prompt": "Talk about going to cafés.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about going to cafés.", "카페에 가는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, a café is a great place to ____.",
                 "제 생각에 카페는 ____하기에 좋은 장소예요.",
                 [[("relax", "쉬다"), ("meet friends", "친구를 만나다"), ("study", "공부하다"),
                   ("read a book", "책을 읽다"), ("chat", "이야기하다")]]),
                ("Personally, I usually order ____.",
                 "개인적으로 저는 보통 ____을(를) 주문해요.",
                 [[("hot chocolate", "핫초코"), ("a smoothie", "스무디"), ("juice", "주스"),
                   ("lemonade", "레모네이드"), ("iced tea", "아이스티")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like cafés is that they are ____.",
                 "제가 카페를 좋아하는 가장 큰 이유는 그곳이 ____하기 때문이에요.",
                 [[("cozy and quiet", "아늑하고 조용한"), ("good for studying", "공부하기 좋은"),
                   ("a nice place to talk", "대화하기 좋은"), ("comfortable", "편안한"),
                   ("full of nice smells", "좋은 향이 가득한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____ at a café.",
                 "예를 들어, 저는 카페에서 자주 ____해요.",
                 [[("study with friends", "친구들과 공부하다"), ("do my homework", "숙제를 하다"),
                   ("read a book", "책을 읽다"), ("chat for hours", "오래 수다 떨다"),
                   ("take a break", "잠시 쉬다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, going to a café helps me ____.",
                 "전반적으로, 카페에 가는 것은 제가 ____하도록 도와줘요.",
                 [[("relax", "쉬다"), ("feel refreshed", "상쾌해지다"), ("concentrate", "집중하다"),
                   ("spend time with friends", "친구와 시간을 보내다"), ("enjoy my day", "하루를 즐기다")]]),
            ]),
        ],
    },
    # ===== UNIT 15 =====
    {
        "emoji": "🌳", "title_ko": "공원 가기", "title_en": "Going to the Park",
        "prompt": "Talk about going to a park.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about going to the park.", "공원에 가는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the park is the best place to ____.",
                 "제 생각에 공원은 ____하기에 가장 좋은 곳이에요.",
                 [[("relax", "쉬다"), ("exercise", "운동하다"), ("walk", "걷다"),
                   ("meet friends", "친구를 만나다"), ("enjoy nature", "자연을 즐기다")]]),
                ("Personally, I like to ____ at the park.",
                 "개인적으로 저는 공원에서 ____하는 것을 좋아해요.",
                 [[("ride my bike", "자전거를 타다"), ("take a walk", "산책하다"), ("play sports", "운동을 하다"),
                   ("have a picnic", "소풍을 하다"), ("walk my dog", "강아지를 산책시키다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I go there is that it is ____.",
                 "제가 그곳에 가는 가장 큰 이유는 그곳이 ____하기 때문이에요.",
                 [[("peaceful and green", "평화롭고 푸른"), ("good for exercise", "운동하기 좋은"),
                   ("free to enter", "무료인"), ("close to my house", "집에서 가까운"),
                   ("full of fresh air", "공기가 상쾌한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on weekends I usually ____.",
                 "예를 들어, 주말에 저는 보통 ____해요.",
                 [[("jog in the morning", "아침에 조깅하다"), ("ride my bike", "자전거를 타다"),
                   ("have a picnic with family", "가족과 소풍하다"), ("play badminton", "배드민턴을 치다"),
                   ("read on a bench", "벤치에서 책을 읽다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, spending time at the park makes me feel ____.",
                 "전반적으로, 공원에서 시간을 보내면 저는 ____한 기분이 들어요.",
                 [[("refreshed", "상쾌한"), ("relaxed", "편안한"), ("healthy", "건강한"),
                   ("happy", "행복한"), ("calm", "차분한")]]),
            ]),
        ],
    },
    # ===== UNIT 16 =====
    {
        "emoji": "🎤", "title_ko": "콘서트·공연", "title_en": "Concerts & Performances",
        "prompt": "Talk about a concert or performance you enjoyed.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about a performance I enjoyed.", "제가 즐긴 공연에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ concerts are the most exciting.",
                 "제 생각에 ____ 콘서트가 가장 신나요.",
                 [[("K-pop", "케이팝"), ("band", "밴드"), ("classical", "클래식"),
                   ("school", "학교"), ("live", "라이브")]]),
                ("Personally, I love watching ____.",
                 "개인적으로 저는 ____ 보는 것을 정말 좋아해요.",
                 [[("live music", "라이브 음악"), ("my favorite singer", "좋아하는 가수"),
                   ("a school festival", "학교 축제"), ("a dance performance", "댄스 공연"),
                   ("a musical", "뮤지컬")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that the ____ is amazing.",
                 "제가 그것을 즐기는 가장 큰 이유는 ____이(가) 멋지기 때문이에요.",
                 [[("atmosphere", "분위기"), ("music", "음악"), ("energy", "에너지"),
                   ("stage", "무대"), ("crowd", "관객")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I once ____.",
                 "예를 들어, 저는 한번 ____했어요.",
                 [[("went to a K-pop concert", "케이팝 콘서트에 갔다"),
                   ("watched a school performance", "학교 공연을 봤다"), ("saw a live band", "라이브 밴드를 봤다"),
                   ("sang along with everyone", "다 함께 따라 불렀다"), ("enjoyed a festival", "축제를 즐겼다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, live performances make me feel ____.",
                 "전반적으로, 라이브 공연은 저를 ____한 기분이 들게 해요.",
                 [[("excited", "신나는"), ("thrilled", "짜릿한"), ("happy", "행복한"),
                   ("energized", "활력 넘치는"), ("moved", "감동받은")]]),
            ]),
        ],
    },
    # ===== UNIT 17 =====
    {
        "emoji": "⛺", "title_ko": "캠핑", "title_en": "Camping",
        "prompt": "Talk about camping or outdoor activities.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about camping.", "캠핑에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, camping is a great way to ____.",
                 "제 생각에 캠핑은 ____하기에 아주 좋은 방법이에요.",
                 [[("enjoy nature", "자연을 즐기다"), ("relax", "쉬다"),
                   ("spend time with family", "가족과 시간을 보내다"), ("take a break", "휴식하다"),
                   ("have an adventure", "모험을 하다")]]),
                ("Personally, my favorite part of camping is ____.",
                 "개인적으로 캠핑에서 제가 가장 좋아하는 부분은 ____예요.",
                 [[("the campfire", "캠프파이어"), ("cooking outside", "야외에서 요리하기"),
                   ("looking at the stars", "별 보기"), ("sleeping in a tent", "텐트에서 자기"),
                   ("hiking", "등산")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that it is ____.",
                 "제가 그것을 좋아하는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("peaceful and quiet", "평화롭고 조용한"), ("close to nature", "자연과 가까운"),
                   ("a fun adventure", "재미있는 모험"), ("good for family time", "가족 시간에 좋은"),
                   ("refreshing", "상쾌한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last summer I ____.",
                 "예를 들어, 지난여름에 저는 ____했어요.",
                 [[("went camping with my family", "가족과 캠핑을 갔다"),
                   ("cooked food over a fire", "불에 음식을 요리했다"), ("watched the stars", "별을 봤다"),
                   ("went hiking", "등산을 갔다"), ("slept in a tent", "텐트에서 잤다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, camping helps me feel ____.",
                 "전반적으로, 캠핑은 제가 ____한 기분이 들게 해줘요.",
                 [[("refreshed", "상쾌한"), ("relaxed", "편안한"), ("close to nature", "자연과 가까운"),
                   ("happy", "행복한"), ("free", "자유로운")]]),
            ]),
        ],
    },
    # ===== UNIT 18 =====
    {
        "emoji": "🍳", "title_ko": "요리하기", "title_en": "Cooking",
        "prompt": "Talk about cooking.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about cooking.", "요리에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, cooking is a ____ hobby.",
                 "제 생각에 요리는 ____ 취미예요.",
                 [[("fun", "재미있는"), ("useful", "유용한"), ("creative", "창의적인"),
                   ("relaxing", "편안한"), ("rewarding", "보람 있는")]]),
                ("Personally, I like to make ____.",
                 "개인적으로 저는 ____ 만드는 것을 좋아해요.",
                 [[("pasta", "파스타"), ("ramen", "라면"), ("sandwiches", "샌드위치"),
                   ("fried rice", "볶음밥"), ("cookies", "쿠키")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that I can ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("make my own food", "직접 음식을 만들다"), ("try new recipes", "새 조리법을 시도하다"),
                   ("share it with family", "가족과 나누다"), ("be creative", "창의적이 되다"),
                   ("save money", "돈을 아끼다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on weekends I sometimes ____.",
                 "예를 들어, 주말에 저는 가끔 ____해요.",
                 [[("cook dinner for my family", "가족을 위해 저녁을 만들다"), ("bake cookies", "쿠키를 굽다"),
                   ("try a new recipe", "새 조리법을 시도하다"), ("make lunch by myself", "혼자 점심을 만들다"),
                   ("help my mom cook", "엄마 요리를 돕다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, cooking makes me feel ____.",
                 "전반적으로, 요리는 저를 ____한 기분이 들게 해요.",
                 [[("proud", "뿌듯한"), ("happy", "행복한"), ("creative", "창의적인"),
                   ("relaxed", "편안한"), ("confident", "자신감 있는")]]),
            ]),
        ],
    },
    # ===== UNIT 19 =====
    {
        "emoji": "📚", "title_ko": "독서", "title_en": "Reading",
        "prompt": "Talk about reading and books.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about reading.", "독서에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ books are the most interesting.",
                 "제 생각에 ____ 책이 가장 흥미로워요.",
                 [[("fantasy", "판타지"), ("adventure", "모험"), ("comic", "만화"),
                   ("mystery", "추리"), ("science", "과학")]]),
                ("Personally, I usually read ____.",
                 "개인적으로 저는 보통 ____을(를) 읽어요.",
                 [[("novels", "소설"), ("comic books", "만화책"), ("magazines", "잡지"),
                   ("webtoons", "웹툰"), ("short stories", "단편")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like reading is that it ____.",
                 "제가 독서를 좋아하는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("is fun and exciting", "재미있고 신나다"), ("teaches me new things", "새로운 걸 알려주다"),
                   ("sparks my imagination", "상상력을 키우다"), ("helps me relax", "쉬게 해주다"),
                   ("improves my vocabulary", "어휘력을 늘리다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently read ____.",
                 "예를 들어, 저는 최근에 ____을(를) 읽었어요.",
                 [[("a fantasy novel", "판타지 소설"), ("a comic book", "만화책"),
                   ("a famous story", "유명한 이야기"), ("a webtoon", "웹툰"), ("a mystery book", "추리 소설")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, reading makes me more ____.",
                 "전반적으로, 독서는 저를 더 ____하게 만들어요.",
                 [[("thoughtful", "사려 깊은"), ("creative", "창의적인"), ("knowledgeable", "아는 게 많은"),
                   ("imaginative", "상상력이 풍부한"), ("calm", "차분한")]]),
            ]),
        ],
    },
    # ===== UNIT 20 =====
    {
        "emoji": "🎉", "title_ko": "명절과 휴일", "title_en": "Holidays",
        "prompt": "Talk about a holiday you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about a holiday I enjoy.", "제가 즐기는 명절에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the best holiday.",
                 "제 생각에 ____이(가) 가장 좋은 명절이에요.",
                 [[("Chuseok", "추석"), ("Lunar New Year", "설날"), ("Christmas", "크리스마스"),
                   ("my birthday", "내 생일"), ("Children's Day", "어린이날")]]),
                ("Personally, my favorite part is ____.",
                 "개인적으로 제가 가장 좋아하는 부분은 ____예요.",
                 [[("the special food", "특별한 음식"), ("seeing my family", "가족을 만나는 것"),
                   ("getting gifts", "선물 받기"), ("the holiday mood", "명절 분위기"),
                   ("the free time", "여유 시간")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I love it is that I can ____.",
                 "제가 그것을 좋아하는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("spend time with family", "가족과 시간을 보내다"), ("eat delicious food", "맛있는 음식을 먹다"),
                   ("relax at home", "집에서 쉬다"), ("meet my relatives", "친척을 만나다"),
                   ("take a break from school", "학교를 쉬다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on ____ we usually ____.",
                 "예를 들어, ____에 우리는 보통 ____해요.",
                 [[("Chuseok", "추석"), ("New Year's Day", "설날"), ("Christmas", "크리스마스"),
                   ("holidays", "명절"), ("my birthday", "내 생일")],
                  [("eat traditional food", "전통 음식을 먹다"), ("visit our grandparents", "조부모님을 뵙다"),
                   ("play games together", "함께 게임을 하다"), ("share gifts", "선물을 나누다"),
                   ("take family photos", "가족사진을 찍다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, holidays make me feel ____.",
                 "전반적으로, 명절은 저를 ____한 기분이 들게 해요.",
                 [[("happy", "행복한"), ("grateful", "감사한"), ("relaxed", "편안한"),
                   ("excited", "신나는"), ("close to my family", "가족과 가까운")]]),
            ]),
        ],
    },
    # ===== UNIT 21 =====
    {
        "emoji": "🚄", "title_ko": "국내 여행", "title_en": "Domestic Trips",
        "prompt": "Talk about a trip you took in your country.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about a trip I took in Korea.", "제가 국내에서 다녀온 여행에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the best place to visit in Korea.",
                 "제 생각에 ____이(가) 한국에서 가보기 가장 좋은 곳이에요.",
                 [[("Jeju Island", "제주도"), ("Busan", "부산"), ("Gyeongju", "경주"),
                   ("Gangneung", "강릉"), ("Seoul", "서울")]]),
                ("Personally, I love to travel by ____.",
                 "개인적으로 저는 ____(으)로 여행하는 것을 좋아해요.",
                 [[("train", "기차"), ("car", "자동차"), ("bus", "버스"),
                   ("KTX", "고속열차"), ("plane", "비행기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that I can ____.",
                 "가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("enjoy beautiful scenery", "아름다운 경치를 즐기다"), ("try local food", "현지 음식을 먹다"),
                   ("visit famous spots", "유명한 곳을 가다"), ("relax with family", "가족과 쉬다"),
                   ("take great photos", "멋진 사진을 찍다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last year I ____.",
                 "예를 들어, 작년에 저는 ____했어요.",
                 [[("went to Busan by train", "기차로 부산에 갔다"), ("visited Jeju Island", "제주도를 방문했다"),
                   ("traveled with my family", "가족과 여행했다"), ("saw the ocean", "바다를 봤다"),
                   ("tried famous local dishes", "유명한 현지 음식을 먹었다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a domestic trip is a ____ way to spend a holiday.",
                 "전반적으로, 국내 여행은 휴일을 보내는 ____ 방법이에요.",
                 [[("relaxing", "편안한"), ("fun", "재미있는"), ("cheap", "저렴한"),
                   ("convenient", "편리한"), ("memorable", "기억에 남는")]]),
            ]),
        ],
    },
    # ===== UNIT 22 =====
    {
        "emoji": "🌍", "title_ko": "해외 여행", "title_en": "Traveling Abroad",
        "prompt": "Talk about traveling to another country.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about traveling to another country.", "다른 나라로 여행하는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the country I most want to visit.",
                 "제 생각에 ____이(가) 제가 가장 가보고 싶은 나라예요.",
                 [[("Japan", "일본"), ("France", "프랑스"), ("the USA", "미국"),
                   ("Italy", "이탈리아"), ("Australia", "호주")]]),
                ("Personally, I'm most excited about ____.",
                 "개인적으로 저는 ____이(가) 가장 기대돼요.",
                 [[("the food", "음식"), ("the culture", "문화"), ("the sights", "명소"),
                   ("the shopping", "쇼핑"), ("the language", "언어")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that I can ____.",
                 "가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("experience a new culture", "새로운 문화를 경험하다"), ("see famous landmarks", "유명한 명소를 보다"),
                   ("try foreign food", "외국 음식을 먹다"), ("meet new people", "새로운 사람을 만나다"),
                   ("practice English", "영어를 연습하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, someday I want to ____.",
                 "예를 들어, 언젠가 저는 ____하고 싶어요.",
                 [[("visit the Eiffel Tower", "에펠탑을 보다"), ("walk around Tokyo", "도쿄를 거닐다"),
                   ("see New York", "뉴욕을 보다"), ("try local dishes", "현지 음식을 먹다"),
                   ("take lots of photos", "사진을 많이 찍다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, traveling abroad would be an ____ experience.",
                 "전반적으로, 해외여행은 ____ 경험이 될 거예요.",
                 [[("amazing", "놀라운"), ("exciting", "신나는"), ("unforgettable", "잊을 수 없는"),
                   ("eye-opening", "견문을 넓히는"), ("valuable", "값진")]]),
            ]),
        ],
    },
    # ===== UNIT 23 =====
    {
        "emoji": "🎮", "title_ko": "게임하기", "title_en": "Playing Games",
        "prompt": "Talk about playing games.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about playing games.", "게임하는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ games are the most fun.",
                 "제 생각에 ____ 게임이 가장 재미있어요.",
                 [[("mobile", "모바일"), ("computer", "컴퓨터"), ("board", "보드"),
                   ("sports", "스포츠"), ("puzzle", "퍼즐")]]),
                ("Personally, I usually play ____.",
                 "개인적으로 저는 보통 ____ 게임을 해요.",
                 [[("on my phone", "휴대폰으로"), ("with friends", "친구들과"), ("on the computer", "컴퓨터로"),
                   ("after school", "방과 후에"), ("on weekends", "주말에")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that it is ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("fun and exciting", "재미있고 신나는"), ("a good way to relax", "좋은 휴식"),
                   ("great with friends", "친구들과 좋은"), ("challenging", "도전적인"),
                   ("a nice hobby", "좋은 취미")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I sometimes ____.",
                 "예를 들어, 저는 가끔 ____해요.",
                 [[("play games online with friends", "온라인으로 친구들과 게임하다"), ("try new games", "새 게임을 해보다"),
                   ("play for about an hour", "한 시간쯤 놀다"), ("join a team", "팀에 들어가다"),
                   ("watch game videos", "게임 영상을 보다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, playing games in moderation is ____.",
                 "전반적으로, 적당히 하는 게임은 ____.",
                 [[("fun", "재미있는"), ("relaxing", "편안한"), ("a good hobby", "좋은 취미"),
                   ("enjoyable", "즐거운"), ("exciting", "신나는")]]),
            ]),
        ],
    },
    # ===== UNIT 24 =====
    {
        "emoji": "💻", "title_ko": "인터넷·SNS", "title_en": "The Internet & Social Media",
        "prompt": "Talk about how you use the Internet or social media.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I use the Internet.", "제가 인터넷을 어떻게 쓰는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most useful website or app.",
                 "제 생각에 ____이(가) 가장 유용한 사이트나 앱이에요.",
                 [[("YouTube", "유튜브"), ("Instagram", "인스타그램"), ("a search engine", "검색 엔진"),
                   ("a study app", "공부 앱"), ("an online library", "온라인 도서관")]]),
                ("Personally, I use the Internet to ____.",
                 "개인적으로 저는 ____하려고 인터넷을 써요.",
                 [[("watch videos", "영상을 보다"), ("chat with friends", "친구와 대화하다"), ("study", "공부하다"),
                   ("find information", "정보를 찾다"), ("listen to music", "음악을 듣다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason it is helpful is that I can ____.",
                 "그것이 도움이 되는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("learn new things", "새로운 걸 배우다"), ("stay in touch with friends", "친구와 연락하다"),
                   ("find useful information", "유용한 정보를 찾다"), ("have fun", "즐기다"),
                   ("do research", "자료를 찾다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [[("watch study videos", "공부 영상을 보다"), ("message my friends", "친구에게 메시지를 보내다"),
                   ("search for information", "정보를 검색하다"), ("share photos", "사진을 공유하다"),
                   ("read the news", "뉴스를 읽다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I try to use the Internet ____.",
                 "전반적으로, 저는 인터넷을 ____ 쓰려고 해요.",
                 [[("wisely", "현명하게"), ("safely", "안전하게"), ("in moderation", "적당히"),
                   ("carefully", "조심스럽게"), ("responsibly", "책임감 있게")]]),
            ]),
        ],
    },
    # ===== UNIT 25 =====
    {
        "emoji": "📺", "title_ko": "TV·드라마", "title_en": "TV & Dramas",
        "prompt": "Talk about the TV shows or dramas you watch.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the TV shows I watch.", "제가 보는 TV 프로그램에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ shows are the most enjoyable.",
                 "제 생각에 ____ 프로그램이 가장 즐거워요.",
                 [[("drama", "드라마"), ("comedy", "코미디"), ("variety", "예능"),
                   ("documentary", "다큐멘터리"), ("animation", "애니메이션")]]),
                ("Personally, I usually watch TV ____.",
                 "개인적으로 저는 보통 ____ TV를 봐요.",
                 [[("after dinner", "저녁 후에"), ("on weekends", "주말에"), ("with my family", "가족과"),
                   ("before bed", "자기 전에"), ("in my free time", "여가 시간에")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that the ____ is interesting.",
                 "제가 그것을 좋아하는 가장 큰 이유는 ____이(가) 흥미롭기 때문이에요.",
                 [[("story", "이야기"), ("characters", "등장인물"), ("plot", "줄거리"),
                   ("acting", "연기"), ("humor", "유머")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently watched ____.",
                 "예를 들어, 저는 최근에 ____을(를) 봤어요.",
                 [[("a popular drama", "인기 드라마"), ("a funny variety show", "웃긴 예능"),
                   ("an animated series", "애니메이션"), ("a documentary", "다큐멘터리"),
                   ("a Korean drama", "한국 드라마")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, watching TV helps me ____.",
                 "전반적으로, TV를 보는 것은 제가 ____하도록 도와줘요.",
                 [[("relax", "쉬다"), ("have fun", "즐기다"), ("forget my stress", "스트레스를 잊다"),
                   ("spend time with family", "가족과 시간을 보내다"), ("enjoy my evening", "저녁을 즐기다")]]),
            ]),
        ],
    },
    # ===== UNIT 26 =====
    {
        "emoji": "🌊", "title_ko": "해변 가기", "title_en": "Going to the Beach",
        "prompt": "Talk about going to the beach or the sea.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about going to the beach.", "해변에 가는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the beach is the best place to ____.",
                 "제 생각에 해변은 ____하기에 가장 좋은 곳이에요.",
                 [[("relax", "쉬다"), ("swim", "수영하다"), ("play", "놀다"),
                   ("watch the sunset", "노을을 보다"), ("spend summer", "여름을 보내다")]]),
                ("Personally, my favorite thing to do there is ____.",
                 "개인적으로 제가 거기서 가장 좋아하는 것은 ____예요.",
                 [[("swim in the sea", "바다에서 수영하기"), ("build sandcastles", "모래성 쌓기"),
                   ("walk along the shore", "해안 걷기"), ("collect shells", "조개 줍기"),
                   ("take photos", "사진 찍기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I love it is that it is ____.",
                 "제가 그곳을 좋아하는 가장 큰 이유는 그곳이 ____하기 때문이에요.",
                 [[("beautiful and relaxing", "아름답고 편안한"), ("fun in summer", "여름에 재미있는"),
                   ("cool and refreshing", "시원하고 상쾌한"), ("great with friends", "친구와 좋은"),
                   ("full of fresh air", "공기가 상쾌한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last summer I ____.",
                 "예를 들어, 지난여름에 저는 ____했어요.",
                 [[("went to the beach with my family", "가족과 해변에 갔다"), ("swam in the ocean", "바다에서 수영했다"),
                   ("built a sandcastle", "모래성을 만들었다"), ("watched the sunset", "노을을 봤다"),
                   ("played beach games", "해변 게임을 했다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a day at the beach makes me feel ____.",
                 "전반적으로, 해변에서 보내는 하루는 저를 ____한 기분이 들게 해요.",
                 [[("refreshed", "상쾌한"), ("happy", "행복한"), ("relaxed", "편안한"),
                   ("free", "자유로운"), ("energized", "활력 넘치는")]]),
            ]),
        ],
    },
    # ===== UNIT 27 =====
    {
        "emoji": "📷", "title_ko": "사진 찍기", "title_en": "Taking Photos",
        "prompt": "Talk about taking photos.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about taking photos.", "사진 찍는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ photos are the most fun to take.",
                 "제 생각에 ____ 사진이 찍기에 가장 재미있어요.",
                 [[("nature", "자연"), ("food", "음식"), ("travel", "여행"),
                   ("selfie", "셀카"), ("pet", "반려동물")]]),
                ("Personally, I usually take photos with ____.",
                 "개인적으로 저는 보통 ____와(과) 함께 사진을 찍어요.",
                 [[("my phone", "휴대폰"), ("a camera", "카메라"), ("my friends", "친구들"),
                   ("my family", "가족"), ("my pet", "반려동물")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that I can ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("capture special moments", "특별한 순간을 담다"), ("be creative", "창의적이 되다"),
                   ("keep memories", "추억을 간직하다"), ("share them online", "온라인에 공유하다"),
                   ("express myself", "나를 표현하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [[("take photos when I travel", "여행할 때 사진을 찍다"), ("photograph my food", "음식을 찍다"),
                   ("take selfies with friends", "친구들과 셀카를 찍다"), ("post pictures online", "사진을 온라인에 올리다"),
                   ("save happy moments", "행복한 순간을 저장하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, taking photos helps me ____.",
                 "전반적으로, 사진을 찍는 것은 제가 ____하도록 도와줘요.",
                 [[("keep good memories", "좋은 추억을 남기다"), ("enjoy the moment", "순간을 즐기다"),
                   ("be creative", "창의적이 되다"), ("share my life", "내 삶을 나누다"),
                   ("remember special days", "특별한 날을 기억하다")]]),
            ]),
        ],
    },
    # ===== UNIT 28 =====
    {
        "emoji": "🏢", "title_ko": "우리 동네", "title_en": "My Neighborhood",
        "prompt": "Describe your neighborhood.",
        "template": [
            _step("① 주제 소개", [
                ("Let me describe my neighborhood.", "우리 동네를 소개할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, my neighborhood is very ____.",
                 "제 생각에 우리 동네는 매우 ____해요.",
                 [[("convenient", "편리한"), ("quiet", "조용한"), ("safe", "안전한"),
                   ("friendly", "정겨운"), ("clean", "깨끗한")]]),
                ("Personally, my favorite place nearby is ____.",
                 "개인적으로 제가 가장 좋아하는 근처 장소는 ____예요.",
                 [[("the park", "공원"), ("the library", "도서관"), ("a café", "카페"),
                   ("the shopping center", "쇼핑센터"), ("the sports center", "체육관")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that ____.",
                 "제가 그곳을 좋아하는 가장 큰 이유는 ____이기 때문이에요.",
                 [[("everything is close by", "모든 게 가깝다"), ("it is safe and quiet", "안전하고 조용하다"),
                   ("there are many parks", "공원이 많다"), ("the people are friendly", "사람들이 친절하다"),
                   ("it has good restaurants", "좋은 식당이 있다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____ in my neighborhood.",
                 "예를 들어, 저는 동네에서 자주 ____해요.",
                 [[("walk to the park", "공원까지 걷다"), ("meet friends", "친구를 만나다"),
                   ("ride my bike", "자전거를 타다"), ("go shopping", "쇼핑을 가다"),
                   ("study at the library", "도서관에서 공부하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I really like living in my ____ neighborhood.",
                 "전반적으로, 저는 우리 ____ 동네에 사는 것이 정말 좋아요.",
                 [[("convenient", "편리한"), ("peaceful", "평화로운"), ("friendly", "정겨운"),
                   ("safe", "안전한"), ("nice", "좋은")]]),
            ]),
        ],
    },
]
