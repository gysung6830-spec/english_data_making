#!/usr/bin/env bash
# ============================================================
#  판매 사이트를 내 컴퓨터에서 띄웁니다.
#  터미널에서:  bash store-start.sh
# ============================================================
cd "$(dirname "$0")"

# --- 관리자 비밀번호 ---------------------------------------
# 아래 따옴표 안을 원하는 비밀번호로 바꾸세요. 영문+숫자 12자 이상, 한글은 넣지 마세요.
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-ortica-change-me-1234}"

# 내 컴퓨터에서는 https 가 아니므로 로그인 쿠키 조건을 풀어 줍니다.
export STORE_HTTPS=0

echo
echo "  Ortica영어 판매 사이트를 시작합니다."
echo
echo "  [1/2] 필요한 라이브러리를 확인합니다..."
python3 -m pip install -q -r store_requirements.txt || {
  echo "  ! 설치에 실패했습니다. 파이썬 3.11 이상이 깔려 있는지 확인해 주세요."
  exit 1
}

echo "  [2/2] 사이트를 켭니다."
( sleep 3
  command -v open    >/dev/null && open    http://localhost:5001 ||
  command -v xdg-open >/dev/null && xdg-open http://localhost:5001 || true ) &

python3 store.py
