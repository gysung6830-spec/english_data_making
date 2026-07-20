"""API·코퍼스 없이 실전서 디자인을 미리 볼 수 있는 목(mock) 데이터.

실제 기출 대신 평가원 스타일 예문으로 5개 챕터(인과/대조/등호/비교/연결어)를 채운다.
`python run_guide.py --mock` 이 이 데이터를 렌더링한다.
"""
from __future__ import annotations

from src.guide.codes import load_part0
from src.guide.schemas import (CardBody, CodeCard, Chapter, Guide, Modifier,
                               Part2, SyntaxBody, SyntaxCard, SyntaxChapter)


def _card(code, code_ko, dir_, sentence, hit, trap, why, correct, skel=""):
    return CodeCard(
        code=code, code_ko=code_ko, dir=dir_, sentence=sentence,
        body=CardBody(highlight=hit, literal_trap=trap, trap_why=why,
                      correct=correct, skeleton=skel),
    )


def _syn(structure, sentence, sk_en, sk_ko, mods, full, check=""):
    return SyntaxCard(
        sentence=sentence, structure=structure,
        body=SyntaxBody(skeleton_en=sk_en, skeleton_ko=sk_ko,
                        modifiers=[Modifier(**m) for m in mods], full_ko=full,
                        self_check=check),
    )


def mock_part2() -> Part2:
    """2부 — 구문별 괄호치기 실전(중3도 읽게) 목 데이터."""
    chapters = [
        SyntaxChapter(
            id="relative", title="관계사절",
            signal="who / which / that / whose / where 가 명사 뒤에 붙어 길게 꾸민다.",
            how="관계사부터 절 끝까지 통째로 괄호 → 꾸밈받는 명사만 뼈대에 남긴다.",
            cards=[
                _syn(
                    "관계사절",
                    "The strategy is to analyze all the possible scenarios that the future "
                    "holds and then to see what proportion of them lead to success.",
                    "The strategy is to analyze scenarios and to see the proportion.",
                    "그 전략은 시나리오를 분석하고 비율을 보는 것이다.",
                    [
                        {"phrase": "that the future holds", "kind": "관계사절",
                         "connector": "~하는", "meaning": "미래가 품고 있는(→ 앞으로 벌어질)"},
                        {"phrase": "what proportion of them lead to success", "kind": "관계사절",
                         "connector": "~하는지", "meaning": "그중 얼마나가 성공으로 이어지는지"},
                    ],
                    "그 전략은 미래에 벌어질 수 있는 모든 시나리오를 분석한 뒤, 그중 어느 정도가 "
                    "성공으로 이어지는지를 보는 것이다.",
                    "다음 문장에서 who~ 절에 직접 괄호쳐 보자.",
                ),
            ],
        ),
        SyntaxChapter(
            id="participle", title="분사구문",
            signal="문두나 콤마 뒤에 V-ing / V-ed 덩어리가 붙는다.",
            how="분사 덩어리를 통째로 괄호 → ~하면서 / ~한 채로 로 뼈대에 붙인다.",
            cards=[
                _syn(
                    "분사구문",
                    "Recognizing how she felt about her failure, Ken approached her and said "
                    "a few encouraging words.",
                    "Ken approached her and said a few words.",
                    "Ken이 그녀에게 다가가 몇 마디를 건넸다.",
                    [
                        {"phrase": "Recognizing how she felt about her failure", "kind": "분사구문",
                         "connector": "~해서", "meaning": "그녀가 실패에 대해 어떻게 느끼는지 알아채고서"},
                        {"phrase": "encouraging", "kind": "분사(형용사)",
                         "connector": "~하는", "meaning": "격려가 되는"},
                    ],
                    "그녀가 실패를 어떻게 느끼는지 알아챘기에(~해서), Ken은 그녀에게 다가가 몇 마디 "
                    "격려의 말을 건넸다.",
                ),
            ],
        ),
        SyntaxChapter(
            id="cleft", title="긴 주어·가주어",
            signal="It is / was … that / to … — 진짜 주어가 뒤로 밀려 있다.",
            how="가주어 It 은 버리고, 뒤의 that / to 덩어리를 진짜 주어로 앞에 놓는다.",
            cards=[
                _syn(
                    "긴 주어·가주어",
                    "It follows that natural selection is unlikely to lead to the evolution "
                    "of perfect, maximally fit individuals.",
                    "That ... follows. (= 그것이 따라 나온다)",
                    "…라는 결론이 따라 나온다.",
                    [
                        {"phrase": "that natural selection is unlikely to lead to the evolution "
                                   "of perfect individuals", "kind": "진주어(that절)",
                         "connector": "~라는 것", "meaning": "자연선택이 완벽한 개체의 진화로 "
                         "이어질 가능성이 낮다는 것"},
                    ],
                    "자연선택이 완벽하고 최대로 적합한 개체의 진화로 이어질 가능성은 낮다는 결론이 "
                    "(그로부터) 따라 나온다.",
                ),
            ],
        ),
    ]
    return Part2(intro="같은 3단계를 구문 유형별로 반복 훈련한다. 유형이 달라도 방법은 똑같다.",
                 chapters=chapters)


def mock_guide() -> Guide:
    chapters = [
        Chapter(
            id="causation", title="인과",
            signal="원인과 결과를 잇는 표현 — 화살표 방향이 생명이다.",
            misread="화살표 방향을 놓쳐 원인과 결과를 뒤바꿔 읽는다",
            tip="코드를 보면 먼저 화살표 방향부터 고정하라 — 누가 원인이고 누가 결과인지.",
            cards=[
                _card(
                    "be attributable to", "A가 B에 기인하다", "backward",
                    "The recent decline in species diversity is largely attributable to "
                    "the fragmentation of natural habitats.",
                    "attributable to",
                    "종 다양성의 감소가 서식지 파편화를 일으켰다.",
                    "‘be attributable to’는 역방향(B←A) — A(감소)가 원인이 아니라 결과다. 원인은 뒤(파편화).",
                    "최근의 종 다양성 감소는 대체로 자연 서식지의 파편화에서 비롯된 것이다(파편화가 원인).",
                    "The decline is attributable to the fragmentation.",
                ),
                _card(
                    "give rise to", "A가 B를 일으키다", "forward",
                    "A subtle shift in consumer expectations can give rise to sweeping "
                    "changes across an entire industry.",
                    "give rise to",
                    "산업 전반의 큰 변화가 소비자 기대의 미묘한 변화를 낳는다.",
                    "‘give rise to’는 정방향(A→B) — 앞(기대 변화)이 원인, 뒤(산업 변화)가 결과. 방향이 반대다.",
                    "소비자 기대의 미묘한 변화가 산업 전반의 광범위한 변화를 일으킬 수 있다.",
                    "A shift can give rise to changes.",
                ),
            ],
        ),
        Chapter(
            id="contrast", title="대조·반의",
            signal="앞뒤 내용을 반대로 뒤집는 신호.",
            misread="대조 신호를 놓쳐 앞뒤를 같은 방향으로 읽는다",
            tip="이 코드가 보이면 앞뒤가 ‘반대’다 — 뒤 내용을 앞과 뒤집어 이해하라.",
            cards=[
                _card(
                    "rather than", "~라기보다는", "",
                    "Creativity emerges from the recombination of familiar ideas rather "
                    "than from a sudden flash of unprecedented insight.",
                    "rather than",
                    "창의성은 익숙한 생각의 재조합에서, 그리고 갑작스러운 통찰에서 나온다.",
                    "‘rather than’은 뒤를 부정하는 대조 신호다. 뒤(갑작스러운 통찰)는 ‘아니다’로 배제해야 한다.",
                    "창의성은 갑작스러운 통찰이 아니라, 익숙한 생각들의 재조합에서 나온다.",
                ),
                _card(
                    "whereas", "~인 반면에", "",
                    "Novices focus on the surface features of a problem, whereas experts "
                    "attend to its underlying structure.",
                    "whereas",
                    "초보자는 문제의 표면적 특징에 집중하고, 그래서 전문가는 그 근본 구조를 본다.",
                    "‘whereas’는 대조(반면에)다. ‘그래서’ 같은 인과·순접으로 읽으면 두 주체의 대비가 사라진다.",
                    "초보자는 문제의 표면적 특징에 집중하는 반면, 전문가는 그 근본 구조에 주목한다.",
                ),
            ],
        ),
        Chapter(
            id="equivalence", title="등호·구별",
            signal="A와 B가 같은지(=) 다른지(≠)를 정하는 표현.",
            misread="A=B(재진술·동격)를 놓쳐 새 정보로 읽거나, 구별을 동일시한다",
            tip="등호(A=B)면 뒤는 앞의 재진술이다 — 새 내용이 아니라 같은 말임을 알아채라.",
            cards=[
                _card(
                    "in other words", "즉, 다시 말해", "",
                    "The medium constrains what can be said; in other words, the form of a "
                    "message quietly shapes its content.",
                    "in other words",
                    "매체가 말할 수 있는 것을 제한한다. 그리고 또 다른 정보로, 메시지의 형식이 내용을 만든다.",
                    "‘in other words’ 뒤는 새 정보가 아니라 앞 문장의 재진술(=)이다. 새 논점으로 세면 논지가 흩어진다.",
                    "매체는 말할 수 있는 바를 제약한다. 즉, 메시지의 형식이 그 내용을 은근히 규정한다(앞의 같은 말).",
                ),
                _card(
                    "distinguish A from B", "A를 B와 구별하다", "",
                    "What distinguishes expertise from mere experience is the ability to "
                    "notice what is absent.",
                    "distinguishes expertise from mere experience",
                    "전문성을 단순 경험과 똑같이 묶어, 둘 다 부재를 알아채는 능력이라고 본다.",
                    "‘distinguish A from B’는 A≠B, 둘을 ‘가르는’ 기준을 말한다. 동일시하면 문장의 핵심(차이)이 사라진다.",
                    "전문성을 단순한 경험과 구별해 주는 것은, 무엇이 ‘없는지’를 알아채는 능력이다.",
                ),
            ],
        ),
        Chapter(
            id="comparison", title="비교·대체·선호",
            signal="둘 중 어느 쪽이 더/우선인지를 정하는 표현.",
            misread="우열·선호의 대상이 뒤바뀐다 (A를 택했는지 B를 택했는지)",
            tip="무엇이 무엇보다 위인지, 무엇이 무엇을 대신하는지 — 두 대상의 관계부터 확정하라.",
            cards=[
                _card(
                    "outweigh", "A가 B보다 더 중요하다/크다", "",
                    "In the long run, the cumulative benefits of trust outweigh the "
                    "short-term costs of appearing vulnerable.",
                    "outweigh",
                    "취약해 보이는 단기 비용이 신뢰의 누적된 이득보다 더 크다.",
                    "‘A outweigh B’는 A가 B보다 크다는 뜻. 주어(신뢰의 이득)와 목적어(단기 비용)를 뒤집으면 결론이 반대가 된다.",
                    "장기적으로는 신뢰의 누적된 이득이 취약해 보이는 단기 비용을 능가한다(이득이 더 크다).",
                ),
                _card(
                    "give way to", "A가 B에게 자리를 내주다", "",
                    "As the evidence accumulated, the old consensus gradually gave way to a "
                    "more nuanced account.",
                    "gave way to",
                    "더 정교한 설명이 낡은 합의에 자리를 내주었다.",
                    "‘A give way to B’는 A가 물러나고 B가 들어선다는 뜻. 주어·대상을 바꾸면 무엇이 사라졌는지가 반대가 된다.",
                    "증거가 쌓이면서, 낡은 합의가 점차 물러나고 더 정교한 설명이 그 자리를 차지했다.",
                ),
            ],
        ),
        Chapter(
            id="connective", title="연결어",
            signal="글의 논리 흐름(부연·예시·인과·양보)을 알리는 신호.",
            misread="연결어의 논리 종류를 오해해 글의 흐름을 반대로/엉뚱하게 잡는다",
            tip="연결어의 ‘논리 종류’부터 판정하라 — 부연인지, 대조인지, 인과인지, 예시인지.",
            cards=[
                _card(
                    "thereby", "그렇게 함으로써", "",
                    "Repeated retrieval strengthens memory traces, thereby making later "
                    "recall faster and more reliable.",
                    "thereby",
                    "반복 인출은 기억 흔적을 강화한다. 그런데도 이후의 회상은 더 빠르고 안정적이다.",
                    "‘thereby’는 역접이 아니라 ‘그 결과·그 수단으로’의 귀결이다. ‘그런데도’로 읽으면 인과가 끊긴다.",
                    "반복 인출은 기억 흔적을 강화하고, 그렇게 함으로써 이후의 회상을 더 빠르고 안정적으로 만든다.",
                ),
                _card(
                    "nonetheless", "그럼에도 불구하고", "",
                    "The model rests on simplified assumptions; nonetheless, its predictions "
                    "match the observed data with surprising accuracy.",
                    "nonetheless",
                    "모형은 단순화된 가정에 기대고 있고, 따라서 그 예측이 데이터와 잘 맞는다.",
                    "‘nonetheless’는 양보·역접(그럼에도)이다. ‘따라서’로 읽으면 ‘가정이 단순한데도 잘 맞는다’는 반전이 사라진다.",
                    "그 모형은 단순화된 가정에 기대고 있다. 그럼에도 불구하고 그 예측은 관측 데이터와 놀랍도록 정확히 들어맞는다.",
                ),
            ],
        ),
    ]
    return Guide(part0=load_part0(), chapters=chapters, part2=mock_part2())
