"""2차 LLM 검수 패스 — 생성된 문항의 정답 타당성을 재검토.

verifier.py 가 형식·구조를 보는 반면, 여기서는 '정답이 실제로 유일하게 맞는가'를
다른 LLM 호출로 점검한다. 통과 못 하면 pipeline 이 그 문항을 재생성한다.
"""
from __future__ import annotations

from ..core.models import Question


def _question_text(q: Question) -> str:
    lines = [f"[유형] {q.type}", f"[발문] {q.stem}"]
    if q.passage_text:
        lines.append(f"[지문]\n{q.passage_text}")
    if q.choices:
        lines.append("[선지]")
        for c in q.choices:
            lines.append(f"{c.label} {c.text}".rstrip())
        lines.append(f"[표시된 정답] {q.answer}")
    else:
        lines.append(f"[모범답안] {q.answer}")
        if q.answer_notes:
            lines.append("[소문항 답] " + " / ".join(q.answer_notes))
    return "\n".join(lines)


def review_question(client, q: Question) -> tuple[bool, str]:
    """(ok, issue) 반환. 검수 호출이 실패하면 (True, '') 로 통과 처리(문항 보존)."""
    from ..core.llm import REVIEW_SYSTEM, ReviewVerdict

    if q.choices:
        checklist = (
            "검토 항목:\n"
            "1) 표시된 정답이 지문 근거상 실제로 맞는가?\n"
            "2) 정답이 유일한가? 다른 선지 중 정답으로 볼 만한 것이 없는가?\n"
            "3) 나머지 선지는 모두 명확히 틀렸는가?\n"
            "4) 지문·선지에 사실/문법 오류가 없는가?\n"
            "하나라도 문제면 ok=false, issue 에 구체적으로.")
    else:
        checklist = (
            "검토 항목:\n"
            "1) 모범답안이 발문·조건·본문에 비추어 맞는가?\n"
            "2) 문항이 실제로 풀 수 있게 구성되었는가(빈칸/밑줄/보기/조건 등)?\n"
            "3) 본문·보기에 오류가 없는가?\n"
            "하나라도 문제면 ok=false, issue 에 구체적으로.")

    prompt = _question_text(q) + "\n\n" + checklist
    try:
        out = client.structured(REVIEW_SYSTEM, prompt, ReviewVerdict, max_retries=1)
    except Exception:  # 검수 호출 실패 → 문항을 버리지 않고 통과 처리
        return True, ""
    return bool(out.ok), (out.issue or "")
