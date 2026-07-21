#!/usr/bin/env python3
"""구문해석 실전서 생성 진입점.

사용법:
    python run_guide.py --mock          # API·코퍼스 없이 샘플 실전서 PDF 미리보기
    python run_guide.py                 # input_corpus/ 의 기출로 실전서 생성(요 API 키)
    python run_guide.py --corpus DIR    # 코퍼스 폴더 지정
    python run_guide.py --per-code N    # 코드당 기출 문장 개수(기본 1)

기존 '지문 자동 분석 도구'(run.py)와는 별개의 교재를 만든다.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.config import ROOT, load_config
from src.guide import render

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("guide")


def main() -> int:
    parser = argparse.ArgumentParser(description="구문해석 실전서 생성기")
    parser.add_argument("--mock", action="store_true", help="샘플 데이터로 디자인 미리보기")
    parser.add_argument("--corpus", default=None, help="기출 코퍼스 폴더 (기본 input_corpus)")
    parser.add_argument("--per-code", type=int, default=1, help="코드당 기출 문장 개수")
    parser.add_argument("--examples", type=int, default=10,
                        help="챕터당 예시 카드 수(중난이도 절반+고난이도 절반)")
    parser.add_argument("--problems", type=int, default=100, help="챕터당 문제 수")
    parser.add_argument("--out", default=None, help="출력 PDF 경로")
    parser.add_argument("--config", default=None, help="설정 파일 경로")
    args = parser.parse_args()

    cfg = load_config(args.config)
    out = Path(args.out) if args.out else (cfg.output_dir / "구문해석_실전서.pdf")

    print("=" * 56)
    print("  구문해석 실전서 생성기")
    print(f"  실행 모드 : {'MOCK(미리보기)' if args.mock else 'API'}")
    print(f"  출력      : {out}")
    print("=" * 56)

    if args.mock:
        from samples.guide_mock import mock_guide
        guide = mock_guide()
    else:
        if not cfg.has_api_key:
            raise SystemExit(
                "ANTHROPIC_API_KEY 가 설정되지 않았습니다. .env 에 키를 넣거나 "
                "--mock 으로 디자인만 확인하세요."
            )
        from src.client import ClaudeClient
        from src.guide.build import build_guide
        corpus_dir = Path(args.corpus) if args.corpus else (ROOT / "input_corpus")
        client = ClaudeClient(cfg.api_key, cfg.model)
        guide = build_guide(client, corpus_dir, per_code=args.per_code,
                            max_retries=cfg.processing.max_retries)
        if not guide.chapters:
            raise SystemExit(
                f"코퍼스({corpus_dir})에서 매칭된 문장이 없습니다. "
                "기출 PDF/텍스트를 넣었는지 확인하세요."
            )

    render.render_pdf(guide, out, sample=args.mock, footer_note=cfg.design.footer_note)
    n_code = sum(len(c.cards) for c in guide.chapters)
    n_syn = sum(len(g.chapters) for g in guide.part2.groups) if guide.part2 else 0
    n_method = len(guide.part0.methods) if guide.part0 else 0
    print("-" * 56)
    print(f"  0부 방법 {n_method}개 · 1부 코드 카드 {n_code}장 · 2부 구문 카드 {n_syn}장")
    print(f"  결과 PDF: {out}")
    print("-" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())
