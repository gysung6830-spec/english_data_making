# -*- coding: utf-8 -*-
"""
1과(Lesson 1) 콘텐츠 — '중등 기초 브릿지' (은아쌤 손글씨판 v2).
대상: 영어를 매우 어려워하는 고1. '과거분사'가 뭔지도 모르는 수준.
지문 출처: 2022 개정 천재(강상구) 공통영어2 · Lesson 1

v2 반영(학생 피드백):
  · 문법을 기초 용어부터 아주 친절하게 + 쉬운 일상 예시
  · 전체 지문 설명 확대 + 지문 내용 T/F(한글) 문제
  · 하루 문장 4개로 늘림 + 영작 순서 넘버링
  · 단어는 소리 내며 '영어+한글 뜻' 함께 쓰기
"""

SOURCE = "2022 개정 천재(강상구) 공통영어2 · Lesson 1 · 고1 2학기 내신 대비"
COPYRIGHT = "ⓒ2026.김은아영어연구소.All rights reserved"
TEACHER = "은아쌤"

DAYS = [
    # ============================ 1일차 ============================
    dict(day=1, week=1, weekday="월", title_en="The Nuisance ①", title_ko="모기가 문다",
        part="PART 1 · 문장 1–9", goal_title="be동사(am·are·is) + 일반동사 3인칭 -s",
        gnote="주어가 하나(he·she·it)면 동사에 <b>-s</b>. You/여럿이면 그냥 원형.",
        open="자, 오늘부터 모기 이야기 시작이야. 하나도 안 어려워. 쌤이랑 아주 천천히 갈 거니까 걱정 마!",
        passage_explain=(
            "여름에 가족·친구랑 캠핑을 갔다고 해보자. 하루 종일 놀고 샤워하고 의자에 앉아 음료수를 마시며 "
            "‘아~ 좋다’ 하는 순간, ‘윙~’ 하는 짜증나는 소리가 들려. 바로 <b>모기</b>야. 모기는 1초에 날개를 600번이나 "
            "치면서 몰래 다가와, 빨대 같은 주둥이로 우리 <b>피부</b>를 찔러 <b>피</b>를 빨아. 그러곤 재빨리 도망치는데, "
            "가렵고 빨간 자국을 남기지. 이 가려움은 모기의 <b>침</b>에 대한 우리 몸의 반응이야. 긁을수록 더 가려워져. "
            "그럼 모기는 우리를 어떻게 찾아낼까? 바로 우리가 내쉬는 이산화탄소가 모기에게 ‘먹이가 가까이 있다’는 신호가 돼."),
        tf=[("모기는 주둥이로 피부를 찔러 피를 빤다.", True),
            ("모기에 물린 자리가 가려운 건 모기의 침에 대한 몸의 반응 때문이다.", True),
            ("물린 곳은 긁을수록 가려움이 줄어든다.", False)],
        words=[("mosquito","모기"),("skin","피부"),("blood","피, 혈액"),("itchy","가려운"),
               ("escape","달아나다, 탈출하다"),("annoying","짜증나는, 성가신"),("victim","먹잇감, 희생자"),
               ("signal","신호"),("pierce","뚫다, 찌르다"),("near","가까운")],
        grammar=dict(
            terms=[("주어","문장에서 ‘누가 / 무엇이’에 해당하는 말. (I, You, He, A mosquito …)"),
                   ("be동사","am·are·is 세 가지. 뜻은 ‘~이다 / ~에 있다’."),
                   ("일반동사","be동사 말고 움직임·행동을 나타내는 동사. (eat 먹다, run 달리다, pierce 찌르다 …)")],
            intro=("우리말은 ‘나는·너는·그는’ 뒤에 똑같이 ‘~이다’를 쓰지? 그런데 영어는 <b>주어에 따라 be동사 모양이 바뀌어</b>. "
                   "I → am, You·We·They → are, He·She·It(하나) → is. 이건 규칙이라 그냥 외우는 거야. "
                   "그리고 eat 같은 <b>일반동사</b>는, 주어가 ‘하나(he·she·it)’일 때만 동사 꽁무니에 <b>-s</b>를 붙여. "
                   "‘그가 달린다’는 He run이 아니라 He run<b>s</b> 처럼!"),
            easy=[("I am happy.","나는 행복해. (I → am)"),
                  ("You are my friend.","너는 내 친구야. (You → are)"),
                  ("She is a teacher.","그녀는 선생님이야. (She → is)"),
                  ("He runs fast.","그는 빨리 달려. (주어 He라서 run에 -s!)")],
            examples=["A mosquito **sneaks** in.  (주어 a mosquito = 하나 → -s)",
                      "It **fills** its belly with blood.  (주어 it = 하나 → -s)"],
            ask="주어가 하나(a mosquito, it)일 때, 동사 뒤에 붙은 글자가 뭐야?",
            answer="-s (sneak→sneaks, fill→fills)",
            rule="주어가 ‘하나(he·she·it)’면 동사에 <b>-s</b>! You·We·They(여럿)엔 안 붙여. 시험 단골 함정이야."),
        practice=[("A mosquito ( sneak / sneaks ) in.","sneaks"),
                  ("You ( am / are / is ) on a camping trip.","are"),
                  ("She ( land / lands ) on your arm.","lands"),
                  ("How ( do / does ) mosquitoes find us?","do")],
        memorize=[
            ("A mosquito sneaks in and pierces your skin.",
             "A mosquito sneaks in / and pierces your skin.",
             "모기가 몰래 들어와 / 네 피부를 찌른다."),
            ("It fills its belly with blood and then escapes.",
             "It fills its belly with blood / and then escapes.",
             "그것은 배를 피로 채우고 / 그러고는 달아난다."),
            ("This is a reaction to the mosquito's saliva.",
             "This is a reaction / to the mosquito's saliva.",
             "이것은 반응이다 / 모기의 침에 대한."),
            ("The more you scratch, the more it itches.",
             "The more you scratch, / the more it itches.",
             "긁으면 긁을수록, / 더 가렵다.")],
        close="첫날 잘했어! 오늘 단어 10개랑 문장들 입에 붙이면 대성공이야. 👍"),

    # ============================ 2일차 ============================
    dict(day=2, week=1, weekday="화", title_en="The Nuisance ②", title_ko="모기는 어떻게 찾을까",
        part="PART 1 · 문장 10–15", goal_title="관계대명사 that / which — 명사를 뒤에서 꾸미기",
        gnote="명사 뒤에 <b>that/which</b>가 오면 ‘~하는 (명사)’로 묶어 읽기.",
        open="어제 배운 모기, 오늘은 걔가 우리를 ‘어떻게 찾아내는지’ 알아볼 거야. 은근 똑똑한 녀석이야!",
        passage_explain=(
            "모기는 우리를 어떻게 귀신같이 찾을까? 첫째, 우리가 숨 쉴 때 나오는 <b>이산화탄소(CO2)</b>에 아주 민감해서 "
            "멀리서도 감지해. 둘째, 우리가 <b>땀</b>을 흘리면 특정 화학물질이 나오는데, 그 냄새가 모기를 끌어당겨. "
            "셋째, 올라간 <b>체온</b>도 알아채지. 그런데 재밌는 사실! 우리를 무는 건 <b>암컷</b> 모기뿐이야. "
            "왜냐하면 암컷은 알을 낳으려고 <b>단백질</b>(우리 피 속에 있음)이 필요하거든. 수컷은 우리를 물지 않아."),
        tf=[("모기는 이산화탄소(CO2)를 멀리서도 감지한다.", True),
            ("우리가 땀을 흘리면 모기를 ‘쫓는’ 물질이 나온다.", False),
            ("우리를 무는 것은 암컷 모기다.", True)],
        words=[("detect","감지하다, 알아차리다"),("sensitive","민감한"),("release","내보내다, 분비하다"),
               ("attract","끌어당기다, 유인하다"),("notice","알아채다"),("cue","단서, 신호"),
               ("protein","단백질"),("female","암컷, 여성"),("bite","물다, 깨물다"),("produce","생산하다, 만들어 내다")],
        grammar=dict(
            terms=[("명사","사람·사물·동물의 ‘이름’. (dog 개, chemical 화학물질, cue 단서 …)"),
                   ("관계대명사","명사 뒤에서 ‘어떤 명사인지’ 설명을 이어 붙여 주는 연결고리. (that·which·who)")],
            intro=("우리말은 ‘<b>나를 좋아하는</b> 친구’처럼 꾸미는 말이 명사 <b>앞</b>에 와. 그런데 영어는 반대로 "
                   "꾸미는 말이 명사 <b>뒤</b>에 붙어! ‘a friend <b>who likes me</b>’(나를 좋아하는 친구). "
                   "이때 명사와 설명을 이어 주는 다리가 <b>관계대명사</b>야. 사람이면 who, 사물·동물이면 that/which를 써. "
                   "‘명사 + that/which + (동사~)’를 보면 그냥 통째로 ‘~하는 (명사)’로 묶어서 읽으면 돼."),
            easy=[("the book that I like","내가 좋아하는 책"),
                  ("a boy who can swim","수영할 수 있는 소년"),
                  ("the cake which she made","그녀가 만든 케이크")],
            examples=["certain chemicals **that attract them**  (화학물질 ← 그들을 유인하는)",
                      "the only cue **[that] they use**  (단서 ← 그들이 이용하는)"],
            ask="that 바로 앞의 명사(chemicals, cue)를, that 뒤 내용이 설명해 주고 있지?",
            answer="응. that 뒤가 앞 명사를 꾸며 줌!",
            rule="사물·동물을 꾸미면 <b>that/which</b>. ‘명사+주어+동사’가 붙어 나오면 그 사이에 that이 숨어(생략) 있는 거야."),
        practice=[("certain chemicals ( that / who ) attract them","that"),
                  ("chemicals that attract them = 그들을 ( 유인하는 / 유인당하는 ) 화학물질","유인하는"),
                  ("a friend ( who / which ) helps me","who"),
                  ("the only cue ( they use / use they )","they use")],
        memorize=[
            ("They are sensitive to CO2 and can detect it.",
             "They are sensitive to CO2 / and can detect it.",
             "그들은 CO2에 민감하다 / 그리고 그것을 감지할 수 있다."),
            ("When you sweat, you release chemicals that attract them.",
             "When you sweat, / you release chemicals / that attract them.",
             "네가 땀을 흘리면, / 화학물질을 내보낸다 / 그들을 유인하는."),
            ("They can notice that your body temperature has risen.",
             "They can notice / that your body temperature has risen.",
             "그들은 알아챌 수 있다 / 네 체온이 올라간 것을."),
            ("Only females bite us; they need protein.",
             "Only females bite us; / they need protein.",
             "암컷만 우리를 문다; / 그들은 단백질이 필요하다.")],
        close="관계대명사 that, ‘~하는 명사’로 묶으면 끝! 오늘도 문장 소리 내서 읽어보자."),

    # ============================ 3일차 ============================
    dict(day=3, week=1, weekday="수", title_en="The Nuisance ③", title_ko="알을 낳기까지",
        part="PART 1 · 문장 16–20", goal_title="가정법 과거 : If + 과거, 주어 would + 동사원형",
        gnote="‘만약 (지금) ~라면 ~할 텐데’ — <b>사실은 반대</b>! 동사는 과거지만 뜻은 현재.",
        open="오늘 문법은 이름이 어려워 보여도(가정법!) 원리는 쉬워. 쌤이 예시로 딱 잡아줄게.",
        passage_explain=(
            "피를 배불리 빤 암컷 모기는 어떻게 할까? 먼저 가장 가까운 <b>수직 벽</b> 같은 곳에 내려앉아. "
            "그다음 <b>중력</b>의 도움으로 빨아들인 피에서 수분을 빼내 피를 진하게(농축) 만들어. "
            "그 진한 피로 며칠에 걸쳐 몸속에서 <b>알</b>을 키우지. 그리고 마지막에 작은 물웅덩이 <b>표면</b> 위에 "
            "약 <b>200개</b>의 알을 낳아. 물 위에 둥둥 뜨는 알들이야. 참고로 우리 피에 단백질이 없었다면 "
            "모기는 애초에 우리를 물 이유가 없었겠지."),
        tf=[("암컷 모기는 빨아들인 피에서 수분을 빼내 농축시킨다.", True),
            ("모기는 한 번에 약 200개의 알을 낳는다.", True),
            ("모기는 알을 마른 땅에 낳는다.", False)],
        words=[("contain","포함하다, 담고 있다"),("bother","귀찮게 하다"),("surface","표면, 겉면"),
               ("gravity","중력"),("land","내려앉다, 착륙하다"),("develop","발달·성숙시키다"),
               ("lay","(알을) 낳다"),("vertical","수직의"),("roughly","대략, 약"),("concentrated","농축된, 진해진")],
        grammar=dict(
            terms=[("가정법","실제와 반대되는 일을 ‘상상해서’ 말하는 방법."),
                   ("동사원형","동사의 기본 모습. is→be, goes→go, would 뒤에 오는 그 모습.")],
            intro=("‘내가 <b>새라면</b> 하늘을 날 텐데.’ — 근데 나는 새가 아니지? 이렇게 <b>사실과 반대인 상상</b>을 "
                   "말할 때 쓰는 게 가정법이야. 영어에선 If절 동사를 일부러 <b>과거형</b>으로 써. "
                   "‘과거형인데 왜 지금 얘기냐?’ 싶지? 바로 그게 ‘사실은 아니야, 상상이야’라는 신호거든. "
                   "그리고 뒤쪽(주절)에는 ‘<b>would + 동사원형</b>’을 써서 ‘~할 텐데’를 나타내."),
            easy=[("If I were a bird, I would fly.","내가 새라면, 날 텐데. (실제로 새 아님)"),
                  ("If I had money, I would buy it.","돈이 있다면, 살 텐데. (실제로 돈 없음)")],
            examples=["If our blood **did not contain** protein, they **would not** bother us.",
                      "→ did/would는 과거형이지만, 지금 얘기! 실제론 반대(피에 단백질이 있음)."],
            ask="실제로 우리 피에 단백질이 있을까, 없을까? (문장은 ‘없다면’이라고 상상 중)",
            answer="실제론 ‘있어’! 그래서 모기가 무는 거야.",
            rule="<b>If + 과거동사, 주어 would + 동사원형</b> = ‘만약 (지금) ~라면 ~할 텐데’. 사실은 그 반대라는 뜻!"),
        practice=[("If our blood ( did not / does not ) contain protein,","did not"),
                  ("they ( will / would ) not bother us.","would"),
                  ("If I ( am / were ) you, I would study.","were"),
                  ("실제로 피에 단백질이 ( 있다 / 없다 )","있다")],
        memorize=[
            ("If our blood did not contain protein, they would not bother us.",
             "If our blood did not contain protein, / they would not bother us.",
             "우리 피에 단백질이 없다면, / 그들은 우리를 안 괴롭힐 텐데."),
            ("She quickly lands on the nearest vertical surface.",
             "She quickly lands / on the nearest vertical surface.",
             "그녀는 재빨리 내려앉는다 / 가장 가까운 수직 표면에."),
            ("With the aid of gravity, she drains off the water.",
             "With the aid of gravity, / she drains off the water.",
             "중력의 도움으로, / 그녀는 수분을 빼낸다."),
            ("She lays roughly 200 eggs on the water.",
             "She lays / roughly 200 eggs / on the water.",
             "그녀는 낳는다 / 약 200개의 알을 / 물 위에.")],
        close="가정법, 생각보다 할 만하지? ‘사실은 반대!’ 이 한마디만 기억해."),

    # ============================ 4일차 ============================
    dict(day=4, week=1, weekday="목", title_en="The Predator ①", title_ko="가장 위험한 동물",
        part="PART 2 · 문장 21–28", goal_title="현재완료 : have / has + 과거분사(p.p.)",
        gnote="<b>have/has + 과거분사</b> = 지금까지 ~해 왔다 / ~한 적 있다.",
        open="오늘은 과거분사(p.p.)라는 걸 처음 배워. 겁먹지 마, 쌤이 완전 바닥부터 설명할게!",
        passage_explain=(
            "퀴즈! 자연에서 가장 위험한 동물은? 상어? 사자? 곰? 정답은 놀랍게도 <b>모기</b>야. "
            "모기는 말라리아·황열 같은 <b>치명적인 병</b>을 옮겨서, 매년 전 세계에서 100만 명이 넘는 사람이 "
            "이 병으로 죽어. 한 역사학 교수(Winegard)에 따르면, 역사를 통틀어 모기가 죽인 사람은 "
            "다른 어떤 원인보다 많은 <b>약 520억 명</b> — 지금까지 살았던 인류의 거의 절반이래. "
            "게다가 모기는 여러 나라의 <b>역사</b>까지 바꿨다고 해. 예를 들면 로마 제국처럼 말이야."),
        tf=[("자연에서 가장 많은 사람을 죽인 동물은 상어다.", False),
            ("모기는 말라리아 같은 치명적인 병을 옮긴다.", True),
            ("모기는 여러 나라의 역사에도 영향을 미쳤다.", True)],
        words=[("predator","포식자, 천적"),("disease","질병, 병"),("deadly","치명적인"),
               ("estimate","추정하다"),("empire","제국"),("fall","몰락, 붕괴"),("claim","주장하다"),
               ("invasion","침략, 침입"),("corruption","부패, 타락"),("nearly","거의")],
        grammar=dict(
            terms=[("과거분사(p.p.)","동사의 ‘세 번째 모습’. 동사는 보통 현재-과거-과거분사 3단 변화를 해. "
                    "예) eat-ate-<b>eaten</b>, go-went-<b>gone</b>. 규칙동사는 과거·과거분사가 똑같이 -ed (kill-killed-killed)."),
                   ("현재완료","have/has + 과거분사")],
            intro=("먼저 <b>과거분사</b>부터! 동사는 보통 모습이 세 개야. eat(먹다)은 eat-ate-<b>eaten</b> "
                   "이렇게 변하는데, 이 세 번째 <b>eaten</b>이 과거분사(줄여서 p.p.)야. kill처럼 규칙적인 동사는 "
                   "그냥 killed로 과거랑 똑같고. 자, <b>현재완료</b>는 ‘have/has + 과거분사’인데, "
                   "‘과거에 일어난 일이 지금까지 쭉 이어진다’는 느낌이야. 그냥 과거 ate는 ‘먹었다(끝)’, "
                   "현재완료 have eaten은 ‘(지금까지) 먹어 왔다 / 먹어 본 적 있다’ 라는 뉘앙스지."),
            easy=[("I have finished my homework.","나는 숙제를 (막) 끝냈어."),
                  ("She has lived here for 5 years.","그녀는 5년째 여기 살아왔어."),
                  ("동사 3단 변화 예","eat-ate-eaten / go-went-gone / kill-killed-killed")],
            examples=["Mosquitoes **have killed** more people ...  (지금까지 죽여 왔다)",
                      "all humans who **have** ever lived  (지금까지 살아 본)"],
            ask="have + killed(죽인)는 옛날에 한 번 하고 끝난 일일까, 지금까지 이어진 일일까?",
            answer="지금까지 쭉 이어져 온 일!",
            rule="<b>have/has + 과거분사(p.p.)</b> = 지금까지 이어진 일. 주어가 여럿이면 have, 하나면 has."),
        practice=[("Mosquitoes ( have / has ) killed many people.","have"),
                  ("She ( have / has ) finished it.","has"),
                  ("all humans who ( have / has ) ever lived","have"),
                  ("‘have killed’ = 지금까지 ( 죽여 왔다 / 죽일 것이다 )","죽여 왔다")],
        memorize=[
            ("The greatest predator in nature is the mosquito.",
             "The greatest predator in nature / is the mosquito.",
             "자연에서 가장 강력한 포식자는 / 모기이다."),
            ("Mosquitoes can pass on deadly diseases like malaria.",
             "Mosquitoes can pass on / deadly diseases / like malaria.",
             "모기는 옮길 수 있다 / 치명적인 병을 / 말라리아 같은."),
            ("Over a million people die of these diseases every year.",
             "Over a million people / die of these diseases / every year.",
             "백만 명이 넘는 사람이 / 이 병들로 죽는다 / 매년."),
            ("Mosquitoes have killed more people than any other cause.",
             "Mosquitoes have killed more people / than any other cause.",
             "모기는 더 많은 사람을 죽여 왔다 / 다른 어떤 원인보다도.")],
        close="과거분사, 오늘 처음인데 잘 따라왔어! 3단 변화(eat-ate-eaten)만 기억해도 반은 성공."),

    # ============================ 5일차 ============================
    dict(day=5, week=1, weekday="금", title_en="The Predator ②", title_ko="로마 제국과 모기",
        part="PART 2 · 문장 29–34", goal_title="수동태 : be동사 + 과거분사(p.p.)",
        gnote="<b>be동사 + 과거분사</b> = ‘~되다 / ~당하다’. 주어가 당하는 쪽.",
        open="한 주 마지막 날! 어제 배운 과거분사(p.p.)를 오늘 또 써먹을 거야. 금요일 파이팅!",
        passage_explain=(
            "제국의 <b>수도</b> 로마는 한때 거대한 <b>습지</b>에 둘러싸여 있었어. 습지는 물이 고여 있어서 "
            "모기가 알 낳기에 딱 좋은 곳 — 즉 <b>이상적인 번식지</b>이자 말라리아 창궐지였지. 재밌는 건, "
            "처음엔 이 모기(병)가 로마를 공격하러 온 적군을 병들게 해서 도시를 지켜주기도 했다는 거야. "
            "하지만 시간이 지나자 모기는 병을 도시뿐 아니라 <b>제국 전체</b>에 퍼뜨려서 수많은 사람을 죽였어. "
            "결국 모기는 로마 역사를 바꾼 셈이지."),
        tf=[("로마는 한때 거대한 습지에 둘러싸여 있었다.", True),
            ("습지는 모기가 살기에 나쁜 곳이었다.", False),
            ("모기는 결국 병을 제국 전체에 퍼뜨렸다.", True)],
        words=[("capital","수도; 자본"),("surround","둘러싸다"),("wetland","습지"),("ideal","이상적인"),
               ("eventually","결국, 마침내"),("spread","퍼뜨리다, 퍼지다"),("population","인구, 개체 수"),
               ("contribute","기여하다, 한몫하다"),("powerful","강력한"),("attack","공격하다")],
        grammar=dict(
            terms=[("능동태 / 수동태","‘내가 한다’는 능동, ‘내가 당한다’는 수동."),
                   ("과거분사(p.p.) 복습","eat-ate-<b>eaten</b>의 그 세 번째 모습! 수동태에도 이게 들어가.")],
            intro=("어제 과거분사(p.p.) 배웠지? (eat-ate-<b>eaten</b>의 eaten!) 오늘은 그걸로 <b>수동태</b>를 만들어. "
                   "수동태는 ‘<b>be동사 + 과거분사</b>’인데, 주어가 직접 하는 게 아니라 <b>당하는</b> 걸 나타내. "
                   "예를 들어 ‘I eat the cake(내가 케이크를 먹는다)’는 능동, ‘The cake <b>is eaten</b>(케이크가 먹힌다)’은 수동. "
                   "케이크는 먹는 게 아니라 먹히는(당하는) 쪽이잖아? 뒤에 ‘by ~’를 붙이면 ‘누구에 의해’인지도 알려줘."),
            easy=[("The window was broken.","창문이 깨졌다. (창문은 당한 쪽)"),
                  ("This book is loved by many people.","이 책은 많은 사람에게 사랑받는다."),
                  ("The room is cleaned every day.","그 방은 매일 청소된다.")],
            examples=["Rome **was surrounded** by a huge wetland.",
                      "→ 로마가 둘러싼 게 아니라, 습지에 ‘둘러싸인’ 것(당한 쪽)!"],
            ask="was + surrounded를 보면, 로마는 ‘하는 쪽’이야 ‘당하는 쪽’이야?",
            answer="당하는 쪽! (둘러싸였다)",
            rule="<b>be동사 + 과거분사</b> = 수동태 ‘~되다/당하다’. ‘by ~’는 ‘~에 의해’."),
        practice=[("Rome ( surrounded / was surrounded ) by a huge wetland.","was surrounded"),
                  ("The window ( broke / was broken ) by the ball.","was broken"),
                  ("주어 Rome은 습지를 ( 둘러쌌다 / 둘러싸였다 )","둘러싸였다"),
                  ("수동태 = be동사 + ( 동사원형 / 과거분사 )","과거분사")],
        memorize=[
            ("Rome was once surrounded by a huge wetland.",
             "Rome was once surrounded / by a huge wetland.",
             "로마는 한때 둘러싸여 있었다 / 거대한 습지로."),
            ("This was an ideal breeding ground for mosquitoes.",
             "This was an ideal breeding ground / for mosquitoes.",
             "이곳은 이상적인 번식지였다 / 모기에게."),
            ("Mosquitoes helped protect the city against the armies.",
             "Mosquitoes helped protect the city / against the armies.",
             "모기는 도시를 지키는 걸 도왔다 / 군대로부터."),
            ("They eventually spread the disease throughout the empire.",
             "They eventually spread the disease / throughout the empire.",
             "그들은 결국 병을 퍼뜨렸다 / 제국 전체에.")],
        close="한 주 동안 정말 수고했어! 주말에 단어 테스트로 가볍게 확인해보자. 😊"),

    # ============================ 6일차 ============================
    dict(day=6, week=2, weekday="월", title_en="The Predator ③", title_ko="스코틀랜드의 실패",
        part="PART 2 · 문장 35–40", goal_title="과거완료 : had + 과거분사(p.p.)",
        gnote="<b>had + 과거분사</b> = 과거보다 ‘더 이전’의 과거. 주어 상관없이 had.",
        open="새 한 주 시작! 오늘은 모기 때문에 나라 하나가 휘청한 실제 이야기야. 흥미진진해.",
        passage_explain=(
            "1698년, 스코틀랜드는 배 다섯 척에 <b>정착민</b> 1,200명과 값진 물자를 싣고 파나마의 다리엔 <b>지역</b>으로 떠났어. "
            "식량난에 시달리던 나라의 경제를 살리려는 <b>야심 찬 계획</b>이었지. 그런데 문제가 있었어. "
            "그곳엔 황열·말라리아 같은 병이 있었는데, 스코틀랜드 사람들은 그런 병을 <b>겪어본 적이 한 번도 없었어</b>. "
            "면역이 전혀 없었던 거지. 결국 6개월 만에 절반 가까이가 죽고, 살아남은 <b>생존자</b>들은 배로 도망쳤어. "
            "계획은 완전히 무너졌지."),
        tf=[("스코틀랜드는 파나마에 교역 거점을 세우려 했다.", True),
            ("정착민들은 현지 병에 이미 익숙했다.", False),
            ("6개월 만에 절반 가까이가 죽었다.", True)],
        words=[("settler","정착민"),("valuable","값진, 귀중한"),("region","지역, 지방"),
               ("ambitious","야심 찬, 원대한"),("encounter","맞닥뜨리다, 접하다"),("survivor","생존자"),
               ("flee","달아나다, 도망치다"),("virtually","사실상, 거의"),("raise","높이다, 끌어올리다"),
               ("create","만들다, 창조하다")],
        grammar=dict(
            terms=[("과거완료","had + 과거분사"),
                   ("과거분사(p.p.) 복습","현재완료(have+p.p.), 수동태(be+p.p.)에 이어 또 나와! 세 번째 모습이야.")],
            intro=("현재완료가 ‘have/has + 과거분사’였지? <b>과거완료</b>는 ‘<b>had + 과거분사</b>’야. "
                   "이건 ‘<b>과거보다 더 이전의 과거</b>’를 나타내. 이야기의 기준이 되는 과거 시점이 있고, "
                   "그보다 더 전에 일어난 일에 had + p.p.를 써. 예를 들어 ‘내가 도착했을 때(과거), "
                   "버스는 <b>이미 떠나 있었다</b>(더 이전)’ → the bus <b>had</b> already <b>left</b>. "
                   "좋은 소식! 주어가 뭐든 항상 <b>had</b> 하나만 쓰면 돼서 오히려 쉬워."),
            easy=[("When I arrived, the train had already left.","내가 도착했을 때, 기차는 이미 떠나 있었다."),
                  ("She had never seen snow before.","그녀는 그전에 눈을 본 적이 없었다.")],
            examples=["nearly half of them **died** (과거)",
                      "No one **had ever encountered** these diseases **before**. (그보다 더 이전)"],
            ask="‘병을 만난 적 없던 것’은 ‘죽은 것(과거)’보다 더 이전 일이야, 더 나중 일이야?",
            answer="더 이전! (과거보다 앞선 과거)",
            rule="<b>had + 과거분사</b> = 과거보다 앞선 과거. 주어 상관없이 언제나 had!"),
        practice=[("No one ( has / had ) ever encountered these diseases before.","had"),
                  ("When we got there, the show ( has / had ) already started.","had"),
                  ("‘had + p.p.’ 는 과거보다 ( 더 이전 / 더 나중 )의 일","더 이전"),
                  ("The plan ( was / were ) brought down by diseases.","was")],
        memorize=[
            ("In 1698, five ships set sail from Scotland.",
             "In 1698, / five ships set sail / from Scotland.",
             "1698년에, / 배 다섯 척이 출항했다 / 스코틀랜드에서."),
            ("They headed for the Darien region of Panama.",
             "They headed for / the Darien region / of Panama.",
             "그들은 향했다 / 다리엔 지역으로 / 파나마의."),
            ("No one had ever encountered these diseases before.",
             "No one had ever encountered / these diseases / before.",
             "아무도 접해본 적 없었다 / 이런 병들을 / 이전에."),
            ("Nearly half of them died, and the survivors fled.",
             "Nearly half of them died, / and the survivors fled.",
             "그들 중 거의 절반이 죽었고, / 생존자들은 달아났다.")],
        close="과거완료도 ‘과거보다 더 과거’ 이거 하나면 끝! 잘 따라오고 있어."),

    # ============================ 7일차 ============================
    dict(day=7, week=2, weekday="화", title_en="The Predator ④", title_ko="뒤늦게 밝혀진 진실",
        part="PART 2 · 문장 41–45", goal_title="가정법 과거완료 : If + had p.p., 주어 would have p.p.",
        gnote="‘(과거에) ~했더라면 ~했을 텐데’ — 지나간 일에 대한 후회, 사실은 반대!",
        open="3일차 가정법의 ‘과거 버전’이야. 이름만 길지 원리는 똑같아. 천천히 가보자.",
        passage_explain=(
            "만약 그 사람들의 <b>면역력</b>이 훨씬 강했더라면, 그렇게 짧은 시간에 많이 죽진 않았을 거야. "
            "놀랍게도 인류는 수천 년 동안 이 병으로 죽어가면서도 ‘이게 어떻게 퍼지는지’ 전혀 몰랐어. "
            "<b>19세기 말</b>이 되어서야 비로소 ‘모기가 말라리아를 옮긴다’는 사실을 <b>알아냈지</b>. "
            "그 전엔 이 작은 <b>곤충</b>이 우리 삶에 이렇게 큰 영향을 줄 거라고 아무도 상상 못 했어. "
            "이제 우리는 알아 — 인간의 역사도 자연의 작용에서 자유롭지 못하다는 걸."),
        tf=[("인류는 오랫동안 병이 어떻게 퍼지는지 몰랐다.", True),
            ("모기가 말라리아를 옮긴다는 사실은 19세기 말에 밝혀졌다.", True),
            ("인간의 역사는 자연과 아무런 상관이 없다.", False)],
        words=[("immune system","면역 체계"),("lose","잃다"),("surprisingly","놀랍게도"),
               ("find out","알아내다, 알게 되다"),("imagine","상상하다"),("tiny","아주 작은"),
               ("insect","곤충, 벌레"),("affect","영향을 주다"),("deeply","깊이, 깊게"),("finding","발견, 밝혀진 사실")],
        grammar=dict(
            terms=[("가정법 과거완료","If + had 과거분사, 주어 would have 과거분사"),
                   ("과거분사(p.p.) 또!","여기서도 had p.p., would have p.p. 처럼 과거분사가 두 번이나 나와.")],
            intro=("3일차에 배운 가정법 기억나? ‘내가 새라면 날 텐데’(지금 상상). 오늘은 그 <b>과거 버전</b>이야. "
                   "‘(그때) 내가 <b>공부했더라면</b> 시험에 <b>붙었을 텐데</b>’ — 이미 지나간 일에 대한 후회지. "
                   "형태는 ‘<b>If + had + 과거분사, 주어 would have + 과거분사</b>’. 과거분사(p.p.)가 또 나오지? "
                   "요 며칠 계속 본 거야. 역시 ‘사실은 반대’ — 실제론 공부 안 해서 떨어졌다는 뜻이야."),
            easy=[("If I had studied, I would have passed.","공부했더라면 붙었을 텐데. (실제론 안 함)"),
                  ("If she had left earlier, she would have caught the bus.","더 일찍 나섰더라면 버스를 탔을 텐데.")],
            examples=["If their immune systems **had been** stronger,",
                      "they **would not have lost** so many lives.  (실제론 약해서 많이 죽음)"],
            ask="‘더 강했더라면’ — 실제로 그들의 면역력은 강했을까, 약했을까?",
            answer="실제론 약했어! 그래서 많이 죽은 거야.",
            rule="<b>If + had 과거분사, 주어 would have 과거분사</b> = ‘(과거에) ~했더라면 ~했을 텐데’. 지나간 일의 후회."),
        practice=[("If their immune systems ( had been / were ) stronger,","had been"),
                  ("they ( would not have lost / would not lose ) so many lives.","would not have lost"),
                  ("If I had known, I ( would have helped / would help ) you.","would have helped"),
                  ("실제로 면역력이 ( 강했다 / 약했다 )","약했다")],
        memorize=[
            ("If their immune systems had been stronger, they would not have lost so many lives.",
             "If their immune systems had been stronger, / they would not have lost so many lives.",
             "면역력이 더 강했더라면, / 그토록 많은 목숨을 잃지 않았을 텐데."),
            ("Humans lived with these diseases for thousands of years.",
             "Humans lived with these diseases / for thousands of years.",
             "인류는 이 병들과 함께 살았다 / 수천 년 동안."),
            ("It was not until the 19th century that we found out the truth.",
             "It was not until the 19th century / that we found out the truth.",
             "19세기 말이 되어서야 / 우리는 진실을 알아냈다."),
            ("Human history is not free from the natural world.",
             "Human history is not free / from the natural world.",
             "인간 역사는 자유롭지 못하다 / 자연 세계로부터.")],
        close="드디어 모기 이야기 끝! 어려운 문법 다 해냈어. 스스로 칭찬해줘. 🙌"),

    # ============================ 8일차 ============================
    dict(day=8, week=2, weekday="수", title_en="Ladybugs", title_ko="무당벌레 (본문 외)",
        part="본문 외 · 무당벌레 문장 1–6", goal_title="최상급 : the + 최상급(-est / most ~) = ‘가장 ~한’",
        gnote="가장 ~한 = <b>the + 최상급</b>. 짧으면 -est, 길면 most.",
        open="이번엔 착한 벌레 이야기! 무당벌레가 왜 정원의 인기스타인지 보자. 귀엽지 않아?",
        passage_explain=(
            "무당벌레는 정원의 이로운 벌레 중에서 <b>가장 유명해</b>. 왜냐하면 식물을 해치는 <b>진딧물</b> 같은 나쁜 벌레를 "
            "엄청 잡아먹거든. 무당벌레 한 마리가 하루에 진딧물 50~60마리, <b>평생</b> 5천 마리 넘게 먹어. 새끼들도 진딧물을 먹지. "
            "그래서 무당벌레를 불러들이는 고수·박하 같은 식물을 심으면 <b>해로운</b> 벌레 걱정을 덜 수 있어. "
            "게다가 무당벌레는 천적이 싫어하는 특정한 <b>냄새</b>를 뿜어서 스스로를 지키기까지 해."),
        tf=[("무당벌레는 진딧물 같은 해충을 잡아먹는다.", True),
            ("무당벌레는 평생 진딧물을 몇 마리밖에 못 먹는다.", False),
            ("무당벌레는 냄새를 뿜어 천적으로부터 자신을 지킨다.", True)],
        words=[("ladybug","무당벌레"),("helpful","도움이 되는, 유익한"),("garden","정원, 텃밭"),
               ("grow","자라다, 기르다"),("lifetime","일생, 평생"),("harmful","해로운"),
               ("defend","방어하다, 지키다"),("give off","내뿜다, 발산하다"),("smell","냄새"),("predator","포식자, 천적")],
        grammar=dict(
            terms=[("원급 / 최상급","원급은 그냥 tall(키 큰), 최상급은 tallest(가장 키 큰)."),
                   ("음절","단어를 소리 낼 때 나눠지는 덩어리. tall은 1음절(짧음), famous는 2음절(김).")],
            intro=("‘<b>가장</b> ~한’을 말할 때 최상급을 써. 규칙은 두 가지야. ① 짧은 단어는 뒤에 <b>-est</b>를 붙여 "
                   "(tall→tall<b>est</b> 가장 키 큰). ② 긴 단어는 앞에 <b>most</b>를 붙여 (famous→<b>most</b> famous 가장 유명한). "
                   "그리고 최상급 앞에는 <b>the</b>를 꼭 붙여! well-known은 좀 기니까 the <b>most</b> well-known 이 되는 거지."),
            easy=[("He is the tallest boy in class.","그는 반에서 가장 키가 크다. (짧은 단어 → -est)"),
                  ("This is the most famous song.","이건 가장 유명한 노래야. (긴 단어 → most)"),
                  ("big → biggest / beautiful → most beautiful","짧으면 -est, 길면 most")],
            examples=["Ladybugs are the **most well-known** of all the helpful bugs.",
                      "→ well-known은 긴 단어라 앞에 most!"],
            ask="긴 단어를 ‘가장 ~한’으로 만들 때, 앞에 뭘 붙여?",
            answer="most (그리고 앞에 the!)",
            rule="가장 ~한 = <b>the + 최상급</b>. 짧으면 -est, 길면 most. ‘of/in ~’으로 범위를 나타내."),
        practice=[("Ladybugs are the ( more / most ) well-known bugs.","most"),
                  ("He is the ( taller / tallest ) in his class.","tallest"),
                  ("‘the most well-known’ = 가장 ( 잘 알려진 / 덜 알려진 )","잘 알려진"),
                  ("This is the most ( beautiful / beautifulest ) place.","beautiful")],
        memorize=[
            ("Ladybugs are the most well-known of all the helpful bugs.",
             "Ladybugs are the most well-known / of all the helpful bugs.",
             "무당벌레는 가장 유명하다 / 모든 이로운 벌레 중에서."),
            ("They eat the bad bugs that prevent plants from growing.",
             "They eat the bad bugs / that prevent plants from growing.",
             "그들은 나쁜 벌레를 먹는다 / 식물이 자라는 걸 막는."),
            ("Each ladybug can eat fifty to sixty aphids per day.",
             "Each ladybug can eat / fifty to sixty aphids / per day.",
             "무당벌레 한 마리는 먹을 수 있다 / 진딧물 50~60마리를 / 하루에."),
            ("They defend themselves by giving off a certain smell.",
             "They defend themselves / by giving off a certain smell.",
             "그들은 스스로를 지킨다 / 특정한 냄새를 뿜어서.")],
        close="최상급 the most, 완전 쉽지? 무당벌레 단어는 일상에서도 자주 써. 챙겨두자!"),

    # ============================ 9일차 ============================
    dict(day=9, week=2, weekday="목", title_en="Earthworms", title_ko="지렁이 (본문 외)",
        part="본문 외 · 지렁이 문장 7–12", goal_title="동명사 : 동사+ing = ‘~하는 것 / ~함’",
        gnote="전치사(by·at·about·after) 뒤에는 동사를 꼭 <b>-ing</b>로!",
        open="마지막 지문은 지렁이야! 징그럽다고? 알고 보면 흙의 영웅이야. 오늘도 힘내자!",
        passage_explain=(
            "지렁이도 정원에 큰 도움이 돼. 첫째, <b>굴</b>을 파서 흙을 부드럽게 하고 공기가 통하게 해 — 식물 뿌리에 좋지. "
            "둘째, 땅에 떨어진 죽은 식물 조각을 먹어 흙으로 되돌려서(재활용) 새 식물이 자라게 도와. "
            "셋째, 지렁이의 <b>배설물</b>은 흙을 더 비옥하게 만들고, 유기물을 분해하는 데도 뛰어나. "
            "단, 주의할 점! 지렁이를 들인 뒤엔 <b>인공 비료</b>를 함부로 쓰면 안 돼. 주변 흙이 확 바뀌면 "
            "지렁이가 다른 곳으로 떠나버리거든."),
        tf=[("지렁이는 굴을 파서 흙에 공기가 통하게 한다.", True),
            ("지렁이의 배설물은 흙을 더 비옥하게 만든다.", True),
            ("지렁이를 들인 뒤에는 인공 비료를 마음껏 써도 된다.", False)],
        words=[("earthworm","지렁이"),("soil","흙, 토양"),("dig","파다"),("root","뿌리"),
               ("recycle","재순환·재활용하다"),("waste","배설물, 노폐물"),("break down","분해하다"),
               ("apply","(비료를) 사용하다"),("introduce","들여놓다, 도입하다"),("around","~ 주위에")],
        grammar=dict(
            terms=[("동명사","동사 + ing. ‘~하는 것/~하기’라는 뜻으로 명사처럼 쓰여."),
                   ("전치사","명사 앞에 붙는 짧은 말. by(~로), at(~에), about(~에 대해), after(~후에) 등.")],
            intro=("동사에 <b>-ing</b>를 붙이면 ‘~하는 것/~하기’가 되어 명사처럼 쓸 수 있어. 이걸 <b>동명사</b>라고 해. "
                   "swim(수영하다)에 ing를 붙이면 swimming(수영하기)이 되는 거지. 특히 중요한 규칙! "
                   "<b>전치사</b>(by, at, about, after 같은 짧은 말) 뒤에는 동사를 무조건 -ing로 바꿔 써야 해. "
                   "‘by <b>digging</b>(파는 것으로써/파서)’처럼 말이야."),
            easy=[("I like swimming.","나는 수영하는 걸 좋아해."),
                  ("Thank you for helping me.","도와줘서 고마워. (for 뒤라 helping)"),
                  ("He is good at singing.","그는 노래를 잘해. (at 뒤라 singing)")],
            examples=["by **digging** tunnels  (굴을 팜으로써)",
                      "excellent at **breaking** down  (분해하는 것에 뛰어난)"],
            ask="by, at, about, after 뒤에 온 단어들의 공통된 꼬리가 뭐야?",
            answer="-ing (전치사 뒤라서!)",
            rule="전치사(by·at·about·after…) 뒤에는 동사를 꼭 <b>-ing</b>로! 이게 동명사야."),
        practice=[("They keep the soil soft by ( dig / digging ) tunnels.","digging"),
                  ("Thank you for ( help / helping ) me.","helping"),
                  ("They are excellent at ( break / breaking ) down matter.","breaking"),
                  ("Be careful about ( apply / applying ) fertilizers.","applying")],
        memorize=[
            ("Earthworms are a great addition to your garden.",
             "Earthworms are a great addition / to your garden.",
             "지렁이는 훌륭한 보탬이다 / 네 정원에."),
            ("They keep your soil soft by digging tunnels.",
             "They keep your soil soft / by digging tunnels.",
             "그들은 흙을 부드럽게 유지한다 / 굴을 팜으로써."),
            ("Their waste makes your soil richer.",
             "Their waste makes / your soil richer.",
             "그들의 배설물은 만든다 / 네 흙을 더 비옥하게."),
            ("They will find a new home when the soil changes.",
             "They will find a new home / when the soil changes.",
             "그들은 새 서식지를 찾을 것이다 / 흙이 바뀌면.")],
        close="1과 완주 축하해! 🎉 이제 총복습으로 배운 걸 확실히 굳혀보자."),
]

GRAMMAR_SUMMARY = [
    ("1일차", "be동사 + 3인칭 -s", "주어가 하나면 동사에 -s (a mosquito sneaks)"),
    ("2일차", "관계대명사 that/which", "명사 뒤에서 꾸밈 (chemicals that attract them)"),
    ("3일차", "가정법 과거", "If+과거, would+원형 (현재 사실의 반대)"),
    ("4일차", "현재완료 have/has+p.p.", "지금까지 ~해 왔다/한 적 있다"),
    ("5일차", "수동태 be+p.p.", "~되다/당하다 (Rome was surrounded)"),
    ("6일차", "과거완료 had+p.p.", "과거보다 앞선 과거"),
    ("7일차", "가정법 과거완료", "If+had p.p., would have p.p. (과거 사실의 반대)"),
    ("8일차", "최상급 the+most/-est", "가장 ~한"),
    ("9일차", "동명사 동사+ing", "전치사 뒤에는 ~ing"),
]
