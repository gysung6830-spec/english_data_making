"""지칭(ref) 부족 시 '지칭 전용' 재생성 보강 오프라인 테스트 (API 없이 가짜 client).

실행: python -m tests.test_ensure_ref
검증 항목:
  - ref 문항이 충분하면(>= _REF_MIN) 별도 호출 없이 원본 유지
  - ref 문항이 부족하면 지칭 전용 호출 결과를 문장 단위로 병합(no/en 매칭)
  - 이미 ref 가 있는 문장은 덮어쓰지 않음
  - 재생성 호출이 예외를 던지면 원본 유지(fail-open)
"""
from __future__ import annotations

from src import prose_generate as pg
from src import prose_render as pr
from src.config import load_config
from src.schemas import Extraction


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


class _FakeClient:
    """client.structured 흉내. ref 전용 호출에 반환할 pack 을 제어한다."""

    def __init__(self, ref_pack=None, raise_exc=False):
        self.ref_pack = ref_pack
        self.raise_exc = raise_exc
        self.calls = 0

    def structured(self, **kwargs):
        self.calls += 1
        if self.raise_exc:
            raise RuntimeError("boom")
        return self.ref_pack


def _extraction():
    return Extraction(title="T", source="S",
                      paragraphs=["He found the photo. She kept it. They left."])


def _main_pack(ref_items_counts):
    """문장 3개짜리 통합 결과. ref_items_counts 로 문장별 ref 개수를 지정."""
    sents = []
    ens = ["He found the photo.", "She kept it.", "They left."]
    for i, (en, n) in enumerate(zip(ens, ref_items_counts), start=1):
        items = [pr.LLMProseItem(id=f"P{j+1}", display="= [ a / b / c ]", answer="a")
                 for j in range(n)]
        sents.append(pr.LLMProseSentence(no=i, en=en, ko="가",
                                         ref_template=en, ref_items=items))
    return pr.LLMProsePack(sentences=sents)


def test_enough_ref_skips_call():
    cfg = load_config()
    llm = _main_pack([2, 1, 0])          # 총 3개 >= _REF_MIN(3)
    fc = _FakeClient()
    pg._ensure_ref(fc, cfg, _extraction(), llm)
    _check("ref 충분하면 재호출 없음", fc.calls == 0)


def test_low_ref_merges_by_no():
    cfg = load_config()
    llm = _main_pack([0, 0, 0])          # 총 0개 < _REF_MIN
    ref_pack = pr.LLMProsePack(sentences=[
        pr.LLMProseSentence(no=2, en="She kept it.", ko="나",
                            ref_template="She kept it {{P1}}.",
                            ref_items=[pr.LLMProseItem(id="P1",
                                       display="= [ the photo / She / They ]",
                                       answer="the photo")]),
    ])
    fc = _FakeClient(ref_pack=ref_pack)
    pg._ensure_ref(fc, cfg, _extraction(), llm)
    _check("부족 시 재호출 1회", fc.calls == 1)
    s2 = llm.sentences[1]
    _check("no 매칭으로 ref 병합", len(s2.ref_items) == 1 and s2.ref_items[0].answer == "the photo")
    _check("ref_template 갱신", "{{P1}}" in s2.ref_template)


def test_does_not_overwrite_existing_ref():
    cfg = load_config()
    llm = _main_pack([1, 0, 0])          # 총 1개 < _REF_MIN → 재생성되지만 기존 문장 보호
    orig = llm.sentences[0].ref_items[0]
    ref_pack = pr.LLMProsePack(sentences=[
        pr.LLMProseSentence(no=1, en="He found the photo.", ko="다",
                            ref_template="He found the photo {{P1}}.",
                            ref_items=[pr.LLMProseItem(id="P1", display="= [ x / y / z ]",
                                                       answer="x")]),
    ])
    fc = _FakeClient(ref_pack=ref_pack)
    pg._ensure_ref(fc, cfg, _extraction(), llm)
    _check("이미 ref 있는 문장은 덮어쓰지 않음", llm.sentences[0].ref_items[0] is orig)


def test_fail_open_on_exception():
    cfg = load_config()
    llm = _main_pack([0, 0, 0])
    fc = _FakeClient(raise_exc=True)
    pg._ensure_ref(fc, cfg, _extraction(), llm)   # 예외를 삼켜야 함
    _check("재생성 예외 시 원본 유지(fail-open)",
           sum(len(s.ref_items) for s in llm.sentences) == 0)


if __name__ == "__main__":
    test_enough_ref_skips_call()
    test_low_ref_merges_by_no()
    test_does_not_overwrite_existing_ref()
    test_fail_open_on_exception()
    print("\n지칭 전용 재생성 보강 오프라인 테스트 통과 ✅")
