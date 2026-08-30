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
#  ③ 모의고사/EBS형: "[고1] 2025 09월 – 18번: 학교 도서관 …"  (편지·심경 등 일반 지문)
_WB_PROBLEM = re.compile(
    r"(\d+)\s*번[^\n]*?(?:모의평가|평가원|WORKBOOK)"
    r"|(\d+)\s+20\d{2}\s+\d+\s*[┃│|]\s*\d*\s*WORKBOOK\w*\s+WORKBOOK\.?"
    r"|\[\s*고\s*\d\s*\][^\n]*?(\d+)\s*번\s*[:：]",
    re.IGNORECASE)
_FOOTNOTE = re.compile(r"(?<!\()\b\d{1,3}\)")            # 각주 번호(괄호쌍 (2)은 보호)
# 문장 앞 일련번호 — '1. Sentence …' 의 '1.' 만 지운다.
# 실제 결과물에서 'reschedule the meeting for September 17. I realize …' 의 '17.' 이
# 통째로 지워져 두 문장이 'September I realize' 로 붙어 버렸다(지문 하나의 13문항이
# 그 비문을 싣고 나갔다). 낱말 뒤에 오는 숫자는 날짜·수량이지 일련번호가 아니다.
# 그래서 '글 첫머리 · 문장이 끝난 자리 · 줄 첫머리' 에서만 일련번호로 본다.
_SENT_NO = re.compile(r"(^|[.!?][\s]|\n)\s*\d{1,3}\.\s+(?=[A-Z“\"‘'(])")
# 페이지 번호 (- 14 -). 앞뒤가 낱말·숫자가 아닐 때만 — 그러지 않으면 전화번호
# '308-555-9847' 의 가운데 토막을 먹어 '308 9847' 이 된다(실제 결과물에서 그랬다).
_PAGE_NO = re.compile(r"(?<![\w])[-–]\s*\d{1,4}\s*[-–](?![\w])")


def _normalize_raw(raw: str) -> str:
    """PDF 추출 원문의 제어문자를 정리한다.

    일부 PDF는 공백을 NUL(\\x00)로 뽑아내(예: '[Flow\\x00Edu]'), 지문 분리·노이즈
    정규식이 안 먹는다. NUL·소프트하이픈·기타 제어문자를 공백/줄바꿈으로 바꾼다.
    """
    raw = raw.replace("\x00", " ").replace("\xad", "")   # NUL·soft hyphen
    raw = raw.replace("\x0c", "\n")                        # 폼피드(페이지 경계) → 줄바꿈
    raw = re.sub(r"[\x01-\x08\x0b\x0e-\x1f]", " ", raw)    # 기타 제어문자(\n·\t 제외)
    return raw


def _dedup_key(s: str) -> str:
    """중복 줄 판별용 정규화 키(영숫자만, 소문자, 공백 단일화)."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _strip_paired_translation(line: str) -> str:
    """EBS 한줄해석 '③ EN ③ KR' 짝 구조에서 번역(반복된 원번호 이후)을 통째로 버린다.

    영어 원문과 한글 번역이 '같은 줄'에서 같은 원번호로 이어질 때, 번역 안에 든 영어
    고유명사·책이름·연도(예: 'Paul R. Ehrlich', 'The Population Bomb', '1968')는 한글만
    지우면 살아남아 원문 뒤에 붙는다. 원번호가 '연속으로 같은 값'이면 그 두 번째 구간
    (번역)을 통째로 제거해 이를 막는다. 원번호가 없거나 짝 구조가 아니면 그대로 둔다."""
    segs = re.split(r"([①-⑳])", line)          # ['pre','③',' EN ','③',' KR', …]
    if len(segs) < 4:
        return line
    out, prev = [segs[0]], None
    for i in range(1, len(segs), 2):
        marker = segs[i]
        seg = segs[i + 1] if i + 1 < len(segs) else ""
        if marker != prev:                      # 같은 번호 반복(번역)이면 버림
            out.append(marker)
            out.append(seg)
        prev = marker
    return "".join(out)


def _clean_pdf_text(segment: str) -> str:
    """한 지문 조각에서 한글·머리글·원번호·워크시트 노이즈를 걷어내고 영어 본문만 남긴다."""
    lines: list[str] = []
    prev_en = ""      # 직전에 채택한 '영어 원문' 줄(한줄해석·제목 중복 판별용)
    for ln in segment.splitlines():
        if _NOISE_LINE.search(ln):
            continue
        ln = _strip_paired_translation(ln)   # '③ EN ③ KR' 한 줄 번역 구간 제거
        ln = _CIRCLED.sub(" ", ln)
        # '한줄해석'처럼 한글이 우세한 줄은 통째로 버린다. (한글만 지우면 그 줄의 마침표·
        #  괄호가 남아 영어 문장에 붙어 'communication..' · '(), ().' 같은 잔재가 생긴다.)
        # 글자 수를 1:1로 비교하면, 번역문에 든 영어 고유명사·책이름(예: 'The Population
        # Bomb Paul R. Ehrlich')이 라틴 문자 수를 밀어 올려 번역 줄이 살아남는다. 한글 1자는
        # 영어 2자 이상의 정보를 담으므로 가중치를 줘서 '한글이 우세한 줄'을 제대로 잡는다.
        hangul = len(_HANGUL.findall(ln))
        latin = len(re.findall(r"[A-Za-z]", ln))
        if hangul and latin <= hangul * 2:
            continue
        stripped = _HANGUL.sub("", ln).replace("­", "")   # 영어 위주 줄에 낀 한글 제거
        # 한줄해석(번역) 줄 판별: EBS 좌지문·우해석은 '영어 원문' 바로 아래에 '한글 번역'
        # 줄이 온다. 안내문 제목·행사명·지명 등 고유명사가 든 번역 줄은 한글을 벗겨도
        # 영어 조각(예: 'Library Bookmark Design Contest')이 살아남아 지문에 끼어든다.
        # 그 조각은 항상 '윗줄(원문) 단어들의 부분집합'이므로, 그럴 때는 줄째로 버린다.
        #  - 한글이 섞였던 줄(번역 잔재)  또는  윗줄과 사실상 똑같은 줄(번역 안 된 제목)
        words = [w for w in re.findall(r"[A-Za-z]+", stripped.lower()) if len(w) >= 3]
        prev_words = set(re.findall(r"[A-Za-z]+", prev_en.lower()))
        is_subset = bool(words) and all(w in prev_words for w in words)
        if is_subset and (hangul or _dedup_key(stripped) == _dedup_key(prev_en)):
            continue
        lines.append(stripped)
        if re.search(r"[A-Za-z]", stripped):
            prev_en = stripped
    text = " ".join(lines)
    # 안내문(행사·대회 안내)의 불릿 기호(* ※ • ‣ ▪)는 목록 표시일 뿐 본문이 아니다.
    # 산문으로 펼치면 'When & Where * September … * Maple Creek …' 처럼 잡음이 되므로
    # 문장 경계(마침표)로 바꿔, 각 항목이 자연스럽게 끊긴 문장으로 읽히게 한다.
    text = re.sub(r"\s*[*※•‣▪]+\s*", ". ", text)
    # 워크시트 노이즈 제거(줄 경계를 넘나들므로 합친 뒤 한 번에)
    text = _WB_HEADER.sub(" ", text)                    # WORKBOOK 러닝 헤더
    text = _PAGE_NO.sub(" ", text)                      # 페이지 번호 - 14 -
    text = _FOOTNOTE.sub("", text)                      # 각주 번호 .1) .2) …
    text = _SENT_NO.sub(r"\1", text)                    # 문장 앞 일련번호 1. 2. …
    text = re.sub(r"\bWORKBOOK\w*\.?", " ", text, flags=re.IGNORECASE)  # 잔여 WORKBOOK
    text = re.sub(r"\(\s*\)", "", text)               # 빈 괄호 () 제거(한글 지운 잔재)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?)])", r"\1", text)   # 구두점 앞 공백 제거(2단 병합 잔여)
    text = re.sub(r"([,;:])\1+", r"\1", text)         # 중복 구두점 정리
    text = re.sub(r",\s*\.", ".", text)               # ' , .' → '.'
    text = re.sub(r"\.\s*\.+", ".", text)             # 연속 마침표(.. 포함) 정리
    text = re.sub(r"^[\s.:;,·)]+", "", text)          # 맨 앞 불릿·헤더 콜론(3번:) 잔재 제거
    return text


# EBS 올림포스 등 'Ch.NN Unit U - …' 형식 지문 경계와 라벨 규칙.
#   "Unit 10 - 3번"                → '10-3'
#   "Unit 11 - 수능 대비 ANALYSIS"  → '11-A'
#   "Unit 12 - 서술형 Practice"     → '서술형'   (논술형 Practice → '논술형')
_UNIT_PROBLEM = re.compile(
    r"Unit\s*(\d+)\s*[-–~]\s*(?:수능\s*대비\s*)?"
    r"(?:(\d+)\s*번"
    r"|(ANALYSIS|Analysis|분석|해설)"
    r"|(서술형|논술형)\s*(?:[-–]?\s*(?:Practice|practice|연습|프랙티스))?)",
    re.IGNORECASE)
# Unit 접두어 없이 '서술형-Practice' / '논술형 Practice' 구획 머리만 있는 경우도 인식.
_PRACTICE_HEAD = re.compile(
    r"(서술형|논술형)\s*[-–]?\s*(?:Practice|practice|연습|프랙티스)", re.IGNORECASE)


def _unit_label(m: "re.Match") -> str | None:
    """_UNIT_PROBLEM 매치 → 라벨. M번→'U-M', ANALYSIS→'U-A', 서술형/논술형→'서술형'/'논술형'."""
    unit = m.group(1)
    if m.group(2):
        return f"{unit}-{m.group(2)}"
    if m.group(3):
        return f"{unit}-A"
    if m.group(4):
        return m.group(4)          # '서술형' / '논술형' (사용자 지정: 유닛 번호 없이)
    return None


def _split_by_unit(raw: str) -> list[tuple[str, str]] | None:
    """'Unit U - M번/ANALYSIS/서술형·논술형 Practice' 및 '서술형-Practice' 머리를 지문
    경계로 삼고 라벨을 만든다. 헤더가 하나도 없으면 None. (헤더 앞 파일 머리말은 버린다.)"""
    marks: list[tuple[int, int, str]] = []
    for m in _UNIT_PROBLEM.finditer(raw):
        lbl = _unit_label(m)
        if lbl:
            marks.append((m.start(), m.end(), lbl))
    for m in _PRACTICE_HEAD.finditer(raw):
        marks.append((m.start(), m.end(), m.group(1)))
    if not marks:
        return None
    marks.sort()
    dedup: list[tuple[int, int, str]] = []
    for s, e, lbl in marks:                 # 겹치는 매치(Unit 헤더 속 서술형 등)는 앞것만
        if dedup and s < dedup[-1][1]:
            continue
        dedup.append((s, e, lbl))
    out: list[tuple[str, str]] = []
    for i, (_s, e, lbl) in enumerate(dedup):
        seg = raw[e:dedup[i + 1][0] if i + 1 < len(dedup) else len(raw)]
        out.append((lbl, seg))
    return out


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
        num = m.group(1) or m.group(2) or m.group(3)
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
    unit = _split_by_unit(raw)          # EBS 올림포스 'Unit U - M번/ANALYSIS' → 라벨 U-M/U-A
    if unit is not None:
        return unit
    if _PASSAGE_SPLIT.search(raw):
        return [(None, s) for s in _PASSAGE_SPLIT.split(raw)]
    return [(None, raw)]


def _passages_from_raw_numbered(raw: str) -> list[tuple[str | None, str]]:
    """정제까지 마친 [(문항번호|None, 영어 본문)] 목록(최소 분량 이상만 채택)."""
    raw = _normalize_raw(raw)         # NUL(\x00) 등 제어문자 정리 → 지문 분리가 제대로 되게
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
            # 라벨: 원본 문항 식별자. 순수 숫자면 'NN번'(모의고사), 이미 형식화된 값
            # (예: '10-3'·'11-A' — EBS Unit)이면 그대로. 없으면 빈 문자열(위치 기준 대체).
            for num, body in numbered:
                if not num:
                    lbl = ""
                elif str(num).isdigit():
                    lbl = f"{num}번"
                else:
                    lbl = str(num)
                out.append((lbl, body))
        else:
            body = load_body(p, client=client)
            if body and body.strip():
                out.append(("", body.strip()))
    return out
