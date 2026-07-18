#!/usr/bin/env python3
"""영어 시험지 자동 생성 툴 — 데모 코드 (명세서 부록 산출물).

API 키 없이도 파이프라인 뼈대를 검증한다:

    지문 데이터(2지문) → [검증] 6종+해설 완비·번호 연속 → 2단 PDF 조판/출력

명세서 §5(동작 순서)의 3)검증 · 4)조판 · 5)출력 단계에 해당한다.
실제 지문을 넣고 Claude API 로 문제를 생성하려면 make_exam.py 를 사용한다.

사용법:
    python 시험지생성_데모코드.py                 # output/데모_시험지.pdf 생성
    python 시험지생성_데모코드.py --header "○○학원 고3 영어"   # 머리글 문구 지정
    python 시험지생성_데모코드.py --out 경로.pdf
"""
from __future__ import annotations

import argparse
from pathlib import Path

from exam import renderer, validator
from exam.demo_data import demo_passages

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="영어 시험지 생성 데모")
    parser.add_argument("--header", default="",
                        help="상단 머리글 문구(학원명/자료명 등). 기본값 비움")
    parser.add_argument("--out", default=str(ROOT / "output" / "데모_시험지.pdf"),
                        help="출력 PDF 경로")
    args = parser.parse_args()

    passages = demo_passages()

    print("=" * 56)
    print("  영어 시험지 자동 생성 — 데모")
    print(f"  지문 수 : {len(passages)}개")
    for i, p in enumerate(passages, 1):
        print(f"    [지문 {i}] {p.title}")
    print("=" * 56)

    # [검증] 6종+해설 완비 · 번호 연속 -------------------------------------
    print("[검증] 6종 문제/해설 완비 확인 …", end=" ")
    validator.validate_passages(passages)
    numbers = validator.validate_numbering(passages, start=1)
    print("통과")
    for i, block in enumerate(numbers, 1):
        print(f"    지문 {i}: 문항 {block[0]}~{block[-1]}번 (문제=해설 동일 번호)")

    # [조판 + 출력] 모든 문제 → 모든 해설, 2단 PDF ------------------------
    out = Path(args.out)
    print(f"[조판/출력] 2단 PDF 생성 …", end=" ")
    renderer.render_pdf(passages, out, header_note=args.header)
    print("완료")
    print("-" * 56)
    print(f"  결과 PDF: {out}")
    print("-" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
