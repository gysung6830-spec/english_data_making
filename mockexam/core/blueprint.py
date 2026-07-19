"""프로파일 → Blueprint 구성 (§2).

핵심 원칙: blueprint 는 **항상 선택한 학교의 프로파일**에서 나온다.
진양고 값(100/18/9)을 다른 학교에 하드코딩하지 않는다.
- 학습된 학교: profile.item_template 을 그대로 Blueprint 로.
- 미학습 학교: school.standard_skeleton() 이 만든 표준 골격 item_template 사용.
"""
from __future__ import annotations

from typing import Any

from .models import Blueprint, BlueprintMeta, Item


def blueprint_from_profile(profile: dict[str, Any], grade: int | None = None) -> Blueprint:
    """resolve_profile() 결과(dict) → Blueprint."""
    meta = BlueprintMeta(
        school_id=profile.get("school_id", "unknown"),
        name=profile.get("name", profile.get("school_id", "unknown")),
        level=profile.get("level", "high"),
        grade=grade if grade is not None else int(profile.get("grade", 1)),
        subject=profile.get("subject", "영어"),
        time_min=int(profile.get("time_min", 50)),
        total_score=float(profile.get("score_pattern", {}).get("total", 100)),
        learned=bool(profile.get("learned", False)),
    )
    items: list[Item] = []
    for raw in profile.get("item_template", []):
        items.append(Item(
            no=int(raw["no"]),
            section=raw["section"],
            type=raw["type"],
            score=float(raw["score"]),
            underlines=raw.get("underlines"),
            subparts=list(raw.get("subparts", [])),
        ))
    bp = Blueprint(meta=meta, items=items)
    # meta.total_score 는 프로파일 선언값을 신뢰하되, 실제 item 합과 어긋나면 합을 채택.
    if items and abs(bp.total_score - meta.total_score) > 0.01:
        meta.total_score = bp.total_score
    return bp


def expected_counts(profile: dict[str, Any]) -> dict[str, int]:
    """검증기가 비교할 기대 문항수(학교별 상대 기준, §5-1)."""
    counts = profile.get("counts")
    if counts:
        return {"choice": int(counts.get("choice", 0)), "essay": int(counts.get("essay", 0))}
    items = profile.get("item_template", [])
    return {
        "choice": len([i for i in items if i["section"] == "choice"]),
        "essay": len([i for i in items if i["section"] == "essay"]),
    }
