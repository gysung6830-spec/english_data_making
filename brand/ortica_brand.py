"""Ortica 브랜드 기본 요소 — 팔레트, 타이포, 각인풍 잎 마크.

톤: 먹빛 바탕 · 샴페인 골드 하이라인 · 세리프 · 넓은 여백.
로고는 좌표를 코드로 계산해 SVG path 로 만든다. 톱니 개수·깊이·잎 비율을
숫자로 조절할 수 있어서 벡터 편집기 없이 다시 뽑을 수 있다.
"""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path(__file__).resolve().parent / "fonts"

# ── 팔레트 ────────────────────────────────────────────────────────────────
PALETTE = {
    "ink": "#0B100E",        # 가장 깊은 먹
    "ink_soft": "#121A16",   # 먹 위 한 겹 밝은 면
    "forest": "#16261F",     # 짙은 숲색 (밝은 배경 위 글자)
    "paper": "#F2EEE4",      # 따뜻한 오프화이트
    "paper_hi": "#FAF7EF",   # 가장 밝은 종이
    "gold": "#BFA063",       # 샴페인 골드 — 가는 선과 작은 글자에만
    "gold_hi": "#DCC48E",    # 밝은 골드
    "sage": "#8B9A90",       # 어두운 배경 위 보조 글자
    "stone": "#6E6558",      # 밝은 배경 위 보조 글자
}
P = PALETTE

# ── 타이포 ────────────────────────────────────────────────────────────────
# 폰트는 fontconfig 로 등록해서 쓴다 (brand/fonts/fetch_fonts.py 참고).
SERIF_LATIN = "'Playfair Display', 'Times New Roman', serif"   # 워드마크·숫자
SERIF_KO = "'Gowun Batang', 'Batang', serif"                    # 한글 제목
SANS_KO = "'Pretendard', 'Malgun Gothic', sans-serif"           # 한글 본문·라벨

REQUIRED_FONTS = ["Playfair Display", "Gowun Batang", "Pretendard"]


def font_css() -> str:
    return f"""
.f-serif {{ font-family: {SERIF_LATIN}; }}
.f-ko {{ font-family: {SERIF_KO}; }}
.f-sans {{ font-family: {SANS_KO}; }}
"""


# ── 질감 / 장식 ───────────────────────────────────────────────────────────
def grain(opacity: float = 0.055, seed: int = 7) -> str:
    """아주 옅은 종이 결. 큰 단색 면이 인쇄물처럼 보이게 한다."""
    return (
        f'<svg class="grain" xmlns="http://www.w3.org/2000/svg" '
        f'style="position:absolute;inset:0;width:100%;height:100%;'
        f'opacity:{opacity};pointer-events:none;mix-blend-mode:overlay">'
        f'<filter id="g{seed}"><feTurbulence type="fractalNoise" baseFrequency="0.82" '
        f'numOctaves="3" seed="{seed}"/></filter>'
        f'<rect width="100%" height="100%" filter="url(#g{seed})"/></svg>'
    )


def rule(color: str, thickness: float = 1.0, width: str = "100%") -> str:
    """가는 수평 괘선."""
    return (f'<div style="width:{width};height:{thickness}px;background:{color};'
            f'opacity:.55"></div>')


# ── 잎 형태 계산 ──────────────────────────────────────────────────────────
def _half_width(t: float, a: float = 1.15, b: float = 1.25) -> float:
    """t=0(잎자루) → t=1(잎끝) 에서의 잎 반폭(0~1로 정규화).

    a 를 줄이면 밑동이 넓은 난형(ovate), b 를 줄이면 잎끝이 뭉툭해진다.
    """
    if t <= 0.0 or t >= 1.0:
        return 0.0
    peak = a / (a + b)
    norm = (peak ** a) * ((1.0 - peak) ** b)
    return ((t ** a) * ((1.0 - t) ** b)) / norm


def _tooth_taper(t: float, head: float = 0.12, tail: float = 0.30) -> float:
    """톱니 크기 가중치. 잎자루·잎끝 쪽에서 0으로 사라져 뾰족한 끝을 만든다."""
    up = min(1.0, t / head) if head > 0 else 1.0
    down = min(1.0, (1.0 - t) / tail) if tail > 0 else 1.0
    return max(0.0, min(up, down))


def leaf_path(
    cx: float,
    base_y: float,
    length: float,
    width: float,
    teeth: int = 15,
    depth: float = 0.07,
    tilt: float = 0.0,
    scale: float = 1.0,
    lean_ratio: float = 0.68,
) -> str:
    """톱니(거치) 있는 잎 외곽선 path.

    cx, base_y : 잎자루가 붙는 지점
    length     : 잎자루 → 잎끝 길이 (위쪽 방향)
    width      : 최대 폭(전체 폭)
    depth      : 톱니 깊이(반폭 대비 비율)
    tilt       : 잎을 기울일 각도(도). 양수면 시계방향.
    scale      : 잎 전체를 잎자루 기준으로 축소(각인 이중선용)
    lean_ratio : 톱니 꼭짓점 위치(0.5=대칭, 클수록 잎끝 쪽으로 눕는다)
    """
    half = width / 2.0 * scale
    length = length * scale
    rad = math.radians(tilt)
    cos_t, sin_t = math.cos(rad), math.sin(rad)
    lean = length * 0.030  # 톱니가 잎끝 쪽으로 눕는 정도

    def place(dx: float, dy: float) -> tuple[float, float]:
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

    def side_segments(side: int) -> list[tuple[str, tuple[float, float] | None,
                                               tuple[float, float]]]:
        """잎자루 → 잎끝 방향의 한쪽 면. (명령, 제어점, 끝점) 목록.

        톱니 하나는 '둥글게 부풀어 오르다(Q) 곧게 떨어진다(L)'로 그린다.
        꼭짓점이 곡선 위 점이 되어 날이 살아 있고, 곧은 내림선이 잎끝 쪽으로
        눕는 결을 만든다.
        """
        segs: list[tuple[str, tuple[float, float] | None, tuple[float, float]]] = []
        prev = place(0.0, 0.0)
        for i in range(teeth):
            t0 = (i / teeth) * t_apex
            t1 = ((i + 1) / teeth) * t_apex
            # 톱니 꼭짓점을 구간 뒤쪽에 두면 오르막이 길고 내리막이 짧아져,
            # 톱날이 잎끝 쪽으로 눕는 자연스러운 결이 생긴다.
            tm = t0 + (t1 - t0) * lean_ratio
            tip = crest(tm, side)
            # 제어점은 이전 골과 톱니 끝 사이에서 바깥으로 부풀린다.
            ctrl = (prev[0] * 0.35 + tip[0] * 0.65, prev[1] * 0.35 + tip[1] * 0.65)
            segs.append(("Q", ctrl, tip))
            nxt = notch(t1, side)
            segs.append(("L", None, nxt))
            prev = nxt
        ctrl = place(side * _half_width((t_apex + 1) / 2) * half * 0.82,
                     (t_apex + 0.05) * length)
        segs.append(("Q", ctrl, place(0.0, length)))
        return segs

    right = side_segments(1)
    left = side_segments(-1)

    start = place(0.0, 0.0)
    d = [f"M {start[0]:.2f} {start[1]:.2f}"]
    for cmd, ctrl, end in right:
        if cmd == "Q" and ctrl is not None:
            d.append(f"Q {ctrl[0]:.2f} {ctrl[1]:.2f} {end[0]:.2f} {end[1]:.2f}")
        else:
            d.append(f"L {end[0]:.2f} {end[1]:.2f}")

    # 왼쪽 면은 잎끝 → 잎자루로 되짚어 내려온다. 각 구간의 끝점이 시작점이 된다.
    left_starts = [start] + [end for _, _, end in left]
    for i in range(len(left) - 1, -1, -1):
        cmd, ctrl, _ = left[i]
        end = left_starts[i]
        if cmd == "Q" and ctrl is not None:
            d.append(f"Q {ctrl[0]:.2f} {ctrl[1]:.2f} {end[0]:.2f} {end[1]:.2f}")
        else:
            d.append(f"L {end[0]:.2f} {end[1]:.2f}")
    d.append("Z")
    return " ".join(d)


def leaf_veins(cx: float, base_y: float, length: float, width: float,
               pairs: int = 4, tilt: float = 0.0, scale: float = 1.0) -> list[str]:
    """중앙맥 + 측맥 path 목록. 측맥은 잎끝 쪽으로 살짝 휜다."""
    half = width / 2.0 * scale
    length = length * scale
    rad = math.radians(tilt)
    cos_t, sin_t = math.cos(rad), math.sin(rad)

    def place(dx: float, dy: float) -> tuple[float, float]:
        x = dx * cos_t + dy * sin_t
        y = -dy * cos_t + dx * sin_t
        return cx + x, base_y + y

    paths = []
    bx, by = place(0.0, 0.0)
    tx, ty = place(0.0, length * 0.965)
    paths.append(f"M {bx:.2f} {by:.2f} L {tx:.2f} {ty:.2f}")

    for i in range(1, pairs + 1):
        t = 0.14 + (0.68 * i / (pairs + 1))
        t_end = min(t + 0.155, 0.94)
        for sign in (1, -1):
            sx, sy = place(0.0, t * length)
            mx, my = place(sign * _half_width((t + t_end) / 2) * half * 0.40,
                           ((t + t_end) / 2) * length)
            ex, ey = place(sign * _half_width(t_end) * half * 0.74, t_end * length)
            paths.append(f"M {sx:.2f} {sy:.2f} Q {mx:.2f} {my:.2f} {ex:.2f} {ey:.2f}")
    return paths


# ── 마크 ──────────────────────────────────────────────────────────────────
def leaf_engraved(size: int, color: str, stroke: float = 0.016,
                  inner: bool = True) -> str:
    """각인풍 잎 — 선으로만 그린다. 큰 화면에서 고급감이 가장 좋다."""
    s = size
    cx, base_y = s / 2, s * 0.865
    length = s * 0.735
    width = length * 0.56
    w = s * stroke

    outer = leaf_path(cx, base_y, length, width)
    veins = leaf_veins(cx, base_y, length, width, pairs=5)
    inner_el = ""
    if inner:
        d = leaf_path(cx, base_y, length, width, scale=0.86)
        inner_el = (f'<path d="{d}" fill="none" stroke="{color}" '
                    f'stroke-width="{w * 0.55:.2f}" stroke-opacity=".34"/>')
    vein_els = "".join(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w * 0.62:.2f}" '
        f'stroke-linecap="round" stroke-opacity=".72"/>' for d in veins
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}"
     width="{s}" height="{s}">
  <path d="M {cx} {base_y:.2f} L {cx} {base_y + s * 0.078:.2f}" stroke="{color}"
        stroke-width="{w:.2f}" stroke-linecap="round"/>
  <path d="{outer}" fill="none" stroke="{color}" stroke-width="{w:.2f}"
        stroke-linejoin="round"/>
  {inner_el}{vein_els}
</svg>"""


def leaf_solid(size: int, color: str, vein_color: str) -> str:
    """면으로 채운 잎 — 파비콘처럼 아주 작게 쓸 때만."""
    s = size
    cx, base_y = s / 2, s * 0.855
    length = s * 0.715
    width = length * 0.62
    main = leaf_path(cx, base_y, length, width, teeth=9, depth=0.12)
    veins = leaf_veins(cx, base_y, length, width, pairs=4)
    vein_els = "".join(
        f'<path d="{d}" fill="none" stroke="{vein_color}" stroke-width="{s * 0.017:.2f}" '
        f'stroke-linecap="round" stroke-opacity=".85"/>' for d in veins
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}"
     width="{s}" height="{s}">
  <path d="M {cx} {base_y:.2f} L {cx} {base_y + s * 0.072:.2f}" stroke="{color}"
        stroke-width="{s * 0.030:.2f}" stroke-linecap="round"/>
  <path d="{main}" fill="{color}"/>{vein_els}
</svg>"""


def crest(size: int, color: str, *, frame: bool = True, stroke: float = 0.014) -> str:
    """잎 + 이중 테두리. 도장(stamp) 같은 인상을 준다."""
    s = size
    w = s * stroke
    frame_el = ""
    if frame:
        o = s * 0.045
        i = s * 0.078
        frame_el = (
            f'<rect x="{o:.1f}" y="{o:.1f}" width="{s - 2 * o:.1f}" '
            f'height="{s - 2 * o:.1f}" fill="none" stroke="{color}" '
            f'stroke-width="{w * 0.85:.2f}" stroke-opacity=".85"/>'
            f'<rect x="{i:.1f}" y="{i:.1f}" width="{s - 2 * i:.1f}" '
            f'height="{s - 2 * i:.1f}" fill="none" stroke="{color}" '
            f'stroke-width="{w * 0.45:.2f}" stroke-opacity=".45"/>'
        )
    leaf = leaf_engraved(int(s * 0.74), color, stroke=stroke * 1.25)
    return f"""<div style="position:relative;width:{s}px;height:{s}px">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" width="{s}" height="{s}"
       style="position:absolute;inset:0">{frame_el}</svg>
  <div style="position:absolute;left:{s * 0.13:.0f}px;top:{s * 0.13:.0f}px">{leaf}</div>
</div>"""


def leaf_watermark(w: int, h: int, color: str, opacity: float, *,
                   cx: float = 0.88, base: float = 0.88, scale: float = 0.95,
                   tilt: float = 14.0, line: bool = True) -> str:
    """배경에 크게 깔리는 잎. 선으로 그려야 시선을 덜 뺏는다.

    크기는 가로·세로 중 짧은 쪽을 기준으로 잡는다. 세로로 긴 상세페이지에서
    세로를 기준 삼으면 잎이 화면을 넘어가 톱니만 어지럽게 남는다.
    """
    unit = min(w, h)
    length = unit * scale
    width = length * 0.58
    d = leaf_path(w * cx, h * base, length, width, teeth=17, depth=0.05, tilt=tilt)
    veins = leaf_veins(w * cx, h * base, length, width, pairs=7, tilt=tilt)
    if line:
        body = (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{unit * 0.004:.2f}"/>'
                + "".join(f'<path d="{v}" fill="none" stroke="{color}" '
                          f'stroke-width="{unit * 0.0028:.2f}"/>' for v in veins))
    else:
        body = f'<path d="{d}" fill="{color}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" style="position:absolute;inset:0;'
            f'opacity:{opacity};pointer-events:none">{body}</svg>')
