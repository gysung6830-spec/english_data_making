"""API 없이 통합 워크북 파이프라인/디자인을 검증하기 위한 목(mock) 데이터.

pipeline 을 --workbook --mock 으로 실행하면 실제 API 대신 이 데이터를 사용한다.
LLMWorkbook 과 동일한 구조라서 build_workbook 을 거쳐 렌더 결과를 미리 볼 수 있다.
"""
from __future__ import annotations

from src import workbook_schemas as ws


def mock_llm_workbook() -> ws.LLMWorkbook:
    """다섯 유형이 골고루 등장하는 예시 워크북(LLM 응답 형태)."""
    return ws.LLMWorkbook(sentences=[
        ws.LLMSentence(
            no=1,
            en_template=(
                "Giving clients {{Q1}} opportunity to {{Q2}} to your designs "
                "while in progress {{Q3}} a key to professional success."
            ),
            ko="진행 중인 여러분의 설계 작업에 대해 고객들이 반응할 충분한 기회를 제공하는 것은 전문적 성공의 핵심이다.",
            questions=[
                ws.LLMQuestion(id="Q1", type="adj", display="[ sufficient / ample / scarce ]",
                               answer="sufficient / ample",
                               reason="sufficient(원문)·ample(유의어) 모두 정답; scarce(부족한)는 반대 의미라 오답"),
                ws.LLMQuestion(id="Q2", type="verb", display="(react)",
                               answer="react", reason="opportunity to + 동사원형(부정사)"),
                ws.LLMQuestion(id="Q3", type="verb", display="(be)",
                               answer="is", reason="동명사구 주어(Giving…)는 단수 취급"),
            ],
        ),
        ws.LLMSentence(
            no=2,
            en_template=(
                "Designers {{Q4}} welcome early feedback often avoid costly revisions, "
                "{{Q5}} those who resist {{Q9}} repeat the same {{Q6}} mistakes."
            ),
            ko="초기 피드백을 반기는 디자이너들은 값비싼 수정을 자주 피하는 반면, 그것에 저항하는 사람들은 똑같이 피할 수 있었던 실수를 반복한다.",
            questions=[
                ws.LLMQuestion(id="Q4", type="rel", display="[ who / which ]",
                               answer="who", reason="선행사 Designers(사람) + 주격 관계대명사"),
                ws.LLMQuestion(id="Q5", type="conj", display="[ while / because ]",
                               answer="while", reason="앞뒤 대조(양보) 흐름 — 인과의 because 는 반대"),
                ws.LLMQuestion(id="Q9", type="ref",
                               display="it = [ early feedback / costly revisions / designers ]",
                               answer="early feedback", reason="it = 앞의 early feedback(초기 피드백)을 가리킴"),
                ws.LLMQuestion(id="Q6", type="adj", display="[ inevitable / avoidable / preventable ]",
                               answer="avoidable / preventable",
                               reason="avoidable(원문)·preventable(유의어) 모두 정답; inevitable(불가피한)은 반대 의미라 오답"),
            ],
        ),
        ws.LLMSentence(
            no=3,
            en_template=(
                "Only after the deadline passed {{Q7}}, and the team finally understood "
                "{{Q8}}."
            ),
            ko="마감이 지나고 나서야 그들은 그 문제가 얼마나 심각했는지 깨달았고, 팀은 마침내 무엇이 잘못되었는지 이해했다.",
            questions=[
                ws.LLMQuestion(
                    id="Q7", type="order",
                    display="〈 they / realized / how / the problem / serious / was 〉",
                    answer="did they realize how serious the problem was",
                    reason="부정어구 Only 문두 도치 + 간접의문문(how+주어+동사) 어순 배열",
                ),
                ws.LLMQuestion(
                    id="Q8", type="order",
                    display="〈 what / gone / had / wrong 〉",
                    answer="what had gone wrong",
                    reason="간접의문문: 의문사(what) + 주어 + 동사 어순",
                ),
            ],
        ),
    ])


def mock_workbook(title: str = "The Value of Early Feedback",
                  subtitle: str = "설계 과정에서 초기 피드백이 전문적 성공의 핵심인 이유") -> ws.Workbook:
    return ws.build_workbook(mock_llm_workbook(), title=title, subtitle=subtitle)
