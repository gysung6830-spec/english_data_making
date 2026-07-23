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
_HANGUL_CHAR = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]")


def _strip_trailing_name_echo(txt: str) -> str:
    """줄 끝에 붙은 '해석부 첫 인물명' 겹침 제거.

    직독직해는 해석문이 대개 주어(인물명)로 시작해, 영어부를 잘라도 그 이름이 줄 끝에
    한 번 더 남는다. 앞쪽에 이미 나온 대문자 토큰이 줄 끝에 반복되면 그것만 걷어낸다.
    """
    toks = txt.split()
    def norm(w: str) -> str:
        return re.sub(r"""[^A-Za-z]""", "", w)
    while len(toks) >= 2:
        last = norm(toks[-1])
        if last and last[:1].isupper() and last in {norm(t) for t in toks[:-1]}:
            toks.pop()
        else:
            break
    return " ".join(toks)


def _page_english_rows(page) -> str:
    """페이지를 줄(행) 단위로 재구성하되, 각 줄에서 '첫 한글 앞 영어부'만 남긴다.

    직독직해/워크북처럼 한 줄에 [영어 원문][한글 해석]이 나란한 자료에서, 한글 해석과
    거기 섞인 인물명 겹침·머리말·쪽번호를 제거해 영어 지문만 복원한다
    (설명형 지문은 거의 완벽히 정리되고, 서사형은 인물명 겹침까지 대부분 제거).
    """
    words = page.extract_words(use_text_flow=False)
    if not words:
        return page.extract_text() or ""
    rows: dict[float, list] = {}
    for w in words:
        rows.setdefault(round(w["top"] / 3.0), []).append(w)
    out: list[str] = []
    for key in sorted(rows):
        ws = sorted(rows[key], key=lambda w: w["x0"])
        txt = " ".join(w["text"] for w in ws)
        m = _HANGUL_CHAR.search(txt)
        had_ko = m is not None
        if had_ko:                              # 첫 한글부터 뒤(=해석부)를 잘라낸다
            txt = txt[:m.start()]
        txt = _SRC_NOISE.sub(" ", txt)          # WORKBOOK·쪽번호·워터마크 제거
        txt = _STUDY_HEADER.sub(" ", txt)
        txt = re.sub(r"[。·※▶◀‣・｜┃]", " ", txt)
        txt = re.sub(r"\s{2,}", " ", txt).strip()
        if not _EN_WORD.search(txt):            # 영어 단어가 없으면 머리말/잡음 → 버림
            continue
        if had_ko:
            txt = _strip_trailing_name_echo(txt)
        if txt:
            out.append(txt)
    return "\n".join(out)


def _read_pdf(path: Path) -> str:
    import pdfplumber
    plain: list[str] = []
    rows_en: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            plain.append(page.extract_text() or "")
            rows_en.append(_page_english_rows(page))
    full = "\n".join(plain)
    # 이중언어(직독직해/워크북)면 줄 단위로 한글 해석을 제거한 영어본을 쓴다.
    if _is_bilingual_study(full):
        return "\n\n".join(r for r in rows_en if r.strip())
    return full


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
# 줄 앞머리 "라벨:" 패턴(안내문 구획 헤더 / 대화문 화자 라벨 공통)
_LABEL_RE = re.compile(r"^\s*([A-Za-z가-힣][A-Za-z가-힣 &/]{0,24}):\s*\S")
# 안내문 구획 라벨 키워드
_NOTICE_LABELS = ("when", "where", "date", "time", "location", "admission", "notice",
                  "highlights", "notes", "details", "registration", "price", "fee",
                  "contact", "venue", "schedule", "program", "hours", "deadline",
                  "eligibility", "prize", "how to")
# 화자 라벨 후보(짧은 단일 토큰)
_SPEAKER_TOKEN = re.compile(r"[A-Za-z]{1,12}|[mwMW]|man|woman|남|여")
_CHART_HINT = re.compile(r"(\d+\s*%|percent|the (?:above|following) (?:graph|chart|table)|그래프|도표|위 표)", re.I)


def detect_format(text: str) -> tuple[FormatType, list[str]]:
    """서술문 / 대화문 / 안내문 / 도표 판별. (format_type, speakers).

    - 안내문: 'Label:' 형태 구획 헤더가 2개 이상(When/Where/Highlights/Notes 등).
    - 대화문: 짧은 화자 라벨('M:'/'Tom:')로 시작하는 발화가 3턴 이상 & 화자 2명 이상.
      (안내문 구획 라벨은 화자에서 제외 → 'Highlights:' 오인 방지)
    - 흔한 단어(when/time)의 단순 등장으로는 안내문으로 판정하지 않는다.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    notice_hits = 0
    turns: list[str] = []
    for ln in lines:
        m = _LABEL_RE.match(ln)
        if not m:
            continue
        label = m.group(1).strip().lower()
        if any(k in label for k in _NOTICE_LABELS):
            notice_hits += 1
            continue
        first = label.replace("&", " ").replace("/", " ").split()
        if first and _SPEAKER_TOKEN.fullmatch(first[0]):
            turns.append(first[0])

    if len(_CHART_HINT.findall(text)) >= 2:
        return "chart", []
    if notice_hits >= 2:
        return "notice", []
    distinct = sorted(set(turns))
    if len(turns) >= 3 and len(distinct) >= 2:
        return "dialogue", distinct
    return "narrative", []


# ---------------------------------------------------------------------------
# 이중언어(직독직해)·EBS 자료 전처리
# ---------------------------------------------------------------------------
_HANGUL_RUN = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]+")
_CIRCLED = re.compile(r"[①-⑳㉑-㉟㉠-㉯]")  # ①~⑳ 및 원문자
_CIRCLED_ONE = re.compile(r"①")            # 각 지문 첫 문장 표시(직독직해 공통)
_EN_WORD = re.compile(r"[A-Za-z]{2,}")
_SENT_END = re.compile(r"(?<=[.!?])\s+")

# 지문 경계 헤더 — 교재 무관하게 폭넓게 인식
#  Ch./Unit/Lesson/Chapter/Day/Test/Week/Part/N강/N회/N일차/지문 N/Passage N/N번 등
_STUDY_HEADER = re.compile(
    r"(?:Ch(?:apter|\.)?|Unit|Lesson|Day|Test|Week|Part|Step|Mini\s*Test|"
    r"Review|Actual\s*Test|모의고사|실전|어법|지문|Passage)\s*\.?\s*\d+"
    r"(?:\s*[-–~]\s*\d+)?\s*번?"
    r"|\d+\s*(?:강|회|일차)\b"
    r"|\d{1,3}\s*번", re.I)                             # 18번·21번 등 문항번호 머리말

# 출처·워터마크·저작권 노이즈(교재/블로그/카페 등)
_SRC_NOISE = re.compile(
    r"\[[^\]\n]{0,40}\]"                                # [EBS] [Flow Edu] 등 대괄호 태그
    r"|한줄해석\([^)]*\)|좌지문우해석|우지문좌해석|직독직해"
    r"|올림포스[가-힣0-9]*|수능특강[가-힣0-9]*|수능완성[가-힣0-9]*"
    r"|마더텅|자이스토리|능률|천재교육|비상교육|지학사|블랙라벨|한수영어"
    # 워크북/모의고사 머리말·쪽번호·워터마크
    r"|WORKBOOK\s*\d*|WORK\s*BOOK|Learning\s*Guide|지문\s*연습(?:하기)?|지문연습"
    r"|단계별|모의평가|한국교육과정평가원|평가원|교육청|수능|기출"
    r"|(?<!\d)-\s*\d{1,3}\s*-(?!\d)"                    # - 3 - 형태 쪽번호
    r"|┃|｜"                                            # 세로 구분자
    r"|(?:https?://)?[\w.-]+\.(?:com|net|kr|co\.kr|tistory\.com|blog\.[\w.-]+)"
    r"(?:/[\w\-./?=&%]*)?"
    r"|Copyright[^\n]*|All\s+rights\s+reserved|무단\s*복제[^\n]*", re.I)


def _is_bilingual_study(text: str) -> bool:
    """직독직해식 이중언어 자료(영어 지문 + 한글 해석 혼재)인지 판단.

    핵심 신호: 같은 줄에서 영어 단어 바로 뒤에 한글이 붙는 '끼어든 해석'.
    (단순히 '지문 N' 구분자만 있는 순수 영어 자료는 여기서 제외한다.)
    """
    has_ko = bool(_HANGUL_RUN.search(text))
    has_en = len(_EN_WORD.findall(text)) > 30
    interleave = len(re.findall(r"[A-Za-z]{3,}[ \t]{1,4}[가-힣]", text))
    circled_ko = text.count("①") >= 2 and bool(re.search(r"①[^\n]{0,120}[가-힣]", text))
    return has_ko and has_en and (interleave >= 4 or circled_ko)


def _clean_english(chunk: str) -> str:
    """이중언어 조각에서 한글 해석·출처·문장번호를 걷어내고 영어 지문만 복원.

    직독직해는 각 문장이 ①②③…로 시작하므로 이를 '문장 경계' 표식으로 삼아,
    한글 해석을 지운 뒤 문장 경계에 마침표를 복원한다.
    """
    SENT = "\x00"                              # 문장 경계 임시 표식
    t = _SRC_NOISE.sub(" ", chunk)
    t = _STUDY_HEADER.sub(" ", t)
    t = _CIRCLED.sub(f" {SENT} ", t)           # 문장번호 → 경계 표식
    t = _HANGUL_RUN.sub(" ", t)                # 한글 해석 제거
    t = re.sub(r"[·∼※▶◀‣・「」『』（），、]", " ", t)
    t = re.sub(r"\s+", " ", t)
    # 한글 제거로 생긴 '고아 구두점'(공백에 둘러싸인 . , ; : ! ?) 삭제
    t = re.sub(r"\s+[.,;:!?]+(?=\s|$)", " ", t)
    # 문장 경계 표식 → 마침표 복원
    t = re.sub(rf"\s*{SENT}\s*", ". ", t)
    t = re.sub(r"([.!?])[.\s]*(?=[.!?])", "", t)  # 연속 문장부호 정리
    t = re.sub(r"\s+([.,;:!?)])", r"\1", t)       # 구두점 앞 공백 제거
    t = re.sub(r"([.,;:!?])\1+", r"\1", t)        # 중복 구두점 축소
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"^[\s.,;:)\]]+", "", t)           # 앞머리 잡구두점 제거
    t = re.sub(r"\s{2,}", " ", t).strip()
    if t and t[-1] not in ".!?\"'":               # 마지막 문장 마침표 보정
        t += "."
    return t


_MIN_PASSAGE_WORDS = 12  # 지문으로 채택할 최소 영어 단어 수


def _split_by_sentences(text: str, target: int = 7, min_words: int = _MIN_PASSAGE_WORDS) -> list[str]:
    """영어 지문 하나를 ~target 문장 묶음으로 나눈다(헤더 없는 자료 대비)."""
    sents = [s for s in _SENT_END.split(text) if s.strip()]
    groups: list[str] = []
    cur: list[str] = []
    for s in sents:
        cur.append(s)
        if len(cur) >= target:
            groups.append(" ".join(cur))
            cur = []
    if cur:
        tail = " ".join(cur)
        if groups and len(_EN_WORD.findall(tail)) < min_words:
            groups[-1] += " " + tail          # 짧은 꼬리는 앞 묶음에 합침
        else:
            groups.append(tail)
    groups = [g for g in groups if len(_EN_WORD.findall(g)) >= min_words]
    return groups or [text]


def _split_bilingual(text: str) -> list[str]:
    """직독직해 자료를 지문 단위로 나눠 영어 지문 리스트로 복원(교재 무관)."""
    raw_chunks: list[str] = []

    # 1순위: '①' 리셋으로 분할 — 모든 직독직해에서 각 지문은 ①로 시작.
    if text.count("①") >= 2:
        raw_chunks = [c for c in re.split(r"(?=①)", text) if c.strip()]

    # 2순위: 단원 헤더로 분할(Ch/Unit/N강/N번 등)
    if len(raw_chunks) < 2:
        heads = list(_STUDY_HEADER.finditer(text))
        if len(heads) >= 2:
            b = [m.start() for m in heads] + [len(text)]
            raw_chunks = [text[b[i]:b[i + 1]] for i in range(len(heads))]

    # 3순위: 경계 신호가 없으면 통째로 두고 뒤에서 문장묶음으로 분할
    if not raw_chunks:
        raw_chunks = [text]

    cleaned = [_clean_english(c) for c in raw_chunks]
    cleaned = [c for c in cleaned if len(_EN_WORD.findall(c)) >= _MIN_PASSAGE_WORDS]

    # 분리 실패(경계 오인 등) → 전체를 한 번에 정제 후 문장묶음으로 재분할.
    if not cleaned:
        whole = _clean_english(text)
        if len(_EN_WORD.findall(whole)) >= _MIN_PASSAGE_WORDS:
            cleaned = _split_by_sentences(whole)

    # 지문이 1개뿐이면(헤더·① 없음) 문장묶음으로 여러 지문 확보
    if len(cleaned) == 1:
        cleaned = _split_by_sentences(cleaned[0])
    return cleaned


# ---------------------------------------------------------------------------
# 지문 경계 분리
# ---------------------------------------------------------------------------
_PASSAGE_MARK = re.compile(r"^\s*(?:지문\s*\d+|passage\s*\d+|\[?\s*\d+\s*\]?)\s*[.:)]?\s*$", re.I)


def split_passages(text: str, source_file: str | None = None,
                   id_prefix: str = "p") -> list[Passage]:
    """빈 줄·번호·제목 패턴으로 여러 지문을 나눈다.

    - 직독직해/EBS식 이중언어 자료면 단원 헤더로 나누고 영어만 복원.
    - '지문 1' / 'Passage 2' / '[1]' 같은 명시적 구분선을 우선 사용.
    - 없으면 2줄 이상 빈 줄을 경계로 삼는다.
    """
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []

    # 0) 직독직해/EBS 이중언어 자료 → 단원별 영어 지문으로 복원
    if _is_bilingual_study(text):
        passages: list[Passage] = []
        for i, body in enumerate(_split_bilingual(text), 1):
            fmt, speakers = detect_format(body)
            passages.append(Passage(id=f"{id_prefix}{i}", text=body,
                                    format_type=fmt, speakers=speakers,
                                    source_file=source_file))
        if passages:
            return passages

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
