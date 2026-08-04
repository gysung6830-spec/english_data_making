"""생성 결과(MockExam)를 JSON 으로 저장/재로드.

분석(LLM)이 끝난 결과물을 JSON 으로 남겨두면, 나중에 그 JSON 만 다시 넣어
'제목(머리글)만 바꿔' PDF 를 재출력할 수 있다(API 재호출·재분석 없음).
ORTICA 영어지문 분석지의 JSON 입력 방식과 동일한 취지.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.models import (
    Blueprint, BlueprintMeta, Choice, MockExam, Question,
)

SCHEMA_VERSION = 1


def _q_to_dict(q: Question) -> dict[str, Any]:
    return {
        "no": q.no, "section": q.section, "type": q.type, "score": q.score,
        "stem": q.stem, "passage_text": q.passage_text, "passage_id": q.passage_id,
        "choices": [[c.label, c.text] for c in q.choices],
        "answer": q.answer, "answer_notes": list(q.answer_notes or []),
        "explanation": q.explanation, "difficulty": q.difficulty,
        "underlines": q.underlines, "meta": dict(q.meta or {}),
    }


def _q_from_dict(d: dict[str, Any]) -> Question:
    return Question(
        no=d["no"], section=d["section"], type=d["type"], score=d.get("score", 0),
        stem=d.get("stem", ""), passage_text=d.get("passage_text", ""),
        passage_id=d.get("passage_id", ""),
        choices=[Choice(lb, tx) for lb, tx in d.get("choices", [])],
        answer=d.get("answer", ""), answer_notes=list(d.get("answer_notes") or []),
        explanation=d.get("explanation", ""), difficulty=d.get("difficulty", "mid"),
        underlines=d.get("underlines"), meta=dict(d.get("meta") or {}),
    )


def exam_to_dict(exam: MockExam, info: dict | None = None) -> dict[str, Any]:
    meta = exam.blueprint.meta
    return {
        "version": SCHEMA_VERSION,
        "header": dict(info or {}),
        "meta": {f: getattr(meta, f) for f in BlueprintMeta.__dataclass_fields__},
        "questions": [_q_to_dict(q) for q in exam.questions],
    }


def save_exam_json(exam: MockExam, info: dict | None, path: str | Path) -> Path:
    p = Path(path)
    p.write_text(json.dumps(exam_to_dict(exam, info), ensure_ascii=False, indent=2),
                 encoding="utf-8")
    return p


def load_exam_json(source: str | Path | dict) -> tuple[MockExam, dict]:
    """JSON(경로/문자열/dict) → (MockExam, header_info). API 호출 없음."""
    if isinstance(source, (str, Path)):
        p = Path(source)
        data = json.loads(p.read_text(encoding="utf-8") if p.exists() else str(source))
    elif isinstance(source, (bytes, bytearray)):
        data = json.loads(source.decode("utf-8"))
    elif isinstance(source, dict):
        data = source
    else:
        data = json.loads(source)
    md = data.get("meta", {})
    meta = BlueprintMeta(**{f: md.get(f) for f in BlueprintMeta.__dataclass_fields__
                            if f in md})
    questions = [_q_from_dict(d) for d in data.get("questions", [])]
    exam = MockExam(blueprint=Blueprint(meta=meta, items=[]), questions=questions)
    return exam, dict(data.get("header") or {})
