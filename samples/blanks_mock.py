"""API 없이 빈칸형 워크북을 미리 보기 위한 목(mock) 데이터 (한 지문)."""
from __future__ import annotations

from src import blanks_schemas as bs

PB, SB, St = bs.LLMPassageBlank, bs.LLMSummaryBlank, bs.LLMBSentence


def mock_blank_set(title: str = "The Human Need for Companionship", no: int = 1) -> bs.LLMBlankSet:
    return bs.LLMBlankSet(
        no=no, title=title,
        subtitle="혼자이고 싶은 마음만큼이나, 인간은 존재와 정체성을 확인받기 위해 타인과의 교제를 갈망한다.",
        sentences=[
            St(no=1, en_template="Although the wish to be alone is often strong, its intensity {{B1}} from person to person.",
               ko="혼자 있고 싶은 소망은 종종 강하지만, 그 강도는 사람마다 다르다.",
               blanks=[PB(id="B1", answer="varies")]),
            St(no=2, en_template="An equally impelling impulse, though, is to {{B2}} the company of others and to spend extended periods of time {{B3}} activities.",
               ko="하지만 똑같이 뿌리칠 수 없는 충동은 다른 사람과 함께 있는 것을 추구하고 활동을 공유하면서 긴 시간을 보내는 것이다.",
               blanks=[PB(id="B2", answer="seek"), PB(id="B3", answer="sharing")]),
            St(no=3, en_template="In these periods we {{B4}} information and feelings in both conversational and {{B5}} forms.",
               ko="이 시간 동안 우리는 대화의 형태와 비언어적 형태 둘 다로 정보와 감정을 교환한다.",
               blanks=[PB(id="B4", answer="exchange"), PB(id="B5", answer="non-verbal")]),
            St(no=4, en_template="We need other people to {{B6}} us with love, support, approval and a myriad of other emotional needs.",
               ko="우리는 우리에게 사랑, 지지, 인정, 그리고 무수히 많은 다른 정서적 필요를 제공해 줄 다른 사람들을 필요로 한다.",
               blanks=[PB(id="B6", answer="provide")]),
            St(no=5, en_template="In a very basic sense we need others to {{B7}} that we have an identity that is {{B8}} and separate from anyone else.",
               ko="아주 기본적인 의미에서 우리는 다른 누구와도 구별되는 고유한 정체성을 가지고 있음을 확인받기 위해 다른 사람들을 필요로 한다.",
               blanks=[PB(id="B7", answer="confirm"), PB(id="B8", answer="unique")]),
        ],
        summary_template="Humans crave {{S1}} with others to confirm their own {{S2}} and to satisfy their emotional {{S3}}. Because this {{S4}} sustains us, we can rarely endure long periods of {{S5}}.",
        summary_blanks=[SB(id="S1", answer="connection"), SB(id="S2", answer="identity"),
                        SB(id="S3", answer="needs"), SB(id="S4", answer="interaction"),
                        SB(id="S5", answer="isolation")])


def mock_blank_workbook(title: str = "The Human Need for Companionship") -> bs.BlankWorkbook:
    llm = bs.LLMBlankWorkbook(sets=[mock_blank_set(title)])
    return bs.build_blank_workbook(llm, title=title, subtitle="유형 B 지문 빈칸 · 유형 A 요약문 빈칸")
