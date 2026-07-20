"""직독직해(레이아웃 B) 생성 — 의미 단위 청크 + 문장별 핵심 문법 + 핵심 단어.

지문 전체(문장 + 해석)를 보고 한 번의 LLM 호출로 문장마다
- 청크: 영어 원문을 '/'로 끊은 의미 단위 + 그 직독직해(한글)
- 핵심 문법: 테두리 태그(★필수 어법 강조) + 짧은 설명
- 핵심 단어: 청크별 word·meaning
- '쉽게' 한 줄 요약
을 만든다. 기존 6개 섹션 도구의 '⑥ 직독직해' 디자인과 동일한 데이터 구조.
"""
from __future__ import annotations

from ..client import ClaudeClient
from .llm_schemas import LiteralBundle
from .models import Analysis, GrammarChip, KeyWord, LitChunk, LiteralSentence

SYSTEM = (
    "당신은 한국 고등학교 영어 지문의 '직독직해(끊어 읽기) 학습지'를 만드는 전문 강사입니다. "
    "각 문장을 의미 단위로 끊어 영어 청크와 그 직독직해(한글)를 짝지어 제시하고, "
    "문장별 핵심 문법과 핵심 단어를 정리합니다. 요청된 JSON 스키마로만 응답하세요."
)

# ★필수 어법 판별용 키워드(관계사·분사·가정법·비교·도치·강조·5형식 등).
_KEY_HINTS = (
    "관계", "분사", "가정법", "비교", "도치", "강조", "5형식", "형식",
    "수동", "to부정사", "동명사", "생략", "병렬", "상관", "부정사",
)


def _is_key_grammar(point: str) -> bool:
    return any(h in point for h in _KEY_HINTS)


def _passage_block(analysis: Analysis) -> str:
    lines = []
    for s in analysis.sentences:
        lines.append(f"{s.index}. {s.text}")
        if s.translation:
            lines.append(f"   ({s.translation})")
    return "\n".join(lines)


def build_prompt(analysis: Analysis) -> str:
    n = len(analysis.sentences)
    return (
        f"다음은 지문(총 {n}문장)입니다. 문장번호·원문·해석을 참고해 '직독직해 표'를 만드세요.\n\n"
        f"[지문]\n{_passage_block(analysis)}\n\n"
        "[작성 규칙]\n"
        "1) sentences: 지문의 각 문장을 no(문장 번호)와 함께 만듭니다.\n"
        "2) chunks: 문장을 의미 단위(주어/동사/목적어/전치사구/관계절 등)로 끊습니다. "
        "각 청크는 english(영어 원문 그대로의 조각)와 korean(그 조각의 직독직해)로 짝지으세요. "
        "청크 순서대로 이으면 원문/해석이 복원되어야 합니다. 한 문장당 3~7개가 적당합니다.\n"
        "3) 각 청크의 words: 그 청크에서 시험에 나올 만한 핵심 단어/표현을 word·meaning 으로 담습니다"
        "(없으면 빈 배열).\n"
        "4) grammar: 그 문장의 핵심 문법을 태그로. point(어법 이름), explanation(짧은 설명), "
        "key(관계사·분사·가정법·비교·도치·강조·5형식 등 필수 어법이면 true).\n"
        "5) note: 문장을 학생 눈높이 반말로 풀어주는 '쉽게' 한 줄(선택, 없으면 빈 문자열).\n"
    )


def build_literal(
    client: ClaudeClient,
    analysis: Analysis,
    max_retries: int = 1,
) -> list[LiteralSentence]:
    """LLM 으로 직독직해(청크/문법/단어/쉽게) 생성. 실패 시 원문·해석 기반 폴백."""
    try:
        b: LiteralBundle = client.structured(
            system=SYSTEM,
            prompt=build_prompt(analysis),
            model_cls=LiteralBundle,
            max_tokens=6000,
            max_retries=max_retries,
        )
    except Exception:
        return _fallback(analysis)

    out: list[LiteralSentence] = []
    for s in b.sentences:
        chunks = [
            LitChunk(
                english=c.english,
                korean=c.korean,
                words=[KeyWord(word=w.word, meaning=w.meaning) for w in c.words if w.word],
            )
            for c in s.chunks
            if c.english
        ]
        grammar = [
            GrammarChip(point=g.point, explanation=g.explanation,
                        key=(g.key or _is_key_grammar(g.point)))
            for g in s.grammar
            if g.point
        ]
        if not chunks:
            continue
        out.append(LiteralSentence(no=s.no, chunks=chunks, grammar=grammar,
                                   note=(s.note or "").strip()))
    return out or _fallback(analysis)


def _fallback(analysis: Analysis) -> list[LiteralSentence]:
    """API 실패 시: 문장 전체를 한 청크로 두어 원문/해석만이라도 대조 표기."""
    return [
        LiteralSentence(no=s.index, chunks=[LitChunk(english=s.text, korean=s.translation)])
        for s in analysis.sentences
    ]
