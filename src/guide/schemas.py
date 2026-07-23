"""구문해석 실전서 - 데이터 스키마.

- CodeCard: '답으로 이어지는 평가원 코드' 한 장(기출 문장 + 오역 + 정답 + 팁)
- Chapter : 한 카테고리(인과/대조/등호/비교/연결어) = 코드 카드 묶음
- Guide   : 실전서 한 권

카드 생성은 Claude 에게 CodeCard(의 생성 부분)만 JSON 으로 강제한다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class CardBody(BaseModel):
    """Claude 가 문장 하나에 대해 생성하는 부분(오역/정답/팁/진짜 의미)."""
    highlight: str = Field(description="문장에서 코드 어구에 해당하는 정확한 원문 부분(그대로 인용)")
    literal_trap: str = Field(description="오역 — 이 코드를 무심코 직역할 때 나오는 잘못된 해석 한 줄")
    trap_why: str = Field(description="그 해석이 왜 틀렸는지(방향/논리/필자 입장 근거) 한 줄")
    correct: str = Field(description="정답 — 문맥·구조를 반영한 올바른 해석 한 줄")
    so_what: str = Field(default="", description="해석하면 이런 내용 — '이 문장 하나만으로' 도출되는 "
                         "구체화. 앞뒤 지문·필자 의도 추측 금지. 지시어 대상이 문장 밖이면 언급하지 말 것")
    so_what_basis: str = Field(default="", description="구체화 근거 — 위 '이런 내용'을 어느 문장 단서에서 "
                               "끌어냈는지(동격·수식어·예시·대조 등)를 '근거: …' 형태로 짧게")
    subject: str = Field(default="", description="주체(누가) — 문장의 진짜 주어를 짧게")
    action: str = Field(default="", description="행위(무엇을 한다) — 진짜 동사+목적어를 짧게")
    skeleton: str = Field(default="", description="이 문장의 뼈대(핵심 주어+동사)만 뽑은 한 줄(선택)")
    cut: str = Field(default="", description="끊어읽기 — 의미 단위 슬래시(/) 직독직해(선택)")


class CodeCard(BaseModel):
    """렌더링에 쓰는 완성 카드(코드 정보 + 문장 + 생성 결과)."""
    code: str                 # 평가원 코드 어구 (예: be attributable to)
    code_ko: str              # 코드 뜻
    dir: str = ""             # 방향/성격 배지 (forward/backward 등, 선택)
    sentence: str             # 기출(또는 예문) 문장 원문
    source: str = ""          # 출처 라벨 (예: 2023 고3 6월 34번)
    difficulty: str = ""      # '중' / '고'
    body: CardBody


# ── 어휘 박스 / 문제 ──────────────────────────────────────────
class VocabItem(BaseModel):
    word: str
    meaning: str


class Problem(BaseModel):
    """예시 외 나머지 기출을 '문제'로 낸다."""
    kind: str                 # 'mc'(객관식: 오역 vs 정답 고르기) | 'short'(주관식)
    sentence: str
    source: str = ""
    prompt: str = ""          # 발문 (예: '밑줄 친 부분의 올바른 해석은?')
    options: list[str] = []   # mc: [오역해석, 정확한해석] (순서는 섞을 수 있음)
    answer_index: int = 0     # mc: 정답 보기 인덱스
    answer: str = ""          # short: 모범 답안(핵심 해석)
    trap: str = ""            # 흔히 하는 오역(주관식 힌트/해설용)
    point: str = ""           # 이 문제의 핵심 포인트(해설)
    cut: str = ""             # 끊어읽기(슬래시 직독직해)


# ── 실전적용: 문제 페이지 ↔ 해설 페이지 ─────────────────────
class PracticeSolution(BaseModel):
    cut: str = ""                 # 끊어읽기(슬래시 직독직해)
    wrong: str = ""               # 오역(흔한 실수)
    wrong_why: str = ""           # 왜 틀렸나
    author_msg: str = ""          # 필자가 하고싶은 말
    key_points: list[str] = []    # 주요구문(각 'X : 설명')


class PracticeItem(BaseModel):
    no: int = 0
    kind: str = "mc"              # 'mc'(객관식) | 'short'(주관식)
    sentence: str                 # 기출 문장(지문)
    source: str = ""
    prompt: str = ""              # 발문
    options: list[str] = []       # mc 선지 [오역, 정답 등]
    answer_index: int = 0
    answer: str = ""              # short 모범답안
    vocab: list[VocabItem] = []   # 문제 페이지 하단 단어 박스
    solution: PracticeSolution | None = None   # 해설 페이지


class Chapter(BaseModel):
    id: str
    title: str                # 예: 인과
    signal: str               # 이 코드들이 하는 역할 한 줄
    misread: str              # 대표 오역 유형
    tip: str                  # 챕터 공통 팁
    core_tip: str = ""        # 문장 '핵심'을 잡는 구체적 tip
    infer_tip: str = ""       # 문장/단어 '유추'하는 법
    cards: list[CodeCard] = []   # 예시(중난이도 5 + 고난이도 5 지향)
    problems: list[Problem] = [] # 나머지 기출을 문제로(레거시 인라인)
    practice: list[PracticeItem] = []  # 실전적용(문제↔해설 페이지, 객5·주5)
    vocab: list[VocabItem] = []  # 페이지 하단 어휘 박스


# ── 0부: 3단계 읽기 엔진 (고정 콘텐츠) ──────────────────────────
class MethodDemo(BaseModel):
    """한 방법(STEP)의 기출 시연: 괄호 → 뼈대 → 완성."""
    sentence: str            # 기출/예문 원문
    bracketed: str = ""      # 수식어를 (…) 로 묶은 모습(텍스트)
    skeleton_en: str = ""    # 뼈대(S+V) 영어
    skeleton_ko: str = ""    # 뼈대 중3 한국어
    full_ko: str = ""        # 살 붙인 완성 해석


class Method(BaseModel):
    step: str                # 예: STEP 1
    title: str               # 예: 괄호치기
    idea: str                # 원리 한 줄
    rule: str = ""           # 규칙
    ms_point: str = ""       # 중3 포인트(왜 쉬워지는지)
    demo: MethodDemo | None = None


class DepthDemo(BaseModel):
    """'읽기 깊이' 실제 예시 — 유형별로 '이만큼만 읽으면 된다'(형광펜)."""
    kind: str                # 유형 라벨 (예: 주제·요지 파악 / 빈칸 추론)
    source: str = ""
    goal: str = ""           # 이 유형에서 '무엇을 찾나' 한 줄
    passage: str = ""        # 지문(==꼭 읽을 곳== 을 == 로 감싼다)
    read: str = ""           # '형광펜만 읽으면 …' 정리 한 줄


class Part0(BaseModel):
    title: str = "3단계 읽기 엔진"
    intro: str = ""
    spine: str = ""          # 관통 철학 한 문장
    methods: list[Method] = []
    depth_demos: list[DepthDemo] = []   # '읽기 깊이' 형광펜 예시
    tools: list[str] = []    # 미니 도구 한 줄 목록


# ── 2부: 구문별 괄호치기 실전 ──────────────────────────────────
class Modifier(BaseModel):
    """괄호칠 수식어 한 덩어리."""
    phrase: str              # 수식어 원문(그대로 인용)
    kind: str                # 관계사절/분사/전치사구/삽입 등
    connector: str           # 붙일 때 쓰는 연결어(~하는/~하면서 등)
    meaning: str             # 그 수식어의 한국어 뜻


class SyntaxBody(BaseModel):
    """Claude 가 한 문장에 대해 생성하는 부분."""
    skeleton_en: str = Field(description="수식어를 뺀 뼈대(핵심 S+V+O) 영어 — 아주 짧게")
    skeleton_ko: str = Field(description="그 뼈대의 중3 수준 쉬운 한국어 해석")
    subject: str = Field(default="", description="주체(누가) — 문장의 진짜 주어를 짧게")
    action: str = Field(default="", description="행위(무엇을 한다) — 진짜 동사+목적어를 짧게")
    modifiers: list[Modifier] = Field(description="괄호칠 수식어 덩어리들(문장에 등장 순서)")
    full_ko: str = Field(description="수식어를 연결어로 붙인 자연스러운 완성 해석")
    real_meaning: str = Field(default="", description="해석하면 이런 내용 — '이 문장 하나만으로' "
                              "도출되는 구체화. 앞뒤 지문·필자 의도 추측 금지. 지시어 대상이 문장 밖이면 언급 말 것")
    self_check: str = Field(default="", description="학생이 직접 괄호쳐 볼 짧은 연습 한 줄(선택)")


class SyntaxBodyOut(SyntaxBody):
    pass


class SyntaxCard(BaseModel):
    sentence: str
    structure: str           # 구문 유형 라벨(관계사절 등)
    source: str = ""
    difficulty: str = ""     # '중' / '고'
    body: SyntaxBody


# ── 해석공식 시각화 ──────────────────────────────────────────
class FormulaRow(BaseModel):
    en: str
    ko: str


class Diagram(BaseModel):
    symbol: str = ""              # 다이어그램 좌측 큰 기호 (NOT / A>B / N←[wh~] 등)
    rows: list[FormulaRow] = []


class WorkExample(BaseModel):
    en: str                       # 기출 문장(원문)
    src: str = ""                 # 출처
    cut: str = ""                 # 끊어읽기(슬래시 직독직해)
    ab: str = ""                  # A→B 단순화(뼈대 관계) 한 줄


class TrainStep(BaseModel):
    level: str                    # 단계 라벨 (① 쉬움 …)
    en: str
    ko: str


class SyntaxChapter(BaseModel):
    id: str
    title: str               # 예: 부정구문
    signal: str              # 이 구문의 감지 신호/설명
    how: str                 # 괄호치는 법 한 줄
    point: str = ""          # Point 박스 개념
    strategy: str = ""       # 실전 해석 전략 한 줄
    diagram: Diagram | None = None    # 해석공식 다이어그램
    examples: list[WorkExample] = []  # 기출 예문 + 끊어읽기
    training: list[TrainStep] = []    # 단계별 트레이닝(쉬움→하드)
    practice: list[PracticeItem] = [] # 실전적용(문제↔해설)
    combat_tip: str = ""
    cards: list[SyntaxCard] = []
    problems: list[Problem] = []
    vocab: list[VocabItem] = []


class SyntaxPartGroup(BaseModel):
    id: str
    title: str               # 예: 극성 판단 구문
    subtitle: str = ""
    strategy: str = ""
    chapters: list[SyntaxChapter] = []


class Part2(BaseModel):
    title: str = "구문해석 — 해석공식을 눈으로"
    intro: str = ""
    groups: list[SyntaxPartGroup] = []


# ── 패러프레이징 파트(지문 단위): 핵심주제가 어떻게 다른 표현으로 전개되는가 ──
class ParaphraseLink(BaseModel):
    excerpt: str = Field(description="지문 속 표현(핵심주제를 담거나 재진술한 문장·구, 원문 인용)")
    role: str = Field(description="역할: 주제제시 / 재진술 / 예시 / 부연 / 결론 중 하나")
    restated: str = Field(description="그 표현이 '핵심주제'를 어떻게 바꿔 말했는지 한국어로 한 줄")


class ParaphrasePassage(BaseModel):
    source: str = ""
    passage: str = Field(description="지문 전체(영어 원문)")
    main_idea: str = Field(description="이 지문의 핵심주제(필자가 하려는 말) 한국어 한 문장")
    main_idea_en: str = Field(default="", description="핵심주제를 담은 영어 한 문장")
    links: list[ParaphraseLink] = Field(description="같은 핵심주제가 다른 표현으로 전개되는 사슬")
    answer_expression: str = Field(default="", description="요지·주제 문제의 정답이 될 만한 "
                                   "패러프레이즈 표현(지문 표현을 바꿔 쓴 것)")


class ParaphrasePart(BaseModel):
    title: str = "패러프레이징 — 같은 주제, 다른 표현"
    intro: str = ""
    passages: list[ParaphrasePassage] = []


# ── 추상 → 구체 파트 ─────────────────────────────────────────
class AbstractChapter(BaseModel):
    id: str
    title: str
    point: str = ""
    strategy: str = ""
    exprs: list[FormulaRow] = []      # 추상 표현 목록 (en → ko)
    examples: list[WorkExample] = []  # 기출 예문 + 구체화(끊어읽기)
    practice: list[PracticeItem] = [] # 실전적용(문제↔해설)


class AbstractPart(BaseModel):
    title: str = "추상 → 구체"
    intro: str = ""
    chapters: list[AbstractChapter] = []


class Guide(BaseModel):
    title: str = "구문해석 실전서"
    kicker: str = "평가원 기출로 익히는"
    subtitle: str = "단어를 몰라도, 문장이 복잡해도 핵심을 놓치지 않는 법"
    part0: Part0 | None = None                 # 0부 기본기
    inference: AbstractPart | None = None       # 어휘 유추(별도 목차) — AbstractPart 재사용
    chapters: list[Chapter] = []               # 1부 평가원 코드
    paraphrase: ParaphrasePart | None = None   # 2부 패러프레이징(지문 단위)
    abstract: AbstractPart | None = None       # 추상→구체
    part2: Part2 | None = None                 # 3부 구문해석


# Claude 구조화 출력 강제용: 한 문장 → CardBody 만 받는다.
class CardBodyOut(CardBody):
    """스키마 검증용 별칭(부가 필드 없이 CardBody 그대로)."""
    pass
