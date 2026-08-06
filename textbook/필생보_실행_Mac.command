#!/bin/bash
# Mac 용 실행: 이 파일을 더블클릭. (최초 1회 '제어(control)+클릭 → 열기' 필요할 수 있음)
cd "$(dirname "$0")"
echo "============================================"
echo "  필생보 교재 생성기 시작"
echo "============================================"
if ! command -v node >/dev/null 2>&1; then
  echo "[오류] Node.js 가 없습니다. https://nodejs.org 에서 LTS 설치 후 다시 실행하세요."
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
  exit 1
fi
if [ ! -d node_modules ]; then
  echo "[최초 1회] 필요한 파일 설치 중... 1~3분 걸립니다."
  if ! npm install; then
    echo "[오류] npm install 실패 — 인터넷 연결 확인 후 다시 실행하세요."
    read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
    exit 1
  fi
  echo "[최초 1회] PDF 엔진(Chromium 브라우저) 설치 중... (건너뛰어도 첫 사용 시 자동 설치)"
  npx --yes playwright install chromium || true
fi
echo "웹앱을 켭니다. 잠시 후 브라우저가 자동으로 열립니다."
echo "안 열리면 http://localhost:3000 을 직접 여세요.  종료: Ctrl + C"
npm run web
