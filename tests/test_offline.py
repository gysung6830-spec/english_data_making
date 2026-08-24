"""API 없이 돌아가는 오프라인 테스트.

실행: python -m tests.test_offline   (또는 pytest)
검증 항목:
  - PDF 전처리(문제/정답 제거)
  - 스키마 검증 (문법 정확히 10개, 어휘 개수 범위)
  - 검증 실패 시 재시도 로직
  - HTML 렌더링
"""
from __future__ import annotations

import json
import types

from src import extract, prompts, render, schemas
from src.client import ClaudeClient, DEFAULT_MAX_TOKENS


# ---- 1. 전처리: 문제/정답/보기 제거 ----------------------------------------
def test_clean_removes_noise():
    raw = (
        "The Value of Curiosity\n"
        "Curiosity drives us to explore.\n"
        "1. What is the main idea?\n"
        "① Memorizing answers.\n"
        "② Curiosity is valuable.\n"
        "정답: ②\n"
        "해설: 호기심이 핵심이다.\n"
    )
    cleaned = extract.clean_text(raw)
    assert "Curiosity drives us" in cleaned        # 본문 보존
    assert "정답" not in cleaned                    # 정답 줄 제거
    assert "①" not in cleaned and "②" not in cleaned  # 객관식 보기 제거
    # 숫자 번호로 시작하는 줄은 '번호 표시'만 떼고 내용은 보존한다.
    #   (문장 나열형 자료에서 첫 줄이 통째로 사라지지 않게 하기 위함이며,
    #    남는 문항 텍스트는 지문 추출 API 단계에서 최종적으로 걸러진다)
    assert "1. What" not in cleaned                # 번호 표시는 제거됨
    print("PASS  전처리(노이즈 제거)")


# ---- 2. 스키마 검증: 문법은 비어있지 않으면 개수 제한 없음 -------------------
def test_grammar_non_empty():
    try:
        schemas.GrammarSection.model_validate({"items": []})
        assert False, "빈 목록은 통과하면 안 됨"
    except Exception:
        pass
    # 개수 제한이 없으므로 3개든 15개든 통과해야 함
    for n in (3, 15):
        items = [{"no": i, "point": "p", "example": "e", "explanation": "x", "sentence_no": i}
                 for i in range(1, n + 1)]
        schemas.GrammarSection.model_validate({"items": items})
    print("PASS  문법 개수 제한 없음(비어있지만 않으면 OK)")


# ---- 3. 어휘 개수 범위 -----------------------------------------------------
def test_vocab_count_range():
    items = [{"no": i, "word": "w", "meaning": "m"} for i in range(1, 6)]  # 5개
    v = schemas.VocabSection.model_validate({"items": items})
    try:
        v.validate_count(12, 20)
        assert False, "범위 밖인데 통과하면 안 됨"
    except ValueError:
        pass
    print("PASS  어휘 개수 범위 검증")


# ---- 4. 재시도 로직 (가짜 클라이언트) --------------------------------------
class _FakeStream:
    """messages.stream(...) 컨텍스트 매니저 흉내."""
    def __init__(self, message):
        self._message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self._message


class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def stream(self, **kwargs):
        text = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        block = types.SimpleNamespace(type="text", text=text)
        msg = types.SimpleNamespace(content=[block], stop_reason="end_turn")
        return _FakeStream(msg)


def test_retry_recovers():
    # 어휘 개수 범위(12~20) 검증으로 재시도를 유도한다.
    def vocab(n):
        return json.dumps({"items": [{"no": i, "word": "w", "meaning": "m"} for i in range(1, n + 1)]})
    bad = vocab(5)     # 5개 -> 범위 밖 -> 실패
    good = vocab(13)   # 13개 -> 통과

    client = ClaudeClient.__new__(ClaudeClient)    # __init__ 우회(가짜 주입)
    client.model = "test"
    client._client = types.SimpleNamespace(messages=_FakeMessages([bad, good]))

    result = client.structured(
        prompts.SYSTEM, "x", schemas.VocabSection, max_retries=1,
        extra_validate=lambda v: v.validate_count(12, 20),
    )
    assert len(result.items) == 13
    assert client._client.messages.calls == 2  # 1회 실패 후 1회 재시도
    print("PASS  검증 실패 후 재시도 복구")


# ---- 5. 렌더링 ------------------------------------------------------------
def test_render_html():
    from samples.sample_mock import mock_report
    html = render.render_html(mock_report(), footer_note="테스트", brand="테스트브랜드")
    assert "직독직해" in html and "made by 테스트브랜드" in html
    assert "핵심 어휘" in html and "해석 포인트(함축의미)" in html
    assert "서술형 출제 예상 문장" in html
    assert "The Value of Curiosity" in html
    print("PASS  HTML 렌더링")


# ---- 6. 강의컨셉 교재: 문장 분리 ------------------------------------------
def test_sentence_split():
    from src import sentences
    text = "Dr. Smith left at 3 p.m. He read 3.5 pages. Did he stop?"
    sents = sentences.split_sentences(text)
    # 약어(Dr.)·소수점(3.5)은 문장 끝으로 오인하지 않는다
    assert any(s.startswith("Dr. Smith") for s in sents)
    assert not any(s.strip() == "5 pages." for s in sents)
    assert sents[-1].endswith("?")
    print("PASS  문장 분리(약어·소수점 예외)")


# ---- 7. 강의컨셉 교재(필생보): 스키마 개수·문장수 검증 --------------------
def test_lecture_schema_and_counts():
    from src.lecture_schemas import Overview, SentenceAnalysis
    from samples.lecture_mock import mock_lecture_passage
    p = mock_lecture_passage()
    # 문장 분석 개수가 지문 문장 수와 같고, 각 문장 misread 가 있으면 통과
    p.analysis.validate_all(len(p.sentences))
    # 오역 위험 부분([[ ]] 빈칸 마크업)이 하나 이상 존재
    assert any("[[" in c.ko for s in p.analysis.sentences for c in s.chunks)
    # 글 내용 정리(글 순서) 블록이 존재
    assert len(p.overview.flow_blocks) >= 2
    # 개수가 다르면 실패
    try:
        p.analysis.validate_all(len(p.sentences) + 1)
        assert False, "문장 수 불일치가 통과하면 안 됨"
    except ValueError:
        pass
    # 문장마다 오답(misread) 1개 이상 존재
    assert all(s.misreads for s in p.analysis.sentences)
    # 재진술 사슬은 영어 표현만(한글 없음)
    import re as _re
    for c in p.overview.restatement_chains:
        for e in c.expressions:
            assert not _re.search(r"[가-힣]", e), f"재진술 표현에 한글: {e}"
    # 재진술 사슬 개수 범위(1~2) 위반 시 실패
    try:
        Overview.model_validate({**p.overview.model_dump(), "restatement_chains": []})
        assert False, "재진술 사슬 개수 위반이 통과하면 안 됨"
    except Exception:
        pass
    # stance/structure 는 정해진 라벨만 허용
    try:
        Overview.model_validate({**p.overview.model_dump(), "stance": "애매함"})
        assert False, "허용되지 않은 주장 라벨이 통과하면 안 됨"
    except Exception:
        pass
    print("PASS  강의컨셉(필생보) 스키마·개수 검증")


# ---- 8. 강의컨셉 교재(필생보): 학생용/강사용 HTML 렌더링 ------------------
def test_lecture_render_html():
    from samples.lecture_mock import mock_lecture_passage
    from src import lecture_render
    p = mock_lecture_passage(item_no="1")
    student = lecture_render.render_lecture_html([p], teacher=False)
    teacher = lecture_render.render_lecture_html([p], teacher=True)
    # 섹션(어휘 리스트 / 끊어읽기 / 오답 판별 / 글 정리·내용 정리)은 둘 다 있음
    for sec in ("어휘 리스트", "끊어읽기", "바르게 고치기", "글 정리", "재진술 사슬", "글 내용 정리"):
        assert sec in student and sec in teacher
    # O/X/△ 내용 판별 오답: 학생용엔 선택 칩(ox-pick), 강사용엔 정답 배지(ox-ans)
    assert "ox-pick" in student
    assert "ox-ans" in teacher
    # [[ ]] 마크업이 학생용엔 빈칸(ko-blank), 강사용엔 채워진 정답(ko-fill)으로
    assert "ko-blank" in student and "ko-fill" not in student
    assert "ko-fill" in teacher
    # 재진술: 강사용은 지문에 형광펜(mark) 표시
    assert "<mark" in teacher
    # [[ ]] 원문 마크업이 렌더 결과엔 남지 않아야 함
    assert "[[" not in student and "[[" not in teacher
    # 오답 해설(ox-why)·예측 정답(pred-a)은 강사용에만
    assert "ox-why" not in student and "ox-why" in teacher
    assert "pred-a" not in student and "pred-a" in teacher
    print("PASS  강의컨셉(필생보) 학생용/강사용 렌더링")


def run_all():
    test_clean_removes_noise()
    test_grammar_non_empty()
    test_vocab_count_range()
    test_retry_recovers()
    test_render_html()
    test_sentence_split()
    test_lecture_schema_and_counts()
    test_lecture_render_html()
    print("\n모든 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
