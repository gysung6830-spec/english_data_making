"""뒷페이지(요약) 생성 — 어휘 리스트 / 논리 흐름도 / 쉬운 예시 목차.

지문 전체(문장 + 해석)를 보고 한 번의 LLM 호출로 세 가지를 만든다.
- 어휘 리스트 : 핵심 어휘 + 유의어/반의어
- 논리 흐름도 : 글의 전개 구조(도입→전개→…→결론)
- 쉬운 예시   : 지문을 쉽게 이해하도록 학생 눈높이 비유 한 줄씩
"""
from __future__ import annotations

from ..client import ClaudeClient
from .llm_schemas import OverviewBundle
from .models import Analysis, FlowStep, OutlineItem, VocabEntry

SYSTEM = (
    "당신은 한국 고등학교 영어 지문 학습지의 '요약 정리 페이지'를 만드는 전문 강사입니다. "
    "지문의 핵심 어휘(유의어·반의어 포함), 글의 논리 흐름, 그리고 학생이 쉽게 이해할 수 있는 "
    "비유 예시를 정리합니다. 요청된 JSON 스키마로만 응답하세요."
)


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
        f"다음은 지문(총 {n}문장)입니다. 문장번호·원문·해석을 참고해 '요약 정리 페이지'를 만드세요.\n\n"
        f"[지문]\n{_passage_block(analysis)}\n\n"
        "[작성 규칙]\n"
        "1) vocab: 지문 핵심 어휘 8~12개. 각 항목 word(단어/표현), meaning(한글 뜻), "
        "syn(유의어, 없으면 '—'), ant(반의어, 없으면 '—'), sent(등장 문장 번호).\n"
        "2) flow: 글의 논리 흐름을 4~6단계로. 각 단계 label(도입/전개/전환/주장/결론 등 짧은 이름), "
        "text(개조식 한 줄), sentences(관련 문장 번호, 예 '1~3').\n"
        "3) outline: 지문을 쉽게 이해하도록 구간별 '쉬운 비유 예시'를 한 줄씩(4~6개). "
        "label(문장 범위, 예 '①~③'), easy(학생 눈높이 반말 비유 한 줄).\n"
    )


def build_overview(
    client: ClaudeClient,
    analysis: Analysis,
    max_retries: int = 1,
) -> tuple[list[VocabEntry], list[FlowStep], list[OutlineItem]]:
    """LLM 로 뒷페이지 3종 생성. 실패 시 빈 목록."""
    try:
        b: OverviewBundle = client.structured(
            system=SYSTEM,
            prompt=build_prompt(analysis),
            model_cls=OverviewBundle,
            max_tokens=4000,
            max_retries=max_retries,
        )
    except Exception:
        return [], [], []
    vocab = [VocabEntry(word=v.word, meaning=v.meaning, syn=v.syn or "—",
                        ant=v.ant or "—", sent=(v.sent or None)) for v in b.vocab if v.word]
    flow = [FlowStep(label=f.label, text=f.text, sentences=f.sentences)
            for f in b.flow if f.label and f.text]
    outline = [OutlineItem(label=o.label, easy=o.easy) for o in b.outline if o.easy]
    return vocab, flow, outline
