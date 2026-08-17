# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_능률_민병천_1과")
from _helpers import *

# =====================================================================
# P7 — Rescue ⑦ 구조 (위성사진 일치와 구조)
# =====================================================================
r7 = [
 "As a final step, Kuo compared the view in Compean's picture with more satellite images.",
 "Finally, he found a match and provided the police with Compean's probable location.",
 "The police sent a rescue helicopter to the location and found Compean less than a mile away from the area indicated by Kuo.",
]

ov7 = Overview(
 theme_ko="위성사진 대조로 찾아낸 조난자의 위치",
 key_grammar=KeyGrammar(
  point="과거분사구 후치수식 (the area indicated by Kuo)",
  source_sentence="The police sent a rescue helicopter to the location and found Compean less than a mile away from the area indicated by Kuo.",
  explanation=[
   GN("쉽게 말하면","명사 뒤에 붙은 '과거분사(-ed)구'는 '~된/~해진'으로 앞 명사를 [[뒤에서]] 꾸며."),
   GN("복원","the area indicated by Kuo = the area [[which was indicated]] by Kuo."),
   GN("주의","현재분사(-ing)는 '~하는'(능동), 과거분사(-ed)는 '~된'([[수동]]) — 여기선 지역이 '가리켜진' 것."),
   GN("해석 요령","'the area / indicated by Kuo'처럼 명사에서 한 번 끊고 [[분사]]구를 뒤에 붙여 읽어."),
  ],
  example_analysis="the area indicated by Kuo = 명사 the area를 과거분사구 indicated by Kuo가 후치수식(수동).",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'the area indicated by Kuo'에서 indicated의 역할은?",
    options=["앞의 명사 the area를 수식하는 과거분사","문장의 본동사","현재분사(능동)로 the police 수식"],
    answer="앞의 명사 the area를 수식하는 과거분사"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="밑줄 친 부분이 '과거분사 후치수식'인 것은?",
    options=["the book written by him","the boy writing a letter","He wrote a book yesterday."],
    answer="the book written by him"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸에 알맞은 말: 'the message ____ by the police'(경찰이 보낸 메시지)",
    options=["sent","sending","sends"],
    answer="sent"),
   GrammarDrill(kind="영작",from_passage=False,
    question="그에 의해 찍힌 사진 (그가 찍은 사진)",
    answer="the picture taken by him"),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 경찰은 그 위치로 구조 헬리콥터를 보냈고 Kuo가 가리킨 지역에서 1마일도 안 되는 거리에서 Compean을 발견했다.",
    answer="The police sent a rescue helicopter to the location and found Compean less than a mile away from the area indicated by Kuo."),
  ]),
 topic="Kuo가 사진 장면을 위성사진과 최종 대조해 위치를 찾고 경찰이 구조하는 climax.",
 stance="중립적",stance_reason="구조에 이르는 사건 전개를 사실 위주로 보도한다.",
 structure="시간·순서(나열)",structure_reason="최종 대조 → 일치 발견·위치 통보 → 헬기 구조의 시간 순서.",
 restatement_chains=[RestatementChain(label="위치 확인",
   expressions=["Compean's probable location","the area indicated by Kuo"],
   variation="'유력한 위치' 추정 → 실제 'Kuo가 가리킨 지역'에서 구조로 이어짐.")],
 flow_blocks=[
  FlowBlock(stage="전개",sentence_range="1",summary="Kuo가 사진 속 장면을 더 많은 [[위성 사진]]과 대조한다."),
  FlowBlock(stage="전환",sentence_range="2",summary="[[일치]]점을 찾아 경찰에 유력한 위치를 알린다."),
  FlowBlock(stage="결론",sentence_range="3",summary="헬기가 그 지역 부근에서 [[Compean]]을 구조한다."),
 ])

i7 = [
 S(r7,1,
  [("compare A with B","A를 B와 비교/대조하다")],
  [("compare","비교하다"),("satellite","위성")],
  [("As a [[final step]],","[[마지막 단계]]로,"),
   ("Kuo [[compared]] the view","Kuo는 그 장면을 [[비교했다]]"),
   ("in Compean's [[picture]]","Compean의 [[사진]] 속"),
   ("with more [[satellite images]].","더 많은 [[위성 사진]]과.")],
  [("Kuo가 새로 사진을 직접 찍어 위성사진과 맞춰 보았다.","그는 Compean이 보낸 사진 속 장면(the view in Compean's picture)을 위성사진과 대조했을 뿐, 직접 촬영한 게 아니야."),
   ("'a final step'은 구조 작업의 첫 단계를 뜻한다.","final step은 여러 분석 끝의 '마지막(최종)' 확인 단계라는 뜻이야, 첫 단계가 아니야.")]),
 S(r7,2,
  [("provide A with B","A에게 B를 제공하다")],
  [("match","일치(하는 것)"),("probable","유력한, 있음직한")],
  [("Finally, he found a [[match]]","마침내, 그는 [[일치]]하는 것을 찾아냈고"),
   ("and [[provided]] the police","경찰에게 [[제공했다]]"),
   ("with Compean's [[probable location]].","Compean의 [[유력한 위치]]를.")],
  [("이 문장의 he는 경찰(the police)을 가리킨다.","he는 Kuo를 가리켜; 그가 일치점을 찾아 경찰에게 위치 정보를 넘겨준 거야. (지칭)"),
   ("probable location은 확정된 정확한 위치를 뜻한다.","probable은 '유력한(추정되는)' 위치로, 확정이 아니라 가능성이 높은 지점이야.")]),
 S(r7,3,
  [("과거분사구 후치수식","the area indicated by Kuo = the area (which was) indicated by Kuo, 앞 명사를 뒤에서 수식"),
   ("less than ~ away","'~도 안 되는 거리에서'라는 거리 표현")],
  [("rescue","구조; 구조하다"),("indicate","가리키다, 나타내다")],
  [("The police sent a [[rescue helicopter]]","경찰은 [[구조 헬리콥터]]를 보냈고"),
   ("to the [[location]]","그 [[위치]]로"),
   ("and found [[Compean]]","그리고 [[Compean]]을 발견했다"),
   ("less than a [[mile]] away","[[1마일]]도 안 되는 거리에서"),
   ("from the area [[indicated by Kuo]].","Kuo가 [[가리킨 지역]]에서.")],
  [("경찰은 Kuo가 지목한 바로 그 지점에서 정확히 Compean을 찾았다.","정확히 그 지점이 아니라 그곳에서 1마일도 안 되는 거리(less than a mile away)에서 발견했어."),
   ("'indicated by Kuo'는 Kuo가 헬리콥터를 직접 조종했다는 뜻이다.","indicated by Kuo는 'Kuo가 가리킨(지목한)' 지역을 수식하는 과거분사구로, 위치를 짚어준 것이지 헬기를 몬 게 아니야. (함축)")]),
]

P7 = build("Rescue ⑦ 구조","구조 · 1 (위성사진 일치와 구조)",r7,ov7,i7)


# =====================================================================
# P8 — Rescue ⑧ 결말·당부 (결말과 안전 당부)
# =====================================================================
r8 = [
 "Thanks to Kuo's unusual skills, Compean was rescued unharmed.",
 "He later thanked Kuo on a video call.",
 "The local police are now reminding hikers who hike alone to inform others of their planned route and to always bring a paper map.",
 "This is Marissa Reynolds from LA. Now back to the studio.",
]

ov8 = Overview(
 theme_ko="무사 구조와 단독 산행 안전 당부",
 key_grammar=KeyGrammar(
  point="remind A to-V (A에게 ~하라고 상기시키다; to부정사 병렬)",
  source_sentence="The local police are now reminding hikers who hike alone to inform others of their planned route and to always bring a paper map.",
  explanation=[
   GN("쉽게 말하면","'remind + 목적어 + to부정사'는 '~에게 …하라고 [[상기시키다/당부하다]]'."),
   GN("구조","reminding hikers ... [[to inform]] ... and to bring — 목적어 뒤 to부정사가 '당부할 내용'."),
   GN("병렬","and 뒤 to always bring이 앞의 to inform과 대등한 [[to부정사]]로 이어져."),
   GN("주의","remind 뒤엔 [[to부정사]]를 취함; 'remind A of + 명사(상기시키다)'와 구분해."),
  ],
  example_analysis="reminding hikers to inform ... and to always bring = remind A(hikers) + to부정사 병렬(inform·bring).",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문에서 'to inform others of their planned route'와 'to always bring a paper map'을 대등하게 잇는 것은?",
    options=["to inform과 to always bring","hikers와 others","route와 map"],
    answer="to inform과 to always bring"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="어법상 알맞은 것: 'The teacher reminded us ____ our homework.'",
    options=["to bring","bring","brought"],
    answer="to bring"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="'remind'의 쓰임이 어법상 바른 문장은?",
    options=["She reminded me to call him.","She reminded me call him.","She reminded me calling him."],
    answer="She reminded me to call him."),
   GrammarDrill(kind="영작",from_passage=False,
    question="그녀는 내게 문을 잠그라고 상기시켰다.",
    answer="She reminded me to lock the door."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 그는 나중에 영상 통화로 Kuo에게 감사했다.",
    answer="He later thanked Kuo on a video call."),
  ]),
 topic="무사 구조된 Compean의 감사와 경찰의 단독 산행 안전 당부, 기자 사인오프.",
 stance="부정적·비판적",stance_reason="단독 산행의 위험을 짚고 경로 공유·종이 지도 지참을 당부(경고)하는 마무리.",
 structure="문제→해결(방안)",structure_reason="혼자 산행의 위험(문제) → 경로 공유와 종이 지도 지참(해결 방안) 제시.",
 restatement_chains=[RestatementChain(label="안전 당부",
   expressions=["inform others of their planned route","always bring a paper map"],
   variation="'경로 공유'와 '종이 지도 지참' 두 안전 수칙으로 이어짐.")],
 flow_blocks=[
  FlowBlock(stage="결론",sentence_range="1",summary="Kuo의 능력 덕에 Compean이 [[무사히]] 구조된다."),
  FlowBlock(stage="전개",sentence_range="2",summary="Compean이 [[영상 통화]]로 Kuo에게 감사한다."),
  FlowBlock(stage="당부",sentence_range="3",summary="경찰이 단독 산행자에게 [[경로 공유]]와 종이 지도 지참을 당부한다."),
  FlowBlock(stage="마무리",sentence_range="4",summary="기자가 보도를 마치고 [[스튜디오]]로 넘긴다."),
 ])

i8 = [
 S(r8,1,
  [("수동태","was rescued = '구조되었다'(당하는 쪽)"),
   ("Thanks to ~","'~ 덕분에'라는 전치사구")],
  [("unusual","특이한, 흔치 않은"),("unharmed","다치지 않은")],
  [("Thanks to Kuo's [[unusual skills]],","Kuo의 [[특이한 기술]] 덕분에,"),
   ("Compean was [[rescued unharmed]].","Compean은 [[다치지 않고 구조되었다]].")],
  [("Compean은 부상을 입은 채 겨우 구조되었다.","unharmed는 '다치지 않은'이라, 무사히 구조되었다는 뜻이야. 부상당했다는 게 아니야. (함축)"),
   ("Kuo의 평범한 기술 덕분에 쉽게 구조되었다.","unusual skills는 '특이한(흔치 않은)' 기술을 뜻해, 평범한 능력이 아니라 남다른 취미 기술이야.")]),
 S(r8,2,
  [("thank A on ~","A에게 ~로 감사하다")],
  [("later","나중에"),("video call","영상 통화")],
  [("He later [[thanked]] Kuo","그는 나중에 Kuo에게 [[감사했다]]"),
   ("on a [[video call]].","[[영상 통화]]로.")],
  [("이 문장의 He는 Kuo를 가리킨다.","He는 구조된 Compean을 가리켜; 자기를 구해준 Kuo에게 고마움을 전한 거야. (지칭)"),
   ("두 사람이 직접 만나 감사 인사를 나눴다.","on a video call, 즉 영상 통화로 감사한 것이지 대면으로 만난 게 아니야.")]),
 S(r8,3,
  [("remind A to-V","remind + 목적어(hikers) + to부정사: ~에게 …하라고 당부/상기시키다"),
   ("to부정사 병렬","to inform ... and to always bring 두 to부정사가 대등 연결"),
   ("관계사절","who hike alone이 앞의 hikers를 수식")],
  [("inform","알리다"),("route","경로, 길")],
  [("The local police are now [[reminding]]","지역 경찰은 지금 [[당부하고 있다]]"),
   ("hikers who [[hike alone]]","[[혼자 산행하는]] 등산객들에게"),
   ("to inform others of their [[planned route]]","자신의 [[예정 경로]]를 다른 사람에게 알리고"),
   ("and to always bring a [[paper map]].","항상 [[종이 지도]]를 챙기라고.")],
  [("경찰이 등산객에게 절대 혼자 산에 가지 말라고 명령했다.","혼자 가는 사람에게 경로를 알리고 종이 지도를 챙기라고 '당부(reminding)'한 것이지, 단독 산행 금지 명령이 아니야. (함축·교훈)"),
   ("종이 지도는 필요 없고 휴대폰만 챙기면 된다는 뜻이다.","오히려 always bring a paper map, 즉 (전자기기가 끊길 때 대비해) 종이 지도를 꼭 챙기라는 당부야.")]),
 S(r8,4,
  [("방송 사인오프","This is ~ from LA = '지금까지 LA에서 ~였습니다'")],
  [("studio","(방송) 스튜디오")],
  [("This is [[Marissa Reynolds]] from LA.","지금까지 LA에서 [[Marissa Reynolds]]였습니다."),
   ("Now back to the [[studio]].","이제 [[스튜디오]]로 넘기겠습니다.")],
  [("'back to the studio'는 기자가 스튜디오로 돌아가 쉰다는 뜻이다.","방송에서 진행을 스튜디오의 앵커에게 넘긴다는 마무리 표현이야. (함축·지칭)"),
   ("Marissa Reynolds는 구조된 등산객의 이름이다.","Marissa Reynolds는 현장을 보도한 기자(reporter)의 이름이야; 조난자는 Compean이야. (지칭)")]),
]

P8 = build("Rescue ⑧ 결말·당부","마무리 · 1 (결말과 안전 당부)",r8,ov8,i8)

PARTS = [P7, P8]
