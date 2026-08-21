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
    return bad


def check_order_shuffle(display: list[int]) -> list[str]:
    """순서 배열의 (A)(B)(C)가 실제로 섞였는가.

    display 가 [1,2,3]이면 (A)(B)(C)가 원문 순서 그대로라 정답이 항상 'A-B-C'가 된다.
    """
    if list(display) == [1, 2, 3]:
        return ["(A)(B)(C)가 원문 순서 그대로입니다 — 섞이지 않으면 문제가 되지 않습니다."]
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
