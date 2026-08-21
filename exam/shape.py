"""'모양만 보고 답이 보이는' 통로를 막는 기계적 검사.

판단이 걸린 유형(빈칸추론·삽입·순서·요약문·내용일치·함의추론)은 정답이 유일한지를
사람이나 모델이 판단해야 하지만, **문항이 무너지는 흔한 방식은 판단이 아니라 모양**이다.
정답만 유독 길거나, 정답 선지에만 없는 단어가 있거나, 삽입할 문장에 지시어가 없어
들어갈 자리가 여러 곳이 되는 식이다. 이런 것들은 글을 이해하지 않아도 규칙으로 잡힌다.

여기 있는 검사는 모두 생성 직후 extra_validate 로 걸려 재요청을 부른다. 재시도를
소진하면 그 문항만 빠지거나 검토메모에 남는다(지문 전체를 버리지 않는다).
"""
from __future__ import annotations

import re

# 지시어·연결사 — 문장이 앞을 '받고 있음'을 알려 주는 표지.
# 삽입 문제의 주어진 문장에 이런 표지가 하나도 없으면 들어갈 자리가 여러 곳이 된다.
# 관사 the/a 는 거의 모든 문장에 있어 단서 구실을 못 하므로 넣지 않는다.
ANAPHORA = {
    "this", "that", "these", "those", "such", "it", "its", "they", "them",
    "their", "he", "she", "his", "her", "another", "other", "others",
    "the same", "the former", "the latter", "both", "either", "neither",
}
CONNECTIVES = {
    "however", "therefore", "thus", "hence", "moreover", "furthermore",
    "nevertheless", "nonetheless", "instead", "meanwhile", "besides",
    "consequently", "accordingly", "similarly", "likewise", "conversely",
    "yet", "still", "also", "then", "but", "so", "because", "since",
    "for example", "for instance", "in contrast", "on the other hand",
    "in addition", "as a result", "in fact", "indeed", "by contrast",
    "at the same time", "in short", "that is", "in other words", "after all",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text.lower())


def cues_in(sentence: str) -> list[str]:
    """문장에서 찾은 지시어·연결사 목록(소문자)."""
    low = " " + " ".join(_words(sentence)) + " "
    found = [p for p in (ANAPHORA | CONNECTIVES) if " " in p and f" {p} " in low]
    found += [w for w in set(_words(sentence)) if w in ANAPHORA or w in CONNECTIVES]
    return sorted(set(found))


def check_insert_cue(sentence: str) -> list[str]:
    """삽입 문제의 '주어진 문장'이 자리를 하나로 굳힐 단서를 갖고 있는가.

    지시어(this·such·they…)나 연결사(however·therefore…)가 하나도 없는 문장은
    앞뒤 어디에 넣어도 말이 되어 복수정답이 된다 — 이 유형이 무너지는 첫 번째 통로다.
    """
    if not (sentence or "").strip():
        return ["주어진 문장이 비어 있습니다."]
    if not cues_in(sentence):
        return ["주어진 문장에 지시어(this·such·they 등)나 연결사(however·therefore 등)가 "
                "하나도 없습니다 — 들어갈 자리가 한 곳으로 굳지 않아 복수정답이 됩니다."]
    return []


def check_choice_shape(choices: list[str], answer_no: int, kind: str = "선지",
                       spread: float = 2.2) -> list[str]:
    """선지 5개가 '모양'으로 정답을 흘리지 않는가.

    실제 출제에서 가장 흔한 사고: 정답만 유독 길다(또는 짧다). 학생은 뜻을 몰라도
    남다른 하나를 고른다. 길이 편차와 중복만 봐도 이 통로는 막힌다.
    """
    bad: list[str] = []
    if len(choices) < 2:
        return bad
    lens = [len(c.strip()) for c in choices]
    if min(lens) == 0:
        return [f"비어 있는 {kind}가 있습니다."]
    if max(lens) > min(lens) * spread:
        bad.append(f"{kind} 길이가 고르지 않습니다(가장 짧은 것 {min(lens)}자 / "
                   f"가장 긴 것 {max(lens)}자) — 길이만 보고 답을 고르게 됩니다.")
    # 정답이 '가장 길거나 가장 짧은 하나'로 혼자 튀는 경우
    if 1 <= answer_no <= len(lens):
        a = lens[answer_no - 1]
        others = lens[:answer_no - 1] + lens[answer_no:]
        if others and (a > max(others) * 1.6 or a * 1.6 < min(others)):
            bad.append(f"정답 {kind}만 길이가 혼자 튑니다(정답 {a}자 / 나머지 "
                       f"{min(others)}~{max(others)}자).")
    if len({c.strip().lower() for c in choices}) != len(choices):
        bad.append(f"같은 {kind}가 두 번 나옵니다.")
    return bad


# 정답 자리에 오면 '긍정형으로 뒤집어야 하는' 부정 의미 어휘.
# 형태만 보고 판정하면(un-·in- 접두어) unique·important·increase 까지 걸리므로
# 실제로 뒤집기가 자연스러운 낱말만 추려 둔다.
NEGATIVE_ANSWERS = {
    "unlikely", "unable", "unaware", "unclear", "uncertain", "unnecessary",
    "unimportant", "unsuccessful", "unwilling", "unfamiliar", "unavailable",
    "unpredictable", "unrealistic", "unsafe", "unhelpful", "unfair", "unequal",
    "impossible", "impractical", "imperfect", "inadequate", "inaccurate",
    "insufficient", "incapable", "incomplete", "ineffective", "inefficient",
    "invisible", "incorrect", "inconsistent",
    "irrelevant", "irregular", "irrational", "illogical", "illegal",
    "dishonest", "disadvantageous",
    "absent", "useless", "meaningless", "helpless", "hopeless", "worthless",
    "powerless", "fruitless",
}
# '-less' 로 끝나면 대개 부정 의미지만, 아래는 부정어가 아니라 접속 부사다.
_NOT_LESS = {"unless", "regardless", "nevertheless", "nonetheless", "bless"}


def _is_negative_word(word: str) -> bool:
    w = word.strip().lower()
    if w in NEGATIVE_ANSWERS:
        return True
    return len(w) >= 7 and w.endswith("less") and w not in _NOT_LESS


def check_summary_answer_polarity(pairs, answer_no: int) -> list[str]:
    """요약문 정답이 '부정 의미 어휘'로 되어 있지 않은가.

    정답이 unlikely·impossible 처럼 그 자체로 부정을 품은 낱말이면, 학생은 요약문을
    제대로 읽지 않고 '지문이 부정적이었지' 하는 인상만으로 고른다. 부정은 요약문 문장
    쪽에 not·never·hardly 로 드러내고, 빈칸의 정답은 그 긍정형으로 두어야 한다.

        나쁨: "DNA storage is ___(A)___ to replace hard drives."   + (A) unlikely
        좋음: "DNA storage is not ___(A)___ to replace hard drives." + (A) likely

    이러면 학생은 문장의 부정을 읽고 '무엇이 부정되는지'를 지문에서 확인해야 한다.
    """
    if not pairs or not (1 <= answer_no <= len(pairs)):
        return []
    ans = pairs[answer_no - 1]
    hit = [str(getattr(ans, k, "")) for k in ("a", "b")
           if _is_negative_word(str(getattr(ans, k, "")))]
    if hit:
        return [f"정답이 부정 의미 어휘({', '.join(hit)})입니다 — 부정은 요약문 문장에 "
                "not·never·hardly 로 드러내고, 빈칸의 정답은 그 긍정형으로 바꾸세요"
                "(예: (A)=unlikely → 문장에 not 을 넣고 (A)=likely)."]
    return []


def check_summary_pairs(pairs, answer_no: int) -> list[str]:
    """요약문 (A)(B) 낱말쌍이 '읽지 않고도' 풀리지 않는가.

    정답 행의 (A) 낱말이 그 행에만 있으면, 학생은 요약문을 읽지 않고 '혼자만 다른
    낱말'을 피해 가거나 골라 버린다. 각 칸의 낱말은 여러 행에 겹쳐 나와야 한다.
    """
    bad: list[str] = []
    if not pairs or not (1 <= answer_no <= len(pairs)):
        return ["요약문 낱말쌍 또는 정답 번호가 잘못되었습니다."]
    col_a = [str(getattr(p, "a", "")).strip().lower() for p in pairs]
    col_b = [str(getattr(p, "b", "")).strip().lower() for p in pairs]
    for label, col in (("(A)", col_a), ("(B)", col_b)):
        if len(set(col)) < 2:
            bad.append(f"{label} 칸의 낱말이 전부 같습니다 — 고를 것이 없습니다.")
            continue
        if len(set(col)) > 3:
            bad.append(f"{label} 칸에 서로 다른 낱말이 {len(set(col))}개입니다 — "
                       "두세 개 안에서 돌려 써야 요약문을 읽고 고르게 됩니다.")
        ans = col[answer_no - 1]
        if col.count(ans) < 2:
            bad.append(f"정답 행의 {label} 낱말('{ans}')이 그 행에만 있습니다 — "
                       "요약문을 읽지 않고도 답이 드러납니다.")
    if len({(a, b) for a, b in zip(col_a, col_b)}) != len(pairs):
        bad.append("같은 (A)(B) 조합이 두 번 나옵니다.")
    return bad + check_summary_answer_polarity(pairs, answer_no)


def check_order_shuffle(display: list[int]) -> list[str]:
    """순서 배열의 (A)(B)(C)(D)가 실제로 섞였는가.

    display 가 [1,2,3,…] 이면 라벨이 원문 순서 그대로라 정답이 늘 'A-B-C-D'가 된다.
    첫 라벨이 첫 덩어리인 것도 피한다 — (A)가 곧 시작이면 절반은 그냥 보인다.
    """
    d = list(display or [])
    if not d:
        return ["(A)(B)(C)… 배치(display)가 비어 있습니다."]
    if d == list(range(1, len(d) + 1)):
        return ["라벨이 원문 순서 그대로입니다 — 섞이지 않으면 문제가 되지 않습니다."]
    if d[0] == 1:
        return ["(A)가 첫 덩어리입니다 — 시작이 드러나 순서를 절반은 그냥 알게 됩니다."]
    return []


def check_phrase_in_passage(phrase: str, sentences: list[str], kind: str) -> list[str]:
    """밑줄 어구·빈칸 어구가 지문에 실제로 있는가(조판이 어긋나는 것을 미리 막는다)."""
    p = " ".join(_words(phrase))
    if not p:
        return [f"{kind}가 비어 있습니다."]
    body = " ".join(_words(" ".join(sentences)))
    if p not in body:
        return [f"{kind}('{phrase.strip()}')가 지문에 그대로 나오지 않습니다."]
    return []


def _content(text: str) -> set[str]:
    """비교용 내용어 집합(짧은 기능어 제외)."""
    return {w for w in _words(text) if len(w) > 3}


# 비교용 내용어 — 어미(s·es·ed·ing)를 떼어 어형 차이를 흡수한다.
def _content_words(text: str) -> set[str]:
    out = set()
    for w in _words(text):
        if len(w) < 4:
            continue
        for suf in ("ing", "es", "ed", "s"):
            if len(w) > len(suf) + 2 and w.endswith(suf):
                w = w[: -len(suf)]
                break
        out.add(w)
    return out


def check_rewrite(rewritten: list[str], original: list[str],
                  min_changed: float = 0.6, min_topic: float = 0.25) -> list[str]:
    """어법 문항용으로 '다시 쓴 지문'이 제구실을 하는가.

    지문을 통째로 외운 학생이 '달라진 낱말 찾기'로 풀지 못하게 하려면 표현이 실제로
    달라야 하고(min_changed), 그러면서도 같은 글이어야 한다(min_topic).
    문장 수가 어긋나면 밑줄 번호가 원문과 안 맞으므로 그대로 거절한다.
    """
    bad: list[str] = []
    if not rewritten or any(not (s or "").strip() for s in rewritten):
        return ["다시 쓴 지문이 비어 있거나 빈 문장이 섞여 있습니다."]
    if len(rewritten) != len(original):
        return [f"다시 쓴 지문의 문장 수가 원문과 다릅니다"
                f"(원문 {len(original)}개 / 다시 쓴 것 {len(rewritten)}개). "
                "문장을 합치거나 나누지 말고 1:1로 다시 쓰세요."]

    def _norm(t: str) -> str:
        return " ".join(_words(t))

    same = sum(1 for r, o in zip(rewritten, original) if _norm(r) == _norm(o))
    changed = 1 - same / len(original)
    if changed < min_changed:
        bad.append(f"문장 {len(original)}개 중 {same}개가 원문과 글자 그대로 같습니다 — "
                   f"최소 {int(min_changed * 100)}%는 표현을 바꿔야 '외워서 풀기'가 막힙니다.")
    a, b = _content(" ".join(rewritten)), _content(" ".join(original))
    if a and b and len(a & b) / len(a | b) < min_topic:
        bad.append("다시 쓴 지문이 원문과 너무 동떨어졌습니다 — 표현만 바꾸고 내용은 "
                   "그대로 유지해야 합니다.")
    return bad


def check_blank_answer_paraphrase(answer: str, blank_phrase: str,
                                  sentences: list[str], min_new: float = 0.5) -> list[str]:
    """빈칸추론의 정답이 '지문에 있던 어구 그대로'가 아닌가.

    빈칸은 지문의 핵심 어구를 지운 자리다. 그 자리에 원문 어구를 그대로 돌려놓는 것이
    정답이면, 학생은 글을 이해하지 않고 '지문에서 본 표현'만 찾아 고른다. 정답은 그 어구를
    '다른 말로 바꿔 쓴 것'이어야 글의 논지를 파악했는지가 드러난다.

    ① 정답 문구가 지문에 그대로 나오면 실격.
    ② 정답의 내용어가 대부분 빈칸 어구에서 온 것이면(새 낱말이 적으면) 실격 —
       어순만 바꾼 것은 패러프레이즈가 아니다.
    """
    a = _content_words(answer)
    if not a:
        return ["정답 선지에 내용어가 없습니다."]
    body = " ".join(_words(" ".join(sentences)))
    if " ".join(_words(answer)) in body:
        return [f"정답('{answer.strip()}')이 지문에 그대로 나옵니다 — 빈칸 어구를 다른 말로 "
                "바꿔 쓴 표현이어야 합니다."]
    bad: list[str] = []
    blank = _content_words(blank_phrase)
    if blank:
        new = a - blank
        if len(new) / len(a) < min_new:
            bad.append(f"정답이 빈칸 어구('{blank_phrase.strip()}')의 낱말을 거의 그대로 "
                       f"씁니다(새 낱말 {len(new)}/{len(a)}) — 어순만 바꾼 것은 "
                       "패러프레이즈가 아닙니다.")
    # 지문에 있는 내용어만으로 이루어졌으면 '본 표현 찾기'가 되어 버린다
    passage = _content_words(" ".join(sentences))
    if a and a <= passage:
        bad.append("정답의 낱말이 모두 지문에 있는 것뿐입니다 — 유의어로 바꾼 낱말이 "
                   "적어도 하나는 있어야 합니다.")
    return bad


# ---------------------------------------------------------------------------
# 부정어형 어휘 — 정답 근거가 '밑줄 안에' 있는지
# ---------------------------------------------------------------------------
# 부정어. 이 중 하나가 정답 밑줄 안에 들어 있어야 '밑줄 친 것 중 부적절한 것'이 성립한다.
NEGATORS = {
    "not", "no", "never", "neither", "nor", "none", "nothing", "nobody",
    "hardly", "scarcely", "barely", "rarely", "seldom", "cannot", "without",
    "n't", "fail", "fails", "failed", "failing",
}


def _has_negator(text: str) -> bool:
    low = (text or "").lower()
    if "n't" in low:
        return True
    return bool(NEGATORS & set(re.findall(r"[a-z']+", low)))


def check_negation_underline(marks, answer_no: int, override_text: str) -> list[str]:
    """부정어형 어휘: 삽입한 부정어가 '정답 밑줄 안'에 있는지 확인한다.

    이 방식은 정답 문장에 not·never 를 넣어 흐름과 모순되게 만든다. 그런데 밑줄을
    원문 낱말에만 그으면, 밑줄 다섯 개는 모두 문맥상 적절하고 부적절한 것은 밑줄
    '바깥'의 부정어가 된다 → '밑줄 친 부분 중 적절하지 않은 것'에 정답이 없다.
    (실제 출력물에서 두 지문 모두 이 방식으로 무너졌다.)

    그래서 정답 밑줄은 삽입한 부정어를 품은 어구여야 한다(예: 'delete' → 'never delete').
    marks: [(sent_no, word, shown)] 또는 word/shown 속성을 가진 객체들.
    """
    bad: list[str] = []
    if not _has_negator(override_text):
        bad.append("부정어형인데 교체 문장에 부정어(not·no·never·hardly …)가 없습니다.")
    items = []
    for m in marks:
        if isinstance(m, (tuple, list)):
            items.append((str(m[1]), str(m[2] if len(m) > 2 else m[1])))
        else:
            items.append((str(getattr(m, "word", "")), str(getattr(m, "shown", ""))))
    if not (1 <= answer_no <= len(items)):
        return bad + [f"정답 밑줄 번호가 범위를 벗어났습니다: {answer_no}"]
    word, shown = items[answer_no - 1]
    if not (_has_negator(word) or _has_negator(shown)):
        bad.append(f"정답 밑줄('{shown or word}')에 부정어가 없습니다 — 삽입한 부정어를 "
                   "포함하는 어구를 정답 밑줄로 잡으세요(예: word='delete' → "
                   "word/shown='never delete'). 그러지 않으면 밑줄 다섯 개가 모두 "
                   "적절해져 정답이 없는 문항이 됩니다.")
    if word.strip() and override_text and word.strip().lower() not in override_text.lower():
        bad.append(f"정답 밑줄 어구('{word.strip()}')가 교체 문장에 그대로 있지 않습니다.")
    return bad


# ---------------------------------------------------------------------------
# 해설 문구 위생 — 내부 용어·출제 메모가 인쇄물로 새는 것을 막는다
# ---------------------------------------------------------------------------
# 스키마 필드명·코드 용어. 해설에 나오면 학생이 읽을 수 없는 말이 인쇄된다.
INTERNAL_TERMS = (
    "override", "sent_no", "answer_no", "start_no", "remove_no", "wrong_reasons",
    "blank_phrase", "choices", "cues", "tokens", "a_ok", "b_ok", "prompt",
    "json", "schema", "placeholder", "토큰", "플레이스홀더", "스키마", "프롬프트",
)
# 출제 과정을 학생에게 설명하는 말 — 해설이 아니라 개발 메모다.
_AUTHOR_NOTES = (
    "배열을 조정", "조정하였다", "조정했다", "무작위로 섞", "섞어 제시",
    "문제에서는", "좋은 문제", "좋은 삽입", "좋은 빈칸", "출제 의도", "정답으로 적절",
    "이 문항은 ~로 설계", "설계하였다", "설계했다",
    "구성한 문제", "구성하였다", "틀리도록", "이 문항은", "문제로 구성",
    "빼낸 문장", "제시된 단어들을", "토큰들을",
)
# 학생용 지문에는 문장 번호가 없다. '(3)에서'·'(9)문장' 식 지칭은 대조할 수 없다.
_SENT_REF = re.compile(r"[(（]\d+[)）]\s*(문장|에서|은|는|이|가|의|과|와|에)")


_HANGUL = re.compile(r"[가-힣]")


def internal_terms_in(obj) -> list[str]:
    """구조화 출력의 '한국어 설명 필드'에서만 내부 용어를 찾는다.

    한글이 없는 문자열은 영어 지문·선지·낱말 목록이므로 건너뛴다. 그러지 않으면
    'consumers face many choices' 같은 정상 영어 선지가 걸려 생성이 헛돌게 된다.
    """
    found: set[str] = set()

    def _walk(v) -> None:
        if isinstance(v, str):
            if not _HANGUL.search(v):
                return
            low = v.lower()
            for t in INTERNAL_TERMS:
                if t.lower() in low:
                    found.add(t)
        elif isinstance(v, dict):
            for x in v.values():
                _walk(x)
        elif isinstance(v, (list, tuple, set)):
            for x in v:
                _walk(x)
        elif hasattr(v, "__dict__"):
            for x in vars(v).values():
                _walk(x)

    _walk(obj)
    return sorted(found)


def check_explanation(text: str) -> list[str]:
    """해설 한 덩어리를 검사한다(내부 용어·출제 메모·문장 번호 지칭·문체 혼재)."""
    bad: list[str] = []
    low = (text or "").lower()
    hit = [t for t in INTERNAL_TERMS if t.lower() in low]
    if hit:
        bad.append("해설에 내부 용어가 그대로 있습니다: " + ", ".join(hit))
    notes = [n for n in _AUTHOR_NOTES if n in (text or "")]
    if notes:
        bad.append("해설에 출제 과정 메모가 있습니다: " + ", ".join(notes))
    if _SENT_REF.search(text or ""):
        bad.append("해설이 '(3)에서'처럼 문장 번호로 지칭합니다 — 학생용 지문에는 "
                   "번호가 없어 대조할 수 없습니다.")
    if re.search(r"(습니다|입니다)\.", text or "") and re.search(r"(이다|한다|된다|아니다)\.", text or ""):
        bad.append("해설에 '-습니다'체와 '-다'체가 섞여 있습니다.")
    return bad


def check_blank_answer_restated(answer: str, blank_sentence: str,
                                sentences: list[str], blank_phrase: str,
                                max_overlap: float = 0.6) -> list[str]:
    """빈칸의 답이 지문 '다른 자리'에 그대로 남아 있지 않은지 본다.

    빈칸으로 지운 어구와 같은 말이 지문 뒤에 또 나오면, 학생은 글을 이해하지 않고
    그 자리를 베껴 고른다(실제 출력물: 'they'll delete the content' 를 빈칸으로 냈는데
    같은 지문 뒤에 'they'd rather delete the content' 가 그대로 남아 있었다).
    """
    key = _content_words(blank_phrase)
    if not key:
        return []
    rest = [s for s in sentences if s.strip() and s.strip() != (blank_sentence or "").strip()]
    for s in rest:
        here = _content_words(s)
        if here and len(key & here) / len(key) >= max_overlap:
            return [f"빈칸 어구('{blank_phrase.strip()}')와 거의 같은 말이 지문 다른 문장에 "
                    f"그대로 남아 있습니다: '{s.strip()}' — 학생이 그 자리를 베껴 답을 "
                    "고를 수 있으니 다른 어구를 빈칸으로 잡으세요."]
    return []


def check_key_overlap(a_answer: str, b_answer: str, label_a: str, label_b: str,
                      max_overlap: float = 0.5) -> list[str]:
    """서로 다른 두 문항의 정답 핵심어가 겹치는지 본다.

    빈칸추론(F)과 요약문(E)은 둘 다 '글의 핵심을 한마디로'를 묻는다. 정답 낱말까지
    같으면 한 문항을 풀면 다른 문항이 저절로 풀린다(실제 출력물: 11번 정답
    'remove their posts' 와 15번 (A) 정답 'remove').
    """
    a, b = _content_words(a_answer), _content_words(b_answer)
    if not a or not b:
        return []
    shared = a & b
    if len(shared) / min(len(a), len(b)) >= max_overlap:
        return [f"{label_a}과 {label_b}의 정답 핵심어가 겹칩니다({', '.join(sorted(shared))}) — "
                "한 문항을 풀면 다른 문항이 저절로 풀립니다."]
    return []


# ---------------------------------------------------------------------------
# 지문에 들어갈 영어 문장이 '깨끗한 한 문장'인가
# ---------------------------------------------------------------------------
# 모델이 지시문 조각을 문장 끝에 흘리는 일이 있다(실제 출력물: '… ordinary
# listeners.output must' 가 지문에 그대로 박혔다). 지문에 들어가는 영어 문장은
# 문장부호로 끝나야 하고, 마침표 뒤에 낱말이 더 붙어 있으면 안 된다.
_TAIL_JUNK = re.compile(r"[.!?][\"'’”)\]]?\s*[A-Za-z]")


def check_clean_sentence(text: str, kind: str = "문장") -> list[str]:
    """지문에 끼워 넣을 영어 문장이 깨끗한지 본다(꼬리 오염·미완결 차단)."""
    s = (text or "").strip()
    if not s:
        return [f"{kind}이 비어 있습니다."]
    if not re.search(r"[.!?][\"'’”)\]]?$", s):
        return [f"{kind}이 문장부호로 끝나지 않습니다 — 지시문 조각이 섞였는지 "
                f"확인하세요: '{s[-40:]}'"]
    # 문장 안의 마침표 뒤에 곧바로 낱말이 붙은 자리(공백 없는 '…listeners.output')
    if re.search(r"[a-z][.!?][A-Za-z]", s):
        return [f"{kind} 안에 붙어 버린 낱말이 있습니다(마침표 뒤 공백 없음): "
                f"'{s[:80]}'"]
    return []


def check_tokens_rebuild(tokens: list[str], answer: str,
                         cues: list[str] | None = None) -> list[str]:
    """어순 배열의 <보기> 낱말이 정답 문장을 복원할 수 있는지 본다.

    이 유형은 일부러 동사를 원형으로 두고 cues 로 알려 주므로 낱말이 그대로 같지는
    않다. 그래서 두 가지만 본다:
      ① 낱말 개수·구성이 맞는가(어형 차이는 cues 에 있는 것만 허용).
      ② 구두점이 붙은 토큰은 정답 문장에 '그 모양 그대로' 있는가.
    ②가 실제 결함을 잡는다 — 원문에 없는 콤마가 붙은 'brain,' 토큰이 나왔다.
    """
    ans = (answer or "").split()
    toks = [str(t) for t in (tokens or []) if str(t).strip()]
    if not ans:
        return ["정답 문장이 비어 있습니다."]
    if not toks:
        return ["<보기> 낱말이 비어 있습니다."]

    def _bare(w: str) -> str:
        return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()

    # ② 구두점이 붙은 토큰은 정답에 그대로 있어야 한다
    ans_forms = {w.lower() for w in ans}
    stray = [t for t in toks if _bare(t) != t.lower() and t.lower() not in ans_forms]
    if stray:
        return [f"<보기> 낱말에 정답 문장에 없는 구두점이 붙어 있습니다: "
                f"{', '.join(stray[:5])} — 학생이 원문대로 배열할 수 없습니다."]

    # ① 낱말 구성(어형 차이는 cues 에 있는 것만)
    from collections import Counter
    cue = {_bare(c) for c in (cues or [])}
    extra = Counter(_bare(t) for t in toks) - Counter(_bare(w) for w in ans)
    missing = Counter(_bare(w) for w in ans) - Counter(_bare(t) for t in toks)
    unexplained = [w for w in extra.elements() if w not in cue]
    if unexplained or sum(extra.values()) != sum(missing.values()):
        parts = []
        if missing:
            parts.append("빠진 것: " + ", ".join(sorted(missing.elements())[:6]))
        if unexplained:
            parts.append("없던 것: " + ", ".join(sorted(unexplained)[:6]))
        if parts:
            return ["<보기> 낱말이 정답 문장과 맞지 않습니다 — " + " / ".join(parts)]
    return []
