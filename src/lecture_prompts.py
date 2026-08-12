"""'강의컨셉 교재' 생성 프롬프트.

원칙(명세):
- 직독직해(전체 번역)는 제공하지 않는다. 학생이 '먼저 시도하고 확인'하는 훈련 자료를 만든다.
- 문장 번호(S1, S2…)는 코드가 미리 매겨 프롬프트에 넣어 주고, LLM 은 그 번호만 '참조'한다.
- 응답은 구조화된 JSON(스키마)으로 강제한다.
- 지문에 실제로 존재하는 것만 출제한다(억지로 지어내지 않음).
"""
from __future__ import annotations

from .lecture_schemas import LectureSentence

SYSTEM = (
    "당신은 한국 고등학교 영어 내신·수능 지문으로 '학생이 능동적으로 훈련하는' 강의 자료를 "
    "만드는 전문 강사입니다. 전체 직독직해(번역)를 나열하지 말고, 학생이 먼저 스스로 해석·판단하고 "
    "확인하도록 설계하세요. 지문에 '실제로 존재하는' 요소만 출제하고, 없는 것은 지어내지 마세요. "
    "요청된 JSON 스키마에 정확히 맞는 JSON 으로만 응답하세요."
)


def _numbered(sentences: list[LectureSentence]) -> str:
    return "\n".join(f"S{s.id}. {s.text}" for s in sentences)


def analysis_prompt(title: str, sentences: list[LectureSentence]) -> str:
    n = len(sentences)
    body = _numbered(sentences)
    return (
        f"[지문 제목] {title}\n\n"
        f"[지문 — 문장 번호가 매겨져 있음 (총 {n}문장, S1~S{n})]\n{body}\n\n"
        "위 지문으로 아래 5개 섹션을 만드세요. 모든 문장 참조는 위 번호(정수)로만 하고, "
        f"1 이상 {n} 이하만 사용하세요(없는 문장 번호 금지).\n\n"

        "① vocab_hints (어휘 힌트, 4~6개)\n"
        "- 문장 이해에 결정적이면서 학생이 모를 확률이 높은 단어를 고르세요"
        "(빈도 낮은 어휘·다의어·수준 높은 단어 우선, 고1~고3 상위 난이도).\n"
        "- 고유명사·누구나 아는 아주 쉬운 단어는 제외. word 는 지문에 나온 형태, "
        "meaning 은 '짧은 뜻'만(문장 전체 해석 금지).\n\n"

        "② translation_traps (오역포인트 교정 연습, 2~3개)\n"
        "- 오역 위험이 높은 문장(구조가 복잡하거나 관용표현·다의어 포함)을 2~3개 고르세요.\n"
        "- 각 항목: sentence_id(대상 문장 번호), "
        "wrong_translation(학생이 흔히 하는 '표면적/직역' 오역 — 그럴듯하지만 틀린 해석), "
        "correct_translation(올바른 해석), "
        "trap_type(다의어/구조오인/관용표현/지칭 오류/반의어 치환 중 하나), "
        "reason(왜 wrong 이 틀렸는지 원인을 한 줄로).\n"
        "- 반드시 위 지문의 실제 문장에서만 만드세요.\n\n"

        "③ role_blocks (문장 역할 파악, 3~5개 블록)\n"
        "- 지문 전체를 앞에서부터 '연속된 문장 묶음' 3~5개로 나누고, 각 블록에 역할 라벨을 다세요.\n"
        "- 라벨은 반드시 [통념/전환/근거/예시/결론] 중에서만. 지문에 없는 역할은 쓰지 마세요"
        "(통념·예시가 없으면 그 라벨은 생략하고 다른 라벨로만 구성. 억지 배정 금지).\n"
        "- sentence_ids 는 그 블록에 속한 '연속' 문장 번호 목록, 전체 블록을 이으면 S1~S"
        f"{n} 을 빠짐없이 덮어야 합니다(겹치지 않게).\n"
        "- reason 에 '이 문장(들)이 왜 이 역할인지' 담화표지(however/for example/therefore 등)나 "
        "내용 근거로 한 줄 설명.\n\n"

        "④ trap_question (함정포인트 문항, 정확히 1개)\n"
        "- 다음 3가지 유형 중 '지문에 실제로 존재하는' 것 하나만 골라 출제하세요"
        "(억지로 만들지 말 것): 지칭 오류(대명사·this/that 등이 가리키는 대상) / "
        "연결어 반전 오독(however, but 등 역접의 방향) / 생략된 주어 오인.\n"
        "- type(위 3개 중 하나), sentence_id(함정이 걸린 문장 번호), "
        "question_text(발문), option_wrong(흔한 오답), option_correct(정답), explanation(해설).\n\n"

        "⑤ paraphrase_items (패러프레이징 줄잇기, 2~3개)\n"
        "- 본문 핵심 문장(또는 블록)을 골라, 그 내용을 '유의어 치환·구조 변형'한 선지를 만드세요.\n"
        "- choice_text 는 본문 표현을 '그대로 복사하지 말고' 반드시 바꿔 쓴 영어 문장.\n"
        "- matched_sentence_ids 는 그 선지가 대응하는 본문 문장 번호(1:1 또는 1:多).\n"
    )
