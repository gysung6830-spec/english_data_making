"""API 없이 빈칸형 워크북을 미리 보기 위한 목(mock) 데이터 (한 지문)."""
from __future__ import annotations

from src import blanks_schemas as bs

PB, SB, St = bs.LLMPassageBlank, bs.LLMSummaryBlank, bs.LLMBSentence


def mock_blank_set(title: str = "The Value of Early Feedback", no: int = 1) -> bs.LLMBlankSet:
    return bs.LLMBlankSet(
        no=no, title=title,
        subtitle="설계 과정에서 초기 피드백이 전문적 성공의 핵심인 이유",
        sentences=[
            St(no=1, en_template="Giving clients {{B1}} opportunity to {{B2}} to your designs while in progress is a key to professional success.",
               ko="진행 중인 설계 작업에 대해 고객이 반응할 충분한 기회를 주는 것이 전문적 성공의 핵심이다.",
               blanks=[PB(id="B1", answer="ample"), PB(id="B2", answer="react")]),
            St(no=2, en_template="Designers who {{B3}} early feedback often {{B4}} costly revisions, while those who resist it repeat the same avoidable mistakes.",
               ko="초기 피드백을 반기는 디자이너들은 값비싼 수정을 자주 피하는 반면, 그것에 저항하는 사람들은 똑같이 피할 수 있었던 실수를 반복한다.",
               blanks=[PB(id="B3", answer="welcome"), PB(id="B4", answer="avoid")]),
            St(no=3, en_template="Only after the deadline passed did they {{B5}} how {{B6}} the problem was, and the team finally understood what had gone wrong.",
               ko="마감이 지난 뒤에야 그들은 문제가 얼마나 심각한지 깨달았고, 팀은 마침내 무엇이 잘못되었는지 이해했다.",
               blanks=[PB(id="B5", answer="realize"), PB(id="B6", answer="serious")]),
        ],
        summary_template="Regularly {{S1}} client feedback during a project helps designers {{S2}} expensive fixes, whereas {{S3}} it leads to {{S4}} mistakes and late {{S5}}.",
        summary_blanks=[SB(id="S1", answer="seeking"), SB(id="S2", answer="avoid"),
                        SB(id="S3", answer="ignoring"), SB(id="S4", answer="repeated"),
                        SB(id="S5", answer="realization")],
        summary_ko="프로젝트 도중 고객 피드백을 꾸준히 구하면 값비싼 수정을 피할 수 있지만, 그것을 무시하면 같은 실수를 반복하고 뒤늦게야 문제를 깨닫게 된다.")


def mock_blank_workbook(title: str = "The Value of Early Feedback") -> bs.BlankWorkbook:
    llm = bs.LLMBlankWorkbook(sets=[mock_blank_set(title)])
    return bs.build_blank_workbook(llm, title=title, subtitle="유형 B 지문 빈칸 · 유형 A 요약문 빈칸")
