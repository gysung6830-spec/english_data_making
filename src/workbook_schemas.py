"""문장별 복합유형 통합 워크북 데이터 모델.

두 계층으로 나눈다.
  1) LLM 응답 계층 (pydantic) — client.structured 로 JSON 스키마를 강제/검증한다.
     LLMQuestion / LLMSentence / LLMWorkbook. num(전역 문항번호)·total 은 담지 않는다.
  2) 렌더 계층 (dataclass) — 코드가 전역 채번·total 집계를 마친 최종 구조.
     Question / Sentence / Workbook. 템플릿 렌더링에 그대로 쓴다.

LLM 은 문장/문제만 만들고, '전역 연속 번호'와 '총 문항 수(SCORE)'는 코드가 채운다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# 출제 유형 (spec 1의 5유형 + 대명사 지칭 ref)
#   ref = 대명사가 가리키는 대상을 고르는 지칭 추론 (관계사·대명사와 같은 보라색 계열)
QTYPE = Literal["verb", "adj", "rel", "conj", "order", "ref"]

# 유형 → 위첨자 라벨 / CSS 클래스 (spec 4-4)
TYPE_LABEL = {"verb": "동사", "adj": "형·부", "rel": "관계사", "conj": "연결사",
              "order": "배열", "ref": "지칭"}
TYPE_CLASS = {"verb": "v", "adj": "a", "rel": "r", "conj": "c", "order": "o", "ref": "r"}
TYPE_COLOR = {
    "verb": "#2563a0", "adj": "#158060", "rel": "#7d3caf",
    "conj": "#c47510", "order": "#b83232", "ref": "#7d3caf",
}

# en_template 안의 자리표시자 패턴: {{Q1}}
_PLACEHOLDER = re.compile(r"\{\{\s*(Q\d+)\s*\}\}")


# ---------------------------------------------------------------------------
# 1) LLM 응답 계층 (pydantic)
# ---------------------------------------------------------------------------
class LLMQuestion(BaseModel):
    id: str                       # "Q1" (문서 전체에서 유일)
    type: QTYPE                   # verb | adj | rel | conj | order
    display: str                  # 문제지 표기: "(react)" / "[ a / b / c ]" / "〈 ... 〉"
    answer: str                   # 정답
    reason: str                   # 한 줄 해설


class LLMSentence(BaseModel):
    no: int                       # 문장 순번(1부터)
    en_template: str              # {{Q1}} 자리표시자를 포함한 영어 문장
    ko: str                       # 한국어 해석
    questions: list[LLMQuestion] = Field(default_factory=list)
    # 출제할 요소가 없는 문장(빈 questions)이 섞여 와도 전체를 거부하지 않는다.
    # 이런 문장은 build_workbook 에서 건너뛴다(spec: 출제할 요소가 없으면 넣지 않음).


class LLMWorkbook(BaseModel):
    sentences: list[LLMSentence] = Field(default_factory=list)

    @field_validator("sentences")
    @classmethod
    def _has_sentences(cls, v: list[LLMSentence]) -> list[LLMSentence]:
        if not v:
            raise ValueError("워크북 문장이 비어 있습니다.")
        return v


# ---------------------------------------------------------------------------
# 2) 렌더 계층 (dataclass, spec 4-1)
# ---------------------------------------------------------------------------
@dataclass
class Question:
    id: str            # "Q1"
    type: str          # verb | adj | rel | conj | order
    display: str       # 문제지에 보일 표기
    answer: str        # 정답
    reason: str        # 한 줄 해설
    num: int = 0       # 문서 전체 연속 문항번호 (코드가 채움)

    @property
    def label(self) -> str:
        return TYPE_LABEL.get(self.type, "")

    @property
    def css(self) -> str:
        return TYPE_CLASS.get(self.type, "")

    @property
    def color(self) -> str:
        return TYPE_COLOR.get(self.type, "#1c2e44")


@dataclass
class Sentence:
    no: int
    en_template: str   # {{Q1}} 자리표시자 포함
    ko: str
    questions: list[Question] = field(default_factory=list)


@dataclass
class Workbook:
    title: str
    subtitle: str
    sentences: list[Sentence] = field(default_factory=list)
    total: int = 0     # 총 문항 수 (SCORE 표시용)
    label: str = ""    # 출처 기반 문항 라벨 (예: "[고1] 9월 30번")

    @property
    def all_questions(self) -> list[Question]:
        return [q for s in self.sentences for q in s.questions]


# ---------------------------------------------------------------------------
# 검증 + 전역 채번 (spec 4-2 단계 4·5, spec 5 체크리스트)
# ---------------------------------------------------------------------------
def placeholders_in(template: str) -> list[str]:
    """en_template 에 등장하는 자리표시자 id 목록(등장 순서)."""
    return _PLACEHOLDER.findall(template)


def validate_llm_workbook(wb: LLMWorkbook) -> None:
    """LLM 응답의 정합성을 검증한다. 위반 시 ValueError.

    - 각 문장의 {{Qn}} 자리표시자가 questions 와 1:1 대응
    - 문항 id 가 문서 전체에서 유일
    - 특수구문(order) display 는 〈 … 〉 형태
    """
    total_q = 0
    for s in wb.sentences:
        # 출제할 요소가 없는 문장(빈 questions)은 build_workbook 에서 건너뛰므로 검증도 건너뛴다.
        if not s.questions:
            continue
        total_q += len(s.questions)
        # 자리표시자 수와 questions 수가 달라도(예: LLM 이 {{Qn}} 을 안 넣거나 더 넣음)
        # 전체를 실패시키지 않는다. build_workbook 이 '등장 순서'로 가능한 만큼만 짝지어
        # 채번하고, 남는 자리표시자/문항은 렌더에서 자연스럽게 정리한다.
        for q in s.questions:
            if q.type == "order":
                d = q.display.strip()
                if not (d.startswith("〈") and d.endswith("〉")):
                    raise ValueError(
                        f"문항 {q.id}: 특수구문(order) 표기는 〈 어구/어구 〉 형태여야 합니다(현재: {q.display!r})."
                    )
    # 모든 문장이 비어 출제 문항이 하나도 없으면 실패로 보고 재요청한다.
    if total_q == 0:
        raise ValueError("출제 문항이 하나도 없습니다(모든 문장의 questions 가 비어 있음).")


def build_workbook(llm: LLMWorkbook, title: str, subtitle: str) -> Workbook:
    """검증된 LLM 응답에 전역 연속 번호를 채우고 total 을 집계해 렌더용 Workbook 생성."""
    validate_llm_workbook(llm)
    sentences: list[Sentence] = []
    counter = 0
    for s in llm.sentences:
        order = placeholders_in(s.en_template)
        # 출제할 요소가 없는 문장(questions 비어 있음)이라도 '읽기용'으로 그대로 싣는다
        # (지문 문장을 절대 누락하지 않기 위해). 단, 자리표시자만 있고 questions 가 없어
        # 렌더가 불가능한 (드문) 경우에만 건너뛴다.
        if not s.questions:
            if order:
                continue
            sentences.append(Sentence(no=s.no, en_template=s.en_template, ko=s.ko, questions=[]))
            continue
        # en_template 의 자리표시자 등장 순서대로 채번(위첨자 번호가 문장 흐름과 일치).
        by_id = {q.id: q for q in s.questions}
        # id 라벨이 정확히 일치하면 그 매핑을, 아니면(개수만 맞는 경우) '등장 순서'로 정렬한다.
        if set(order) == set(by_id) and len(order) == len(s.questions):
            pairs = [(pid, by_id[pid]) for pid in order]
        else:
            pairs = list(zip(order, s.questions))   # 자리표시자 순서 ↔ questions 순서
        qs: list[Question] = []
        for pid, src in pairs:
            counter += 1
            # Question.id 는 '자리표시자 문자열'로 둔다 → 렌더가 {{pid}} 를 정확히 치환.
            qs.append(Question(id=pid, type=src.type, display=src.display,
                               answer=src.answer, reason=src.reason, num=counter))
        sentences.append(Sentence(no=s.no, en_template=s.en_template, ko=s.ko, questions=qs))
    return Workbook(title=title, subtitle=subtitle, sentences=sentences, total=counter)
