# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_YBM_박준언_1과")
from _helpers import *

# =====================================================================
# P1 — Warning: Fake News Alert! ① (도입 · 1 흔들바위 오보)
# =====================================================================
r1 = [
 "While scrolling through her social media one day, Gina was astonished when she saw the news headline, \"The Heundeulbawi in Seoraksan National Park Has Fallen.\"",
 "Gina immediately shared the shocking story with her close friends.",
 "Later, during the morning news on TV, a reporter standing next to the undamaged Heundeulbawi said, \"Today's Internet stories of the Heundeulbawi being damaged were fake.\"",
 "Gina was embarrassed by the fact that she had spread the fake news.",
]

ov1 = Overview(
 theme_ko="가짜 뉴스를 퍼뜨리고 당황한 Gina (흔들바위 오보)",
 key_grammar=KeyGrammar(
  point="동격의 that (the fact that ~)",
  source_sentence="Gina was embarrassed by the fact that she had spread the fake news.",
  explanation=[
   GN("쉽게 말하면","'the fact that ~'은 뒤 that절이 앞 명사 fact의 [[내용]]을 그대로 풀어 주는 동격 구문이야."),
   GN("관계사와 구별","동격 that 뒤에는 문장이 [[완전]]해 — 빠진 성분이 없으면 관계대명사가 아니라 동격 that."),
   GN("자주 쓰는 명사","fact, news, idea, [[belief]], truth 처럼 '내용'을 담는 명사 뒤에 동격 that이 온다."),
   GN("과거완료","had spread는 당황한 시점보다 [[먼저]] 퍼뜨린 일을 나타내는 과거완료."),
  ],
  example_analysis="the fact = that she had spread the fake news : that절이 fact의 내용을 설명하는 동격.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'the fact that she had spread the fake news'에서 that의 역할은?",
    options=["fact와 동격을 이루는 접속사 that","목적격 관계대명사 that","지시대명사 that"],
    answer="fact와 동격을 이루는 접속사 that"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 that이 '동격'으로 쓰인 것은?",
    options=["the news that he won surprised us","the book that I read yesterday","the man that came here"],
    answer="the news that he won surprised us"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 말은? 'The ____ that she lied hurt me.' (그녀가 거짓말했다는 사실)",
    options=["fact","reason","place"],
    answer="fact"),
   GrammarDrill(kind="영작",from_passage=False,
    question="그가 떠났다는 소식이 우리를 놀라게 했다.",
    answer="The news that he had left surprised us."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) Gina는 자신이 가짜 뉴스를 퍼뜨렸다는 사실에 당황했다.",
    answer="Gina was embarrassed by the fact that she had spread the fake news."),
  ]),
 topic="흔들바위가 무너졌다는 인터넷 오보를 사실로 믿고 퍼뜨렸다가 당황한 Gina의 일화.",
 stance="중립적",
 stance_reason="Gina의 경험을 시간 순서로 전달하는 도입 서사라 특정 주장보다 사건 묘사가 중심이다.",
 structure="시간·순서(나열)",
 structure_reason="소셜미디어 목격 → 공유 → 아침 뉴스 정정 → 당황으로 사건이 시간 순서로 이어진다.",
 restatement_chains=[
  RestatementChain(label="충격 뉴스가 결국 가짜로",
   expressions=["the shocking story","the fake news"],
   variation="'충격적 이야기'로 퍼진 것이 뒤에서 '가짜 뉴스'로 정정된다."),
 ],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1",summary="Gina가 흔들바위가 [[무너졌다]]는 뉴스 헤드라인을 보고 놀란다."),
  FlowBlock(stage="전개",sentence_range="2",summary="곧바로 그 충격적인 소식을 친구들에게 [[공유]]한다."),
  FlowBlock(stage="전환",sentence_range="3",summary="아침 TV 뉴스에서 기자가 그 이야기가 [[가짜]]였다고 정정한다."),
  FlowBlock(stage="결론",sentence_range="4",summary="가짜 뉴스를 퍼뜨렸다는 사실에 Gina가 [[당황]]한다."),
 ],
)

i1 = [
 S(r1,1,
  [("분사구문","While scrolling ~ = While she was scrolling ~"),("감정 수동태","was astonished: '놀라게 되다(놀랐다)'")],
  [("scroll through","(화면을) 훑어 내리다"),("astonished","깜짝 놀란"),("headline","(뉴스) 표제")],
  [("While [[scrolling through]] her social media one day,","어느 날 소셜 미디어를 [[훑어보던]] 중에,"),
   ("Gina was [[astonished]]","Gina는 [[깜짝 놀랐다]]"),
   ("when she saw the news [[headline]],","그녀가 뉴스 [[헤드라인]]을 봤을 때,"),
   ("[[\"The Heundeulbawi in Seoraksan National Park Has Fallen.\"]]","[[\"설악산 국립공원의 흔들바위가 무너졌다.\"]]")],
  [("Gina가 직접 흔들바위 앞에서 무너지는 장면을 목격했다는 뜻이다.","소셜 미디어를 훑어보다 뉴스 헤드라인을 본 것이지, 현장을 직접 본 게 아니야."),
   ("was astonished는 Gina가 뉴스를 지어냈다는 뜻이다.","astonished는 '깜짝 놀란' 감정 상태로, 헤드라인을 보고 놀란 것이지 뉴스를 만든 게 아니야.")]),
 S(r1,2,
  [("부사 위치","immediately가 동사 shared 앞에서 '즉시'를 강조")],
  [("immediately","즉시"),("shocking","충격적인")],
  [("Gina immediately [[shared]]","Gina는 즉시 [[공유했다]]"),
   ("the [[shocking]] story","그 [[충격적인]] 이야기를"),
   ("with her close [[friends]].","가까운 [[친구들]]에게.")],
  [("(지칭) the shocking story는 Gina가 직접 겪은 실화를 가리킨다.","the shocking story는 앞의 '흔들바위가 무너졌다'는 뉴스 헤드라인을 가리켜, 실화가 아니라 그 오보를 뜻해."),
   ("Gina가 친구들에게 사실 확인을 부탁했다는 내용이다.","shared the shocking story는 충격적 이야기를 곧바로 퍼뜨린 것으로, 사실 확인을 요청한 게 아니야.")]),
 S(r1,3,
  [("현재분사 수식","standing next to ~ 가 앞의 a reporter를 뒤에서 수식"),("동명사 수동","the Heundeulbawi being damaged: 흔들바위가 훼손되는 것")],
  [("undamaged","훼손되지 않은"),("reporter","기자"),("fake","가짜의")],
  [("Later, during the [[morning]] news on TV,","나중에, TV [[아침]] 뉴스 방송 중,"),
   ("a reporter standing next to the [[undamaged]] Heundeulbawi said,","[[멀쩡한]] 흔들바위 옆에 서 있던 기자가 말했다,"),
   ("[[\"Today's Internet stories of the Heundeulbawi being damaged were fake.\"]]","[[\"오늘 흔들바위가 훼손됐다는 인터넷 이야기들은 가짜였습니다.\"]]")],
  [("(함축) 기자는 흔들바위가 실제로 훼손됐다고 확인해 주었다.","기자는 멀쩡한(undamaged) 흔들바위 옆에서 '그 이야기들은 가짜였다(were fake)'고 말했어 — 훼손은 사실이 아니야."),
   ("기자가 흔들바위 복구 공사를 보도하고 있다는 내용이다.","standing next to the undamaged Heundeulbawi는 훼손 안 된 바위 옆에 서서 오보를 바로잡는 장면이야.")]),
 S(r1,4,
  [("동격 that","the fact = that절 내용(자신이 가짜 뉴스를 퍼뜨림)"),("과거완료","had spread: 당황하기 이전에 이미 퍼뜨린 일")],
  [("embarrassed","당황한, 창피한"),("spread","퍼뜨리다"),("fact","사실")],
  [("Gina was [[embarrassed]]","Gina는 [[당황했다(창피했다)]]"),
   ("by the [[fact]]","~라는 [[사실]] 때문에"),
   ("that she had [[spread]] the fake news.","그녀가 가짜 뉴스를 [[퍼뜨렸다는]].")],
  [("Gina는 남이 퍼뜨린 가짜 뉴스 때문에 화가 났다는 뜻이다.","she had spread ~ 로 보아 가짜 뉴스를 퍼뜨린 사람은 Gina 자신 — 남 탓이 아니라 스스로 창피해한 거야."),
   ("(함축) Gina가 가짜 뉴스를 즐겁게 받아들였다는 내용이다.","embarrassed는 '창피하고 당황한' 감정으로, 자신이 오보를 퍼뜨린 것을 뉘우치는 속뜻이 담겨 있어.")]),
]

P1 = build("Warning: Fake News Alert! ①","도입 · 1 (흔들바위 오보)",r1,ov1,i1)


# =====================================================================
# P2 — Warning: Fake News Alert! ② (도입 · 2 운동선수 사망 오보)
# =====================================================================
r2 = [
 "It reminded her of another incident of fake news that had happened a while ago.",
 "The news that a famous athlete had died became the number one issue online, but it turned out to be fake.",
 "It had been made by content creators who sought people's attention.",
 "They produced provocative false stories to make money by raising the number of views of their posts.",
 "At that time, Gina criticized those who had made and spread fake news because it had hurt the athlete and confused people.",
 "This time, however, Gina herself had accidentally contributed to the spread of fake news.",
]

ov2 = Overview(
 theme_ko="관심과 돈을 노린 가짜 뉴스, 그리고 Gina의 자성 (운동선수 사망 오보)",
 key_grammar=KeyGrammar(
  point="과거완료 수동태 (had been p.p.)",
  source_sentence="It had been made by content creators who sought people's attention.",
  explanation=[
   GN("쉽게 말하면","'had been p.p.'는 과거완료(had+p.p.)와 수동태(be+p.p.)가 합쳐져 '(그 전에 이미) ~되어 있었다'는 [[수동]]의 완료야."),
   GN("형태","had + been + 과거분사 → 여기서는 had been [[made]]."),
   GN("시제 관계","기준이 되는 과거(뉴스가 화제가 된 때)보다 [[먼저]] 만들어져 있었음을 나타낸다."),
   GN("행위자","'by + 행위자'로 누가 했는지 밝혀 — by content [[creators]]."),
  ],
  example_analysis="It had been made by content creators : It(가짜 뉴스)이 '만들어진' 대상이라 수동, 그 이전 시점이라 과거완료.",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'It had been made by content creators'의 시제·태로 알맞은 것은?",
    options=["과거완료 수동태","현재완료 능동태","과거 진행형"],
    answer="과거완료 수동태"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="다음 중 '과거완료 수동태' 문장은?",
    options=["The house had been built before 1900.","The house has just been sold.","The house was building then."],
    answer="The house had been built before 1900."),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것은? 'The letter ____ before I arrived.' (내가 도착하기 전에 이미 보내져 있었다)",
    options=["had been sent","has sent","was sending"],
    answer="had been sent"),
   GrammarDrill(kind="영작",from_passage=False,
    question="그 다리는 전쟁 전에 이미 지어져 있었다.",
    answer="The bridge had been built before the war."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 그것은 사람들의 관심을 좇는 콘텐츠 제작자들에 의해 만들어졌다.",
    answer="It had been made by content creators who sought people's attention."),
  ]),
 topic="조회수와 돈을 노린 제작자들이 만든 운동선수 사망 오보와, 그것을 비판했던 Gina가 이번엔 스스로 오보를 퍼뜨린 대조.",
 stance="부정적·비판적",
 stance_reason="관심과 돈을 위해 자극적 거짓을 만든 제작자를 비판하고 가짜 뉴스의 해악을 지적한다.",
 structure="비교·대조",
 structure_reason="'At that time(비판하던 과거)'과 'This time, however(스스로 퍼뜨린 현재)'를 대조한다.",
 restatement_chains=[
  RestatementChain(label="돈을 노린 가짜 뉴스",
   expressions=["provocative false stories","to make money"],
   variation="'자극적 거짓 이야기'가 결국 '돈을 벌기 위한' 수단으로 드러난다."),
 ],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1",summary="그 일이 얼마 전의 또 다른 가짜 뉴스 [[사건]]을 떠올리게 한다."),
  FlowBlock(stage="사례",sentence_range="2",summary="유명 운동선수 사망 뉴스가 화제 1위였으나 [[가짜]]로 밝혀졌다."),
  FlowBlock(stage="원인",sentence_range="3~4",summary="관심과 [[돈]]을 노린 제작자들이 조회수를 올리려 거짓 이야기를 만들었다."),
  FlowBlock(stage="대조",sentence_range="5",summary="그때 Gina는 사람들을 해친 가짜 뉴스 제작자들을 [[비난]]했다."),
  FlowBlock(stage="반전",sentence_range="6",summary="그러나 이번엔 Gina 자신이 뜻하지 않게 확산에 [[기여]]했다."),
 ],
)

i2 = [
 S(r2,1,
  [("관계대명사 that","incident를 수식하는 주격 that절"),("과거완료","had happened: 지금보다 앞선 '얼마 전' 사건")],
  [("remind A of B","A에게 B를 떠올리게 하다"),("incident","사건"),("a while ago","얼마 전에")],
  [("It [[reminded]] her","그것은 그녀에게 [[떠올리게 했다]]"),
   ("of another [[incident]] of fake news","가짜 뉴스의 또 다른 [[사건]]을"),
   ("that had [[happened]] a while ago.","얼마 전에 [[일어났던]].")],
  [("(지칭) It은 흔들바위 그 바위 자체를 가리킨다.","It은 앞 문단에서 Gina가 가짜 뉴스를 퍼뜨려 당황했던 '그 일(경험)'을 가리켜, 그 경험이 또 다른 사건을 떠올리게 한 거야."),
   ("Gina가 얼마 전에 겪은 즐거운 추억을 떠올렸다는 내용이다.","another incident of fake news는 '또 다른 가짜 뉴스 사건'으로, 즐거운 추억이 아니라 과거의 오보를 떠올린 거야.")]),
 S(r2,2,
  [("동격 that","The news = that a famous athlete had died(뉴스의 내용)"),("과거완료","had died: 화제가 되기 이전의 (거짓) 사망"),("turn out to be","알고 보니 ~이다")],
  [("athlete","운동선수"),("issue","이슈, 화제"),("turn out","(결국) ~로 밝혀지다")],
  [("The news that a famous [[athlete]] had died","유명한 [[운동선수]]가 죽었다는 뉴스가"),
   ("became the number one [[issue]] online,","온라인에서 [[화제]] 1위가 되었지만,"),
   ("but it [[turned out]] to be fake.","[[알고 보니]] 가짜였다.")],
  [("(함축) 유명 운동선수가 실제로 사망했다는 뜻이다.","'it turned out to be fake(알고 보니 가짜였다)'로 보아 사망 뉴스는 거짓 — 실제로 죽은 게 아니야."),
   ("(지칭) but 뒤의 it은 the number one issue를 가리킨다.","it은 '운동선수가 죽었다는 뉴스'를 가리켜, 그 뉴스가 가짜로 밝혀졌다는 뜻이야.")]),
 S(r2,3,
  [("과거완료 수동태","had been made: 그 전에 이미 '만들어져' 있었다"),("관계대명사 who","content creators를 수식")],
  [("content creator","콘텐츠 제작자"),("seek","좇다, 추구하다"),("attention","관심")],
  [("It had been [[made]]","그것은 [[만들어졌다(만들어져 있었다)]]"),
   ("by content [[creators]]","[[콘텐츠 제작자들]]에 의해"),
   ("who [[sought]] people's attention.","사람들의 관심을 [[좇는]].")],
  [("(지칭) It은 유명 운동선수를 가리킨다.","It은 앞 문장의 '운동선수 사망 뉴스(가짜 뉴스)'를 가리켜, 그 가짜 뉴스가 제작자들에 의해 만들어졌다는 뜻이야."),
   ("제작자들이 사람들을 도우려고 뉴스를 만들었다는 내용이다.","who sought people's attention은 '관심을 좇았다'는 뜻으로, 돕기 위해서가 아니라 관심을 끌려고 만든 거야.")]),
 S(r2,4,
  [("to부정사(목적)","to make money: 돈을 벌기 위해"),("by -ing","by raising ~: ~함으로써(수단)")],
  [("provocative","자극적인, 도발적인"),("false","거짓의"),("views","조회수"),("post","게시물")],
  [("They produced [[provocative]] false stories","그들은 [[자극적인]] 거짓 이야기를 만들었다"),
   ("to make [[money]]","[[돈]]을 벌기 위해"),
   ("by raising the number of [[views]] of their posts.","자기 게시물의 [[조회수]]를 올려서.")],
  [("(함축) 그들은 좋은 정보를 알리려고 이야기를 만들었다는 뜻이다.","to make money by raising ~ views로 보아 목적은 조회수를 올려 돈을 버는 것 — 선의가 아니야."),
   ("그들이 만든 것은 사실에 근거한 뉴스였다는 내용이다.","provocative false stories는 '자극적인 거짓 이야기'로, 사실이 아니라 지어낸 이야기야.")]),
 S(r2,5,
  [("관계대명사 who","those who ~: ~한 사람들"),("과거완료","had made/spread, had hurt: 비난하던 시점 이전의 일"),("병렬 구조","made and spread / hurt and confused")],
  [("criticize","비난하다"),("confuse","혼란스럽게 하다"),("those who","~한 사람들")],
  [("At that [[time]],","그 [[때]]에는,"),
   ("Gina [[criticized]] those","Gina는 그 사람들을 [[비난했다]]"),
   ("who had made and [[spread]] fake news","가짜 뉴스를 만들고 [[퍼뜨린]]"),
   ("because it had hurt the athlete and [[confused]] people.","그것이 운동선수를 다치게 하고 사람들을 [[혼란스럽게 했기]] 때문에.")],
  [("(지칭) those who ~는 Gina 자신을 가리킨다.","those who had made and spread fake news는 '가짜 뉴스를 만들고 퍼뜨린 사람들'로, 그때 Gina는 그들을 비난한 것이지 자신을 가리키는 게 아니야."),
   ("(함축) Gina는 가짜 뉴스가 무해하다고 여겼다는 뜻이다.","because it had hurt the athlete and confused people로 보아 Gina는 가짜 뉴스가 해롭다고 봤기에 비난한 거야.")]),
 S(r2,6,
  [("재귀대명사 강조","herself: 'Gina 자신이'를 강조"),("과거완료","had contributed: 이번 일에 이미 기여함"),("대조 연결어","however: 앞의 '그때'와 대조")],
  [("accidentally","뜻하지 않게, 우연히"),("contribute to","~에 기여하다"),("spread","확산")],
  [("This time, [[however]],","[[그러나]] 이번에는,"),
   ("Gina herself had [[accidentally]] contributed","Gina 자신이 [[뜻하지 않게]] 기여했다"),
   ("to the [[spread]] of fake news.","가짜 뉴스의 [[확산]]에.")],
  [("(함축) Gina가 일부러 가짜 뉴스를 퍼뜨렸다는 뜻이다.","accidentally(뜻하지 않게) contributed로 보아 고의가 아니라 실수로 확산에 기여한 거야."),
   ("(지칭) This time은 과거 운동선수 사망 오보 사건을 가리킨다.","This time은 지금 Gina가 흔들바위 오보를 퍼뜨린 '이번 일'을 가리켜, 과거의 'At that time'과 대조돼.")]),
]

P2 = build("Warning: Fake News Alert! ②","도입 · 2 (운동선수 사망 오보)",r2,ov2,i2)

PARTS = [P1, P2]
