"""입력 파일(붙여넣기 텍스트 외) → 영어 지문 본문 추출.

지원 형식:
  .txt            그대로 읽음(오프라인)
  .pdf            pdfplumber 로 텍스트 추출(오프라인). 스캔본(글자 없음)이면 안내.
  .jpg/.png/...   Claude 비전으로 지문을 읽어 텍스트화(ANTHROPIC_API_KEY 필요)

파일 1개 = 지문 1개로 취급한다.
"""
from __future__ import annotations

from pathlib import Path

from src import extract  # 기존 분석 도구의 PDF/이미지 유틸 재사용
from .schemas import PassageText

TXT_EXTS = {".txt"}
PDF_EXTS = {".pdf"}
IMAGE_EXTS = set(extract.IMAGE_EXTS)
SUPPORTED_EXTS = TXT_EXTS | PDF_EXTS | IMAGE_EXTS

_VISION_SYSTEM = (
    "You are a precise OCR assistant. You transcribe English reading passages "
    "from images exactly as written."
)
_VISION_PROMPT = (
    "이 이미지에 있는 '영어 지문 본문'만 정확히 그대로 옮겨 적으세요. "
    "문항 번호·보기·발문·정답·해설·한글 해석은 모두 제외하고, 지문 문장만 원문 그대로 "
    "이어서 반환하세요(줄바꿈은 공백으로)."
)


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTS


def read_txt(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def read_pdf(path: str | Path) -> str:
    """글자 PDF에서 지문 텍스트를 추출(1차 정제 포함)."""
    return extract.extract_passage_text(path)


def read_image_text(client, path: str | Path, max_retries: int = 1) -> str:
    """사진/캡처에서 Claude 비전으로 지문 본문을 옮겨 적는다."""
    out: PassageText = client.structured(
        system=_VISION_SYSTEM,
        prompt=_VISION_PROMPT,
        model_cls=PassageText,
        max_tokens=2000,
        max_retries=max_retries,
        image_path=str(path),
    )
    return out.text.strip()


def load_body(path: str | Path, client=None) -> str:
    """파일 1개 -> 지문 본문 텍스트."""
    p = Path(path)
    ext = p.suffix.lower()

    if ext in TXT_EXTS:
        return read_txt(p)

    if ext in PDF_EXTS:
        text = read_pdf(p)
        if extract.looks_empty(text):
            raise ValueError(
                f"'{p.name}': 글자가 없는(스캔본) PDF로 보입니다. 해당 페이지를 "
                "사진(JPG/PNG)으로 저장해 올려 주세요."
            )
        return text

    if ext in IMAGE_EXTS:
        if client is None:
            raise ValueError(
                f"'{p.name}': 사진 지문을 읽으려면 ANTHROPIC_API_KEY 가 필요합니다."
            )
        return read_image_text(client, p)

    raise ValueError(f"'{p.name}': 지원하지 않는 형식입니다(.txt/.pdf/.jpg/.png/.webp).")


def load_bodies(paths, client=None) -> list[tuple[str, str]]:
    """여러 파일 -> [(파일명, 지문본문)] 목록. 파일 1개 = 지문 1개."""
    out: list[tuple[str, str]] = []
    for p in paths:
        body = load_body(p, client=client)
        if body and body.strip():
            out.append((Path(p).name, body.strip()))
    return out
