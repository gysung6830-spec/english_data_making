"""내용 O/X 생성기 — 열 진술을 각각 참·거짓으로 판정하게 한다. 지문은 원본 그대로.

한 지문에서 두 문항이 나온다: 한글판과 영어판. 둘은 '같은 사실을 번역한 것'이
아니라 서로 다른 사실을 묻는다 — 같은 사실이면 한 판을 푼 학생이 다른 판을 뜻으로
옮겨 적어 버린다. 영어판은 영어 진술을 읽어 내는 일 자체가 과제가 된다.

[출제 원리]
① O 는 늘 두 개, 나머지는 모두 X.
   O 가 절반쯤이면 학생이 감으로 반은 맞힌다. 여덟 대 둘이면 '왜 X 인지'를 하나하나
   짚어야 하고, 대충 O 를 찍는 습관이 통하지 않는다.
② O 진술은 '눈에 덜 띄는 세부'를 유의어로 바꿔 쓴다.
   원문 낱말이 많이 보이면 O 처럼 느껴진다. 그래서 O 에는 원문 낱말을 숨기고,
   X 에는 오히려 원문 낱말을 그대로 노출해 그럴듯하게 만든다.
③ X 는 여덟 축(shape.OX_AXES)을 하나씩 쓴다.
   한 축을 되풀이하면 그 하나를 알아챈 학생이 나머지도 같은 눈으로 한꺼번에 걸러 낸다.
   축은 글 속에 괄호로 적게 하지 않고 axis 필드로 따로 받는다 — 조판기가 이름을
   붙이므로 표기가 늘 같고, 축이 겹쳤는지 코드가 셀 수 있다.
   다만 겹쳤다고 다시 만들지는 않는다. 이 유형은 한 호출로 진술 스무 개를 만드는
   가장 비싼 호출이라, 축 하나 겹친 값으로 통째로 다시 부르면 문항 값이 두 배가 된다.
   프롬프트에서 '하나씩'을 못 박아 처음부터 맞게 나오게 한다.
   여덟 축은 모두 '읽고 이해했는가'를 묻는 것들이다. 낱말 하나만 바꿔 놓고 눈썰미를
   재는 두 방식은 일부러 뺐다 — 숫자·기간만 살짝 틀리는 '부분 일치 + 한 요소 왜곡'과
   '늘·오직·반드시'로 키우는 '정도·빈도 과장'. 그런 함정은 글을 이해한 학생도 걸리고
   대충 읽은 학생도 운으로 피해서, 실력을 가르지 못한다.
④ O 두 개의 자리는 코드가 정한다(answer_spread.ox_positions).
   모델에게 맡기면 앞쪽으로 몰리는 버릇이 나오고, 문항마다 같은 자리에 O 가 오면
   지문을 읽지 않고 자리만 보고 찍는다. 열두 문항까지 어느 둘도 같은 자리 짝을
   쓰지 않으며, 두 O 는 늘 세 칸 이상 떨어져 있다.

[한 지문에서 스무 진술이 나오는가 — 나온다. 다만 무엇을 겹치게 두느냐에 달렸다]
실제 EBS 지문(약 135낱말)에서 판정 가능한 명제는 열댓 개다. 그런데 20진술 중 X 가
열여섯이다. X 마다 다른 명제를 요구하면 16 > 13 이라 모델은 지문에 없는 이야기를
지어낸다 — 정답 시비의 첫째 원인이다.

그럴 필요가 없다. **겹치면 안 되는 것은 O 넷뿐이다.**
  · O 는 '지문과 일치한다'는 같은 사실이라, 두 판이 같은 사실을 O 로 물으면 한쪽이
    다른 쪽의 번역이 된다. 한 판을 푼 학생이 그대로 옮겨 적는다.
  · X 는 그렇지 않다. 한글판이 5번 문장을 '인과 역전'으로 비틀고 영어판이 같은 5번
    문장을 '조건 삭제'로 비틀면, 판정 근거가 달라 서로 다른 문제다. 옮겨 적을 수 없다.
그래서 X 는 두 판 사이에 대목을 겹쳐 써도 된다(한 판 안에서는 되도록 흩는다).
필요한 서로 다른 명제는 16개가 아니라 4개다 — 열댓 개면 넉넉하다.

[재료를 세는 자는 문장 수가 아니라 낱말 수다]
실제 지문 둘을 재어 보고 고쳤다.
    지문1  5문장 141낱말 → 명제 약 13개 (문장이 길고 종속절이 많다)
    지문2 10문장 132낱말 → 약 13~16개
문장 수는 두 배 차이인데 명제 수는 비슷하다. 낱말 수가 거의 같으니 당연하다.
문장 수로 자르면 정보가 더 많은 지문1이 오히려 축소 대상이 된다. 그래서 낱말로 센다.

  낱말 100개 미만 → 영어판을 8진술로(총 18개) + 두 판의 O 가 같은 대목에 기대는 것 허용.
      [schemas.ox_sizes · OX_WORDS_SHORT]
  낱말 120개 미만 → 재료가 없는 축은 '미언급인데 그럴듯'으로 대체 허용(판마다 최대 2회).
      [OX_WORDS_THIN] 인과 관계가 없는 지문에서 '인과 역전'을, 단서구가 없는 지문에서
      '조건 삭제'를 만들어 내는 것보다 낫다.
실제 EBS 지문 둘(141·132낱말)은 어느 문턱에도 걸리지 않아 20진술 전부를 낸다.
"""
from __future__ import annotations

from .. import answer_spread, build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import (Analysis, ContentOXOut, N_OX_TRUE, OX_WORDS_SHORT,
                       OX_WORDS_THIN, ox_sizes, passage_words)
from ..types import CONTENT, CONTENT_2
from .base import context

# 짧은 지문에서 '미언급인데 그럴듯'으로 대신 채워도 되는 횟수(판마다).
_FILL_ALLOWANCE = 2

_PROMPT = """아래 '정본 지문'으로 '내용 O/X' 문제를 **두 개** 만드세요. 발문은 '다음 진술이 글의
내용과 일치하면 O, 일치하지 않으면 X 를 쓰시오.' 이며, 지문은 원본 그대로 쓰입니다.
당신은 진술과 그 판정만 만듭니다.

- korean: 한국어 진술 **{n_ko}개**
- english: 영어 진술 **{n_en}개**
- 각 항목은 text(진술) · is_true(글과 일치하면 true) · why(그 판정의 근거, 한국어) ·
  axis(어느 축으로 비틀었는지 — 아래 여덟 이름 중 하나를 '글자 그대로'. O 진술은 "일치").

[가장 중요한 조건]
- 두 목록 각각에서 is_true 가 true 인 것은 **정확히 {n_true}개**입니다.
  한글판은 나머지 {x_ko}개가, 영어판은 나머지 {x_en}개가 모두 false 입니다.
{o_rule}- 진술을 늘어놓는 순서는 신경 쓰지 마세요. O 자리는 조판기가 다시 정합니다.

[O 진술 {n_true}개를 쓰는 법]
- 지문에서 '눈에 덜 띄는 세부 사실'을 고르세요(맨 앞 문장의 주제문은 너무 쉽습니다).
- 원문 단어를 그대로 쓰지 말고 **유의어로 바꿔 쓰세요**. 원문 낱말이 그대로 보이면
  읽지 않고도 O 로 찍힙니다.
- **영어판 O 는 지문의 낱말을 다섯 개 넘게 연달아 쓰면 안 됩니다.** 문장 구조부터
  바꿔 다시 쓰세요(능동↔수동 · 구를 절로 · 어순 조정). 잘 만든 O 는 지문과 연달아
  겹치는 낱말이 두세 개를 넘지 않습니다. X 는 반대로 원문 낱말을 그대로 노출해도 됩니다.
- 두 O 는 지문의 서로 다른 대목에서 가져오세요.

[X 진술을 쓰는 법 — 축이 겹치지 않게]
**한글판의 X {x_ko}개, 영어판의 X {x_en}개는 각각 아래 축을 하나씩 씁니다.**
한 축을 되풀이하면 그 하나를 알아챈 학생이 나머지도 같은 눈으로 한꺼번에 걸러 냅니다.
축을 흩어 놓으면 학생은 그만큼 다른 방식으로 따져 봐야 합니다.
한글판과 영어판은 각각 따로 축을 고릅니다(두 판 사이에는 겹쳐도 됩니다).
각 X 진술에는 지문에 실제로 나온 단어를 일부 그대로 노출해 그럴듯하게 만드세요.

**axis 에는 아래 여덟 이름 중 하나를 '한 글자도 바꾸지 말고' 그대로 적으세요.**
띄어쓰기·가운뎃점까지 같아야 합니다('조건삭제' 아님, '조건 삭제'). 표에 없는 이름을
적으면 해설의 축 표시가 빠집니다.

  axis 에 적을 이름            무엇을 비트는가
  ─────────────────────────  ────────────────────────────────────────────────
  주체·대상 바꿔치기            지문의 진짜 관계에서 행위자와 대상만 맞바꿈
  인과 날조                    지문에 나란히 놓인 두 사실을 '때문에'로 엮음
  인과 역전                    지문의 원인과 결과를 뒤집음
  조건 삭제                    '이론상·~할 때에는' 같은 단서를 떼어 무조건으로 만듦
  시점 뒤집기                  '앞으로 그럴 수 있다'를 '이미 그렇게 했다'로(또는 반대)
  부정 뒤집기                  지문이 '아니다'라고 못 박은 것을 '그렇다'로(또는 반대)
  논지·화자 뒤집기              필자가 반박하려고 소개한 통념을 필자의 주장인 것처럼
  미언급인데 그럴듯             지문과 모순은 아니지만 아예 언급되지 않은 상식적 진술

{axis_rule}
[쓰지 말아야 할 두 가지 — 반드시 지키세요]
  · **부분 일치 + 한 요소만 왜곡 금지** — 나머지는 다 맞는데 숫자·기간·대상 하나만
    살짝 바꿔 놓는 방식. 예: '수만 년' 을 '수백 년' 으로.
  · **정도·빈도 과장 금지** — '~하기도 한다' 를 '늘·오직·반드시·모든' 으로 키우는 방식.
  둘 다 글을 이해했는지가 아니라 눈썰미를 재는 함정입니다. 이해한 학생도 놓치고 대충
  읽은 학생도 운으로 피해서 실력을 가르지 못합니다. X 는 '읽고 따져 봐야 아는' 것으로만
  만드세요.

[why 쓰는 법] 모두 한국어로.
- O: 지문의 어느 문장에 근거하는지(원문 표현을 짧게 인용).
- X: 지문은 무엇이라 했는데 진술의 '어느 부분'이 왜 어긋나는지.
- **축 이름은 why 안에 쓰지 마세요.** axis 필드에만 적으면 조판기가 붙여 줍니다
  (같은 말을 두 번 쓸 필요가 없고, 표기도 늘 같아집니다).

[확실성] O 는 지문과 '완전히' 일치해야 하고(과장·축소 없이), X 는 지문의 특정 문장과
'확실히' 어긋나거나 지문에 없어야 합니다. 판정이 갈릴 여지가 있으면 안 됩니다.

{ctx}
"""

# 재료가 넉넉한 지문 — O 넷을 서로 다른 사실에서 뽑을 수 있다.
_O_RULE_STRICT = """- **O 4개(판마다 2개)는 서로 다른 사실이어야 합니다.** 한글판이 A·B 를 O 로 물었다면
  영어판은 C·D 를 O 로 무세요. O 는 '지문과 일치한다'는 같은 사실이라, 두 언어로 쓰면
  그대로 번역이 되어 한 판을 푼 학생이 옮겨 적습니다.
- **X 는 두 판이 같은 대목을 써도 됩니다.** 한글판이 어느 문장을 '인과 역전'으로
  비틀고 영어판이 같은 문장을 '조건 삭제'로 비틀면, 판정 근거가 달라 서로 다른
  문제입니다. 옮겨 적을 수 없습니다.
  · 다만 **한 판 안에서는** 되도록 서로 다른 대목을 비트세요(같은 문장만 여덟 번
    비틀면 나머지 지문을 읽지 않아도 풀립니다).
  · 두 판의 X 를 억지로 다른 대목에 배정하려 하지 마세요. 지문 하나에서 판정 가능한
    사실은 열댓 개뿐이라, 열여섯 개를 다른 대목에 흩으려 하면 지문에 없는 이야기를
    지어내게 됩니다.
"""

# 짧은 지문 — 서로 다른 사실이 넷이나 나오지 않는다.
_O_RULE_SHARED = """- 한글판과 영어판은 **서로 다른 사실**을 묻는 것이 원칙입니다. 영어판은 한글판의
  번역이 아닙니다 — 같은 문장을 두 언어로 내면 한 판을 푼 학생이 그대로 옮겨 적습니다.
- **다만 이 지문은 낱말이 {w}개로 짧습니다.** O 로 쓸 만한 '눈에 덜 띄는 세부 사실'이
  넷이나 나오지 않을 수 있습니다. 그럴 때는 두 판의 O 가 같은 문장에 기대도 됩니다.
  대신 **묻는 각도가 완전히 달라야** 합니다.
  · 한 판이 그 문장의 '무엇이 무엇을 한다'를 물었다면, 다른 판은 '어떤 조건에서'나
    '그래서 어떻게 되는가'를 무세요.
  · 두 진술을 나란히 놓았을 때 한쪽을 번역하면 다른 쪽이 되는 관계면 안 됩니다.
  · 억지로 다른 사실을 지어내지는 마세요 — 지문에 없는 O 는 그 자체로 오답입니다.
"""

# 문장이 넉넉한 지문 — 여덟 축의 재료가 대체로 다 있다.
_AXIS_RULE_STRICT = """- 지문에 통념·인용이 없어 '논지·화자 뒤집기'를 쓸 자리가 마땅치 않으면, 필자가 글을
  맺는 태도(낙관·경계·유보)를 반대로 세우면 됩니다. 그래도 어려우면 그 한 자리만
  다른 축으로 채우고 axis 에 그 축 이름을 적으세요 — 억지로 만든 진술보다 낫습니다.
"""

# 짧은 지문 — 여덟 축의 재료가 다 있지 않다. 없는 축은 지어내지 말고 대체하게 한다.
_AXIS_RULE_RELAXED = """- **이 지문은 낱말이 {w}개로 짧아 위 여덟 축의 재료가 다 있지는 않습니다.**
  인과 관계가 없는 지문에서 '인과 역전'을, '이론상·~할 때에는' 같은 단서구가 없는
  지문에서 '조건 삭제'를, 통념·인용이 없는 지문에서 '논지·화자 뒤집기'를 만들어 내면
  지문에 근거가 없는 진술이 되어 **정답 시비가 납니다**.
  · 지문에 재료가 있는 축부터 쓰세요.
  · 재료가 없는 축은 **건너뛰고 '미언급인데 그럴듯'으로 채우세요**(한 판에서
    최대 {fill}회까지. axis 에도 '미언급인데 그럴듯'이라고 적습니다).
  · 없는 축을 지어내는 것보다 이쪽이 낫습니다. 채운 진술도 '지문에 없다'는 근거가
    분명하므로 정답은 확실합니다.
"""


def generate_pair(client: ClaudeClient, analysis: Analysis, body: str,
                  max_retries: int = 1, passage_index: int = 0,
                  variant_hint: str = "") -> dict[str, tuple[str, str, list[str]]]:
    """한 번의 호출로 한글판·영어판 두 문항을 만든다.

    두 판이 서로 다른 사실을 물어야 하므로 한 번에 만든다. 따로 부르면 같은 사실을
    두 번 묻게 되고(모델은 다른 호출에서 무엇을 물었는지 모른다), 호출도 두 배가 된다.
    """
    words = passage_words(analysis.sentences)
    n_ko, n_en = ox_sizes(analysis.sentences)
    # 재료를 세는 자는 낱말 수다(schemas 의 주석 참고 — 문장 수는 명제 수와 어긋난다).
    shared_o = words < OX_WORDS_SHORT     # O 넷을 서로 다른 명제로 뽑을 수 없다
    relaxed_axes = words < OX_WORDS_THIN  # 여덟 축의 재료가 다 있지 않다
    fill = _FILL_ALLOWANCE if relaxed_axes else 0

    prompt = _PROMPT.format(
        n_ko=n_ko, n_en=n_en, n_true=N_OX_TRUE,
        x_ko=n_ko - N_OX_TRUE, x_en=n_en - N_OX_TRUE,
        o_rule=(_O_RULE_SHARED.format(w=words) if shared_o else _O_RULE_STRICT),
        axis_rule=(_AXIS_RULE_RELAXED.format(w=words, fill=fill)
                   if relaxed_axes else _AXIS_RULE_STRICT),
        ctx=context(analysis),
    )

    def _chk(out: ContentOXOut) -> None:
        # 개수는 지문 길이에 따라 달라지므로 스키마가 '8 또는 10'까지만 본다.
        # 이 지문에 요구한 정확한 수는 여기서 확인한다(어긋나면 재시도 안내에 실린다).
        for label, items, want in (("한글판", out.korean, n_ko),
                                   ("영어판", out.english, n_en)):
            if len(items) != want:
                raise ValueError(f"{label} 진술이 {len(items)}개입니다 — 이 지문은 낱말이 "
                                 f"{words}개이므로 정확히 {want}개여야 합니다.")
        # 쓰지 않기로 한 두 함정은 되돌린다 — 문항의 값을 깎는 결함이고 드물게 나온다.
        bad = shape.check_ox_axes([it.why for it in out.korean + out.english]
                                  + [it.axis for it in out.korean + out.english])
        # 영어판 O 가 지문을 그대로 베끼면 학생이 읽지 않고 O 로 찍는다 — 이 유형이
        # 재려는 것이 통째로 무너지므로 되돌린다(한글판은 언어가 달라 잴 수 없다).
        bad += shape.check_ox_copied([it.text for it in out.english],
                                     [it.is_true for it in out.english],
                                     analysis.sentences)
        if bad:
            raise ValueError("내용 O/X 설계 결함 — " + " ".join(bad))

    out: ContentOXOut = client.structured(
        system=SYSTEM,
        prompt=((variant_hint + "\n" if variant_hint else "") + prompt),
        cache_prefix=context(analysis),
        model_cls=ContentOXOut,
        max_tokens=6000,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    # 축 이름의 표기 흔들림('조건삭제' ↔ '조건 삭제')을 표의 표기로 되돌린다. 표에 없는
    # 이름은 빈 문자열이 되어 알약을 달지 않는다 — 틀린 이름을 인쇄하느니 안 다는 편이
    # 낫고, 문항 자체는 멀쩡하므로 다시 만들지 않는다(shape.normalize_ox_axis 참고).
    for it in out.korean + out.english:
        it.axis = shape.normalize_ox_axis(it.axis)

    seed = answer_spread.seed_of(analysis.title)
    res: dict[str, tuple[str, str, list[str]]] = {}
    for version, (slot, items) in enumerate(((CONTENT, out.korean),
                                             (CONTENT_2, out.english))):
        placed = answer_spread.place_ox(
            items,
            answer_spread.ox_positions(passage_index, version, seed, n=len(items)))
        q, a = B.make_content_ox(analysis.sentences,
                                 [it.text for it in placed],
                                 [it.is_true for it in placed],
                                 [it.why for it in placed],
                                 axes=[it.axis for it in placed])
        # 축이 겹쳤는지는 검토 메모로만 남긴다(다시 만들지 않는다 — 위 머리말 참고).
        # 짧은 지문에서 '채우라고 시킨' 겹침은 결함이 아니므로 세지 않는다.
        res[slot] = (q, a, shape.check_ox_axis_coverage(
            [it.axis for it in placed], allow_repeat=fill))
    return res


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, difficulty: str = "",
             answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    """한글판 하나만 필요할 때(옛 경로 호환). 통합본은 generate_pair 를 쓴다."""
    return generate_pair(client, analysis, body, max_retries=max_retries,
                         variant_hint=variant_hint)[CONTENT]
