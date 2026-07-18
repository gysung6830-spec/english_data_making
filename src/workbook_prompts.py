"""문장별 복합유형 통합 워크북 LLM 프롬프트 (spec 3).

한 문장 안에서 해당하는 문법 요소가 나올 때마다 그 자리에 맞는 출제 유형을 동시에 적용한다.
응답은 구조화된 JSON(LLMWorkbook 스키마)으로 강제한다.
"""
from __future__ import annotations

SYSTEM = (
    "당신은 한국 고등학교 영어 내신 워크북 출제 전문가다. "
    "주어진 영어 지문으로 '문장별 복합유형 통합 워크북'을 만든다. "
    "핵심 원칙: 한 문장 안에서 해당하는 문법 요소가 나올 때마다 그 자리에 맞는 방식을 동시에 적용한다. "
    "요청된 JSON 스키마에 정확히 맞는 JSON 으로만 응답한다."
)

_RULES = """[다섯 가지 출제 유형]
1) 동사·준동사(type=verb) → (동사원형)을 주고 문맥에 맞게 어형 변화시킨다.
   판단: 수일치, 시제, 태(능동/수동), to부정사/동명사/분사, 조동사 뒤 원형, 정동사 vs 준동사.
   display 예: "(react)"  answer 예: "react"
2) 형용사·부사(type=adj) → [ 원문 / 유의어 / 반의어 ] 3개를 섞어 제시하고 문맥상 알맞은 것을 고르게 한다.
   원문과 유의어는 뜻이 통해 '둘 다 정답'이고, 반의어(문맥상 반대 의미) 하나만 오답이다.
   그러므로 answer 에는 원문과 유의어를 함께(슬래시로 구분해) 적는다.
   display 예: "[ sufficient / ample / scarce ]"  answer 예: "sufficient / ample"  (scarce = 반의어·오답)
3) 관계사·대명사(type=rel) → [ A / B ]로 어법상 알맞은 것을 고르게 한다.
   오답은 유의어가 아니라 '문법적으로 혼동되는 것'(격, 관계사 vs 관계부사, that vs what, 지시대명사 수).
   display 예: "[ which / where ]"  answer 예: "which"
4) 연결사(type=conj) → [ A / B ]로 문맥 흐름에 맞는 것을 고르게 한다.
   오답은 '논리 방향이 반대인 연결어'로 넣는다(첨가/유사 ↔ 대조, 인과 ↔ 양보).
   display 예: "[ However / Similarly ]"  answer 예: "However"
5) 특수구문(type=order) → 어구를 뒤섞어 순서를 배열하게 한다.
   대상 구문: 간접의문문 / 강조구문(It is~that) / 도치 / 가정법 / 비교구문(as~as, 비교급+than).
   대소문자·구두점을 살려 슬래시로 구분해 제시하며, 표기는 반드시 〈 … 〉 로 감싼다.
   display 예: "〈 how / the current medical environment / each type of user / experiences 〉"
   answer 예: "how each type of user experiences the current medical environment"

[표기·채번 규칙]
- en_template 은 문제로 낼 자리마다 {{Q1}}, {{Q2}} … 자리표시자를 넣은 '원문 문장'이다.
  자리표시자 자리에는 원래 있던 단어를 넣지 말고 {{Qn}} 만 둔다. 나머지 문장은 원문 그대로 둔다.
- 각 문장의 questions 에는 그 문장에 등장한 {{Qn}} 과 '정확히 1:1'로 대응하는 항목만 담는다.
- id 는 문서 전체에서 Q1, Q2, Q3 … 처럼 '연속'되도록 채번한다(문장이 바뀌어도 이어서).
- 한 문장에 출제할 요소가 여러 개면 여러 문항으로 나눈다. 출제할 요소가 없으면 그 문장은 넣지 않는다.
- answer 는 그 자리에 들어갈 최종 정답(어형 변화·선택·배열 결과)이다.
- reason 은 한국어 한 줄 근거다(예: "opportunity to + 동사원형", "scarce(부족한)는 문맥 반대").

[출력 형식 — JSON]
지문을 문장 단위로 나누고, 각 문장마다 {no, en_template, ko, questions:[{id,type,display,answer,reason}]} 구조로 출력한다.
다른 말 없이 JSON 만 출력한다. type 값은 verb / adj / rel / conj / order 중 하나다."""


def _passage_block(title: str, body: str, ko: str = "") -> str:
    block = f"[지문 제목] {title}\n\n[지문 본문]\n{body}"
    if ko and ko.strip():
        block += f"\n\n[해석]\n{ko.strip()}"
    else:
        block += "\n\n[해석] (없음 — 문장별로 자연스러운 한국어 해석을 직접 생성해 ko 에 넣을 것)"
    return block


def workbook_prompt(title: str, body: str, ko: str = "") -> str:
    return (
        "아래 영어 지문으로 '문장별 복합유형 통합 워크북'을 만든다.\n\n"
        + _RULES
        + "\n\n"
        + _passage_block(title, body, ko)
    )


def regenerate_sentence_prompt(title: str, body: str, s_no: int, err: str) -> str:
    """검증 실패한 특정 문장만 다시 출제할 때 쓰는 프롬프트(spec 4-2 단계 5)."""
    return (
        f"다음 지문의 {s_no}번째 문장에 대한 워크북 출제가 조건을 위반했습니다: {err}\n"
        "해당 문장 하나만 다시 출제하세요. 출력은 sentences 에 그 문장 1개만 담은 JSON 입니다.\n\n"
        + _RULES
        + "\n\n"
        + _passage_block(title, body)
    )
