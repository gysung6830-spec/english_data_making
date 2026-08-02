# -*- coding: utf-8 -*-
"""
2과(Lesson 2) 콘텐츠 — '중등 기초 브릿지' (은아쌤 손글씨판).
지문 출처: 2022 개정 천재(강상구) 공통영어2 · Lesson 2 (장애인을 위한 발명 / 자율주행차)
대상: 영어를 매우 어려워하는 고1. 1과에서 배운 문법을 이어받아 확장.
구조는 content_lesson1.py 와 동일 (generate.py가 두 과를 함께 처리).
"""

SOURCE = "2022 개정 천재(강상구) 공통영어2 · Lesson 2 · 고1 2학기 내신 대비"
COPYRIGHT = "ⓒ2026.김은아영어연구소.All rights reserved"
TEACHER = "은아쌤"

DAYS = [
    # ===== 11일차 (3주차 월) 본문 1-6 =====
    dict(day=11, week=3, weekday="월", title_en="3D Braille Map ①", title_ko="장애, 그리고 두 발명가",
        part="본문 · 문장 1–6", goal_title="to부정사 : to + 동사원형 = ‘~하기 위해 / ~하는 것’",
        gnote="<b>to + 동사원형</b> = ‘~하기 위해’(목적), ‘~하는 것’.",
        open="2과 시작! 이번엔 장애가 있는 사람들을 돕는 멋진 발명 이야기야. 흥미로울 거야.",
        passage_explain=(
            "전 세계 인구의 약 <b>15%</b>(적어도 10억 명)가 어떤 형태의 <b>장애</b>를 겪어. 이들도 다른 사람처럼 "
            "장소·물건·서비스에 <b>접근</b>할 수 있어야 하는데, 많은 사람에게 접근은 여전히 <b>문제</b>야. "
            "이 문제를 풀려고 국제 과학 대회에 <b>발명품</b>을 들고 나온 두 십 대가 있어. 그중 Seoyoung Jun은 "
            "숙제를 하다가, 한쪽 눈을 감고도 연필꽂이를 문제없이 집는 걸 보고 ‘어? 3차원 공간 인식에 두 눈이 다 필요하진 않네?’ 하고 깨달았어."),
        tf=[("전 세계 인구의 약 15%가 어떤 형태의 장애를 겪는다.", True),
            ("Seoyoung은 두 눈을 다 떠야만 물건을 집을 수 있었다.", False),
            ("두 청소년은 국제 과학 대회에서 발명품을 선보였다.", True)],
        words=[("disability","장애"),("population","인구"),("experience","겪다, 경험하다"),
               ("access","접근(하다)"),("remain","남아 있다"),("issue","문제, 사안"),
               ("invention","발명품"),("tackle","해결하다, 씨름하다"),("competition","경연, 대회"),
               ("realize","깨닫다, 알아차리다")],
        grammar=dict(
            terms=[("to부정사","to + 동사원형. ‘~하기 위해 / ~하는 것 / ~할’ 등으로 쓰여."),
                   ("동사원형","동사의 기본 모습. to 뒤엔 항상 원형!")],
            intro=("‘to + 동사원형’을 <b>to부정사</b>라고 해. 가장 많이 쓰는 뜻은 <b>‘~하기 위해’</b>(목적)야. "
                   "예: ‘I study <b>to pass</b>.(합격하기 위해 공부한다)’. 또 ‘~하는 것’(I want <b>to eat</b> 먹는 것을 원한다)으로도 쓰여. "
                   "중요한 건, to 뒤엔 무조건 동사 <b>원형</b>이 온다는 거!"),
            easy=[("I study hard to pass the exam.","시험에 합격하기 위해 열심히 공부해."),
                  ("She wants to help people.","그녀는 사람들을 돕고 싶어 해."),
                  ("He came to see you.","그는 너를 보러 왔어.")],
            examples=["...inventions **to tackle** the issue  (그 문제를 해결하기 위한 발명품)",
                      "In order **to function**, they need access.  (활동하기 위해서)"],
            ask="‘to tackle’ 은 ‘무엇을 위해’인지 나타내지? 뜻이 뭘까?",
            answer="‘~하기 위해’ (해결하기 위해)",
            rule="<b>to + 동사원형</b> = to부정사. 대표 뜻은 ‘~하기 위해’(목적)와 ‘~하는 것’."),
        practice=[("I exercise ( to / for ) stay healthy.","to"),
                  ("They need water ( drink / to drink ).","to drink"),
                  ("She went out ( buy / to buy ) milk.","to buy"),
                  ("‘to tackle’ = 해결( 하기 위해 / 했다 )","하기 위해")],
        memorize=[
            ("For many of them, access still remains an issue.",
             "For many of them, / access still remains an issue.",
             "그들 중 다수에게, / 접근은 여전히 문제로 남아 있다."),
            ("They need to have the same access as everyone else.",
             "They need to have the same access / as everyone else.",
             "그들은 같은 접근권을 가질 필요가 있다 / 다른 모두와 똑같이."),
            ("Here are two teenagers who presented new inventions.",
             "Here are two teenagers / who presented new inventions.",
             "여기 두 청소년이 있다 / 새 발명품을 선보인."),
            ("She realized that she didn't need both eyes.",
             "She realized / that she didn't need both eyes.",
             "그녀는 깨달았다 / 두 눈이 다 필요하진 않다는 것을.")],
        close="첫날부터 잘했어! to부정사, ‘~하기 위해’ 이 뜻만 잡아도 오늘은 성공이야."),

    # ===== 12일차 (화) 본문 7-12 =====
    dict(day=12, week=3, weekday="화", title_en="3D Braille Map ②", title_ko="아이디어의 탄생",
        part="본문 · 문장 7–12", goal_title="명사절 that : ‘~라는 것을’",
        gnote="동사 뒤 <b>that + 주어 + 동사</b> = ‘~라는 것을’ (목적어 덩어리).",
        open="어제 Seoyoung의 발견, 오늘은 그게 어떻게 발명 아이디어로 이어졌는지 볼 거야!",
        passage_explain=(
            "Seoyoung은 조사를 통해 ‘뇌는 <b>시각</b>이 전혀 없어도 3차원 정보를 <b>처리</b>할 수 있다’는 걸 알게 됐어. "
            "여기서 시각 <b>장애</b>가 있는 사람들을 위한 새 <b>장치</b> 아이디어가 탄생했지. 시각을 잃은 사람들은 주로 "
            "<b>촉각</b>으로 공간 정보를 얻거든. 그래서 그녀의 길 안내 장치는 이 사실에 기반을 뒀어. 이 작은 장치는 "
            "<b>적외선</b>을 쏘아 벽·가구 같은 주변 물체의 3차원 정보를 모으고, 반사된 빛이 장치에 정보를 전해 핀을 올려."),
        tf=[("뇌는 시각이 전혀 없어도 3차원 정보를 처리할 수 있다.", True),
            ("시각을 잃은 사람들은 주로 시각으로 공간 정보를 얻는다.", False),
            ("이 장치는 적외선으로 주변 정보를 모은다.", True)],
        words=[("research","조사, 연구"),("process","처리하다"),("device","장치, 기기"),
               ("vision","시각, 시력"),("sight","시력, 시각"),("spatial","공간의"),
               ("touch","촉각, 만지다"),("navigation","길 안내"),("gather","모으다, 수집하다"),
               ("furniture","가구")],
        grammar=dict(
            terms=[("명사절","문장 속에서 명사(목적어·주어) 역할을 하는 ‘문장 덩어리’."),
                   ("접속사 that","‘~라는 것’이라는 뜻으로 문장을 이어 줌.")],
            intro=("‘~라는 것을 안다/생각한다’처럼, 동사(know, learn, think 등) 뒤에 <b>‘that + 주어 + 동사’</b>가 오면 "
                   "‘<b>~라는 것을</b>’로 해석해. 이 that 덩어리 전체가 목적어(명사) 역할을 하는 거야. "
                   "이 that은 관계대명사(명사 꾸미기)랑 달라 — ‘~라는 것’ 통째로 이어 주는 접속사야. 생략되기도 해."),
            easy=[("I know that you are honest.","나는 네가 정직하다는 것을 안다."),
                  ("She thinks that it is true.","그녀는 그것이 사실이라고 생각한다."),
                  ("I heard that he left.","그가 떠났다는 걸 들었어.")],
            examples=["She learned **that the brain can process 3D information**.  (뇌가 3D 정보를 처리할 수 있다는 것을)",
                      "She realized **that it didn't require both eyes**."],
            ask="‘learned that ~’ 에서 that 뒤 내용은 무슨 뜻으로 이어질까?",
            answer="‘~라는 것을’ (배웠다)",
            rule="동사 뒤 <b>that + 주어 + 동사</b> = ‘~라는 것을’. 이 덩어리가 통째로 목적어야."),
        practice=[("I know ( that / what ) she is kind.","that"),
                  ("‘that the brain can process’ = 뇌가 처리할 수 있다는 ( 것 / 곳 )","것"),
                  ("He said ( that / to ) he was tired.","that"),
                  ("She believes that it ( is / being ) possible.","is")],
        memorize=[
            ("She learned that the brain can process 3D information.",
             "She learned / that the brain can process 3D information.",
             "그녀는 알게 되었다 / 뇌가 3D 정보를 처리할 수 있다는 것을."),
            ("The idea for a new device was born.",
             "The idea for a new device / was born.",
             "새 장치에 대한 아이디어가 / 생겨났다."),
            ("Those who have lost sight get information from touch.",
             "Those who have lost sight / get information from touch.",
             "시각을 잃은 사람들은 / 촉각으로부터 정보를 얻는다."),
            ("She based her device on this fact.",
             "She based her device / on this fact.",
             "그녀는 장치의 근거를 두었다 / 이 사실에.")],
        close="‘that ~라는 것을’ 이거 하나 챙겼으면 오늘 충분해. 내일 또 보자!"),

    # ===== 13일차 (수) 본문 13-18 =====
    dict(day=13, week=3, weekday="수", title_en="3D Braille Map ③", title_ko="장치는 어떻게 작동할까",
        part="본문 · 문장 13–18", goal_title="접속사 when : ‘~할 때 / ~하면’",
        gnote="<b>when + 주어 + 동사</b> = ‘~할 때 / ~하면’. 두 문장을 시간으로 이어 줌.",
        open="오늘은 장치가 실제로 어떻게 작동하는지! 조금 기술적이지만 쌤이 쉽게 풀어줄게.",
        passage_explain=(
            "사용자는 올라온 핀들의 <b>위치</b>와 <b>높낮이</b>를 손으로 ‘읽어서’ 앞에 있는 <b>구조물</b>·물체의 배치를 파악하고 "
            "비켜 갈 수 있어. 장치의 핵심은 작은 컴퓨터에 연결된 3차원 <b>심도 감지기</b>야. Seoyoung은 아홉 개의 모터(3×3)를 "
            "<b>조종</b>하도록 프로그램을 짰고, 각 모터가 핀 하나를 위아래로 움직여. 감지기는 앞 공간 18칸을 <b>훑고</b>, "
            "장애물을 <b>감지</b>하면 그 높이에 따라 핀이 중간이나 위로 올라와."),
        tf=[("반사된 적외선이 정보를 장치에 전달하면 핀이 올라온다.", True),
            ("사용자는 핀의 위치와 높낮이를 읽어 장애물을 파악한다.", True),
            ("이 장치의 핵심은 큰 텔레비전 화면이다.", False)],
        words=[("convey","전달하다"),("indicate","나타내다"),("obstacle","장애물"),
               ("position","위치"),("height","높이"),("structure","구조물, 구조"),
               ("depth","깊이, 심도"),("sensor","감지기, 센서"),("control","조종하다"),
               ("scan","훑다, 살피다")],
        grammar=dict(
            terms=[("접속사","두 문장을 이어 주는 말. (when, because, if …)"),
                   ("부사절","‘언제/왜/만약’ 등을 나타내며 문장을 꾸미는 덩어리.")],
            intro=("<b>when</b>은 ‘~할 때 / ~하면’이라는 뜻으로 두 문장을 이어 줘. "
                   "‘<b>When</b> it rains, I stay home.(비가 오면, 집에 있어)’처럼. "
                   "when 덩어리(when + 주어 + 동사)는 문장 앞에 올 수도 있고 뒤에 올 수도 있어. 앞에 오면 뒤에 콤마(,)를 찍어."),
            easy=[("When I was young, I liked candy.","어렸을 때, 나는 사탕을 좋아했어."),
                  ("Call me when you arrive.","도착하면(도착할 때) 전화해."),
                  ("When it gets dark, turn on the light.","어두워지면, 불을 켜.")],
            examples=["**When it detects an obstacle**, the pin rises.  (장애물을 감지하면)",
                      "**When you run the app**, gestures are captured."],
            ask="‘When it detects an obstacle’ 은 ‘언제’를 나타내지? 뜻이 뭘까?",
            answer="‘~할 때 / ~하면’ (장애물을 감지하면)",
            rule="<b>when + 주어 + 동사</b> = ‘~할 때 / ~하면’. 시간·상황을 이어 줘."),
        practice=[("( When / What ) I woke up, it was noon.","When"),
                  ("‘when it detects’ = 그것이 감지( 할 때 / 하지 않을 때 )","할 때"),
                  ("I was happy when she ( come / came ).","came"),
                  ("( When / Who ) you are ready, tell me.","When")],
        memorize=[
            ("The bounced beam conveys that information to the device.",
             "The bounced beam / conveys that information / to the device.",
             "반사된 적외선이 / 그 정보를 전달한다 / 장치에."),
            ("The device raises little pins to indicate obstacles.",
             "The device raises little pins / to indicate obstacles.",
             "장치는 작은 핀들을 올린다 / 장애물을 나타내기 위해."),
            ("The heart of this device is a 3D depth sensor.",
             "The heart of this device / is a 3D depth sensor.",
             "이 장치의 핵심은 / 3D 심도 감지기이다."),
            ("The sensor can scan eighteen blocks of space.",
             "The sensor can scan / eighteen blocks of space.",
             "감지기는 훑을 수 있다 / 18개의 공간 블록을.")],
        close="when ‘~할 때’ 완벽! 오늘 단어(장치 관련)는 시험에도 잘 나와. 꼭 챙기자."),

    # ===== 14일차 (목) 본문 19-23 =====
    dict(day=14, week=3, weekday="목", title_en="3D Braille Map ④", title_ko="마침내 성공",
        part="본문 · 문장 19–23", goal_title="관계대명사 that / which — 명사를 뒤에서 꾸미기 (복습)",
        gnote="명사 + <b>that/which + 동사</b> = ‘~하는 (명사)’. 사람이면 who.",
        open="드디어 장치가 작동하는 순간! Seoyoung의 기쁨을 함께 느껴보자. 감동이야.",
        passage_explain=(
            "장치가 <b>처음</b> 작동했을 때, Seoyoung은 믿기지 않았어. 실수가 아닌지 확인하려고 껐다가 다시 켰지. "
            "그런데 또 작동하자, 그녀는 기쁜 나머지 <b>소리를 질렀어</b>! 이 성공까지 연구·제작·<b>시험</b>에 무려 7개월이 걸렸대. "
            "그녀는 이제 스마트폰에 연결되고, 핀과 높이 단계가 더 많은 <b>미래 버전</b>을 꿈꾸고 있어."),
        tf=[("장치가 처음 작동했을 때 Seoyoung은 바로 믿었다.", False),
            ("연구·제작·시험에 7개월이 걸렸다.", True),
            ("그녀는 스마트폰에 연결되는 미래 버전을 상상한다.", True)],
        words=[("work","작동하다"),("believe","믿다"),("mistake","실수"),
               ("shut off","끄다"),("reboot","다시 가동하다"),("scream","소리 지르다"),
               ("joy","기쁨"),("imagine","상상하다"),("version","버전, 판"),("connect","연결하다")],
        grammar=dict(
            terms=[("관계대명사","명사 뒤에서 그 명사를 꾸며 주는 연결고리 (that/which/who)."),
                   ("선행사","꾸밈을 받는 앞의 명사.")],
            intro=("2일차(1과)에 배운 관계대명사 기억나? 명사 뒤에 that/which가 오면 ‘~하는 (명사)’로 묶어 읽는 거! "
                   "오늘 문장에서 다시 확인하자. ‘a future version <b>that could be connected to a smartphone</b>’ = "
                   "‘스마트폰에 연결될 수 있는 미래 버전’. that 뒤가 앞 명사(version)를 꾸며 주지? 사람을 꾸미면 who를 써."),
            easy=[("a book that is interesting","재미있는 책"),
                  ("the man who called me","나에게 전화한 남자"),
                  ("a car which runs fast","빨리 달리는 차")],
            examples=["a future version **that could be connected to a smartphone**  (연결될 수 있는 미래 버전)",
                      "two teenagers **who presented new inventions**  (발명품을 선보인 청소년들)"],
            ask="that 뒤 내용은 앞의 명사(version)를 꾸며 주지? 뜻이 뭘까?",
            answer="‘연결될 수 있는 (버전)’",
            rule="명사 + <b>that/which + 동사</b> = ‘~하는 (명사)’. 사람이면 who."),
        practice=[("a version ( that / who ) works well","that"),
                  ("the boy ( who / which ) helped me","who"),
                  ("‘version that could be connected’ = 연결될 수 있는 ( 버전 / 사람 )","버전"),
                  ("a device ( which / what ) is small","which")],
        memorize=[
            ("When Seoyoung's device worked, she didn't believe it.",
             "When Seoyoung's device worked, / she didn't believe it.",
             "Seoyoung의 장치가 작동했을 때, / 그녀는 믿지 못했다."),
            ("When it worked again, she started screaming with joy.",
             "When it worked again, / she started screaming with joy.",
             "그것이 다시 작동하자, / 그녀는 기뻐서 소리 지르기 시작했다."),
            ("It had been seven long months of research.",
             "It had been / seven long months of research.",
             "7개월이라는 긴 시간이 걸렸다 / 연구에."),
            ("She imagines a future version connected to a smartphone.",
             "She imagines a future version / connected to a smartphone.",
             "그녀는 미래 버전을 상상한다 / 스마트폰에 연결된.")],
        close="Seoyoung 이야기 끝! 포기하지 않으면 이런 결과가 나오는구나. 우리도 화이팅!"),

    # ===== 15일차 (금) 본문 24-29 =====
    dict(day=15, week=3, weekday="금", title_en="Sign Language App ①", title_ko="수어 번역 앱의 시작",
        part="본문 · 문장 24–29", goal_title="의문사 + to부정사 : how to ~ = ‘~하는 방법’",
        gnote="<b>how to + 동사원형</b> = ‘~하는 방법 / 어떻게 ~할지’.",
        open="한 주 마지막 날! 이번엔 또 다른 발명가 Nand의 수어 번역 앱 이야기야. 대단해!",
        passage_explain=(
            "프로그래머 Nand Vinchhi는 기계 장치가 필요 없는 걸 <b>발명</b>하고 싶었어. 어느 날 친구들과 이야기하다 "
            "‘수어를 <b>번역</b>하는 앱’ 아이디어를 떠올렸지. 다들 개발을 접었지만 Nand는 계속 생각했고, 단 몇 달 만에 "
            "미국식 수어(ASL)를 실시간으로 번역하는 <b>인공지능</b> 앱을 만들었어. 손동작이 말에 해당하는 앱이었지. "
            "가장 어려웠던 건, 앱이 <b>손동작</b>을 <b>인식</b>하게 만드는 방법을 찾는 것이었어."),
        tf=[("Nand는 기계 장치가 필요 없는 것을 발명하고 싶어 했다.", True),
            ("그는 며칠 만에 수어 번역 앱을 완전히 포기했다.", False),
            ("가장 어려운 부분은 손동작을 인식하게 만드는 방법이었다.", True)],
        words=[("invent","발명하다"),("require","필요로 하다"),("mechanical","기계의"),
               ("come up with","떠올리다"),("translate","번역하다"),("develop","개발하다"),
               ("artificial intelligence","인공지능"),("figure out","알아내다"),
               ("recognize","인식하다"),("gesture","손동작, 제스처")],
        grammar=dict(
            terms=[("의문사","how(어떻게), what(무엇), where(어디) 등 묻는 말."),
                   ("to부정사","to + 동사원형 (11일차 복습).")],
            intro=("‘<b>how to + 동사원형</b>’은 ‘<b>~하는 방법 / 어떻게 ~할지</b>’라는 뜻이야. "
                   "‘I know <b>how to swim</b>.(수영하는 법을 안다)’처럼. how 말고 <b>what to</b>(무엇을 ~할지), "
                   "<b>where to</b>(어디서 ~할지)도 같은 방식이야. 뒤엔 항상 동사원형!"),
            easy=[("I know how to ride a bike.","나는 자전거 타는 법을 알아."),
                  ("Tell me what to do.","무엇을 할지 말해줘."),
                  ("She learned how to cook.","그녀는 요리하는 법을 배웠어.")],
            examples=["figuring out **how to make the app recognize gestures**  (앱이 손동작을 인식하게 만드는 방법)"],
            ask="‘how to make ~’ 는 무슨 뜻일까?",
            answer="‘~하는 방법 / 어떻게 ~할지’ (만드는 방법)",
            rule="<b>how to + 동사원형</b> = ‘~하는 방법’. what to, where to도 같은 짝."),
        practice=[("I don't know how ( use / to use ) it.","to use"),
                  ("Tell me ( what / how ) to do next.","what"),
                  ("She learned how ( cook / to cook ).","to cook"),
                  ("‘how to make’ = 만드는 ( 방법 / 사람 )","방법")],
        memorize=[
            ("Nand wanted to invent something without a device.",
             "Nand wanted to invent something / without a device.",
             "Nand는 무언가를 발명하고 싶었다 / 장치 없이."),
            ("They came up with an idea for an app.",
             "They came up with an idea / for an app.",
             "그들은 아이디어를 떠올렸다 / 앱에 대한."),
            ("He developed an app based on artificial intelligence.",
             "He developed an app / based on artificial intelligence.",
             "그는 앱을 개발했다 / 인공지능에 기반한."),
            ("The hardest part was making the app recognize gestures.",
             "The hardest part was / making the app recognize gestures.",
             "가장 어려운 부분은 / 앱이 손동작을 인식하게 만드는 것이었다.")],
        close="한 주 수고했어! 주말에 3주차 단어 테스트로 가볍게 점검하자. 😊"),

    # ===== 16일차 (4주차 월) 본문 30-35 =====
    dict(day=16, week=4, weekday="월", title_en="Sign Language App ②", title_ko="앱을 완성하기까지",
        part="본문 · 문장 30–35", goal_title="수동태 : be동사 + 과거분사(p.p.) (복습)",
        gnote="<b>be동사 + 과거분사</b> = ‘~되다 / ~당하다’. 주어가 당하는 쪽.",
        open="새 한 주! Nand가 어려움을 어떻게 넘겼는지 볼 거야. 잠자기가 비결이었대. 신기하지?",
        passage_explain=(
            "막혀서 <b>꼼짝 못할</b> 때, Nand는 잠을 자며 생각하곤 했는데 그 방법이 통했어. 그는 손가락 끝처럼 수어에 "
            "중요한 <b>신체 부위</b>에 <b>초점</b>을 맞추기로 했지. 기계학습으로 자기가 찍은 영상 속 주요 지점을 앱이 "
            "<b>식별</b>하도록 학습시켰어. 사용자가 앱을 실행하면 카메라가 동작을 <b>포착</b>하고, 앱은 알고리즘으로 "
            "그 동작에 맞는 수어 단어를 찾아 문자로 바꾼 뒤 소리 내어 말해줘."),
        tf=[("막힐 때 Nand는 잠을 자며 생각했고, 그 방법이 효과가 있었다.", True),
            ("그는 손가락 끝 같은 주요 지점에 초점을 맞췄다.", True),
            ("앱은 동작을 문자로 바꾸지 않고 그대로 둔다.", False)],
        words=[("stuck","꼼짝 못하는, 막힌"),("pay off","효과가 있다, 성과를 내다"),("focus on","~에 집중하다"),
               ("fingertip","손가락 끝"),("identify","식별하다"),("capture","포착하다"),
               ("algorithm","알고리즘"),("match","맞추다, 일치시키다"),("turn into","~로 바뀌다"),
               ("aloud","소리 내어")],
        grammar=dict(
            terms=[("수동태","be동사 + 과거분사 = ‘~되다/당하다’ (1과 5일차 복습)."),
                   ("과거분사(p.p.)","동사의 세 번째 모습. capture-captured-captured (규칙동사).")],
            intro=("1과 5일차에 배운 <b>수동태</b>가 또 나와! ‘be동사 + 과거분사 = ~되다/당하다’. "
                   "여기선 손동작이 카메라에 ‘포착<b>된다</b>(당한다)’처럼 쓰여. "
                   "‘gestures <b>are captured</b> by the camera’ — 손동작은 잡는 게 아니라 잡히는(당하는) 쪽이지? "
                   "‘by ~’를 붙이면 ‘누구/무엇에 의해’인지 알려줘."),
            easy=[("The song is loved by everyone.","그 노래는 모두에게 사랑받는다."),
                  ("The email was sent.","이메일이 보내졌다."),
                  ("Rice is grown in Korea.","쌀은 한국에서 재배된다.")],
            examples=["gestures **are captured** by the camera  (동작이 카메라에 포착된다)",
                      "...which **are turned into** text  (문자로 바뀐다)"],
            ask="‘are captured’ 는 손동작이 ‘하는’ 쪽이야 ‘당하는’ 쪽이야?",
            answer="당하는 쪽! (포착된다)",
            rule="<b>be + 과거분사</b> = 수동태 ‘~되다/당하다’. by ~는 ‘~에 의해’."),
        practice=[("Gestures ( capture / are captured ) by the camera.","are captured"),
                  ("The words ( turn / are turned ) into text.","are turned"),
                  ("수동태 = be동사 + ( 원형 / 과거분사 )","과거분사"),
                  ("This app ( uses / is used ) by many people.","is used")],
        memorize=[
            ("When he was stuck, he would go to sleep.",
             "When he was stuck, / he would go to sleep.",
             "막혔을 때, / 그는 잠을 자곤 했다."),
            ("For Nand, sleeping on it paid off.",
             "For Nand, / sleeping on it paid off.",
             "Nand에게, / 하룻밤 자며 생각하는 게 효과가 있었다."),
            ("He decided to focus on the fingertips.",
             "He decided to focus / on the fingertips.",
             "그는 집중하기로 했다 / 손가락 끝에."),
            ("Gestures are captured by the camera.",
             "Gestures are captured / by the camera.",
             "동작이 포착된다 / 카메라에 의해.")],
        close="수동태 복습 완료! ‘be + 과거분사 = 당하다’ 이거 이제 자동으로 나오지?"),

    # ===== 17일차 (화) 본문 36-40 =====
    dict(day=17, week=4, weekday="화", title_en="Sign Language App ③", title_ko="정확도와 꿈",
        part="본문 · 문장 36–40", goal_title="관계대명사 what : ‘~하는 것’",
        gnote="<b>what</b> = ‘~하는 것’. 앞에 꾸밈 받는 명사가 없으면 that/which가 아니라 what!",
        open="Nand 이야기 마무리! 그의 앱이 얼마나 정확한지, 어떤 꿈을 꾸는지 보자.",
        passage_explain=(
            "Nand에 따르면 그의 시스템은 지금 <b>90.4% 정확도</b>로 수어를 번역하고, 수어에서 번역까지 <b>지연</b>은 "
            "약 0.3초밖에 안 돼. 그는 이 <b>기술</b>이 언젠가 기존 의사소통 플랫폼의 일부가 되길 꿈꿔. 그러면 수어 사용자가 "
            "수어를 모르는 사람과도 대화할 수 있겠지. 이 두 발명품의 <b>공통점</b>은, 장애가 있는 사람들의 일상을 "
            "높이려고 기술을 <b>창의적으로</b> 활용했다는 거야. 이런 노력이 모두에게 더 열린 세상을 만들 거야."),
        tf=[("시스템의 번역 정확도는 약 90.4%이다.", True),
            ("수어에서 번역까지 몇 분이 걸린다.", False),
            ("두 발명품의 공통점은 기술을 창의적으로 활용했다는 것이다.", True)],
        words=[("accuracy","정확도"),("delay","지연, 지체"),("technology","기술"),
               ("existing","기존의"),("communicate","소통하다"),("in common","공통으로, 공통점"),
               ("creative","창의적인"),("enhance","향상시키다, 높이다"),("effort","노력"),
               ("accessible","접근하기 쉬운")],
        grammar=dict(
            terms=[("관계대명사 what","‘~하는 것’이라는 뜻. 앞에 꾸밈 받는 명사가 없어!"),
                   ("선행사","보통 which/that 앞엔 명사가 있는데, what은 그게 없음.")],
            intro=("<b>what</b>은 ‘<b>~하는 것</b>’이라는 뜻의 특별한 관계대명사야. that/which와 달리 "
                   "<b>앞에 명사가 없어</b> — what 자체가 ‘~하는 것’을 이미 품고 있거든. "
                   "‘<b>What he said</b> is true.(그가 말한 것은 사실이다)’처럼. 헷갈리면 이렇게 기억해: "
                   "앞에 명사 있으면 that/which, 없으면 what!"),
            easy=[("What he said is true.","그가 말한 것은 사실이야."),
                  ("I don't understand what you mean.","네가 뜻하는 것을 모르겠어."),
                  ("This is what I want.","이게 내가 원하는 거야.")],
            examples=["**What these inventions have in common** is a creative use of technology.  (이 발명품들이 공통으로 가진 것은)"],
            ask="‘What these inventions have in common’ 은 무슨 뜻일까?",
            answer="‘이 발명품들이 공통으로 가진 것’",
            rule="<b>what</b> = ‘~하는 것’. 앞에 명사가 없으면 that/which가 아니라 what!"),
        practice=[("( What / That ) he wants is money.","What"),
                  ("This is ( what / who ) I made.","what"),
                  ("‘what they have in common’ = 그들이 공통으로 가진 ( 것 / 곳 )","것"),
                  ("Tell me ( what / when ) you need.","what")],
        memorize=[
            ("His system translates signs with 90.4% accuracy.",
             "His system translates signs / with 90.4% accuracy.",
             "그의 시스템은 수어를 번역한다 / 90.4% 정확도로."),
            ("The technology could become part of communication platforms.",
             "The technology could become / part of communication platforms.",
             "그 기술은 될 수 있다 / 의사소통 플랫폼의 일부가."),
            ("What these inventions have in common is a creative use of technology.",
             "What these inventions have in common / is a creative use of technology.",
             "이 발명품들의 공통점은 / 기술의 창의적 활용이다."),
            ("Their efforts will make the world more accessible.",
             "Their efforts will make / the world more accessible.",
             "그들의 노력은 만들 것이다 / 세상을 더 접근하기 쉽게.")],
        close="본문 완주! 관계대명사 what ‘~하는 것’, 시험 단골이야. 꼭 기억해."),

    # ===== 18일차 (수) 본문 외 1-6 =====
    dict(day=18, week=4, weekday="수", title_en="Self-driving Cars ①", title_ko="자율주행차의 장점",
        part="본문 외 · 자율주행 1–6", goal_title="관계부사 where : ‘그곳에서 ~하는’",
        gnote="장소 명사 + <b>where</b> = ‘그곳에서 ~하는’. could = ‘~할 수 있을’(부드러운 추측).",
        open="이번엔 본문 밖 지문 — 자율주행차야! 미래 자동차, 궁금하지 않아?",
        passage_explain=(
            "자동차가 이제 ‘사람으로부터의 <b>자유</b>’를 향해 가고 있어. <b>목표</b>는 사람처럼 생각하고 운전하는 "
            "인공지능 차를 만드는 것. 이 기술은 점점 더 <b>접근 가능한</b> 수준에 <b>이르렀어</b>. 자율주행차엔 분명한 "
            "<b>장점</b>이 있어. 무엇보다, 운전이 <b>더 이상</b> 나이나 <b>능력</b>의 제한을 받지 않게 돼. "
            "예를 들어 시각장애인도 자율주행차에 <b>의존해</b> 이동할 수 있지."),
        tf=[("자율주행차의 목표는 인간처럼 생각하고 운전하는 것이다.", True),
            ("자율주행차에는 분명한 장점이 있다.", True),
            ("자율주행차는 나이가 많으면 탈 수 없다.", False)],
        words=[("freedom","자유"),("goal","목표"),("reach","이르다, 도달하다"),
               ("increasingly","점점 더"),("advantage","장점, 이점"),("no longer","더 이상 ~않다"),
               ("limit","제한하다"),("ability","능력"),("rely on","~에 의존하다"),
               ("accessible","접근 가능한")],
        grammar=dict(
            terms=[("관계부사 where","‘장소’ 명사 뒤에서 ‘그곳에서 ~하는’으로 설명."),
                   ("조동사 could","‘~할 수 있을’ 같은 부드러운 가능성·추측.")],
            intro=("장소를 뜻하는 명사(place, point 등) 뒤에 <b>where</b>가 오면 ‘<b>그곳에서 ~하는</b>’이라고 설명을 붙여. "
                   "‘the point <b>where it is accessible</b>(그것이 가능해지는 지점)’. 관계대명사(which)는 뒤 문장에 "
                   "빠진 자리가 있지만, where는 ‘그곳에서’라는 완전한 자리를 채워 줘. 그리고 could는 ‘~할 수 있을’ 정도의 부드러운 추측이야."),
            easy=[("This is the place where I was born.","여기가 내가 태어난 곳이야."),
                  ("It reached a point where it works.","그것이 작동하는 지점에 이르렀어."),
                  ("A person could rely on it.","사람이 그것에 의존할 수도 있어.")],
            examples=["the point **where it is becoming accessible**  (접근 가능해지는 지점)",
                      "a person who has lost sight **could rely on** a self-driving car"],
            ask="‘the point where ~’ 에서 where 뒤는 무엇을 설명할까?",
            answer="그 ‘지점(장소)’에서 어떤 일이 일어나는지",
            rule="장소 명사 + <b>where</b> = ‘그곳에서 ~하는’. could = ‘~할 수 있을’."),
        practice=[("This is the house ( where / which ) I live.","where"),
                  ("It reached a point ( where / who ) it works.","where"),
                  ("She ( could / can ) rely on it.","could"),
                  ("the place ( where / what ) we met","where")],
        memorize=[
            ("Cars are now making steps toward their own freedom.",
             "Cars are now making steps / toward their own freedom.",
             "자동차는 이제 나아가고 있다 / 자신만의 자유를 향해."),
            ("The goal is to build a car that uses AI.",
             "The goal is to build a car / that uses AI.",
             "목표는 차를 만드는 것이다 / 인공지능을 쓰는."),
            ("Self-driving cars have clear advantages.",
             "Self-driving cars / have clear advantages.",
             "자율주행차는 / 분명한 장점이 있다."),
            ("A blind person could rely on a self-driving car.",
             "A blind person / could rely on a self-driving car.",
             "시각장애인은 / 자율주행차에 의존할 수 있을 것이다.")],
        close="where ‘그곳에서 ~하는’ 챙겼지? 내일은 자율주행차의 걱정거리를 볼 거야."),

    # ===== 19일차 (목) 본문 외 7-12 =====
    dict(day=19, week=4, weekday="목", title_en="Self-driving Cars ②", title_ko="자율주행차의 걱정",
        part="본문 외 · 자율주행 7–12", goal_title="가정법 과거 : If + 과거, 주어 would/could + 동사원형 (복습)",
        gnote="‘만약 (지금) ~라면 ~할 텐데’ — <b>사실은 반대</b>! (1과 3일차 복습)",
        open="2과 마지막 지문! 자율주행차의 밝은 면 뒤에 있는 걱정도 알아보자.",
        passage_explain=(
            "<b>게다가</b>, 대부분의 <b>사고</b>는 도로 위 <b>부주의한</b> 사람들 때문에 나. 운전 중 휴대폰, 졸음운전, "
            "음주운전 같은 것들 말이야. 자율주행차가 있다면 이런 <b>걱정</b>을 안 해도 되겠지. 하지만 기술이 아직 완벽하지 "
            "않아서 <b>안전</b>에 대한 심각한 <b>우려</b>도 있어. 자율주행차는 센서·GPS·프로그램에만 의존해서 <b>제대로</b> "
            "작동하는데, 이 중 하나라도 <b>고장 나거나</b> 나쁜 목적에 쓰이면, 탑승자와 다른 사람들의 안전·<b>보안</b>이 위험해질 수 있어."),
        tf=[("대부분의 사고는 부주의한 사람들 때문에 일어난다.", True),
            ("자율주행 기술은 이미 완벽하다.", False),
            ("센서 등이 고장 나면 안전이 위험해질 수 있다.", True)],
        words=[("furthermore","게다가"),("accident","사고"),("careless","부주의한"),
               ("crash","충돌, 사고"),("concern","우려, 걱정"),("safety","안전"),
               ("depend on","~에 의존하다"),("properly","제대로"),("break down","고장 나다"),
               ("security","보안")],
        grammar=dict(
            terms=[("가정법 과거","If + 과거동사, 주어 would/could + 동사원형 (1과 3일차 복습)."),
                   ("사실의 반대","가정법은 실제와 반대인 상상!")],
            intro=("1과 3일차에 배운 <b>가정법 과거</b>가 또 나와! ‘If + 과거동사, 주어 would/could + 동사원형’ = "
                   "‘만약 (지금) ~라면 ~할 텐데’. 실제론 반대라는 뜻이야. 자율주행 지문 마지막이 딱 이 형태야: "
                   "‘If any of these <b>broke down</b>, safety <b>could be put</b> at risk.(고장 난다면, 안전이 위험에 처할 수도)’ "
                   "— broke는 과거형이지만 ‘실제로 고장 난 건 아니고, 만약 그렇다면’이라는 상상이야."),
            easy=[("If I had a car, I would drive.","차가 있다면 운전할 텐데. (실제론 없음)"),
                  ("If it were cheaper, I could buy it.","더 싸다면 살 수 있을 텐데."),
                  ("If I knew, I would tell you.","안다면 말해줄 텐데. (실제론 모름)")],
            examples=["If any of these **broke down**, safety **could be put** at risk.  (고장 난다면, 위험해질 수도)"],
            ask="broke/could 는 과거형인데, 실제로 지금 고장 났을까?",
            answer="아니, 상상! ‘만약 고장 난다면’ (사실은 아직 아님)",
            rule="<b>If + 과거, 주어 would/could + 원형</b> = 가정법 과거. 사실은 반대!"),
        practice=[("If I ( had / have ) time, I would help.","had"),
                  ("If it broke, safety ( could / can ) be at risk.","could"),
                  ("If I ( am / were ) rich, I would travel.","were"),
                  ("가정법은 사실과 ( 같은 / 반대 )","반대")],
        memorize=[
            ("Most accidents are caused by careless people.",
             "Most accidents are caused / by careless people.",
             "대부분의 사고는 일어난다 / 부주의한 사람들 때문에."),
            ("People would not need to worry about such situations.",
             "People would not need / to worry about such situations.",
             "사람들은 필요 없을 것이다 / 그런 상황을 걱정할."),
            ("The technology is still far from perfect.",
             "The technology is still / far from perfect.",
             "그 기술은 아직 / 완벽과는 거리가 멀다."),
            ("A self-driving car depends only on its sensors and GPS.",
             "A self-driving car depends only / on its sensors and GPS.",
             "자율주행차는 오직 의존한다 / 센서와 GPS에.")],
        close="2과 완주 축하해! 🎉 내일은 2과 전체를 총복습하며 마무리하자."),
]

GRAMMAR_SUMMARY = [
    ("11일차", "to부정사", "to + 동사원형 = ‘~하기 위해/~하는 것’"),
    ("12일차", "명사절 that", "‘~라는 것을’ (동사 뒤 목적어)"),
    ("13일차", "접속사 when", "‘~할 때 / ~하면’"),
    ("14일차", "관계대명사 that/which", "명사 뒤에서 ‘~하는 (명사)’"),
    ("15일차", "how to", "‘~하는 방법’ (의문사+to부정사)"),
    ("16일차", "수동태 be+p.p.", "‘~되다/당하다’"),
    ("17일차", "관계대명사 what", "‘~하는 것’ (앞에 명사 없음)"),
    ("18일차", "관계부사 where", "‘그곳에서 ~하는’ (장소)"),
    ("19일차", "가정법 과거", "‘만약 ~라면 ~할 텐데’ (사실의 반대)"),
]

# ── 직독직해: 각 날짜 지문 전체 문장 (영어, 우리말) ──
SENTENCES = {
 11: [
  ("At least one billion people, or 15% of the world's population, experience some form of disability.","적어도 10억 명, 즉 전 세계 인구의 15%는 어떠한 형태의 장애를 겪고 있다."),
  ("In order to fully function in everyday life, they need to have the same physical and social access to the places, goods, and services in their communities as everyone else.","그들이 일상에서 온전히 활동하려면, 다른 모두와 동일하게 공동체 내의 장소, 재화 및 서비스에 물리적으로나 사회적으로 접근할 수 있어야 한다."),
  ("For many of them, however, access still remains an issue.","그러나 그들 중 다수에게 접근은 여전히 문제로 남아 있다."),
  ("Here are two teenagers who presented new inventions to tackle the issue at an international science competition.","국제 과학 경연 대회에 이 문제를 해결하기 위한 새 발명품을 내놓은 두 십 대 청소년이 여기에 있다."),
  ("While thinking about her homework, Seoyoung Jun closed one eye and successfully picked up her pencil holder.","숙제를 생각하다가 Seoyoung Jun은 한쪽 눈을 감은 채로 문제없이 연필꽂이를 집어 들었다."),
  ("At that moment, she realized that orienting herself in a 3D space didn't require both eyes. This surprised her.","그 순간 그녀는 3차원 공간에서 자기 위치를 인식하는 데에 양쪽 눈이 필요하지는 않음을 알았다. 그녀에게는 이것이 놀라웠다."),
 ],
 12: [
  ("With research, she learned that the brain can process 3D information without any vision at all.","조사를 통해 그녀는 뇌가 시각이 전혀 없더라도 3차원 정보를 처리할 수 있다는 것을 알게 되었다."),
  ("And with that, the idea for a new device for people with visual disabilities was born.","이렇게 시각 장애를 가진 사람들을 위한 새로운 장치에 대한 아이디어가 탄생했다."),
  ("Those who have lost sight get their spatial information mainly from touch, not vision.","시각을 잃은 사람들은 시각이 아니라 주로 촉각으로부터 공간에 대한 정보를 얻는다."),
  ("She based her new navigation device on this fact.","그녀의 새로운 길 안내 장치는 이 사실에 기반을 두었다."),
  ("This little device sends a beam of infrared light to gather 3D information about what may lie around the user, including walls and furniture.","이 작은 장치는 적외선광을 보내서 벽과 가구를 포함하여 사용자 주위에 놓여 있을 수 있는 것들에 관한 3차원 정보를 수집한다."),
  ("The bounced beam conveys that information to the device, which then raises little pins to indicate where those obstacles are.","반사된 적외선이 그 정보를 장치에 전송하는데, 그러면 그 장치는 장애물이 있는 곳을 나타내도록 작은 핀들을 올린다."),
 ],
 13: [
  ("By \"reading\" the positions and heights of those pins, the user can understand the arrangement of structures and objects lying ahead and navigate around them.","그 핀들의 위치와 높낮이를 '읽음'으로써, 사용자는 앞에 놓인 구조물과 물체들의 배치를 파악하고 그것들을 비켜갈 수 있다."),
  ("The heart of this device is a 3D depth sensor connected to a small computer.","이 장치의 핵심은 작은 컴퓨터에 연결된 3차원 심도 감지기이다."),
  ("Seoyoung coded the computer to control the nine motors lined up in three rows of three so that each motor could move a pin up and down.","Seoyoung은 컴퓨터가 세 개씩 세 줄로 배열된 아홉 개의 모터를 조종해서 각 모터가 하나의 핀을 위아래로 움직일 수 있도록 프로그램을 짰다."),
  ("The sensor can scan eighteen blocks of space before it, each 0.06㎥ in size.","감지기는 그 앞에 있는 0.06㎥ 크기의 상자 모양의 공간 열여덟 개를 훑을 수 있다."),
  ("When it detects an obstacle in any of these blocks, the corresponding pin rises to either the middle or high position, depending on the height of the obstacle.","그것이 이 상자들 중 어느 것에서라도 장애물을 감지하면, 그 장애물의 높이에 따라 해당 핀이 중간 또는 상부 위치로 올라간다."),
  ("By running your hand over the nine pins, you can tell where the obstacles are and how high they are.","아홉 개의 핀 위에 손을 대서, 장애물이 어디에 있고 높이는 어느 정도인지를 알 수 있게 된다."),
 ],
 14: [
  ("When Seoyoung's device worked for the first time, she didn't believe it.","최초로 Seoyoung의 장치가 작동했을 때 그녀는 믿기지 않았다."),
  ("To be sure it wasn't a mistake, she shut it off and rebooted it.","잘못된 게 아니라는 걸 확인하기 위해 그녀는 그것을 끄고 다시 가동했다."),
  ("When it worked again, she started screaming with joy.","그것이 다시 작동하자 그녀는 기쁜 나머지 소리를 질렀다."),
  ("It had been seven long months of research, building, and testing.","7개월이라는 긴 시간이 연구와 제작, 그리고 시험에 소요되었다."),
  ("She imagines a future version that could be connected to a smartphone, with more pins and more height positions.","그녀는 스마트폰에 연결될 수 있고, 더 많은 핀과 높이 단계가 있는 앞으로의 버전을 그리고 있다."),
 ],
 15: [
  ("As a coder, Nand Vinchhi wanted to invent something that didn't require a mechanical device.","컴퓨터 프로그래머로서 Nand Vinchhi는 기계 장치를 필요로 하지 않는 무언가를 발명하고 싶었다."),
  ("One day, he was brainstorming with friends, and the group came up with an idea for an app that could translate sign language.","어느 날, 그는 친구들과 자유롭게 생각을 나누고 있었고, 그들은 수어를 번역하는 앱에 대한 아이디어를 떠올렸다."),
  ("In the end, they decided not to develop it, but Nand couldn't stop thinking about the translator.","결국 그들은 그것을 개발하지 않기로 했지만, Nand는 번역 앱에 대한 생각을 떨칠 수가 없었다."),
  ("In just a few months, he developed an app based on artificial intelligence for translating American Sign Language (ASL) in real time.","단 몇 달 만에 그는 미국식 수어를 실시간으로 번역하는 인공 지능 기반의 앱을 개발했다."),
  ("Nand's app was basically a speech-to-text app for sign language, where hand movements corresponded to speech.","Nand의 앱은 기본적으로 수어 대상의 말-문자 변환 앱이었고, 여기에서는 손동작이 말에 해당했다."),
  ("The hardest part was figuring out how to make the app recognize hand gestures.","가장 어려운 부분은 앱이 손동작을 인식하게 만드는 방법을 찾는 것이었다."),
 ],
 16: [
  ("At times, he felt he was stuck. When that happened, he would go to sleep.","때로는 꼼짝도 못하는 느낌이 들었다. 그럴 때면, 그는 잠을 자곤 했다."),
  ("For Nand, sleeping on it paid off.","Nand에게 하룻밤을 자며 생각하는 방법은 효과가 있었다."),
  ("He decided to focus on the body parts which are important in signing, such as individual fingertips.","그는 각각의 손가락 끝과 같이 수어를 쓸 때 중요한 신체 부위에 초점을 맞추기로 했다."),
  ("Using a machine-learning program, he then taught the app to identify those key points in the videos he took.","그런 다음 그는 기계학습 프로그램을 이용해서 그가 찍은 영상 속에서 그 주요 지점들을 앱이 식별하도록 학습시켰다."),
  ("When the user runs the app, gestures are captured by the camera.","사용자가 앱을 실행하면 카메라는 동작을 포착한다."),
  ("Then, the app uses an algorithm to match the movements with words in ASL, which are turned into text and then spoken aloud.","그러면 앱은 알고리즘을 통해 동작에 맞는 미국식 수어의 어휘를 찾고, 이것이 문자로 변환된 뒤 발화된다."),
 ],
 17: [
  ("According to Nand, his system now translates signs with 90.4% accuracy, and the delay from signing to translation is only about three-tenths of a second.","Nand에 의하면, 그의 시스템은 현재 90.4%의 정확도로 수어를 번역하고, 수어에서 번역까지 지연되는 시간은 약 0.3초에 불과하다."),
  ("He imagines the technology could someday become part of existing communication platforms.","그는 이 기술이 언젠가 현재 사용되는 의사소통 플랫폼의 일부가 될 것을 꿈꾼다."),
  ("That could help ASL speakers communicate with those who don't know the language.","그것은 미국식 수어를 사용하는 사람들이 그 수어를 모르는 이들과 대화하는 데 도움이 될 것이다."),
  ("What these inventions have in common is a creative use of technology to enhance the daily lives of people with disabilities.","이 발명품들의 공통점은 장애를 가진 사람들의 일상의 질을 높이기 위해 기술을 창조적으로 활용했다는 것이다."),
  ("Their efforts will go a long way toward a more accessible world for all.","그들의 노력은 모든 이들에게 보다 접근이 용이한 세상이 되는 데에 큰 도움이 될 것이다."),
 ],
 18: [
  ("Cars are now making steps toward their own kind of freedom; that is, freedom from people.","자동차는 이제 자신만의 자유를 향해 나아가고 있다, 즉, 사람들로부터의 자유이다."),
  ("The goal is to build a car that uses artificial intelligence so that it thinks and drives like a human.","목표는 인간처럼 생각하고 운전할 수 있도록 인공 지능을 사용하는 자동차를 만드는 것이다."),
  ("The technology for a self-driving car has reached the point where it is becoming increasingly accessible.","자율 주행 자동차 기술은 점점 더 접근 가능한 수준에 이르렀다."),
  ("Self-driving cars have clear advantages.","자율 주행 자동차에는 분명한 장점이 있다."),
  ("Most of all, sitting behind the wheel would no longer be limited by age or ability.","무엇보다, 운전대에 앉는 것이 더 이상 나이나 능력의 제한을 받지 않을 것이다."),
  ("For example, a person who has lost sight could rely on a self-driving car to go from one place to another.","예를 들어, 시각 장애인은 자율 주행 자동차를 이용해 한 장소에서 다른 장소로 이동할 수 있다."),
 ],
 19: [
  ("Furthermore, most accidents are caused by careless people on the road.","게다가, 대부분의 사고는 도로에서 부주의한 사람들에 의해 발생한다."),
  ("For example, many crashes are caused by people using their phones while driving, falling asleep at the wheel, or driving while drunk.","예를 들어, 많은 충돌은 운전 중에 휴대 전화를 사용하거나, 운전대를 잡고 졸거나, 음주 상태에서 운전을 하는 사람들로 인해 발생한다."),
  ("With a self-driving car, people would not need to worry about such situations on the road.","자율 주행 자동차가 있다면 사람들은 도로 위에서 그런 상황을 걱정할 필요가 없을 것이다."),
  ("However, there are also some serious concerns when it comes to the safety of self-driving cars, since the technology is still far from perfect.","하지만 기술이 아직 완벽하지 않기 때문에, 자율 주행 자동차의 안전성을 놓고 보면 심각한 우려 역시 존재한다."),
  ("In fact, a self-driving car depends only on its sensors, GPS, and computer programs to work properly.","실제로, 자율 주행 자동차는 제대로 작동하기 위해 센서, GPS, 컴퓨터 프로그램에만 의존한다."),
  ("If any of these broke down or were used for unintended purposes, then the safety and security of the rider as well as other people on the road could be put at risk.","이들 중 어느 것이라도 고장이 나거나 의도하지 않은 목적으로 사용된다면, 탑승자는 물론 도로에 있는 다른 사람들의 안전과 보안이 위험에 처할 수 있다."),
 ],
}
for _d in DAYS:
    _d["sentences"] = SENTENCES[_d["day"]]
