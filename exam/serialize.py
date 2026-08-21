"""생성 결과(분석·문항 HTML)를 JSON 으로 저장/복원.

이미 분석·생성이 끝난 결과를 JSON 으로 남겨 두면, 나중에 재분석·재생성(=API 비용)
없이 그대로 다시 렌더할 수 있다. 제목(머리글·지문 제목)만 바꿔 재출력할 때 쓴다.

JSON 은 사람이 읽고 고칠 수 있는 형태라, 지문 제목 등은 파일에서 직접 수정해도 된다.
"""
from __future__ import annotations

from .set2 import TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
from .types import TYPE_LABELS, TYPE_ORDER, TYPE_PROMPTS, Passage

SCHEMA_VERSION = 1
APP_TAG = "ortica-exam"


def passage_to_dict(p: Passage) -> dict:
    """Passage → 직렬화 dict(문제·해설 HTML·제목·라벨·검토 플래그 모두 보존)."""
    return {
        "title": p.title,
        "source_label": getattr(p, "source_label", "") or "",
        "q": dict(p.q),
        "a": dict(p.a),
        "flags": {k: list(v) for k, v in getattr(p, "flags", {}).items()},
    }


def passage_from_dict(d: dict) -> Passage:
    p = Passage(title=str(d.get("title", "") or ""))
    p.source_label = str(d.get("source_label", "") or "")
    p.q = dict(d.get("q", {}) or {})
    p.a = dict(d.get("a", {}) or {})
    p.flags = {k: list(v) for k, v in (d.get("flags") or {}).items()}
    return p


# 세트 마커 → (유형 순서, 발문, 라벨)
#   "M" = 통합본(1회+2회에서 중복 유형을 뺀 11유형) · "1"/"2" = 기존 회차별
def _merged_meta():
    from .merged import MERGED_LABELS, MERGED_ORDER, MERGED_PROMPTS
    return (MERGED_ORDER, MERGED_PROMPTS, MERGED_LABELS)


_SET_META = {
    "1": (TYPE_ORDER, TYPE_PROMPTS, TYPE_LABELS),
    "2": (TYPE_ORDER2, TYPE_PROMPTS2, TYPE_LABELS2),
}


def dump_parts(part_meta: list[dict], header: str = "", doc_name: str = "") -> dict:
    """part_meta: [{"set":"1"/"2","tag":str,"sections":list,"passages":[Passage,…]}] → JSON dict.

    tag 는 머리글(header)을 뺀 파트 제목("변형문제")이라,
    복원 시 새 머리글과 다시 합칠 수 있다.
    """
    return {
        "version": SCHEMA_VERSION,
        "app": APP_TAG,
        "header": header,
        "doc_name": doc_name,
        "parts": [
            {
                "set": str(pm["set"]),
                "tag": pm["tag"],
                "sections": list(pm.get("sections") or []),
                "group_by": pm.get("group_by", "passage"),
                "passages": [passage_to_dict(p) for p in pm["passages"]],
            }
            for pm in part_meta
        ],
    }


def _header_note(tag: str, header: str) -> str:
    return f"{tag} — {header}" if (tag and header) else (tag or header)


def load_parts(data: dict, header_override: str | None = None) -> tuple[list[dict], dict]:
    """JSON dict → (render_pdf_multi 용 parts, 메타). header_override 로 머리글만 교체 가능.

    반환 parts 는 renderer.render_pdf_multi 에 그대로 넣을 수 있는 형태.
    """
    if not isinstance(data, dict) or not isinstance(data.get("parts"), list) or not data["parts"]:
        raise ValueError("올바른 분석 결과 JSON 이 아닙니다(parts 없음).")

    header = header_override if header_override is not None else str(data.get("header", "") or "")
    parts: list[dict] = []
    for pm in data["parts"]:
        setk = str(pm.get("set", "1"))
        order, prompts, labels = (_merged_meta() if setk == "M"
                                  else _SET_META.get(setk, _SET_META["1"]))
        passages = [passage_from_dict(pd) for pd in (pm.get("passages") or [])]
        if not passages:
            raise ValueError("빈 파트가 있습니다(지문 없음).")
        # 문항 완비 검증(JSON 손상·수정 실수 방지)
        for p in passages:
            missing = [t for t in order if t not in p.q or t not in p.a]
            if missing:
                raise ValueError(f"'{p.title}' 파트에 빠진 유형이 있습니다: {missing}")
        gb = pm.get("group_by", "passage")
        part = {
            "passages": passages,
            "header_note": _header_note(str(pm.get("tag", "") or ""), header),
            "sections": pm.get("sections") or None,
            "group_by": gb if gb in ("passage", "type") else "passage",
        }
        # 조판 메타는 세트와 상관없이 항상 명시한다(기본값에 기대지 않는다).
        part.update(type_order=order, prompts=prompts, labels=labels)
        parts.append(part)

    meta = {"header": header,
            "doc_name": str(data.get("doc_name", "") or ""),
            "n_parts": len(parts)}
    return parts, meta
