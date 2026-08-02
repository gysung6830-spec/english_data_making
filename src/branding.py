"""브랜드(회사 파일) 공통 디자인 토큰 · 폰트 임베드.

- 모든 산출물 PDF(통합 워크북 · 단일 유형 · 빈칸형)의 시각 아이덴티티를 통일한다.
- 폰트는 '나눔스퀘어라운드(NanumSquareRound)'로 통일한다. 어느 컴퓨터에서 열어도
  동일하게 보이도록, 저장소에 번들된 폰트를 @font-face(파일 URL)로 직접 로드한다.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"

# 회사 파일 색 팔레트 (초록 계열 + 포인트)
GREEN = "#2e8267"        # 주색 (제목·표 헤더·섹션)
GREEN_DARK = "#256b55"
GREEN_LINE = "#2f8f6d"

# 하단 저작권 문구. 하단 왼쪽에 배치되며 페이지 번호는 병합 후 하단 오른쪽에 찍힌다.
FOOTER_BRAND = "© 2026. Ortica영어. All rights reserved."

# 표지·상단에 쓰는 스튜디오(브랜드) 이름
BRAND = "Ortica영어"

# 통일 폰트 스택 (번들 @font-face 우선, 없으면 시스템 폴백)
FONT_STACK = ("'NanumSquareRound','NanumSquareRoundOTF','나눔스퀘어라운드',"
              "'Malgun Gothic','맑은 고딕','Nanum Gothic','Apple SD Gothic Neo',sans-serif")


import base64
from functools import lru_cache


@lru_cache(maxsize=4)
def _font_data_uri(name: str) -> str:
    """폰트 파일을 base64 data URI 로 인코딩(경로·타이밍 문제 없이 HTML 에 임베드)."""
    p = FONT_DIR / name
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:font/ttf;base64,{b64}"


def font_face_css() -> str:
    """번들된 나눔스퀘어라운드를 @font-face 로 등록하는 CSS(렌더 시 <head>에 주입).

    폰트 파일을 'base64 data URI' 로 직접 임베드한다. file:// 절대경로 방식은 실행 환경(웹/원격)에
    따라 경로를 못 찾거나 로딩 타이밍 문제로 시스템 폰트로 폴백될 수 있어, 어디서든 동일하게
    나눔스퀘어라운드로 렌더되도록 인라인 임베드로 바꿨다. 파일이 없으면 빈 문자열(시스템 폴백)."""
    reg = _font_data_uri("NanumSquareRoundR.ttf")
    bold = _font_data_uri("NanumSquareRoundB.ttf")
    if not (reg and bold):
        return ""
    return (
        "@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:400;"
        f"src:url('{reg}') format('truetype');}}"
        "@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:700;"
        f"src:url('{bold}') format('truetype');}}"
        # 800/900 요청 시에도 Bold 로 매핑(합성 굵기 방지)
        "@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:800;"
        f"src:url('{bold}') format('truetype');}}"
    )
