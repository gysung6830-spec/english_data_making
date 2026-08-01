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

# 하단 저작권 문구(사용자 지정 유지). 페이지 번호는 인쇄 푸터가 붙인다.
FOOTER_BRAND = "© 2026. 은아 T. All rights reserved."

# 표지·상단에 쓰는 스튜디오(브랜드) 이름
BRAND = "김은아영어연구소"

# 통일 폰트 스택 (번들 @font-face 우선, 없으면 시스템 폴백)
FONT_STACK = ("'NanumSquareRound','NanumSquareRoundOTF','나눔스퀘어라운드',"
              "'Malgun Gothic','맑은 고딕','Nanum Gothic','Apple SD Gothic Neo',sans-serif")


def _font_url(name: str) -> str:
    p = FONT_DIR / name
    return p.resolve().as_uri()   # file:///... (절대 경로)


def font_face_css() -> str:
    """번들된 나눔스퀘어라운드를 @font-face 로 등록하는 CSS(렌더 시 <head>에 주입).

    Regular(400)·Bold(700) 두 굵기. 파일이 없으면 빈 문자열(시스템 폰트 폴백)."""
    reg = FONT_DIR / "NanumSquareRoundR.ttf"
    bold = FONT_DIR / "NanumSquareRoundB.ttf"
    if not (reg.exists() and bold.exists()):
        return ""
    return (
        "@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:400;"
        f"src:url('{_font_url('NanumSquareRoundR.ttf')}') format('truetype');}}"
        "@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:700;"
        f"src:url('{_font_url('NanumSquareRoundB.ttf')}') format('truetype');}}"
        # 800/900 요청 시에도 Bold 로 매핑(합성 굵기 방지)
        "@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:800;"
        f"src:url('{_font_url('NanumSquareRoundB.ttf')}') format('truetype');}}"
    )
