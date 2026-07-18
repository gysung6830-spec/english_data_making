#!/usr/bin/env bash
# ============================================================
#  웹앱 실행 (브라우저에서 파일 올리고 버튼만 누르면 됩니다)
#  터미널에서:  bash run_webapp.sh
#  그다음 브라우저에서:  http://localhost:5000
#  종료:  이 창에서 Ctrl + C
# ============================================================
set -e
cd "$(dirname "$0")"

# 설치가 안 돼 있으면 먼저 setup.sh 안내
if ! python -c "import flask" >/dev/null 2>&1; then
  echo "⚠ 아직 설치가 안 됐습니다. 먼저 아래를 한 번 실행하세요:"
  echo "    bash setup.sh"
  exit 1
fi

# 통합 워크북 렌더용 Chromium 확인(없어도 6개 분석 자료는 동작)
if ! python -c "from playwright.sync_api import sync_playwright" >/dev/null 2>&1; then
  echo "ℹ 통합 워크북 기능을 쓰려면 Chromium 설치가 필요합니다:"
  echo "    python -m playwright install chromium"
fi

PORT="${PORT:-5000}" python webapp.py
