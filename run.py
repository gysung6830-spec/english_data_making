#!/usr/bin/env python3
"""영어 지문 자동 분석 자료 생성 도구 - 실행 진입점.

가장 간단한 사용법:
    1) input 폴더에 지문 PDF들을 넣는다.
    2) python run.py
    3) output 폴더에 분석 PDF가 생성된다.

옵션:
    python run.py            # 일반(동기) 처리 — 6개 분석 자료
    python run.py --batch    # 대량 처리(Batch API, 비용 절감)
    python run.py --mock     # API 없이 샘플 데이터로 디자인만 미리보기
    python run.py --workbook # '문장별 복합유형 통합 워크북' 생성
    python run.py --config path/to/config.yaml
"""
from __future__ import annotations

import argparse
import sys

from src.config import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="영어 지문 자동 분석 도구")
    parser.add_argument("--batch", action="store_true", help="Batch API 로 대량 처리")
    parser.add_argument("--mock", action="store_true",
                        help="API 없이 샘플 데이터로 출력 PDF 미리보기")
    parser.add_argument("--workbook", action="store_true",
                        help="'문장별 복합유형 통합 워크북' 생성")
    parser.add_argument("--blanks", action="store_true",
                        help="'빈칸형 워크북(지문 빈칸 + 요약문 빈칸)' 생성")
    parser.add_argument("--config", default=None, help="설정 파일 경로")
    args = parser.parse_args()

    cfg = load_config(args.config)

    print("=" * 56)
    print("  영어 지문 자동 분석 도구")
    print(f"  입력 폴더 : {cfg.input_dir}")
    print(f"  출력 폴더 : {cfg.output_dir}")
    print(f"  모델      : {cfg.model}")
    kind = ("빈칸형 워크북" if args.blanks else
            "통합 워크북" if args.workbook else "지문 분석")
    mode = "MOCK(미리보기)" if args.mock else ("BATCH" if args.batch else "일반")
    print(f"  산출물    : {kind}")
    print(f"  실행 모드 : {mode}")
    from src import branding
    print(f"  폰트      : 나눔스퀘어라운드 "
          f"{'번들 임베드(OK)' if branding.fonts_available() else '⚠ 번들 없음 — 시스템 폴백'}")
    print("=" * 56)

    if args.blanks:
        from src.pipeline import run_folder_blanks
        result = run_folder_blanks(cfg, mock=args.mock)
    elif args.workbook:
        from src.pipeline import run_folder_workbook
        result = run_folder_workbook(cfg, mock=args.mock)
    elif args.batch and not args.mock:
        from src.batch import run_folder_batch
        result = run_folder_batch(cfg, cfg.model)
    else:
        from src.pipeline import run_folder
        result = run_folder(cfg, mock=args.mock)

    print("-" * 56)
    print(f"  총 {result['total']}개 중 성공 {result['success']}개, "
          f"실패 {result['failed']}개")
    if result["failed"]:
        print(f"  실패 내역: {cfg.logs_dir / 'failed.jsonl'}")
    print(f"  결과 PDF: {cfg.output_dir}")
    print("-" * 56)
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
