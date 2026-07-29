"""API 없이 단일 유형 산문 워크시트 디자인을 검증하기 위한 목(mock) 데이터."""
from __future__ import annotations

from src import prose_render as pr


def mock_llm_prose() -> pr.LLMProsePack:
    """어법·어형·어휘가 골고루 들어간 예시 산문 워크시트(LLM 응답 형태)."""
    def I(pid, disp, ans):
        return pr.LLMProseItem(id=pid, display=disp, answer=ans)

    return pr.LLMProsePack(
        title="Inheritance and the Limits of Adaptation",
        subtitle="유전의 보수성과 적응의 한계",
        sentences=[
            pr.LLMProseSentence(
                no=1,
                en=("Darwin understood that since inheritance is conservative, it is in the "
                    "nature of the organism to impose itself on the surroundings."),
                ko="다윈은 유전이 보수적이므로, 유기체가 주변 환경에 자신을 강요하는 것이 그 본성이라는 것을 이해했다.",
                grammar_template=("Darwin understood {{P1}} since inheritance is conservative, it is "
                                  "in the nature of the organism to impose {{P2}} on the surroundings."),
                grammar_items=[I("P1", "[ that / what ]", "that"),
                               I("P2", "[ it / itself ]", "itself")],
                form_template=("Darwin {{P1}} that since inheritance is conservative, it is in the "
                               "nature of the organism to impose itself on the surroundings."),
                form_items=[I("P1", "(understand)", "understood")],
                vocab_template=("Darwin understood that since inheritance is {{P1}}, it is in the "
                                "nature of the organism to impose itself on the surroundings."),
                vocab_items=[I("P1", "[ progressive / conservative ]", "conservative")],
            ),
            pr.LLMProseSentence(
                no=2,
                en="But needs and opportunity do not perfectly match.",
                ko="하지만 필요와 기회는 완벽하게 일치하지 않는다.",
                grammar_template="But needs and opportunity {{P1}} not perfectly match.",
                grammar_items=[I("P1", "[ do / does ]", "do")],
                form_template="But needs and opportunity do not perfectly {{P1}}.",
                form_items=[I("P1", "(match)", "match")],
                vocab_template="But needs and opportunity do not {{P1}} match.",
                vocab_items=[I("P1", "[ imperfectly / perfectly ]", "perfectly")],
            ),
            pr.LLMProseSentence(
                no=3,
                en="As a result, not every living thing can live everywhere.",
                ko="결과적으로, 모든 생물이 모든 곳에서 살 수 있는 것은 아니다.",
                grammar_template="As a result, not every {{P1}} thing can live everywhere.",
                grammar_items=[I("P1", "[ lived / living ]", "living")],
                form_template="As a result, not every living thing can {{P1}} everywhere.",
                form_items=[I("P1", "(live)", "live")],
                vocab_template="As a result, not every living thing can live {{P1}}.",
                vocab_items=[I("P1", "[ everywhere / nowhere ]", "everywhere")],
            ),
        ],
    )


def mock_prose_pack(title: str = "샘플 지문", header: str = "") -> pr.ProsePack:
    llm = mock_llm_prose()
    return pr.build_prose_pack(llm, header=header or title,
                               title=title, subtitle=llm.subtitle)
