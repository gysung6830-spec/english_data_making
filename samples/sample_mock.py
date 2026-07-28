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
        train=schemas.TrainSection(
            topic_training=schemas.TopicTraining(
                clues=[
                    schemas.TrainClue(word="curiosity", meaning="호기심"),
                    schemas.TrainClue(word="explore / inquire", meaning="탐구하다 / 질문하다"),
                    schemas.TrainClue(word="learning / remember", meaning="학습 / 기억하다"),
                    schemas.TrainClue(word="ask questions", meaning="질문하다"),
                ],
                material="호기심과 학습",
                topic="호기심은 학습과 기억을 돕는 원동력이므로, 교육은 암기보다 질문하는 태도를 길러야 한다.",
                steps=[
                    "제목과 첫 문장을 보고 '무엇에 관한 글'인지 한 단어로 잡아 봐.",
                    "반복되는 단어(curiosity, explore, learning)에 동그라미 쳐 봐 — 그게 소재야.",
                    "글쓴이가 그 소재를 '좋다/필요하다'처럼 어떻게 평가하는지 찾아봐.",
                    "소재 + 글쓴이의 생각 = 주제. 한 문장으로 이어 붙여 봐.",
                ],
            ),
            questions=[
                schemas.TrainQuestion(
                    qtype="주제",
                    instruction="다음 글의 주제로 가장 적절한 것은?",
                    passage_excerpt="",
                    choices=[
                        schemas.TrainChoice(symbol="①", text="the importance of memorizing correct answers",
                                            correct=False, reason="지문과 반대 — 글은 암기보다 질문을 강조함."),
                        schemas.TrainChoice(symbol="②", text="why curiosity matters in learning",
                                            correct=True, reason="소재(호기심)+글쓴이 생각(학습에 중요)을 그대로 담음 — 정답."),
                        schemas.TrainChoice(symbol="③", text="the history of modern education systems",
                                            correct=False, reason="지문에 없는 내용."),
                        schemas.TrainChoice(symbol="④", text="how teachers should grade student exams",
                                            correct=False, reason="너무 좁음 — 지문 일부(시험)만 다룸."),
                        schemas.TrainChoice(symbol="⑤", text="the difficulty of studying science subjects",
                                            correct=False, reason="지문에 없는 내용."),
                    ],
                    answer="②",
                    solution=(
                        "먼저 소재를 잡아요: 반복되는 단어가 curiosity라 '호기심'이 소재예요. "
                        "글쓴이는 호기심이 학습·기억에 좋다고 말하죠. 그래서 '호기심이 학습에서 왜 중요한가'가 주제예요. "
                        "①은 반대로 말했고, ③⑤는 지문에 없는 내용, ④는 시험 얘기만 하는 너무 좁은 선지라 지워요."),
                ),
                schemas.TrainQuestion(
                    qtype="요지",
                    instruction="다음 글의 요지로 가장 적절한 것은?",
                    passage_excerpt="",
                    choices=[
                        schemas.TrainChoice(symbol="①", text="정답을 빨리 외우는 학생이 성적이 좋다.",
                                            correct=False, reason="지문과 반대."),
                        schemas.TrainChoice(symbol="②", text="교육은 호기심을 억눌러 집중력을 길러야 한다.",
                                            correct=False, reason="반대로 말함 — 호기심은 길러야 할 대상."),
                        schemas.TrainChoice(symbol="③", text="호기심을 자극하는 교육이 학습에 효과적이다.",
                                            correct=True, reason="소재+주장을 정확히 담음 — 정답."),
                        schemas.TrainChoice(symbol="④", text="모든 학생은 항상 스스로 공부해야만 한다.",
                                            correct=False, reason="'모든/항상/~만' 같은 지나친 단정 — 경계 선지."),
                        schemas.TrainChoice(symbol="⑤", text="시험 성적은 학습에서 가장 중요하지 않다.",
                                            correct=False, reason="지문이 강조한 핵심(호기심)이 빠짐."),
                    ],
                    answer="③",
                    solution=(
                        "요지는 주제를 '한 문장 주장'으로 바꾼 거예요. 호기심이 학습에 좋다는 게 핵심이니 ③이 정답. "
                        "④처럼 '모든/항상/~만'이 들어간 선지는 지나치게 단정적이라 대개 오답이에요."),
                ),
                schemas.TrainQuestion(
                    qtype="빈칸추론",
                    instruction="다음 빈칸에 들어갈 말로 가장 적절한 것은?",
                    passage_excerpt="Education should encourage learners to _______ rather than simply memorize answers.",
                    choices=[
                        schemas.TrainChoice(symbol="①", text="obey rules", correct=False, reason="지문 내용과 무관."),
                        schemas.TrainChoice(symbol="②", text="explore and inquire", correct=True,
                                            reason="반복 어구(explore/inquire)와 일치 — 정답."),
                        schemas.TrainChoice(symbol="③", text="avoid mistakes", correct=False, reason="지문에 없는 내용."),
                        schemas.TrainChoice(symbol="④", text="memorize faster", correct=False, reason="빈칸 뒤 '단순 암기 말고'와 모순."),
                        schemas.TrainChoice(symbol="⑤", text="compete harder", correct=False, reason="지문에 없는 내용."),
                    ],
                    answer="②",
                    solution=(
                        "빈칸은 'rather than memorize(암기 말고)'와 대비돼요. 그러니 암기의 반대인 '탐구·질문'이 들어가야죠. "
                        "본문에서 반복된 explore, inquire와 같은 ②가 정답이에요."),
                ),
            ],
            reading_tip=(
                "선지는 '지문에 있었나?'를 기준으로 읽어요. always·never·only·모든처럼 지나치게 단정적인 말은 대개 오답이고, "
                "지문 일부만 말하는 '너무 좁은' 선지나 지문 밖까지 넓히는 '너무 넓은' 선지도 지워요. "
                "남는 하나가 소재+주장을 함께 담고 있으면 그게 정답입니다."),
        ),
    )
