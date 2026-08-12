"""API 없이 강의컨셉 교재(필생보) 렌더링/파이프라인을 검증하기 위한 목(mock) 데이터."""
from __future__ import annotations

from src.lecture_schemas import (Chunk, GrammarChip, LecturePassage,
                                 LectureSentence, Misread, Overview,
                                 RestatementChain, SentenceAnalysis,
                                 SentenceItem, Vocab)


def _S(id, english, role, grammar, vocab, chunks, misreads):
    return SentenceItem(
        id=id, english=english, role=role,
        grammar=[GrammarChip(tag=t, note=n) for t, n in grammar],
        vocab=[Vocab(word=w, meaning=m) for w, m in vocab],
        chunks=[Chunk(en=e, ko=k, blank=b) for e, k, b in chunks],
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
    )

    items = [
        _S(1, raw[0], "주제 제시", [("관계사 that","앞의 the role 을 that절이 수식"), ("분사구 including","주어를 부연 설명")],
           [("developmental", "발달의"), ("nonhuman primate", "인간이 아닌 영장류"),
            ("recognize", "인정하다, 인식하다"), ("play a role in", "~에서 역할을 하다")],
           [("Many developmental theorists and researchers,", "많은 발달 이론가들과 연구자들은,", False),
            ("including those studying human as well as nonhuman primate subjects,", "인간뿐 아니라 인간이 아닌 영장류를 연구 대상으로 삼는 사람들까지 포함해,", True),
            ("have recognized the role", "그 역할을 인정해 왔다", False),
            ("that fear can play in a primate's social development.", "두려움이 영장류의 사회적 발달에서 할 수 있는", True)],
           [("두려움이 사회성 발달과 무관하다는 것을 밝히는 문장이다.",
             "정반대야. 학자들이 두려움이 사회성 발달에 '역할을 한다'는 걸 인정해 왔다는, 두려움이 영향을 준다는 주제를 던지는 문장이야."),
            ("영장류를 연구하는 구체적 방법을 소개하는 문장이다.",
             "연구 방법 소개가 아니라, 두려움이 발달에 하는 역할을 학자들이 인정해 왔다는 '주제 제시'야.")]),
        _S(2, raw[1], "근거", [("부사절 when/until","시간·조건을 나타내는 종속절"), ("수동태 has been p.p.","아기가 '위로받는' 것")],
           [("infant", "아기, 유아"), ("seek out", "찾아 나서다"),
            ("exploratory", "탐색의"), ("reassure", "안심시키다"),
            ("attachment object", "애착 대상")],
           [("When an infant is frightened", "아기가 겁을 먹으면", False),
            ("it always seeks out its mother for protection and safety,", "그 아기는 항상 보호와 안전을 위해 엄마를 찾아 나선다,", False),
            ("and all exploratory and play activity stops", "그리고 모든 탐색과 놀이 활동이 멈춘다", False),
            ("until the infant has been sufficiently comforted and reassured", "그 아기가 충분히 위로받고 안심하게 될 때까지", True),
            ("by its attachment object.", "자신의 애착 대상에 의해", False)],
           [("아기가 두려움을 스스로 극복해 가는 과정을 설명한다.",
             "극복 과정이 아니라, 겁먹으면 엄마에게 가서 안심할 때까지 탐색·놀이가 '멈춘다'는, 주제를 뒷받침하는 근거 문장이야."),
            ("놀이가 아기의 두려움을 없애 준다는 내용이다.",
             "놀이가 두려움을 없앤다는 게 아니라, 반대로 겁먹으면 놀이가 멈춘다는 얘기야.")]),
        _S(3, raw[2], "결과 정리", [("비교급 than","'~보다 더 적다' 비교"), ("than절 도치·생략","than will infants who are not = 자주 겁먹지 않는 아기들")],
           [("frequently", "자주"), ("very likely", "~할 가능성이 매우 높다"),
            ("opportunity", "기회")],
           [("Thus, frequently frightened infants", "따라서 자주 겁을 먹는 아기들은", False),
            ("will very likely have less time to explore", "탐색할 시간이 더 적을 가능성이 매우 높고", False),
            ("and fewer opportunities to play", "놀 기회도 더 적을 (가능성이 높다)", False),
            ("than will infants who are not.", "그렇지 않은(자주 겁먹지 않는) 아기들보다", True)],
           [("겁을 자주 먹는 아기가 오히려 놀이 기회를 더 많이 얻는다는 내용이다.",
             "정반대야. 자주 겁먹는 아기는 그렇지 않은 아기보다 탐색·놀이 시간·기회가 '더 적다'는, 앞 문장의 결과를 정리한 거야."),
            ("아기들이 즐기는 놀이의 종류를 비교하는 문장이다.",
             "놀이 '종류'가 아니라 탐색·놀이의 '양(시간·기회)'을 비교해서 결과를 말하고 있어.")]),
        _S(4, raw[3], "결론", [("serve to+동사원형","'~하는 역할을 하다'"), ("조건절 if","성향이 유지된다면")],
           [("voluntary", "자발적인"), ("restraint", "억제, 제약"),
            ("serve to", "~하는 역할을 하다"), ("tendency", "성향, 경향"),
            ("maintain", "유지하다")],
           [("Such voluntary restraints may serve to slow down", "그러한 자발적인 억제는 늦추는 역할을 할 수 있다", True),
            ("the social development of shy or anxious infants", "소심하거나 불안한 아기들의 사회적 발달을", False),
            ("if these tendencies are maintained", "만약 이런 성향이 유지된다면", False),
            ("throughout their childhood years.", "그들의 유년기 내내", False)],
           [("이런 자기 억제가 사회성 발달을 오히려 촉진한다는 결론이다.",
             "촉진이 아니라 '늦출 수 있다'는 결론이야. 스스로 놀이를 접는 태도가 유년기 내내 이어지면 발달이 느려질 수 있다는 마무리야."),
            ("한때의 일시적 행동이라 발달에는 영향이 없다는 내용이다.",
             "일시적이라 영향이 없다는 게 아니라, '유년기 내내 유지되면' 발달을 늦출 수 있다는 조건부 결론이야.")]),
    ]

    return LecturePassage(title=title, source=source, item_no=item_no,
                          sentences=sentences, overview=overview,
                          analysis=SentenceAnalysis(sentences=items))
