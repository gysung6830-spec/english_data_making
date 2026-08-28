"""텍스트 → 지문/문장 파싱.

지문 구분 = 문제 번호 헤더 한 줄 (예: "[고3] 2026년 5월 - 26번: 제목").
문장 구분 = 원문자 ①②③…⑳.
영어/한글 분리 = 줄 단위 판별(한글 2자 이상 → 해석).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

# ── 데이터 모델 ────────────────────────────────────────────────

@dataclass
class Chunk:
    en: str          # 영어 청크(구~절 사이 의미 단위)
    ko: str          # 그 청크의 우리말 뜻


_ALNUM_RE = re.compile(r"[0-9A-Za-z]")


def _letters(s: str) -> str:
    """영숫자만 남긴 문자열(문장부호·공백 정규화 비교용)."""
    return "".join(_ALNUM_RE.findall(s or ""))


# 강제 '~다' 종결로 '다다'가 중복된 경우(예: 고양이보다→보다다, 있다→있다다)
_DUP_DA_RE = re.compile(r"다다(?=[\s.!?…)\]\"'”’》」』]*$)")
# 비술어(전치사구 등)에 억지로 '다'를 붙여 딱딱해진 종결
#  (…에서다/…위해서다/…있어서다/…대해서다/…통해서다/…로서다 → 끝의 '다' 제거)
_STIFF_END_RE = re.compile(
    r"(에서|에게서|께서|위해서|위하여서|대해서|관해서|통해서|있어서|없어서|"
    r"로서|으로서|로써|으로써)다(?=[\s.!?…)\]\"'”’》」』]*$)"
)


def tidy_chunk_ko(ko: str) -> str:
    """직독직해 청크 뜻의 흔한 오타·번역투 정리.

    (1) '마지막 조각은 ~다로 끝내라'는 지시 때문에 이미 '다'로 끝나는 말
        ('보다', '있다'…)에 '다'를 한 번 더 붙인 '다다'를 하나로 줄인다.
    (2) 전치사구 등 비술어에 억지로 '다'를 붙여 딱딱해진 종결
        ('…중에서다', '…있어서다')에서 끝의 '다'를 떼어 자연스럽게 만든다.
    """
    ko = (ko or "").strip()
    ko = _DUP_DA_RE.sub("다", ko)
    ko = _STIFF_END_RE.sub(lambda m: m.group(1), ko)
    return ko


# 규칙 기반 끊어읽기(폴백): AI 청크 생성 실패 시 최소한의 의미 단위로 나눔
_BREAK_BEFORE = {
    "that", "which", "who", "whom", "whose", "where", "when", "why",
    "because", "if", "although", "though", "while", "since", "unless",
    "and", "but", "so", "or", "nor", "yet",
}
# 조각이 이미 길 때(5단어+)만 그 앞에서 끊는 전치사류
_BREAK_BEFORE_LONG = {
    "in", "of", "for", "on", "at", "with", "to", "from", "into",
    "as", "than", "by", "about", "through", "between", "along",
}


def rough_sense_split(en: str) -> List[str]:
    """영어 문장을 규칙만으로 의미 단위(구~절)로 대략 끊는다.

    AI 청크 생성이 실패한 긴 문장에 최소한의 끊어읽기를 제공하기 위한 폴백.
    콤마·대시 뒤, 절/등위접속사·관계사 앞, 문장 내부 마침표 뒤에서 끊고,
    너무 짧은 조각(2단어 미만)은 앞 조각에 붙인다. 원문은 그대로 보존된다.
    """
    words = en.split()
    if len(words) <= 6:
        return [en.strip()] if en.strip() else []
    chunks: List[List[str]] = []
    cur: List[str] = []
    for w in words:
        bare = w.strip(".,;:!?\"'()—–").lower()
        # 절/등위접속사·관계사 앞에서 끊기, 또는 조각이 길면 전치사 앞에서도 끊기
        if (bare in _BREAK_BEFORE and len(cur) >= 3) or \
           (bare in _BREAK_BEFORE_LONG and len(cur) >= 5):
            chunks.append(cur)
            cur = [w]
        else:
            cur.append(w)
        # 콤마·대시·문장내 마침표 뒤에서 끊기
        if re.search(r"[,—–]$", w) or re.search(r"[.!?]$", w):
            if len(cur) >= 3:
                chunks.append(cur)
                cur = []
    if cur:
        chunks.append(cur)
    # 너무 짧은 조각은 이웃에 병합
    merged: List[List[str]] = []
    for c in chunks:
        if merged and len(c) < 2:
            merged[-1].extend(c)
        else:
            merged.append(c)
    return [" ".join(c) for c in merged if c]


def realign_chunks(en: str, chunks: List["Chunk"]) -> List["Chunk"]:
    """직독직해 청크의 영어 텍스트를 원문(en)에서 '그대로' 다시 잘라 맞춘다.

    AI가 돌려준 청크는 끊는 위치는 좋아도 문장부호(따옴표·대시 공백·마침표)가
    원문과 미세하게 달라질 수 있다. 끊는 경계(글자 수)는 그대로 두고 각 청크의
    실제 텍스트만 원문에서 잘라오면, 조각을 이어 붙였을 때 원문과 100% 일치한다.
    글자(영숫자) 순서가 원문과 다르면(=단어가 실제로 다르면) 영어는 원본을 두되,
    한글 뜻('다다' 중복 등)은 항상 정리한다.
    """
    if not chunks:
        return chunks
    if _letters("".join(c.en for c in chunks)) != _letters(en):
        # 청크가 원문과 글자 수준으로 다르면(AI가 단어를 넣거나 뺌) 원문을 신뢰한다.
        # 규칙 기반으로 다시 끊어 영어가 항상 원문과 100% 일치하게 함(뜻은 문장 전체 사용).
        pieces = rough_sense_split(en)
        return [Chunk(en=p, ko="") for p in pieces] or \
            [Chunk(en=en.strip(), ko="")]

    # 각 청크의 원문 내 경계(start, end)를 구한다(연속 슬라이스).
    bounds: List[Tuple[int, int]] = []
    pos, n = 0, len(chunks)
    for i, c in enumerate(chunks):
        if i == n - 1:
            bounds.append((pos, len(en)))
        else:
            need = len(_letters(c.en))
            j, cnt = pos, 0
            while j < len(en) and cnt < need:
                if en[j].isalnum():
                    cnt += 1
                j += 1
            # 글자 뒤에 붙는 문장부호(공백 아닌)는 앞 청크에 붙인다
            while j < len(en) and not en[j].isalnum() and en[j] != " ":
                j += 1
            bounds.append((pos, j))
            pos = j

    # 경계가 '단어 중간'(양쪽이 모두 글자)이면 앞 청크와 병합(clich/és 방지).
    kos = [tidy_chunk_ko(c.ko) for c in chunks]
    m_bounds: List[Tuple[int, int]] = [bounds[0]]
    m_kos: List[str] = [kos[0]]
    for i in range(1, len(bounds)):
        s, e = bounds[i]
        b = m_bounds[-1][1]  # 앞 청크 끝 = 이 청크 시작
        if 0 < b < len(en) and en[b - 1].isalnum() and en[b].isalnum():
            m_bounds[-1] = (m_bounds[-1][0], e)          # 병합
            m_kos[-1] = (m_kos[-1] + " " + kos[i]).strip()
        else:
            m_bounds.append((s, e))
            m_kos.append(kos[i])

    return [Chunk(en=en[s:e].strip(), ko=k)
            for (s, e), k in zip(m_bounds, m_kos)]


@dataclass
class Sentence:
    num: int        # 문장 번호 (①→1)
    en: str         # 영어 원문
    ko: str = ""    # 한글 해석 (없으면 빈 문자열)
    chunks: List["Chunk"] = field(default_factory=list)  # 직독직해용 청크


@dataclass
class Vocab:
    word: str        # 영어 단어/표현
    meaning: str     # 한글 뜻(문맥상)


@dataclass
class Passage:
    label: str                              # "[고3] 2026년 5월 - 26번"
    title: str                              # 제목/주제
    sentences: List[Sentence] = field(default_factory=list)
    vocab: List[Vocab] = field(default_factory=list)  # 하단 어휘 리스트
    raw: str = ""                           # 번호 없는 지문 원문(문장 자동분리용)


# ── 정규식/상수 ───────────────────────────────────────────────

# 원문자: ①~⑳(U+2460~2473), ㉑~㉟(U+3251~325F), ㊱~㊿(U+32B1~32BF)
CIRCLED = (
    "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
    "㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟"
    "㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿"
)
_CIRCLED_BASE = 0x2460  # ① (하위호환용 상수)
CIRCLED_SET = set(CIRCLED)

# 지문 헤더:  [ ... ] ... N번 : 제목
#   그룹1 = 라벨( [고3] 2026년 5월 - 26번 ), 그룹2 = 번호, 그룹3 = 제목
HEADER_RE = re.compile(
    r"(\[[^\]]*\][^:：\n]*?(\d+)\s*번)\s*[:：]\s*(.*)"
)

# 대체 헤더:  '31번 …' / '41~42번 …' / '43~45번 …' 처럼 줄이 'N번' 또는
#   범위 'N~M번'으로 시작하는 형식 (EXAM4YOU 워크북 등. 콜론/대괄호 없음)
HEADER_RE2 = re.compile(r"^\s*(\d{1,3}(?:\s*[~∼\-]\s*\d{1,3})?)\s*번\b(.*)$")

# 대체 헤더:  'Ch. 05 Unit 13 - 1번: 제목' / 'Ch. 05 Unit 13 - 수능 대비 ANALYSIS: 제목'
#   (올림포스 등. Ch/Chapter/Unit/Lesson + 숫자로 시작하고 콜론이 있는 줄)
HEADER_RE3 = re.compile(
    r"(?i)^\s*((?:ch(?:apter)?|unit|lesson)\.?\s*\d[^:：\n]*?)\s*[:：]\s*(.+)$"
)

# 아라비아 숫자 문장 번호:  줄 시작의 'N. ' (원문자 대신 쓰는 자료)
_ARABIC_MARK_RE = re.compile(r"(?m)^[ \t]*(\d{1,2})\.[ \t]+")

# 각주 참조:  문장 끝의 '1)' '2)' 같은 위첨자 표기 제거
_FOOTNOTE_RE = re.compile(r"\s*\d{1,3}\)\s*$")

# 페이지 번호 줄:  '- 14 -', '14' 등
_PAGENUM_RE = re.compile(r"^\s*[-–—]?\s*\d{1,4}\s*[-–—]?\s*$")

# 자료 머리말/꼬리말·안내문(워터마크) 줄
_JUNK_RE = re.compile(
    r"(?i)(flowedu\.tistory|\[\s*flow\s*edu\s*\]|^\s*\[EBS\]|EXAM4YOU|"
    r"영문과\s*해석을\s*읽고|지문\s*연습하기|^\s*WORKBOOK\b|"
    r"한\s*줄\s*해석|한\s*줄\s*영어|좌지문\s*우?\s*해석|직독\s*직해)"
)

# 자료 러닝 헤더/푸터(예: '[고3] 2026년 6월 모의고사 한줄해석')가 문장에 섞인 것
_MATERIAL_HDR_RE = re.compile(
    r"\[?\s*고\s*\d\s*\]?\s*\d{4}\s*년\s*\d{1,2}\s*월\s*"
    r"(?:모의고사|모의평가|학력평가)?\s*"
    r"(?:한\s*줄\s*해석|한\s*줄\s*영어|좌지문\s*우?\s*해석|직독\s*직해)\s*\d*"
)


def _strip_material_header(s: str) -> str:
    """문장에 섞여 들어온 자료 러닝 헤더/푸터 텍스트를 제거."""
    return _re_sub_collapse(_MATERIAL_HDR_RE.sub(" ", s or ""))


# 문장 앞에 붙은 자료 라벨: '[Summary]', '[요약]', '[요약문]', '[Paraphrase]' 등
_LEAD_LABEL_RE = re.compile(
    r"^\s*\[\s*(?:summary|abstract|paraphrase|요약문?|주제문?)\s*\]\s*", re.I
)


def _strip_lead_label(s: str) -> str:
    """문장 맨 앞의 자료 라벨('[Summary]' 등)을 제거."""
    return _LEAD_LABEL_RE.sub("", s or "").strip()


def _re_sub_collapse(s: str) -> str:
    return re.sub(r"\s{2,}", " ", s).strip()

# 한글 음절 영역
_HANGUL_RE = re.compile(r"[가-힣]")

# 정상 제목 최대 길이(이보다 길면 2단 표 뒤섞임으로 보고 원문 파싱으로 되돌림)
_MAX_TITLE_LEN = 150


def circled_to_int(ch: str) -> int:
    """원문자 → 정수. ①→1 … ⑳→20, ㉑→21 … ㉟→35, ㊱→36 … ㊿→50. 아니면 0."""
    o = ord(ch)
    if 0x2460 <= o <= 0x2473:   # ①~⑳
        return o - 0x2460 + 1
    if 0x3251 <= o <= 0x325F:   # ㉑~㉟
        return o - 0x3251 + 21
    if 0x32B1 <= o <= 0x32BF:   # ㊱~㊿
        return o - 0x32B1 + 36
    return 0


def _count_hangul(s: str) -> int:
    return len(_HANGUL_RE.findall(s))


def _is_korean_line(line: str) -> bool:
    """한글이 2자 이상 포함된 줄 → 한글 해석으로 간주."""
    return _count_hangul(line) >= 2


def _split_mixed_line(line: str) -> Tuple[str, str]:
    """한 줄에 영/한이 섞이면 한글 첫 등장 위치에서 분리.

    반환: (영어부분, 한글부분).
    """
    m = _HANGUL_RE.search(line)
    if not m:
        return line.strip(), ""
    idx = m.start()
    return line[:idx].strip(), line[idx:].strip()


def _split_en_ko(chunk: str) -> Tuple[str, str]:
    """문장 조각(원문자 제거된 본문) → (영어, 한글).

    - 한글 없는 줄 → 영어.
    - 한글 있는 줄:
        · 아직 영어를 못 잡았고 앞부분이 영어면 → 같은 줄에 영/한이 섞인
          경우로 보고 한글 첫 등장 위치에서 분리.
        · 이미 영어 줄을 잡았다면 → 그 줄 전체가 한글 해석(영어 고유명사가
          섞여 있어도 통째로 해석으로 둠).
    """
    en_parts: List[str] = []
    ko_parts: List[str] = []
    for raw_line in chunk.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _PAGENUM_RE.match(line):
            continue  # 페이지 번호 줄('- 14 -' 등) 무시
        if _JUNK_RE.search(line):
            continue  # [EBS]/[Flow Edu] 머리말·꼬리말 무시
        if _is_korean_line(line):
            if not en_parts:
                # 아직 영어를 못 잡음 → 같은 줄 혼합 가능성. 분리 시도.
                en, ko = _split_mixed_line(line)
                if en:
                    en_parts.append(en)
                if ko:
                    ko_parts.append(ko)
            else:
                # 영어는 이미 별도 줄에서 잡음 → 이 줄은 통째로 해석.
                ko_parts.append(line)
        else:
            en_parts.append(line)
    en = " ".join(p.strip() for p in en_parts if p.strip())
    ko = " ".join(p.strip() for p in ko_parts if p.strip())
    return en.strip(), ko.strip()


def _strip_footnote(s: str) -> str:
    """문장 끝의 각주 참조('...related.1)')를 제거."""
    return _FOOTNOTE_RE.sub("", s).rstrip()


def _parse_sentences(body: str) -> List[Sentence]:
    """지문 본문 → 문장 리스트.

    문장 번호는 원문자(①②)를 우선 인식하고, 없으면 아라비아 숫자('1.' '2.')
    를 인식한다. 같은 번호가 두 번 나오면(영어줄 + 한글줄) 하나로 병합한다.
    """
    # (마커 시작, 본문 시작, 번호)
    marks: List[Tuple[int, int, int]] = []
    for i, ch in enumerate(body):
        n = circled_to_int(ch)
        if n:
            marks.append((i, i + 1, n))

    # 원문자가 없으면 아라비아 숫자 문장번호로 대체
    if not marks:
        for m in _ARABIC_MARK_RE.finditer(body):
            marks.append((m.start(), m.end(), int(m.group(1))))
        marks.sort()

    if not marks:
        return []

    # 마커 앞의 서두(헤더/안내문 잔여물)는 버린다.
    chunks: List[Tuple[int, str]] = []
    for k, (ms, cs, num) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body)
        chunks.append((num, body[cs:end]))

    # 번호 순서대로 병합
    merged: "dict[int, List[str]]" = {}
    order: List[int] = []
    for num, text in chunks:
        if num not in merged:
            merged[num] = []
            order.append(num)
        merged[num].append(text)

    sentences: List[Sentence] = []
    for num in order:
        combined = "\n".join(merged[num])
        en, ko = _split_en_ko(combined)
        en = _strip_lead_label(_strip_material_header(_strip_footnote(en)))
        ko = _strip_lead_label(_strip_material_header(ko))
        if not en and not ko:
            continue
        sentences.append(Sentence(num=num, en=en, ko=ko))
    return sentences


def _clean_title(s: str) -> str:
    """제목 문자열 정리(구분자·중복 공백 정돈)."""
    s = s.replace("┃", " · ").replace("|", " · ")
    s = " ".join(s.split())
    return s.strip(" -–—·:：")


def _match_header(line: str):
    """헤더 줄이면 (라벨, 제목) 반환, 아니면 None."""
    m = HEADER_RE.search(line)
    if m:
        return m.group(1).strip(), m.group(3).strip()
    m = HEADER_RE2.match(line)
    if m:
        rest = m.group(2)
        # 'N번' 뒤에 실제 제목/설명이 있어야 헤더로 인정(문장 오인 방지)
        if _count_hangul(rest) >= 2 or len(rest.strip()) >= 4:
            # 범위(41~42) 정규화: 구분자 주변 공백 제거
            num = re.sub(r"\s*[~∼\-]\s*", "~", m.group(1))
            return f"{num}번", _clean_title(rest)
    m = HEADER_RE3.match(line)
    if m:
        return _clean_title(m.group(1)), _clean_title(m.group(2))
    return None


def _starts_with_marker(line: str) -> bool:
    """줄이 문장 번호(원문자 또는 'N. ')로 시작하는가."""
    s = line.lstrip()
    if not s:
        return False
    if s[0] in CIRCLED_SET:
        return True
    return bool(re.match(r"\d{1,2}\.[ \t]", s))


def split_passages(raw: str) -> List[Passage]:
    """텍스트 전체 → 지문 리스트."""
    if not raw:
        return []

    # PDF 추출에서 섞이는 널문자/소프트하이픈을 공백으로 정규화
    raw = raw.replace("\x00", " ").replace("\xad", " ")

    lines = raw.splitlines()

    # 헤더 줄 위치 찾기
    header_idx: List[Tuple[int, str, str]] = []  # (줄번호, label, title)
    for i, line in enumerate(lines):
        hm = _match_header(line)
        if hm:
            header_idx.append((i, hm[0], hm[1]))

    passages: List[Passage] = []

    if not header_idx:
        # 헤더가 전혀 없으면 전체를 한 지문으로 취급(라벨/제목 비움)
        sents = _parse_sentences(raw)
        if sents:
            passages.append(Passage(label="", title="", sentences=sents))
        return passages

    for k, (line_no, label, title) in enumerate(header_idx):
        body_start = line_no + 1
        body_end = header_idx[k + 1][0] if k + 1 < len(header_idx) else len(lines)
        body_lines = lines[body_start:body_end]

        body = "\n".join(body_lines)
        sents = _parse_sentences(body)
        # 번호가 없어 문장을 못 나눈 경우, 원문(잡음 제거)을 남겨 AI 문장분리에 사용
        raw = "" if sents else _clean_raw(body_lines)

        # 제목이 다음 줄로 이어지는 경우: 문장 마커가 있는 자료에서만 이어붙임
        # (번호 없는 통짜 지문은 본문 전체가 제목에 딸려가는 것을 방지)
        if sents:
            extra = []
            for bl in body_lines:
                if _starts_with_marker(bl):
                    break
                s = bl.strip()
                if s and not _JUNK_RE.search(s):
                    extra.append(s)
            if extra:
                title = _clean_title((title + " " + " ".join(extra)).strip())

        # 워크북 안내문 등 보일러플레이트만 있는 제목은 비운다
        if title and _JUNK_RE.search(title):
            title = ""

        # 제목이 비정상적으로 길면(2단 표가 뒤섞여 지문 전체가 딸려온 경우)
        # 파싱된 문장들도 어긋난 잡음이므로, 원문(raw)으로 되돌려 AI 문장분리에 맡김
        if sents and len(title) > _MAX_TITLE_LEN:
            raw = _clean_raw(body_lines)
            sents = []
            title = ""

        # 같은 번호 헤더가 다음 페이지에 반복되면(장문 등) 이전 지문에 이어붙임
        if passages and label and passages[-1].label == label:
            passages[-1].sentences.extend(sents)
            if raw:
                passages[-1].raw = (passages[-1].raw + " " + raw).strip()
            if not passages[-1].title and title:
                passages[-1].title = title
        else:
            passages.append(Passage(label=label, title=title,
                                   sentences=sents, raw=raw))

    return passages


def _clean_raw(body_lines: List[str]) -> str:
    """번호 없는 지문 원문에서 안내문·페이지번호·널문자 등을 제거."""
    out = []
    for ln in body_lines:
        s = ln.replace("\x00", " ").strip()
        if not s or _JUNK_RE.search(s) or _PAGENUM_RE.match(s):
            continue
        out.append(s)
    return " ".join(out).strip()
