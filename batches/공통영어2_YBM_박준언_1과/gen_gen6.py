# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_YBM_박준언_1과")
from _helpers import *

# =====================================================================
# P10 — Further Reading: Echo Chamber ①  (본문 외 · 1)
# =====================================================================
r10 = [
 "These days, everyone accesses the news through the Internet or social media, and often selectively takes the information that suits their tastes or beliefs.",
 "However, consistently encountering similar perspectives without considering alternative views can lead you to be trapped in an \"echo chamber.\"",
 "An echo chamber refers to an enclosed space where sound doesn't leak out and returns as an echo.",
 "The term \"echo chamber\" is also used to describe any situation in which you only hear opinions you already agree with.",
 "This can distort your understanding of reality, and limit your ability to think critically and engage in meaningful debates.",
]

ov10 = Overview(
 theme_ko="에코 챔버(반향실)란 무엇인가",
 key_grammar=KeyGrammar(
  point="관계부사 where (장소 선행사 수식)",
  source_sentence="An echo chamber refers to an enclosed space where sound doesn't leak out and returns as an echo.",
  explanation=[
   GN("쉽게 말하면","'장소' 명사 뒤의 where는 그 장소에서 '무슨 일이 일어나는지'를 설명하는 [[관계부사]]야."),
   GN("복원","where = [[in which]] — 'a space where sound ~' = 'a space in which sound ~'."),
   GN("선행사","where 앞의 [[space]](공간)가 선행사 — 장소를 나타내는 명사가 온다."),
   GN("주의","where 뒤에는 주어·동사를 갖춘 [[완전한]] 절이 온다(빠진 성분 없음)."),
  ],
  example_analysis="an enclosed space where sound doesn't leak out ~ = 선행사 space를 관계부사 where가 수식.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'an enclosed space where sound doesn't leak out'에서 where의 역할은?",
    options=["장소를 선행사로 받는 관계부사","'어디'를 묻는 의문사","시간을 나타내는 관계부사"],
    answer="장소를 선행사로 받는 관계부사"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 where가 관계부사로 쓰인 것은?",
    options=["This is the house where he lives.","I don't know where he lives.","Where are you going now?"],
    answer="This is the house where he lives."),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것: 'the room ____ we studied together'",
    options=["where","which","who"],
    answer="where"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 반향실은 소리가 새어 나가지 않고 메아리로 되돌아오는 밀폐된 공간을 가리킨다.",
    answer="An echo chamber refers to an enclosed space where sound doesn't leak out and returns as an echo."),
   GrammarDrill(kind="영작",from_passage=False,
    question="이곳은 내가 태어난 도시이다.",
    answer="This is the city where I was born."),
  ]),
 topic="뉴스를 취사선택하다 갇히게 되는 '에코 챔버(반향실)'의 뜻과 위험.",
 stance="부정적·비판적",
 stance_reason="에코 챔버가 현실 이해를 왜곡하고 비판적 사고를 제한한다고 경고한다.",
 structure="주장→근거·예시",
 structure_reason="'갇힐 수 있다'는 주장 뒤에 반향실의 정의와 그 폐해로 뒷받침한다.",
 restatement_chains=[
  RestatementChain(label="에코 챔버의 정의",
   expressions=["echo chamber","an enclosed space","any situation in which you only hear opinions you already agree with"],
   variation="'소리가 갇힌 공간' → '동의하는 의견만 듣는 상황'으로 개념이 확장된다."),
 ],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1~2",summary="뉴스를 [[선택적]]으로 취하다 '에코 챔버'에 갇힐 수 있다."),
  FlowBlock(stage="전개",sentence_range="3~4",summary="에코 챔버는 소리가 [[메아리]]로 되돌아오는 밀폐 공간이자, 동의하는 의견만 듣는 상황."),
  FlowBlock(stage="결론",sentence_range="5",summary="이는 현실 이해를 [[왜곡]]하고 비판적 사고를 제한한다."),
 ])

i10 = [
 S(r10,1,
  [("관계대명사 that","'the information that suits ~' — 선행사 information 수식")],
  [("access","접하다, 접근하다"),("selectively","선택적으로"),("suit","~에 맞다"),("belief","신념")],
  [("These days, everyone [[accesses]] the news","요즘, 모두가 뉴스를 [[접한다]]"),
   ("through the [[Internet]] or social media,","[[인터넷]]이나 소셜 미디어를 통해,"),
   ("and often selectively [[takes]] the information","그리고 흔히 선택적으로 정보를 [[취한다]]"),
   ("that [[suits]] their tastes or beliefs.","자신의 취향이나 신념에 [[맞는]] (정보를).")],
  [("모두가 모든 뉴스를 빠짐없이 받아들인다는 뜻이다.","'selectively takes the information that suits their tastes(입맛에 맞는 정보만 골라 취함)'이므로 전부가 아니라 취사선택이야.")]),
 S(r10,2,
  [("분사(동명사) 주어","'consistently encountering ~' 이 긴 주어"),("결과 lead to","'lead you to be trapped' — ~하게 이끌다")],
  [("consistently","지속적으로"),("perspective","관점"),("alternative","대안적인"),("trapped","갇힌")],
  [("However, consistently [[encountering]] similar perspectives","그러나, 비슷한 관점을 지속적으로 [[접하는 것]]은"),
   ("without [[considering]] alternative views","대안적 관점을 [[고려하지]] 않고"),
   ("can lead you to be [[trapped]]","당신을 [[갇히게]] 만들 수 있다"),
   ("in an \"[[echo chamber]].\"","\"[[반향실]](에코 챔버)\" 안에.")],
  [("비슷한 관점을 자주 접하면 시야가 넓어진다는 뜻이다.","오히려 'trapped in an echo chamber(반향실에 갇힘)'라서 시야가 좁아진다는 경고야.")]),
 S(r10,3,
  [("관계부사 where","'a space where sound ~' — 장소 선행사 수식"),("병렬","doesn't leak out and returns 병렬")],
  [("refer to","~을 가리키다"),("enclosed","밀폐된"),("leak","새다"),("echo","메아리")],
  [("An echo chamber [[refers to]]","반향실은 ~을 [[가리킨다]]"),
   ("an [[enclosed]] space","[[밀폐된]] 공간을"),
   ("where sound doesn't [[leak out]]","소리가 [[새어 나가지]] 않고"),
   ("and [[returns]] as an echo.","(그리고) 메아리로 [[되돌아오는]] (공간).")],
  [("반향실은 소리가 밖으로 잘 퍼지는 열린 공간이다.","'enclosed space where sound doesn't leak out(소리가 새지 않는 밀폐 공간)'이므로 열린 공간이 아니라 닫힌 공간이야.")]),
 S(r10,4,
  [("전치사+관계대명사","'situation in which ~' — in which = where"),("접촉동사 agree with","'opinions you agree with'")],
  [("term","용어"),("describe","묘사하다, 설명하다"),("situation","상황"),("agree","동의하다")],
  [("The [[term]] \"echo chamber\"","\"반향실\"이라는 [[용어]]는"),
   ("is also used to [[describe]]","~을 [[묘사하는]] 데도 쓰인다"),
   ("any [[situation]] in which","~한 어떤 [[상황]]이든"),
   ("you only hear [[opinions]]","당신이 [[의견]]만 듣는"),
   ("you already [[agree]] with.","이미 [[동의하는]] (의견).")],
  [("반향실은 다양한 반대 의견까지 폭넓게 듣는 상황을 뜻한다.","'only hear opinions you already agree with(이미 동의하는 의견만 들음)'라서 반대 의견은 차단되는 상황이야.")]),
 S(r10,5,
  [("지시대명사 This","앞 상황(에코 챔버에 갇힘) 전체를 받음"),("병렬","distort ~ and limit ~ 병렬")],
  [("distort","왜곡하다"),("reality","현실"),("critically","비판적으로"),("meaningful","의미 있는")],
  [("This can [[distort]]","이것은 ~을 [[왜곡할]] 수 있고"),
   ("your understanding of [[reality]],","현실에 대한 당신의 [[이해]]를,"),
   ("and [[limit]] your ability","그리고 당신의 능력을 [[제한한다]]"),
   ("to think [[critically]]","[[비판적으로]] 사고하고"),
   ("and [[engage in]] meaningful debates.","의미 있는 토론에 [[참여하는]] (능력).")],
  [("여기서 This는 앞 문장의 '메아리(echo)'만을 가리킨다.","This는 '에코 챔버에 갇혀 동의하는 의견만 듣는 상황' 전체를 가리켜 — 그것이 현실 이해를 왜곡한다는 뜻이야."),
   ("이 문장은 부정적 함축 없이 단순 사실만 서술한다.","사실은 에코 챔버의 해로움을 강조하는 함축이 담겨 있어 — 비판적 사고를 '제한한다(limit)'는 경고야.")]),
]

P10 = build("Further Reading: Echo Chamber ①","본문 외 · 1 (에코 챔버란)",r10,ov10,i10)

# =====================================================================
# P11 — Further Reading: Echo Chamber ②  (본문 외 · 2)
# =====================================================================
r11 = [
 "Worse still, an echo chamber may foster social division, making collaboration on common issues challenging.",
 "To avoid falling into this trap, you must actively seek diverse sources of information and engage with people who have different views.",
 "Always remember to check the information you receive, and keep an open mind when discussing new ideas.",
 "Even if you really want something to be true, it doesn't always mean that it is true.",
]

ov11 = Overview(
 theme_ko="에코 챔버의 사회적 폐해와 대처법",
 key_grammar=KeyGrammar(
  point="분사구문 making (결과·부대상황)",
  source_sentence="Worse still, an echo chamber may foster social division, making collaboration on common issues challenging.",
  explanation=[
   GN("쉽게 말하면","콤마 뒤의 '-ing ~'는 '접속사+주어'를 지운 [[분사구문]]으로, 여기선 '~하면서/그 결과 ~'를 뜻해."),
   GN("복원","making collaboration ~ challenging = [[and it makes]] collaboration ~ challenging."),
   GN("의미상 주어","분사구문의 주인은 주절 주어와 [[같아]] — 여기선 an echo chamber."),
   GN("5형식","make + collaboration(목적어) + [[challenging]](목적격보어) 구조."),
  ],
  example_analysis="making collaboration on common issues challenging = 주절의 결과를 나타내는 분사구문.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'making collaboration on common issues challenging'의 문법 기능은?",
    options=["결과·부대상황을 나타내는 분사구문","목적을 나타내는 부정사구","조건을 나타내는 부사절"],
    answer="결과·부대상황을 나타내는 분사구문"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 부분이 분사구문인 것은?",
    options=["He left the room, waving his hand.","The waving flag is red.","He is waving his hand now."],
    answer="He left the room, waving his hand."),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것: 'She sat there, ____ a book.' (책을 읽으면서)",
    options=["reading","read","to read"],
    answer="reading"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 설상가상으로, 반향실은 공통의 문제에 대한 협력을 어렵게 만들면서 사회적 분열을 조장할 수 있다.",
    answer="Worse still, an echo chamber may foster social division, making collaboration on common issues challenging."),
   GrammarDrill(kind="영작",from_passage=False,
    question="그녀는 노래를 부르며 저녁을 준비했다.",
    answer="She prepared dinner, singing a song."),
  ]),
 topic="에코 챔버가 낳는 사회 분열과, 거기서 벗어나기 위한 실천 방안.",
 stance="부정적·비판적",
 stance_reason="에코 챔버를 '함정'으로 규정하고, 능동적으로 벗어나라고 촉구한다.",
 structure="문제→해결(방안)",
 structure_reason="사회 분열이라는 문제를 제시하고, 다양한 정보 탐색·열린 마음이라는 해결책을 준다.",
 restatement_chains=[
  RestatementChain(label="함정에서 벗어나는 방법",
   expressions=["this trap","diverse sources of information","people who have different views"],
   variation="'함정' → '다양한 정보·다른 견해의 사람'으로 대처법이 구체화된다."),
 ],
 flow_blocks=[
  FlowBlock(stage="심화",sentence_range="1",summary="더 나쁘게도 에코 챔버는 사회 [[분열]]을 조장해 협력을 어렵게 한다."),
  FlowBlock(stage="방안",sentence_range="2~3",summary="[[다양한]] 정보를 찾고, 정보를 확인하며 열린 마음을 유지하라."),
  FlowBlock(stage="결론",sentence_range="4",summary="바란다고 해서 그것이 [[사실]]이 되는 것은 아니다."),
 ])

i11 = [
 S(r11,1,
  [("분사구문 making","'making ~ challenging' — 결과·부대상황"),("5형식","make + 목적어 + challenging(목적격보어)")],
  [("worse still","설상가상으로"),("foster","조장하다, 촉진하다"),("division","분열"),("collaboration","협력")],
  [("[[Worse still]], an echo chamber","[[설상가상으로]], 반향실은"),
   ("may [[foster]] social division,","사회적 분열을 [[조장할]] 수 있고,"),
   ("making [[collaboration]] on common issues","공통의 문제에 대한 [[협력]]을"),
   ("[[challenging]].","[[어렵게]] 만들면서.")],
  [("협력이 반향실 덕분에 오히려 더 쉬워진다는 뜻이다.","'making collaboration ~ challenging(협력을 어렵게 만듦)'이므로 쉬워지는 게 아니라 어려워진다는 부정적 결과야.")]),
 S(r11,2,
  [("목적 to부정사","'To avoid ~' — ~하기 위해서"),("관계대명사 who","'people who have ~' 수식")],
  [("avoid","피하다"),("trap","함정"),("diverse","다양한"),("engage with","~와 교류하다")],
  [("To avoid [[falling into]] this trap,","이 [[함정에 빠지지]] 않으려면,"),
   ("you must actively [[seek]]","당신은 [[적극적으로]] 찾아야 한다"),
   ("[[diverse]] sources of information","[[다양한]] 정보의 원천을"),
   ("and [[engage with]] people","그리고 사람들과 [[교류하며]]"),
   ("who have [[different]] views.","[[다른]] 견해를 가진 (사람들과).")],
  [("여기서 this trap은 '정보 과잉' 자체를 가리킨다.","this trap은 앞서 말한 '에코 챔버(echo chamber)'를 가리켜 — 그 함정에 빠지지 않으려면 다양한 정보를 찾으라는 뜻이야.")]),
 S(r11,3,
  [("remember to+동사원형","'앞으로 확인할 것'을 기억하라"),("명령문 병렬","remember ~ and keep ~")],
  [("remember","기억하다"),("receive","받다"),("open mind","열린 마음"),("discuss","논의하다")],
  [("Always remember to [[check]]","항상 [[확인하는 것]]을 기억하라"),
   ("the information you [[receive]],","당신이 [[받는]] 정보를,"),
   ("and keep an [[open mind]]","그리고 [[열린 마음]]을 유지하라"),
   ("when [[discussing]] new ideas.","새로운 생각을 [[논의할]] 때.")],
  [("이미 받은 정보는 굳이 확인할 필요가 없다는 뜻이다.","'remember to check the information you receive(받는 정보를 꼭 확인하라)'는 명령이라 확인은 필수라는 조언이야.")]),
 S(r11,4,
  [("양보 Even if","'설령 ~일지라도'"),("부분부정","doesn't always — '항상 ~인 것은 아니다'")],
  [("even if","설령 ~일지라도"),("really","정말로"),("mean","의미하다"),("true","사실인, 참인")],
  [("Even if you really [[want]]","당신이 정말로 [[원한다]] 해도"),
   ("something to be [[true]],","무언가가 [[사실]]이기를,"),
   ("it doesn't always [[mean]]","그것이 항상 [[의미하는]] 것은 아니다"),
   ("that it is [[true]].","그것이 [[사실]]이라고 (말할 수는 없다).")],
  [("원하기만 하면 그것이 저절로 사실이 된다는 뜻이다.","반대야 — 'it doesn't always mean that it is true(원한다고 사실이 되는 건 아니다)'라는 함축으로, 바람과 사실은 다르다는 경고야."),
   ("원하는 것은 결코 사실일 수 없다는 뜻이다.","'doesn't always(항상 ~은 아니다)'는 부분부정이라 '전부 거짓'이 아니라 '늘 참인 것은 아니다'라는 뜻이야.")]),
]

P11 = build("Further Reading: Echo Chamber ②","본문 외 · 2 (사회 분열과 대처)",r11,ov11,i11)

PARTS = [P10, P11]
