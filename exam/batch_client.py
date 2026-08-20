"""Batch API 클라이언트 — 같은 요청을 '모아서' 보내 비용을 절반으로 낮춘다.

Anthropic Batch API 는 "급하지 않으니 여유 있을 때 처리해도 된다"고 양보하는 대신
**정가의 50%** 로 처리해 준다(모델·프롬프트가 같으므로 품질은 완전히 동일하다).
대신 즉시 응답이 아니라 최대 24시간 안에 끝난다(실제로는 보통 훨씬 빠르다).

설계 — 생성기 코드는 그대로 두고 '클라이언트만' 바꾼다:
  · 파이프라인은 이미 지문·유형을 여러 스레드로 동시에 만든다.
  · 그 스레드들이 부르는 structured() 를 곧바로 보내지 않고 잠깐(window) 모은다.
  · 모인 요청을 한 배치로 제출하고, 끝나면 각 스레드에 결과를 돌려준다.
따라서 generators/*.py, gen2.py, pipeline.py 는 전혀 수정할 필요가 없다.

검증 실패 시 재시도는 기존과 같다(지시문을 덧붙여 다음 배치에 다시 넣는다).
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from pydantic import ValidationError

from src.client import (
    ClaudeClient as _BaseClient,
    DEFAULT_MAX_TOKENS,
    build_request,
    extract_text,
    parse_response_text,
)

# 요청을 모으는 시간(초). 이 시간 안에 도착한 요청들이 한 배치로 묶인다.
DEFAULT_WINDOW = 4.0
# 배치 상태 확인 간격(초).
DEFAULT_POLL = 15.0


class _Slot:
    """요청 한 건의 결과를 기다리는 자리."""

    __slots__ = ("event", "text", "error")

    def __init__(self) -> None:
        self.event = threading.Event()
        self.text: str | None = None
        self.error: Exception | None = None

    def set_ok(self, text: str) -> None:
        self.text = text
        self.event.set()

    def set_err(self, err: Exception) -> None:
        self.error = err
        self.event.set()

    def wait(self) -> str:
        self.event.wait()
        if self.error is not None:
            raise self.error
        return self.text or ""


class BatchingClaudeClient(_BaseClient):
    """structured() 호출을 모아 Batch API 로 보내는 클라이언트(정가의 50%).

    쓰는 쪽 입장에서는 기존 ClaudeClient 와 완전히 같다(같은 메서드·같은 반환).
    """

    def __init__(self, *args, window: float = DEFAULT_WINDOW,
                 poll: float = DEFAULT_POLL, progress=None, logger=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._window = max(0.5, float(window))
        self._poll = max(1.0, float(poll))
        self._progress = progress
        self._logger = logger
        self._lock = threading.Lock()
        self._pending: list[tuple[str, dict, _Slot]] = []
        self._flusher: threading.Thread | None = None
        self._batch_no = 0

    # -- 공개 API (기존과 동일) ------------------------------------------
    def structured(self, system: str, prompt: str, model_cls,
                   max_tokens: int = DEFAULT_MAX_TOKENS, max_retries: int = 1,
                   extra_validate=None, image_path: str | Path | None = None,
                   cache_prefix: str | None = None):
        """동기 클라이언트와 같은 계약. 내부적으로만 배치로 처리한다."""
        cur_prompt = prompt
        last_err: Exception | None = None
        for _attempt in range(max_retries + 1):
            req = build_request(self.model, system, cur_prompt, model_cls, max_tokens,
                                image_path=image_path, cache_prefix=cache_prefix,
                                thinking=self.thinking, effort=self.effort)
            text = self._submit(req)
            try:
                obj = parse_response_text(text, model_cls)
                if extra_validate:
                    extra_validate(obj)
                return obj
            except (ValidationError, ValueError, json.JSONDecodeError) as e:
                last_err = e
                cur_prompt = (
                    prompt
                    + f"\n\n[주의] 직전 응답이 조건을 위반했습니다: {e}\n"
                    "이번에는 스키마와 개수 조건을 반드시 지켜 다시 작성하세요."
                )
        raise RuntimeError(f"검증 실패(재시도 소진): {last_err}")

    # -- 내부: 모으기 → 제출 → 나눠주기 ----------------------------------
    def _submit(self, req: dict) -> str:
        """요청을 대기열에 넣고, 배치 결과가 올 때까지 이 스레드를 재운다."""
        slot = _Slot()
        with self._lock:
            self._pending.append((f"r{uuid.uuid4().hex[:16]}", req, slot))
            if self._flusher is None or not self._flusher.is_alive():
                self._flusher = threading.Thread(target=self._flush_loop, daemon=True)
                self._flusher.start()
        return slot.wait()

    def _flush_loop(self) -> None:
        """window 만큼 기다려 요청을 모은 뒤 배치로 보낸다. 대기열이 비면 종료."""
        while True:
            time.sleep(self._window)
            with self._lock:
                if not self._pending:
                    self._flusher = None
                    return
                items, self._pending = self._pending, []
                self._batch_no += 1
                no = self._batch_no
            try:
                self._run_batch(no, items)
            except Exception as e:      # noqa: BLE001 — 배치 실패는 각 요청에 전달
                for _cid, _req, slot in items:
                    slot.set_err(e)

    def _run_batch(self, no: int, items: list[tuple[str, dict, _Slot]]) -> None:
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request

        note = f"배치 #{no} 제출 — {len(items)}건 (정가의 50%)"
        if self._progress:
            self._progress.note(note)
        if self._logger:
            self._logger.info(note)

        batch = self.raw.messages.batches.create(
            requests=[Request(custom_id=cid,
                              params=MessageCreateParamsNonStreaming(**req))
                      for cid, req, _slot in items])
        while True:                                  # 끝날 때까지 상태 확인
            b = self.raw.messages.batches.retrieve(batch.id)
            if getattr(b, "processing_status", None) == "ended":
                break
            time.sleep(self._poll)

        by_id = {cid: slot for cid, _req, slot in items}
        got = 0
        for result in self.raw.messages.batches.results(batch.id):
            slot = by_id.pop(result.custom_id, None)
            if slot is None:
                continue
            kind = result.result.type
            if kind == "succeeded":
                slot.set_ok(extract_text(result.result.message))
                got += 1
            else:                                    # errored·canceled·expired
                slot.set_err(RuntimeError(f"배치 요청 실패({kind})"))
        for slot in by_id.values():                  # 결과가 안 온 건(이론상 없음)
            slot.set_err(RuntimeError("배치 결과가 오지 않았습니다"))

        done = f"배치 #{no} 완료 — 성공 {got}/{len(items)}"
        if self._progress:
            self._progress.note(done)
        if self._logger:
            self._logger.info(done)
