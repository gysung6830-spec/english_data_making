"""동형모의고사 오프라인 테스트 (API 키 없이 전 구간 검증)."""
from __future__ import annotations

from pathlib import Path

import pytest

from mockexam.core.blueprint import blueprint_from_profile
from mockexam.ingest.loader import detect_format, load_passages, split_passages
from mockexam.corpus.selector import assign_passages, profile_passage
from mockexam.pipeline import generate_mock
from mockexam.school import (
    resolve_profile, standard_skeleton, load_schools_index,
)
from mockexam.verify.verifier import verify

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "input" / "sample_passages.txt"


# ---------------------------------------------------------------------------
# 학교 프로파일 / blueprint
# ---------------------------------------------------------------------------
def test_schools_index_has_five():
    ids = {s["school_id"] for s in load_schools_index()}
    assert {"munsan_ms", "daegok_ms", "jinyang_hs", "jeil_ghs", "dongmyeong_hs"} <= ids


def test_jinyang_blueprint_matches_spec():
    prof = resolve_profile("jinyang_hs", 1)
    assert prof["learned"] is True
    bp = blueprint_from_profile(prof, 1)
    assert len(bp.choice_items) == 18
    assert len(bp.essay_items) == 9
    assert abs(bp.total_score - 100.0) < 0.01


def test_unlearned_school_uses_standard_skeleton_not_jinyang():
    prof = resolve_profile("munsan_ms", 1)
    assert prof["learned"] is False
    bp = blueprint_from_profile(prof, 1)
    # 진양고(18/9)를 베끼지 않는다.
    assert (len(bp.choice_items), len(bp.essay_items)) != (18, 9)
    assert abs(bp.total_score - 100.0) < 0.01


def test_middle_and_high_skeletons_sum_to_100():
    for level in ("middle", "high"):
        skel = standard_skeleton(level, 1)
        total = sum(i["score"] for i in skel["item_template"])
        assert abs(total - 100.0) < 0.01, (level, total)


# ---------------------------------------------------------------------------
# 입력 파싱 / 형식 판별
# ---------------------------------------------------------------------------
def test_passage_split_and_format_detection():
    passages = load_passages([SAMPLE])
    assert len(passages) == 4
    fmts = {p.format_type for p in passages}
    assert "dialogue" in fmts
    assert "notice" in fmts


def test_detect_format_dialogue():
    txt = "M: Hello there.\nW: Hi, how are you?\nM: Good, thanks."
    fmt, speakers = detect_format(txt)
    assert fmt == "dialogue"


def test_bilingual_ebs_material_is_cleaned_and_split():
    """직독직해(EBS) 자료: 단원별 분리 + 한글 해석 제거 후 영어 지문 복원."""
    from mockexam.ingest.loader import split_passages
    raw = (
        "[EBS]올림포스영어독해기본1한줄해석(좌지문우해석) Ch. 04 Unit 10 - 2번: 한글 제목 "
        "① Although the wish to be alone is often strong, its intensity varies from "
        "혼자 있고 싶은 소망은 강하다. person to person. ② An equally impelling impulse "
        "하지만 다른 충동도 있다 is to seek the company of others and to share time. "
        "[EBS]올림포스영어독해기본1한줄해석(좌지문우해석) Ch. 04 Unit 10 - 3번: 다른 제목 "
        "① At one end of the spectrum was the forest gardening of New Guinea "
        "변화의 한쪽 끝. ② This approach left minimal traces on the land. 최소 흔적.")
    ps = split_passages(raw)
    assert len(ps) == 2, [p.text for p in ps]
    joined = " ".join(p.text for p in ps)
    # 한글·출처·문장번호가 제거되어야 한다
    assert "혼자" not in joined and "제목" not in joined
    assert "EBS" not in joined and "①" not in joined
    assert "Although the wish to be alone" in ps[0].text
    assert "forest gardening" in ps[1].text
    # 문장 경계(마침표)가 복원되어야 한다
    assert ps[0].text.rstrip().endswith((".", "!", "?"))
    assert ps[0].text.count(".") >= 1


def test_bilingual_other_textbook_headers_and_watermark():
    """다른 교재 형식(N강 헤더 + URL 워터마크)도 지문 분리·정제."""
    from mockexam.ingest.loader import split_passages
    raw = (
        "마더텅 5강 http://mothertongue.co.kr "
        "① Success often comes from small habits repeated every single day 매일 반복된다. "
        "② Over time these tiny habits shape exactly who we eventually become 우리를 만든다. "
        "③ The lesson is that consistency beats intensity in the long run 일관성이 이긴다. "
        "6강 ① Reading widely builds both empathy and broad general knowledge 독서는 쌓는다. "
        "② It also steadily improves attention and focus over many years 집중력 향상. "
        "③ Thus a daily reading habit rewards the patient learner 보상한다.")
    ps = split_passages(raw)
    assert len(ps) == 2
    joined = " ".join(p.text for p in ps)
    assert "mothertongue" not in joined and "마더텅" not in joined
    assert "습관" not in joined and "①" not in joined
    assert "Success often comes" in ps[0].text
    assert "Reading widely builds" in ps[1].text


def test_bilingual_headerless_splits_into_passages():
    """헤더·문장번호 없는 직독직해도 문장묶음으로 여러 지문 확보."""
    from mockexam.ingest.loader import split_passages
    sents = [f"This is English study sentence number {i} about a topic 한글 해석 {i}."
             for i in range(1, 17)]
    ps = split_passages(" ".join(sents))
    assert len(ps) >= 2
    assert all("한글" not in p.text for p in ps)


# ---------------------------------------------------------------------------
# 배정 (형식 하드제약)
# ---------------------------------------------------------------------------
def test_assignment_format_hard_constraint():
    passages = load_passages([SAMPLE])
    pmap = {p.id: p for p in passages}
    prof = resolve_profile("jinyang_hs", 1)
    bp = blueprint_from_profile(prof, 1)
    assigns = assign_passages(bp, passages, difficulty="mid")
    for a in assigns:
        if a.type == "dialogue_mismatch" and a.passage_id:
            assert pmap[a.passage_id].format_type == "dialogue"
        if a.type == "notice_match" and a.passage_id:
            assert pmap[a.passage_id].format_type == "notice"


def _synthetic_passages(n):
    from mockexam.core.models import Passage
    topics = ["talent", "traffic", "sleep", "coral reefs", "invention", "reading",
              "volunteering", "language", "habits", "memory", "climate", "music"]
    out = []
    for i in range(n):
        t = topics[i % len(topics)]
        text = (f"Research about {t} shows an interesting pattern. When people focus "
                f"on {t}, however, they often overlook the details. Therefore the way "
                f"we treat {t} matters, and in conclusion small choices shape it. "
                f"For instance, one study proved that {t} can change over time.")
        out.append(Passage(id=f"p{i+1}", text=text, format_type="narrative"))
    return out


def test_few_passages_unlimited_reuse_all_filled():
    """지문 수 < 문항 수: 제한 없이 재사용하여 모든 문항을 채운다(스킵 없음)."""
    bp = blueprint_from_profile(resolve_profile("jinyang_hs", 1), 1)   # 27슬롯
    passages = _synthetic_passages(3)                                  # 3 < 27
    assigns = assign_passages(bp, passages, difficulty="mid")
    assert len(assigns) == 27
    assert all(a.passage_id is not None for a in assigns), "스킵된 문항이 있으면 안 됨"
    from collections import Counter
    used = Counter(a.passage_id for a in assigns)
    assert max(used.values()) > 2, "지문 부족 시 2회 초과 재사용이 허용돼야 함"


def test_enough_passages_cap_two_and_all_filled():
    """지문 수 ≥ 문항 수: 한 지문 최대 2회, 그리고 모든 문항이 채워진다."""
    bp = blueprint_from_profile(resolve_profile("jinyang_hs", 1), 1)   # 27슬롯
    passages = _synthetic_passages(30)                                 # 30 ≥ 27
    assigns = assign_passages(bp, passages, difficulty="mid")
    assert all(a.passage_id is not None for a in assigns), "스킵된 문항이 있으면 안 됨"
    from collections import Counter
    used = Counter(a.passage_id for a in assigns)
    assert max(used.values()) <= 2, f"지문 충분 시 최대 2회: {used}"


# ---------------------------------------------------------------------------
# 전체 파이프라인 (오프라인) + 검증기
# ---------------------------------------------------------------------------
def test_generate_offline_passes_verifier():
    res = generate_mock("jinyang_hs", [SAMPLE], difficulty="중", grade=1, client=None)
    rep = res.verify_report
    # 핵심 검증(문항수/배점/유형배치/번호연속)은 반드시 통과
    by = {c.name: c for c in rep.checks}
    assert by["문항수"].ok, by["문항수"].detail
    assert by["배점합"].ok, by["배점합"].detail
    assert by["유형·배치"].ok, by["유형·배치"].detail
    assert by["번호연속"].ok, by["번호연속"].detail
    assert by["정답유일성"].ok, by["정답유일성"].detail


def test_strict_schema_has_no_unsupported_keywords():
    """Anthropic strict 출력이 거부하는 키워드가 어떤 스키마에도 없어야 한다."""
    import json
    from mockexam.core.client import to_strict_schema
    from mockexam.core.llm import ChoiceQuestionOut, EssayQuestionOut
    banned = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
              "multipleOf", "minLength", "maxLength", "minItems", "maxItems",
              "default", "title", "examples", "$ref", "$defs")
    for M in (ChoiceQuestionOut, EssayQuestionOut):
        js = json.dumps(to_strict_schema(M))
        for k in banned:
            assert f'"{k}"' not in js, f"{M.__name__} 에 {k} 가 남아있음"


def test_no_strict_output_config_and_lenient_parse():
    """strict 구조화 출력을 쓰지 않아 스키마 키워드 400 이 원천 불가능.

    요청에 output_config 가 없고, 응답은 코드펜스/설명이 섞여도 파싱된다.
    """
    from mockexam.core.client import build_request, parse_response_text
    from mockexam.core.llm import ChoiceQuestionOut
    req = build_request("m", "sys", "prompt", ChoiceQuestionOut)
    assert "output_config" not in req          # ← 400 유발하던 부분이 사라짐
    assert "JSON" in req["messages"][0]["content"]
    fenced = ('설명입니다\n```json\n{"passage":"P","choices":["a","b","c","d","e"],'
              '"answer_index":2,"explanation":"e"}\n```')
    obj = parse_response_text(fenced, ChoiceQuestionOut)
    assert obj.answer_index == 2 and len(obj.choices) == 5


class _FakeLLMClient:
    """LLM 응답을 흉내내는 가짜 클라이언트 — LLM 경로(build_choice/essay)를
    실제 키 없이 오프라인 테스트로 검증한다(리팩터/응답처리 버그 조기 발견)."""

    def structured(self, system, prompt, model_cls, **kw):
        name = model_cls.__name__
        if name == "ChoiceQuestionOut":
            return model_cls(
                passage=("Intro. ①<u>a</u> ②<u>b</u> ③<u>c</u> ④<u>d</u> ⑤<u>e</u>. "
                         "(A) one (B) two (C) three ____ blank."),
                choices=["opt1", "opt2", "opt3", "opt4", "opt5"],
                answer_index=3, explanation="정답 ③. 근거 …")
        if name == "EssayQuestionOut":
            return model_cls(
                passage="Passage with a ____ blank. [요약문] A ____ summary.",
                bogi=["w1", "w2", "w3"], conditions=["본문 단어만 쓸 것"],
                blank_ko="우리말 문장", answers=["지시 :: 정답"], explanation="해설 …")
        raise AssertionError(f"unexpected model {name}")


def test_full_llm_path_runs_without_error():
    """가짜 LLM으로 전체 생성 경로를 태워 리팩터/응답처리 버그를 잡는다.

    (이 테스트가 있었다면 prompt_extra AttributeError 를 사전에 잡았음)
    """
    res = generate_mock("jinyang_hs", [SAMPLE], difficulty="중", grade=1,
                        client=_FakeLLMClient())
    assert len(res.exam.questions) == 27
    # LLM 경로가 실제로 실행되어 내용이 채워졌는지(자리표시자가 아님)
    for q in res.exam.choice_questions:
        assert q.answer in "①②③④⑤"
    for q in res.exam.essay_questions:
        assert q.answer


def test_generation_selfcheck_rejects_bad_structure():
    """생성 단계 자가검증: 구조·<보기>·정답 누락이면 ValueError(→ 자동 재작성 유발)."""
    from mockexam.core.models import Item
    from mockexam.core.llm import ChoiceQuestionOut, EssayQuestionOut
    from mockexam.generators.base import _validate_choice_out, _validate_essay_out

    # 어법 유형인데 지문에 밑줄(①~⑤)이 없으면 거부
    it_g = Item(no=1, section="choice", type="grammar", score=3, underlines=5)
    bad = ChoiceQuestionOut(passage="No underlines here.",
                            choices=list("abcde"), answer_index=3, explanation="e")
    with pytest.raises(ValueError):
        _validate_choice_out(it_g, bad)
    good = ChoiceQuestionOut(
        passage="①<u>a</u> ②<u>b</u> ③<u>c</u> ④<u>d</u> ⑤<u>e</u>.",
        choices=list("abcde"), answer_index=3, explanation="e")
    _validate_choice_out(it_g, good)  # 통과(예외 없음)

    # 배열영작 서술형인데 <보기> 비면 거부
    it_e = Item(no=1, section="essay", type="word_arrange", score=4)
    bad_e = EssayQuestionOut(passage="p", bogi=[], answers=["x"])
    with pytest.raises(ValueError):
        _validate_essay_out(it_e, bad_e)
    good_e = EssayQuestionOut(passage="p", bogi=["w1", "w2"], answers=["x"])
    _validate_essay_out(it_e, good_e)  # 통과


def test_review_flag_from_confidence_and_verbatim():
    """해설지 '⚠ 확인 권장' 사유 판정: 자가확신 '주의' + 유의어원리 위반(정답=지문복붙)."""
    from mockexam.core.models import Item
    from mockexam.core.llm import ChoiceQuestionOut
    from mockexam.generators.base import _flag_reason

    it = Item(no=1, section="choice", type="main_point", score=3)
    # 확신도 '주의' → 플래그
    o1 = ChoiceQuestionOut(passage="The passage about bees and honey.",
                           choices=["요지 A", "요지 B", "요지 C", "요지 D", "요지 E"],
                           answer_index=1, explanation="e", answer_confidence="주의")
    assert _flag_reason(it, o1)
    # 확신도 '확실' + 정답이 지문과 겹치지 않는 패러프레이즈 → 플래그 없음
    o2 = ChoiceQuestionOut(passage="The passage about bees and honey.",
                           choices=["꿀벌의 협업", "b", "c", "d", "e"],
                           answer_index=1, explanation="e", answer_confidence="확실")
    assert not _flag_reason(it, o2)
    # 정답 선지가 지문 문장을 거의 그대로 복붙 → 유의어원리 위반 플래그
    o3 = ChoiceQuestionOut(passage="Bees make honey from flower nectar every summer.",
                           choices=["Bees make honey from flower nectar every summer",
                                    "b", "c", "d", "e"],
                           answer_index=1, explanation="e", answer_confidence="확실")
    assert _flag_reason(it, o3)


def test_review_flag_collected_on_separate_last_page(tmp_path):
    """확인 권장 문항은 해설지 인라인이 아니라 맨 끝 별도 페이지에 모아 표시한다."""
    from mockexam.render.exam import build_answer_html, _review_summary_body, render_exam

    res = generate_mock("jinyang_hs", [SAMPLE], difficulty="중", grade=1, client=None)
    res.exam.questions[0].meta["review_flag"] = "정답 유일성 자가점검에서 '주의'로 표시됨"
    # 해설지 본문에는 인라인 ⚠·주석이 없어야 한다
    ans = build_answer_html(res.exam, {}, footer="")
    assert "⚠ 확인 권장" not in ans and "자동 점검 참고" not in ans
    # 별도 페이지에는 해당 문항이 모여 나온다
    summary = _review_summary_body(res.exam)
    assert "확인 권장 문항" in summary and "1번" in summary
    # 전체 렌더에도 별도 페이지가 마지막에 포함된다
    out = render_exam(res.exam, tmp_path, header_info={}, footer="", to_pdf=False)
    doc = out["problem_html"].read_text(encoding="utf-8")
    assert "확인 권장 문항" in doc


def test_pdf_vision_extraction_and_flag_review():
    """API 키 있으면 PDF는 비전으로 추출하고, 의심문항(⚠)만 2차 검수로 확정한다."""
    from mockexam.ingest.vision import VisionPassages, VisionPassage
    from mockexam.core.llm import ChoiceQuestionOut, EssayQuestionOut
    from mockexam.verify.review import ReviewVerdict

    class VisFake:
        def structured(self, system, prompt, model_cls, **kw):
            n = model_cls.__name__
            if n == "VisionPassages":
                assert str(kw.get("image_path", "")).endswith(".pdf")  # PDF가 비전으로
                return VisionPassages(passages=[VisionPassage(
                    text=("Preservation and conservation have long been linked; both "
                          "keep an object in its present state and protect it from change "
                          "for study and display over many years."),
                    format="narrative")])
            if n == "ChoiceQuestionOut":
                return ChoiceQuestionOut(
                    passage="①<u>a</u> ②<u>b</u> ③<u>c</u> ④<u>d</u> ⑤<u>e</u>. (A) x (B) y (C) z ____.",
                    choices=list("abcde"), answer_index=3, explanation="e",
                    answer_confidence="주의")            # 전부 의심 → 검수 대상
            if n == "EssayQuestionOut":
                return EssayQuestionOut(
                    passage="p ____. [요약문] s ____.", bogi=["w1", "w2"],
                    conditions=["c"], blank_ko="우리말", answers=["지시 :: 정답"],
                    explanation="e", answer_confidence="확실")
            if n == "ReviewVerdict":
                return ReviewVerdict(ok=True, issue="")   # 검수 통과 → 플래그 해제
            raise AssertionError(n)

    # .pdf 경로면 비전 분기(가짜 client 가 가로채므로 실제 파일 IO 없음)
    res = generate_mock("jinyang_hs", ["/tmp/__nofile__.pdf"], difficulty="중",
                        grade=1, client=VisFake())
    assert len(res.exam.questions) == 27
    flagged = [q.no for q in res.exam.questions
               if isinstance(q.meta, dict) and q.meta.get("review_flag")]
    assert not flagged, "검수 통과한 의심문항은 ⚠가 해제되어야 한다"


def test_transient_generation_failure_auto_recovers():
    """일시적 생성 실패(응답 텍스트 없음 등) 문항은 파이프라인이 자동 재시도로 복구한다."""
    class Flaky(_FakeLLMClient):
        def __init__(self):
            self.fail_once = True

        def structured(self, system, prompt, model_cls, **kw):
            if (model_cls.__name__ == "EssayQuestionOut"
                    and "밑줄 친 우리말" in prompt and self.fail_once):
                self.fail_once = False
                raise RuntimeError("응답에 텍스트 블록이 없습니다.")
            return super().structured(system, prompt, model_cls, **kw)

    res = generate_mock("jinyang_hs", [SAMPLE], difficulty="중", grade=1,
                        client=Flaky())
    failed = [q for q in res.exam.questions
              if isinstance(q.meta, dict)
              and str(q.meta.get("review_flag", "")).startswith("생성 실패")]
    assert not failed, "일시적 실패가 자동 재시도로 복구되어야 한다"


def test_dialogue_notice_format_fallback():
    """대화/안내문 지문이 없어 대체된 경우, 지어내지 말고 일반 내용(불)일치로 전환."""
    from mockexam.core.models import Item, Passage
    from mockexam.generators.base import GenContext, PassageAnalysis
    from mockexam.generators.dialogue import gen_dialogue_mismatch, gen_notice_match

    ctx = GenContext(profile={"name": "t"}, difficulty="mid", client=None)

    def stem_of(fn, typ, fmt):
        p = Passage(id="x", text="A B C. D E F. G H I. J K L. M N O.", format_type=fmt)
        return fn(Item(no=1, section="choice", type=typ, score=3),
                  p, PassageAnalysis.of(p), ctx).stem

    assert "대화" in stem_of(gen_dialogue_mismatch, "dialogue_mismatch", "dialogue")
    assert "대화" not in stem_of(gen_dialogue_mismatch, "dialogue_mismatch", "narrative")
    assert "안내문" in stem_of(gen_notice_match, "notice_match", "notice")
    assert "안내문" not in stem_of(gen_notice_match, "notice_match", "narrative")


def test_structural_selfcheck_alignment():
    """원리↔검증 정합성: 유형이 요구하는 구조가 빠지면 생성단계에서 반드시 걸린다.

    (implied_meaning=<u>, order/vocab_3blank_abc=(A)(B)(C), blank_single=____)
    """
    from mockexam.core.models import Item
    from mockexam.core.llm import ChoiceQuestionOut
    from mockexam.generators.base import _validate_choice_out

    def out(passage):
        return ChoiceQuestionOut(passage=passage, choices=list("abcde"),
                                 answer_index=1, explanation="e")

    cases = [
        ("implied_meaning", "No underline here.", "He <u>broke the ice</u> at once."),
        ("order", "Intro then paragraphs.", "Intro. (A) one (B) two (C) three."),
        ("vocab_3blank_abc", "no markers", "(A) x (B) y (C) z in text."),
        ("blank_single", "no blank at all", "The key point is ____ indeed."),
    ]
    for typ, bad, good in cases:
        it = Item(no=1, section="choice", type=typ, score=3)
        with pytest.raises(ValueError):
            _validate_choice_out(it, out(bad))     # 구조 없음 → 걸림
        _validate_choice_out(it, out(good))        # 구조 있음 → 통과


def test_answer_index_range_validated():
    from pydantic import ValidationError
    from mockexam.core.llm import ChoiceQuestionOut
    import pytest as _pt
    for bad in (0, 6, -1):
        with _pt.raises(ValidationError):
            ChoiceQuestionOut(passage="p", choices=list("abcde"),
                              answer_index=bad, explanation="e")
    ok = ChoiceQuestionOut(passage="p", choices=list("abcde"),
                           answer_index=4, explanation="e")
    assert ok.answer_index == 4


def test_create_with_retry_backoff(monkeypatch):
    """429/529 는 백오프로 재시도하고, 그 외 오류는 즉시 전파."""
    import mockexam.core.client as C
    monkeypatch.setattr(C.time, "sleep", lambda *_: None)  # 실제 대기 제거

    class Boom(Exception):
        def __init__(self, status): self.status_code = status

    class FakeMessages:
        def __init__(self, fails, status): self.n = 0; self.fails = fails; self.status = status
        def create(self, **kw):
            if self.n < self.fails:
                self.n += 1
                raise Boom(self.status)
            return "ok"

    class FakeClient:
        def __init__(self, fails, status): self.messages = FakeMessages(fails, status)

    # 429 두 번 실패 후 성공
    assert C.create_with_retry(FakeClient(2, 429), {}, max_attempts=5) == "ok"
    # 529(과부하)도 재시도 대상
    assert C.create_with_retry(FakeClient(1, 529), {}, max_attempts=5) == "ok"
    # 400 은 재시도 대상 아님 → 즉시 전파
    import pytest as _pt
    with _pt.raises(Boom):
        C.create_with_retry(FakeClient(1, 400), {}, max_attempts=5)


def test_one_question_failure_does_not_kill_exam():
    """한 문항 생성이 실패해도 나머지는 완성되고 전체 문항수는 유지된다."""
    from mockexam.generators.base import GenContext
    from mockexam.generators.engine import generate_all

    class RaisingClient:
        def structured(self, *a, **k):
            raise RuntimeError("검증 실패(재시도 소진)")

    bp = blueprint_from_profile(resolve_profile("jinyang_hs", 1), 1)
    passages = _synthetic_passages(20)
    assigns = assign_passages(bp, passages, difficulty="mid")
    pmap = {p.id: p for p in passages}
    ctx = GenContext(profile=resolve_profile("jinyang_hs", 1), difficulty="mid",
                     client=RaisingClient())
    exam, logs = generate_all(bp, assigns, pmap, ctx)
    assert len(exam.questions) == 27, "실패해도 전 문항이 채워져야 함"
    assert any(l.get("note") == "generation_failed" for l in logs)


def test_generate_offline_high_school_unlearned():
    res = generate_mock("dongmyeong_hs", [SAMPLE], difficulty="상", grade=2, client=None)
    assert res.blueprint.meta.learned is False
    by = {c.name: c for c in res.verify_report.checks}
    assert by["배점합"].ok
    assert by["번호연속"].ok
