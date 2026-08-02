"""API 없이 단일 유형 산문 워크시트 디자인을 검증하기 위한 목(mock) 데이터.

통합/영작/빈칸 목데이터와 '같은 지문'(초기 피드백)을 사용해 샘플 전체가 한 지문으로
일관되게 보이도록 한다.
"""
from __future__ import annotations

from src import prose_render as pr


def mock_llm_prose() -> pr.LLMProsePack:
    """어법·어형·어휘가 골고루 들어간 예시 산문 워크시트(LLM 응답 형태) — 초기 피드백 지문."""
    def I(pid, disp, ans):
        return pr.LLMProseItem(id=pid, display=disp, answer=ans)

    return pr.LLMProsePack(
        title="The Value of Early Feedback",
        subtitle="설계 과정에서 초기 피드백이 전문적 성공의 핵심인 이유",
        sentences=[
            pr.LLMProseSentence(
                no=1,
                en=("Giving clients ample opportunity to react to your designs while in "
                    "progress is a key to professional success."),
                ko="진행 중인 설계 작업에 대해 고객이 반응할 충분한 기회를 주는 것이 전문적 성공의 핵심이다.",
                grammar_template=("Giving clients ample opportunity to react to your designs while in "
                                  "progress {{P1}} a key to professional success."),
                grammar_items=[I("P1", "[ is / are ]", "is")],
                form_template=("{{P1}} clients ample opportunity to {{P2}} to your designs while in "
                               "progress {{P3}} a key to professional success."),
                form_items=[I("P1", "(give)", "Giving"), I("P2", "(react)", "react"),
                            I("P3", "(be)", "is")],
                vocab_template=("Giving clients {{P1}} opportunity to react to your designs while in "
                                "progress is a key to professional success."),
                vocab_items=[I("P1", "[ ample / scant ]", "ample")],
                vocab_easy_template=("Giving clients ample opportunity to react to your designs while in "
                                     "progress is a key to professional {{P1}}."),
                vocab_easy_items=[I("P1", "[ success / failure ]", "success")],
            ),
            pr.LLMProseSentence(
                no=2,
                en=("Designers who welcome early feedback often avoid costly revisions, while "
                    "those who resist it repeat the same avoidable mistakes."),
                ko="초기 피드백을 반기는 디자이너들은 값비싼 수정을 자주 피하는 반면, 그것에 저항하는 사람들은 똑같이 피할 수 있었던 실수를 반복한다.",
                grammar_template=("Designers {{P1}} welcome early feedback often avoid costly revisions, "
                                  "{{P2}} those who resist it repeat the same avoidable mistakes."),
                grammar_items=[I("P1", "[ who / which ]", "who"),
                               I("P2", "[ while / because ]", "while")],
                form_template=("Designers who {{P1}} early feedback often {{P2}} costly revisions, while "
                               "those who {{P3}} it {{P4}} the same avoidable mistakes."),
                form_items=[I("P1", "(welcome)", "welcome"), I("P2", "(avoid)", "avoid"),
                            I("P3", "(resist)", "resist"), I("P4", "(repeat)", "repeat")],
                vocab_template=("Designers who welcome early feedback often avoid costly revisions, while "
                                "those who resist it repeat the same {{P1}} mistakes."),
                vocab_items=[I("P1", "[ avoidable / inevitable ]", "avoidable")],
                vocab_easy_template=("Designers who welcome {{P1}} feedback often avoid costly revisions, "
                                     "while those who resist it repeat the same avoidable mistakes."),
                vocab_easy_items=[I("P1", "[ early / late ]", "early")],
            ),
            pr.LLMProseSentence(
                no=3,
                en=("Only after the deadline passed did they realize how serious the problem was, "
                    "and the team finally understood what had gone wrong."),
                ko="마감이 지난 뒤에야 그들은 문제가 얼마나 심각한지 깨달았고, 팀은 마침내 무엇이 잘못되었는지 이해했다.",
                grammar_template=("Only after the deadline passed {{P1}} how serious the problem was, "
                                  "and the team finally understood what had gone wrong."),
                grammar_items=[I("P1", "[ did they realize / they realized ]", "did they realize")],
                form_template=("Only after the deadline {{P1}} did they {{P2}} how serious the problem "
                               "was, and the team finally {{P3}} what had {{P4}} wrong."),
                form_items=[I("P1", "(pass)", "passed"), I("P2", "(realize)", "realize"),
                            I("P3", "(understand)", "understood"), I("P4", "(go)", "gone")],
                vocab_template=("Only after the deadline passed did they realize how {{P1}} the problem "
                                "was, and the team finally understood what had gone wrong."),
                vocab_items=[I("P1", "[ serious / superficial ]", "serious")],
                vocab_easy_template=("Only after the deadline passed did they realize how serious the "
                                     "problem was, and the team finally {{P1}} what had gone wrong."),
                vocab_easy_items=[I("P1", "[ understood / ignored ]", "understood")],
            ),
        ],
    )


def mock_prose_pack(title: str = "The Value of Early Feedback", header: str = "") -> pr.ProsePack:
    llm = mock_llm_prose()
    return pr.build_prose_pack(llm, header=header or title,
                               title=title, subtitle=llm.subtitle)
