#!/usr/bin/env python3
"""영어 시험지 자동 생성 웹앱 실행 진입점.

    python webapp.py            # http://127.0.0.1:5000
    python webapp.py --port 8080 --host 0.0.0.0

지문을 붙여넣고 옵션을 고르면 브라우저에서 바로 시험지 PDF를 미리보기/다운로드한다.
API 키가 없으면 '데모' 모드로 내장 지문을 사용해 디자인을 미리볼 수 있다.
"""
from __future__ import annotations

import argparse

from web.app import app


def main() -> int:
    parser = argparse.ArgumentParser(description="영어 시험지 생성 웹앱")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--preview", action="store_true",
                        help="미리보기 전용: .env 에 키가 있어도 API 를 쓰지 않음(비용 0)")
    args = parser.parse_args()

    app.config["PREVIEW_ONLY"] = args.preview
    mode = " [미리보기 전용]" if args.preview else ""
    print(f"  ▶ 웹앱 실행: http://{args.host}:{args.port}{mode}")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
