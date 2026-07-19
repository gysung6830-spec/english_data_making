"""입력 파일(붙여넣기 텍스트 외) → 영어 지문 본문 추출.

지원 형식:
  .txt            그대로 읽음(오프라인)
  .pdf            pdfplumber 로 텍스트 추출(오프라인). 스캔본(글자 없음)이면 안내.
  .jpg/.png/...   Claude 비전으로 지문을 읽어 텍스트화(ANTHROPIC_API_KEY 필요)

파일 1개 = 지문 1개로 취급한다.
"""
from __future__ import annotations

import re
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


# 한글 음절/자모, 원 번호, 워크시트 머리글/꼬리말 노이즈
_HANGUL = re.compile(r"[가-힣㄰-㆏ᄀ-ᇿ]")
_CIRCLED = re.compile(r"[①-⑳]")               # ①~⑳
_NOISE_LINE = re.compile(
    r"(\[EBS\]|\[Flow\s*Edu\]|flowedu|tistory|올림포스|한줄해석|좌지문|우해석"
    r"|정답\s*및\s*해설|^\s*Ch\.\s*\d)",
    re.IGNORECASE,
)
# 여러 지문이 한 파일에 있을 때의 경계(각 지문 끝의 출처 꼬리말)
_PASSAGE_SPLIT = re.compile(r"\[Flow\s*Edu\][^\n]*", re.IGNORECASE)


def _clean_pdf_text(segment: str) -> str:
    """한 지문 조각에서 한글·머리글·원번호를 걷어내고 영어 본문만 남긴다."""
    lines: list[str] = []
    for ln in segment.splitlines():
        if _NOISE_LINE.search(ln):
            continue
        ln = _CIRCLED.sub(" ", ln)
        ln = _HANGUL.sub("", ln)                        # 한글 제거(영어 지문엔 한글 없음)
        ln = ln.replace("­", "")                        # soft hyphen 등
        if len(re.sub(r"[^A-Za-z]", "", ln)) < 2:       # 영어가 거의 없으면 버림
            continue
        lines.append(ln.strip())
    text = re.sub(r"\s+", " ", " ".join(lines)).strip()
    text = re.sub(r"\s+([,.;:!?)])", r"\1", text)   # 구두점 앞 공백 제거(2단 병합 잔여)
    text = re.sub(r"([,;:])\1+", r"\1", text)         # 중복 구두점 정리
    text = re.sub(r",\s*\.", ".", text)               # ' , .' → '.'
    return text


def read_pdf_passages(path: str | Path) -> list[str]:
    """PDF에서 '영어 지문'들을 추출한다(여러 지문이면 각각 분리).

    - 영어+한글 2단, 여러 지문이 섞인 워크시트도 한글·머리글을 제거하고
      지문 단위로 나눠 돌려준다.
    - 글자 없는(스캔) PDF면 빈 리스트.
    """
    raw = extract.extract_raw_text(path)
    segments = _PASSAGE_SPLIT.split(raw) if _PASSAGE_SPLIT.search(raw) else [raw]
    passages: list[str] = []
    for seg in segments:
        body = _clean_pdf_text(seg)
        # 문제로 쓸 만한 최소 분량(영어 글자 수) 이상만 채택
        if len(re.sub(r"[^A-Za-z]", "", body)) >= 120:
            passages.append(body)
    return passages


def read_pdf(path: str | Path) -> str:
    """글자 PDF에서 지문 텍스트를 추출(정제). 여러 지문이면 이어 붙여 반환."""
    passages = read_pdf_passages(path)
    return " ".join(passages)


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

    if ext in IMAGE_EXTS:  # noqa: RET503
        if client is None:
            raise ValueError(
                f"'{p.name}': 사진 지문을 읽으려면 ANTHROPIC_API_KEY 가 필요합니다."
            )
        return read_image_text(client, p)

    raise ValueError(f"'{p.name}': 지원하지 않는 형식입니다(.txt/.pdf/.jpg/.png/.webp).")


def load_bodies(paths, client=None) -> list[tuple[str, str]]:
    """여러 파일 -> [(라벨, 지문본문)] 목록.

    보통 파일 1개 = 지문 1개지만, PDF 한 개에 지문이 여러 개면(예: EBS 워크시트)
    각각을 별도 지문으로 분리한다.
    """
    out: list[tuple[str, str]] = []
    for p in paths:
        p = Path(p)
        if p.suffix.lower() in PDF_EXTS:
            passages = read_pdf_passages(p)
            if not passages:
                raise ValueError(
                    f"'{p.name}': 글자가 없는(스캔본) PDF로 보입니다. "
                    "해당 페이지를 사진(JPG/PNG)으로 저장해 올려 주세요."
                )
            if len(passages) == 1:
                out.append((p.name, passages[0]))
            else:
                for i, body in enumerate(passages, 1):
                    out.append((f"{p.name} #{i}", body))
        else:
            body = load_body(p, client=client)
            if body and body.strip():
                out.append((p.name, body.strip()))
    return out
