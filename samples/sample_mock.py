"""API 없이 파이프라인/디자인을 검증하기 위한 목(mock) 데이터.

pipeline 을 --mock 으로 실행하면 실제 API 대신 이 데이터를 사용한다.
스키마와 동일한 구조라서 렌더링 결과를 미리 확인할 수 있다.
"""
from __future__ import annotations

from src import schemas


def mock_report(title: str = "The Value of Curiosity", source: str = "Mock Reader 2024",
                item_no: str = "") -> schemas.Report:
    return schemas.Report(
        title=title,
        source=source,
        item_no=item_no,
        summary=schemas.SummarySection(
            overall="호기심은 학습과 성장의 원동력이므로 교육은 정답 암기보다 질문하는 태도를 길러야 한다.",
            theme_en="The Value of Curiosity in Learning",
            keywords=["호기심", "학습과 성장의 원동력", "질문하는 태도"],
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
            schemas.Sentence(
                no=3,
                english="Curiosity is essential because it can fuel motivation and creativity.",
                translation="호기심은 동기와 창의성을 촉진할 수 있기에 필수적이다.",
                chunks=[
                    schemas.Chunk(
                        english="Curiosity is essential",
                        syntax="2형식(S+V+C)",
                        korean="호기심은 필수적이다",
                        words=[schemas.KeyWord(word="essential", meaning="필수적인")],
                    ),
                    schemas.Chunk(
                        english="because it can fuel motivation and creativity",
                        syntax="이유의 부사절(because)",
                        korean="그것이 동기와 창의성을 촉진할 수 있기 때문에",
                        words=[schemas.KeyWord(word="fuel", meaning="촉진하다, 연료를 대다"),
                               schemas.KeyWord(word="motivation", meaning="동기"),
                               schemas.KeyWord(word="creativity", meaning="창의성")],
                    ),
                ],
            ),
            schemas.Sentence(
                no=4,
                english="Teachers who encourage students to inquire help them retain and expand their knowledge.",
                translation="학생들이 질문하도록 장려하는 교사는 학생들이 지식을 오래 기억하고 확장하도록 돕는다.",
                chunks=[
                    schemas.Chunk(
                        english="Teachers who encourage students to inquire",
                        syntax="관계대명사(who) + 5형식(encourage+O+to부정사)",
                        korean="학생들이 질문하도록 장려하는 교사는",
                        words=[schemas.KeyWord(word="encourage", meaning="장려하다"),
                               schemas.KeyWord(word="inquire", meaning="질문하다, 탐구하다")],
                    ),
                    schemas.Chunk(
                        english="help them retain and expand their knowledge",
                        syntax="5형식(help+O+원형부정사)",
                        korean="그들이 지식을 기억하고 확장하도록 돕는다",
                        words=[schemas.KeyWord(word="retain", meaning="유지하다, 기억하다"),
                               schemas.KeyWord(word="expand", meaning="확장하다")],
                    ),
                ],
            ),
            schemas.Sentence(
                no=5,
                english="When learners engage with real problems, they gain deeper insight.",
                translation="학습자가 실제 문제에 몰두할 때, 그들은 더 깊은 통찰을 얻는다.",
                chunks=[
                    schemas.Chunk(
                        english="When learners engage with real problems",
                        syntax="시간의 부사절(when)",
                        korean="학습자가 실제 문제에 몰두할 때",
                        words=[schemas.KeyWord(word="engage", meaning="몰두하다")],
                    ),
                    schemas.Chunk(
                        english="they gain deeper insight",
                        syntax="비교급(deeper)",
                        korean="그들은 더 깊은 통찰을 얻는다",
                        words=[schemas.KeyWord(word="insight", meaning="통찰")],
                    ),
                ],
            ),
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
            schemas.VocabItem(no=i, word=w, meaning=m, synonyms=s, antonyms=a, sentence_no=sn)
            for i, (w, m, s, a, sn) in enumerate([
                ("curiosity", "호기심", "inquisitiveness", "indifference", 1),
                ("explore", "탐구하다", "investigate", "ignore", 1),
                ("essential", "필수적인", "vital, crucial", "trivial", 3),
                ("encourage", "장려하다", "promote", "discourage", 4),
                ("fuel", "촉진하다, 연료를 대다", "stimulate", "hinder", 3),
                ("retain", "유지하다, 기억하다", "keep", "lose", 4),
                ("motivation", "동기", "drive", "apathy", 3),
                ("creativity", "창의성", "originality", "conformity", 3),
                ("inquire", "질문하다, 탐구하다", "ask", "answer", 4),
                ("expand", "확장하다", "broaden", "shrink", 4),
                ("engage", "몰두하다", "involve", "withdraw", 5),
                ("insight", "통찰", "understanding", "confusion", 5),
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
            easy_explanation="핵심은 '스스로 궁금해할 때 배운 내용이 오래 남는다'는 것이다. 정답을 외우게 하기보다 질문하도록 이끄는 편이 효과적이다.",
            examples=[
                "좋아하는 분야의 정보는 따로 외우지 않아도 잘 기억하는 것과 같다. 스스로 궁금해서 찾아본 내용이기 때문이다.",
                "누가 시켜서가 아니라 관심이 생겨 직접 찾아본 내용이 더 오래 기억에 남는 것과 비슷하다.",
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
                "2문장 - they - (curious students, 호기심 많은 학생들)")),
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
