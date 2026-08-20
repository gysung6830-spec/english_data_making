"""변형문제 2회(A~G) LLM 생성 + 오케스트레이션.

1회와 같은 원칙: 분석 1회(analyzer, 정본 문장은 원문 그대로) → 유형별 생성 → build2 조립.
C(어법)는 1회 생성기를 그대로 재사용한다.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

from . import analyzer, answer_spread, build2, difficulty, renderer, review, validator
from ._concurrent import run_parallel
from .generators import grammar as _grammar_gen
from .generators.base import context
from .llm import SYSTEM, ClaudeClient
from .schemas import Analysis, WordMark, WrongReason, _require_all_distractors
from .set2 import (
    A, B, C, D, E, F, G, TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2,
)
from .types import Passage


# ---------------------------------------------------------------------------
# 구조화 출력 스키마
# ---------------------------------------------------------------------------
class AOut(BaseModel):
    marks: list[WordMark]                 # 5개(ⓐ~ⓔ)
    answer_no: int
    reason: str
    choices: list[str]                    # 5개 짝 문자열(예 "ⓐ, ⓒ")

    @field_validator("marks", "choices")
    @classmethod
    def _five(cls, v):
        if len(v) != 5:
            raise ValueError("A유형은 밑줄·선지가 각각 5개여야 합니다.")
        return v


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


class GOut(BaseModel):
    statements: list[str]
    matches: list[bool]
    reason: str
    per_stmt: list[str] = Field(default_factory=list)

    def check(self):
        if len(self.statements) != len(self.matches):
            raise ValueError("statements 와 matches 개수가 다릅니다.")
        if len(self.statements) != 5:
            raise ValueError("G유형 진술은 정확히 5개여야 합니다.")
        if not (1 <= sum(self.matches) <= 5):
            raise ValueError("일치 개수는 1~5개여야 합니다(0개 불가).")


# ---------------------------------------------------------------------------
# 유형별 생성기
# ---------------------------------------------------------------------------
def _gen_A(client, analysis, body, max_retries=1, answer_pos=None):
    p = ("아래 정본으로 '어법·어휘 짝짓기(A)'를 만드세요. 밑줄 5개(ⓐ~ⓔ, marks: sent_no·word·shown).\n"
         "그중 정확히 2개만 오답: 1개는 어법 오류(shown 을 틀린 형태로), 1개는 반의어(shown 을 문맥상 "
         "어색한 반대말로). 나머지 3개는 shown=원본. choices 5개는 두 밑줄의 짝(예 'ⓐ, ⓒ'), "
         "answer_no 는 실제 오답 두 개의 짝. reason 은 한국어.\n\n{ctx}")
    out: AOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), AOut,
                                  max_tokens=2500, max_retries=max_retries, cache_prefix=context(analysis))
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    choices, answer_no = out.choices, out.answer_no
    old_no = answer_no
    if answer_pos:   # 정답 위치 분산(짝 선지 재배열 — 정오 불변)
        choices, answer_no, _ = answer_spread.place_answer(choices, answer_no, answer_pos)
    reason = answer_spread.relabel_answer_ref(out.reason, old_no, answer_no)
    flags: list[str] = []
    q, a = build2.make_A(analysis.sentences, marks, answer_no, reason, choices, flags=flags)
    return q, a, flags


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


def _gen_C(client, analysis, body, max_retries=1, answer_pos=None):
    # 어법(복수정답)은 1회 생성기를 그대로 재사용(정답 위치가 읽는 순서로 정해져 분산 대상 아님)
    return _grammar_gen.generate(client, analysis, body, max_retries=max_retries)


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


def _gen_G(client, analysis, body, max_retries=1, answer_pos=None):
    def _extra(o: GOut):
        o.check()
    p = ("아래 정본으로 '내용일치 개수(G)'를 만드세요. 지문 문장을 패러프레이즈한 한국어 진술 5개를 "
         "statements 로, 각 진술의 일치 여부를 matches(bool 5개)로 줍니다. 불일치는 주체·정도·인과를 "
         "뒤집거나 없는 내용. per_stmt 는 각 진술이 왜 일치/불일치인지(한국어). reason 한국어.\n\n{ctx}")
    out: GOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), GOut,
                                  max_tokens=2500, max_retries=max_retries, extra_validate=_extra,
                                  cache_prefix=context(analysis))
    per = {i + 1: t for i, t in enumerate(out.per_stmt)} if out.per_stmt else {}
    q, a = build2.make_G(analysis.sentences, out.statements, sum(out.matches), out.reason, per)
    return q, a, []


_GENERATORS2 = {A: _gen_A, B: _gen_B, C: _gen_C, D: _gen_D, E: _gen_E, F: _gen_F, G: _gen_G}


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
                logger.warning("[2회 %s] 생성 실패(시도 %d): %s", t, attempt + 1, e)
            continue
        ok, reason = _verify.verify(client, t, q, a, max_retries=max_retries)
        if not ok:
            if attempt == 0:
                if logger:
                    logger.info("[2회 %s] 자기검증 실패 → 재생성: %s", t, reason)
                continue
            fl = list(fl) + [f"자동검증: {reason or '정답 유일성·정오답 재확인'}"]
        return q, a, fl
    if logger:
        logger.error("[2회 %s] 최종 생성 실패 — 이 문항은 제외합니다: %s", t, last_err)
    return None    # 지문 전체를 버리지 않고 이 유형만 건너뛴다


def build_passage2(client, body, max_retries=1, logger=None, analysis=None,
                   level=None, passage_index=0) -> Passage:
    """2회 지문 1개 -> A~G. 유형은 병렬 생성, analysis 를 주면 분석을 건너뛴다.
    level(상/중/하)로 전체 난이도를 조절한다.
    passage_index 로 정답 위치를 지문마다 다르게 분산한다(정답 번호 몰림 방지)."""
    if analysis is None:
        analysis = analyzer.analyze(client, body, max_retries=max_retries)
    if level:
        analysis.difficulty_note = difficulty.clause(level)
    passage = Passage(title=analysis.title)

    def _task(t):
        gen = _GENERATORS2[t]
        apos = (answer_spread.pick(passage_index, answer_spread.SLOTS2[t],
                                   len(answer_spread.SLOTS2),
                                   seed=answer_spread.seed_of(analysis.title, level))
                if t in answer_spread.SLOTS2 else None)
        return lambda: _gen_one_type2(gen, client, analysis, body, t, max_retries,
                                      logger, apos)

    results = run_parallel([(t, _task(t)) for t in TYPE_ORDER2])
    from . import review as _rv
    for t in TYPE_ORDER2:
        res = results.get(t)
        if res is None:      # 이 유형은 최종 생성 실패 → 건너뛰고 나머지는 살린다
            continue
        q, a, fl = res
        passage.set_qa(t, q, a)
        passage.flag(t, fl)   # '확인 권장'(자동 보정·오답 근거 약함) 사유가 있으면 기록
        passage.flag(t, _rv.type_fit_flags(getattr(analysis, "passage_type", "prose"), t))
    if not passage.q:
        raise RuntimeError(f"[{passage.title}] 2회 모든 유형 생성 실패")
    return passage


def build_passages2(client, bodies, max_retries=1, logger=None, analyses=None,
                    level=None, labels=None) -> list:
    """2회 여러 지문 -> 검증된 Passage 리스트(조판 없음). 합본용.

    labels 를 주면 각 지문 라벨(원본 PDF 문항번호 등)을 조판 라벨로 쓴다.
    """
    from .pipeline import analyze_bodies
    if analyses is None:
        analyses = analyze_bodies(client, bodies, max_retries=max_retries, logger=logger)
    passages = []
    for i, (body, analysis) in enumerate(zip(bodies, analyses), 1):
        if logger:
            logger.info("[2회 %d/%d] 지문 생성 중 …", i, len(bodies))
        passage = build_passage2(client, body, max_retries=max_retries,
                                 logger=logger, analysis=analysis, level=level,
                                 passage_index=i - 1)
        if labels and i - 1 < len(labels):
            passage.source_label = labels[i - 1]
        passages.append(passage)
    validator.validate_passages(passages, TYPE_ORDER2)
    validator.validate_numbering(passages, 1, TYPE_ORDER2)
    return passages


def build_exam2(client, bodies, out_path, header_note="", max_retries=1, logger=None,
                analyses=None, level=None, sections=None, labels=None) -> Path:
    passages = build_passages2(client, bodies, max_retries=max_retries, logger=logger,
                               analyses=analyses, level=level, labels=labels)
    return renderer.render_pdf(passages, out_path, header_note=header_note,
                               type_order=TYPE_ORDER2, prompts=TYPE_PROMPTS2, labels=TYPE_LABELS2,
                               sections=sections)
