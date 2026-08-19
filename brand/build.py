"""Ortica 블로그 이미지 생성기.

    pip install pillow                   # 최초 1회
    python brand/sample_shots.py         # 실제 자료 예시 이미지 뽑기
    python brand/build.py all            # 전체 세트 → brand/assets

    python brand/build.py thumb --title "빈칸추론이 안 풀리는<br>진짜 이유" \
                                --sub "지문 구조부터 다시" --tag "수능 독해"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog import BOOKS, BY_KEY, MATERIALS  # noqa: E402
from ortica_brand import (  # noqa: E402
    PALETTE as P,
    font_css,
    leaf_path,
    logomark_svg,
)
from render import html_to_png, page  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets"
SAMPLES = OUT / "samples"

BRAND_EN = "Ortica"
BRAND_KO = "오르티카 영어"
TAGLINE = "고등 모의고사 · 내신 · 수능자료 제작"
CONCEPT = "필자의 생각이 보이는 영어"
KEYWORDS = ["고등 모의고사", "내신", "수능자료 제작"]

# 네이버 본문 폭에 맞춘 기본 가로.
DOC_W = 900

CSS = f"""
{font_css()}
body {{ font-family:'OrticaSans','Malgun Gothic',sans-serif; color:{P['ink']}; }}
.stage {{ position:relative; width:100%; height:100%; overflow:hidden; }}
.wm {{ font-weight:700; letter-spacing:.01em; line-height:1; }}
.ko {{ font-weight:700; letter-spacing:.02em; }}
.sans {{ font-weight:400; }}
.chip {{ display:inline-block; border-radius:999px; font-weight:700; white-space:nowrap; }}
"""


# ── 테마 ──────────────────────────────────────────────────────────────────
def theme(dark: bool) -> dict[str, str]:
    if dark:
        return {
            "bg": f"linear-gradient(135deg, {P['green_900']} 0%, #0A2A20 100%)",
            "fg": P["paper"], "muted": "#9FBFB0", "accent": P["leaf"],
            "rule": "rgba(138,203,94,.42)", "line": "rgba(255,255,255,.14)",
            "chip_bg": "rgba(255,255,255,.10)", "chip_fg": P["leaf"],
            "wm": P["leaf"], "wm_op": "0.05",
        }
    return {
        "bg": f"linear-gradient(135deg, {P['paper']} 0%, {P['cream']} 100%)",
        "fg": P["green_900"], "muted": P["muted"], "accent": P["green_700"],
        "rule": "rgba(27,90,70,.30)", "line": "rgba(27,90,70,.14)",
        "chip_bg": "rgba(27,90,70,.09)", "chip_fg": P["green_700"],
        "wm": P["green_700"], "wm_op": "0.055",
    }


def mark(dark: bool, size: int) -> str:
    """배경 위에 얹는 잎 마크(배경판 없는 버전에 색만 맞춘다)."""
    svg = logomark_svg(size, "plain")
    if dark:
        return (svg.replace(f'fill="{P["green_700"]}"', f'fill="{P["leaf"]}"')
                   .replace(f'stroke="{P["cream"]}"', f'stroke="{P["green_900"]}"'))
    return svg


def watermark(w: int, h: int, t: dict[str, str]) -> str:
    """배경에 크게 깔리는 잎.

    크기는 가로·세로 중 짧은 쪽을 기준으로 잡는다. 세로로 긴 상세페이지에서
    세로를 기준 삼으면 잎이 화면을 넘어가 톱니만 어지럽게 남는다.
    """
    unit = min(w, h)
    length = unit * 1.45
    d = leaf_path(w * 0.90, h * 0.88, length, length * 0.62,
                  teeth=13, depth=0.055, tilt=16)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" style="position:absolute;inset:0;'
            f'pointer-events:none"><path d="{d}" fill="{t["wm"]}" '
            f'fill-opacity="{t["wm_op"]}"/></svg>')


def chip(text: str, t: dict[str, str], px: float) -> str:
    return (f'<span class="chip" style="background:{t["chip_bg"]};color:{t["chip_fg"]};'
            f'padding:{px * 0.52:.0f}px {px * 1.05:.0f}px;font-size:{px:.0f}px;'
            f'margin-right:{px * 0.55:.0f}px">{text}</span>')


def rule(t: dict[str, str], width: str = "100%", thickness: float = 1) -> str:
    return f'<div style="width:{width};height:{thickness}px;background:{t["rule"]}"></div>'


def stage(inner: str, *, dark: bool, w: int, h: int, wm: bool = True) -> str:
    t = theme(dark)
    return (f'<div class="stage" style="background:{t["bg"]}">'
            f'{watermark(w, h, t) if wm else ""}'
            f'<div style="position:relative;width:100%;height:100%">{inner}</div></div>')


def signature(px: float, dark: bool) -> str:
    t = theme(dark)
    return f"""<div style="display:flex;align-items:center;gap:{px * 0.5:.0f}px">
      <div style="width:{px:.0f}px;line-height:0">{mark(dark, int(px))}</div>
      <div class="wm" style="font-size:{px * 0.72:.0f}px;color:{t['fg']}">{BRAND_EN}</div>
      <div class="sans" style="font-size:{px * 0.44:.0f}px;color:{t['muted']};
           letter-spacing:.06em">{BRAND_KO}</div>
    </div>"""


def shot(name: str) -> str:
    """실제 자료 예시 이미지. 파일이 없으면 빈 문자열."""
    path = SAMPLES / name
    if not name or not path.exists():
        return ""
    return (f'<img src="{path.as_uri()}" style="display:block;width:100%;'
            f'border-radius:10px;box-shadow:0 6px 22px rgba(14,31,26,.16)">')


def shot_crop(name: str, out: Path, width: int, ratio: float = 0.72) -> str:
    """예시 이미지의 윗부분만 잘라 목록용 썸네일로 만든다."""
    src = SAMPLES / name
    if not name or not src.exists():
        return ""
    from PIL import Image

    with Image.open(src) as im:
        rgb = im.convert("RGB")
        h = min(rgb.height, int(rgb.width * ratio))
        out.parent.mkdir(parents=True, exist_ok=True)
        rgb.crop((0, 0, rgb.width, h)).resize(
            (width, round(h * width / rgb.width)), Image.LANCZOS).save(out)
    return out.name


def sample_height(name: str, width: int) -> int:
    """예시 이미지를 width 로 놓았을 때의 세로 픽셀."""
    from PIL import Image

    with Image.open(SAMPLES / name) as im:
        return round(width * im.height / im.width)


# ── 브랜드 기본 ───────────────────────────────────────────────────────────
def build_profile(size: int, dark: bool = True) -> str:
    """프로필 — 심볼과 Ortica 만. 원형으로 잘려도 안전하게 가운데로 모은다."""
    s, t = size, theme(dark)
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      align-items:center;justify-content:center">
      <div style="width:{s * 0.50:.0f}px;line-height:0">{mark(dark, int(s * 0.50))}</div>
      <div class="wm" style="margin-top:{s * 0.045:.0f}px;font-size:{s * 0.150:.0f}px;
           color:{t['fg']}">{BRAND_EN}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=s, h=s, wm=False), CSS, s, s)


def build_title(width: int, height: int, dark: bool = True) -> str:
    """네이버 블로그 타이틀 (가로 966px 고정 영역)."""
    h, t = height, theme(dark)
    chips = "".join(chip(k, t, h * 0.055) for k in KEYWORDS)
    inner = f"""<div style="height:100%;display:flex;align-items:center;
      padding:0 {h * 0.19:.0f}px">
      <div style="width:{h * 0.44:.0f}px;flex:0 0 auto;line-height:0">
        {mark(dark, int(h * 0.44))}</div>
      <div style="flex:0 0 auto;margin-left:{h * 0.10:.0f}px">
        <div class="wm" style="font-size:{h * 0.235:.0f}px;color:{t['fg']}">{BRAND_EN}</div>
        <div class="ko" style="margin-top:{h * 0.035:.0f}px;font-size:{h * 0.070:.0f}px;
             color:{t['accent']}">{BRAND_KO}</div>
      </div>
      <div style="flex:1 1 auto;margin-left:{h * 0.085:.0f}px;
           padding-left:{h * 0.085:.0f}px;border-left:1px solid {t['rule']};
           display:flex;flex-direction:column;justify-content:center">
        <div class="ko" style="font-size:{h * 0.075:.0f}px;color:{t['fg']}">{CONCEPT}</div>
        <div class="sans" style="margin-top:{h * 0.028:.0f}px;font-size:{h * 0.050:.0f}px;
             color:{t['muted']}">{TAGLINE}</div>
        <div style="margin-top:{h * 0.045:.0f}px">{chips}</div>
      </div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_cover(width: int, height: int, dark: bool = True) -> str:
    """모바일 홈 커버 — 가장자리는 기기별로 잘리므로 가운데 안전영역에만."""
    h, t = height, theme(dark)
    chips = "".join(chip(k, t, h * 0.026) for k in KEYWORDS)
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      align-items:center;justify-content:center;text-align:center">
      <div style="width:{h * 0.19:.0f}px;line-height:0">{mark(dark, int(h * 0.19))}</div>
      <div class="wm" style="margin-top:{h * 0.030:.0f}px;font-size:{h * 0.115:.0f}px;
           color:{t['fg']}">{BRAND_EN}</div>
      <div class="ko" style="margin-top:{h * 0.018:.0f}px;font-size:{h * 0.040:.0f}px;
           color:{t['accent']};letter-spacing:.14em">{BRAND_KO}</div>
      <div style="width:{h * 0.11:.0f}px;height:2px;background:{P['gold']};
           margin:{h * 0.038:.0f}px auto"></div>
      <div class="ko" style="font-size:{h * 0.048:.0f}px;color:{t['fg']}">{CONCEPT}</div>
      <div class="sans" style="margin-top:{h * 0.022:.0f}px;font-size:{h * 0.032:.0f}px;
           color:{t['muted']}">{TAGLINE}</div>
      <div style="margin-top:{h * 0.045:.0f}px">{chips}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_logo_horizontal(width: int, height: int, dark: bool = False) -> str:
    """배경 투명 가로형 로고."""
    h, t = height, theme(dark)
    inner = f"""<div style="width:100%;height:100%;display:flex;align-items:center;
      justify-content:center;gap:{h * 0.16:.0f}px;background:transparent">
      <div style="width:{h * 0.78:.0f}px;line-height:0">{mark(dark, int(h * 0.78))}</div>
      <div>
        <div class="wm" style="font-size:{h * 0.44:.0f}px;color:{t['fg']}">{BRAND_EN}</div>
        <div class="ko" style="margin-top:{h * 0.06:.0f}px;font-size:{h * 0.135:.0f}px;
             color:{t['accent']}">{BRAND_KO}</div>
      </div>
    </div>"""
    return page(f'<div class="stage" style="background:transparent">{inner}</div>',
                CSS, width, height)


def build_favicon(size: int) -> str:
    return page(f'<div class="stage">{logomark_svg(size, "dark")}</div>', CSS, size, size)


# ── 라인업 (실제 자료 예시 포함) ──────────────────────────────────────────
def build_lineup(width: int, items, *, heading: str, caption: str,
                 dark: bool = True, thumb_w: int = 320) -> tuple[str, int]:
    """자료 목록. 각 줄에 실제 산출물 썸네일을 함께 보여 준다."""
    u = width / 100
    t = theme(dark)
    rows, height = [], int(u * 30)

    for it in items:
        thumb = ""
        if it.sample:
            name = shot_crop(it.sample, OUT / "thumbs" / f"t-{it.key}.png", thumb_w)
            if name:
                thumb = (f'<img src="{(OUT / "thumbs" / name).as_uri()}" '
                         f'style="width:100%;display:block;border-radius:8px;'
                         f'box-shadow:0 4px 16px rgba(14,31,26,.22)">')
        if not thumb:
            thumb = (f'<div style="width:100%;height:{u * 21:.0f}px;border-radius:8px;'
                     f'border:1px dashed {t["rule"]};display:flex;align-items:center;'
                     f'justify-content:center"><span class="sans" '
                     f'style="font-size:{u * 1.7:.0f}px;color:{t["muted"]}">'
                     f'예시 준비 중</span></div>')

        pts = "".join(
            f'<div class="sans" style="font-size:{u * 1.8:.0f}px;color:{t["muted"]};'
            f'line-height:1.68;padding-left:{u * 1.6:.0f}px;position:relative;'
            f'word-break:keep-all;margin-top:{u * .6:.0f}px">'
            f'<span style="position:absolute;left:0;color:{t["accent"]}">·</span>'
            f'<b style="color:{t["fg"]};font-weight:700">{head}</b> — {desc}</div>'
            for head, desc in it.points[:4])

        rows.append(f"""<div style="display:flex;gap:{u * 3.2:.0f}px;
          padding:{u * 3.4:.0f}px 0;border-top:1px solid {t['line']}">
          <div style="flex:0 0 {u * 31:.0f}px">{thumb}</div>
          <div style="flex:1 1 auto">
            <div style="display:flex;align-items:baseline;gap:{u * 1.4:.0f}px">
              <div class="wm" style="font-size:{u * 2.0:.0f}px;color:{t['accent']}">{it.no}</div>
              <div class="ko" style="font-size:{u * 3.5:.0f}px;color:{t['fg']}">{it.name}</div>
            </div>
            <div class="sans" style="margin-top:{u * 1.0:.0f}px;font-size:{u * 2.0:.0f}px;
                 color:{t['fg']};line-height:1.65;word-break:keep-all;opacity:.9">
              {it.one_line}</div>
            <div style="margin-top:{u * 1.2:.0f}px">{pts}</div>
          </div>
        </div>""")
        height += int(u * (16 + 4.6 * len(it.points[:4])))

    inner = f"""<div style="display:flex;flex-direction:column;
      padding:{u * 6.5:.0f}px {u * 6.5:.0f}px {u * 4.5:.0f}px">
      <div>
        <div class="ko" style="font-size:{u * 5.4:.0f}px;color:{t['fg']}">{heading}</div>
        <div class="sans" style="margin-top:{u * 1.6:.0f}px;font-size:{u * 2.05:.0f}px;
             color:{t['muted']};line-height:1.7;word-break:keep-all">{caption}</div>
      </div>
      <div>{''.join(rows)}</div>
      <div style="display:flex;justify-content:center;padding-top:{u * 4:.0f}px">
        {signature(u * 3.2, dark)}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height), height


# ── 상세페이지 ────────────────────────────────────────────────────────────
def build_hero(item, width: int, height: int, dark: bool = True) -> str:
    u = width / 100
    t = theme(dark)
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      justify-content:space-between;padding:{u * 8:.0f}px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>{chip(item.no, t, u * 1.9)}</div>
        <div class="sans" style="font-size:{u * 1.7:.0f}px;color:{t['muted']};
             letter-spacing:.08em">{TAGLINE}</div>
      </div>
      <div>
        <div style="width:{u * 10:.0f}px;line-height:0;margin-bottom:{u * 3:.0f}px">
          {mark(dark, int(u * 10))}</div>
        <div class="ko" style="font-size:{u * 8.4:.0f}px;color:{t['fg']};line-height:1.26;
             word-break:keep-all">{item.name}</div>
        <div style="margin:{u * 3:.0f}px 0">{rule(t, f"{u * 12:.0f}px", 2)}</div>
        <div class="sans" style="font-size:{u * 2.5:.0f}px;color:{t['muted']};
             line-height:1.75;word-break:keep-all;max-width:{u * 74:.0f}px">
          {item.one_line}</div>
      </div>
      <div>{signature(u * 3.4, dark)}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_points(item, width: int, dark: bool = False) -> tuple[str, int]:
    """구성 설명 + 실제 산출물 예시."""
    u = width / 100
    t = theme(dark)
    rows = "".join(f"""<div style="display:flex;gap:{u * 2.6:.0f}px;
      padding:{u * 2.3:.0f}px 0;border-top:1px solid {t['line']}">
      <div class="wm" style="flex:0 0 {u * 4.5:.0f}px;font-size:{u * 2.2:.0f}px;
           color:{t['accent']};padding-top:{u * .4:.0f}px">{i:02d}</div>
      <div style="flex:1 1 auto">
        <div class="ko" style="font-size:{u * 2.7:.0f}px;color:{t['fg']}">{head}</div>
        <div class="sans" style="margin-top:{u * .9:.0f}px;font-size:{u * 2.0:.0f}px;
             color:{t['muted']};line-height:1.75;word-break:keep-all">{desc}</div>
      </div>
    </div>""" for i, (head, desc) in enumerate(item.points, 1))

    sample_block, sample_px = "", 0
    img = shot(item.sample)
    if img:
        inner_w = width - int(u * 15)
        sample_px = sample_height(item.sample, inner_w) + int(u * 11)
        sample_block = f"""<div style="margin-top:{u * 4:.0f}px">
          <div class="ko" style="font-size:{u * 2.4:.0f}px;color:{t['fg']};
               margin-bottom:{u * 1.5:.0f}px">실제 자료 예시</div>
          {img}
          <div class="sans" style="margin-top:{u * 1.3:.0f}px;font-size:{u * 1.75:.0f}px;
               color:{t['muted']};line-height:1.6;word-break:keep-all">
            {item.sample_note}</div>
        </div>"""

    inner = f"""<div style="display:flex;flex-direction:column;padding:{u * 7.5:.0f}px">
      <div>
        <div class="ko" style="font-size:{u * 4.4:.0f}px;color:{t['fg']}">{item.name} 구성</div>
        <div class="sans" style="margin-top:{u * 1.6:.0f}px;font-size:{u * 2.05:.0f}px;
             color:{t['muted']};line-height:1.75;word-break:keep-all">{item.lead}</div>
      </div>
      <div style="margin-top:{u * 3:.0f}px">{rows}</div>
      {sample_block}
      <div style="display:flex;justify-content:center;padding-top:{u * 4:.0f}px">
        {signature(u * 3.0, dark)}</div>
    </div>"""
    h = int(u * (44 + 12.0 * len(item.points))) + sample_px
    return page(stage(inner, dark=dark, w=width, h=h), CSS, width, h), h


def build_spec(item, width: int, dark: bool = True) -> tuple[str, int]:
    u = width / 100
    t = theme(dark)
    specs = "".join(f"""<div style="display:flex;padding:{u * 2.0:.0f}px 0;
      border-top:1px solid {t['line']}">
      <div class="sans" style="flex:0 0 {u * 20:.0f}px;font-size:{u * 1.95:.0f}px;
           color:{t['accent']};letter-spacing:.04em">{k}</div>
      <div class="sans" style="flex:1 1 auto;font-size:{u * 2.2:.0f}px;color:{t['fg']}">{v}</div>
    </div>""" for k, v in item.spec)
    who = "".join(f"""<div class="sans" style="font-size:{u * 2.05:.0f}px;color:{t['muted']};
      line-height:1.85;padding-left:{u * 2.4:.0f}px;position:relative;word-break:keep-all">
      <span style="position:absolute;left:0;color:{t['accent']}">·</span>{w}</div>"""
      for w in item.who)
    price = ""
    if item.price:
        price = f"""<div style="margin-top:{u * 3.6:.0f}px;padding-top:{u * 3:.0f}px;
          border-top:1px solid {t['line']}">
          <div class="ko" style="font-size:{u * 2.0:.0f}px;color:{t['accent']}">가격</div>
          <div class="wm" style="margin-top:{u * 1.2:.0f}px;font-size:{u * 4.4:.0f}px;
               color:{t['fg']}">{item.price}</div>
          <div class="sans" style="margin-top:{u * .9:.0f}px;font-size:{u * 1.8:.0f}px;
               color:{t['muted']}">{item.price_note}</div>
        </div>"""
    inner = f"""<div style="display:flex;flex-direction:column;padding:{u * 7.5:.0f}px">
      <div class="ko" style="font-size:{u * 4.2:.0f}px;color:{t['fg']}">자료 안내</div>
      <div style="margin-top:{u * 3.2:.0f}px">{specs}</div>
      <div style="margin-top:{u * 4.2:.0f}px">
        <div class="ko" style="font-size:{u * 2.4:.0f}px;color:{t['accent']}">이런 분께</div>
        <div style="margin-top:{u * 1.5:.0f}px">{who}</div>
      </div>
      {price}
      <div style="display:flex;justify-content:center;padding-top:{u * 4.5:.0f}px">
        {signature(u * 3.0, dark)}</div>
    </div>"""
    h = int(u * (40 + 6.2 * len(item.spec) + 5.4 * len(item.who) + (16 if item.price else 0)))
    return page(stage(inner, dark=dark, w=width, h=h), CSS, width, h), h


# ── 포스트 썸네일 ─────────────────────────────────────────────────────────
def build_thumb(width: int, height: int, title: str, sub: str = "", tag: str = "",
                dark: bool = True, number: str = "") -> str:
    u = min(width, height) / 100
    t = theme(dark)
    rows = [r.strip() for r in re.split(r"<br\s*/?>", title) if r.strip()]
    longest = max((len(r) for r in rows), default=1)
    weight = max(len(rows), longest / 12)
    size = u * (10.0 if weight <= 2 else 8.8 if weight <= 3 else 7.4 if weight <= 4 else 6.4)

    top = []
    if tag:
        top.append(chip(tag, t, u * 2.0))
    if number:
        top.append(f'<span class="wm" style="font-size:{u * 2.2:.0f}px;color:{P["gold"]};'
                   f'letter-spacing:.10em">{number}</span>')
    sub_el = (f'<div class="sans" style="margin-top:{u * 3:.0f}px;font-size:{u * 2.6:.0f}px;'
              f'color:{t["muted"]};line-height:1.7;word-break:keep-all">{sub}</div>') if sub else ""

    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      justify-content:space-between;padding:{u * 8.5:.0f}px">
      <div style="display:flex;align-items:center">{''.join(top)}</div>
      <div>
        <div class="ko" style="font-size:{size:.0f}px;color:{t['fg']};line-height:1.36;
             word-break:keep-all">{title}</div>
        {sub_el}
      </div>
      <div>{signature(u * 3.4, dark)}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


# ── 블로그 원고 초안 ──────────────────────────────────────────────────────
POSTS = HERE / "posts"


def write_posts() -> list[Path]:
    POSTS.mkdir(exist_ok=True)
    made = []

    def img(name: str) -> str:
        return f"![]({name})\n<!-- 이미지: brand/assets/{name} -->"

    for it in MATERIALS + BOOKS:
        pts = "\n\n".join(f"**{h}**\n\n{d}" for h, d in it.points)
        who = "\n".join(f"- {w}" for w in it.who)
        spec = "\n".join(f"- {k} — {v}" for k, v in it.spec)
        sample = (f"\n{img('samples/' + it.sample)}\n\n{it.sample_note}\n" if it.sample
                  else "\n<!-- 실제 자료 화면 캡처를 여기에 넣으세요 -->\n")
        md = f"""# {it.name}

{img(f'detail-{it.key}-1-hero.png')}

{it.lead}

## 무엇이 들어 있나

{pts}

## 실제 자료 예시
{sample}
<!-- ▼ 직접 채울 곳 (VOICE.md §4) ─────────────────────────────
   · 이 자료를 만들게 된 계기가 된 구체적인 순간 한 문단
   · 수업에서 써 본 결과 — 학생 반응이나 바뀐 점
   · 만들면서 버린 버전 이야기
────────────────────────────────────────────────────── -->

## 구성

{spec}

## 이런 분께

{who}

<!-- 가격과 구매 방법(링크·계좌·폼)을 여기에 넣으세요 -->
"""
        (POSTS / f"{it.no.lower()}-{it.key}.md").write_text(md, encoding="utf-8")
        made.append(POSTS / f"{it.no.lower()}-{it.key}.md")

    rows = "\n".join(f"**{it.no}. {it.name}** — {it.one_line}\n" for it in MATERIALS)
    brows = "\n".join(f"**{it.name}** — {it.one_line}\n" for it in BOOKS)
    (POSTS / "00-lineup.md").write_text(f"""# 자료 라인업

{img('lineup-materials.png')}

{rows}

# 제작 교재 · 고3

{img('lineup-books.png')}

{brows}

<!-- 가격은 brand/catalog.py 의 price 에 넣으면 상세페이지에 함께 나옵니다. -->
""", encoding="utf-8")
    made.append(POSTS / "00-lineup.md")
    return made


# ── 실행 ──────────────────────────────────────────────────────────────────
def emit(made: list[Path], name: str, html: str, w: int, h: int) -> None:
    made.append(html_to_png(html, OUT / name, w, h))
    print(f"  ✔ {name}  ({w}×{h})")


def build_all() -> list[Path]:
    made: list[Path] = []

    print("브랜드 기본")
    emit(made, "profile-naver-161.png", build_profile(161), 161, 161)
    emit(made, "profile-400.png", build_profile(400), 400, 400)
    emit(made, "profile-light-400.png", build_profile(400, dark=False), 400, 400)
    emit(made, "title-966x300-dark.png", build_title(966, 300), 966, 300)
    emit(made, "title-966x300-light.png", build_title(966, 300, dark=False), 966, 300)
    emit(made, "title-966x200-dark.png", build_title(966, 200), 966, 200)
    emit(made, "cover-mobile-1200x900.png", build_cover(1200, 900), 1200, 900)
    emit(made, "logo-horizontal-light-bg.png", build_logo_horizontal(1200, 300), 1200, 300)
    emit(made, "logo-horizontal-dark-bg.png",
         build_logo_horizontal(1200, 300, dark=True), 1200, 300)
    for n in (32, 180, 512):
        emit(made, f"favicon-{n}.png", build_favicon(n), n, n)

    print("라인업")
    html, h = build_lineup(DOC_W, MATERIALS, heading="자료 라인업",
                           caption="지문 한 장을 어디까지 쓸 수 있는지에 맞춰 여섯 갈래로 "
                                   "나눴습니다. 옆에 붙인 이미지는 모두 실제 출력물입니다.")
    emit(made, "lineup-materials.png", html, DOC_W, h)
    html, h = build_lineup(DOC_W, BOOKS, heading="제작 교재 · 고3",
                           caption="수업에서 직접 쓰면서 다듬은 교재입니다. "
                                   "고3과 N수생을 기준으로 만들었습니다.", dark=False)
    emit(made, "lineup-books.png", html, DOC_W, h)

    print("상세페이지")
    for it in MATERIALS + BOOKS:
        dark = it.key not in {"workbook", "voca", "syntax"}
        emit(made, f"detail-{it.key}-1-hero.png",
             build_hero(it, DOC_W, 1100, dark=dark), DOC_W, 1100)
        html, h = build_points(it, DOC_W, dark=not dark)
        emit(made, f"detail-{it.key}-2-points.png", html, DOC_W, h)
        html, h = build_spec(it, DOC_W, dark=dark)
        emit(made, f"detail-{it.key}-3-spec.png", html, DOC_W, h)

    print("포스트 썸네일 샘플")
    emit(made, "thumb-800-sample.png",
         build_thumb(800, 800, "빈칸추론이 안 풀리는<br>진짜 이유 세 가지",
                     sub="지문 구조부터 다시 보는 독해법", tag="수능 독해", number="No.01"),
         800, 800)
    emit(made, "thumb-og-1200x630-sample.png",
         build_thumb(1200, 630, "고3 3월 학평<br>전 지문 어휘 정리",
                     sub="시험에 나온 순서 그대로", tag="내신 · 모의고사", dark=False),
         1200, 630)
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description="Ortica 블로그 이미지 생성")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("all", help="전체 세트 생성")
    sub.add_parser("posts", help="블로그 원고 초안만 다시 생성")

    one = sub.add_parser("item", help="자료 하나의 상세페이지만 다시 생성")
    one.add_argument("key", help=f"자료 키 ({', '.join(BY_KEY)})")

    t = sub.add_parser("thumb", help="포스트 썸네일 1장 생성")
    t.add_argument("--title", required=True, help="제목. 줄바꿈은 <br>")
    t.add_argument("--sub", default="")
    t.add_argument("--tag", default="")
    t.add_argument("--number", default="")
    t.add_argument("--size", default="800x800")
    t.add_argument("--light", action="store_true", help="밝은 배경으로")
    t.add_argument("--out", default="")

    args = ap.parse_args()
    if args.cmd == "thumb":
        w, h = (int(v) for v in args.size.lower().split("x"))
        out = Path(args.out) if args.out else OUT / "thumb.png"
        html_to_png(build_thumb(w, h, args.title, args.sub, args.tag,
                                dark=not args.light, number=args.number), out, w, h)
        print(f"✔ {out}  ({w}×{h})")
        return

    if args.cmd == "posts":
        for f in write_posts():
            print(f"  ✔ {f.name}")
        return

    if args.cmd == "item":
        it = BY_KEY[args.key]
        made: list[Path] = []
        emit(made, f"detail-{it.key}-1-hero.png", build_hero(it, DOC_W, 1100), DOC_W, 1100)
        html, h = build_points(it, DOC_W, dark=False)
        emit(made, f"detail-{it.key}-2-points.png", html, DOC_W, h)
        html, h = build_spec(it, DOC_W)
        emit(made, f"detail-{it.key}-3-spec.png", html, DOC_W, h)
        return

    made = build_all()
    posts = write_posts()
    print(f"\n이미지 {len(made)}개 → {OUT}")
    print(f"원고 초안 {len(posts)}개 → {POSTS}")


if __name__ == "__main__":
    main()
