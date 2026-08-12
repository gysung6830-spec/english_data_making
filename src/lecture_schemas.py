"""'강의컨셉 교재 자동생성기' 데이터 모델 (pydantic).

명세서 4장(데이터 모델)을 구현한다. 학생이 능동적으로 훈련하는 5개 섹션
(어휘 힌트 / 오역포인트 / 문장 역할 / 함정포인트 / 패러프레이징)의 구조화된 출력이다.

- 문장 분리·번호(S1, S2…)는 코드가 결정론적으로 매기고(LectureSentence),
  LLM 응답(LectureAnalysis)은 그 문장 번호를 '참조'만 하도록 설계한다.
  (번호가 흔들리지 않아 검증·렌더링이 안정적)
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# 문장 역할 라벨(고정 5종) — 명세 3-C
ROLE_LABELS: tuple[str, ...] = ("통념", "전환", "근거", "예시", "결론")
RoleLabel = Literal["통념", "전환", "근거", "예시", "결론"]

# 오역 유형 태그 — 명세 3-B
TransTrapType = Literal["다의어", "구조오인", "관용표현", "지칭 오류", "반의어 치환"]

# 함정포인트 유형(3종 중 실제 존재하는 1개만) — 명세 3-D
TrapQType = Literal["지칭 오류", "연결어 반전 오독", "생략된 주어 오인"]


# ---------------------------------------------------------------------------
# 문장 (코드가 분리·번호 부여)
# ---------------------------------------------------------------------------
class LectureSentence(BaseModel):
    id: int          # 1부터. 화면에는 S1, S2… 로 표시
    text: str


# ---------------------------------------------------------------------------
# 3-A. 어휘 힌트 (4~6개)
# ---------------------------------------------------------------------------
class VocabHint(BaseModel):
    word: str        # 단어/표현(지문에 나온 형태)
    meaning: str     # 짧은 뜻(전체 해석 아님)


# ---------------------------------------------------------------------------
# 3-B. 오역포인트 교정 연습 (2~3개)
# ---------------------------------------------------------------------------
class TranslationTrap(BaseModel):
    sentence_id: int              # 대상 문장 번호(지문 내 실제 문장)
    wrong_translation: str        # 흔히 하는 오역(표면적/직역 오류)
    correct_translation: str      # 올바른 해석
    trap_type: TransTrapType      # 오역 유형 태그
    reason: str                   # 왜 오역인지(다의어/구조오인/관용표현 등 원인)


# ---------------------------------------------------------------------------
# 3-C. 문장 역할 파악 (3~5개 블록)
# ---------------------------------------------------------------------------
class RoleBlock(BaseModel):
    sentence_ids: list[int]       # 이 블록에 묶이는 문장 번호들(연속)
    correct_label: RoleLabel      # 정답 라벨(5종 중 하나)
    reason: str                   # 이 역할인 근거 1줄

    @field_validator("sentence_ids")
    @classmethod
    def _non_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("역할 블록에 문장 번호가 없습니다.")
        return v


# ---------------------------------------------------------------------------
# 3-D. 함정포인트 문항 (1개)
# ---------------------------------------------------------------------------
class TrapQuestion(BaseModel):
    type: TrapQType
    sentence_id: int = 0          # 함정이 걸린 문장 번호(참고용, 없으면 0)
    question_text: str            # 발문(예: "밑줄 친 it 이 가리키는 것은?")
    option_wrong: str             # 흔히 하는 오답
    option_correct: str           # 올바른 답
    explanation: str              # 해설


# ---------------------------------------------------------------------------
# 3-E. 패러프레이징 줄잇기 (2~3개)
# ---------------------------------------------------------------------------
class ParaphraseItem(BaseModel):
    choice_text: str                 # 선지(본문 표현을 유의어/구조 변형한 문장)
    matched_sentence_ids: list[int]  # 대응하는 본문 문장 번호(1:1 또는 1:多)

    @field_validator("matched_sentence_ids")
    @classmethod
    def _non_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("패러프레이징 선지에 대응 문장이 없습니다.")
        return v


# ---------------------------------------------------------------------------
# LLM 응답 (문장 번호를 참조하는 5개 섹션)
# ---------------------------------------------------------------------------
class LectureAnalysis(BaseModel):
    vocab_hints: list[VocabHint] = Field(min_length=4, max_length=6)
    translation_traps: list[TranslationTrap] = Field(min_length=2, max_length=3)
    role_blocks: list[RoleBlock] = Field(min_length=3, max_length=5)
    trap_question: TrapQuestion
    paraphrase_items: list[ParaphraseItem] = Field(min_length=2, max_length=3)

    def validate_refs(self, n_sentences: int) -> None:
        """모든 문장 번호 참조가 [1, n] 범위 안인지 검증(없는 문장 지어내기 방지)."""
        def _ok(i: int) -> bool:
            return 1 <= i <= n_sentences

        bad: list[str] = []
        for t in self.translation_traps:
            if not _ok(t.sentence_id):
                bad.append(f"오역포인트 문장 {t.sentence_id}")
        for b in self.role_blocks:
            for i in b.sentence_ids:
                if not _ok(i):
                    bad.append(f"역할블록 문장 {i}")
        if self.trap_question.sentence_id and not _ok(self.trap_question.sentence_id):
            bad.append(f"함정포인트 문장 {self.trap_question.sentence_id}")
        for p in self.paraphrase_items:
            for i in p.matched_sentence_ids:
                if not _ok(i):
                    bad.append(f"패러프레이징 문장 {i}")
        if bad:
            raise ValueError(
                f"지문에 없는 문장 번호를 참조했습니다(총 문장 {n_sentences}개): "
                + ", ".join(bad)
            )


# ---------------------------------------------------------------------------
# 최종 조립 결과 (렌더링 입력) — 명세 4장 PassageOutput
# ---------------------------------------------------------------------------
class LecturePassage(BaseModel):
    title: str
    source: str = ""
    item_no: str = ""              # 원본 교재의 문항 번호(제목 앞에 표시)
    sentences: list[LectureSentence]
    analysis: LectureAnalysis
