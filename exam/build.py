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
import zlib
import re

from . import format as F
from .schemas import N_OX, N_OX_SHORT, N_OX_TRUE


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

    표시어(마커 안 문구)가 원본단어 앞의 낱말까지 포함하는 경우(예: 원본단어 'confirm',
    표시어 'to confirm')에는, 바로 앞에 이미 있는 그 낱말('to ')까지 함께 치환한다.
    그러지 않으면 'to to confirm' 처럼 낱말이 중복돼 문항이 성립하지 않는다.
    """
    sents = list(sentences)
    if overrides:
        for i, txt in overrides.items():
            sents[i] = txt
    esc = [F.esc(s) for s in sents]
    if marks:
        # 마커를 곧바로 넣지 않고 '플레이스홀더'로 먼저 치환한 뒤 마지막에 교체한다.
        # → 뒤 마크가 앞 마크가 넣은 마커 HTML 안에서 다시 매칭돼 '밑줄이 중첩'되는 일을 차단.
        #   같은 단어를 두 번 지정하면 두 번째는 '다음 출현'을 잡고, 없으면 명확히 실패한다.
        placeholders: dict[str, str] = {}
        for k, (idx, word, marker) in enumerate(marks):
            if not (0 <= idx < len(esc)):
                raise ValueError(f"밑줄 대상 문장 번호가 범위를 벗어났습니다: {idx}")
            token = f"\x00{k}\x00"
            esc_word = re.escape(F.esc(word))
            # 1) 단어 경계 → 2) 대소문자 무시 → 3) 부분 문자열(대소문자 무시)
            for pat in (
                re.compile(r"(?<!\w)" + esc_word + r"(?!\w)"),
                re.compile(r"(?<!\w)" + esc_word + r"(?!\w)", re.IGNORECASE),
                re.compile(esc_word, re.IGNORECASE),
            ):
                new, n = pat.subn(lambda _m: token, esc[idx], count=1)
                if n:
                    esc[idx] = new
                    placeholders[token] = marker
                    break
            else:
                raise ValueError(f"문장 {idx} 에서 '{word}' 를 찾지 못했습니다(중복 지정 가능성).")
        text = " ".join(esc)
        for token, marker in placeholders.items():
            text = text.replace(token, marker)
        return text
    return " ".join(esc)


def expand_marks(sentences: list[str],
                 marks: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    """표시어가 원본단어 '앞 낱말'까지 포함할 때, 그 앞 낱말도 치환 대상에 넣는다.

    LLM 이 밑줄 대상을 word='confirm', shown='to confirm' 처럼 돌려주면, 원본의 'to' 는
    그대로 남고 표시어에도 'to' 가 있어 'to to confirm' 으로 중복된다(실제 결과물 버그).
    표시어의 낱말열이 원본단어의 낱말열로 '끝나고' 앞에 여분 낱말이 있으면, 문장에서
    '여분 낱말 + 원본단어'가 실제로 이어져 있을 때만 원본단어를 그 구간으로 넓힌다.
    (조건이 안 맞으면 원래대로 두어 기존 동작을 바꾸지 않는다.)
    """
    out: list[tuple[int, str, str]] = []
    for idx, word, shown in marks:
        w_toks, s_toks = word.split(), shown.split()
        extra = len(s_toks) - len(w_toks)
        if (0 <= idx < len(sentences) and extra > 0
                and s_toks[extra:] == w_toks):
            lead = " ".join(s_toks[:extra])
            span = f"{lead} {word}"
            if re.search(r"(?<!\w)" + re.escape(span) + r"(?!\w)", sentences[idx], re.IGNORECASE):
                out.append((idx, span, shown))    # 'to confirm' 통째로 치환 → 중복 방지
                continue
        out.append((idx, word, shown))
    return out


def flag_ambiguous_marks(sentences: list[str], marks: list[tuple[int, str, str]],
                         flags: list[str] | None) -> None:
    """밑줄 대상 낱말이 그 문장에 여러 번 나오면 '확인 권장' 사유를 남긴다.

    조판기는 '첫 번째 출현'을 밑줄로 잡는데, LLM 은 다른 위치를 염두에 두고 해설을
    쓸 수 있다(예: that 이 한 문장에 4번 나오는데 해설은 뒤쪽 that 을 설명). 그러면
    밑줄과 해설이 어긋나 문항이 성립하지 않으므로, 사람이 한 번 보게 표시한다.
    (자동으로 고칠 수는 없다 — 어느 위치가 맞는지는 해설을 읽어야 알 수 있다.)
    """
    if flags is None:
        return
    from . import review as _rv

    for idx, word, _shown in marks:
        if not (0 <= idx < len(sentences)):
            continue
        w = str(word).strip()
        if not w or len(w.split()) > 2:      # 긴 어구는 애초에 모호하지 않다
            continue
        n = len(re.findall(r"(?<!\w)" + re.escape(w) + r"(?!\w)",
                           sentences[idx], re.IGNORECASE))
        if n > 1:
            if _rv.FIX_AMBIG not in flags:
                flags.append(_rv.FIX_AMBIG)
            return


def keep_sentence_case(sentences: list[str],
                       marks: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    """치환 낱말이 문장 맨 앞이면 표시어의 첫 글자를 대문자로 되돌린다.

    유의어형 어휘는 'Many studies' 의 Many 를 numerous 로 바꾸는데, 그대로 넣으면
    문장이 소문자로 시작한다(실제 출력물: '② numerous studies show …'). 학생 눈에는
    그냥 오타로 보이고, 밑줄이 어디까지인지도 흐려진다.
    """
    out: list[tuple[int, str, str]] = []
    for idx, word, shown in marks:
        s = sentences[idx].strip() if 0 <= idx < len(sentences) else ""
        if (s.lower().startswith(str(word).strip().lower())
                and shown and shown[:1].islower()):
            shown = shown[0].upper() + shown[1:]
        out.append((idx, word, shown))
    return out


def _underline_marks(marks: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    """(문장idx, 원본단어, 표시단어) -> (문장idx, 원본단어, 밑줄HTML) 로 변환."""
    return [
        (idx, word, F.underline(i, shown))
        for i, (idx, word, shown) in enumerate(marks, 1)
    ]


def _relabel(text: str, remap: dict[int, int]) -> str:
    """해설이 부른 밑줄 번호를 재매핑 뒤의 표시 번호로 옮긴다."""
    from . import answer_spread as _as

    if not text or all(k == v for k, v in (remap or {}).items()):
        return text
    return _as.relabel_choice_refs(text, remap)


def order_marks(sentences: list[str], marks: list[tuple[int, str, str]]):
    """밑줄 marks 를 '지문 읽는 순서'(문장 index → 문장 내 등장 위치)로 정렬한다.

    LLM 이 밑줄을 읽는 순서와 다르게 돌려줘도, 번호 ①②③…가 항상 본문 순서대로 매겨지게
    한다(예: ⑤가 ④보다 앞에 나오는 오류 방지). 옛 1-based 번호 → 새 1-based 번호 매핑을
    함께 돌려줘 정답 번호를 다시 맞춘다.
    """
    def _key(i: int):
        idx, word, _shown = marks[i]
        s = sentences[idx].lower() if 0 <= idx < len(sentences) else ""
        pos = s.find(str(word).lower())
        return (idx, pos if pos >= 0 else len(s) + i)

    order = sorted(range(len(marks)), key=_key)   # 안정 정렬(동률은 원래 순서 유지)
    remap = {old + 1: new + 1 for new, old in enumerate(order)}
    return [marks[i] for i in order], remap


# ---------------------------------------------------------------------------
# ① 순서 배열
# ---------------------------------------------------------------------------
def _norm(s: str) -> str:
    """문장 비교용 정규화(소문자·영숫자만)."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def resolve_passage_sentence(answer: str, tokens: list[str] | None,
                             sentences: list[str], min_score: float = 0.5) -> str | None:
    """어순배열 정답을 '지문에 실제로 있는 문장'으로 확정한다(원래 배열 보장).

    LLM 이 축약형(it's↔it is)·구두점·미세 단어 차이로 정확히 일치하지 않게 답하는 경우가
    있어, 하드 실패 대신 '토큰·답과 가장 잘 겹치는 지문 문장'으로 스냅한다.
    반환: 확정된 지문 문장(그대로) / 매칭 실패 시 None.
    """
    na = _norm(answer)
    for s in sentences:                       # ① 정확히 일치하면 그대로
        if _norm(s) == na:
            return s
    # ② 토큰(학생이 배열하는 낱개 단어) + 답의 단어 집합과 가장 잘 겹치는 문장으로 스냅
    tok_set = set(_norm(" ".join(tokens)).split()) if tokens else set()
    ntok = len(_norm(" ".join(tokens)).split()) if tokens else len(na.split())
    words = set(na.split()) | tok_set
    best, score = None, 0.0
    for s in sentences:
        sw = set(_norm(s).split())
        if not sw or not words:
            continue
        j = len(words & sw) / len(words | sw)
        if j > score:
            best, score = s, j
    if best is None or score < min_score:
        return None
    # ③ 후보 문장이 토큰보다 크게 길면(토큰이 문장의 '일부'만 담은 경우) 전체 문장으로
    #    늘리지 않고, 토큰과 맞는 '연속 구간'만 원문 그대로 잘라 반환한다. 학생이 배열할 수
    #    없는 단어가 정답에 섞이지 않게 한다.
    if ntok and len(_norm(best).split()) > ntok + 2:
        return _token_span(best, tok_set, ntok)
    return best


def _token_span(sentence: str, tok_set: set, n: int) -> str | None:
    """지문 문장에서 토큰(tok_set, n개)과 가장 잘 맞는 연속 n-단어 구간을 원문 그대로 돌려준다."""
    orig = sentence.split()
    norm = [_norm(w) for w in orig]
    if len(norm) < n or not tok_set:
        return None
    best_i, best_ov = None, 0.0
    for i in range(len(norm) - n + 1):
        sset = set(norm[i:i + n])
        ov = len(sset & tok_set) / len(sset | tok_set)
        if ov > best_ov:
            best_ov, best_i = ov, i
    if best_i is None or best_ov < 0.8:
        return None
    return " ".join(orig[best_i:best_i + n]).strip().strip(",;:")   # 연결 구두점 정리


def _even_split(total: int, parts: int) -> list[int]:
    """total 을 parts 개의 연속 덩어리로 최대한 고르게 나눈다(각 >=1)."""
    base, rem = divmod(total, parts)
    return [base + (1 if i < rem else 0) for i in range(parts)]


# 순서 배열을 몇 덩어리로 쪼갤지. 4덩어리면 경우의 수가 6 → 24 로 늘어 찍기가 어려워진다.
DEFAULT_ORDER_BLOCKS = 4
MIN_ORDER_BLOCKS = 3


def _order_options(labels: str, correct: list[str], seed: int) -> tuple[list[str], int]:
    """정답 순서를 포함한 선지 5개를 만든다. (선지, 정답 번호) 반환.

    두 가지를 지킨다.
      ① 오답은 '두 덩어리만 자리를 맞바꾼' 순열에서 먼저 고른다 — 정답과 한 끗 차이라야
         학생이 연결 근거를 따져 보게 된다(아무렇게나 뒤섞으면 눈으로 걸러진다).
      ② 첫 라벨이 한쪽으로 몰리지 않게 한다. 다섯 중 넷이 (D)로 시작하고 정답만 (B)로
         시작하면, 글을 읽지 않고 '혼자 다른 것'을 골라 맞힌다.
    덩어리가 4개면 맞바꾼 순열이 6가지라, 지문마다 다른 조합이 나오도록 seed 로 돌려 고른다.
    """
    correct_t = tuple(correct)
    k = len(labels)
    swaps = []
    for i in range(k):
        for j in range(i + 1, k):
            q = list(correct_t)
            q[i], q[j] = q[j], q[i]
            swaps.append(tuple(q))
    others = [q for q in itertools.permutations(labels)
              if q != correct_t and q not in swaps]
    pool = swaps + others
    pool = [pool[(seed + i) % len(pool)] for i in range(len(pool))]   # 시작 위치만 이동

    first = {correct_t[0]: 1}
    picked: list[tuple] = []
    for cap in (2, 3, k + 1):        # 몰림 한도를 조금씩 풀며 4개를 채운다
        for q in pool:
            if len(picked) == 4:
                break
            if q in picked or q == correct_t:
                continue
            if first.get(q[0], 0) >= cap:
                continue
            picked.append(q)
            first[q[0]] = first.get(q[0], 0) + 1
        if len(picked) == 4:
            break

    def fmt(q):
        return "-".join(f"({c})" for c in q)

    options = sorted([fmt(correct_t)] + [fmt(q) for q in picked])
    return options, options.index(fmt(correct_t)) + 1


def make_order(sentences: list[str], given_n: int, block_sizes: list[int],
               display: list[int], reason: str,
               flags: list[str] | None = None) -> tuple[str, str]:
    """given_n: 앞 몇 문장이 '주어진 글' / block_sizes: 나머지를 몇 덩어리로 /
    display: (A)(B)(C)… 가 각각 원래 몇 번째 덩어리인지.

    덩어리 수는 block_sizes 길이로 정해진다(3 또는 4). 문장이 모자라면 3덩어리로 줄인다.
    LLM 이 문장 수를 잘못 세어 값이 어긋나도 실패하지 않도록 스스로 보정한다.
    flags(리스트)를 주면, 실제로 보정이 일어났을 때 '확인 권장' 사유를 담아 준다.
    """
    from . import review as _rv

    n = len(sentences)
    if n < MIN_ORDER_BLOCKS + 1:
        raise ValueError(
            f"순서 문제를 만들기에 문장이 너무 적습니다({MIN_ORDER_BLOCKS + 1}문장 이상 필요).")

    corrected = False
    # 덩어리 수: 요청값을 따르되, 주어진 글 1문장 + 덩어리당 1문장은 있어야 한다
    want = len(block_sizes) if isinstance(block_sizes, list) else DEFAULT_ORDER_BLOCKS
    if want not in (3, 4):
        want, corrected = DEFAULT_ORDER_BLOCKS, True
    k = min(want, n - 1)
    if k < MIN_ORDER_BLOCKS:
        k = MIN_ORDER_BLOCKS
    if k != want:
        corrected = True          # 문장이 모자라 덩어리 수를 줄였다

    # given_n: 최소 1, 나머지로 k덩어리를 만들 수 있도록 최대 n-k 로 보정
    try:
        given_val = int(given_n)
    except (TypeError, ValueError):
        given_val, corrected = 1, True
    given_n = max(1, min(given_val, n - k))
    if given_n != given_val:
        corrected = True
    remaining = n - given_n

    # block_sizes: k개·양수·합==remaining 이 아니면 고르게 재분배
    valid = (isinstance(block_sizes, list) and len(block_sizes) == k
             and all(isinstance(x, int) and x >= 1 for x in block_sizes)
             and sum(block_sizes) == remaining)
    if not valid:
        block_sizes = _even_split(remaining, k)
        corrected = True

    # display: 1..k 의 순열이 아니면 기본값으로 보정(앞 두 덩어리를 맞바꾼 배열)
    if sorted(display or []) != list(range(1, k + 1)):
        display = [2, 1] + list(range(3, k + 1))
        corrected = True

    if corrected and flags is not None:
        flags.append(_rv.FIX_ORDER)

    rest = sentences[given_n:]
    given = " ".join(sentences[:given_n])

    blocks: list[str] = []
    idx = 0
    for sz in block_sizes:
        blocks.append(" ".join(rest[idx:idx + sz]))
        idx += sz

    labels = "ABCD"[:k]
    label_block = [d - 1 for d in display]          # 라벨 L(0=A) -> 원래 덩어리 idx
    segs = [blocks[label_block[L]] for L in range(k)]

    # 정답: 원래 순서(덩어리 0,1,2,…)를 복원하는 라벨 배열
    correct = []
    for blk in range(k):
        for L in range(k):
            if label_block[L] == blk:
                correct.append(labels[L])
    seed = zlib.crc32(" ".join(sentences).encode("utf-8"))
    options, answer_no = _order_options(labels, correct, seed)

    q = F.order_q(given, segs, options)
    a = F.order_a(answer_no, reason)
    return q, a


# ---------------------------------------------------------------------------
# ② 문장 삽입
# ---------------------------------------------------------------------------
MIN_INSERT_MARKS = 4     # 삽입 문제의 최소 선지 수(①~④)


def make_insert(sentences: list[str], remove_idx: int, reason: str,
                flags: list[str] | None = None) -> tuple[str, str]:
    """remove_idx: 빼낼 '주어진 문장'의 인덱스(내부 문장: 1 ~ len-2).

    LLM 이 첫/마지막 문장 등 범위를 벗어난 번호를 줘도 내부로 보정한다.
    flags(리스트)를 주면 실제 보정 시 '확인 권장' 사유를 담아 준다.
    """
    from . import review as _rv

    n = len(sentences)
    if n < 3:
        raise ValueError("삽입 문제를 만들기에 문장이 너무 적습니다(3문장 이상 필요).")
    try:
        idx_val = int(remove_idx)
    except (TypeError, ValueError):
        idx_val = 1
    remove_idx = max(1, min(idx_val, n - 2))   # 내부 문장으로 보정
    if remove_idx != idx_val and flags is not None:
        flags.append(_rv.FIX_INSERT)
    given = sentences[remove_idx]
    rest = [s for i, s in enumerate(sentences) if i != remove_idx]
    gaps = len(rest) - 1                                # rest 문장 사이 간격 수
    n_marks = min(5, gaps)
    # 자리가 셋뿐이면 찍어도 3분의 1이라 변별이 거의 없다(실제 출력물: ①②③ 뿐).
    # 문항을 버리기보다 내보내되, 선생님이 알아보도록 검토 메모를 남긴다.
    if n_marks < MIN_INSERT_MARKS and flags is not None:
        flags.append(f"선지가 {n_marks}개뿐입니다 — 지문이 짧아 넣을 자리가 부족합니다"
                     f"(지문 {n}문장). 배포 전 문항 유지 여부를 판단하세요.")
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
# 제목 (영어 선지) — 지문은 원본 그대로. 조판은 주제와 같은 모양.
# ---------------------------------------------------------------------------
def make_title(sentences: list[str], choices: list[str], answer_no: int,
               reason: str, wrong: dict[int, str]) -> tuple[str, str]:
    q = F.topic_q(" ".join(sentences), choices)
    a = F.topic_a(answer_no, reason, wrong)
    return q, a


# ---------------------------------------------------------------------------
# 무관한 문장 — 도입문 뒤 문장들에 ①~⑤, 그 사이에 새 문장 하나를 '끼워 넣는다'
# ---------------------------------------------------------------------------
MIN_IRRELEVANT_MARKS = 4     # 무관한 문장의 최소 선지 수(①~④)


def irrelevant_marks(n_sentences: int) -> int:
    """지문 길이로 ①~⑤ 개수를 정한다(도입문 1개는 반드시 남긴다).

    번호가 붙는 자리는 '원문 문장 (k-1)개 + 새로 쓴 문장 1개' 로 채운다. 그래서
    필요한 원문 문장은 도입문 1개 + (k-1)개다.

    수능 형식은 다섯 개지만, 네 문장짜리 지문에서는 도입문을 빼면 넷뿐이다.
    네 개까지는 내신에서 흔히 쓰는 형식이라 넷으로 줄여 낸다.
    """
    return max(0, min(5, n_sentences))


def make_irrelevant(sentences: list[str], start_no: int, answer_no: int,
                    sentence: str, reason: str,
                    wrong: dict[int, str]) -> tuple[str, str]:
    """지문 뒤쪽 문장들에 ①~⑤를 달고, answer_no 자리에 sentence 를 '끼워 넣는다'.

    도입문(번호 앞 문장들)은 번호 없이 그대로 두어 글의 주제를 먼저 제시한다.

    원문 문장은 하나도 버리지 않는다. 예전에는 그 자리의 원문 문장을 새 문장으로
    갈아 끼웠는데, 그러면 지문에서 문장 하나가 통째로 사라져 앞뒤가 끊기고 나머지
    선지의 해설이 '있지도 않은 문장'을 근거로 든다(실제 출력물: 12번에서 주제
    문장인 '포옹과 공감' 문장이 사라졌고, 28번에서는 ④의 But 이 대비할 앞 문장이
    없어졌다). start_no 는 호환을 위해 남겨 두지만 쓰지 않는다 — 번호 구간은 늘
    지문 끝까지 닿아야 하므로 하나로 정해진다.
    """
    n = len(sentences)
    k = irrelevant_marks(n)
    if k < MIN_IRRELEVANT_MARKS:
        raise ValueError(f"무관한 문장 문제는 문장 {MIN_IRRELEVANT_MARKS}개 "
                         f"이상이 필요합니다(지문 문장 {n}개).")
    if not (1 <= answer_no <= k):
        raise ValueError(f"무관한 문장 번호는 1~{k} 여야 합니다(현재 {answer_no}).")
    if not (sentence or "").strip():
        raise ValueError("무관한 문장 본문이 비어 있습니다.")
    # ①이 붙는 자리는 '뒤에서부터' 정해진다. 번호 구간이 지문 끝까지 닿아야 원문
    # 문장을 하나도 버리지 않는다(start_no 는 모델이 고르지 않는다).
    start = n - (k - 1) + 1
    intro = " ".join(s.strip() for s in sentences[:start - 1])
    rest = [s.strip() for s in sentences[start - 1:]]      # 원문 k-1 개
    marked = rest[:answer_no - 1] + [sentence.strip()] + rest[answer_no - 1:]
    q = F.irrelevant_q(intro, marked)
    a = F.irrelevant_a(answer_no, reason, wrong)
    return q, a


# ---------------------------------------------------------------------------
# 내용 일치 (원본 그대로 + 한글 선지) — 서술형 앞
# ---------------------------------------------------------------------------
def make_content(sentences: list[str], choices: list[str], answer_no: int,
                 reason: str, wrong: dict[int, str]) -> tuple[str, str]:
    q = F.content_q(" ".join(sentences), choices)
    a = F.content_a(answer_no, reason, wrong)
    return q, a


def make_content_ox(sentences: list[str], statements: list[str],
                    truths: list[bool], reasons: list[str],
                    axes: list[str] | None = None) -> tuple[str, str]:
    """내용 O/X — 진술을 각각 참·거짓으로 판정하게 한다(O 는 늘 2개).

    진술 수는 10개가 보통이고, 문장 5개 이하 지문의 영어판만 8개다(schemas.ox_sizes).
    """
    n = len(statements)
    if n not in (N_OX_SHORT, N_OX) or not (n == len(truths) == len(reasons)):
        raise ValueError(f"내용 O/X 는 진술·판정·근거의 개수가 같아야 하고, 그 수는 "
                         f"{N_OX_SHORT} 또는 {N_OX}여야 합니다"
                         f"(현재 진술 {n}·판정 {len(truths)}·근거 {len(reasons)}).")
    n_true = sum(1 for t in truths if t)
    if n_true != N_OX_TRUE:
        raise ValueError(f"O 인 진술이 {n_true}개입니다 — 정확히 {N_OX_TRUE}개여야 합니다.")
    yes = [i for i, t in enumerate(truths, 1) if t]
    if yes[1] - yes[0] < 3:
        raise ValueError(f"O 두 개가 {yes[0]}번·{yes[1]}번으로 붙어 있습니다 — "
                         "세 칸 이상 떨어뜨려야 자리만 보고 찍지 못합니다.")
    q = F.content_ox_q(" ".join(s.strip() for s in sentences), statements)
    a = F.content_ox_a(list(truths), list(reasons), axes)
    return q, a


# ---------------------------------------------------------------------------
# ④ 어휘 (지정 단어만 원본과 다름)
# ---------------------------------------------------------------------------
def make_vocab(sentences: list[str], marks: list[tuple[int, str, str]],
               answer_no: int, reason: str,
               overrides: dict[int, str] | None = None,
               flags: list[str] | None = None) -> tuple[str, str]:
    """marks: [(문장idx, 원본단어, 표시단어)] 5개.
    - 방식1(반의어): 정답 표시단어=반의어, 나머지=유의어.
    - 방식2(부정어): 표시단어=원본단어 그대로 + overrides 로 정답 문장에 부정어 삽입.
    """
    if len(marks) != 5:
        raise ValueError("어휘 밑줄은 5개여야 합니다.")
    # 밑줄을 찾을 대상은 '교체가 끝난 문장'이다. 원본 문장으로 순서를 매기면
    # 부정어형처럼 문장을 갈아 끼우는 방식에서 밑줄 위치·번호가 실제 지문과 어긋난다.
    eff = list(sentences)
    for i, txt in (overrides or {}).items():
        if 0 <= i < len(eff):
            eff[i] = txt
    # 밑줄 번호를 '읽는 순서'로 매기고 정답 번호도 그에 맞춰 재매핑
    marks, remap = order_marks(eff, marks)
    answer_no = remap.get(answer_no, answer_no)
    # 해설이 '네 번째 밑줄'·'3번'처럼 부른 번호도 같이 옮긴다. 그러지 않으면
    # 정답은 ④인데 해설은 '세 번째 밑줄이 정답'이라고 어긋난다(실제 결과물).
    reason = _relabel(reason, remap)
    marks = expand_marks(eff, marks)          # 'to confirm' 류 낱말 중복 방지
    marks = keep_sentence_case(eff, marks)    # 문장 첫 낱말이면 대문자 유지
    flag_ambiguous_marks(eff, marks, flags)   # 같은 낱말 여러 번 → 확인 권장
    marked = _passage_html(eff, _underline_marks(marks))
    return F.vocab_q(marked), F.vocab_a(answer_no, reason)


# ---------------------------------------------------------------------------
# ⑤ 어법 (지정 단어만 원본과 다름, 복수정답)
# ---------------------------------------------------------------------------
def make_grammar(sentences: list[str], marks: list[tuple[int, str, str]],
                 answer_nos: list[int], reasons: dict[int, str],
                 flags: list[str] | None = None,
                 points: dict[int, str] | None = None) -> tuple[str, str]:
    """marks: [(문장idx, 원본단어, 표시단어)] 2~8개. 틀린 것은 표시단어가 오답형.
    points: 밑줄 번호별 '문법 항목' 이름(해설에 알약으로 붙는다)."""
    if not (2 <= len(marks) <= 8):
        raise ValueError("어법 밑줄은 2~8개여야 합니다.")
    # 밑줄 번호를 '읽는 순서'로 매기고 정답 번호·근거·항목 키도 그에 맞춰 재매핑
    marks, remap = order_marks(sentences, marks)
    answer_nos = sorted(remap.get(n, n) for n in answer_nos)
    reasons = {remap.get(n, n): _relabel(t, remap) for n, t in reasons.items()}
    points = {remap.get(n, n): t for n, t in (points or {}).items()}
    marks = expand_marks(sentences, marks)      # 'to confirm' 류 낱말 중복 방지
    marks = keep_sentence_case(sentences, marks)    # 문장 첫 낱말이면 대문자 유지
    flag_ambiguous_marks(sentences, marks, flags)   # 같은 낱말 여러 번 → 확인 권장
    marked = _passage_html(sentences, _underline_marks(marks))
    return F.grammar_q(marked), F.grammar_a(answer_nos, reasons, points)


# ---------------------------------------------------------------------------
# 어법 개수 — 밑줄 5~7개 중 '틀린 것이 몇 개인지' 세게 한다
# ---------------------------------------------------------------------------
N_COUNT_MARKS = 6        # 밑줄 ①~⑥
MAX_WRONG_COUNT = 6      # 선지는 1개~6개
FIXED_WRONG_COUNT = 4    # 틀린 것은 늘 4개(정답 ④)


def make_grammar_count(sentences: list[str], marks: list[tuple[int, str, str]],
                       wrong_nos: list[int], reasons: dict[int, str],
                       note: str = "",
                       flags: list[str] | None = None) -> tuple[str, str]:
    """marks: [(문장idx, 원본단어, 표시단어)] 6개. 정답은 '틀린 밑줄의 개수'(=4개)."""
    if len(marks) != N_COUNT_MARKS:
        raise ValueError(f"어법 개수 문항의 밑줄은 정확히 {N_COUNT_MARKS}개여야 합니다.")
    marks, remap = order_marks(sentences, marks)      # 읽는 순서로 번호 재매핑
    wrong = sorted({remap.get(n, n) for n in wrong_nos})
    reasons = {remap.get(n, n): t for n, t in reasons.items()}
    n_wrong = len(wrong)
    if n_wrong != FIXED_WRONG_COUNT:
        raise ValueError(f"틀린 밑줄은 정확히 {FIXED_WRONG_COUNT}개여야 합니다"
                         f"(현재 {n_wrong}개).")
    marks = expand_marks(sentences, marks)            # 'to confirm' 류 낱말 중복 방지
    flag_ambiguous_marks(sentences, marks, flags)     # 같은 낱말 여러 번 → 확인 권장
    marked = _passage_html(sentences, _underline_marks(marks))
    q = F.grammar_count_q(marked, MAX_WRONG_COUNT)
    a = F.grammar_count_a(n_wrong, reasons, note)
    return q, a


def make_grammar_fix(sentences: list[str], marks: list[tuple[int, str, str]],
                     wrong_nos: list[int], reasons: dict[int, str],
                     note: str = "",
                     flags: list[str] | None = None,
                     points: dict[int, str] | None = None) -> tuple[str, str]:
    """어법 서술형 — 틀린 밑줄 4개의 '번호 + 바르게 고친 형태'를 학생이 적는다.

    개수만 세는 문항과 재료는 같다(밑줄 6개·틀린 것 4개). 다만 답을 고르는 대신
    적게 하므로 찍어서 맞힐 수 없고, '무엇이 왜 틀렸는지'까지 알아야 한다.
    고친 형태는 따로 물을 필요가 없다 — 다시 쓴 지문의 원래 낱말(word)이 곧 정답이고,
    보여 준 낱말(shown)이 틀린 형태다.
    """
    if len(marks) != N_COUNT_MARKS:
        raise ValueError(f"어법 서술형의 밑줄은 정확히 {N_COUNT_MARKS}개여야 합니다.")
    marks, remap = order_marks(sentences, marks)      # 읽는 순서로 번호 재매핑
    wrong = sorted({remap.get(n, n) for n in wrong_nos})
    reasons = {remap.get(n, n): t for n, t in reasons.items()}
    points = {remap.get(n, n): t for n, t in (points or {}).items()}
    if len(wrong) != FIXED_WRONG_COUNT:
        raise ValueError(f"틀린 밑줄은 정확히 {FIXED_WRONG_COUNT}개여야 합니다"
                         f"(현재 {len(wrong)}개).")
    fixes = {}
    for no in wrong:
        _idx, word, shown = marks[no - 1]
        if shown.strip().lower() == word.strip().lower():
            raise ValueError(f"{no}번 밑줄이 틀린 것으로 표시됐는데 원래 낱말과 같습니다"
                             f"('{shown}') — 고칠 것이 없습니다.")
        fixes[no] = (shown.strip(), word.strip())
    marks = expand_marks(sentences, marks)            # 'to confirm' 류 낱말 중복 방지
    flag_ambiguous_marks(sentences, marks, flags)     # 같은 낱말 여러 번 → 확인 권장
    marked = _passage_html(sentences, _underline_marks(marks))
    return (F.grammar_fix_q(marked, FIXED_WRONG_COUNT),
            F.grammar_fix_a(fixes, reasons, note, points))


# ---------------------------------------------------------------------------
# ⑥ 서술형 (원본 + 파생 과제)
# ---------------------------------------------------------------------------
def strip_ab_label(seg: str) -> str:
    """요약문 조각에서 '(A)'·'(B)' 빈칸 라벨을 제거하고 공백을 정리한다.

    LLM 이 before/mid/after 조각에 라벨 '(A)'·'(B)'를 직접 넣으면, 조판기가 붙이는
    라벨과 겹쳐 '(A),(A)_____'·'(B)(B)_____'처럼 중복된다. 조각에서는 라벨을 빼고
    조판기가 한 번만 붙이도록 정리한다."""
    s = re.sub(r"\(\s*[ABab]\s*\)", "", seg or "")
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)      # 라벨 제거로 생긴 '낱말 ,' → '낱말,'
    return re.sub(r"\s{2,}", " ", s).strip()


def take_trailing_punct(seg: str) -> tuple[str, str]:
    """조각 끝의 구두점을 떼어 돌려준다. LLM 이 '(A),'처럼 라벨 뒤에 붙인 구두점은
    라벨을 지우면 조각 끝에 남는데, 이는 '빈칸 뒤'에 와야 하므로 빈칸 뒤로 옮긴다."""
    m = re.search(r"([,.;:!?]+)$", seg)
    return (seg[:m.start()].rstrip(), m.group(1)) if m else (seg, "")


def make_short(
    sentences: list[str],
    q1_prompt: str, q1_answer: str,
    q2_prompt: str, q2_tokens: list[str], q2_cues: list[str], q2_answer: str,
    q3_prompt: str, q3_before: str, q3_mid: str, q3_after: str,
    q3_cue_a: str, q3_cue_b: str, q3_ans_a: str, q3_ans_b: str, q3_reason: str,
    flags: list[str] | None = None,
) -> tuple[str, str]:
    from . import review as _rv

    # (2) 영작 정답은 '지문에 실제로 있는 문장 그대로'여야 한다(원래 배열 보장).
    #     정확히 일치하지 않으면 토큰·답과 가장 잘 맞는 지문 문장으로 스냅(교정)한다.
    snapped = resolve_passage_sentence(q2_answer, q2_tokens, sentences)
    if snapped is None:
        raise ValueError("서술형(2) 영작 정답이 지문 문장과 맞지 않습니다(원래 배열을 찾지 못함).")
    # 정확 일치가 아니라 '유사도 스냅'으로 바뀐 경우만 확인 권장(부호만 다른 경우는 제외).
    if _norm(snapped) != _norm(q2_answer) and flags is not None:
        flags.append(_rv.FIX_SNAP)
    q2_answer = snapped
    # LLM 이 조각에 '(A)/(B)' 라벨을 넣어도 '(A)(A)_____'처럼 겹치지 않게 정리하고,
    # 빈칸 앞뒤 공백을 확보한다(요약문 빈칸 E 유형과 동일 처리).
    q3_before = strip_ab_label(q3_before)
    q3_mid = strip_ab_label(q3_mid)
    q3_after = strip_ab_label(q3_after)
    q3_before, _pa = take_trailing_punct(q3_before)
    q3_mid, _pb = take_trailing_punct(q3_mid)
    summary_html = (
        F.esc(q3_before) + " " + F.blank("A", q3_cue_a) + F.esc(_pa)
        + " " + F.esc(q3_mid) + " " + F.blank("B", q3_cue_b) + F.esc(_pb)
        + " " + F.esc(q3_after)
    )
    summary_html = re.sub(r"\s+([,.;:!?])", r"\1",
                          re.sub(r"\s{2,}", " ", summary_html)).strip()
    q = F.short_answer_q(
        passage=" ".join(sentences),
        q1_prompt=q1_prompt,
        q2_prompt=q2_prompt, q2_tokens=q2_tokens, q2_cues=q2_cues,
        q3_prompt=q3_prompt, q3_summary_html=summary_html,
    )
    a = F.short_answer_a(q1_answer, q2_answer,
                         {"A": q3_ans_a, "B": q3_ans_b}, q3_reason)
    return q, a
