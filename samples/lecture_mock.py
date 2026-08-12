"""API 없이 강의컨셉 교재(필생보) 렌더링/파이프라인을 검증하기 위한 목(mock) 데이터."""
from __future__ import annotations

from src.lecture_schemas import (Chunk, LecturePassage, LectureSentence,
                                 Overview, RestatementChain, SentenceAnalysis,
                                 SentenceItem, Vocab)


def _S(id, english, syntax, vocab, chunks, options, ans, expl=""):
    return SentenceItem(
        id=id, english=english, syntax_tag=syntax,
        vocab=[Vocab(word=w, meaning=m) for w, m in vocab],
        chunks=[Chunk(en=e, ko=k, blank=b) for e, k, b in chunks],
        content_options=options, content_answer_index=ans, content_explanation=expl,
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
        _S(1, raw[0], "관계사절(play a role)·분사구",
           [("developmental", "발달의"), ("nonhuman primate", "인간이 아닌 영장류"),
            ("recognize", "인정하다, 인식하다"), ("play a role in", "~에서 역할을 하다")],
           [("Many developmental theorists and researchers,", "많은 발달 이론가들과 연구자들은,", False),
            ("including those studying human as well as nonhuman primate subjects,", "인간뿐 아니라 인간이 아닌 영장류를 연구 대상으로 삼는 사람들까지 포함해,", True),
            ("have recognized the role", "그 역할을 인정해 왔다", False),
            ("that fear can play in a primate's social development.", "두려움이 영장류의 사회적 발달에서 할 수 있는", True)],
           ["학자들이 두려움이 사회성 발달에 하는 역할을 인정해 왔다는, 주제를 던지는 문장",
            "두려움이 사회성 발달과 무관하다는 주장을 반박하는 문장",
            "영장류 연구 방법을 소개하는 문장"], 0,
           "play a role in(~에서 역할을 하다)이 관계사로 쪼개진 형태. 주제 제시 문장이야."),
        _S(2, raw[1], "부사절(when/until)·수동태",
           [("infant", "아기, 유아"), ("seek out", "찾아 나서다"),
            ("exploratory", "탐색의"), ("reassure", "안심시키다"),
            ("attachment object", "애착 대상")],
           [("When an infant is frightened", "아기가 겁을 먹으면", False),
            ("it always seeks out its mother for protection and safety,", "그 아기는 항상 보호와 안전을 위해 엄마를 찾아 나선다,", False),
            ("and all exploratory and play activity stops", "그리고 모든 탐색과 놀이 활동이 멈춘다", False),
            ("until the infant has been sufficiently comforted and reassured", "그 아기가 충분히 위로받고 안심하게 될 때까지", True),
            ("by its attachment object.", "자신의 애착 대상에 의해", False)],
           ["겁먹으면 엄마에게 가고, 안심할 때까지 탐색·놀이가 멈춘다는 근거",
            "아기가 엄마를 위로해 주는 장면",
            "아기가 놀이를 통해 두려움을 극복한다는 내용"], 0,
           "until은 '~까지 (멈춘 상태가) 계속'이고 has been comforted는 수동('위로받는다')."),
        _S(3, raw[2], "비교급 than절 도치·생략",
           [("frequently", "자주"), ("very likely", "~할 가능성이 매우 높다"),
            ("opportunity", "기회")],
           [("Thus, frequently frightened infants", "따라서 자주 겁을 먹는 아기들은", False),
            ("will very likely have less time to explore", "탐색할 시간이 더 적을 가능성이 매우 높고", False),
            ("and fewer opportunities to play", "놀 기회도 더 적을 (가능성이 높다)", False),
            ("than will infants who are not.", "그렇지 않은(자주 겁먹지 않는) 아기들보다", True)],
           ["자주 겁먹는 아기는 탐색·놀이 시간과 기회가 줄어든다는 결과 정리",
            "겁먹는 아기가 오히려 더 많이 논다는 내용",
            "아기들의 놀이 종류를 비교하는 문장"], 0,
           "than 뒤 도치·생략. who are not = 자주 겁먹지 '않는' 아기들이 비교 대상."),
        _S(4, raw[3], "조건절·serve to+동사원형",
           [("voluntary", "자발적인"), ("restraint", "억제, 제약"),
            ("serve to", "~하는 역할을 하다"), ("tendency", "성향, 경향"),
            ("maintain", "유지하다")],
           [("Such voluntary restraints may serve to slow down", "그러한 자발적인 억제는 늦추는 역할을 할 수 있다", True),
            ("the social development of shy or anxious infants", "소심하거나 불안한 아기들의 사회적 발달을", False),
            ("if these tendencies are maintained", "만약 이런 성향이 유지된다면", False),
            ("throughout their childhood years.", "그들의 유년기 내내", False)],
           ["스스로 놀이를 접는 태도가 유년기 내내 이어지면 사회성 발달이 느려진다는 결론",
            "자발적인 봉사가 발달을 돕는다는 내용",
            "억제가 발달을 빠르게 한다는 내용"], 0,
           "serve를 '봉사하다'로 읽으면 오역. serve to+동사원형='~하는 역할을 하다'. 결론 문장."),
    ]

    return LecturePassage(title=title, source=source, item_no=item_no,
                          sentences=sentences, overview=overview,
                          analysis=SentenceAnalysis(sentences=items))
