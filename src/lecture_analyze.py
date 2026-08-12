"""한 지문 -> '강의컨셉 교재' 5개 섹션 분석 (LecturePassage 조립)."""
from __future__ import annotations

from pathlib import Path

from . import lecture_prompts, pipeline, schemas, sentences
from .client import ClaudeClient
from .config import Config
from .lecture_schemas import LectureAnalysis, LecturePassage, LectureSentence


def analyze_lecture_passage(
    client: ClaudeClient, cfg: Config, extraction: schemas.Extraction
) -> LecturePassage:
    """추출된 본문 -> 문장 분리(코드) -> 5개 섹션(LLM) -> LecturePassage."""
    title = extraction.title
    sents = [
        LectureSentence(id=i, text=t)
        for i, t in enumerate(sentences.split_passage(extraction.paragraphs), start=1)
    ]
    if not sents:
        raise ValueError("지문에서 문장을 분리하지 못했습니다.")
    n = len(sents)

    analysis: LectureAnalysis = client.structured(
        system=lecture_prompts.SYSTEM,
        prompt=lecture_prompts.analysis_prompt(title, sents),
        model_cls=LectureAnalysis,
        max_tokens=16000,
        max_retries=cfg.processing.max_retries,
        extra_validate=lambda a: a.validate_refs(n),
    )
    return LecturePassage(
        title=title,
        source=extraction.source,
        item_no=extraction.item_no,
        sentences=sents,
        analysis=analysis,
    )


def build_lecture_passages_for_pdf(
    client: ClaudeClient, cfg: Config, src: Path, focus_items: str = ""
) -> list[LecturePassage]:
    """한 파일(PDF/사진/HWP) -> 여러 LecturePassage(지문 순서대로).

    본문 추출 단계는 기존 분석 파이프라인과 동일한 로직을 공유한다.
    """
    pset = pipeline.extract_passage_set(client, cfg, src, focus_items)
    return [analyze_lecture_passage(client, cfg, ex) for ex in pset.passages]
