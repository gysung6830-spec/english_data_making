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
                       spread: float = 2.2, noun_phrase: bool = False) -> list[str]:
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
    if noun_phrase:
        bad += _odd_clause(choices, kind)
    return bad


def _odd_clause(choices: list[str], kind: str) -> list[str]:
    """명사구로 통일해야 하는 선지(주제)에 하나만 '절'이 섞였는가.

    실제 결과물: 주제 선지 넷은 명사구인데 정답만 'situational forces, not personal
    flaws, explain why bystanders fail to help, as …' 처럼 삽입구가 둘 든 완전한
    절이었다. 학생이 뜻을 몰라도 모양으로 골라낸다.

    삽입구가 둘 이상(쉼표 2개 이상)인 선지가 '혼자'일 때만 잡는다. 쉼표 하나는
    명사구에도 자연스럽게 들어가므로(‘Tantrums, Explained’) 세지 않는다.
    """
    if len(choices) < 4 or any(re.search(r"[가-힣]", c) for c in choices):
        return []
    heavy = [i + 1 for i, c in enumerate(choices) if c.count(",") >= 2]
    if len(heavy) == 1:
        return [f"{heavy[0]}번 {kind}만 삽입구가 둘 이상인 절입니다 — 나머지는 명사구라 "
                "모양만 보고 답을 고를 수 있습니다. 선지의 갈래를 맞추세요."]
    return []


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
    "빼낸 문장", "빼낼 문장", "뺀 문장", "제거한 문장", "제거할 문장",
    "제시된 단어들을", "토큰들을",
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


# 이 접두어가 붙은 사유는 '다시 만들면 고쳐지는 것'이라, 검수 승격의 방아쇠가 된다
# (tiering._ESCALATE_PREFIX). 접두어가 없는 사유는 검토 메모로만 남는다.
ESCALATE = "자동검사: "


def check_explanation(text: str) -> list[str]:
    """해설 한 덩어리를 검사한다(내부 용어·출제 메모·문장 번호 지칭·문체 혼재).

    앞의 셋은 해설을 못 쓰게 만들고 다시 쓰면 고쳐지므로 승격 대상으로 표시한다.
    문체 혼재는 읽는 데 지장이 없어 메모로만 남긴다(값싼 모델을 계속 쓰기 위해).
    """
    bad: list[str] = []
    low = (text or "").lower()
    hit = [t for t in INTERNAL_TERMS if t.lower() in low]
    if hit:
        bad.append(ESCALATE + "해설에 내부 용어가 그대로 있습니다: " + ", ".join(hit))
    notes = [n for n in _AUTHOR_NOTES if n in (text or "")]
    if notes:
        bad.append(ESCALATE + "해설에 출제 과정 메모가 있습니다: " + ", ".join(notes))
    if _SENT_REF.search(text or ""):
        bad.append(ESCALATE + "해설이 '(3)에서'처럼 문장 번호로 지칭합니다 — 학생용 "
                   "지문에는 번호가 없어 대조할 수 없습니다.")
    if re.search(r"(습니다|입니다)\.", text or "") and re.search(r"(이다|한다|된다|아니다)\.", text or ""):
        bad.append("해설에 '-습니다'체와 '-다'체가 섞여 있습니다.")
    # 오답을 설계할 때 쓰는 내부 분류 이름('축')이 그대로 문장이 되어 나온다
    # (실제 출력물 17번: '① 방향 반전 축이다.'). 읽는 사람에게는 뜻이 없는 말이다.
    if re.search(r"(?:^|[\s'\"(])축(이다|입니다|의 오답|을 쓴|에 해당)", text or ""):
        bad.append("해설이 오답 분류 이름을 그대로 문장으로 씁니다('… 축이다') — "
                   "'방향 반전 — 이유' 처럼 쓰세요.")
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
    if re.search(r"[a-z]{3}[.!?]+[A-Za-z]", s):     # 약어(U.S.·e.g.)는 거르고
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


# ---------------------------------------------------------------------------
# 낱말 하나를 갈아 끼웠을 때 '문장이 깨지는' 자리
# ---------------------------------------------------------------------------
# 어휘 문항은 낱말 하나만 바꾼다. 그런데 그 낱말이 뒤따르는 불변화사·전치사와 한
# 덩어리이거나(구동사), 목적어를 요구하는 타동사이면, 바꾼 순간 문장이 영어가 아니게
# 된다. 그러면 학생은 글을 읽지 않고 '덜컹거리는 자리'만 보고 답을 고른다.
# 실제 출력물에서 한 회차에 세 번 나왔다:
#   'help them calm down'   → 'help them upset down'      (구동사의 down 이 남았다)
#   'the ability to listen to what' → '… to hear to what' (전치사 to 가 남았다)
#   'would usually respond,' → 'would usually ignore,'    (목적어 없는 타동사)
#
# 판정은 '불변화사를 데려가는 동사 목록'으로 한다. 원래 낱말이 그 목록에 있고(그
# 불변화사가 원래 낱말의 것이었다는 증거) 바꾼 낱말이 없으면 깨진 것이다. 목록에
# 없는 낱말끼리의 교체는 건드리지 않는다 — 오탐이 한 번 나면 멀쩡한 문항이 죽는다.
_PARTICLE_TAKERS: dict[str, set[str]] = {
    "down": {"calm", "settle", "quiet", "quieten", "cool", "slow", "tone", "wind",
             "simmer", "break", "close", "shut", "sit", "lie", "put", "turn", "write",
             "cut", "back", "run", "let", "hand", "pass", "narrow", "tie", "water",
             "step", "tear", "knock", "bring", "come", "go", "get", "fall", "lay",
             "hold", "track", "hunt", "strike", "die", "slam", "scale"},
    "up": {"give", "bring", "pick", "take", "set", "make", "look", "grow", "end",
           "come", "show", "put", "open", "speed", "build", "sum", "wake", "stand",
           "catch", "clean", "cover", "hang", "keep", "line", "live", "mix", "move",
           "pull", "save", "sign", "split", "turn", "add", "back", "blow", "break",
           "call", "cheer", "dress", "eat", "fill", "hold", "own", "pile", "sober"},
    "off": {"cool", "take", "put", "set", "cut", "turn", "call", "show", "pay",
            "write", "break", "close", "shut", "hold", "lay", "let", "pull", "see",
            "send", "shake", "wear", "back", "drop", "kick", "level", "ward"},
    "out": {"carry", "point", "figure", "find", "work", "turn", "bring", "hand",
            "leave", "rule", "spell", "stand", "stretch", "wear", "wipe", "sort",
            "set", "give", "run", "help", "burn", "check", "cross", "die", "drop",
            "fill", "hold", "iron", "lay", "pass", "pick", "sell", "single", "watch"},
    "to": {"listen", "respond", "react", "reply", "refer", "lead", "contribute",
           "adapt", "apply", "belong", "relate", "attend", "object", "adhere",
           "resort", "amount", "testify", "appeal", "subscribe", "cling", "conform",
           "correspond", "defer", "revert", "yield", "speak", "talk", "turn", "point",
           "see", "stick", "agree", "admit", "confess", "commit", "add", "return",
           "switch", "expose", "subject", "owe", "compare", "link", "connect",
           "attribute", "devote", "dedicate", "introduce", "submit", "give", "look",
           "come", "go", "get", "amount", "cater", "object", "consent", "surrender"},
    "on": {"depend", "rely", "focus", "insist", "concentrate", "dwell", "comment",
           "reflect", "count", "impose", "base", "act", "carry", "go", "live", "take",
           "put", "turn", "try", "keep", "hold", "move", "pass", "work", "call",
           "draw", "touch", "bank", "border", "capitalize", "elaborate", "hinge",
           "prey", "rest", "seize", "settle", "spy", "thrive"},
    "with": {"deal", "cope", "interfere", "agree", "comply", "associate", "compete",
             "identify", "sympathize", "begin", "part", "meet", "live", "go", "come",
             "catch", "put", "bear", "clash", "collide", "correlate", "credit",
             "empathize", "engage", "grapple", "provide", "reckon", "side", "trust"},
    "from": {"stem", "arise", "benefit", "suffer", "result", "differ", "refrain",
             "derive", "emerge", "escape", "recover", "separate", "prevent", "stop",
             "keep", "protect", "hide", "borrow", "learn", "come", "hear", "range",
             "abstain", "deter", "discourage", "distinguish", "exempt", "profit",
             "recoil", "resign", "retire", "shrink", "spring", "stray", "withdraw"},
    "of": {"consist", "approve", "dispose", "conceive", "think", "dream", "complain",
           "boast", "accuse", "remind", "rid", "deprive", "convince", "inform",
           "hear", "know", "speak", "die", "smell", "taste", "despair", "beware",
           "admit", "acquit", "assure", "cure", "partake", "repent", "tire"},
    "for": {"wait", "look", "search", "hope", "long", "ask", "care", "apply",
            "account", "allow", "compensate", "substitute", "pay", "stand", "call",
            "make", "head", "opt", "yearn", "strive", "provide", "prepare", "aim",
            "arrange", "settle", "fall", "go", "run", "answer", "atone", "blame",
            "campaign", "hunger", "mistake", "qualify", "root", "vouch", "wish"},
    "about": {"think", "care", "talk", "worry", "complain", "wonder", "know", "hear",
              "learn", "argue", "ask", "forget", "dream", "speak", "write", "read",
              "bring", "come", "go", "set", "boast", "fret", "fuss", "quibble"},
    "into": {"turn", "break", "run", "look", "divide", "translate", "transform",
             "enter", "dig", "delve", "tap", "bump", "crash", "fall", "get", "go",
             "come", "put", "talk", "force", "burst", "check", "convert", "grow",
             "merge", "plunge", "sink", "split", "venture"},
    "at": {"look", "stare", "glance", "aim", "arrive", "laugh", "point", "shout",
           "guess", "excel", "hint", "marvel", "work", "get", "come", "jump", "gaze",
           "grasp", "hammer", "peer", "scoff", "smile", "wonder"},
    "in": {"result", "believe", "participate", "engage", "specialize", "succeed",
           "invest", "indulge", "persist", "interfere", "join", "take", "give",
           "step", "fill", "bring", "come", "live", "stay", "hand", "break", "check",
           "confide", "delight", "dwell", "excel", "revel", "share", "trade"},
}

# 목적어 없이는 문장이 성립하지 않는 타동사(원형·3인칭 단수형만 본다 — 분사형까지
# 넣으면 'the risks involved,' 같은 멀쩡한 자리를 잡아 버린다).
_NEED_OBJECT = {
    "ignore", "discuss", "mention", "emphasize", "approach", "enter", "resemble",
    "lack", "deny", "accompany", "obtain", "resist", "achieve", "avoid", "regard",
    "involve", "include", "contain", "require", "seek", "affect", "exceed",
    "surpass", "await", "abandon", "acquire", "address", "attain", "consume",
    "convey", "endure", "generate", "impose", "neglect", "possess", "reject",
    "resemble", "restrict", "reveal", "seize", "suppress", "undermine", "withhold",
}
# 뒤에 아무것도 없다고 볼 문장부호(여기서 절이 끝난다)
_CLAUSE_END = re.compile(r"^\s*(?:[,;:.!?]|$)")


# 앞에 이것이 오면 밑줄 낱말은 동사가 아니라 명사다(the intensity of …).
_DET = {"the", "a", "an", "this", "that", "these", "those", "their", "its", "his",
        "her", "our", "your", "my", "no", "any", "some", "each", "every", "one"}
# 명사 뒤에는 거의 붙지 않는 '부사 불변화사'만 조판 뒤 검사에 쓴다.
_ADVERBIAL = {k: _PARTICLE_TAKERS[k] for k in ("down", "up", "out", "off")}


def _swap_bases(w: str) -> set[str]:
    """어형을 벗겨 사전에서 찾을 후보들(단수형 -s, 과거 -ed, -ing)."""
    w = re.sub(r"^[^\w]+|[^\w]+$", "", (w or "").lower())
    out = {w}
    for suf, cut in (("ies", 3), ("es", 2), ("s", 1), ("ed", 2), ("ing", 3)):
        if len(w) > cut + 2 and w.endswith(suf):
            stem = w[:-cut]
            out.add(stem)
            out.add(stem + "e")           # hoped → hope · using → use
            if len(stem) > 2 and stem[-1] == stem[-2]:
                out.add(stem[:-1])        # stopped → stop
    return {x for x in out if x}


def check_swap_breaks(sentence: str, word: str, shown: str) -> list[str]:
    """원본 낱말 word 를 shown 으로 갈아 끼웠을 때 문장이 깨지는지 본다.

    sentence 는 '갈아 끼우기 전' 원문 문장이다(뒤따르는 낱말은 교체로 바뀌지 않으므로
    원문에서 그대로 읽으면 된다).
    """
    w, s = (word or "").strip(), (shown or "").strip()
    if not w or not s or w.lower() == s.lower():
        return []
    text = sentence or ""
    m = re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", text, re.IGNORECASE)
    if not m:
        return []
    after = text[m.end():]
    bad: list[str] = []

    # ① 구동사·전치사가 남는가
    nxt = re.match(r"\s*([A-Za-z]+)", after)
    if nxt:
        part = nxt.group(1).lower()
        takers = _PARTICLE_TAKERS.get(part)
        if takers and (_swap_bases(w) & takers) and not (_swap_bases(s) & takers):
            bad.append(f"'{w} {part}'는 한 덩어리로 쓰이는 표현인데 '{s} {part}'는 "
                       f"영어가 되지 않습니다 — 뒤의 '{part}'까지 함께 손보거나 다른 "
                       "낱말을 고르세요.")

    # ② 목적어가 필요한 타동사인데 목적어가 없는가
    if (_swap_bases(s) & _NEED_OBJECT) and _CLAUSE_END.match(after):
        bad.append(f"'{s}'는 목적어가 필요한 타동사인데 뒤에 목적어가 없습니다 "
                   f"('… {s}{after[:12].rstrip()}') — 문장이 성립하지 않습니다.")
    return bad


def check_marks_in_passage(body: str, marks: list[tuple[str, str]]) -> list[str]:
    """조판이 끝난 지문에서 '밑줄 낱말 자체가 문장을 깨뜨리는' 자리를 찾는다.

    원본 낱말을 모르므로 확실한 것 하나만 본다 — 목적어가 필요한 타동사인데 바로
    뒤에서 절이 끝나는 경우('… would usually ignore, just as we hope'). 구동사가
    깨진 경우는 원본 낱말을 알아야 판정할 수 있어 생성 시점(check_swap_breaks)에서
    막는다.
    """
    bad: list[str] = []
    text = body or ""
    for _no, word in marks or []:
        w = (word or "").strip()
        if not w:
            continue
        m = re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", text)
        if not m:
            continue
        after = text[m.end():]
        # ① 목적어가 필요한 타동사인데 바로 뒤에서 절이 끝난다
        if (_swap_bases(w) & _NEED_OBJECT) and _CLAUSE_END.match(after):
            bad.append(f"밑줄 '{w}'는 목적어가 필요한 타동사인데 뒤에 목적어가 "
                       "없습니다 — 문장이 성립하지 않습니다.")
        # ② 부사 불변화사(down·up·out·off)가 남았다. 전치사(to·of·in …)는 명사 뒤에도
        #    흔히 붙어 오탐이 나므로 여기서는 보지 않는다(생성 시점에서 막는다).
        nxt = re.match(r"\s*([A-Za-z]+)", after)
        before = text[:m.start()].split()[-1:] if text[:m.start()].split() else []
        if nxt and (not before or before[0].lower() not in _DET):
            part = nxt.group(1).lower()
            takers = _ADVERBIAL.get(part)
            if takers is not None and not (_swap_bases(w) & takers):
                bad.append(f"밑줄 '{w} {part}'는 영어 표현이 되지 않습니다 — 원래 "
                           f"구동사에서 낱말만 갈아 끼워 '{part}'가 남았는지 "
                           "확인하세요.")
    return bad


def check_marks_swaps(sentences: list[str], marks) -> list[str]:
    """밑줄 목록 전체에 check_swap_breaks 를 건다.

    marks 는 sent_no(1-based)·word·shown 을 가진 객체들(WordMark).
    """
    bad: list[str] = []
    for m in marks or []:
        i = int(getattr(m, "sent_no", 0)) - 1
        if 0 <= i < len(sentences):
            bad += check_swap_breaks(sentences[i], getattr(m, "word", ""),
                                     getattr(m, "shown", ""))
    return bad


def check_tokens_shuffled(tokens: list[str], answer: str) -> list[str]:
    """어순 배열 <보기> 가 정답 순서 그대로 실려 있지 않은지 본다.

    그대로면 학생은 배열이 아니라 베껴 쓰기를 한다(실제 출력물 16번).
    """
    toks = [str(t).strip() for t in (tokens or []) if str(t).strip()]
    words = (answer or "").split()
    if len(toks) < 4 or len(toks) != len(words):
        return []

    def _b(w: str) -> str:
        return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()

    if [_b(t) for t in toks] == [_b(w) for w in words]:
        return ["<보기> 낱말이 정답 문장 순서 그대로입니다 — 섞이지 않아 "
                "학생이 베껴 쓰기만 하면 됩니다."]
    return []


def check_linker_pairs(pairs, answer_no: int) -> list[str]:
    """연결어 선지가 '한 자리만 보고' 풀리지 않는지 본다.

    (A)-(B) 짝 다섯 중 정답의 (A) 낱말이 그 짝에만 있으면, 학생은 (B) 는 보지도 않고
    (A) 하나만 판정해 답을 고른다. 반대도 마찬가지다. 그러면 두 자리를 낸 뜻이 없다.
    수능이 이 유형을 낼 때 늘 지키는 조건이라, 여기서도 강제한다.
    """
    got = [((p.a if hasattr(p, "a") else p[0]).strip().lower(),
            (p.b if hasattr(p, "b") else p[1]).strip().lower()) for p in (pairs or [])]
    if not (1 <= answer_no <= len(got)):
        return ["정답 번호가 선지 범위를 벗어났습니다."]
    bad: list[str] = []
    a_ans, b_ans = got[answer_no - 1]
    n_a = sum(1 for a, _ in got if a == a_ans)
    n_b = sum(1 for _, b in got if b == b_ans)
    if n_a < 2:
        bad.append(f"(A) 정답 '{a_ans}' 가 한 선지에만 있습니다 — (A)만 보고 답이 "
                   "나옵니다. 같은 (A) 를 쓰는 오답을 하나 더 두세요.")
    if n_b < 2:
        bad.append(f"(B) 정답 '{b_ans}' 가 한 선지에만 있습니다 — (B)만 보고 답이 "
                   "나옵니다. 같은 (B) 를 쓰는 오답을 하나 더 두세요.")
    if len(set(a for a, _ in got)) > 4:
        bad.append("(A) 자리에 서로 다른 낱말이 다섯 개입니다 — 겹치는 것이 있어야 "
                   "두 자리를 모두 따지게 됩니다.")
    return bad


# 내용 O/X 의 오답 여덟 축 — 이름을 한곳에 둔다(프롬프트·검사·조판이 같은 말을 쓴다).
OX_AXES: tuple[str, ...] = (
    "주체·대상 바꿔치기",
    "인과 날조",
    "인과 역전",
    "조건 삭제",
    "시점 뒤집기",
    "부정 뒤집기",
    "논지·화자 뒤집기",
    "미언급인데 그럴듯",
)
OX_TRUE_AXIS = "일치"        # O 진술의 axis 자리


def check_ox_axis_coverage(axes) -> list[str]:
    """X 여덟 개가 여덟 축을 '하나씩' 썼는지 본다.

    이 검사는 걸려도 다시 만들지 않는다 — 검토 메모로만 남긴다. 내용 O/X 는 한 번에
    진술 스무 개를 만드는 가장 비싼 호출이라, 축이 하나 겹쳤다고 통째로 다시 부르면
    문항 하나 값이 두 배가 된다. 그만한 결함이 아니다(여덟 축 중 일곱만 써도 문항은
    성립한다). 대신 프롬프트에서 '하나씩'을 못 박아 처음부터 맞게 나오게 한다.
    """
    used = [a for a in (axes or []) if (a or "").strip()
            and (a or "").strip() != OX_TRUE_AXIS]
    if not used:
        return []
    dup = sorted({a for a in used if used.count(a) > 1})
    miss = [a for a in OX_AXES if a not in used]
    bad = []
    if dup:
        bad.append(f"오답 축이 겹칩니다: {', '.join(dup)}. 여덟 축을 하나씩 쓰면 "
                   "학생이 같은 눈으로 여럿을 한꺼번에 걸러 내지 못합니다.")
    if miss and len(used) >= len(OX_AXES):
        bad.append(f"쓰이지 않은 오답 축이 있습니다: {', '.join(miss)}.")
    return bad


# 내용 O/X 에서 쓰지 않기로 한 두 함정 — 해설에 그 이름이 적혀 있으면 걸러 낸다.
# 둘 다 '읽고 이해했는가'가 아니라 눈썰미를 재는 방식이라 실력을 가르지 못한다.
_BANNED_OX_AXES = (
    "부분 일치", "한 요소만", "한 요소 왜곡",
    "정도·빈도 과장", "정도 과장", "빈도 과장", "정도·범위 과장",
)


def check_ox_axes(reasons) -> list[str]:
    """O/X 근거에 '쓰지 않기로 한 함정'의 이름이 적혀 있는지 본다."""
    hit = sorted({a for a in _BANNED_OX_AXES
                  for r in (reasons or []) if a in (r or "")})
    if not hit:
        return []
    return [f"쓰지 않기로 한 함정을 썼습니다: {', '.join(hit)}. 숫자·기간 한 군데만 "
            "바꾸거나 '늘·오직·반드시'로 키우는 방식은 눈썰미를 잴 뿐입니다 — "
            "읽고 따져 봐야 아는 것으로 다시 만드세요."]
