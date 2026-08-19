"""Ortica 블로그 이미지 세트 생성기.

    python brand/build.py all          # 전체 세트를 brand/assets 에 생성
    python brand/build.py thumb --title "수능 빈칸추론 3점 문항 푸는 법" \
                                --sub "2026 수능 대비" --tag "독해 전략"

크로미움만 있으면 되고 별도 설치는 필요 없다. (경로는 render.chrome_binary 참고)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ortica_brand import (  # noqa: E402
    PALETTE,
    font_css,
    leaf_path,
    logomark_svg,
)
from render import html_to_png, page  # noqa: E402

OUT = Path(__file__).resolve().parent / "assets"
P = PALETTE

BRAND_KO = "오르티카 영어"
TAGLINE = "고등 내신 · 수능 영어 지문 분석"
KEYWORDS = ["지문 분석", "구문 · 직독직해", "핵심 어휘"]

BASE_CSS = f"""
{font_css()}
body {{ font-family: 'OrticaSans', 'Malgun Gothic', sans-serif; color: {P['ink']}; }}
.stage {{ position:relative; width:100%; height:100%; overflow:hidden; }}
.watermark {{ position:absolute; inset:0; pointer-events:none; }}
.wordmark {{ font-weight:700; letter-spacing:.01em; line-height:1; }}
.ko {{ font-weight:700; letter-spacing:.06em; }}
.sub {{ font-weight:400; }}
.chip {{ display:inline-block; border-radius:999px; font-weight:700; white-space:nowrap; }}
"""


def watermark(w: int, h: int, color: str, opacity: float, *,
              cx: float = 0.84, base: float = 1.30, scale: float = 1.5,
              tilt: float = 16.0) -> str:
    """배경에 크게 깔리는 잎 워터마크.

    크게 확대하면 톱니가 물결처럼 도드라져 시선을 뺏는다. 워터마크에서는
    톱니를 얕게(depth) 가져가 실루엣만 남긴다.
    """
    d = leaf_path(w * cx, h * base, h * scale, h * scale * 0.72,
                  teeth=13, depth=0.055, tilt=tilt)
    return (f'<svg class="watermark" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'xmlns="http://www.w3.org/2000/svg"><path d="{d}" fill="{color}" '
            f'fill-opacity="{opacity}"/></svg>')


def theme(dark: bool) -> dict[str, str]:
    if dark:
        return {
            "bg": f"linear-gradient(135deg, {P['green_900']} 0%, #0A2A20 100%)",
            "fg": P["paper"],
            "muted": "#9FBFB0",
            "accent": P["leaf"],
            "rule": "rgba(138,203,94,.45)",
            "chip_bg": "rgba(255,255,255,.10)",
            "chip_fg": P["leaf"],
            "mark": "dark_on_dark",
            "wm": P["leaf"],
            "wm_op": "0.05",
        }
    return {
        "bg": f"linear-gradient(135deg, {P['paper']} 0%, {P['cream']} 100%)",
        "fg": P["green_900"],
        "muted": P["muted"],
        "accent": P["green_700"],
        "rule": "rgba(27,90,70,.28)",
        "chip_bg": "rgba(27,90,70,.09)",
        "chip_fg": P["green_700"],
        "mark": "light_on_light",
        "wm": P["green_700"],
        "wm_op": "0.055",
    }


def mark_for(dark: bool, size: int) -> str:
    """배경 위에 얹을 마크(배경판 없는 plain 버전에 색만 맞춘다)."""
    svg = logomark_svg(size, "plain")
    if dark:
        return (svg.replace(f'fill="{P["green_700"]}"', f'fill="{P["leaf"]}"')
                   .replace(f'stroke="{P["green_700"]}"', f'stroke="{P["leaf"]}"')
                   .replace(f'stroke="{P["cream"]}"', f'stroke="{P["green_900"]}"'))
    return svg


# ── 개별 에셋 ─────────────────────────────────────────────────────────────
def build_profile(size: int, dark: bool = True) -> str:
    """프로필 이미지 — 원형으로 잘려도 안전하도록 마크를 중앙에 크게."""
    t = theme(dark)
    s = size
    glow = ("radial-gradient(circle at 50% 38%, rgba(138,203,94,.16) 0%, "
            "rgba(138,203,94,0) 62%)") if dark else \
           ("radial-gradient(circle at 50% 38%, rgba(27,90,70,.10) 0%, "
            "rgba(27,90,70,0) 62%)")
    body = f"""<div class="stage" style="background:{t['bg']};display:flex;
      align-items:center;justify-content:center">
      <div style="position:absolute;inset:0;background:{glow}"></div>
      <div style="position:relative;text-align:center">
        <div style="width:{s * 0.58:.0f}px;margin:0 auto">{mark_for(dark, int(s * 0.58))}</div>
        <div class="ko" style="margin-top:{s * 0.020:.0f}px;font-size:{s * 0.100:.0f}px;
             color:{t['accent']};letter-spacing:.16em">ORTICA</div>
      </div>
    </div>"""
    return page(body, BASE_CSS, s, s)


def build_title(width: int, height: int, dark: bool = False) -> str:
    """네이버 블로그 상단 타이틀 이미지(가로 966px 고정 영역용)."""
    t = theme(dark)
    mark = int(height * 0.42)
    chips = "".join(
        f'<span class="chip" style="background:{t["chip_bg"]};color:{t["chip_fg"]};'
        f'padding:{height * 0.032:.0f}px {height * 0.062:.0f}px;'
        f'font-size:{height * 0.062:.0f}px;margin-left:{height * 0.033:.0f}px">{k}</span>'
        for k in KEYWORDS
    )
    body = f"""<div class="stage" style="background:{t['bg']};display:flex;
      align-items:center;padding:0 {height * 0.19:.0f}px">
      {watermark(width, height, t['wm'], t['wm_op'], cx=0.88, base=1.45, scale=1.9, tilt=18)}
      <div style="position:relative;display:flex;align-items:center;gap:{height * 0.10:.0f}px;
           width:100%">
        <div style="width:{mark}px;flex:0 0 auto">{mark_for(dark, mark)}</div>
        <div style="flex:0 0 auto">
          <div class="wordmark" style="font-size:{height * 0.235:.0f}px;color:{t['fg']}">Ortica</div>
          <div class="ko" style="margin-top:{height * 0.035:.0f}px;
               font-size:{height * 0.075:.0f}px;color:{t['accent']}">{BRAND_KO}</div>
        </div>
        <div style="flex:1 1 auto;height:{height * 0.30:.0f}px;
             border-left:1px solid {t['rule']};margin-left:{height * 0.09:.0f}px;
             padding-left:{height * 0.09:.0f}px;display:flex;flex-direction:column;
             justify-content:center">
          <div class="sub" style="font-size:{height * 0.070:.0f}px;color:{t['muted']};
               letter-spacing:.02em">{TAGLINE}</div>
          <div style="margin-top:{height * 0.055:.0f}px;margin-left:-{height * 0.033:.0f}px">
            {chips}</div>
        </div>
      </div>
    </div>"""
    return page(body, BASE_CSS, width, height)


def build_logo_horizontal(width: int, height: int, dark: bool = False) -> str:
    """가로형 로고 (배경 투명) — 유튜브·자료 표지·워터마크용."""
    fg = P["paper"] if dark else P["green_900"]
    accent = P["leaf"] if dark else P["green_700"]
    mark = int(height * 0.78)
    body = f"""<div class="stage" style="display:flex;align-items:center;justify-content:center;
      gap:{height * 0.16:.0f}px;background:transparent">
      <div style="width:{mark}px">{mark_for(dark, mark)}</div>
      <div>
        <div class="wordmark" style="font-size:{height * 0.44:.0f}px;color:{fg}">Ortica</div>
        <div class="ko" style="margin-top:{height * 0.06:.0f}px;
             font-size:{height * 0.135:.0f}px;color:{accent}">{BRAND_KO}</div>
      </div>
    </div>"""
    return page(body, BASE_CSS, width, height)


def build_cover(width: int, height: int, dark: bool = True) -> str:
    """모바일 홈 커버 — 가장자리는 기기별로 잘리므로 중앙 안전영역에만 배치."""
    t = theme(dark)
    mark = int(height * 0.20)
    chips = "".join(
        f'<span class="chip" style="background:{t["chip_bg"]};color:{t["chip_fg"]};'
        f'padding:{height * 0.014:.0f}px {height * 0.028:.0f}px;'
        f'font-size:{height * 0.026:.0f}px;margin:0 {height * 0.008:.0f}px">{k}</span>'
        for k in KEYWORDS
    )
    body = f"""<div class="stage" style="background:{t['bg']};display:flex;
      align-items:center;justify-content:center;text-align:center">
      {watermark(width, height, t['wm'], t['wm_op'], cx=0.90, base=1.34, scale=1.8, tilt=15)}
      <div style="position:relative">
        <div style="width:{mark}px;margin:0 auto">{mark_for(dark, mark)}</div>
        <div class="wordmark" style="margin-top:{height * 0.030:.0f}px;
             font-size:{height * 0.115:.0f}px;color:{t['fg']}">Ortica</div>
        <div class="ko" style="margin-top:{height * 0.018:.0f}px;
             font-size:{height * 0.040:.0f}px;color:{t['accent']};
             letter-spacing:.12em">{BRAND_KO}</div>
        <div style="width:{height * 0.11:.0f}px;height:2px;background:{P['gold']};
             margin:{height * 0.040:.0f}px auto"></div>
        <div class="sub" style="font-size:{height * 0.036:.0f}px;color:{t['muted']};
             line-height:1.55">{TAGLINE}<br>지문 하나를 끝까지 파고드는 영어 노트</div>
        <div style="margin-top:{height * 0.045:.0f}px">{chips}</div>
      </div>
    </div>"""
    return page(body, BASE_CSS, width, height)


def build_thumb(width: int, height: int, title: str, sub: str = "", tag: str = "",
                dark: bool = False, number: str = "") -> str:
    """포스트 대표 이미지 / 썸네일 템플릿."""
    t = theme(dark)
    unit = min(width, height)
    # <br> 로 나눈 줄 중 가장 긴 줄과 줄 수를 함께 보고 제목 크기를 정한다.
    rows = [r.strip() for r in re.split(r"<br\s*/?>", title) if r.strip()]
    longest = max((len(r) for r in rows), default=1)
    weight = max(len(rows), longest / 13)
    title_size = unit * (0.115 if weight <= 2 else 0.100 if weight <= 3
                         else 0.086 if weight <= 4 else 0.074)

    tag_el = ""
    if tag:
        tag_el = (f'<span class="chip" style="background:{t["chip_bg"]};color:{t["chip_fg"]};'
                  f'padding:{unit * 0.018:.0f}px {unit * 0.040:.0f}px;'
                  f'font-size:{unit * 0.038:.0f}px">{tag}</span>')
    num_el = ""
    if number:
        num_el = (f'<span class="wordmark" style="color:{P["gold"]};'
                  f'font-size:{unit * 0.038:.0f}px;margin-left:{unit * 0.030:.0f}px;'
                  f'letter-spacing:.10em">{number}</span>')
    sub_el = ""
    if sub:
        sub_el = (f'<div class="sub" style="margin-top:{unit * 0.035:.0f}px;'
                  f'font-size:{unit * 0.042:.0f}px;color:{t["muted"]};line-height:1.5">{sub}</div>')

    body = f"""<div class="stage" style="background:{t['bg']};display:flex;
      flex-direction:column;justify-content:space-between;
      padding:{unit * 0.085:.0f}px {unit * 0.085:.0f}px">
      {watermark(width, height, t['wm'], t['wm_op'], cx=0.90, base=1.30, scale=1.55, tilt=18)}
      <div style="position:relative">{tag_el}{num_el}</div>
      <div style="position:relative">
        <div class="wordmark" style="font-size:{title_size:.0f}px;color:{t['fg']};
             line-height:1.32;letter-spacing:-.01em;word-break:keep-all">{title}</div>
        {sub_el}
      </div>
      <div style="position:relative;display:flex;align-items:center;
           gap:{unit * 0.028:.0f}px;border-top:1px solid {t['rule']};
           padding-top:{unit * 0.045:.0f}px">
        <div style="width:{unit * 0.085:.0f}px">{mark_for(dark, int(unit * 0.085))}</div>
        <div class="wordmark" style="font-size:{unit * 0.048:.0f}px;color:{t['fg']}">Ortica</div>
        <div class="ko" style="font-size:{unit * 0.034:.0f}px;color:{t['muted']};
             letter-spacing:.08em">{BRAND_KO}</div>
      </div>
    </div>"""
    return page(body, BASE_CSS, width, height)


def build_favicon(size: int) -> str:
    body = f'<div class="stage">{logomark_svg(size, "dark")}</div>'
    return page(body, BASE_CSS, size, size)


# ── 실행 ──────────────────────────────────────────────────────────────────
def build_all() -> list[Path]:
    made: list[Path] = []

    def emit(name: str, html: str, w: int, h: int) -> None:
        path = html_to_png(html, OUT / name, w, h)
        made.append(path)
        print(f"  ✔ {name}  ({w}×{h})")

    print("프로필 이미지")
    emit("profile-naver-161.png", build_profile(161, dark=True), 161, 161)
    emit("profile-400.png", build_profile(400, dark=True), 400, 400)
    emit("profile-light-400.png", build_profile(400, dark=False), 400, 400)

    print("블로그 타이틀 이미지 (네이버 가로 966px)")
    emit("title-966x300-light.png", build_title(966, 300, dark=False), 966, 300)
    emit("title-966x300-dark.png", build_title(966, 300, dark=True), 966, 300)
    emit("title-966x200-light.png", build_title(966, 200, dark=False), 966, 200)

    print("모바일 커버")
    emit("cover-mobile-1200x900.png", build_cover(1200, 900, dark=True), 1200, 900)
    emit("cover-wide-1600x900.png", build_cover(1600, 900, dark=True), 1600, 900)

    print("가로형 로고 (배경 투명)")
    emit("logo-horizontal-dark-bg.png", build_logo_horizontal(1200, 300, dark=True), 1200, 300)
    emit("logo-horizontal-light-bg.png", build_logo_horizontal(1200, 300, dark=False), 1200, 300)

    print("로고마크")
    emit("mark-dark-512.png", page(logomark_svg(512, "dark"), BASE_CSS, 512, 512), 512, 512)
    emit("mark-light-512.png", page(logomark_svg(512, "light"), BASE_CSS, 512, 512), 512, 512)
    emit("mark-plain-512.png", page(logomark_svg(512, "plain"), BASE_CSS, 512, 512), 512, 512)

    print("파비콘 / 앱 아이콘")
    emit("favicon-32.png", build_favicon(32), 32, 32)
    emit("favicon-180.png", build_favicon(180), 180, 180)
    emit("favicon-512.png", build_favicon(512), 512, 512)

    print("포스트 썸네일 샘플")
    emit("thumb-800-sample.png",
         build_thumb(800, 800, "빈칸추론이 안 풀리는<br>진짜 이유 3가지",
                     sub="지문 구조부터 다시 보는 독해법", tag="수능 독해", number="No.01"),
         800, 800)
    emit("thumb-og-1200x630-sample.png",
         build_thumb(1200, 630, "고1 3월 모의고사<br>전 지문 어휘 정리",
                     sub="시험에 나온 순서 그대로", tag="내신 · 모의고사", dark=True),
         1200, 630)
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description="Ortica 블로그 이미지 생성")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("all", help="전체 세트 생성")

    t = sub.add_parser("thumb", help="포스트 썸네일 1장 생성")
    t.add_argument("--title", required=True, help="제목. 줄바꿈은 <br> 로")
    t.add_argument("--sub", default="", help="부제")
    t.add_argument("--tag", default="", help="좌측 상단 카테고리 태그")
    t.add_argument("--number", default="", help="회차 표기 (예: No.12)")
    t.add_argument("--size", default="800x800", help="가로x세로 (기본 800x800)")
    t.add_argument("--dark", action="store_true", help="딥그린 배경")
    t.add_argument("--out", default="", help="출력 경로 (기본 brand/assets/thumb.png)")

    args = ap.parse_args()
    if args.cmd == "thumb":
        w, h = (int(v) for v in args.size.lower().split("x"))
        out = Path(args.out) if args.out else OUT / "thumb.png"
        html = build_thumb(w, h, args.title, args.sub, args.tag, args.dark, args.number)
        html_to_png(html, out, w, h)
        print(f"✔ {out}  ({w}×{h})")
        return

    made = build_all()
    print(f"\n총 {len(made)}개 파일 → {OUT}")


if __name__ == "__main__":
    main()
