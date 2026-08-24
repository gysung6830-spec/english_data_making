"""어법·어휘 짝짓기 생성기 — '적절하지 않은 것끼리 짝지어진 것은?'

밑줄 ⓐ~ⓔ 5개 중 **정확히 2개**만 부적절하고, 학생은 그 둘을 짝으로 고른다.
한쪽은 어법 오류(수 일치·태·준동사 등), 다른 한쪽은 문맥상 어휘 오류(반의어 함정)라
어법과 어휘를 한 문항에서 함께 확인한다. **하나만 찾아서는 답이 나오지 않으므로**
찍기가 통하지 않고, 둘 다 정확히 짚어야 한다.

선지(짝 5개)는 LLM 이 아니라 코드가 만든다 — 정답 짝이 반드시 하나만 들어가고,
오답 짝이 실수로 정답이 되는 일이 없도록 보장하기 위해서다. 오답 짝은 '정답 두 개 중
하나만 포함한 짝' 3개와 '둘 다 포함하지 않은 짝' 1개로 짠다. 하나만 찾은 학생이
그대로 답을 고를 수 없게 하는 배치다.
"""
from __future__ import annotations

import re
from itertools import combinations

from .. import answer_spread, build2, review, shape
from ..format2 import cletter
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, PairOddOut
from .base import context
from .vocab import _mark_words

_PROMPT = """아래 '정본 지문'으로 '어법·어휘 짝짓기' 문제를 만드세요. 발문은
'밑줄 친 부분 중, 어법상 또는 문맥상 낱말의 쓰임이 적절하지 않은 것끼리 짝지어진 것은?'입니다.
지문을 새로 쓰지 말고, 밑줄 칠 낱말과 보여줄 형태만 정하세요.

- marks: 밑줄 정확히 5개(ⓐ~ⓔ). 각 항목은 sent_no(1-based), word(지문의 원본 낱말),
  shown(문제에 보여줄 형태). 읽는 순서대로 나열하세요.
- 그중 **정확히 2개만** 부적절하게 만듭니다. 나머지 3개는 shown 을 word 와 똑같이 둡니다.
  · grammar_no — **어법**상 틀린 밑줄 하나. shown 을 어법상 틀린 형태로 바꿉니다.
    (수 일치 / 시제 / 태 / 준동사 / 관계사 / 병렬 / 대명사)
  · vocab_no — **문맥**상 낱말이 부적절한 밑줄 하나. shown 을 원본의 '반의어'로 바꿔
    글의 흐름과 어긋나게 만듭니다. 어법은 멀쩡해야 하고 '뜻'만 어긋나야 합니다.
  · 이 둘은 서로 다른 밑줄이어야 하고, 되도록 떨어진 문장에 두세요.

[적절한 밑줄 3개] shown 을 word 와 똑같이 두어 어법·문맥 모두 흠이 없어야 합니다.
학생이 헷갈릴 만한 자리(관계절 안의 동사, 병렬 구조, 다의어 등)를 골라 두면 좋습니다.

[근거] reasons 는 **밑줄 5개 전부**에 대해 하나씩 씁니다.
- 부적절한 둘: 무엇이 왜 틀렸고 어떤 형태·낱말로 고쳐야 하는지. 어법 오류인지 어휘 오류인지
  괄호로 밝히세요. 예) "관계절 주어 who 가 people(복수)을 받으므로 perform (어법)".
- 적절한 셋: 왜 적절한지. 학생이 왜 헷갈릴 만한지까지 짚어 주면 좋습니다.
reason: 총평 한 줄(한국어) — 부적절한 것이 어느 둘인지.

[확실성] 이 유형은 '둘 다' 맞아야 정답이므로 판정이 하나만 어긋나도 문항이 무너집니다.
- 부적절한 둘은 '누가 봐도 확실히' 틀려야 합니다(문체 취향·미묘한 용법 차이는 안 됩니다).
- 적절한 셋은 '완전히' 옳아야 합니다. 하나라도 어색하면 부적절한 것이 3개가 됩니다.
- 밑줄 밖의 본문에는 손대지 마세요.

{ctx}
"""


def build_pairs(a: int, b: int, seed: int = 0) -> tuple[list[str], int]:
    """정답 짝 (a,b)를 포함한 짝 선지 5개를 만든다. (선지 문자열, 정답 번호) 반환.

    오답은 '정답 둘 중 하나만 포함한 짝' 3개 + '둘 다 없는 짝' 1개로 짠다.
    하나만 찾아낸 학생이 그대로 답을 고를 수 없게 하는 배치다.
    """
    ans = tuple(sorted((a, b)))
    rest = [n for n in range(1, 6) if n not in ans]
    overlap = [p for p in combinations(range(1, 6), 2)
               if p != ans and len(set(p) & set(ans)) == 1]
    disjoint = [p for p in combinations(rest, 2)]
    # 지문마다 조합이 달라지도록 시드로 고르기 시작 위치만 옮긴다(무작위 아님).
    k = seed % max(1, len(overlap))
    picked = [overlap[(k + i) % len(overlap)] for i in range(3)]
    picked.append(disjoint[seed % len(disjoint)])
    pairs = [ans] + picked
    texts = [f"{cletter(x)}-{cletter(y)}" for x, y in pairs]
    return texts, 1                     # 정답은 일단 1번(뒤에서 위치를 분산한다)


_MARKER = re.compile(r"^\s*[ⓐ-ⓔ①-⑧]\s*[:.)]?\s*")


def _strip_marker(text: str) -> str:
    """사유 앞에 모델이 스스로 붙인 밑줄 기호를 뗀다(조판이 다시 붙인다)."""
    return _MARKER.sub("", (text or "").strip())


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, answer_pos: int | None = None,
             variant_hint: str = "", avoid: set[str] | None = None,
             with_words: bool = False):
    """avoid: 같은 지문의 다른 밑줄 문항이 이미 쓴 낱말(겹치면 재요청).
    with_words=True 면 (q, a, flags, 이 문항이 쓴 낱말들)을 돌려준다(밑줄 묶음용)."""
    taken = {w.lower() for w in (avoid or set())}

    def _chk(out: PairOddOut) -> None:
        out.check()
        dup = sorted(_mark_words(out.marks) & taken)
        if dup:
            raise ValueError(f"다른 밑줄 문항과 낱말이 겹칩니다: {', '.join(dup)}. "
                             "겹치지 않는 낱말로 다시 고르세요.")
        # 어휘 자리를 갈아 끼우다 구동사·전치사가 깨지면 어법 오류처럼 보인다.
        broke = shape.check_marks_swaps(analysis.sentences, out.marks)
        if broke:
            raise ValueError("낱말을 바꾸자 문장이 깨졌습니다 — " + " ".join(broke))

    avoid_note = ""
    if taken:
        avoid_note = ("\n[겹침 금지] 같은 지문에 밑줄 문항이 여럿입니다. 아래 낱말은 다른 문항이 "
                      "이미 밑줄로 썼으니 이번에는 하나도 쓰지 마세요.\n"
                      f"피할 낱말: {', '.join(sorted(taken))}\n")

    out: PairOddOut = client.structured(
        system=SYSTEM,
        prompt=((variant_hint + "\n" if variant_hint else "")
                + _PROMPT.format(ctx=context(analysis)) + avoid_note),
        cache_prefix=context(analysis),
        model_cls=PairOddOut,
        max_tokens=3000,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    seed = answer_spread.seed_of(analysis.title)
    choices, answer_no = build_pairs(out.grammar_no, out.vocab_no, seed=seed)
    if answer_pos:      # 정답 위치 분산(짝 선지 재배열 — 정오 불변)
        choices, answer_no, _ = answer_spread.place_answer(choices, answer_no, answer_pos)

    # 밑줄별 사유는 '번호 → 글' 로 넘긴다. 밑줄 기호는 조판이 붙이므로(그리고 읽는
    # 순서로 다시 매겨지므로) 여기서 붙이면 안 된다. 모델이 사유 앞에 스스로 'ⓐ' 를
    # 달아 오면 마커가 겹쳐 찍힌다(실제 출력물 7번 'ⓐ ⓐ contain:').
    reasons = {r.no: _strip_marker(r.text) for r in out.reasons}
    head = (out.reason or "").strip()

    marks = [(m.sent_no - 1, m.word, m.shown) for m in out.marks]
    flags: list[str] = []
    q, a = build2.make_A(analysis.sentences, marks, answer_no, head, choices,
                         flags=flags, reasons=reasons)
    flags = flags + review.type_fit_flags(getattr(analysis, "passage_type", "prose"), "A")
    if with_words:
        return q, a, flags, _mark_words(out.marks)
    return q, a, flags
