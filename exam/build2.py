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

from . import build as B1
from . import format as F
from . import format2 as F2


# A · 어법·어휘 짝짓기 -------------------------------------------------------
def make_A(sentences, marks, answer_no, reason, choices):
    """marks: [(문장idx, 원본단어, 표시단어)] 5개(ⓐ~ⓔ). choices: 5개 짝 문자열."""
    if len(marks) != 5:
        raise ValueError("A 유형 밑줄은 5개여야 합니다.")
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
def make_D(tokens, cues, answer_sentence, reason=""):
    for t in tokens:
        if " " in t.strip():
            raise ValueError(f"낱개 단어여야 합니다(구 묶음 금지): '{t}'")
    return F2.D_q(tokens, cues), F2.D_a(answer_sentence, reason)


# E · 요약문 빈칸(객관식) ---------------------------------------------------
def make_E(before, mid, after, choice_pairs, answer_no, reason):
    """choice_pairs: [(a_word, b_word)] 5개."""
    summary = (F.esc(before) + F2.blank_ab("A") + F.esc(mid)
               + F2.blank_ab("B") + F.esc(after))
    choices = [F2.E_pair(a, b) for a, b in choice_pairs]
    return F2.E_q(summary, choices), F2.E_a(answer_no, reason)


# F · 빈칸추론 --------------------------------------------------------------
def make_F(before, after, choices, answer_no, reason, wrong):
    passage_html = F.esc(before) + F2.blank_line() + F.esc(after)
    return F2.F_q(passage_html, choices), F2.F_a(answer_no, reason, wrong)


# G · 내용일치 개수 ---------------------------------------------------------
def make_G(sentences, statements, match_count, reason, per_stmt):
    return (F2.G_q(" ".join(sentences), statements),
            F2.G_a(match_count, reason, per_stmt))
