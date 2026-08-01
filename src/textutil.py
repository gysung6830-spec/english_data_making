"""가벼운 텍스트 유틸 (무거운 의존성 없음).

지문을 '완전한 문장' 단위로 나눠, 프롬프트에 '그대로 쓸 문장 목록'으로 넘기기 위한 것.
LLM 이 문장 앞부분(주어·도입구)을 임의로 잘라내는 문제를 구조적으로 막는다.
"""
from __future__ import annotations

import re

# 마침표가 문장 끝이 아닌 흔한 약어(뒤에 대문자가 와도 문장 분리하면 안 됨)
_ABBR = [
    "e.g.", "i.e.", "etc.", "vs.", "cf.", "al.", "Mr.", "Mrs.", "Ms.",
    "Dr.", "Prof.", "St.", "Fig.", "No.", "U.S.", "U.K.", "a.m.", "p.m.",
]
_SENT_BOUNDARY = re.compile(r'(?<=[.!?])["”’)\]]?\s+(?=[A-Z"“‘(\[])')


def split_sentences(text: str) -> list[str]:
    """영어 지문을 완전한 문장 리스트로 분리(문장 끝부호 유지, 약어 보호)."""
    if not text:
        return []
    t = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    # 약어의 마침표를 임시로 치환해 분리 대상에서 제외
    for ab in _ABBR:
        t = t.replace(ab, ab.replace(".", "\x00"))
    parts = _SENT_BOUNDARY.split(t)
    out = [p.replace("\x00", ".").strip() for p in parts if p.strip()]
    return out


# 모든 생성기(통합·단일유형·빈칸)에 공통으로 붙이는 '교사 검수 느낌' 문체 지침.
STYLE_GUIDE = """[문체 — 경력 있는 교사가 손수 만들고 검수한 자료처럼]
- 해설·근거(reason)는 '교사 채점 노트'처럼 짧고 단정한 개조식(명사형)으로 쓴다.
  좋은 예) "to부정사 → 동사원형", "복수 주어 수일치", "현재완료 수동(have p.p.)".
  금지) "정답은 ~입니다", "이 문장에서는 ~", "~라고 볼 수 있습니다" 같은 완결 서술·군더더기.
- 한글 해석(ko)은 번역기·직역투가 아니라 '내신 교재체의 자연스러운 우리말'로 매끄럽게 쓴다.
  기계번역 느낌의 어색한 어순, "~하는 것이다"의 남발, 불필요한 수동태 직역을 피한다.
- 확신 없는 말투("~인 듯", "일반적으로", "아마도", "~일 수 있다"), 메타 설명(모델·AI 언급),
  이모지, 불필요한 영어 혼용 설명을 쓰지 않는다.
- 전반적으로 'AI가 자동 생성한 티'가 나지 않게 담백하고 실무적으로 쓴다."""


def sentence_list_block(body: str, header: str = "문장 목록") -> str:
    """프롬프트에 붙일 '그대로 쓸 문장 목록' 블록. 문장이 1개 이하면 빈 문자열."""
    sents = split_sentences(body)
    if len(sents) < 2:
        return ""
    lines = "\n".join(f"S{i}) {s}" for i, s in enumerate(sents, start=1))
    return (
        f"[{header} — 아래 문장을 '그대로' 사용하라]\n"
        "아래는 지문을 완전한 문장 단위로 나눈 목록이다. 각 문장을 '하나도 빠뜨리지 말고',\n"
        "'첫 단어부터 끝 문장부호까지 원문 그대로'(자리표시자로 바꾸는 부분만 예외) 순서대로 사용하라.\n"
        "문장의 앞부분(주어·도입구)을 잘라내거나, 한 문장을 여러 조각으로 쪼개지 말 것.\n"
        + lines
    )


# ── 출처(파일명 등) → 문항 라벨 "[고1] 9월 30번" 형태 ──────────────────
_GRADE = re.compile(r'고\s*([1-3])|고등?\s*([1-3])\s*학년|([1-3])\s*학년')
_MONTH = re.compile(r'([1-9]|1[0-2])\s*월')
_QNUM = re.compile(r'([1-9][0-9]?)\s*번')
_UUID_PREFIX = re.compile(r'^[0-9a-fA-F]{6,}-')


def source_label(source: str, fallback: str = "") -> str:
    """출처 문자열(파일명 등)에서 '[고N] M월 K번' 형태의 문항 라벨을 만든다.

    학년/월/문항번호 중 찾은 것만 조합한다. 하나도 못 찾으면 fallback(또는 정리된 원문)을 돌려준다.
    예) "고1_9월_30번.pdf" → "[고1] 9월 30번",  "2024 고3 6월 모의고사 21" → "[고3] 6월"
    """
    s = (source or "").strip()
    if not s:
        return fallback
    base = _UUID_PREFIX.sub("", s)                 # 업로드 UUID 접두 제거
    base = re.sub(r'\.[A-Za-z0-9]{1,5}$', "", base)  # 확장자 제거
    parts: list[str] = []
    mg = _GRADE.search(base)
    if mg:
        g = next((x for x in mg.groups() if x), None)
        if g:
            parts.append(f"[고{g}]")
    mm = _MONTH.search(base)
    if mm:
        parts.append(f"{mm.group(1)}월")
    mq = _QNUM.search(base)
    if mq:
        parts.append(f"{mq.group(1)}번")
    if parts:
        return " ".join(parts)
    # 못 찾으면 정리된 파일명(구분자 정돈, 너무 길면 자름)
    cleaned = re.sub(r'[_]+', " ", base).strip()
    if fallback:
        return fallback
    return (cleaned[:24] + "…") if len(cleaned) > 25 else cleaned
