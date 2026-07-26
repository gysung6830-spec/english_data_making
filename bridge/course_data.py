# -*- coding: utf-8 -*-
"""영어, 처음부터 다시 — 기초 문법·해석 교재 데이터.

문법을 아예 모르는 학생을 위해, 하루 DAY 하나씩 아주 작게.
쉬운 예문으로 개념을 잡고, 마지막에 '우리 지문(모기, 천재 공통영어2 L1)' 문장으로 적용한다.

DAY 구조:
  no, title, goal,
  intro_html, note1,
  concept_title, concept_html,
  rule_title, rules[{label, html}]  (없으면 섹션 번호 자동 조정),
  worked[{sent, lines[], note}],
  practice_intro, practice[{sent, hint}], answbox_labels[],
  vocab[{en, ko, pos}],
  textbook_intro, textbook[{sent, lines[]}],
  answers_html
"""

# ============================================================
# 표지
# ============================================================
COVER = {
    "title": "영어, 처음부터 다시",
    "subtitle": "문법을 하나도 몰라도 시작하는 기초 문법·해석 교재",
    "tag": "고1 2학기 내신 대비 · DAY 1–2 샘플",
    "book": "적용 지문 : 2022 개정 천재(강상구) 공통영어2 · Lesson 1 (모기 이야기)",
    "intro": [
        "중학 문법을 <b>하나도 몰라도</b> 시작할 수 있게 만들었어요.",
        "문법 용어를 외우는 게 목적이 아니에요. 문장이 <b>&ldquo;읽히게&rdquo;</b> 만드는 게 목적이에요.",
        "하루 한 DAY, <b>아주 작게</b> 한 개념씩만 배웁니다.",
        "개념은 <b>쉬운 예문</b>으로, 마지막 적용은 <b>우리 학교 교과서(모기 지문)</b> 문장으로 합니다.",
    ],
}

# ============================================================
# 글 전체 내용 한 페이지
# ============================================================
OVERVIEW = {
    "source": "2022 개정 천재(강상구) 공통영어2 · Lesson 1 · The Nuisance / The Predator",
    "oneline": "한 문장 요약 &nbsp;→&nbsp; \"작고 성가신 모기가, 사실은 인류 역사상 가장 많은 사람을 죽인 무서운 존재였다.\"",
    "parts": [
        {"title": "PART 1. 성가신 존재", "en": "The Nuisance",
         "body": "캠핑을 갔는데 <b>모기</b>가 윙윙거리며 다가와 피부를 뚫고 피를 빨아요. 그 자리가 가렵고 빨갛게 붓죠. "
                 "모기는 우리가 내쉬는 <b>이산화탄소</b>, 땀 냄새, 체온을 감지해 먹잇감을 찾아요. "
                 "피를 빠는 건 <b>암컷</b>뿐인데, <b>알을 낳을 단백질</b>이 필요하기 때문이에요. 배불리 피를 빨고 물웅덩이에 알을 낳습니다."},
        {"title": "PART 2. 포식자", "en": "The Predator",
         "body": "자연에서 인간을 가장 많이 죽인 동물은 상어·사자·곰이 아니라 <b>모기</b>예요. "
                 "모기가 옮기는 <b>말라리아·황열</b>로 매년 100만 명 넘게 죽고, 역사상 약 <b>520억 명</b>이 목숨을 잃었대요. "
                 "모기는 <b>로마 제국의 몰락</b>, <b>스코틀랜드의 식민지 실패</b>에도 영향을 줬어요. "
                 "사람들은 19세기 말이 되어서야 모기가 병을 옮긴다는 걸 알았고, 결국 <b>인간의 역사도 자연의 영향</b>에서 자유롭지 않다는 걸 깨닫죠."},
    ],
    "flow": [
        {"h": "모기가 문다", "t": "피부를 뚫고<br>피를 빤다"},
        {"h": "먹잇감 찾기", "t": "CO2·땀·체온<br>감지"},
        {"h": "왜 무나", "t": "암컷이 알 낳을<br>단백질 필요"},
        {"h": "역사를 바꾼 포식자", "t": "말라리아로<br>제국까지 흔듦"},
    ],
    "extra": "<b>본문 외 지문</b> : 정원에 <b>이로운 벌레</b> 이야기 — 무당벌레(진딧물을 먹어 식물을 지킴), 지렁이(흙을 비옥하고 부드럽게 함).",
}


# ============================================================
# DAY 1 — 문장의 뼈대 (주어 + 동사)
# ============================================================
DAY1 = {
    "no": 1,
    "title": "영어 문장에도 뼈대가 있다",
    "goal": "아무리 긴 문장이라도 <b>&ldquo;누가 / 뭐했다&rdquo;</b> 두 개를 먼저 찾을 수 있게 된다.",
    "intro_html": """
      <p>영어가 안 읽히는 이유가 <b>단어를 몰라서</b>라고 생각하죠? 반은 맞고 반은 틀려요.</p>
      <p>진짜 이유는 문장에서 <b>뭐가 중요한지</b>를 못 골라내서예요. 영어 문장은 사람 몸이랑 똑같아요.
      <b>뼈대</b>가 있고, 거기에 <b>살</b>이 붙어 있어요.</p>
      <p class="keyline"><b>뼈대 = 누가(주어) + 뭐했다(동사).</b> 나머지는 전부 살이에요. 살은 몰라도 됩니다. 진짜로요.</p>
    """,
    "note1": "우리 오늘 목표는 &ldquo;완벽한 해석&rdquo;이 아니에요. 문장 보고 <b>&ldquo;누가 뭐했는지&rdquo;</b>만 말할 수 있으면 오늘은 성공이에요.",
    "concept_title": "단어는 4가지 역할 중 하나를 맡아요",
    "concept_html": """
      <table class="concept">
        <thead><tr><th>이름</th><th>하는 일</th><th>한국어로 치면</th><th>영어 예시</th></tr></thead>
        <tbody>
          <tr><td><b>명사</b></td><td>이름을 나타내요 (누가/무엇)</td><td>학생, 물, 학교</td><td class="en">student, water, school</td></tr>
          <tr><td><b>동사</b></td><td>움직임·상태 (~하다/~이다)</td><td>뛰다, 좋아하다, ~이다</td><td class="en">run, like, is</td></tr>
          <tr><td><b>형용사</b></td><td>명사를 꾸며요 (어떤?)</td><td>예쁜, 큰, 오래된</td><td class="en">pretty, big, old</td></tr>
          <tr><td><b>부사</b></td><td>동사를 꾸며요 (어떻게/언제?)</td><td>빨리, 어제, 정말</td><td class="en">fast, yesterday, really</td></tr>
        </tbody>
      </table>
      <div class="keyline">여기서 딱 두 개만 기억하세요. <b>명사 = 누가</b>, &nbsp; <b>동사 = 뭐했다.</b></div>
    """,
    "rule_title": "뼈대 찾는 법 (2단계)",
    "rules": [
        {"label": "STEP 1 — 동사부터 찾는다",
         "html": "&ldquo;~하다 / ~이다&rdquo;로 끝나는 말을 찾으세요. 문장에 반드시 하나는 있어요.<br>"
                 "<b>is, are, was, plays, studied, looks …</b> 이런 애들이 동사예요."},
        {"label": "STEP 2 — 동사 앞을 본다",
         "html": "동사 바로 앞쪽에 있는 명사가 <b>주어</b>예요. &ldquo;누가?&rdquo;에 답이 되는 말이죠.<br>"
                 "앞에 단어가 여러 개 붙어 있어도 당황하지 마세요. 그건 다 꾸며주는 <b>살</b>이에요."},
    ],
    "worked": [
        {"sent": "My brother plays soccer every day.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>plays</span> (한다 → 동사!)",
                   "<span class='q'>동사 앞은?</span> My brother (내 형/동생)",
                   "<span class='q'>뼈대는?</span> <span class='bone'>내 형이 한다</span>",
                   "<span class='q'>나머지는?</span> soccer(뭘?), every day(언제?) → 살"],
         "note": "every day 를 몰라도 &ldquo;내 형이 축구를 한다&rdquo;는 나왔죠? 이게 뼈대의 힘이에요."},
        {"sent": "The old man in the park looks happy.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>looks</span> (~해 보인다)",
                   "<span class='q'>동사 앞은?</span> The old man in the park … 근데 이게 다 주어일까요?",
                   "<span class='q'>핵심만!</span> the old man (그 노인) — in the park 는 &lsquo;어디에 있는&rsquo;을 알려주는 살",
                   "<span class='q'>뼈대는?</span> <span class='bone'>그 노인이 행복해 보인다</span>"],
         "note": "주어가 길어 보이면 겁먹지 말고 &ldquo;진짜 누구?&rdquo;만 물어보세요. <b>공원</b>이 행복해 보이는 게 아니잖아요."},
        {"sent": "She studied English last night.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>studied</span> (공부했다 — 과거형)",
                   "<span class='q'>동사 앞은?</span> She (그녀가)",
                   "<span class='q'>뼈대는?</span> <span class='bone'>그녀가 공부했다</span>"],
         "note": "studied 에 <b>-ed</b> 가 붙었죠? 이건 &ldquo;이미 지나간 일&rdquo;이라는 표시예요. 뒤 DAY에서 제대로 배울 거예요."},
    ],
    "practice_intro": "주어와 동사를 찾아 쓰고, <b>뼈대만</b> 우리말로 써보세요. 살(꾸미는 말)은 몰라도 괜찮아요.",
    "practice": [
        {"sent": "My sister likes pizza.", "hint": None},
        {"sent": "The students in my class are very kind.", "hint": "주어가 길어요. &ldquo;진짜 누가?&rdquo;만 잡으세요."},
        {"sent": "He watched a movie yesterday.", "hint": None},
        {"sent": "The girl with long hair sings well.", "hint": "with long hair 는 살이에요."},
    ],
    "answbox_labels": ["주어(누가)", "동사(뭐했나)", "뼈대 해석"],
    "vocab": [
        {"en": "brother", "ko": "남자 형제 (형/오빠/남동생)", "pos": "명사"},
        {"en": "sister", "ko": "여자 형제 (누나/언니/여동생)", "pos": "명사"},
        {"en": "soccer", "ko": "축구", "pos": "명사"},
        {"en": "park", "ko": "공원", "pos": "명사"},
        {"en": "student", "ko": "학생", "pos": "명사"},
        {"en": "movie", "ko": "영화", "pos": "명사"},
        {"en": "play", "ko": "(운동을) 하다, 놀다", "pos": "동사"},
        {"en": "look", "ko": "~해 보이다, 보다", "pos": "동사"},
        {"en": "study", "ko": "공부하다", "pos": "동사"},
        {"en": "watch", "ko": "보다, 지켜보다", "pos": "동사"},
        {"en": "like", "ko": "좋아하다", "pos": "동사"},
        {"en": "sing", "ko": "노래하다", "pos": "동사"},
        {"en": "old", "ko": "오래된, 나이 든", "pos": "형용사"},
        {"en": "kind", "ko": "친절한", "pos": "형용사"},
        {"en": "yesterday", "ko": "어제", "pos": "부사"},
    ],
    "textbook_intro": "이제 우리 지문(모기 이야기)의 진짜 문장으로 연습해요. 어려워 보여도 <b>뼈대(누가/뭐했다)</b>만 찾으면 됩니다!",
    "textbook": [
        {"sent": "A mosquito sneaks in.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>sneaks in</span> (몰래 들어온다)",
                   "<span class='q'>주어는?</span> A mosquito (모기 한 마리)",
                   "<span class='q'>뼈대는?</span> <span class='bone'>모기가 몰래 들어온다</span>"]},
        {"sent": "It fills its belly with blood.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>fills</span> (채운다)",
                   "<span class='q'>주어는?</span> It (그것 = 모기)",
                   "<span class='q'>뼈대는?</span> <span class='bone'>그것이 채운다</span> &nbsp;(with blood=피로, its belly=배를 → 살)"]},
        {"sent": "Only females bite us.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>bite</span> (문다)",
                   "<span class='q'>주어는?</span> females (암컷들) — only는 &lsquo;오직&rsquo;이라는 살",
                   "<span class='q'>뼈대는?</span> <span class='bone'>암컷이 문다</span>"]},
    ],
    "answers_html": """
      <p><b>1.</b> 주어 My sister / 동사 likes / 뼈대: 내 여동생(누나·언니)이 좋아한다</p>
      <p><b>2.</b> 주어 The students(학생들) / 동사 are / 뼈대: 학생들은 친절하다 &nbsp;(in my class=우리 반의 → 살)</p>
      <p><b>3.</b> 주어 He / 동사 watched / 뼈대: 그가 봤다 &nbsp;(a movie=영화를, yesterday=어제 → 살)</p>
      <p><b>4.</b> 주어 The girl(그 소녀) / 동사 sings / 뼈대: 그 소녀가 노래한다 &nbsp;(with long hair=긴 머리의 → 살)</p>
    """,
}


# ============================================================
# DAY 2 — be동사
# ============================================================
DAY2 = {
    "no": 2,
    "title": "be동사 — \"~이다\"를 담당하는 동사",
    "goal": "<b>am / are / is / was / were</b> 를 보면 &ldquo;아, ~이다구나&rdquo; 하고 바로 알아본다.",
    "intro_html": """
      <p>영어 동사는 크게 두 종류예요. 움직임을 나타내는 동사(run, eat, study)와,
      그냥 <b>&ldquo;~이다 / ~에 있다&rdquo;</b>만 말하는 동사. 후자를 <b>be동사</b>라고 불러요.</p>
      <p class="keyline">be동사는 딱 다섯 개뿐이에요. <b>am, are, is, was, were.</b> 이 다섯 개만 알면 오늘 절반은 끝납니다.</p>
    """,
    "note1": "be동사는 뜻이 거의 없어요. <b>&ldquo;= (같다)&rdquo;</b> 기호라고 생각하세요. &nbsp;I am a student → 나 = 학생.",
    "concept_title": "주어에 따라 모양이 바뀝니다",
    "concept_html": """
      <table class="concept">
        <thead><tr><th>주어</th><th>현재 (~이다)</th><th>과거 (~였다)</th><th>예문</th></tr></thead>
        <tbody>
          <tr><td><b>I</b> (나)</td><td class="en">am</td><td class="en">was</td><td class="en">I am tired.</td></tr>
          <tr><td><b>You / We / They</b> (너·우리·그들)</td><td class="en">are</td><td class="en">were</td><td class="en">They are my friends.</td></tr>
          <tr><td><b>He / She / It</b> (그·그녀·그것)</td><td class="en">is</td><td class="en">was</td><td class="en">She is a teacher.</td></tr>
          <tr><td><b>단수명사</b> (하나)</td><td class="en">is</td><td class="en">was</td><td class="en">The cat is cute.</td></tr>
          <tr><td><b>복수명사</b> (둘 이상)</td><td class="en">are</td><td class="en">were</td><td class="en">The cats are cute.</td></tr>
        </tbody>
      </table>
      <div class="keyline">규칙은 하나예요. <b>주어가 하나면 is, 여럿이면 are, 나는 am.</b> &nbsp;(과거는 is·단수→was, are·복수→were)</div>
    """,
    "rule_title": None,
    "rules": None,
    "worked": [
        {"sent": "My mother is a nurse.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>is</span> (be동사!)",
                   "<span class='q'>주어는?</span> My mother (우리 엄마)",
                   "<span class='q'>뼈대는?</span> <span class='bone'>우리 엄마는 간호사이다</span> (엄마 = 간호사)"],
         "note": "is 앞뒤를 &ldquo;=&rdquo;로 이어보세요. My mother = a nurse. 이게 be동사의 전부예요."},
        {"sent": "The books on the desk are new.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>are</span>",
                   "<span class='q'>왜 are?</span> books 가 여럿(복수)이니까요. on the desk 에 속으면 안 돼요.",
                   "<span class='q'>뼈대는?</span> <span class='bone'>그 책들은 새것이다</span>"],
         "note": "시험에 진짜 자주 나와요. 동사 바로 앞 단어(desk)가 아니라 <b>진짜 주어</b>(books)에 맞춘다는 것!"},
        {"sent": "We were very hungry last night.",
         "lines": ["<span class='q'>동사는?</span> <span class='hl'>were</span> (was/were 는 과거)",
                   "<span class='q'>주어는?</span> We (우리는)",
                   "<span class='q'>뼈대는?</span> <span class='bone'>우리는 배가 고팠다</span>"],
         "note": "were 가 보이면 &ldquo;지난 일이구나&rdquo; 하고 바로 과거로 해석하세요."},
    ],
    "practice_intro": "빈칸에 알맞은 be동사를 쓰고, 뼈대를 우리말로 써보세요.",
    "practice": [
        {"sent": "I ______ a high school student.", "hint": "나 → ?"},
        {"sent": "My friends ______ in the library now.", "hint": "친구들 → 여럿"},
        {"sent": "The movie ______ really boring yesterday.", "hint": "어제 → 과거"},
        {"sent": "The children in the room ______ noisy.", "hint": "진짜 주어는 children (아이들)"},
    ],
    "answbox_labels": ["빈칸 be동사", "주어(누가)", "뼈대 해석"],
    "vocab": [
        {"en": "mother", "ko": "어머니, 엄마", "pos": "명사"},
        {"en": "nurse", "ko": "간호사", "pos": "명사"},
        {"en": "teacher", "ko": "선생님", "pos": "명사"},
        {"en": "library", "ko": "도서관", "pos": "명사"},
        {"en": "desk", "ko": "책상", "pos": "명사"},
        {"en": "children", "ko": "아이들 (child의 복수)", "pos": "명사"},
        {"en": "friend", "ko": "친구", "pos": "명사"},
        {"en": "tired", "ko": "피곤한", "pos": "형용사"},
        {"en": "hungry", "ko": "배고픈", "pos": "형용사"},
        {"en": "new", "ko": "새로운", "pos": "형용사"},
        {"en": "cute", "ko": "귀여운", "pos": "형용사"},
        {"en": "boring", "ko": "지루한", "pos": "형용사"},
        {"en": "noisy", "ko": "시끄러운", "pos": "형용사"},
        {"en": "really", "ko": "정말로", "pos": "부사"},
        {"en": "now", "ko": "지금", "pos": "부사"},
    ],
    "textbook_intro": "우리 지문(모기)에도 be동사가 나와요. is / are / was 를 찾아 &ldquo;= (같다)&rdquo;로 이어 읽어 보세요.",
    "textbook": [
        {"sent": "You are on a camping trip.",
         "lines": ["<span class='q'>be동사는?</span> <span class='hl'>are</span> (주어 You → are)",
                   "<span class='q'>뜻은?</span> 여기 are 는 &lsquo;~에 있다/~하는 중이다&rsquo;",
                   "<span class='q'>뼈대는?</span> <span class='bone'>너는 캠핑 여행 중이다</span>"]},
        {"sent": "This is a mild allergic reaction.",
         "lines": ["<span class='q'>be동사는?</span> <span class='hl'>is</span> (주어 This=하나 → is)",
                   "<span class='q'>=로 이으면?</span> This = a mild allergic reaction",
                   "<span class='q'>뼈대는?</span> <span class='bone'>이것은 (가벼운) 알레르기 반응이다</span>"]},
        {"sent": "The fall of the Western Roman Empire was gradual.",
         "lines": ["<span class='q'>be동사는?</span> <span class='hl'>was</span> (과거 → &lsquo;~였다&rsquo;)",
                   "<span class='q'>진짜 주어는?</span> The fall (몰락) — of the ~ Empire 는 살",
                   "<span class='q'>뼈대는?</span> <span class='bone'>그 몰락은 점진적이었다 (서서히였다)</span>"]},
    ],
    "answers_html": """
      <p><b>1.</b> am &nbsp;/ 주어 I &nbsp;/ 뼈대: 나는 고등학생이다</p>
      <p><b>2.</b> are &nbsp;/ 주어 My friends(친구들, 여럿) &nbsp;/ 뼈대: 내 친구들은 도서관에 있다 (now=지금 → 살)</p>
      <p><b>3.</b> was &nbsp;/ 주어 The movie(하나) + yesterday(과거) &nbsp;/ 뼈대: 그 영화는 지루했다</p>
      <p><b>4.</b> are &nbsp;/ 주어 The children(아이들, 여럿) &nbsp;/ 뼈대: 아이들은 시끄럽다 (in the room=방 안의 → 살)</p>
    """,
}


DAYS = [DAY1, DAY2]
