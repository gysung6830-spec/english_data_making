"""단일 유형 산문 워크시트 LLM 프롬프트.

한 지문을 문장 단위로 두고, 같은 지문에 대해 네 가지 단일 유형 표기를 한꺼번에 생성한다.
  - 어법 양자택일(grammar)  : 시험에 나올 만한 '모든' 어법을 [ A / B ] 로
  - 어형 변형(form)          : '모든' 동사·준동사·동명사를 (원형) + 빈칸으로
  - 어휘 양자택일(vocab)     : 시험에 나올 만한(반의어 내기 좋은) 어휘를 [ 원문 / 반의어 ] 로
  - 한글 해석 연습(translate): 표기 없이 원문만 (작성칸은 렌더가 그림)
응답은 구조화 JSON(LLMProsePack)으로 강제한다.
"""
from __future__ import annotations

SYSTEM = (
    "당신은 한국 고등학교 영어 내신 워크북 출제 전문가다. "
    "주어진 영어 지문 하나로 '단일 유형 산문 워크시트' 데이터를 만든다. "
    "지문을 문장 단위로 나누고, 각 문장에 대해 어법·어형·어휘 세 가지 유형의 인라인 표기를 "
    "'같은 원문 문장' 위에 각각 따로 만든다. 요청된 JSON 스키마에 정확히 맞는 JSON 으로만 응답한다."
)

_RULES = """[문장 완전성 — 매우 중요]
- 지문을 '마침표(.)/물음표(?)/느낌표(!)' 기준의 온전한 문장 단위로만 나눈다. 절·구로 쪼개거나
  문장의 앞부분(주어·도입부)을 생략하지 말 것. en 과 각 template 은 그 문장의 '첫 단어부터 끝
  문장부호까지' 원문을 한 글자도 빠뜨리지 않고 담는다(자리표시자로 바뀐 부분만 예외).
- 지문의 모든 문장을 등장 순서대로 빠짐없이 낸다.

[세 가지 인라인 표기를 문장마다 각각 만든다]
공통: 각 표기용 문장(grammar_template / form_template / vocab_template)은 '원문 문장 그대로'이며,
표기할 자리에만 {{P1}}, {{P2}} … 자리표시자를 넣는다. 자리표시자 자리에는 원래 단어를 넣지 말고
{{Pn}} 만 둔다. id 는 각 문장·각 유형 안에서 P1, P2 … 로 붙인다(문장이 바뀌면 다시 P1 부터).
각 유형의 items 는 그 유형 template 의 {{Pn}} 과 '정확히 1:1'로 대응한다.

1) 어법 양자택일(grammar) → display = "[ A / B ]", 정답 하나.
   ★ 그 문장에서 '시험에 나올 만한 모든 어법 포인트'를 빠짐없이 출제한다(한 문장에 여러 개 가능).
     대상: 관계사(who/which/that/what, 관계대명사 vs 관계부사), 접속사 that vs what,
           수일치(단·복수 동사), 시제, 태(능동/수동), to부정사 vs 동명사, 분사(-ing/-ed),
           대명사 격·수(it/itself, they/them), 병렬, 비교·도치 등 어법상 혼동되는 지점 전부.
   오답 B 는 '유의어'가 아니라 '문법적으로 혼동되는 것'을 넣는다.
   display 예: "[ that / what ]"   answer 예: "that"
2) 어형 변형(form) → display = "(원형)", 정답은 문맥에 맞게 변형한 최종 형태.
   ★ 그 문장에 나오는 '모든 동사·준동사·동명사'를 빠짐없이 (원형)으로 제시한다.
     정동사(be·have 포함), to부정사, 동명사, 현재/과거분사(분사구문 포함)를 전부 대상으로 한다.
     어형 변화가 필요 없어 원형 그대로가 답인 경우도 그대로 낸다(예: 조동사 뒤 원형).
   ★ 조동사가 결합된 동사구(have been, has been, had been, is being 등)는 조동사를 따로 나누지 말고
     대표 동사원형 하나로만 낸다. 특히 'have been'류는 '(be) 하나로만' 내고 정답을 완료형 전체로 쓴다.
     예: "have been related" → "(be)" answer "have been" + 뒤에 "(relate)" answer "related".
   display 예: "(understand)"   answer 예: "understood"   /   display 예: "(produce)" answer 예: "producing"
3) 어휘 양자택일(vocab) → display = "[ 원문 / 반의어 ]", 정답은 원문 어휘.
   ★ '시험에 나올 만한' 어휘, 특히 '반의어를 내기 좋은'(대조가 뚜렷한) 내용어만 선별한다.
     아주 흔하거나 기능어성인 것, 반의어가 애매한 것은 제외. 한 문장에 여럿이면 핵심만.
   오답은 그 어휘의 '반의어(문맥상 반대 의미)'를 넣는다.
   display 예: "[ conservative / progressive ]"   answer 예: "conservative"
   ★ 원문·반의어 순서는 매 문항 무작위로 섞어라(원문을 항상 앞에 두지 말 것).

[한글 해석 연습(translate)] 은 별도 표기가 없다. en(원문)과 ko(정확한 한국어 해석)만 있으면 된다.

[출력 형식 — JSON]
{title, subtitle, sentences:[{
   no, en(원문 그대로), ko(자연스러운 한국어 해석),
   grammar_template, grammar_items:[{id,display,answer}],
   form_template,    form_items:[{id,display,answer}],
   vocab_template,   vocab_items:[{id,display,answer}]
}]}
- en 은 자리표시자 없는 '완전한 원문'이다(한글 해석 연습·정답 근거로 쓰인다).
- 어떤 유형에서 그 문장에 출제할 것이 없으면 해당 template = en 그대로, items = [] 로 둔다.
- 다른 말 없이 JSON 만 출력한다."""


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


def prose_prompt(title: str, body: str, ko: str = "") -> str:
    from .textutil import STYLE_GUIDE

    return (
        "아래 영어 지문으로 '단일 유형 산문 워크시트' 데이터를 만든다.\n\n"
        + _RULES
        + "\n\n"
        + STYLE_GUIDE
        + "\n\n"
        + _passage_block(title, body, ko)
    )
