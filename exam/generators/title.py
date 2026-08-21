"""제목 생성기 (수능 24번) — 영어 선지. 지문은 원본 그대로.

주제(23번)와 짝을 이루는 유형이다. 주제가 '무엇을 다루는 글인가'를 명사구로 묻는다면,
제목은 거기에 '함축·비유·대구'를 더해 글 전체를 한 줄로 압축하게 한다. 그래서 같은
지문에서 나와도 주제 문제와 답이 겹치지 않는다.
"""
from __future__ import annotations

import re

from .. import answer_spread, build as B
from .. import review
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, TitleOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '제목' 문제를 만드세요. 지문은 원본 그대로 쓰이며,
당신은 영어 선지 5개만 만듭니다. 주제가 아니라 '제목'입니다.

[제목과 주제의 차이] 반드시 지키세요.
- 주제는 글의 내용을 '설명'하지만, 제목은 글 전체를 '압축해 내건 간판'입니다.
- 제목은 짧고(대체로 4~9 단어), 함축적이며, 비유·대구·콜론(:)·의문형 같은 장치를 씁니다.
  예) "Small Choices, Large Consequences" / "When Less Turns Out to Be More" /
      "Monoculture: The Hidden Cost of Uniformity"
- 완전한 서술문(주어+동사로 끝나는 평서문)은 제목답지 않습니다. 명사구·대구·의문형으로.

선지(choices) 5개
- 정답 1개: 글 전체(도입~결론)를 포괄하고, 필자의 초점(역접 뒤 주장·반복어구)을 담습니다.
  지문 단어를 그대로 베끼지 말고 다른 말로 재진술하세요.
- 오답 4개는 아래 축에서 골라 설계하고, '매력적 오답' 1개를 반드시 넣습니다.
  1) 범위 비틀기 — 글보다 너무 넓거나(대주제로 확대), 너무 좁게(예시 하나만 제목화).
  2) 방향 반전 — 필자 주장과 반대로 내걺.
  3) 표면 어휘 함정 — 지문의 눈에 띄는 단어를 그대로 써서 익숙해 보이나 논점이 아님.
  4) 근거 없음 — 그럴듯하나 글에 근거가 없음.
  5) 초점 이동 — 소재는 맞지만 필자의 논점이 아닌 곁가지를 제목으로.
- '매력적 오답' 1개는 정답과 비슷하되 '한 끗(범위 또는 방향)'만 어긋나게 합니다.

- answer_no: 정답 선지 번호(1~5).
- reason: 정답 근거(한국어) — 글의 어느 부분이 그 제목을 뒷받침하는지.
- wrong_reasons: 오답 4개 각각 '어느 축인지 + 왜 제목이 될 수 없는지'(한국어).

[확실성] 정답은 글 전체를 정확히 포괄해야 하고(과대·과소 금지), 오답 4개는 각각 위 축으로
'확실히' 어긋나 반박 가능해야 합니다. 정답은 오직 하나입니다.

[갈래] 먼저 아래 셋 중 '하나'를 골라, 5개 선지를 **모두 그 갈래로** 만드세요.
  (가) 비유·대구형 — 두 요소를 맞세우거나 빗대어 압축합니다.
       예) "Small Choices, Large Consequences" / "When Less Turns Out to Be More"
  (나) 의문형 — 다섯 개 모두 물음표로 끝납니다.
       예) "Why Do Machines Forget?" / "Can a Molecule Outlast a Factory?"
  (다) 콜론형 — "주제어: 압축된 논평" 꼴로 통일합니다.
       예) "Monoculture: The Hidden Cost of Uniformity"
평범한 설명형 명사구("The Importance of Sleep" 같은 밋밋한 요약)는 쓰지 마세요. 제목은 글을
'설명'하는 것이 아니라 '내걸어 압축'하는 것입니다.

[형식] 고른 갈래 안에서 아래 넷을 5개 선지 '모두'에 똑같이 지켜야 합니다. 하나만 모양이
달라도 학생이 내용을 읽지 않고 그 하나를 고르게 되어 문제가 무너집니다.
  (1) 마침표(.)로 끝내지 마세요. 제목은 문장이 아닙니다(의문형의 물음표는 허용).
  (2) 영어 제목 표기법(Title Case) — 관사·전치사·접속사(a, the, of, in, to, and 등)를 빼고
      모든 낱말의 첫 글자를 대문자로 씁니다. 첫 낱말과 끝 낱말은 무조건 대문자.
  (3) 길이를 비슷하게 맞추세요. 대체로 4~10 단어이며, 한 선지만 유독 길거나 짧으면 안 됩니다.
  (4) 갈래 표지를 섞지 마세요 — 넷은 물음표인데 하나만 아니거나, 넷은 콜론인데 하나만
      없으면 그 하나가 곧 답으로 보입니다.

{ctx}
"""

# Title Case 판정에서 소문자로 두어도 되는 낱말(관사·등위접속사·짧은 전치사).
_SMALL = {"a", "an", "the", "and", "but", "or", "nor", "for", "yet", "so",
          "at", "by", "in", "of", "on", "to", "up", "as", "if", "via",
          "from", "into", "over", "with", "than", "that", "when", "upon"}


def _words(choice: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", choice)


def _titlecase_ratio(choice: str) -> float:
    """제목 표기법을 지킨 낱말의 비율(관사·전치사류는 세지 않는다)."""
    ws = _words(choice)
    graded = [w for i, w in enumerate(ws)
              if i == 0 or i == len(ws) - 1 or w.lower() not in _SMALL]
    if not graded:
        return 1.0
    return sum(1 for w in graded if w[:1].isupper()) / len(graded)


def check_title_form(choices: list[str]) -> list[str]:
    """선지 5개가 '제목 형식으로 통일'되었는지 본다. 어긋난 사유 목록을 돌려준다.

    한 선지만 모양이 다르면 학생이 내용을 읽지 않고 그것을 고르게 되므로,
    개별 선지의 옳고 그름보다 '다섯 개가 같은 모양인가'를 본다.
    """
    bad: list[str] = []
    # ① 마침표로 끝나는 서술문 — 제목이 아니다(물음표·느낌표는 제목으로 쓰인다)
    dotted = [i for i, c in enumerate(choices, 1) if c.strip().endswith(".")]
    if dotted:
        bad.append(f"선지 {dotted} 가 마침표로 끝납니다(제목은 문장이 아닙니다).")
    # ② 제목 표기법(Title Case) 통일
    ratios = [_titlecase_ratio(c) for c in choices]
    low = [i for i, r in enumerate(ratios, 1) if r < 0.8]
    if low and len(low) < len(choices):
        bad.append(f"선지 {low} 만 제목 표기법(Title Case)을 지키지 않았습니다.")
    elif low:
        bad.append("선지 전부가 제목 표기법(Title Case)을 지키지 않았습니다.")
    # ③ 길이 — 한 선지만 유독 길거나 짧으면 그 자체가 단서가 된다
    lens = [len(_words(c)) for c in choices]
    if lens and max(lens) - min(lens) >= 8:
        bad.append(f"선지 길이가 고르지 않습니다(가장 짧은 것 {min(lens)}단어 / "
                   f"가장 긴 것 {max(lens)}단어).")
    if any(n < 2 for n in lens):
        bad.append("낱말 하나뿐인 선지가 있습니다(제목으로 너무 짧습니다).")
    if any(n > 14 for n in lens):
        bad.append("14단어를 넘는 선지가 있습니다(제목으로 너무 깁니다).")
    # ④ 갈래 표지(물음표·콜론)를 섞지 않았는가 — 하나만 다르면 그것이 곧 답으로 보인다
    for mark, name in (("?", "물음표(의문형)"), (":", "콜론형")):
        n = sum(1 for c in choices if mark in c)
        if 0 < n < len(choices):
            bad.append(f"{name} 선지가 {n}개뿐입니다 — 다섯 개를 같은 갈래로 통일하세요"
                       f"(전부 쓰거나 전부 쓰지 않기).")
    # ⑤ 같은 선지 중복
    if len({c.strip().lower() for c in choices}) != len(choices):
        bad.append("같은 선지가 두 번 나옵니다.")
    return bad


def _extra(out: TitleOut) -> None:
    bad = check_title_form(out.choices)
    if bad:
        raise ValueError("제목 선지 형식 통일 실패 — " + " ".join(bad))


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    out: TitleOut = client.structured(
        system=SYSTEM,
        prompt=(variant_hint + "\n" if variant_hint else "") + _PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=TitleOut,
        max_tokens=2500,
        max_retries=max_retries,
        extra_validate=_extra,
    )
    wrong = {w.no: w.text for w in out.wrong_reasons}
    choices, answer_no = out.choices, out.answer_no
    old_no = answer_no
    if answer_pos:   # 정답 위치 분산(선지 재배열 — 정오 불변)
        choices, answer_no, wrong = answer_spread.place_answer(
            choices, answer_no, answer_pos, wrong)
    reason = answer_spread.relabel_answer_ref(out.reason, old_no, answer_no)
    q, a = B.make_title(analysis.sentences, choices, answer_no, reason, wrong)
    return q, a, review.weak_distractors(out.wrong_reasons)
