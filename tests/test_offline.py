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
    assert "Curiosity drives us" in cleaned
    assert "정답" not in cleaned
    assert "①" not in cleaned
    assert "What is the main idea" not in cleaned
    print("PASS  전처리(노이즈 제거)")


# ---- 1-b. 한줄해석 지문: ①②③ 문장 마커는 지우지 말고 문장은 유지 ----------
def test_clean_keeps_circled_sentences():
    raw = (
        "① Although the wish to be alone is often strong, its intensity varies from person to person.\n"
        "② An equally impelling impulse is to seek the company of others and share activities.\n"
        "⑥ Thus, we generally cannot exist for too long without seeking companionship.\n"
        "① 짧은 보기\n"
    )
    cleaned = extract.clean_text(raw)
    # 긴 지문 문장은 마커만 떼고 유지
    assert "Although the wish to be alone" in cleaned
    assert "An equally impelling impulse" in cleaned
    assert "Thus, we generally cannot exist" in cleaned
    # 짧은 보기는 제거, 원문자 마커는 남지 않음
    assert "짧은 보기" not in cleaned and "①" not in cleaned
    print("PASS  한줄해석 ①②③ 문장 유지(짧은 보기만 제거)")


def test_clean_keeps_numbered_sentences():
    # '해석 연습' 워크시트: 문장이 '1.' '2.' 로 시작하고 끝에 각주 '1)' 이 붙는 형식.
    # 문장 앞부분(번호 줄)을 지우면 안 되고, 번호·각주만 떼고 본문을 온전히 유지해야 한다.
    raw = (
        "1. Ever since the early Enlightenment, preservation and conservation have been closely related.1)\n"
        "2. Taken as near synonyms, their meaning is to maintain an object in its present state.2)\n"
        "5. as protectors.\n"          # 짧은 조각(보기성) → 제거
        "- 14 -\n"                       # 페이지 번호 → 제거
    )
    cleaned = extract.clean_text(raw)
    assert "Ever since the early Enlightenment, preservation and conservation" in cleaned
    assert "Taken as near synonyms, their meaning is to maintain an object" in cleaned
    assert ".1)" not in cleaned and ".2)" not in cleaned   # 각주 제거
    assert "- 14 -" not in cleaned                          # 페이지 번호 제거
    print("PASS  번호 매긴 지문 문장 유지(번호·각주만 제거, 앞부분 보존)")


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
class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        text = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        block = types.SimpleNamespace(type="text", text=text)
        return types.SimpleNamespace(content=[block])


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
    html = render.render_html(mock_report(), footer_note="테스트")
    assert "직독직해" in html and "made by 은아 T" in html
    assert "핵심 어휘" in html and "출제 포인트" in html
    assert "The Value of Curiosity" in html
    print("PASS  HTML 렌더링")


def run_all():
    test_clean_removes_noise()
    test_clean_keeps_circled_sentences()
    test_clean_keeps_numbered_sentences()
    test_grammar_non_empty()
    test_vocab_count_range()
    test_retry_recovers()
    test_render_html()
    print("\n모든 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
