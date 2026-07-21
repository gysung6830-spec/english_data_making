"""빈칸형 워크북 데이터 모델 (유형 B 지문 빈칸 + 유형 A 요약문 빈칸).

- LLM 응답 계층(pydantic): client.structured 로 JSON 강제.
- 렌더 계층(dataclass): 전역 연속 채번 + 단어뱅크 셔플을 마친 최종 구조.

한 지문 = 한 세트: [지문 빈칸형(첫 글자 힌트 + 한글 해석)] → [요약문 빈칸형(번호만 + 단어뱅크)].
번호는 문서 전체에서 연속(지문 빈칸 1)~, 이어서 요약문 빈칸).
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z]\w*)\s*\}\}")

# 빈칸 밑줄/번호 색 (spec 6.4)
KIND_CLASS = {"passage": "pb", "summary": "sb"}   # pb=지문(초록) / sb=요약(청색)


def placeholders_in(t: str) -> list[str]:
    return _PLACEHOLDER.findall(t)


# ---------------------------------------------------------------------------
# LLM 응답 계층 (pydantic)
# ---------------------------------------------------------------------------
class LLMPassageBlank(BaseModel):
    id: str            # "B1"
    answer: str        # 지문 속 원래 단어


class LLMBSentence(BaseModel):
    no: int
    en_template: str   # 원문 그대로, 빈칸 자리에 {{B1}}
    ko: str            # 한글 해석
    blanks: list[LLMPassageBlank] = Field(default_factory=list)


class LLMSummaryBlank(BaseModel):
    id: str            # "S1"
    answer: str        # 요약문 속 정답 단어


class LLMBlankSet(BaseModel):
    no: int
    title: str
    subtitle: str = ""
    sentences: list[LLMBSentence]                 # 유형 B (지문 빈칸)
    summary_template: str                          # 유형 A 요약문, 빈칸 자리에 {{S1}}
    summary_blanks: list[LLMSummaryBlank] = Field(default_factory=list)
    summary_ko: str = ""                           # 요약문의 한국어 해석(해설용)

    @field_validator("sentences")
    @classmethod
    def _has_sent(cls, v):
        if not v:
            raise ValueError("지문 빈칸형 문장이 비어 있습니다.")
        return v


class LLMBlankWorkbook(BaseModel):
    sets: list[LLMBlankSet]

    @field_validator("sets")
    @classmethod
    def _has_sets(cls, v):
        if not v:
            raise ValueError("빈칸 워크북 지문이 비어 있습니다.")
        return v


# ---------------------------------------------------------------------------
# 렌더 계층 (dataclass)
# ---------------------------------------------------------------------------
@dataclass
class Blank:
    id: str
    answer: str
    kind: str          # passage | summary
    num: int = 0

    @property
    def first(self) -> str:
        # 지문 빈칸형만 첫 글자 힌트 (요약문 빈칸형은 없음)
        return self.answer[0] if (self.kind == "passage" and self.answer) else ""

    @property
    def css(self) -> str:
        return KIND_CLASS.get(self.kind, "pb")


@dataclass
class BSentence:
    no: int
    en_template: str
    ko: str
    blanks: list[Blank] = field(default_factory=list)


@dataclass
class BlankSet:
    no: int
    title: str
    subtitle: str
    sentences: list[BSentence]           # 유형 B
    summary_template: str                # 유형 A
    summary_blanks: list[Blank]
    wordbank: list[str]                  # 요약문 정답만 랜덤
    summary_ko: str = ""                 # 요약문 한국어 해석(해설용)

    @property
    def passage_blanks(self) -> list[Blank]:
        return [b for s in self.sentences for b in s.blanks]


@dataclass
class BlankWorkbook:
    title: str
    subtitle: str
    sets: list[BlankSet]
    total: int = 0


# ---------------------------------------------------------------------------
# 검증 + 채번 + 단어뱅크 구성
# ---------------------------------------------------------------------------
def validate_llm_blank_workbook(wb: LLMBlankWorkbook) -> None:
    # id 라벨이 어긋나도 개수만 맞으면 build 가 '등장 순서'로 정렬하므로, 개수만 검증한다.
    for st in wb.sets:
        for s in st.sentences:
            if len(placeholders_in(s.en_template)) != len(s.blanks):
                raise ValueError(
                    f"세트 {st.no} 문장 {s.no}: 지문 빈칸 자리표시자 수와 blanks 수가 다릅니다.")
        if len(placeholders_in(st.summary_template)) != len(st.summary_blanks):
            raise ValueError(f"세트 {st.no}: 요약문 빈칸 자리표시자 수와 summary_blanks 수가 다릅니다.")


def _align(order: list[str], items: list):
    """자리표시자(등장 순서) ↔ items 를 매핑. id 가 정확히 맞으면 그 매핑을, 아니면 순서대로."""
    by_id = {b.id: b for b in items}
    if set(order) == set(by_id) and len(order) == len(items):
        return [(pid, by_id[pid]) for pid in order]
    return list(zip(order, items))


def build_blank_workbook(llm: LLMBlankWorkbook, title: str, subtitle: str,
                         seed: int = 7) -> BlankWorkbook:
    """검증 → 전역 연속 채번(지문→요약) → 단어뱅크 셔플 → 렌더용 BlankWorkbook."""
    validate_llm_blank_workbook(llm)
    counter = 0
    sets: list[BlankSet] = []
    for st in llm.sets:
        # 유형 B: 문장별로 en_template 자리표시자 순서대로 채번 (id=자리표시자 문자열)
        bsents: list[BSentence] = []
        for s in st.sentences:
            numbered: list[Blank] = []
            for pid, src in _align(placeholders_in(s.en_template), s.blanks):
                counter += 1
                numbered.append(Blank(id=pid, answer=src.answer, kind="passage", num=counter))
            bsents.append(BSentence(no=s.no, en_template=s.en_template, ko=s.ko, blanks=numbered))
        # 유형 A: 요약문 자리표시자 순서대로 이어서 채번
        s_numbered: list[Blank] = []
        for pid, src in _align(placeholders_in(st.summary_template), st.summary_blanks):
            counter += 1
            s_numbered.append(Blank(id=pid, answer=src.answer, kind="summary", num=counter))
        # 단어뱅크: 정답만 랜덤(정답 개수 = 빈칸 개수, 중복 정답은 중복 표기)
        answers = [b.answer for b in s_numbered]
        rng = random.Random(seed + st.no)
        bank = answers[:]
        rng.shuffle(bank)
        sets.append(BlankSet(
            no=st.no, title=st.title, subtitle=st.subtitle,
            sentences=bsents, summary_template=st.summary_template,
            summary_blanks=s_numbered, wordbank=bank, summary_ko=st.summary_ko,
        ))
    return BlankWorkbook(title=title, subtitle=subtitle, sets=sets, total=counter)
