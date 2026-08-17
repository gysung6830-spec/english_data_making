# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_YBM_박준언_1과")
from _helpers import *

# ============================================================
# P3 · 영향 · 1 (가짜뉴스의 정의와 해악)
# ============================================================
r3 = [
 "Unfortunately, becoming an accidental distributor of fake news like Gina is not unusual.",
 "Fake news is a deliberate attempt to manipulate people by spreading inaccurate information.",
 "It is made by certain groups with the intention of attracting people's attention, making profits, or gaining political benefits.",
 "It can confuse people, disturb society, and even seriously harm the public as well as all individuals involved.",
]

ov3 = Overview(
 theme_ko="가짜뉴스의 정의와 그 해악",
 key_grammar=KeyGrammar(
  point="동명사 주어 (동명사구가 문장의 주어)",
  source_sentence="Unfortunately, becoming an accidental distributor of fake news like Gina is not unusual.",
  explanation=[
   GN("쉽게 말하면","'becoming ~'처럼 -ing로 시작하는 동명사구가 문장의 [[주어]] 자리에 왔어."),
   GN("동사 수일치","동명사 주어는 [[단수]] 취급 — 그래서 뒤 동사가 'is'야."),
   GN("핵심","주어는 'becoming an accidental distributor of fake news like Gina' 전체, 서술어는 [[is not unusual]]."),
   GN("해석","'~가 되는 [[것]]은 …이다'로 명사처럼 풀어."),
  ],
  example_analysis="becoming ... like Gina(동명사구 주어) + is not unusual(서술어).",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'becoming an accidental distributor of fake news like Gina'의 문장 내 역할은?",
    options=["주어","목적어","보어"],answer="주어"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="다음 중 동명사가 '주어'로 쓰인 것은?",
    options=["Reading books is fun.","I enjoy reading books.","She is reading books."],
    answer="Reading books is fun."),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸: '____ early is good for health.'(일찍 일어나는 것)",
    options=["Waking up","Wake up","Woke up"],answer="Waking up"),
   GrammarDrill(kind="영작",from_passage=False,
    question="친구를 돕는 것은 중요하다.",answer="Helping friends is important."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) Gina처럼 가짜뉴스의 뜻하지 않은 유포자가 되는 것은 드문 일이 아니다.",
    answer="Becoming an accidental distributor of fake news like Gina is not unusual."),
  ]),
 topic="가짜뉴스의 정의와 그것이 개인·사회에 끼치는 해악.",
 stance="부정적·비판적",
 stance_reason="가짜뉴스를 '의도적 조작'으로 규정하고 혼란·피해를 강조한다.",
 structure="주장→근거·예시",
 structure_reason="가짜뉴스의 정의(주장) → 제작 목적·해악(근거)으로 전개.",
 restatement_chains=[
  RestatementChain(label="가짜뉴스의 해로움",
   expressions=["a deliberate attempt to manipulate people","seriously harm the public"],
   variation="'조종하려는 의도적 시도' → '대중에게 심각한 해'로 이어진다."),
 ],
 flow_blocks=[
  FlowBlock(stage="도입",sentence_range="1",summary="Gina처럼 우연한 [[유포자]]가 되는 일은 흔하다."),
  FlowBlock(stage="정의",sentence_range="2~3",summary="가짜뉴스는 사람을 조종하려는 [[의도적]] 조작이며 특정 집단이 이득을 위해 만든다."),
  FlowBlock(stage="결과",sentence_range="4",summary="개인과 사회 모두에 [[해악]]을 끼친다."),
 ],
)

i3 = [
 S(r3,1,
  [("동명사 주어","becoming ~ = '~가 되는 것'이 문장 주어"),("이중부정","not unusual = 드물지 않다 → 흔하다")],
  [("distributor","유포자"),("unusual","드문·특이한")],
  [("Unfortunately, becoming [[an accidental distributor]] of fake news like Gina","불행히도, Gina처럼 가짜뉴스의 [[뜻하지 않은 유포자]]가 되는 것은"),
   ("is [[not unusual]].","[[드문 일이 아니다]].")],
  [("Gina가 일부러 가짜뉴스를 퍼뜨린 사람이라는 뜻이다.","'accidental distributor(뜻하지 않은 유포자)'이므로 Gina는 의도 없이 우연히 퍼뜨린 사람이야 — 고의가 아니다."),
   ("'not unusual'은 그런 일이 거의 없다는 뜻이다.","'not unusual(드물지 않다)'은 이중부정으로 '실제로는 매우 흔하다'는 속뜻이야 — 드물다는 게 아니야. (함축)")]),
 S(r3,2,
  [("to부정사 형용사적 용법","attempt to manipulate = 조종하려는 시도"),("동명사(전치사 뒤)","by spreading = 퍼뜨림으로써")],
  [("deliberate","의도적인"),("manipulate","조종하다"),("inaccurate","부정확한")],
  [("Fake news is [[a deliberate attempt]]","가짜뉴스는 [[의도적인 시도]]이다"),
   ("to [[manipulate]] people","사람들을 [[조종하려는]]"),
   ("by spreading [[inaccurate information]].","[[부정확한 정보]]를 퍼뜨림으로써.")],
  [("가짜뉴스는 실수로 잘못된 정보가 섞인 것이다.","'a deliberate attempt(의도적인 시도)'라 했으니 우연한 실수가 아니라 사람을 조종하려는 고의적 행위야.")]),
 S(r3,3,
  [("수동태","is made by ~ = ~에 의해 만들어진다"),("병렬 동명사","attracting ~, making ~, or gaining ~ 나열")],
  [("intention","의도"),("profit","이익"),("political","정치적")],
  [("It is [[made]] by certain groups","그것은 특정 집단에 의해 [[만들어진다]]"),
   ("with the intention of [[attracting people's attention]],","[[사람들의 관심을 끌려는]] 의도로,"),
   ("[[making profits]],","[[이익을 내거나]],"),
   ("or [[gaining political benefits]].","또는 [[정치적 이익을 얻으려는]] 것이다.")],
  [("여기서 It은 앞 문장의 Gina를 가리킨다.","It은 앞 문장의 'Fake news(가짜뉴스)'를 가리켜 — 가짜뉴스가 특정 집단에 의해 만들어진다는 뜻이야. (지칭)"),
   ("가짜뉴스는 대중의 이익을 위해 만들어진다.","관심 끌기·돈벌이·정치적 이득이 목적이라 했으니 대중을 위한 게 아니라 만든 집단의 이득이 목적이야.")]),
 S(r3,4,
  [("병렬 동사","confuse ~, disturb ~, and harm ~ 나열"),("B as well as A","the public as well as all individuals = 개인뿐 아니라 대중도")],
  [("disturb","어지럽히다"),("individual","개인"),("involved","관련된")],
  [("It can [[confuse people]],","그것은 사람들을 [[혼란스럽게 하고]],"),
   ("[[disturb society]],","[[사회를 어지럽히며]],"),
   ("and even seriously [[harm]] the public","심지어 대중을 심각하게 [[해칠]] 수도 있다"),
   ("as well as [[all individuals involved]].","[[관련된 모든 개인]]뿐만 아니라.")],
  [("가짜뉴스는 개인에게만 피해를 준다.","'the public as well as all individuals(개인뿐 아니라 대중도)'라 했으니 개인은 물론 사회 전체에 해를 끼쳐.")]),
]

P3 = build("The Impact of Fake News ①","영향 · 1 (가짜뉴스의 정의와 해악)",r3,ov3,i3)

# ============================================================
# P4 · 영향 · 2 (비상사태 확산·암본 지진)
# ============================================================
r4 = [
 "It is very common for fake news to spread during states of emergency.",
 "For example, after an earthquake measuring 6.5 struck Ambon, Indonesia, in September 2019, thousands of residents did not return to their homes and were still in shelters for two weeks.",
 "This was because of fake news stories on social media that another earthquake followed by a tsunami was about to strike.",
 "One of those messages said, \"It's up to you if you want to believe me or not, but apparently Ambon is going to sink in the next few days.\"",
 "Many displaced people were so anxious about aftershocks that the government had to announce that the information was fake.",
]

ov4 = Overview(
 theme_ko="비상사태 속 가짜뉴스의 확산 (암본 지진 사례)",
 key_grammar=KeyGrammar(
  point="so ~ that 구문 (너무 …해서 ~하다)",
  source_sentence="Many displaced people were so anxious about aftershocks that the government had to announce that the information was fake.",
  explanation=[
   GN("쉽게 말하면","'so + 형용사/부사 + that + 절'은 '너무 ~해서 …하다'라는 [[원인·결과]] 구문이야."),
   GN("형태","so 뒤엔 형용사/부사, that 뒤엔 [[결과]]를 나타내는 완전한 절이 와."),
   GN("여기선","so anxious ~ that the government had to announce = 너무 [[불안해서]] 정부가 발표해야 했다."),
   GN("주의","이때 that은 '~것'이 아니라 [[결과]]를 잇는 접속사야."),
  ],
  example_analysis="so anxious about aftershocks(원인) that the government had to announce(결과).",
  drills=[
   GrammarDrill(kind="객관식",from_passage=True,
    question="지문 'so anxious about aftershocks that the government had to announce'이 나타내는 의미 관계는?",
    options=["원인과 결과","비교","조건"],answer="원인과 결과"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="빈칸: 'He was ___ tired ___ he fell asleep.'(너무 피곤해서 잠들었다)",
    options=["so ~ that","such ~ that","too ~ to"],answer="so ~ that"),
   GrammarDrill(kind="객관식",from_passage=False,
    question="다음 중 'so ~ that' 구문이 바르게 쓰인 것은?",
    options=["It was so hot that we stayed inside.","It was such a hot day.","It was too hot to play."],
    answer="It was so hot that we stayed inside."),
   GrammarDrill(kind="영작",from_passage=False,
    question="그 영화는 너무 지루해서 나는 잠이 들었다.",answer="The movie was so boring that I fell asleep."),
   GrammarDrill(kind="영작",from_passage=True,
    question="(지문) 많은 이재민들이 너무 불안한 나머지 정부가 그 정보가 가짜라고 발표해야 했다.",
    answer="Many displaced people were so anxious that the government had to announce that the information was fake."),
  ]),
 topic="비상사태 때 가짜뉴스가 퍼지는 현상과 2019년 인도네시아 암본 지진 사례.",
 stance="부정적·비판적",
 stance_reason="가짜뉴스가 불러온 공포·혼란을 사례로 들어 그 위험성을 비판한다.",
 structure="주장→근거·예시",
 structure_reason="비상사태 때 가짜뉴스가 흔하다는 주장 → 암본 지진 사례로 뒷받침.",
 restatement_chains=[
  RestatementChain(label="비상사태 속 가짜뉴스",
   expressions=["fake news to spread during states of emergency","fake news stories on social media"],
   variation="'비상사태 때 퍼지는 가짜뉴스' → '소셜 미디어의 가짜뉴스 이야기'로 구체화된다."),
 ],
 flow_blocks=[
  FlowBlock(stage="주장",sentence_range="1",summary="[[비상사태]] 때 가짜뉴스가 잘 퍼진다."),
  FlowBlock(stage="사례",sentence_range="2~3",summary="2019 암본 지진 후 [[쓰나미]] 괴담에 주민들이 집에 못 돌아갔다."),
  FlowBlock(stage="확산",sentence_range="4",summary="'[[암본이 가라앉는다]]'는 메시지가 돌았다."),
  FlowBlock(stage="결말",sentence_range="5",summary="불안이 커져 정부가 [[가짜]]라고 발표했다."),
 ],
)

i4 = [
 S(r4,1,
  [("가주어·진주어","It ~ to spread = to부정사가 진주어"),("의미상 주어 for","for fake news = to부정사의 주체")],
  [("emergency","비상사태"),("spread","퍼지다")],
  [("It is very [[common]]","(그것은) 매우 [[흔한]] 일이다"),
   ("for fake news to [[spread]]","가짜뉴스가 [[퍼지는]] 것은"),
   ("during [[states of emergency]].","[[비상사태]] 동안.")],
  [("가짜뉴스는 비상사태 때만 만들어진다는 뜻이다.","비상사태 '동안 퍼지는(spread during ~)' 일이 흔하다는 뜻이야 — 그때만 만들어진다는 말은 아니야.")]),
 S(r4,2,
  [("현재분사 수식","an earthquake measuring 6.5 = 규모를 나타내는 분사"),("병렬 구조","did not return ~ and were still ~ 나열")],
  [("earthquake","지진"),("resident","주민"),("shelter","대피소")],
  [("For example, after an earthquake [[measuring 6.5]]","예를 들어, [[규모 6.5의]] 지진이"),
   ("struck [[Ambon, Indonesia]], in September 2019,","2019년 9월 [[인도네시아 암본을]] 강타한 뒤,"),
   ("thousands of residents [[did not return]] to their homes","수천 명의 주민이 집으로 [[돌아가지 않았고]]"),
   ("and were still [[in shelters for two weeks]].","[[2주 동안 대피소에 머물렀다]].")],
  [("주민들은 지진으로 집이 무너져 대피소에 머물렀다.","집이 무너져서가 아니라 '또 지진·쓰나미가 온다'는 가짜뉴스가 두려워 돌아가지 않은 거야(뒤 문장 근거).")]),
 S(r4,3,
  [("동격·관계 that","stories that ~ = 어떤 이야기인지 설명"),("과거분사 수식","followed by a tsunami = 쓰나미가 뒤따르는")],
  [("tsunami","쓰나미"),("strike","강타하다")],
  [("This was [[because of]] fake news stories","이것은 가짜뉴스 이야기 [[때문이었다]]"),
   ("on [[social media]]","[[소셜 미디어]]에 올라온"),
   ("that another earthquake [[followed by a tsunami]]","또 다른 지진이 [[쓰나미를 동반해]]"),
   ("was about to [[strike]].","곧 [[닥칠 것이라는]].")],
  [("This는 지진 그 자체를 가리킨다.","This는 앞 문장 내용, 즉 '주민들이 집에 안 돌아가고 대피소에 머문 일'을 가리켜 — 지진 자체가 아니야. (지칭)"),
   ("주민들이 대피한 건 실제로 쓰나미가 왔기 때문이다.","쓰나미가 온다는 '가짜뉴스(fake news stories)' 때문이었어 — 실제로 온 게 아니야.")]),
 S(r4,4,
  [("직접 인용","said, \"...\" = 실제 말을 그대로 인용"),("It's up to you","'~하는 것은 네게 달렸다'")],
  [("apparently","보아하니"),("sink","가라앉다")],
  [("One of [[those messages]] said,","그 [[메시지들]] 중 하나는 말했다,"),
   ("\"It's up to you if you want to [[believe]] me or not,","\"나를 [[믿을지 말지는]] 네게 달렸지만,"),
   ("but apparently Ambon is going to [[sink]]","하지만 보아하니 암본은 곧 [[가라앉을]]"),
   ("in the [[next few days]].\"","[[며칠]] 안에 그럴 것이다.\"")],
  [("those messages는 정부의 공식 발표를 가리킨다.","those messages는 소셜 미디어에 퍼진 '가짜뉴스 메시지'를 가리켜 — 공식 발표가 아니야. (지칭)"),
   ("암본이 실제로 곧 가라앉는다는 사실을 전한 것이다.","'apparently(보아하니)'가 붙은 소문일 뿐 사실이 아니야 — 뒤에서 정부가 '가짜'라고 밝혀. (함축)")]),
 S(r4,5,
  [("so ~ that 구문","너무 …해서 ~하다(원인·결과)"),("동격 that","announce that ~ = ~라고 발표하다")],
  [("displaced","집을 잃은"),("anxious","불안한"),("aftershock","여진"),("announce","발표하다")],
  [("Many [[displaced people]] were","많은 [[이재민들]]은"),
   ("so [[anxious about aftershocks]]","[[여진을 너무 걱정한 나머지]]"),
   ("that the government had to [[announce]]","정부는 [[발표해야 했다]]"),
   ("that the information was [[fake]].","그 정보가 [[가짜라고]].")],
  [("사람들이 여진을 걱정하지 않아 정부가 나섰다.","'so anxious ~ that(너무 걱정한 나머지)'이라 했으니 주민들이 몹시 불안해했고, 그래서 정부가 발표한 거야."),
   ("정부는 그 정보가 사실이라고 발표했다.","'the information was fake(그 정보는 가짜)'라고 발표했어 — 사실이 아니라 가짜임을 알린 거야.")]),
]

P4 = build("The Impact of Fake News ②","영향 · 2 (비상사태 확산·암본 지진)",r4,ov4,i4)

PARTS = [P3, P4]
