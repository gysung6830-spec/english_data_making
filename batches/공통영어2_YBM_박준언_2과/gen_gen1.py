# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_YBM_박준언_2과")
from _helpers import *

# =====================================================================
# P1 — Dry ① 수도 단수
# =====================================================================
r1 = [
 "The kitchen tap makes strange sounds. It coughs. It spits once, and then goes silent.",
 "“Mom,” I shout out into the living room, “water is not coming out.”",
 "“Alyssa, shush!” Mom says.",
 "She is watching the TV, where a news anchor is talking about the “flow crisis.”",
 "This is what the media has been calling the drought ever since people got tired of hearing the word “drought.”",
 "Now the crisis is entering a new stage. We have no running water out of the tap.",
]

ov1 = Overview(
 theme_ko="수도가 끊긴 순간 — 가뭄이 새 국면에 들다",
 key_grammar=KeyGrammar(
  point="관계부사 where (앞 명사를 보충설명하는 계속적 용법)",
  source_sentence="She is watching the TV, where a news anchor is talking about the “flow crisis.”",
  explanation=[
   GN("쉽게 말하면","콤마 뒤의 where는 앞 명사(the TV)를 [[보충설명]]하는 계속적 용법 — '그런데 그곳에서 ~'로 이어 읽는다."),
   GN("복원","the TV, where ~ = the TV, [[and there]] a news anchor is talking ~ 로 풀 수 있다."),
   GN("관계부사 자리","where 뒤에는 빠진 곳 없는 [[완전한 절]]이 온다(주어+동사 다 갖춤)."),
   GN("주의","이때 where는 앞 명사를 한정하지 않고 [[덧붙여]] 설명만 한다 — 콤마가 신호."),
  ],
  example_analysis="the TV, where a news anchor is talking ~ = 선행사 the TV를 뒤에서 보충설명하는 계속적 용법 where.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'the TV, where a news anchor is talking ~'에서 where의 역할은?",
    options=["선행사 the TV를 보충설명하는 관계부사(계속적 용법)","이유를 나타내는 접속사","의문사 where(어디)"],
    answer="선행사 the TV를 보충설명하는 관계부사(계속적 용법)"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 where가 '계속적 용법 관계부사'인 것은?",
    options=["We visited Seoul, where my aunt lives.","Where did you put my keys?","This is the house where I grew up."],
    answer="We visited Seoul, where my aunt lives."),
   GrammarDrill(kind="객관식",from_passage=False,
    question="'그녀는 부엌으로 갔는데, 그곳에서 물소리가 났다.' — 빈칸: She went to the kitchen, ____ she heard water.",
    options=["where","which","what"],
    answer="where"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 그녀는 TV를 보고 있는데, 그곳에서는 뉴스 앵커가 '흐름 위기'에 대해 말하고 있다.",
    answer="She is watching the TV, where a news anchor is talking about the flow crisis."),
   GrammarDrill(kind="영작",from_passage=False,
    question="우리는 공원에 도착했는데, 그곳에서 아이들이 놀고 있었다.",
    answer="We arrived at the park, where children were playing."),
  ]),
 topic="주방 수도가 끊기며 가뭄이 '흐름 위기'라는 새 국면으로 들어서는 장면.",
 stance="중립적",stance_reason="화자가 단수가 시작되는 순간을 있는 그대로 보여 주는 서사 도입부.",
 structure="시간·순서(나열)",structure_reason="수도꼭지 소음 → 엄마와의 대화 → 뉴스 → 위기의 새 단계로 시간 순 전개.",
 restatement_chains=[
  RestatementChain(label="가뭄에서 흐름 위기로",
   expressions=["flow crisis","the crisis is entering a new stage"],
   variation="언론이 부르는 '흐름 위기'가 이제 '새 국면'으로 심화된다."),
 ],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1",summary="부엌 수도꼭지가 [[이상한 소리]]를 내다 물이 끊긴다."),
  FlowBlock(stage="전개",sentence_range="2~3",summary="화자가 단수를 외치자 엄마는 [[조용히]] 하라며 TV에 집중한다."),
  FlowBlock(stage="배경",sentence_range="4~5",summary="뉴스가 가뭄을 [[흐름 위기]]로 바꿔 부른 경위를 설명한다."),
  FlowBlock(stage="전환",sentence_range="6",summary="위기가 [[새 국면]]에 들어 수도에서 물이 아예 안 나온다."),
 ])

i1 = [
 S(r1,1,[("대명사 It","앞 명사 the tap을 받는 대명사")],
  [("tap","수도꼭지"),("spit","(물을) 뱉어내다")],
  [("The kitchen tap [[makes strange sounds]].","부엌 수도꼭지가 [[이상한 소리를 낸다]]."),
   ("It [[coughs]].","그것이 [[콜록거린다]]."),
   ("It [[spits]] once,","그것이 한 번 [[뱉어내고]],"),
   ("and then [[goes silent]].","그러고는 [[조용해진다]].")],
  [("It coughs / It spits의 It은 엄마(Mom)를 가리킨다.","(지칭) 틀렸다. It은 the kitchen tap(수도꼭지)을 가리킨다. 물이 끊겨 수도꼭지가 이상한 소리를 내는 것이다."),
   ("수도꼭지에서 물이 세차게 쏟아지는 장면이다.","틀렸다. spits once → goes silent, 즉 한 번 뱉고는 조용해진다 — 물이 나오다 끊기는 순간을 묘사한다.")]),
 S(r1,2,[("직접 인용","따옴표 안이 화자가 외친 말")],
  [("shout out","소리쳐 외치다")],
  [("“Mom,” I [[shout out]]","“엄마,” 하고 나는 [[소리친다]]"),
   ("into the [[living room]],","[[거실]]을 향해,"),
   ("“water is not [[coming out]].”","“물이 [[안 나온다]].”")],
  [("화자가 물이 잘 나온다고 알리려고 외친다.","틀렸다. water is not coming out — 물이 안 나온다고 외치는 것으로, 단수 상황을 알리는 말이다.")]),
 S(r1,3,[("명령·감탄","shush! = 조용히 시키는 말")],
  [("shush","쉿, 조용히 해")],
  [("“Alyssa, [[shush]]!”","“앨리사, [[조용히 해]]!”"),
   ("Mom [[says]].","엄마가 [[말한다]].")],
  [("엄마가 놀라서 딸의 이름을 다정하게 부른 것이다.","(함축) 틀렸다. shush!는 '조용히 해'라는 제지의 말로, 실제로는 TV 뉴스에 집중하려고 딸을 막는 것이다.")]),
 S(r1,4,[("관계부사 where","콤마 뒤 계속적 용법 — 앞 명사 the TV를 보충설명")],
  [("news anchor","뉴스 앵커"),("flow crisis","흐름 위기")],
  [("She is [[watching the TV]],","그녀는 [[TV를 보고 있는데]],"),
   ("where a [[news anchor]]","그곳에서는 [[뉴스 앵커]]가"),
   ("is [[talking]] about","[[말하고 있다]]"),
   ("the “[[flow crisis]].”","그 “[[흐름 위기]]”에 대해.")],
  [("She는 뉴스 앵커(a news anchor)를 가리킨다.","(지칭) 틀렸다. She는 앞 문장의 Mom(엄마)을 가리킨다 — TV를 보고 있는 사람은 엄마다.")]),
 S(r1,5,[("관계대명사 what","선행사를 포함한 '~하는 것'"),("현재완료","has been calling — 계속되어 온 호칭")],
  [("media","언론·미디어"),("drought","가뭄")],
  [("This is what the [[media]]","이것은 [[언론]]이"),
   ("has been [[calling]] the drought","그 가뭄을 [[불러 온]] 이름이다"),
   ("ever since people got [[tired]]","사람들이 [[지쳐버린]] 뒤로 줄곧"),
   ("of [[hearing]] the word “drought.”","“가뭄”이라는 말을 [[듣는]] 것에.")],
  [("This는 the word “drought”를 가리킨다.","(지칭) 틀렸다. This는 앞의 'flow crisis(흐름 위기)'를 가리킨다 — 언론이 drought 대신 쓰는 새 명칭이다."),
   ("언론이 용어를 바꾼 건 상황이 나아졌기 때문이다.","(함축) 틀렸다. 사람들이 'drought'라는 말에 지쳐서 언론이 'flow crisis'로 바꿔 부르는 것 — 실제로는 가뭄이 계속되고 있다.")]),
 S(r1,6,[("현재진행","is entering — 위기가 진행 중")],
  [("stage","국면·단계"),("running water","(수도로) 흐르는 물")],
  [("Now the crisis is [[entering]]","이제 그 위기는 [[접어든다]]"),
   ("a [[new stage]].","[[새로운 국면]]에."),
   ("We have no [[running water]]","우리에겐 [[흐르는 물]]이 전혀 없다"),
   ("out of the [[tap]].","[[수도꼭지]]에서 나오는.")],
  [("위기가 이제 끝나가는 마지막 단계라는 뜻이다.","틀렸다. a new stage는 위기가 더 심각해지는 새 단계로, 수도에서 물이 아예 안 나오는(no running water) 상황을 가리킨다.")]),
]

P1 = build("Dry ① 수도 단수","장면 · 1 (수도가 끊기다)",r1,ov1,i1)

# =====================================================================
# P2 — Dry ② 사재기 인파
# =====================================================================
r2 = [
 "“To the mall!” says Uncle Basil. My little brother Garrett and I jump in our uncle’s truck.",
 "As we pull into the parking lot, we can see the crowd.",
 "“You two go in. I’ll meet you inside,” Uncle Basil says.",
 "Inside it’s like Black Friday at its worst — but today it’s not televisions and video games people are after.",
 "What I see in the carts in the checkout line are mostly water bottles. The essentials of life.",
 "There is a look of impatience on the faces of the people in line. There is even hostility, hidden by a thin layer of politeness. Even that politeness is stretched thin.",
]

ov2 = Overview(
 theme_ko="물을 사재기하는 몰의 군중 — 생필품이 된 물",
 key_grammar=KeyGrammar(
  point="관계대명사 what (선행사를 포함한 '~하는 것')",
  source_sentence="What I see in the carts in the checkout line are mostly water bottles. The essentials of life.",
  explanation=[
   GN("쉽게 말하면","what은 the thing which와 같아 '~하는 [[것]]'이라는 뜻이며, 그 자체에 선행사를 [[포함]]한다."),
   GN("자리","여기서 What I see ~ 덩어리 전체가 문장의 [[주어]] 노릇을 한다."),
   GN("that와 구별","앞에 꾸밀 명사(선행사)가 없으면 that이 아니라 [[what]]을 쓴다."),
   GN("복원","What I see = [[The thing]] that I see — '내가 보는 것'."),
  ],
  example_analysis="What I see in the carts ~ = 선행사를 포함한 관계대명사 what이 이끄는 명사절이 주어.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'What I see in the carts ~ are mostly water bottles'에서 What의 역할은?",
    options=["선행사를 포함한 관계대명사(~하는 것)","의문사 what(무엇)","동격의 접속사 that"],
    answer="선행사를 포함한 관계대명사(~하는 것)"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 what이 '선행사를 포함한 관계대명사'인 것은?",
    options=["What he wants is a glass of water.","I don’t know what time it is.","What a beautiful day it is!"],
    answer="What he wants is a glass of water."),
   GrammarDrill(kind="객관식",from_passage=False,
    question="'그가 말한 것이 나를 놀라게 했다.' — 빈칸: ____ he said surprised me.",
    options=["What","That","Which"],
    answer="What"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 계산대 줄의 카트에서 내가 보는 것은 대부분 물병들이다.",
    answer="What I see in the carts in the checkout line are mostly water bottles."),
   GrammarDrill(kind="영작",from_passage=False,
    question="그가 원하는 것은 약간의 물이다.",
    answer="What he wants is some water."),
  ]),
 topic="물을 사재기하려 몰에 몰려든 군중 속으로 화자가 들어가는 장면.",
 stance="중립적",stance_reason="화자가 사재기 인파의 모습을 관찰해 보여 주는 서사 장면.",
 structure="시간·순서(나열)",structure_reason="몰로 출발 → 주차장 도착 → 매장 진입 → 계산대 → 줄 선 사람들 관찰의 시간 순.",
 restatement_chains=[
  RestatementChain(label="생필품이 된 물",
   expressions=["mostly water bottles","The essentials of life"],
   variation="카트를 채운 '물병'이 곧 '삶의 필수품'으로 다시 표현된다."),
 ],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1",summary="바질 삼촌의 트럭을 타고 [[몰]]로 향한다."),
  FlowBlock(stage="전개",sentence_range="2~3",summary="주차장에 도착해 [[군중]]을 보고, 삼촌은 아이들만 먼저 들여보낸다."),
  FlowBlock(stage="사례",sentence_range="4~5",summary="사람들이 노리는 건 전자제품이 아니라 [[물병]] — 삶의 필수품이다."),
  FlowBlock(stage="확장",sentence_range="6",summary="줄 선 사람들 얼굴엔 초조함과, 얇은 예의에 가려진 [[적의]]가 서려 있다."),
 ])

i2 = [
 S(r2,1,[("직접 인용","따옴표 안이 삼촌의 말"),("소유격","our uncle’s truck")],
  [("mall","(대형) 쇼핑몰"),("jump in","(차에) 올라타다")],
  [("“To the [[mall]]!”","“[[몰]]로 가자!”"),
   ("says [[Uncle Basil]].","하고 [[바질 삼촌]]이 말한다."),
   ("My little [[brother Garrett]] and I","내 [[남동생 개럿]]과 나는"),
   ("[[jump]] in our uncle’s truck.","삼촌의 트럭에 [[올라탄다]].")],
  [("our uncle은 개럿(Garrett)을 가리킨다.","(지칭) 틀렸다. our uncle은 Uncle Basil(바질 삼촌)을 가리킨다 — 화자와 개럿이 삼촌의 트럭에 올라타는 것이다.")]),
 S(r2,2,[("시간 부사절","As ~ = ~할 때")],
  [("pull into","(차를) 몰고 들어가다"),("crowd","군중, 인파")],
  [("As we [[pull into]]","우리가 [[몰고 들어설]] 때"),
   ("the [[parking lot]],","그 [[주차장]]으로,"),
   ("we can see the [[crowd]].","우리는 그 [[군중]]을 볼 수 있다.")],
  [("군중이 보인다는 건 평범한 쇼핑객 몇 명뿐이라는 뜻이다.","(함축) 틀렸다. the crowd는 물을 사재기하러 몰려든 대규모 인파를 뜻한다 — 물 위기로 몰이 붐비는 상황의 속뜻이다.")]),
 S(r2,3,[("직접 인용","따옴표 안이 삼촌의 지시"),("조동사 축약","I’ll = I will")],
  [("go in","안으로 들어가다"),("meet","만나다")],
  [("“You two [[go in]].","“너희 둘은 [[들어가]]."),
   ("I’ll [[meet]] you inside,”","안에서 [[만나자]],”"),
   ("[[Uncle Basil]] says.","[[바질 삼촌]]이 말한다.")],
  [("삼촌이 아이들과 함께 곧장 매장으로 들어간다.","틀렸다. 삼촌은 'You two go in'이라며 둘만 먼저 들여보내고, 자신은 나중에 안에서 만나자고 한다.")]),
 S(r2,4,[("강조구문·생략","it’s not ~ (that) people are after — 관계사 생략"),("비유","like Black Friday at its worst")],
  [("at its worst","최악인 상태로"),("after","(be after) ~을 노리다")],
  [("Inside it’s like [[Black Friday]]","안은 마치 [[블랙 프라이데이]] 같다"),
   ("at its [[worst]] —","그 [[최악]]의 상태인 —"),
   ("but today it’s not [[televisions]] and video games","하지만 오늘은 [[텔레비전]]이나 비디오 게임이 아니라"),
   ("people are [[after]].","사람들이 [[노리는]] 것이.")],
  [("사람들이 블랙 프라이데이처럼 TV와 게임기를 사려 몰려든다.","(함축) 틀렸다. today it’s not televisions and video games — 오늘 사람들이 노리는 건 전자제품이 아니라 물이다. 최악의 사재기를 반어적으로 비교한 것.")]),
 S(r2,5,[("관계대명사 what","선행사 포함 '~하는 것'이 주어"),("동격·부연","The essentials of life = water bottles")],
  [("cart","(쇼핑) 카트"),("essentials","필수품")],
  [("What I see in the [[carts]]","내가 [[카트]]에서 보는 것은"),
   ("in the [[checkout line]]","[[계산대 줄]]의"),
   ("are mostly [[water bottles]].","대부분 [[물병들]]이다."),
   ("The [[essentials]] of life.","삶의 [[필수품]].")],
  [("사람들이 물을 사치품처럼 여겨 카트에 담는다.","틀렸다. water bottles를 'The essentials of life(삶의 필수품)'라 부른다 — 물이 생존의 필수품이 되어 버린 상황이다.")]),
 S(r2,6,[("과거분사구","hidden by ~ = ~에 가려진 (수동)"),("지시형용사 that","that politeness")],
  [("impatience","초조함"),("hostility","적의, 적대감"),("politeness","예의, 정중함")],
  [("There is a look of [[impatience]]","[[초조한]] 기색이 서려 있다"),
   ("on the faces of the [[people in line]].","줄 선 [[사람들]]의 얼굴에."),
   ("There is even [[hostility]],","심지어 [[적의]]마저 있다,"),
   ("[[hidden]] by a thin layer of politeness.","얇은 예의의 층에 [[가려진]] 채."),
   ("Even that politeness is [[stretched thin]].","그 예의마저도 [[얇게 늘어져]] 있다.")],
  [("that politeness는 사람들의 적의(hostility)를 가리킨다.","(지칭) 틀렸다. that politeness는 앞의 'a thin layer of politeness(얇은 예의)'를 가리킨다 — 그 예의조차 한계에 다다랐다는 뜻."),
   ("사람들이 서로 예의 바르게 질서를 잘 지키고 있다.","(함축) 틀렸다. hostility hidden by a thin layer of politeness — 겉으론 예의지만 속으론 적의가 끓어 곧 무너질 상황의 속뜻이다.")]),
]

P2 = build("Dry ② 사재기 인파","장면 · 2 (몰의 군중)",r2,ov2,i2)

PARTS = [P1, P2]
