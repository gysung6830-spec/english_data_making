"""영구 기출 저장소(data/corpus.jsonl) 조회 계층.

교재 생성기와 코퍼스를 잇는 다리. 새 기출이 쌓이면(ingest_corpus.py) 이 조회가
자동으로 더 많은 후보를 돌려주므로, 교재 재료가 코퍼스와 함께 늘어난다.

핵심 원칙(교재 규칙과 동일):
  - 제외 문항(20·25~29번) 문장은 기본적으로 뺀다.
  - 기본은 self_contained(앞 문장 없이 단독 출제 가능) 문장만.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "data" / "corpus.jsonl"

EXCLUDE_ITEM_NOS = {20, 25, 26, 27, 28, 29}


def load_corpus(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else DEFAULT_STORE
    if not p.exists():
        return []
    out: list[dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _keep(rec: dict, exclude_items: bool) -> bool:
    if exclude_items and rec.get("item") in EXCLUDE_ITEM_NOS:
        return False
    return True


def query(
    records: list[dict] | None = None,
    *,
    code: str | None = None,
    type: str | None = None,
    self_contained: bool = True,
    difficulty: str | None = None,
    exclude_items: bool = True,
    contains: str | None = None,
) -> list[dict]:
    """조건에 맞는 기출 문장 레코드를 돌려준다.

    code   평가원 코드 id(causation·contrast·equivalence·comparison·connective·
           polarity_positive·polarity_negative) 중 하나가 포함된 문장.
    type   구문 유형 id(emphasis·inversion·parallel·apposition·what_clause·
           insertion·participle·that_clause·wh_clause·prep_stack).
    """
    recs = records if records is not None else load_corpus()
    rx = re.compile(re.escape(contains), re.IGNORECASE) if contains else None
    out = []
    for r in recs:
        if not _keep(r, exclude_items):
            continue
        if self_contained and not r.get("self_contained"):
            continue
        if code and code not in (r.get("codes") or []):
            continue
        if type and r.get("type") != type:
            continue
        if difficulty and r.get("difficulty") != difficulty:
            continue
        if rx and not rx.search(r["text"]):
            continue
        out.append(r)
    return out


def pick(
    n: int,
    *,
    prefer_difficulty: str | None = "고",
    **kwargs,
) -> list[dict]:
    """조건에 맞는 문장을 최대 n개 뽑는다(난이도 '고' 우선, 그다음 긴 문장 우선).

    결정적 정렬 — 같은 코퍼스면 항상 같은 결과(재현 가능).
    """
    hits = query(**kwargs)
    hits.sort(
        key=lambda r: (
            0 if (prefer_difficulty and r.get("difficulty") == prefer_difficulty) else 1,
            -len(r["text"]),
            r["id"],
        )
    )
    return hits[:n]


def coverage(records: list[dict] | None = None, *, exclude_items: bool = True) -> dict:
    """챕터(코드·구문유형)별로 지금 저장소에서 뽑을 수 있는 문장 수."""
    from .codes import load_categories
    from .syntax import SYNTAX_TYPES

    recs = records if records is not None else load_corpus()
    out: dict[str, int] = {}
    for cat in load_categories():
        out[f"code:{cat.id}"] = len(
            query(recs, code=cat.id, exclude_items=exclude_items)
        )
    for st in SYNTAX_TYPES:
        out[f"type:{st.id}"] = len(
            query(recs, type=st.id, exclude_items=exclude_items)
        )
    return out
