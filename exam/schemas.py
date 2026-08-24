"""LLM 이 각 단계에서 돌려줘야 하는 구조화 JSON 스키마 (pydantic).

핵심 원칙(단일 지문 공유):
- 생성기는 '지문을 다시 쓰지' 않는다. 대신 분석 결과의 문장(sentences)을
  '어떻게 변형할지'(문장 번호·단어·순서)만 돌려준다.
- 실제 HTML 조립은 코드(exam.build)가 정본 문장에서 수행하므로,
  6종이 모두 '같은 지문'을 공유하는 것이 구조적으로 보장된다.
- 문장 번호(sent_no, remove_no 등)는 분석 결과에 표시된 (1),(2)… 와 같은 '1-based'.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


def _require_all_distractors(answer_no: int, wrong_reasons) -> None:
    """정답을 제외한 4개 선지가 모두 '틀린 이유'와 함께 설명됐는지 확인.

    → 각 오답이 왜 틀린지 근거를 반드시 대게 하여 '정답급 오답'을 걸러낸다.
    """
    expected = {i for i in range(1, 6) if i != answer_no}
    got = {w.no for w in wrong_reasons}
    if got != expected:
        raise ValueError(f"오답 설명은 정답(제외) 4개 선지를 모두 다뤄야 합니다: "
                         f"필요 {sorted(expected)}, 받음 {sorted(got)}")


# ---------------------------------------------------------------------------
# 공통: 지문 1회 분석 (analyzer) — 6종이 나눠 쓴다
# ---------------------------------------------------------------------------
class KeyTerm(BaseModel):
    word: str
    synonym: str
    antonym: str = ""


class PassageText(BaseModel):
    """사진/이미지에서 비전으로 옮겨 적은 영어 지문 본문."""
    text: str


class Analysis(BaseModel):
    title: str
    # 정본 지문(문장 단위). LLM 이 돌려주는 값은 '참고용'이고, analyze() 가 곧바로
    # '사용자가 넣은 원문을 코드가 나눈 것'으로 덮어쓴다. 그래서 여기에 개수 조건을
    # 걸면 안 된다 — 쓰지도 않을 값 때문에 생성 전체가 죽는다(실제로 모델이 빈
    # 배열을 돌려줘 지문 두 개짜리 작업이 통째로 실패했다).
    sentences: list[str] = Field(default_factory=list)
    main_idea: str
    # 지문 종류(유형 적합성 검수용): prose(설명·논설)·narrative(서사·심경)·
    # notice(안내문)·chart(도표)·letter(편지)·dialogue(대화). 기본 prose.
    passage_type: str = "prose"
    key_terms: list[KeyTerm] = Field(default_factory=list)
    hardest_sentence: str = ""
    # 공통 출제 지침(생성 전에 주입, 모든 유형 프롬프트에 함께 전달). LLM 이 채우지 않음.
    difficulty_note: str = ""

    @field_validator("sentences")
    @classmethod
    def _clean_sentences(cls, v: list[str]) -> list[str]:
        """빈 줄만 걸러 낸다. '몇 개 이상'은 원문을 보고 analyze() 가 판정한다."""
        return [s.strip() for s in v if s and s.strip()]


# ---------------------------------------------------------------------------
# ① 순서 배열 — 정본을 덩어리로 쪼개 라벨만 섞음
# ---------------------------------------------------------------------------
class OrderOut(BaseModel):
    """순서 배열 — 나머지 문장을 (A)(B)(C)(D) 네 덩어리로 쪼개 라벨만 섞는다.

    네 덩어리면 가능한 배열이 6가지에서 24가지로 늘어 찍기가 훨씬 어려워진다.
    문장이 모자란 짧은 지문에서는 세 덩어리도 허용한다(빌더가 알아서 줄인다).
    """

    given_n: int                   # 앞에서 몇 문장을 '주어진 글'로 (>=1)
    block_sizes: list[int]         # 나머지를 3~4덩어리로 (len==3 또는 4)
    display: list[int]             # (A)(B)(C)(D) 가 각각 원래 몇 번째 덩어리인지
    reason: str

    @field_validator("block_sizes")
    @classmethod
    def _three_or_four(cls, v: list[int]) -> list[int]:
        if len(v) not in (3, 4):
            raise ValueError("block_sizes 는 3개 또는 4개여야 합니다(기본 4).")
        if any(x < 1 for x in v):
            raise ValueError("각 덩어리에는 문장이 1개 이상 있어야 합니다.")
        return v

    @model_validator(mode="after")
    def _perm(self):
        k = len(self.block_sizes)
        if sorted(self.display) != list(range(1, k + 1)):
            raise ValueError(f"display 는 1~{k} 의 순열이어야 합니다"
                             f"(block_sizes 가 {k}개이므로).")
        return self


# ---------------------------------------------------------------------------
# ② 문장 삽입 — 정본에서 문장 하나만 빼냄
# ---------------------------------------------------------------------------
class InsertOut(BaseModel):
    remove_no: int                 # 빼낼 문장 번호(1-based, 내부 문장)
    reason: str


# ---------------------------------------------------------------------------
# ③ 주제 (영어 선지, 지문은 원본 그대로)
# ---------------------------------------------------------------------------
class WrongReason(BaseModel):
    no: int
    text: str


class TitleOut(BaseModel):
    """제목(수능 24번) — 영어 명사구 선지 5개. 구조는 주제와 같다."""

    choices: list[str]
    answer_no: int
    reason: str
    wrong_reasons: list[WrongReason]

    @field_validator("choices")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("제목 선지는 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v

    @model_validator(mode="after")
    def _distractors(self):
        # 이 검사가 없어 정답 번호까지 오답 목록에 들어갔고, 해설에 빈 줄이 찍혔다.
        _require_all_distractors(self.answer_no, self.wrong_reasons)
        return self


class IrrelevantOut(BaseModel):
    """무관한 문장(수능 35번).

    도입 문장 뒤 연속 5문장에 ①~⑤를 붙이고, 그중 한 자리(answer_no)의 원문 문장을
    새로 쓴 '흐름과 무관한 문장'(sentence)으로 갈아 끼운다. 나머지 4자리는 원문 그대로.
    """

    start_no: int          # ①이 붙을 원문 문장 번호(1-based). 도입문이 있어야 하므로 2 이상.
    answer_no: int         # 1~5 — 무관한 문장을 끼워 넣을 자리
    sentence: str          # 그 자리에 넣을, 흐름과 무관한 새 영어 문장
    reason: str
    wrong_reasons: list[WrongReason]

    @field_validator("answer_no")
    @classmethod
    def _in_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("무관한 문장 번호는 1~5 여야 합니다.")
        return v

    @field_validator("start_no")
    @classmethod
    def _has_intro(cls, v: int) -> int:
        if v < 2:
            raise ValueError("①은 도입 문장 다음부터 시작해야 합니다(start_no 는 2 이상).")
        return v


class TopicOut(BaseModel):
    choices: list[str]
    answer_no: int
    reason: str
    wrong_reasons: list[WrongReason]

    @field_validator("choices")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("주제 선지는 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v

    @model_validator(mode="after")
    def _distractors(self):
        _require_all_distractors(self.answer_no, self.wrong_reasons)
        return self


# ---------------------------------------------------------------------------
# 내용 일치 (한글 선지, 지문은 원본 그대로) — 서술형 앞
# ---------------------------------------------------------------------------
class GrammarCountOut(BaseModel):
    """어법상 틀린 것의 '개수'를 묻는 유형(수능 29번 계열의 내신 변형).

    밑줄 6개(①~⑥) 중 **정확히 4개**가 틀렸고, 선지는 ①1개~⑥6개다.
    어느 것이 틀렸는지 고르는 대신 몇 개가 틀렸는지 세게 한다 — 밑줄 여섯을 하나도
    빠짐없이 판정해야 하고, 하나만 잘못 봐도 개수가 어긋난다.
    """

    rewritten: list[str]           # 다시 쓴 지문(원문과 문장 수 동일)
    marks: list[WordMark]          # 밑줄 정확히 6개(①~⑥)
    wrong_nos: list[int]           # 그중 어법상 틀린 밑줄 번호 — 정확히 4개
    reasons: list[GrammarReason]   # 밑줄 6개 각각이 왜 옳은지/틀린지
    reason: str = ""               # 전체 총평(한국어)

    @field_validator("marks")
    @classmethod
    def _count(cls, v: list[WordMark]) -> list[WordMark]:
        if len(v) != 6:
            raise ValueError("어법 개수 문항의 밑줄은 정확히 6개여야 합니다.")
        return v

    def check(self) -> None:
        n = len(self.marks)
        if len(set(self.wrong_nos)) != 4:
            raise ValueError(f"틀린 밑줄은 정확히 4개여야 합니다"
                             f"(현재 {len(set(self.wrong_nos))}개).")
        for a in self.wrong_nos:
            if not 1 <= a <= n:
                raise ValueError(f"틀린 밑줄 번호 {a} 가 범위를 벗어났습니다(1~{n}).")
        if len(self.reasons) != n:
            raise ValueError(f"밑줄 {n}개 각각의 근거(reasons)가 필요합니다.")


class PairOddOut(BaseModel):
    """어법·어휘 짝짓기 — '적절하지 않은 것끼리 짝지어진 것은?'

    밑줄 ⓐ~ⓔ 5개 중 **정확히 2개**만 부적절하고, 학생은 그 둘을 짝으로 고른다.
    한쪽은 어법 오류(수 일치·태·준동사 등), 다른 한쪽은 문맥상 어휘 오류(반의어 함정)로
    둘 다 넣어 두 능력을 한 문항에서 함께 확인한다. 하나만 찾아서는 답이 안 나오므로
    찍기가 통하지 않는다.

    선지(짝 5개)는 코드가 만든다 — 정답 짝이 반드시 하나만 들어가도록 보장하기 위해서다.
    """

    marks: list[WordMark]          # 밑줄 5개(ⓐ~ⓔ). 부적절한 것은 shown 이 오답형.
    grammar_no: int                # 어법상 틀린 밑줄 번호(1~5)
    vocab_no: int                  # 문맥상 낱말이 부적절한 밑줄 번호(1~5)
    reasons: list[GrammarReason]   # 밑줄 5개 각각이 왜 적절/부적절한지
    reason: str = ""               # 총평(한국어)

    @field_validator("marks")
    @classmethod
    def _five(cls, v: list[WordMark]) -> list[WordMark]:
        if len(v) != 5:
            raise ValueError("어법·어휘 짝짓기의 밑줄은 정확히 5개여야 합니다.")
        return v

    def check(self) -> None:
        for name, no in (("grammar_no", self.grammar_no), ("vocab_no", self.vocab_no)):
            if not 1 <= no <= 5:
                raise ValueError(f"{name} 는 1~5 여야 합니다(현재 {no}).")
        if self.grammar_no == self.vocab_no:
            raise ValueError("어법 오류와 어휘 오류는 서로 '다른' 밑줄이어야 합니다"
                             "(부적절한 것이 정확히 2개여야 짝이 성립합니다).")
        if len(self.reasons) != 5:
            raise ValueError("밑줄 5개 각각의 근거(reasons)가 필요합니다.")


class ContentOut(BaseModel):
    choices: list[str]             # 한글 선지 5개
    answer_no: int                 # 글과 일치하는 정답 번호(1~5)
    reason: str                    # 정답이 글의 어느 문장과 일치하는지
    wrong_reasons: list[WrongReason]  # 각 오답이 '어느 부분에서' 틀렸는지

    @field_validator("choices")
    @classmethod
    def _five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("내용 일치 선지는 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v

    @model_validator(mode="after")
    def _distractors(self):
        _require_all_distractors(self.answer_no, self.wrong_reasons)
        return self


# ---------------------------------------------------------------------------
# ④ 어휘 — 정본에서 지정 단어만 밑줄/치환
# ---------------------------------------------------------------------------
class WordMark(BaseModel):
    sent_no: int                   # 밑줄 단어가 있는 문장 번호(1-based)
    word: str                      # 정본 문장 속 원본 단어(찾을 대상)
    shown: str                     # 문제에 보여줄 단어(유의어/반의어/원본/오답형)


class VocabOut(BaseModel):
    marks: list[WordMark]          # 밑줄 5개
    answer_no: int                 # 문맥상 부적절한 밑줄 번호(1~5)
    reason: str
    override_no: int = 0           # (방식2) 부정어를 넣을 문장 번호(1-based, 0=없음)
    override_text: str = ""        # (방식2) 그 문장의 교체 텍스트

    @field_validator("marks")
    @classmethod
    def _five(cls, v: list[WordMark]) -> list[WordMark]:
        if len(v) != 5:
            raise ValueError("어휘 밑줄은 정확히 5개여야 합니다.")
        return v

    @field_validator("answer_no")
    @classmethod
    def _range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("answer_no 는 1~5 여야 합니다.")
        return v


# ---------------------------------------------------------------------------
# ⑤ 어법 (복수정답, 최대 8밑줄)
# ---------------------------------------------------------------------------
class GrammarReason(BaseModel):
    no: int
    text: str


class GrammarOut(BaseModel):
    # 어법 문항은 '정본 그대로'가 아니라 다시 쓴 지문 위에 낸다 — 지문을 통째로 외운
    # 학생이 '달라진 낱말 찾기'로 풀어 버리는 것을 막는다.
    rewritten: list[str]           # 내용은 같고 표현만 바꾼 지문(원문과 문장 수 동일)
    marks: list[WordMark]          # 밑줄 2~8개(틀린 것은 shown 이 오답형)
    answer_nos: list[int]          # 틀린 밑줄 번호들(복수)
    reasons: list[GrammarReason]

    @field_validator("marks")
    @classmethod
    def _count(cls, v: list[WordMark]) -> list[WordMark]:
        if not (2 <= len(v) <= 8):
            raise ValueError("어법 밑줄은 2~8개여야 합니다.")
        return v

    def check(self) -> None:
        n = len(self.marks)
        if not self.answer_nos:
            raise ValueError("복수 정답이 최소 1개는 있어야 합니다.")
        for a in self.answer_nos:
            if not (1 <= a <= n):
                raise ValueError(f"정답 번호 {a} 가 범위를 벗어났습니다(1~{n}).")


# ---------------------------------------------------------------------------
# ⑥ 서술형 (세 소문항, 지문은 원본 그대로)
# ---------------------------------------------------------------------------
class ShortOut(BaseModel):
    q1_prompt: str
    q1_answer: str                 # 한글 모범 답안
    q2_prompt: str
    q2_tokens: list[str]           # 낱개 단어(구 묶음 금지)
    q2_cues: list[str]             # 변형할 제시어(동사 원형 등)
    q2_answer: str
    q3_prompt: str
    q3_before: str
    q3_mid: str
    q3_after: str
    q3_cue_a: str
    q3_cue_b: str
    q3_ans_a: str
    q3_ans_b: str
    q3_reason: str

    @field_validator("q2_tokens")
    @classmethod
    def _tokens(cls, v: list[str]) -> list[str]:
        v = [t.strip() for t in v if t and t.strip()]
        if len(v) < 4:
            raise ValueError("영작 <보기> 낱개 단어는 최소 4개 이상이어야 합니다.")
        for t in v:
            if " " in t:
                raise ValueError(f"낱개 단어여야 합니다(구 묶음 금지): '{t}'")
        return v

    @field_validator("q2_cues")
    @classmethod
    def _cues(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("변형할 제시어(cue)가 최소 1개는 있어야 합니다.")
        return v
