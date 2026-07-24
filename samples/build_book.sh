#!/usr/bin/env bash
# 형광펜 독해 교재 빌드: 표지·목차 + PART1(형광펜독해) + PART2(패러프레이징) → 하나의 PDF
# 폰트: 영어=세리프(Liberation Serif), 한글=NanumSquareRound (설치 필요)
#   NanumSquareRound 설치: npm pack @kfonts/nanum-square-round → package/src/*.ttf 를
#   /usr/share/fonts/truetype/nanumsquareround/ 에 복사 후 fc-cache -f
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}"
render(){ "$CHROME" --headless --no-sandbox --disable-gpu \
  --print-to-pdf="$DIR/$2.pdf" --no-pdf-header-footer "file://$DIR/$1.html" 2>/dev/null; }

# 문제은행 재생성(지문 은행/데이터 기반) — 레포 루트에서 실행
( cd "$DIR/.." && python3 -m src.gen_workbook 80 && python3 -m src.gen_paraphrase ) >/dev/null 2>&1 || true

render cover_toc _cover
render strategy_compact_sample 형광펜독해_샘플
render paraphrase_section 패러프레이징_훈련
render 패러프레이징_50 _pp50
render 유형별훈련_워크북 _workbook

python3 - "$DIR" <<'PY'
import sys, fitz
d=sys.argv[1]; out=fitz.open()
# 표지·목차 → PART1 유형훈련 예시 → PART2 패러프레이징(방법론·해부·50문항) → PART3 유형별 훈련 워크북(80)
for f in ["_cover","형광펜독해_샘플","패러프레이징_훈련","_pp50","_workbook"]:
    out.insert_pdf(fitz.open(f"{d}/{f}.pdf"))
out.save(f"{d}/형광펜독해_교재.pdf")
print("교재 빌드 완료:", out.page_count, "pages →", f"{d}/형광펜독해_교재.pdf")
PY
