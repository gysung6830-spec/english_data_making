"""입력 파싱: PDF / 사진(OCR) / HWP / TXT → 텍스트 → 지문 단위 분리 (§3-A-0).

어떤 입력이든 먼저 텍스트로 변환한 뒤 Passage[] 로 만든다.
대화문·안내문·도표는 형식 신호로 함께 식별한다.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..core.models import FormatType, Passage

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


# ---------------------------------------------------------------------------
# 파일 → 원문 텍스트
# ---------------------------------------------------------------------------
def _read_pdf(path: Path) -> str:
    import pdfplumber
    parts: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _read_image_ocr(path: Path) -> str:
    """사진/스캔 → OCR. pytesseract 없으면 안내 메시지와 함께 빈 문자열."""
    try:
        import pytesseract
        from PIL import Image
    except Exception:  # pragma: no cover - 선택 의존성
        return ""
    return pytesseract.image_to_string(Image.open(str(path)), lang="eng+kor")


def _read_hwp(path: Path) -> str:
    """HWP 본문 추출(best-effort). 미설치 시 빈 문자열."""
    try:  # pragma: no cover - 선택 의존성
        import olefile  # noqa: F401
        import hwp5  # noqa: F401
    except Exception:
        return ""
    try:  # pragma: no cover
        from hwp5.hwp5txt import main as _  # noqa: F401
    except Exception:
        return ""
    return ""  # 실제 변환은 환경에 hwp5 CLI 가 있을 때 별도 처리


def read_text(path: str | Path) -> str:
    """입력 파일 → 원문 텍스트(형식 유지)."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        txt = _read_pdf(p)
        if _looks_empty(txt):          # 스캔본 → OCR 재시도
            # PDF 를 이미지로 렌더해 OCR 하는 것은 무거우므로 여기선 원문만 반환.
            return txt
        return txt
    if ext in IMAGE_EXTS:
        return _read_image_ocr(p)
    if ext == ".hwp":
        return _read_hwp(p)
    if ext in {".txt", ".md"}:
        return p.read_text(encoding="utf-8", errors="ignore")
    # 알 수 없는 확장자는 텍스트로 시도
    return p.read_text(encoding="utf-8", errors="ignore")


def _looks_empty(text: str) -> bool:
    return len(re.sub(r"[^A-Za-z]", "", text)) < 40


# ---------------------------------------------------------------------------
# 형식 유형 판별 (§3-A-1 마지막 행)
# ---------------------------------------------------------------------------
_SPEAKER_RE = re.compile(r"^\s*([A-Z][a-zA-Z]{0,14}|[MWＭＷ]|남|여|Man|Woman)\s*:\s+", re.M)
_NOTICE_HINT = re.compile(r"\b(When|Where|Date|Time|Location|Admission|Notice|Highlights|Notes|Details|Registration)\b", re.I)
_CHART_HINT = re.compile(r"(\d+\s*%|percent|the (?:above|following) (?:graph|chart|table)|그래프|도표|위 표)", re.I)


def detect_format(text: str) -> tuple[FormatType, list[str]]:
    """서술문 / 대화문 / 안내문 / 도표 판별. (format_type, speakers)."""
    speakers = sorted({m.group(1).strip() for m in _SPEAKER_RE.finditer(text)})
    if len(speakers) >= 2 or (speakers and _SPEAKER_RE.findall(text).__len__() >= 3):
        return "dialogue", speakers
    if len(_CHART_HINT.findall(text)) >= 2:
        return "chart", []
    if len(_NOTICE_HINT.findall(text)) >= 3:
        return "notice", []
    return "narrative", []


# ---------------------------------------------------------------------------
# 지문 경계 분리
# ---------------------------------------------------------------------------
_PASSAGE_MARK = re.compile(r"^\s*(?:지문\s*\d+|passage\s*\d+|\[?\s*\d+\s*\]?)\s*[.:)]?\s*$", re.I)


def split_passages(text: str, source_file: str | None = None,
                   id_prefix: str = "p") -> list[Passage]:
    """빈 줄·번호·제목 패턴으로 여러 지문을 나눈다.

    - '지문 1' / 'Passage 2' / '[1]' 같은 명시적 구분선을 우선 사용.
    - 없으면 2줄 이상 빈 줄을 경계로 삼는다.
    """
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []

    # 1) 명시적 마커로 분할
    chunks: list[str] = []
    if _has_explicit_markers(text):
        cur: list[str] = []
        for line in text.split("\n"):
            if _PASSAGE_MARK.match(line):
                if cur and "".join(cur).strip():
                    chunks.append("\n".join(cur).strip())
                cur = []
            else:
                cur.append(line)
        if cur and "".join(cur).strip():
            chunks.append("\n".join(cur).strip())
    else:
        # 2) 빈 줄(2줄+)로 분할
        chunks = [c.strip() for c in re.split(r"\n\s*\n\s*\n?", text) if c.strip()]

    # 너무 짧은 조각은 앞 지문에 병합
    merged = _merge_short(chunks)

    passages: list[Passage] = []
    for i, body in enumerate(merged, 1):
        fmt, speakers = detect_format(body)
        passages.append(Passage(
            id=f"{id_prefix}{i}" if fmt != "dialogue" else f"d{i}",
            text=body,
            format_type=fmt,
            speakers=speakers,
            source_file=source_file,
        ))
    return passages


def _has_explicit_markers(text: str) -> bool:
    return sum(1 for line in text.split("\n") if _PASSAGE_MARK.match(line)) >= 2


def _merge_short(chunks: list[str], min_words: int = 25) -> list[str]:
    out: list[str] = []
    for c in chunks:
        if out and len(c.split()) < min_words:
            out[-1] = out[-1] + "\n" + c
        else:
            out.append(c)
    return out


def load_passages(paths: list[str | Path]) -> list[Passage]:
    """여러 입력 파일 → 전체 Passage[] (id 재부여)."""
    all_p: list[Passage] = []
    for path in paths:
        raw = read_text(path)
        ps = split_passages(raw, source_file=str(path))
        all_p.extend(ps)
    # 전역 id 재부여(형식 접두 유지)
    n_narr = n_dlg = 0
    for p in all_p:
        if p.format_type == "dialogue":
            n_dlg += 1
            p.id = f"d{n_dlg}"
        else:
            n_narr += 1
            p.id = f"p{n_narr}"
    return all_p
