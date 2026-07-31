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
    slash: bool = False                # 이 토큰 뒤에 끊어읽기 경계 '/' 표시

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
    translation: str = ""                        # 한글 해석(온전한 해석 = 박스)
    reading_ko: str = ""                         # 직독직해(끊어읽기) 한글, ' / '로 구분
    badge: str | None = None                     # '빈','서','예시' 등 짧은 뱃지
    gloss_en: str | None = None                  # 함축 의미 영어(독해 Point 박스)
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
# 직독직해(레이아웃 B) 요소 — 의미 단위 청크 + 문장별 핵심 문법 + 핵심 단어
# ---------------------------------------------------------------------------
@dataclass
class KeyWord:
    """직독직해 하단의 핵심 단어 한 항목."""

    word: str
    meaning: str


@dataclass
class LitChunk:
    """의미 단위(‘/’로 끊는 직독직해 청크). 영어·한글이 같은 색으로 대응된다."""

    english: str
    korean: str
    words: list["KeyWord"] = field(default_factory=list)  # 이 청크의 핵심 단어


@dataclass
class GrammarChip:
    """문장에 딸린 핵심 문법 태그(테두리 알약) + 설명."""

    point: str               # 어법 이름(예: '과거분사 후치수식')
    explanation: str = ""    # 짧은 설명
    key: bool = False        # ★필수 어법(관계사·분사·가정법·비교·도치·강조·5형식 등)
    ci: int | None = None    # 해당 청크 색 인덱스(0~7). 없으면 기본 문법색


@dataclass
class LiteralSentence:
    """직독직해(B형) 문장 하나 = 번호 + 청크들 + 핵심 문법 + '쉽게' 한 줄."""

    no: int
    chunks: list[LitChunk] = field(default_factory=list)
    grammar: list[GrammarChip] = field(default_factory=list)
    note: str = ""           # '쉽게' 요약 한 줄(선택)

    @property
    def words(self) -> list["KeyWord"]:
        """청크에 흩어진 핵심 단어를 문장 단위로 모은 목록."""
        return [w for c in self.chunks for w in c.words]


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
    # 직독직해(레이아웃 B) — 비어 있으면 렌더 시 원문/해석만 대체 표기한다.
    literal: list[LiteralSentence] = field(default_factory=list)
    # 뒷면을 1페이지에 맞추기 위해 더 압축할지(렌더러가 측정해 설정). 장문이면 False 유지.
    back_tight: bool = False
    # 앞면(분석) 밀도: '' | 'normal' | 'compact' | 'ultra'. 렌더러가 지문별로 측정해
    # 1페이지에 맞는 가장 큰(덜 압축된) 단계를 넣는다. 장문이면 ultra 여도 2페이지.
    front_density: str = ""

    @property
    def has_points(self) -> bool:
        return any(s.points for s in self.sentences)

    @property
    def has_back(self) -> bool:
        return bool(self.vocab or self.flow)

    @property
    def has_literal(self) -> bool:
        return bool(self.literal)
