#!/usr/bin/env bash
# ============================================================
#  최초 1회만 실행하는 설치 스크립트  (다른 컴퓨터에서 처음 받았을 때)
#  터미널에서:  bash setup.sh
#
#  하는 일
#   1) PDF 렌더 엔진(WeasyPrint)이 쓰는 '시스템 라이브러리' 설치
#      (+ 스캔 PDF OCR용 poppler)  ← 이게 없으면 PDF 생성이 실패합니다
#   2) 파이썬 라이브러리 설치 (requirements.txt)
#   3) API 키 설정 파일(.env) 준비
#
#  ※ 지문 폰트(나눔스퀘어라운드)는 PDF에 직접 임베드돼 있어 별도 설치가 필요 없습니다.
# ============================================================
set -e

echo "[1/3] 시스템 라이브러리 설치 (WeasyPrint 렌더 + poppler)..."
if command -v apt-get >/dev/null 2>&1; then            # Debian/Ubuntu 계열
  sudo apt-get update
  sudo apt-get install -y \
    python3-pip python3-venv \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev libcairo2 shared-mime-info \
    poppler-utils || echo "   ⚠ 일부 패키지 설치 실패 — 위 목록을 수동 설치해 주세요."
elif command -v brew >/dev/null 2>&1; then             # macOS (Homebrew)
  brew install pango gdk-pixbuf libffi cairo poppler || \
    echo "   ⚠ 자동 설치 실패 — 'brew install pango poppler' 를 수동 실행해 주세요."
else
  echo "   ⚠ apt-get/brew 를 찾지 못했습니다."
  echo "     - Windows: 아래 문서의 'Windows' 절을 참고해 GTK/poppler 를 설치하세요."
  echo "       (WeasyPrint 공식 설치 안내: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)"
fi

echo "[2/3] 파이썬 라이브러리 설치 중..."
pip install -r requirements.txt

echo "[3/3] API 키 설정 파일 준비..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "   .env 파일을 만들었습니다. 파일을 열어 ANTHROPIC_API_KEY 를 입력하세요."
else
  echo "   .env 파일이 이미 있습니다."
fi

echo ""
echo "설치 완료! 다음 중 하나로 실행하세요:"
echo "    python webapp.py            # 브라우저에서 사용 → http://127.0.0.1:5000"
echo "    python webapp.py --preview  # API 키 없이 디자인만 미리보기(비용 0)"
