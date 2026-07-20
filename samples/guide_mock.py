"""API 없이 실전서 디자인을 미리 볼 수 있는 목(mock) 데이터.

★ 모든 예문은 넣어주신 4개 평가원 기출(2022·2023 고3)에서 실제로 뽑은 문장이다.
   (분석·해설은 샘플 시연용으로 작성 — 실제 생성은 --mock 없이 API 로 동일 구조를 채운다.)
`python run_guide.py --mock` 이 이 데이터를 렌더링한다.
"""
from __future__ import annotations

from src.guide.codes import load_part0
from src.guide.schemas import (CardBody, CodeCard, Chapter, Guide, Modifier,
                               Part2, SyntaxBody, SyntaxCard, SyntaxChapter)


# ── 1부: 평가원 코드 카드 (오역 → 정답 → 진짜 의미) ─────────────
def _code(code, code_ko, dir_, sentence, hit, trap, why, correct, so_what):
    return CodeCard(
        code=code, code_ko=code_ko, dir=dir_, sentence=sentence,
        body=CardBody(highlight=hit, literal_trap=trap, trap_why=why,
                      correct=correct, so_what=so_what),
    )


# ── 2부: 구문 카드 (뼈대 → 살 붙이기 → 완성 → 진짜 의미) ────────
def _syn(structure, sentence, sk_en, sk_ko, mods, full, real, check=""):
    return SyntaxCard(
        sentence=sentence, structure=structure,
        body=SyntaxBody(skeleton_en=sk_en, skeleton_ko=sk_ko,
                        modifiers=[Modifier(**m) for m in mods], full_ko=full,
                        real_meaning=real, self_check=check),
    )


def mock_part2() -> Part2:
    chapters = [
        SyntaxChapter(
            id="relative", title="관계사절",
            signal="who / which / that / whose / where 가 명사 뒤에 붙어 길게 꾸민다.",
            how="관계사부터 절 끝까지 괄호 → 앞 명사만 뼈대에 남기고, '~하는'으로 뒤에서 붙인다.",
            cards=[_syn(
                "관계사절",
                "Consider two athletes who both want to play in college.",
                "Consider two athletes.", "두 선수를 생각해 보라.",
                [{"phrase": "who both want to play in college", "kind": "관계사절",
                  "connector": "~하는", "meaning": "둘 다 대학에서 (운동을) 뛰고 싶어하는"}],
                "둘 다 대학에서 뛰고 싶어하는 두 선수를 생각해 보라.",
                "즉, 목표가 똑같은 두 선수를 세워 두고 이제 그 '차이'를 비교하려는 도입 문장이다.",
                "다음 문장에서 who~ 절에 직접 괄호쳐 보자.",
            )],
        ),
        SyntaxChapter(
            id="participle", title="분사·분사구문",
            signal="문두나 콤마 뒤에 V-ing / V-ed 덩어리가 붙는다.",
            how="분사 덩어리를 괄호 → 주절 뼈대부터 읽고 ~하면서 / ~한 채로 / ~해서로 붙인다.",
            cards=[_syn(
                "분사구문",
                "Recognizing how she felt about her failure, Ken, her teammate, approached "
                "her and said a few encouraging words.",
                "Ken approached her and said a few words.", "Ken이 그녀에게 다가가 몇 마디를 했다.",
                [{"phrase": "Recognizing how she felt about her failure", "kind": "분사구문",
                  "connector": "~해서", "meaning": "그녀가 실패를 어떻게 느끼는지 알아채고서"},
                 {"phrase": "her teammate", "kind": "삽입(동격)",
                  "connector": "~인", "meaning": "그녀의 팀 동료인"}],
                "그녀가 실패를 어떻게 느끼는지 알아챘기에, 팀 동료인 Ken이 그녀에게 다가가 "
                "격려의 말을 몇 마디 건넸다.",
                "즉, Ken이 그녀의 속상함을 눈치채고 위로하러 다가간 장면이다.",
            )],
        ),
        SyntaxChapter(
            id="insertion", title="삽입·동격",
            signal="— … — 또는 , or / , which / 콤마 동격이 문장 중간에 끼어든다.",
            how="대시·콤마 사이는 통째로 괄호(없는 셈) → 뼈대부터 읽고 부가 설명으로 취급한다.",
            cards=[_syn(
                "삽입·동격",
                "For the present generation of artists, the computer, or more appropriately, "
                "the laptop, is one in a collection of intelligent tools.",
                "The computer is one tool.", "컴퓨터는 도구 하나다.",
                [{"phrase": "or more appropriately, the laptop", "kind": "삽입(동격)",
                  "connector": "즉", "meaning": "더 정확히 말하면 노트북"}],
                "요즘 세대 예술가에게 컴퓨터, 더 정확히는 노트북은 여러 지능형 도구 중 하나다.",
                "즉, 요즘 예술가에겐 노트북이 특별한 게 아니라 붓·물감처럼 흔한 작업 도구일 뿐이라는 뜻.",
            )],
        ),
        SyntaxChapter(
            id="prep_stack", title="전치사구 후치수식 겹침",
            signal="명사 뒤에 of/in/for/with 전치사구가 두 개 이상 줄줄이 이어진다.",
            how="전치사구는 뒤에서 앞으로 '~의 / ~을 위한'으로 차례차례 붙여 명사를 완성한다.",
            cards=[_syn(
                "전치사구 겹침",
                "Last week, I made a reservation for one of your company's swimming pools for "
                "our summer swim camp.",
                "I made a reservation.", "저는 예약을 했습니다.",
                [{"phrase": "for one of your company's swimming pools", "kind": "전치사구",
                  "connector": "~을", "meaning": "귀사의 수영장 중 하나를"},
                 {"phrase": "for our summer swim camp", "kind": "전치사구",
                  "connector": "~을 위한", "meaning": "저희 여름 수영 캠프를 위해"}],
                "지난주에 저는 여름 수영 캠프를 위해 귀사의 수영장 중 하나를 예약했습니다.",
                "즉, '무엇을·무엇을 위해'는 전치사구가 담당할 뿐, 뼈대는 그냥 '예약했다'이다.",
            )],
        ),
        SyntaxChapter(
            id="cleft", title="긴 주어·가주어",
            signal="It is / was … that / to … — 진짜 주어가 뒤로 밀려 있다.",
            how="가주어 It은 버리고, 뒤의 that/to 덩어리를 진짜 주어로 앞에 놓는다.",
            cards=[_syn(
                "가주어",
                "It follows that natural selection is unlikely to lead to the evolution of "
                "perfect, maximally fit individuals.",
                "That ... follows.", "…라는 결론이 따라 나온다.",
                [{"phrase": "that natural selection is unlikely to lead to the evolution of "
                            "perfect, maximally fit individuals", "kind": "진주어(that절)",
                  "connector": "~라는 것", "meaning": "자연선택이 완벽한 개체의 진화로 이어질 "
                  "가능성이 낮다는 것"}],
                "자연선택이 완벽하고 최대로 적합한 개체의 진화로 이어질 가능성은 낮다는 결론이 "
                "(그로부터) 따라 나온다.",
                "즉, 진화는 '최고로 완벽한 생물'을 만드는 게 아니라 그저 '그럭저럭 적응한' 생물을 남긴다는 뜻.",
            )],
        ),
        SyntaxChapter(
            id="inversion", title="도치·강조",
            signal="문두에 Not only / Never / Only 가 나오고 주어·동사가 뒤집힌다.",
            how="원래 어순(주어+동사)으로 되돌려 읽는다. 문두 부정어는 '거의/결코 ~않다'로.",
            cards=[_syn(
                "도치(Not only 도치)",
                "Not only is it less convenient—in terms of time, cost and comfort—to access "
                "locations in cities, but the very process of moving around in cities generates "
                "a number of negative externalities.",
                "It is not only less convenient to access locations, but moving generates "
                "negative effects.",
                "도시에서 이동이 덜 편할 뿐 아니라, 이동 자체가 부정적 부작용을 낳는다.",
                [{"phrase": "in terms of time, cost and comfort", "kind": "삽입",
                  "connector": "~면에서", "meaning": "시간·비용·편의 면에서"}],
                "도시에서 (시간·비용·편의 면에서) 장소에 접근하기가 덜 편할 뿐 아니라, 도시를 "
                "돌아다니는 과정 자체가 여러 부정적 외부효과를 낳는다.",
                "즉, 도시 이동은 '불편하다'로 끝이 아니라, 그 이동이 매연·혼잡 같은 사회적 비용까지 만든다는 이중고.",
            )],
        ),
        SyntaxChapter(
            id="comparison", title="비교구문",
            signal="more … than, as … as — 비교 기준이 뒤에 온다.",
            how="than/as 뒤(비교 기준)를 괄호 → '무엇보다 / 무엇만큼'을 뼈대 뒤에 붙인다.",
            cards=[_syn(
                "비교구문",
                "Due to its popularity, thirty more students are coming to the camp than we "
                "expected, so we need one more swimming pool.",
                "Thirty more students are coming than we expected.",
                "예상보다 30명 더 많은 학생이 온다.",
                [{"phrase": "than we expected", "kind": "비교 기준",
                  "connector": "~보다", "meaning": "우리가 예상했던 것보다"}],
                "인기 때문에, 예상했던 것보다 30명이 더 많은 학생이 캠프에 와서 수영장이 하나 더 필요하다.",
                "즉, 신청이 몰려 예상 인원을 30명이나 초과했으니 수영장을 추가로 잡아야 한다는 실무적 요청.",
            )],
        ),
        SyntaxChapter(
            id="parallel", title="병렬·상관접속사",
            signal="not only A but (also) B / both A and B — 짝을 이뤄 대칭된다.",
            how="A와 B의 '급(단어 종류)'을 맞춰 같은 자리에 놓고 대칭으로 읽는다.",
            cards=[_syn(
                "상관접속사(not only A but also B)",
                "Not only musicians and psychologists, but also committed music enthusiasts and "
                "experts often voice the opinion that the beauty of music lies in an expressive "
                "deviation from the exactly defined score.",
                "Not only A but also B voice the opinion.", "A뿐 아니라 B도 그 의견을 낸다.",
                [{"phrase": "that the beauty of music lies in an expressive deviation from the "
                            "exactly defined score", "kind": "동격(that절)",
                  "connector": "~라는", "meaning": "음악의 아름다움은 정확히 정해진 악보에서 "
                  "벗어난 표현적 일탈에 있다는"}],
                "음악가와 심리학자뿐 아니라 열성적인 음악 애호가와 전문가들도, 음악의 아름다움은 "
                "정확히 정해진 악보에서 벗어난 '표현적 일탈'에 있다는 의견을 자주 낸다.",
                "즉, 악보를 완벽히 지킨 연주가 아니라 살짝 벗어나 감정을 실은 연주가 아름답다고 "
                "전문가부터 애호가까지 입을 모은다는 뜻.",
                "A(musicians and psychologists)와 B(enthusiasts and experts)에 각각 괄호쳐 보자.",
            )],
        ),
    ]
    return Part2(intro="같은 3단계를 구문 유형별로 반복 훈련한다. 유형이 달라도 방법은 똑같다 — "
                 "이런 구조면 → 이렇게 해석 → 해석하면 이런 내용.", chapters=chapters)


def mock_guide() -> Guide:
    chapters = [
        Chapter(
            id="causation", title="인과",
            signal="원인과 결과를 잇는 표현 — 화살표 방향이 생명이다.",
            misread="화살표 방향을 놓쳐 원인과 결과를 뒤바꿔 읽는다",
            tip="코드를 보면 먼저 화살표 방향부터 고정하라 — 누가 원인이고 누가 결과인지.",
            cards=[_code(
                "be due to", "A가 B 때문이다(A=결과)", "backward",
                "This ability is due to the activity of plant meristems, regions of "
                "undifferentiated tissue in roots and shoots that can divide.",
                "is due to",
                "이 능력이 식물 분열조직의 활동을 '일으킨다'(능력이 원인).",
                "'be due to'는 역방향 — A(능력)가 원인이 아니라 결과다. 원인은 뒤(분열조직 활동).",
                "이 능력은 식물 분열조직의 활동 '덕분에/때문에' 생긴다(활동이 원인).",
                "즉, 식물이 평생 새 기관을 만들 수 있는 건 분열조직이 계속 세포를 만들어 주기 때문이라는 말.",
            ), _code(
                "lead to", "A가 B로 이어지다(A=원인)", "forward",
                "Rising incomes inevitably lead to increases in motorization.",
                "lead to",
                "자동차화(motorization)의 증가가 소득 상승을 이끈다.",
                "'lead to'는 정방향(A→B) — 앞(소득 상승)이 원인, 뒤(자동차화)가 결과. 주어·목적어를 바꾸면 인과가 뒤집힌다.",
                "소득 증가는 필연적으로 자동차화(자동차 보유·이용 증가)로 이어진다.",
                "즉, 사람들이 잘살게 될수록 차를 더 많이 사고 타게 된다는, 거의 예외 없는 흐름.",
            )],
        ),
        Chapter(
            id="contrast", title="대조·반의",
            signal="앞뒤 내용을 반대로 뒤집는 신호.",
            misread="대조 신호를 놓쳐 앞뒤를 같은 방향으로 읽는다",
            tip="이 코드가 보이면 앞뒤가 ‘반대’다 — 뒤 내용을 앞과 뒤집어 이해하라.",
            cards=[_code(
                "unlike", "~와는 달리", "",
                "It is largely because, unlike animals, they can generate new organs and "
                "tissues throughout their life cycle.",
                "unlike",
                "동물과 마찬가지로, 그들(식물)도 새 기관을 만들 수 있기 때문이다.",
                "'unlike'는 대조 — 동물과 ‘달리’다. 같은 방향으로 읽으면 식물과 동물의 대비가 사라진다.",
                "동물과 ‘달리’ 그들(식물)은 평생에 걸쳐 새로운 기관과 조직을 만들 수 있기 때문이다.",
                "즉, ‘동물은 못 하는데 식물은 한다’는 차이가 이 문장이 말하려는 핵심이다.",
            ), _code(
                "although", "비록 ~일지라도(양보)", "",
                "Although this is true, it has also become a tired and played-out argument.",
                "Although",
                "이것이 사실이기 때문에, 그것은 낡고 진부한 주장이 되었다.",
                "'although'는 양보(비록 ~지만) — 앞을 인정하되 뒤에서 뒤집는다. ‘~때문에’로 읽으면 정반대.",
                "비록 이것이 사실이지만, 그것은 이제 낡고 진부해진 주장이기도 하다.",
                "즉, 맞는 말이긴 해도 너무 여러 번 우려먹어 더는 신선하지 않다는 평가.",
            )],
        ),
        Chapter(
            id="equivalence", title="등호·구별",
            signal="A와 B가 같은지(=) 다른지(≠)를 정하는 표현.",
            misread="A=B(재진술)를 놓쳐 새 정보로 읽는다",
            tip="등호(A=B)면 뒤는 앞의 재진술이다 — 새 내용이 아니라 같은 말임을 알아채라.",
            cards=[_code(
                "in other words", "즉, 다시 말해", "",
                "In other words, as museums struggle to survive in a competitive economy, their "
                "budgets often prioritise those parts of themselves that are open to the public.",
                "In other words",
                "그리고 또 다른 정보로, 박물관은 예산을 배정한다.",
                "'in other words' 뒤는 새 정보가 아니라 앞 문장의 재진술(=)이다. 새 논점으로 세면 논지가 흩어진다.",
                "다시 말해, 박물관은 경쟁 경제에서 살아남으려 예산을 ‘대중에게 공개되는 부분’에 우선 배정한다.",
                "즉, 돈이 걸리니 박물관도 관람객 눈에 보이는 전시 위주로 예산을 쓴다는 뜻.",
            )],
        ),
        Chapter(
            id="comparison", title="비교·대체·선호",
            signal="둘 중 어느 쪽이 더/우선인지를 정하는 표현.",
            misread="우열·선호의 대상이 뒤바뀐다",
            tip="무엇이 무엇보다 위인지, 무엇이 무엇을 대신하는지 — 두 대상의 관계부터 확정하라.",
            cards=[_code(
                "rather than", "~가 아니라(뒤를 부정)", "",
                "Urban transport professionals have largely acquiesced to the view that "
                "automobile demand in cities needs to be managed rather than accommodated.",
                "rather than",
                "자동차 수요는 관리되기보다 ‘수용’되어야 한다.",
                "'rather than'은 뒤(accommodated)를 부정한다 — 관리 O, 수용 X. 앞뒤를 바꾸면 결론이 정반대.",
                "도시의 자동차 수요는 (도로를 늘려) 수용할 게 아니라 ‘관리’되어야 한다.",
                "즉, 차가 늘면 길을 넓혀 받아주던 방식을 버리고 수요 자체를 억제·관리하자는 입장.",
            )],
        ),
        Chapter(
            id="connective", title="연결어",
            signal="글의 논리 흐름(부연·대조·인과)을 알리는 신호.",
            misread="연결어의 논리 종류를 오해해 흐름을 반대로 잡는다",
            tip="연결어의 ‘논리 종류’부터 판정하라 — 부연인지, 대조인지, 인과인지.",
            cards=[_code(
                "however", "하지만(역접)", "",
                "However, those data do not actually show that different cultures have different "
                "emotions, if we think of emotions as central, neurally implemented states.",
                "However",
                "따라서 그 데이터는 문화마다 감정이 다름을 보여준다.",
                "'however'는 역접 — 앞 내용을 뒤집는다. ‘따라서’로 읽으면 앞 주장을 그대로 이어받아 정반대가 된다.",
                "하지만 그 데이터가 문화마다 감정이 ‘다르다’는 것을 실제로 보여주는 건 아니다.",
                "즉, 겉보기 데이터와 달리, 감정을 뇌에 구현된 핵심 상태로 보면 문화 간 감정은 다르지 않다는 반박.",
            )],
        ),
        Chapter(
            id="polarity_positive", title="긍정·강조 신호",
            signal="필자가 ‘중요하다·핵심이다’라고 힘주는 대목.",
            misread="강조 신호를 흘려 필자가 무엇을 ‘중시’하는지(=입장)를 놓친다",
            tip="긍정·강조어가 나오면 거기가 필자의 핵심 주장이다 — 밑줄 긋고 답의 근거로 삼아라.",
            cards=[_code(
                "central", "핵심적인", "",
                "Improving the quality of alternative options, such as walking, cycling, and "
                "public transport, is a central element of this strategy.",
                "central",
                "대안 수단의 질 개선은 이 전략의 여러 요소 중 하나일 뿐이다.",
                "'central(핵심)'을 곁다리로 흘리면 필자가 ‘가장 중시하는’ 것을 놓친다 — 여기가 주장의 중심이다.",
                "대안 수단(도보·자전거·대중교통)의 질을 높이는 것이 이 전략의 ‘핵심’ 요소다.",
                "즉, 필자는 차를 줄이는 정책의 성패가 ‘대안 교통을 얼마나 좋게 만드느냐’에 달렸다고 못박는 것.",
            ), _code(
                "fundamental", "근본적인, 핵심적인", "",
                "Rather than irrelevant, moral questions are fundamental to the imposition of tax.",
                "fundamental",
                "도덕적 질문은 세금 부과와 무관한, 부차적인 문제다.",
                "'fundamental(근본적)'은 강한 긍정·핵심 신호. 앞의 ‘rather than irrelevant’도 ‘무관하지 않다’고 못박는다. 흘리면 필자 입장을 정반대로 읽는다.",
                "도덕적 질문은 (무관하기는커녕) 세금 부과에 근본적으로 중요하다.",
                "즉, 세금을 매기는 일은 숫자·행정이 아니라 ‘무엇이 옳은가’라는 도덕 문제가 핵심이라는 주장.",
            )],
        ),
        Chapter(
            id="polarity_negative", title="부정·부재·거부 신호",
            signal="‘아니다·없다·거의 안 한다’로 문장의 극성을 뒤집는 말.",
            misread="부정·부재어를 놓쳐 필자 의견을 정반대(긍정)로 읽는다",
            tip="부정어가 보이면 극성이 뒤집힌다 — 놓치면 필자 의견과 정반대로 멀어진다.",
            cards=[_code(
                "rarely", "좀처럼 ~않다", "",
                "Young contemporary artists who employ digital technologies in their practice "
                "rarely make reference to computers.",
                "rarely",
                "디지털 기술을 쓰는 젊은 예술가들은 컴퓨터를 자주 언급한다.",
                "'rarely(좀처럼 ~않다)'를 놓치면 문장 극성이 정반대가 되어 필자 의견과 완전히 멀어진다.",
                "디지털 기술을 쓰는 젊은 현대 예술가들은 정작 컴퓨터를 ‘좀처럼 언급하지 않는다’.",
                "즉, 도구로는 컴퓨터를 쓰면서도 자기 작품을 말할 땐 컴퓨터를 감추는 ‘역설’을 필자가 지적하는 것.",
            ), _code(
                "unlikely to", "~할 가능성이 없는", "",
                "It follows that natural selection is unlikely to lead to the evolution of "
                "perfect, maximally fit individuals.",
                "unlikely to",
                "자연선택은 완벽한 개체의 진화로 이어질 가능성이 높다.",
                "'unlikely to(~할 가능성이 없는)'를 놓치면 극성이 정반대 — 필자는 ‘이어지지 않는다’고 말하는 중이다.",
                "자연선택이 완벽하고 최고로 적합한 개체의 진화로 이어질 가능성은 낮다.",
                "즉, 진화는 ‘완벽한 생물’을 빚어내는 게 아니라 그저 그럭저럭 적응한 생물을 남길 뿐이라는 뜻.",
            )],
        ),
    ]
    return Guide(part0=load_part0(), chapters=chapters, part2=mock_part2())
