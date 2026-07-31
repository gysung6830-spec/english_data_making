"""LLM 호출 래퍼 (§4 core/llm.py).

mockexam.core.client 의 ClaudeClient(구조화 JSON + 재시도)를 사용한다.
유형별 프롬프트는 각 generator 가 만들고, 여기서는 스키마·시스템 프롬프트·매핑만 담당.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


def get_client(api_key: str, model: str = "claude-opus-4-8"):
    from .client import ClaudeClient  # 지연 임포트
    return ClaudeClient(api_key=api_key, model=model)


# ---------------------------------------------------------------------------
# 구조화 출력 스키마
# ---------------------------------------------------------------------------
class ChoiceQuestionOut(BaseModel):
    """객관식 1문항 LLM 출력."""

    passage: str = Field(..., description="문제에 실릴 지문. 밑줄이 필요한 유형이면 "
                         "①<u>...</u> 형식으로 정확히 지정 개수만큼 표시")
    # 개수/범위 제약을 JSON 스키마에 넣지 않는다(Anthropic strict 는 minItems·
    # minimum·maximum 등을 지원하지 않음). 대신 아래 validator 로 검증한다.
    choices: list[str] = Field(..., description="정확히 5개 선지 텍스트(라벨 제외)")
    answer_index: int = Field(..., description="정답 선지 번호(1~5)")
    explanation: str = Field(..., description=(
        "자세한 해설. 반드시 (1) 정답이 왜 맞는지 근거, (2) 오답 각각(①~⑤ 중 정답 제외)이 "
        "왜 틀렸는지 한 줄씩, (3) 관련 핵심 포인트(문법 규칙·어휘 뜻·글의 논지 등)를 포함. "
        "핵심 교정어/근거는 <b>...</b>로 강조하고, 대표 함정은 '[오답 함정] ...'으로 표기."))
    answer_confidence: str = Field("확실", description=(
        "정답이 '유일하게' 성립함에 대한 확신도: '확실' 또는 '주의' 중 하나. 다른 선지도 "
        "정답이 될 여지가 조금이라도 있거나 애매하면 반드시 '주의'로 표시."))

    @field_validator("choices")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("선지는 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_index")
    @classmethod
    def _in_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("정답 번호는 1~5 여야 합니다.")
        return v


class EssayQuestionOut(BaseModel):
    """서술형 1문항 LLM 출력.

    중첩 스키마 참조를 피하려고 answers 를 문자열 리스트로 둔다.
    각 항목은 '소문항 지시 :: 정답' 형식(구분자 없으면 통째로 정답).
    """

    passage: str = Field(..., description=(
        "문제에 실릴 지문. 이 유형이 요구하는 빈칸은 정확히 '____'(밑줄 4개)로, "
        "밑줄 표시가 필요한 부분은 <u>...</u>로 지문 안에 반드시 넣을 것. "
        "요약문형이면 요약문을 지문 끝에 '[요약문] ...' 로 포함하고 빈칸을 넣을 것."))
    bogi: list[str] = Field(default_factory=list, description=(
        "<보기> 단어 상자에 넣을 단어들(배열영작·어형변형·골라넣기 유형일 때만; "
        "그 외 유형은 빈 리스트)"))
    conditions: list[str] = Field(default_factory=list, description=(
        "<조건> 상자에 넣을 조건 문구들(예: '주어진 괄호 속 단어를 사용할 것', "
        "'본문에 사용된 단어만 사용할 것'). 조건이 없으면 빈 리스트"))
    blank_ko: str = Field("", description="밑줄 친 우리말(영작 유형에서 학생이 영작할 한국어 문장). 없으면 빈 문자열")
    answers: list[str] = Field(
        ..., description="소문항별 정답. 각 항목은 '소문항 지시 :: 정답' 형식")
    explanation: str = Field("", description=(
        "자세한 해설. 각 소문항의 정답 근거, 어형변형/어순/문법 포인트, 본문 근거 위치를 "
        "구체적으로 설명. 핵심은 <b>...</b>로 강조."))
    answer_confidence: str = Field("확실", description=(
        "정답이 '유일하게' 성립함에 대한 확신도: '확실' 또는 '주의' 중 하나. 정답이 여러 개 "
        "가능하거나 채점 기준이 애매하면 반드시 '주의'로 표시."))


def system_prompt(profile: dict[str, Any], difficulty_ko: str) -> str:
    """학교 스타일을 주입한 시스템 프롬프트(§8.5.5)."""
    name = profile.get("name", "해당 학교")
    focus = ", ".join(profile.get("grammar_focus", []) or [])
    notes = " / ".join(profile.get("notes", []) or [])
    return (
        f"당신은 {name}의 영어 내신 출제 교사다. 이 학교의 동형모의고사 문항을 만든다.\n"
        f"- 난이도: {difficulty_ko} (요청 난이도에 맞춰 오답 매력도·단서·어휘를 조절).\n"
        f"- 어법 출제 축: {focus or '일반'}.\n"
        f"- 학교 특이점: {notes or '없음'}.\n"
        "출제 원리(명세 §3-C)를 따르고, 정답은 반드시 1개만 성립하게 하며, "
        "선지에는 그럴듯한 함정을 배치한다. 지문·선지·정답은 원본을 베끼지 말고 새로 만든다.\n"
        "지문·선지·해설 어디에도 'WORKBOOK', '지문 N', 'N번 문장', 교재·출처·저작권 표기 등 "
        "원본 자료의 흔적을 절대 넣지 않는다. 해설에서 본문을 가리킬 때는 인용문이나 '본문 "
        "첫 문장' 같은 표현만 쓴다.\n"
        "모든 한국어(발문·해설)는 한글로만 쓰고 한자(漢字)를 섞지 않는다(예: '分析' X → '분석').\n"
        "반드시 요구된 JSON 스키마로만 답한다."
    )
