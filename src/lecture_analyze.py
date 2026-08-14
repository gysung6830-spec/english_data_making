"""한 지문 -> '강의컨셉 교재(필생보 스타일)' 분석 (LecturePassage 조립).

2단계 LLM 호출: (1) 지문 전체 개관 → (2) 문장별 분석(비유를 공유).
"""
from __future__ import annotations

from pathlib import Path

from . import lecture_prompts, pipeline, schemas, sentences
from .client import ClaudeClient
from .config import Config
from .lecture_schemas import (LecturePassage, LectureSentence, Overview,
                             SentenceAnalysis)


def analyze_lecture_passage(
    client: ClaudeClient, cfg: Config, extraction: schemas.Extraction
) -> LecturePassage:
    """추출된 본문 -> 문장 분리(코드) -> 개관+문장분석(LLM) -> LecturePassage."""
    title = extraction.title
    sents = [
        LectureSentence(id=i, text=t)
        for i, t in enumerate(sentences.split_passage(extraction.paragraphs), start=1)
    ]
    if not sents:
        raise ValueError("지문에서 문장을 분리하지 못했습니다.")
    n = len(sents)
    r = cfg.processing.max_retries

    # 1차: 지문 전체 개관 (예측 정답 + 비유)
    overview: Overview = client.structured(
        system=lecture_prompts.SYSTEM,
        prompt=lecture_prompts.overview_prompt(title, sents),
        model_cls=Overview,
        max_tokens=8000,
        max_retries=r,
    )

    # 2차: 어휘 + 문장별 끊어읽기(빈칸)/내용 객관식
    #   ⑤ 핵심 문법을 넘겨 ③ 어법 칩과 역할 분담(중복 배제)하도록 함
    kg_point = getattr(getattr(overview, "key_grammar", None), "point", "") or ""
    analysis: SentenceAnalysis = client.structured(
        system=lecture_prompts.SYSTEM,
        prompt=lecture_prompts.sentence_prompt(title, sents, key_grammar_point=kg_point),
        model_cls=SentenceAnalysis,
        max_tokens=24000,
        max_retries=r,
        extra_validate=lambda a: a.validate_all(n),
    )

    return LecturePassage(
        title=title,
        source=extraction.source,
        item_no=extraction.item_no,
        sentences=sents,
        overview=overview,
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
