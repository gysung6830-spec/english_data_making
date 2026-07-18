#!/usr/bin/env bash
# ============================================================
#  최초 1회만 실행하는 설치 스크립트
#  터미널에서:  bash setup.sh
# ============================================================
set -e

echo "[1/3] 파이썬 라이브러리 설치 중..."
pip install -r requirements.txt

echo "[2/3] 한글 폰트(나눔고딕) 설치 확인..."
if ! fc-list | grep -qi nanum; then
  echo "   나눔 폰트가 없어 설치를 시도합니다 (관리자 권한 필요할 수 있음)."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y fonts-nanum || \
      echo "   ⚠ 자동 설치 실패. 나눔고딕 폰트를 직접 설치해 주세요."
  elif command -v brew >/dev/null 2>&1; then
    brew install --cask font-nanum-gothic || \
      echo "   ⚠ 자동 설치 실패. 나눔고딕 폰트를 직접 설치해 주세요."
  else
    echo "   ⚠ 자동 설치 도구를 찾지 못했습니다. 나눔고딕 폰트를 직접 설치해 주세요."
  fi
else
  echo "   나눔 폰트가 이미 설치되어 있습니다."
fi

echo "[3/3] API 키 설정 파일 준비..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "   .env 파일을 만들었습니다. 파일을 열어 ANTHROPIC_API_KEY 를 입력하세요."
else
  echo "   .env 파일이 이미 있습니다."
fi

echo ""
echo "설치 완료! 이제 input 폴더에 PDF를 넣고 다음을 실행하세요:"
echo "    python run.py"
