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
    max_retries: int = 1
    use_batch_for_bulk: bool = True


@dataclass
class DesignCfg:
    footer_note: str = ""
    one_pdf_per_passage: bool = True
    brand: str = "은아 T"   # 직독직해 'made by ~' · 출제표 '~ tip' 에 넣는 이름(footer 와 무관)


@dataclass
class OutputsCfg:
    """어떤 PDF 를 생성할지 선택 (분석지 / 어휘 리스트 / 영단어 시험지)."""
    analysis: bool = True
    wordlist: bool = True
    quiz: bool = True


@dataclass
class QualityCfg:
    """무인(대량) 처리용 품질 세팅 — 오류 자동 복구 + 의심 결과 자동 플래그.

    사람이 전수 검수하기 어려운 환경에서: (1) 문제 파일만 조건부로 자동 복구하고,
    (2) 그래도 미심쩍은 소수만 '검수 권장'으로 표시해 사람이 그것만 보게 한다.
    """
    vision_fallback: bool = True   # 문제 파일에만 조건부로 PDF→이미지 비전 재추출
    auto_flag: bool = True         # 의심 결과를 자동으로 '검수 권장' 표시
    lower_start_ratio: float = 0.4  # 소문자로 시작하는 문장 비율 임계(조각 판정)
    min_sentences: int = 2         # 지문당 최소 문장 수(미만이면 추출 실패 의심)


@dataclass
class Config:
    model: str = "claude-opus-4-8"
    input_dir: Path = field(default_factory=lambda: ROOT / "input")
    output_dir: Path = field(default_factory=lambda: ROOT / "output")
    logs_dir: Path = field(default_factory=lambda: ROOT / "logs")
    vocab: VocabCfg = field(default_factory=VocabCfg)
    processing: ProcessingCfg = field(default_factory=ProcessingCfg)
    design: DesignCfg = field(default_factory=DesignCfg)
    outputs: OutputsCfg = field(default_factory=OutputsCfg)
    quality: QualityCfg = field(default_factory=QualityCfg)
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
    outputs = data.get("outputs", {})
    quality = data.get("quality", {})

    cfg = Config(
        model=data.get("model", "claude-opus-4-8"),
        input_dir=_resolve(ROOT, paths.get("input", "input")),
        output_dir=_resolve(ROOT, paths.get("output", "output")),
        logs_dir=_resolve(ROOT, paths.get("logs", "logs")),
        vocab=VocabCfg(min=int(vocab.get("min", 12)), max=int(vocab.get("max", 20))),
        processing=ProcessingCfg(
            parallel_sections=bool(proc.get("parallel_sections", True)),
            max_retries=int(proc.get("max_retries", 1)),
            use_batch_for_bulk=bool(proc.get("use_batch_for_bulk", True)),
        ),
        design=DesignCfg(
            footer_note=str(design.get("footer_note", "")),
            one_pdf_per_passage=bool(design.get("one_pdf_per_passage", True)),
            brand=str(design.get("brand", "은아 T")),
        ),
        outputs=OutputsCfg(
            analysis=bool(outputs.get("analysis", True)),
            wordlist=bool(outputs.get("wordlist", True)),
            quiz=bool(outputs.get("quiz", True)),
        ),
        quality=QualityCfg(
            vision_fallback=bool(quality.get("vision_fallback", True)),
            auto_flag=bool(quality.get("auto_flag", True)),
            lower_start_ratio=float(quality.get("lower_start_ratio", 0.4)),
            min_sentences=int(quality.get("min_sentences", 2)),
        ),
        api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
    )
    # 플레이스홀더 그대로면 키 없음 처리
    if cfg.api_key and "여기에" in cfg.api_key:
        cfg.api_key = None

    for d in (cfg.input_dir, cfg.output_dir, cfg.logs_dir):
        d.mkdir(parents=True, exist_ok=True)
    return cfg
