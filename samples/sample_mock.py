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
        ]),
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
            schemas.ExamItem(question_type="지칭추론(대명사)",
                             content="it / they 등이 가리키는 대상(호기심·학생 등)을 문맥으로 찾기.",
                             tip="대명사 앞의 명사를 되짚어 무엇을 받는지 확인."),
            schemas.ExamItem(question_type="어휘",
                             content="essential / encourage / retain 등 핵심 어휘의 의미·유의어를 묻는 문제.",
                             tip="유의어(vital, promote)로 변형될 수 있으니 함께 암기."),
            schemas.ExamItem(question_type="순서배열·문장삽입",
                             content="Therefore 등 연결어와 지시어를 단서로 문장 순서·삽입 위치 찾기.",
                             tip="연결어가 글의 흐름을 잡는 핵심 신호이므로 표시하며 읽기."),
            schemas.ExamItem(question_type="서술형",
                             content="호기심이 학습에 도움이 되는 이유를 지문 근거로 영어로 서술하기.",
                             tip="because it fuels learning 구문을 활용해 작성."),
        ]),
    )
