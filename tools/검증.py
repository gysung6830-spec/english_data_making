#!/usr/bin/env python3
"""완성된 산출물을 기계로 검산해 문항별로 보여 준다 (API 미사용, 몇 초).

검사 본체는 exam/audit.py 에 있다(웹앱도 같은 것을 쓴다). 이 파일은 결과를
사람이 읽는 표로 펴는 일만 한다.

사용:
    python tools/검증.py 결과.json      # 웹앱이 저장한 결과
    python tools/검증.py                # 데모로 시험 삼아
    python tools/검증.py 결과.json -q   # 지적된 문항만
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exam import audit  # noqa: E402
from exam.merged import demo_passages_merged  # noqa: E402

_OK, _NG = "✓", "✗"


def report(passages, only_bad: bool = False) -> int:
    total = bad_items = 0
    no = 1
    for pi, p in enumerate(passages, 1):
        rows, whole = audit.check_passage(p, no)
        no += len(rows)
        title = getattr(p, "title", "") or f"지문 {pi}"
        print(f"\n{'─' * 72}\n[지문 {pi}] {title}   ({len(rows)}문항)")
        for w in whole:
            print(f"  ! {w}")
        for it in rows:
            total += 1
            issues = it["bad"]
            if issues:
                bad_items += 1
            elif only_bad:
                continue
            key = it["key"] if audit.answer_no(it["key"]) else (it["key_tail"] or it["key"])
            print(f"{_NG if issues else _OK} {it['no']:>3}. {it['label']:<12} "
                  f"정답 {(key or '-')[:44]}")
            for m in issues:
                print(f"        · {m}")
            for f in it["flags"]:
                print(f"        (검토메모) {f}")
    print(f"\n{'─' * 72}")
    print(f"총 {total}문항 · 지적 {bad_items}문항 · 이상 없음 {total - bad_items}문항")
    return 1 if bad_items else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="완성된 산출물을 기계로 검산 (API 미사용)")
    ap.add_argument("json", nargs="?", help="웹앱이 저장한 결과(.json). 없으면 데모")
    ap.add_argument("-q", "--only-bad", action="store_true", help="지적된 문항만")
    args = ap.parse_args()

    if args.json:
        from exam import serialize
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        parts, _ = serialize.load_parts(data)
        passages = [p for part in parts for p in part["passages"]]
    else:
        passages = demo_passages_merged()

    if not passages:
        print("지문이 없습니다.", file=sys.stderr)
        return 2
    return report(passages, only_bad=args.only_bad)


if __name__ == "__main__":
    raise SystemExit(main())
