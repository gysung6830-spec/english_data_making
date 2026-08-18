"""동형모의고사 핵심 데이터 구조.

명세 §4 / §8 순서에 따라 가장 먼저 정의한다.
- Passage / PassageProfile : 입력 지문과 그 성질(§3-A)
- Item / Blueprint         : 그 학교 프로파일에서 뽑은 시험 스펙(§2)
- Assignment               : 유형 슬롯 ↔ 지문 배정 결과(§3-A-4)
- Question                 : 실제 생성된 문항(§5 검증 대상)

⚠️ 이 파일에는 진양고 등 특정 학교의 숫자를 하드코딩하지 않는다.
   모든 기대값(문항수·배점·유형순서)은 학교 프로파일에서 온다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Section = Literal["choice", "essay"]
FormatType = Literal["narrative", "dialogue", "notice", "chart"]
Difficulty = Literal["low", "mid", "mid_high", "high"]

# 사용자 입력(한글) → 내부 난이도 코드
DIFFICULTY_KO = {"하": "low", "중": "mid", "중상": "mid_high", "상": "high"}
DIFFICULTY_KO_REV = {v: k for k, v in DIFFICULTY_KO.items()}


# ---------------------------------------------------------------------------
# 입력 지문
# ---------------------------------------------------------------------------
@dataclass
class Passage:
    """올린 지문 1개(§3-A-0에서 분리된 단위)."""

    id: str
    text: str
    format_type: FormatType = "narrative"
    title: str | None = None
    source_file: str | None = None
    speakers: list[str] = field(default_factory=list)   # 대화문일 때 화자 라벨
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def words(self) -> int:
        return len(self.text.split())


@dataclass
class PassageProfile:
    """지문 프로파일(§3-A-1). 규칙 1차 측정 + 필요 시 LLM 확정."""

    passage_id: str
    format_type: FormatType = "narrative"
    logic_structure: float = 0.0     # 논리구조 뚜렷함 0~1
    has_conclusion: float = 0.0      # 결론문 존재 0~1
    grammar_diversity: float = 0.0   # 문법 다양성 0~1
    vocab_contrast: float = 0.0      # 어휘 대비쌍 0~1
    words: int = 0
    avg_sentence_len: float = 0.0
    rare_word_ratio: float = 0.0     # 저빈도 어휘 비율
    difficulty: Difficulty = "mid"
    source: Literal["rule", "llm"] = "rule"  # 마지막 확정 근거
    raw: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 시험 스펙 (그 학교 프로파일에서 나옴)
# ---------------------------------------------------------------------------
@dataclass
class Item:
    """blueprint 안의 문항 1개 스펙(§2)."""

    no: int
    section: Section
    type: str
    score: float
    underlines: int | None = None
    subparts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"no": self.no, "section": self.section,
                             "type": self.type, "score": self.score}
        if self.underlines is not None:
            d["underlines"] = self.underlines
        if self.subparts:
            d["subparts"] = self.subparts
        return d


@dataclass
class BlueprintMeta:
    school_id: str
    name: str
    level: str                # high | middle
    grade: int
    subject: str = ""
    time_min: int = 50
    total_score: float = 100.0
    pages: int = 7            # 원본 페이지수(하단 쪽번호 '( n ) / ( pages )'에 맞춤)
    learned: bool = False     # 학습 데이터 기반인지, 학교급 표준 골격인지


@dataclass
class Blueprint:
    """그 학교의 시험 스펙(§2). choice/essay 각각 1번부터 번호."""

    meta: BlueprintMeta
    items: list[Item] = field(default_factory=list)

    @property
    def choice_items(self) -> list[Item]:
        return [i for i in self.items if i.section == "choice"]

    @property
    def essay_items(self) -> list[Item]:
        return [i for i in self.items if i.section == "essay"]

    @property
    def total_score(self) -> float:
        return round(sum(i.score for i in self.items), 2)

    def type_sequence(self, section: Section) -> list[str]:
        return [i.type for i in self.items if i.section == section]

    def to_dict(self) -> dict[str, Any]:
        m = self.meta
        return {
            "meta": {"school_id": m.school_id, "name": m.name, "level": m.level,
                     "grade": m.grade, "subject": m.subject, "time_min": m.time_min,
                     "total_score": m.total_score, "learned": m.learned},
            "counts": {"choice": len(self.choice_items),
                       "essay": len(self.essay_items)},
            "items": [i.to_dict() for i in self.items],
        }


# ---------------------------------------------------------------------------
# 배정 / 생성 결과
# ---------------------------------------------------------------------------
@dataclass
class Assignment:
    """유형 슬롯 ↔ 지문 배정(§3-A-4)."""

    no: int
    section: Section
    type: str
    passage_id: str | None
    fit_score: float = 0.0
    source: Literal["rule", "llm", "format"] = "rule"
    note: str | None = None   # "substituted" | "skipped_no_passage" 등

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"no": self.no, "section": self.section, "type": self.type,
                             "passage_id": self.passage_id,
                             "fit_score": round(self.fit_score, 3), "source": self.source}
        if self.note:
            d["note"] = self.note
        return d


@dataclass
class Choice:
    label: str          # ①②③④⑤ 또는 (A)(B)...
    text: str


@dataclass
class Question:
    """생성된 문항 1개(§5 검증 대상)."""

    no: int
    section: Section
    type: str
    score: float
    stem: str                                   # 발문
    passage_text: str = ""                      # 문제에 실릴 지문(변형 포함)
    passage_id: str | None = None
    choices: list[Choice] = field(default_factory=list)
    answer: str = ""                            # 정답 라벨 또는 서술형 정답
    answer_notes: list[str] = field(default_factory=list)  # 서술형 소문항 정답
    explanation: str = ""
    difficulty: Difficulty = "mid"
    underlines: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "no": self.no, "section": self.section, "type": self.type,
            "score": self.score, "stem": self.stem, "passage_id": self.passage_id,
            "choices": [{"label": c.label, "text": c.text} for c in self.choices],
            "answer": self.answer, "answer_notes": self.answer_notes,
            "explanation": self.explanation, "difficulty": self.difficulty,
            "underlines": self.underlines,
        }


@dataclass
class MockExam:
    """완성된 동형모의고사 1세트."""

    blueprint: Blueprint
    questions: list[Question] = field(default_factory=list)
    form: str = "A"

    @property
    def choice_questions(self) -> list[Question]:
        return [q for q in self.questions if q.section == "choice"]

    @property
    def essay_questions(self) -> list[Question]:
        return [q for q in self.questions if q.section == "essay"]
