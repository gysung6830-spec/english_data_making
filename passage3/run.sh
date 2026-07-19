#!/usr/bin/env bash
# ============================================================
#  웹앱 실행 (macOS / Linux)
#  터미널에서:  bash run.sh
#  종료하려면 이 창에서 Ctrl+C
# ============================================================
cd "$(dirname "$0")"
echo "============================================"
echo "  영어 지문 → 3형식 PDF 생성기 (웹앱)"
echo "  브라우저에서  http://localhost:5000  접속"
echo "  (종료: Ctrl+C)"
echo "============================================"

# 3초 뒤 브라우저 자동 열기(가능한 경우)
( sleep 3
  if command -v open >/dev/null 2>&1; then open http://localhost:5000
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open http://localhost:5000
  fi ) >/dev/null 2>&1 &

python webapp.py
