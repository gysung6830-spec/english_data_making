"""내용 O/X 생성기 — 열 진술을 각각 참·거짓으로 판정하게 한다. 지문은 원본 그대로.

한 지문에서 두 문항이 나온다: 한글판과 영어판. 둘은 '같은 사실을 번역한 것'이
아니라 서로 다른 사실을 묻는다 — 같은 사실이면 한 판을 푼 학생이 다른 판을 뜻으로
옮겨 적어 버린다. 영어판은 영어 진술을 읽어 내는 일 자체가 과제가 된다.

[출제 원리]
① O 는 늘 두 개, 나머지 여덟 개는 X.
   O 가 절반쯤이면 학생이 감으로 반은 맞힌다. 여덟 대 둘이면 '왜 X 인지'를 하나하나
   짚어야 하고, 대충 O 를 찍는 습관이 통하지 않는다.
② O 진술은 '눈에 덜 띄는 세부'를 유의어로 바꿔 쓴다.
   원문 낱말이 많이 보이면 O 처럼 느껴진다. 그래서 O 에는 원문 낱말을 숨기고,
   X 에는 오히려 원문 낱말을 그대로 노출해 그럴듯하게 만든다.
③ X 여덟 개는 서로 다른 여덟 가지 축으로 비튼다(아래 프롬프트의 (1)~(8)).
   한 축을 되풀이하면 하나를 알아챈 학생이 나머지도 같은 눈으로 걸러 낸다.
   여덟 축은 모두 '읽고 이해했는가'를 묻는 것들이다. 낱말 하나만 바꿔 놓고 눈썰미를
   재는 두 방식은 일부러 뺐다 — 숫자·기간만 살짝 틀리는 '부분 일치 + 한 요소 왜곡'과
   '늘·오직·반드시'로 키우는 '정도·빈도 과장'. 그런 함정은 글을 이해한 학생도 걸리고
   대충 읽은 학생도 운으로 피해서, 실력을 가르지 못한다.
④ O 두 개의 자리는 코드가 정한다(answer_spread.ox_positions).
   모델에게 맡기면 앞쪽으로 몰리는 버릇이 나오고, 문항마다 같은 자리에 O 가 오면
   지문을 읽지 않고 자리만 보고 찍는다. 열두 문항까지 어느 둘도 같은 자리 짝을
   쓰지 않으며, 두 O 는 늘 세 칸 이상 떨어져 있다.
"""
from __future__ import annotations

from .. import answer_spread, build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, ContentOXOut
from ..types import CONTENT, CONTENT_2
from .base import context

_PROMPT = """아래 '정본 지문'으로 '내용 O/X' 문제를 **두 개** 만드세요. 발문은 '다음 진술이 글의
내용과 일치하면 O, 일치하지 않으면 X 를 쓰시오.' 이며, 지문은 원본 그대로 쓰입니다.
당신은 진술과 그 판정만 만듭니다.

- korean: 한국어 진술 **10개**
- english: 영어 진술 **10개**
- 각 항목은 text(진술) · is_true(글과 일치하면 true) · why(그 판정의 근거, 한국어).

[가장 중요한 조건]
- 두 목록 각각에서 is_true 가 true 인 것은 **정확히 2개**, 나머지 8개는 false 입니다.
- 한글판과 영어판은 **서로 다른 사실**을 물어야 합니다. 영어판은 한글판의 번역이
  아닙니다. 같은 문장을 두 언어로 내면 한 판을 푼 학생이 다른 판을 그대로 옮겨 적습니다.
  · 한글판이 A·B 사실을 O 로 물었다면, 영어판은 C·D 를 O 로 무세요.
  · X 진술도 서로 다른 대목을 비틀어야 합니다.
- 진술을 늘어놓는 순서는 신경 쓰지 마세요. O 자리는 조판기가 다시 정합니다.

[O 진술 2개를 쓰는 법]
- 지문에서 '눈에 덜 띄는 세부 사실'을 고르세요(맨 앞 문장의 주제문은 너무 쉽습니다).
- 원문 단어를 그대로 쓰지 말고 **유의어로 바꿔 쓰세요**. 원문 낱말이 그대로 보이면
  읽지 않고도 O 로 찍힙니다.
- 두 O 는 지문의 서로 다른 대목에서 가져오세요.

[X 진술 8개를 쓰는 법 — 아래 여덟 축을 '하나씩' 쓰세요]
한 축을 되풀이하면 하나를 알아챈 학생이 나머지도 같은 눈으로 걸러 냅니다.
각 X 진술에는 지문에 실제로 나온 단어를 일부 그대로 노출해 그럴듯하게 만드세요.
  (1) 주체·대상 바꿔치기 — 지문의 진짜 관계에서 행위자와 대상만 맞바꿈
  (2) 인과 날조 — 지문에 나란히 놓인 두 사실을 '때문에'로 엮음
  (3) 인과 역전 — 지문의 원인과 결과를 뒤집음
  (4) 조건 삭제 — '이론상·~할 때에는' 같은 단서를 떼어 무조건으로 만듦
  (5) 시점 뒤집기 — '앞으로 그럴 수 있다'를 '이미 그렇게 했다'로(또는 그 반대)
  (6) 부정 뒤집기 — 지문이 '아니다'라고 못 박은 것을 '그렇다'로(또는 그 반대)
  (7) 논지·화자 뒤집기 — 필자가 반박하려고 소개한 통념을 필자의 주장인 것처럼
  (8) 미언급인데 그럴듯 — 지문과 모순은 아니지만 아예 언급되지 않은 상식적 진술

[쓰지 말아야 할 두 가지 — 반드시 지키세요]
  · **부분 일치 + 한 요소만 왜곡 금지** — 나머지는 다 맞는데 숫자·기간·대상 하나만
    살짝 바꿔 놓는 방식. 예: '수만 년' 을 '수백 년' 으로.
  · **정도·빈도 과장 금지** — '~하기도 한다' 를 '늘·오직·반드시·모든' 으로 키우는 방식.
  둘 다 글을 이해했는지가 아니라 눈썰미를 재는 함정입니다. 이해한 학생도 놓치고 대충
  읽은 학생도 운으로 피해서 실력을 가르지 못합니다. X 는 '읽고 따져 봐야 아는' 것으로만
  만드세요.

[why 쓰는 법] 모두 한국어로.
- O: 지문의 어느 문장에 근거하는지(원문 표현을 짧게 인용).
- X: 지문은 무엇이라 했는데 진술의 '어느 부분'이 왜 어긋나는지. 끝에 축 이름을
  괄호로 적으세요(예: (주체 바꿔치기)). '(1)번 축' 처럼 번호로 부르지는 마세요.

[확실성] O 는 지문과 '완전히' 일치해야 하고(과장·축소 없이), X 는 지문의 특정 문장과
'확실히' 어긋나거나 지문에 없어야 합니다. 판정이 갈릴 여지가 있으면 안 됩니다.

{ctx}
"""


def generate_pair(client: ClaudeClient, analysis: Analysis, body: str,
                  max_retries: int = 1, passage_index: int = 0,
                  variant_hint: str = "") -> dict[str, tuple[str, str, list[str]]]:
    """한 번의 호출로 한글판·영어판 두 문항을 만든다.

    두 판이 서로 다른 사실을 물어야 하므로 한 번에 만든다. 따로 부르면 같은 사실을
    두 번 묻게 되고(모델은 다른 호출에서 무엇을 물었는지 모른다), 호출도 두 배가 된다.
    """
    def _chk(out: ContentOXOut) -> None:
        bad = shape.check_ox_axes([it.why for it in out.korean + out.english])
        if bad:
            raise ValueError("내용 O/X 설계 결함 — " + " ".join(bad))

    out: ContentOXOut = client.structured(
        system=SYSTEM,
        prompt=((variant_hint + "\n" if variant_hint else "")
                + _PROMPT.format(ctx=context(analysis))),
        cache_prefix=context(analysis),
        model_cls=ContentOXOut,
        max_tokens=6000,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    seed = answer_spread.seed_of(analysis.title)
    res: dict[str, tuple[str, str, list[str]]] = {}
    for version, (slot, items) in enumerate(((CONTENT, out.korean),
                                             (CONTENT_2, out.english))):
        placed = answer_spread.place_ox(
            items, answer_spread.ox_positions(passage_index, version, seed))
        q, a = B.make_content_ox(analysis.sentences,
                                 [it.text for it in placed],
                                 [it.is_true for it in placed],
                                 [it.why for it in placed])
        res[slot] = (q, a, [])
    return res


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, difficulty: str = "",
             answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    """한글판 하나만 필요할 때(옛 경로 호환). 통합본은 generate_pair 를 쓴다."""
    return generate_pair(client, analysis, body, max_retries=max_retries,
                         variant_hint=variant_hint)[CONTENT]
