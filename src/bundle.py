"""<<ORTICA>> 영어지문 분석지 — 분석 결과(JSON) 저장/복원.

API 로 한 번 분석한 결과를 JSON 으로 저장해 두고, 나중에 '제목만 바꿔' 다시 렌더링할 때
API 를 재호출하지 않도록 한다(비용 0). 저장 대상은 파이프라인이 만든 지문별 4종 객체다.
  - workbook : 통합 카드(Workbook, dataclass)
  - prose    : 단일 유형 산문 워크시트(ProsePack, dataclass)
  - blanks   : 빈칸형 세트(LLMBlankSet, pydantic)
  - writing  : 영작 워크북(WritingPack, dataclass)

dataclass 는 필드 트리를 재귀적으로 dict 로 바꾸고(__dc__ 태그), pydantic 은 model_dump/
model_validate 로 처리(__pyd__ 태그)한다. 계산 property 는 저장하지 않는다(복원 시 재계산).
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from . import blanks_schemas as bs
from . import prose_render as pr
from . import writing_render as wr
from . import workbook_schemas as ws

FORMAT = "ORTICA-ANALYSIS"
VERSION = 1

# 복원용 클래스 레지스트리
_DC = {c.__name__: c for c in (
    ws.Workbook, ws.Sentence, ws.Question,
    pr.ProsePack, pr.ProseWorksheet, pr.PSentence, pr.PItem,
    wr.WritingPack, wr.WSentence, wr.WItem,
    bs.BlankWorkbook, bs.BlankSet, bs.BSentence, bs.Blank,
)}
_PYD = {c.__name__: c for c in (bs.LLMBlankSet,)}


# ── 직렬화 ───────────────────────────────────────────────────────────
def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return {"__pyd__": obj.__class__.__name__, "data": obj.model_dump()}
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: dict[str, Any] = {"__dc__": obj.__class__.__name__}
        for f in dataclasses.fields(obj):
            out[f.name] = _to_jsonable(getattr(obj, f.name))
        return out
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, tuple):
        return [_to_jsonable(x) for x in obj]
    return obj


def _from_jsonable(v: Any) -> Any:
    if isinstance(v, dict):
        if "__pyd__" in v:
            cls = _PYD.get(v["__pyd__"])
            if cls is None:
                raise ValueError(f"알 수 없는 모델: {v['__pyd__']}")
            return cls.model_validate(v["data"])
        if "__dc__" in v:
            cls = _DC.get(v["__dc__"])
            if cls is None:
                raise ValueError(f"알 수 없는 타입: {v['__dc__']}")
            kwargs = {k: _from_jsonable(val) for k, val in v.items() if k != "__dc__"}
            return cls(**kwargs)
        return v
    if isinstance(v, list):
        return [_from_jsonable(x) for x in v]
    return v


# ── 번들(여러 지문) ──────────────────────────────────────────────────
def dump_bundle(wbs: list, packs: list, blank_sets: list, writing_packs: list,
                source_name: str = "") -> dict:
    """지문별 4종 객체를 JSON 직렬화 가능한 dict 로 묶는다."""
    n = max(len(wbs or []), len(packs or []), len(blank_sets or []), len(writing_packs or []))

    def at(seq, i):
        return seq[i] if seq and i < len(seq) else None

    passages = []
    for i in range(n):
        passages.append({
            "workbook": _to_jsonable(at(wbs, i)),
            "prose": _to_jsonable(at(packs, i)),
            "blanks": _to_jsonable(at(blank_sets, i)),
            "writing": _to_jsonable(at(writing_packs, i)),
        })
    return {"format": FORMAT, "version": VERSION, "brand": "ORTICA",
            "source_name": source_name, "passages": passages}


def load_bundle(data: dict):
    """dump_bundle 로 만든 dict → (wbs, packs, blank_sets, writing_packs, source_name)."""
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise ValueError("ORTICA 분석 JSON 형식이 아닙니다.")
    wbs, packs, blank_sets, writing_packs = [], [], [], []
    for p in data.get("passages", []):
        wbs.append(_from_jsonable(p.get("workbook")))
        packs.append(_from_jsonable(p.get("prose")))
        blank_sets.append(_from_jsonable(p.get("blanks")))
        writing_packs.append(_from_jsonable(p.get("writing")))
    return wbs, packs, blank_sets, writing_packs, data.get("source_name", "")


def save_json(data: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


# ── 제목 조회/수정 ───────────────────────────────────────────────────
def passage_titles(wbs, packs, writing_packs, blank_sets) -> list[str]:
    """지문별 현재 제목 목록(대표값: 통합카드 → 산문 → 영작 → 빈칸 순으로 존재하는 것)."""
    n = max(len(wbs or []), len(packs or []), len(writing_packs or []), len(blank_sets or []))
    titles = []
    for i in range(n):
        t = ""
        for seq in (wbs, packs, writing_packs, blank_sets):
            if seq and i < len(seq) and getattr(seq[i], "title", ""):
                t = seq[i].title
                break
        titles.append(t)
    return titles


def set_passage_title(wbs, packs, writing_packs, blank_sets, index: int, title: str) -> None:
    """한 지문(index)의 제목을 모든 유형 객체에 동일하게 반영한다."""
    for seq in (wbs, packs, writing_packs, blank_sets):
        if seq and index < len(seq):
            try:
                seq[index].title = title
            except Exception:
                pass
