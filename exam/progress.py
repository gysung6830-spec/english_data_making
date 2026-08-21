"""진행 상황 표시 — 오래 걸리는 생성 작업이 어디까지 왔는지 터미널에 알려 준다.

웹앱은 요청 하나로 수백~수천 번의 API 호출을 하므로, 브라우저는 그저 기다릴 뿐
'얼마나 남았는지' 알 수 없다. 그래서 서버 터미널(웹앱을 띄운 창)에 한 줄씩 찍는다.

    ▶ 지문 분석 20개 시작
    ✓ [ 3/ 20] 변형문제 · 지문 3 완료 | 경과 2분 12초 · 남은 예상 ~12분

- 지문 생성이 병렬이라 완료 순서는 뒤섞일 수 있다(번호는 '완료 개수' 기준).
- 남은 예상은 '지금까지 평균 소요 × 남은 개수'라 초반에는 부정확할 수 있다.
"""
from __future__ import annotations

import sys
import threading
import time


def human(sec: float) -> str:
    """초 → '2시간 12분' / '3분 5초' / '42초'."""
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}시간 {m}분"
    if m:
        return f"{m}분 {s}초"
    return f"{s}초"


class Progress:
    """완료 개수를 세어 경과·남은 예상 시간과 함께 한 줄씩 출력한다(스레드 안전)."""

    def __init__(self, total: int, stream=None, enabled: bool = True):
        self.total = max(0, int(total))
        self.done = 0
        self.t0 = time.time()
        self.enabled = enabled and self.total > 0
        self._stream = stream or sys.stderr
        self._lock = threading.Lock()

    def _write(self, line: str) -> None:
        if not self.enabled:
            return
        try:
            self._stream.write(line + "\n")
            self._stream.flush()
        except Exception:      # noqa: BLE001 — 출력 실패가 생성을 막으면 안 된다
            pass

    def note(self, message: str) -> None:
        """단계 안내(개수 증가 없음)."""
        self._write(f"  ▶ {message}")

    def step(self, message: str = "") -> None:
        """1건 완료 — 진행률·경과·남은 예상을 함께 찍는다."""
        if not self.enabled:
            return
        with self._lock:
            self.done += 1
            done, total = self.done, self.total
            elapsed = time.time() - self.t0
        width = len(str(total))
        eta = (elapsed / done) * (total - done) if done else 0
        tail = f"남은 예상 ~{human(eta)}" if done < total else "완료"
        self._write(f"  ✓ [{done:>{width}}/{total}] {message} "
                    f"| 경과 {human(elapsed)} · {tail}")

    def finish(self, message: str = "생성 완료") -> None:
        self._write(f"  ★ {message} · 총 소요 {human(time.time() - self.t0)}")


class NullProgress(Progress):
    """아무것도 출력하지 않는 진행 표시(데모·테스트용)."""

    def __init__(self) -> None:
        super().__init__(0, enabled=False)
