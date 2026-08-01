"""영작 워크북 LLM 프롬프트.

한 지문을 문장 단위로 두고, 각 문장에서 '학생이 한글→영어로 옮길 때 자주 틀리는
영작 포인트 어구'만 골라 그 자리에서만 어순을 배열하게 한다(문장 전체 배열이 아님).
응답은 구조화 JSON(LLMWritingPack)으로 강제한다.
"""
from __future__ import annotations

SYSTEM = (
    "당신은 한국 고등학교 영어 내신 서술형(영작) 출제 전문가다. "
    "주어진 영어 지문 하나로 '영작 포인트 배열' 워크북 데이터를 만든다. "
    "문장 전체를 배열시키는 것이 아니라, 한 문장에서 학생이 한글을 영어로 옮길 때 "
    "'어순·구조에서 자주 틀리는 핵심 어구'만 골라 그 자리에서만 배열하게 한다. "
    "요청된 JSON 스키마에 정확히 맞는 JSON 으로만 응답한다."
)

_RULES = """[출제 원리 — 무엇을 '영작 포인트'로 뽑는가]
핵심: '우리말만 보고 영어로 옮길 때 어순·구조에서 오답이 나기 쉬운 어구'만 뽑는다.
단어 하나가 아니라 어순이 꼬이는 '어구 덩어리(보통 3~5개 조각)'를 뽑아 그 안에서만 순서를 섞는다.

아래 우선순위로 문장마다 선별한다(위일수록 우선):
 1) 특수구문 — 부분부정(not every), 도치(much less …), 비교(as~as / 비교급+than), 강조·가정법
    예: Not every living thing / much less alter themselves
 2) 준동사 구조 — to부정사·동명사·분사구(위치·형태를 헷갈림)
    예: compared to the constraints of inheritance
 3) 관계사·접속사 절의 어순 — 간접의문문/관계절에서 주어·동사 순서
 4) 수식어 위치 — 빈도부사·정도부사 등(do not perfectly match 의 perfectly 위치)
 5) 연어·관용 전치사구 — regardless of, compared to, in terms of 등 덩어리 표현
 6) 어순이 우리말과 크게 다른 곳 — 동사+목적어+전치사구, 재귀대명사 위치 등
    예: to impose itself on the surroundings

[뽑지 말 것]
- 주어·관사·단순 SVO 처럼 어순이 뻔한 곳(배열 문제로 가치 없음).
- 섞을 게 없는 1~2단어짜리 자명한 구, 고유명사·숫자 나열.

[한 문장당 개수 — 매우 중요]
- 문장에 영작 포인트가 여러 개면 '모두 출제'하되, 한 문장당 박스는 '최대 2개'까지만 만든다.
- 포인트가 3곳 이상이면 위 우선순위가 높은 2개만 고른다.
- 포인트가 1곳뿐이면 1개만, 뚜렷한 포인트가 없으면 그 문장은 items 를 비운다(억지로 만들지 말 것).

[각 박스(영작 포인트)의 구성]
- template: 그 문장을 '원문 그대로' 두되, 영작 포인트 자리에만 {{A1}}, {{A2}} 를 넣는다.
  (한 문장에 최대 A1, A2 까지. 자리표시자 자리에는 원래 어구를 넣지 말고 {{An}} 만 둔다.)
- items[].chunks: 그 자리에 들어갈 '바른 순서'의 조각 배열(3~5개 권장). 조각은 단어 또는
  짧은 청크(예: "compared", "to", "the constraints", "of inheritance"). 조각을 '바른 순서대로'
  담는다. 실제 화면에 보일 뒤섞인 보기는 코드가 이 chunks 를 무작위로 섞어 만든다.
- items[].answer: 조각을 바르게 이어 붙인 '정답 어구'(대소문자·구두점 포함). 문두면 첫 글자 대문자.
- 대소문자·구두점은 정답 기준으로 유지한다(문장부호는 template 쪽에 두고 answer 에는 어구만 담아도 됨).

[문장 완전성]
- 지문을 '마침표(.)/물음표(?)/느낌표(!)' 기준의 온전한 문장 단위로 나눈다. 절·구로 쪼개거나
  앞부분(주어·도입부)을 생략하지 말 것.
- template 은 그 문장의 '첫 단어부터 끝 문장부호까지' 원문 그대로에 {{An}} 만 삽입한 것이다.
- 지문의 모든 문장을 등장 순서대로 빠짐없이 sentences 에 담는다(포인트가 없어도 문장은 싣고 items=[]).
- ko 에는 그 문장의 자연스러운 한국어 해석을 넣는다(영작의 길잡이). 입력에 해석이 있으면 그대로 쓴다.

[출력 형식 — JSON]
{title, subtitle, sentences:[{no, ko, template, items:[{id, chunks:[...], answer}]}]}
- 다른 말 없이 JSON 만 출력한다."""


def writing_prompt(title: str, body: str, ko: str = "") -> str:
    from .textutil import sentence_list_block, STYLE_GUIDE

    block = f"[지문 제목] {title}\n\n[지문 본문]\n{body}"
    if ko and ko.strip():
        block += f"\n\n[해석]\n{ko.strip()}"
    else:
        block += "\n\n[해석] (없음 — 문장별로 자연스러운 한국어 해석을 직접 생성해 ko 에 넣을 것)"
    slb = sentence_list_block(body)
    if slb:
        block += "\n\n" + slb
    return (
        "아래 영어 지문으로 '영작 워크북' 데이터를 만든다.\n\n"
        + _RULES + "\n\n" + STYLE_GUIDE + "\n\n" + block
    )
