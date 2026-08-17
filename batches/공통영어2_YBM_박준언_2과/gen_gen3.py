# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_YBM_박준언_2과")
from _helpers import *

# =====================================================================
# P5 — 장면 · 5 (Garrett과 얼음)  "Dry ⑤ 얼음이라는 기지"
# =====================================================================
r5 = [
 "I look for Garrett, whom I find in the frozen aisle. Then I see something.",
 "Just past the frozen vegetables and ice cream, there is a case packed with ice. I open the door and reach for a bag.",
 "“What are you doing? We need water, not ice,” he reminds me.",
 "“Ice is water. Just help me,” I tell him.",
 "Garrett and I put one bag of ice after another into our cart, until it is piled as high as it can get.",
 "By now other people have taken notice and begin to empty the ice case.",
]

ov5 = Overview(
 theme_ko="얼음을 물 대신 확보하는 화자의 기지",
 key_grammar=KeyGrammar(
  point="관계대명사 whom (목적격)",
  source_sentence="I look for Garrett, whom I find in the frozen aisle. Then I see something.",
  explanation=[
   GN("쉽게 말하면","목적격 관계대명사 [[whom]]은 사람 선행사를 받아, 뒤 절에서 빠진 [[목적어]] 자리를 채운다."),
   GN("복원","Garrett, whom I find ~ = Garrett + I find [[him]] (him=Garrett)."),
   GN("주의","주격이면 who, find의 목적어라서 여기선 [[whom]]을 쓴다."),
   GN("회화","목적격이라 실제 회화에선 whom을 [[생략]]하거나 who로도 쓴다."),
  ],
  example_analysis="whom = find의 목적어(선행사 Garrett)로 관계절을 이끈다.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'Garrett, whom I find'에서 whom의 문법적 역할은?",
    options=["find의 목적어","find의 주어","전치사 in의 목적어"],answer="find의 목적어"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것: 'The man ____ I met yesterday is a doctor.'",
    options=["whom","whose","which"],answer="whom"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 관계대명사가 '목적격'인 것은?",
    options=["the boy whom she loves","the boy who runs fast","the boy whose bag is red"],
    answer="the boy whom she loves"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 나는 Garrett을 찾는데, 그를 냉동 코너에서 발견한다.",
    answer="I look for Garrett, whom I find in the frozen aisle."),
   GrammarDrill(kind="영작",from_passage=False,
    question="그녀는 내가 신뢰하는 친구다.",
    answer="She is a friend whom I trust."),
  ]),
 topic="화자가 냉동 코너에서 얼음을 발견해 물 대신 카트에 쌓는 장면.",
 stance="중립적",stance_reason="상황을 있는 그대로 보여 주는 서사 묘사.",
 structure="시간·순서(나열)",structure_reason="Garrett을 찾음→얼음 발견→반대→설득→쌓기→타인 동참의 시간 순.",
 restatement_chains=[
  RestatementChain(label="물이 아니라 얼음",
   expressions=["need water, not ice","Ice is water"],
   variation="'물이지 얼음이 아니야'라는 반대가 'Ice is water'라는 기지로 뒤집힌다.")],
 flow_blocks=[
  FlowBlock(stage="전개",sentence_range="1",summary="냉동 코너에서 Garrett을 찾다가 [[무언가]]를 발견한다."),
  FlowBlock(stage="사례",sentence_range="2",summary="얼음이 가득 찬 [[진열장]]을 열고 봉지를 집는다."),
  FlowBlock(stage="대조",sentence_range="3~4",summary="Garrett은 물이 필요하다며 반대하지만 화자는 '[[Ice is water]]'라며 설득한다."),
  FlowBlock(stage="확장",sentence_range="5~6",summary="얼음을 카트에 높이 쌓자 다른 사람들도 [[동참]]해 진열장을 비운다."),
 ])

i5 = [
 S(r5,1,
  [("관계대명사 whom(목적격)","find의 목적어 자리 — 선행사 Garrett")],
  [("aisle","(매장) 통로, 코너"),("frozen","냉동의")],
  [("I look for [[Garrett]],","나는 [[Garrett]]을 찾는데,"),
   ("whom I [[find]] in the frozen aisle.","그를 냉동 코너에서 [[발견한다]]."),
   ("Then I see [[something]].","그때 나는 [[무언가]]를 본다.")],
  [("화자는 Garrett을 끝내 찾지 못했다.","'whom I find in the frozen aisle'는 냉동 코너에서 그를 '찾아냈다'는 뜻 — 못 찾은 게 아니다.")]),
 S(r5,2,
  [("there is 구문","'~이 있다' — a case가 진짜 주어")],
  [("case","진열장, 케이스"),("packed","가득 채워진")],
  [("Just past the frozen [[vegetables]] and ice cream,","냉동 [[채소]]와 아이스크림을 막 지나,"),
   ("there is a case [[packed]] with ice.","얼음이 [[가득 찬]] 진열장이 있다."),
   ("I open the door and [[reach for]] a bag.","나는 문을 열고 봉지 하나를 [[잡으려 손을 뻗는다]].")],
  [("화자가 연 진열장에는 물병이 채워져 있었다.","'a case packed with ice'는 '얼음'이 가득한 진열장 — 물이 아니라 얼음이다.")]),
 S(r5,3,
  [("호격·명령","상대에게 상기시키는 대사")],
  [("remind","상기시키다")],
  [("“What are you [[doing]]?","“[[뭐 하는]] 거야?"),
   ("We [[need]] water, not ice,”","우리는 물이 [[필요해]], 얼음 말고,”"),
   ("he [[reminds]] me.","그가 내게 [[상기시킨다]].")],
  [("여기서 'he'는 뒤에 나오는 정장 남자를 가리킨다.","(지칭) 'he'는 Garrett이다 — 정장 남자는 아직 등장하지 않았다."),
   ("Garrett은 얼음을 더 담자고 재촉한다.","Garrett은 'We need water, not ice'라며 얼음 담기를 오히려 말린다.")]),
 S(r5,4,
  [("생략(주어)","'Just help me'는 명령문 — 주어 you 생략")],
  [("tell","말하다")],
  [("“Ice is [[water]].","“얼음도 [[물이야]]."),
   ("Just [[help]] me,”","그냥 나 좀 [[도와줘]],”"),
   ("I [[tell]] him.","나는 그에게 [[말한다]].")],
  [("'Ice is water'는 얼음과 물이 같은 물질이라는 과학 설명이다.","(함축) 실제로는 '얼음을 녹이면 물이 되니 물 대용이 된다'는 화자의 기지 — 지금 물을 못 구하니 얼음으로 대신하겠다는 속뜻.")]),
 S(r5,5,
  [("as ~ as 원급","'가능한 한 높이' — as high as it can get")],
  [("pile","쌓다"),("cart","카트")],
  [("Garrett and I put one bag of ice [[after another]]","Garrett과 나는 얼음 봉지를 [[하나씩 차례로]]"),
   ("into our [[cart]],","우리 [[카트]]에 담는데,"),
   ("until it is [[piled]] as high as it can get.","그것이 최대한 높이 [[쌓일]] 때까지.")],
  [("'until it is piled'의 it은 얼음 봉지 하나를 가리킨다.","(지칭) 'it'은 our cart(카트)다 — 카트가 최대한 높이 쌓일 때까지 담는다는 뜻.")]),
 S(r5,6,
  [("현재완료","have taken notice — 방금까지 벌어진 일")],
  [("take notice","알아차리다, 주목하다"),("empty","비우다")],
  [("By now other people have taken [[notice]]","이제 다른 사람들도 [[알아차리고]]"),
   ("and begin to [[empty]] the ice case.","얼음 진열장을 [[비우기]] 시작한다.")],
  [("다른 사람들은 화자를 말리려고 다가온다.","'begin to empty the ice case'는 그들도 얼음을 가져가 진열장을 비우기 시작한다는 뜻 — 말리는 게 아니라 경쟁하듯 동참한다.")]),
]

P5 = build("Dry ⑤ 얼음이라는 기지","장면 · 5 (Garrett과 얼음)",r5,ov5,i5)


# =====================================================================
# P6 — 장면 · 6 (수상한 '도움')  "Dry ⑥ 낯선 남자의 호의"
# =====================================================================
r6 = [
 "The cart is ridiculously heavy now, and almost impossible to push. Then, a man in a business suit comes up behind us. He smiles.",
 "“Looks like you could use some help.” He doesn’t wait for us to answer before grabbing the cart’s handle.",
 "“Thank you for helping us,” I tell him.",
 "“Not a problem. We all need to help one another.” He smiles again, and I return the smile.",
 "It is good to know that difficult times can bring out the best in people. I decide that one favor deserves another.",
 "“Why don’t you take a bag of ice for yourself,” I suggest.",
 "His smile does not fade. “I have a better idea,” he says. “Why don’t you take a bag of ice for yourselves, and I’ll keep the rest.”",
]

ov6 = Overview(
 theme_ko="호의를 가장해 얼음을 가로채려는 낯선 남자",
 key_grammar=KeyGrammar(
  point="가주어 It - 진주어 to부정사 (It is ~ to-V)",
  source_sentence="It is good to know that difficult times can bring out the best in people. I decide that one favor deserves another.",
  explanation=[
   GN("쉽게 말하면","문장 앞의 [[It]]은 가주어이고, 진짜 주어는 뒤의 [[to know ~]]다."),
   GN("복원","It is good to know ~ = [[To know]] ~ is good."),
   GN("왜 그래?","to부정사 주어가 길어서 뒤로 보내고 빈자리를 [[It]]으로 채운 것."),
   GN("주의","이 It은 '그것'이라고 [[해석하지]] 않는다(가주어).")],
  example_analysis="It(가주어) = to know that ~(진주어)를 뒤로 뺀 구조.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'It is good to know ~'에서 밑줄 친 It의 정체는?",
    options=["가주어","지시대명사 '그것'","비인칭(날씨) 주어"],answer="가주어"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것: '____ is fun to swim in the sea.'",
    options=["It","That","There"],answer="It"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="'가주어 It - 진주어 to부정사' 구문인 것은?",
    options=["It is hard to learn Latin.","It is my new book.","It rains a lot here."],
    answer="It is hard to learn Latin."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 어려운 때가 사람들의 가장 좋은 면을 끌어낸다는 것을 아는 것은 좋은 일이다.",
    answer="It is good to know that difficult times can bring out the best in people."),
   GrammarDrill(kind="영작",from_passage=False,
    question="그를 만나는 것은 쉽지 않다.",
    answer="It is not easy to meet him."),
  ]),
 topic="정장 차림 남자가 도움을 핑계로 얼음을 가로채려는 장면.",
 stance="중립적",stance_reason="반전이 드러나기까지 상황을 담담히 보여 주는 서사.",
 structure="시간·순서(나열)",structure_reason="남자 등장→카트를 잡음→감사→화자의 선의→반전의 시간 순.",
 restatement_chains=[
  RestatementChain(label="호의를 가장한 속셈",
   expressions=["We all need to help one another","I’ll keep the rest"],
   variation="'서로 돕자'는 명분이 '나머지는 내가 갖겠다'는 속셈으로 뒤집힌다.")],
 flow_blocks=[
  FlowBlock(stage="전개",sentence_range="1",summary="정장 차림의 낯선 [[남자]]가 뒤에서 다가와 미소 짓는다."),
  FlowBlock(stage="사례",sentence_range="2",summary="대답도 안 기다리고 카트 [[손잡이]]를 잡아 버린다."),
  FlowBlock(stage="전개",sentence_range="3~4",summary="화자는 감사를 표하고 남자는 '서로 [[돕자]]'며 미소를 주고받는다."),
  FlowBlock(stage="확장",sentence_range="5~6",summary="화자는 호의에 보답하려 얼음 [[한 봉지]]를 권한다."),
  FlowBlock(stage="결론",sentence_range="7",summary="남자는 미소를 지운 채 '[[나머지는 내가]]'라며 속셈을 드러낸다."),
 ])

i6 = [
 S(r6,1,
  [("too ~ to / 형용사구","'거의 밀 수 없을 만큼' — almost impossible to push")],
  [("ridiculously","터무니없이"),("business suit","정장")],
  [("The cart is [[ridiculously]] heavy now,","카트는 이제 [[터무니없이]] 무겁고,"),
   ("and almost [[impossible]] to push.","밀기가 거의 [[불가능하다]]."),
   ("Then, a man in a business [[suit]]","그때 [[정장]] 차림의 한 남자가"),
   ("[[comes up]] behind us.","우리 뒤로 [[다가온다]]."),
   ("He [[smiles]].","그가 [[미소 짓는다]].")],
  [("'He smiles'의 He는 Garrett을 가리킨다.","(지칭) 여기서 He는 방금 등장한 'a man in a business suit'(정장 남자)다 — Garrett이 아니다.")]),
 S(r6,2,
  [("could use","'~이 있으면 좋겠다, 필요하다'의 완곡 표현"),
   ("before -ing","'~하기 전에' — 대답도 전에 손잡이를 잡음")],
  [("could use","~이 필요하다"),("grab","움켜쥐다")],
  [("“[[Looks like]] you could use some help.”","“도움이 좀 [[필요해 보이네요]].”"),
   ("He doesn’t [[wait]] for us to answer","그는 우리가 대답하기를 [[기다리지]] 않고"),
   ("before [[grabbing]] the cart’s handle.","카트 손잡이를 먼저 [[움켜쥔다]].")],
  [("남자는 화자들의 허락을 받은 뒤 정중히 카트를 밀어 준다.","(함축) 'doesn't wait for us to answer'—대답도 안 기다리고 손잡이를 잡는 강압적 행동으로, 뒤에 드러날 속셈의 복선이다.")]),
 S(r6,3,
  [("thank for -ing","'~해 준 것에 감사하다'")],
  [("tell","말하다")],
  [("“Thank you for [[helping]] us,”","“[[도와주셔서]] 감사해요,”"),
   ("I [[tell]] him.","나는 그에게 [[말한다]].")],
  [("화자는 남자의 속셈을 눈치채고 비꼬듯 인사한다.","(함축) 화자는 진심으로 'Thank you'라고 감사한다 — 아직 남자의 의도를 모르는 극적 아이러니다.")]),
 S(r6,4,
  [("one another","'서로' — 셋 이상 사이의 상호")],
  [("one another","서로"),("return","(웃음 등을) 되돌려 주다")],
  [("“Not a [[problem]].","“[[별일]] 아니에요."),
   ("We all need to [[help]] one another.”","우리 모두 서로를 [[도와야]] 하죠.”"),
   ("He [[smiles]] again,","그는 다시 [[미소 짓고]],"),
   ("and I [[return]] the smile.","나도 [[미소로 답한다]].")],
  [("'We all need to help one another'는 남자의 진심 어린 신념이다.","(함축) 실제로는 얼음을 가로채려는 명분·미끼일 뿐 — 곧 'I'll keep the rest'로 속셈이 드러난다.")]),
 S(r6,5,
  [("가주어 It-진주어 to부정사","It is good to know ~ — 진주어 to know"),
   ("that 명사절","know의 목적어절")],
  [("bring out","끌어내다"),("deserve","~을 받을 만하다")],
  [("It is good [[to know]]","[[안다는 것]]은 좋은 일이다"),
   ("that difficult times can [[bring out]] the best in people.","어려운 때가 사람들의 가장 좋은 면을 [[끌어낸다]]는 것을."),
   ("I decide that one favor [[deserves]] another.","나는 한 번의 호의가 또 다른 호의를 [[받을 만하다]]고 생각한다.")],
  [("화자는 남자를 의심하기로 마음먹는다.","'one favor deserves another'는 받은 호의에 보답하려는 선의 — 의심이 아니라 오히려 고마움에 보답하려는 마음이다(그 선의를 남자가 이용).")]),
 S(r6,6,
  [("Why don’t you ~?","'~하는 게 어때?' 제안")],
  [("suggest","제안하다")],
  [("“Why don’t you [[take]] a bag of ice for yourself,”","“얼음 한 봉지 [[가져가시는]] 게 어때요,”"),
   ("I [[suggest]].","나는 [[제안한다]].")],
  [("화자는 남자에게 얼음을 전부 가지라고 넘겨준다.","화자가 권한 것은 'a bag of ice'—딱 한 봉지에 대한 보답 제안이지 전부가 아니다.")]),
 S(r6,7,
  [("Why don’t you ~?","제안 형식으로 요구를 포장"),
   ("비교급","a better idea — '더 좋은' 생각")],
  [("fade","사라지다, 옅어지다"),("the rest","나머지")],
  [("His smile does not [[fade]].","그의 미소는 [[사라지지]] 않는다."),
   ("“I have a better [[idea]],” he says.","“더 좋은 [[생각]]이 있어요,” 그가 말한다."),
   ("“Why don’t you [[take]] a bag of ice for yourselves,","“얼음은 한 봉지만 [[가져가시고]],"),
   ("and I’ll [[keep]] the rest.”","나머지는 내가 [[갖겠어요]].”")],
  [("남자는 화자들에게 얼음을 양보하며 진심으로 도와준다.","(함축) 실제로는 화자에게 딱 한 봉지만 주고 'the rest(나머지)' 전부를 자기가 가로채려는 속셈 — '도움'은 얼음을 빼앗기 위한 구실이다."),
   ("'the rest'는 남은 물병들을 가리킨다.","(지칭) 'the rest'는 카트에 높이 쌓인 '나머지 얼음 봉지들 전부'를 가리킨다.")]),
]

P6 = build("Dry ⑥ 낯선 남자의 호의","장면 · 6 (수상한 '도움')",r6,ov6,i6)


PARTS = [P5, P6]
