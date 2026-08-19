"""변형문제 2회(A~G) 변형기. 1회처럼 '정본 문장'에서 파생한다.

- A(어법·어휘): 밑줄 5개 중 오답 2개(어법1+반의어1) → 짝 고르기
- B(함의추론): 한 어구 밑줄 + 한글 의미 선지
- C(어법): 1회 build.make_grammar 재사용(복수정답)
- D(어순): 낱개 배열 <보기>(동사 원형)
- E(요약 빈칸): (A)(B) + 단어쌍 선지
- F(빈칸추론): 본문 빈칸 + 영어 선지
- G(내용일치 개수): 진술 5개 중 일치 개수
"""
from __future__ import annotations

import re

from . import build as B1
from . import format as F
from . import format2 as F2


# A · 어법·어휘 짝짓기 -------------------------------------------------------
def make_A(sentences, marks, answer_no, reason, choices):
    """marks: [(문장idx, 원본단어, 표시단어)] 5개(ⓐ~ⓔ). choices: 5개 짝 문자열."""
    if len(marks) != 5:
        raise ValueError("A 유형 밑줄은 5개여야 합니다.")
    # 밑줄 문자 ⓐ~ⓔ 를 '읽는 순서'로 매기고, 선지 문자열의 문자도 같은 순서로 재표기
    # (선지는 그대로 두고 문자만 상호 치환하므로 정답 번호는 불변).
    marks, remap = B1.order_marks(sentences, marks)
    if remap and any(o != n for o, n in remap.items()):
        trans = {ord(F2.CIRC_LETTER[o - 1]): F2.CIRC_LETTER[n - 1]
                 for o, n in remap.items() if o - 1 < len(F2.CIRC_LETTER)}
        choices = [c.translate(trans) for c in choices]
    lettered = [(idx, word, F2.uletter(i, shown)) for i, (idx, word, shown) in enumerate(marks, 1)]
    marked = B1._passage_html(sentences, lettered)
    return F2.A_q(marked, choices), F2.A_a(answer_no, reason)


# B · 함의추론 --------------------------------------------------------------
def make_B(sentences, phrase, choices, answer_no, reason, wrong):
    return (F2.B_q(" ".join(sentences), phrase, choices),
            F2.B_a(answer_no, reason, wrong))


# C · 어법(복수정답) — 1회 빌더 재사용 --------------------------------------
def make_C(sentences, marks, answer_nos, reasons):
    return B1.make_grammar(sentences, marks, answer_nos, reasons)


# D · 어순 배열 -------------------------------------------------------------
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


# 문장부호 정규화(길이 보존): 굽은 따옴표·대시·비분할공백을 표준형으로.
_SOFT = str.maketrans({
    "’": "'", "‘": "'", "ʼ": "'",            # 굽은 작은따옴표
    "“": '"', "”": '"',                            # 굽은 큰따옴표
    "—": "-", "–": "-", "‒": "-", "―": "-",  # 대시
    " ": " ",                                            # nbsp
})


def _soft(s: str) -> str:
    return s.translate(_SOFT).lower()


def locate_phrase(phrase: str, sentences: list[str]):
    """LLM 어구를 지문에서 찾되, 따옴표·대시 차이를 무시한다.

    반환: (문장 index, '지문 실제 표기의 정확한 부분문자열') / 못 찾으면 (None, None).
    _soft 는 문자 1:1 치환+소문자라 길이를 보존하므로, 정규화 위치가 원문 위치와 그대로
    대응한다 → 원문(굽은 따옴표 등)을 그대로 잘라내 빈칸/밑줄 매칭이 어긋나지 않게 한다.
    """
    sp = _soft(phrase.strip())
    if not sp:
        return None, None
    for i, s in enumerate(sentences):
        j = _soft(s).find(sp)
        if j >= 0:
            return i, s[j:j + len(sp)]
    return None, None


def make_D(sentences, tokens, cues, answer_sentence, reason="", flags=None):
    """정답 문장은 반드시 '지문에 실제로 있는 문장'이어야 한다(원래 배열 보장).
    정확히 일치하지 않으면 토큰·답과 가장 잘 맞는 지문 문장으로 스냅(교정)한다.
    flags(리스트)를 주면 유사도 스냅이 실제로 일어났을 때 '확인 권장' 사유를 담는다."""
    from . import review as _rv

    for t in tokens:
        if " " in t.strip():
            raise ValueError(f"낱개 단어여야 합니다(구 묶음 금지): '{t}'")
    # 토큰이 정답 문장을 '온전히' 복원할 수 있어야 한다. 개수가 다르면(예: 동사 누락)
    # 배열이 불가능한 깨진 문항이므로 실패시켜 재생성하게 한다.
    n_words = len(answer_sentence.split())
    if len(tokens) != n_words:
        raise ValueError(
            f"어순 배열 토큰 개수가 정답 문장과 다릅니다(토큰 {len(tokens)} ≠ 문장 {n_words}). "
            "일부 단어가 빠졌을 수 있어 다시 생성합니다.")
    snapped = B1.resolve_passage_sentence(answer_sentence, tokens, sentences)
    if snapped is None:
        raise ValueError("어순 배열 정답이 지문 문장과 맞지 않습니다(원래 배열을 찾지 못함).")
    if _norm(snapped) != _norm(answer_sentence) and flags is not None:
        flags.append(_rv.FIX_SNAP)
    # 제시어(원형으로 바꾼 동사) 자동 보강: 정답 문장에 '그대로' 없는 토큰은 어형이
    # 변형된 것이므로 cue 로 표시한다(LLM 이 cues 에 빠뜨려도 학생이 알아볼 수 있게).
    ans_words = {F2._bareword(w) for w in answer_sentence.split()}
    cues = list(cues) + [tk for tk in tokens
                         if F2._bareword(tk) and F2._bareword(tk) not in ans_words]
    return F2.D_q(tokens, cues), F2.D_a(snapped, reason)


# E · 요약문 빈칸(객관식) ---------------------------------------------------
def make_E(sentences, before, mid, after, choice_pairs, answer_no, reason):
    """choice_pairs: [(a_word, b_word)] 5개. 요약문 위에 지문도 함께 제시한다."""
    before = B1.strip_ab_label(before)
    mid = B1.strip_ab_label(mid)
    after = B1.strip_ab_label(after)
    before, pa = B1.take_trailing_punct(before)   # '(A),' 잔재 → (A) 빈칸 뒤로
    mid, pb = B1.take_trailing_punct(mid)          # '(B),' 잔재 → (B) 빈칸 뒤로
    # 빈칸 라벨 앞뒤로 공백을 두어 'like(A)_____and' 처럼 붙지 않게 한다.
    summary = (F.esc(before) + " " + F2.blank_ab("A") + F.esc(pa) + " " + F.esc(mid)
               + " " + F2.blank_ab("B") + F.esc(pb) + " " + F.esc(after))
    summary = re.sub(r"\s+([,.;:!?])", r"\1", re.sub(r"\s{2,}", " ", summary)).strip()
    choices = [F2.E_pair(a, b) for a, b in choice_pairs]
    return F2.E_q(" ".join(sentences), summary, choices), F2.E_a(answer_no, reason)


# F · 빈칸추론 (지문 전체 + 핵심 어구 빈칸) ---------------------------------
def make_F(sentences, blank_sent_idx, blank_phrase, choices, answer_no, reason, wrong):
    """지문 전체를 보여주되, blank_sent_idx 문장의 blank_phrase(핵심/주제 어구)만 빈칸으로.
    정답 선지는 원문 어구를 '유의어로 패러프레이즈'한 것이어야 한다(원문 그대로 금지).
    """
    # 빈칸 어구는 지문 전체에 '정확히 한 번'만 나와야 한다(여러 번이면 다른 곳에서 베낄 수 있음).
    occ = len(re.findall(re.escape(blank_phrase), " ".join(sentences), re.IGNORECASE))
    if occ != 1:
        raise ValueError(f"빈칸 어구는 지문에 정확히 한 번만 나와야 합니다(현재 {occ}회): "
                         f"'{blank_phrase}'")
    marked = B1._passage_html(sentences, [(blank_sent_idx, blank_phrase, F2.blank_line())])
    return F2.F_q(marked, choices), F2.F_a(answer_no, reason, wrong)


# G · 내용일치 개수 ---------------------------------------------------------
def make_G(sentences, statements, match_count, reason, per_stmt):
    n = len(statements)
    if not (1 <= match_count <= n):
        raise ValueError(f"일치 개수는 1~{n} 여야 합니다(현재 {match_count}).")
    return (F2.G_q(" ".join(sentences), statements),
            F2.G_a(match_count, reason, per_stmt))
