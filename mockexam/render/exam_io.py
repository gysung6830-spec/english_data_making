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


def _choices_from(raw: Any) -> list[Choice]:
    """선지 배열 → Choice 목록. [라벨,본문] 쌍이 아닌 항목은 건너뛴다(부분 손상 허용)."""
    out: list[Choice] = []
    for c in raw or []:
        if isinstance(c, dict) and "label" in c:          # {"label":..,"text":..} 형태도 허용
            out.append(Choice(str(c.get("label", "")), str(c.get("text", ""))))
        elif isinstance(c, (list, tuple)) and len(c) >= 2:
            out.append(Choice(str(c[0]), str(c[1])))
        # 그 외(길이 부족·형식 오류)는 무시 — 통째 거부 대신 살릴 수 있는 만큼 살린다
    return out


def _q_from_dict(d: dict[str, Any]) -> Question:
    return Question(
        no=d.get("no", 0), section=d.get("section", "choice"),
        type=d.get("type", "unknown"), score=d.get("score", 0),
        stem=d.get("stem", ""), passage_text=d.get("passage_text", ""),
        passage_id=d.get("passage_id", ""),
        choices=_choices_from(d.get("choices")),
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


# BlueprintMeta 필수 필드(기본값 없음)에 대한 안전 기본값 — 부분 JSON 도 렌더 가능케.
_META_FALLBACK = {"school_id": "", "name": "", "level": "high", "grade": 1}


def _load_data(source: str | Path | dict | bytes) -> dict:
    """경로/문자열(JSON)/bytes/dict 를 모두 dict 로. bytes 를 str 보다 먼저 처리."""
    if isinstance(source, dict):
        return source
    if isinstance(source, (bytes, bytearray)):
        return json.loads(bytes(source).decode("utf-8"))
    if isinstance(source, Path):
        return json.loads(source.read_text(encoding="utf-8"))
    # str: 경로일 수도, JSON 문자열일 수도. 짧고 '{' 로 시작하지 않을 때만 경로로 시도.
    s = str(source)
    if not s.lstrip().startswith(("{", "[")) and len(s) < 4096:
        try:
            p = Path(s)
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except OSError:
            pass
    return json.loads(s)


def load_exam_json(source: str | Path | dict) -> tuple[MockExam, dict]:
    """JSON(경로/문자열/bytes/dict) → (MockExam, header_info). API 호출 없음.

    부분적으로 어긋난 JSON(필수 메타 누락·선지 형식 오류)도 통째 거부하지 않고
    가능한 만큼 살려서 로드한다(제목만 바꿔 재출력이 목적이므로).
    """
    data = _load_data(source)
    if not isinstance(data, dict):
        raise ValueError("JSON 최상위가 객체가 아닙니다(.exam.json 형식이 아님).")
    ver = data.get("version")
    if ver is not None and ver > SCHEMA_VERSION:
        # 미래 버전 파일 — 거부하지 않되, 새 필드는 무시될 수 있음을 알린다.
        import warnings as _w
        _w.warn(f"exam.json version {ver} > 지원 {SCHEMA_VERSION}: 일부 필드가 무시될 수 있음",
                RuntimeWarning, stacklevel=2)
    md = data.get("meta") or {}
    kw = {f: md.get(f) for f in BlueprintMeta.__dataclass_fields__ if md.get(f) is not None}
    for f, dv in _META_FALLBACK.items():        # 필수 필드 누락 시 안전 기본값
        kw.setdefault(f, dv)
    meta = BlueprintMeta(**kw)
    questions = [_q_from_dict(d) for d in (data.get("questions") or []) if isinstance(d, dict)]
    exam = MockExam(blueprint=Blueprint(meta=meta, items=[]), questions=questions)
    return exam, dict(data.get("header") or {})
