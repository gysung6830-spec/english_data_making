"""문제/해설 HTML 조각 빌더 (볼드 규칙의 단일 출처).

데모 데이터와 LLM 생성기가 모두 이 빌더를 통해 HTML 을 만들므로,
명세서 §4 의 볼드 5곳 규칙이 한곳에서 일관되게 적용된다.

빌더는 유형(type)별로 (question_html, answer_html) 를 만들어
Passage.set_qa(type, q, a) 에 그대로 넣을 수 있게 돌려준다.
"""
from __future__ import annotations

from markupsafe import escape

CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]


def circ(i: int) -> str:
    """1-based 번호 -> 원 번호."""
    return CIRCLED[i - 1]


def esc(text: str) -> str:
    return str(escape(text))


def write_lines(n: int = 1) -> str:
    """학생이 답을 적을 수 있는 빈 줄 n개(서술형용)."""
    return '<div class="write-lines">' + "".join('<span class="wline"></span>' for _ in range(n)) + "</div>"


def weave(chunks: list[str], markers_html: list[str]) -> str:
    """본문 조각(chunks) 사이에 마커 HTML 을 끼워 넣어 본문 HTML 을 만든다.

    len(chunks) == len(markers_html) + 1 이어야 한다.
    chunks 는 평문으로 취급해 escape 하고, markers_html 은 그대로 둔다.
    삽입(위치 마커)·어휘/어법(밑줄 마커) 본문 조립에 공용으로 쓴다.
    """
    if len(chunks) != len(markers_html) + 1:
        raise ValueError(
            f"chunks({len(chunks)}) 는 markers({len(markers_html)})+1 이어야 합니다."
        )
    out = [esc(chunks[0])]
    for m, c in zip(markers_html, chunks[1:]):
        out.append(m)
        out.append(esc(c))
    return "".join(out)


# ---------------------------------------------------------------------------
# ① 순서 배열
# ---------------------------------------------------------------------------
def order_q(given: str, segs: list[str], orders: list[str]) -> str:
    """given: 주어진 글 / segs: (A)(B)(C)… 덩어리들 / orders: 5개 순서 조합 문자열."""
    parts = [f'<div class="passage given">{esc(given)}</div>']
    for i, seg in enumerate(segs):
        label = "ABCDEFG"[i]
        parts.append(f'<div class="seg"><span class="seg-label">({label})</span> {esc(seg)}</div>')
    lis = "".join(
        f'<li><span class="cnum">{circ(i)}</span> {esc(o)}</li>'
        for i, o in enumerate(orders, 1)
    )
    parts.append(f'<ol class="choices order">{lis}</ol>')
    return "\n".join(parts)


def order_a(answer_no: int, reason: str) -> str:
    return (
        f'<p><span class="answer-key">{circ(answer_no)}</span></p>'
        f'<p class="reason">{esc(reason)}</p>'
    )


# ---------------------------------------------------------------------------
# ② 문장 삽입
# ---------------------------------------------------------------------------
def insert_q(given_sentence: str, marked_passage_html: str) -> str:
    """given_sentence: 주어진 문장 / marked_passage_html: ①~⑤ 위치가 박힌 본문 HTML."""
    return (
        f'<div class="given-sentence">{esc(given_sentence)}</div>'
        f'<div class="passage">{marked_passage_html}</div>'
    )


def insert_a(answer_no: int, reason: str) -> str:
    return (
        f'<p><span class="answer-key">{circ(answer_no)}</span></p>'
        f'<p class="reason">{esc(reason)}</p>'
    )


def irrelevant_q(intro: str, marked: list[str]) -> str:
    """무관한 문장 문제 본문 — 도입문 뒤에 ①~⑤ 를 단 문장 5개를 이어 붙인다."""
    body = esc(intro)
    for i, sent in enumerate(marked, 1):
        body += f' <span class="cnum">{circ(i)}</span> {esc(sent)}'
    return f'<div class="passage">{body}</div>'


def irrelevant_a(answer_no: int, reason: str, wrong_reasons: dict[int, str]) -> str:
    parts = [
        f'<p><span class="answer-key">{circ(answer_no)}</span></p>',
        f'<p class="reason">{esc(reason)}</p>',
    ]
    for i in sorted(wrong_reasons):
        parts.append(f'<p class="wrong">{circ(i)} {esc(wrong_reasons[i])}</p>')
    return "".join(parts)


def pos(i: int) -> str:
    """삽입 문제 본문에 넣는 위치 마커."""
    return f'<span class="cnum">{circ(i)}</span>'


# ---------------------------------------------------------------------------
# ③ 주제 (영어 선지)
# ---------------------------------------------------------------------------
def topic_q(passage: str, choices: list[str]) -> str:
    lis = "".join(
        f'<li><span class="cnum">{circ(i)}</span> {esc(c)}</li>'
        for i, c in enumerate(choices, 1)
    )
    return (
        f'<div class="passage">{esc(passage)}</div>'
        f'<ol class="choices topic">{lis}</ol>'
    )


def topic_a(answer_no: int, reason: str, wrong_reasons: dict[int, str]) -> str:
    parts = [
        f'<p><span class="answer-key">{circ(answer_no)}</span></p>',
        f'<p class="reason">{esc(reason)}</p>',
    ]
    for i in sorted(wrong_reasons):
        parts.append(f'<p class="wrong">{circ(i)} {esc(wrong_reasons[i])}</p>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# 내용 일치 (한글 선지) — 서술형 앞에 배치
# ---------------------------------------------------------------------------
def content_q(passage: str, choices: list[str]) -> str:
    lis = "".join(
        f'<li><span class="cnum">{circ(i)}</span> {esc(c)}</li>'
        for i, c in enumerate(choices, 1)
    )
    return (
        f'<div class="passage">{esc(passage)}</div>'
        f'<ol class="choices content">{lis}</ol>'
    )


def content_a(answer_no: int, reason: str, wrong_reasons: dict[int, str]) -> str:
    """정답 근거 + 각 오답이 '어느 부분에서' 글과 어긋나는지 짚는다."""
    parts = [
        f'<p><span class="answer-key">{circ(answer_no)}</span></p>',
        f'<p class="reason">{esc(reason)}</p>',
    ]
    for i in sorted(wrong_reasons):
        parts.append(f'<p class="wrong">{circ(i)} {esc(wrong_reasons[i])}</p>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# ④ 어휘 (문맥상 부적절)
# ---------------------------------------------------------------------------
def vocab_q(marked_passage_html: str) -> str:
    """marked_passage_html: ①~⑤ 밑줄이 박힌 본문 HTML (underline() 사용)."""
    return f'<div class="passage">{marked_passage_html}</div>'


def underline(i: int, word: str) -> str:
    """어휘/어법 본문 속 번호+밑줄 표기."""
    return f'<span class="cnum">{circ(i)}</span> <u>{esc(word)}</u>'


def vocab_a(answer_no: int, reason: str) -> str:
    return (
        f'<p><span class="answer-key">{circ(answer_no)}</span></p>'
        f'<p class="reason">{esc(reason)}</p>'
    )


# ---------------------------------------------------------------------------
# ⑤ 어법 (복수정답)
# ---------------------------------------------------------------------------
def grammar_q(marked_passage_html: str) -> str:
    """marked_passage_html: ①~⑧ 밑줄/네모가 박힌 본문 HTML."""
    return f'<div class="passage">{marked_passage_html}</div>'


def grammar_a(answer_nos: list[int], reasons: dict[int, str]) -> str:
    keys = ", ".join(circ(n) for n in sorted(answer_nos))
    parts = [f'<p><span class="answer-key">{keys}</span></p>']
    for i in sorted(reasons):
        parts.append(f'<p class="reason">{circ(i)} {esc(reasons[i])}</p>')
    return "".join(parts)


def grammar_count_q(marked_passage_html: str, max_count: int = 5) -> str:
    """어법 개수형 — 밑줄이 박힌 본문 + '1개~5개' 선지."""
    lis = "".join(f'<li><span class="cnum">{circ(i)}</span> {i}개</li>'
                  for i in range(1, max_count + 1))
    return (f'<div class="passage">{marked_passage_html}</div>'
            f'<ol class="choices count">{lis}</ol>')


def grammar_count_a(answer_no: int, reasons: dict[int, str], note: str = "") -> str:
    """정답(=틀린 개수) + 밑줄마다 옳은지 틀린지."""
    parts = [f'<p><span class="answer-key">{circ(answer_no)}</span> '
             f'({answer_no}개)</p>']
    if note:
        parts.append(f'<p class="reason">{esc(note)}</p>')
    for i in sorted(reasons):
        parts.append(f'<p class="reason">{circ(i)} {esc(reasons[i])}</p>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# ⑥ 서술형 (세 소문항)
# ---------------------------------------------------------------------------
def short_answer_q(
    passage: str,
    q1_prompt: str,
    q2_prompt: str,
    q2_tokens: list[str],
    q2_cues: list[str],
    q3_prompt: str,
    q3_summary_html: str,
) -> str:
    """세 소문항을 함께 구성.

    q2_tokens: 낱개 단어(구 묶음 금지). q2_cues: 그 중 학생이 변형할 제시어(굵게).
    q3_summary_html: (A)(B) 빈칸 + 제시어가 박힌 한 문장 요약문 HTML(blank() 사용).
    """
    # (2) <보기> 낱개 단어 배열 — 제시어(cue)만 굵게
    cue_set = {c.strip().lower() for c in q2_cues}
    toks = []
    for tk in q2_tokens:
        if tk.strip().lower() in cue_set:
            toks.append(f'<span class="cue">{esc(tk)}</span>')
        else:
            toks.append(esc(tk))
    boki = " / ".join(toks)

    return (
        f'<div class="passage">{esc(passage)}</div>'
        f'<div class="sub-q"><span class="sub-label">(1)</span> {esc(q1_prompt)}'
        f'{write_lines(2)}</div>'
        f'<div class="sub-q"><span class="sub-label">(2)</span> {esc(q2_prompt)}'
        f'<div class="boki"><span class="boki-title">&lt;보기&gt;</span> {boki}</div>'
        f'{write_lines(1)}</div>'
        f'<div class="sub-q"><span class="sub-label">(3)</span> {esc(q3_prompt)}'
        f'<div class="boki">{q3_summary_html}</div></div>'
    )


def blank(letter: str, cue: str) -> str:
    """요약문 빈칸: (A)___ (cue) — 제시어(cue)만 굵게."""
    return f'({letter})<span class="blank">_____</span> (<span class="cue">{esc(cue)}</span>)'


def short_answer_a(
    q1_answer: str,
    q2_answer: str,
    q3_answers: dict[str, str],
    q3_reason: str = "",
) -> str:
    parts = [
        f'<p>(1) <span class="answer-key">정답</span> {esc(q1_answer)}</p>',
        f'<p>(2) <span class="answer-key">정답</span> {esc(q2_answer)}</p>',
    ]
    a3 = " / ".join(f'({k}) <span class="answer-key">{esc(v)}</span>' for k, v in q3_answers.items())
    parts.append(f'<p>(3) {a3}</p>')
    if q3_reason:
        parts.append(f'<p class="reason">{esc(q3_reason)}</p>')
    return "".join(parts)
