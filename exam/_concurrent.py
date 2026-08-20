"""API 호출 병렬 실행 헬퍼.

유형별 생성은 서로 독립적이고 I/O 대기(네트워크)가 대부분이므로, 스레드로 동시에
호출하면 전체 소요시간이 '가장 느린 한 호출' 수준으로 줄어든다.
(anthropic 클라이언트는 스레드 안전하고, 각 호출당 429/5xx 는 SDK 가 자동 재시도한다.)
"""
from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, "") or default))
    except ValueError:
        return default


# 실제로 동시에 나가는 API 호출 수의 '전체 상한'.
# 지문·유형·회차를 겹쳐 돌려도 이 수를 넘지 않으므로 레이트리밋에 안전하다.
# 환경변수 EXAM_CONCURRENCY 로 조정(요금제 한도가 넉넉하면 12~16 권장).
API_CONCURRENCY = _env_int("EXAM_CONCURRENCY", 8)
_API_GATE = threading.BoundedSemaphore(API_CONCURRENCY)

# 스레드 풀 크기(대기 슬롯). 실제 동시 호출은 위 _API_GATE 가 통제하므로 넉넉히 잡는다.
MAX_WORKERS = _env_int("EXAM_MAX_WORKERS", max(API_CONCURRENCY * 2, 12))


@contextmanager
def api_slot():
    """API 호출 1건이 실제로 나가는 동안만 잡는 슬롯(전체 동시 호출 상한 적용)."""
    _API_GATE.acquire()
    try:
        yield
    finally:
        _API_GATE.release()


def set_concurrency(n: int) -> int:
    """동시 호출 상한을 설정값으로 바꾼다(환경변수가 지정돼 있으면 그쪽이 우선).

    생성 시작 전에 한 번 부르는 용도. 반환값은 실제 적용된 상한.
    """
    global API_CONCURRENCY, MAX_WORKERS, _API_GATE
    if os.environ.get("EXAM_CONCURRENCY"):      # 환경변수 우선(운영 중 임시 조정)
        return API_CONCURRENCY
    n = max(1, int(n or 1))
    if n != API_CONCURRENCY:
        API_CONCURRENCY = n
        _API_GATE = threading.BoundedSemaphore(n)
        MAX_WORKERS = max(n * 2, 12)
    return API_CONCURRENCY


def run_parallel(tasks, max_workers: int | None = None) -> dict:
    """tasks: [(key, 무인자 콜러블)] → {key: 결과}. 하나라도 실패하면 그 원인으로 예외.

    key 순서와 무관하게 완료되는 대로 수거한다.
    """
    if not tasks:
        return {}
    if max_workers is None:      # 정의 시점이 아니라 '호출 시점'의 설정을 따른다
        max_workers = MAX_WORKERS
    results: dict = {}
    first_err: tuple | None = None
    with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as ex:
        futs = {ex.submit(fn): key for key, fn in tasks}
        for fut in as_completed(futs):
            key = futs[fut]
            try:
                results[key] = fut.result()
            except Exception as e:  # noqa: BLE001 — 첫 오류를 컨텍스트와 함께 올린다
                if first_err is None:
                    first_err = (key, e)
    if first_err is not None:
        key, e = first_err
        raise RuntimeError(f"[{key}] 생성 실패: {e}") from e
    return results
