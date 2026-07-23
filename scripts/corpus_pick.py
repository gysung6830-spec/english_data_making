"""영구 저장소에서 챕터별 실제 기출 후보를 뽑아 본다(교재 재료 확보).

새 기출을 ingest 한 뒤 이 스크립트로 챕터별 후보를 확인하고, 골라서 교재
YAML(문제/카드)에 넣으면 된다. 코퍼스가 늘면 후보도 자동으로 늘어난다.

사용:
  python scripts/corpus_pick.py --coverage            # 챕터별 뽑기 가능 수
  python scripts/corpus_pick.py --type apposition -n 5
  python scripts/corpus_pick.py --code contrast -n 5 --difficulty 고
  python scripts/corpus_pick.py --code causation -n 8 --all   # 제외문항 포함
"""
from __future__ import annotations

import argparse

from src.guide.corpus_store import coverage, load_corpus, pick


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default=None, help="평가원 코드 id")
    ap.add_argument("--type", default=None, help="구문 유형 id")
    ap.add_argument("-n", type=int, default=5, help="뽑을 개수")
    ap.add_argument("--difficulty", default=None, choices=["중", "고"])
    ap.add_argument("--all", action="store_true", help="제외문항(20·25~29번)도 포함")
    ap.add_argument("--any", action="store_true", help="자기완결 조건 해제")
    ap.add_argument("--coverage", action="store_true", help="챕터별 후보 수만 출력")
    args = ap.parse_args()

    recs = load_corpus()
    if not recs:
        print("저장소가 비어 있습니다. 먼저: python scripts/ingest_corpus.py")
        return

    if args.coverage:
        cov = coverage(recs)
        print(f"총 {len(recs)}문장 · 챕터별 뽑기 가능 수(제외문항 뺀 기준)")
        for k, v in cov.items():
            bar = "█" * min(v, 40)
            print(f"  {k:22s} {v:4d} {bar}")
        return

    got = pick(
        args.n,
        code=args.code,
        type=args.type,
        self_contained=not args.any,
        difficulty=args.difficulty,
        exclude_items=not args.all,
    )
    label = args.type or args.code or "(전체)"
    print(f"[{label}] 후보 {len(got)}개")
    for r in got:
        print(f"  · ({r['source']}) {r['text']}")


if __name__ == "__main__":
    main()
