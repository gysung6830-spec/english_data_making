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
    """문장 3개짜리 통합 결과. ref_items_counts 로 문장별 '출제 가능한' ref 개수를 지정.

    실제 지칭처럼 대명사를 남기고 그 뒤에 {{Pn}} 을 넣어, render 가드를 통과(=renderable)하도록
    구성한다. 정답은 보기 안에 있고 한글·가주어·원문소실이 없다.
    """
    sents = []
    # (en, 대명사 뒤에 {{Pn}} 을 넣은 base 문장 조각, 보기)
    specs = [
        ("He found the photo.", "He {ph} found the photo.",
         "= [ Compean / a rescue team / the police ]", "Compean"),
        ("She kept it in her bag.", "She kept it {ph} in her bag.",
         "= [ the photo / a signal / her bag ]", "the photo"),
        ("They left the camp.", "They {ph} left the camp.",
         "= [ the hikers / the police / the camp ]", "the hikers"),
    ]
    for i, (n, (en, base, disp, ans)) in enumerate(zip(ref_items_counts, specs), start=1):
        phs = "".join(f"{{{{P{j+1}}}}}" for j in range(n))         # {{P1}}{{P2}}...
        template = base.format(ph=phs) if n else en
        items = [pr.LLMProseItem(id=f"P{j+1}", display=disp, answer=ans)
                 for j in range(n)]
        sents.append(pr.LLMProseSentence(no=i, en=en, ko="가",
                                         ref_template=template, ref_items=items))
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


def test_nonrenderable_raw_still_triggers():
    # raw ref_items 는 많지만(3+) render 가드에서 전부 버려지는 경우(가주어 it 등)
    # → renderable 수는 0 이므로 폴백이 켜지고, 버려질 문장을 폴백 결과로 덮어써야 한다.
    cfg = load_config()
    bad = pr.LLMProseItem(id="P1", display="= [ 앞 문장 / a / b ]", answer="앞 문장")
    # 가주어 it: _ref_is_expletive 로 render 에서 버려짐 → renderable 0
    llm = pr.LLMProsePack(sentences=[
        pr.LLMProseSentence(no=1, en="It turns out that a photo helped.", ko="가",
                            ref_template="It {{P1}} turns out that a photo helped.",
                            ref_items=[bad]),
        pr.LLMProseSentence(no=2, en="She kept it.", ko="나",
                            ref_template="She kept it.", ref_items=[]),
        pr.LLMProseSentence(no=3, en="They left.", ko="다",
                            ref_template="They left.", ref_items=[]),
    ])
    _check("raw 는 있으나 renderable 0", pr.renderable_ref_count(llm) == 0)
    ref_pack = pr.LLMProsePack(sentences=[
        pr.LLMProseSentence(no=2, en="She kept it.", ko="나",
                            ref_template="She kept it {{P1}}.",
                            ref_items=[pr.LLMProseItem(id="P1",
                                       display="= [ the photo / She / They ]",
                                       answer="the photo")]),
    ])
    fc = _FakeClient(ref_pack=ref_pack)
    pg._ensure_ref(fc, cfg, _extraction(), llm)
    _check("renderable 0 이면 폴백 재호출", fc.calls == 1)
    _check("빈 문장에 폴백 지칭 채움", llm.sentences[1].ref_items[0].answer == "the photo")
    _check("버려질 가주어 문장은 그대로(덮어쓸 폴백 없음)", llm.sentences[0].ref_items[0] is bad)


# ── 어법·어휘 '문장당 최소 2개' 미달 top-up 보강 ───────────────────────────
def _count_sentence(no, g, ve, v):
    """no번 문장에 어법 g·어휘하 ve·어휘상 v개 문항(짧고 '고유한' en 으로 가드 통과·중복 회피)."""
    def tmpl(n):
        return "w " + " ".join(f"{{{{P{j+1}}}}} w" for j in range(n))
    def two(n):     # 2지선다(어법·어휘하)
        return [pr.LLMProseItem(id=f"P{j+1}", display=f"[x{j}/y{j}]", answer=f"x{j}")
                for j in range(n)]
    def three(n):   # 3개 중 2개(어휘상)
        return [pr.LLMProseItem(id=f"P{j+1}", display=f"[a{j}/b{j}/c{j}]", answer=f"a{j} / b{j}")
                for j in range(n)]
    return pr.LLMProseSentence(
        no=no, en=f"n{no} aa bb cc dd ee ff", ko="가",
        grammar_template=tmpl(g), grammar_items=two(g),
        vocab_easy_template=tmpl(ve), vocab_easy_items=two(ve),
        vocab_template=tmpl(v), vocab_items=three(v))


def test_counts_enough_skips_call():
    cfg = load_config()
    llm = pr.LLMProsePack(sentences=[_count_sentence(1, 2, 2, 2), _count_sentence(2, 3, 2, 2)])
    fc = _FakeClient()
    pg._ensure_counts(fc, cfg, _extraction(), llm)
    _check("어법·어휘 충분하면 재호출 없음", fc.calls == 0)


def test_counts_low_merges():
    cfg = load_config()
    # 2번 문장의 어법이 1개(min 2 미달) → top-up 재요청으로 채워야 함
    llm = pr.LLMProsePack(sentences=[_count_sentence(1, 2, 2, 2), _count_sentence(2, 1, 2, 2)])
    top = pr.LLMProsePack(sentences=[_count_sentence(2, 3, 2, 2)])   # 2번 어법 3개 제공
    fc = _FakeClient(ref_pack=top)
    pg._ensure_counts(fc, cfg, _extraction(), llm)
    _check("미달 시 top-up 재호출 1회", fc.calls == 1)
    _check("부족 문장 어법 채움(1→3)", len(llm.sentences[1].grammar_items) == 3)
    _check("충분했던 문장은 그대로(2개)", len(llm.sentences[0].grammar_items) == 2)


def test_counts_fail_open():
    cfg = load_config()
    llm = pr.LLMProsePack(sentences=[_count_sentence(1, 1, 2, 2)])
    fc = _FakeClient(raise_exc=True)
    pg._ensure_counts(fc, cfg, _extraction(), llm)          # 예외 삼킴
    _check("top-up 예외 시 원본 유지(fail-open)", len(llm.sentences[0].grammar_items) == 1)


if __name__ == "__main__":
    test_enough_ref_skips_call()
    test_low_ref_merges_by_no()
    test_does_not_overwrite_existing_ref()
    test_fail_open_on_exception()
    test_nonrenderable_raw_still_triggers()
    test_counts_enough_skips_call()
    test_counts_low_merges()
    test_counts_fail_open()
    print("\n지칭·개수 보강 오프라인 테스트 통과 ✅")
