"""변형문제 2회(A~G) 전용 HTML 조각 빌더. 볼드 규칙은 1회와 동일(format.py 재사용)."""
from __future__ import annotations

import re

from . import format as F

CIRC_LETTER = ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ", "ⓕ", "ⓖ", "ⓗ"]


def _bareword(w: str) -> str:
    """비교용: 앞뒤 구두점 제거 + 소문자('found,' → 'found', 'Second' → 'second')."""
    return re.sub(r"[^a-z0-9']+", "", w.lower())


def cletter(i: int) -> str:
    return CIRC_LETTER[i - 1]


def uletter(i: int, word: str) -> str:
    """ⓐ~ⓗ 문자 밑줄(어법·어휘 짝짓기용)."""
    return f'<span class="cnum">{cletter(i)}</span> <u>{F.esc(word)}</u>'


def _choices_ol(choices: list[str], cls: str = "") -> str:
    lis = "".join(
        f'<li><span class="cnum">{F.circ(i)}</span> {F.esc(c)}</li>'
        for i, c in enumerate(choices, 1)
    )
    return f'<ol class="choices {cls}">{lis}</ol>'


def _answer(answer_no: int, reason: str, wrong: dict[int, str] | None = None) -> str:
    parts = [f'<p><span class="answer-key">{F.circ(answer_no)}</span></p>',
             f'<p class="reason">{F.esc(reason)}</p>']
    for i in sorted(wrong or {}):
        parts.append(f'<p class="wrong">{F.circ(i)} {F.esc(wrong[i])}</p>')
    return "".join(parts)


# A · 어법·어휘 짝짓기 -------------------------------------------------------
def A_q(marked_passage_html: str, choices: list[str]) -> str:
    return f'<div class="passage">{marked_passage_html}</div>' + _choices_ol(choices)


def A_a(answer_no: int, reason: str,
        reasons: dict[int, str] | None = None) -> str:
    """짝짓기 해설 — 총평 한 줄 + 밑줄 ⓐ~ⓔ 별 사유를 '한 줄씩' 찍는다.

    예전에는 다섯 사유를 ' / ' 로 이어 한 문단에 몰아넣어, 해설편에서 열 줄짜리
    덩어리가 되어 어느 기호의 설명인지 눈으로 좇기 어려웠다.
    """
    parts = [f'<p><span class="answer-key">{F.circ(answer_no)}</span></p>']
    if (reason or "").strip():
        parts.append(f'<p class="reason">{F.esc(reason)}</p>')
    for i in sorted(reasons or {}):
        parts.append(f'<p class="wrong">{cletter(i)} {F.esc(reasons[i])}</p>')
    return "".join(parts)


# B · 함의추론(밑줄 1개 + 한글 선지) ----------------------------------------
def B_q(passage: str, phrase: str, choices: list[str]) -> str:
    esc_p = F.esc(passage)
    marked = esc_p.replace(F.esc(phrase), f"<u>{F.esc(phrase)}</u>", 1)
    return f'<div class="passage">{marked}</div>' + _choices_ol(choices, "content")


def B_a(answer_no: int, reason: str, wrong: dict[int, str]) -> str:
    return _answer(answer_no, reason, wrong)


# E · 요약문 빈칸(객관식) ---------------------------------------------------
def blank_ab(letter: str) -> str:
    return f'({letter})<span class="blank">_____</span>'


def E_q(passage: str, summary_html: str, choices: list[str]) -> str:
    lis = "".join(
        f'<li><span class="cnum">{F.circ(i)}</span> {c}</li>'   # choices 는 (A)-(B) HTML
        for i, c in enumerate(choices, 1)
    )
    return (f'<div class="passage">{F.esc(passage)}</div>'
            f'<div class="boki"><span class="boki-title">&lt;요약문&gt;</span> {summary_html}</div>'
            f'<ol class="choices">{lis}</ol>')


def E_pair(a_word: str, b_word: str) -> str:
    return f'(A) <b class="cue">{F.esc(a_word)}</b> &nbsp;····&nbsp; (B) <b class="cue">{F.esc(b_word)}</b>'


def E_a(answer_no: int, reason: str, wrong: dict[int, str] | None = None) -> str:
    return _answer(answer_no, reason, wrong)


# F · 빈칸추론 --------------------------------------------------------------
def F_q(passage_html_with_blank: str, choices: list[str]) -> str:
    return f'<div class="passage">{passage_html_with_blank}</div>' + _choices_ol(choices)


def blank_line() -> str:
    return '<span class="blank">__________</span>'


def F_a(answer_no: int, reason: str, wrong: dict[int, str]) -> str:
    return _answer(answer_no, reason, wrong)


# D · 어순 배열(서술형) -----------------------------------------------------
def D_q(tokens: list[str], cues: list[str], korean: str = "") -> str:
    # 구두점에 영향받지 않게 '맨몸 단어'로 비교(예: 'find,' 토큰도 cue 'find' 로 볼드).
    cue_set = {_bareword(c) for c in cues if _bareword(c)}
    toks = []
    for tk in tokens:
        if _bareword(tk) in cue_set:
            toks.append(f'<span class="cue">{F.esc(tk)}</span>')
        else:
            toks.append(F.esc(tk))
    # 우리말 뜻이 어순을 정한다. 학생이 보는 것은 섞인 낱말뿐이므로, 이 줄이 없으면
    # 문법에 맞는 다른 배열도 정답이 된다.
    # 라벨을 함께 붙이는 까닭: 발문(set2.TYPE_PROMPTS2)은 유형마다 고정이라 옛 결과
    # JSON 을 다시 조판할 때도 같은 문장이 쓰인다. 그래서 발문을 고치는 대신, 이 줄만
    # 보고도 무엇을 만들라는 것인지 알 수 있게 한다(우리말 뜻이 없던 옛 문항은 이 줄이
    # 통째로 빠지므로 예전 그대로 나온다).
    head = (f'<div class="d-korean"><span class="d-korean-label">우리말</span> '
            f'{F.esc(korean.strip())}</div>'
            if (korean or "").strip() else "")
    return (head
            + f'<div class="boki"><span class="boki-title">&lt;보기&gt;</span> {" / ".join(toks)}</div>'
            + F.write_lines(1))   # 답 쓰는 칸


def D_a(sentence: str, reason: str = "") -> str:
    out = [f'<p><span class="answer-key">정답</span> {F.esc(sentence)}</p>']
    if reason:
        out.append(f'<p class="reason">{F.esc(reason)}</p>')
    return "".join(out)


# G · 내용일치 개수 ---------------------------------------------------------
_ABC = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)"]


def G_q(passage: str, statements: list[str]) -> str:
    lis = "".join(
        f'<li>{_ABC[i]} {F.esc(s)}</li>' for i, s in enumerate(statements)
    )
    # 선지 개수(1개~N개)는 진술 수에 맞춰 동적으로
    ch = "".join(
        f'<li><span class="cnum">{F.circ(i)}</span> {i}개</li>'
        for i in range(1, len(statements) + 1)
    )
    return (f'<div class="passage">{F.esc(passage)}</div>'
            f'<ul class="choices">{lis}</ul>'
            f'<ol class="choices inline">{ch}</ol>')


def G_a(match_count: int, reason: str, per_stmt: dict[int, str]) -> str:
    parts = [f'<p><span class="answer-key">{F.circ(match_count)}</span> ({match_count}개 일치)</p>',
             f'<p class="reason">{F.esc(reason)}</p>']
    for i in sorted(per_stmt):
        parts.append(f'<p class="wrong">{_ABC[i - 1]} {F.esc(per_stmt[i])}</p>')
    return "".join(parts)


# 연결어 (A)(B) ------------------------------------------------------------
def linker_q(passage_html_with_blanks: str, choices: list[str]) -> str:
    lis = "".join(
        f'<li><span class="cnum">{F.circ(i)}</span> {c}</li>'   # choices 는 (A)-(B) HTML
        for i, c in enumerate(choices, 1)
    )
    return (f'<div class="passage">{passage_html_with_blanks}</div>'
            f'<ol class="choices">{lis}</ol>')


def linker_a(answer_no: int, reason: str, wrong: dict[int, str] | None = None) -> str:
    return _answer(answer_no, reason, wrong)
