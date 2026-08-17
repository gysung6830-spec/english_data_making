# -*- coding: utf-8 -*-
import json
SCRATCH="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad"
U102_en=[
"Although the wish to be alone is often strong, its intensity varies from person to person.",
"An equally impelling impulse, though, is to seek the company of others and to spend extended periods of time sharing activities.",
"In these periods we exchange information and feelings in both conversational and non-verbal forms (facial expressions, eye contact, gestures, touching, and so on).",
"We need other people to provide us with love, support, approval, bodily contact, reassurance, physical help and a myriad of other practical, physical and emotional needs.",
"In a very basic sense we need others to confirm that we are there, that we exist and that we have an identity that is unique and separate from anyone else.",
"Thus, we generally cannot exist for too long without seeking companionship."]
U102_ko=[
"혼자 있고 싶은 소망은 종종 강하지만, 그 강도는 사람마다 다르다.",
"하지만 똑같이 뿌리칠 수 없는 충동은 다른 사람과 함께 있는 것을 추구하고 활동을 공유하면서 긴 시간을 보내는 것이다.",
"이 시간 동안 우리는 대화의 형태와 비언어적 형태(표정, 눈 맞춤, 몸짓, 접촉 등) 둘 다로 정보와 감정을 교환한다.",
"우리는 우리에게 사랑, 지지, 인정, 신체적 접촉, 안심, 신체적 도움, 그리고 무수히 많은 다른 실질적, 신체적, 정서적 필요사항들을 제공해 줄 다른 사람들을 필요로 한다.",
"아주 기본적인 의미에서 우리는 우리가 거기에 있고, 우리가 존재하며, 고유하면서 다른 누구와도 구별되는 정체성을 가지고 있다는 것을 확인하기 위해 다른 사람들을 필요로 한다.",
"따라서 우리는 일반적으로 교제를 추구하지 않고는 그렇게 오랫동안 살아갈 수 없다."]
U141_en=[
"Personal branding is not something that you have to do behind the scenes.",
"For many it does not always feel comfortable to deliberately plan how we are going to promote ourselves and our accomplishments to others.",
"Personal branding, however, is essential to achieving success.",
"The key takeaway from this concept is awareness and anticipation.",
"If you are not aware of the opportunities to brand yourself, you may not be directed to leave a favorable impression.",
"If you cannot anticipate the opportunities that will present themselves to favorably demonstrate your brand through capability, you may not be prepared when they occur.",
"So as you begin to think about what you want to be known for, begin to be more aware of what you want people to say about you when you are not in the room as an effective way to guide your personal brand."]
U141_ko=[
"퍼스널 브랜딩은 여러분이 남몰래 해야 하는 것이 아니다.",
"의도적으로 우리 자신과 우리의 업적을 다른 사람들에게 어떻게 홍보할지 계획하는 것이 많은 사람에게 항상 편안하게 느껴지는 것은 아니다.",
"하지만 퍼스널 브랜딩은 성공을 이루는 데 필수적이다.",
"이 개념의 주요한 핵심은 인식과 예상이다.",
"만약 자신을 눈에 띄게 할 기회를 인식하지 못한다면, 여러분은 호의적인 인상을 남기게 되지 못할 수도 있다.",
"역량을 통해 여러분의 브랜드를 호의적으로 보여 주기 위해 자신을 나타낼 기회를 예상할 수 없다면, 여러분은 기회가 생길 때 준비가 되어 있지 않은 것일지도 모른다.",
"그래서 자신이 무엇으로 알려지고 싶은지에 대해 생각을 시작할 때, 여러분의 퍼스널 브랜드를 이끌 효과적인 방법으로서 사람들이 여러분이 방에 없을 때 여러분에 대해 무엇을 말하기를 원하는지를 더 많이 인식하기 시작하라."]
U142_en=[
"The ability to detect visual movement played an interesting role in the history of astronomy.",
"In 1930, Clyde Tombaugh was searching the skies for a possible undiscovered planet beyond Neptune.",
"He photographed each region of the sky twice, several days apart.",
"Stars essentially remain unmoving in photos, while a planet moves from one photo to the next.",
"However, how would he find a small dot that moved among all the countless unmoving dots in the sky?",
"He put each pair of photos on a machine that would flip back and forth between one photo and the other.",
"When he came to one pair of photos, he immediately noticed one dot moving as the machine flipped back and forth.",
"He identified that dot as Pluto, which astronomers now list as a dwarf planet."]
U142_ko=[
"시각적 움직임을 감지하는 능력은 천문학의 역사에서 흥미로운 역할을 했다.",
"1930년에, Clyde Tombaugh는 해왕성 너머에 있을지도 모르는 미발견 행성을 찾기 위해 하늘을 탐색하고 있었다.",
"그는 하늘의 각 영역을 며칠 간격으로 두 번씩 촬영했다.",
"항성은 본질적으로 사진에서 움직이지 않는 상태로 남아 있는 반면, 행성은 한 사진에서 다음 사진으로 가면서 이동한다.",
"하지만 그가 하늘에서 움직이지 않는 수많은 점들 사이에서 움직인 하나의 작은 점을 어떻게 찾을 것인가?",
"그는 각 쌍의 사진을 한 사진과 다른 사진 사이를 앞뒤로 뒤집어주는 기계에 놓았다.",
"한 쌍의 사진에 다다랐을 때, 그는 기계가 앞뒤로 뒤집을 때 점 하나가 움직이는 것을 즉시 알아챘다.",
"그는 그 점을 명왕성으로 확인했는데, 천문학자들은 현재 그것을 왜소 행성의 목록에 포함한다."]
U143_en=[
"People are cutting down forests much faster than the rate at which forests can regrow.",
"We need to dramatically reduce our use of wood, not just because the supply is decreasing, and not just because entire species of flora and fauna that live in forests are vanishing, but because the forest performs an important function.",
"Forests control global warming by absorbing carbon from the atmosphere and reducing greenhouse gases.",
"They also provide oxygen for us to breathe.",
"There are too many trivial and shortsighted uses of wood.",
"When a hurricane advances on a city, people board up their windows with plywood.",
"After the storm has passed, they discard the plywood.",
"It's ironic to think that for purposes such as these, forests are cut down that otherwise would aid in controlling such storms."]
U143_ko=[
"사람들은 숲이 재성장할 수 있는 속도보다 훨씬 더 빠르게 숲을 베어내고 있다.",
"우리는 목재 사용을 급격하게 줄여야 하는데, 이는 공급이 감소하고 있기 때문만이 아니라, 그리고 숲에 서식하는 동식물군 전체 종이 사라지고 있기 때문만이 아니라, 숲이 중요한 기능을 수행하기 때문이다.",
"숲은 대기로부터 탄소를 흡수하고 온실 가스를 줄여 지구온난화를 억제한다.",
"그것은 또한 우리가 숨 쉴 수 있는 산소를 공급한다.",
"목재의 사소하고 근시안적인 쓰임새가 너무 많다.",
"허리케인이 도시로 다가오면 사람들은 합판으로 창문을 막는다.",
"폭풍이 지난 후에, 그들은 합판을 버린다.",
"이러한 목적을 위해 숲이 베어지는데, 그렇지 않다면 숲이 그러한 폭풍을 통제하는 데 도움이 되었으리라는 것을 생각하면 아이러니이다."]
def pack(en,ko): return [{"n":i+1,"en":en[i],"ko_gloss":ko[i]} for i in range(len(en))]
sub={
 "U102":("P1","Unit10-2","자신의 존재·정체성 확인을 위해 타인과의 교제·유대를 갈망하는 인간의 본성",
   "need + 목적어 + to부정사 (5형식: …가 ~하도록 필요로 하다)", pack(U102_en,U102_ko)),
 "U141":("P2","Unit14-1","성공을 위해 자리에 없을 때 회자될 평판을 관리하는 퍼스널 브랜딩의 중요성",
   "가주어 it - 진주어 to부정사 (It ~ to-V: …하는 것이 …하다)", pack(U141_en,U141_ko)),
 "U142":("P3","Unit14-2","사진 간 시각적 움직임 포착 기술로 이룬 Clyde Tombaugh의 명왕성 발견",
   "대조의 접속사 while (~인 반면에)", pack(U142_en,U142_ko)),
 "U143":("P4","Unit14-3","기후 조절이라는 숲의 기능을 망각한 채 이뤄지는 근시안적 목재 남용 비판",
   "가정법 otherwise (otherwise + 조동사 과거: 그렇지 않다면 ~할 텐데)", pack(U143_en,U143_ko)),
}
groups={"add1":["U102","U141"],"add2":["U142","U143"]}
for g,keys in groups.items():
    data=[{"var":sub[k][0],"item_no":sub[k][1],"title":sub[k][2],"key_grammar_hint":sub[k][3],"sentences":sub[k][4]} for k in keys]
    json.dump(data, open(f"{SCRATCH}/assign_{g}.json","w"), ensure_ascii=False, indent=1)
    print(g,"→",[d["item_no"] for d in data],"문장",sum(len(d["sentences"]) for d in data))
