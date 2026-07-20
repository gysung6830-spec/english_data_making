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
    so_what: str = Field(default="", description="해석하면 이런 내용 — 이 문장이 결국 말하려는 바를 "
                         "구체적으로(추상적 문장을 실제 상황으로 풀어서) 한 줄")
    skeleton: str = Field(default="", description="이 문장의 뼈대(핵심 주어+동사)만 뽑은 한 줄(선택)")


class CodeCard(BaseModel):
    """렌더링에 쓰는 완성 카드(코드 정보 + 문장 + 생성 결과)."""
    code: str                 # 평가원 코드 어구 (예: be attributable to)
    code_ko: str              # 코드 뜻
    dir: str = ""             # 방향/성격 배지 (forward/backward 등, 선택)
    sentence: str             # 기출(또는 예문) 문장 원문
    source: str = ""          # 출처 라벨 (예: 2023 수능 34번), 선택
    body: CardBody


class Chapter(BaseModel):
    id: str
    title: str                # 예: 인과
    signal: str               # 이 코드들이 하는 역할 한 줄
    misread: str              # 대표 오역 유형
    tip: str                  # 챕터 공통 팁
    cards: list[CodeCard] = []


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


class Part0(BaseModel):
    title: str = "3단계 읽기 엔진"
    intro: str = ""
    spine: str = ""          # 관통 철학 한 문장
    methods: list[Method] = []
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
    modifiers: list[Modifier] = Field(description="괄호칠 수식어 덩어리들(문장에 등장 순서)")
    full_ko: str = Field(description="수식어를 연결어로 붙인 자연스러운 완성 해석")
    real_meaning: str = Field(default="", description="해석하면 이런 내용 — 이 문장이 결국 말하려는 "
                              "바를 구체적으로(추상→구체) 풀어 준 한 줄")
    self_check: str = Field(default="", description="학생이 직접 괄호쳐 볼 짧은 연습 한 줄(선택)")


class SyntaxBodyOut(SyntaxBody):
    pass


class SyntaxCard(BaseModel):
    sentence: str
    structure: str           # 구문 유형 라벨(관계사절 등)
    source: str = ""
    body: SyntaxBody


class SyntaxChapter(BaseModel):
    id: str
    title: str               # 예: 관계사절
    signal: str              # 이 구문의 감지 신호/설명
    how: str                 # 이 구문을 괄호치는 법 한 줄
    cards: list[SyntaxCard] = []


class Part2(BaseModel):
    title: str = "구문별 괄호치기 실전"
    intro: str = ""
    chapters: list[SyntaxChapter] = []


class Guide(BaseModel):
    title: str = "구문해석 실전서"
    kicker: str = "평가원 기출로 익히는"
    subtitle: str = "단어를 몰라도, 문장이 복잡해도 핵심을 놓치지 않는 법"
    part0: Part0 | None = None                 # 0부 기본기
    chapters: list[Chapter] = []               # 1부 평가원 코드
    part2: Part2 | None = None                 # 2부 구문해석


# Claude 구조화 출력 강제용: 한 문장 → CardBody 만 받는다.
class CardBodyOut(CardBody):
    """스키마 검증용 별칭(부가 필드 없이 CardBody 그대로)."""
    pass
