"""API 없이 영작 워크북 디자인을 검증하기 위한 목(mock) 데이터.

통합/단일유형/빈칸과 '같은 지문'(초기 피드백)을 사용한다. 문장 속 '영작 포인트'만 배열.
"""
from __future__ import annotations

from src import writing_render as wr


def mock_llm_writing() -> wr.LLMWritingPack:
    """문장 속 '영작 포인트'만 배열하는 예시(LLM 응답 형태). 한 문장 최대 2박스."""
    def I(aid, chunks, ans):
        return wr.LLMWritingItem(id=aid, chunks=chunks, answer=ans)

    return wr.LLMWritingPack(
        title="The Value of Early Feedback",
        subtitle="영작 포인트 배열 연습",
        sentences=[
            wr.LLMWritingSentence(
                no=1,
                ko="진행 중인 설계 작업에 대해 고객이 반응할 충분한 기회를 주는 것이 전문적 성공의 핵심이다.",
                template="Giving clients ample opportunity {{A1}} is a key to professional success.",
                items=[I("A1", ["to", "react", "to", "your", "designs", "while", "in", "progress"],
                         "to react to your designs while in progress")],
            ),
            wr.LLMWritingSentence(
                no=2,
                ko="초기 피드백을 반기는 디자이너들은 값비싼 수정을 자주 피하는 반면, 그것에 저항하는 사람들은 똑같이 피할 수 있었던 실수를 반복한다.",
                template="Designers who welcome early feedback often avoid costly revisions, {{A1}} the same avoidable mistakes.",
                items=[I("A1", ["while", "those", "who", "resist", "it", "repeat"],
                         "while those who resist it repeat")],
            ),
            wr.LLMWritingSentence(
                no=3,
                ko="마감이 지난 뒤에야 그들은 문제가 얼마나 심각한지 깨달았고, 팀은 마침내 무엇이 잘못되었는지 이해했다.",
                template="Only after the deadline passed {{A1}}, and the team finally understood {{A2}}.",
                items=[I("A1", ["did", "they", "realize", "how", "serious", "the", "problem", "was"],
                         "did they realize how serious the problem was"),
                       I("A2", ["what", "had", "gone", "wrong"], "what had gone wrong")],
            ),
        ],
    )


def mock_writing_pack(title: str = "The Value of Early Feedback", header: str = "") -> wr.WritingPack:
    llm = mock_llm_writing()
    return wr.build_writing_pack(llm, header=header or title,
                                 title=title, subtitle=llm.subtitle)
