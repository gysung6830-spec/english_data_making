"""브랜드 글꼴 내려받기 (최초 1회).

    python brand/fonts/fetch_fonts.py

글꼴 파일은 용량이 커서 저장소에 넣지 않는다. 이 스크립트가 brand/fonts/ 로
받아 두면 렌더러가 fontconfig 로 자동으로 잡는다. 셋 다 오픈 라이선스다.

- Playfair Display (OFL) — 워드마크·숫자
- Gowun Batang (OFL)     — 한글 제목 (명조)
- Pretendard (OFL)       — 한글 본문·라벨
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"
PT = ("https://raw.githubusercontent.com/orioncactus/pretendard/main"
      "/packages/pretendard/dist/public/static")

FILES = {
    "PlayfairDisplay[wght].ttf": f"{GF}/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "GowunBatang-Regular.ttf": f"{GF}/gowunbatang/GowunBatang-Regular.ttf",
    "GowunBatang-Bold.ttf": f"{GF}/gowunbatang/GowunBatang-Bold.ttf",
    "Pretendard-Regular.otf": f"{PT}/Pretendard-Regular.otf",
    "Pretendard-Medium.otf": f"{PT}/Pretendard-Medium.otf",
    "Pretendard-SemiBold.otf": f"{PT}/Pretendard-SemiBold.otf",
    "Pretendard-Bold.otf": f"{PT}/Pretendard-Bold.otf",
}

FONTS_CONF = """<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir prefix="default">.</dir>
  <cachedir prefix="default">.fc-cache</cachedir>
  <include ignore_missing="yes">/etc/fonts/conf.d</include>
</fontconfig>
"""


def main() -> None:
    missing = 0
    for name, url in FILES.items():
        dest = HERE / name
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"  · {name} (이미 있음)")
            continue
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                dest.write_bytes(r.read())
            print(f"  ✔ {name}  {dest.stat().st_size // 1024}KB")
        except Exception as exc:  # noqa: BLE001
            missing += 1
            print(f"  ✘ {name} — {exc}")

    (HERE / "fonts.conf").write_text(FONTS_CONF, encoding="utf-8")
    (HERE / ".fc-cache").mkdir(exist_ok=True)
    print("\nfonts.conf 준비 완료.")
    if missing:
        print(f"{missing}개를 못 받았습니다. 네트워크를 확인하고 다시 실행하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
