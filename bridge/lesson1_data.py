# -*- coding: utf-8 -*-
"""중등 기초 브릿지 학습지 — Lesson 1 (2022 개정 천재(강상구) 공통영어2) 데이터.

각 '일차(day)'는 아래 구조를 가진다.
  day_no, title, range_label, part_heading(optional),
  goal_grammar, goal_sub,
  passage:  [{no, en}]
  vocab:    [{en, pron, pos, ko}]
  vocab_tip(optional),
  grammar:  [{level('core'|''|'up'), tag, title, rule(html), examples:[{en,ko}]}]
  literal:  [{no, en, ko}]   # ' / ' 가 끊어읽기 구분자
  quiz_html, answer_html
"""

# 자주 쓰는 안내문
_TIP = ("※ 발음은 원어민 소리와 다를 수 있는 <b>참고용 한글 표기</b>예요. "
        "단어는 &lsquo;영어→뜻&rsquo;, &lsquo;뜻→영어&rsquo; 양방향으로 외우면 시험에 강해요.")


# ============================================================
# 교재 표지
# ============================================================
COVER = {
    "title": "영어, 처음부터 다시",
    "subtitle": "문법을 하나도 몰라도 시작하는 기초 문법·단어·해석 교재",
    "tag": "고1 2학기 내신 대비 · Lesson 1",
    "book": "적용 지문 : 2022 개정 천재(강상구) 공통영어2 · Lesson 1 (모기 이야기)",
    "intro": [
        "중학 단어·문법을 <b>하나도 몰라도</b> 시작할 수 있게 만들었어요.",
        "지문에 나온 <b>단어 전부</b>와 <b>끊어읽기 해석</b>을 하루치씩 함께 담았어요.",
        "문법은 <b>가장 쉬운 것부터</b>, 어려운 건 &lsquo;지금은 몰라도 OK&rsquo;로 표시했어요.",
        "하루 한 DAY, 마지막엔 <b>직접 풀어보는 문제</b>로 확인합니다.",
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
# 1일차 — 본문 1~9  (be동사 & 3인칭 -s)
# ============================================================
DAY1 = {
    "day_no": 1,
    "title": "The Nuisance (성가신 존재) ① — 모기가 문다",
    "range_label": "PART 1 · 문장 1–9",
    "part_heading": "PART 1  THE NUISANCE (성가신 존재)",
    "goal_grammar": "be동사(am·are·is)와 일반동사 3인칭 -s",
    "goal_sub": "주어가 '하나(he/she/it)'면 동사에 -s! 이것만 잡아도 오늘은 성공.",
    "passage": [
        {"no": 1, "en": "You are on a camping trip with your family or friends."},
        {"no": 2, "en": "After a long day of hiking, you take a quick shower, sit in your favorite camping chair, pick up a soda, and let out a deep, contented sigh."},
        {"no": 3, "en": "Right at that moment, you hear that annoying and familiar buzzing sound."},
        {"no": 4, "en": "Beating its wings as fast as 600 times per second, a mosquito sneaks in and pierces your skin with its straw-like mouthparts."},
        {"no": 5, "en": "Next, it fills its belly with blood and then escapes quickly, leaving behind an itchy red bump."},
        {"no": 6, "en": "This is a mild allergic reaction to the mosquito's saliva."},
        {"no": 7, "en": "The more you scratch the bump, the more it itches."},
        {"no": 8, "en": "But how do mosquitoes find their victims anyway?"},
        {"no": 9, "en": "Carbon dioxide, which humans and other animals breathe out, is actually a key signal to mosquitoes that a nice meal is near."},
    ],
    "vocab": [
        {"en": "camping trip", "pron": "캠핑 트립", "pos": "명사", "ko": "캠핑 여행"},
        {"en": "hiking", "pron": "하이킹", "pos": "명사", "ko": "등산, 도보 여행 (hike 등산하다)"},
        {"en": "quick", "pron": "퀵", "pos": "형용사", "ko": "빠른, 재빠른 (→ quickly 재빨리)"},
        {"en": "favorite", "pron": "페이버릿", "pos": "형용사", "ko": "가장 좋아하는"},
        {"en": "pick up", "pron": "픽 업", "pos": "동사", "ko": "집어 들다, 줍다"},
        {"en": "soda", "pron": "소다", "pos": "명사", "ko": "탄산음료"},
        {"en": "let out", "pron": "렛 아웃", "pos": "동사", "ko": "(소리·한숨을) 내뱉다, 내쉬다"},
        {"en": "contented", "pron": "컨텐티드", "pos": "형용사", "ko": "만족한, 흡족한"},
        {"en": "sigh", "pron": "싸이", "pos": "명사", "ko": "한숨 (let out a sigh 한숨을 내쉬다)"},
        {"en": "right", "pron": "라잇", "pos": "부사", "ko": "바로, 정확히 (right at that moment 바로 그때)"},
        {"en": "moment", "pron": "모먼트", "pos": "명사", "ko": "순간, 때"},
        {"en": "annoying", "pron": "어노잉", "pos": "형용사", "ko": "짜증나는, 성가신"},
        {"en": "familiar", "pron": "퍼밀리어", "pos": "형용사", "ko": "익숙한, 낯익은"},
        {"en": "buzzing", "pron": "버징", "pos": "형용사", "ko": "윙윙거리는 (buzz 윙윙거리다)"},
        {"en": "beat", "pron": "비트", "pos": "동사", "ko": "(날개를) 퍼덕이다, 치다"},
        {"en": "wing", "pron": "윙", "pos": "명사", "ko": "날개"},
        {"en": "per second", "pron": "퍼 세컨드", "pos": "부사구", "ko": "초당, 1초에 (per ~마다)"},
        {"en": "mosquito", "pron": "머스키토우", "pos": "명사", "ko": "모기"},
        {"en": "sneak in", "pron": "스닉 인", "pos": "동사", "ko": "몰래 들어오다"},
        {"en": "pierce", "pron": "피어스", "pos": "동사", "ko": "뚫다, 찌르다"},
        {"en": "skin", "pron": "스킨", "pos": "명사", "ko": "피부"},
        {"en": "straw-like", "pron": "스트로라이크", "pos": "형용사", "ko": "빨대 같은 (straw 빨대 + like ~같은)"},
        {"en": "mouthparts", "pron": "마우스파츠", "pos": "명사", "ko": "(곤충의) 주둥이, 입 부분"},
        {"en": "fill", "pron": "필", "pos": "동사", "ko": "채우다 (fill A with B: A를 B로 채우다)"},
        {"en": "belly", "pron": "벨리", "pos": "명사", "ko": "배, 복부"},
        {"en": "blood", "pron": "블러드", "pos": "명사", "ko": "피, 혈액"},
        {"en": "escape", "pron": "이스케입", "pos": "동사", "ko": "달아나다, 탈출하다"},
        {"en": "leave behind", "pron": "리브 비하인드", "pos": "동사", "ko": "뒤에 남겨 두다 (leave-left-left)"},
        {"en": "itchy", "pron": "이치", "pos": "형용사", "ko": "가려운 (itch 가렵다 / 가려움)"},
        {"en": "bump", "pron": "범프", "pos": "명사", "ko": "혹, 부어오른 자국"},
        {"en": "mild", "pron": "마일드", "pos": "형용사", "ko": "가벼운, 약한, 순한"},
        {"en": "allergic reaction", "pron": "얼러직 리액션", "pos": "명사", "ko": "알레르기 반응 (reaction 반응)"},
        {"en": "saliva", "pron": "썰라이버", "pos": "명사", "ko": "침, 타액"},
        {"en": "scratch", "pron": "스크래치", "pos": "동사", "ko": "긁다"},
        {"en": "victim", "pron": "빅팀", "pos": "명사", "ko": "먹잇감, 희생자, 피해자"},
        {"en": "anyway", "pron": "애니웨이", "pos": "부사", "ko": "대체, 도대체, 어쨌든"},
        {"en": "carbon dioxide", "pron": "카본 다이옥사이드", "pos": "명사", "ko": "이산화탄소 (CO2)"},
        {"en": "breathe out", "pron": "브리드 아웃", "pos": "동사", "ko": "숨을 내쉬다 (breathe 숨쉬다)"},
        {"en": "actually", "pron": "액추얼리", "pos": "부사", "ko": "사실은, 실제로"},
        {"en": "key", "pron": "키", "pos": "형용사", "ko": "핵심적인, 중요한 (a key signal 핵심 신호)"},
        {"en": "signal", "pron": "시그널", "pos": "명사", "ko": "신호"},
        {"en": "meal", "pron": "밀", "pos": "명사", "ko": "식사, 끼니, 먹을거리"},
        {"en": "near", "pron": "니어", "pos": "형용사", "ko": "가까운, 가까이에"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "가장 먼저", "title": "문장의 뼈대 — 누가(주어) + 뭐했다(동사)",
         "rule": "영어 문장은 사람 몸이랑 똑같아요. <b>뼈대</b>가 있고 거기에 <b>살</b>이 붙어요. "
                 "<b>누가(주어) + 뭐했다(동사)</b> 딱 두 개만 먼저 찾으면 절반은 성공! 나머지(꾸미는 살)는 몰라도 돼요.",
         "examples": [
             {"en": "<span class='hl'>A mosquito</span> <span class='hl'>sneaks</span> in.", "ko": "<b>모기가</b> <b>몰래 들어온다</b> &nbsp;(누가=모기 / 뭐했다=들어온다)"},
             {"en": "<span class='hl'>It</span> <span class='hl'>fills</span> its belly.", "ko": "<b>그것이</b> <b>채운다</b> &nbsp;(its belly=배를 → 살)"},
         ]},
        {"level": "core", "tag": "오늘의 핵심", "title": "be동사 (am · are · is) = ~이다 / ~에 있다",
         "rule": "동사 중에 뜻이 거의 없는 <b>be동사</b>가 있어요. <b>&ldquo;= (같다)&rdquo;</b> 기호라고 생각하세요. "
                 "주어에 따라 <b>I → am</b>, <b>You/We/They → are</b>, <b>He/She/It(하나) → is</b>.",
         "examples": [
             {"en": "You <span class='hl'>are</span> on a camping trip.", "ko": "너는 캠핑 여행 중<b>이다</b>. (are = ~에 있다/~하는 중이다)"},
             {"en": "This <span class='hl'>is</span> a mild allergic reaction.", "ko": "이것<b>은</b> 가벼운 알레르기 반응<b>이다</b>. (This = a reaction)"},
         ]},
        {"level": "", "tag": "오늘의 핵심", "title": "일반동사에 붙는 -s : 주어가 '하나'일 때",
         "rule": "움직임을 나타내는 <b>일반동사</b>는, 주어가 <b>하나(he/she/it)</b>이면 뒤에 <b>-s / -es</b>를 붙여요. 시험 단골 포인트!",
         "examples": [
             {"en": "a mosquito <span class='hl'>sneaks</span> in and <span class='hl'>pierces</span> your skin", "ko": "모기(하나)가 몰래 들어와 피부를 <b>뚫는다</b>"},
             {"en": "it <span class='hl'>fills</span> its belly", "ko": "그것(모기)이 배를 <b>채운다</b>"},
         ]},
        {"level": "up", "tag": "지금은 몰라도 OK", "title": "오늘 지문의 어려운 문법은 나중에 배워요!",
         "rule": "이 지문엔 <b>분사구문(Beating~), 관계대명사(which~), the 비교급</b> 같은 어려운 것도 살짝 섞여 있어요. "
                 "<b>지금은 하나도 몰라도 됩니다.</b> 뒤 DAY에서 하나씩 천천히 배울 거예요. 오늘은 &lsquo;누가/뭐했다&rsquo;와 be동사만 잡으면 성공!",
         "examples": [
             {"en": "The more you scratch, the more it itches.", "ko": "(참고) 긁을수록 더 가렵다 — &lsquo;~할수록 더~&rsquo;는 나중에!"},
         ]},
    ],
    "literal": [
        {"no": 1, "en": "You are / on a camping trip / with your family or friends.",
         "ko": "너는 있다 / 캠핑 여행 중에 / 가족이나 친구들과 함께."},
        {"no": 2, "en": "After a long day of hiking, / you take a quick shower, / sit in your favorite camping chair, / pick up a soda, / and let out a deep, contented sigh.",
         "ko": "등산으로 긴 하루를 보낸 뒤, / 너는 간단히 샤워를 하고, / 좋아하는 캠핑 의자에 앉아, / 탄산음료를 집어 들고, / 깊고 흡족한 한숨을 내쉰다."},
        {"no": 3, "en": "Right at that moment, / you hear / that annoying and familiar buzzing sound.",
         "ko": "바로 그 순간, / 너는 듣는다 / 그 성가시고 익숙한 윙윙 소리를."},
        {"no": 4, "en": "Beating its wings as fast as 600 times per second, / a mosquito sneaks in / and pierces your skin / with its straw-like mouthparts.",
         "ko": "초당 600번만큼 빠르게 날개를 퍼덕이면서, / 모기가 몰래 들어와 / 네 피부를 뚫는다 / 빨대 같은 주둥이로."},
        {"no": 5, "en": "Next, / it fills its belly with blood / and then escapes quickly, / leaving behind an itchy red bump.",
         "ko": "다음으로, / 그것은 배를 피로 채우고 / 그런 다음 재빨리 달아난다, / 가려운 빨간 혹을 남긴 채로."},
        {"no": 6, "en": "This is / a mild allergic reaction / to the mosquito's saliva.",
         "ko": "이것은 ~이다 / 가벼운 알레르기 반응 / 모기의 침에 대한."},
        {"no": 7, "en": "The more you scratch the bump, / the more it itches.",
         "ko": "네가 혹을 긁으면 긁을수록, / 그것은 더 가렵다."},
        {"no": 8, "en": "But how do mosquitoes find / their victims / anyway?",
         "ko": "그런데 모기는 어떻게 찾을까 / 자기 먹잇감을 / 대체?"},
        {"no": 9, "en": "Carbon dioxide, / which humans and other animals breathe out, / is actually a key signal to mosquitoes / that a nice meal is near.",
         "ko": "이산화탄소는, / (인간과 다른 동물들이 내쉬는 것인데,) / 사실 모기에게 핵심 신호이다 / 좋은 먹을거리가 가까이 있다는."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">mosquito</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">skin</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">blood</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">itchy</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">escape</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">annoying</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">victim</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">signal</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">pierce</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">near</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 침, 타액</span> → <span class="q-fill"></span> &nbsp; <span class="kr">2) 한숨</span> → <span class="q-fill"></span> &nbsp; <span class="kr">3) 날개</span> → <span class="q-fill"></span></div>
      <div class="q-line"><span class="kr">4) 익숙한</span> → <span class="q-fill"></span> &nbsp; <span class="kr">5) 이산화탄소</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">6) 긁다</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>괄호 안에서 알맞은 것 고르기 (오늘의 핵심 문법)</div>
      <div class="q-line">1) You ( am / are / is )&nbsp; on a camping trip.</div>
      <div class="q-line">2) A mosquito ( sneak / sneaks )&nbsp; in and ( pierce / pierces )&nbsp; your skin.</div>
      <div class="q-line">3) How ( do / does )&nbsp; mosquitoes find their victims?</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) This is a mild allergic reaction to the mosquito's saliva.<span class="q-write"></span></div>
      <div class="q-line">2) The more you scratch the bump, the more it itches.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 모기 &nbsp; 2 피부 &nbsp; 3 피/혈액 &nbsp; 4 가려운 &nbsp; 5 달아나다/탈출하다 &nbsp; 6 짜증나는/성가신 &nbsp; 7 먹잇감/희생자 &nbsp; 8 신호 &nbsp; 9 뚫다/찌르다 &nbsp; 10 가까운</div>
    <div class="ans-block"><b>B.</b> 1 saliva &nbsp; 2 sigh &nbsp; 3 wing &nbsp; 4 familiar &nbsp; 5 carbon dioxide &nbsp; 6 scratch</div>
    <div class="ans-block"><b>C.</b> 1 are (주어 You → are) &nbsp; 2 sneaks, pierces (주어 a mosquito=하나 → 동사에 -s) &nbsp; 3 do (mosquitoes=여럿 → do)</div>
    <div class="ans-block"><b>D.</b> 1 이것은 모기의 침에 대한 가벼운 알레르기 반응이다. &nbsp; 2 (네가) 혹을 긁으면 긁을수록, 그것은 더 가렵다.</div>
    """,
}


# ============================================================
# 2일차 — 본문 10~15  (관계대명사 that/which)
# ============================================================
DAY2 = {
    "day_no": 2,
    "title": "The Nuisance (성가신 존재) ② — 모기는 어떻게 찾을까",
    "range_label": "PART 1 · 문장 10–15",
    "part_heading": None,
    "goal_grammar": "관계대명사 that / which — 명사를 뒤에서 꾸며 주기",
    "goal_sub": "명사 + [that/which ~] = \"~하는 (명사)\". 이 덩어리를 묶어 읽으면 문장이 쉬워져요.",
    "passage": [
        {"no": 10, "en": "They are highly sensitive to CO2 and can detect it from far away."},
        {"no": 11, "en": "That's not the only cue they use to find their victims."},
        {"no": 12, "en": "When you sweat, you release certain chemicals that attract them."},
        {"no": 13, "en": "Moreover, they can easily notice that your body temperature has risen."},
        {"no": 14, "en": "Why do they want our blood in the first place?"},
        {"no": 15, "en": "It turns out that only females bite us; they need protein to produce eggs."},
    ],
    "vocab": [
        {"en": "highly", "pron": "하일리", "pos": "부사", "ko": "매우, 대단히"},
        {"en": "sensitive", "pron": "센서티브", "pos": "형용사", "ko": "민감한 (be sensitive to ~에 민감하다)"},
        {"en": "detect", "pron": "디텍트", "pos": "동사", "ko": "감지하다, 알아차리다"},
        {"en": "from far away", "pron": "프롬 파 어웨이", "pos": "부사구", "ko": "멀리서, 먼 곳에서"},
        {"en": "cue", "pron": "큐", "pos": "명사", "ko": "단서, 신호"},
        {"en": "the only", "pron": "디 온리", "pos": "형용사", "ko": "유일한, 단 하나의"},
        {"en": "use", "pron": "유즈", "pos": "동사", "ko": "사용하다, 이용하다"},
        {"en": "find", "pron": "파인드", "pos": "동사", "ko": "찾다, 발견하다 (find-found-found)"},
        {"en": "sweat", "pron": "스웻", "pos": "동사", "ko": "땀을 흘리다; 땀"},
        {"en": "release", "pron": "릴리스", "pos": "동사", "ko": "내보내다, 분비하다, 방출하다"},
        {"en": "certain", "pron": "써튼", "pos": "형용사", "ko": "특정한, 어떤; 확실한"},
        {"en": "chemical", "pron": "케미컬", "pos": "명사", "ko": "화학 물질"},
        {"en": "attract", "pron": "어트랙트", "pos": "동사", "ko": "끌어당기다, 유인하다"},
        {"en": "moreover", "pron": "모어오버", "pos": "부사", "ko": "게다가, 더욱이"},
        {"en": "easily", "pron": "이질리", "pos": "부사", "ko": "쉽게 (easy 쉬운)"},
        {"en": "notice", "pron": "노티스", "pos": "동사", "ko": "알아채다, 알아차리다"},
        {"en": "body temperature", "pron": "바디 템퍼러처", "pos": "명사", "ko": "체온"},
        {"en": "rise", "pron": "라이즈", "pos": "동사", "ko": "오르다, 상승하다 (rise-rose-risen)"},
        {"en": "in the first place", "pron": "인 더 퍼스트 플레이스", "pos": "숙어", "ko": "애초에, 우선, 무엇보다"},
        {"en": "it turns out that", "pron": "잇 턴즈 아웃 댓", "pos": "숙어", "ko": "~인 것으로 드러나다, 알고 보니 ~이다"},
        {"en": "female", "pron": "피메일", "pos": "명사", "ko": "암컷; 여성 (↔ male 수컷)"},
        {"en": "bite", "pron": "바이트", "pos": "동사", "ko": "물다, 깨물다 (bite-bit-bitten)"},
        {"en": "protein", "pron": "프로틴", "pos": "명사", "ko": "단백질"},
        {"en": "produce", "pron": "프러듀스", "pos": "동사", "ko": "생산하다, 만들어 내다"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "관계대명사 that / which : 명사를 뒤에서 꾸민다",
         "rule": "&lsquo;명사 + <b>[that/which + (동사~)]</b>&rsquo; 은 통째로 <b>&ldquo;~하는 (명사)&rdquo;</b> 로 해석해요. 사람이면 who, 사물·동물이면 that/which 를 써요.",
         "examples": [
             {"en": "certain chemicals <span class='hl'>that attract them</span>", "ko": "그들을 <b>유인하는</b> 특정한 화학 물질"},
             {"en": "the only cue <span class='hl'>[that] they use</span>", "ko": "그들이 <b>이용하는</b> 유일한 단서"},
         ]},
        {"level": "core", "tag": "오늘의 핵심", "title": "관계대명사가 사라질 때 (목적격 생략)",
         "rule": "꾸밈을 받는 명사가 뒤 문장에서 <b>목적어</b> 역할이면 that/which 를 <b>생략</b>할 수 있어요. 그래서 &lsquo;명사 + 주어 + 동사&rsquo; 처럼 붙어 나오면 사이에 관계대명사가 숨어 있다고 보면 돼요.",
         "examples": [
             {"en": "the only cue <span class='hl'>(that)</span> they use", "ko": "그들이 이용하는 유일한 단서 (cue를 use의 목적어로)"},
         ]},
        {"level": "", "tag": "문법 3", "title": "조동사 can = ~할 수 있다 (뒤 동사는 원형)",
         "rule": "<b>can</b> 뒤에는 항상 <b>동사원형</b>이 와요 (-s 안 붙임). 부정은 <b>can't/cannot</b>.",
         "examples": [
             {"en": "they <span class='hl'>can detect</span> it from far away", "ko": "그들은 멀리서도 그것을 <b>감지할 수 있다</b>"},
         ]},
        {"level": "", "tag": "문법 4", "title": "접속사 that = \"~라는 것을\" (명사절)",
         "rule": "notice / know / turn out 뒤의 <b>that</b> 은 &lsquo;~라는 것&rsquo; 이라는 <b>내용 덩어리</b>를 이끌어요. 이 that 은 해석에서 종종 생략돼요.",
         "examples": [
             {"en": "they notice <span class='hl'>that</span> your body temperature has risen", "ko": "체온이 올라간 <b>것을</b> 알아챈다"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "to + 동사원형 = \"~하기 위해\" (목적)",
         "rule": "동사 뒤 <b>to + 동사원형</b>은 흔히 <b>&ldquo;~하기 위해서&rdquo;</b> 라는 목적으로 해석해요.",
         "examples": [
             {"en": "they need protein <span class='hl'>to produce</span> eggs", "ko": "알을 <b>낳기 위해</b> 단백질이 필요하다"},
         ]},
    ],
    "literal": [
        {"no": 10, "en": "They are highly sensitive to CO2 / and can detect it / from far away.",
         "ko": "그들은 이산화탄소에 매우 민감하다 / 그리고 그것을 감지할 수 있다 / 멀리서도."},
        {"no": 11, "en": "That's not / the only cue / they use / to find their victims.",
         "ko": "그것은 ~아니다 / 유일한 단서가 / 그들이 이용하는 / 먹잇감을 찾기 위해."},
        {"no": 12, "en": "When you sweat, / you release certain chemicals / that attract them.",
         "ko": "네가 땀을 흘리면, / 너는 특정한 화학 물질을 내보낸다 / 그들을 유인하는."},
        {"no": 13, "en": "Moreover, / they can easily notice / that your body temperature has risen.",
         "ko": "게다가, / 그들은 쉽게 알아챌 수 있다 / 네 체온이 올라갔다는 것을."},
        {"no": 14, "en": "Why do they want / our blood / in the first place?",
         "ko": "그들은 왜 원할까 / 우리의 혈액을 / 애초에?"},
        {"no": 15, "en": "It turns out / that only females bite us; / they need protein / to produce eggs.",
         "ko": "드러난다 / 암컷만 우리를 문다는 것이; / 그들은 단백질이 필요하다 / 알을 낳기 위해."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">detect</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">sensitive</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">release</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">attract</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">notice</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">cue</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">protein</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">female</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">bite</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">produce</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 체온</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">2) 화학 물질</span> → <span class="q-fill"></span> &nbsp; <span class="kr">3) 게다가</span> → <span class="q-fill"></span></div>
      <div class="q-line"><span class="kr">4) 땀을 흘리다</span> → <span class="q-fill"></span> &nbsp; <span class="kr">5) 특정한</span> → <span class="q-fill"></span> &nbsp; <span class="kr">6) 오르다/상승하다</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>밑줄 친 관계대명사 덩어리를 우리말로 (오늘의 핵심 문법)</div>
      <div class="q-line">1) chemicals <u>that attract them</u> → <span class="kr">그들을 (</span><span class="q-fill lg"></span><span class="kr">) 화학 물질</span></div>
      <div class="q-line">2) the only cue <u>they use</u> → <span class="kr">그들이 (</span><span class="q-fill lg"></span><span class="kr">) 유일한 단서</span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) When you sweat, you release certain chemicals that attract them.<span class="q-write"></span></div>
      <div class="q-line">2) They need protein to produce eggs.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 감지하다 &nbsp; 2 민감한 &nbsp; 3 내보내다/분비하다 &nbsp; 4 유인하다/끌어당기다 &nbsp; 5 알아채다 &nbsp; 6 단서/신호 &nbsp; 7 단백질 &nbsp; 8 암컷/여성 &nbsp; 9 물다 &nbsp; 10 생산하다/만들어 내다</div>
    <div class="ans-block"><b>B.</b> 1 body temperature &nbsp; 2 chemical &nbsp; 3 moreover &nbsp; 4 sweat &nbsp; 5 certain &nbsp; 6 rise</div>
    <div class="ans-block"><b>C.</b> 1 (그들을) <b>유인하는</b> 화학 물질 &nbsp; 2 (그들이) <b>이용하는</b> 유일한 단서 &nbsp;— that/which 앞의 명사를 꾸며요.</div>
    <div class="ans-block"><b>D.</b> 1 네가 땀을 흘리면, 너는 그들을 유인하는 특정한 화학 물질을 내보낸다(분비한다). &nbsp; 2 그들은 알을 낳기 위해 단백질이 필요하다.</div>
    """,
}


# ============================================================
# 3일차 — 본문 16~20  (가정법 과거)
# ============================================================
DAY3 = {
    "day_no": 3,
    "title": "The Nuisance (성가신 존재) ③ — 알을 낳기까지",
    "range_label": "PART 1 · 문장 16–20",
    "part_heading": None,
    "goal_grammar": "가정법 과거 : If + 과거, 주어 would + 동사원형",
    "goal_sub": "\"만약 (지금) ~라면 ~할 텐데\" — 사실은 그렇지 않다는 뜻. 동사가 과거지만 해석은 현재!",
    "passage": [
        {"no": 16, "en": "If our blood did not contain protein, they would not bother us."},
        {"no": 17, "en": "After the mosquito successfully takes a blood meal of up to three times her own body weight, she quickly lands on the nearest vertical surface."},
        {"no": 18, "en": "With the aid of gravity, she drains off the water from the blood she took."},
        {"no": 19, "en": "Using this concentrated blood, she develops her eggs over the next few days."},
        {"no": 20, "en": "She then lays roughly 200 floating eggs on the surface of a small pool of water."},
    ],
    "vocab": [
        {"en": "contain", "pron": "컨테인", "pos": "동사", "ko": "포함하다, 담고 있다"},
        {"en": "protein", "pron": "프로틴", "pos": "명사", "ko": "단백질"},
        {"en": "bother", "pron": "바더", "pos": "동사", "ko": "귀찮게 하다, 성가시게 하다"},
        {"en": "successfully", "pron": "석세스풀리", "pos": "부사", "ko": "성공적으로 (success 성공)"},
        {"en": "take a meal", "pron": "테이크 어 밀", "pos": "동사구", "ko": "먹이를 섭취하다 (여기선 피를 빨다)"},
        {"en": "up to", "pron": "업 투", "pos": "숙어", "ko": "최대 ~까지, ~에 이르는"},
        {"en": "three times", "pron": "쓰리 타임즈", "pos": "부사구", "ko": "세 배 (times 배·곱)"},
        {"en": "body weight", "pron": "바디 웨이트", "pos": "명사", "ko": "체중, 몸무게 (weight 무게)"},
        {"en": "land", "pron": "랜드", "pos": "동사", "ko": "내려앉다, 착륙하다"},
        {"en": "nearest", "pron": "니어리스트", "pos": "형용사", "ko": "가장 가까운 (near의 최상급)"},
        {"en": "vertical", "pron": "버티컬", "pos": "형용사", "ko": "수직의, 세로의 (↔ horizontal 수평의)"},
        {"en": "surface", "pron": "써피스", "pos": "명사", "ko": "표면, 겉면"},
        {"en": "with the aid of", "pron": "위드 디 에이드 오브", "pos": "숙어", "ko": "~의 도움을 받아 (aid 도움)"},
        {"en": "gravity", "pron": "그래비티", "pos": "명사", "ko": "중력"},
        {"en": "drain off", "pron": "드레인 오프", "pos": "동사", "ko": "빼내다, 흘려 내보내다"},
        {"en": "concentrated", "pron": "컨센트레이티드", "pos": "형용사", "ko": "농축된, 진해진"},
        {"en": "develop", "pron": "디벨럽", "pos": "동사", "ko": "발달시키다, 성숙시키다, 발전시키다"},
        {"en": "over the next few days", "pron": "오버 더 넥스트 퓨 데이즈", "pos": "부사구", "ko": "그 후 며칠에 걸쳐"},
        {"en": "lay", "pron": "레이", "pos": "동사", "ko": "(알을) 낳다; 놓다 (lay-laid-laid)"},
        {"en": "roughly", "pron": "러플리", "pos": "부사", "ko": "대략, 약"},
        {"en": "floating", "pron": "플로팅", "pos": "형용사", "ko": "물에 뜨는, 떠다니는 (float 뜨다)"},
        {"en": "pool", "pron": "풀", "pos": "명사", "ko": "웅덩이, (작은) 물웅덩이"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "가정법 과거 : If + 과거동사, 주어 would + 동사원형",
         "rule": "&ldquo;만약 (지금) ~라면 …할 텐데&rdquo; 처럼 <b>현재 사실과 반대</b>되는 상상을 말할 때 써요. If절 동사는 <b>과거형</b>이지만 뜻은 <b>현재</b>! 주절은 <b>would/could + 동사원형</b>.",
         "examples": [
             {"en": "<span class='hl'>If</span> our blood <span class='hl'>did not contain</span> protein, they <span class='hl'>would not bother</span> us.", "ko": "만약 우리 피가 단백질을 담고 있지 않<b>다면</b>, 그들은 우리를 귀찮게 하지 않<b>을 텐데</b>. (→ 사실은 담고 있어서 문다)"},
         ]},
        {"level": "", "tag": "문법 2", "title": "관계대명사 목적격 생략 (복습)",
         "rule": "&lsquo;명사 + 주어 + 동사&rsquo; 가 바로 붙어 나오면 그 사이에 <b>관계대명사(that/which)가 생략</b>된 거예요.",
         "examples": [
             {"en": "the blood <span class='hl'>[that]</span> she took", "ko": "그녀가 취한 그 피"},
         ]},
        {"level": "", "tag": "문법 3", "title": "접속사 after = \"~한 뒤에\"",
         "rule": "<b>after</b> 는 두 문장을 이어 &lsquo;~한 후에&rsquo; 라는 순서를 나타내요. 뒤에 &lsquo;주어+동사&rsquo; 가 와요.",
         "examples": [
             {"en": "<span class='hl'>After</span> the mosquito takes a blood meal, she lands …", "ko": "모기가 피를 빤 <b>뒤에</b>, 내려앉는다 …"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "-ing 로 시작하는 덩어리 (분사구문, 복습)",
         "rule": "문장 앞의 <b>동사+ing</b> 덩어리는 &ldquo;~하면서 / ~해서&rdquo; 로 이어 읽어요.",
         "examples": [
             {"en": "<span class='hl'>Using</span> this concentrated blood, she develops her eggs", "ko": "이 농축된 피를 <b>사용해서</b>, 그녀는 알을 성숙시킨다"},
         ]},
    ],
    "literal": [
        {"no": 16, "en": "If our blood did not contain protein, / they would not bother us.",
         "ko": "만약 우리 피가 단백질을 담고 있지 않다면, / 그들은 우리를 귀찮게 하지 않을 텐데."},
        {"no": 17, "en": "After the mosquito successfully takes a blood meal / of up to three times her own body weight, / she quickly lands / on the nearest vertical surface.",
         "ko": "모기가 성공적으로 피를 빤 뒤에 / 자기 체중의 최대 세 배에 달하는, / 그것은 재빨리 내려앉는다 / 가장 가까운 수직 표면에."},
        {"no": 18, "en": "With the aid of gravity, / she drains off the water / from the blood she took.",
         "ko": "중력의 도움을 받아, / 그것은 수분을 빼낸다 / 자신이 취한 피에서."},
        {"no": 19, "en": "Using this concentrated blood, / she develops her eggs / over the next few days.",
         "ko": "이 농축된 피를 사용해, / 그것은 알을 성숙시킨다 / 그 후 며칠에 걸쳐."},
        {"no": 20, "en": "She then lays / roughly 200 floating eggs / on the surface of a small pool of water.",
         "ko": "그런 다음 그것은 낳는다 / 물에 뜨는 약 200개의 알을 / 작은 물웅덩이 표면에."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">contain</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">bother</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">surface</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">gravity</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">land</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">develop</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">lay</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">vertical</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">roughly</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">concentrated</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 중력</span> → <span class="q-fill"></span> &nbsp; <span class="kr">2) 체중</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">3) 표면</span> → <span class="q-fill"></span></div>
      <div class="q-line"><span class="kr">4) 성공적으로</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">5) 웅덩이</span> → <span class="q-fill"></span> &nbsp; <span class="kr">6) 포함하다</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>가정법 과거 완성하기 (오늘의 핵심 문법)</div>
      <div class="q-line">1) If our blood ( did not / does not ) contain protein, they ( will / would ) not bother us.</div>
      <div class="q-line">2) 위 문장의 뜻: 실제로 우리 피에는 단백질이 ( 있다 / 없다 ). &nbsp;→ 알맞은 것에 &#9711;</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) If our blood did not contain protein, they would not bother us.<span class="q-write"></span></div>
      <div class="q-line">2) With the aid of gravity, she drains off the water from the blood she took.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 포함하다 &nbsp; 2 귀찮게 하다 &nbsp; 3 표면 &nbsp; 4 중력 &nbsp; 5 내려앉다/착륙하다 &nbsp; 6 발달·성숙시키다 &nbsp; 7 (알을) 낳다 &nbsp; 8 수직의 &nbsp; 9 대략/약 &nbsp; 10 농축된</div>
    <div class="ans-block"><b>B.</b> 1 gravity &nbsp; 2 body weight &nbsp; 3 surface &nbsp; 4 successfully &nbsp; 5 pool &nbsp; 6 contain</div>
    <div class="ans-block"><b>C.</b> 1 did not, would (가정법 과거: If+과거, 주어 would+원형) &nbsp; 2 있다 (가정법은 사실의 반대 → 실제로는 단백질이 있어서 문다)</div>
    <div class="ans-block"><b>D.</b> 1 만약 우리 피가 단백질을 담고 있지 않다면, 그들은 우리를 귀찮게 하지 않을 것이다. &nbsp; 2 중력의 도움을 받아, 그것(모기)은 자신이 취한 피에서 수분을 빼낸다.</div>
    """,
}


# ============================================================
# 4일차 — 본문 21~28  (현재완료 have p.p.)
# ============================================================
DAY4 = {
    "day_no": 4,
    "title": "The Predator (포식자) ① — 가장 위험한 동물",
    "range_label": "PART 2 · 문장 21–28",
    "part_heading": "PART 2  THE PREDATOR (포식자)",
    "goal_grammar": "현재완료 : have / has + 과거분사(p.p.)",
    "goal_sub": "\"지금까지 ~해 왔다 / ~한 적이 있다\" — 과거가 지금까지 이어지는 느낌.",
    "passage": [
        {"no": 21, "en": "If you had to choose our greatest predator in nature, which would you pick? Sharks, lions, or bears?"},
        {"no": 22, "en": "According to history professor Timothy Winegard, it is actually the mosquito."},
        {"no": 23, "en": "Mosquitoes can pass on deadly diseases like malaria and yellow fever."},
        {"no": 24, "en": "Over a million people worldwide die of these diseases every year."},
        {"no": 25, "en": "Throughout history, Winegard estimates that mosquitoes have killed more people than any other single cause — about fifty-two billion people, nearly half of all humans who have ever lived."},
        {"no": 26, "en": "Winegard claims that mosquitoes also played a role in shaping the history of several countries."},
        {"no": 27, "en": "Take the Roman Empire, for example. The fall of the Western Roman Empire was gradual, spanning over centuries."},
        {"no": 28, "en": "Here are commonly cited reasons for the fall of the empire: invasions by outside forces, economic troubles, and corruption."},
    ],
    "vocab": [
        {"en": "choose", "pron": "추즈", "pos": "동사", "ko": "고르다, 선택하다 (choose-chose-chosen)"},
        {"en": "greatest", "pron": "그레이티스트", "pos": "형용사", "ko": "가장 큰·위대한 (great의 최상급)"},
        {"en": "predator", "pron": "프레데터", "pos": "명사", "ko": "포식자, 천적"},
        {"en": "nature", "pron": "네이처", "pos": "명사", "ko": "자연"},
        {"en": "pick", "pron": "픽", "pos": "동사", "ko": "고르다, 뽑다"},
        {"en": "according to", "pron": "어코딩 투", "pos": "숙어", "ko": "~에 따르면"},
        {"en": "professor", "pron": "프러페서", "pos": "명사", "ko": "교수"},
        {"en": "pass on", "pron": "패스 온", "pos": "동사", "ko": "옮기다, 전달하다, 전염시키다"},
        {"en": "deadly", "pron": "데들리", "pos": "형용사", "ko": "치명적인, 목숨을 앗아가는 (death 죽음)"},
        {"en": "disease", "pron": "디지즈", "pos": "명사", "ko": "질병, 병"},
        {"en": "malaria", "pron": "멀레리아", "pos": "명사", "ko": "말라리아"},
        {"en": "yellow fever", "pron": "옐로우 피버", "pos": "명사", "ko": "황열 (fever 열·열병)"},
        {"en": "worldwide", "pron": "월드와이드", "pos": "부사", "ko": "전 세계적으로"},
        {"en": "die of", "pron": "다이 오브", "pos": "동사", "ko": "~로 죽다 (병·원인으로)"},
        {"en": "throughout", "pron": "쓰루아웃", "pos": "전치사", "ko": "~내내, ~전체에 걸쳐"},
        {"en": "estimate", "pron": "에스티메이트", "pos": "동사", "ko": "추정하다, 어림잡다"},
        {"en": "kill", "pron": "킬", "pos": "동사", "ko": "죽이다"},
        {"en": "single", "pron": "싱글", "pos": "형용사", "ko": "단 하나의, 단일의"},
        {"en": "cause", "pron": "코즈", "pos": "명사", "ko": "원인, 이유"},
        {"en": "billion", "pron": "빌리언", "pos": "명사", "ko": "10억"},
        {"en": "nearly", "pron": "니얼리", "pos": "부사", "ko": "거의"},
        {"en": "claim", "pron": "클레임", "pos": "동사", "ko": "주장하다"},
        {"en": "play a role in", "pron": "플레이 어 롤 인", "pos": "숙어", "ko": "~에 역할을 하다, 한몫하다"},
        {"en": "shape", "pron": "셰입", "pos": "동사", "ko": "형성하다, 만들어 가다"},
        {"en": "several", "pron": "세버럴", "pos": "형용사", "ko": "여러, 몇몇의"},
        {"en": "empire", "pron": "엠파이어", "pos": "명사", "ko": "제국"},
        {"en": "fall", "pron": "폴", "pos": "명사", "ko": "몰락, 붕괴; 떨어짐"},
        {"en": "gradual", "pron": "그래주얼", "pos": "형용사", "ko": "점진적인, 서서히 일어나는"},
        {"en": "span", "pron": "스팬", "pos": "동사", "ko": "(기간에) 걸치다, 이어지다"},
        {"en": "century", "pron": "센추리", "pos": "명사", "ko": "세기, 100년"},
        {"en": "cited", "pron": "사이티드", "pos": "형용사", "ko": "언급되는, 인용되는 (cite 인용하다)"},
        {"en": "invasion", "pron": "인베이전", "pos": "명사", "ko": "침략, 침입"},
        {"en": "outside forces", "pron": "아웃사이드 포스이즈", "pos": "명사", "ko": "외부 세력, 외세"},
        {"en": "economic", "pron": "이코노믹", "pos": "형용사", "ko": "경제의, 경제적인"},
        {"en": "corruption", "pron": "커럽션", "pos": "명사", "ko": "부패, 타락"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "현재완료 : have / has + 과거분사(p.p.)",
         "rule": "&lsquo;have/has + p.p.&rsquo; 은 <b>과거에 일어난 일이 지금과 이어져 있다</b>는 느낌이에요. ① <b>~해 왔다</b>(계속) ② <b>~한 적이 있다</b>(경험) ③ <b>막 ~했다</b>(완료). 주어가 하나면 <b>has</b>.",
         "examples": [
             {"en": "mosquitoes <span class='hl'>have killed</span> more people …", "ko": "모기가 (지금까지) 더 많은 사람을 <b>죽여 왔다</b>"},
             {"en": "all humans who <span class='hl'>have ever lived</span>", "ko": "지금까지 <b>살아 본 적 있는</b> 모든 인간"},
         ]},
        {"level": "", "tag": "문법 2", "title": "비교급 more ~ than = \"~보다 더 …한\"",
         "rule": "&lsquo;more + 원급 + than&rsquo; 은 <b>&ldquo;~보다 더 …&rdquo;</b>. <b>than any other + 단수명사</b>는 &lsquo;다른 어떤 것보다&rsquo; = 사실상 <b>최상급</b>(가장 ~) 의미예요.",
         "examples": [
             {"en": "<span class='hl'>more</span> people <span class='hl'>than any other</span> single cause", "ko": "다른 어떤 단일 원인<b>보다 더</b> 많은 사람 (= 가장 많이)"},
         ]},
        {"level": "", "tag": "문법 3", "title": "접속사 that = \"~라는 것을\" (복습)",
         "rule": "estimate / claim / know 뒤의 <b>that</b> 은 &lsquo;~라는 내용&rsquo; 을 이끄는 덩어리예요.",
         "examples": [
             {"en": "Winegard claims <span class='hl'>that</span> mosquitoes played a role …", "ko": "Winegard는 모기가 역할을 했다<b>고</b> 주장한다"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "가정법 과거 (복습) : If you had to choose …, which would you pick?",
         "rule": "3일차에서 배운 가정법! &ldquo;만약 ~해야 한다면, 무엇을 고를래?&rdquo; 처럼 <b>상상해 보는</b> 질문이에요.",
         "examples": [
             {"en": "If you <span class='hl'>had to</span> choose …, which <span class='hl'>would</span> you pick?", "ko": "만약 고른다<b>면</b>, 무엇을 고르<b>겠는가?</b>"},
         ]},
    ],
    "literal": [
        {"no": 21, "en": "If you had to choose / our greatest predator in nature, / which would you pick? / Sharks, lions, or bears?",
         "ko": "만약 네가 골라야 한다면 / 자연에서 우리의 가장 강력한 포식자를, / 너는 무엇을 고르겠는가? / 상어, 사자, 아니면 곰?"},
        {"no": 22, "en": "According to history professor Timothy Winegard, / it is actually the mosquito.",
         "ko": "역사학 교수 Timothy Winegard에 따르면, / 그것은 사실 모기이다."},
        {"no": 23, "en": "Mosquitoes can pass on / deadly diseases / like malaria and yellow fever.",
         "ko": "모기는 옮길 수 있다 / 치명적인 질병을 / 말라리아와 황열 같은."},
        {"no": 24, "en": "Over a million people worldwide / die of these diseases / every year.",
         "ko": "전 세계 백만 명이 넘는 사람들이 / 이런 질병으로 죽는다 / 매년."},
        {"no": 25, "en": "Throughout history, / Winegard estimates / that mosquitoes have killed more people / than any other single cause / — about fifty-two billion people, / nearly half of all humans who have ever lived.",
         "ko": "역사를 통틀어, / Winegard는 추정한다 / 모기가 더 많은 사람을 죽여 왔다고 / 다른 어떤 단일 원인보다 / — 약 520억 명, / 지금까지 살아 본 모든 인간의 거의 절반."},
        {"no": 26, "en": "Winegard claims / that mosquitoes also played a role / in shaping the history of several countries.",
         "ko": "Winegard는 주장한다 / 모기가 또한 역할을 했다고 / 여러 나라의 역사를 형성하는 데."},
        {"no": 27, "en": "Take the Roman Empire, for example. / The fall of the Western Roman Empire was gradual, / spanning over centuries.",
         "ko": "로마 제국을 예로 들어보자. / 서로마 제국의 몰락은 점진적이었다, / 여러 세기에 걸쳐."},
        {"no": 28, "en": "Here are commonly cited reasons / for the fall of the empire: / invasions by outside forces, / economic troubles, and corruption.",
         "ko": "여기 흔히 언급되는 이유들이 있다 / 제국의 몰락에 대한: / 외세의 침략, / 경제적 문제, 그리고 부패."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">predator</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">disease</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">deadly</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">estimate</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">empire</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">fall</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">claim</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">invasion</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">corruption</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">nearly</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 자연</span> → <span class="q-fill"></span> &nbsp; <span class="kr">2) 세기(100년)</span> → <span class="q-fill"></span> &nbsp; <span class="kr">3) ~에 따르면</span> → <span class="q-fill lg"></span></div>
      <div class="q-line"><span class="kr">4) 옮기다/전염시키다</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">5) 여러/몇몇의</span> → <span class="q-fill"></span> &nbsp; <span class="kr">6) 원인</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>현재완료 완성하기 (오늘의 핵심 문법)</div>
      <div class="q-line">1) Mosquitoes ( have / has ) killed many people.</div>
      <div class="q-line">2) all humans who ( have / has ) ever lived &nbsp;→ 뜻: 지금까지 (&nbsp;<span class="q-fill lg"></span>&nbsp;) 모든 인간</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) Over a million people worldwide die of these diseases every year.<span class="q-write"></span></div>
      <div class="q-line">2) Mosquitoes have killed more people than any other single cause.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 포식자/천적 &nbsp; 2 질병 &nbsp; 3 치명적인 &nbsp; 4 추정하다 &nbsp; 5 제국 &nbsp; 6 몰락/붕괴 &nbsp; 7 주장하다 &nbsp; 8 침략 &nbsp; 9 부패 &nbsp; 10 거의</div>
    <div class="ans-block"><b>B.</b> 1 nature &nbsp; 2 century &nbsp; 3 according to &nbsp; 4 pass on &nbsp; 5 several &nbsp; 6 cause</div>
    <div class="ans-block"><b>C.</b> 1 have (주어 mosquitoes=여럿 → have) &nbsp; 2 have / <b>살아 본 적 있는</b> (경험의 현재완료)</div>
    <div class="ans-block"><b>D.</b> 1 매년 전 세계에서 백만 명이 넘는 사람들이 이런 질병으로 죽는다. &nbsp; 2 모기는 다른 어떤 단일 원인보다도 더 많은 사람을 죽여 왔다.</div>
    """,
}


# ============================================================
# 5일차 — 본문 29~34  (수동태 be + p.p.)
# ============================================================
DAY5 = {
    "day_no": 5,
    "title": "The Predator (포식자) ② — 로마 제국과 모기",
    "range_label": "PART 2 · 문장 29–34",
    "part_heading": None,
    "goal_grammar": "수동태 : be동사 + 과거분사(p.p.)",
    "goal_sub": "\"~되다 / ~당하다\" — 주어가 직접 하는 게 아니라 당하는 쪽. by ~ (~에 의해).",
    "passage": [
        {"no": 29, "en": "Diseases like malaria, however, also contributed."},
        {"no": 30, "en": "Rome, the capital of the empire, was once surrounded by a huge stretch of wetland."},
        {"no": 31, "en": "This was an ideal breeding ground for mosquitoes and hence a hot spot for malaria."},
        {"no": 32, "en": "On the one hand, mosquitoes helped protect the city against the armies coming to attack it."},
        {"no": 33, "en": "However, they eventually spread the disease not only throughout the city, but also throughout the empire, crushing much of the population."},
        {"no": 34, "en": "Here is another reason why Winegard considers the mosquito a powerful agent of historical change."},
    ],
    "vocab": [
        {"en": "contribute", "pron": "컨트리뷰트", "pos": "동사", "ko": "기여하다, 한몫하다"},
        {"en": "capital", "pron": "캐피털", "pos": "명사", "ko": "수도; 자본"},
        {"en": "once", "pron": "원스", "pos": "부사", "ko": "한때, 예전에; 한 번"},
        {"en": "surround", "pron": "써라운드", "pos": "동사", "ko": "둘러싸다, 에워싸다"},
        {"en": "huge", "pron": "휴즈", "pos": "형용사", "ko": "거대한, 엄청난"},
        {"en": "stretch", "pron": "스트레치", "pos": "명사", "ko": "펼쳐진 지역, 뻗은 구간"},
        {"en": "wetland", "pron": "웻랜드", "pos": "명사", "ko": "습지 (wet 젖은 + land 땅)"},
        {"en": "ideal", "pron": "아이디얼", "pos": "형용사", "ko": "이상적인, 더없이 좋은"},
        {"en": "breeding ground", "pron": "브리딩 그라운드", "pos": "명사", "ko": "번식지, 온상 (breed 번식하다)"},
        {"en": "hence", "pron": "헨스", "pos": "부사", "ko": "따라서, 그러므로"},
        {"en": "hot spot", "pron": "핫 스팟", "pos": "명사", "ko": "多발 지역, 창궐지, 핫스팟"},
        {"en": "on the one hand", "pron": "온 더 원 핸드", "pos": "숙어", "ko": "한편으로는"},
        {"en": "protect A against B", "pron": "프러텍트 어겐스트", "pos": "동사구", "ko": "B로부터 A를 보호하다"},
        {"en": "army", "pron": "아미", "pos": "명사", "ko": "군대 (복수 armies)"},
        {"en": "attack", "pron": "어택", "pos": "동사", "ko": "공격하다"},
        {"en": "eventually", "pron": "이벤추얼리", "pos": "부사", "ko": "결국, 마침내"},
        {"en": "spread", "pron": "스프레드", "pos": "동사", "ko": "퍼뜨리다, 퍼지다 (spread-spread-spread)"},
        {"en": "not only A but also B", "pron": "낫 온리 벗 올소", "pos": "숙어", "ko": "A뿐만 아니라 B도"},
        {"en": "crush", "pron": "크러시", "pos": "동사", "ko": "궤멸시키다, 짓밟다, 으스러뜨리다"},
        {"en": "population", "pron": "파퓰레이션", "pos": "명사", "ko": "인구, 개체 수"},
        {"en": "another", "pron": "어나더", "pos": "형용사", "ko": "또 하나의, 또 다른"},
        {"en": "consider A B", "pron": "컨시더", "pos": "동사구", "ko": "A를 B로 여기다·간주하다"},
        {"en": "powerful", "pron": "파워풀", "pos": "형용사", "ko": "강력한"},
        {"en": "agent", "pron": "에이전트", "pos": "명사", "ko": "동인, 원동력; 행위자"},
        {"en": "historical", "pron": "히스토리컬", "pos": "형용사", "ko": "역사의, 역사적인"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "수동태 : be동사 + 과거분사(p.p.) = \"~되다 / ~당하다\"",
         "rule": "주어가 스스로 하는 게 아니라 <b>당하는</b> 쪽일 때 써요. 형태는 <b>be(am/are/is/was/were) + p.p.</b>, &lsquo;<b>by + 행위자</b>&rsquo; 로 &lsquo;누구에 의해&rsquo; 를 붙여요.",
         "examples": [
             {"en": "Rome <span class='hl'>was surrounded by</span> a huge wetland.", "ko": "로마는 거대한 습지에 <b>둘러싸여 있었다</b>. (로마가 둘러싼 게 아니라 당한 것)"},
         ]},
        {"level": "", "tag": "문법 2", "title": "동격 콤마 : 명사, 명사, = \"~인 (명사)\"",
         "rule": "명사 뒤에 콤마로 다른 명사가 오면 <b>같은 대상을 다시 설명</b>하는 거예요.",
         "examples": [
             {"en": "Rome<span class='hl'>, the capital of the empire,</span>", "ko": "로마는<b>, 제국의 수도인데,</b>"},
         ]},
        {"level": "", "tag": "문법 3", "title": "not only A but also B = \"A뿐만 아니라 B도\"",
         "rule": "두 가지를 <b>모두</b> 강조할 때 써요. A와 B 자리에는 같은 종류(구·절)가 와요.",
         "examples": [
             {"en": "<span class='hl'>not only</span> throughout the city, <span class='hl'>but also</span> throughout the empire", "ko": "도시 전역<b>뿐만 아니라</b> 제국 전체<b>에도</b>"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "consider A B = \"A를 B로 여기다\" (5형식) / 관계부사 why",
         "rule": "동사 뒤에 &lsquo;A + B&rsquo; 두 덩어리가 오면 <b>&ldquo;A를 B라고 여긴다&rdquo;</b>. reason <b>why</b> ~ 는 &lsquo;~한 이유&rsquo;.",
         "examples": [
             {"en": "Winegard <span class='hl'>considers the mosquito a powerful agent</span>", "ko": "Winegard는 <b>모기를 강력한 동인이라 여긴다</b>"},
         ]},
    ],
    "literal": [
        {"no": 29, "en": "Diseases like malaria, / however, / also contributed.",
         "ko": "말라리아 같은 질병도, / 그러나, / 또한 기여했다."},
        {"no": 30, "en": "Rome, / the capital of the empire, / was once surrounded / by a huge stretch of wetland.",
         "ko": "로마는, / 제국의 수도였는데, / 한때 둘러싸여 있었다 / 거대하게 펼쳐진 습지로."},
        {"no": 31, "en": "This was an ideal breeding ground for mosquitoes / and hence a hot spot for malaria.",
         "ko": "이곳은 모기에게 이상적인 번식지였다 / 그래서 말라리아의 창궐지였다."},
        {"no": 32, "en": "On the one hand, / mosquitoes helped protect the city / against the armies / coming to attack it.",
         "ko": "한편으로, / 모기는 도시를 보호하는 데 도움이 되었다 / 군대로부터 / 그곳을 공격하러 오는."},
        {"no": 33, "en": "However, / they eventually spread the disease / not only throughout the city, / but also throughout the empire, / crushing much of the population.",
         "ko": "하지만, / 그들은 결국 질병을 퍼뜨렸다 / 도시 전역뿐만 아니라, / 제국 전체에도, / 인구의 상당수를 궤멸시키면서."},
        {"no": 34, "en": "Here is another reason / why Winegard considers the mosquito / a powerful agent of historical change.",
         "ko": "여기 또 하나의 이유가 있다 / Winegard가 모기를 여기는 / 역사 변천의 강력한 동인이라고."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">capital</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">surround</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">wetland</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">ideal</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">eventually</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">spread</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">population</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">contribute</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">powerful</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">attack</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 수도</span> → <span class="q-fill"></span> &nbsp; <span class="kr">2) 군대</span> → <span class="q-fill"></span> &nbsp; <span class="kr">3) 결국</span> → <span class="q-fill lg"></span></div>
      <div class="q-line"><span class="kr">4) 인구</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">5) 거대한</span> → <span class="q-fill"></span> &nbsp; <span class="kr">6) 따라서/그러므로</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>수동태 고르기 (오늘의 핵심 문법)</div>
      <div class="q-line">1) Rome ( surrounded / was surrounded ) by a huge wetland.</div>
      <div class="q-line">2) 위 문장의 주어 Rome은 습지를 ( 둘러쌌다 / 둘러싸였다 ). &nbsp;→ 알맞은 것에 &#9711;</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) Rome, the capital of the empire, was once surrounded by a huge stretch of wetland.<span class="q-write"></span></div>
      <div class="q-line">2) They spread the disease not only throughout the city, but also throughout the empire.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 수도/자본 &nbsp; 2 둘러싸다 &nbsp; 3 습지 &nbsp; 4 이상적인 &nbsp; 5 결국/마침내 &nbsp; 6 퍼뜨리다/퍼지다 &nbsp; 7 인구/개체 수 &nbsp; 8 기여하다 &nbsp; 9 강력한 &nbsp; 10 공격하다</div>
    <div class="ans-block"><b>B.</b> 1 capital &nbsp; 2 army &nbsp; 3 eventually &nbsp; 4 population &nbsp; 5 huge &nbsp; 6 hence</div>
    <div class="ans-block"><b>C.</b> 1 was surrounded (수동태 be+p.p.) &nbsp; 2 둘러싸였다 (당하는 쪽 = 수동)</div>
    <div class="ans-block"><b>D.</b> 1 제국의 수도였던 로마는 한때 거대하게 펼쳐진 습지로 둘러싸여 있었다. &nbsp; 2 그들은 도시 전역뿐만 아니라 제국 전체에도 질병을 퍼뜨렸다.</div>
    """,
}


# ============================================================
# 6일차 — 본문 35~40  (과거완료 had p.p.)
# ============================================================
DAY6 = {
    "day_no": 6,
    "title": "The Predator (포식자) ③ — 스코틀랜드의 실패",
    "range_label": "PART 2 · 문장 35–40",
    "part_heading": None,
    "goal_grammar": "과거완료 : had + 과거분사(p.p.)",
    "goal_sub": "\"(과거의 그때보다) 더 이전에 ~했었다\" — 과거보다 한 발 더 앞선 과거.",
    "passage": [
        {"no": 35, "en": "In 1698, five ships set sail from Scotland, carrying twelve hundred settlers and valuable trade goods."},
        {"no": 36, "en": "They headed for the Darien region of Panama, where Scotland planned to create a trading center."},
        {"no": 37, "en": "After struggling through years of a food crisis, Scotland had hoped this would help raise its economic prospects."},
        {"no": 38, "en": "The ambitious plan, however, was brought down by the local diseases: yellow fever and malaria."},
        {"no": 39, "en": "Virtually no one from Scotland had ever encountered any of these diseases before."},
        {"no": 40, "en": "After six months, nearly half of them died, and the survivors returned to their ships and fled."},
    ],
    "vocab": [
        {"en": "set sail", "pron": "셋 세일", "pos": "동사구", "ko": "출항하다, 항해를 시작하다 (sail 항해하다)"},
        {"en": "carry", "pron": "캐리", "pos": "동사", "ko": "나르다, 싣다, 운반하다"},
        {"en": "settler", "pron": "세틀러", "pos": "명사", "ko": "정착민 (settle 정착하다)"},
        {"en": "valuable", "pron": "밸류어블", "pos": "형용사", "ko": "값진, 귀중한 (value 가치)"},
        {"en": "trade goods", "pron": "트레이드 굿즈", "pos": "명사", "ko": "교역 물자, 무역 상품 (goods 상품)"},
        {"en": "head for", "pron": "헤드 포", "pos": "동사", "ko": "~로 향하다, 가다"},
        {"en": "region", "pron": "리전", "pos": "명사", "ko": "지역, 지방"},
        {"en": "plan to", "pron": "플랜 투", "pos": "동사", "ko": "~할 계획이다"},
        {"en": "create", "pron": "크리에이트", "pos": "동사", "ko": "만들다, 창조하다"},
        {"en": "trading center", "pron": "트레이딩 센터", "pos": "명사", "ko": "교역 거점, 무역 중심지"},
        {"en": "struggle through", "pron": "스트러글 쓰루", "pos": "동사", "ko": "~을 힘겹게 헤쳐 나가다"},
        {"en": "food crisis", "pron": "푸드 크라이시스", "pos": "명사", "ko": "식량난, 식량 위기 (crisis 위기)"},
        {"en": "hope", "pron": "호프", "pos": "동사", "ko": "바라다, 희망하다"},
        {"en": "raise", "pron": "레이즈", "pos": "동사", "ko": "높이다, 올리다, 끌어올리다"},
        {"en": "economic prospects", "pron": "이코노믹 프라스펙츠", "pos": "명사", "ko": "경제적 전망 (prospect 전망)"},
        {"en": "ambitious", "pron": "앰비셔스", "pos": "형용사", "ko": "야심 찬, 원대한 (ambition 야망)"},
        {"en": "bring down", "pron": "브링 다운", "pos": "동사", "ko": "무너뜨리다, 좌절시키다 (bring-brought-brought)"},
        {"en": "local", "pron": "로컬", "pos": "형용사", "ko": "그 지역의, 현지의; 풍토의"},
        {"en": "virtually", "pron": "버추얼리", "pos": "부사", "ko": "사실상, 거의"},
        {"en": "no one", "pron": "노 원", "pos": "대명사", "ko": "아무도 ~않다"},
        {"en": "encounter", "pron": "인카운터", "pos": "동사", "ko": "맞닥뜨리다, (병 등을) 접하다"},
        {"en": "survivor", "pron": "써바이버", "pos": "명사", "ko": "생존자 (survive 살아남다)"},
        {"en": "return", "pron": "리턴", "pos": "동사", "ko": "돌아가다, 돌아오다"},
        {"en": "flee", "pron": "플리", "pos": "동사", "ko": "달아나다, 도망치다 (flee-fled-fled)"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "과거완료 : had + 과거분사(p.p.) = \"(그 전에) ~했었다\"",
         "rule": "과거의 어느 시점을 기준으로, 그보다 <b>더 이전에</b> 일어난 일을 나타내요. 형태는 <b>had + p.p.</b> (주어와 상관없이 had). &lsquo;~한 적이 있었다(경험)&rsquo; 도 자주 나와요.",
         "examples": [
             {"en": "Scotland <span class='hl'>had hoped</span> this would help …", "ko": "스코틀랜드는 이것이 도움이 되기를 <b>바랐었다</b> (그 전에)"},
             {"en": "no one <span class='hl'>had ever encountered</span> these diseases before", "ko": "아무도 이런 병을 이전에 <b>접해 본 적이 없었다</b>"},
         ]},
        {"level": "", "tag": "문법 2", "title": "수동태 (복습) : was brought down by",
         "rule": "5일차의 수동태! <b>be + p.p.</b> = &lsquo;~되다/당하다&rsquo;. bring down 의 p.p.는 <b>brought down</b>.",
         "examples": [
             {"en": "The plan <span class='hl'>was brought down by</span> the diseases.", "ko": "그 계획은 질병에 의해 <b>무너졌다</b>."},
         ]},
        {"level": "", "tag": "문법 3", "title": "관계부사 where = \"그곳에서 ~하는\" (장소)",
         "rule": "장소 명사 뒤의 <b>where</b> 는 &lsquo;그곳에서 ~하는&rsquo; 이라는 설명을 붙여요.",
         "examples": [
             {"en": "the Darien region, <span class='hl'>where</span> Scotland planned to create a center", "ko": "다리엔 지역, <b>그곳에</b> 스코틀랜드가 거점을 만들려던"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "분사구문 (복습) : carrying ~ = \"~을 싣고서\"",
         "rule": "문장 뒤의 <b>동사+ing</b> 덩어리는 &lsquo;~하면서/~한 채로&rsquo;. after <b>struggling</b> 처럼 &lsquo;전치사+ing&rsquo; 도 자주 나와요.",
         "examples": [
             {"en": "five ships set sail, <span class='hl'>carrying</span> settlers and goods", "ko": "다섯 척의 배가 출항했다, 정착민과 물자를 <b>싣고서</b>"},
         ]},
    ],
    "literal": [
        {"no": 35, "en": "In 1698, / five ships set sail from Scotland, / carrying twelve hundred settlers / and valuable trade goods.",
         "ko": "1698년에, / 다섯 척의 배가 스코틀랜드에서 출항했다, / 1,200명의 정착민을 싣고 / 그리고 값진 교역 물자를."},
        {"no": 36, "en": "They headed for the Darien region of Panama, / where Scotland planned to create a trading center.",
         "ko": "그들은 파나마의 다리엔 지역으로 향했다, / 그곳에 스코틀랜드는 교역 거점을 만들 계획이었다."},
        {"no": 37, "en": "After struggling through years of a food crisis, / Scotland had hoped / this would help raise its economic prospects.",
         "ko": "수년간의 식량난을 힘겹게 헤쳐 나온 뒤, / 스코틀랜드는 바랐었다 / 이것이 경제적 전망을 끌어올리는 데 도움이 되기를."},
        {"no": 38, "en": "The ambitious plan, however, / was brought down / by the local diseases: / yellow fever and malaria.",
         "ko": "그 야심 찬 계획은, 그러나, / 무너졌다 / 그 지역의 질병들로: / 황열과 말라리아."},
        {"no": 39, "en": "Virtually no one from Scotland / had ever encountered / any of these diseases / before.",
         "ko": "스코틀랜드에서 온 사람은 사실상 아무도 / 접해 본 적이 없었다 / 이런 질병들 중 어느 것도 / 이전에."},
        {"no": 40, "en": "After six months, / nearly half of them died, / and the survivors returned to their ships / and fled.",
         "ko": "6개월 후, / 그들 중 거의 절반이 죽었고, / 생존자들은 배로 돌아가 / 달아났다."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">settler</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">valuable</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">region</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">ambitious</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">encounter</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">survivor</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">flee</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">virtually</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">raise</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">create</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 출항하다</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">2) ~로 향하다</span> → <span class="q-fill"></span> &nbsp; <span class="kr">3) 식량난</span> → <span class="q-fill lg"></span></div>
      <div class="q-line"><span class="kr">4) 정착민</span> → <span class="q-fill"></span> &nbsp; <span class="kr">5) 생존자</span> → <span class="q-fill"></span> &nbsp; <span class="kr">6) 돌아가다</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>과거완료 고르기 (오늘의 핵심 문법)</div>
      <div class="q-line">1) No one ( has / had ) ever encountered these diseases before.</div>
      <div class="q-line">2) &lsquo;had + p.p.&rsquo; 는 과거보다 ( 더 이전 / 더 나중 )의 일을 나타낸다. &nbsp;→ 알맞은 것에 &#9711;</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) Virtually no one from Scotland had ever encountered any of these diseases before.<span class="q-write"></span></div>
      <div class="q-line">2) After six months, nearly half of them died, and the survivors returned to their ships and fled.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 정착민 &nbsp; 2 값진/귀중한 &nbsp; 3 지역 &nbsp; 4 야심 찬 &nbsp; 5 맞닥뜨리다/접하다 &nbsp; 6 생존자 &nbsp; 7 달아나다/도망치다 &nbsp; 8 사실상/거의 &nbsp; 9 높이다/끌어올리다 &nbsp; 10 만들다/창조하다</div>
    <div class="ans-block"><b>B.</b> 1 set sail &nbsp; 2 head for &nbsp; 3 food crisis &nbsp; 4 settler &nbsp; 5 survivor &nbsp; 6 return</div>
    <div class="ans-block"><b>C.</b> 1 had (과거완료) &nbsp; 2 더 이전 (과거보다 앞선 과거)</div>
    <div class="ans-block"><b>D.</b> 1 스코틀랜드에서 온 사람은 사실상 아무도 이전에 이런 질병들 중 어느 것도 접해 본 적이 없었다. &nbsp; 2 6개월 후, 그들 중 거의 절반이 죽었고, 생존자들은 배로 돌아가 달아났다.</div>
    """,
}


# ============================================================
# 7일차 — 본문 41~45  (가정법 과거완료)
# ============================================================
DAY7 = {
    "day_no": 7,
    "title": "The Predator (포식자) ④ — 뒤늦게 밝혀진 진실",
    "range_label": "PART 2 · 문장 41–45",
    "part_heading": None,
    "goal_grammar": "가정법 과거완료 : If + had p.p., 주어 would have p.p.",
    "goal_sub": "\"(과거에) ~했더라면 ~했을 텐데\" — 이미 지나간 일에 대한 후회·아쉬움. 사실은 반대!",
    "passage": [
        {"no": 41, "en": "If their immune systems had been much stronger, they would not have lost so many lives in such a short time."},
        {"no": 42, "en": "Surprisingly, human beings lived with and died of these diseases for thousands of years without understanding how they were spread."},
        {"no": 43, "en": "It was not until the end of the nineteenth century that we found out that mosquitoes spread malaria."},
        {"no": 44, "en": "Before this finding, no one imagined that these tiny annoying insects might be affecting our lives so deeply."},
        {"no": 45, "en": "Now we all know that human history is not free from the workings of the natural world."},
    ],
    "vocab": [
        {"en": "immune system", "pron": "이뮨 시스템", "pos": "명사", "ko": "면역 체계, 면역계"},
        {"en": "much", "pron": "머치", "pos": "부사", "ko": "(비교급 강조) 훨씬"},
        {"en": "stronger", "pron": "스트롱거", "pos": "형용사", "ko": "더 강한 (strong의 비교급)"},
        {"en": "lose", "pron": "루즈", "pos": "동사", "ko": "잃다 (lose-lost-lost)"},
        {"en": "so many", "pron": "소 메니", "pos": "표현", "ko": "그토록 많은"},
        {"en": "such a short time", "pron": "서치 어 숏 타임", "pos": "표현", "ko": "그토록 짧은 시간"},
        {"en": "surprisingly", "pron": "서프라이징리", "pos": "부사", "ko": "놀랍게도"},
        {"en": "human being", "pron": "휴먼 비잉", "pos": "명사", "ko": "인간, 사람"},
        {"en": "die of", "pron": "다이 오브", "pos": "동사", "ko": "~로 죽다"},
        {"en": "thousands of", "pron": "싸우전즈 오브", "pos": "표현", "ko": "수천의, 수천 년의"},
        {"en": "without ~ing", "pron": "위드아웃", "pos": "숙어", "ko": "~하지 않은 채, ~없이"},
        {"en": "understand", "pron": "언더스탠드", "pos": "동사", "ko": "이해하다, 알다"},
        {"en": "spread", "pron": "스프레드", "pos": "동사", "ko": "퍼지다, 퍼뜨리다 (be spread 퍼지다)"},
        {"en": "not until", "pron": "낫 언틸", "pos": "숙어", "ko": "~이 되어서야 비로소"},
        {"en": "nineteenth century", "pron": "나인틴쓰 센추리", "pos": "명사", "ko": "19세기"},
        {"en": "find out", "pron": "파인드 아웃", "pos": "동사", "ko": "알아내다, 알게 되다"},
        {"en": "finding", "pron": "파인딩", "pos": "명사", "ko": "발견, 밝혀진 사실"},
        {"en": "imagine", "pron": "이매진", "pos": "동사", "ko": "상상하다"},
        {"en": "tiny", "pron": "타이니", "pos": "형용사", "ko": "아주 작은"},
        {"en": "insect", "pron": "인섹트", "pos": "명사", "ko": "곤충, 벌레"},
        {"en": "affect", "pron": "어펙트", "pos": "동사", "ko": "영향을 주다, 영향을 미치다"},
        {"en": "deeply", "pron": "디플리", "pos": "부사", "ko": "깊이, 깊게"},
        {"en": "be free from", "pron": "비 프리 프롬", "pos": "숙어", "ko": "~에서 자유롭다, ~와 무관하다"},
        {"en": "workings", "pron": "워킹즈", "pos": "명사", "ko": "작용, 작동 방식"},
        {"en": "natural world", "pron": "내추럴 월드", "pos": "명사", "ko": "자연계, 자연 세계"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "가정법 과거완료 : If + had p.p., 주어 would have p.p.",
         "rule": "&ldquo;(과거에) ~했더라면 …했을 텐데&rdquo; 처럼 <b>과거 사실과 반대</b>되는 상상·후회예요. If절은 <b>had + p.p.</b>, 주절은 <b>would/could have + p.p.</b>. (3일차 가정법 과거는 &lsquo;현재&rsquo;, 오늘은 &lsquo;과거&rsquo;!)",
         "examples": [
             {"en": "If their immune systems <span class='hl'>had been</span> stronger, they <span class='hl'>would not have lost</span> so many lives.", "ko": "면역계가 더 강했<b>더라면</b>, 그토록 많은 목숨을 잃지 않<b>았을 텐데</b>. (→ 사실은 약해서 많이 죽었다)"},
         ]},
        {"level": "", "tag": "문법 2", "title": "without + ~ing = \"~하지 않은 채, ~없이\"",
         "rule": "전치사 <b>without</b> 뒤에는 <b>동사+ing</b> 가 와서 &lsquo;~하지 않고&rsquo; 라는 뜻이 돼요.",
         "examples": [
             {"en": "<span class='hl'>without understanding</span> how they were spread", "ko": "그것들이 어떻게 퍼지는지 <b>알지 못한 채</b>"},
         ]},
        {"level": "", "tag": "문법 3", "title": "It was not until ~ that … = \"~이 되어서야 비로소 …했다\"",
         "rule": "강조 구문 <b>It was ~ that …</b> 와 <b>not until</b> 이 합쳐진 표현이에요. &lsquo;그제서야&rsquo; 느낌으로 해석해요.",
         "examples": [
             {"en": "<span class='hl'>It was not until</span> the end of the 19th century <span class='hl'>that</span> we found out …", "ko": "19세기 말이 <b>되어서야 비로소</b> 우리는 알아냈다 …"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "be free from = \"~에서 자유롭다 / ~와 무관하다\"",
         "rule": "마지막 문장의 핵심 표현! <b>not free from</b> = &lsquo;~에서 자유롭지 못하다&rsquo; = &lsquo;영향을 받는다&rsquo;.",
         "examples": [
             {"en": "human history is <span class='hl'>not free from</span> the natural world", "ko": "인간 역사는 자연계에서 <b>자유롭지 못하다</b> (= 영향을 받는다)"},
         ]},
    ],
    "literal": [
        {"no": 41, "en": "If their immune systems had been much stronger, / they would not have lost so many lives / in such a short time.",
         "ko": "만약 그들의 면역계가 훨씬 더 강했더라면, / 그토록 많은 목숨을 잃지 않았을 텐데 / 그토록 짧은 시간에."},
        {"no": 42, "en": "Surprisingly, / human beings lived with and died of these diseases / for thousands of years / without understanding how they were spread.",
         "ko": "놀랍게도, / 인간은 이 질병들과 함께 살고 그로 인해 죽었다 / 수천 년 동안 / 그것들이 어떻게 퍼지는지 알지 못한 채."},
        {"no": 43, "en": "It was not until the end of the nineteenth century / that we found out / that mosquitoes spread malaria.",
         "ko": "19세기 말이 되어서야 비로소 / 우리는 알아냈다 / 모기가 말라리아를 퍼뜨린다는 것을."},
        {"no": 44, "en": "Before this finding, / no one imagined / that these tiny annoying insects / might be affecting our lives so deeply.",
         "ko": "이 발견 이전에는, / 아무도 상상하지 못했다 / 이 작고 성가신 곤충들이 / 우리 삶에 그토록 깊이 영향을 주고 있을지도 모른다는 것을."},
        {"no": 45, "en": "Now we all know / that human history is not free / from the workings of the natural world.",
         "ko": "이제 우리는 모두 안다 / 인간의 역사가 자유롭지 못하다는 것을 / 자연계의 작용으로부터."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">immune system</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">lose</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">surprisingly</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">find out</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">imagine</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">tiny</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">insect</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">affect</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">deeply</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">finding</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 인간/사람</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">2) 면역계</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">3) 곤충</span> → <span class="q-fill"></span></div>
      <div class="q-line"><span class="kr">4) 상상하다</span> → <span class="q-fill"></span> &nbsp; <span class="kr">5) 영향을 주다</span> → <span class="q-fill"></span> &nbsp; <span class="kr">6) 알아내다</span> → <span class="q-fill lg"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>가정법 과거완료 완성하기 (오늘의 핵심 문법)</div>
      <div class="q-line">1) If their immune systems ( had been / were ) stronger, they ( would not have lost / would not lose ) so many lives.</div>
      <div class="q-line">2) 위 문장은 실제로 면역계가 ( 강했다 / 약했다 )는 뜻이다. &nbsp;→ 알맞은 것에 &#9711;</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) It was not until the end of the nineteenth century that we found out that mosquitoes spread malaria.<span class="q-write"></span></div>
      <div class="q-line">2) Now we all know that human history is not free from the workings of the natural world.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 면역 체계 &nbsp; 2 잃다 &nbsp; 3 놀랍게도 &nbsp; 4 알아내다/알게 되다 &nbsp; 5 상상하다 &nbsp; 6 아주 작은 &nbsp; 7 곤충 &nbsp; 8 영향을 주다 &nbsp; 9 깊이 &nbsp; 10 발견/밝혀진 사실</div>
    <div class="ans-block"><b>B.</b> 1 human being &nbsp; 2 immune system &nbsp; 3 insect &nbsp; 4 imagine &nbsp; 5 affect &nbsp; 6 find out</div>
    <div class="ans-block"><b>C.</b> 1 had been, would not have lost (가정법 과거완료) &nbsp; 2 약했다 (사실의 반대 → 실제로는 약해서 많이 죽었다)</div>
    <div class="ans-block"><b>D.</b> 1 19세기 말이 되어서야 비로소 우리는 모기가 말라리아를 퍼뜨린다는 것을 알아냈다. &nbsp; 2 이제 우리는 모두 인간의 역사가 자연계의 작용에서 자유롭지 못하다는 것을 안다.</div>
    """,
}


# ============================================================
# 8일차 — 본문 외(무당벌레) 1~6  (최상급)
# ============================================================
DAY8 = {
    "day_no": 8,
    "title": "본문 외 지문 · Ladybugs (무당벌레)",
    "range_label": "본문 외 · 무당벌레 문장 1–6",
    "part_heading": "■ Ladybugs (무당벌레)",
    "goal_grammar": "최상급 : the + 최상급(-est / most ~) = \"가장 ~한\"",
    "goal_sub": "of/in ~ 와 함께 \"(~ 중에서) 가장 …한\". 짧은 단어는 -est, 긴 단어는 most.",
    "passage": [
        {"no": 1, "en": "Ladybugs are probably the most well-known of all the helpful bugs in the garden."},
        {"no": 2, "en": "First of all, they eat quite a few of the bad bugs that prevent plants from growing."},
        {"no": 3, "en": "Each ladybug can eat fifty to sixty aphids per day and over five thousand in its lifetime."},
        {"no": 4, "en": "Their young eat aphids, too."},
        {"no": 5, "en": "If you grow plants that attract ladybugs, such as cilantro or mint, you may not have to worry about harmful bugs anymore."},
        {"no": 6, "en": "Even better, ladybugs can defend themselves by giving off a certain smell that their predators do not like."},
    ],
    "vocab": [
        {"en": "ladybug", "pron": "레이디버그", "pos": "명사", "ko": "무당벌레"},
        {"en": "probably", "pron": "프라버블리", "pos": "부사", "ko": "아마도"},
        {"en": "well-known", "pron": "웰 노운", "pos": "형용사", "ko": "잘 알려진, 유명한"},
        {"en": "helpful", "pron": "헬프풀", "pos": "형용사", "ko": "도움이 되는, 유익한"},
        {"en": "bug", "pron": "버그", "pos": "명사", "ko": "벌레, 곤충"},
        {"en": "garden", "pron": "가든", "pos": "명사", "ko": "정원, 텃밭"},
        {"en": "first of all", "pron": "퍼스트 오브 올", "pos": "숙어", "ko": "우선, 무엇보다 먼저"},
        {"en": "quite a few", "pron": "콰이트 어 퓨", "pos": "표현", "ko": "상당수, 꽤 많은"},
        {"en": "prevent A from ~ing", "pron": "프리벤트 프롬", "pos": "동사구", "ko": "A가 ~하는 것을 막다"},
        {"en": "grow", "pron": "그로우", "pos": "동사", "ko": "자라다, 기르다 (grow-grew-grown)"},
        {"en": "each", "pron": "이치", "pos": "형용사", "ko": "각각의, 각 (뒤에 단수)"},
        {"en": "aphid", "pron": "에이피드", "pos": "명사", "ko": "진딧물"},
        {"en": "per day", "pron": "퍼 데이", "pos": "부사구", "ko": "하루에, 하루당"},
        {"en": "over", "pron": "오버", "pos": "전치사", "ko": "~이 넘는, ~ 이상"},
        {"en": "lifetime", "pron": "라이프타임", "pos": "명사", "ko": "일생, 평생"},
        {"en": "young", "pron": "영", "pos": "명사", "ko": "(동물의) 새끼, 유충"},
        {"en": "such as", "pron": "서치 애즈", "pos": "숙어", "ko": "~와 같은, 예를 들어"},
        {"en": "cilantro", "pron": "실란트로", "pos": "명사", "ko": "고수 (허브의 일종)"},
        {"en": "mint", "pron": "민트", "pos": "명사", "ko": "박하, 민트"},
        {"en": "have to", "pron": "해브 투", "pos": "조동사", "ko": "~해야 한다 (don't have to ~할 필요 없다)"},
        {"en": "worry about", "pron": "워리 어바웃", "pos": "동사", "ko": "~에 대해 걱정하다"},
        {"en": "harmful", "pron": "함풀", "pos": "형용사", "ko": "해로운 (harm 해)"},
        {"en": "anymore", "pron": "애니모어", "pos": "부사", "ko": "더 이상 (부정문에서)"},
        {"en": "even better", "pron": "이븐 베터", "pos": "표현", "ko": "한결 더 좋은 것은"},
        {"en": "defend", "pron": "디펜드", "pos": "동사", "ko": "방어하다, 지키다"},
        {"en": "give off", "pron": "기브 오프", "pos": "동사", "ko": "(냄새·빛 등을) 내뿜다, 발산하다"},
        {"en": "certain", "pron": "써튼", "pos": "형용사", "ko": "특정한, 어떤"},
        {"en": "smell", "pron": "스멜", "pos": "명사", "ko": "냄새"},
        {"en": "predator", "pron": "프레데터", "pos": "명사", "ko": "포식자, 천적"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "최상급 : the + 최상급 = \"가장 ~한\"",
         "rule": "여럿 중 &lsquo;가장&rsquo; 을 말할 때 써요. <b>짧은 단어</b>는 <b>-est</b> (tall→tallest), <b>긴 단어</b>는 앞에 <b>most</b> (famous→most famous). 앞에 <b>the</b> 를 붙이고, &lsquo;<b>of/in ~</b>&rsquo; 로 범위를 나타내요.",
         "examples": [
             {"en": "the <span class='hl'>most well-known</span> of all the helpful bugs", "ko": "모든 이로운 벌레 중 <b>가장 잘 알려진</b>"},
         ]},
        {"level": "", "tag": "문법 2", "title": "prevent A from ~ing = \"A가 ~하는 것을 막다\"",
         "rule": "&lsquo;막다/방해하다&rsquo; 계열 동사는 <b>from + ~ing</b> 과 짝을 이뤄요.",
         "examples": [
             {"en": "bad bugs that <span class='hl'>prevent</span> plants <span class='hl'>from growing</span>", "ko": "식물이 <b>자라는 것을 막는</b> 나쁜 벌레들"},
         ]},
        {"level": "", "tag": "문법 3", "title": "don't have to = \"~할 필요 없다\"",
         "rule": "<b>have to</b>(~해야 한다)의 부정은 &lsquo;하지 말라&rsquo;가 아니라 <b>&ldquo;~할 필요 없다&rdquo;</b> 예요. 헷갈리기 쉬운 시험 포인트!",
         "examples": [
             {"en": "you <span class='hl'>may not have to</span> worry about bugs", "ko": "벌레에 대해 <b>걱정하지 않아도 될지도</b> 모른다"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "재귀대명사 -self / by ~ing",
         "rule": "주어와 목적어가 같으면 <b>themselves</b>(그들 자신)처럼 &lsquo;-self/-selves&rsquo;. <b>by + ~ing</b> 는 &lsquo;~함으로써&rsquo;(방법).",
         "examples": [
             {"en": "ladybugs can defend <span class='hl'>themselves</span> <span class='hl'>by giving off</span> a smell", "ko": "무당벌레는 냄새를 <b>내뿜음으로써</b> <b>스스로를</b> 방어한다"},
         ]},
    ],
    "literal": [
        {"no": 1, "en": "Ladybugs are probably / the most well-known / of all the helpful bugs / in the garden.",
         "ko": "무당벌레는 아마도 / 가장 잘 알려져 있다 / 모든 이로운 벌레 중에서 / 정원에서."},
        {"no": 2, "en": "First of all, / they eat quite a few of the bad bugs / that prevent plants from growing.",
         "ko": "우선, / 그들은 나쁜 벌레의 상당수를 먹는다 / 식물이 자라는 것을 막는."},
        {"no": 3, "en": "Each ladybug can eat / fifty to sixty aphids per day / and over five thousand / in its lifetime.",
         "ko": "각 무당벌레는 먹을 수 있다 / 하루에 진딧물 50~60마리를 / 그리고 5천 마리 넘게 / 평생에."},
        {"no": 4, "en": "Their young / eat aphids, / too.",
         "ko": "그들의 새끼도 / 진딧물을 먹는다, / 또한."},
        {"no": 5, "en": "If you grow plants / that attract ladybugs, / such as cilantro or mint, / you may not have to worry / about harmful bugs anymore.",
         "ko": "만약 네가 식물을 기르면 / 무당벌레를 끌어들이는, / 고수나 박하 같은, / 너는 걱정하지 않아도 될지 모른다 / 해로운 벌레에 대해 더 이상."},
        {"no": 6, "en": "Even better, / ladybugs can defend themselves / by giving off a certain smell / that their predators do not like.",
         "ko": "한결 더 좋은 것은, / 무당벌레가 스스로를 방어할 수 있다는 것이다 / 특정한 냄새를 내뿜음으로써 / 그들의 포식자가 좋아하지 않는."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">ladybug</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">helpful</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">garden</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">grow</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">lifetime</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">harmful</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">defend</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">give off</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">smell</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">predator</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 우선</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">2) 아마도</span> → <span class="q-fill"></span> &nbsp; <span class="kr">3) 더 이상</span> → <span class="q-fill"></span></div>
      <div class="q-line"><span class="kr">4) 걱정하다</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">5) 벌레</span> → <span class="q-fill"></span> &nbsp; <span class="kr">6) 잘 알려진</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>최상급 고르기 (오늘의 핵심 문법)</div>
      <div class="q-line">1) Ladybugs are the ( more / most ) well-known of all the helpful bugs.</div>
      <div class="q-line">2) &lsquo;the most well-known&rsquo; 의 뜻: 가장 ( 잘 알려진 / 덜 알려진 ). &nbsp;→ 알맞은 것에 &#9711;</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) They eat quite a few of the bad bugs that prevent plants from growing.<span class="q-write"></span></div>
      <div class="q-line">2) Ladybugs can defend themselves by giving off a certain smell.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 무당벌레 &nbsp; 2 도움이 되는 &nbsp; 3 정원/텃밭 &nbsp; 4 자라다/기르다 &nbsp; 5 일생/평생 &nbsp; 6 해로운 &nbsp; 7 방어하다 &nbsp; 8 내뿜다/발산하다 &nbsp; 9 냄새 &nbsp; 10 포식자/천적</div>
    <div class="ans-block"><b>B.</b> 1 first of all &nbsp; 2 probably &nbsp; 3 anymore &nbsp; 4 worry about &nbsp; 5 bug &nbsp; 6 well-known</div>
    <div class="ans-block"><b>C.</b> 1 most (well-known은 긴 단어 → most) &nbsp; 2 잘 알려진</div>
    <div class="ans-block"><b>D.</b> 1 그들은 식물이 자라는 것을 막는 나쁜 벌레의 상당수를 먹는다. &nbsp; 2 무당벌레는 특정한 냄새를 내뿜음으로써 스스로를 방어할 수 있다.</div>
    """,
}


# ============================================================
# 9일차 — 본문 외(지렁이) 7~12  (동명사)
# ============================================================
DAY9 = {
    "day_no": 9,
    "title": "본문 외 지문 · Earthworms (지렁이)",
    "range_label": "본문 외 · 지렁이 문장 7–12",
    "part_heading": "■ Earthworms (지렁이)",
    "goal_grammar": "동명사 : 동사+ing 가 \"~하는 것/~함\" (명사 역할)",
    "goal_sub": "전치사(by·at·about·after) 뒤에는 반드시 ~ing! \"~함으로써 / ~하는 것에 / ~한 뒤\".",
    "passage": [
        {"no": 7, "en": "Earthworms are a great addition to your garden as well."},
        {"no": 8, "en": "They help keep your soil soft and breathable by digging tunnels that bring air to the roots of plants."},
        {"no": 9, "en": "They also eat the dead bits of plants that fall to the ground, recycling them back into the soil and helping new plants to grow."},
        {"no": 10, "en": "Moreover, their waste makes your soil richer, and they are excellent at breaking down organic matter in your garden."},
        {"no": 11, "en": "However, you should be careful about applying artificial fertilizers to your garden after introducing earthworms."},
        {"no": 12, "en": "They will find a new home when the soil around them changes."},
    ],
    "vocab": [
        {"en": "earthworm", "pron": "어쓰웜", "pos": "명사", "ko": "지렁이 (earth 흙 + worm 벌레)"},
        {"en": "addition", "pron": "어디션", "pos": "명사", "ko": "추가되는 것, 보탬 (add 더하다)"},
        {"en": "as well", "pron": "애즈 웰", "pos": "부사", "ko": "또한, 역시"},
        {"en": "help", "pron": "헬프", "pos": "동사", "ko": "돕다 (help + 동사원형: ~하는 것을 돕다)"},
        {"en": "keep A 형용사", "pron": "킵", "pos": "동사구", "ko": "A를 ~한 상태로 유지하다"},
        {"en": "soil", "pron": "소일", "pos": "명사", "ko": "흙, 토양"},
        {"en": "soft", "pron": "소프트", "pos": "형용사", "ko": "부드러운"},
        {"en": "breathable", "pron": "브리더블", "pos": "형용사", "ko": "통기성 있는, 숨 쉴 수 있는"},
        {"en": "dig", "pron": "디그", "pos": "동사", "ko": "파다 (dig-dug-dug)"},
        {"en": "tunnel", "pron": "터널", "pos": "명사", "ko": "굴, 터널"},
        {"en": "root", "pron": "루트", "pos": "명사", "ko": "뿌리"},
        {"en": "dead bits", "pron": "데드 비츠", "pos": "명사", "ko": "죽은 부분·조각 (bit 조각)"},
        {"en": "fall to the ground", "pron": "폴 투 더 그라운드", "pos": "동사구", "ko": "땅에 떨어지다"},
        {"en": "recycle", "pron": "리사이클", "pos": "동사", "ko": "재순환시키다, 재활용하다"},
        {"en": "back into", "pron": "백 인투", "pos": "전치사구", "ko": "다시 ~ 속으로"},
        {"en": "moreover", "pron": "모어오버", "pos": "부사", "ko": "게다가, 더욱이"},
        {"en": "waste", "pron": "웨이스트", "pos": "명사", "ko": "배설물, 노폐물; 낭비"},
        {"en": "make A 비교급", "pron": "메이크", "pos": "동사구", "ko": "A를 더 ~하게 만들다"},
        {"en": "rich", "pron": "리치", "pos": "형용사", "ko": "비옥한; 풍부한 (richer 더 비옥한)"},
        {"en": "excellent at", "pron": "엑설런트 앳", "pos": "형용사구", "ko": "~에 탁월한, 뛰어난"},
        {"en": "break down", "pron": "브레이크 다운", "pos": "동사", "ko": "분해하다, 부수다"},
        {"en": "organic matter", "pron": "오가닉 매터", "pos": "명사", "ko": "유기물 (matter 물질)"},
        {"en": "careful about", "pron": "케어풀 어바웃", "pos": "형용사구", "ko": "~에 대해 조심하는"},
        {"en": "apply", "pron": "어플라이", "pos": "동사", "ko": "(비료 등을) 사용하다, 적용하다"},
        {"en": "artificial fertilizer", "pron": "아티피셜 퍼틸라이저", "pos": "명사", "ko": "인공 비료 (artificial 인공의)"},
        {"en": "introduce", "pron": "인트러듀스", "pos": "동사", "ko": "들여놓다, 도입하다; 소개하다"},
        {"en": "around", "pron": "어라운드", "pos": "전치사", "ko": "~ 주위에, 둘레에"},
    ],
    "vocab_tip": _TIP,
    "grammar": [
        {"level": "core", "tag": "오늘의 핵심", "title": "동명사 : 동사+ing = \"~하는 것 / ~함\" (명사 역할)",
         "rule": "동사에 <b>-ing</b> 를 붙이면 명사처럼 쓰여요. 특히 <b>전치사(by, at, about, after …) 뒤</b>에는 동사를 <b>반드시 ~ing</b> 로 바꿔 써요.",
         "examples": [
             {"en": "<span class='hl'>by digging</span> tunnels", "ko": "굴을 <b>팜으로써</b> (by ~ing: ~함으로써)"},
             {"en": "excellent <span class='hl'>at breaking down</span> organic matter", "ko": "유기물을 <b>분해하는 것에</b> 탁월한"},
             {"en": "careful <span class='hl'>about applying</span> … <span class='hl'>after introducing</span> earthworms", "ko": "비료 <b>주는 것을</b> 조심하는 … 지렁이를 <b>들여놓은 뒤</b>"},
         ]},
        {"level": "", "tag": "문법 2", "title": "help + (to) 동사원형 = \"~하는 것을 돕다\"",
         "rule": "<b>help</b> 뒤에는 <b>동사원형</b>(또는 to+동사원형)이 와요. help <b>keep</b>, help <b>raise</b> 처럼요.",
         "examples": [
             {"en": "They <span class='hl'>help keep</span> your soil soft", "ko": "그들은 흙을 부드럽게 <b>유지하는 것을 돕는다</b>"},
         ]},
        {"level": "", "tag": "문법 3", "title": "make A 비교급 = \"A를 더 ~하게 만들다\"",
         "rule": "make 뒤에 &lsquo;A + 형용사&rsquo; 가 오면 <b>&ldquo;A를 ~하게 만들다&rdquo;</b>. 형용사가 비교급이면 &lsquo;더 ~하게&rsquo;.",
         "examples": [
             {"en": "their waste <span class='hl'>makes your soil richer</span>", "ko": "그들의 배설물은 <b>흙을 더 비옥하게 만든다</b>"},
         ]},
        {"level": "up", "tag": "한 단계 위", "title": "분사구문 (복습) : recycling ~, helping ~",
         "rule": "문장 뒤의 <b>동사+ing</b> 덩어리는 &lsquo;~하면서&rsquo;. 관계대명사 that 도 여러 번 복습해요.",
         "examples": [
             {"en": "eat the dead bits …, <span class='hl'>recycling</span> them and <span class='hl'>helping</span> new plants to grow", "ko": "죽은 부분을 먹는다, 그것들을 <b>재순환시키면서</b> 새 식물이 자라도록 <b>도우면서</b>"},
         ]},
    ],
    "literal": [
        {"no": 7, "en": "Earthworms are a great addition / to your garden / as well.",
         "ko": "지렁이는 훌륭한 보탬이다 / 네 정원에 / 또한."},
        {"no": 8, "en": "They help keep your soil soft and breathable / by digging tunnels / that bring air to the roots of plants.",
         "ko": "그들은 흙을 부드럽고 통기성 있게 유지하도록 돕는다 / 굴을 팜으로써 / 식물의 뿌리에 공기를 가져다주는."},
        {"no": 9, "en": "They also eat the dead bits of plants / that fall to the ground, / recycling them back into the soil / and helping new plants to grow.",
         "ko": "그들은 또한 식물의 죽은 부분을 먹는다 / 땅에 떨어진, / 그것들을 흙으로 다시 재순환시키면서 / 그리고 새 식물이 자라도록 도우면서."},
        {"no": 10, "en": "Moreover, / their waste makes your soil richer, / and they are excellent / at breaking down organic matter / in your garden.",
         "ko": "게다가, / 그들의 배설물은 흙을 더 비옥하게 만든다, / 그리고 그들은 탁월하다 / 유기물을 분해하는 것에 / 네 정원에서."},
        {"no": 11, "en": "However, / you should be careful / about applying artificial fertilizers / to your garden / after introducing earthworms.",
         "ko": "그러나, / 너는 조심해야 한다 / 인공 비료를 사용하는 것을 / 정원에 / 지렁이를 들여놓은 뒤에는."},
        {"no": 12, "en": "They will find a new home / when the soil around them changes.",
         "ko": "그들은 새로운 서식지를 찾을 것이다 / 그들 주변의 흙이 바뀌면."},
    ],
    "quiz_html": """
    <div class="q-block">
      <div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>
      <table class="q"><tbody>
        <tr><td class="q-num">1</td><td class="q-word">earthworm</td><td class="q-blank"></td><td class="q-num">2</td><td class="q-word">soil</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">3</td><td class="q-word">dig</td><td class="q-blank"></td><td class="q-num">4</td><td class="q-word">root</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">5</td><td class="q-word">recycle</td><td class="q-blank"></td><td class="q-num">6</td><td class="q-word">waste</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">7</td><td class="q-word">break down</td><td class="q-blank"></td><td class="q-num">8</td><td class="q-word">apply</td><td class="q-blank"></td></tr>
        <tr><td class="q-num">9</td><td class="q-word">introduce</td><td class="q-blank"></td><td class="q-num">10</td><td class="q-word">around</td><td class="q-blank"></td></tr>
      </tbody></table>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">B</span>우리말을 보고 알맞은 영어 단어 쓰기 (위 단어표에서)</div>
      <div class="q-line"><span class="kr">1) 흙/토양</span> → <span class="q-fill"></span> &nbsp; <span class="kr">2) 뿌리</span> → <span class="q-fill"></span> &nbsp; <span class="kr">3) 게다가</span> → <span class="q-fill"></span></div>
      <div class="q-line"><span class="kr">4) 유기물</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">5) 인공 비료</span> → <span class="q-fill lg"></span> &nbsp; <span class="kr">6) 파다</span> → <span class="q-fill"></span></div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">C</span>동명사 고르기 — 전치사 뒤에는 ~ing! (오늘의 핵심 문법)</div>
      <div class="q-line">1) They help keep your soil soft by ( dig / digging ) tunnels.</div>
      <div class="q-line">2) They are excellent at ( break / breaking ) down organic matter.</div>
      <div class="q-line">3) Be careful about ( apply / applying ) fertilizers after ( introduce / introducing ) earthworms.</div>
    </div>
    <div class="q-block">
      <div class="q-h"><span class="q-badge">D</span>다음 문장을 우리말로 해석하기</div>
      <div class="q-line">1) Their waste makes your soil richer.<span class="q-write"></span></div>
      <div class="q-line">2) They will find a new home when the soil around them changes.<span class="q-write"></span></div>
    </div>
    """,
    "answer_html": """
    <div class="ans-block"><b>A.</b> 1 지렁이 &nbsp; 2 흙/토양 &nbsp; 3 파다 &nbsp; 4 뿌리 &nbsp; 5 재순환시키다/재활용하다 &nbsp; 6 배설물/노폐물 &nbsp; 7 분해하다 &nbsp; 8 (비료를) 사용하다/적용하다 &nbsp; 9 들여놓다/도입하다 &nbsp; 10 ~ 주위에</div>
    <div class="ans-block"><b>B.</b> 1 soil &nbsp; 2 root &nbsp; 3 moreover &nbsp; 4 organic matter &nbsp; 5 artificial fertilizer &nbsp; 6 dig</div>
    <div class="ans-block"><b>C.</b> 1 digging &nbsp; 2 breaking &nbsp; 3 applying, introducing &nbsp;— 전치사(by/at/about/after) 뒤에는 반드시 ~ing!</div>
    <div class="ans-block"><b>D.</b> 1 그들의 배설물은 흙을 더 비옥하게 만든다. &nbsp; 2 그들 주변의 흙이 바뀌면, 그들은 새로운 서식지를 찾을 것이다.</div>
    """,
}


DAYS = [DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7, DAY8, DAY9]
