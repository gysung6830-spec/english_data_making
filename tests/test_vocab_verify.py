"""어휘 (상) 자동 교차검증 오프라인 테스트 (API 없이 가짜 client 사용).

실행: python -m tests.test_vocab_verify
검증 항목:
  - 검증 대상(어휘 상)이 없으면 client 를 호출하지 않고 원본 유지
  - ok=False 또는 valid_count!=2 인 문항만 제거, 정상 문항은 유지
  - 검증 호출이 예외를 던지면 원본을 그대로 유지(fail-open)
"""
from __future__ import annotations

from src import vocab_verify as vv
from src.config import load_config
from src.prose_render import LLMProseItem, LLMProsePack, LLMProseSentence


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


class _FakeClient:
    """client.structured 를 흉내내는 가짜. 호출 여부와 반환 판정을 제어한다."""

    def __init__(self, verdicts=None, raise_exc=False):
        self.verdicts = verdicts or []
        self.raise_exc = raise_exc
        self.calls = 0

    def structured(self, **kwargs):
        self.calls += 1
        if self.raise_exc:
            raise RuntimeError("boom")
        return vv.VocabVerifyResult(verdicts=self.verdicts)


def _pack():
    return LLMProsePack(sentences=[
        LLMProseSentence(
            no=1, en="A B C.", ko="가.",
            vocab_template="A {{P1}} B {{P2}} C.",
            vocab_items=[
                LLMProseItem(id="P1", display="[ big / large / bog ]",
                             answer="big / large", gloss="큰"),
                LLMProseItem(id="P2", display="[ different / diverse / distinct ]",
                             answer="different / diverse", gloss="다른"),
            ]),
        LLMProseSentence(
            no=2, en="X Y.", ko="나.",
            vocab_template="X {{P1}} Y.",
            vocab_items=[LLMProseItem(id="P1", display="[ start / begin / stark ]",
                                      answer="start / begin", gloss="시작하다")]),
    ])


def test_no_items_skips_call():
    cfg = load_config()
    llm = LLMProsePack(sentences=[LLMProseSentence(no=1, en="x", ko="y")])
    fc = _FakeClient()
    out = vv.verify_vocab_pack(fc, cfg, llm)
    _check("어휘(상) 없으면 client 미호출", fc.calls == 0)
    _check("원본 그대로 반환", out is llm)


def test_drops_error_items():
    cfg = load_config()
    llm = _pack()
    # 1:P2 는 정답 3개(출제오류) → ok=False. 2:P1 은 valid_count=1 → 제거. 1:P1 은 정상 유지.
    fc = _FakeClient(verdicts=[
        vv.VocabVerdict(key="1:P1", ok=True, valid_count=2),
        vv.VocabVerdict(key="1:P2", ok=False, valid_count=3, reason="세 보기 모두 유의어"),
        vv.VocabVerdict(key="2:P1", ok=True, valid_count=1, reason="유의어가 문맥상 어색"),
    ])
    out = vv.verify_vocab_pack(fc, cfg, llm)
    s1 = out.sentences[0].vocab_items
    s2 = out.sentences[1].vocab_items
    _check("client 1회 호출", fc.calls == 1)
    _check("정상 문항(1:P1) 유지", [it.id for it in s1] == ["P1"])
    _check("valid_count=1 문항(2:P1) 제거", len(s2) == 0)


def test_fail_open_on_exception():
    cfg = load_config()
    llm = _pack()
    before = sum(len(s.vocab_items) for s in llm.sentences)
    fc = _FakeClient(raise_exc=True)
    out = vv.verify_vocab_pack(fc, cfg, llm)
    after = sum(len(s.vocab_items) for s in out.sentences)
    _check("검증 예외 시 원본 유지(fail-open)", before == after == 3)


def test_options_parser():
    _check("보기 파싱", vv._options_of("[ a / b / c ]") == ["a", "b", "c"])


if __name__ == "__main__":
    test_no_items_skips_call()
    test_drops_error_items()
    test_fail_open_on_exception()
    test_options_parser()
    print("\n어휘 (상) 자동 교차검증 오프라인 테스트 통과 ✅")
