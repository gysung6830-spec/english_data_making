"""HTML → PNG 렌더러 (headless Chromium).

Playwright 없이 크로미움 `--screenshot` 만 쓴다. 설치 의존성이 없어서
다른 PC 에서도 크로미움 경로만 맞으면 그대로 돌아간다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_CANDIDATES = [
    os.environ.get("CHROME_BIN", ""),
    "/opt/pw-browsers/chromium",
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def chrome_binary() -> str:
    for c in _CANDIDATES:
        if c and Path(c).exists():
            return c
    found = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chrome")
    if found:
        return found
    raise RuntimeError(
        "크로미움/크롬을 찾지 못했습니다. CHROME_BIN 환경변수로 실행 파일 경로를 지정하세요."
    )


# 헤드리스 크로미움은 --window-size 중 일부(대략 80px)를 뷰포트에서 떼어 간다.
# 넉넉히 더 크게 잡아 두고 정확한 크기로 잘라내는 편이 버전에 안 휘둘린다.
_VIEWPORT_PAD = 260


def html_to_png(html: str, out_path: Path, width: int, height: int,
                supersample: int = 2) -> Path:
    """HTML 문자열을 정확히 width×height PNG 로 저장.

    supersample 배로 크게 렌더한 뒤 축소해서 글자·곡선 가장자리를 매끈하게 만든다.
    """
    from PIL import Image

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "page.html"
        src.write_text(html, encoding="utf-8")
        raw = Path(tmp) / "raw.png"
        cmd = [
            chrome_binary(),
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--disable-lcd-text",
            f"--force-device-scale-factor={supersample}",
            "--default-background-color=00000000",
            f"--screenshot={raw}",
            f"--window-size={width},{height + _VIEWPORT_PAD}",
            f"--user-data-dir={tmp}/profile",
            src.as_uri(),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if not raw.exists():
            raise RuntimeError(f"렌더 실패: {proc.stderr[-2000:]}")

        img = Image.open(raw).convert("RGBA")
        box = (0, 0, width * supersample, height * supersample)
        if img.width < box[2] or img.height < box[3]:
            raise RuntimeError(
                f"렌더 캔버스가 작습니다({img.width}×{img.height} < {box[2]}×{box[3]}). "
                "_VIEWPORT_PAD 를 늘려 보세요."
            )
        img = img.crop(box)
        if supersample != 1:
            img = img.resize((width, height), Image.LANCZOS)
        img.save(out_path)
    return out_path


# 내용 끝을 표시하는 한 줄. 이 색을 찾아 실제 높이를 잰다.
SENTINEL = "#FF00FF"
_SENTINEL_RGB = (255, 0, 255)


def measure_height(make_page, width: int, max_height: int = 6000,
                   pad: int = 0) -> int:
    """내용이 실제로 끝나는 높이를 브라우저에 물어본다.

    make_page(sentinel_html) 는 본문 맨 끝에 sentinel_html 을 붙인 완성 HTML 을
    돌려주는 함수다. 넉넉한 캔버스에 한 번 그린 뒤 그 표식 줄을 찾는다.

    글자 수로 높이를 어림하면 한글 줄바꿈·이미지 비율 때문에 늘 어긋난다.
    한 번 더 그리는 값이 아깝지만, 잘리거나 빈 여백이 남는 것보다 낫다.
    """
    from PIL import Image

    mark = (f'<div style="width:100%;height:2px;background:{SENTINEL};'
            f'flex:0 0 auto"></div>')
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "probe.png"
        html_to_png(make_page(mark), probe, width, max_height, supersample=1)
        with Image.open(probe) as im:
            rgb = im.convert("RGB")
            px = rgb.load()
            xs = range(0, width, max(1, width // 40))
            for y in range(rgb.height - 1, -1, -1):
                if sum(px[x, y] == _SENTINEL_RGB for x in xs) > len(list(xs)) * 0.6:
                    return min(max_height, y + pad)
    raise RuntimeError(
        f"내용 끝을 못 찾았습니다. max_height({max_height})를 늘려 보세요.")


def page(body: str, css: str, width: int, height: int, extra_head: str = "") -> str:
    """스크린샷 크기에 정확히 맞춘 HTML 문서 껍데기."""
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">{extra_head}
<style>
*, *::before, *::after {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; }}
body {{ width:{width}px; height:{height}px; overflow:hidden;
        -webkit-font-smoothing: antialiased; }}
{css}
</style></head><body>{body}</body></html>"""
