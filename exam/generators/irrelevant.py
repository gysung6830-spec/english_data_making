"""무관한 문장 생성기 (수능 35번) — 원문에 없던 문장 하나를 새로 써서 끼워 넣는다.

변형문제로서의 값어치가 특히 크다. 다른 유형은 지문을 통째로 외운 학생이 기억만으로
풀 수 있지만, 이 유형은 '원문에 없던 문장'을 새로 만들어 넣으므로 암기가 통하지 않는다.
글의 논리 흐름을 실제로 이해했는지가 그대로 드러난다.

구조: 도입문(번호 없음) + 연속 5문장(①~⑤). 그중 한 자리의 원문 문장을 버리고,
같은 소재를 다루지만 논지 전개에서 벗어나는 새 문장으로 갈아 끼운다.
"""
from __future__ import annotations

import re

from .. import build as B
from .. import review
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, IrrelevantOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '무관한 문장' 문제를 만드세요. 발문은 '다음 글에서 전체
흐름과 관계 없는 문장은?'입니다.

[문제 구조]
- 도입 문장(들)은 번호 없이 그대로 두고, 그 다음 '연속된 5개 문장'에 ①~⑤를 붙입니다.
- start_no: ①이 붙을 원문 문장 번호(1-based). 도입문이 최소 1개 있어야 하므로 2 이상이며,
  start_no + 4 가 마지막 문장 번호를 넘지 않아야 합니다.
  가급적 글의 주제가 드러난 도입부 뒤에서 시작하세요.
- answer_no: 1~5 중 '무관한 문장'을 끼워 넣을 자리. 그 자리의 원문 문장은 버려집니다.
- sentence: 그 자리에 넣을, 새로 쓴 영어 문장 1개(정답).

[무관한 문장을 쓰는 법] — 이 유형의 핵심입니다. 두 가지를 '동시에' 지켜야 합니다.

(가) 낱말은 지문에서 가져올 것 — 필수
  · 지문에 실제로 나온 핵심 낱말을 '최소 두 개' 그대로 넣으세요(어형 변화는 허용).
  · 전혀 다른 소재(고양이·날씨·출장비 등)로 튀면 학생이 읽지도 않고 찾아냅니다. 낱말만
    보면 이 글의 문장처럼 보여야 합니다.

(나) 논리는 어긋나게 할 것 — 필수
  낱말이 같아도 '글이 밀고 가는 논지'에는 기여하지 않아야 합니다. 아래 방식으로 논리를
  틀어 주세요(하나만 골라 쓰면 됩니다):
  · 인과 뒤집기 — 지문이 A 때문에 B라고 했다면, B 때문에 A라고 쓰기
  · 없던 인과 만들기 — 지문에 함께 나온 두 사실을 원인·결과로 엮어 버리기
  · 조건·범위 바꾸기 — 지문이 '어떤 경우에'라고 한 것을 '항상·모든 경우에'로
  · 평가 뒤집기 — 지문이 장점으로 든 것을 단점(또는 그 반대)으로 다루기
  · 곁가지로 새기 — 같은 낱말을 쓰되 필자가 다루지 않는 측면(비용·역사·통계)으로

[반드시 피할 것]
  · 논지를 그대로 다시 말하기(패러프레이즈) — 그러면 정답이 성립하지 않습니다.
  · 앞뒤와 지시어·연결사가 어긋나 문장 자체가 덜컹거리는 것 — 티가 나면 문제가 아니라
    오류가 됩니다. 문장 하나만 떼어 읽으면 자연스러워야 하고, 논리를 따져야만 어긋난 것이
    드러나야 합니다.

[나머지 4문장] 원문 그대로 쓰이므로 당연히 흐름에 맞습니다.

- reason: 왜 그 문장이 전체 흐름에서 벗어나는지 한국어로 설명. 글의 논지를 한 줄로 짚고,
  그 문장이 그 논지에 어떻게 기여하지 않는지 콕 집어 쓰세요.
- wrong_reasons: 나머지 4개 번호 각각이 앞뒤와 어떻게 이어지는지(지시어·연결사·논리 관계)
  한국어로 설명.

[확실성] 무관한 문장은 하나뿐이어야 합니다. 나머지 4개는 원문이므로 흐름에 맞고, 새로 쓴
문장만 '확실히' 논지에서 벗어나야 합니다. 애매하면 안 됩니다.

{ctx}
"""


# 낱말 겹침을 셀 때 무시할 기능어(이것만 겹치면 '지문 낱말을 썼다'고 볼 수 없다).
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "in", "on", "at", "to", "for",
    "with", "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "it", "its", "this", "that", "these", "those", "they", "them", "their", "we",
    "our", "you", "your", "he", "she", "his", "her", "not", "no", "can", "may",
    "will", "would", "could", "should", "must", "have", "has", "had", "do", "does",
    "did", "than", "then", "so", "such", "more", "most", "some", "many", "much",
    "one", "also", "now", "when", "while", "into", "over", "out", "up", "there",
}


def _content_words(text: str) -> set[str]:
    """비교용 내용어 집합 — 소문자화하고 흔한 어미(s·es·ed·ing)를 떼어 어형 차이를 흡수."""
    out = set()
    for w in re.findall(r"[A-Za-z][A-Za-z'-]*", text.lower()):
        if len(w) < 3 or w in _STOP:
            continue
        for suf in ("ing", "es", "ed", "s"):
            if len(w) > len(suf) + 2 and w.endswith(suf):
                w = w[: -len(suf)]
                break
        out.add(w)
    return out


def check_irrelevant_sentence(sentence: str, sentences: list[str]) -> list[str]:
    """끼워 넣을 문장이 '지문 낱말을 쓰되 논지에서 벗어나는가'를 본다.

    낱말이 겹치지 않으면 학생이 읽지도 않고 찾아내고(너무 쉬움), 어느 한 문장과 거의
    같으면 그건 무관한 문장이 아니라 원문 되풀이다(정답이 성립하지 않음).
    """
    bad: list[str] = []
    new = _content_words(sentence)
    if not new:
        return ["끼워 넣을 문장에 내용어가 없습니다."]
    passage = _content_words(" ".join(sentences))
    shared = new & passage
    if len(shared) < 2:
        bad.append(f"지문에 나온 낱말을 {len(shared)}개만 썼습니다(2개 이상 필요) — "
                   "소재가 동떨어져 읽지 않고도 답이 보입니다.")
    for i, s in enumerate(sentences, 1):
        own = _content_words(s)
        if own and len(new & own) / len(new | own) >= 0.7:
            bad.append(f"{i}번 문장과 거의 같습니다 — 원문 되풀이는 무관한 문장이 아닙니다.")
            break
    return bad


def _extra(out: IrrelevantOut) -> None:
    if not (out.sentence or "").strip():
        raise ValueError("무관한 문장(sentence)이 비어 있습니다.")
    if len(out.wrong_reasons) != 4:
        raise ValueError("나머지 4개 문장의 근거(wrong_reasons)가 4개여야 합니다.")


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    n = len(analysis.sentences)
    if n < 6:      # 도입문 1개 + ①~⑤ 5개 = 최소 6문장
        raise ValueError(f"무관한 문장 문제에는 문장이 6개 이상 필요합니다(현재 {n}개).")

    def _check(out: IrrelevantOut) -> None:
        _extra(out)
        bad = check_irrelevant_sentence(out.sentence, analysis.sentences)
        if bad:
            raise ValueError("끼워 넣을 문장이 조건에 맞지 않습니다 — " + " ".join(bad))

    ctx = context(analysis)
    out: IrrelevantOut = client.structured(
        system=SYSTEM,
        prompt=((variant_hint + "\n" if variant_hint else "")
                + _PROMPT.format(ctx=ctx)
                + f"\n[문장 수] 이 지문은 {n}개 문장입니다. "
                  f"start_no 는 2 이상 {n - 4} 이하여야 합니다."),
        cache_prefix=ctx,
        model_cls=IrrelevantOut,
        max_tokens=2500,
        max_retries=max_retries,
        extra_validate=_check,
    )
    # 범위를 벗어나면 조판 가능한 자리로 당겨 붙인다(문항을 버리지 않는다).
    start_no = min(max(out.start_no, 2), n - 4)
    flags: list[str] = []
    if start_no != out.start_no:
        flags.append(review.FIX_INSERT)
    wrong = {w.no: w.text for w in out.wrong_reasons if w.no != out.answer_no}
    q, a = B.make_irrelevant(analysis.sentences, start_no, out.answer_no,
                             out.sentence, out.reason, wrong)
    return q, a, flags + review.weak_distractors(out.wrong_reasons)
