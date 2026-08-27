"""④ 어휘 생성기 (문맥상 부적절) — 정본에서 지정 단어만 변형. 세 방식 지원.

세 방식을 한 지문에서 모두 출제한다(pipeline.VOCAB_METHODS). 발문은 같지만 밑줄을
만드는 방식이 달라 서로 다른 문제가 된다:
  method="synonym"  : 밑줄 5개 중 1개=반의어(정답), 나머지=유의어로 패러프레이즈.
  method="original" : 정답 1개만 반의어, 나머지 4개는 '원문 단어 그대로' 노출.
  method="negation" : 밑줄은 원문 그대로, 정답 문장에만 부정어(no/not/neither)를 넣어
      글의 흐름과 모순되게 만든다(override_no/override_text).
"""
from __future__ import annotations

from .. import build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, VocabOut
from .base import context

SYNONYM = "synonym"
NEGATION = "negation"
ORIGINAL = "original"

_PROMPT_SYNONYM = """아래 '정본 지문'으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 반의어]
지문을 새로 쓰지 말고, 밑줄 칠 단어와 표시할 단어만 정하세요.

- marks: 밑줄 5개. 각 항목은 sent_no(문장 번호 1-based), word(그 문장의 원본 단어),
  shown(문제에 보여줄 단어). '형용사·부사·동사' 위주로 고르세요.
- 정확히 1개(answer_no)는 shown 을 '반의어'로 하여 문맥상 어색하게 만듭니다 → 정답.
- 나머지 4개는 shown 을 원본 단어의 '유의어'로 바꿔 둡니다(원문 단어 그대로 노출 금지).
- [확실성] 정답 1개만 확실히 어색해야 한다. 유의어로 바꾼 나머지 4개는 바꾼 뒤에도 문맥이
  '완전히 자연스러워야' 하며 조금이라도 어색하면 안 된다(그러면 정답이 2개가 됨).
- reason: 정답이 왜 문맥에 어긋나는지, 나머지는 왜 적절한지 한국어로 설명.
- override_no 는 0, override_text 는 빈 문자열로 두세요.

{ctx}
"""

_PROMPT_ORIGINAL = """아래 '정본 지문'으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 원문 단어]
지문을 새로 쓰지 말고, 밑줄 칠 단어와 표시할 단어만 정하세요.

- marks: 밑줄 5개. 각 항목은 sent_no(문장 번호 1-based), word(그 문장의 원본 단어),
  shown(문제에 보여줄 단어). '형용사·부사·동사' 위주로 고르세요.
- 정확히 1개(answer_no)는 shown 을 '반의어'로 하여 문맥상 어색하게 만듭니다 → 정답.
- 나머지 4개는 shown 을 'word 와 똑같이'(원문 단어 그대로) 둡니다. 유의어로 바꾸지 마세요.
- [확실성] 정답 1개만 확실히 어색해야 하고, 나머지 4개는 원문 그대로라 당연히 자연스럽습니다.
- reason: 정답이 왜 문맥에 어긋나는지 한국어로 설명.
- override_no 는 0, override_text 는 빈 문자열로 두세요.

{ctx}
"""

_PROMPT_NEGATION = """아래 '정본 지문'으로 '어휘(문맥상 부적절)' 문제를 만드세요. [방식: 부정어 삽입]
지문을 새로 쓰지 말고, 밑줄과 '정답 문장의 부정어 삽입'만 정하세요.

- override_no: 부정어를 넣을 문장 번호(1-based).
  override_text: 그 문장에 부정어(not/no/never/neither/hardly 등)를 자연스럽게 넣어 글 전체
  흐름과 '모순'되게 만든 문장.
- marks: 밑줄 5개. sent_no·word·shown. 형용사·부사·동사 위주. shown 은 word 와 '똑같이'.
- answer_no: 정답 밑줄 번호. 그 밑줄은 override_no 문장에 있어야 합니다.

[가장 중요 — 정답 밑줄은 '부정어를 품은 어구'여야 합니다]
  밑줄을 원문 낱말에만 그으면 다섯 개가 모두 문맥상 적절해지고, 부적절한 것은 밑줄
  '바깥'의 부정어가 됩니다. 그러면 '밑줄 친 부분 중 적절하지 않은 것'에 정답이 없습니다.
  · 정답 밑줄의 word 와 shown 을 둘 다 '부정어 + 원문 낱말'로 잡으세요.
      나쁨: 문장 'they would never delete the content' + 정답 밑줄 word='perceived'
      좋음: 문장 'they would never delete the content' + 정답 밑줄 word='never delete',
            shown='never delete'
  · 그 어구는 override_text 안에 '그대로' 있어야 합니다(철자·띄어쓰기 포함).
  · 나머지 밑줄 4개는 다른 문장에서 원문 낱말 그대로 고르세요.

- reason: 그 부정 표현이 글의 흐름과 어떻게 모순되는지 한국어로 설명. 'override'·'교체
  문장' 같은 작업 용어는 쓰지 말고, 학생이 읽을 말('이 자리에 never 가 들어가면 …')로
  쓰세요.

{ctx}
"""


_PROMPTS = {SYNONYM: _PROMPT_SYNONYM, NEGATION: _PROMPT_NEGATION, ORIGINAL: _PROMPT_ORIGINAL}


def _mark_words(marks) -> set[str]:
    """이 문항이 '밑줄로 쓴 낱말' 전체 — 원본 낱말과 표시 낱말을 모두 담는다.

    원본만 담으면 구멍이 난다. 짝짓기가 rational 을 emotional 로 바꿔 보여 주면
    'emotional' 은 어디에도 기록되지 않고, 다음 어휘 문항이 그 낱말에 다시 밑줄을
    긋는다(실제 출력물: 7번 ⓒ emotional 과 10번 ① emotional).
    """
    out: set[str] = set()
    for m in marks or []:
        for s in (getattr(m, "word", ""), getattr(m, "shown", "")):
            s = (s or "").strip().lower()
            if s:
                out.add(s)
                out.update(w for w in s.split() if len(w) > 2)
    return out


def _avoid_clause(taken: set[str]) -> str:
    """이미 다른 어휘 문제가 밑줄로 쓴 낱말을 피하라는 지시문."""
    if not taken:
        return ""
    words = ", ".join(sorted(taken))
    return ("\n[겹침 금지] 같은 지문으로 어휘 문제를 여러 개 만드는 중입니다. 아래 낱말은 "
            "다른 문제에서 이미 밑줄로 썼으니 이번 문제에서는 '하나도 쓰지 마세요'. 다른 "
            f"낱말을 고르세요(품사가 달라도 됩니다).\n피할 낱말: {words}\n")


def _sent_clause(taken: set[int]) -> str:
    """이미 다른 어휘 문제가 '정답 자리'로 쓴 문장을 피하라는 지시문(권고).

    셋이 같은 문장을 정답으로 삼으면 학생이 같은 자리를 세 번 읽는다(실제 출력물:
    24·25·26번의 정답이 모두 여덟 번째 문장에 있었다). 다만 짧은 지문에서는 피할
    자리가 없을 수 있으므로 '권고'로만 두고, 어기더라도 문항을 버리지 않는다.
    """
    if not taken:
        return ""
    nos = ", ".join(f"{n}번" for n in sorted(taken))
    return ("\n[정답 자리 분산] 같은 지문의 다른 어휘 문제가 이미 아래 문장을 '정답'으로 "
            f"썼습니다. 가급적 다른 문장에서 정답을 고르세요.\n이미 쓴 문장: {nos}\n")


def _restore_original_marks(out: VocabOut, method: str) -> list[int]:
    """원문단어형·부정어형에서 '정답이 아닌 밑줄'을 원문 낱말로 되돌린다.

    두 방식은 정답 하나만 손대고 나머지 밑줄은 원문 그대로 두는 것이 설계다. 원문
    그대로면 필자가 쓴 말이므로 어색할 수가 없고, 그래서 정답이 둘이 될 수 없다.
    바로 여기에 이 두 유형의 안전성이 통째로 걸려 있다.

    그런데 지금까지는 프롬프트로 시키기만 하고 코드가 확인하지 않았다. 모델이 한
    낱말이라도 유의어로 바꿔 놓으면 그 자리가 어색해질 수 있고, 그러면 정답이 둘이 된다.

    되돌리는 것이 거부보다 낫다 — 산출물이 곧바로 판매되기 때문이다.
      · 거부하면 재시도를 한 번 쓰고, 재시도가 소진되면 그 문항이 통째로 빠진다.
        빠진 문항은 검토 메모가 아니라 '없는 문항'으로 팔려 나간다.
      · 되돌리는 것은 추측이 아니다. 바른 낱말(word)이 같은 항목에 들어 있으므로
        프롬프트가 원래 시킨 상태를 그대로 복원할 뿐이다. 호출도 재시도도 쓰지 않는다.

    유의어형(SYNONYM)은 나머지 넷을 '일부러' 유의어로 바꾸는 방식이라 손대지 않는다.
    그쪽 위험은 코드로 없앨 수 없어 자기검증에 맡긴다.
    """
    if method not in (ORIGINAL, NEGATION):
        return []
    fixed: list[int] = []
    for i, m in enumerate(out.marks, 1):
        if i == out.answer_no:
            continue
        if m.shown.strip().lower() != m.word.strip().lower():
            m.shown = m.word
            fixed.append(i)
    return fixed


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, method: str = SYNONYM,
             avoid: set[str] | None = None,
             avoid_sents: set[int] | None = None,
             report: dict | None = None) -> tuple[str, str, list[str]]:
    """avoid: 다른 어휘 문제가 이미 밑줄로 쓴 낱말(소문자). 겹치면 재요청한다.
    avoid_sents: 다른 어휘 문제가 이미 정답 자리로 쓴 문장 번호(권고).
    report: 주면 {"answer_sent": 문장번호} 를 채워 준다(다음 문항의 avoid_sents 용)."""
    prompt = _PROMPTS.get(method, _PROMPT_SYNONYM)
    taken = {w.lower() for w in (avoid or set())}

    def _extra(o: VocabOut) -> None:
        dup = sorted(_mark_words(o.marks) & taken)
        if dup:
            raise ValueError(
                f"다른 어휘 문제와 밑줄이 겹칩니다: {', '.join(dup)}. 겹치지 않는 낱말로 다시 고르세요.")
        # 낱말 하나를 갈아 끼우다 구동사·전치사·타동사 목적어가 깨지면, 학생은 글을
        # 읽지 않고 '덜컹거리는 자리'만 보고 답을 고른다(실제 출력물: 'upset down',
        # 'hear to what', '목적어 없는 ignore,').
        broke = shape.check_marks_swaps(analysis.sentences, o.marks)
        if broke:
            raise ValueError("낱말을 바꾸자 문장이 깨졌습니다 — " + " ".join(broke))
        if method == NEGATION:
            # 정답 근거(부정어)가 밑줄 '안'에 있어야 문항이 성립한다.
            bad = (shape.check_clean_sentence(o.override_text, "교체 문장")
                   + shape.check_negation_underline(o.marks, o.answer_no, o.override_text))
            if bad:
                raise ValueError("부정어형 설계 결함 — " + " ".join(bad))

    out: VocabOut = client.structured(
        system=SYSTEM,
        prompt=(prompt.format(ctx=context(analysis)) + _avoid_clause(taken)
                + _sent_clause(set(avoid_sents or ()))),
        cache_prefix=context(analysis),
        model_cls=VocabOut,
        max_tokens=2500,
        max_retries=max_retries,
        extra_validate=_extra,
    )
    fixed = _restore_original_marks(out, method)
    if report is not None:
        report["answer_sent"] = (out.override_no
                                 or (out.marks[out.answer_no - 1].sent_no
                                     if 1 <= out.answer_no <= len(out.marks) else 0))
    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    overrides = None
    if out.override_no and out.override_text.strip():
        overrides = {out.override_no - 1: out.override_text}
    flags: list[str] = []
    q, a = B.make_vocab(analysis.sentences, marks, out.answer_no, out.reason,
                        overrides=overrides, flags=flags)
    if fixed:
        flags.append(f"정답 아닌 밑줄 {', '.join(map(str, fixed))}번을 원문 낱말로 되돌림")
    return q, a, flags, _mark_words(out.marks)


def generate_group(client: ClaudeClient, analysis: Analysis, body: str,
                   methods: dict[str, str], max_retries: int = 1,
                   logger=None, first=None, avoid: set[str] | None = None,
                   used_out: dict[str, set[str]] | None = None,
                   ) -> dict[str, tuple[str, str, list[str]]]:
    """정본에 밑줄을 치는 문항들을 '차례로' 만들어 밑줄이 겹치지 않게 한다.

    한 지문에 밑줄 문항이 여럿이면 저마다 '눈에 띄는 낱말'을 고르기 때문에 같은 자리에
    몰린다. 앞 문항이 쓴 낱말을 다음 문항에 '피할 낱말'로 넘겨 그것을 막는다.

    methods: {어휘 슬롯키: 방식}
    first:   [(슬롯키, 만드는 함수)] — 어휘보다 먼저 만들 밑줄 문항(짝짓기 등).
             함수는 avoid(피할 낱말 집합)를 받아 (q, a, flags, 쓴 낱말들)을 돌려준다.
    avoid:   이미 다른 밑줄 문항이 쓴 낱말(검수 승격으로 일부만 다시 만들 때 필요).
    used_out: {슬롯키: 그 문항이 쓴 낱말들} 을 채워 준다(다음 재생성의 avoid 용).
    한 슬롯이 실패해도 나머지는 살린다(그 슬롯만 빠지고 검토메모에 남는다).

    어휘 3종 중 '유의어형' 하나만 자기검증을 받는다(아래 _verify_synonym 참고).
    """
    from .. import verify as _verify

    used: set[str] = set(avoid or ())
    used_sents: set[int] = set()
    out: dict[str, tuple[str, str, list[str]]] = {}

    for slot, make in (first or []):
        try:
            q, a, flags, words = make(used)
        except Exception as e:      # noqa: BLE001 — 슬롯 단위 격리
            if logger:
                logger.warning("[%s] 생성 실패: %s", slot, e)
            continue
        used |= words
        if used_out is not None:
            used_out[slot] = set(words)
        out[slot] = (q, a, flags)

    for slot, method in methods.items():
        report: dict = {}
        try:
            q, a, flags, words = generate(client, analysis, body,
                                          max_retries=max_retries, method=method,
                                          avoid=used, avoid_sents=used_sents,
                                          report=report)
        except Exception as e:      # noqa: BLE001 — 슬롯 단위 격리
            if logger:
                logger.warning("[%s] 어휘 생성 실패: %s", slot, e)
            continue
        used |= words
        if report.get("answer_sent"):
            used_sents.add(report["answer_sent"])
        if used_out is not None:
            used_out[slot] = set(words)
        if method == SYNONYM:
            flags = list(flags) + _verify_synonym(_verify, client, q, a,
                                                  max_retries, logger, slot)
        out[slot] = (q, a, flags)
    return out


def _verify_synonym(_verify, client, q: str, a: str, max_retries: int,
                    logger, slot: str) -> list[str]:
    """유의어형 어휘만 자기검증을 건다. 어휘 3종 중 이것 하나뿐이다.

    왜 이것만인가 — 위험은 '모델이 갈아 끼운 낱말 중 정답이 아닌 것'에서만 생긴다.
    원문 그대로 둔 낱말은 필자가 쓴 말이므로 어색할 수가 없다.
      · 원문단어형·부정어형: 정답 아닌 밑줄 넷이 원문 그대로다(코드가 그렇게 복원한다
        — _restore_original_marks). 위험한 낱말이 0개라 물어볼 것이 없다.
      · 유의어형: 정답 아닌 넷을 '일부러' 유의어로 바꾼다. 그 넷이 바뀐 뒤에도 문맥에
        맞는지는 판단이고, 판단은 코드가 못 한다. 위험한 낱말이 4개다.
    그래서 지문당 검증 호출이 3회가 아니라 1회만 늘어난다.

    걸렸을 때 여기서 다시 만들지 않는 까닭: 산출물이 곧바로 판매되므로, 같은 모델로
    한 번 더 굴리는 것보다 상위 모델 승격에 넘기는 편이 낫다. '자동검증:' 로 시작하는
    사유를 달면 tiering.needs_escalation 이 이 문항을 승격 대상으로 잡는다.
    """
    ok, reason = _verify.verify(client, "vocab_synonym", q, a, max_retries=max_retries)
    if ok:
        return []
    if logger:
        logger.info("[%s] 어휘 자기검증 실패 → 승격 대상: %s", slot, reason)
    return [f"자동검증: {reason or '오답 넷의 문맥 적합성 재확인'}"]
