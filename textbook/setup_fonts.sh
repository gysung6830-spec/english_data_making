#!/usr/bin/env bash
# setup_fonts.sh — NanumSquareRound(.ttf)를 로컬 폰트 디렉터리에 설치
#
# 이 스크립트는 docx → LibreOffice(soffice) → pdf 변환(build_v4.js)이 정확히
# NanumSquareRound 로 렌더되도록 시스템 폰트로 등록한다.
#   (배포용 디자인 PDF(preview_pdf.js)는 폰트를 base64 로 임베드하므로 이 설치가 없어도 됨.)
#
# 사용법: bash setup_fonts.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="${HOME}/.local/share/fonts/NanumSquareRound"
mkdir -p "$DEST"
cp "$DIR"/fonts/*.ttf "$DEST"/
if command -v fc-cache >/dev/null 2>&1; then
  fc-cache -f "$DEST" >/dev/null 2>&1 || true
fi
echo "✓ NanumSquareRound 설치 완료: $DEST"
echo "  (Windows 는 fonts/*.ttf 를 더블클릭 → '설치' 로 등록하세요.)"
