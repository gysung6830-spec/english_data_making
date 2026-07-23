"""변형문제 2회(A~G) LLM 생성 + 오케스트레이션.

1회와 같은 원칙: 분석 1회(analyzer, 정본 문장은 원문 그대로) → 유형별 생성 → build2 조립.
C(어법)는 1회 생성기를 그대로 재사용한다.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

from . import analyzer, build2, renderer, validator
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
def _gen_A(client, analysis, body, max_retries=1):
    p = ("아래 정본으로 '어법·어휘 짝짓기(A)'를 만드세요. 밑줄 5개(ⓐ~ⓔ, marks: sent_no·word·shown).\n"
         "그중 정확히 2개만 오답: 1개는 어법 오류(shown 을 틀린 형태로), 1개는 반의어(shown 을 문맥상 "
         "어색한 반대말로). 나머지 3개는 shown=원본. choices 5개는 두 밑줄의 짝(예 'ⓐ, ⓒ'), "
         "answer_no 는 실제 오답 두 개의 짝. reason 은 한국어.\n\n{ctx}")
    out: AOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), AOut,
                                  max_tokens=2500, max_retries=max_retries)
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    return build2.make_A(analysis.sentences, marks, out.answer_no, out.reason, out.choices)


def _gen_B(client, analysis, body, max_retries=1):
    p = ("아래 정본으로 '함의추론(B)'을 만드세요. 비유·맥락의존 어구 하나를 phrase 로 고르고(지문에 "
         "그대로 있는 표현), 그 함축 의미를 묻습니다. choices 5개는 '영어'. 정답=글 전체 논지를 "
         "반영한 재진술, 오답 4=축자적 오독 또는 논지 위배. reason·wrong_reasons 는 한국어.\n\n{ctx}")
    out: BOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), BOut,
                                  max_tokens=2500, max_retries=max_retries)
    wrong = {w.no: w.text for w in out.wrong_reasons}
    return build2.make_B(analysis.sentences, out.phrase, out.choices, out.answer_no,
                         out.reason, wrong)


def _gen_C(client, analysis, body, max_retries=1):
    # 어법(복수정답)은 1회 생성기를 그대로 재사용
    return _grammar_gen.generate(client, analysis, body, max_retries=max_retries)


def _gen_D(client, analysis, body, max_retries=1):
    p = ("아래 정본으로 '어순 배열(D)'을 만드세요. answer 는 반드시 '지문에 실제로 있는 문장 그대로'"
         "여야 하며(원래 배열이 정답), 그 문장을 낱개 단어로 뒤섞어 tokens 로 줍니다(구 묶음 금지). "
         "어형변화가 필요한 동사는 원형으로 두고 cues 에 넣습니다. reason 한국어.\n\n{ctx}")
    out: DOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), DOut,
                                  max_tokens=1500, max_retries=max_retries)
    return build2.make_D(analysis.sentences, out.tokens, out.cues, out.answer, out.reason)


def _gen_E(client, analysis, body, max_retries=1):
    p = ("아래 정본으로 '요약문 빈칸(E)'을 만드세요. 지문을 한 문장 요약하되 핵심어 2곳을 (A)(B)로 "
         "비우고 before/mid/after 로 나눕니다. pairs 5개는 (a,b) 단어쌍 선지입니다.\n"
         "- 정답 쌍: (A)(B) 둘 다 논지에 맞되, 지문 단어를 '그대로 쓰지 말고 유의어(패러프레이즈)'로.\n"
         "- 오답 4: (A)만 맞음 / (B)만 맞음 / 둘 다 어긋남 을 고루 섞고, 그중 일부에는 '지문에 실제 "
         "나온 단어'를 넣어 맞아 보이게(함정) 만듭니다.\n"
         "- 각 쌍에 a_ok/b_ok(그 자리가 논지에 맞는지 true/false)를 표시하세요. (A)(B) 둘 다 true인 "
         "쌍은 '정답 하나뿐'이어야 하고, 그 번호가 answer_no 입니다(우연히 둘 다 맞는 오답이 없게).\n"
         "answer_no·reason 은 한국어.\n\n{ctx}")
    out: EOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), EOut,
                                  max_tokens=2000, max_retries=max_retries)
    pairs = [(x.a, x.b) for x in out.pairs]
    return build2.make_E(analysis.sentences, out.before, out.mid, out.after, pairs,
                         out.answer_no, out.reason)


def _gen_F(client, analysis, body, max_retries=1):
    p = ("아래 정본으로 '빈칸추론(F)'을 만드세요. 지문 전체를 보여주되, 글의 '가장 핵심(주제)'을 담은 "
         "어구 하나를 blank_phrase 로 지정합니다(지문에 그대로 있는 표현). 그 어구가 빈칸이 됩니다.\n"
         "choices 5개는 영어. 정답은 blank_phrase 와 '의미가 동일한 정확한 유의어 패러프레이즈'여야 "
         "한다(원문 어구를 그대로 쓰지 말 것, 뜻이 어긋나도 안 됨). 오답 4개는 소재는 쓰되 각각 "
         "'확실히' 모순·무관이어서 정답으로 읽힐 여지가 없어야 한다. answer_no·reason·wrong_reasons 는 "
         "한국어.\n\n{ctx}")
    out: FOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), FOut,
                                  max_tokens=2500, max_retries=max_retries)
    # blank_phrase 가 있는 문장을 찾는다
    phrase = out.blank_phrase.strip()
    idx = next((i for i, s in enumerate(analysis.sentences)
                if phrase.lower() in s.lower()), None)
    if idx is None:
        raise ValueError(f"빈칸 어구를 지문에서 찾지 못했습니다: '{phrase}'")
    wrong = {w.no: w.text for w in out.wrong_reasons}
    return build2.make_F(analysis.sentences, idx, phrase, out.choices,
                         out.answer_no, out.reason, wrong)


def _gen_G(client, analysis, body, max_retries=1):
    def _extra(o: GOut):
        o.check()
    p = ("아래 정본으로 '내용일치 개수(G)'를 만드세요. 지문 문장을 패러프레이즈한 한국어 진술 5개를 "
         "statements 로, 각 진술의 일치 여부를 matches(bool 5개)로 줍니다. 불일치는 주체·정도·인과를 "
         "뒤집거나 없는 내용. per_stmt 는 각 진술이 왜 일치/불일치인지(한국어). reason 한국어.\n\n{ctx}")
    out: GOut = client.structured(SYSTEM, p.format(ctx=context(analysis)), GOut,
                                  max_tokens=2500, max_retries=max_retries, extra_validate=_extra)
    per = {i + 1: t for i, t in enumerate(out.per_stmt)} if out.per_stmt else {}
    return build2.make_G(analysis.sentences, out.statements, sum(out.matches), out.reason, per)


_GENERATORS2 = {A: _gen_A, B: _gen_B, C: _gen_C, D: _gen_D, E: _gen_E, F: _gen_F, G: _gen_G}


# ---------------------------------------------------------------------------
# 오케스트레이션
# ---------------------------------------------------------------------------
def _gen_one_type2(gen, client, analysis, body, t, max_retries, logger):
    """2회 한 유형 생성(실패 시 한 번 더). (q, a) 반환."""
    last_err = None
    for attempt in range(2):
        try:
            return gen(client, analysis, body, max_retries=max_retries)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if logger:
                logger.warning("[2회 %s] 생성 실패(시도 %d): %s", t, attempt + 1, e)
    raise RuntimeError(f"2회 '{t}' 유형 생성 실패: {last_err}")


def build_passage2(client, body, max_retries=1, logger=None, analysis=None) -> Passage:
    """2회 지문 1개 -> A~G. 유형은 병렬 생성, analysis 를 주면 분석을 건너뛴다."""
    if analysis is None:
        analysis = analyzer.analyze(client, body, max_retries=max_retries)
    passage = Passage(title=analysis.title)

    def _task(t):
        gen = _GENERATORS2[t]
        return lambda: _gen_one_type2(gen, client, analysis, body, t, max_retries, logger)

    results = run_parallel([(t, _task(t)) for t in TYPE_ORDER2])
    for t in TYPE_ORDER2:
        q, a = results[t]
        passage.set_qa(t, q, a)
    validator.check_passage(passage, TYPE_ORDER2)
    return passage


def build_exam2(client, bodies, out_path, header_note="", max_retries=1, logger=None,
                analyses=None) -> Path:
    from .pipeline import analyze_bodies
    if analyses is None:
        analyses = analyze_bodies(client, bodies, max_retries=max_retries, logger=logger)
    passages = []
    for i, (body, analysis) in enumerate(zip(bodies, analyses), 1):
        if logger:
            logger.info("[2회 %d/%d] 지문 생성 중 …", i, len(bodies))
        passages.append(build_passage2(client, body, max_retries=max_retries,
                                       logger=logger, analysis=analysis))
    validator.validate_passages(passages, TYPE_ORDER2)
    validator.validate_numbering(passages, 1, TYPE_ORDER2)
    return renderer.render_pdf(passages, out_path, header_note=header_note,
                               type_order=TYPE_ORDER2, prompts=TYPE_PROMPTS2, labels=TYPE_LABELS2)
