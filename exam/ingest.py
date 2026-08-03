"""입력 파일(붙여넣기 텍스트 외) → 영어 지문 본문 추출.

지원 형식:
  .txt            그대로 읽음(오프라인)
  .pdf            pdfplumber 로 텍스트 추출(오프라인). 스캔본(글자 없음)이면 안내.
  .hwp/.hwpx      한글 파일에서 텍스트 추출(오프라인). PDF와 동일하게 정제·분리.
  .jpg/.png/...   Claude 비전으로 지문을 읽어 텍스트화(ANTHROPIC_API_KEY 필요)

파일 1개 = 지문 1개로 취급한다(단, 한 파일에 지문이 여럿이면 각각 분리).
"""
from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

from src import extract  # 기존 분석 도구의 PDF/이미지 유틸 재사용
from . import hwp as _hwp
from .schemas import PassageText

TXT_EXTS = {".txt"}
PDF_EXTS = {".pdf"}
HWP_EXTS = {".hwp", ".hwpx"}
IMAGE_EXTS = set(extract.IMAGE_EXTS)
SUPPORTED_EXTS = TXT_EXTS | PDF_EXTS | HWP_EXTS | IMAGE_EXTS

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
    r"|정답\s*및\s*해설|^\s*Ch\.\s*\d"
    r"|모의평가|평가원|해석\s*연습|자연스러운\s*해석|해석을\s*써|단계별"      # 워크북 머리글·안내
    r"|EXAM\s*4\s*YOU|EXAM4Y[O0]U"                                          # 워크북 로고
    r"|^\s*[-–]\s*\d{1,4}\s*[-–]\s*$)",                                      # 페이지 번호 (- 14 -)
    re.IGNORECASE,
)
# 여러 지문이 한 파일에 있을 때의 경계(각 지문 끝의 출처 꼬리말)
_PASSAGE_SPLIT = re.compile(r"\[Flow\s*Edu\][^\n]*", re.IGNORECASE)

# 워크북(WORKBOOK) 워크시트 노이즈
#  - 러닝 헤더:   "31 2026 6 ┃3 WORKBOOK4 WORKBOOK. 1."  (문제번호 + 연·월 + WORKBOOK)
#  - 각주 번호:   "related.1)"  "use.2)"  "do.6)"  (문장 끝 참조 숫자)
#  - 문장 번호:   "1. Ever ~"  ". 2. Taken ~"  (문장 앞 일련번호)
_WB_HEADER = re.compile(
    r"\d+\s+20\d{2}\s+\d+\s*[┃│|]\s*\d*\s*WORKBOOK\w*\s+WORKBOOK\.?", re.IGNORECASE)
# 문제(지문) 경계가 되는 워크북 머리글 — 두 형태 모두 인식하고 '문제번호'를 캡처한다.
#  ① 실제 원본:  "31번 2026년 6월 한국교육과정평가원 모의평가┃고3 단계별 WORKBOOK4 …"
#  ② 도구 출력형: "31 2026 6 ┃3 WORKBOOK4 WORKBOOK. 1."
_WB_PROBLEM = re.compile(
    r"(\d+)\s*번[^\n]*?(?:모의평가|평가원|WORKBOOK)"
    r"|(\d+)\s+20\d{2}\s+\d+\s*[┃│|]\s*\d*\s*WORKBOOK\w*\s+WORKBOOK\.?",
    re.IGNORECASE)
_FOOTNOTE = re.compile(r"(?<!\()\b\d{1,3}\)")            # 각주 번호(괄호쌍 (2)은 보호)
_SENT_NO = re.compile(r"(?<![\w.])\d{1,3}\.\s+(?=[A-Z“\"‘'(])")  # 문장 앞 일련번호
_PAGE_NO = re.compile(r"[-–]\s*\d{1,4}\s*[-–]")          # 페이지 번호 (- 14 -)


def _clean_pdf_text(segment: str) -> str:
    """한 지문 조각에서 한글·머리글·원번호·워크시트 노이즈를 걷어내고 영어 본문만 남긴다."""
    lines: list[str] = []
    for ln in segment.splitlines():
        if _NOISE_LINE.search(ln):
            continue
        ln = _CIRCLED.sub(" ", ln)
        # '한줄해석'처럼 한글이 우세한 줄은 통째로 버린다. (한글만 지우면 그 줄의 마침표·
        #  괄호가 남아 영어 문장에 붙어 'communication..' · '(), ().' 같은 잔재가 생긴다.)
        hangul = len(_HANGUL.findall(ln))
        latin = len(re.findall(r"[A-Za-z]", ln))
        if hangul and latin <= hangul:
            continue
        ln = _HANGUL.sub("", ln)                        # 영어 위주 줄에 낀 한글만 제거
        ln = ln.replace("­", "")                        # soft hyphen 등
        lines.append(ln)
    text = " ".join(lines)
    # 워크시트 노이즈 제거(줄 경계를 넘나들므로 합친 뒤 한 번에)
    text = _WB_HEADER.sub(" ", text)                    # WORKBOOK 러닝 헤더
    text = _PAGE_NO.sub(" ", text)                      # 페이지 번호 - 14 -
    text = _FOOTNOTE.sub("", text)                      # 각주 번호 .1) .2) …
    text = _SENT_NO.sub("", text)                       # 문장 앞 일련번호 1. 2. …
    text = re.sub(r"\bWORKBOOK\w*\.?", " ", text, flags=re.IGNORECASE)  # 잔여 WORKBOOK
    text = re.sub(r"\(\s*\)", "", text)               # 빈 괄호 () 제거(한글 지운 잔재)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?)])", r"\1", text)   # 구두점 앞 공백 제거(2단 병합 잔여)
    text = re.sub(r"([,;:])\1+", r"\1", text)         # 중복 구두점 정리
    text = re.sub(r",\s*\.", ".", text)               # ' , .' → '.'
    text = re.sub(r"\.\s*\.+", ".", text)             # 연속 마침표(.. 포함) 정리
    return text


def _split_by_workbook(raw: str) -> list[tuple[str, str]] | None:
    """WORKBOOK 워크시트: 헤더의 '문제번호'가 바뀌는 곳을 지문 경계로 삼는다.

    같은 번호가 이어지면(연속 페이지) 한 지문으로 합치고, 번호가 달라지면 새 지문.
    반환: [(문제번호, 본문 조각), …] (문항 번호를 함께 보존). 헤더가 없으면 None.
    """
    matches = list(_WB_PROBLEM.finditer(raw))
    if len(matches) < 2:
        return None
    result: list[list[str]] = []      # [[문제번호, 본문], …] 순서 유지
    for i, m in enumerate(matches):
        num = m.group(1) or m.group(2)
        seg = raw[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(raw)]
        if result and result[-1][0] == num:
            result[-1][1] += " " + seg
        else:
            result.append([num, seg])
    return [(num, seg) for num, seg in result]


def _numbered_segments(raw: str) -> list[tuple[str | None, str]]:
    """원문 텍스트를 '지문 단위'로 나눈다. 각 지문에 문항 번호가 있으면 함께 돌려준다.

    ① WORKBOOK 문제번호별(번호 보존) → ② [Flow Edu] 꼬리말별(번호 없음) → ③ 통째로 1개.
    """
    wb = _split_by_workbook(raw)
    if wb is not None:
        return wb
    if _PASSAGE_SPLIT.search(raw):
        return [(None, s) for s in _PASSAGE_SPLIT.split(raw)]
    return [(None, raw)]


def _passages_from_raw_numbered(raw: str) -> list[tuple[str | None, str]]:
    """정제까지 마친 [(문항번호|None, 영어 본문)] 목록(최소 분량 이상만 채택)."""
    out: list[tuple[str | None, str]] = []
    for num, seg in _numbered_segments(raw):
        body = _clean_pdf_text(seg)
        # 문제로 쓸 만한 최소 분량(영어 글자 수) 이상만 채택
        if len(re.sub(r"[^A-Za-z]", "", body)) >= 120:
            out.append((num, body))
    return out


def _passages_from_raw(raw: str) -> list[str]:
    """추출한 원문 텍스트 → 한글·머리글·워크시트 노이즈 제거 후 영어 지문들로 분리."""
    return [body for _, body in _passages_from_raw_numbered(raw)]


def read_pdf_passages_numbered(path: str | Path) -> list[tuple[str | None, str]]:
    """PDF에서 [(문항번호|None, 영어 본문)] 목록. 워크시트면 문제번호를 함께 보존한다."""
    return _passages_from_raw_numbered(extract.extract_raw_text(path))


def read_hwp_passages_numbered(path: str | Path) -> list[tuple[str | None, str]]:
    """HWP/HWPX에서 [(문항번호|None, 영어 본문)] 목록(PDF와 동일한 정제·분리)."""
    return _passages_from_raw_numbered(_hwp.read_hwp_any(path))


def read_pdf_passages(path: str | Path) -> list[str]:
    """PDF에서 '영어 지문'들을 추출한다(여러 지문이면 각각 분리).

    - 영어+한글 2단, 여러 지문이 섞인 워크시트도 한글·머리글을 제거하고
      지문 단위로 나눠 돌려준다.
    - 글자 없는(스캔) PDF면 빈 리스트.
    """
    return _passages_from_raw(extract.extract_raw_text(path))


def read_hwp_passages(path: str | Path) -> list[str]:
    """HWP/HWPX에서 '영어 지문'들을 추출한다(PDF와 동일한 정제·분리)."""
    return _passages_from_raw(_hwp.read_hwp_any(path))


def read_pdf_passages_vision(client, path: str | Path, max_pages: int = 20,
                             logger=None) -> list[str]:
    """텍스트가 없는 '스캔 PDF'만 Claude 비전으로 페이지별 OCR 해 지문을 뽑는다.

    조건부 사용: 글자 PDF 는 pdfplumber(오프라인)로 처리하고, 여기 vision 은 텍스트
    추출이 실패한 문제(스캔) 파일에만 폴백으로 쓴다(비용·속도 절약). 페이지 1장 = 문제
    1개로 보고 페이지별로 OCR → 정제한다.
    """
    from pdf2image import convert_from_path   # 지연 임포트(무거움)

    tmpdir = Path(tempfile.mkdtemp(prefix="pdfvis_"))
    passages: list[str] = []
    try:
        images = convert_from_path(str(path), dpi=150)
        n = len(images)
        if n > max_pages and logger:
            logger.warning("스캔 PDF %d쪽 중 앞 %d쪽만 OCR 합니다(비용 상한).", n, max_pages)
        for i, im in enumerate(images[:max_pages], 1):
            png = tmpdir / f"p{i}.png"
            im.save(png, "PNG")
            try:
                txt = read_image_text(client, png)
            except Exception as e:  # noqa: BLE001 — 한 쪽 실패는 건너뛴다
                if logger:
                    logger.warning("[OCR %d/%d] 실패: %s", i, n, e)
                continue
            body = _clean_pdf_text(txt)
            if len(re.sub(r"[^A-Za-z]", "", body)) >= 120:
                passages.append(body)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
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

    if ext in HWP_EXTS:
        passages = read_hwp_passages(p)
        if not passages:
            raise ValueError(
                f"'{p.name}': HWP에서 영어 지문을 찾지 못했습니다. 지문이 이미지로 "
                "들어 있거나 형식이 특수할 수 있으니, 지문을 복사해 붙여넣거나 "
                "PDF/사진으로 저장해 올려 주세요."
            )
        return " ".join(passages)

    if ext in IMAGE_EXTS:  # noqa: RET503
        if client is None:
            raise ValueError(
                f"'{p.name}': 사진 지문을 읽으려면 ANTHROPIC_API_KEY 가 필요합니다."
            )
        return read_image_text(client, p)

    raise ValueError(
        f"'{p.name}': 지원하지 않는 형식입니다(.txt/.pdf/.hwp/.hwpx/.jpg/.png/.webp)."
    )


def load_bodies(paths, client=None, vision_fallback: bool = True,
                logger=None) -> list[tuple[str, str]]:
    """여러 파일 -> [(라벨, 지문본문)] 목록.

    라벨은 원본 PDF의 '영어지문 문항번호'(예: "31번")이며, 번호를 알 수 없으면
    빈 문자열이다(조판기가 위치 기준 "지문 1/2/…" 로 대체).
    보통 파일 1개 = 지문 1개지만, PDF 한 개에 지문이 여러 개면(예: EBS 워크시트)
    각각을 별도 지문으로 분리한다. 글자 없는 '스캔 PDF'는 client·vision_fallback 이
    있을 때만 조건부로 Claude 비전 OCR 로 처리한다(문제 파일만).
    """
    out: list[tuple[str, str]] = []
    for p in paths:
        p = Path(p)
        ext = p.suffix.lower()
        if ext in PDF_EXTS or ext in HWP_EXTS:
            numbered = (read_pdf_passages_numbered(p) if ext in PDF_EXTS
                        else read_hwp_passages_numbered(p))
            if not numbered and ext in PDF_EXTS and vision_fallback and client is not None:
                # 텍스트가 전혀 없는 스캔 PDF → 조건부 Vision OCR 폴백(번호는 알 수 없음)
                if logger:
                    logger.info("[%s] 글자 없는 스캔 PDF — Vision OCR 폴백", p.name)
                numbered = [(None, b) for b in read_pdf_passages_vision(client, p, logger=logger)]
            if not numbered:
                if ext in PDF_EXTS:
                    raise ValueError(
                        f"'{p.name}': 글자가 없는(스캔본) PDF에서 지문을 찾지 못했습니다. "
                        "API 키가 있으면 자동 OCR 되며, 없으면 사진(JPG/PNG)으로 올려 주세요."
                    )
                raise ValueError(
                    f"'{p.name}': HWP에서 영어 지문을 찾지 못했습니다. 지문을 복사해 "
                    "붙여넣거나 PDF/사진으로 저장해 올려 주세요."
                )
            # 라벨: 원본에 '영어지문 문항번호'가 있으면 'NN번', 없으면 빈 문자열
            # (조판기가 위치 기준 "지문 1/2/…" 로 대체). 파일명은 라벨로 쓰지 않는다.
            for num, body in numbered:
                out.append((f"{num}번" if num else "", body))
        else:
            body = load_body(p, client=client)
            if body and body.strip():
                out.append(("", body.strip()))
    return out
