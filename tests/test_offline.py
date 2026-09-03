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
def test_wordtest_sections():
    """단어 시험지: 80개 → 영→한 40 / 한→영 40, 방향 교체 + 첫 글자 힌트."""
    from src import wordtest

    words = [{"no": i + 1, "word": f"word{i+1}", "meaning": f"뜻{i+1}"} for i in range(80)]
    secs = wordtest.build_sections(words, seed=1)
    assert [s["dir"] for s in secs] == ["en2ko", "ko2en"]
    assert len(secs[0]["questions"]) == 40 and len(secs[1]["questions"]) == 40
    # 원본 뒤쪽 절반(41~80)이 영→한, 앞쪽 절반(1~40)이 한→영 으로 방향이 바뀐다
    assert {q["prompt"] for q in secs[0]["questions"]} == {w["word"] for w in words[40:]}
    assert {q["answer"] for q in secs[1]["questions"]} == {w["word"] for w in words[:40]}
    assert all(q["hint"] == q["answer"][0] for q in secs[1]["questions"])
    assert [q["qno"] for q in secs[0]["questions"]] == list(range(1, 41))
    print("PASS  단어 시험지 문항 구성")


def test_render_html():
    from samples.sample_mock import mock_report
    html = render.render_html(mock_report(), footer_note="테스트", brand="테스트브랜드")
    assert "직독직해" in html and "made by 테스트브랜드" in html
    assert "핵심 어휘" in html and "해석 포인트(함축의미)" in html
    assert "서술형 출제 예상 문장" in html
    assert "The Value of Curiosity" in html
    print("PASS  HTML 렌더링")


def run_all():
    test_clean_removes_noise()
    test_grammar_non_empty()
    test_vocab_count_range()
    test_retry_recovers()
    test_render_html()
    test_wordtest_sections()
    print("\n모든 오프라인 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()
