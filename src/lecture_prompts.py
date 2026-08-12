"""'강의컨셉 교재(필생보)' 생성 프롬프트.

구성: ① 어휘 리스트 → ② 문장별(끊어읽기 빈칸 채우기 + 내용 객관식) → ③ 글 예측.
- 학생은 '틀리기 쉬운 부분'만 빈칸으로 채우고, 각 문장 내용을 객관식으로 확인한다.
- 문장 번호(1..n)는 코드가 매겨 프롬프트에 넣어 주고, LLM 은 그 번호를 그대로 사용한다.
- 응답은 구조화된 JSON(스키마)으로 강제한다. 지문에 실제로 있는 내용만 쓴다.
- 2단계 호출: (1) 개관(Overview) → (2) 문장별 분석(SentenceAnalysis).
"""
from __future__ import annotations

from .lecture_schemas import STANCES, STRUCTURES, LectureSentence

SYSTEM = (
    "당신은 한국 고등학교 영어 내신·수능 지문으로 '필자의 생각이 보이는 영어독해' 워크북을 "
    "만드는 전문 강사입니다. 학생이 어휘를 익히고, 각 문장에서 틀리기 쉬운 부분만 빈칸으로 채우고, "
    "문장 내용을 객관식으로 확인한 뒤, 지문 전체를 예측하도록 설계합니다. 담백하고 자연스러운 "
    "설명체를 쓰고, 지문에 실제로 있는 내용만 근거로 하며, 요청된 JSON 스키마에 정확히 맞는 "
    "JSON 으로만 응답하세요."
)


def _numbered(sentences: list[LectureSentence]) -> str:
    return "\n".join(f"{s.id} {s.text}" for s in sentences)


# 1차: 지문 전체 개관(③ 글 예측 정답) ----------------------------------------
def overview_prompt(title: str, sentences: list[LectureSentence]) -> str:
    n = len(sentences)
    return (
        f"[지문 제목] {title}\n\n"
        f"[지문 — 문장 번호가 매겨져 있음 (총 {n}문장)]\n{_numbered(sentences)}\n\n"
        "위 지문의 '글 예측 정답'을 만드세요.\n\n"
        "- theme_ko: 이 지문의 주제를 나타내는 '한글 명사구' 제목"
        "(예: '두려움이 영장류·아기의 사회성 발달을 늦추는 이유'). 완결 문장이 아니라 제목다운 명사구.\n"
        "- topic(🔎 소재): 이 지문이 '무엇에 관한 글인지' 한 줄로.\n"
        f"- stance(🗣 필자 의견): 다음 중 하나만 — {' / '.join(STANCES)}.\n"
        "- stance_reason: 평가어(형용사)·마지막 문장 등 근거를 한 줄로.\n"
        f"- structure(🧩 글의 구조): 다음 중 하나만 — {' / '.join(STRUCTURES)}.\n"
        "- structure_reason: 그렇게 본 근거를 전환·연결표현이나 문장 번호로 한 줄.\n"
        "- restatement_chains(🔗 재진술 사슬): 2~3개. 지문에서 '같은 개념'이 서로 다른 표현으로 "
        "반복·변주되는 흐름. 각 사슬은 label(개념의 한글 이름), expressions(지문에 나온 순서대로의 "
        "'영어 표현' 2개 이상, 지문에 실제로 있는 표현 그대로), variation(어떻게 바뀌어 가는지 한 줄).\n"
    )


# 2차: 어휘 + 문장별 끊어읽기/내용 ------------------------------------------
def sentence_prompt(title: str, sentences: list[LectureSentence]) -> str:
    n = len(sentences)
    return (
        f"[지문 제목] {title}\n\n"
        f"[지문 — 문장 번호가 매겨져 있음 (총 {n}문장)]\n{_numbered(sentences)}\n\n"
        f"위 {n}개 문장을 '한 문장도 빠짐없이(id 1~{n} 전부)' 분석해 sentences 배열에 순서대로 담으세요.\n"
        "각 문장 항목:\n"
        "- id: 위 문장 번호 그대로.\n"
        "- english: 그 문장의 원문 전체를 첫 단어부터 마침표까지 그대로.\n"
        "- syntax_tag: 그 문장의 핵심 구문·문법을 짧게(예: '관계사절(play a role)·분사구', "
        "'비교급 than절 도치·생략'). 특별한 게 없으면 빈 문자열.\n"
        "- vocab: 그 문장에서 학생이 모를 만한 핵심 단어·표현 2~5개를 {word, meaning}로. "
        "쉬운 단어는 빼고 다의어·숙어·수준 높은 어휘 위주로. (맨 위 '어휘 리스트'로 모읍니다.)\n"
        "- chunks(끊어읽기): 문장을 의미 단위로 끊어 각 조각을 {en, ko, blank}로. en 을 순서대로 "
        "이으면 그 문장의 english 와 정확히 같아야 하고(맨 앞 주어·동사를 첫 chunk 에 포함), ko 는 그 "
        "조각만의 직독직해입니다.\n"
        "  · blank(빈칸): 그 조각이 '오역될 위험이 큰 부분'이면 true, 아니면 false. 한 문장에서 "
        "'가장 틀리기 쉬운 1~2개 조각'만 true 로 하세요(다의어·구조 오인·비교 대상·지칭·수동/도치/생략 등). "
        "학생은 true 인 조각의 ko 를 직접 써넣습니다. 너무 쉬운 조각은 blank=false.\n"
        "- content_options(이 문장 내용 객관식): 이 문장이 '무슨 내용/역할인지'를 묻는 객관식 선지 "
        "2~4개(한국어). 정답 1개는 그 문장의 핵심 내용·글에서의 역할(주제 제시/근거/예시/전환/결론 등)을 "
        "바르게 요약하고, 오답은 '흔히 하는 오해'로 그럴듯하지만 틀리게 만드세요.\n"
        "- content_answer_index: 위 선지에서 정답의 위치(0부터).\n"
        "- content_explanation: 정답 근거나 오답이 왜 틀린지 한 줄(선택, 없으면 빈 문자열).\n"
    )
