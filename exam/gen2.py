"""추론형 유형 LLM 생성 — 빈칸추론(F) · 함의추론(B) · 요약문 빈칸(E) · 어순 배열(D).

pipeline 의 산문형 유형과 원칙이 같다: 분석 1회(analyzer, 정본 문장은 원문 그대로)
→ 유형별 생성 → build2 조립. 어떤 유형을 어떤 순서로 낼지는 merged.py 가 정한다.
"""
from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from . import answer_spread, build2, review
from .generators.base import context
from .llm import SYSTEM
from .schemas import WrongReason, _require_all_distractors
from .set2 import B, D, E, F


# ---------------------------------------------------------------------------
# 구조화 출력 스키마
# ---------------------------------------------------------------------------
class BOut(BaseModel):
    phrase: str
    choices: list[str]
    answer_no: int
    reason: str
    wrong_reasons: list[WrongReason]

    @field_validator("choices")
    @classmethod
    def _five(cls, v):
        if len(v) != 5:
            raise ValueError("B유형 선지는 5개여야 합니다.")
        return v

    @model_validator(mode="after")
    def _distractors(self):
        _require_all_distractors(self.answer_no, self.wrong_reasons)
        return self


class DOut(BaseModel):
    tokens: list[str]
    cues: list[str]
    answer: str
    reason: str = ""


class Pair(BaseModel):
    a: str
    b: str
    a_ok: bool           # (A) 자리가 논지에 맞는가
    b_ok: bool           # (B) 자리가 논지에 맞는가


class EOut(BaseModel):
    before: str
    mid: str
    after: str
    pairs: list[Pair]
    answer_no: int
    reason: str

    @field_validator("pairs")
    @classmethod
    def _five(cls, v):
        if len(v) != 5:
            raise ValueError("E유형 선지쌍은 5개여야 합니다.")
        return v

    @model_validator(mode="after")
    def _one_correct(self):
        # (A)(B) 둘 다 맞는 쌍이 '정확히 하나'여야 하고 그게 정답이어야 한다
        both = [i + 1 for i, p in enumerate(self.pairs) if p.a_ok and p.b_ok]
        if both != [self.answer_no]:
            raise ValueError(f"(A)(B) 둘 다 맞는 선지는 정답 1개뿐이어야 합니다: "
                             f"둘다맞음 {both}, answer_no {self.answer_no}")
        return self


class FOut(BaseModel):
    blank_phrase: str                     # 지문에 실제로 있는 '핵심/주제' 어구(이걸 빈칸으로)
    choices: list[str]                    # 5개(영어). 정답은 blank_phrase 의 유의어 패러프레이즈
    answer_no: int
    reason: str
    wrong_reasons: list[WrongReason]

    @field_validator("choices")
    @classmethod
    def _five(cls, v):
        if len(v) != 5:
            raise ValueError("F유형 선지는 5개여야 합니다.")
        return v

    @model_validator(mode="after")
    def _distractors(self):
        _require_all_distractors(self.answer_no, self.wrong_reasons)
        return self


# ---------------------------------------------------------------------------
# 유형별 생성기
# ---------------------------------------------------------------------------
def _gen_B(client, analysis, body, max_retries=1, answer_pos=None, variant_hint=""):
    p = ("아래 정본으로 '함의추론(B)'을 만드세요. 비유·맥락의존 어구 하나를 phrase 로 고르되(지문에 "
         "그대로 있는, 어휘 난도 있는 표현으로 '축자 함정'을 깐다), 그 '문맥적' 의미를 묻습니다.\n"
         "- 정답: 밑줄 표현을 '지문 맥락에서 풀어 쓴 재진술'(사전적·축자 뜻 아님). 밑줄의 긍/부정(±) "
         "방향과 글의 주제를 '동시에' 만족해야 정답.\n"
         "- 오답 4(각기 다른 축): ⓐ 축자 해석(곧이곧대로) ⓑ 방향 반전(±반대) ⓒ 과대 일반화 "
         "ⓓ 부분만 ⓔ 무관. 하나는 정답과 비슷하나 한 끗 어긋난 '매력적 오답'.\n"
         "choices 5개는 '영어'. reason·wrong_reasons(오답별 어느 축인지) 는 한국어.\n\n{ctx}")
    if variant_hint:
        p = variant_hint + "\n" + p
    out: BOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), BOut,
                                  max_tokens=2500, max_retries=max_retries, cache_prefix=context(analysis))
    wrong = {w.no: w.text for w in out.wrong_reasons}
    # 따옴표·대시 차이로 밑줄이 안 그어지지 않게, 지문 실제 표기로 교정(못 찾으면 원문 유지)
    _, exact = build2.locate_phrase(out.phrase, analysis.sentences)
    phrase = exact or out.phrase
    choices, answer_no = out.choices, out.answer_no
    old_no = answer_no
    if answer_pos:   # 정답 위치 분산(선지 재배열 — 정오 불변)
        choices, answer_no, wrong = answer_spread.place_answer(
            choices, answer_no, answer_pos, wrong)
    reason = answer_spread.relabel_answer_ref(out.reason, old_no, answer_no)
    q, a = build2.make_B(analysis.sentences, phrase, choices, answer_no,
                         reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)


def _gen_D(client, analysis, body, max_retries=1, answer_pos=None):
    p = ("아래 정본으로 '어순 배열(D)'을 만드세요. 아래 [문장] 목록에서 문장 하나를 골라, answer 는 "
         "그 문장을 '글자 그대로'(단어·축약형·구두점 포함, 요약·수정·의역 금지) 복사한 것이어야 "
         "합니다(원래 배열이 정답). 그 문장을 낱개 단어로 뒤섞어 tokens 로 줍니다(구 묶음 금지). "
         "어형변화가 필요한 동사는 원형으로 두고 cues 에 넣습니다. reason 한국어.\n\n{ctx}")
    out: DOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), DOut,
                                  max_tokens=1500, max_retries=max_retries, cache_prefix=context(analysis))
    flags: list[str] = []
    q, a = build2.make_D(analysis.sentences, out.tokens, out.cues, out.answer,
                         out.reason, flags=flags)
    return q, a, flags


def _gen_E(client, analysis, body, max_retries=1, answer_pos=None):
    p = ("아래 정본으로 '요약문 빈칸(E)'을 만드세요. 지문을 한 문장 요약하되 핵심어 2곳을 (A)(B)로 "
         "비우고 before/mid/after 로 나눕니다. (A)는 before와 mid 사이, (B)는 mid와 after 사이에 "
         "자동으로 들어갑니다. before/mid/after 조각 '안에는' '(A)'·'(B)' 라벨을 절대 쓰지 마세요"
         "(라벨은 조판기가 붙입니다). pairs 5개는 (a,b) 단어쌍 선지입니다.\n"
         "- 정답 쌍: (A)(B) 둘 다 논지에 맞되, 지문 단어를 '그대로 쓰지 말고 유의어(패러프레이즈)'로.\n"
         "- 오답 4: (A)만 맞음 / (B)만 맞음 / 둘 다 어긋남 을 고루 섞고, 그중 일부에는 '지문에 실제 "
         "나온 단어'를 넣어 맞아 보이게(함정) 만듭니다.\n"
         "- 각 쌍에 a_ok/b_ok(그 자리가 논지에 맞는지 true/false)를 표시하세요. (A)(B) 둘 다 true인 "
         "쌍은 '정답 하나뿐'이어야 하고, 그 번호가 answer_no 입니다(우연히 둘 다 맞는 오답이 없게).\n"
         "answer_no·reason 은 한국어.\n\n{ctx}")
    out: EOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), EOut,
                                  max_tokens=2000, max_retries=max_retries, cache_prefix=context(analysis))
    pairs = [(x.a, x.b) for x in out.pairs]
    answer_no = out.answer_no
    old_no = answer_no
    if answer_pos:   # 정답 위치 분산(단어쌍 선지 재배열 — 정오 불변)
        pairs, answer_no, _ = answer_spread.place_answer(pairs, answer_no, answer_pos)
    reason = answer_spread.relabel_answer_ref(out.reason, old_no, answer_no)
    q, a = build2.make_E(analysis.sentences, out.before, out.mid, out.after, pairs,
                         answer_no, reason)
    return q, a, []


def _gen_F(client, analysis, body, max_retries=1, answer_pos=None):
    p = ("아래 정본으로 '빈칸추론(F)'을 만드세요. 지문 전체를 보여주되, 글의 '가장 핵심(주제)'을 담은 "
         "어구 하나를 blank_phrase 로 지정합니다(지문에 그대로 있는 표현). 그 어구가 빈칸이 됩니다.\n"
         "choices 5개는 영어. 정답은 blank_phrase 와 '의미가 동일한 정확한 유의어 패러프레이즈'여야 "
         "한다(원문 어구를 그대로 쓰지 말 것, 뜻이 어긋나도 안 됨). 오답 4개는 소재는 쓰되 각각 "
         "'확실히' 모순·무관이어서 정답으로 읽힐 여지가 없어야 한다. answer_no·reason·wrong_reasons 는 "
         "한국어.\n\n{ctx}")
    out: FOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), FOut,
                                  max_tokens=2500, max_retries=max_retries, cache_prefix=context(analysis))
    # blank_phrase 가 있는 문장을 찾는다(따옴표·대시 차이 무시, 지문 실제 표기로 교정)
    idx, phrase = build2.locate_phrase(out.blank_phrase, analysis.sentences)
    if idx is None:
        raise ValueError(f"빈칸 어구를 지문에서 찾지 못했습니다: '{out.blank_phrase.strip()}'")
    wrong = {w.no: w.text for w in out.wrong_reasons}
    choices, answer_no = out.choices, out.answer_no
    old_no = answer_no
    if answer_pos:   # 정답 위치 분산(선지 재배열 — 정오 불변)
        choices, answer_no, wrong = answer_spread.place_answer(
            choices, answer_no, answer_pos, wrong)
    reason = answer_spread.relabel_answer_ref(out.reason, old_no, answer_no)
    q, a = build2.make_F(analysis.sentences, idx, phrase, choices,
                         answer_no, reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)


_GENERATORS2 = {B: _gen_B, D: _gen_D, E: _gen_E, F: _gen_F}


# ---------------------------------------------------------------------------
# 오케스트레이션
# ---------------------------------------------------------------------------
def _gen_one_type2(gen, client, analysis, body, t, max_retries, logger, answer_pos=None):
    """2회 한 유형 생성. 구조 검증 실패 시 재시도 + 고위험 유형은 LLM 자기검증.
    (q, a, flags) 반환 — 자기검증 2회 실패면 문항은 유지하고 '확인 권장' 사유를 단다."""
    from . import verify as _verify
    last_err = None
    for attempt in range(2):
        try:
            q, a, fl = gen(client, analysis, body, max_retries=max_retries, answer_pos=answer_pos)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if logger:
                logger.warning("[%s] 생성 실패(시도 %d): %s", t, attempt + 1, e)
            continue
        ok, reason = _verify.verify(client, t, q, a, max_retries=max_retries)
        if not ok:
            if attempt == 0:
                if logger:
                    logger.info("[%s] 자기검증 실패 → 재생성: %s", t, reason)
                continue
            fl = list(fl) + [f"자동검증: {reason or '정답 유일성·정오답 재확인'}"]
        return q, a, fl
    if logger:
        logger.error("[%s] 최종 생성 실패 — 이 문항은 제외합니다: %s", t, last_err)
    return None    # 지문 전체를 버리지 않고 이 유형만 건너뛴다


def make_task2(t, client, analysis, body, max_retries=1, logger=None,
               passage_index=0, slots=None):
    """2회 계열(A~G) 유형 t 하나를 만드는 '무인자 함수'.

    통합본(merged)도 같은 생성기를 그대로 쓰므로 여기서 한 번만 정의한다.
    slots 는 정답 위치 분산용 슬롯표(세트마다 다르다). 생략하면 2회용.
    """
    gen = _GENERATORS2[t]
    slots = answer_spread.SLOTS2 if slots is None else slots
    apos = (answer_spread.pick(passage_index, slots[t], len(slots),
                               seed=answer_spread.seed_of(analysis.title))
            if t in slots else None)
    return lambda: _gen_one_type2(gen, client, analysis, body, t, max_retries, logger, apos)
