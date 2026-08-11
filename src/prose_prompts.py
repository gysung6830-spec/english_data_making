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
   ★ 그 문장에서 어법 포인트를 '문장당 최소 2개, 최대 4개' 출제한다.
     후보가 4개보다 많으면 아래 우선순위가 높은 것부터 4개만, 2개보다 적으면 최소 2개는 발굴한다
     (어법 요소가 정말 빈약한 아주 짧은 문장만 예외로 그 이하). 아래는 '선별 우선순위'다(위일수록 우선):
       1. ★태 (능동/수동) — '위주로' 출제한다. be+p.p. vs 능동, 특히 분사 -ing/-ed 의 능·수동
          (수식·분사구문 포함), have been p.p. 등 완료수동. 매 지문에서 태를 가장 많이 낸다.
       2. 가정법 (if 가정법·도치 가정법·should/were 등 동사형)
       3. 도치 · 어순 · 비교구문 (부정어 도치, 간접의문문 어순, as~as, 비교급+than)
       4. 준동사 (to부정사 vs 동명사 vs 분사)
       5. 병렬구조 (등위·상관접속사로 연결된 요소의 형태 일치)
       6. 관계사 (관계대명사 vs 관계부사, that vs what, 계속적 용법)
       7. 형용사 vs 부사 (수식 관계)
       8. 접속사 vs 전치사 / 접속사 vs 관계사 (because vs because of, that vs 관계사)
       9. 시제 일치
       10. 수일치 (주어–동사 단·복수) — ★난도가 낮아 '가급적 내지 말 것'. 다른 어법 포인트가
           정말 없을 때만 최소한으로. 단순 주어-동사 수일치만 있는 문항은 지양한다.
     ★★ '주어 수일치만' 묻는 be/do/have 선택([ was / were ], [ is / are ], [ does / do ],
        [ has / have ])은 원칙적으로 내지 말 것. 같은 be동사 자리라도 '태'(be+p.p. vs 능동, 예:
        [ were covered / covered ])나 '시제'로 물을 수 있으면 반드시 그쪽으로 낸다. 오답을 단지
        수만 바꾼 형태로 두지 말 것. (예: "His legs [ were / was ] covered" 금지 →
        "His legs [ were covered / covered ]" 로 태를 묻는다.)
     오답 B 는 위 항목에서 '문법적으로 혼동되는 것'을 넣는다(유의어 금지).
   display 예: "[ that / what ]"   answer 예: "that"
2) 어형 변형(form) → display = "(원형)", 정답은 문맥에 맞게 변형한 최종 형태.
   ★ 그 문장에 나오는 '모든 동사·준동사·동명사'를 빠짐없이 (원형)으로 제시한다.
     정동사(be·have 포함), to부정사, 동명사, 현재/과거분사(분사구문 포함)를 전부 대상으로 한다.
     어형 변화가 필요 없어 원형 그대로가 답인 경우도 그대로 낸다(예: 조동사 뒤 원형).
   ★★★ 완료형(had/have/has + p.p.), 수동태(be + p.p.), 진행형(be + -ing), 완료수동(have/had been + p.p.)
     처럼 '조동사 + 본동사'로 된 동사구는 — 조동사(be·have·had 등)를 '문장에 남기거나 미리 채워 두지 말고'
     — '본동사 원형 하나'만 (원형)으로 제시한다. 그 동사구 전체(조동사·사이에 낀 부사 포함)를 지우고
     자리표시자만 두며, 정답에는 '조동사까지 포함한 완성된 동사구 전체'를 쓴다. '한 칸(placeholder 1개)'으로만 낸다.
       "was found"        → 표기 "(find)"    정답 "was found"
       "had destroyed"    → 표기 "(destroy)" 정답 "had destroyed"
       "had planned"      → 표기 "(plan)"    정답 "had planned"
       "were covered"     → 표기 "(cover)"   정답 "were covered"
       "were hanging"     → 표기 "(hang)"    정답 "were hanging"
       "have been related"→ 표기 "(relate)"  정답 "have been related"   (be 와 relate 로 쪼개지 말 것)
       "was recently rescued" → 표기 "(rescue)" 정답 "was recently rescued"  (사이 부사도 정답에 포함)
     ★ 금지: "was (find)", "had (destroy)", "were (hang)" 처럼 조동사를 문장에 남겨 두는 것.
     ★ 금지: 하나의 동사구를 "(be)" + "(p.p.)" 처럼 '두 칸'으로 쪼개는 것.
   ★ 조동사(will/can/must/should 등) + 동사원형은 조동사를 문장에 남기고 본동사만 (원형)으로 낸다(원형이 답).
   ★★ (원형)으로 낼 동사는 '문장에서 그 동사(와 딸린 to·조동사·부사)를 지우고' 자리표시자만 남긴다.
     자리표시자 바로 옆에 같은 동사를 '또' 남겨 중복시키지 말 것.
     올바른 예: "We need to dramatically reduce our use" → form_template "We need to dramatically {{P1}} our use"
       (display "(reduce)", answer "reduce").
     금지 예: "We need {{P1}} dramatically reduce our use" (display "(to reduce)") — reduce 가 남아 중복됨.
   display 예: "(understand)"   answer 예: "understood"   /   display 예: "(produce)" answer 예: "producing"
3) 어휘 — '난도 하'와 '난도 상' 두 종류를 '모두' 만든다(같은 문장에 대해 각각).
   ★ 각 유형은 '한 문장에 최소 2개, 최대 4개'를 출제한다(어휘가 정말 부족한 아주 짧은 문장만 예외로 1개).
   공통: 각 유형 template 은 원문에 {{Pn}} 만 삽입. 보기 순서는 매 문항 무작위로 섞어라.
   ★★ {{Pn}} 은 '원래 그 단어가 있던 자리에 정확히' 놓는다. 주변 단어(주어·동사 등)를 옮기거나
     빠뜨리지 말 것. template 은 그 단어만 {{Pn}} 으로 바뀔 뿐, 나머지는 원문 문장 그대로 온전해야 한다.
     (금지 예: 원문 "The reason pessimists sound smart is that they can avoid being wrong" 에서
      avoid 를 낼 때 "The reason {{P1}} sound smart is that they can being wrong" 처럼 주어 pessimists 를
      지우거나 avoid 를 딴 데로 옮기면 안 된다. 올바른: "…is that they can {{P1}} being 'wrong'".)
   ★ template 에는 반드시 그 문장의 원문 텍스트가 담겨야 한다. 자리표시자만 달랑 넣거나(예: "{{P1}}"),
     문장을 비우지 말 것.
   ★ 각 item 에는 정답 단어의 '한글 뜻'을 gloss 에 넣는다(해설에 뜻을 함께 보여주기 위함). 필수.

   ★ 난도 하(vocab_easy) — '양자택일'(2개 중 1개):
     - display = "[ 원문 / 반의어 ]", answer = 원문(1개).
     - 비교적 쉬운 내용어 + '뜻이 뚜렷이 반대인 반의어'로 정답이 분명하게.
     - 예: display "[ increase / decrease ]" answer "increase" gloss "증가하다"
   ★ 난도 상(vocab) — '3개 중 2개 고르기':
     - 세 보기 = ① 원문 단어  ② 원문의 '유의어'(뜻이 통함)  ③ '원문과 형태(철자)가 비슷하지만 뜻이 다른 단어'.
       display = "[ A / B / C ]"(세 개를 무작위 순서로). answer = '원문 / 유의어'(정답 2개, 슬래시로 구분).
     - ★★ 오답 ③ 은 '유의어가 절대 아니어야 한다'. 원문·유의어와 뜻이 조금이라도 통하면 정답이 3개가 되어
       '출제 오류'다. 세 보기 중 뜻이 통하는 것은 '정확히 2개'뿐이어야 한다.
       금지 예: "[ different / diverse / distinct ]" — 셋 다 '다른'의 뜻 → 정답 3개 → 절대 금지.
       올바른 예: "[ different / diverse / diffident ]" (diffident=수줍은; 형태만 비슷, 뜻은 확실히 다름).
     - ③ 은 '실제 존재하는 영단어'로, 원문과 철자가 닮았으나 문맥에 넣으면 명백히 어색한 것을 쓴다.
     - gloss = 원문(=유의어)의 한글 뜻 1개.
     - 예: display "[ comprehensive / comprehensible / thorough ]"
          answer "comprehensive / thorough"  gloss "포괄적인"  (comprehensible=형태 유사 오답)
   ※ 상은 학술·추상 어휘 위주로 어렵게, 하는 쉽게 — 난이도 차이가 분명해야 한다.
4) 대명사 지칭 선택(ref) → 지문 속 대명사·지시어(it, they, them, this, that, those 등)가
   '무엇을 가리키는지'를 고르게 한다.
   ★ 지문 전체에서 '가리키는 대상이 분명한' 지시어를 '넉넉히'(가능하면 지문당 4개 이상) 찾아 출제한다.
     특히 it/this/that/which/they/them 이 '특정 명사구' 또는 '앞 문장' 을 분명히 가리키는 곳을 우선한다.
     (단, he/his/him 만 계속 이어지며 사람이 여럿이라 헷갈리는 곳은 출제하지 않는다.)
   ★★ '가주어·가목적어 it' 과 '유도부사 there' 는 '가리키는 대상이 없으므로' 절대 출제하지 말 것.
     금지 예: "It turns out that …", "It is important that …", "It takes time to …", "There is/are …".
     it 은 '특정 명사(구)를 실제로 가리킬 때'만 출제한다(예: 사진→it, 검은 재→it).
   ★★ 소유격 대명사(his/her/their/its)를 낼 때 '정답 = 그 소유격이 실제로 가리키는 소유자'여야 한다.
     특히 his/her/their 는 '사람'을 가리키므로 정답도 '사람(명사구)'이라야 한다. 소유격 뒤 사물(예: his
     battery 의 battery)이 '어느 기기의 것인지'를 정답으로 삼지 말 것 — 정답이 사물이 되면 소유격 인칭
     대명사의 지시를 잘못 잡은 출제오류다. 이런 혼동이 생기면 아예 출제하지 말 것(its 처럼 사물을 가리키는
     소유격은 사물이 정답이어도 됨).
     금지 예: "the last of his {{P1}} battery" 정답 "his cell phone" — his 는 Compean(사람)을 가리키므로 오류.
   ★ 그 대명사를 '문장에 그대로 남겨 두고', 대명사 '바로 뒤'에 {{Pn}} 자리표시자를 넣는다
     (대명사를 지우고 {{Pn}} 으로 대체하지 말 것 — 문장에서 대명사가 사라지면 안 된다).
     또한 대명사·주변 단어를 하나도 빠뜨리지 말 것(빠지면 문항이 폐기된다).
   ★ display 는 "= [ 후보 / 후보 / 후보 ]" 형식이며(보기 3개), answer 는 그 3개 중 '정확히 하나'와
     '문자 그대로 똑같이' 일치해야 한다(철자·대소문자·구두점까지). 보기에 없는 답을 쓰면 안 된다.
   [출제 오류 방지 — 매우 중요]
   ★ 정답은 '유일'해야 한다. 그 대명사가 문맥상 '한 대상만' 확실히 가리킬 때만 출제한다.
     두 개 이상으로 해석될 여지가 조금이라도 있으면 '출제하지 말 것'(items=[]).
   ★★ 오답 보기가 '정답이 될 수도 있으면' 절대 안 된다. 특히 they/them/them 이 '경찰·구조대'처럼
     둘 이상의 집단을 가리킬 수 있는 자리에서, 그 다른 집단을 오답 보기로 넣지 말 것 — 정답이 둘이 되어
     출제오류다. 그런 자리는 아예 출제하지 않는다.
     금지 예: "they = [ the local police / a rescue team / Compean ]" (경찰·구조대 둘 다 수색 주체 → 모호).
   ★★ 지시형용사 this/that/these 가 '명사를 수식'하는데 그 명사가 '이야기·보도·소식'처럼 담화 자체를
     뜻하면(this story, this report, this news) 출제하지 말 것. this/that 은 '단독 대명사로 앞 내용을
     가리킬 때'(아래 (2))만 '앞 문장' 정답으로 낸다. "this story"에 '앞 문장'을 정답으로 달지 말 것.
   ★★ 관계대명사 that/which 를 지칭으로 낼 때, 선행사가 'N1 of N2 that …'처럼 두 명사 중 어디에
     걸리는지 문법적으로 모호하면 출제하지 말 것 — 근접(N2)과 의미(N1)가 갈려 정답 시비가 난다.
     금지 예: "miniatures of crime scenes that {{P1}} were highly detailed" (that 이 miniatures인지
     crime scenes인지 불명확). 선행사가 '하나로 분명한' 관계대명사만 낸다.
   ★ '너무 자명하거나 반복적인' 문항은 넣지 말 것. 같은 사람(예: Compean)을 가리키는 his/he 지칭을
     한 지문에서 몇 번이고 반복하면 변별력이 없다 — 지칭 대상이 헷갈릴 만한 '알짜' 자리 위주로 낸다.
   ★ 오답 2개는 '지문에 실제로 나온 명사구'이되, 문맥상 그 대명사의 지시 대상이 '될 수 없는' 것이라야 한다
     (그럴듯하지만 확실히 틀린 것). 정답과 뜻이 겹치거나 함께 정답이 될 수 있는 것은 오답으로 쓰지 말 것.
   ★ 아래 (1)·(2) 두 경우만 출제한다. 둘 다 아니면 내지 않는다.
     (1) '명확한 명사구 선행사'가 있는 대명사 → 그 명사구가 정답, 다른 명사구 2개가 오답.
     (2) this/that/it 이 '앞 문장(또는 앞 절) 전체의 내용'을 가리키는 경우
         → 정답 보기를 '앞 문장' 으로 쓰고 answer="앞 문장". (보기에 '앞 문장'을 반드시 포함)
         ※ 지문의 '첫 문장'에는 앞 문장이 없으므로 '앞 문장' 정답을 쓰지 말 것.
   ★ 보기는 지문에 실제로 나온 명사(구)만 '영어 원문 그대로'. 괄호 주석 금지, 다른 대명사를 보기로 넣지 말 것
     ((2)의 '앞 문장'만 예외). 일반적 you/we/they 나 he/his/him 만 이어지는 모호한 경우는 출제하지 않는다.
   ★★ 보기에 '한글'을 넣지 말 것(오직 '앞 문장'만 예외). 대명사가 '행동·구'(예: 길 건너기 전 '양쪽 살피기')를
     가리켜 마땅한 '영어 명사구' 보기가 없으면, 그 자리는 아예 출제하지 말 것(items 에서 제외).
     금지 예: "it = [ Vision / the street / 양쪽 살피기 ]" — 한글 보기 혼입은 출제오류.
   예1(명사구): ref_template "…, those who resist it {{P1}} repeat the same mistakes."
       display "= [ early feedback / costly revisions / designers ]"  answer "early feedback"
   예2(앞 문장): ref_template "This {{P1}} explains why we adapt so quickly."
       display "= [ 앞 문장 / the euphoria / little kids ]"  answer "앞 문장"

[한글 해석 연습(translate)] 은 별도 표기가 없다. en(원문)과 ko(정확한 한국어 해석)만 있으면 된다.

[출력 형식 — JSON]
{title, subtitle, sentences:[{
   no, en(원문 그대로), ko(자연스러운 한국어 해석),
   grammar_template, grammar_items:[{id,display,answer}],
   form_template,    form_items:[{id,display,answer}],
   vocab_easy_template,  vocab_easy_items:[{id,display,answer,gloss}],   (어휘 난도 하: 2택1)
   vocab_template,       vocab_items:[{id,display,answer,gloss}],        (어휘 난도 상: 3중 2택)
   ref_template,         ref_items:[{id,display,answer}]                 (대명사 지칭 선택)
}]}
- 어휘 item 의 gloss 는 정답 단어의 한글 뜻(필수). 다른 유형 item 은 gloss 불필요.
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


# ── 대명사 지칭(ref) 전용 재생성 프롬프트 ──────────────────────────────
# 6종 통합 호출이 아주 긴 지문에서 ref 문항을 불안정하게(때때로 0개) 내는 문제를
# 보완하기 위한 '지칭만' 집중 호출. 결과는 LLMProsePack 이되 ref_template/ref_items 만 채운다.
REF_SYSTEM = (
    "당신은 한국 고등학교 영어 내신 워크북 출제 전문가다. 주어진 영어 지문에서 "
    "'대명사·지시어 지칭 선택(ref)' 문항만 집중적으로 출제한다. "
    "요청된 JSON 스키마(LLMProsePack)에 정확히 맞는 JSON 으로만 응답한다."
)

_REF_ONLY_RULES = """[대명사 지칭 선택(ref) — 이 유형만 집중 출제한다]
지문 속 대명사·지시어(it, they, them, this, that, those 등)가 '무엇을 가리키는지' 고르게 한다.
★ 지문 전체에서 '가리키는 대상이 분명한' 지시어를 '넉넉히'(가능하면 지문당 4개 이상, 최소 3개) 찾아 낸다.
  특히 it/this/that/which/they/them 이 '특정 명사구' 또는 '앞 문장' 을 분명히 가리키는 곳을 우선한다.
  (단, he/his/him 만 계속 이어지며 사람이 여럿이라 헷갈리는 곳은 출제하지 않는다.)
★★ '가주어·가목적어 it' 과 '유도부사 there' 는 '가리키는 대상이 없으므로' 절대 출제하지 말 것.
  금지 예: "It turns out that …", "It is important that …", "It takes time to …", "There is/are …".
  it 은 '특정 명사(구)를 실제로 가리킬 때'만 출제한다(예: 사진→it, 검은 재→it).
★★ 소유격 대명사(his/her/their/its)를 낼 때 '정답 = 그 소유격이 실제로 가리키는 소유자'여야 한다.
  his/her/their 는 '사람'을 가리키므로 정답도 사람(명사구)이라야 하고, 소유격 뒤 사물(예: his battery 의
  battery)이 '어느 기기의 것인지'를 정답으로 삼지 말 것. 그런 혼동이 생기면 아예 출제하지 않는다
  (its 처럼 사물을 가리키는 소유격은 사물이 정답이어도 됨).
★ 그 대명사를 '문장에 그대로 남겨 두고', 대명사 '바로 뒤'에 {{P1}} 자리표시자를 넣는다
  (대명사를 지우고 {{Pn}} 으로 대체하지 말 것 — 문장에서 대명사가 사라지면 안 된다).
  또한 대명사·주변 단어를 하나도 빠뜨리지 말 것(빠지면 문항이 폐기된다). id 는 문장마다 P1 부터.
★ display 는 "= [ 후보 / 후보 / 후보 ]" 형식이며(보기 3개), answer 는 그 3개 중 '정확히 하나'와
  '문자 그대로 똑같이' 일치해야 한다(철자·대소문자·구두점까지). 보기에 없는 답을 쓰면 안 된다.
[출제 오류 방지 — 매우 중요]
★ 정답은 '유일'해야 한다. 그 대명사가 문맥상 '한 대상만' 확실히 가리킬 때만 출제한다.
  두 개 이상으로 해석될 여지가 조금이라도 있으면 '출제하지 말 것'.
★★ 오답 보기가 '정답이 될 수도 있으면' 안 된다. 특히 they/them 이 '경찰·구조대'처럼 둘 이상의 집단을
  가리킬 수 있는 자리에서 그 다른 집단을 오답으로 넣지 말 것 — 정답이 둘이 되어 출제오류다. 그런 자리는
  아예 출제하지 않는다. 금지 예: "they = [ the local police / a rescue team / Compean ]".
★★ 지시형용사 this/that/these 가 '명사를 수식'하는데 그 명사가 '이야기·보도·소식'처럼 담화 자체를 뜻하면
  (this story, this report) 출제하지 말 것. this/that 은 '단독 대명사로 앞 내용을 가리킬 때'((2))만 낸다.
★★ 관계대명사 that/which 는 선행사가 'N1 of N2 that …'처럼 두 명사 중 어디에 걸리는지 모호하면 출제 금지
  (근접 N2와 의미 N1 이 갈려 정답 시비). 선행사가 하나로 분명한 관계대명사만 낸다.
★ '너무 자명하거나 반복적인' 문항은 넣지 말 것(같은 사람을 가리키는 his/he 반복 지양). 변별력 있는 자리 위주.
★ 오답 2개는 '지문에 실제로 나온 명사구'이되, 문맥상 그 대명사의 지시 대상이 '될 수 없는' 것이라야 한다.
★ 아래 (1)·(2) 두 경우만 출제한다. 둘 다 아니면 내지 않는다.
  (1) '명확한 명사구 선행사'가 있는 대명사 → 그 명사구가 정답, 다른 명사구 2개가 오답.
  (2) this/that/it 이 '앞 문장(또는 앞 절) 전체의 내용'을 가리키는 경우
      → 정답 보기를 '앞 문장' 으로 쓰고 answer="앞 문장". (보기에 '앞 문장'을 반드시 포함)
      ※ 지문의 '첫 문장'에는 앞 문장이 없으므로 '앞 문장' 정답을 쓰지 말 것.
★★ 보기에 '한글'을 넣지 말 것(오직 '앞 문장'만 예외). 마땅한 '영어 명사구' 보기가 없으면 그 자리는 출제하지 않는다.

[출력 형식 — JSON]
지문의 '모든 문장'을 등장 순서대로 no,en,ko 와 함께 담되, ref 문항이 있는 문장만 ref_template/ref_items 를 채운다.
{title, subtitle, sentences:[{
   no, en(원문 그대로), ko(자연스러운 한국어 해석),
   ref_template(원문에 {{Pn}} 삽입), ref_items:[{id,display,answer}]
}]}
- ref 를 낼 것이 없는 문장은 ref_template = en 그대로, ref_items = [] 로 둔다.
- 다른 유형(grammar/form/vocab)은 채우지 않는다(빈 문자열/빈 배열로 둔다).
- 다른 말 없이 JSON 만 출력한다."""


def ref_only_prompt(title: str, body: str, ko: str = "") -> str:
    from .textutil import STYLE_GUIDE

    return (
        "아래 영어 지문에서 '대명사 지칭 선택(ref)' 문항만 집중적으로 만든다.\n\n"
        + _REF_ONLY_RULES
        + "\n\n"
        + STYLE_GUIDE
        + "\n\n"
        + _passage_block(title, body, ko)
    )
