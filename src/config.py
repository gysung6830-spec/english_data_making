"""설정 로드 (config.yaml + .env)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class VocabCfg:
    min: int = 12
    max: int = 20


@dataclass
class ProcessingCfg:
    parallel_sections: bool = True
    max_retries: int = 2                 # 검증 실패 시 재시도(무인 배치 신뢰도)
    use_batch_for_bulk: bool = True
    # 오류 감축 설정 — 사람이 일일이 검수하지 않는 배치 운영용
    thinking: bool = True                # 적응형 사고(추론) 켜기 → 정답 설계 오류↓
    effort: str = "high"                 # low/medium/high/xhigh — 높을수록 신중(비용↑)
    pdf_vision_fallback: bool = True      # 텍스트 없는 스캔 PDF만 Vision OCR로 조건부 처리


@dataclass
class DesignCfg:
    footer_note: str = ""
    one_pdf_per_passage: bool = True


@dataclass
class Config:
    model: str = "claude-opus-4-8"
    input_dir: Path = field(default_factory=lambda: ROOT / "input")
    output_dir: Path = field(default_factory=lambda: ROOT / "output")
    logs_dir: Path = field(default_factory=lambda: ROOT / "logs")
    vocab: VocabCfg = field(default_factory=VocabCfg)
    processing: ProcessingCfg = field(default_factory=ProcessingCfg)
    design: DesignCfg = field(default_factory=DesignCfg)
    api_key: str | None = None

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)


def _resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def load_config(path: str | Path | None = None) -> Config:
    """config.yaml 과 .env 를 읽어 Config 객체로 반환한다."""
    load_dotenv(ROOT / ".env")
    cfg_path = Path(path) if path else (ROOT / "config.yaml")
    data: dict[str, Any] = {}
    if cfg_path.exists():
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    paths = data.get("paths", {})
    vocab = data.get("vocab", {})
    proc = data.get("processing", {})
    design = data.get("design", {})

    cfg = Config(
        model=data.get("model", "claude-opus-4-8"),
        input_dir=_resolve(ROOT, paths.get("input", "input")),
        output_dir=_resolve(ROOT, paths.get("output", "output")),
        logs_dir=_resolve(ROOT, paths.get("logs", "logs")),
        vocab=VocabCfg(min=int(vocab.get("min", 12)), max=int(vocab.get("max", 20))),
        processing=ProcessingCfg(
            parallel_sections=bool(proc.get("parallel_sections", True)),
            max_retries=int(proc.get("max_retries", 2)),
            use_batch_for_bulk=bool(proc.get("use_batch_for_bulk", True)),
            thinking=bool(proc.get("thinking", True)),
            effort=str(proc.get("effort", "high")),
            pdf_vision_fallback=bool(proc.get("pdf_vision_fallback", True)),
        ),
        design=DesignCfg(
            footer_note=str(design.get("footer_note", "")),
            one_pdf_per_passage=bool(design.get("one_pdf_per_passage", True)),
        ),
        api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
    )
    # 플레이스홀더 그대로면 키 없음 처리
    if cfg.api_key and "여기에" in cfg.api_key:
        cfg.api_key = None

    for d in (cfg.input_dir, cfg.output_dir, cfg.logs_dir):
        d.mkdir(parents=True, exist_ok=True)
    return cfg
