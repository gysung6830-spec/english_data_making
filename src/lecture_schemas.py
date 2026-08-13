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
    label: str                 # 개념의 한글 이름(예: '두려움을 느끼는 아기')
    expressions: list[str]     # 지문에 실제로 나온 '영어' 표현들(순서대로, 2개 이상)
    variation: str = ""        # ↳변주: 표현이 어떻게 바뀌어 가는지 한 줄(한국어)

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
class GrammarDrill(BaseModel):
    """핵심 문법 연습문제(객관식 / 영작). '해석' 유형은 사용하지 않는다."""
    kind: Literal["객관식", "영작"]
    question: str         # 객관식=문제(밑줄·빈칸 포함) / 영작=한국어 문장
    answer: str           # 모범 답(객관식=정답 선택지 원문)
    options: list[str] = Field(default_factory=list)  # 객관식 선택지(3~5개)
    words: list[str] = Field(default_factory=list)    # 영작 제시 단어(반드시 제공)
    from_passage: bool = False  # 영작: 지문에 실제로 있는 문장 복원이면 True(응용이면 False)


class GrammarNote(BaseModel):
    """핵심 문법 설명의 한 줄 — 앞에 '신호어 칩' + 설명 본문."""
    chip: str             # 짧은 신호어 라벨(예: '쉽게 말하면', '왜 그래?', '생략', '복원', '주의', '해석 요령')
    text: str             # 설명 한 줄([[ ]] 빈칸 가능)


class KeyGrammar(BaseModel):
    """⑤ '이 지문의 핵심 문법 1개' — 지문 문장 박스 + 신호어 칩 설명 + 연습문제."""
    point: str            # 문법명(예: '관계사 that', '비교급 than절 도치·생략')
    source_sentence: str = ""   # 이 문법이 '실제로 나온' 지문 원문 문장(맨 위 박스에 표시)
    explanation: list[GrammarNote] = Field(min_length=3, max_length=6)  # 칩+설명(각 한 줄)
    example: str = ""     # (선택) 지문 속 짧은 예
    example_analysis: str = ""  # 지문 문장에서 무엇이 도치/생략/수식됐는지 한 줄
    # 연습문제: 객관식 3 + 영작 2(지문 문장 1 + 응용 1) = 5개 (해석 제외)
    drills: list[GrammarDrill] = Field(min_length=5, max_length=5)


class Overview(BaseModel):
    theme_ko: str                 # 지문 제목용 한글 명사구(자료 상단 제목)
    key_grammar: KeyGrammar       # 🔑 지문 앞 핵심 문법 1개
    topic: str                    # 🔎 소재(한 줄)
    stance: Stance                # 🗣 필자 의견
    stance_reason: str
    structure: Structure          # 🧩 글의 구조
    structure_reason: str
    # 재진술 사슬: 억지로 만들지 말고, 필자 핵심 의견을 이루는 개념의 실제 사슬만(1~2개)
    restatement_chains: list[RestatementChain] = Field(min_length=1, max_length=2)
    # 📝 글 내용 정리(글 순서): 의미 단위 블록 흐름(도입→전개→사례…)
    flow_blocks: list["FlowBlock"] = Field(min_length=2, max_length=6)


# ---------------------------------------------------------------------------
# ① 어휘 / ② 문장별 (LLM 2차 호출)
# ---------------------------------------------------------------------------
class Vocab(BaseModel):
    word: str
    meaning: str


class FlowBlock(BaseModel):
    """④ 글 내용 정리(글 순서)의 한 블록 — 도입/전개/사례/조건/확장 등."""
    stage: str            # 그 블록의 역할(도입/전개/사례/조건/전환/확장/결론 등)
    sentence_range: str   # 문장 번호 범위(예: '1~2', '6')
    summary: str          # 한 줄 요약. 핵심 단어는 [[ ]]로 감싸면 학생용에서 빈칸이 됨
    easy_example: str = ""  # 쉬운 일상 비유 한 줄


class Chunk(BaseModel):
    # 끊어읽기 조각. en/ko 안에서 '해석 어려운/오역 위험' 부분을 [[ ]]로 감싸면,
    # en 은 그 부분이 강조 표시(오역 주의), ko 는 그 부분이 '단어 위주 빈칸'이 된다.
    # ([[ ]]는 조각 통째가 아니라 단어/짧은 구 위주로, 조각 중간에 둬도 됨)
    en: str          # 영어 의미 단위(끊어읽기 조각)
    ko: str          # 그 조각의 직독직해 한국어


class GrammarChip(BaseModel):
    tag: str          # 짧은 어법명(칩 라벨). 예: '관계사 that', '분사구문', '비교급 도치'
    note: str = ""    # 간단 설명 한 줄(필생보처럼)


class Misread(BaseModel):
    """모두 '틀린 해석(X)'. 학생은 왜 X인지 찾고, why 로 확인한다."""
    statement: str    # 흔히 하는 오해/오역(틀린 해석 X)
    why: str          # 왜 틀렸는지 + 바른 뜻(어려운 내용도 쉬운 말로), 글 흐름 이해에 도움


class SentenceItem(BaseModel):
    id: int
    english: str                  # 문장 원문 전체
    grammar: list[GrammarChip] = Field(default_factory=list)  # 어법 칩(1~3개)
    vocab: list[Vocab] = Field(default_factory=list)   # 이 문장 핵심 어휘(→ 어휘 리스트로 집계)
    chunks: list[Chunk]           # ② 끊어읽기([[ ]]로 오역 위험 단어 빈칸)
    # 내용 확인: '이렇게 읽으면 오답(X)' 1~2개 → 왜 X인지 찾기
    misreads: list[Misread] = Field(min_length=1, max_length=2)

    @field_validator("chunks")
    @classmethod
    def _has_chunks(cls, v: list[Chunk]) -> list[Chunk]:
        if not v:
            raise ValueError("문장에 끊어읽기 chunk 가 없습니다.")
        return v

    def check(self) -> None:
        if not self.misreads:
            raise ValueError(f"문장 {self.id}: 오답(misread) 항목이 없습니다.")


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


# 전방 참조(Overview -> FlowBlock) 해소
Overview.model_rebuild()
