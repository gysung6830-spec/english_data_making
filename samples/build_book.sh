#!/usr/bin/env bash
# 형광펜 독해 교재 빌드: 표지·목차 + PART1(형광펜독해) + PART2(패러프레이징) → 하나의 PDF
# 폰트: 영어=세리프(Liberation Serif), 한글=NanumSquareRound (설치 필요)
#   NanumSquareRound 설치: npm pack @kfonts/nanum-square-round → package/src/*.ttf 를
#   /usr/share/fonts/truetype/nanumsquareround/ 에 복사 후 fc-cache -f
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}"
render(){ local prof; prof="$(mktemp -d)"; rm -f "$DIR/$2.pdf"; \
  "$CHROME" --headless --no-sandbox --disable-gpu --user-data-dir="$prof" --disk-cache-dir=/dev/null \
  --print-to-pdf="$DIR/$2.pdf" --no-pdf-header-footer "file://$DIR/$1.html" 2>/dev/null; \
  rm -rf "$prof"; }

# 문제은행 재생성(지문 은행/데이터 기반) — 레포 루트에서 실행 (범위 전 문항 224)
( cd "$DIR/.." && python3 -m src.gen_workbook 999 ) >/dev/null 2>&1 || true

render cover_toc _cover
render reading_principles _principles
render strategy_compact_sample 형광펜독해_샘플
render 유형별훈련_워크북 _workbook

python3 - "$DIR" <<'PY'
import sys, fitz
d=sys.argv[1]; out=fitz.open()
# 표지·목차 → PART0 원리+신호사전 → PART1 대표카드(형광펜독해_샘플)
#          → PART1 유형별 훈련(문항마다 재진술 훈련 내장)
for f in ["_cover","_principles","형광펜독해_샘플","_workbook"]:
    out.insert_pdf(fitz.open(f"{d}/{f}.pdf"))
out.save(f"{d}/_book_raw.pdf")
print("병합 완료:", out.page_count, "pages")
PY
# 후처리: 문제=왼쪽/해설=오른쪽 정렬 + 전 페이지 푸터(페이지번호+저작권)
python3 "$DIR/finalize_book.py" "$DIR/_book_raw.pdf" "$DIR/형광펜독해_교재.pdf"
rm -f "$DIR/_book_raw.pdf"
