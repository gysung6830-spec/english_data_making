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
    "문장마다 '내용 TMI'(그 문장 뜻을 쉬운 반말로 풀어주는 독해 카드)와 "
    "'어법 Point'(시험에 나오는 어법을 ①②로 짚는 카드)를 간결하게 만듭니다. "
    "요청된 JSON 스키마로만 응답하세요."
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


def _circled(n: int) -> str:
    """1..20 → 원문자 ①..⑳. 범위 밖은 (n)."""
    return chr(0x2460 + n - 1) if 1 <= n <= 20 else f"({n})"


def build_grammar_point(sentence: Sentence) -> Point | None:
    """어법 토큰(note_kind='red')을 ①②… 로 번호 매기고, 인라인 주석은 번호로 바꾼 뒤
    오른쪽 '어법 Point' 박스에 '① 어법이름'을 나열한다. (내용 TMI 없음)

    - 인라인: 해당 어법 글자는 빨강, 주석은 '①' 빨강.
    - 박스   : '① to부정사의 의미상의 주어' 처럼 원문자 번호와 어법명을 나열.
    """
    items: list[tuple[int, str, str | None]] = []
    n = 0
    for t in sentence.tokens:
        if t.note and t.note_kind == "red":
            n += 1
            items.append((n, t.note, t.wrong))
            t.note = _circled(n)        # 인라인은 원문자 번호만
            t.note_kind = "red"
            t.color = t.color or "red"  # 어법 글자 빨강
    if not items:
        return None
    rows = []
    for num, name, wrong in items:
        row = f'<span class="gn">{_circled(num)}</span> {escape(name)}'
        if wrong:
            row += f" · <b>{escape(wrong)}</b>"
        rows.append(row)
    return Point(kind="grammar", caption=f"{sentence.index}번 문장 어법 Point",
                 body_html="<br>".join(rows))


def rule_only_points(sentence: Sentence) -> list[Point]:
    """API 없이 어법 Point 만 규칙기반으로 생성."""
    facts = _grammar_facts(sentence)
    if not facts:
        return []
    lis = "".join(f"<li>{escape(f)}</li>" for f in facts[:5])
    body = f"<ul>{lis}</ul>"
    return [Point(kind="grammar", caption=f"{sentence.index}번 문장 어법 Point",
                  body_html=body)]


def build_points_prompt(sentence: Sentence, passage_summary: str, strength: str) -> str:
    facts = _grammar_facts(sentence)
    fact_block = ""
    if facts:
        fact_block = "\n[analyzer 가 잡은 어법 요소]\n- " + "\n- ".join(facts) + "\n"
    limit = "핵심 1개(어법이 뚜렷하면 어법 우선)" if strength == "key" else "1~2개(내용 TMI/어법)"
    n = sentence.index
    return (
        f"다음은 지문의 {n}번 문장입니다.\n\n"
        f"[문장]\n{sentence.text}\n"
        f"[해석]\n{sentence.translation}\n"
        + fact_block +
        (f"\n[지문 요지]\n{passage_summary}\n" if passage_summary else "") +
        "\n[작성 규칙]\n"
        f"- 이 문장의 포인트 카드를 {limit} 만드세요. 포인트가 약하면 빈 배열도 허용.\n"
        "- kind: 'reading'(내용 TMI) 또는 'grammar'(어법 Point).\n"
        f"- caption: 내용 TMI 는 '{n}번 문장 내용 TMI', 어법 Point 는 '{n}번 문장 어법 Point' 로 정확히.\n"
        "- 내용 TMI(reading): 그 문장이 '무슨 말인지'를 학생 눈높이의 친근한 반말('~야','~거야')로 "
        "1~2문장 풀어주세요. 필요하면 대비(A↔B)·비유를 곁들이되 과하지 않게. body_html 은 보통 평문.\n"
        "- 어법 Point(grammar): 위 analyzer 요소를 근거로 시험 어법을 짚으세요. "
        "body_html 은 '① 포인트명'으로 시작하고 근거를 <ul><li>…</li></ul> 로, 오답형은 <b>form(X)</b> 로, "
        "동치 구조는 '= …' 로. 핵심어는 <b>…</b>. 과한 마크업·인라인 style 금지.\n"
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
