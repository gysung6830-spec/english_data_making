"""완성된 산출물을 기계로 검산한다 (API 미사용).

생성 시점의 검사(exam/shape.py)는 문항 하나가 만들어질 때만 돈다. 그래서
'다 만들고 난 뒤에야 보이는 것'과 '문항끼리 부딪히는 것'은 걸리지 않는다.
사람이 PDF 를 손으로 대조하면 서른 문항에 한 시간이 걸리는데, 그렇게 찾은
결함의 대부분은 사실 규칙으로 잡히는 것들이었다. 이 모듈이 그것을 맡는다.

잡는 것 (문항 안)
  · 정답 표기가 없거나 선지 범위를 벗어남
  · 선지 개수·중복·길이 편중, 정답만 혼자 튀는 길이
  · 밑줄 개수(어휘 5 · 어법개수 6 · 짝짓기 5), 어법개수 정답이 ④인지
  · 지문 오염 — 마침표 뒤에 낱말이 붙음, 따옴표 짝이 안 맞음, 소문자로 시작
  · 어순 배열 <보기> 가 정답 문장을 복원하는지
  · 삽입·무관한 문장의 선지 수가 모자란지
  · 해설 위생 — 내부 용어·출제 메모·문장 번호 지칭·문체 혼재

잡는 것 (문항끼리)
  · 어휘·짝짓기의 밑줄 낱말이 겹침
  · 빈칸추론과 요약문의 정답 핵심어가 겹침
  · 삽입의 주어진 문장과 어순 배열의 정답이 같은 문장
  · 정답 번호가 한쪽에 몰림

못 잡는 것
  · '이 오답도 정답으로 읽히는가' — 글을 읽어야 하는 판단은 사람이나 모델의 몫이다.

웹앱은 조판 직전에 apply_to_flags() 로 이 결과를 검토 메모에 합친다.
사람이 쓰는 CLI 는 tools/검증.py.
"""
from __future__ import annotations

import re
from collections import Counter

from . import shape
from .merged import MERGED_LABELS, MERGED_ORDER
from .schemas import N_OX


_CIRC = "①②③④⑤⑥⑦⑧⑨⑩"
_MARKS = "①②③④⑤⑥⑦⑧⑨⑩ⓐⓑⓒⓓⓔ"

# 유형별로 기대하는 밑줄 개수(없으면 검사하지 않는다)
_N_MARKS = {"vocab": 5, "vocab_2": 5, "vocab_3": 5, "pair_odd": 5,
            "grammar_count": 6, "grammar_fix": 6}
# 선지 개수 — 허용하는 값들. 내용 O/X 영어판은 짧은 지문에서 8개다(schemas.ox_sizes).
_N_CHOICES = {"grammar_count": (6,), "content": (10,), "content_2": (8, 10)}
# <li> 선지가 없는 유형. 삽입·무관한 문장은 본문 속 위치 표시(①~⑤)가 선지 구실을 한다.
_NO_CHOICES = {"grammar", "vocab", "vocab_2", "vocab_3", "D", "insert",
               "irrelevant", "grammar_fix"}


def _txt(h: str) -> str:
    h = re.sub(r"<br\s*/?>", " ", h or "")
    t = re.sub(r"<[^>]+>", " ", h)
    t = (t.replace("&#39;", "'").replace("&nbsp;", " ").replace("&quot;", '"')
          .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------------------
# 문항 하나에서 필요한 조각을 뽑는다
# ---------------------------------------------------------------------------
def _parse(t: str, q: str, a: str) -> dict:
    key = re.search(r'<span class="answer-key">(.*?)</span>(.*?)</p>', a, re.S)
    body = re.search(r'<div class="passage[^"]*">(.*?)</div>', q, re.S)
    given = re.search(r'<div class="given-sentence">(.*?)</div>', q, re.S)
    boki = re.search(r'<div class="boki">(.*?)</div>', q, re.S)
    return {
        "type": t,
        "label": MERGED_LABELS.get(t, t),
        "key": _txt(key.group(1)) if key else "",
        "key_tail": _txt(key.group(2)) if key else "",
        "choices": [_txt(c) for c in re.findall(r"<li>(.*?)</li>", q, re.S)],
        "marks": [(n, _txt(w)) for n, w
                  in re.findall(r'<span class="cnum">(.)</span>\s*<u>(.*?)</u>', q)],
        "pos": re.findall(r'<span class="cnum">([①-⑧])</span>(?!\s*<u>)', q),
        "body": _txt(body.group(1)) if body else "",
        "given": _txt(given.group(1)) if given else "",
        "boki": _txt(boki.group(1)) if boki else "",
        "cues": [_txt(c) for c in re.findall(r'<span class="cue">(.*?)</span>', q, re.S)],
        "explain": _txt(a),
    }


def answer_no(key: str) -> int:
    """정답 표기에서 첫 번호를 뽑는다(복수정답이면 첫 번째)."""
    for c in key:
        if c in _CIRC:
            return _CIRC.index(c) + 1
    return 0


# ---------------------------------------------------------------------------
# 문항 안 검사
# ---------------------------------------------------------------------------
def _check_item(it: dict) -> list[str]:
    t, bad = it["type"], []

    # 정답 표기
    if not it["key"]:
        bad.append("정답 표기가 없습니다.")
    n_ans = answer_no(it["key"])
    if it["choices"] and n_ans and n_ans > len(it["choices"]):
        bad.append(f"정답 번호({it['key']})가 선지 수({len(it['choices'])})를 넘습니다.")

    # 선지
    if t not in _NO_CHOICES:
        want = _N_CHOICES.get(t, (5,))
        if len(it["choices"]) not in want:
            bad.append(f"선지가 {len(it['choices'])}개입니다"
                       f"(기대 {'·'.join(map(str, want))}개).")
        if it["choices"]:
            bad += shape.check_choice_shape(
                [re.sub(r"^[①-⑧]\s*", "", c) for c in it["choices"]], n_ans,
                noun_phrase=(t == "topic"))

    # 밑줄
    want_marks = _N_MARKS.get(t)
    if want_marks and len(it["marks"]) != want_marks:
        bad.append(f"밑줄이 {len(it['marks'])}개입니다(기대 {want_marks}개).")
    if t == "grammar" and not (2 <= len(it["marks"]) <= 8):
        bad.append(f"어법 밑줄이 {len(it['marks'])}개입니다(2~8개여야 합니다).")

    # 어법 개수 — 정답은 늘 ④(4개)
    if t == "grammar_count" and it["key"] and "④" not in it["key"]:
        bad.append(f"어법 개수의 정답이 {it['key']}입니다 — 틀린 것은 늘 4개(④)로 냅니다.")

    # 어법 서술형 — 고쳐 쓸 것이 정확히 4개, 모두 '보여 준 형태 → 바른 형태'
    if t == "grammar_fix":
        fixes = re.findall(r"[①-⑧][^,]*?→", it["key"])
        if len(fixes) != 4:
            bad.append(f"고쳐 쓸 밑줄이 {len(fixes)}개입니다(4개여야 합니다).")

    # 내용 O/X — 진술이 모두 판정돼야 하고, O 는 늘 둘이며 서로 붙어 있으면 안 된다.
    # 진술 수는 지문 길이에 따라 8 또는 10이므로(schemas.ox_sizes) 문제편의 진술 수와 맞춘다.
    if t in ("content", "content_2"):
        marks = re.findall(r"[①-⑩]\s*([OX])", it["key"])
        want = len(it["choices"]) or N_OX
        if len(marks) != want:
            bad.append(f"O/X 판정이 {len(marks)}개입니다(진술 {want}개 모두여야 합니다).")
        elif marks.count("O") != 2:
            bad.append(f"O 가 {marks.count('O')}개입니다 — 늘 2개여야 합니다"
                       "(비율이 흔들리면 학생이 감으로 찍습니다).")
        else:
            yes = [i for i, m in enumerate(marks, 1) if m == "O"]
            if yes[1] - yes[0] < 3:
                bad.append(f"O 두 개가 {yes[0]}번·{yes[1]}번으로 붙어 있습니다 — "
                           "세 칸 이상 떨어뜨려야 자리만 보고 찍지 못합니다.")

    # 위치 표시(삽입·무관한 문장)의 자리 수
    if t in ("insert", "irrelevant"):
        n_pos = len(it["pos"])
        if n_pos and n_pos < 4:
            bad.append(f"선지가 {n_pos}개뿐입니다 — 지문이 짧아 자리가 부족합니다"
                       "(찍어도 맞을 확률이 높습니다).")

    # 밑줄 낱말이 문장을 깨뜨리는가(목적어 없는 타동사)
    if it["marks"] and it["body"]:
        bad += shape.check_marks_in_passage(it["body"], it["marks"])

    # 지문 오염
    for name, text in (("지문", it["body"]), ("주어진 문장", it["given"])):
        if text:
            bad += [f"{name}: {m}" for m in _check_passage(text, name)]

    # 어순 배열 <보기>
    if t == "D" and it["boki"]:
        toks = [x.strip() for x in it["boki"].replace("<보기>", "").split("/")]
        ans = it["key_tail"] or it["key"]
        if ans:
            bad += shape.check_tokens_rebuild(toks, ans, it["cues"])
            bad += shape.check_tokens_shuffled(toks, ans)

    # 해설 위생
    bad += [re.sub(r"^자동검사:\s*", "", m) for m in shape.check_explanation(it["explain"])]
    return bad


def _check_passage(text: str, name: str) -> list[str]:
    """조판된 지문에서 눈에 띄는 오염을 찾는다."""
    bad = []
    # 마침표 뒤에 곧바로 낱말이 붙음 — 모델이 지시문 조각을 흘린 자국
    # 낱말 세 글자 이상 뒤에 오는 마침표만 본다(U.S.·e.g. 같은 약어를 걸러내기 위해).
    m = re.search(r"[a-z]{3}[.!?]+[A-Za-z]\w*", text)
    if m:
        bad.append(f"마침표 뒤에 낱말이 붙어 있습니다('{m.group(0)}') — 지시문 조각이 "
                   "섞였는지 확인하세요.")
    # 문장이 소문자로 시작 — 유의어 치환이 첫 낱말을 갈아 끼운 자국.
    # 여기서는 split_sentences 를 쓸 수 없다. 그 함수는 '대문자로 시작하는 문장'만
    # 나누므로, 소문자로 시작하는 문장은 앞 문장에 붙어 버려 영영 안 보인다.
    # 대신 약어·이니셜의 마침표만 가리고 '남은 마침표'에서 모두 자른다.
    from .analyzer import mask_abbrev

    for s in re.split(r"(?<=[.!?])\s+", mask_abbrev(text)):
        s = s.replace("\x00", ".")
        s = re.sub(r"^[①-⑧ⓐ-ⓔ\s]+", "", s.strip())
        if s and s[0].isalpha() and s[0].islower():
            bad.append(f"문장이 소문자로 시작합니다('{s[:34]}…').")
            break
    # 따옴표 짝
    if text.count('"') % 2:
        bad.append("큰따옴표 짝이 맞지 않습니다.")
    return bad


# ---------------------------------------------------------------------------
# 문항끼리 검사
# ---------------------------------------------------------------------------
def _check_cross(items: dict[str, dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}

    def _add(t: str, msg: str) -> None:
        out.setdefault(t, []).append(msg)

    # 1) 밑줄 낱말 겹침 — 정본에 밑줄을 치는 문항끼리
    # '다시 쓴 지문' 위에 서는 둘은 뺀다 — 어법 서술형(grammar_fix)과
    # 어휘 원문단어형(vocab_2). 지문이 다르므로 같은 낱말을 써도 겹침이 아니다.
    same_body = [t for t in ("grammar", "pair_odd", "vocab", "vocab_3")
                 if t in items]
    seen: dict[str, str] = {}
    for t in same_body:
        for _n, w in items[t]["marks"]:
            k = w.strip().lower()
            if k in seen and seen[k] != t:
                _add(t, f"밑줄 '{w}'가 {MERGED_LABELS.get(seen[k], seen[k])} 문항과 "
                        "겹칩니다.")
            seen.setdefault(k, t)

    # 1-b) 어휘 문항의 '정답 밑줄'이 같은 문장에 몰렸는가
    #      한 문장이 세 문항에서 잇달아 정답 자리가 되면 문제집이 되풀이처럼 읽힌다
    #      (실제 출력물: 24·25·26번의 정답이 모두 여덟 번째 문장에 있었다).
    vocab_t = [t for t in ("vocab_2", "vocab", "vocab_3") if t in items]
    where: dict[int, list[str]] = {}
    for t in vocab_t:
        sent = _answer_sentence(items[t])
        if sent:
            where.setdefault(sent, []).append(t)
    for _sent, ts in where.items():
        # 셋 이상이 겹치거나, 어휘 문항이 '모두' 한 문장에 몰렸을 때만 알린다.
        # 짧은 지문에서는 둘이 겹치는 일이 흔해, 그것까지 알리면 메모가 시끄러워진다.
        if len(ts) >= 3 or (len(ts) >= 2 and len(ts) == len(vocab_t)):
            names = ", ".join(f"{items[t]['no']}번" for t in ts)
            for t in ts:
                _add(t, f"어휘 문항의 정답 밑줄이 같은 문장에 몰려 있습니다({names}) — "
                        f"학생이 같은 자리를 {len(ts)}번 읽습니다.")

    # 1-c) 내용 O/X 두 판의 O 자리가 같은가
    if "content" in items and "content_2" in items:
        def _yes(it):
            return tuple(i for i, m in enumerate(
                re.findall(r"[①-⑩]\s*([OX])", it["key"]), 1) if m == "O")
        if _yes(items["content"]) and _yes(items["content"]) == _yes(items["content_2"]):
            msg = ("내용 O/X 두 판의 O 자리가 같습니다 — 한 판을 푼 학생이 다른 판을 "
                   "자리만 보고 옮겨 적습니다.")
            _add("content", msg)
            _add("content_2", msg)

    # 2) 빈칸추론과 요약문의 정답 핵심어
    if "F" in items and "E" in items:
        fa = _choice_of(items["F"])
        ea = _choice_of(items["E"])
        for msg in shape.check_key_overlap(fa, ea, "빈칸추론", "요약문"):
            _add("F", msg)
            _add("E", msg)

    # 3) 삽입의 주어진 문장 = 어순 배열의 정답
    if "insert" in items and "D" in items:
        g = _norm(items["insert"]["given"])
        d = _norm(items["D"]["key_tail"] or items["D"]["key"])
        if g and d and (g == d or g in d or d in g):
            msg = ("문장 삽입의 '주어진 문장'과 어순 배열의 정답이 같은 문장입니다 — "
                   "삽입 문항이 어순 배열의 답을 완성된 형태로 보여 줍니다.")
            _add("insert", msg)
            _add("D", msg)
    return out


def _answer_sentence(it: dict) -> int:
    """정답 밑줄이 지문의 '몇 번째 문장'에 있는지(1-based, 못 찾으면 0).

    문장의 글로 맞대면 안 된다 — 어휘 문항끼리는 바로 그 낱말이 서로 다르므로
    같은 문장인데도 다른 글이 된다(24·25·26번의 respond/ignore/rarely/never).
    자리(번째)로 맞대야 같은 문장임이 드러난다.
    """
    n = answer_no(it["key"])
    marks = it["marks"]
    if not (1 <= n <= len(marks)):
        return 0
    word = marks[n - 1][1]
    if not word:
        return 0
    for i, sent in enumerate(re.split(r"(?<=[.!?])\s+", it["body"]), 1):
        if re.search(r"(?<![\w])" + re.escape(word) + r"(?![\w])", sent):
            return i
    return 0


def _choice_of(it: dict) -> str:
    n = answer_no(it["key"])
    if 1 <= n <= len(it["choices"]):
        return re.sub(r"^[①-⑧]\s*", "", it["choices"][n - 1])
    return ""


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


# ---------------------------------------------------------------------------
# 지문 하나 검산
# ---------------------------------------------------------------------------
def check_passage(passage, start_no: int = 1) -> tuple[list[dict], list[str]]:
    """(문항별 결과, 지문 전체 사유). 문항별 결과는 출제 순서대로."""
    items: dict[str, dict] = {}
    rows: list[dict] = []
    no = start_no
    for t in MERGED_ORDER:
        q, a = (passage.q.get(t) or "").strip(), (passage.a.get(t) or "").strip()
        if not (q and a):
            continue
        it = _parse(t, q, a)
        it["no"] = no
        items[t] = it
        rows.append(it)
        no += 1

    for it in rows:
        it["bad"] = _check_item(it)
        it["flags"] = list(passage.flags.get(it["type"], []))

    for t, msgs in _check_cross(items).items():
        items[t]["bad"] += msgs

    whole: list[str] = []
    missing = [MERGED_LABELS.get(t, t) for t in MERGED_ORDER if t not in items]
    if missing:
        whole.append(f"{len(missing)}개 유형이 빠졌습니다: {', '.join(missing)}")
    # 정답 번호 쏠림 — 단일정답 문항만 센다
    keys = [answer_no(it["key"]) for it in rows
            if it["type"] not in ("grammar", "D", "grammar_fix",
                                  "content", "content_2")
            and answer_no(it["key"])]
    if keys:
        c = Counter(keys)
        top, n = c.most_common(1)[0]
        if n > max(3, len(keys) // 2):
            whole.append(f"정답이 {_CIRC[top - 1]}에 몰려 있습니다({n}/{len(keys)}문항).")
    return rows, whole


_MEMO_HEAD = re.compile(r"^(?:자동검사|자동검증):\s*")


def _memo_key(msg: str) -> str:
    """같은 지적인지 가리는 열쇠 — 승격 표시와 줄표 뒤 설명을 떼고 본다.

    생성 때 붙인 사유와 검산이 다시 찾아낸 사유는 말끝만 다를 뿐 같은 지적인
    경우가 많다(실제 출력물: '선지가 3개뿐입니다 —' 가 검토메모에 두 번 실렸다).
    """
    m = _MEMO_HEAD.sub("", (msg or "").strip())
    return re.split(r"\s*—\s*|\s*\(", m)[0].strip()


def apply_to_flags(passage, start_no: int = 1) -> int:
    """검산 결과를 Passage.flags 에 합친다(검토 메모에 그대로 실린다).

    승격이 끝난 뒤에 부르는 것이 맞다 — 이건 '다 만들고 난 뒤'의 시선이라,
    다시 만들어서 고칠 것이 아니라 사람이 배포 전에 볼 것이다.
    """
    rows, whole = check_passage(passage, start_no)
    n = 0
    for it in rows:
        have = {_memo_key(m) for m in passage.flags.get(it["type"], [])}
        fresh = []
        for m in it["bad"]:
            k = _memo_key(m)
            if k in have:
                continue
            have.add(k)
            fresh.append(m)
        if fresh:
            passage.flag(it["type"], fresh)
            n += len(fresh)
    if whole and rows:
        passage.flag(rows[0]["type"], whole)
        n += len(whole)
    return n
