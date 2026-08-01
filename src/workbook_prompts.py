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
   ★ 지문에 나오는 '모든' 동사와 준동사를 '빠짐없이' (원형)으로 제시한다.
     - 정동사(be·have 포함), to부정사, 동명사, 현재/과거분사(분사구문 포함)를 전부 대상으로 한다.
     - 예외: 특수구문(order)으로 어구 전체를 배열시키는 절 안의 동사는 그 order 문항에 포함되므로 중복 출제하지 않는다.
   ★ 조동사가 결합된 동사구(완료·수동·진행: have been, has been, had been, is being, will be 등)는
     각 조동사를 '따로따로 빈칸으로 나누지 말고' 대표 동사원형 하나로만 제시한다.
     특히 'have been / has been / had been' 은 '(be) 하나로만' 내고 정답을 그 완료형 전체로 쓴다.
     예: "have been closely related" → display "(be)", answer "have been"  (뒤의 related 는 별도 (relate) 문항).
     (have)+(be) 처럼 둘로 쪼개지 말 것.
   판단: 수일치, 시제, 태(능동/수동), to부정사/동명사/분사, 조동사 뒤 원형, 정동사 vs 준동사.
   display 예: "(react)"  answer 예: "react"
2) 형용사·부사(type=adj) → [ 원문 / 유의어 / 반의어 ] 3개를 섞어 제시하고 문맥상 알맞은 것을 고르게 한다.
   ★ '모든' 형용사·부사가 아니라, '시험에 나올 만한 핵심' 형용사·부사만 선별해 출제한다.
     (유의어/반의어 대비가 뚜렷하고 어휘 학습 가치가 있는 것 위주. 아주 흔하거나 기능어성인 것,
      단순 나열 속 형용사는 제외. 한 문장에 여럿이면 가장 중요한 1~2개만.)
   ★ 단, 동사에서 나온 '분사'(현재분사 -ing, 과거분사 -ed; 예: extended, using, perceived, failed)는
     형용사처럼 쓰여도 '형용사(adj)'로 내지 말고, 반드시 '동사·준동사(verb)'로 보아 (원형)으로 출제한다.
   원문과 유의어는 뜻이 통해 '둘 다 정답'이고, 반의어(문맥상 반대 의미) 하나만 오답이다.
   그러므로 answer 에는 원문과 유의어를 함께(슬래시로 구분해) 적는다.
   ★ 세 보기의 '순서를 매 문항 무작위로 섞어라'. 원문을 항상 첫 번째에 두지 말 것(뻔해지지 않게).
   display 예: "[ scarce / ample / sufficient ]"  answer 예: "sufficient / ample"  (scarce = 반의어·오답)
3) 관계사·대명사(type=rel) → [ A / B ]로 어법상 알맞은 것을 고르게 한다.
   오답은 유의어가 아니라 '문법적으로 혼동되는 것'(격, 관계사 vs 관계부사, that vs what, 지시대명사 수).
   ★ 한 문장에 어법 포인트가 여럿이면 '단일 유형 어법'과 동일한 우선순위를 따른다(위일수록 우선):
     가정법 → 도치·어순·비교 → 태(능동/수동) → 준동사 → 병렬 → 수일치 → 관계사
     → 형용사·부사 → 접속사 vs 전치사/관계사 → 시제 일치.
     (단, 이 중 가정법·도치·비교는 특수구문(order)으로, 태·준동사·수일치·시제는 동사(verb)로 이미
      출제되므로, rel 에서는 '관계사 · that/what · 접속사 vs 관계사 · 지시대명사 수'를 이 순서 기준으로 고른다.)
   display 예: "[ which / where ]"  answer 예: "which"
4) 연결사(type=conj) → [ A / B ]로 문맥 흐름에 맞는 것을 고르게 한다.
   오답은 '논리 방향이 반대인 연결어'로 넣는다(첨가/유사 ↔ 대조, 인과 ↔ 양보).
   display 예: "[ However / Similarly ]"  answer 예: "However"
5) 특수구문(type=order) → 어구를 뒤섞어 순서를 배열하게 한다.
   대상 구문: 간접의문문 / 강조구문(It is~that) / 도치 / 가정법 / 비교구문(as~as, 비교급+than).
   대소문자·구두점을 살려 슬래시로 구분해 제시하며, 표기는 반드시 〈 … 〉 로 감싼다.
   display 예: "〈 how / the current medical environment / each type of user / experiences 〉"
   answer 예: "how each type of user experiences the current medical environment"
6) 대명사 지칭(type=ref) → 지문 속 대명사·지시어(it, they, them, this, that, those 등)가
   '무엇을 가리키는지'를 고르게 한다.
   ★ 그 대명사를 '문장에 그대로 남겨 두고', 대명사 '바로 뒤'에 {{Qn}} 자리표시자를 넣는다
     (대명사를 지우고 {{Qn}} 으로 대체하지 말 것 — 그러면 문장에서 대명사가 사라진다).
   ★ display 는 '= [ 후보 / 후보 / 후보 ]' 형식이며, 대명사는 문장에 이미 있으므로 display 에는 다시 쓰지 않는다.
   ★ 아래 (1)·(2) 두 경우만 지칭으로 출제한다. 둘 다 아니면(가리킬 명사구도 없고 앞 문장을
     뜻하지도 않으면) 그 자리는 '지칭으로 내지 말 것'. 억지로 만들지 않는다.
     (1) 지문에 '명확한 명사구 선행사'가 있는 대명사(it, they, them 등)
         → 그 명사구를 정답 보기로, 지문에 나온 다른 명사구 2개를 오답 보기로 넣는다.
     (2) 지시어(this, that, it 등)가 '앞 문장(또는 앞 절) 전체의 내용'을 가리키는 경우
         → 특정 명사구 대신 정답 보기를 '앞 문장' 으로 쓴다(필요하면 '앞 문장의 내용').
   ★ 보기 규칙: 지문에 실제로 나온 명사(구)만, 원문 그대로 넣는다.
     - 괄호 주석·부연 설명을 붙이지 말 것(예: "him(the speaker)" ❌).
     - 후보로 또 다른 대명사(it/they/him 등)를 넣지 말 것((2)의 '앞 문장'만 예외).
     - 가리키는 대상이 대명사뿐이거나(he/his/him 만 이어지는 구간) 모호하면 출제하지 않는다.
   en_template 예: "..., those who resist it {{Q9}} repeat the same mistakes."  (대명사 it 뒤에 {{Q9}})
   display 예(명사구): "= [ early feedback / costly revisions / designers ]"  answer 예: "early feedback"
   display 예(앞 문장): "= [ 앞 문장 / the results / the researchers ]"  answer 예: "앞 문장"
   reason 예: "This = 앞 문장 전체의 내용을 받음"

[유형을 골고루 — 매우 중요]
- 한 지문 전체가 '동사(verb) 문항만'으로 채워지면 안 된다. 지문에 관계사·대명사, 연결사,
  특수구문(가정법·도치·비교·간접의문문·강조), 형용사·부사, 지칭 요소가 있으면 '반드시' 그 유형으로도
  출제해 6개 유형이 지문 전체에 골고루 분포하도록 한다.
- 특히 관계사(rel)·연결사(conj)·특수구문(order)·지칭(ref)은 놓치기 쉬우니 문장을 훑어보며 적극 발굴한다.
- 동사(verb)만 잔뜩 내고 다른 유형을 누락하는 것은 오류로 간주한다.

[한 문장 출제 개수 · 유형 우선순위]
- 한 문장에서 만드는 문항({{Qn}})은 '최대 5개'까지만 둔다.
- 한 문장의 출제 후보가 5개를 넘으면 아래 '유형 우선순위'가 높은 것부터 5개만 남긴다(위일수록 우선):
    1. 지칭(ref)  2. 특수구문(order)  3. 동사·준동사(verb)  4. 관계사·대명사(rel)  5. 연결사(conj)  6. 형용사·부사(adj)
- 이 상한은 verb 의 '모든 동사·준동사를 빠짐없이' 원칙보다 우선한다. 상한을 넘겨 동사를 다 담지 못하면,
  위 우선순위에 따라 취사선택한다(동사끼리 경합하면 문맥상 어형 변화가 뚜렷한 것부터).
- 단, 문항 수를 5개로 제한하더라도 '문장 자체'는 그대로 싣는다(문장을 통째로 빼지 말 것).

[문장 완전성 — 매우 중요]
- 지문을 '마침표(.)/물음표(?)/느낌표(!)' 기준의 온전한 문장 단위로만 나눈다. 절·구 단위로
  쪼개지 말 것. 한 문장을 여러 조각으로 분할하거나, 문장의 앞부분(주어·도입부 등)을 생략하지 말 것.
- 각 en_template 은 해당 문장의 '첫 단어부터 끝 문장부호까지' 원문을 '한 글자도 빠뜨리지 말고'
  그대로 담는다(자리표시자로 바뀐 부분만 예외). 예: "Conservation aims to keep an object in its
  present state, to {{Q1}} it from change, ..." 처럼 문장 첫머리부터 포함한다.
  ★ 자리표시자로 바꾸지 않는 단어(부사·수식어 등)도 하나도 빠뜨리지 말 것.
    예: "have been closely related" 를 낼 때 부사 'closely' 를 빠뜨리고 "{{Q1}} {{Q2}} related"
    처럼 쓰면 안 된다. 반드시 "{{Q1}} {{Q2}} closely related" 로 남긴다.
- 지문의 모든 문장을 '등장 순서대로 빠짐없이' 낸다. (출제할 요소가 전혀 없는 문장은 questions 를
  빈 배열로 두더라도 문장 자체는 그대로 실어 지문이 온전히 보이게 한다.)

[표기·채번 규칙]
- en_template 은 문제로 낼 자리마다 {{Q1}}, {{Q2}} … 자리표시자를 넣은 '원문 문장'이다.
  자리표시자 자리에는 원래 있던 단어를 넣지 말고 {{Qn}} 만 둔다. 나머지 문장은 원문 그대로 둔다.
- 각 문장의 questions 에는 그 문장에 등장한 {{Qn}} 과 '정확히 1:1'로 대응하는 항목만 담는다.
- id 는 문서 전체에서 Q1, Q2, Q3 … 처럼 '연속'되도록 채번한다(문장이 바뀌어도 이어서).
- 한 문장에 출제할 요소가 여러 개면 여러 문항으로 나눈다. 출제할 요소가 없어도 문장은 그대로 싣되
  questions 만 빈 배열로 둔다(문장을 통째로 빼지 말 것).
- answer 는 그 자리에 들어갈 최종 정답(어형 변화·선택·배열 결과)이다.
- reason 은 한국어 한 줄 근거다(예: "opportunity to + 동사원형", "scarce(부족한)는 문맥 반대").

[출력 형식 — JSON]
지문을 문장 단위로 나누고, 각 문장마다 {no, en_template, ko, questions:[{id,type,display,answer,reason}]} 구조로 출력한다.
다른 말 없이 JSON 만 출력한다. type 값은 verb / adj / rel / conj / order / ref 중 하나다."""


def _passage_block(title: str, body: str, ko: str = "") -> str:
    from .textutil import sentence_list_block

    block = f"[지문 제목] {title}\n\n[지문 본문]\n{body}"
    if ko and ko.strip():
        block += f"\n\n[해석]\n{ko.strip()}"
    else:
        block += "\n\n[해석] (없음 — 문장별로 자연스러운 한국어 해석을 직접 생성해 ko 에 넣을 것)"
    slb = sentence_list_block(body)
    if slb:
        block += "\n\n" + slb
    return block


def workbook_prompt(title: str, body: str, ko: str = "") -> str:
    from .textutil import STYLE_GUIDE

    return (
        "아래 영어 지문으로 '문장별 복합유형 통합 워크북'을 만든다.\n\n"
        + _RULES
        + "\n\n"
        + STYLE_GUIDE
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
