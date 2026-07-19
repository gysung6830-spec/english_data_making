"""LLM 호출 래퍼 (§4 core/llm.py).

기존 src/client.py 의 ClaudeClient(구조화 JSON + 재시도)를 재사용한다.
유형별 프롬프트는 각 generator 가 만들고, 여기서는 스키마·시스템 프롬프트·매핑만 담당.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

# 기존 src 패키지의 LLM 래퍼 재사용
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def get_client(api_key: str, model: str = "claude-opus-4-8"):
    from src.client import ClaudeClient  # 지연 임포트
    return ClaudeClient(api_key=api_key, model=model)


# ---------------------------------------------------------------------------
# 구조화 출력 스키마
# ---------------------------------------------------------------------------
class ChoiceQuestionOut(BaseModel):
    """객관식 1문항 LLM 출력."""

    passage: str = Field(..., description="문제에 실릴 지문. 밑줄이 필요한 유형이면 "
                         "①<u>...</u> 형식으로 정확히 지정 개수만큼 표시")
    choices: list[str] = Field(..., min_length=5, max_length=5,
                               description="5개 선지 텍스트(라벨 제외)")
    answer_index: int = Field(..., ge=1, le=5, description="정답 선지 번호(1~5)")
    explanation: str = Field(..., description="정답 근거 해설")

    @field_validator("choices")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("선지는 정확히 5개여야 합니다.")
        return v


class EssaySubAnswer(BaseModel):
    label: str = Field(..., description="소문항 지시(예: '보기 단어 모두 활용 영작')")
    answer: str = Field(..., description="그 소문항의 정답")


class EssayQuestionOut(BaseModel):
    """서술형 1문항 LLM 출력."""

    passage: str = Field(..., description="문제에 실릴 지문(빈칸/밑줄 포함 가능)")
    prompt_extra: str = Field("", description="발문에 덧붙일 조건/보기(예: [보기] 단어들, 조건)")
    answers: list[EssaySubAnswer] = Field(..., description="소문항별 정답")


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
        "반드시 요구된 JSON 스키마로만 답한다."
    )
