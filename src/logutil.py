"""로깅 및 처리 결과 기록 (성공/실패 파일 구분)."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(logs_dir: Path) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("english_analyzer")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = logging.FileHandler(logs_dir / "run.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    return logger


class Manifest:
    """처리된 파일 / 실패한 파일을 JSONL 로 기록한다."""

    def __init__(self, logs_dir: Path):
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.processed_path = logs_dir / "processed.jsonl"
        self.failed_path = logs_dir / "failed.jsonl"

    def record_success(self, source: str, output: str, meta: dict | None = None) -> None:
        self._append(
            self.processed_path,
            {"time": datetime.now().isoformat(timespec="seconds"),
             "source": source, "output": output, **(meta or {})},
        )

    def record_failure(self, source: str, error: str, stage: str = "") -> None:
        self._append(
            self.failed_path,
            {"time": datetime.now().isoformat(timespec="seconds"),
             "source": source, "stage": stage, "error": error},
        )

    @staticmethod
    def _append(path: Path, obj: dict) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
