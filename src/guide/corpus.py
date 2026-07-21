"""기출 코퍼스 처리 — 사용자가 넣은 기출 PDF/이미지에서 문장을 뽑고,
각 평가원 코드가 등장하는 문장을 '유형별로' 모은다.

핵심 역할(요청사항): 평가원 기출 문장들을 학습해 '비슷한 유형끼리' 모아 준다.
= 코드(기능어)별로 그 코드가 든 문장을 그룹핑.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .. import extract
from .codes import Category, Code

# 영어 문장 분리(약식): 마침표/물음표/느낌표 뒤 공백 기준, 약어 예외 최소 처리.
_ABBR = {"e.g", "i.e", "etc", "vs", "Mr", "Mrs", "Ms", "Dr", "St", "cf"}
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def split_sentences(text: str) -> list[str]:
    """영어 지문 텍스트를 문장 단위로 분리."""
    # 줄바꿈을 공백으로 정규화(문장이 줄을 넘길 수 있음)
    flat = re.sub(r"\s*\n\s*", " ", text)
    flat = re.sub(r"\s{2,}", " ", flat).strip()
    raw = _SENT_SPLIT.split(flat)
    out: list[str] = []
    for s in raw:
        s = s.strip()
        # 약어로 잘못 끊긴 조각을 앞 문장에 다시 붙임
        if out and out[-1].rstrip(".").split()[-1] in _ABBR:
            out[-1] = out[-1] + " " + s
            continue
        if len(re.sub(r"[^A-Za-z]", "", s)) >= 8:   # 알파벳 8자 미만은 잡음 취급
            out.append(s)
    return out


_HANGUL = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]")
_BOX = re.compile(r"[│┃❙▶◀■□●○◦·※★☆　。、〔〕「」『』【】]")
_FLOAT_PUNCT = re.compile(r"(?<=\s)[.,;:]+(?=\s)")   # 양옆이 공백인 '떠 있는' 구두점
_NUM_TOKEN = re.compile(r"(?<!\S)-?\d+(?:st|nd|rd|th)?-?(?!\S)")  # 홀로 선 숫자/페이지 번호


def extract_english(text: str) -> str:
    """평가원 워크북(영문+국문 2단 + 세로 저작권 워터마크)에서 영어 본문만 복원한다.

    한글·워터마크 문자를 지우면 영어 조각이 남고, 조각을 이어 붙이면 원 문장이 복원된다.
    (예: '... will be held 및\n개장 ... on June 1st.' → '... will be held on June 1st.')
    """
    t = _HANGUL.sub(" ", text)
    t = _BOX.sub(" ", t)
    t = t.replace("’", "'").replace("“", '"').replace("”", '"').replace("‘", " ")
    t = re.sub(r"\s*\n\s*", " ", t)          # 줄바꿈 → 공백(조각 잇기)
    # 워크북 머리말/안내 토큰 제거
    t = re.sub(r"\bWORKBOOK\s*0?\b", " ", t)
    t = re.sub(r"\bLearning Guide\b", " ", t)
    # 페이지 표식('- 1 -')과 홀로 선 숫자 제거 (문장 내부 '1st' 등은 보존)
    t = re.sub(r"-\s*\d+\s*-", " ", t)
    t = _NUM_TOKEN.sub(" ", t)
    t = _FLOAT_PUNCT.sub(" ", t)             # 국문 열에서 떨어져 나온 떠 있는 구두점 제거
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)   # 구두점 앞 공백 제거
    t = re.sub(r"([!?.]){2,}", r"\1", t)     # 중복 문장부호 축약 (?? → ?)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def read_corpus_text(path: str | Path, english_only: bool = True) -> str:
    """PDF/텍스트 파일에서 텍스트를 뽑는다(이미지는 여기선 제외 — API 단계에서 처리).

    english_only=True 면 평가원 워크북의 국문·워터마크를 걷어내고 영어 본문만 남긴다.
    """
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        raw = extract.extract_raw_text(path)
    elif path.suffix.lower() in (".txt", ".md"):
        raw = path.read_text(encoding="utf-8", errors="ignore")
    else:
        return ""
    return extract_english(raw) if english_only else raw


# ── 출처(연·월·문항번호) 추출 ─────────────────────────────
_FILE_META = re.compile(r"(20\d\d).*?(고\s*[123]).*?(\d{1,2})\s*월")
# 문항 마커: 수능/모평 영어 지문은 18~45번
_QNO = re.compile(r"(?<!\d)(1[89]|[2-4]\d)번")


def exam_label(path: str | Path) -> str:
    """파일명에서 시험 라벨을 만든다. 예: '2024_고3_6월.pdf' → '2024 고3 6월'."""
    name = Path(path).stem
    m = _FILE_META.search(name.replace("_", " "))
    if m:
        year, grade, month = m.group(1), m.group(2).replace(" ", ""), m.group(3)
        return f"{year} {grade} {month}월"
    return name


_CLAUSE = re.compile(r"\b(who|which|that|whose|where|when|because|although|while|"
                     r"\w+ing|\w+ed)\b", re.IGNORECASE)


def estimate_difficulty(sentence: str) -> str:
    """길이·콤마·절 표지로 '중'/'고' 난이도를 어림한다(휴리스틱)."""
    n = len(sentence)
    commas = sentence.count(",")
    clauses = len(_CLAUSE.findall(sentence))
    score = n / 55 + commas + clauses * 0.6
    return "고" if (n >= 135 or commas >= 3 or score >= 6) else "중"


@dataclass
class SourcedSentence:
    text: str
    source: str = ""     # 예: '2024 고3 6월 23번'
    difficulty: str = ""

    def graded(self):
        if not self.difficulty:
            self.difficulty = estimate_difficulty(self.text)
        return self


def _sourced_from_file(f: Path) -> list[SourcedSentence]:
    """한 파일 → (문항번호가 달린) 문장 목록. 문항 마커로 분할해 출처를 붙인다."""
    label = exam_label(f)
    raw = read_corpus_text(f, english_only=False)  # 문항 마커(한글) 보존을 위해 원문에서 분할
    if not raw:
        return []
    out: list[SourcedSentence] = []
    parts = _QNO.split(raw)
    # parts = [pre, qno, seg, qno, seg, ...] — 앞부분(pre)은 문항번호 미상
    if len(parts) == 1:
        for s in split_sentences(extract_english(raw)):
            out.append(SourcedSentence(text=s, source=label))
        return out
    # pre 구간
    for s in split_sentences(extract_english(parts[0])):
        out.append(SourcedSentence(text=s, source=label))
    for i in range(1, len(parts) - 1, 2):
        qno, seg = parts[i], parts[i + 1]
        src = f"{label} {qno}번"
        for s in split_sentences(extract_english(seg)):
            out.append(SourcedSentence(text=s, source=src))
    return out


def collect_sourced(corpus_dir: str | Path) -> list[SourcedSentence]:
    """corpus_dir 의 모든 파일 → 출처가 달린 문장 목록(중복 제거)."""
    corpus_dir = Path(corpus_dir)
    seen: set[str] = set()
    out: list[SourcedSentence] = []
    if not corpus_dir.exists():
        return out
    for f in sorted(corpus_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() not in (".pdf", ".txt", ".md"):
            continue
        for ss in _sourced_from_file(f):
            key = re.sub(r"\s+", " ", ss.text.lower()).strip()
            if key not in seen:
                seen.add(key)
                out.append(ss)
    return out


def collect_sentences(corpus_dir: str | Path) -> list[str]:
    """corpus_dir 안의 모든 파일에서 문장만 모아 중복 제거(출처 없이)."""
    return [ss.text for ss in collect_sourced(corpus_dir)]


@dataclass
class Passage:
    text: str            # 지문 전체(영어)
    source: str = ""     # 예: '2024 고3 6월 23번'


def collect_passages(corpus_dir: str | Path, min_words: int = 40) -> list[Passage]:
    """문항 단위로 '지문 전체'를 모은다(패러프레이징 파트용 — 지문 통째 학습)."""
    corpus_dir = Path(corpus_dir)
    out: list[Passage] = []
    if not corpus_dir.exists():
        return out
    for f in sorted(corpus_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() not in (".pdf", ".txt", ".md"):
            continue
        buckets: dict[str, list[str]] = {}
        order: list[str] = []
        for ss in _sourced_from_file(f):
            buckets.setdefault(ss.source, []).append(ss.text)
            if ss.source not in order:
                order.append(ss.source)
        for src in order:
            text = " ".join(buckets[src]).strip()
            if len(text.split()) >= min_words:
                out.append(Passage(text=text, source=src))
    return out


def _as_sourced(items) -> list[SourcedSentence]:
    """list[str] 또는 list[SourcedSentence] 를 SourcedSentence 목록으로 정규화."""
    out = []
    for it in items:
        out.append(it if isinstance(it, SourcedSentence) else SourcedSentence(text=str(it)))
    return out


@dataclass
class Match:
    code: Code
    sentence: str
    hit: str        # 문장에서 실제 매칭된 부분
    source: str = ""


def match_category(category: Category, sentences, per_code: int = 1) -> list[Match]:
    """한 카테고리의 각 코드에 대해, 그 코드가 든 문장을 per_code 개까지 모은다.

    sentences 는 list[str] 또는 list[SourcedSentence] 둘 다 허용(출처 보존).
    → 결과가 곧 '유형별로 모인 기출 문장'.
    """
    pool = _as_sourced(sentences)
    matches: list[Match] = []
    used: set[str] = set()
    for code in category.codes:
        found = 0
        for ss in pool:
            if ss.text in used:
                continue
            hit = code.matches(ss.text)
            if hit:
                matches.append(Match(code=code, sentence=ss.text, hit=hit, source=ss.source))
                used.add(ss.text)
                found += 1
                if found >= per_code:
                    break
    return matches
