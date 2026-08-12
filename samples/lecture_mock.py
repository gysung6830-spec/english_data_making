"""API 없이 강의컨셉 교재(필생보) 렌더링/파이프라인을 검증하기 위한 목(mock) 데이터."""
from __future__ import annotations

from src.lecture_schemas import (Chunk, LecturePassage, LectureSentence,
                                 Overview, RestatementChain, SentenceAnalysis,
                                 SentenceItem, TransProblem, Vocab)


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
        structure_reason="1문장에서 '두려움이 사회성 발달에 역할을 한다'고 던지고, 2문장에서 아기 행동으로 근거를 대고, Thus로 결과를 정리해.",
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
        analogy_name="놀이터 벤치",
        analogy_desc="놀이터에서 겁먹으면 엄마가 앉은 벤치로 달려가 안 놀고 앉아 있는 아이를 떠올리며 읽어.",
        gist="두려움을 자주 느끼는 아기는 엄마 품으로 돌아가느라 탐색·놀이 기회를 잃고, 그 성향이 유년기 내내 이어지면 사회적 발달이 느려질 수 있다는 거야!",
    )

    items = [
        SentenceItem(
            id=1, english=raw[0], syntax_tag="관계사절(play a role)·분사구",
            vocab=[Vocab(word="developmental", meaning="발달의"),
                   Vocab(word="nonhuman primate", meaning="인간이 아닌 영장류"),
                   Vocab(word="recognize", meaning="인정하다, 인식하다"),
                   Vocab(word="play a role in", meaning="~에서 역할을 하다")],
            chunks=[Chunk(en="Many developmental theorists and researchers,", ko="많은 발달 이론가들과 연구자들은,"),
                    Chunk(en="including those studying human as well as nonhuman primate subjects,", ko="인간뿐 아니라 인간이 아닌 영장류를 연구 대상으로 삼는 사람들까지 포함해,"),
                    Chunk(en="have recognized the role", ko="그 역할을 인정해 왔다"),
                    Chunk(en="that fear can play in a primate's social development.", ko="두려움이 영장류의 사회적 발달에서 할 수 있는")],
            catch="학자들이 두려움이 사회성 발달에 한몫한다는 걸 인정해 왔다 — 글의 주제를 던지는 문장이야.",
            easy_example="놀이터 벤치 얘기를 꺼내기 전에 '겁먹는 게 노는 데 영향을 준다'는 걸 전문가들도 안다고 깔아주는 셈이야.",
        ),
        SentenceItem(
            id=2, english=raw[1], syntax_tag="부사절(when/until)·수동태",
            vocab=[Vocab(word="infant", meaning="아기, 유아"),
                   Vocab(word="seek out", meaning="찾아 나서다"),
                   Vocab(word="exploratory", meaning="탐색의"),
                   Vocab(word="reassure", meaning="안심시키다"),
                   Vocab(word="attachment object", meaning="애착 대상")],
            chunks=[Chunk(en="When an infant is frightened", ko="아기가 겁을 먹으면"),
                    Chunk(en="it always seeks out its mother for protection and safety,", ko="그 아기는 항상 보호와 안전을 위해 엄마를 찾아 나선다,"),
                    Chunk(en="and all exploratory and play activity stops", ko="그리고 모든 탐색과 놀이 활동이 멈춘다"),
                    Chunk(en="until the infant has been sufficiently comforted and reassured", ko="그 아기가 충분히 위로받고 안심하게 될 때까지"),
                    Chunk(en="by its attachment object.", ko="자신의 애착 대상에 의해")],
            catch="겁먹으면 엄마에게 달려가고 안심할 때까지 탐색·놀이가 완전히 멈춘다 — 주제를 뒷받침하는 구체 근거야.",
            easy_example="놀이터에서 무서운 일이 생기면 곧장 엄마 벤치로 뛰어가 안심될 때까지 미끄럼틀엔 손도 안 대는 장면이야.",
        ),
        SentenceItem(
            id=3, english=raw[2], syntax_tag="비교급 than절 도치·생략",
            vocab=[Vocab(word="frequently", meaning="자주"),
                   Vocab(word="very likely", meaning="~할 가능성이 매우 높다"),
                   Vocab(word="opportunity", meaning="기회")],
            chunks=[Chunk(en="Thus, frequently frightened infants", ko="따라서 자주 겁을 먹는 아기들은"),
                    Chunk(en="will very likely have less time to explore", ko="탐색할 시간이 더 적을 가능성이 매우 높고"),
                    Chunk(en="and fewer opportunities to play", ko="놀 기회도 더 적을 (가능성이 높다)"),
                    Chunk(en="than will infants who are not.", ko="그렇지 않은 아기들보다")],
            catch="겁을 자주 먹는 아기는 탐색·놀이 시간과 기회 자체가 줄어든다 — 앞 문장의 결과를 정리해.",
            easy_example="벤치에 자주 앉는 아이는 계속 뛰어노는 친구보다 노는 시간 총합이 확 적어지는 거야.",
        ),
        SentenceItem(
            id=4, english=raw[3], syntax_tag="조건절·serve to+동사원형",
            vocab=[Vocab(word="voluntary", meaning="자발적인"),
                   Vocab(word="restraint", meaning="억제, 제약"),
                   Vocab(word="serve to", meaning="~하는 역할을 하다"),
                   Vocab(word="tendency", meaning="성향, 경향"),
                   Vocab(word="maintain", meaning="유지하다")],
            chunks=[Chunk(en="Such voluntary restraints may serve to slow down", ko="그러한 자발적인 억제는 늦추는 역할을 할 수 있다"),
                    Chunk(en="the social development of shy or anxious infants", ko="소심하거나 불안한 아기들의 사회적 발달을"),
                    Chunk(en="if these tendencies are maintained", ko="만약 이런 성향이 유지된다면"),
                    Chunk(en="throughout their childhood years.", ko="그들의 유년기 내내")],
            catch="스스로 놀이를 접는 이런 태도가 유년기 내내 계속되면 사회성 발달이 느려질 수 있다 — 글의 결론이야.",
            easy_example="몇 번 벤치에 앉는 건 괜찮은데, 몇 년 동안 계속 벤치만 지키면 친구들과 어울리는 법 배우는 속도가 느려진다는 마무리야.",
        ),
    ]

    problems = [
        TransProblem(
            no=1, sentence_id=1, focus="the role that fear can play",
            kind="객관식",
            question="밑줄 친 부분의 우리말 해석으로 알맞은 것은?",
            options=["두려움이 연기하는 역할",
                     "두려움이 (영장류의 사회적 발달에서) 할 수 있는 역할",
                     "두려움이 놀이를 하는 역할"],
            answer_index=1,
            answer_text="두려움이 (영장류의 사회적 발달에서) 할 수 있는 역할",
            explanation="play a role in(~에서 역할을 하다)이 관계사 that 으로 쪼개진 형태야. play를 '연기하다·놀다'로 읽으면 오역.",
        ),
        TransProblem(
            no=2, sentence_id=2, focus="until the infant has been sufficiently comforted",
            kind="객관식",
            question="until 절의 의미로 알맞은 것은?",
            options=["아기가 충분히 위로받을 때까지 (활동이 멈춘 상태가 계속됨)",
                     "아기가 위로하기 전까지 멈추지 않음",
                     "아기가 위로받자마자 활동을 멈춤"],
            answer_index=0,
            answer_text="아기가 충분히 위로받을 때까지 (활동이 멈춘 상태가 계속됨)",
            explanation="until은 '~까지 (그 상태가) 계속'이고, has been comforted는 수동이라 '위로받는다'야. 반대로 꼬아 읽지 말 것.",
        ),
        TransProblem(
            no=3, sentence_id=3, focus="than will infants who are not",
            kind="주관식",
            question="비교 대상인 'infants who are not'이 가리키는 아기를 우리말로 쓰시오.",
            options=[],
            answer_index=-1,
            answer_text="자주 겁먹지 않는 아기들 (not frequently frightened)",
            explanation="than 뒤에 도치·생략이 있어 who are not = who are not frequently frightened. '하지 않을 아기'가 아니야.",
        ),
        TransProblem(
            no=4, sentence_id=4, focus="serve to slow down",
            kind="주관식",
            question="밑줄 친 serve to slow down 을 우리말로 해석하시오.",
            options=[],
            answer_index=-1,
            answer_text="늦추는 역할을 하다 / 늦추는 작용을 하다",
            explanation="serve를 '봉사하다'로 읽으면 오역. serve to+동사원형은 '~하는 역할을 하다'.",
        ),
    ]

    return LecturePassage(title=title, source=source, item_no=item_no,
                          sentences=sentences, overview=overview,
                          analysis=SentenceAnalysis(sentences=items, problems=problems))
