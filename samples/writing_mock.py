"""API 없이 영작 워크북 디자인을 검증하기 위한 목(mock) 데이터."""
from __future__ import annotations

from src import writing_render as wr


def mock_llm_writing() -> wr.LLMWritingPack:
    """문장 속 '영작 포인트'만 배열하는 예시(LLM 응답 형태). 한 문장 최대 2박스."""
    def I(aid, chunks, ans):
        return wr.LLMWritingItem(id=aid, chunks=chunks, answer=ans)

    return wr.LLMWritingPack(
        title="Darwin · 적응과 진화",
        subtitle="영작 포인트 배열 연습",
        sentences=[
            wr.LLMWritingSentence(
                no=1,
                ko="살아있는 유기체는 주변 환경에 자신을 강요하려 하지 않는다.",
                template="A living organism does not try {{A1}}.",
                items=[I("A1", ["to", "impose", "itself", "on the surroundings"],
                         "to impose itself on the surroundings")],
            ),
            wr.LLMWritingSentence(
                no=2,
                ko="그것은 조건의 성격과 상관없이 그 환경에 적응한다.",
                template="It adapts to that environment, {{A1}}.",
                items=[I("A1", ["regardless", "of", "the nature", "of the conditions"],
                         "regardless of the nature of the conditions")],
            ),
            wr.LLMWritingSentence(
                no=3,
                ko="유기체와 그 환경이 완벽하게 일치하지 않을 때, 진화가 일어난다.",
                template="When an organism and its environment {{A1}}, evolution {{A2}}.",
                items=[I("A1", ["do", "not", "perfectly", "match"], "do not perfectly match"),
                       I("A2", ["takes", "place"], "takes place")],
            ),
            wr.LLMWritingSentence(
                no=4,
                ko="모든 생명체가 변화하는 조건에 성공적으로 적응할 수 있는 것은 아니다.",
                template="{{A1}} can successfully adapt to changing conditions.",
                items=[I("A1", ["Not", "every", "living thing"], "Not every living thing")],
            ),
            wr.LLMWritingSentence(
                no=5,
                ko="유기체는 스스로를 바꾸기는커녕 자신의 환경을 통제할 수도 없다.",
                template="Organisms cannot control their environment, {{A1}}.",
                items=[I("A1", ["much", "less", "alter", "themselves"], "much less alter themselves")],
            ),
            wr.LLMWritingSentence(
                no=6,
                ko="이러한 자유는 유전의 제약에 비하면 미미하다.",
                template="This freedom is slight {{A1}}.",
                items=[I("A1", ["compared", "to", "the constraints", "of inheritance"],
                         "compared to the constraints of inheritance")],
            ),
        ],
    )


def mock_writing_pack(title: str = "샘플 지문", header: str = "") -> wr.WritingPack:
    llm = mock_llm_writing()
    return wr.build_writing_pack(llm, header=header or title,
                                 title=title, subtitle=llm.subtitle)
