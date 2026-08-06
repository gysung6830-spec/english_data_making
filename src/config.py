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
    max_retries: int = 2
    use_batch_for_bulk: bool = True


@dataclass
class ExtractionCfg:
    """PDF 지문 추출 방식.

    pdf_mode:
      - "vision": PDF 를 페이지 이미지로 렌더해 Claude 비전으로 읽음(정확도 최고, 비용 큼)
      - "text"  : pdfplumber 텍스트 추출(빠르고 저렴하나 표/다단에서 부정확할 수 있음)
      - "auto"  : text 로 먼저 시도하고, 비어있거나 깨져 보이면 vision 으로 보완
                  (무인 배치 권장값: 정상 파일은 저렴한 텍스트, 문제 파일만 비전)
    """
    pdf_mode: str = "auto"
    dpi: int = 150


@dataclass
class DesignCfg:
    footer_note: str = ""
    one_pdf_per_passage: bool = True
    brand: str = ""   # 직독직해 'made by ~' 에 넣는 브랜드 이름(footer 와 무관, 비우면 미표시)


@dataclass
class OutputsCfg:
    """어떤 PDF 를 생성할지 선택 (분석지 / 어휘 리스트 / 영단어 시험지)."""
    analysis: bool = True
    wordlist: bool = False      # (사용 안 함) 직독직해 단어 기반 어휘 리스트
    quiz: bool = False          # (사용 안 함) 직독직해 단어 기반 영단어 시험지
    student: bool = False       # 학생용(정답 빈칸) 분석지
    vocablist: bool = True      # 핵심 어휘 리스트(유의어·반의어)
    vocabtest: bool = True      # 핵심 어휘 시험지(뜻쓰기+유의어/반의어 줄긋기)


@dataclass
class Config:
    model: str = "claude-opus-4-8"
    input_dir: Path = field(default_factory=lambda: ROOT / "input")
    output_dir: Path = field(default_factory=lambda: ROOT / "output")
    logs_dir: Path = field(default_factory=lambda: ROOT / "logs")
    vocab: VocabCfg = field(default_factory=VocabCfg)
    processing: ProcessingCfg = field(default_factory=ProcessingCfg)
    extraction: ExtractionCfg = field(default_factory=ExtractionCfg)
    design: DesignCfg = field(default_factory=DesignCfg)
    outputs: OutputsCfg = field(default_factory=OutputsCfg)
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
    extraction = data.get("extraction", {})
    design = data.get("design", {})
    outputs = data.get("outputs", {})

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
        ),
        extraction=ExtractionCfg(
            pdf_mode=str(extraction.get("pdf_mode", "auto")).lower(),
            dpi=int(extraction.get("dpi", 150)),
        ),
        design=DesignCfg(
            footer_note=str(design.get("footer_note", "")),
            one_pdf_per_passage=bool(design.get("one_pdf_per_passage", True)),
            brand=str(design.get("brand", "")),
        ),
        outputs=OutputsCfg(
            analysis=bool(outputs.get("analysis", True)),
            wordlist=bool(outputs.get("wordlist", True)),
            quiz=bool(outputs.get("quiz", True)),
            student=bool(outputs.get("student", False)),
            vocablist=bool(outputs.get("vocablist", True)),
            vocabtest=bool(outputs.get("vocabtest", True)),
        ),
        api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
    )
    # 플레이스홀더 그대로면 키 없음 처리
    if cfg.api_key and "여기에" in cfg.api_key:
        cfg.api_key = None

    for d in (cfg.input_dir, cfg.output_dir, cfg.logs_dir):
        d.mkdir(parents=True, exist_ok=True)
    return cfg
