"""client.structured 의 '출력 잘림 자동 증량' 오프라인 테스트 (실제 API 없이).

실행: python -m tests.test_client
"""
from __future__ import annotations

from pydantic import BaseModel

from src.client import ClaudeClient, MAX_OUTPUT_TOKENS


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


class _M(BaseModel):
    x: int


class _Blk:
    type = "text"

    def __init__(self, t):
        self.text = t


class _Msg:
    def __init__(self, text, stop):
        self.content = [_Blk(text)]
        self.stop_reason = stop


class _Messages:
    def __init__(self, outer):
        self.o = outer

    def create(self, **req):
        self.o.calls.append(req["max_tokens"])
        # 처음 두 번은 max_tokens 로 잘린 불완전 JSON, 그 다음 완전한 JSON
        if len(self.o.calls) < 3:
            return _Msg('{"x": 1', "max_tokens")
        return _Msg('{"x": 42}', "end_turn")


class _Fake:
    def __init__(self):
        self.calls = []
        self.messages = _Messages(self)


def _client():
    c = ClaudeClient.__new__(ClaudeClient)
    c.model = "m"
    c._client = _Fake()
    return c


def test_truncation_autoscale():
    c = _client()
    obj = c.structured(system="s", prompt="p", model_cls=_M, max_tokens=16000, max_retries=1)
    _check("잘린 뒤 완전 응답 파싱 성공", obj.x == 42)
    _check("토큰 한도 증량", c._client.calls[0] < c._client.calls[1] < c._client.calls[2])
    _check("상한 초과 없음", all(t <= MAX_OUTPUT_TOKENS for t in c._client.calls))
    # 잘림 재시도는 스키마 위반 재시도 소진에서 제외 → max_retries=1 이어도 3회 호출됨
    _check("잘림 재시도는 소진 횟수 별도", len(c._client.calls) == 3)


def test_no_truncation_single_call():
    # 처음부터 완전 응답이면 한 번만 호출
    c = ClaudeClient.__new__(ClaudeClient)
    c.model = "m"

    class OneShot(_Fake):
        def __init__(self):
            super().__init__()
            self.messages = _Messages(self)

        class _Msgs:
            pass

    fake = _Fake()
    fake.messages.create = lambda **req: (fake.calls.append(req["max_tokens"]) or _Msg('{"x": 7}', "end_turn"))
    c._client = fake
    obj = c.structured(system="s", prompt="p", model_cls=_M, max_tokens=8000, max_retries=1)
    _check("정상 응답은 1회 호출", obj.x == 7 and len(fake.calls) == 1)


if __name__ == "__main__":
    test_truncation_autoscale()
    test_no_truncation_single_call()
    print("\nclient 출력 잘림 자동 증량 오프라인 테스트 통과 ✅")
