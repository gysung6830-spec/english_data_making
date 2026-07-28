# -*- coding: utf-8 -*-
"""
성인(중급 이상) 영어 회화 교재 콘텐츠 (OPIC 주제 기반 · '내 의견 말하기' 템플릿).

중학생용(textbook_data.py)과 같은 구조지만, 성인 학습자에 맞춰
템플릿 문장과 어휘를 한 단계 높였습니다(직장·워라밸·자기계발 등 성인 주제 포함).

■ 템플릿 line 형식: (영어문장, 한글해석, [빈칸별 보기목록])
  - 각 보기목록 = [(영어단어/구, 한글뜻), ...]  (빈칸당 5개)
build_textbook.py 가 이 파일을 읽어 output/성인영어회화교재_OPIC20.pdf 를 만듭니다.
"""

TITLE = "성인 영어 회화 교재"
SUBTITLE = "OPIC 주제로 말하는 나의 의견 · 성인 · 중급 이상 · 템플릿 + 워드뱅크"
FOOTER = "성인 영어 회화 교재 · 내 의견 말하기 템플릿 + 워드뱅크"
KICKER = "ADULT · INTERMEDIATE & UP"

HOW_TO_USE = [
    ("1. 워드뱅크 보기 익히기", "오른쪽 워드뱅크에서 각 번호에 들어갈 보기 단어·표현과 뜻을 먼저 확인합니다."),
    ("2. 빈칸 채우기", "왼쪽 템플릿의 빈칸 번호에 맞춰 같은 번호 보기 중 하나를 골라 문장을 완성합니다."),
    ("3. 소리 내어 말하기", "①~⑤ 문장을 자연스럽게 이어 한 편의 '내 의견'으로 1분 내외 말해 봅니다."),
    ("4. 확장하기", "보기 대신 자신의 실제 경험·생각으로 바꾸고, 연결어로 문장을 늘리면 완성도가 올라갑니다."),
]

STEPS_GUIDE = [
    ("① 주제 소개", "무엇에 대해 말할지 자연스럽게 열기"),
    ("② 내 의견·선호", "핵심 의견/선호를 한 문장으로 제시"),
    ("③ 이유", "그렇게 생각하는 근거 1~2가지"),
    ("④ 예시·경험", "구체적 사례나 실제 경험 들기"),
    ("⑤ 마무리", "핵심을 정리하며 인상적으로 마무리"),
]

EXPRESSIONS = [
    ("의견 제시", [
        ("In my opinion, ~", "제 생각에는 ~"),
        ("Personally, I believe (that) ~", "개인적으로 저는 ~라고 생각해요"),
        ("From my perspective, ~", "제 관점에서는 ~"),
        ("I'd argue that ~", "저는 ~라고 봐요"),
    ]),
    ("선호 표현", [
        ("I prefer A to B", "저는 B보다 A를 선호해요"),
        ("What appeals to me most is ~", "제게 가장 끌리는 것은 ~"),
        ("I tend to lean toward ~", "저는 ~쪽으로 기울어요"),
        ("I'm particularly fond of ~", "저는 특히 ~을 좋아해요"),
    ]),
    ("이유·연결", [
        ("The main reason is that ~", "가장 큰 이유는 ~이기 때문이에요"),
        ("This is largely because ~", "이는 주로 ~때문이에요"),
        ("On top of that, ~", "게다가 ~"),
        ("What's more, ~", "더욱이 ~"),
    ]),
    ("예시·마무리", [
        ("For instance, ~ / To give an example, ~", "예를 들어 ~"),
        ("All in all, ~ / At the end of the day, ~", "결국 ~"),
        ("That's why ~", "그래서 ~인 거예요"),
        ("Having said that, ~ / On the other hand, ~", "그렇긴 하지만 ~ / 반면에 ~"),
    ]),
]


def _step(label, lines):
    return {"label": label, "lines": lines}


UNITS = [
    # ===== U1 =====
    {
        "emoji": "🙋", "title_ko": "자기소개", "title_en": "Introducing Yourself",
        "prompt": "Could you tell me a little about yourself?",
        "template": [
            _step("① 주제 소개", [
                ("Sure, let me tell you a bit about myself.", "네, 제 소개를 조금 할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("To begin with, I would describe myself as a(n) ____ person.",
                 "우선, 저는 스스로를 ____ 사람이라고 표현하고 싶어요.",
                 [[("outgoing", "외향적인"), ("easygoing", "느긋한"), ("detail-oriented", "꼼꼼한"),
                   ("ambitious", "야심 있는"), ("laid-back", "여유로운")]]),
                ("Personally, I'm particularly passionate about ____.",
                 "개인적으로 저는 ____에 특히 열정적이에요.",
                 [[("my career", "제 커리어"), ("learning new things", "새로운 것 배우기"),
                   ("staying active", "활동적으로 지내기"), ("spending time with family", "가족과 시간 보내기"),
                   ("self-improvement", "자기계발")]]),
            ]),
            _step("③ 이유", [
                ("One thing that defines me is that I tend to ____.",
                 "저를 잘 나타내는 점은 제가 ____하는 편이라는 거예요.",
                 [[("stay positive", "긍정적으로 지내다"), ("work hard", "열심히 하다"),
                   ("get along with others", "남들과 잘 지내다"), ("take on challenges", "도전을 받아들이다"),
                   ("plan ahead", "미리 계획하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For instance, in my free time I usually ____.",
                 "예를 들어, 여가 시간에 저는 보통 ____해요.",
                 [[("read and unwind", "책 읽으며 쉬다"), ("catch up with friends", "친구들과 만나다"),
                   ("work out", "운동하다"), ("explore new places", "새로운 곳을 다니다"),
                   ("pursue my hobbies", "취미를 즐기다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, I consider myself a(n) ____ and open-minded person.",
                 "결국, 저는 스스로를 ____하고 열린 사람이라고 생각해요.",
                 [[("driven", "의욕적인"), ("friendly", "친근한"), ("reliable", "믿음직한"),
                   ("curious", "호기심 많은"), ("balanced", "균형 잡힌")]]),
            ]),
        ],
    },
    # ===== U2 =====
    {
        "emoji": "💼", "title_ko": "직장·하는 일", "title_en": "Your Job",
        "prompt": "Tell me about your job or what you do.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about what I do for a living.", "제가 하는 일에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, my job is quite ____.",
                 "제 생각에 제 일은 꽤 ____해요.",
                 [[("rewarding", "보람 있는"), ("demanding", "힘든"), ("dynamic", "역동적인"),
                   ("meaningful", "의미 있는"), ("fast-paced", "빠르게 돌아가는")]]),
                ("Personally, what I enjoy most is ____.",
                 "개인적으로 제가 가장 즐기는 것은 ____예요.",
                 [[("solving problems", "문제 해결"), ("working with a team", "팀으로 일하기"),
                   ("meeting new people", "새로운 사람 만나기"), ("learning on the job", "일하며 배우기"),
                   ("seeing results", "결과를 보는 것")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I find it fulfilling is that I can ____.",
                 "그 일이 충족감을 주는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("make a real impact", "실질적인 영향을 주다"), ("grow professionally", "전문적으로 성장하다"),
                   ("use my skills", "내 역량을 발휘하다"), ("take on responsibility", "책임을 맡다"),
                   ("contribute to the team", "팀에 기여하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on a typical day I ____.",
                 "예를 들어, 평범한 하루에 저는 ____해요.",
                 [[("handle several tasks at once", "여러 일을 동시에 처리하다"), ("attend meetings", "회의에 참석하다"),
                   ("collaborate with colleagues", "동료와 협업하다"), ("manage projects", "프로젝트를 관리하다"),
                   ("deal with clients", "고객을 상대하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, despite the pressure, my job is ____.",
                 "전반적으로, 부담은 있지만 제 일은 ____.",
                 [[("satisfying", "만족스러운"), ("worthwhile", "가치 있는"), ("a good fit for me", "저에게 잘 맞는"),
                   ("something I take pride in", "자부심을 느끼는 것"), ("keeping me motivated", "동기를 주는")]]),
            ]),
        ],
    },
    # ===== U3 =====
    {
        "emoji": "🏠", "title_ko": "사는 곳·동네", "title_en": "Where You Live",
        "prompt": "Describe the place where you live.",
        "template": [
            _step("① 주제 소개", [
                ("Let me describe the area where I live.", "제가 사는 동네를 소개할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, my neighborhood is remarkably ____.",
                 "제 생각에 우리 동네는 상당히 ____해요.",
                 [[("convenient", "편리한"), ("quiet", "조용한"), ("well-developed", "잘 발달된"),
                   ("walkable", "걷기 좋은"), ("lively", "활기찬")]]),
                ("What I appreciate most is ____.",
                 "제가 가장 마음에 들어하는 건 ____예요.",
                 [[("the easy access to transport", "편리한 교통 접근성"), ("the peaceful atmosphere", "평화로운 분위기"),
                   ("the nearby amenities", "가까운 편의시설"), ("the sense of community", "이웃 간의 정"),
                   ("the green spaces", "녹지 공간")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like living here is that ____.",
                 "제가 여기 사는 것을 좋아하는 가장 큰 이유는 ____이기 때문이에요.",
                 [[("everything is within walking distance", "모든 게 걸어갈 거리에 있다"),
                   ("it strikes a nice balance", "균형이 잘 잡혀 있다"), ("the area is safe", "지역이 안전하다"),
                   ("it suits my lifestyle", "내 생활방식에 맞다"), ("the rent is reasonable", "집세가 적당하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on weekends I often ____.",
                 "예를 들어, 주말에 저는 자주 ____해요.",
                 [[("take a stroll nearby", "근처를 산책하다"), ("visit local cafés", "동네 카페에 가다"),
                   ("relax at home", "집에서 쉬다"), ("run errands easily", "볼일을 쉽게 보다"),
                   ("meet friends around here", "이 근처에서 친구를 만나다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, it's a ____ place to live.",
                 "결국, 살기에 ____ 곳이에요.",
                 [[("comfortable", "편안한"), ("convenient", "편리한"), ("pleasant", "쾌적한"),
                   ("practical", "실용적인"), ("welcoming", "정겨운")]]),
            ]),
        ],
    },
    # ===== U4 =====
    {
        "emoji": "🤝", "title_ko": "가족·인간관계", "title_en": "Family & Relationships",
        "prompt": "Tell me about your family or the people close to you.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about the people close to me.", "제게 가까운 사람들에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the people close to me are incredibly ____.",
                 "제 생각에 제게 가까운 사람들은 정말 ____해요.",
                 [[("supportive", "힘이 되는"), ("understanding", "이해심 많은"), ("dependable", "믿음직한"),
                   ("easygoing", "편한"), ("caring", "배려심 있는")]]),
                ("Personally, I value ____ the most in a relationship.",
                 "개인적으로 관계에서 제가 가장 중요하게 여기는 것은 ____예요.",
                 [[("honesty", "정직함"), ("trust", "신뢰"), ("communication", "소통"),
                   ("respect", "존중"), ("loyalty", "의리")]]),
            ]),
            _step("③ 이유", [
                ("The main reason we stay close is that we ____.",
                 "우리가 가깝게 지내는 가장 큰 이유는 우리가 ____하기 때문이에요.",
                 [[("make time for each other", "서로를 위해 시간을 내다"), ("support one another", "서로를 지지하다"),
                   ("share similar values", "비슷한 가치를 지니다"), ("communicate openly", "솔직하게 소통하다"),
                   ("respect each other's space", "서로의 공간을 존중하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, we regularly ____.",
                 "예를 들어, 우리는 정기적으로 ____해요.",
                 [[("get together for dinner", "저녁을 함께하다"), ("keep in touch", "연락을 유지하다"),
                   ("help each other out", "서로 돕다"), ("celebrate special occasions", "특별한 날을 함께 기념하다"),
                   ("check in on each other", "서로 안부를 묻다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, having such ____ relationships means a lot to me.",
                 "전반적으로, 이런 ____ 관계가 있다는 게 제겐 큰 의미예요.",
                 [[("strong", "든든한"), ("close", "가까운"), ("meaningful", "의미 있는"),
                   ("healthy", "건강한"), ("lasting", "오래가는")]]),
            ]),
        ],
    },
    # ===== U5 =====
    {
        "emoji": "🎈", "title_ko": "여가 시간", "title_en": "Free Time",
        "prompt": "What do you usually do in your free time?",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I spend my free time.", "제가 여가를 어떻게 보내는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the best way to spend my free time is ____.",
                 "제 생각에 여가를 보내는 가장 좋은 방법은 ____예요.",
                 [[("doing something relaxing", "편안한 걸 하는 것"), ("being active outdoors", "야외에서 활동하는 것"),
                   ("catching up on rest", "밀린 휴식을 취하는 것"), ("pursuing a hobby", "취미를 즐기는 것"),
                   ("socializing", "사람들과 어울리는 것")]]),
                ("Personally, I try to ____ whenever I can.",
                 "개인적으로 저는 가능할 때마다 ____하려고 해요.",
                 [[("unwind and recharge", "쉬며 재충전하다"), ("make time for myself", "나를 위한 시간을 갖다"),
                   ("do what I love", "좋아하는 걸 하다"), ("get some fresh air", "바람을 쐬다"),
                   ("stay productive", "생산적으로 지내다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that it helps me ____.",
                 "가장 큰 이유는 그것이 제가 ____하도록 도와주기 때문이에요.",
                 [[("relieve stress", "스트레스를 풀다"), ("clear my mind", "머리를 비우다"),
                   ("maintain a work-life balance", "워라밸을 지키다"), ("feel refreshed", "상쾌해지다"),
                   ("stay motivated", "동기를 유지하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, after a long week I usually ____.",
                 "예를 들어, 긴 한 주가 끝나면 저는 보통 ____해요.",
                 [[("watch a movie at home", "집에서 영화를 보다"), ("meet up with friends", "친구들과 만나다"),
                   ("go for a walk", "산책을 가다"), ("try a new restaurant", "새 식당에 가보다"),
                   ("simply take it easy", "그냥 여유를 부리다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, my free time keeps me ____.",
                 "결국, 여가 시간은 저를 ____하게 유지해 줘요.",
                 [[("balanced", "균형 잡힌"), ("refreshed", "상쾌한"), ("happy", "행복한"),
                   ("recharged", "재충전된"), ("at ease", "편안한")]]),
            ]),
        ],
    },
    # ===== U6 =====
    {
        "emoji": "🎨", "title_ko": "취미·관심사", "title_en": "Hobbies & Interests",
        "prompt": "Tell me about a hobby or interest of yours.",
        "template": [
            _step("① 주제 소개", [
                ("Let me tell you about one of my hobbies.", "제 취미 중 하나를 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the perfect hobby for me.",
                 "제 생각에 ____이(가) 제게 딱 맞는 취미예요.",
                 [[("photography", "사진"), ("cooking", "요리"), ("hiking", "등산"),
                   ("playing an instrument", "악기 연주"), ("reading", "독서")]]),
                ("Personally, I've been really into ____ lately.",
                 "개인적으로 저는 최근에 ____에 푹 빠져 있어요.",
                 [[("learning languages", "언어 배우기"), ("working out", "운동"), ("gardening", "원예"),
                   ("collecting things", "수집"), ("watching documentaries", "다큐 보기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that it allows me to ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 그것이 제가 ____하게 해주기 때문이에요.",
                 [[("express my creativity", "창의력을 발휘하다"), ("escape from daily stress", "일상의 스트레스에서 벗어나다"),
                   ("keep learning", "계속 배우다"), ("challenge myself", "스스로 도전하다"),
                   ("unwind", "긴장을 풀다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I usually ____.",
                 "예를 들어, 저는 보통 ____해요.",
                 [[("set aside time on weekends", "주말에 시간을 내다"), ("practice regularly", "규칙적으로 연습하다"),
                   ("join online communities", "온라인 커뮤니티에 참여하다"), ("try new techniques", "새로운 방법을 시도하다"),
                   ("do it with friends", "친구들과 함께하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, this hobby has become a ____ part of my life.",
                 "전반적으로, 이 취미는 제 삶의 ____ 부분이 됐어요.",
                 [[("meaningful", "의미 있는"), ("rewarding", "보람 있는"), ("essential", "필수적인"),
                   ("enjoyable", "즐거운"), ("defining", "나를 나타내는")]]),
            ]),
        ],
    },
    # ===== U7 =====
    {
        "emoji": "🏃", "title_ko": "운동·건강관리", "title_en": "Exercise & Health",
        "prompt": "How do you stay healthy or active?",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I stay healthy.", "제가 어떻게 건강을 관리하는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the best way to stay in shape.",
                 "제 생각에 ____이(가) 몸매를 유지하는 가장 좋은 방법이에요.",
                 [[("going to the gym", "헬스장 가기"), ("jogging", "조깅"), ("doing yoga", "요가"),
                   ("swimming", "수영"), ("home workouts", "홈트레이닝")]]),
                ("Personally, I try to ____ as much as possible.",
                 "개인적으로 저는 가능한 한 ____하려고 해요.",
                 [[("exercise regularly", "규칙적으로 운동하다"), ("eat a balanced diet", "균형 잡힌 식사를 하다"),
                   ("stay active", "활동적으로 지내다"), ("get enough sleep", "충분히 자다"),
                   ("manage my stress", "스트레스를 관리하다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I make the effort is that it helps me ____.",
                 "제가 노력하는 가장 큰 이유는 그것이 제가 ____하도록 돕기 때문이에요.",
                 [[("stay energetic", "활기차게 지내다"), ("keep fit", "건강을 유지하다"),
                   ("relieve stress", "스트레스를 풀다"), ("boost my mood", "기분을 좋게 하다"),
                   ("stay focused", "집중력을 유지하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I usually ____.",
                 "예를 들어, 저는 보통 ____해요.",
                 [[("work out three times a week", "주 3회 운동하다"), ("take a walk after work", "퇴근 후 걷다"),
                   ("stretch every morning", "매일 아침 스트레칭하다"), ("watch what I eat", "식단을 신경 쓰다"),
                   ("use a fitness app", "운동 앱을 쓰다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, staying healthy keeps me ____.",
                 "결국, 건강을 지키는 것은 저를 ____하게 유지해 줘요.",
                 [[("energetic", "활기찬"), ("focused", "집중된"), ("in good shape", "건강한"),
                   ("positive", "긍정적인"), ("productive", "생산적인")]]),
            ]),
        ],
    },
    # ===== U8 =====
    {
        "emoji": "🍔", "title_ko": "외식·음식", "title_en": "Dining Out & Food",
        "prompt": "Talk about eating out or your favorite food.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about eating out and the food I love.", "외식과 제가 좋아하는 음식에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ cuisine is the most enjoyable.",
                 "제 생각에 ____ 요리가 가장 즐거워요.",
                 [[("Korean", "한식"), ("Italian", "이탈리안"), ("Japanese", "일식"),
                   ("Mexican", "멕시칸"), ("Thai", "태국")]]),
                ("Personally, I tend to prefer ____ dishes.",
                 "개인적으로 저는 ____ 음식을 선호하는 편이에요.",
                 [[("spicy", "매운"), ("savory", "감칠맛 나는"), ("healthy", "건강한"),
                   ("hearty", "든든한"), ("home-style", "집밥 같은")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I love dining out is that I can ____.",
                 "제가 외식을 좋아하는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("try new flavors", "새로운 맛을 보다"), ("treat myself", "나에게 한턱 내다"),
                   ("enjoy time with others", "사람들과 시간을 즐기다"), ("discover local spots", "맛집을 발견하다"),
                   ("take a break from cooking", "요리에서 벗어나다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on special occasions I usually ____.",
                 "예를 들어, 특별한 날엔 저는 보통 ____해요.",
                 [[("book a nice restaurant", "좋은 식당을 예약하다"), ("try a trendy place", "요즘 뜨는 곳에 가보다"),
                   ("order my favorite dish", "좋아하는 음식을 시키다"), ("go out with friends", "친구들과 나가다"),
                   ("explore a new neighborhood", "새 동네를 가보다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, good food is one of life's simple ____.",
                 "전반적으로, 맛있는 음식은 삶의 소소한 ____ 중 하나예요.",
                 [[("pleasures", "즐거움"), ("joys", "기쁨"), ("comforts", "위안"),
                   ("luxuries", "사치"), ("rewards", "보상")]]),
            ]),
        ],
    },
    # ===== U9 =====
    {
        "emoji": "☕", "title_ko": "카페·커피", "title_en": "Cafés & Coffee",
        "prompt": "Talk about cafés or coffee in your life.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about cafés and coffee in my life.", "제 삶 속 카페와 커피에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, a café is the ideal place to ____.",
                 "제 생각에 카페는 ____하기에 이상적인 곳이에요.",
                 [[("get some work done", "일을 하다"), ("catch up with friends", "친구와 이야기하다"),
                   ("relax with a book", "책 보며 쉬다"), ("take a break", "잠시 쉬다"),
                   ("clear my head", "머리를 식히다")]]),
                ("Personally, I usually go for ____.",
                 "개인적으로 저는 보통 ____을(를) 마셔요.",
                 [[("an americano", "아메리카노"), ("a latte", "라떼"), ("a cold brew", "콜드브루"),
                   ("a cappuccino", "카푸치노"), ("herbal tea", "허브차")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I like cafés is that they offer a ____ atmosphere.",
                 "제가 카페를 좋아하는 가장 큰 이유는 ____ 분위기를 주기 때문이에요.",
                 [[("cozy", "아늑한"), ("calm", "차분한"), ("productive", "집중되는"),
                   ("pleasant", "쾌적한"), ("welcoming", "편안한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____ at a café.",
                 "예를 들어, 저는 카페에서 자주 ____해요.",
                 [[("work on my laptop", "노트북으로 일하다"), ("meet colleagues", "동료를 만나다"),
                   ("read for a while", "잠시 책을 읽다"), ("people-watch", "사람 구경을 하다"),
                   ("unwind after work", "퇴근 후 쉬다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, grabbing a coffee is a small daily ____.",
                 "결국, 커피 한잔은 소소한 일상의 ____예요.",
                 [[("ritual", "습관"), ("pleasure", "즐거움"), ("comfort", "위안"),
                   ("treat", "소소한 사치"), ("routine", "일과")]]),
            ]),
        ],
    },
    # ===== U10 =====
    {
        "emoji": "🚄", "title_ko": "국내 여행", "title_en": "Domestic Travel",
        "prompt": "Talk about traveling within your country.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about traveling within Korea.", "국내 여행에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the best domestic destination.",
                 "제 생각에 ____이(가) 최고의 국내 여행지예요.",
                 [[("Jeju Island", "제주도"), ("Busan", "부산"), ("Gangneung", "강릉"),
                   ("Gyeongju", "경주"), ("Jeonju", "전주")]]),
                ("Personally, I prefer to travel ____.",
                 "개인적으로 저는 ____ 여행하는 것을 선호해요.",
                 [[("by train", "기차로"), ("by car", "차로"), ("on a short getaway", "짧은 여행으로"),
                   ("with family", "가족과"), ("off-season", "비수기에")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy it is that I can ____.",
                 "제가 그것을 즐기는 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("recharge from daily life", "일상에서 재충전하다"), ("explore local culture", "지역 문화를 둘러보다"),
                   ("enjoy the scenery", "경치를 즐기다"), ("try regional food", "지역 음식을 먹다"),
                   ("avoid the hassle of flying", "비행의 번거로움을 피하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, last year I ____.",
                 "예를 들어, 작년에 저는 ____했어요.",
                 [[("took a weekend trip to Busan", "주말에 부산에 다녀왔다"), ("drove along the coast", "해안을 따라 드라이브했다"),
                   ("visited a quiet town", "조용한 마을을 방문했다"), ("went hiking in the mountains", "산으로 등산을 갔다"),
                   ("stayed at a nice resort", "좋은 리조트에 묵었다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, a domestic trip is a ____ way to unwind.",
                 "전반적으로, 국내 여행은 쉬기에 ____ 방법이에요.",
                 [[("convenient", "편리한"), ("affordable", "부담 없는"), ("relaxing", "편안한"),
                   ("refreshing", "상쾌한"), ("hassle-free", "번거롭지 않은")]]),
            ]),
        ],
    },
    # ===== U11 =====
    {
        "emoji": "🌍", "title_ko": "해외 여행", "title_en": "Traveling Abroad",
        "prompt": "Talk about traveling abroad.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about traveling to other countries.", "해외 여행에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is a country worth visiting.",
                 "제 생각에 ____은(는) 가볼 만한 나라예요.",
                 [[("Japan", "일본"), ("France", "프랑스"), ("Italy", "이탈리아"),
                   ("the US", "미국"), ("Vietnam", "베트남")]]),
                ("Personally, when I travel I focus on ____.",
                 "개인적으로 여행할 때 저는 ____에 집중해요.",
                 [[("the local culture", "현지 문화"), ("the food", "음식"), ("historic sites", "역사 유적"),
                   ("the nightlife", "밤 문화"), ("meeting locals", "현지인 만나기")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I love it is that it lets me ____.",
                 "제가 그것을 사랑하는 가장 큰 이유는 제가 ____하게 해주기 때문이에요.",
                 [[("broaden my perspective", "시야를 넓히다"), ("step out of my comfort zone", "안전지대에서 벗어나다"),
                   ("experience different cultures", "다른 문화를 경험하다"), ("create lasting memories", "오래 남을 추억을 만들다"),
                   ("recharge completely", "완전히 재충전하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on my last trip I ____.",
                 "예를 들어, 지난 여행에서 저는 ____했어요.",
                 [[("explored the old town", "구시가지를 둘러봤다"), ("tried the local cuisine", "현지 음식을 먹어봤다"),
                   ("visited famous landmarks", "유명 명소를 방문했다"), ("wandered around on foot", "걸어서 돌아다녔다"),
                   ("met interesting people", "흥미로운 사람들을 만났다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, traveling abroad is always an ____ experience.",
                 "결국, 해외 여행은 언제나 ____ 경험이에요.",
                 [[("eye-opening", "견문을 넓히는"), ("unforgettable", "잊지 못할"), ("enriching", "풍요롭게 하는"),
                   ("exciting", "신나는"), ("rewarding", "보람 있는")]]),
            ]),
        ],
    },
    # ===== U12 =====
    {
        "emoji": "🎬", "title_ko": "영화·드라마", "title_en": "Movies & Dramas",
        "prompt": "Talk about the movies or shows you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the movies and shows I enjoy.", "제가 즐기는 영화와 드라마에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ are the most engaging to watch.",
                 "제 생각에 ____이(가) 보기에 가장 몰입돼요.",
                 [[("thrillers", "스릴러"), ("dramas", "드라마"), ("documentaries", "다큐멘터리"),
                   ("comedies", "코미디"), ("sci-fi films", "SF 영화")]]),
                ("Personally, I'm drawn to stories with ____.",
                 "개인적으로 저는 ____이(가) 있는 이야기에 끌려요.",
                 [[("a gripping plot", "몰입되는 줄거리"), ("well-written characters", "잘 그려진 인물"),
                   ("a deep message", "깊은 메시지"), ("unexpected twists", "반전"),
                   ("strong emotion", "강한 감정")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I enjoy them is that they ____.",
                 "제가 그것들을 즐기는 가장 큰 이유는 그것들이 ____하기 때문이에요.",
                 [[("let me escape reality", "현실에서 벗어나게 하다"), ("make me think", "생각하게 하다"),
                   ("resonate with me", "공감을 주다"), ("keep me on the edge of my seat", "손에 땀을 쥐게 하다"),
                   ("help me unwind", "쉬게 해주다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I recently watched ____.",
                 "예를 들어, 저는 최근에 ____을(를) 봤어요.",
                 [[("a critically acclaimed film", "평이 좋은 영화"), ("a binge-worthy series", "정주행할 만한 시리즈"),
                   ("a thought-provoking documentary", "생각거리를 주는 다큐"), ("a classic movie", "고전 영화"),
                   ("a popular drama", "인기 드라마")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, films and shows are my favorite way to ____.",
                 "전반적으로, 영화와 드라마는 제가 가장 좋아하는 ____ 방법이에요.",
                 [[("relax", "쉬는"), ("unwind", "긴장을 푸는"), ("escape", "벗어나는"),
                   ("recharge", "재충전하는"), ("spend an evening", "저녁을 보내는")]]),
            ]),
        ],
    },
    # ===== U13 =====
    {
        "emoji": "🎵", "title_ko": "음악", "title_en": "Music",
        "prompt": "Talk about the music you listen to.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the music I listen to.", "제가 듣는 음악에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most enjoyable genre.",
                 "제 생각에 ____이(가) 가장 즐거운 장르예요.",
                 [[("pop", "팝"), ("jazz", "재즈"), ("indie", "인디"),
                   ("classical", "클래식"), ("hip-hop", "힙합")]]),
                ("Personally, I listen to music mostly ____.",
                 "개인적으로 저는 주로 ____ 음악을 들어요.",
                 [[("while commuting", "출퇴근하며"), ("when I work out", "운동할 때"), ("to relax", "쉬려고"),
                   ("while working", "일하면서"), ("to lift my mood", "기분을 띄우려고")]]),
            ]),
            _step("③ 이유", [
                ("The main reason music matters to me is that it ____.",
                 "음악이 제게 중요한 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("sets the mood", "분위기를 만든다"), ("helps me focus", "집중하게 한다"),
                   ("lifts my spirits", "기운을 북돋운다"), ("brings back memories", "추억을 떠올리게 한다"),
                   ("keeps me company", "함께해 준다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I often ____.",
                 "예를 들어, 저는 자주 ____해요.",
                 [[("make my own playlists", "내 플레이리스트를 만들다"), ("discover new artists", "새 아티스트를 발견하다"),
                   ("go to live concerts", "라이브 콘서트에 가다"), ("listen on my way to work", "출근길에 듣다"),
                   ("sing along", "따라 부르다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, music is an ____ part of my daily life.",
                 "결국, 음악은 제 일상의 ____ 부분이에요.",
                 [[("essential", "필수적인"), ("inseparable", "뗄 수 없는"), ("important", "중요한"),
                   ("enjoyable", "즐거운"), ("everyday", "일상적인")]]),
            ]),
        ],
    },
    # ===== U14 =====
    {
        "emoji": "🛒", "title_ko": "쇼핑", "title_en": "Shopping",
        "prompt": "Talk about your shopping habits.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about my shopping habits.", "제 쇼핑 습관에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most convenient way to shop.",
                 "제 생각에 ____이(가) 가장 편리한 쇼핑 방법이에요.",
                 [[("online shopping", "온라인 쇼핑"), ("shopping at malls", "몰에서 쇼핑"),
                   ("visiting local stores", "동네 가게"), ("using delivery apps", "배달 앱 이용"),
                   ("second-hand markets", "중고 거래")]]),
                ("Personally, I usually shop for ____.",
                 "개인적으로 저는 보통 ____을(를) 사요.",
                 [[("clothes", "옷"), ("groceries", "식료품"), ("electronics", "전자제품"),
                   ("household items", "생활용품"), ("gifts", "선물")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I prefer it is that it is ____.",
                 "제가 그것을 선호하는 가장 큰 이유는 그것이 ____하기 때문이에요.",
                 [[("quick and easy", "빠르고 쉬운"), ("budget-friendly", "부담 없는"),
                   ("time-saving", "시간을 아끼는"), ("hassle-free", "번거롭지 않은"),
                   ("full of options", "선택지가 많은")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I tend to ____.",
                 "예를 들어, 저는 ____하는 편이에요.",
                 [[("compare prices before buying", "사기 전에 가격을 비교하다"), ("wait for sales", "세일을 기다리다"),
                   ("stick to a budget", "예산을 지키다"), ("read reviews first", "후기를 먼저 읽다"),
                   ("buy only what I need", "필요한 것만 사다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, I try to be a ____ shopper.",
                 "전반적으로, 저는 ____ 소비자가 되려고 해요.",
                 [[("smart", "현명한"), ("practical", "실용적인"), ("mindful", "신중한"),
                   ("budget-conscious", "예산을 의식하는"), ("savvy", "요령 있는")]]),
            ]),
        ],
    },
    # ===== U15 =====
    {
        "emoji": "📱", "title_ko": "기술·스마트폰", "title_en": "Technology & Smartphones",
        "prompt": "Talk about how technology affects your life.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how technology shapes my life.", "기술이 제 삶에 어떤 영향을 주는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ has changed my daily life the most.",
                 "제 생각에 ____이(가) 제 일상을 가장 많이 바꿨어요.",
                 [[("the smartphone", "스마트폰"), ("social media", "소셜미디어"), ("online shopping", "온라인 쇼핑"),
                   ("streaming services", "스트리밍"), ("mobile banking", "모바일 뱅킹")]]),
                ("Personally, I rely on technology to ____.",
                 "개인적으로 저는 ____하려고 기술에 의존해요.",
                 [[("stay connected", "연락을 유지하다"), ("get things done", "일을 처리하다"),
                   ("find information", "정보를 찾다"), ("manage my schedule", "일정을 관리하다"),
                   ("entertain myself", "여가를 즐기다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason it's so useful is that it makes life more ____.",
                 "그것이 아주 유용한 가장 큰 이유는 삶을 더 ____하게 만들기 때문이에요.",
                 [[("convenient", "편리한"), ("efficient", "효율적인"), ("connected", "연결된"),
                   ("productive", "생산적인"), ("flexible", "유연한")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I use my phone to ____.",
                 "예를 들어, 저는 휴대폰으로 ____해요.",
                 [[("check emails", "이메일을 확인하다"), ("pay for things", "결제하다"),
                   ("navigate around", "길을 찾다"), ("keep in touch", "연락하다"),
                   ("order food", "음식을 주문하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("That said, I try to use technology ____.",
                 "그렇긴 하지만, 저는 기술을 ____ 쓰려고 해요.",
                 [[("in moderation", "적당히"), ("mindfully", "신중하게"), ("responsibly", "책임감 있게"),
                   ("wisely", "현명하게"), ("without overdoing it", "과하지 않게")]]),
            ]),
        ],
    },
    # ===== U16 =====
    {
        "emoji": "💬", "title_ko": "SNS·인터넷", "title_en": "Social Media",
        "prompt": "Talk about how you use social media.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I use social media.", "제가 SNS를 어떻게 쓰는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most useful platform.",
                 "제 생각에 ____이(가) 가장 유용한 플랫폼이에요.",
                 [[("Instagram", "인스타그램"), ("YouTube", "유튜브"), ("KakaoTalk", "카카오톡"),
                   ("LinkedIn", "링크드인"), ("a blog", "블로그")]]),
                ("Personally, I mainly use it to ____.",
                 "개인적으로 저는 주로 ____하려고 그것을 써요.",
                 [[("keep up with friends", "친구 소식을 접하다"), ("follow my interests", "관심사를 팔로우하다"),
                   ("share moments", "순간을 공유하다"), ("get news", "소식을 얻다"),
                   ("network", "인맥을 쌓다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason it's handy is that I can ____.",
                 "그것이 편리한 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("stay informed", "정보를 얻다"), ("connect with others", "사람들과 연결되다"),
                   ("express myself", "나를 표현하다"), ("discover new things", "새로운 걸 발견하다"),
                   ("kill time", "시간을 보내다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, I usually ____.",
                 "예를 들어, 저는 보통 ____해요.",
                 [[("scroll through my feed", "피드를 훑어보다"), ("post occasionally", "가끔 게시하다"),
                   ("message friends", "친구에게 메시지하다"), ("watch short videos", "짧은 영상을 보다"),
                   ("save useful posts", "유용한 글을 저장하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("That said, I try not to ____.",
                 "그렇긴 하지만, 저는 ____하지 않으려고 해요.",
                 [[("spend too much time on it", "너무 오래 하다"), ("compare myself to others", "남과 비교하다"),
                   ("take it too seriously", "지나치게 진지하게 여기다"), ("rely on it too much", "지나치게 의존하다"),
                   ("get distracted", "주의가 흐트러지다")]]),
            ]),
        ],
    },
    # ===== U17 =====
    {
        "emoji": "⛅", "title_ko": "날씨·계절", "title_en": "Weather & Seasons",
        "prompt": "Talk about the weather or your favorite season.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about the weather and my favorite season.", "날씨와 제가 좋아하는 계절에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most pleasant season.",
                 "제 생각에 ____이(가) 가장 쾌적한 계절이에요.",
                 [[("autumn", "가을"), ("spring", "봄"), ("early summer", "초여름"),
                   ("winter", "겨울"), ("late spring", "늦봄")]]),
                ("Personally, I much prefer ____ weather.",
                 "개인적으로 저는 ____ 날씨를 훨씬 좋아해요.",
                 [[("mild", "온화한"), ("crisp", "상쾌한"), ("sunny", "맑은"),
                   ("cool", "시원한"), ("dry", "건조한")]]),
            ]),
            _step("③ 이유", [
                ("The main reason is that ____.",
                 "가장 큰 이유는 ____이기 때문이에요.",
                 [[("the temperature is just right", "기온이 딱 좋다"),
                   ("it's perfect for outdoor activities", "야외 활동에 완벽하다"),
                   ("the scenery is beautiful", "경치가 아름답다"), ("I feel more energetic", "더 활기차진다"),
                   ("it lifts my mood", "기분이 좋아진다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, during that season I like to ____.",
                 "예를 들어, 그 계절에 저는 ____하는 걸 좋아해요.",
                 [[("go for long walks", "오래 산책하다"), ("spend time outdoors", "야외에서 시간을 보내다"),
                   ("take short trips", "짧은 여행을 하다"), ("enjoy the scenery", "경치를 즐기다"),
                   ("meet friends outside", "밖에서 친구를 만나다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, the weather has a real impact on my ____.",
                 "전반적으로, 날씨는 제 ____에 실제로 영향을 줘요.",
                 [[("mood", "기분"), ("energy", "활력"), ("plans", "계획"),
                   ("productivity", "생산성"), ("daily routine", "일상")]]),
            ]),
        ],
    },
    # ===== U18 =====
    {
        "emoji": "🎉", "title_ko": "명절·모임", "title_en": "Holidays & Gatherings",
        "prompt": "Talk about holidays or get-togethers you enjoy.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about holidays and gatherings I enjoy.", "제가 즐기는 명절과 모임에 대해 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, ____ is the most meaningful holiday.",
                 "제 생각에 ____이(가) 가장 의미 있는 명절이에요.",
                 [[("Chuseok", "추석"), ("Lunar New Year", "설날"), ("Christmas", "크리스마스"),
                   ("New Year's", "새해"), ("a family birthday", "가족 생일")]]),
                ("Personally, what I enjoy most is ____.",
                 "개인적으로 제가 가장 즐기는 건 ____예요.",
                 [[("getting together with family", "가족과 모이는 것"), ("the festive atmosphere", "명절 분위기"),
                   ("the traditional food", "전통 음식"), ("the time off", "쉬는 시간"),
                   ("catching up with relatives", "친척과 만나는 것")]]),
            ]),
            _step("③ 이유", [
                ("The main reason it matters to me is that I can ____.",
                 "그것이 제게 중요한 가장 큰 이유는 제가 ____할 수 있기 때문이에요.",
                 [[("reconnect with loved ones", "가까운 사람들과 다시 만나다"), ("take a proper break", "제대로 쉬다"),
                   ("keep traditions alive", "전통을 이어가다"), ("recharge", "재충전하다"),
                   ("appreciate what I have", "가진 것에 감사하다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, on holidays we usually ____.",
                 "예를 들어, 명절에 우리는 보통 ____해요.",
                 [[("gather for a big meal", "함께 식사를 하다"), ("visit relatives", "친척을 방문하다"),
                   ("exchange gifts", "선물을 주고받다"), ("share stories", "이야기를 나누다"),
                   ("take family photos", "가족사진을 찍다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, these gatherings are a ____ part of the year.",
                 "결국, 이런 모임은 한 해의 ____ 부분이에요.",
                 [[("special", "특별한"), ("meaningful", "의미 있는"), ("cherished", "소중한"),
                   ("memorable", "기억에 남는"), ("joyful", "즐거운")]]),
            ]),
        ],
    },
    # ===== U19 =====
    {
        "emoji": "📈", "title_ko": "자기계발", "title_en": "Self-Development",
        "prompt": "Talk about how you try to improve yourself.",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I try to grow.", "제가 어떻게 성장하려 하는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the best way to grow is ____.",
                 "제 생각에 성장하는 가장 좋은 방법은 ____예요.",
                 [[("learning new skills", "새 기술 배우기"), ("reading regularly", "꾸준히 독서하기"),
                   ("setting clear goals", "명확한 목표 세우기"), ("stepping out of my comfort zone", "안전지대 벗어나기"),
                   ("reflecting on myself", "자기 성찰하기")]]),
                ("Personally, I've been working on ____.",
                 "개인적으로 저는 ____에 힘쓰고 있어요.",
                 [[("improving my English", "영어 실력 향상"), ("managing my time better", "시간 관리"),
                   ("building good habits", "좋은 습관 만들기"), ("learning something new", "새로운 것 배우기"),
                   ("staying disciplined", "자기 관리")]]),
            ]),
            _step("③ 이유", [
                ("The main reason I make the effort is that I want to ____.",
                 "제가 노력하는 가장 큰 이유는 제가 ____하고 싶기 때문이에요.",
                 [[("keep growing", "계속 성장하다"), ("reach my goals", "목표를 이루다"),
                   ("stay competitive", "경쟁력을 유지하다"), ("feel a sense of progress", "성장을 느끼다"),
                   ("better myself", "더 나아지다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, these days I ____.",
                 "예를 들어, 요즘 저는 ____해요.",
                 [[("take online courses", "온라인 강의를 듣다"), ("read before bed", "자기 전에 책을 읽다"),
                   ("set weekly goals", "주간 목표를 세우다"), ("track my progress", "진행 상황을 기록하다"),
                   ("practice consistently", "꾸준히 연습하다")]]),
            ]),
            _step("⑤ 마무리", [
                ("Overall, self-development keeps me ____.",
                 "전반적으로, 자기계발은 저를 ____하게 유지해 줘요.",
                 [[("motivated", "동기부여된"), ("focused", "집중된"), ("fulfilled", "충족된"),
                   ("moving forward", "앞으로 나아가는"), ("confident", "자신감 있는")]]),
            ]),
        ],
    },
    # ===== U20 =====
    {
        "emoji": "😌", "title_ko": "스트레스·워라밸", "title_en": "Stress & Work-Life Balance",
        "prompt": "How do you manage stress and balance your life?",
        "template": [
            _step("① 주제 소개", [
                ("Let me talk about how I manage stress.", "제가 스트레스를 어떻게 관리하는지 이야기할게요.", []),
            ]),
            _step("② 내 의견·선호", [
                ("In my opinion, the key to a good balance is ____.",
                 "제 생각에 좋은 균형의 핵심은 ____예요.",
                 [[("setting boundaries", "경계를 정하는 것"), ("making time to rest", "쉴 시간을 갖는 것"),
                   ("staying organized", "정리된 상태 유지"), ("knowing my limits", "내 한계를 아는 것"),
                   ("prioritizing what matters", "중요한 것을 우선하는 것")]]),
                ("Personally, when I'm stressed I tend to ____.",
                 "개인적으로 스트레스를 받으면 저는 ____하는 편이에요.",
                 [[("take a break", "잠시 쉬다"), ("go for a walk", "산책하다"), ("talk it out", "털어놓다"),
                   ("exercise", "운동하다"), ("do something I enjoy", "좋아하는 걸 하다")]]),
            ]),
            _step("③ 이유", [
                ("The main reason it works is that it helps me ____.",
                 "그것이 효과적인 가장 큰 이유는 제가 ____하도록 돕기 때문이에요.",
                 [[("clear my mind", "머리를 비우다"), ("calm down", "진정하다"),
                   ("regain perspective", "시야를 되찾다"), ("recharge", "재충전하다"),
                   ("let go of tension", "긴장을 풀다")]]),
            ]),
            _step("④ 예시·경험", [
                ("For example, after a stressful day I usually ____.",
                 "예를 들어, 스트레스 많은 하루가 끝나면 저는 보통 ____해요.",
                 [[("switch off from work", "일에서 벗어나다"), ("spend time on a hobby", "취미에 시간을 쓰다"),
                   ("get some rest", "휴식을 취하다"), ("meet a close friend", "가까운 친구를 만나다"),
                   ("unplug for a while", "잠시 전자기기를 끄다")]]),
            ]),
            _step("⑤ 마무리", [
                ("All in all, managing stress well keeps me ____.",
                 "결국, 스트레스를 잘 관리하는 것은 저를 ____하게 유지해 줘요.",
                 [[("balanced", "균형 잡힌"), ("healthy", "건강한"), ("level-headed", "침착한"),
                   ("productive", "생산적인"), ("at peace", "평온한")]]),
            ]),
        ],
    },
]
