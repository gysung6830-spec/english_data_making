"""PDF 비전 추출 — Claude 네이티브 PDF 비전으로 지문을 깨끗하게 뽑는다.

텍스트 추출(pdfplumber)이 만드는 오류(출처 누출·지문 병합·각주·이중언어 깨짐)를
원천 차단하기 위해, API 키가 있을 때 PDF 자체를 Claude 에게 보여 지문만 받는다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..core.models import Passage

_FMT = {"narrative", "dialogue", "notice", "chart"}

VISION_SYSTEM = (
    "당신은 학습지·시험지 PDF에서 '영어 지문'만 깨끗하게 추출하는 전문가다. "
    "교재명·출처·워터마크(WORKBOOK 등)·페이지번호·문장번호·각주·한글 해석은 모두 버리고, "
    "순수한 영어 지문 본문만 원문 그대로(철자·문장부호 유지) 담는다. 반드시 JSON 스키마로만 답한다."
)


class VisionPassage(BaseModel):
    text: str = Field(..., description=(
        "영어 지문 본문(원문 그대로). 교재·출처·문장번호(1. 2.)·각주(1) 2))·페이지번호·"
        "한글 해석은 절대 포함하지 말 것."))
    format: str = Field("narrative", description=(
        "지문 형식: 'narrative'(일반 글) / 'dialogue'(대화문) / 'notice'(안내문) / 'chart'(도표)"))


class VisionPassages(BaseModel):
    passages: list[VisionPassage] = Field(..., description="PDF 안 영어 지문들(각각 하나씩)")


def extract_passages_pdf_vision(client: Any, pdf_path: str | Path,
                                max_tokens: int = 16000) -> list[Passage]:
    """PDF를 Claude 비전으로 읽어 지문 리스트를 반환. 실패 시 예외 전파."""
    prompt = (
        "이 PDF에 담긴 '영어 지문'들을 각각 하나씩 분리해 추출하라.\n"
        "- 교재명·출처·저작권·워터마크(WORKBOOK, 평가원 등), 페이지번호(- 14 -), "
        "문장 앞 번호(1. 2. 3.), 각주 표시(1) 2)), 한글 해석/지시문은 모두 제외한다.\n"
        "- 영어 지문 본문만 원문 그대로(철자·문장부호 유지) 담는다.\n"
        "- 지문이 여러 개면 passages 배열에 각각 넣는다(한 지문을 쪼개거나 두 지문을 "
        "합치지 말 것).\n"
        "- 각 지문 형식을 narrative/dialogue/notice/chart 로 분류한다."
    )
    out = client.structured(VISION_SYSTEM, prompt, VisionPassages,
                            max_tokens=max_tokens, image_path=str(pdf_path))
    passages: list[Passage] = []
    ci = di = 0
    for p in out.passages:
        text = (p.text or "").strip()
        if len(text.split()) < 12:          # 너무 짧은 조각은 버림
            continue
        fmt = p.format if p.format in _FMT else "narrative"
        if fmt == "dialogue":
            di += 1; pid = f"d{di}"
        else:
            ci += 1; pid = f"p{ci}"
        passages.append(Passage(id=pid, text=text, format_type=fmt))
    return passages
