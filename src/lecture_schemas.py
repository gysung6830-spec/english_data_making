"""'강의컨셉 교재(필생보 스타일)' 데이터 모델 (pydantic).

학생이 문제를 풀며 스스로 학습하고(①②③), 강사는 답지(④⑤)로 정답을 함께 맞춰보는
'필자의 생각이 보이는 영어독해' 워크북 형식을 구현한다.

- 문장 분리·번호(1..n)는 코드가 결정론적으로 매기고(LectureSentence),
  문장별 분석(SentenceItem)은 그 번호를 그대로 사용한다.
- LLM 호출은 2단계: (1) 지문 전체 개관(Overview) → (2) 문장별 분석(SentenceAnalysis).
  개관에서 정한 '비유(analogy)'를 문장별 쉬운 예시가 공유하도록 순서를 잡는다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# 🗗 필자 주장 (3택)
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
# 문장 (코드가 분리·번호 부여) — ① 지문 통째로 읽기
# ---------------------------------------------------------------------------
class LectureSentence(BaseModel):
    id: int          # 1부터
    text: str


# ---------------------------------------------------------------------------
# ⑤ 재진술 사슬 (같은 개념이 지문에서 어떻게 다시 표현되는지)
# ---------------------------------------------------------------------------
class RestatementChain(BaseModel):
    label: str                    # 사슬 제목(예: '두려움을 느끼는 아기')
    expressions: list[str]        # 지문에 나온 순서대로의 표현들(2개 이상)
    variation: str                # ↳변주: 표현이 어떻게 바뀌어 가는지 한 줄

    @field_validator("expressions")
    @classmethod
    def _min_two(cls, v: list[str]) -> list[str]:
        v = [e.strip() for e in v if e and e.strip()]
        if len(v) < 2:
            raise ValueError("재진술 사슬은 표현이 2개 이상이어야 합니다.")
        return v


# ---------------------------------------------------------------------------
# 지문 전체 개관 (LLM 1차 호출) — ②/⑤ 예측·정답 + ④ 비유
# ---------------------------------------------------------------------------
class Overview(BaseModel):
    theme_ko: str                 # 지문 제목용 한글 명사구(자료 상단 제목)
    topic: str                    # 🔎 소재(한 줄)
    stance: Stance                # 🗣 필자 주장
    stance_reason: str            # 그렇게 본 근거(평가어·마지막 문장 등)
    structure: Structure          # 🧩 글의 구조
    structure_reason: str         # 그렇게 본 근거(전환·연결표현/문장 번호)
    restatement_chains: list[RestatementChain] = Field(min_length=2, max_length=3)
    analogy_name: str             # 💡 이 지문의 비유 이름(예: '놀이터 벤치')
    analogy_desc: str             # 비유를 지문 전체에 어떻게 대응시키는지 한 줄
    gist: str                     # ✅ 이 지문, 이 정도는 캐치!(전체 요지)


# ---------------------------------------------------------------------------
# ③/④ 문장별 분석 (LLM 2차 호출)
# ---------------------------------------------------------------------------
class Vocab(BaseModel):
    word: str
    meaning: str


class Chunk(BaseModel):
    en: str          # 영어 의미 단위(끊어읽기 조각)
    ko: str          # 그 조각의 직독직해 한국어


class SentenceItem(BaseModel):
    id: int
    english: str                  # 문장 원문 전체
    syntax_tag: str = ""          # 구문 태그(예: '관계사절(play a role)·분사구')
    vocab: list[Vocab] = Field(default_factory=list)   # 📘 어휘(힌트로 제공)
    chunks: list[Chunk]           # ④ 끊어읽기(/) + 직독직해
    catch: str = ""               # ✅ 이 정도는 캐치(이 문장으로 하고 싶은 말)
    easy_example: str = ""        # 💡 쉬운 예시(지문 비유 활용)

    @field_validator("chunks")
    @classmethod
    def _has_chunks(cls, v: list[Chunk]) -> list[Chunk]:
        if not v:
            raise ValueError("문장에 끊어읽기 chunk 가 없습니다.")
        return v


# 오역 포인트 문제 — 학생이 '해석을 다 적는' 대신 위험 지점만 골라 푼다
ProblemKind = Literal["객관식", "주관식"]


class TransProblem(BaseModel):
    no: int
    sentence_id: int              # 대상 문장 번호
    focus: str                    # 문제의 초점이 되는 '영어 구/표현'(밑줄 대상)
    kind: ProblemKind             # 객관식 / 주관식
    question: str                 # 발문
    options: list[str] = Field(default_factory=list)  # 객관식 선지(2~4). 주관식은 빈 리스트
    answer_index: int = -1        # 객관식 정답 인덱스(0부터). 주관식은 -1
    answer_text: str = ""         # 정답(주관식 정답 문구, 또는 객관식 정답 표현)
    explanation: str              # 오역 원인·해설

    @field_validator("options")
    @classmethod
    def _strip(cls, v: list[str]) -> list[str]:
        return [o.strip() for o in v if o and o.strip()]

    def check(self) -> None:
        if self.kind == "객관식":
            if not (2 <= len(self.options) <= 4):
                raise ValueError(f"객관식 선지는 2~4개여야 합니다(문제 {self.no}).")
            if not (0 <= self.answer_index < len(self.options)):
                raise ValueError(f"객관식 정답 인덱스가 범위를 벗어났습니다(문제 {self.no}).")
        else:  # 주관식
            if not self.answer_text.strip():
                raise ValueError(f"주관식 정답(answer_text)이 비어 있습니다(문제 {self.no}).")


class SentenceAnalysis(BaseModel):
    sentences: list[SentenceItem]
    problems: list[TransProblem] = Field(min_length=3, max_length=6)

    def validate_all(self, n: int) -> None:
        got = len(self.sentences)
        if got != n:
            raise ValueError(f"문장 분석 개수({got})가 지문 문장 수({n})와 다릅니다.")
        ids = sorted(s.id for s in self.sentences)
        if ids != list(range(1, n + 1)):
            raise ValueError(f"문장 번호가 1~{n} 과 정확히 일치해야 합니다(현재 {ids}).")
        for p in self.problems:
            if not (1 <= p.sentence_id <= n):
                raise ValueError(f"문제 {p.no}의 문장 번호({p.sentence_id})가 지문 범위를 벗어납니다.")
            p.check()

    # 하위호환용 별칭
    def validate_count(self, n: int) -> None:
        self.validate_all(n)


# ---------------------------------------------------------------------------
# 최종 조립 결과 (렌더링 입력)
# ---------------------------------------------------------------------------
class LecturePassage(BaseModel):
    title: str                    # 영어 제목/식별용(추출 단계 title)
    source: str = ""
    item_no: str = ""             # 원본 교재 문항 번호(제목 앞 표시)
    sentences: list[LectureSentence]
    overview: Overview
    analysis: SentenceAnalysis

    @property
    def theme_ko(self) -> str:
        return self.overview.theme_ko or self.title
