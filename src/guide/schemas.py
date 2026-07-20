"""구문해석 실전서 - 데이터 스키마.

- CodeCard: '답으로 이어지는 평가원 코드' 한 장(기출 문장 + 오역 + 정답 + 팁)
- Chapter : 한 카테고리(인과/대조/등호/비교/연결어) = 코드 카드 묶음
- Guide   : 실전서 한 권

카드 생성은 Claude 에게 CodeCard(의 생성 부분)만 JSON 으로 강제한다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class CardBody(BaseModel):
    """Claude 가 문장 하나에 대해 생성하는 부분(오역/정답/팁)."""
    highlight: str = Field(description="문장에서 코드 어구에 해당하는 정확한 원문 부분(그대로 인용)")
    literal_trap: str = Field(description="오역 — 이 코드를 무심코 직역할 때 나오는 잘못된 해석 한 줄")
    trap_why: str = Field(description="그 해석이 왜 틀렸는지(방향/논리 근거) 한 줄")
    correct: str = Field(description="정답 — 문맥·구조를 반영한 올바른 해석 한 줄")
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


class Guide(BaseModel):
    title: str = "구문해석 실전서"
    kicker: str = "평가원 기출로 익히는"
    subtitle: str = "단어를 몰라도, 문장이 복잡해도 핵심을 놓치지 않는 법"
    chapters: list[Chapter] = []


# Claude 구조화 출력 강제용: 한 문장 → CardBody 만 받는다.
class CardBodyOut(CardBody):
    """스키마 검증용 별칭(부가 필드 없이 CardBody 그대로)."""
    pass
