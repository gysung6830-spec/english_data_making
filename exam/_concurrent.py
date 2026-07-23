"""API 호출 병렬 실행 헬퍼.

유형별 생성은 서로 독립적이고 I/O 대기(네트워크)가 대부분이므로, 스레드로 동시에
호출하면 전체 소요시간이 '가장 느린 한 호출' 수준으로 줄어든다.
(anthropic 클라이언트는 스레드 안전하고, 각 호출당 429/5xx 는 SDK 가 자동 재시도한다.)
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

# 동시 호출 상한(레이트리밋 여유). 필요시 조정.
MAX_WORKERS = 6


def run_parallel(tasks, max_workers: int = MAX_WORKERS) -> dict:
    """tasks: [(key, 무인자 콜러블)] → {key: 결과}. 하나라도 실패하면 그 원인으로 예외.

    key 순서와 무관하게 완료되는 대로 수거한다.
    """
    if not tasks:
        return {}
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
