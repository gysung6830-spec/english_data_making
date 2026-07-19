"""포인트 박스 생성 (명세서 §5-4).

문장별로 오른쪽에 놓일 포인트 카드를 만든다.
- 어법 Point : analyzer 가 잡은 문법 요소(토큰 note/wrong)에서 유도.
- 독해 Point : 요지·대비·열거를 LLM 이 추출.

LLM 이 없거나 강도='없음'이면 어법 Point 만 규칙기반으로 생성한다.
"""
from __future__ import annotations

from markupsafe import escape

from ..client import ClaudeClient
from .llm_schemas import PointBundle
from .models import Point, Sentence

SYSTEM = (
    "당신은 한국 고등학교 영어 학습지의 '포인트 박스'를 쓰는 전문 강사입니다. "
    "문장마다 독해 Point(요지·대비·열거·지칭)와 어법 Point(시험에 나오는 어법)를 "
    "간결한 카드로 만듭니다. 요청된 JSON 스키마로만 응답하세요."
)


def _grammar_facts(sentence: Sentence) -> list[str]:
    """문장 토큰에서 어법 근거(주석/오답형)를 뽑아 목록으로."""
    facts: list[str] = []
    for t in sentence.tokens:
        if t.note and t.note_kind in ("red", "lbl", "blue"):
            frag = f"'{t.text}' — {t.note}"
            if t.wrong:
                frag += f" (오답형 {t.wrong})"
            facts.append(frag)
        elif t.wrong:
            facts.append(f"'{t.text}' — 오답형 {t.wrong}")
    # 중복 제거(순서 유지)
    seen: set[str] = set()
    uniq = []
    for f in facts:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def rule_only_points(sentence: Sentence) -> list[Point]:
    """API 없이 어법 Point 만 규칙기반으로 생성."""
    facts = _grammar_facts(sentence)
    if not facts:
        return []
    lis = "".join(f"<li>{escape(f)}</li>" for f in facts[:5])
    body = f"<ul>{lis}</ul>"
    return [Point(kind="grammar", caption=f"{sentence.index}번 문장 어법 Point", body_html=body)]


def build_points_prompt(sentence: Sentence, passage_summary: str, strength: str) -> str:
    facts = _grammar_facts(sentence)
    fact_block = ""
    if facts:
        fact_block = "\n[analyzer 가 잡은 어법 요소]\n- " + "\n- ".join(facts) + "\n"
    limit = "핵심 1개(어법이 뚜렷하면 어법 우선)" if strength == "key" else "1~2개(독해/어법)"
    return (
        f"다음은 지문의 {sentence.index}번 문장입니다.\n\n"
        f"[문장]\n{sentence.text}\n"
        f"[해석]\n{sentence.translation}\n"
        + fact_block +
        (f"\n[지문 요지]\n{passage_summary}\n" if passage_summary else "") +
        "\n[작성 규칙]\n"
        f"- 이 문장의 포인트 카드를 {limit} 만드세요. 포인트가 약하면 빈 배열도 허용.\n"
        "- kind: 'reading'(독해) 또는 'grammar'(어법).\n"
        "- caption: 'N번 문장 독해 Point' 또는 'N번 문장 어법 Point' 형식.\n"
        "- body_html: 간결한 설명. 핵심어는 <b>…</b>, 목록은 <ul><li>…</li></ul>, "
        "비교표가 필요하면 <table> 사용. 과한 마크업·인라인 style 은 넣지 마세요.\n"
        "- 어법 Point 는 위 analyzer 요소를 근거로, 왜 시험에 나오는지/무엇이 오답인지 짚으세요.\n"
        "- 독해 Point 는 요지·대비(A↔B)·열거·지칭 대상 등 '내용 이해'에 도움이 되는 것만.\n"
    )


# 신뢰 HTML 로 허용할 태그(그 외는 escape 되어 텍스트로 표시됨)
_ALLOWED = {"b", "strong", "em", "u", "br", "ul", "ol", "li", "table", "tr", "td",
            "th", "thead", "tbody", "span", "small", "p"}


def _sanitize_html(html: str) -> str:
    """LLM 이 준 body_html 에서 허용 태그만 남기고 나머지는 이스케이프.

    간단한 화이트리스트 방식(속성 제거). 학습지 포인트 박스는 서식이 단순하므로 충분.
    """
    import re

    out: list[str] = []
    pos = 0
    for m in re.finditer(r"</?([a-zA-Z][a-zA-Z0-9]*)(\s[^>]*)?>", html):
        out.append(str(escape(html[pos:m.start()])))
        tag = m.group(1).lower()
        closing = m.group(0).startswith("</")
        if tag in _ALLOWED:
            out.append(f"</{tag}>" if closing else f"<{tag}>")
        else:
            out.append(str(escape(m.group(0))))
        pos = m.end()
    out.append(str(escape(html[pos:])))
    return "".join(out)


def build_points(
    client: ClaudeClient,
    sentence: Sentence,
    passage_summary: str = "",
    strength: str = "full",
    max_retries: int = 1,
) -> list[Point]:
    """LLM 로 독해/어법 포인트 생성. 실패 시 규칙기반 어법 Point 로 폴백."""
    if strength == "none":
        return []
    try:
        bundle = client.structured(
            system=SYSTEM,
            prompt=build_points_prompt(sentence, passage_summary, strength),
            model_cls=PointBundle,
            max_tokens=3000,
            max_retries=max_retries,
        )
    except Exception:
        return rule_only_points(sentence)
    points = [
        Point(kind=p.kind, caption=p.caption, body_html=_sanitize_html(p.body_html))
        for p in bundle.points
        if p.caption and p.body_html
    ]
    return points or rule_only_points(sentence)
