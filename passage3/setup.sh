#!/usr/bin/env bash
# ============================================================
#  영어 지문 → 3형식 PDF 생성기 · 최초 1회 설치 스크립트
#  터미널에서:  bash setup.sh
#  (macOS / Linux 용. Windows 는 setup.bat 실행)
# ============================================================
set -e
cd "$(dirname "$0")"

echo "[1/3] 파이썬 라이브러리 설치 중..."
pip install -r requirements.txt

echo "[2/3] 렌더링용 Chromium 설치 중 (playwright)..."
python -m playwright install chromium || \
  echo "   ⚠ Chromium 자동 설치 실패. 인터넷 연결을 확인하고 'python -m playwright install chromium' 을 다시 실행하세요."

echo "[3/3] 한글 폰트(나눔스퀘어) 설치 확인..."
if command -v fc-list >/dev/null 2>&1 && fc-list | grep -qi "nanumsquare\|나눔스퀘어"; then
  echo "   나눔스퀘어가 이미 설치되어 있습니다."
else
  echo "   나눔스퀘어를 설치합니다 (관리자 권한이 필요할 수 있음)."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y fonts-nanum fonts-nanum-extra && fc-cache -f || \
      echo "   ⚠ 자동 설치 실패. '나눔스퀘어' 폰트를 직접 설치해 주세요."
  elif command -v brew >/dev/null 2>&1; then
    brew install --cask font-nanum-square || \
      echo "   ⚠ 자동 설치 실패. '나눔스퀘어' 폰트를 직접 설치해 주세요."
  else
    echo "   ⚠ 자동 설치 도구를 못 찾았습니다. '나눔스퀘어' 폰트를 직접 설치해 주세요."
    echo "     (인터넷이 되면 웹폰트로 자동 로드되므로 없어도 대개 동작합니다.)"
  fi
fi

echo ""
echo "설치 완료! 웹앱을 실행하려면:"
echo "    bash run.sh        (또는  python webapp.py )"
echo "그다음 브라우저에서  http://localhost:5000  접속."
echo ""
echo "(선택) 스캔/사진 자동 OCR·해석 자동 번역을 쓰려면 API 키를 설정하세요:"
echo "    export ANTHROPIC_API_KEY=sk-..."
