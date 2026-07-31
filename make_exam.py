#!/usr/bin/env python3
"""영어 시험지 자동 생성 툴 — 실제 실행 진입점 (Claude API).

지문을 넣으면 지문마다 6종 변형문제(순서·삽입·주제·어휘·어법·서술형)를
자동 생성해 고등 모의고사 스타일 2단 PDF로 출력한다.

사용법:
    1) .env 에 ANTHROPIC_API_KEY 를 넣는다.
    2) input/ 폴더에 지문을 .txt 로 넣는다 (파일 1개 = 지문 1개, 여러 개 가능).
    3) python make_exam.py --header "○○학원 고3 영어"
    4) output/시험지.pdf 가 생성된다.

옵션:
    --header  상단 머리글 문구(기본값 비움)
    --out     출력 PDF 경로
    --input   지문 .txt 폴더(기본 input/)
    --demo    API 없이 데모 2지문으로 미리보기(= 시험지생성_데모코드.py 와 동일)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import load_config
from src.logutil import setup_logging

ROOT = Path(__file__).resolve().parent


def list_input_files(input_dir: Path):
    """input 폴더의 지원 파일(.txt/.pdf/.jpg/.png/...)을 정렬해 수집."""
    from exam import ingest
    return sorted(p for p in input_dir.iterdir()
                  if p.is_file() and ingest.is_supported(p))


def main() -> int:
    parser = argparse.ArgumentParser(description="영어 시험지 자동 생성")
    parser.add_argument("--header", default="", help="상단 머리글 문구(학원명/자료명 등)")
    parser.add_argument("--out", default=None, help="출력 PDF 경로")
    parser.add_argument("--input", default=None,
                        help="지문 파일 폴더(기본 input/). .txt/.pdf/.jpg/.png 지원")
    parser.add_argument("--config", default=None, help="설정 파일 경로")
    parser.add_argument("--vocab-method", choices=["synonym", "negation"],
                        default="synonym",
                        help="어휘 문제 방식: synonym(반의어 정답) 또는 negation(부정어 삽입)")
    parser.add_argument("--content-difficulty", choices=["plain", "hard"],
                        default="hard",
                        help="내용 일치 난이도: hard(헷갈리는 함정 오답) 또는 plain(명확한 오답)")
    parser.add_argument("--demo", action="store_true",
                        help="API 없이 데모 2지문으로 미리보기")
    args = parser.parse_args()

    cfg = load_config(args.config)
    logger = setup_logging(cfg.logs_dir)
    out_path = Path(args.out) if args.out else (cfg.output_dir / "시험지.pdf")

    # 데모 모드: API 불필요 --------------------------------------------------
    if args.demo:
        from exam import renderer, validator
        from exam.demo_data import demo_passages
        passages = demo_passages()
        validator.validate_passages(passages)
        validator.validate_numbering(passages, start=1)
        renderer.render_pdf(passages, out_path, header_note=args.header)
        logger.info("데모 시험지 생성 완료: %s", out_path)
        return 0

    # 실제 모드 --------------------------------------------------------------
    input_dir = Path(args.input) if args.input else cfg.input_dir
    files = list_input_files(input_dir)
    if not files:
        logger.error("input 폴더에 지문 파일(.txt/.pdf/.jpg/.png)이 없습니다: %s", input_dir)
        logger.error("(API 없이 미리보려면: python make_exam.py --demo)")
        return 1

    if not cfg.has_api_key:
        logger.error("ANTHROPIC_API_KEY 가 설정되지 않았습니다. .env 에 키를 넣거나 --demo 를 쓰세요.")
        return 1

    from exam import ingest
    from exam.pipeline import build_exam
    from exam.llm import ClaudeClient

    client = ClaudeClient(cfg.api_key, cfg.model,
                          thinking=cfg.processing.thinking, effort=cfg.processing.effort)

    # 파일 -> 지문 텍스트(사진은 비전으로 읽음)
    try:
        bodies = ingest.load_bodies(files, client=client)
    except Exception as e:  # noqa: BLE001
        logger.error("지문 추출 실패: %s", e)
        return 1
    if not bodies:
        logger.error("지문을 추출하지 못했습니다.")
        return 1
    logger.info("총 %d개 지문으로 시험지 생성 시작", len(bodies))

    result = build_exam(
        client,
        [b for _, b in bodies],
        out_path,
        header_note=args.header,
        max_retries=cfg.processing.max_retries,
        logger=logger,
        vocab_method=args.vocab_method,
        content_difficulty=args.content_difficulty,
    )
    logger.info("시험지 생성 완료: %s", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
