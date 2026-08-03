# -*- coding: utf-8 -*-
"""
난이도 중상(중3 수준) 영어 회화 교재 콘텐츠 (OPIC 주제 기반 · '내 의견 말하기').

'난이도 중'(중학)과 '난이도 상'(성인) 사이의 중간 단계입니다.
문장을 조금 더 길게(because/so/even when 등 연결), 어휘도 한 단계 올렸습니다.

■ line 형식: (영어문장, 한글해석, [빈칸별 [(영어, 뜻), ...]])
"""

TITLE = "OPIC 회화 교재 · 난이도 중상"
SUBTITLE = "OPIC 28개 주제로 말하는 나의 의견 · 난이도 중상(중3 수준) · 템플릿 + 워드뱅크"
FOOTER = "OPIC 회화 교재 · 난이도 중상"
KICKER = "OPIC SPEAKING · 난이도 중상 (중3 · UPPER-INTERMEDIATE)"

HOW_TO_USE = [
    ("1. 워드뱅크 보기 익히기", "오른쪽 워드뱅크에서 각 번호에 들어갈 보기 단어·표현과 뜻을 먼저 확인합니다."),
    ("2. 빈칸 채우기", "왼쪽 템플릿의 빈칸 번호에 맞춰 같은 번호 보기 중 하나를 골라 문장을 완성합니다."),
    ("3. 소리 내어 말하기", "①~⑤ 문장을 자연스럽게 이어 한 편의 '내 의견'으로 40초~1분간 말해 봅니다."),
    ("4. 확장하기", "보기에 없는 나만의 표현으로 바꾸고 연결어로 문장을 늘리면 완성도가 올라갑니다."),
]

STEPS_GUIDE = [
    ("① 주제 소개", "무엇에 대해 말할지 자연스럽게 열기"),
    ("② 내 의견·선호", "내 생각/선호를 한 문장으로 제시"),
    ("③ 이유", "그렇게 생각하는 이유 1~2가지"),
    ("④ 예시·경험", "구체적인 예나 내 경험 들기"),
    ("⑤ 마무리", "핵심을 다시 정리하며 마무리"),
]

EXPRESSIONS = [
    ("의견 제시", [
        ("In my opinion, ~", "제 생각에는 ~"),
        ("Personally, I think (that) ~", "개인적으로 저는 ~라고 생각해요"),
        ("What I like most is ~", "제가 가장 좋아하는 것은 ~"),
        ("I'd say (that) ~", "~라고 말하고 싶어요"),
    ]),
    ("선호 표현", [
        ("I prefer A to B", "저는 B보다 A를 더 좋아해요"),
        ("I'm really into ~", "저는 ~에 푹 빠져 있어요"),
        ("I'm a big fan of ~", "저는 ~의 열렬한 팬이에요"),
        ("I've been into ~ lately", "요즘 ~에 빠져 있어요"),
    ]),
    ("이유·연결", [
        ("The main reason is that ~", "가장 큰 이유는 ~이기 때문이에요"),
        ("This is because ~ / because ~", "이는 ~때문이에요"),
        ("In addition, ~ / Also, ~", "게다가 ~ / 또한 ~"),
        ("even when ~ / even though ~", "~할 때조차 / 비록 ~이지만"),
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
    # ===== 01 =====
    {
        "emoji": "👪", "title_ko": "나와 가족", "title_en": "Me & My Family",
        "prompt": "Tell me about your family.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you a little about my family.", "제 가족에 대해 조금 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, family matters the most because they ____.",
                 "제 생각에 가족은 ____하기 때문에 가장 중요해요.",
                 [[("always support me", "늘 나를 지지한다"), ("know me best", "나를 가장 잘 안다"),
                   ("stand by me", "내 곁을 지킨다"), ("cheer me up", "기운을 북돋운다"),
                   ("accept me as I am", "있는 그대로 받아준다")]]),
                ("Personally, I'd describe my family as ____.",
                 "개인적으로 저는 우리 가족을 ____하다고 표현하고 싶어요.",
                 [[("close-knit", "사이가 돈독한"), ("easygoing", "느긋한"), ("supportive", "힘이 되는"),
                   ("cheerful", "밝은"), ("warm-hearted", "마음이 따뜻한")]]),
            ]),
            _step("③ 이유", [
                ("The main reason we get along is that we ____.",
                 "우리가 잘 지내는 가장 큰 이유는 우리가 ____하기 때문이에요.",
                 [[("make time for each other", "서로 시간을 낸다"), ("talk about everything", "뭐든 이야기한다"),
                   ("help each other out", "서로 돕는다"), ("respect one another", "서로 존중한다"),
                   ("share our feelings", "감정을 나눈다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, whenever I have a hard time, my parents ____.",
                 "예를 들어, 제가 힘들 때면 부모님은 ____해요.",
                 [[("listen carefully", "귀 기울여 들어준다"), ("give me honest advice", "솔직한 조언을 준다"),
                   ("encourage me", "격려해준다"), ("calm me down", "진정시켜준다"),
                   ("support my choice", "내 선택을 지지한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, I feel grateful to have such a ____ family.",
                 "결국, 저는 이렇게 ____한 가족이 있어 감사해요.",
                 [[("caring", "배려심 있는"), ("supportive", "힘이 되는"), ("warm", "따뜻한"),
                   ("loving", "사랑이 많은"), ("reliable", "든든한")]]),
            ]),
        ],
    },
    # ===== 02 =====
    {
        "emoji": "🏠", "title_ko": "우리 집", "title_en": "My Home",
        "prompt": "Describe the place where you live.",
        "template": [
            _step("① 주제 소개", [
                ("Let me describe the place where I live.", "제가 사는 곳을 소개할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, my home is the most ____ place for me.",
                 "제 생각에 우리 집은 제게 가장 ____한 곳이에요.",
                 [[("comfortable", "편안한"), ("relaxing", "편히 쉴 수 있는"), ("peaceful", "평화로운"),
                   ("familiar", "익숙한"), ("special", "특별한")]]),
                ("What I like most about it is ____.",
                 "제가 가장 좋아하는 점은 ____예요.",
                 [[("my own room", "내 방"), ("the cozy atmosphere", "아늑한 분위기"),
                   ("the quiet mood", "조용한 분위기"), ("spending time with family", "가족과 보내는 시간"),
                   ("how comfortable it feels", "편안한 느낌")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [[("I can fully relax there", "거기서 푹 쉴 수 있다"), ("it feels safe and warm", "안전하고 따뜻하다"),
                   ("everything I need is there", "필요한 게 다 있다"), ("I can be myself", "나답게 있을 수 있다"),
                   ("it is close to school", "학교에서 가깝다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, after a busy day, I usually ____ at home.",
                 "예를 들어, 바쁜 하루가 끝나면 저는 보통 집에서 ____해요.",
                 [[("relax and listen to music", "쉬며 음악을 듣는다"), ("chat with my family", "가족과 이야기한다"),
                   ("watch something fun", "재미있는 걸 본다"), ("take a rest", "쉰다"),
                   ("do my own thing", "내 일을 한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, my home is a place where I truly feel ____.",
                 "전반적으로, 우리 집은 제가 진짜 ____하다고 느끼는 곳이에요.",
                 [[("relaxed", "편안한"), ("comfortable", "편안한"), ("safe", "안전한"),
                   ("at peace", "평온한"), ("happy", "행복한")]]),
            ]),
        ],
    },
    # ===== 03 =====
    {
        "emoji": "🏫", "title_ko": "학교 생활", "title_en": "My School Life",
        "prompt": "Talk about your school life.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my school life.", "제 학교 생활에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the best thing about school is ____.",
                 "제 생각에 학교에서 가장 좋은 점은 ____예요.",
                 [[("hanging out with friends", "친구들과 어울리는 것"), ("learning new things", "새로운 걸 배우는 것"),
                   ("club activities", "동아리 활동"), ("my favorite subjects", "좋아하는 과목"),
                   ("school events", "학교 행사")]]),
                ("Personally, my favorite subject is ____ because it is ____.",
                 "개인적으로 제가 가장 좋아하는 과목은 ____인데, ____하기 때문이에요.",
                 [[("science", "과학"), ("English", "영어"), ("history", "역사"),
                   ("math", "수학"), ("art", "미술")],
                  [("interesting", "흥미로운"), ("useful in real life", "실생활에 유용한"),
                   ("easy to follow", "따라가기 쉬운"), ("challenging in a good way", "적당히 도전적인"),
                   ("taught in a fun way", "재미있게 배우는")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 ____이기 때문이에요.",
                 [[("the teacher explains it well", "선생님이 잘 설명한다"), ("I can join in actively", "적극적으로 참여할 수 있다"),
                   ("we do hands-on activities", "직접 해보는 활동을 한다"), ("it makes me curious", "호기심을 자극한다"),
                   ("I feel I'm improving", "실력이 는다고 느낀다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ class, we often ____.",
                 "예를 들어, ____ 수업에서 우리는 자주 ____해요.",
                 [[("science", "과학"), ("English", "영어"), ("art", "미술"),
                   ("P.E.", "체육"), ("music", "음악")],
                  [("do experiments", "실험을 한다"), ("have group discussions", "조별 토론을 한다"),
                   ("work on projects", "프로젝트를 한다"), ("present our ideas", "생각을 발표한다"),
                   ("play learning games", "학습 게임을 한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, school life is ____ for me.",
                 "전반적으로, 학교 생활은 저에게 ____해요.",
                 [[("busy but rewarding", "바쁘지만 보람 있는"), ("full of good memories", "좋은 추억이 많은"),
                   ("sometimes tough but fun", "힘들지만 재미있는"), ("a valuable experience", "값진 경험"),
                   ("better than I expected", "기대보다 좋은")]]),
            ]),
        ],
    },
    # ===== 04 =====
    {
        "emoji": "🎨", "title_ko": "취미", "title_en": "My Hobbies",
        "prompt": "What do you like to do in your free time?",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about what I do in my free time.", "제가 여가에 하는 일을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is a great way to spend my free time.",
                 "제 생각에 ____은(는) 여가를 보내기에 아주 좋은 방법이에요.",
                 [[("drawing", "그림 그리기"), ("reading", "독서"), ("playing the guitar", "기타 치기"),
                   ("taking photos", "사진 찍기"), ("working out", "운동")]]),
                ("Personally, I've been really into ____ these days.",
                 "개인적으로 저는 요즘 ____에 푹 빠져 있어요.",
                 [[("sketching", "스케치"), ("listening to music", "음악 감상"), ("watching movies", "영화 보기"),
                   ("baking", "베이킹"), ("collecting things", "수집")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that it helps me ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 그것이 제가 ____하도록 돕기 때문이에요.",
                 [[("relieve stress", "스트레스를 푼다"), ("express myself", "나를 표현한다"),
                   ("forget my worries", "걱정을 잊는다"), ("focus better", "더 집중한다"),
                   ("feel refreshed", "상쾌해진다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on weekends I usually ____.",
                 "예를 들어, 주말에 저는 보통 ____해요.",
                 [[("spend hours on it", "몇 시간씩 몰두한다"), ("practice by myself", "혼자 연습한다"),
                   ("watch tutorials", "강좌를 본다"), ("do it with friends", "친구들과 한다"),
                   ("try new things", "새로운 걸 시도한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, this hobby makes my life more ____.",
                 "전반적으로, 이 취미는 제 삶을 더 ____하게 만들어요.",
                 [[("enjoyable", "즐거운"), ("colorful", "다채로운"), ("meaningful", "의미 있는"),
                   ("balanced", "균형 잡힌"), ("exciting", "신나는")]]),
            ]),
        ],
    },
    # ===== 05 =====
    {
        "emoji": "⚽", "title_ko": "운동", "title_en": "Sports & Exercise",
        "prompt": "Tell me about a sport or exercise you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about a sport I enjoy.", "제가 즐기는 운동에 대해 말할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most exciting sport to play.",
                 "제 생각에 ____이(가) 하기에 가장 신나는 운동이에요.",
                 [[("soccer", "축구"), ("basketball", "농구"), ("badminton", "배드민턴"),
                   ("swimming", "수영"), ("table tennis", "탁구")]]),
                ("Personally, I prefer ____ to watching sports on TV.",
                 "개인적으로 저는 TV로 스포츠를 보는 것보다 ____을(를) 더 좋아해요.",
                 [[("playing myself", "직접 하는 것"), ("exercising outdoors", "야외 운동"),
                   ("team sports", "팀 운동"), ("working out", "운동하는 것"), ("being active", "활동적으로 지내는 것")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that it ____.",
                 "제가 그것을 좋아하는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("keeps me healthy", "건강을 지켜준다"), ("builds my stamina", "체력을 길러준다"),
                   ("relieves stress", "스트레스를 풀어준다"), ("teaches teamwork", "협동심을 길러준다"),
                   ("boosts my mood", "기분을 좋게 한다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I usually ____.",
                 "예를 들어, 저는 보통 ____해요.",
                 [[("play soccer twice a week", "주 2회 축구를 한다"), ("go swimming on weekends", "주말에 수영한다"),
                   ("jog in the morning", "아침에 조깅한다"), ("practice with my club", "동아리와 연습한다"),
                   ("exercise after school", "방과 후 운동한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, playing sports keeps me ____.",
                 "전반적으로, 운동은 저를 ____하게 유지해 줘요.",
                 [[("healthy and active", "건강하고 활동적인"), ("energetic", "활기찬"), ("in good shape", "건강한"),
                   ("positive", "긍정적인"), ("refreshed", "상쾌한")]]),
            ]),
        ],
    },
    # ===== 06 =====
    {
        "emoji": "🍚", "title_ko": "음식", "title_en": "Food & Meals",
        "prompt": "Talk about your favorite food.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my favorite food.", "제가 가장 좋아하는 음식을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most delicious food.",
                 "제 생각에 ____이(가) 가장 맛있는 음식이에요.",
                 [[("pizza", "피자"), ("fried chicken", "치킨"), ("tteokbokki", "떡볶이"),
                   ("sushi", "초밥"), ("bibimbap", "비빔밥")]]),
                ("Personally, I tend to prefer ____ food.",
                 "개인적으로 저는 ____ 음식을 선호하는 편이에요.",
                 [[("spicy", "매운"), ("savory", "감칠맛 나는"), ("sweet", "단"),
                   ("home-cooked", "집에서 만든"), ("healthy", "건강한")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I love it is its ____.",
                 "제가 그것을 좋아하는 가장 큰 이유는 그것의 ____ 때문이에요.",
                 [[("rich flavor", "진한 맛"), ("unique taste", "독특한 맛"), ("chewy texture", "쫄깃한 식감"),
                   ("spicy kick", "매콤함"), ("fresh ingredients", "신선한 재료")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [[("eat it with friends", "친구들과 먹는다"), ("cook it at home", "집에서 만든다"),
                   ("order it on weekends", "주말에 시킨다"), ("have it as a treat", "특별식으로 먹는다"),
                   ("make it with my family", "가족과 만든다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, good food always ____.",
                 "전반적으로, 맛있는 음식은 항상 ____.",
                 [[("cheers me up", "기운을 북돋운다"), ("makes my day better", "하루를 좋게 만든다"),
                   ("brings people together", "사람들을 모은다"), ("relieves my stress", "스트레스를 풀어준다"),
                   ("puts me in a good mood", "기분을 좋게 한다")]]),
            ]),
        ],
    },
    # ===== 07 =====
    {
        "emoji": "🐶", "title_ko": "반려동물", "title_en": "Pets",
        "prompt": "Do you have a pet, or would you like one?",
        "template": [
            _step("① 주제 소개", [
                ("Let me share my thoughts about pets.", "반려동물에 대한 제 생각을 나눌게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, pets are more than just animals; they are ____.",
                 "제 생각에 반려동물은 단순한 동물 이상이에요; 그들은 ____예요.",
                 [[("true companions", "진정한 친구"), ("part of the family", "가족의 일원"),
                   ("loyal friends", "충직한 친구"), ("a great comfort", "큰 위안"),
                   ("everyday buddies", "일상의 벗")]]),
                ("Personally, I would love to have a ____.",
                 "개인적으로 저는 ____을(를) 키우고 싶어요.",
                 [[("dog", "강아지"), ("cat", "고양이"), ("rabbit", "토끼"),
                   ("hamster", "햄스터"), ("small dog", "소형견")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that they ____.",
                 "가장 큰 이유는 그들이 ____하기 때문이에요.",
                 [[("are loyal and loving", "충직하고 다정하다"), ("always comfort me", "늘 위로해준다"),
                   ("make me smile", "웃게 해준다"), ("are fun to be with", "함께 있으면 즐겁다"),
                   ("never judge me", "나를 판단하지 않는다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, a dog will ____ no matter what.",
                 "예를 들어, 강아지는 무슨 일이 있어도 ____해요.",
                 [[("greet you happily", "반갑게 맞아준다"), ("stay by your side", "곁을 지킨다"),
                   ("cheer you up", "기운을 북돋운다"), ("wait for you all day", "하루 종일 기다린다"),
                   ("love you no matter what", "무조건 사랑한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, having a pet can make life much more ____.",
                 "전반적으로, 반려동물을 키우면 삶이 훨씬 더 ____해질 수 있어요.",
                 [[("joyful", "즐거운"), ("warm", "따뜻한"), ("meaningful", "의미 있는"),
                   ("lively", "활기찬"), ("fulfilling", "충족되는")]]),
            ]),
        ],
    },
    # ===== 08 =====
    {
        "emoji": "🌈", "title_ko": "날씨와 계절", "title_en": "Weather & Seasons",
        "prompt": "Talk about your favorite season.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my favorite season.", "제가 가장 좋아하는 계절을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most pleasant season.",
                 "제 생각에 ____이(가) 가장 쾌적한 계절이에요.",
                 [[("fall", "가을"), ("spring", "봄"), ("early summer", "초여름"),
                   ("winter", "겨울"), ("late autumn", "늦가을")]]),
                ("Personally, I prefer ____ weather to hot, humid days.",
                 "개인적으로 저는 덥고 습한 날보다 ____ 날씨를 좋아해요.",
                 [[("cool and dry", "시원하고 건조한"), ("mild", "온화한"), ("crisp", "상쾌한"),
                   ("breezy", "산들바람 부는"), ("sunny", "맑은")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [[("the weather is perfect for going out", "외출하기 딱 좋다"),
                   ("the scenery is beautiful", "경치가 아름답다"),
                   ("it is neither too hot nor too cold", "너무 덥지도 춥지도 않다"),
                   ("the air feels fresh", "공기가 상쾌하다"), ("it puts me in a good mood", "기분이 좋아진다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in ____ I love to ____.",
                 "예를 들어, ____에 저는 ____하는 걸 좋아해요.",
                 [[("fall", "가을"), ("spring", "봄"), ("summer", "여름"),
                   ("winter", "겨울"), ("vacation", "방학")],
                  [("go hiking", "등산을 간다"), ("take walks in the park", "공원을 산책한다"),
                   ("go on a picnic", "소풍을 간다"), ("travel with my family", "가족과 여행한다"),
                   ("take photos of the scenery", "경치 사진을 찍는다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, the weather really ____.",
                 "전반적으로, 날씨는 정말 ____.",
                 [[("affects my mood", "기분에 영향을 준다"), ("shapes my plans", "계획을 좌우한다"),
                   ("changes how I feel", "감정을 바꾼다"), ("matters to me", "나에게 중요하다"),
                   ("decides what I do", "무엇을 할지 정한다")]]),
            ]),
        ],
    },
    # ===== 09 =====
    {
        "emoji": "🎬", "title_ko": "영화와 음악", "title_en": "Movies & Music",
        "prompt": "Talk about the movies or music you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the movies and music I enjoy.", "제가 즐기는 영화와 음악을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ movies are the most entertaining.",
                 "제 생각에 ____ 영화가 가장 재미있어요.",
                 [[("action", "액션"), ("comedy", "코미디"), ("animation", "애니메이션"),
                   ("fantasy", "판타지"), ("thriller", "스릴러")]]),
                ("Personally, I'm a big fan of ____.",
                 "개인적으로 저는 ____의 열렬한 팬이에요.",
                 [[("K-pop", "케이팝"), ("pop", "팝"), ("hip-hop", "힙합"),
                   ("ballads", "발라드"), ("movie soundtracks", "영화 OST")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like them is that the ____ is really ____.",
                 "제가 그것들을 좋아하는 가장 큰 이유는 ____이(가) 정말 ____하기 때문이에요.",
                 [[("story", "이야기"), ("soundtrack", "음악"), ("acting", "연기"),
                   ("plot", "줄거리"), ("melody", "멜로디")],
                  [("touching", "감동적인"), ("exciting", "흥미진진한"), ("impressive", "인상적인"),
                   ("catchy", "중독성 있는"), ("powerful", "강렬한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently enjoyed ____, and I couldn't stop ____.",
                 "예를 들어, 저는 최근에 ____을(를) 즐겼는데, ____을(를) 멈출 수 없었어요.",
                 [[("a new action film", "새 액션 영화"), ("a popular drama", "인기 드라마"),
                   ("an IU song", "아이유 노래"), ("a Marvel movie", "마블 영화"), ("a hit song", "인기곡")],
                  [("watching it", "보는 것"), ("talking about it", "이야기하는 것"),
                   ("listening to it", "듣는 것"), ("recommending it", "추천하는 것"),
                   ("thinking about it", "생각하는 것")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, movies and music help me ____.",
                 "전반적으로, 영화와 음악은 제가 ____하도록 도와줘요.",
                 [[("relax and recharge", "쉬며 재충전한다"), ("forget my stress", "스트레스를 잊는다"),
                   ("enjoy my free time", "여가를 즐긴다"), ("express my feelings", "감정을 표현한다"),
                   ("escape for a while", "잠시 벗어난다")]]),
            ]),
        ],
    },
    # ===== 10 =====
    {
        "emoji": "✈️", "title_ko": "여행과 방학", "title_en": "Travel & Vacation",
        "prompt": "Talk about a trip or how you spend your vacation.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I spend my vacation.", "제가 방학을 어떻게 보내는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, traveling is one of the best ways to spend a vacation because it ____.",
                 "제 생각에 여행은 ____하기 때문에 방학을 보내는 가장 좋은 방법 중 하나예요.",
                 [[("refreshes my mind", "마음을 새롭게 한다"), ("broadens my view", "시야를 넓혀준다"),
                   ("creates good memories", "좋은 추억을 만든다"), ("breaks my routine", "일상을 벗어나게 한다"),
                   ("teaches me a lot", "많은 걸 알려준다")]]),
                ("Personally, I really want to visit ____.",
                 "개인적으로 저는 ____에 정말 가보고 싶어요.",
                 [[("Jeju Island", "제주도"), ("Busan", "부산"), ("Tokyo", "도쿄"),
                   ("Europe", "유럽"), ("a quiet countryside", "조용한 시골")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that I can ____.",
                 "가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("experience new cultures", "새로운 문화를 경험한다"), ("try local food", "현지 음식을 먹는다"),
                   ("see famous places", "유명한 곳을 본다"), ("relax far from home", "집을 떠나 쉰다"),
                   ("make unforgettable memories", "잊지 못할 추억을 만든다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last vacation I ____.",
                 "예를 들어, 지난 방학에 저는 ____했어요.",
                 [[("traveled with my family", "가족과 여행했다"), ("visited the beach", "해변에 갔다"),
                   ("explored a new city", "새 도시를 둘러봤다"), ("went camping", "캠핑을 갔다"),
                   ("took lots of photos", "사진을 많이 찍었다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a good trip is always ____.",
                 "전반적으로, 좋은 여행은 항상 ____.",
                 [[("memorable", "기억에 남는"), ("refreshing", "상쾌한"), ("worth it", "가치 있는"),
                   ("exciting", "신나는"), ("unforgettable", "잊지 못할")]]),
            ]),
        ],
    },
    # ===== 11 =====
    {
        "emoji": "🙋", "title_ko": "자기소개", "title_en": "Self-Introduction",
        "prompt": "Introduce yourself.",
        "template": [
            _step("① 주제 소개", [
                ("Let me introduce myself.", "제 소개를 할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("To start with, I'd describe myself as a(n) ____ person.",
                 "우선, 저는 스스로를 ____ 사람이라고 표현하고 싶어요.",
                 [[("outgoing", "외향적인"), ("easygoing", "느긋한"), ("curious", "호기심 많은"),
                   ("hard-working", "성실한"), ("positive", "긍정적인")]]),
                ("Personally, I'm really interested in ____.",
                 "개인적으로 저는 ____에 정말 관심이 있어요.",
                 [[("music", "음악"), ("sports", "운동"), ("science", "과학"),
                   ("drawing", "그림"), ("languages", "언어")]]),
            ]),
            _step("③ 이유", [
                ("One thing that describes me well is that I ____.",
                 "저를 잘 나타내는 한 가지는 제가 ____한다는 거예요.",
                 [[("get along with almost anyone", "거의 누구와도 잘 지낸다"), ("try my best at everything", "무엇이든 최선을 다한다"),
                   ("love learning new things", "새로운 걸 배우길 좋아한다"), ("listen to others carefully", "남의 말을 잘 듣는다"),
                   ("stay positive", "긍정적으로 지낸다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, in my free time I usually ____.",
                 "예를 들어, 여가 시간에 저는 보통 ____해요.",
                 [[("hang out with friends", "친구들과 논다"), ("play sports", "운동을 한다"),
                   ("listen to music", "음악을 듣는다"), ("read or draw", "읽거나 그린다"),
                   ("watch videos", "영상을 본다")]]),
            ]),
            _step("⑤ 마무리", [
                ("In the future, I hope to become a ____ person.",
                 "앞으로 저는 ____ 사람이 되고 싶어요.",
                 [[("confident", "자신감 있는"), ("helpful", "도움이 되는"), ("respected", "존경받는"),
                   ("well-rounded", "다재다능한"), ("happy", "행복한")]]),
            ]),
        ],
    },
    # ===== 12 =====
    {
        "emoji": "👫", "title_ko": "친구", "title_en": "Friends",
        "prompt": "Tell me about your best friend.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about my best friend.", "제 가장 친한 친구를 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, a good friend should be ____ above all.",
                 "제 생각에 좋은 친구는 무엇보다 ____해야 해요.",
                 [[("honest", "정직한"), ("trustworthy", "믿음직한"), ("kind", "친절한"),
                   ("understanding", "이해심 있는"), ("loyal", "의리 있는")]]),
                ("Personally, my best friend is really ____.",
                 "개인적으로 제 가장 친한 친구는 정말 ____해요.",
                 [[("friendly", "친근한"), ("funny", "웃긴"), ("thoughtful", "사려 깊은"),
                   ("easygoing", "느긋한"), ("dependable", "믿음직한")]]),
            ]),
            _step("③ 이유", [
                ("The main reason we are close is that we ____.",
                 "우리가 친한 가장 큰 이유는 우리가 ____하기 때문이에요.",
                 [[("understand each other", "서로를 이해한다"), ("share the same interests", "관심사가 같다"),
                   ("always have fun together", "늘 함께 즐겁다"), ("help each other out", "서로 돕는다"),
                   ("can talk about anything", "뭐든 이야기할 수 있다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, when I'm down, my friend always ____.",
                 "예를 들어, 제가 우울할 때 친구는 항상 ____해요.",
                 [[("cheers me up", "기운을 북돋운다"), ("listens to me", "내 말을 들어준다"),
                   ("stays by my side", "곁에 있어준다"), ("makes me laugh", "웃게 해준다"),
                   ("knows just what to say", "딱 맞는 말을 해준다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a true friend makes my life much more ____.",
                 "전반적으로, 진정한 친구는 제 삶을 훨씬 더 ____하게 만들어요.",
                 [[("enjoyable", "즐거운"), ("meaningful", "의미 있는"), ("fun", "재미있는"),
                   ("colorful", "다채로운"), ("happy", "행복한")]]),
            ]),
        ],
    },
    # ===== 13 =====
    {
        "emoji": "🛒", "title_ko": "쇼핑", "title_en": "Shopping",
        "prompt": "Talk about your shopping habits.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my shopping habits.", "제 쇼핑 습관을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most convenient way to shop these days.",
                 "제 생각에 요즘 ____이(가) 가장 편리한 쇼핑 방법이에요.",
                 [[("online shopping", "온라인 쇼핑"), ("shopping at the mall", "몰 쇼핑"),
                   ("using delivery apps", "배달 앱"), ("visiting local shops", "동네 가게"),
                   ("second-hand trading", "중고 거래")]]),
                ("Personally, I usually shop for ____.",
                 "개인적으로 저는 보통 ____을(를) 사요.",
                 [[("clothes", "옷"), ("shoes", "신발"), ("snacks", "간식"),
                   ("books", "책"), ("gadgets", "전자기기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that ____.",
                 "제가 그것을 좋아하는 가장 큰 이유는 ____이기 때문이에요.",
                 [[("it saves a lot of time", "시간이 많이 절약된다"), ("there are so many choices", "선택지가 많다"),
                   ("I can compare prices easily", "가격 비교가 쉽다"), ("the deals are great", "할인이 좋다"),
                   ("it's fun to browse", "구경하는 게 재미있다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, before buying something, I usually ____.",
                 "예를 들어, 무언가를 사기 전에 저는 보통 ____해요.",
                 [[("compare prices", "가격을 비교한다"), ("read reviews", "후기를 읽는다"),
                   ("wait for a sale", "세일을 기다린다"), ("check my budget", "예산을 확인한다"),
                   ("ask my friends", "친구에게 물어본다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I try to be a ____ shopper.",
                 "전반적으로, 저는 ____ 소비자가 되려고 해요.",
                 [[("smart", "현명한"), ("careful", "신중한"), ("practical", "실용적인"),
                   ("budget-minded", "예산을 의식하는"), ("thoughtful", "사려 깊은")]]),
            ]),
        ],
    },
    # ===== 14 =====
    {
        "emoji": "☕", "title_ko": "카페 가기", "title_en": "Going to Cafés",
        "prompt": "Talk about going to cafés.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about going to cafés.", "카페에 가는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, a café is a great place to ____.",
                 "제 생각에 카페는 ____하기에 좋은 곳이에요.",
                 [[("relax", "쉬다"), ("study", "공부하다"), ("meet friends", "친구를 만나다"),
                   ("read a book", "책을 읽다"), ("take a break", "잠시 쉬다")]]),
                ("Personally, I usually order ____.",
                 "개인적으로 저는 보통 ____을(를) 주문해요.",
                 [[("hot chocolate", "핫초코"), ("a smoothie", "스무디"), ("iced tea", "아이스티"),
                   ("a lemonade", "레모네이드"), ("juice", "주스")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like cafés is that they have a ____ atmosphere.",
                 "제가 카페를 좋아하는 가장 큰 이유는 ____ 분위기가 있기 때문이에요.",
                 [[("cozy", "아늑한"), ("calm", "차분한"), ("comfortable", "편안한"),
                   ("quiet", "조용한"), ("pleasant", "쾌적한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____ at a café.",
                 "예를 들어, 저는 카페에서 자주 ____해요.",
                 [[("study with friends", "친구들과 공부한다"), ("do my homework", "숙제를 한다"),
                   ("chat for hours", "오래 수다 떤다"), ("read quietly", "조용히 읽는다"),
                   ("just relax", "그냥 쉰다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, going to a café helps me ____.",
                 "전반적으로, 카페에 가는 것은 제가 ____하도록 도와줘요.",
                 [[("relax", "쉰다"), ("focus better", "더 집중한다"), ("recharge", "재충전한다"),
                   ("enjoy some free time", "여가를 즐긴다"), ("feel refreshed", "상쾌해진다")]]),
            ]),
        ],
    },
    # ===== 15 =====
    {
        "emoji": "🌳", "title_ko": "공원 가기", "title_en": "Going to the Park",
        "prompt": "Talk about going to a park.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about going to the park.", "공원에 가는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the park is one of the best places to ____.",
                 "제 생각에 공원은 ____하기에 가장 좋은 곳 중 하나예요.",
                 [[("relax", "쉬다"), ("exercise", "운동하다"), ("enjoy nature", "자연을 즐기다"),
                   ("meet friends", "친구를 만나다"), ("clear my mind", "머리를 식히다")]]),
                ("Personally, I like to ____ when I go there.",
                 "개인적으로 저는 거기 가면 ____하는 걸 좋아해요.",
                 [[("take a walk", "산책한다"), ("ride my bike", "자전거를 탄다"), ("have a picnic", "소풍을 즐긴다"),
                   ("play sports", "운동을 한다"), ("sit and relax", "앉아서 쉰다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I go is that it is ____.",
                 "제가 가는 가장 큰 이유는 그곳이 ____하기 때문이에요.",
                 [[("peaceful and green", "평화롭고 푸른"), ("great for exercise", "운동하기 좋은"),
                   ("close to home", "집에서 가까운"), ("free and open", "무료로 열려 있는"),
                   ("full of fresh air", "공기가 상쾌한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on weekends I usually ____.",
                 "예를 들어, 주말에 저는 보통 ____해요.",
                 [[("jog in the morning", "아침에 조깅한다"), ("walk with my family", "가족과 걷는다"),
                   ("have a picnic", "소풍을 간다"), ("read on a bench", "벤치에서 읽는다"),
                   ("take photos", "사진을 찍는다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, spending time in the park makes me feel ____.",
                 "전반적으로, 공원에서 시간을 보내면 저는 ____한 기분이 들어요.",
                 [[("refreshed", "상쾌한"), ("relaxed", "편안한"), ("healthy", "건강한"),
                   ("calm", "차분한"), ("happy", "행복한")]]),
            ]),
        ],
    },
    # ===== 16 =====
    {
        "emoji": "🎤", "title_ko": "콘서트·공연", "title_en": "Concerts & Performances",
        "prompt": "Talk about a concert or performance you enjoyed.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about a performance I enjoyed.", "제가 즐긴 공연을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ concerts are the most exciting to watch.",
                 "제 생각에 ____ 콘서트가 보기에 가장 신나요.",
                 [[("K-pop", "케이팝"), ("band", "밴드"), ("live music", "라이브"),
                   ("school", "학교"), ("dance", "댄스")]]),
                ("Personally, what I love most is ____.",
                 "개인적으로 제가 가장 좋아하는 것은 ____예요.",
                 [[("the live atmosphere", "라이브 분위기"), ("singing along", "따라 부르는 것"),
                   ("the energy of the crowd", "관객의 열기"), ("seeing my favorite artist", "좋아하는 가수를 보는 것"),
                   ("the amazing stage", "멋진 무대")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that the ____ is unforgettable.",
                 "제가 그것을 즐기는 가장 큰 이유는 ____이(가) 잊을 수 없기 때문이에요.",
                 [[("atmosphere", "분위기"), ("music", "음악"), ("energy", "에너지"),
                   ("performance", "공연"), ("experience", "경험")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I once ____ and it was amazing.",
                 "예를 들어, 저는 한번 ____했는데 정말 멋졌어요.",
                 [[("went to a K-pop concert", "케이팝 콘서트에 갔다"), ("watched a school festival", "학교 축제를 봤다"),
                   ("saw a live band", "라이브 밴드를 봤다"), ("sang along with everyone", "다 함께 따라 불렀다"),
                   ("enjoyed a musical", "뮤지컬을 즐겼다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, live performances make me feel ____.",
                 "전반적으로, 라이브 공연은 저를 ____한 기분이 들게 해요.",
                 [[("excited", "신나는"), ("thrilled", "짜릿한"), ("energized", "활력 넘치는"),
                   ("moved", "감동받은"), ("alive", "살아 있는 듯한")]]),
            ]),
        ],
    },
    # ===== 17 =====
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
                 [[("enjoy nature", "자연을 즐기다"), ("escape the city", "도시를 벗어나다"),
                   ("spend time with family", "가족과 시간을 보내다"), ("relax outdoors", "야외에서 쉬다"),
                   ("try something new", "새로운 걸 해보다")]]),
                ("Personally, my favorite part is ____.",
                 "개인적으로 제가 가장 좋아하는 부분은 ____예요.",
                 [[("the campfire", "캠프파이어"), ("cooking outdoors", "야외 요리"),
                   ("watching the stars", "별 보기"), ("sleeping in a tent", "텐트에서 자기"),
                   ("the fresh air", "상쾌한 공기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that it is ____.",
                 "제가 그것을 좋아하는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("peaceful and quiet", "평화롭고 조용한"), ("close to nature", "자연과 가까운"),
                   ("a fun adventure", "재미있는 모험"), ("good for family time", "가족 시간에 좋은"),
                   ("a nice break from routine", "일상에서 좋은 휴식")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last summer I ____.",
                 "예를 들어, 지난여름에 저는 ____했어요.",
                 [[("went camping with my family", "가족과 캠핑을 갔다"), ("cooked over a campfire", "캠프파이어로 요리했다"),
                   ("watched the night sky", "밤하늘을 봤다"), ("went on a hike", "등산을 했다"),
                   ("slept under the stars", "별 아래에서 잤다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, camping helps me feel ____.",
                 "전반적으로, 캠핑은 제가 ____한 기분이 들게 해줘요.",
                 [[("refreshed", "상쾌한"), ("relaxed", "편안한"), ("closer to nature", "자연과 가까운"),
                   ("free", "자유로운"), ("recharged", "재충전된")]]),
            ]),
        ],
    },
    # ===== 18 =====
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
                 [[("pasta", "파스타"), ("ramen", "라면"), ("fried rice", "볶음밥"),
                   ("sandwiches", "샌드위치"), ("simple desserts", "간단한 디저트")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that I can ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("make food to my taste", "내 입맛대로 만든다"), ("try new recipes", "새 조리법을 시도한다"),
                   ("share it with others", "남들과 나눈다"), ("be creative", "창의력을 발휘한다"),
                   ("relax while cooking", "요리하며 쉰다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on weekends I sometimes ____.",
                 "예를 들어, 주말에 저는 가끔 ____해요.",
                 [[("cook for my family", "가족을 위해 요리한다"), ("bake something sweet", "단 걸 굽는다"),
                   ("try a new dish", "새 음식을 만든다"), ("cook with friends", "친구들과 요리한다"),
                   ("prepare my own meals", "직접 식사를 준비한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, cooking makes me feel ____.",
                 "전반적으로, 요리는 저를 ____한 기분이 들게 해요.",
                 [[("proud", "뿌듯한"), ("creative", "창의적인"), ("relaxed", "편안한"),
                   ("satisfied", "만족스러운"), ("confident", "자신감 있는")]]),
            ]),
        ],
    },
    # ===== 19 =====
    {
        "emoji": "📚", "title_ko": "독서", "title_en": "Reading",
        "prompt": "Talk about reading and books.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about reading.", "독서에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ books are the most interesting to read.",
                 "제 생각에 ____ 책이 읽기에 가장 흥미로워요.",
                 [[("fantasy", "판타지"), ("mystery", "추리"), ("adventure", "모험"),
                   ("science", "과학"), ("comic", "만화")]]),
                ("Personally, I usually read ____.",
                 "개인적으로 저는 보통 ____을(를) 읽어요.",
                 [[("novels", "소설"), ("webtoons", "웹툰"), ("magazines", "잡지"),
                   ("short stories", "단편"), ("comic books", "만화책")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like reading is that it ____.",
                 "제가 독서를 좋아하는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("sparks my imagination", "상상력을 자극한다"), ("teaches me new things", "새로운 걸 알려준다"),
                   ("helps me relax", "쉬게 해준다"), ("improves my vocabulary", "어휘력을 늘려준다"),
                   ("takes me to another world", "다른 세계로 데려간다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently read ____ and really enjoyed it.",
                 "예를 들어, 저는 최근에 ____을(를) 읽고 정말 즐겼어요.",
                 [[("a fantasy novel", "판타지 소설"), ("a famous story", "유명한 이야기"),
                   ("a popular webtoon", "인기 웹툰"), ("a mystery book", "추리 소설"),
                   ("a science book", "과학책")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, reading makes me more ____.",
                 "전반적으로, 독서는 저를 더 ____하게 만들어요.",
                 [[("thoughtful", "사려 깊은"), ("creative", "창의적인"), ("knowledgeable", "아는 게 많은"),
                   ("imaginative", "상상력이 풍부한"), ("open-minded", "열린 마음의")]]),
            ]),
        ],
    },
    # ===== 20 =====
    {
        "emoji": "🎉", "title_ko": "명절과 휴일", "title_en": "Holidays",
        "prompt": "Talk about a holiday you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about a holiday I enjoy.", "제가 즐기는 명절을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most meaningful holiday.",
                 "제 생각에 ____이(가) 가장 의미 있는 명절이에요.",
                 [[("Chuseok", "추석"), ("Lunar New Year", "설날"), ("Christmas", "크리스마스"),
                   ("my birthday", "내 생일"), ("New Year's", "새해")]]),
                ("Personally, what I enjoy most is ____.",
                 "개인적으로 제가 가장 즐기는 건 ____예요.",
                 [[("getting together with family", "가족과 모이는 것"), ("the delicious food", "맛있는 음식"),
                   ("the holiday mood", "명절 분위기"), ("the days off", "쉬는 날"),
                   ("meeting relatives", "친척을 만나는 것")]]),
            ]),
            _step("③ 이유", [
                ("The main reason it matters to me is that I can ____.",
                 "그것이 제게 중요한 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("spend time with family", "가족과 시간을 보낸다"), ("take a real break", "제대로 쉰다"),
                   ("enjoy traditional food", "전통 음식을 즐긴다"), ("catch up with relatives", "친척과 안부를 나눈다"),
                   ("forget about school", "학교를 잊는다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on holidays we usually ____.",
                 "예를 들어, 명절에 우리는 보통 ____해요.",
                 [[("share a big meal", "함께 식사한다"), ("visit our grandparents", "조부모님을 뵙는다"),
                   ("play games together", "함께 게임한다"), ("take family photos", "가족사진을 찍는다"),
                   ("exchange gifts", "선물을 주고받는다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, holidays make me feel ____.",
                 "전반적으로, 명절은 저를 ____한 기분이 들게 해요.",
                 [[("happy", "행복한"), ("grateful", "감사한"), ("relaxed", "편안한"),
                   ("close to my family", "가족과 가까운"), ("warm", "따뜻한")]]),
            ]),
        ],
    },
    # ===== 21 =====
    {
        "emoji": "🚄", "title_ko": "국내 여행", "title_en": "Domestic Trips",
        "prompt": "Talk about traveling within your country.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about traveling within Korea.", "국내 여행에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the best place to travel in Korea.",
                 "제 생각에 ____이(가) 한국에서 여행하기 가장 좋은 곳이에요.",
                 [[("Jeju Island", "제주도"), ("Busan", "부산"), ("Gangneung", "강릉"),
                   ("Gyeongju", "경주"), ("Jeonju", "전주")]]),
                ("Personally, I prefer to travel ____.",
                 "개인적으로 저는 ____ 여행하는 것을 선호해요.",
                 [[("by train", "기차로"), ("by car", "차로"), ("on a short trip", "짧은 여행으로"),
                   ("with my family", "가족과"), ("during vacation", "방학에")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that I can ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("enjoy beautiful scenery", "아름다운 경치를 즐긴다"), ("try local food", "현지 음식을 먹는다"),
                   ("relax away from home", "집을 떠나 쉰다"), ("visit famous spots", "유명한 곳을 간다"),
                   ("learn about the area", "그 지역을 알게 된다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last year I ____.",
                 "예를 들어, 작년에 저는 ____했어요.",
                 [[("took a trip to Busan", "부산 여행을 갔다"), ("visited Jeju Island", "제주도에 갔다"),
                   ("traveled with my family", "가족과 여행했다"), ("saw the ocean", "바다를 봤다"),
                   ("tried famous local dishes", "유명한 현지 음식을 먹었다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a domestic trip is a ____ way to relax.",
                 "전반적으로, 국내 여행은 쉬기에 ____ 방법이에요.",
                 [[("convenient", "편리한"), ("affordable", "부담 없는"), ("relaxing", "편안한"),
                   ("refreshing", "상쾌한"), ("easy", "쉬운")]]),
            ]),
        ],
    },
    # ===== 22 =====
    {
        "emoji": "🌍", "title_ko": "해외 여행", "title_en": "Traveling Abroad",
        "prompt": "Talk about traveling abroad.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about traveling to other countries.", "해외 여행에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is a country I really want to visit.",
                 "제 생각에 ____은(는) 제가 정말 가보고 싶은 나라예요.",
                 [[("Japan", "일본"), ("France", "프랑스"), ("the US", "미국"),
                   ("Italy", "이탈리아"), ("Australia", "호주")]]),
                ("Personally, when I travel abroad, I focus on ____.",
                 "개인적으로 해외여행 때 저는 ____에 집중해요.",
                 [[("the local culture", "현지 문화"), ("the food", "음식"), ("famous landmarks", "유명 명소"),
                   ("meeting new people", "새로운 사람 만나기"), ("the scenery", "경치")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I love it is that it lets me ____.",
                 "제가 그것을 사랑하는 가장 큰 이유는 그것이 제가 ____하게 해주기 때문이에요.",
                 [[("experience new cultures", "새로운 문화를 경험한다"), ("broaden my view", "시야를 넓힌다"),
                   ("try foreign food", "외국 음식을 먹는다"), ("practice my English", "영어를 연습한다"),
                   ("make special memories", "특별한 추억을 만든다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, someday I hope to ____.",
                 "예를 들어, 언젠가 저는 ____하고 싶어요.",
                 [[("visit the Eiffel Tower", "에펠탑을 본다"), ("explore Tokyo", "도쿄를 둘러본다"),
                   ("travel across Europe", "유럽을 여행한다"), ("see New York", "뉴욕을 본다"),
                   ("meet people from other countries", "외국 사람들을 만난다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, traveling abroad would be an ____ experience.",
                 "전반적으로, 해외 여행은 ____ 경험이 될 거예요.",
                 [[("amazing", "놀라운"), ("unforgettable", "잊지 못할"), ("exciting", "신나는"),
                   ("eye-opening", "견문을 넓히는"), ("valuable", "값진")]]),
            ]),
        ],
    },
    # ===== 23 =====
    {
        "emoji": "🎮", "title_ko": "게임하기", "title_en": "Playing Games",
        "prompt": "Talk about playing games.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about playing games.", "게임하는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ games are the most fun to play.",
                 "제 생각에 ____ 게임이 하기에 가장 재미있어요.",
                 [[("mobile", "모바일"), ("computer", "컴퓨터"), ("board", "보드"),
                   ("sports", "스포츠"), ("puzzle", "퍼즐")]]),
                ("Personally, I usually play ____.",
                 "개인적으로 저는 보통 ____ 게임을 해요.",
                 [[("with my friends", "친구들과"), ("on my phone", "휴대폰으로"), ("on weekends", "주말에"),
                   ("after studying", "공부 후에"), ("in my free time", "여가 시간에")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that it ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("helps me relax", "쉬게 해준다"), ("is fun with friends", "친구들과 재미있다"),
                   ("feels exciting", "신난다"), ("challenges my mind", "머리를 쓰게 한다"),
                   ("relieves stress", "스트레스를 풀어준다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I sometimes ____.",
                 "예를 들어, 저는 가끔 ____해요.",
                 [[("play online with friends", "온라인으로 친구들과 한다"), ("try new games", "새 게임을 해본다"),
                   ("play for about an hour", "한 시간쯤 한다"), ("join a team", "팀에 들어간다"),
                   ("watch gaming videos", "게임 영상을 본다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, gaming in moderation is a ____ way to relax.",
                 "전반적으로, 적당한 게임은 쉬기에 ____ 방법이에요.",
                 [[("fun", "재미있는"), ("enjoyable", "즐거운"), ("harmless", "해롭지 않은"),
                   ("good", "좋은"), ("nice", "괜찮은")]]),
            ]),
        ],
    },
    # ===== 24 =====
    {
        "emoji": "💻", "title_ko": "인터넷·SNS", "title_en": "The Internet & Social Media",
        "prompt": "Talk about how you use the Internet or social media.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I use the Internet.", "제가 인터넷을 어떻게 쓰는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most useful app or website.",
                 "제 생각에 ____이(가) 가장 유용한 앱이나 사이트예요.",
                 [[("YouTube", "유튜브"), ("a search engine", "검색 엔진"), ("Instagram", "인스타그램"),
                   ("a study app", "공부 앱"), ("an online dictionary", "온라인 사전")]]),
                ("Personally, I mainly use the Internet to ____.",
                 "개인적으로 저는 주로 ____하려고 인터넷을 써요.",
                 [[("watch videos", "영상을 본다"), ("find information", "정보를 찾는다"),
                   ("chat with friends", "친구와 대화한다"), ("study", "공부한다"),
                   ("listen to music", "음악을 듣는다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason it's helpful is that I can ____.",
                 "그것이 유용한 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("learn new things", "새로운 걸 배운다"), ("stay in touch with friends", "친구와 연락한다"),
                   ("find useful information", "유용한 정보를 찾는다"), ("enjoy my free time", "여가를 즐긴다"),
                   ("do research easily", "자료를 쉽게 찾는다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [[("watch study videos", "공부 영상을 본다"), ("message my friends", "친구에게 메시지한다"),
                   ("search for information", "정보를 검색한다"), ("share posts", "게시물을 공유한다"),
                   ("read the news", "뉴스를 읽는다")]]),
            ]),
            _step("⑤ 마무리", [
                ("That said, I try to use it ____.",
                 "그렇긴 하지만, 저는 그것을 ____ 쓰려고 해요.",
                 [[("wisely", "현명하게"), ("in moderation", "적당히"), ("safely", "안전하게"),
                   ("carefully", "조심스럽게"), ("responsibly", "책임감 있게")]]),
            ]),
        ],
    },
    # ===== 25 =====
    {
        "emoji": "📺", "title_ko": "TV·드라마", "title_en": "TV & Dramas",
        "prompt": "Talk about the TV shows or dramas you watch.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the TV shows I watch.", "제가 보는 TV 프로그램을 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ shows are the most enjoyable.",
                 "제 생각에 ____ 프로그램이 가장 즐거워요.",
                 [[("drama", "드라마"), ("variety", "예능"), ("comedy", "코미디"),
                   ("documentary", "다큐멘터리"), ("animation", "애니메이션")]]),
                ("Personally, I usually watch TV ____.",
                 "개인적으로 저는 보통 ____ TV를 봐요.",
                 [[("after dinner", "저녁 후에"), ("on weekends", "주말에"), ("with my family", "가족과"),
                   ("before bed", "자기 전에"), ("in my free time", "여가 시간에")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that the ____ keeps me interested.",
                 "제가 그것을 좋아하는 가장 큰 이유는 ____이(가) 흥미를 잃지 않게 하기 때문이에요.",
                 [[("story", "이야기"), ("characters", "등장인물"), ("plot", "줄거리"),
                   ("humor", "유머"), ("acting", "연기")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently watched ____ and really liked it.",
                 "예를 들어, 저는 최근에 ____을(를) 보고 정말 좋았어요.",
                 [[("a popular drama", "인기 드라마"), ("a funny variety show", "웃긴 예능"),
                   ("an animated series", "애니메이션"), ("a documentary", "다큐멘터리"),
                   ("a Korean drama", "한국 드라마")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, watching TV helps me ____.",
                 "전반적으로, TV를 보는 것은 제가 ____하도록 도와줘요.",
                 [[("relax", "쉰다"), ("have fun", "즐긴다"), ("forget my stress", "스트레스를 잊는다"),
                   ("spend time with family", "가족과 시간을 보낸다"), ("enjoy my evening", "저녁을 즐긴다")]]),
            ]),
        ],
    },
    # ===== 26 =====
    {
        "emoji": "🌊", "title_ko": "해변 가기", "title_en": "Going to the Beach",
        "prompt": "Talk about going to the beach or the sea.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about going to the beach.", "해변에 가는 것에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the beach is the perfect place to ____.",
                 "제 생각에 해변은 ____하기에 완벽한 곳이에요.",
                 [[("relax", "쉬다"), ("swim", "수영하다"), ("cool off", "더위를 식히다"),
                   ("watch the sunset", "노을을 보다"), ("spend summer", "여름을 보내다")]]),
                ("Personally, my favorite thing to do there is ____.",
                 "개인적으로 제가 거기서 가장 좋아하는 것은 ____예요.",
                 [[("swim in the sea", "바다에서 수영하기"), ("walk along the shore", "해안 걷기"),
                   ("build sandcastles", "모래성 쌓기"), ("collect shells", "조개 줍기"),
                   ("take photos", "사진 찍기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I love it is that it is ____.",
                 "제가 그곳을 좋아하는 가장 큰 이유는 그곳이 ____하기 때문이에요.",
                 [[("beautiful and relaxing", "아름답고 편안한"), ("cool and refreshing", "시원하고 상쾌한"),
                   ("fun in summer", "여름에 재미있는"), ("great with friends", "친구와 좋은"),
                   ("full of fresh air", "공기가 상쾌한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last summer I ____.",
                 "예를 들어, 지난여름에 저는 ____했어요.",
                 [[("went to the beach with friends", "친구들과 해변에 갔다"), ("swam in the ocean", "바다에서 수영했다"),
                   ("watched the sunset", "노을을 봤다"), ("played beach games", "해변 게임을 했다"),
                   ("relaxed by the sea", "바닷가에서 쉬었다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a day at the beach makes me feel ____.",
                 "전반적으로, 해변에서 보내는 하루는 저를 ____한 기분이 들게 해요.",
                 [[("refreshed", "상쾌한"), ("happy", "행복한"), ("relaxed", "편안한"),
                   ("free", "자유로운"), ("energized", "활력 넘치는")]]),
            ]),
        ],
    },
    # ===== 27 =====
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
                 [[("nature", "자연"), ("travel", "여행"), ("food", "음식"),
                   ("selfie", "셀카"), ("pet", "반려동물")]]),
                ("Personally, I usually take photos with ____.",
                 "개인적으로 저는 보통 ____와(과) 함께 사진을 찍어요.",
                 [[("my phone", "휴대폰"), ("a camera", "카메라"), ("my friends", "친구들"),
                   ("my family", "가족"), ("my pet", "반려동물")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that I can ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("capture special moments", "특별한 순간을 담는다"), ("keep good memories", "좋은 추억을 남긴다"),
                   ("be creative", "창의력을 발휘한다"), ("share them with others", "남들과 나눈다"),
                   ("express myself", "나를 표현한다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [[("take photos when I travel", "여행할 때 찍는다"), ("photograph nice scenery", "멋진 경치를 찍는다"),
                   ("take selfies with friends", "친구들과 셀카를 찍는다"), ("post pictures online", "사진을 올린다"),
                   ("save happy moments", "행복한 순간을 저장한다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, taking photos helps me ____.",
                 "전반적으로, 사진을 찍는 것은 제가 ____하도록 도와줘요.",
                 [[("keep memories", "추억을 간직한다"), ("enjoy the moment", "순간을 즐긴다"),
                   ("be creative", "창의적이 된다"), ("remember special days", "특별한 날을 기억한다"),
                   ("share my life", "내 삶을 나눈다")]]),
            ]),
        ],
    },
    # ===== 28 =====
    {
        "emoji": "🏢", "title_ko": "우리 동네", "title_en": "My Neighborhood",
        "prompt": "Describe your neighborhood.",
        "template": [
            _step("① 주제 소개", [
                ("Let me describe my neighborhood.", "우리 동네를 소개할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, my neighborhood is quite ____.",
                 "제 생각에 우리 동네는 꽤 ____해요.",
                 [[("convenient", "편리한"), ("quiet", "조용한"), ("safe", "안전한"),
                   ("friendly", "정겨운"), ("clean", "깨끗한")]]),
                ("Personally, my favorite place nearby is ____.",
                 "개인적으로 제가 가장 좋아하는 근처 장소는 ____예요.",
                 [[("the park", "공원"), ("the library", "도서관"), ("a café", "카페"),
                   ("the shopping street", "상가"), ("the sports center", "체육관")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like it is that ____.",
                 "제가 그곳을 좋아하는 가장 큰 이유는 ____이기 때문이에요.",
                 [[("everything is close by", "모든 게 가깝다"), ("it is safe and quiet", "안전하고 조용하다"),
                   ("there are nice places to hang out", "놀 만한 곳이 있다"), ("the people are friendly", "사람들이 친절하다"),
                   ("it has good restaurants", "좋은 식당이 있다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____ around my neighborhood.",
                 "예를 들어, 저는 동네에서 자주 ____해요.",
                 [[("walk to the park", "공원까지 걷는다"), ("meet friends", "친구를 만난다"),
                   ("ride my bike", "자전거를 탄다"), ("study at the library", "도서관에서 공부한다"),
                   ("grab a snack", "간식을 사 먹는다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I really enjoy living in such a ____ neighborhood.",
                 "전반적으로, 저는 이렇게 ____ 동네에 사는 것이 정말 좋아요.",
                 [[("convenient", "편리한"), ("peaceful", "평화로운"), ("friendly", "정겨운"),
                   ("safe", "안전한"), ("pleasant", "쾌적한")]]),
            ]),
        ],
    },
]


# ===== 워드뱅크 확장(빈칸당 5개 → 7개). 빈칸 순서대로 (영어, 뜻) 2개씩 추가 =====
_EXTRA = {
    1: [[("always believe in me", "늘 나를 믿는다"), ("are there for me", "나를 위해 있어준다")],
        [("loving", "사랑이 많은"), ("down-to-earth", "소탈한")],
        [("laugh together often", "자주 함께 웃다"), ("do things together", "함께 무언가를 하다")],
        [("give me space", "여지를 준다"), ("cheer me up", "기운을 북돋운다")],
        [("close", "가까운"), ("wonderful", "멋진")]],
    2: [[("cozy", "아늑한"), ("welcoming", "정겨운")],
        [("the balcony", "발코니"), ("the kitchen", "부엌")],
        [("it is quiet and private", "조용하고 개인적이다"), ("I feel at ease there", "마음이 편하다")],
        [("do my homework", "숙제를 하다"), ("play some music", "음악을 틀다")],
        [("calm", "차분한"), ("cozy", "아늑한")]],
    3: [[("lunch time", "점심시간"), ("break time", "쉬는 시간")],
        [("P.E.", "체육"), ("coding", "코딩")],
        [("exciting", "신나는"), ("practical", "실용적인")],
        [("I enjoy the class", "수업이 즐겁다"), ("the lessons are lively", "수업이 활기차다")],
        [("history", "역사"), ("math", "수학")],
        [("give presentations", "발표를 하다"), ("read together", "함께 읽다")],
        [("never boring", "지루하지 않은"), ("full of friends", "친구가 많은")]],
    4: [[("listening to music", "음악 감상"), ("playing games", "게임하기")],
        [("dancing", "춤"), ("cooking", "요리")],
        [("enjoy my day", "하루를 즐기다"), ("feel happy", "행복해지다")],
        [("join a club", "동아리에 들다"), ("learn from videos", "영상으로 배우다")],
        [("interesting", "흥미로운"), ("fun", "재미있는")]],
    5: [[("volleyball", "배구"), ("baseball", "야구")],
        [("playing outdoors", "야외에서 하기"), ("joining a team", "팀에 들기")],
        [("flexibility", "유연성"), ("focus", "집중력")],
        [("work out at home", "집에서 운동하다"), ("join a sports club", "스포츠 동아리에 들다")],
        [("active", "활동적인"), ("in shape", "몸매를 유지한")]],
    6: [[("ramen", "라면"), ("gimbap", "김밥")],
        [("Italian", "이탈리안"), ("mild", "순한")],
        [("nice smell", "좋은 향"), ("soft texture", "부드러운 식감")],
        [("share it with friends", "친구들과 나눠 먹다"), ("have it after school", "방과 후에 먹다")],
        [("tastes great", "정말 맛있다"), ("lifts my mood", "기분을 좋게 한다")]],
    7: [[("best friends", "최고의 친구"), ("faithful companions", "충실한 벗")],
        [("puppy", "강아지"), ("turtle", "거북이")],
        [("are gentle and cute", "온순하고 귀엽다"), ("always welcome me", "늘 반겨준다")],
        [("follow you around", "졸졸 따라다니다"), ("protect your home", "집을 지켜주다")],
        [("happy", "행복한"), ("cheerful", "밝은")]],
    8: [[("early spring", "이른 봄"), ("late fall", "늦가을")],
        [("clear", "맑은"), ("warm", "따뜻한")],
        [("the leaves turn colorful", "단풍이 물든다"), ("the days are pleasant", "날이 쾌적하다")],
        [("early summer", "초여름"), ("the weekend", "주말")],
        [("play sports", "운동을 하다"), ("walk in the park", "공원을 걷다")],
        [("changes my day", "하루를 바꾼다"), ("lifts my spirits", "기분을 띄운다")]],
    9: [[("horror", "공포"), ("sci-fi", "SF")],
        [("R&B", "알앤비"), ("dance music", "댄스 음악")],
        [("soundtrack", "사운드트랙"), ("characters", "등장인물")],
        [("fun", "재미있는"), ("beautiful", "아름다운")],
        [("enjoying it", "즐기는 것"), ("humming it", "흥얼거리는 것")],
        [("a comedy film", "코미디 영화"), ("a famous OST", "유명한 OST")],
        [("have fun", "즐기다"), ("escape for a while", "잠시 벗어나다")]],
    10: [[("helps me grow", "성장하게 한다"), ("gives me energy", "활력을 준다")],
         [("London", "런던"), ("Sydney", "시드니")],
         [("learn new things", "새로운 걸 배우다"), ("take great photos", "멋진 사진을 찍다")],
         [("tried local food", "현지 음식을 먹었다"), ("stayed at a hotel", "호텔에 묵었다")],
         [("fun", "재미있는"), ("special", "특별한")]],
    11: [[("kind", "친절한"), ("honest", "정직한")],
         [("games", "게임"), ("cooking", "요리")],
         [("help others gladly", "기꺼이 남을 돕다"), ("stay calm", "침착함을 유지하다")],
         [("draw pictures", "그림을 그리다"), ("exercise", "운동을 하다")],
         [("kind", "친절한"), ("hard-working", "성실한")]],
    12: [[("supportive", "힘이 되는"), ("reliable", "믿음직한")],
         [("funny", "웃긴"), ("caring", "배려심 있는")],
         [("trust each other", "서로 믿다"), ("spend a lot of time together", "많은 시간을 함께 보내다")],
         [("gives good advice", "좋은 조언을 준다"), ("understands me", "나를 이해한다")],
         [("exciting", "신나는"), ("special", "특별한")]],
    13: [[("shopping at markets", "시장에서 사기"), ("browsing shops", "매장 구경하기")],
         [("accessories", "액세서리"), ("stationery", "문구")],
         [("there are many choices", "선택지가 많다"), ("it's easy to find deals", "할인을 찾기 쉽다")],
         [("check reviews", "후기를 확인하다"), ("look for coupons", "쿠폰을 찾다")],
         [("wise", "현명한"), ("mindful", "신중한")]],
    14: [[("have a drink", "음료를 마시다"), ("take a break", "잠시 쉬다")],
         [("an americano", "아메리카노"), ("a milkshake", "밀크셰이크")],
         [("warm", "따뜻한"), ("cozy", "아늑한")],
         [("meet my friends", "친구를 만나다"), ("listen to music", "음악을 듣다")],
         [("take a rest", "쉬다"), ("clear my mind", "머리를 식히다")]],
    15: [[("play", "놀다"), ("get fresh air", "바람을 쐬다")],
         [("jog", "조깅하다"), ("sit on a bench", "벤치에 앉다")],
         [("open and wide", "넓고 트인"), ("nice for a walk", "산책하기 좋은")],
         [("walk with friends", "친구들과 걷다"), ("take photos", "사진을 찍다")],
         [("free", "자유로운"), ("peaceful", "평화로운")]],
    16: [[("rock", "록"), ("pop", "팝")],
         [("a band play", "밴드 연주"), ("a talent show", "장기자랑")],
         [("performance", "공연"), ("lighting", "조명")],
         [("danced with the crowd", "관객과 춤췄다"), ("met a singer", "가수를 만났다")],
         [("amazed", "감탄한"), ("alive", "살아 있는 듯한")]],
    17: [[("breathe fresh air", "맑은 공기를 마시다"), ("get away from it all", "모든 것에서 벗어나다")],
         [("the night sky", "밤하늘"), ("being in nature", "자연 속에 있는 것")],
         [("away from the city", "도시에서 벗어난"), ("exciting", "신나는")],
         [("made a campfire", "캠프파이어를 피웠다"), ("enjoyed the fresh air", "상쾌한 공기를 즐겼다")],
         [("peaceful", "평화로운"), ("recharged", "재충전된")]],
    18: [[("healthy", "건강한"), ("enjoyable", "즐거운")],
         [("soup", "수프"), ("pancakes", "팬케이크")],
         [("eat healthier", "더 건강하게 먹다"), ("relax while cooking", "요리하며 쉬다")],
         [("cook with friends", "친구들과 요리하다"), ("make a snack", "간식을 만들다")],
         [("accomplished", "뿌듯한"), ("happy", "행복한")]],
    19: [[("history", "역사"), ("romance", "로맨스")],
         [("essays", "에세이"), ("newspapers", "신문")],
         [("broadens my mind", "시야를 넓히다"), ("calms me down", "마음을 진정시키다")],
         [("an adventure story", "모험 이야기"), ("a comic book", "만화책")],
         [("patient", "인내심 있는"), ("curious", "호기심 많은")]],
    20: [[("New Year's Day", "새해"), ("summer vacation", "여름방학")],
         [("the fun events", "즐거운 행사"), ("seeing my relatives", "친척을 만나는 것")],
         [("get some rest", "푹 쉬다"), ("enjoy the mood", "분위기를 즐기다")],
         [("cook together", "함께 요리하다"), ("watch TV together", "함께 TV를 보다")],
         [("warm", "따뜻한"), ("thankful", "감사한")]],
    21: [[("Sokcho", "속초"), ("Yeosu", "여수")],
         [("by subway", "지하철로"), ("by bus", "버스로")],
         [("learn about history", "역사를 배우다"), ("breathe fresh air", "맑은 공기를 마시다")],
         [("climbed a mountain", "산에 올랐다"), ("stayed by the sea", "바닷가에 묵었다")],
         [("refreshing", "상쾌한"), ("easy", "편한")]],
    22: [[("the UK", "영국"), ("Canada", "캐나다")],
         [("the people", "사람들"), ("the history", "역사")],
         [("learn a language", "언어를 배우다"), ("make new friends", "새 친구를 사귀다")],
         [("see the Colosseum", "콜로세움을 보다"), ("walk along the beach", "해변을 걷다")],
         [("wonderful", "멋진"), ("special", "특별한")]],
    23: [[("racing", "레이싱"), ("role-playing", "롤플레잉")],
         [("at home", "집에서"), ("with my brother", "형제와")],
         [("is a fun break", "즐거운 휴식이다"), ("cheers me up", "기운을 북돋운다")],
         [("play with my brother", "형제와 하다"), ("learn new skills", "새 기술을 배우다")],
         [("enjoyable", "즐거운"), ("harmless", "해롭지 않은")]],
    24: [[("a news app", "뉴스 앱"), ("a map app", "지도 앱")],
         [("play games", "게임을 하다"), ("read the news", "뉴스를 읽다")],
         [("share my ideas", "생각을 나누다"), ("watch anything anytime", "언제든 보다")],
         [("watch fun clips", "재미있는 영상을 보다"), ("look things up", "검색해 보다")],
         [("for a set time", "정해진 시간만"), ("without overdoing it", "과하지 않게")]],
    25: [[("news", "뉴스"), ("quiz", "퀴즈")],
         [("after homework", "숙제 후에"), ("when I relax", "쉴 때")],
         [("theme", "주제"), ("ending", "결말")],
         [("a talent show", "오디션 프로그램"), ("a nature documentary", "자연 다큐")],
         [("take a break", "잠시 쉬다"), ("laugh a lot", "많이 웃다")]],
    26: [[("cool off", "더위를 식히다"), ("have fun", "즐기다")],
         [("play in the waves", "파도에서 놀기"), ("relax on the sand", "모래에서 쉬기")],
         [("wide and open", "넓고 트인"), ("perfect for summer", "여름에 딱 좋은")],
         [("collected shells", "조개를 주웠다"), ("took nice photos", "멋진 사진을 찍었다")],
         [("cool", "시원한"), ("peaceful", "평화로운")]],
    27: [[("people", "인물"), ("night views", "야경")],
         [("my classmates", "반 친구들"), ("a new camera", "새 카메라")],
         [("look back later", "나중에 다시 보다"), ("enjoy the moment", "순간을 즐기다")],
         [("take nature photos", "자연 사진을 찍다"), ("make photo albums", "사진첩을 만들다")],
         [("capture beauty", "아름다움을 담다"), ("tell my story", "내 이야기를 전하다")]],
    28: [[("lively", "활기찬"), ("pleasant", "쾌적한")],
         [("the playground", "놀이터"), ("a bakery", "빵집")],
         [("it is clean and tidy", "깨끗하고 정돈되어 있다"), ("there is a lot to do", "할 게 많다")],
         [("take a walk", "산책하다"), ("grab a snack", "간식을 사 먹다")],
         [("clean", "깨끗한"), ("lively", "활기찬")]],
}


def _augment_wordbank():
    for _ui, _u in enumerate(UNITS, 1):
        _extras = _EXTRA.get(_ui, [])
        _blanks = [opts for st in _u["template"]
                   for (_en, _ko, choices) in st["lines"] for opts in choices]
        assert len(_extras) == len(_blanks), \
            f"UNIT {_ui}: 추가보기 {len(_extras)}개 != 빈칸 {len(_blanks)}개"
        for opts, add in zip(_blanks, _extras):
            opts.extend(add)


_augment_wordbank()
