"""구문 분석 학습지의 데이터 모델 (명세서 §4).

지문 1회 분석 결과(`Analysis`)를 만들어 렌더러(레이아웃 A/B)가 소비한다.
LLM 응답을 그대로 담을 수 있도록 순수 dataclass 로 정의하고, 렌더링에 필요한
파생 값(성분 라벨 색·오답형 표기 등)은 renderer 쪽에서 CSS 로 처리한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# 주석 종류 → CSS 클래스. 명세서 §3.2 색상 토큰과 대응.
NOTE_KINDS = ("lbl", "red", "gray", "blue")

# 하이라이트 종류: y=노랑, g=연두, p=라벤더(담화표지/강조)
HL_KINDS = ("y", "g", "p")


@dataclass
class Token:
    """화면에 보일 단어/구 + 그 아래·위에 붙는 문법 주석."""

    text: str                          # 화면에 보일 단어/구
    role: str | None = None            # 'S','V','O','C','S①' ... (성분 라벨)
    note: str | None = None            # 문법 주석 (예: '현재분사')
    note_kind: str = "lbl"             # 'lbl' | 'red' | 'gray' | 'blue'
    wrong: str | None = None           # 오답형 '(X)'  예: 'directed/direct(X)'
    above: str | None = None           # 토큰 위 메모 (예: 'it is 생략')
    hl: str | None = None              # 'y' | 'g' | None (노랑/연두 하이라이트)
    underline: bool = False            # 밑줄
    color: str | None = None           # 'red' | 'blue' | None (본문 글자색)

    def __post_init__(self) -> None:
        if self.note_kind not in NOTE_KINDS:
            self.note_kind = "lbl"
        if self.hl not in (None, *HL_KINDS):
            self.hl = None


@dataclass
class Point:
    """문장 오른쪽에 놓이는 포인트 카드."""

    kind: str                # 'reading' | 'grammar'
    caption: str             # 'N번 문장 어법 Point'
    body_html: str           # 박스 내용(리스트/표 포함 가능, 신뢰된 HTML)

    @property
    def is_grammar(self) -> bool:
        return self.kind == "grammar"


@dataclass
class Sentence:
    """문장 하나 = 번호 + 줄 단위 토큰 + 해석 + 포인트들."""

    index: int                                   # 문장 번호(1부터)
    lines: list[list[Token]] = field(default_factory=list)  # 줄바꿈 단위 토큰
    translation: str = ""                        # 한글 해석
    badge: str | None = None                     # '빈','서','예시' 등 짧은 뱃지
    gloss_en: str | None = None                  # 함축 의미 영어(떠먹여주는 Point 박스)
    gloss_ko: str | None = None                  # 함축 의미 한글(영어와 병기)
    refs: list[str] = field(default_factory=list)  # 대명사 지칭(예: 'it → the teabag')
    points: list[Point] = field(default_factory=list)       # 오른쪽 박스들

    @property
    def has_feed(self) -> bool:
        return bool(self.refs or self.gloss_en)

    @property
    def tokens(self) -> list[Token]:
        """줄 구분 없이 펼친 토큰 목록."""
        return [t for line in self.lines for t in line]

    @property
    def text(self) -> str:
        """영어 원문(토큰을 공백으로 이어붙임)."""
        return " ".join(t.text for t in self.tokens).strip()


# ---------------------------------------------------------------------------
# 뒷페이지(요약 페이지) 요소 — 어휘 리스트 / 논리 흐름도 / 쉬운 예시 목차
# ---------------------------------------------------------------------------
@dataclass
class VocabEntry:
    """핵심 어휘 한 항목 (유의어·반의어 포함)."""

    word: str
    meaning: str
    syn: str = ""            # 유의어(쉼표 구분)
    ant: str = ""            # 반의어(쉼표 구분)
    sent: int | None = None  # 등장 문장 번호(선택)


@dataclass
class FlowStep:
    """논리 흐름도의 한 단계 (쉬운 예시를 같은 목차에 포함)."""

    label: str               # '비유','원리','적용','주장','결론' 등 단계명
    text: str                # 개조식 논리 내용
    easy: str = ""           # 학생 눈높이 쉬운 예시 한 줄(같은 단계에 함께 표시)
    sentences: str = ""      # 관련 문장 번호(예: '1~3')


@dataclass
class Analysis:
    """지문 1개의 전체 분석 결과 (렌더러 입력)."""

    title_en: str = ""
    title_ko: str = ""
    lecture_label: str = ""                      # '20' / '14강'
    date: str = ""                               # '2025년 09월'
    sentences: list[Sentence] = field(default_factory=list)
    # 뒷페이지(선택) — 비어 있으면 렌더 시 뒷페이지를 만들지 않는다.
    vocab: list[VocabEntry] = field(default_factory=list)
    flow: list[FlowStep] = field(default_factory=list)

    @property
    def has_points(self) -> bool:
        return any(s.points for s in self.sentences)

    @property
    def has_back(self) -> bool:
        return bool(self.vocab or self.flow)
