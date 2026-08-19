"""Ortica 브랜드 기본 요소 — 팔레트, 로고마크(쐐기풀 잎), 폰트 임베딩.

로고마크는 좌표를 코드로 계산해 SVG path 로 만든다. 크기·톱니 개수·비율을
숫자 하나로 조절할 수 있어서, 나중에 로고를 다듬을 때 벡터 편집기 없이도
재생성할 수 있다.
"""

from __future__ import annotations

import base64
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "templates" / "fonts"

# ── 팔레트 ────────────────────────────────────────────────────────────────
# 학습 콘텐츠용: 신뢰감(딥그린) + 생기(리프그린) + 종이질감(크림) + 강조(골드)
PALETTE = {
    "ink": "#0E1F1A",        # 본문 텍스트
    "green_900": "#10382C",  # 가장 어두운 배경
    "green_700": "#1B5A46",  # 주색
    "green_500": "#2E8B6B",  # 보조
    "leaf": "#8ACB5E",       # 잎 하이라이트 / 포인트
    "cream": "#F5F0E2",      # 밝은 배경
    "paper": "#FFFDF7",      # 가장 밝은 배경
    "gold": "#DCA945",       # 강조선
    "muted": "#7E9086",      # 부가 텍스트
}


def font_data_url(name: str) -> str:
    """templates/fonts 의 woff 를 data URL 로 (CSS @font-face 임베딩용)."""
    raw = (FONT_DIR / name).read_bytes()
    return "data:font/woff;base64," + base64.b64encode(raw).decode()


def font_css() -> str:
    return f"""
@font-face {{
  font-family: 'OrticaSans';
  src: url('{font_data_url("NanumSquareRoundB.woff")}') format('woff');
  font-weight: 700;
  font-style: normal;
}}
@font-face {{
  font-family: 'OrticaSans';
  src: url('{font_data_url("NanumSquareRoundR.woff")}') format('woff');
  font-weight: 400;
  font-style: normal;
}}
"""


# ── 로고마크: 쐐기풀(ortica) 잎 ───────────────────────────────────────────
def _half_width(t: float, a: float = 0.38, b: float = 0.72) -> float:
    """t=0(잎자루) → t=1(잎끝) 에서의 잎 반폭(0~1로 정규화).

    a 를 줄이면 밑동이 넓은 난형(ovate), b 를 줄이면 잎끝이 뭉툭해진다.
    """
    if t <= 0.0 or t >= 1.0:
        return 0.0
    peak = a / (a + b)
    norm = (peak ** a) * ((1.0 - peak) ** b)
    return ((t ** a) * ((1.0 - t) ** b)) / norm


def _tooth_taper(t: float, head: float = 0.10, tail: float = 0.22) -> float:
    """톱니 크기 가중치. 잎자루·잎끝 쪽에서 0으로 사라져 뾰족한 끝을 만든다."""
    up = min(1.0, t / head) if head > 0 else 1.0
    down = min(1.0, (1.0 - t) / tail) if tail > 0 else 1.0
    return max(0.0, min(up, down))


def leaf_path(
    cx: float,
    base_y: float,
    length: float,
    width: float,
    teeth: int = 9,
    depth: float = 0.15,
    tilt: float = 0.0,
) -> str:
    """톱니(거치) 있는 잎 외곽선 path.

    cx, base_y : 잎자루가 붙는 지점
    length     : 잎자루 → 잎끝 길이 (위쪽 방향)
    width      : 최대 폭(전체 폭)
    depth      : 톱니 깊이(반폭 대비 비율)
    tilt       : 잎을 기울일 각도(도). 양수면 시계방향.

    톱니는 곡선(2차 베지에)으로 이어 붙여 자연스럽게 만들고, 잎끝 방향으로
    눕혀서 쐐기풀 특유의 결을 낸다.
    """
    half = width / 2.0
    rad = math.radians(tilt)
    cos_t, sin_t = math.cos(rad), math.sin(rad)
    lean = length * 0.030  # 톱니가 잎끝 쪽으로 눕는 정도

    def place(dx: float, dy: float) -> tuple[float, float]:
        """잎 로컬좌표(dx=가로, dy=잎자루로부터 위로)를 캔버스 좌표로."""
        x = dx * cos_t + dy * sin_t
        y = -dy * cos_t + dx * sin_t
        return cx + x, base_y + y

    t_apex = 0.90  # 이 지점부터 잎끝까지는 톱니 없이 매끈하게 뺀다

    def notch(t: float, side: int) -> tuple[float, float]:
        f = 1.0 - depth * _tooth_taper(t)
        return place(side * _half_width(t) * half * f, t * length)

    def crest(t: float, side: int) -> tuple[float, float]:
        f = 1.0 + depth * 0.62 * _tooth_taper(t)
        return place(side * _half_width(t) * half * f, t * length + lean * _tooth_taper(t))

    def side_segments(side: int) -> list[tuple[str, tuple[float, float], tuple[float, float]]]:
        """한쪽 면을 잎자루 → 잎끝 순서로 (명령, 제어점, 끝점) 목록으로."""
        segs = []
        for i in range(teeth):
            t0 = (i / teeth) * t_apex
            t1 = ((i + 1) / teeth) * t_apex
            tm = (t0 + t1) / 2
            segs.append(("Q", crest(tm, side), notch(t1, side)))
        # 잎끝: 마지막 톱니에서 뾰족한 끝까지 매끈한 곡선
        ctrl = place(side * _half_width((t_apex + 1) / 2) * half * 0.85,
                     (t_apex + 0.06) * length)
        segs.append(("Q", ctrl, place(0.0, length)))
        return segs

    right = side_segments(1)
    left = side_segments(-1)

    start = place(0.0, 0.0)
    d = [f"M {start[0]:.2f} {start[1]:.2f}"]
    for _, ctrl, end in right:
        d.append(f"Q {ctrl[0]:.2f} {ctrl[1]:.2f} {end[0]:.2f} {end[1]:.2f}")
    # 왼쪽 면은 잎끝 → 잎자루 방향으로 되짚어 내려온다.
    prev_ends = [start] + [end for _, _, end in left]
    for i in range(len(left) - 1, -1, -1):
        _, ctrl, _ = left[i]
        end = prev_ends[i]
        d.append(f"Q {ctrl[0]:.2f} {ctrl[1]:.2f} {end[0]:.2f} {end[1]:.2f}")
    d.append("Z")
    return " ".join(d)


def leaf_veins(
    cx: float,
    base_y: float,
    length: float,
    width: float,
    pairs: int = 3,
    tilt: float = 0.0,
) -> list[str]:
    """중앙맥 + 측맥 path 목록."""
    half = width / 2.0
    rad = math.radians(tilt)
    cos_t, sin_t = math.cos(rad), math.sin(rad)

    def place(dx: float, dy: float) -> tuple[float, float]:
        x = dx * cos_t + dy * sin_t
        y = -dy * cos_t + dx * sin_t
        return cx + x, base_y + y

    paths = []
    bx, by = place(0.0, 0.0)
    tx, ty = place(0.0, length * 0.97)
    paths.append(f"M {bx:.2f} {by:.2f} L {tx:.2f} {ty:.2f}")

    for i in range(1, pairs + 1):
        t = 0.18 + (0.62 * i / (pairs + 1))
        t_end = min(t + 0.16, 0.95)
        for sign in (1, -1):
            sx, sy = place(0.0, t * length)
            ex, ey = place(sign * _half_width(t_end) * half * 0.72, t_end * length)
            paths.append(f"M {sx:.2f} {sy:.2f} L {ex:.2f} {ey:.2f}")
    return paths


def logomark_svg(size: int = 200, style: str = "dark") -> str:
    """정사각 로고마크. style: dark(딥그린 바탕) / light(크림 바탕) / plain(배경 없음)."""
    p = PALETTE
    if style == "dark":
        bg, leaf_fill, vein, ring = p["green_900"], p["leaf"], p["green_900"], p["green_500"]
    elif style == "light":
        bg, leaf_fill, vein, ring = p["cream"], p["green_700"], p["cream"], p["leaf"]
    else:
        bg, leaf_fill, vein, ring = "none", p["green_700"], p["cream"], "none"

    s = size
    cx = s / 2
    base_y = s * 0.815
    length = s * 0.655
    width = s * 0.48

    main = leaf_path(cx, base_y, length, width, teeth=9)
    veins = leaf_veins(cx, base_y, length, width, pairs=3)

    bg_el = ""
    if bg != "none":
        r = s * 0.26
        bg_el = (f'<rect x="0" y="0" width="{s}" height="{s}" rx="{r:.1f}" ry="{r:.1f}" '
                 f'fill="{bg}"/>')
        if ring != "none":
            inset = s * 0.055
            bg_el += (f'<rect x="{inset:.1f}" y="{inset:.1f}" '
                      f'width="{s - 2 * inset:.1f}" height="{s - 2 * inset:.1f}" '
                      f'rx="{r - inset * 0.7:.1f}" ry="{r - inset * 0.7:.1f}" '
                      f'fill="none" stroke="{ring}" stroke-width="{s * 0.012:.2f}" '
                      f'stroke-opacity="0.55"/>')

    vein_els = "".join(
        f'<path d="{d}" stroke="{vein}" stroke-width="{s * 0.014:.2f}" '
        f'stroke-linecap="round" fill="none" stroke-opacity="0.75"/>'
        for d in veins
    )
    stalk_top = base_y
    stalk_bot = base_y + s * 0.075
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" width="{s}" height="{s}">
  {bg_el}
  <g>
    <path d="M {cx} {stalk_top:.2f} L {cx} {stalk_bot:.2f}" stroke="{leaf_fill}"
          stroke-width="{s * 0.030:.2f}" stroke-linecap="round"/>
    <path d="{main}" fill="{leaf_fill}"/>
    {vein_els}
  </g>
</svg>"""


def leaf_watermark_svg(w: int, h: int, color: str, opacity: float = 0.09) -> str:
    """배경 워터마크용 큰 잎 하나."""
    length = h * 1.35
    width = h * 0.95
    d = leaf_path(w * 0.86, h * 1.18, length, width, teeth=9, tilt=18)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}"><path d="{d}" fill="{color}" '
            f'fill-opacity="{opacity}"/></svg>')
