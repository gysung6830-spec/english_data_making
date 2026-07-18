"""정본(canonical) 지문 하나에서 6종 문제를 파생하는 변형기.

명세서 §3·§5 의 "지문 1회 분석, 6종이 나눠 씀"을 코드로 강제한다.
- 모든 유형이 '같은 문장들(sentences)'을 공유한다.
- 유형별로 원본을 변형하는 정도만 다르며, 연결 텍스트는 원본과 동일하다.
  (어휘/어법은 '지정된 밑줄 단어'만 원본과 달라지고, 나머지는 그대로다.)

데모 데이터와 LLM 생성기가 모두 이 변형기를 호출하므로,
"유형마다 지문이 재서술되는" 문제가 구조적으로 사라진다.
"""
from __future__ import annotations

import itertools
import re

from . import format as F


# ---------------------------------------------------------------------------
# 내부: 문장들 -> (지정 단어만 밑줄/치환된) 본문 HTML
# ---------------------------------------------------------------------------
def _passage_html(
    sentences: list[str],
    marks: list[tuple[int, str, str]] | None = None,
    overrides: dict[int, str] | None = None,
) -> str:
    """정본 문장들을 본문 HTML 로 만든다.

    - overrides: {문장idx: 교체문장} — 그 문장만 통째로 바꿈(어법 구조 변경·부정어 삽입용).
    - marks: [(문장idx, 원본단어, 마커HTML)] — 그 문장에서 단어 첫 등장을 마커로 치환.
    연결 텍스트는 원본 그대로 유지되고, 마커/override 로 지정한 부분만 달라진다.
    """
    sents = list(sentences)
    if overrides:
        for i, txt in overrides.items():
            sents[i] = txt
    esc = [F.esc(s) for s in sents]
    if marks:
        for idx, word, marker in marks:
            pat = re.compile(r"(?<!\w)" + re.escape(F.esc(word)) + r"(?!\w)")
            new, n = pat.subn(lambda _m: marker, esc[idx], count=1)
            if n == 0:
                raise ValueError(f"문장 {idx} 에서 '{word}' 를 찾지 못했습니다.")
            esc[idx] = new
    return " ".join(esc)


def _underline_marks(marks: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    """(문장idx, 원본단어, 표시단어) -> (문장idx, 원본단어, 밑줄HTML) 로 변환."""
    return [
        (idx, word, F.underline(i, shown))
        for i, (idx, word, shown) in enumerate(marks, 1)
    ]


# ---------------------------------------------------------------------------
# ① 순서 배열
# ---------------------------------------------------------------------------
def make_order(sentences: list[str], given_n: int, block_sizes: list[int],
               display: list[int], reason: str) -> tuple[str, str]:
    """given_n: 앞 몇 문장이 '주어진 글' / block_sizes: 나머지를 3덩어리로 /
    display: (A)(B)(C) 가 각각 원래 몇 번째 덩어리(1~3)인지.
    """
    if len(block_sizes) != 3 or len(display) != 3:
        raise ValueError("block_sizes·display 는 각각 3개여야 합니다.")
    if sorted(display) != [1, 2, 3]:
        raise ValueError("display 는 1,2,3 의 순열이어야 합니다.")
    rest = sentences[given_n:]
    if sum(block_sizes) != len(rest):
        raise ValueError("block_sizes 합이 나머지 문장 수와 다릅니다.")
    given = " ".join(sentences[:given_n])

    blocks: list[str] = []
    k = 0
    for sz in block_sizes:
        blocks.append(" ".join(rest[k:k + sz]))
        k += sz

    # (A)(B)(C) 각 라벨이 보여줄 덩어리(0-based)
    label_block = [d - 1 for d in display]              # label L(0=A) -> block idx
    seg_a, seg_b, seg_c = (blocks[label_block[L]] for L in range(3))

    # 정답: 원래 순서(덩어리 0,1,2)를 복원하는 라벨 배열
    correct = []
    for b in range(3):
        for L in range(3):
            if label_block[L] == b:
                correct.append("ABC"[L])
    correct_str = "-".join(f"({c})" for c in correct)

    perms = ["-".join(f"({c})" for c in p) for p in itertools.permutations("ABC")]
    options = [correct_str] + [p for p in perms if p != correct_str]
    options = sorted(options[:5])
    answer_no = options.index(correct_str) + 1

    q = F.order_q(given, seg_a, seg_b, seg_c, options)
    a = F.order_a(answer_no, reason)
    return q, a


# ---------------------------------------------------------------------------
# ② 문장 삽입
# ---------------------------------------------------------------------------
def make_insert(sentences: list[str], remove_idx: int, reason: str) -> tuple[str, str]:
    """remove_idx: 빼낼 '주어진 문장'의 인덱스(내부 문장: 1 ~ len-2)."""
    n = len(sentences)
    if not (1 <= remove_idx <= n - 2):
        raise ValueError(f"remove_idx 는 1~{n - 2}(내부 문장)여야 합니다.")
    given = sentences[remove_idx]
    rest = [s for i, s in enumerate(sentences) if i != remove_idx]
    gaps = len(rest) - 1                                # rest 문장 사이 간격 수
    n_marks = min(5, gaps)
    true_gap = remove_idx                               # rest 에서 원래 위치 간격(1-based)

    # 정답 간격을 포함하도록 n_marks 개의 연속 간격 창을 잡는다
    start = max(1, min(true_gap - n_marks // 2, gaps - n_marks + 1))
    marked_gaps = list(range(start, start + n_marks))
    answer_no = marked_gaps.index(true_gap) + 1

    # 표시할 간격에서만 chunk 를 나눈다 (그 외 문장은 이어 붙임)
    chunks: list[str] = []
    buff = [rest[0]]
    marks_set = set(marked_gaps)
    for j in range(1, len(rest)):
        if j in marks_set:
            chunks.append(" ".join(buff))
            buff = [rest[j]]
        else:
            buff.append(rest[j])
    chunks.append(" ".join(buff))

    markers = [f" {F.pos(i)} " for i in range(1, n_marks + 1)]
    marked = F.weave(chunks, markers)
    q = F.insert_q(given, marked)
    a = F.insert_a(answer_no, reason)
    return q, a


# ---------------------------------------------------------------------------
# ③ 주제 (원본 그대로)
# ---------------------------------------------------------------------------
def make_topic(sentences: list[str], choices: list[str], answer_no: int,
               reason: str, wrong: dict[int, str]) -> tuple[str, str]:
    q = F.topic_q(" ".join(sentences), choices)
    a = F.topic_a(answer_no, reason, wrong)
    return q, a


# ---------------------------------------------------------------------------
# ④ 어휘 (지정 단어만 원본과 다름)
# ---------------------------------------------------------------------------
def make_vocab(sentences: list[str], marks: list[tuple[int, str, str]],
               answer_no: int, reason: str,
               overrides: dict[int, str] | None = None) -> tuple[str, str]:
    """marks: [(문장idx, 원본단어, 표시단어)] 5개.
    - 방식1(반의어): 정답 표시단어=반의어, 나머지=유의어.
    - 방식2(부정어): 표시단어=원본단어 그대로 + overrides 로 정답 문장에 부정어 삽입.
    """
    if len(marks) != 5:
        raise ValueError("어휘 밑줄은 5개여야 합니다.")
    marked = _passage_html(sentences, _underline_marks(marks), overrides)
    return F.vocab_q(marked), F.vocab_a(answer_no, reason)


# ---------------------------------------------------------------------------
# ⑤ 어법 (지정 단어만 원본과 다름, 복수정답)
# ---------------------------------------------------------------------------
def make_grammar(sentences: list[str], marks: list[tuple[int, str, str]],
                 answer_nos: list[int], reasons: dict[int, str]) -> tuple[str, str]:
    """marks: [(문장idx, 원본단어, 표시단어)] 2~8개. 틀린 것은 표시단어가 오답형."""
    if not (2 <= len(marks) <= 8):
        raise ValueError("어법 밑줄은 2~8개여야 합니다.")
    marked = _passage_html(sentences, _underline_marks(marks))
    return F.grammar_q(marked), F.grammar_a(answer_nos, reasons)


# ---------------------------------------------------------------------------
# ⑥ 서술형 (원본 + 파생 과제)
# ---------------------------------------------------------------------------
def make_short(
    sentences: list[str],
    q1_prompt: str, q1_answer: str,
    q2_prompt: str, q2_tokens: list[str], q2_cues: list[str], q2_answer: str,
    q3_prompt: str, q3_before: str, q3_mid: str, q3_after: str,
    q3_cue_a: str, q3_cue_b: str, q3_ans_a: str, q3_ans_b: str, q3_reason: str,
) -> tuple[str, str]:
    summary_html = (
        F.esc(q3_before) + F.blank("A", q3_cue_a)
        + F.esc(q3_mid) + F.blank("B", q3_cue_b)
        + F.esc(q3_after)
    )
    q = F.short_answer_q(
        passage=" ".join(sentences),
        q1_prompt=q1_prompt,
        q2_prompt=q2_prompt, q2_tokens=q2_tokens, q2_cues=q2_cues,
        q3_prompt=q3_prompt, q3_summary_html=summary_html,
    )
    a = F.short_answer_a(q1_answer, q2_answer,
                         {"A": q3_ans_a, "B": q3_ans_b}, q3_reason)
    return q, a
