#!/usr/bin/env python3
"""극단 지문 시험대 — 지문의 '모양'이 극단일 때 조판이 무너지지 않는지 본다.

지금까지 실제 결과물에서 나온 결함은 **전부 지문의 극단에서** 나왔다.

  · 5문장짜리 짧은 지문   → 무관한 문장이 통째로 빠지고, 삽입이 3지선다가 됐다
  · 이름 가운데 이니셜     → 'Paul R.' 에서 문장이 갈려 'Paul R. ① Ehrlich' 가 됐다
  · 인용문 안의 마침표     → 따옴표가 열린 채 끝나는 반쪽 문장이 지문에 실렸다
  · 문장 첫 낱말을 치환    → 'numerous studies …' 처럼 소문자로 시작했다

여러 지문으로 스무 번을 돌려도 이 조합이 안 나오면 안 잡힌다. 그래서 무작위로
많이 돌리는 대신 **극단을 일부러 골라** 고정 시험대로 둔다. API 를 쓰지 않고
구조만 보므로 커밋할 때마다 몇 초에 돌릴 수 있다.

여기서 보는 것은 '문제의 질'이 아니라 '조판이 성립하는가'다. 질(복수정답·오답
매력도·해설의 정확성)은 사람과 모델이 읽어야 한다.

단독 실행:  python tests/test_stress.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from exam import audit, build as B, build2 as B2  # noqa: E402
from exam.analyzer import split_sentences  # noqa: E402
from exam.types import (  # noqa: E402
    CONTENT,
    GRAMMAR,
    INSERT,
    IRRELEVANT,
    ORDER,
    TOPIC,
    VOCAB,
    Passage,
)

# ---------------------------------------------------------------------------
# 극단 지문 — 각각 '무엇이 극단인지'를 이름에 적어 둔다
# ---------------------------------------------------------------------------
STRESS: dict[str, str] = {}

STRESS["짧은 지문(5문장)"] = (
    "A group of researchers at the University of Twente in the Netherlands "
    "recently 3D-printed two identically shaped mugs with different textures to "
    "test the effects on taste. One was covered in a rounded bobbly texture, and "
    "the other had a blocky, angular texture. In a supermarket taste test, the "
    "researchers offered shoppers a sample of coffee from one of the mugs and "
    "asked them to evaluate the taste. Drinks in the round bobbly mug tasted "
    "sweeter, while in the angular mug the same drinks tasted more bitter. If you "
    "are trying to cut down on your sugar, avoid drinking from a rough mug."
)

STRESS["이니셜·약어"] = (
    "The American biologist Paul R. Ehrlich has been predicting collapse for "
    "decades. Dr. J. M. Keynes once warned that the long run is a misleading "
    "guide to current affairs. Many forecasts made in the U.S. during the 1970s "
    "turned out to be badly wrong. Some scholars, e.g. Simon and Boserup, argued "
    "the opposite case. Mr. Ehrlich never withdrew his claim. Instead he moved "
    "the date again. A pessimistic stance is a safe one."
)

STRESS["인용문 안 마침표"] = (
    "In 1970 he said that 'sometime in the next 15 years, the end will come. And "
    "by \"the end\" I mean an utter breakdown of the capacity of the planet to "
    "support humanity.' Of course, that was terribly wrong. He had another go: he "
    "said that 'England will not exist in the year 2000.' Wrong again. Critics "
    "replied that 'the record speaks for itself. No apology has ever been "
    "offered.' The pattern has never changed. Readers still trust the warning."
)

STRESS["숫자·기호"] = (
    "Drinks in the round mug tasted on average around 18 percent sweeter. In the "
    "angular-textured mug the same drinks tasted up to 27 percent more bitter. "
    "The 1968 book sold 3.5 million copies within a decade. Between 1970 and "
    "1985, roughly 40% of the forecasts were revised. A single gram of DNA could "
    "hold as much data as 10,000 hard drives. The team used a 3D printer costing "
    "$2,400. These figures are widely cited today."
)

STRESS["첫 낱말이 내용어"] = (
    "Many studies show that musical training shifts the brain's processing of "
    "music. Several guesses exist about why this happens. Trained musicians hear "
    "music more like language than ordinary listeners do. Recently, researchers "
    "confirmed the pattern in children as well. Numerous scans support the same "
    "conclusion. Emotion still plays a part in every case. Language areas "
    "nonetheless dominate the response."
)

STRESS["긴 지문(11문장)"] = (
    "Every living cell carries a molecule called DNA. It works as nature's own "
    "hard drive. What makes it remarkable is not only that it stores information. "
    "It also packs an enormous amount into a vanishingly small space. A single "
    "gram could hold as much data as millions of ordinary drives. It is also "
    "astonishingly durable. It survives in bone and ice for tens of thousands of "
    "years. Inspired by such efficiency, researchers began to encode digital "
    "files into synthetic DNA. The technique is still slow and expensive. It "
    "allows information to be preserved for thousands of years. One day our "
    "libraries may be stored safely inside molecules."
)


# ---------------------------------------------------------------------------
# 문장 나누기 — 조판의 모든 것이 여기서 시작한다
# ---------------------------------------------------------------------------
def _quotes_balanced(s: str) -> bool:
    if s.count('"') % 2:
        return False
    from exam.analyzer import _quote_open
    return not _quote_open(s)


def check_sentences(name: str, body: str) -> list[str]:
    """문장 하나하나가 '온전한 문장'인가."""
    bad = []
    sents = split_sentences(body)
    if len(sents) < 4:
        bad.append(f"문장이 {len(sents)}개로 나뉘었습니다 — 너무 적습니다.")
    for i, s in enumerate(sents, 1):
        if not s[:1].isupper() and not s[:1] in "'\"(":
            bad.append(f"{i}번째 문장이 대문자로 시작하지 않습니다: '{s[:40]}…'")
        if not re.search(r"[.!?][\"'’”)\]]?$", s):
            bad.append(f"{i}번째 문장이 문장부호로 끝나지 않습니다: '…{s[-40:]}'")
        if not _quotes_balanced(s):
            bad.append(f"{i}번째 문장의 따옴표 짝이 맞지 않습니다: '{s[:60]}…'")
    # 원문 낱말이 하나도 새거나 사라지지 않아야 한다
    if " ".join(sents).split() != " ".join(body.split()).split():
        bad.append("문장을 붙이면 원문과 달라집니다(낱말이 새거나 사라졌습니다).")
    return bad


# ---------------------------------------------------------------------------
# 지문 하나로 조판 가능한 문항을 실제로 만들어 본다(API 없이)
# ---------------------------------------------------------------------------
_STOP = {"the", "a", "an", "and", "but", "of", "in", "on", "to", "for", "with",
         "that", "this", "it", "is", "are", "was", "were", "as", "at", "by",
         "from", "or", "he", "she", "they", "you", "not", "has", "have", "had"}


def _content_word(sentence: str, taken: set[str]) -> str | None:
    """그 문장에서 밑줄 칠 만한 낱말 하나(한 번만 나오고, 기능어가 아닌 것)."""
    for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", sentence):
        low = w.lower()
        if low in _STOP or low in taken:
            continue
        if len(re.findall(r"(?<!\w)" + re.escape(w) + r"(?!\w)", sentence)) == 1:
            return w
    return None


def build_passage(name: str, body: str) -> tuple[Passage, list[str]]:
    """극단 지문으로 조판 가능한 유형을 실제로 만들어 Passage 를 채운다."""
    sents = split_sentences(body)
    n = len(sents)
    p = Passage(title=name)
    notes: list[str] = []

    # 주제·제목·내용일치 — 지문을 손대지 않는 유형
    five = [f"선지 {i} 내용" for i in range(1, 6)]
    wrong = {i: "근거" for i in (1, 2, 4, 5)}
    p.set_qa(TOPIC, *B.make_topic(sents, five, 3, "근거", wrong))
    p.set_qa(CONTENT, *B.make_content(sents, five, 3, "근거", wrong))

    # 어휘 — 문장마다 낱말 하나씩. 첫 낱말도 일부러 한 번 고른다(대문자 유지 확인).
    taken: set[str] = set()
    marks = []
    first_word = sents[0].split()[0].strip(".,")
    marks.append((0, first_word, first_word.lower()))     # 첫 낱말 → 소문자로 치환 시도
    taken.add(first_word.lower())
    for i in range(1, n):
        w = _content_word(sents[i], taken)
        if w and len(marks) < 5:
            marks.append((i, w, w))
            taken.add(w.lower())
    if len(marks) == 5:
        p.set_qa(VOCAB, *B.make_vocab(sents, marks, 3, "근거"))
    else:
        notes.append(f"밑줄 칠 낱말을 5개 고르지 못했습니다({len(marks)}개).")

    # 어법 — 밑줄 3개
    gmarks = marks[:3]
    if len(gmarks) == 3:
        p.set_qa(GRAMMAR, *B.make_grammar(
            sents, gmarks, [2], {2: "수 일치"}))

    # 순서 배열 — 주어진 글 1문장 + 나머지를 3~4덩어리로
    k = 4 if n >= 5 else 3
    rest = n - 1
    sizes = [rest // k] * k
    for i in range(rest - sum(sizes)):
        sizes[i] += 1
    if all(s > 0 for s in sizes):
        p.set_qa(ORDER, *B.make_order(sents, 1, sizes, [2, 1, 4, 3][:k], "근거"))
    else:
        notes.append(f"순서 배열 덩어리를 나눌 문장이 모자랍니다(문장 {n}개).")

    # 문장 삽입 — 자리가 모자라면 사유가 남아야 한다
    ins_flags: list[str] = []
    p.set_qa(INSERT, *B.make_insert(sents, 2, "근거", flags=ins_flags))
    p.flag(INSERT, ins_flags)

    # 무관한 문장 — 자리 수가 지문 길이에 맞춰 줄어야 한다
    kk = B.irrelevant_marks(n)
    if kk >= B.MIN_IRRELEVANT_MARKS:
        p.set_qa(IRRELEVANT, *B.make_irrelevant(
            sents, 2, 2, "This unrelated sentence mentions costs and profits.",
            "근거", {i: "이어짐" for i in range(1, kk + 1) if i != 2}))
    else:
        notes.append(f"무관한 문장을 낼 자리가 모자랍니다(문장 {n}개 → 자리 {kk}개).")

    # 어순 배열 — 지문 문장 하나를 낱개 단어로
    target = sents[1]
    toks = target.split()
    p.set_qa("D", *B2.make_D(sents, toks, [], target, "근거"))
    return p, notes


# 시험대가 스스로 만들어 내는 잡음 — 여기서 보려는 것이 아니다.
#   · 유형을 8종만 만든다(나머지는 LLM 없이 못 만든다) → '유형이 빠졌습니다'
#   · 선지·해설을 가짜로 채운다 → 선지 개수·길이·정답 쏠림
_NOISE = ("유형이 빠졌습니다", "정답이", "선지", "오답 선지 근거")


# 짧은 지문에서 삽입 자리가 모자란 것은 '결함'이 아니라 '알림'이다 — 지문이 짧아서
# 생기는 일이고, 코드가 제대로 알아차렸다는 뜻이다. 세지 말고 보여만 준다.
_NOTICE = ("자리가 부족",)


def _harness_noise(msg: str) -> bool:
    if any(k in msg for k in _NOTICE):
        return False
    return any(k in msg for k in _NOISE)


def _is_notice(msg: str) -> bool:
    return any(k in msg for k in _NOTICE)


# ---------------------------------------------------------------------------
# 시험
# ---------------------------------------------------------------------------
def run(verbose: bool = True) -> int:
    total_bad = 0
    for name, body in STRESS.items():
        problems: list[str] = []
        problems += check_sentences(name, body)
        try:
            p, notes = build_passage(name, body)
        except Exception as e:                    # noqa: BLE001 — 조판 실패도 결함이다
            problems.append(f"조판 실패: {type(e).__name__}: {e}")
            p, notes = None, []
        if p is not None:
            rows, whole = audit.check_passage(p)
            for it in rows:
                problems += [f"{it['label']}: {m}" for m in it["bad"]
                             if not _harness_noise(m)]
            problems += [m for m in whole if not _harness_noise(m)]

        notices = [m for m in problems if _is_notice(m)]
        problems = [m for m in problems if not _is_notice(m)]
        n = len(split_sentences(body))
        mark = "✗" if problems else "✓"
        if verbose:
            print(f"{mark} {name}  (문장 {n}개)")
            for m in notes + notices:
                print(f"      (알림) {m}")
            for m in problems:
                print(f"      · {m}")
        total_bad += len(problems)
    if verbose:
        print(f"\n지문 {len(STRESS)}개 · 지적 {total_bad}건")
    return total_bad


def test_stress_passages() -> None:
    """극단 지문에서도 조판이 성립해야 한다."""
    bad = run(verbose=False)
    assert bad == 0, f"극단 지문에서 {bad}건이 걸렸습니다 — python tests/test_stress.py 로 확인하세요."

    # 짧은 지문에서도 무관한 문장을 낸다(①~⑤). 삽입은 자리가 모자라면 알린다.
    short = split_sentences(STRESS["짧은 지문(5문장)"])
    assert B.irrelevant_marks(len(short)) == 5, len(short)
    p, _ = build_passage("짧은", STRESS["짧은 지문(5문장)"])
    assert any("선지가" in f for f in p.flags.get(INSERT, [])), p.flags

    # 이니셜이 문장을 가르지 않는다
    sents = split_sentences(STRESS["이니셜·약어"])
    joined = " ".join(sents)
    for name in ("Paul R. Ehrlich", "Dr. J. M. Keynes", "the U.S. during",
                 "e.g. Simon", "Mr. Ehrlich"):
        assert any(name in s for s in sents), f"'{name}' 가 문장 경계로 갈렸습니다: {sents}"
    assert joined.count("Paul R. Ehrlich") == 1
    print("✓ 극단 지문 시험대(짧은 지문·이니셜·인용문·숫자·첫낱말·긴 지문) 통과")


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
