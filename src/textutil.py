"""가벼운 텍스트 유틸 (무거운 의존성 없음).

지문을 '완전한 문장' 단위로 나눠, 프롬프트에 '그대로 쓸 문장 목록'으로 넘기기 위한 것.
LLM 이 문장 앞부분(주어·도입구)을 임의로 잘라내는 문제를 구조적으로 막는다.
"""
from __future__ import annotations

import hashlib
import random
import re


def shuffle_choices(display: str, seed_text: str) -> str:
    """선택형 보기 '[ A / B (/ C) ]'(지칭은 '= [ … ]')의 순서를 섞는다.

    LLM 이 정답을 늘 앞쪽에 배치하는 편향이 있어 정답 위치가 한쪽으로 쏠린다. 정답은
    '텍스트'로 채점되므로(위치 무관) 보기 순서를 바꿔도 정오에 영향이 없다.
    시드가 '내용 기반'이라 같은 문항은 항상 같은 배치(재생성·테스트 재현성)이되, 문항마다
    위치가 고르게 분포한다. '(원형)'·'〈 … 〉' 같은 비[]선택형 display 는 그대로 둔다.
    """
    s = display.strip()
    prefix = ""
    if s.startswith("="):                       # 지칭 '= [ … ]'
        prefix = "= "
        s = s[1:].strip()
    if not (s.startswith("[") and s.endswith("]")):
        return display                          # (원형)·〈 … 〉 등 비[]선택형은 그대로
    opts = [o.strip() for o in s[1:-1].split("/") if o.strip()]
    if len(opts) < 2:
        return display
    seed = int.from_bytes(hashlib.md5(seed_text.encode("utf-8")).digest()[:8], "big")
    order = opts[:]
    random.Random(seed).shuffle(order)
    return prefix + "[ " + " / ".join(order) + " ]"


def _norm_seq(s: str) -> str:
    """어순 비교용 정규화(소문자·영숫자만, 공백 1칸)."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def shuffle_order_display(display: str, answer: str = "") -> str:
    """순서배열 어구 '〈 a / b / c 〉' 를 '정답 어순과도 다르게' 다시 섞는다.

    LLM 이 순서배열을 '정답 순서 그대로' 내보내면(예: 〈 It / was / not / until … 〉 정답
    "It was not until …") 문제가 무의미해진다. 정답 어순·입력 순서 둘 다와 다를 때까지 섞는다.
    '〈 … 〉' 형식이 아니면 그대로 둔다.
    """
    s = display.strip()
    if not (s.startswith("〈") and s.endswith("〉")):
        return display
    parts = [p.strip() for p in s[1:-1].split("/") if p.strip()]
    if len(parts) < 2:
        return display
    correct = _norm_seq(answer) if answer and answer.strip() else _norm_seq(" ".join(parts))
    order = parts[:]
    for _ in range(20):
        random.shuffle(order)
        if order != parts and _norm_seq(" ".join(order)) != correct:
            break
    return "〈 " + " / ".join(order) + " 〉"

# 마침표가 문장 끝이 아닌 흔한 약어(뒤에 대문자가 와도 문장 분리하면 안 됨)
_ABBR = [
    "e.g.", "i.e.", "etc.", "vs.", "cf.", "al.", "Mr.", "Mrs.", "Ms.",
    "Dr.", "Prof.", "St.", "Fig.", "No.", "U.S.", "U.K.", "a.m.", "p.m.",
]
_SENT_BOUNDARY = re.compile(r'(?<=[.!?])["”’)\]]?\s+(?=[A-Z"“‘(\[])')


# 이름 이니셜(예: "Paul R. Ehrlich", "George W. Bush", "J. K. Rowling")의 마침표.
#   '앞에 다른 글자가 붙지 않은 대문자 한 글자 + 마침표'는 문장 끝이 아니라 이니셜로 본다.
_INITIAL = re.compile(r'(?<![A-Za-z])([A-Z])\.')


def split_sentences(text: str) -> list[str]:
    """영어 지문을 완전한 문장 리스트로 분리(문장 끝부호 유지, 약어·이니셜 보호)."""
    if not text:
        return []
    t = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    # 약어의 마침표를 임시로 치환해 분리 대상에서 제외
    for ab in _ABBR:
        t = t.replace(ab, ab.replace(".", "\x00"))
    # 이름 이니셜의 마침표도 보호(예: "Paul R. Ehrlich" 를 "Paul R." 와 "Ehrlich…" 로 쪼개지 않게)
    t = _INITIAL.sub(lambda m: m.group(1) + "\x00", t)
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


def _norm_word(w: str) -> str:
    return w.strip(".,;:'\"()[]?!’“”").lower()


def dedup_placeholder(template: str, marker: str, answer: str) -> str:
    """자리표시자(marker) 바로 앞/뒤에 정답(answer)과 '겹치는 단어'가 남아 있으면 제거한다.

    통합카드 등에서 배열/어형 문항을 만들 때, 정답 어구를 자리표시자로 바꾸고도 그 어구를
    문장 본문에 그대로 남겨 '중복'되는 오류를 정리한다.
      예) "estimate how long a resource {{Q}}"  answer "how long a resource would last"
          → "estimate {{Q}}" (앞의 'how long a resource' 중복 제거)
      예) "might {{Q}} run"  answer "be run"  → "might {{Q}}" (뒤의 'run' 중복 제거)
    실제로 겹칠 때만 제거하므로(정답 경계 단어와 정확히 일치) 일반 문장은 건드리지 않는다.
    """
    if marker not in template or not (answer or "").strip():
        return template
    before, after = template.split(marker, 1)
    ans = [_norm_word(w) for w in answer.split()]
    if not ans:
        return template
    bt = before.split()
    at = after.split()
    # 앞부분의 끝 k개가 정답의 앞 k개와 같으면(중복) 제거
    for k in range(min(len(bt), len(ans)), 0, -1):
        if [_norm_word(x) for x in bt[-k:]] == ans[:k]:
            bt = bt[:-k]
            break
    # 뒷부분의 앞 j개가 정답의 끝 j개와 같으면(중복) 제거
    for j in range(min(len(at), len(ans)), 0, -1):
        if [_norm_word(x) for x in at[:j]] == ans[-j:]:
            at = at[j:]
            break
    # 부사(…ly) 하나가 낀 '비인접' 중복도 제거: "{{Q}} usually respond"(정답 끝 'respond'),
    #   "{{Q}} sufficiently comforted"(정답 끝 'comforted'). 부사는 남기고 중복 동사만 뺀다.
    if len(at) >= 2 and at[0].lower().endswith("ly") and _norm_word(at[1]) == ans[-1]:
        at = [at[0]] + at[2:]
    left = (" ".join(bt) + " ") if bt else ""
    right = (" " + " ".join(at)) if at else ""
    result = left + marker + right
    result = re.sub(r"\s+([.,;:!?’”)])", r"\1", result)   # 구두점 앞 공백 제거
    return re.sub(r"\s{2,}", " ", result).strip()


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


def qno_label(source: str) -> str:
    """파일명 등에서 '문항 번호'만 'NN번' 형태로 뽑는다(LLM 추출 실패 시의 보조 수단).

    확실한 신호(예: '30번', '_30_', '문항 30')만 잡고, 못 찾으면 빈 문자열.
    LLM 추출(q_no)이 1순위이고 이 함수는 fallback 이다.
    """
    s = (source or "").strip()
    if not s:
        return ""
    base = _UUID_PREFIX.sub("", s)
    base = re.sub(r'\.[A-Za-z0-9]{1,5}$', "", base)
    m = _QNUM.search(base)                       # 'NN번'
    if m:
        return f"{m.group(1)}번"
    m = re.search(r'문항\s*([1-9][0-9]?)', base)   # '문항 NN'
    if m:
        return f"{m.group(1)}번"
    m = re.search(r'(?:^|[_\s-])([1-9][0-9]?)(?:[_\s-]|$)', base)  # 구분자로 둘러싸인 번호
    if m:
        return f"{m.group(1)}번"
    return ""


_UNIT_EN = re.compile(r'[Uu]nit\s*0*([0-9]+)')      # "Unit 10"
_UNIT_KO = re.compile(r'([0-9]+)\s*과')             # "10과"
_DESC_LABELS = ("서술형", "논술형")                    # 번호 대신 그대로 두는 라벨


def _unit_of(*texts: str) -> str:
    """여러 텍스트에서 '단원(Unit) 번호'만 뽑는다(예: 'Ch. 04 Unit 10' → '10')."""
    for t in texts:
        m = _UNIT_EN.search(t or "") or _UNIT_KO.search(t or "")
        if m:
            return m.group(1)
    return ""


def format_qno(q_no: str, *hints: str) -> str:
    """지문 라벨을 '단원-문항' 형식으로 정규화한다.

    예: q_no '1번' + 힌트 'Ch. 04 Unit 10' → '10-1'
        ANALYSIS(수능대비 분석) 지문 → '10-A'
        '서술형' / '논술형' 은 그대로 둔다.
    - LLM 이 이미 '10-1' / '10-A' 형태로 주면 그대로 사용한다.
    - 단원/문항을 못 정하면 빈 문자열을 돌려준다(상위 fallback 이 처리).
    """
    s = (q_no or "").strip()
    if re.fullmatch(r'[0-9]+-([0-9]+|[A-Za-z])', s):   # 이미 최종 형식(10-1, 10-A)
        return s
    if s in _DESC_LABELS:
        return s
    blob = " ".join([s, *[h or "" for h in hints]])
    for d in _DESC_LABELS:                              # 서술형/논술형은 그대로
        if d in blob:
            return d
    unit = _unit_of(s, *hints)
    # 문항 식별: 'N번' → N, ANALYSIS → A
    m = re.search(r'([0-9]+)\s*번', s) or re.search(r'([0-9]+)\s*번', blob)
    item = m.group(1) if m else ("A" if re.search(r'analysis', blob, re.I) else "")
    if unit and item:
        return f"{unit}-{item}"
    if item:                                           # 단원 못 찾음 → 문항만
        return item if item == "A" else f"{item}번"
    return ""                                           # 판단 불가 → 상위 fallback


def file_tag(name: str, maxlen: int = 16) -> str:
    """파일명에서 뱃지에 쓸 '짧은 식별자'를 만든다.

    UUID 접두·확장자 제거 후, 지문번호와 '중복되는 번호 토큰'(예: '30~40번', '30-40', '30번',
    '문항 30')은 제거한다 → 뱃지가 '파일명 · 30번'에서 파일명이 또 '30~40번'이 되는 중복을 방지.
    번호를 빼고 남는 설명이 없으면 빈 문자열을 돌려준다(그러면 뱃지는 지문번호만 표시).
    """
    s = (name or "").strip()
    if not s:
        return ""
    base = _UUID_PREFIX.sub("", s)
    base = re.sub(r'\.[A-Za-z0-9]{1,5}$', "", base)      # 확장자 제거
    # 번호 토큰 제거: '30~40번', '30-40번', '30~40', '30번', '문항 30' 등
    base = re.sub(r'문항\s*\d+', " ", base)
    base = re.sub(r'\d+\s*[~\-–]\s*\d+\s*번?', " ", base)
    base = re.sub(r'(?<![A-Za-z])\d+\s*번', " ", base)
    base = re.sub(r'\s*[,·]\s*', " ", base)             # 쉼표·가운뎃점 → 공백
    base = re.sub(r'\s+', " ", base).strip(" _-,·")
    base = re.sub(r'^번\s*', "", base)                  # 맨 앞 고아 '번'(번호 제거 잔여) 정리
    base = base.strip(" _-,·")
    if len(base) > maxlen:
        base = base[:maxlen].rstrip(" _-") + "…"
    return base
