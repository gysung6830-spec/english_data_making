# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_능률_민병천_1과")
from _helpers import *

# =====================================================================
# P3 — 조난 · 2 (약한 신호로 보낸 구조 요청) · "Rescue ③ 구조 요청"
# key_grammar: 독립부정사 관용표현 (To make matters worse)
# =====================================================================
r3 = [
 "Compean was deep in the forest, so his cell phone couldn't get a signal.",
 "To make matters worse, its battery was nearly dead.",
 "He climbed up to a higher spot and found a weak signal.",
 "He used the last of his battery to send a text message to his friend.",
 "In the message, he said that he was lost and needed help.",
 "He also sent a picture to show his surroundings.",
 "Compean's friend shared the message and the picture with the local police.",
]

ov3 = Overview(
 theme_ko="약한 신호로 보낸 구조 요청",
 key_grammar=KeyGrammar(
  point="독립부정사 관용표현 (To make matters worse: 설상가상으로)",
  source_sentence="To make matters worse, its battery was nearly dead.",
  explanation=[
   GN("쉽게 말하면","'To make matters worse'는 문장 전체를 꾸미는 [[독립부정사]] 관용표현으로 '설상가상으로'라는 뜻."),
   GN("독립부정사","주어와 상관없이 문장 앞에 붙어 부사처럼 쓰이는, 굳어진 [[to부정사]] 표현이야."),
   GN("같은 표현","to be honest(솔직히), to begin with(우선), so to speak([[말하자면]]) 도 같은 부류."),
   GN("해석 요령","콤마로 끊고 '[[설상가상으로]]'라고 통으로 해석하면 자연스러움."),
  ],
  example_analysis="To make matters worse = 주절과 별개로 문장 전체를 꾸미는 독립부정사(부사적 관용구).",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'To make matters worse'의 뜻으로 알맞은 것은?",
    options=["설상가상으로","솔직히 말하면","우선 첫째로"],answer="설상가상으로"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 들어갈 관용표현은? '____, it started to rain.'(설상가상으로)",
    options=["To make matters worse","Making matters worse","Made matters worse"],
    answer="To make matters worse"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="'솔직히 말하면'을 뜻하는 독립부정사 관용표현은?",
    options=["to be honest","to make matters worse","to begin with"],answer="to be honest"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 설상가상으로, 그것의 배터리는 거의 다 됐다.",
    answer="To make matters worse, its battery was nearly dead."),
   GrammarDrill(kind="영작",from_passage=False,
    question="설상가상으로, 비가 내리기 시작했다.",
    answer="To make matters worse, it started to rain."),
  ]),
 topic="숲속에서 조난당한 Compean이 약한 신호로 친구에게 구조를 요청하는 과정.",
 stance="중립적",stance_reason="사건 경과를 시간 순서로 전하는 보도 부분.",
 structure="시간·순서(나열)",structure_reason="신호 없음→높은 곳→문자·사진→경찰 공유의 시간 흐름.",
 restatement_chains=[RestatementChain(label="구조 요청 전달",
   expressions=["send a text message to his friend",
    "shared the message and the picture with the local police"],
   variation="'친구에게 문자' → '친구가 경찰과 공유'로 도움 요청이 전달됨.")],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1~2",summary="숲 깊은 곳이라 [[신호]]가 없고 배터리도 거의 방전됨."),
  FlowBlock(stage="전개",sentence_range="3~4",summary="높은 곳에서 약한 신호를 잡아 마지막 배터리로 [[문자]]를 보냄."),
  FlowBlock(stage="전개",sentence_range="5~6",summary="길을 잃었다는 메시지와 [[주변]] 사진을 함께 보냄."),
  FlowBlock(stage="전환",sentence_range="7",summary="친구가 메시지와 사진을 지역 [[경찰]]과 공유함."),
 ])

i3 = [
 S(r3,1,[("결과 접속사 so","'그래서 ~하다'로 앞의 원인에 대한 결과를 이음")],
  [("signal","신호")],
  [("Compean was [[deep in the forest]],","Compean은 [[숲속 깊이]] 있었다,"),
   ("so his cell phone couldn't [[get a signal]].","그래서 그의 휴대폰은 [[신호를 잡지]] 못했다.")],
  [("Compean이 신호를 못 잡은 건 휴대폰이 고장 났기 때문이다.",
    "고장이 아니라 'deep in the forest(숲속 깊이)' 있어서 신호가 안 잡힌 거야 — 위치가 원인.")]),
 S(r3,2,[("독립부정사 관용표현","To make matters worse = '설상가상으로'(문장 전체 수식)")],
  [("nearly","거의"),("dead","(배터리가) 다 된")],
  [("[[To make matters worse]],","[[설상가상으로]],"),
   ("its battery was [[nearly dead]].","그것의 배터리는 [[거의 다 됐다]].")],
  [("'its battery'의 its는 숲(forest)을 가리킨다.",
    "its는 앞 문장의 'his cell phone(그의 휴대폰)'을 가리켜 — 휴대폰의 배터리라는 뜻."),
   ("배터리가 거의 다 됐다는 건 아직 여유가 많다는 뜻이다.",
    "'nearly dead(거의 방전)'라 시간이 얼마 없다는 속뜻 — 상황이 더 나빠졌다는 함축이야.")]),
 S(r3,3,[("비교급 higher","'더 높은' + 병렬 동사 climbed ~ and found")],
  [("spot","장소, 지점"),("weak","약한")],
  [("He climbed up to [[a higher spot]]","그는 [[더 높은 곳]]으로 올라가서"),
   ("and found [[a weak signal]].","[[약한 신호]]를 찾았다.")],
  [("그는 신호를 찾으려 산을 내려갔다.",
    "반대야 — 'climbed up to a higher spot(더 높은 곳으로 올라감)'해서 약한 신호를 잡은 거야.")]),
 S(r3,4,[("부사적 to부정사","to send = '보내기 위해'(목적)")],
  [("last","마지막"),("text message","문자 메시지")],
  [("He used [[the last of his battery]]","그는 [[배터리의 마지막까지]] 써서"),
   ("to send a [[text message]] to his friend.","친구에게 [[문자 메시지]]를 보냈다.")],
  [("그는 배터리를 아끼려고 문자를 보내지 않았다.",
    "'used the last of his battery to send a text(마지막 배터리로 문자를 보냄)' — 아낀 게 아니라 다 써서 보낸 거야.")]),
 S(r3,5,[("명사절 that","said의 목적어 절 + 병렬 was lost and needed")],
  [("said","말했다"),("lost","길을 잃은")],
  [("In the message, he [[said]]","그 메시지에서, 그는 [[말했다]]"),
   ("that he [[was lost]] and needed help.","그가 [[길을 잃었고]] 도움이 필요하다고.")],
  [("그는 자신이 길을 잘 알고 있다고 전했다.",
    "반대야 — 'he was lost and needed help(길을 잃었고 도움이 필요)'라고 했어.")]),
 S(r3,6,[("부사적 to부정사","to show = '보여주기 위해'(목적)")],
  [("picture","사진"),("surroundings","주변 환경")],
  [("He also sent a [[picture]]","그는 또한 [[사진]]을 보냈다"),
   ("to show his [[surroundings]].","그의 [[주변 환경]]을 보여주기 위해.")],
  [("그는 자기 얼굴을 찍은 셀카를 보냈다.",
    "얼굴이 아니라 'to show his surroundings(주변 환경을 보여주려)' 사진을 보낸 거야.")]),
 S(r3,7,[("share A with B","'B에게 A를 공유하다' + 병렬 목적어 the message and the picture")],
  [("shared","공유했다"),("local police","지역 경찰")],
  [("Compean's friend [[shared]]","Compean의 친구는 [[공유했다]]"),
   ("the [[message and the picture]]","그 [[메시지와 사진]]을"),
   ("with the [[local police]].","지역 [[경찰]]에게.")],
  [("친구가 사진을 인터넷에 올려 널리 퍼뜨렸다.",
    "인터넷이 아니라 'shared ~ with the local police(지역 경찰과 공유)'했어 — 신고한 거야.")]),
]

P3 = build("Rescue ③ 구조 요청","조난 · 2 (약한 신호로 보낸 구조 요청)",r3,ov3,i3)

# =====================================================================
# P4 — 수색 · 1 (경찰 수색의 난관) · "Rescue ④ 수색 난관"
# key_grammar: 전치사 despite + 동명사
# =====================================================================
r4 = [
 "When the local police were informed of the missing hiker, they immediately sent a rescue team.",
 "Despite searching through the night, they still didn't have any idea where Compean was.",
 "In the picture, his legs were hanging over the edge of a canyon with rocks and green trees.",
 "His legs were covered in black ash from the recent forest fires.",
 "However, the picture didn't help the police much because the quality was poor due to the weak signal, and his location settings were turned off.",
]

ov4 = Overview(
 theme_ko="경찰 수색의 난관",
 key_grammar=KeyGrammar(
  point="전치사 despite + 동명사 (~에도 불구하고)",
  source_sentence="Despite searching through the night, they still didn't have any idea where Compean was.",
  explanation=[
   GN("쉽게 말하면","despite는 [[전치사]]라서 뒤에 명사나 [[동명사(-ing)]]가 오고 '~에도 불구하고'라는 뜻."),
   GN("주의","despite 뒤에는 '주어+동사'의 절이 [[올 수 없다]] — 접속사 although와 헷갈리지 말 것."),
   GN("바꿔쓰기","Despite searching ~ = [[Although]] they searched ~ (접속사+절)."),
   GN("같은 뜻","in spite of + 동명사도 [[같은]] 뜻으로 쓸 수 있어."),
  ],
  example_analysis="Despite searching = 전치사 despite + 동명사 searching(양보 부사구).",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'Despite searching through the night'에서 despite 뒤에 온 형태는?",
    options=["동명사(searching)","동사원형(search)","절(they searched)"],
    answer="동명사(searching)"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 것은? 'Despite ____ hard, he failed.'",
    options=["trying","he tried","to try"],answer="trying"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="despite와 바꿔 쓸 수 있는 접속사는? (뒤에 절이 옴)",
    options=["Although","Because","Therefore"],answer="Although"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 밤새 수색했음에도, 그들은 여전히 Compean이 어디 있는지 전혀 알지 못했다.",
    answer="Despite searching through the night, they still didn't have any idea where Compean was."),
   GrammarDrill(kind="영작",from_passage=False,
    question="열심히 노력했음에도, 그는 시험에 떨어졌다.",
    answer="Despite trying hard, he failed the exam."),
  ]),
 topic="경찰이 밤새 수색했지만 사진의 결함 탓에 실종자 위치를 못 찾은 난관.",
 stance="중립적",stance_reason="수색 과정과 사진의 문제점을 사실 그대로 전하는 보도 부분.",
 structure="시간·순서(나열)",structure_reason="신고 접수→밤샘 수색→사진 분석→도움 안 됨의 시간 흐름.",
 restatement_chains=[RestatementChain(label="수색의 난관",
   expressions=["didn't have any idea where Compean was",
    "the picture didn't help the police much"],
   variation="'위치를 전혀 모름' → '사진도 도움이 안 됨'으로 난관이 이어짐.")],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1",summary="경찰이 실종 신고를 받고 즉시 [[구조팀]]을 보냄."),
  FlowBlock(stage="전개",sentence_range="2",summary="밤새 수색했지만 위치를 [[전혀]] 알아내지 못함."),
  FlowBlock(stage="사례",sentence_range="3~4",summary="사진 속 다리는 협곡 가장자리에 걸쳐 있고 검은 [[재]]로 덮임."),
  FlowBlock(stage="결론",sentence_range="5",summary="나쁜 화질과 꺼진 [[위치 설정]] 탓에 사진이 큰 도움이 안 됨."),
 ])

i4 = [
 S(r4,1,[("수동태","were informed of = '~을 통보받다'"),
   ("시간 부사절 when","'~했을 때'")],
  [("informed","통보받은, 알게 된"),("rescue team","구조팀")],
  [("When the local police [[were informed of]] the missing hiker,","지역 경찰이 실종된 등산객을 [[통보받았을]] 때,"),
   ("they [[immediately]] sent","그들은 [[즉시]] 보냈다"),
   ("a [[rescue team]].","[[구조팀]]을.")],
  [("경찰은 신고를 받고도 한참 뒤에야 구조팀을 보냈다.",
    "'immediately sent a rescue team(즉시 구조팀을 보냄)'이라 지체 없이 곧바로 보낸 거야.")]),
 S(r4,2,[("전치사 despite + 동명사","Despite searching = '수색했음에도 불구하고'"),
   ("간접의문문","where Compean was = '어디 있는지'(의문사+주어+동사)")],
  [("searching","수색하기"),("idea","생각, 짐작")],
  [("Despite [[searching through the night]],","[[밤새 수색]]했음에도 불구하고,"),
   ("they still didn't have [[any idea]]","그들은 여전히 [[전혀 알지]] 못했다"),
   ("where [[Compean]] was.","[[Compean]]이 어디 있었는지를.")],
  [("'they'는 실종된 등산객 일행을 가리킨다.",
    "they는 앞 문장의 'the local police(지역 경찰/구조팀)'을 가리켜."),
   ("밤새 수색했으니 경찰은 곧 Compean을 찾아냈다.",
    "(함축) 'Despite searching(수색에도 불구하고)'와 'didn't have any idea'가 대비돼 — 애써도 못 찾았다는 속뜻이야.")]),
 S(r4,3,[("과거진행 수동적 묘사","were hanging = '걸쳐 있었다'")],
  [("hanging","걸쳐 있는, 매달린"),("canyon","협곡")],
  [("In the [[picture]],","[[사진]] 속에서,"),
   ("his legs were hanging over [[the edge of a canyon]]","그의 다리가 [[협곡 가장자리]] 너머로 걸쳐 있었다"),
   ("with [[rocks and green trees]].","[[바위와 초록 나무]]가 있는.")],
  [("사진 속 다리는 평평한 들판 위에 편히 놓여 있었다.",
    "들판이 아니라 'over the edge of a canyon(협곡 가장자리 너머)'에 걸쳐 있었어 — 위험한 위치.")]),
 S(r4,4,[("수동태","were covered in = '~로 덮여 있었다'")],
  [("ash","재"),("forest fires","산불")],
  [("His legs were covered in [[black ash]]","그의 다리는 [[검은 재]]로 덮여 있었다"),
   ("from the [[recent forest fires]].","최근 [[산불]]에서 나온.")],
  [("다리의 검은 재는 그가 직접 불을 피운 흔적이다.",
    "불을 피운 게 아니라 'from the recent forest fires(최근 산불)'에서 묻은 재야 — 산불 지역 근처에 있었다는 단서.")]),
 S(r4,5,[("이유 접속사 because","'~하기 때문에'"),
   ("수동태","were turned off = '꺼져 있었다'")],
  [("quality","화질, 품질"),("location settings","위치 설정")],
  [("However, the picture didn't [[help the police much]]","그러나, 그 사진은 [[경찰에게 큰 도움이]] 되지 못했다"),
   ("because the [[quality was poor]]","[[화질이 나빴기]] 때문이었다"),
   ("due to the [[weak signal]],","[[약한 신호]] 탓에,"),
   ("and his location settings were [[turned off]].","그리고 그의 위치 설정이 [[꺼져 있었다]].")],
  [("사진이 도움이 안 된 건 경찰이 게을러서였다.",
    "경찰 탓이 아니라 'quality was poor(화질이 나쁨)'와 'location settings were turned off(위치 설정이 꺼짐)' 두 가지가 원인이야.")]),
]

P4 = build("Rescue ④ 수색 난관","수색 · 1 (경찰 수색의 난관)",r4,ov4,i4)

PARTS = [P3, P4]
