"""생성기 공통 헬퍼.

모든 생성기는 같은 방식으로 동작한다: 분석 결과(Analysis) + 원문을 받아
LLM 에 유형별 요청을 보내고, 구조화 결과를 exam.format 빌더로 HTML 화한 뒤
(question_html, answer_html) 를 돌려준다.
"""
from __future__ import annotations

from ..schemas import Analysis


def context(analysis: Analysis) -> str:
    """분석 결과를 생성기 프롬프트에 넣을 공통 컨텍스트 문자열로 만든다."""
    sents = "\n".join(f"({i}) {s}" for i, s in enumerate(analysis.sentences, 1))
    terms = "\n".join(
        f"- {t.word} | 유의어: {t.synonym or '-'} | 반의어: {t.antonym or '-'}"
        for t in analysis.key_terms
    )
    base = (
        f"[제목] {analysis.title}\n"
        f"[주제 한 문장] {analysis.main_idea}\n"
        f"[문장]\n{sents}\n"
        f"[핵심어휘·유의어·반의어]\n{terms}\n"
        f"[문법 밀집 문장] {analysis.hardest_sentence}\n"
    )
    note = getattr(analysis, "difficulty_note", "") or ""
    if note:
        base += f"{note}\n"
    return base


# 지문 '다시 쓰기' 지침 — 두 유형이 함께 쓴다.
#   · 어법 서술형(7번): 밑줄 여섯을 다시 쓴 지문 위에 놓는다.
#   · 어휘 원문단어형(9번): 오답 넷을 원문 낱말 그대로 두는 방식이라, 정본 위에 세우면
#     외운 학생이 '원문과 다른 낱말 하나'를 찾는 것으로 끝난다. 다시 쓴 지문 위에서는
#     그 지름길이 통째로 막힌다.
REWRITE_RULES = """[1단계 — 지문 다시 쓰기] rewritten
이 문항의 지문은 원문 그대로가 아니라 '다시 쓴 것'을 씁니다. 학생이 지문을 외운 상태로
원문과 달라진 낱말만 찾아 푸는 것을 막기 위해서입니다.
  · 문장을 합치거나 나누지 말고 '원문과 같은 개수'로, 1:1 대응되게 다시 쓰세요.
  · 각 문장의 '내용·논리·순서'는 그대로 두고 표현만 바꿉니다. 사실을 더하거나 빼지 마세요.
  · 바꾸는 방법: 유의어 교체 / 능동↔수동 / 구를 절로(또는 그 반대) / 어순 조정 /
    분사구문↔접속사절 / 명사구↔that절 등.
  · 최소한 문장의 60% 이상은 원문과 글자 그대로 같지 않아야 합니다.
  · **다시 쓴 지문 자체는 어법상 완전히 옳아야 합니다.** 오류는 2단계에서만 넣습니다.
    다시 쓰다가 실수로 어색한 문장이 되면 밑줄이 아닌 곳에 오류가 생겨 문항이 무너집니다.
    문장을 완성한 뒤 주어-동사 수 일치, 시제, 관계사, 병렬을 스스로 한 번 더 확인하세요.
"""
