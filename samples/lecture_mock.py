"""API 없이 강의컨셉 교재(필생보) 렌더링/파이프라인을 검증하기 위한 목(mock) 데이터."""
from __future__ import annotations

from src.lecture_schemas import (Chunk, FlowBlock, GrammarChip, GrammarDrill,
                                 GrammarNote, KeyGrammar, LecturePassage,
                                 LectureSentence, Misread, Overview,
                                 RestatementChain, SentenceAnalysis,
                                 SentenceItem, Vocab)


def _S(id, english, grammar, vocab, chunks, misreads):
    return SentenceItem(
        id=id, english=english,
        grammar=[GrammarChip(tag=t, note=n) for t, n in grammar],
        vocab=[Vocab(word=w, meaning=m) for w, m in vocab],
        chunks=[Chunk(en=e, ko=k) for e, k in chunks],
        misreads=[Misread(statement=s, why=w) for s, w in misreads],
    )


def mock_lecture_passage(title: str = "Fear and Social Development",
                         source: str = "Mock Reader 2024",
                         item_no: str = "") -> LecturePassage:
    raw = [
        "Many developmental theorists and researchers, including those studying human as well as nonhuman primate subjects, have recognized the role that fear can play in a primate's social development.",
        "When an infant is frightened it always seeks out its mother for protection and safety, and all exploratory and play activity stops until the infant has been sufficiently comforted and reassured by its attachment object.",
        "Thus, frequently frightened infants will very likely have less time to explore and fewer opportunities to play than will infants who are not.",
        "Such voluntary restraints may serve to slow down the social development of shy or anxious infants if these tendencies are maintained throughout their childhood years.",
    ]
    sentences = [LectureSentence(id=i, text=t) for i, t in enumerate(raw, 1)]

    overview = Overview(
        theme_ko="두려움이 영장류·아기의 사회성 발달을 늦추는 이유",
        key_grammar=KeyGrammar(
            point="비교급 than절의 도치·생략",
            source_sentence="Thus, frequently frightened infants will very likely have less time to "
                            "explore and fewer opportunities to play than will infants who are not.",
            explanation=[
                GrammarNote(chip="쉽게 말하면",
                            text="'A는 B보다 더 ~하다'를 말할 때 than 뒤 B에서 가끔 '[[조동사(do/will/be)+주어]]' 순으로 순서가 뒤집혀. 이걸 도치라고 불러."),
                GrammarNote(chip="왜 그래?",
                            text="주어가 길거나 글맛을 살리고 싶을 때 같은 말 반복하기 싫어서 이렇게 자리를 바꿔 쓰는 거거든."),
                GrammarNote(chip="생략",
                            text="than 앞뒤로 겹치는 동사·표현은 굳이 두 번 안 쓰고 뒤쪽을 [[생략]]해 버려 — 그래서 문장이 짧아 보이는 거야."),
                GrammarNote(chip="복원",
                            text="원래대로 풀면 than will infants who are not → 'than infants who are not (frequently frightened) will (have)' 이런 뜻이야."),
                GrammarNote(chip="주의",
                            text="than은 [[접속사]]로도 전치사로도 쓰이는데, 뒤에 '절(주어+동사)'이 오면 접속사고, 바로 이때 도치가 보여."),
                GrammarNote(chip="해석 요령",
                            text="서두르지 말고 먼저 '비교 대상 B가 뭔지'부터 딱 잡은 다음 'B보다 더/덜 ~하다'로 옮기면 편해."),
            ],
            example="",
            example_analysis="than 뒤가 'will infants'로 조동사+주어 도치, 뒤의 have와 frequently frightened는 생략됐어.",
            drills=[
                # 객관식 (a) 지문 문장 1개(from_passage=True)
                GrammarDrill(kind="객관식", from_passage=True,
                             question="지문의 '… fewer opportunities to play than will infants who are not.' "
                                      "에서 밑줄 친 'than will infants' 에 대한 설명으로 옳은 것은?",
                             options=["than 뒤에 '조동사(will)+주어(infants)' 순으로 도치가 일어났다",
                                      "than 은 전치사이고 뒤의 infants 는 그 목적어다",
                                      "infants 가 동사, will 이 주어로 쓰였다"],
                             answer="than 뒤에 '조동사(will)+주어(infants)' 순으로 도치가 일어났다"),
                # 객관식 (b)(c) 지문에 없는 응용 2개(from_passage=False)
                GrammarDrill(kind="객관식", from_passage=False,
                             question="다음 중 than 뒤에 도치가 '어법상 옳게' 일어난 문장은?",
                             options=["He runs faster than does his brother.",
                                      "He runs faster than his brother does run.",
                                      "He runs faster than runs his brother does."],
                             answer="He runs faster than does his brother."),
                GrammarDrill(kind="객관식", from_passage=False,
                             question="밑줄 친 부분의 해석으로 알맞은 것은? "
                                      "'She reads more books than do her friends.'",
                             options=["그녀는 자기 친구들보다 더 많은 책을 읽는다",
                                      "그녀의 친구들이 그녀보다 더 많은 책을 읽는다",
                                      "그녀와 친구들이 같은 수의 책을 읽는다"],
                             answer="그녀는 자기 친구들보다 더 많은 책을 읽는다"),
                # 영작 (a): 지문에 실제로 있는 문장 복원(from_passage=True) — 핵심 문법이 쓰인 문장
                GrammarDrill(kind="영작", from_passage=True,
                             question="(지문 3문장) 따라서 자주 겁을 먹는 아기들은 그렇지 않은 "
                                      "아기들보다 탐색할 시간과 놀 기회가 더 적을 가능성이 높다.",
                             words=["frequently frightened", "less time to explore",
                                    "fewer opportunities", "than will infants who are not"],
                             answer="Thus, frequently frightened infants will very likely have less "
                                    "time to explore and fewer opportunities to play than will "
                                    "infants who are not."),
                # 영작 (b): 지문에 없는 응용 문장(from_passage=False) — 같은 문법 응용
                GrammarDrill(kind="영작", from_passage=False,
                             question="그는 내가 그런 것보다 더 열심히 공부했다.",
                             words=["studied", "harder", "than", "did", "I"],
                             answer="He studied harder than did I."),
            ],
        ),
        topic="겁을 잘 먹는 아기는 엄마에게 붙어 있느라 탐색·놀이를 못하고, 그게 오래 지속되면 사회성 발달이 느려질 수 있다는 얘기야.",
        stance="부정적·비판적",
        stance_reason="'less time', 'fewer opportunities', 'slow down the social development' 같은 손실·지체 표현으로 두려움의 효과를 부정적으로 봐.",
        structure="주장→근거·예시",
        structure_reason="1문장에서 주제를 던지고, 2문장에서 아기 행동으로 근거를 대고, Thus로 결과를 정리해.",
        restatement_chains=[
            RestatementChain(
                label="두려움을 느끼는 아기",
                expressions=["fear", "When an infant is frightened",
                             "frequently frightened infants", "shy or anxious infants"],
                variation="추상명사 fear → 상태 서술 → 자주 겁먹는 아기 → 소심·불안한 아기로 점점 구체화돼.",
            ),
            RestatementChain(
                label="탐색·놀이 중단",
                expressions=["all exploratory and play activity stops",
                             "less time to explore and fewer opportunities to play",
                             "Such voluntary restraints"],
                variation="'활동이 멈춘다'는 동사 서술 → '시간·기회가 적다'는 비교 → '자발적 제약'이라는 명사로 압축돼.",
            ),
        ],
        flow_blocks=[
            FlowBlock(stage="도입", sentence_range="1",
                      summary="학자들은 두려움이 아기의 [[사회성 발달]]에 역할을 한다고 인정해 왔다.",
                      easy_example="겁먹는 게 노는 데 영향을 준다는 걸 전문가들도 안다는 얘기."),
            FlowBlock(stage="근거", sentence_range="2",
                      summary="겁먹은 아기는 엄마를 찾고, 안심할 때까지 탐색·놀이가 [[멈춘다]].",
                      easy_example="무서우면 곧장 엄마 벤치로 뛰어가 미끄럼틀엔 손도 안 대는 장면."),
            FlowBlock(stage="결과", sentence_range="3",
                      summary="그래서 자주 겁먹는 아기는 그렇지 않은 아기보다 탐색·놀이 기회가 [[더 적다]].",
                      easy_example="벤치에 자주 앉는 아이는 노는 시간 총합이 확 줄어드는 거야."),
            FlowBlock(stage="결론", sentence_range="4",
                      summary="이런 자기 제약이 유년기 내내 이어지면 사회성 발달이 [[느려질]] 수 있다.",
                      easy_example="몇 년 동안 벤치만 지키면 어울리는 법 배우는 속도가 느려진다는 마무리."),
        ],
    )

    items = [
        _S(1, raw[0], [("관계사 that","앞의 the role 을 that절이 수식"), ("분사구 including","주어를 부연 설명")],
           [("developmental", "발달의"), ("nonhuman primate", "인간이 아닌 영장류"),
            ("recognize", "인정하다, 인식하다"), ("play a role in", "~에서 역할을 하다")],
           [("Many developmental [[theorists]] and researchers,", "많은 발달 [[이론가]]들과 연구자들은,"),
            ("[[including those studying human as well as nonhuman primate subjects]],", "[[인간뿐 아니라 인간이 아닌 영장류를 연구 대상으로 삼는 사람들까지 포함해서]],"),
            ("have [[recognized]]", "[[인정해]] 왔다"),
            ("[[the role that fear can play in a primate's social development]].", "[[두려움이 영장류의 사회성 발달에서 할 수 있는 역할을]].")],
           [("두려움이 사회성 발달과 무관하다는 것을 밝히는 문장이다.",
             "정반대야. 학자들이 두려움이 사회성 발달에 '역할을 한다'는 걸 인정해 왔다는, 두려움이 영향을 준다는 주제를 던지는 문장이야."),
            ("영장류를 연구하는 구체적 방법을 소개하는 문장이다.",
             "연구 방법 소개가 아니라, 두려움이 발달에 하는 역할을 학자들이 인정해 왔다는 '주제 제시'야.")]),
        _S(2, raw[1], [("부사절 when/until","시간·조건을 나타내는 종속절"), ("수동태 has been p.p.","아기가 '위로받는' 것")],
           [("infant", "아기, 유아"), ("seek out", "찾아 나서다"),
            ("exploratory", "탐색의"), ("reassure", "안심시키다"),
            ("attachment object", "애착 대상")],
           [("When an infant is [[frightened]]", "아기가 [[겁을 먹으면]]"),
            ("it always", "그 아기는 항상"),
            ("[[seeks out its mother for protection and safety]],", "[[보호와 안전을 위해 자기 엄마를 찾아 나선다]],"),
            ("and all exploratory and play activity [[stops]]", "그리고 모든 탐색·놀이 활동이 [[멈춘다]]"),
            ("[[until the infant has been sufficiently comforted and reassured]]", "[[그 아기가 충분히 위로받고 안심하게 될 때까지]]"),
            ("by its [[attachment object]].", "자신의 [[애착 대상]]에 의해")],
           [("아기가 두려움을 스스로 극복해 가는 과정을 설명한다.",
             "극복 과정이 아니라, 겁먹으면 엄마에게 가서 안심할 때까지 탐색·놀이가 '멈춘다'는, 주제를 뒷받침하는 근거 문장이야."),
            ("놀이가 아기의 두려움을 없애 준다는 내용이다.",
             "놀이가 두려움을 없앤다는 게 아니라, 반대로 겁먹으면 놀이가 멈춘다는 얘기야.")]),
        _S(3, raw[2], [("비교급 than","'~보다 더 적다' 비교"), ("than절 도치·생략","than will infants who are not = 자주 겁먹지 않는 아기들")],
           [("frequently", "자주"), ("very likely", "~할 가능성이 매우 높다"),
            ("opportunity", "기회")],
           [("Thus, [[frequently]] frightened infants", "따라서 [[자주]] 겁을 먹는 아기들은"),
            ("[[will very likely have less time to explore]]", "[[탐색할 시간이 더 적을 가능성이 매우 높고]]"),
            ("and fewer [[opportunities]] to play", "놀 [[기회]]도 더 적을 것이다"),
            ("[[than will infants who are not]].", "[[그렇지 않은(자주 겁먹지 않는) 아기들보다]].")],
           [("겁을 자주 먹는 아기가 오히려 놀이 기회를 더 많이 얻는다는 내용이다.",
             "정반대야. 자주 겁먹는 아기는 그렇지 않은 아기보다 탐색·놀이 시간·기회가 '더 적다'는, 앞 문장의 결과를 정리한 거야."),
            ("아기들이 즐기는 놀이의 종류를 비교하는 문장이다.",
             "놀이 '종류'가 아니라 탐색·놀이의 '양(시간·기회)'을 비교해서 결과를 말하고 있어.")]),
        _S(4, raw[3], [("serve to+동사원형","'~하는 역할을 하다'"), ("조건절 if","성향이 유지된다면")],
           [("voluntary", "자발적인"), ("restraint", "억제, 제약"),
            ("serve to", "~하는 역할을 하다"), ("tendency", "성향, 경향"),
            ("maintain", "유지하다")],
           [("Such [[voluntary]] restraints", "그러한 [[자발적인]] 억제는"),
            ("[[may serve to slow down]]", "[[늦추는 역할을 할 수도 있다]]"),
            ("the social development of [[shy or anxious]] infants", "[[소심하거나 불안한]] 아기들의 사회성 발달을"),
            ("[[if these tendencies are maintained]]", "[[만약 이런 성향이 계속 유지된다면]]"),
            ("throughout their [[childhood]] years.", "그들의 [[유년기]] 내내")],
           [("이런 자기 억제가 사회성 발달을 오히려 촉진한다는 결론이다.",
             "촉진이 아니라 '늦출 수 있다'는 결론이야. 스스로 놀이를 접는 태도가 유년기 내내 이어지면 발달이 느려질 수 있다는 마무리야."),
            ("한때의 일시적 행동이라 발달에는 영향이 없다는 내용이다.",
             "일시적이라 영향이 없다는 게 아니라, '유년기 내내 유지되면' 발달을 늦출 수 있다는 조건부 결론이야.")]),
    ]

    return LecturePassage(title=title, source=source, item_no=item_no,
                          sentences=sentences, overview=overview,
                          analysis=SentenceAnalysis(sentences=items))
