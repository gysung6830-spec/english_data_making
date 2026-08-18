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
    choice_roles: list[str] = Field(default_factory=list, description=(
        "의미 이해형(요지·제목·빈칸·함의)일 때만 채운다. 5개 선지 각각의 역할을 "
        "'정답'/'무관'/'모순' 중 하나로 순서대로. 정답 1 + 무관 2 + 모순 2 가 되어야 한다. "
        "그 외 유형(어법·불일치·순서 등)은 빈 리스트."))

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
        "<조건> 상자 문구들. 채점 가능하도록 되도록 다음을 포함: (1) 사용할 단어/보기 "
        "범위(예: '주어진 단어를 모두 사용', '본문에 쓰인 단어만 사용'), (2) 어형 변화 허용 "
        "여부(예: '필요시 어형을 바꿀 것'), (3) 답의 분량(예: '총 N단어로', '한 문장으로'), "
        "(4) 감점/부분점수 기준이 있으면 명시. 조건이 없으면 빈 리스트."))
    blank_ko: str = Field("", description="밑줄 친 우리말(영작 유형에서 학생이 영작할 한국어 문장). 없으면 빈 문자열")
    answers: list[str] = Field(
        ..., description="소문항별 정답. 각 항목은 '소문항 지시 :: 정답' 형식")
    explanation: str = Field("", description=(
        "자세한 해설. 각 소문항의 정답 근거, 어형변형/어순/문법 포인트, 본문 근거 위치를 "
        "구체적으로 설명. 핵심은 <b>...</b>로 강조."))
    answer_confidence: str = Field("확실", description=(
        "정답이 '유일하게' 성립함에 대한 확신도: '확실' 또는 '주의' 중 하나. 정답이 여러 개 "
        "가능하거나 채점 기준이 애매하면 반드시 '주의'로 표시."))


# '고난도 어휘'의 상한 — 지문을 억지로 어렵게 바꾸지 않도록 못박는다(동형·복수정답 위험↓).
_HARD_VOCAB = (
    "단, 지문을 원문보다 크게 어렵게 다시 쓰지 말고(지문 어휘·문장은 최대한 유지), 어려움은 "
    "선지·오답·과제 요구 수준에서만 준다. '고난도 어휘'는 수능 빈출 고급어 수준까지만 쓰고, "
    "사전 없이는 못 읽는 초저빈도어·전문용어·비표준 표현은 쓰지 않는다."
)

# 난이도 4단계 구체 정의 — 각 단계가 '무엇을' 조절하는지 프롬프트에 명시(난이도 일관성↑).
_DIFFICULTY_SPEC = {
    # 하 — '문제를 풀면서 학습이 되도록'
    "하": "학생이 지문을 미리 공부하지 않아도, 지금 지문을 읽으며 풀 수 있게 하라. 정답 단서를 "
          "지문 안에 뚜렷이 두고(추론 1단계), 문제를 푸는 과정에서 글의 핵심 내용이 자연스럽게 "
          "학습되도록 구성한다. 오답은 명백히 무관·모순이라 정답의 근거가 저절로 이해된다. "
          "쉬운 기본 어휘.",
    # 중 — '지문을 미리 공부해 놔야 풀 수 있음'(내신 암기 대비형)
    "중": "시험 범위 지문을 미리 정독·학습한 학생이라야 풀 수 있게 하라. 지문의 세부 정보·정확한 "
          "표현·구체적 사실을 알아야 정답이 갈리게 하고, 처음 보는 사람은 시간 안에 확신하기 "
          "어렵게 한다. 오답은 지문을 대충 읽으면 고를 만한 유의어·유사 정보 함정. 표준 수능 어휘.",
    # 상 — '지문에 대한 깊은 이해 필요'
    "상": "단순 암기로는 부족하고, 글의 논지·함의·인과·필자 의도를 깊이 이해하고 종합·적용해야 "
          "풀 수 있게 하라(추론 2~3단계). 오답 유의어는 정답과 매우 근접해 정밀 독해가 필요하고, "
          "빈칸은 추상적 핵심 명제 자리, 함의·밑줄형은 축자적 오독을 유도하는 함정을 강화한다. "
          + _HARD_VOCAB,
    # 중상 — '중·상 문항을 반반 배치'(문항별로 중/상을 나눠 생성하므로 이 문자열은 폴백용)
    "중상": "이 시험은 '중' 난이도 문항과 '상' 난이도 문항을 절반씩 섞는다. 각 문항은 중 또는 "
            "상 기준 중 하나를 따른다.",
}


def system_prompt(profile: dict[str, Any], difficulty_ko: str) -> str:
    """학교 스타일을 주입한 시스템 프롬프트(§8.5.5)."""
    name = profile.get("name", "해당 학교")
    focus = ", ".join(profile.get("grammar_focus", []) or [])
    notes = " / ".join(profile.get("notes", []) or [])
    dspec = _DIFFICULTY_SPEC.get(difficulty_ko, "")
    return (
        f"당신은 {name}의 영어 내신 출제 교사다. 이 학교의 동형모의고사 문항을 만든다.\n"
        f"- 난이도: {difficulty_ko} — {dspec}\n"
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
