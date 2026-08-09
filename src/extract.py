"""PDF -> 텍스트 추출 및 지문 본문 후보 정리(휴리스틱).

여기서는 스캔본이 아닌 텍스트 PDF 를 가정한다.
문제/정답/해설 등 불필요한 줄을 1차로 걷어내되, 최종적인 '본문만 추출'은
분석 파이프라인의 추출(extraction) API 호출에서 한 번 더 정제한다.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

# 지원하는 이미지 확장자 (사진/캡처 자동 처리용)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS

# 문제/정답/해설로 보이는 줄을 걸러내기 위한 패턴
#   (원문자 ①②③ 는 '문장 번호'로도 쓰이므로 줄 전체 삭제 규칙에서 제외 — 아래 _NUM_PREFIX 로 번호만 제거)
_NOISE_PATTERNS = [
    re.compile(r"^\s*(정답|해설|풀이|어휘|해석|출제|답)\s*[:：)]"),
    re.compile(r"^\s*\[?\s*(정답|해설)\s*\]?"),
    re.compile(r"^\s*(문|문제)\s*\d+"),
    re.compile(r"^\s*[A-E]\)\s"),                       # A) B) 보기
]

# 문장/문항 번호 표시( '1.' '2)' '(3)' 그리고 원문자 ①②③…⑳ ) —
#   줄 전체가 아니라 '번호만' 떼어 내용은 보존한다.
#   (해석 연습·한줄해석 등 문장이 번호로 나열된 자료에서 문장 첫 줄이 통째로 사라지는 것을 방지)
_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
_NUM_PREFIX = re.compile(r"^\s*(?:\(?[1-9]\d?\)?\s*[.)]|[" + _CIRCLED + r"])\s+")

# 페이지 번호/머리말 같은 짧은 잡음 줄
_SHORT_NOISE = re.compile(r"^\s*[-–—•·\d\s]{0,4}$")


def _extract_page_columns(page) -> str:
    """페이지를 좌/우 2단으로 나눠 '왼쪽 칼럼 전체 → 오른쪽 칼럼' 순서로 읽는다.

    모의고사처럼 2단 편집인 시험지에서 좌우 칼럼이 한 줄로 뒤섞이는 것을 방지한다.
    """
    mid = page.width / 2.0
    left = page.crop((0, 0, mid, page.height)).extract_text() or ""
    right = page.crop((mid, 0, page.width, page.height)).extract_text() or ""
    return left + "\n" + right


def extract_raw_text(pdf_path: str | Path, two_column: bool = False) -> str:
    """PDF 전체에서 텍스트를 뽑는다.

    two_column=True 이면 각 페이지를 좌/우 칼럼 순서로 읽는다(2단 시험지용).
    일반 지문·교재는 two_column=False(기본) 로 그대로 읽어 부작용이 없다.
    """
    pdf_path = Path(pdf_path)
    parts: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            if two_column:
                parts.append(_extract_page_columns(page))
            else:
                parts.append(page.extract_text() or "")
    return "\n".join(parts)


def clean_text(raw: str) -> str:
    """문제/정답/해설 등으로 보이는 줄을 1차 제거한다."""
    kept: list[str] = []
    for line in raw.splitlines():
        s = line.rstrip()
        if not s.strip():
            kept.append("")
            continue
        if _SHORT_NOISE.match(s):
            continue
        if any(p.search(s) for p in _NOISE_PATTERNS):
            continue
        # 숫자 번호로 시작하는 줄은 줄 전체를 버리지 말고 번호 표시만 떼어 '내용은 보존'.
        m = _NUM_PREFIX.match(s)
        if m:
            s = s[m.end():]
            if not s.strip():
                continue
        kept.append(s)
    # 연속 빈 줄 압축
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# 모의고사 듣기 영역 종료 안내 문구(이 뒤부터가 독해 영역).
#   예) "이제 듣기 문제가 끝났습니다. 18번부터는 문제지의 지시에 따라 …"
_LISTENING_END = re.compile(
    r"이제\s*듣기[^\n]{0,20}끝났습니다"
    r"|\d+\s*번부터는\s*문제지의\s*지시"
)


def strip_listening(text: str) -> str:
    """모의고사면 듣기(1~17) 안내 문구를 찾아 그 앞부분을 잘라내고 독해 영역만 남긴다.

    안내 문구가 없으면(일반 지문·교재) 원문을 그대로 반환하므로 부작용이 없다.
    """
    m = _LISTENING_END.search(text)
    if not m:
        return text
    return text[m.end():]


def extract_passage_text(pdf_path: str | Path, two_column: bool = False) -> str:
    """PDF -> (2단 처리 + 듣기 영역 제거 + 1차 정제된) 지문 후보 텍스트.

    two_column=True 는 2단 시험지(모의고사)일 때만 사용한다.
    """
    return clean_text(strip_listening(extract_raw_text(pdf_path, two_column)))


def looks_empty(text: str) -> bool:
    """텍스트가 사실상 비어있는지(스캔본/추출 실패) 판단."""
    letters = re.sub(r"[^A-Za-z]", "", text)
    return len(letters) < 40


# 정상 영어 지문이면 반드시 여러 번 등장하는 흔한 기능어
_COMMON_WORDS = {
    "the", "and", "of", "to", "a", "in", "is", "that", "it", "for", "as",
    "with", "was", "on", "are", "be", "this", "by", "not", "or", "have",
    "from", "but", "an", "they", "we", "he", "she", "his", "her", "which",
    "you", "their", "can", "at", "all", "has", "would", "when", "who",
}


def looks_garbled(text: str) -> bool:
    """추출은 됐지만 글자가 깨지거나 조각나서 분석에 부적합한지 판단.

    무인(無人) 배치에서 '문제 파일'을 걸러 비전(vision)으로 다시 읽게 하는 신호.
    정상 지문을 비전으로 잘못 넘기지 않도록 '명백히 깨진' 경우만 True(보수적).
    """
    letters = re.sub(r"[^A-Za-z]", "", text)
    if len(letters) < 40:
        return False  # 사실상 비어있는 경우는 looks_empty 가 담당
    # 1) 공백을 제외한 글자 중 알파벳 비중이 지나치게 낮으면(특수문자/깨진 글자 범벅) 의심
    visible = re.sub(r"\s", "", text)
    if visible and len(letters) / len(visible) < 0.55:
        return True
    # 2) 정상 영어 지문이면 흔한 기능어(the/and/of...)가 여러 개 나온다.
    #    충분히 긴데도 거의 없으면 단어가 조각나 깨진 것으로 본다.
    words = re.findall(r"[A-Za-z]+", text.lower())
    if len(words) >= 40:
        common = sum(1 for w in words if w in _COMMON_WORDS)
        if common / len(words) < 0.08:
            return True
    return False


def render_pdf_to_images(pdf_path: str | Path, dpi: int = 150,
                         max_pages: int = 12) -> list[Path]:
    """PDF 각 페이지를 이미지(PNG)로 렌더해 임시 파일 경로 목록을 반환.

    pdfplumber 텍스트 추출이 부정확한 경우, 페이지를 이미지로 만들어
    Claude 비전으로 직접 읽기 위함(사진 입력과 동일한 정확도).
    """
    import tempfile

    try:
        import fitz  # PyMuPDF
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "PDF를 이미지로 읽으려면 PyMuPDF가 필요합니다. "
            "'pip install PyMuPDF' 를 실행한 뒤 다시 시도하세요."
        ) from e

    pdf_path = Path(pdf_path)
    out_dir = Path(tempfile.mkdtemp(prefix="pdfimg_"))
    imgs: list[Path] = []
    with fitz.open(str(pdf_path)) as doc:
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            p = out_dir / f"p{i + 1:02d}.png"
            pix.save(str(p))
            imgs.append(p)
    return imgs
