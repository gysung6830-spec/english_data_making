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

_RULES = """[다섯 가지 출제 유형] — 아래는 '출제 우선순위' 순서다(위일수록 먼저 채운다).
1) 특수구문(type=order) — ★최우선. 어구를 뒤섞어 순서를 배열하게 한다.
   핵심 대상: 강조구문(It is ~ that) · 도치(부정어 도치·장소부사구 도치·so/neither+동사+주어) · 가정법.
   (문장에 이런 특수구문이 있으면 반드시 1개 출제한다. 없으면 간접의문문·비교구문(as~as, 비교급+than)도
    특수구문으로 낼 수 있다.)
   대소문자·구두점을 살려 슬래시로 구분해 제시하며, 표기는 반드시 〈 … 〉 로 감싼다.
   display 예: "〈 how / the current medical environment / each type of user / experiences 〉"
   answer 예: "how each type of user experiences the current medical environment"
2) 어형변형: 동사·준동사(type=verb) → (동사원형)을 주고 문맥에 맞게 어형 변화시킨다.
   ★ '한 문장에 2개'를 목표로 낸다(문장에 동사·준동사가 2개 이상이면 2개, 1개뿐이면 1개).
   ★ '준동사(to부정사·동명사·분사) 위주'로 고른다. 준동사가 있으면 그것을 먼저 낸다.
     준동사가 부족하면 시제·태(수동)·수일치 판단이 헷갈리는 정동사로 채운다.
   ★★★ 완료형(had/have/has+p.p.), 수동태(be+p.p.), 진행형(be+-ing), 완료수동(have/had been+p.p.) 처럼
     '조동사 + 본동사'로 된 동사구는 — 조동사(be·have·had 등)를 '문장에 남기거나 미리 채워 두지 말고' —
     '본동사 원형 하나'만 (원형)으로 제시한다. 동사구 전체(조동사·사이 부사 포함)를 지우고 자리표시자 하나만
     두며, 정답에는 '조동사까지 포함한 완성된 동사구 전체'를 쓴다. 절대 두 칸으로 쪼개지 말 것.
       "was found" → "(find)" / "was found"      "had destroyed" → "(destroy)" / "had destroyed"
       "were covered" → "(cover)" / "were covered"   "were hanging" → "(hang)" / "were hanging"
       "have been related" → "(relate)" / "have been related"   ('(be)'+'(relate)' 로 쪼개지 말 것)
     ★ 금지: "was (find)", "had (destroy)" 처럼 조동사를 문장에 남기는 것 / (have)+(be) 처럼 둘로 쪼개는 것.
   판단: to부정사/동명사/분사, 태(능동/수동), 수일치, 시제, 조동사 뒤 원형, 정동사 vs 준동사.
   display 예: "(react)"  answer 예: "react"  /  display 예: "(produce)" answer 예: "producing"
3) 형용사·부사(type=adj) → [ 원문 / 유의어 / 반의어 ] 3개를 섞어 제시하고 문맥상 알맞은 것을 고르게 한다.
   ★ 유의어/반의어 대비가 뚜렷하고 어휘 학습 가치가 있는 핵심 형용사·부사를 고른다.
   ★ 단, 동사에서 나온 '분사'(현재분사 -ing, 과거분사 -ed; 예: extended, using, perceived, failed)는
     형용사처럼 쓰여도 '형용사(adj)'로 내지 말고, 반드시 '동사·준동사(verb)'로 보아 (원형)으로 출제한다.
   원문과 유의어는 뜻이 통해 '둘 다 정답'이고, 반의어(문맥상 반대 의미) 하나만 오답이다.
   그러므로 answer 에는 원문과 유의어를 함께(슬래시로 구분해) 적는다.
   ★★ answer 는 '문맥에 실제로 맞는 보기'와 '정확히' 일치해야 한다(개수 무관하게 정직하게):
     - 마땅한 유의어가 없는 단어면 억지로 유의어를 만들지 말고 '정답 1개 + 반의어/부적절어 2개'로 낸다.
       이때 answer 에는 문맥에 맞는 그 1개만 적는다.
       예: 원문이 'insufficient'(충분치 않은)면 [ sufficient / insufficient / adequate ] → answer "insufficient"
           (sufficient·adequate 는 둘 다 반대 의미라 오답. 이 경우 answer 에 유의어를 넣지 않는다.)
     - 반대로, 문맥에 맞는 보기를 answer 에서 빠뜨리거나, 문맥에 안 맞는 보기를 answer 에 넣지 말 것.
     - '유의어'를 오답 자리에 두지 말 것(정답이 되어 버림).
   ★ 세 보기의 '순서를 매 문항 무작위로 섞어라'. 원문을 항상 첫 번째에 두지 말 것(뻔해지지 않게).
   display 예: "[ scarce / ample / sufficient ]"  answer 예: "sufficient / ample"  (scarce = 반의어·오답)
4) 연결사(type=conj) → [ A / B ]로 문맥 흐름에 맞는 것을 고르게 한다.
   오답은 '논리 방향이 반대인 연결어'로 넣는다(첨가/유사 ↔ 대조, 인과 ↔ 양보).
   ★ 'rather than / instead of / other than / as ~ as' 같은 비교·병렬·대조 표현의 선택은
     '관계사(rel)가 아니라 연결사(conj)'로 분류한다(관계사·격과 무관하므로).
   display 예: "[ However / Similarly ]"  answer 예: "However"  /  "[ rather than / other than ]" answer "rather than"
5) 관계사(type=rel) → [ A / B ]로 어법상 알맞은 것을 고르게 한다.
   오답은 유의어가 아니라 '문법적으로 혼동되는 것'(격, 관계대명사 vs 관계부사, that vs what, 지시대명사 수).
   대상: 관계사(who/which/that/what/where/when/whose) · that vs what · 접속사 vs 관계사 · 지시대명사 수.
   (가정법·도치·비교는 특수구문(order)으로, 태·준동사·수일치·시제는 동사(verb)로 이미 출제되므로 rel 에서 빼되,
    관계사·that/what·지시대명사는 rel 로 낸다.)
   ★★ '관계사/접속사 그 자리 자체'만 [ ]로 바꾼다. 문장의 '본동사(정동사)'를 [ ]로 바꾸거나 삭제하지 말 것 —
     각 절에는 반드시 동사가 남아 있어야 한다. (오류 예: "behaviour that {{Qn}} them apart" 처럼 본동사 sets 를
     [that/what] 로 없애면 '문장에 동사가 사라져' 안 됨. 올바른 예: 관계사 that 을 시험하려면
     "behaviour {{Qn}} sets them apart" 처럼 관계사 자리만 바꾸고 동사 sets 는 그대로 둔다.)
   ★ 이미 문장에 있는 관계사(that·which 등)를 그대로 둔 채 그 '바로 옆'에 또 [ ]를 만들지 말 것(이중 표시 금지).
   display 예: "[ which / where ]"  answer 예: "which"

[출제 원리 — 매우 중요]
★★ [절대 규칙] '모든 문장'은 반드시 '최소 1개' 이상의 문항({{Qn}})을 낸다 — questions 가 빈 문장은
   절대 허용하지 않는다. 아무리 짧거나 단순한 문장이라도 아래 우선순위로 훑어 '최소 1개'는 무조건 낸다
   (동사가 있으면 어형변형, 형용사·부사, 전치사·연결어, 관사·수, 대명사(one/it/this) 등 무엇이든 1개).
★ 모든 문장은 '기본 3개, 최대 5개'의 문항을 목표로 한다.
   - 어떤 문장이든 아래 '우선순위(채우는 순서)'로 훑어 되도록 3개를 발굴한다.
   - 출제 요소가 정말 빈약한 아주 짧은 문장은 3개 미만이 될 수 있으나, '0개(빈 문장)는 절대 안 된다' —
     최소 1개는 반드시 낸다.
★ 한 문장에서 문항을 고르는 우선순위(위에서부터 채운다):
     1순위 특수구문(order): 강조구문·도치·가정법이 있으면 반드시 1개.
     2순위 어형변형(verb): 준동사 위주로 2개.
     3순위 형용사·부사(adj): 대비가 뚜렷한 핵심 1개.
     4순위 연결사(conj): 논리 흐름 연결어가 있으면 1개.
     5순위 관계사(rel): 관계사·that/what·지시대명사 등 1개.
   → 위에서부터 채워 3~5개를 만든다. 후보가 5개를 넘으면 '우선순위가 낮은 것부터' 버려 5개로 맞춘다.
   → 특수구문·연결사·관계사가 그 문장에 없으면 건너뛰고, 어형변형(2)+형용사부사 등으로 최소 3개를 채운다.
★ [지문 전체 커버리지] 한 지문 안에서 다섯 유형(order·verb·adj·conj·rel)이 '각각 최소 1번'은
   나오도록 한다. 어떤 유형이 특정 문장에 없으면, 그 유형이 존재하는 다른 문장에서 반드시 발굴해
   지문 전체로 5종을 모두 채운다(해당 요소가 지문 어디에도 정말 없을 때만 예외).
※ 대명사 지칭(ref) 유형은 통합 카드에서 내지 않는다(지칭은 별도 워크시트가 담당한다).

[문장 완전성 — 매우 중요]
- 지문을 '마침표(.)/물음표(?)/느낌표(!)' 기준의 온전한 문장 단위로만 나눈다. 절·구 단위로
  쪼개지 말 것. 한 문장을 여러 조각으로 분할하거나, 문장의 앞부분(주어·도입부 등)을 생략하지 말 것.
- 각 en_template 은 해당 문장의 '첫 단어부터 끝 문장부호까지' 원문을 '한 글자도 빠뜨리지 말고'
  그대로 담는다(자리표시자로 바뀐 부분만 예외). 예: "Conservation aims to keep an object in its
  present state, to {{Q1}} it from change, ..." 처럼 문장 첫머리부터 포함한다.
  ★ 자리표시자로 바꾸지 않는 단어(부사·수식어 등)도 하나도 빠뜨리지 말 것.
    예: "They quickly posted the picture" 에서 post 를 낼 때 부사 'quickly' 를 빠뜨리지 말고
    "They quickly {{Q1}} the picture" 로 남긴다(quickly 유지).
    ※ 단, '조동사+본동사' 동사구(have been closely related, was recently rescued 등)를 (원형) 한 칸으로
      낼 때는 그 동사구 '전체'(조동사·사이 부사 포함)를 지우고 정답에 담는다:
      "have been closely related" → "(relate)" 정답 "have been closely related".
  ★ 자리표시자를 넣고 남은 문장은 '반드시 문법적으로 온전'해야 한다. 특히 각 절의 '본동사'가
    자리표시자로 사라져 문장에 동사가 없어지는 일이 없도록 한다(관계사·연결사 문항을 만들 때 흔한 실수).
  ★★ [자리표시자 = 원문에서 그 어구를 '뺀' 자리] {{Qn}} 은 '테스트할 그 어구가 원래 있던 바로 그 위치'에
     놓고, 그 어구는 문장 본문에서 '완전히 제거'한다. 아래 두 실수를 절대 하지 말 것:
     (가) 중복: 배열(order) 〈 〉 로 낼 어구를 문장 본문에도 그대로 남기면 안 된다.
         금지 예: "estimate how long a resource {{Q}}"(={{Q}}=〈how long a resource would last〉)
                 → 'how long a resource' 가 본문·보기에 '두 번' 나와 중복.
         올바른 예: "estimate {{Q}}"(={{Q}}=〈how/long/a/resource/would/last〉).
     (나) 이동·소실: 접속사·연결사(conj)를 낼 때는 '그 접속사의 원래 자리'에 {{Qn}}을 놓는다.
         문장 맨 앞 접속사(Although 등)를 테스트하려면 그 '맨 앞'에 {{Qn}}을 두고, 문장 끝의 다른
         단어(resolved 등)를 지워 그 자리에 넣지 말 것.
         금지 예: "Although team members … want their ideas considered and {{Q}}"(정답 Although)
                 → 앞의 Although 는 그대로 두고 끝의 resolved 를 지워 옮긴 오류.
         올바른 예: "{{Q}} team members … want their ideas considered and resolved."(정답 Although)
   ※ 요약: 자리표시자를 뺀 나머지 문장은 원문과 '한 단어도 다르지 않게'(추가·중복·삭제·이동 없이) 같아야 한다.
- 지문의 모든 문장을 '등장 순서대로 빠짐없이' 낸다. 그리고 '모든 문장'은 questions 에 '최소 1개'의
  문항을 반드시 담는다(빈 배열 금지 — 위 [절대 규칙] 참조). 정말 뽑을 게 없어 보이는 문장도
  동사 어형·형용사/부사·전치사·대명사 중 하나로 최소 1문항을 만든다.

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
다른 말 없이 JSON 만 출력한다. type 값은 order / verb / adj / conj / rel 중 하나다(ref 는 통합 카드에서 쓰지 않는다).
각 문장은 최소 3개(최대 5개)의 questions 를 담고, 지문 전체로 다섯 유형이 모두 한 번 이상 나오게 한다."""


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
