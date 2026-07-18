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


# ---- 2. 스키마 검증: 문법 10개 강제 ----------------------------------------
def test_grammar_exactly_10():
    items = [{"no": i, "point": "p", "example": "e", "explanation": "x"} for i in range(1, 10)]
    try:
        schemas.GrammarSection.model_validate({"items": items})
        assert False, "9개인데 통과하면 안 됨"
    except Exception:
        pass
    items.append({"no": 10, "point": "p", "example": "e", "explanation": "x"})
    schemas.GrammarSection.model_validate({"items": items})  # 10개면 통과
    print("PASS  문법 정확히 10개 검증")


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
    good_items = [{"no": i, "point": "p", "example": "e", "explanation": "x"}
                  for i in range(1, 11)]
    bad = json.dumps({"items": good_items[:9]})    # 9개 -> 실패
    good = json.dumps({"items": good_items})       # 10개 -> 성공

    client = ClaudeClient.__new__(ClaudeClient)    # __init__ 우회(가짜 주입)
    client.model = "test"
    client._client = types.SimpleNamespace(messages=_FakeMessages([bad, good]))

    result = client.structured(prompts.SYSTEM, "x", schemas.GrammarSection, max_retries=1)
    assert len(result.items) == 10
    assert client._client.messages.calls == 2  # 1회 실패 후 1회 재시도
    print("PASS  검증 실패 후 재시도 복구")


# ---- 5. 렌더링 ------------------------------------------------------------
def test_render_html():
    from samples.sample_mock import mock_report
    html = render.render_html(mock_report(), footer_note="테스트")
    assert "직독직해" in html and "핵심 문법 TOP 10" in html
    assert "The Value of Curiosity" in html
    print("PASS  HTML 렌더링")


def run_all():
    test_clean_removes_noise()
    test_grammar_exactly_10()
    test_vocab_count_range()
    test_retry_recovers()
    test_render_html()
    print("\n모든 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
