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
def make_A(sentences, marks, answer_no, reason, choices, flags=None, reasons=None,
           points=None):
    """marks: [(문장idx, 원본단어, 표시단어)] 5개(ⓐ~ⓔ). choices: 5개 짝 문자열.
    reasons: {밑줄번호: 사유} — 밑줄을 읽는 순서로 다시 매길 때 함께 옮긴다."""
    if len(marks) != 5:
        raise ValueError("A 유형 밑줄은 5개여야 합니다.")
    # 밑줄 문자 ⓐ~ⓔ 를 '읽는 순서'로 매기고, 선지 문자열의 문자도 같은 순서로 재표기
    # (선지는 그대로 두고 문자만 상호 치환하므로 정답 번호는 불변).
    marks, remap = B1.order_marks(sentences, marks)
    if remap and any(o != n for o, n in remap.items()):
        trans = {ord(F2.CIRC_LETTER[o - 1]): F2.CIRC_LETTER[n - 1]
                 for o, n in remap.items() if o - 1 < len(F2.CIRC_LETTER)}
        choices = [c.translate(trans) for c in choices]
        # 사유도 같이 옮기지 않으면 'ⓑ told' 설명이 ⓒ 자리에 붙는다.
        # 사유 '안'에서 부르는 기호(ⓒ 는 rational 이어야 …)도 함께 옮긴다.
        if reasons:
            reasons = {remap.get(o, o): t.translate(trans) for o, t in reasons.items()}
        if points:
            points = {remap.get(o, o): t for o, t in points.items()}
        if reason:
            reason = reason.translate(trans)
    marks = B1.expand_marks(sentences, marks)   # 'to confirm' 류 낱말 중복 방지
    B1.flag_ambiguous_marks(sentences, marks, flags)   # 같은 낱말 여러 번 → 확인 권장
    lettered = [(idx, word, F2.uletter(i, shown)) for i, (idx, word, shown) in enumerate(marks, 1)]
    marked = B1._passage_html(sentences, lettered)
    return F2.A_q(marked, choices), F2.A_a(answer_no, reason, reasons, points)


# B · 함의추론 --------------------------------------------------------------
def make_B(sentences, phrase, choices, answer_no, reason, wrong):
    return (F2.B_q(" ".join(sentences), phrase, choices),
            F2.B_a(answer_no, reason, wrong))


# C · 어법(복수정답) — 1회 빌더 재사용 --------------------------------------
def make_C(sentences, marks, answer_nos, reasons, flags=None):
    return B1.make_grammar(sentences, marks, answer_nos, reasons, flags=flags)


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


def _shuffle_tokens(tokens: list[str], answer: str) -> list[str]:
    """<보기> 낱말을 '정답 순서가 아니게' 섞는다(지문마다 같은 결과 — 재현 가능).

    모델에게 "뒤섞어 주세요"라고만 하면 그대로 원래 순서로 돌려주는 일이 있다
    (실제 출력물 16번: 서른여섯 낱말이 정답 문장 순서 그대로 실렸다 — 학생이
    베껴 쓰기만 하면 되는 문항이 된다). 섞는 일은 모델에게 맡기지 않는다.

    무작위로 한 번 섞으면 '앞뒤가 원문 그대로 붙어 있는 토막'이 길게 남을 수 있다.
    여러 번 섞어 그 토막이 가장 짧은 것을 고른다.
    """
    import hashlib
    import random

    toks = list(tokens)
    if len(toks) < 3:
        return toks
    # 각 토큰이 정답 문장에서 몇 번째 낱말인지(어형이 달라진 토큰은 -1)
    words = [F2._bareword(w) for w in (answer or "").split()]
    taken: set[int] = set()
    pos: list[int] = []
    for t in toks:
        b = F2._bareword(t)
        j = next((i for i, w in enumerate(words) if w == b and i not in taken), -1)
        if j >= 0:
            taken.add(j)
        pos.append(j)

    def runs(order: list[int]) -> int:
        """이웃한 두 자리가 정답에서도 이웃하고 순서까지 같은 횟수."""
        return sum(1 for i in range(len(order) - 1)
                   if order[i] >= 0 and order[i + 1] == order[i] + 1)

    rng = random.Random(int(hashlib.sha1((answer or "").encode()).hexdigest()[:8], 16))
    idx = list(range(len(toks)))
    best, best_score = None, None
    for _ in range(32):
        cand = list(idx)
        rng.shuffle(cand)
        order = [pos[i] for i in cand]
        if order == sorted(o for o in order if o >= 0) and -1 not in order:
            continue                    # 정답 순서 그대로 — 버린다
        sc = runs(order)
        if best_score is None or sc < best_score:
            best, best_score = cand, sc
            if sc == 0:
                break
    if best is None:                    # 낱말이 너무 적어 어떻게 섞어도 같을 때
        return list(reversed(toks))
    return [toks[i] for i in best]


def make_D(sentences, tokens, cues, answer_sentence, reason="", flags=None,
           korean: str = ""):
    """정답 문장은 반드시 '지문에 실제로 있는 문장'이어야 한다(원래 배열 보장).
    정확히 일치하지 않으면 토큰·답과 가장 잘 맞는 지문 문장으로 스냅(교정)한다.
    flags(리스트)를 주면 유사도 스냅이 실제로 일어났을 때 '확인 권장' 사유를 담는다.

    korean: 정답 문장의 우리말 뜻. 학생이 보는 것은 섞인 낱말뿐이라 이것이 어순을
    정한다 — 없으면 문법에 맞는 다른 어순도 정답이 되어 버린다."""
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
    # 섞는 일은 코드가 한다(모델이 정답 순서 그대로 돌려주는 일이 있다).
    return (F2.D_q(_shuffle_tokens(tokens, snapped), cues, korean),
            F2.D_a(snapped, reason))


# 연결어 (A)(B) -------------------------------------------------------------
def make_linker(sentences, a_no: int, b_no: int, remove_a: str, remove_b: str,
                pairs, answer_no: int, reason: str, wrong=None):
    """지문 두 문장의 첫머리를 (A)·(B) 빈칸으로 만든다.

    그 문장이 이미 연결어로 시작하면(However, / Rather, …) 그것을 지우고 빈칸을
    놓는다. 지우지 않으면 '(A)_____ However, …' 처럼 연결어가 둘이 된다.
    remove 로 준 말이 그 문장 첫머리에 실제로 없으면 문항이 어긋난 것이라 거절한다
    (조용히 무시하면 학생용 지문에 연결어가 둘 남는다).
    """
    n = len(sentences)
    if not (1 <= a_no < b_no <= n):
        raise ValueError(f"연결어 자리는 1 이상 {n} 이하이고 (A) 가 (B) 보다 앞서야 "
                         f"합니다(현재 A={a_no}, B={b_no}).")
    if a_no == 1:
        raise ValueError("첫 문장에는 연결어 자리를 두지 않습니다(앞에 이어받을 글이 없습니다).")

    out = [s.strip() for s in sentences]
    for no, rm, letter in ((a_no, remove_a, "A"), (b_no, remove_b, "B")):
        sent = out[no - 1]
        rm = (rm or "").strip()
        if rm:
            if not sent.lower().startswith(rm.lower()):
                raise ValueError(f"({letter}) 문장이 '{rm}' 로 시작하지 않습니다: "
                                 f"'{sent[:40]}…'")
            sent = sent[len(rm):].lstrip(" ,")
            sent = sent[:1].upper() + sent[1:] if sent else sent
        out[no - 1] = f"\x00{letter}\x00 " + sent

    body = F.esc(" ".join(out))
    for letter in ("A", "B"):
        body = body.replace(f"\x00{letter}\x00", F2.blank_ab(letter))
    choices = [F2.E_pair(p.a, p.b) if hasattr(p, "a") else F2.E_pair(*p) for p in pairs]
    return F2.linker_q(body, choices), F2.linker_a(answer_no, reason, wrong)


# E · 요약문 빈칸(객관식) ---------------------------------------------------
def make_E(sentences, before, mid, after, choice_pairs, answer_no, reason, wrong=None):
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
    return F2.E_q(" ".join(sentences), summary, choices), F2.E_a(answer_no, reason, wrong)


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
