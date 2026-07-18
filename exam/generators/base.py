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
    return (
        f"[제목] {analysis.title}\n"
        f"[주제 한 문장] {analysis.main_idea}\n"
        f"[문장]\n{sents}\n"
        f"[핵심어휘·유의어·반의어]\n{terms}\n"
        f"[문법 밀집 문장] {analysis.hardest_sentence}\n"
    )
