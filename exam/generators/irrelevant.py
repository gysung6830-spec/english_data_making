"""무관한 문장 생성기 (수능 35번) — 원문에 없던 문장 하나를 새로 써서 끼워 넣는다.

변형문제로서의 값어치가 특히 크다. 다른 유형은 지문을 통째로 외운 학생이 기억만으로
풀 수 있지만, 이 유형은 '원문에 없던 문장'을 새로 만들어 넣으므로 암기가 통하지 않는다.
글의 논리 흐름을 실제로 이해했는지가 그대로 드러난다.

구조: 도입문(번호 없음) + 연속 5문장(①~⑤). 그중 한 자리의 원문 문장을 버리고,
같은 소재를 다루지만 논지 전개에서 벗어나는 새 문장으로 갈아 끼운다.
"""
from __future__ import annotations

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

[무관한 문장을 쓰는 법] — 이 유형의 핵심입니다.
- '소재는 같게, 논지는 벗어나게' 만듭니다. 지문의 핵심어를 1~2개 그대로 써서 언뜻 어울려
  보이게 하되, 필자가 밀고 가는 논지에는 기여하지 않아야 합니다.
- 좋은 이탈 방식:
  · 같은 소재의 '일반 상식·배경 설명'으로 빠지기(글의 주장과 무관한 사실 진술)
  · 필자가 다루지 않는 '다른 측면'으로 화제 전환(예: 논지는 원인인데 비용·역사로 새기)
  · 논지와 반대 방향의 조언·권고를 슬쩍 끼우기
- 피할 것: 전혀 다른 소재(고양이·날씨 등)로 튀면 너무 쉬워집니다. 반대로 논지를 그대로
  다시 말하면(패러프레이즈) 정답이 성립하지 않습니다.
- 앞뒤 문장과 지시어·연결사가 어색하게 이어지지 않도록, 문장 자체는 자연스럽게 쓰세요.
  (연결이 부자연스러워 티가 나면 문제가 아니라 오류가 됩니다.)

[나머지 4문장] 원문 그대로 쓰이므로 당연히 흐름에 맞습니다.

- reason: 왜 그 문장이 전체 흐름에서 벗어나는지 한국어로 설명. 글의 논지를 한 줄로 짚고,
  그 문장이 그 논지에 어떻게 기여하지 않는지 콕 집어 쓰세요.
- wrong_reasons: 나머지 4개 번호 각각이 앞뒤와 어떻게 이어지는지(지시어·연결사·논리 관계)
  한국어로 설명.

[확실성] 무관한 문장은 하나뿐이어야 합니다. 나머지 4개는 원문이므로 흐름에 맞고, 새로 쓴
문장만 '확실히' 논지에서 벗어나야 합니다. 애매하면 안 됩니다.

{ctx}
"""


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
        extra_validate=_extra,
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
