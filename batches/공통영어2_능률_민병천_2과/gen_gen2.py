# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_능률_민병천_2과")
from _helpers import *

# ============================================================
# P3 · 3 · Magrath와 법의학의 불씨
# ============================================================
r3 = [
 "Lee heard many interesting stories of real-life crime from her friend, George Burgess Magrath.",
 "He was a medical examiner who wanted to change the investigation system.",
 "This was because, at that time, people with no medical knowledge investigated and closed many death cases without examining the bodies.",
 "He also had a passion for educating medical students in legal medicine.",
 "Magrath's passion sparked Lee's interest in legal medicine.",
]

ov3 = Overview(
 theme_ko="법의학의 불씨가 된 친구 Magrath",
 key_grammar=KeyGrammar(
  point="주격 관계대명사 who (사람 선행사 수식)",
  source_sentence="He was a medical examiner who wanted to change the investigation system.",
  explanation=[
   GN("쉽게 말하면","'a medical examiner who wanted ~'에서 who는 앞의 사람 [[선행사]]를 꾸미는 관계대명사."),
   GN("주격","who 뒤에 곧바로 [[동사]](wanted)가 오면 who가 그 절의 주어 역할을 하는 주격이야."),
   GN("복원","a medical examiner who wanted ~ = a medical examiner, [[and he]] wanted ~ 로 풀 수 있어."),
   GN("주의","선행사가 사람이면 who, 사물이면 [[which]]/that 을 쓴다."),
  ],
  example_analysis="a medical examiner (선행사·사람) + who wanted to change ~ (주격 관계사절이 뒤에서 수식).",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'a medical examiner who wanted to change ~'에서 who의 역할은?",
    options=["주격 관계대명사","목적격 관계대명사","의문사"],answer="주격 관계대명사"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것: 'I know a doctor ___ helps poor people.'",
    options=["who","whom","which"],answer="who"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 who가 '주격 관계대명사'인 것은?",
    options=["The man who called me is my uncle.","I wonder who she is.","She is the one whom I trust."],
    answer="The man who called me is my uncle."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 그는 수사 체계를 바꾸고 싶어 한 검시관이었다.",
    answer="He was a medical examiner who wanted to change the investigation system."),
   GrammarDrill(kind="영작",from_passage=False,
    question="나는 프랑스어를 할 수 있는 친구가 한 명 있다.",
    answer="I have a friend who can speak French."),
  ]),
 topic="친구 Magrath의 영향으로 Lee가 법의학에 관심을 갖게 된 계기.",
 stance="중립적",stance_reason="Lee의 생애 사실과 관심의 발단을 담담히 전개한다.",
 structure="시간·순서(나열)",structure_reason="이야기를 들음→인물 소개→배경→열정→관심 발생으로 이어지는 시간 순서.",
 restatement_chains=[RestatementChain(label="법의학에 대한 관심",
   expressions=["passion for educating medical students","sparked Lee's interest in legal medicine"],
   variation="'교육에 대한 열정' → '법의학에 대한 관심 촉발'로 이어진다.")],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1~2",summary="Lee는 친구 [[Magrath]]에게서 실제 범죄 이야기를 들었고, 그는 수사 체계를 바꾸려던 검시관이었다."),
  FlowBlock(stage="배경",sentence_range="3",summary="당시 [[의학 지식]] 없는 사람들이 시신도 살피지 않고 사건을 종결했기 때문이다."),
  FlowBlock(stage="전개",sentence_range="4~5",summary="교육에 대한 Magrath의 [[열정]]이 법의학을 향한 Lee의 관심에 불을 붙였다."),
 ])

i3 = [
 S(r3,1,[("전치사구 수식","of real-life crime, from her friend가 stories를 뒤에서 꾸밈"),("동격","her friend = George Burgess Magrath")],
  [("real-life crime","실제 범죄"),("medical examiner","검시관")],
  [("Lee [[heard]] many interesting stories","Lee는 많은 흥미로운 이야기를 [[들었다]]"),
   ("of [[real-life crime]]","[[실제 범죄]]에 관한"),
   ("from her friend, [[George Burgess Magrath]].","친구인 [[George Burgess Magrath]]로부터.")],
  [("Lee가 직접 범죄를 수사하며 이야기를 얻었다.","'from her friend(친구로부터)' 들은 것 — 직접 수사가 아니라 친구에게서 전해 들은 이야기야.")]),
 S(r3,2,[("주격 관계대명사 who","a medical examiner를 who wanted ~ 절이 수식")],
  [("investigation system","수사 체계")],
  [("He was a [[medical examiner]]","그는 [[검시관]]이었다"),
   ("who [[wanted]] to change","바꾸고 [[싶어 한]]"),
   ("the [[investigation]] system.","그 [[수사]] 체계를.")],
  [("Magrath는 기존 수사 체계에 만족하고 있었다.","'who wanted to change the investigation system' — 체계를 바꾸고 싶어 한 사람이라 만족이 아니야.")]),
 S(r3,3,[("지시대명사 This","앞 문장(체계를 바꾸려 함)의 이유를 받음"),("동시 병렬","investigated and closed 두 동사 병렬")],
  [("medical knowledge","의학 지식"),("examine","조사하다·검시하다")],
  [("This was [[because]],","이는 ~ [[때문]]이었다,"),
   ("at that [[time]],","그 [[당시]],"),
   ("people with no [[medical knowledge]]","[[의학 지식]]이 없는 사람들이"),
   ("[[investigated]] and closed","[[조사하고]] 종결했다"),
   ("many [[death cases]]","많은 [[사망 사건]]을"),
   ("without [[examining]] the bodies.","시신을 [[살피지]] 않은 채.")],
  [("'This'는 Lee가 이야기에 흥미를 느낀 것을 가리킨다.","This는 앞 문장의 'Magrath가 수사 체계를 바꾸고 싶어 했다'는 사실을 가리켜 — 그 이유를 설명하는 지칭이야."),
   ("당시엔 전문가들이 시신을 꼼꼼히 검시했다.","'people with no medical knowledge ~ without examining the bodies' — 의학 지식 없는 사람들이 시신도 안 보고 사건을 닫았어(정반대).")]),
 S(r3,4,[("전치사+동명사","for educating이 passion을 한정")],
  [("passion","열정"),("legal medicine","법의학")],
  [("He also had a [[passion]]","그는 또한 [[열정]]을 가졌다"),
   ("for [[educating]] medical students","의학도들을 [[가르치는]] 것에 대한"),
   ("in [[legal medicine]].","[[법의학]] 분야에서.")],
  [("그의 열정은 오직 범죄 사건 해결에만 있었다.","'a passion for educating medical students' — 의학도를 법의학으로 교육하려는 열정이야, 사건 해결만이 아니라.")]),
 S(r3,5,[("무생물 주어","passion이 주어로 interest를 sparked")],
  [("spark","촉발하다·불을 붙이다"),("interest","관심")],
  [("Magrath's passion [[sparked]]","Magrath의 열정은 [[불러일으켰다]]"),
   ("Lee's [[interest]]","Lee의 [[관심]]을"),
   ("in [[legal medicine]].","[[법의학]]에 대한.")],
  [("Lee의 관심은 Magrath와 무관하게 저절로 생겨났다.","'Magrath's passion sparked Lee's interest' — 속뜻은 그의 열정이 계기였다는 것, 실제로는 그가 없었다면 관심도 없었을 것이라는 함축이야.")]),
]
P3 = build("Lee ③ 법의학의 불씨","3 · Magrath와 법의학의 불씨",r3,ov3,i3)

# ============================================================
# P4 · 4 · 법의학에 헌신하고 하버드를 설득하다
# ============================================================
r4 = [
 "Lee started studying legal medicine by reading books and speaking with experts.",
 "She believed that medical examiner systems would be adopted more widely across the country.",
 "Furthermore, she wanted to see more young medical students trained in legal medicine.",
 "She decided to devote the rest of her life to developing this field.",
 "In 1931, she persuaded Harvard University to use her fortune to make a new branch of study: legal medicine.",
 "She also helped set up a library with rare books and documents.",
]

ov4 = Overview(
 theme_ko="법의학에 헌신하고 하버드를 설득하다",
 key_grammar=KeyGrammar(
  point="persuade + 목적어 + to부정사 (…를 설득해 …하게 하다)",
  source_sentence="In 1931, she persuaded Harvard University to use her fortune to make a new branch of study: legal medicine.",
  explanation=[
   GN("쉽게 말하면","'persuade + 목적어 + to부정사'는 '(목적어)를 설득해 (…)하게 만들다'라는 [[사역성]] 구문이야."),
   GN("형태","persuaded Harvard University [[to use]] ~ 처럼 목적어 뒤에 to부정사가 온다."),
   GN("의미상 주어","to use의 실제 주체는 목적어인 [[Harvard University]] — 재산을 쓰는 건 대학이야."),
   GN("같은 꼴 동사","ask, tell, want, [[allow]] 등도 '동사+목적어+to부정사' 꼴을 쓴다."),
  ],
  example_analysis="persuaded (동사) + Harvard University (목적어) + to use ~ (to부정사) 구조.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'persuaded Harvard University to use ~'의 구조는?",
    options=["persuade+목적어+to부정사","persuade+that절","persuade+동명사"],answer="persuade+목적어+to부정사"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것: 'She persuaded him ___ stay.'",
    options=["to","that","for"],answer="to"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="어법상 옳은 문장은?",
    options=["They persuaded me to join the team.","They persuaded me join the team.","They persuaded me joining the team."],
    answer="They persuaded me to join the team."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 1931년, 그녀는 하버드 대학을 설득해 자신의 재산으로 법의학이라는 새 학문 분야를 만들게 했다.",
    answer="In 1931, she persuaded Harvard University to use her fortune to make a new branch of study: legal medicine."),
   GrammarDrill(kind="영작",from_passage=False,
    question="선생님은 우리에게 더 열심히 공부하라고 설득했다.",
    answer="The teacher persuaded us to study harder."),
  ]),
 topic="Lee가 법의학 공부에 헌신하고 하버드를 설득해 새 학문 분야를 세운 과정.",
 stance="긍정적",stance_reason="법의학에 여생을 바친 그녀의 헌신과 업적을 긍정적으로 조명한다.",
 structure="시간·순서(나열)",structure_reason="공부 시작→신념→바람→결심→1931년 하버드 설득→도서관 마련의 시간 순서.",
 restatement_chains=[RestatementChain(label="법의학 확산의 꿈",
   expressions=["adopted more widely across the country","see more young medical students trained in legal medicine"],
   variation="'제도의 전국적 확산' → '더 많은 학생의 법의학 교육'으로 구체화된다.")],
 flow_blocks=[
  FlowBlock(stage="전개",sentence_range="1~2",summary="Lee는 [[독학]]으로 법의학을 공부하며 검시관 제도가 전국에 더 널리 채택되리라 믿었다."),
  FlowBlock(stage="결심",sentence_range="3~4",summary="더 많은 학생이 법의학 교육을 받길 바라며 [[여생]]을 이 분야 발전에 바치기로 했다."),
  FlowBlock(stage="업적",sentence_range="5~6",summary="1931년 하버드를 [[설득해]] 법의학 학문을 세우고 희귀 도서 도서관도 마련했다."),
 ])

i4 = [
 S(r4,1,[("by+동명사","방법을 나타내는 by reading, speaking 병렬")],
  [("legal medicine","법의학"),("expert","전문가")],
  [("Lee [[started]] studying legal medicine","Lee는 법의학 공부를 [[시작했다]]"),
   ("by [[reading]] books","책을 [[읽으며]]"),
   ("and [[speaking]] with experts.","전문가들과 [[이야기하며]].")],
  [("Lee는 정식 학위 과정에 등록해 법의학을 배웠다.","'by reading books and speaking with experts' — 책을 읽고 전문가와 대화하며 독학하듯 공부한 것이지 정규 과정 등록이 아니야.")]),
 S(r4,2,[("목적어 that절","believed that ~"),("수동태","would be adopted"),("비교급","more widely")],
  [("medical examiner","검시관"),("adopt","채택하다")],
  [("She [[believed]] that","그녀는 ~ [[믿었다]]"),
   ("medical examiner [[systems]]","검시관 [[제도]]가"),
   ("would be [[adopted]]","[[채택될]] 것이라고"),
   ("more [[widely]] across the country.","전국에 걸쳐 더 [[널리]].")],
  [("그녀는 검시관 제도가 곧 사라질 것이라 믿었다.","'would be adopted more widely' — 제도가 사라진다가 아니라 실제로는 더 널리 채택될 것이라 믿은 함축이야(정반대).")]),
 S(r4,3,[("지각동사 see+목적어+과거분사","see ~ students trained (수동 관계)")],
  [("furthermore","게다가"),("train","훈련·교육하다")],
  [("Furthermore, she [[wanted]] to see","게다가, 그녀는 보고 [[싶어 했다]]"),
   ("more young [[medical students]]","더 많은 젊은 [[의학도]]들이"),
   ("[[trained]] in legal medicine.","법의학 교육을 [[받는]] 것을.")],
  [("그녀는 학생들이 법의학을 멀리하기를 바랐다.","'wanted to see more young students trained' — 더 많은 학생이 법의학 교육을 받길 바란 것이야.")]),
 S(r4,4,[("decide+to부정사","결심의 대상"),("지시형용사 this","this field=법의학")],
  [("devote","바치다·헌신하다"),("develop","발전시키다")],
  [("She [[decided]] to devote","그녀는 바치기로 [[결심했다]]"),
   ("the rest of her [[life]]","그녀의 남은 [[생애]]를"),
   ("to developing this [[field]].","이 [[분야]]를 발전시키는 데.")],
  [("'this field'는 일반적인 의학 전체를 가리킨다.","this field는 앞서 말한 법의학(legal medicine)을 가리켜 — 바로 그 분야에 여생을 바치기로 한 거야.")]),
 S(r4,5,[("persuade+목적어+to부정사","persuaded Harvard University to use ~"),("콜론","study: legal medicine 로 부연")],
  [("persuade","설득하다"),("fortune","재산")],
  [("In 1931, she [[persuaded]] Harvard University","1931년, 그녀는 하버드 대학을 [[설득했다]]"),
   ("to use her [[fortune]]","그녀의 [[재산]]을 쓰도록"),
   ("to make a new [[branch of study]]:","새로운 [[학문 분야]]를 만들도록:"),
   ("[[legal medicine]].","바로 [[법의학]]을.")],
  [("하버드가 먼저 자기 돈으로 법의학과를 세우자고 Lee에게 제안했다.","'she persuaded Harvard to use HER fortune' — Lee가 자신의 재산을 쓰도록 하버드를 설득한 것이지 하버드가 제안한 게 아니야.")]),
 S(r4,6,[("help+원형","helped set up"),("전치사구 수식","with rare books and documents")],
  [("rare","희귀한"),("document","문서")],
  [("She also [[helped]] set up a library","그녀는 또한 도서관 설립을 [[도왔다]]"),
   ("with [[rare]] books","[[희귀한]] 책들과"),
   ("and [[documents]].","[[문서들]]이 있는.")],
  [("그녀가 마련한 도서관은 흔한 교과서로 채워졌다.","'a library with rare books and documents' — 희귀한 책과 문서로 채운 도서관이야, 흔한 책이 아니야.")]),
]
P4 = build("Lee ④ 헌신과 설득","4 · 법의학에 헌신하고 하버드를 설득하다",r4,ov4,i4)

PARTS = [P3, P4]
