#!/usr/bin/env python3
"""원본 파일 사전 점검 (API 미사용·무료).

원본 PDF/HWP 를 넣으면, 생성(=API 비용) 전에 '지문이 깨끗하게 뽑히는지'만 확인한다.
웹앱이 생성 직전에 자동으로 하는 점검과 같은 것으로, 터미널에서 미리 돌려볼 때 쓴다.

사용:
    python tools/검증.py 원본.pdf [원본2.pdf ...]
    python tools/검증.py 원본.pdf --show      # 추출된 지문 본문도 함께 출력

나가는 코드: 문제 없으면 0, 확인할 항목이 있으면 1.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exam import ingest, precheck   # noqa: E402


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("-")]
    show = "--show" in argv
    if not args:
        print(__doc__)
        return 2

    bad = 0
    for path in args:
        p = Path(path)
        if not p.exists():
            print(f"✗ 파일이 없습니다: {p}")
            bad = 1
            continue
        print(f"\n=== {p.name} ===")
        try:
            pairs = ingest.load_bodies([p])      # client 없음 → 오프라인 추출만
        except Exception as e:                    # noqa: BLE001
            print(f"  ✗ 추출 실패: {e}")
            bad = 1
            continue
        bodies = [b for _, b in pairs]
        labels = [lb for lb, _ in pairs]
        rep = precheck.precheck(bodies, labels)

        for i, (lb, body) in enumerate(zip(labels, bodies)):
            name = lb or f"지문 {i + 1}"
            hits = [it for it in rep.issues if it.label == name]
            mark = "⚠️" if hits else "✅"
            print(f"  {mark} [{name}] {len(body)}자")
            for it in hits:
                print(f"      · {it.kind}: {it.detail}")
            if show:
                print(f"      {body[:300]}{'…' if len(body) > 300 else ''}")

        print(f"  → {rep.summary()}")
        if not rep.ok:
            bad = 1

    print("\n" + ("⚠️  확인이 필요한 항목이 있습니다. 생성 전에 점검하세요."
                  if bad else "✅ 모두 통과 — 그대로 생성해도 됩니다."))
    return bad


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
