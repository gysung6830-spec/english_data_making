"""'강의컨셉 교재(필생보)' 데이터 모델 (pydantic).

학생이 문제를 풀며 스스로 학습하는 워크북. 구성 순서:
  ① 어휘 리스트
  ② 문장별: 끊어읽기 해석(오역 위험 부분 '빈칸 채우기', 주관식) + '이 문장 내용' 객관식
  ③ 글 예측: 소재 / 필자 의견 / 글의 구조 / 재진술

- 문장 분리·번호(1..n)는 코드가 결정론적으로 매기고(LectureSentence),
  문장별 분석(SentenceItem)은 그 번호를 그대로 사용한다.
- LLM 호출 2단계: (1) 개관(Overview) → (2) 문장별 분석(SentenceAnalysis).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# 🗣 필자 의견 (3택)
STANCES: tuple[str, ...] = ("긍정적", "부정적·비판적", "중립적")
Stance = Literal["긍정적", "부정적·비판적", "중립적"]

# 🧩 글의 구조 (6택)
STRUCTURES: tuple[str, ...] = (
    "통념→반박(반전)", "주장→근거·예시", "문제→해결(방안)",
    "비교·대조", "시간·순서(나열)", "예시→일반화(결론)",
)
Structure = Literal[
    "통념→반박(반전)", "주장→근거·예시", "문제→해결(방안)",
    "비교·대조", "시간·순서(나열)", "예시→일반화(결론)",
]


# ---------------------------------------------------------------------------
# 문장 (코드가 분리·번호 부여)
# ---------------------------------------------------------------------------
class LectureSentence(BaseModel):
    id: int
    text: str


# ---------------------------------------------------------------------------
# ③ 재진술 사슬
# ---------------------------------------------------------------------------
class RestatementChain(BaseModel):
    label: str
    expressions: list[str]
    variation: str

    @field_validator("expressions")
    @classmethod
    def _min_two(cls, v: list[str]) -> list[str]:
        v = [e.strip() for e in v if e and e.strip()]
        if len(v) < 2:
            raise ValueError("재진술 사슬은 표현이 2개 이상이어야 합니다.")
        return v


# ---------------------------------------------------------------------------
# 지문 전체 개관 (LLM 1차 호출) — ③ 글 예측
# ---------------------------------------------------------------------------
class Overview(BaseModel):
    theme_ko: str                 # 지문 제목용 한글 명사구(자료 상단 제목)
    topic: str                    # 🔎 소재(한 줄)
    stance: Stance                # 🗣 필자 의견
    stance_reason: str
    structure: Structure          # 🧩 글의 구조
    structure_reason: str
    restatement_chains: list[RestatementChain] = Field(min_length=2, max_length=3)


# ---------------------------------------------------------------------------
# ① 어휘 / ② 문장별 (LLM 2차 호출)
# ---------------------------------------------------------------------------
class Vocab(BaseModel):
    word: str
    meaning: str


class Chunk(BaseModel):
    en: str          # 영어 의미 단위(끊어읽기 조각)
    ko: str          # 그 조각의 직독직해 한국어
    blank: bool = False   # True면 '오역 위험' → 학생용에서 ko 를 빈칸으로(주관식)


class SentenceItem(BaseModel):
    id: int
    english: str                  # 문장 원문 전체
    syntax_tag: str = ""          # 구문 태그(예: '관계사절(play a role)·분사구')
    vocab: list[Vocab] = Field(default_factory=list)   # 이 문장 핵심 어휘(→ ① 어휘 리스트로 집계)
    chunks: list[Chunk]           # ② 끊어읽기(오역 위험 부분 blank=true)
    # ② '이 문장 내용' 객관식
    content_options: list[str] = Field(min_length=2, max_length=4)
    content_answer_index: int     # 정답 위치(0부터)
    content_explanation: str = "" # (선택) 정답 근거·오답 이유

    @field_validator("chunks")
    @classmethod
    def _has_chunks(cls, v: list[Chunk]) -> list[Chunk]:
        if not v:
            raise ValueError("문장에 끊어읽기 chunk 가 없습니다.")
        return v

    def check(self) -> None:
        if not (0 <= self.content_answer_index < len(self.content_options)):
            raise ValueError(f"문장 {self.id}: 내용 객관식 정답 인덱스가 범위를 벗어났습니다.")


class SentenceAnalysis(BaseModel):
    sentences: list[SentenceItem]

    def validate_all(self, n: int) -> None:
        got = len(self.sentences)
        if got != n:
            raise ValueError(f"문장 분석 개수({got})가 지문 문장 수({n})와 다릅니다.")
        ids = sorted(s.id for s in self.sentences)
        if ids != list(range(1, n + 1)):
            raise ValueError(f"문장 번호가 1~{n} 과 정확히 일치해야 합니다(현재 {ids}).")
        for s in self.sentences:
            s.check()

    # 하위호환 별칭
    def validate_count(self, n: int) -> None:
        self.validate_all(n)


# ---------------------------------------------------------------------------
# 최종 조립 결과 (렌더링 입력)
# ---------------------------------------------------------------------------
class LecturePassage(BaseModel):
    title: str
    source: str = ""
    item_no: str = ""
    sentences: list[LectureSentence]
    overview: Overview
    analysis: SentenceAnalysis

    @property
    def theme_ko(self) -> str:
        return self.overview.theme_ko or self.title
