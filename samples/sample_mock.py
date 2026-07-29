"""API 없이 파이프라인/디자인을 검증하기 위한 목(mock) 데이터.

pipeline 을 --mock 으로 실행하면 실제 API 대신 이 데이터를 사용한다.
스키마와 동일한 구조라서 렌더링 결과를 미리 확인할 수 있다.
"""
from __future__ import annotations

from src import schemas


def mock_report(title: str = "The Value of Curiosity", source: str = "Mock Reader 2024") -> schemas.Report:
    return schemas.Report(
        title=title,
        source=source,
        summary=schemas.SummarySection(
            overall="호기심은 학습과 성장의 원동력이므로 교육은 정답 암기보다 질문하는 태도를 길러야 한다.",
        ),
        literal=schemas.LiteralSection(sentences=[
            schemas.Sentence(no=1, chunks=[
                schemas.Chunk(
                    english="Curiosity drives us",
                    syntax="3형식 (S+V+O)",
                    korean="호기심은 우리를 이끈다",
                    words=[schemas.KeyWord(word="curiosity", meaning="호기심"),
                           schemas.KeyWord(word="drive", meaning="이끌다, 몰아가다")],
                ),
                schemas.Chunk(
                    english="to explore the unknown",
                    syntax="to부정사(부사적 용법, 목적)",
                    korean="미지의 것을 탐구하도록",
                    words=[schemas.KeyWord(word="explore", meaning="탐구하다"),
                           schemas.KeyWord(word="the unknown", meaning="미지의 것")],
                ),
            ]),
            schemas.Sentence(no=2, chunks=[
                schemas.Chunk(
                    english="Studies show that curious students",
                    syntax="that절(목적어), 명사구 주어",
                    korean="연구는 보여준다 / 호기심 많은 학생들이",
                    words=[schemas.KeyWord(word="curious", meaning="호기심 많은")],
                ),
                schemas.Chunk(
                    english="remember information longer",
                    syntax="비교급 부사(longer)",
                    korean="정보를 더 오래 기억한다는 것을",
                    words=[schemas.KeyWord(word="remember", meaning="기억하다")],
                ),
            ]),
        ]),
        grammar=schemas.GrammarSection(items=[
            schemas.GrammarItem(no=i, point=p, example=ex, explanation=exp, sentence_no=(i - 1) % 2 + 1)
            for i, (p, ex, exp) in enumerate([
                ("to부정사의 부사적 용법", "to explore the unknown", "'~하기 위해'라는 목적을 나타낸다."),
                ("that 명사절", "Studies show that curious students...", "show 의 목적어로 that절이 쓰였다."),
                ("비교급", "remember information longer", "long 의 비교급 longer 로 정도 차이를 표현."),
                ("주어-동사 수일치", "Curiosity drives us", "단수 주어에 3인칭 단수 동사 drives."),
                ("관계대명사 which", "a skill which improves", "선행사를 수식하는 형용사절을 이끈다."),
                ("현재완료", "has become essential", "과거부터 현재까지의 결과를 나타낸다."),
                ("동명사 주어", "Asking questions matters", "동명사구가 문장의 주어로 쓰였다."),
                ("수동태", "is encouraged in class", "행위의 대상을 주어로 하는 be+p.p."),
                ("접속사 because", "because it fuels learning", "이유를 나타내는 부사절을 이끈다."),
                ("가주어 it", "It is important to ask", "진주어 to부정사를 뒤로 보낸 구조."),
            ], start=1)
        ]),
        vocab=schemas.VocabSection(items=[
            schemas.VocabItem(no=i, word=w, meaning=m, synonyms=s, antonyms=a, example=e)
            for i, (w, m, s, a, e) in enumerate([
                ("curiosity", "호기심", "inquisitiveness", "indifference", "Curiosity drives us to explore."),
                ("explore", "탐구하다", "investigate", "ignore", "to explore the unknown"),
                ("essential", "필수적인", "vital, crucial", "trivial", "has become essential"),
                ("encourage", "장려하다", "promote", "discourage", "is encouraged in class"),
                ("fuel", "촉진하다, 연료를 대다", "stimulate", "hinder", "it fuels learning"),
                ("retain", "유지하다, 기억하다", "keep", "lose", "retain information longer"),
                ("motivation", "동기", "drive", "apathy", "boosts motivation"),
                ("creativity", "창의성", "originality", "conformity", "sparks creativity"),
                ("inquire", "질문하다, 탐구하다", "ask", "answer", "students who inquire"),
                ("expand", "확장하다", "broaden", "shrink", "expand their knowledge"),
                ("engage", "몰두하다", "involve", "withdraw", "engage with problems"),
                ("insight", "통찰", "understanding", "confusion", "gain new insight"),
            ], start=1)
        ], english_summary=(
            "Curiosity is essential because it fuels motivation, helps students retain "
            "information, and sparks creativity. Therefore, education should encourage "
            "learners to explore and inquire rather than simply memorize answers."
        ), english_summary_ko=(
            "호기심은 동기를 북돋우고, 학생들이 정보를 오래 기억하게 하며, 창의력을 자극하므로 필수적이다. "
            "따라서 교육은 학습자가 단순히 답을 외우기보다 탐구하고 질문하도록 장려해야 한다."
        )),
        structure=schemas.StructureSection(
            flow_type="logic",
            genre_reason="주장과 근거로 이루어진 논설문이므로 논리 전개형으로 분석함.",
            easy_explanation="한마디로 '궁금해야 공부가 된다' 이거임. 정답 외우기보다 스스로 질문하게 하는 게 훨씬 남는 장사.",
            examples=[
                "좋아하는 아이돌 정보는 안 외워도 줄줄 나오는데, 그게 바로 궁금해서 스스로 파고들었기 때문인 거랑 똑같음.",
                "게임 공략을 누가 시켜서가 아니라 궁금해서 찾아보면 기가 막히게 기억나는 원리임.",
            ],
            stages=[
                schemas.FlowStage(stage="[도입]", content="호기심의 정의를 제시하고 화제를 던짐", evidence="문장 1"),
                schemas.FlowStage(stage="[전개]", content="호기심이 학습·기억에 미치는 효과를 근거로 듦", evidence="문장 2"),
                schemas.FlowStage(stage="[상술]", content="연구 결과로 주장을 뒷받침함", evidence="문장 2"),
                schemas.FlowStage(stage="[결론]", content="질문 장려 교육의 필요성을 강조함", evidence="문장 3"),
            ],
        ),
        exam=schemas.ExamSection(items=[
            schemas.ExamItem(question_type="지칭추론(대명사)", content=(
                "1문장 - us - (호기심을 지닌 우리 사람들)\n"
                "2문장 - they가 나오면 - (curious students, 호기심 많은 학생들)")),
            schemas.ExamItem(question_type="함축의미", content=(
                "1문장 \"drives us to explore the unknown\"\n"
                "· 문맥상 의미: 호기심이 우리를 미지의 영역으로 나아가게 하는 원동력이 됨\n"
                "· 영어 정답 표현: curiosity is what pushes people to investigate what they don't yet know\n"
                "⚠️ 직역 함정: 'drives'를 '운전하다'로, 또는 단순히 '탐험하게 한다'로만 읽으면 오답")),
            schemas.ExamItem(question_type="서술형", content=(
                "Children who are encouraged to ask questions tend to retain "
                "their curiosity far longer than those who are simply given answers.\n"
                "관계대명사(who) 두 번, 분사구문(encouraged), 비교구문(longer than), "
                "5형식(are given)")),
        ]),
    )


def mock_worksheet(title: str = "The Value of Curiosity",
                   source: str = "Mock Reader 2024") -> schemas.Worksheet:
    """API 없이 서술형 교재 디자인을 미리 볼 수 있는 목 데이터."""
    passage = (
        "Curiosity drives us to explore the unknown. Studies show that curious "
        "students remember information longer and stay motivated in class. When "
        "learners are encouraged to ask questions, they retain their curiosity far "
        "longer than those who are simply given answers. Therefore, education should "
        "encourage learners to inquire rather than simply memorize answers, because "
        "curiosity fuels creativity and lifelong learning."
    )
    return schemas.Worksheet(
        title=title,
        source=source,
        passage=passage,
        summary=schemas.WSSummaryType(items=[
            schemas.WSSummaryItem(
                sentence="Curious learners tend to [[A]] information longer and stay [[B]] in class.",
                blanks=[
                    schemas.WSSummaryBlank(label="A", answer="remember", meaning="기억하다"),
                    schemas.WSSummaryBlank(label="B", answer="motivated", meaning="동기부여된"),
                ]),
            schemas.WSSummaryItem(
                sentence="Education should [[A]] students to ask questions rather than [[B]] answers.",
                blanks=[
                    schemas.WSSummaryBlank(label="A", answer="encourage", meaning="장려하다"),
                    schemas.WSSummaryBlank(label="B", answer="memorize", meaning="암기하다"),
                ]),
            schemas.WSSummaryItem(
                sentence="Curiosity [[A]] us to explore the unknown and fuels lifelong [[B]].",
                blanks=[
                    schemas.WSSummaryBlank(label="A", answer="drives", meaning="이끌다"),
                    schemas.WSSummaryBlank(label="B", answer="learning", meaning="학습"),
                ]),
        ]),
        paraphrase=schemas.WSParaphraseType(questions=[
            schemas.WSParaphraseQ(
                original="Curious students remember information longer.",
                options=[
                    "Students who are curious retain what they learn for a longer time.",
                    "Students forget information more quickly when they are curious.",
                    "Curiosity has no effect on how long students recall information.",
                    "Teachers remember curious students for a long time.",
                    "Information makes students more curious over time.",
                ],
                answer=1,
                explanation=("① remember longer → retain for a longer time 로 의미 보존(정답). "
                             "②는 반의어(forget quickly), ③은 효과 부정으로 의미가 뒤집힘.")),
            schemas.WSParaphraseQ(
                original="Education should encourage learners to ask questions.",
                options=[
                    "Learners should discourage education from asking questions.",
                    "Education ought to promote learners' questioning.",
                    "Education must stop learners from asking too many questions.",
                    "Questions should be answered by education, not learners.",
                    "Learners should memorize questions given by their teachers.",
                ],
                answer=2,
                explanation="② encourage→promote, ask questions→questioning 로 동일 의미(정답)."),
            schemas.WSParaphraseQ(
                original="Curiosity drives us to explore the unknown.",
                options=[
                    "The unknown drives our curiosity away from exploration.",
                    "We explore the unknown only when curiosity disappears.",
                    "Curiosity pushes us to investigate what we do not yet know.",
                    "Exploring the unknown makes us less curious over time.",
                    "The unknown remains unexplored despite our curiosity.",
                ],
                answer=3,
                explanation="③ drives us to explore → pushes us to investigate 로 의미 보존(정답)."),
        ]),
        arrange=schemas.WSArrangeType(
            ideas=[
                schemas.WSArrangeItem(
                    korean="호기심은 학습을 촉진하므로 교육에서 장려되어야 한다.",
                    given_words=["be", "curiosity", "in", "encouraged", "should",
                                 "education", "because", "it", "fuels", "learning"],
                    word_count="10단어",
                    answer="Curiosity should be encouraged in education because it fuels learning.",
                    explanation="주어(Curiosity)+조동사 수동태(should be encouraged) 뼈대를 먼저 잡는다."),
                schemas.WSArrangeItem(
                    korean="호기심 많은 학생은 정보를 더 오래 기억한다.",
                    given_words=["students", "remember", "curious", "longer", "information"],
                    word_count="5단어",
                    answer="Curious students remember information longer.",
                    explanation="형용사(curious)+주어, 비교급 부사(longer) 위치."),
            ],
            titles=[
                schemas.WSArrangeItem(
                    korean="호기심의 힘",
                    given_words=["of", "the", "curiosity", "power"],
                    word_count="4단어",
                    answer="The Power of Curiosity",
                    explanation="제목은 'the + 명사 + of + 명사' 명사구 형태."),
                schemas.WSArrangeItem(
                    korean="질문이 학습을 이끄는 방법",
                    given_words=["how", "drives", "questioning", "learning"],
                    word_count="4단어",
                    answer="How Questioning Drives Learning",
                    explanation="의문사 How + 동명사 주어(Questioning)."),
            ]),
        compose=schemas.WSComposeType(items=[
            schemas.WSComposeItem(
                korean="질문하도록 격려받는 아이들은 호기심을 더 오래 유지한다.",
                given_words=["encourage", "retain"],
                conditions=["관계대명사 who 사용", "분사(수동) 활용", "비교급 longer 사용"],
                word_count="12단어",
                answer="Children who are encouraged to ask questions retain their curiosity longer.",
                explanation="who 관계절 + are encouraged(수동) + longer(비교급)."),
            schemas.WSComposeItem(
                korean="호기심은 우리가 미지의 것을 탐구하도록 이끈다.",
                given_words=["drive", "explore"],
                conditions=["5형식(drive+O+to부정사) 사용"],
                word_count="7단어",
                answer="Curiosity drives us to explore the unknown.",
                explanation="drive + 목적어(us) + to explore 의 5형식 구조."),
            schemas.WSComposeItem(
                korean="질문하는 것은 학습에서 중요하다.",
                given_words=["ask", "matter"],
                conditions=["동명사 주어 사용"],
                word_count="6단어",
                answer="Asking questions matters in learning.",
                explanation="동명사구(Asking questions)가 주어."),
        ]),
        choice=schemas.WSChoiceType(sets=[
            schemas.WSClozeSet(
                choices=["retain", "explore", "motivated", "memorize", "discourage"],
                sentences=[
                    schemas.WSClozeSentence(label="A",
                        text="Curious students [[A]] information far longer than their peers.",
                        answer="retain"),
                    schemas.WSClozeSentence(label="B",
                        text="A good teacher inspires learners to [[B]] the unknown with confidence.",
                        answer="explore"),
                    schemas.WSClozeSentence(label="C",
                        text="Students who ask questions stay [[C]] throughout the lesson.",
                        answer="motivated"),
                    schemas.WSClozeSentence(label="D",
                        text="Rote drills only force children to [[D]] answers without understanding.",
                        answer="memorize"),
                ],
                unused="discourage",
                explanation="A retain, B explore, C motivated, D memorize 가 각각 들어가고 "
                            "⑤ discourage(막다)만 문맥상 쓸 곳이 없다."),
            schemas.WSClozeSet(
                choices=["fuels", "curiosity", "lifelong", "abrupt", "creativity"],
                sentences=[
                    schemas.WSClozeSentence(label="A",
                        text="A sense of wonder [[A]] the desire to keep learning.",
                        answer="fuels"),
                    schemas.WSClozeSentence(label="B",
                        text="Genuine [[B]] leads people to question what they already know.",
                        answer="curiosity"),
                    schemas.WSClozeSentence(label="C",
                        text="Reading widely supports [[C]] learning well into old age.",
                        answer="lifelong"),
                    schemas.WSClozeSentence(label="D",
                        text="Asking questions sparks the [[D]] needed to solve new problems.",
                        answer="creativity"),
                ],
                unused="abrupt",
                explanation="A fuels, B curiosity, C lifelong, D creativity 가 들어가고 "
                            "④ abrupt(갑작스러운)는 어느 빈칸과도 어울리지 않는다."),
        ]),
        error=schemas.WSErrorType(items=[
            schemas.WSErrorItem(
                text="Curiosity drive us to explore the unknown.",
                error="drive", correction="drives",
                explanation="주어 Curiosity 는 3인칭 단수이므로 동사에 -s (수일치)."),
            schemas.WSErrorItem(
                text="Curious students remembers information longer.",
                error="remembers", correction="remember",
                explanation="복수 주어 students 에는 동사원형 remember (수일치)."),
            schemas.WSErrorItem(
                text="Children who is encouraged to ask questions stay curious.",
                error="is", correction="are",
                explanation="관계대명사 who 의 선행사가 복수(Children)이므로 are."),
            schemas.WSErrorItem(
                text="It is important asking questions in class.",
                error="asking", correction="to ask",
                explanation="가주어 It 의 진주어는 to부정사(to ask)."),
        ]),
    )
