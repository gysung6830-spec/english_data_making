"""Ortica 블로그 이미지 생성기.

    python brand/fonts/fetch_fonts.py    # 최초 1회 (글꼴 내려받기)
    pip install pillow                   # 최초 1회
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
    SANS_KO,
    SERIF_KO,
    SERIF_LATIN,
    crest,
    grain,
    leaf_engraved,
    leaf_solid,
    leaf_watermark,
)
from render import html_to_png, page  # noqa: E402

OUT = Path(__file__).resolve().parent / "assets"

BRAND_EN = "ORTICA"
BRAND_KO = "오르티카 영어"
TAGLINE = "수능 · 내신 영어 자료 연구"

# 블로그 본문 폭에 맞춘 기본 가로. 네이버 본문은 이 정도에서 가장 선명하다.
DOC_W = 900

CSS = f"""
body {{ font-family: {SANS_KO}; }}
.stage {{ position:relative; width:100%; height:100%; overflow:hidden; }}
.ink {{ background:{P['ink']}; color:{P['paper']}; }}
.paper {{ background:{P['paper_hi']}; color:{P['forest']}; }}
.wm {{ font-family:{SERIF_LATIN}; font-weight:500; }}
.ko {{ font-family:{SERIF_KO}; font-weight:700; }}
.ko-r {{ font-family:{SERIF_KO}; font-weight:400; }}
.sans {{ font-family:{SANS_KO}; font-weight:400; }}
.label {{ font-family:{SANS_KO}; font-weight:600; text-transform:uppercase; }}
.num {{ font-family:{SERIF_LATIN}; font-weight:400; }}
.hr {{ border:0; border-top:1px solid currentColor; opacity:.28; margin:0; }}
.center {{ text-align:center; }}
"""


# ── 공통 조각 ─────────────────────────────────────────────────────────────
def wordmark(px: float, color: str, track: float = 0.30) -> str:
    return (f'<div class="wm" style="font-size:{px:.0f}px;color:{color};'
            f'letter-spacing:{track}em;line-height:1;text-indent:{track}em">{BRAND_EN}</div>')


def small_caps(text: str, px: float, color: str, track: float = 0.28) -> str:
    return (f'<div class="label" style="font-size:{px:.0f}px;color:{color};'
            f'letter-spacing:{track}em">{text}</div>')


def gold_rule(width: str, thickness: float = 1.0, opacity: float = 0.65,
              margin: str = "0") -> str:
    return (f'<div style="width:{width};height:{thickness}px;background:{P["gold"]};'
            f'opacity:{opacity};margin:{margin}"></div>')


def signature(px: float, dark: bool, gap: float = 0.55) -> str:
    """푸터용 작은 서명 — 잎 + ORTICA + 한글."""
    line = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    return f"""<div style="display:flex;align-items:center;gap:{px * gap:.0f}px">
      <div style="width:{px:.0f}px;line-height:0">{leaf_engraved(int(px), P['gold'], stroke=0.032)}</div>
      <div class="wm" style="font-size:{px * 0.62:.0f}px;color:{line};letter-spacing:.24em">{BRAND_EN}</div>
      <div class="sans" style="font-size:{px * 0.36:.0f}px;color:{sub};letter-spacing:.10em">{BRAND_KO}</div>
    </div>"""


def stage(inner: str, *, dark: bool, pad: str = "0", extra: str = "",
          w: int = 0, h: int = 0, wm: bool = True) -> str:
    """공통 무대 — 배경 + 잎 워터마크 + 종이 결."""
    cls = "ink" if dark else "paper"
    wm_el = ""
    if wm and w and h:
        wm_el = leaf_watermark(w, h, P["gold"] if dark else P["forest"],
                               0.15 if dark else 0.09,
                               cx=0.90, base=0.86, scale=0.98, tilt=13)
    return (f'<div class="stage {cls}" style="padding:{pad};{extra}">'
            f'{wm_el}{grain(0.05 if dark else 0.035)}'
            f'<div style="position:relative;width:100%;height:100%">{inner}</div></div>')


# ── 브랜드 기본 ───────────────────────────────────────────────────────────
def build_profile(size: int, dark: bool = True) -> str:
    s = size
    fg = P["paper"] if dark else P["forest"]
    body_inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      align-items:center;justify-content:center">
      <div style="line-height:0">{crest(int(s * 0.50), P['gold'], stroke=0.016)}</div>
      <div style="margin-top:{s * 0.045:.0f}px">{wordmark(s * 0.095, fg, 0.30)}</div>
    </div>"""
    return page(stage(body_inner, dark=dark, w=s, h=s, wm=False), CSS, s, s)


def build_title(width: int, height: int, dark: bool = False) -> str:
    """네이버 블로그 타이틀 (가로 966px 고정 영역)."""
    h = height
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    inner = f"""<div style="height:100%;display:flex;align-items:center;
      padding:0 {h * 0.22:.0f}px">
      <div style="line-height:0;flex:0 0 auto">{crest(int(h * 0.50), P['gold'], stroke=0.016)}</div>
      <div style="flex:0 0 auto;margin-left:{h * 0.13:.0f}px">
        {wordmark(h * 0.215, fg, 0.30)}
        <div style="margin-top:{h * 0.055:.0f}px">{gold_rule(f"{h * 0.42:.0f}px")}</div>
        <div class="ko-r" style="margin-top:{h * 0.055:.0f}px;font-size:{h * 0.078:.0f}px;
             color:{sub};letter-spacing:.14em">{BRAND_KO}</div>
      </div>
      <div style="flex:1 1 auto;display:flex;justify-content:flex-end;align-items:center">
        <div style="text-align:right;white-space:nowrap">
          <div class="ko" style="font-size:{h * 0.072:.0f}px;color:{fg};
               letter-spacing:.04em">{TAGLINE}</div>
          <div style="margin-top:{h * 0.042:.0f}px;display:flex;justify-content:flex-end">
            {gold_rule(f"{h * 0.24:.0f}px")}</div>
          <div class="sans" style="margin-top:{h * 0.042:.0f}px;font-size:{h * 0.042:.0f}px;
               color:{sub};letter-spacing:.10em">
            한줄해석 · 지문분석지 · 워크북 · 변형문제 · 동형모의고사</div>
        </div>
      </div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_cover(width: int, height: int, dark: bool = True) -> str:
    h = height
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      align-items:center;justify-content:center;text-align:center">
      <div style="line-height:0">{crest(int(h * 0.24), P['gold'], stroke=0.016)}</div>
      <div style="margin-top:{h * 0.045:.0f}px">{wordmark(h * 0.105, fg, 0.32)}</div>
      <div style="margin-top:{h * 0.035:.0f}px">{gold_rule(f"{h * 0.10:.0f}px")}</div>
      <div class="ko" style="margin-top:{h * 0.035:.0f}px;font-size:{h * 0.052:.0f}px;
           color:{fg};letter-spacing:.06em">{TAGLINE}</div>
      <div class="sans" style="margin-top:{h * 0.026:.0f}px;font-size:{h * 0.030:.0f}px;
           color:{sub};letter-spacing:.14em;line-height:1.9">
        한줄해석 · 지문분석지 · 워크북<br>변형문제 6종 · 동형모의고사 · 필생보</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_logo_horizontal(width: int, height: int, dark: bool = False) -> str:
    """배경 투명 가로형 로고."""
    h = height
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    inner = f"""<div style="width:100%;height:100%;display:flex;align-items:center;
      justify-content:center;gap:{h * 0.14:.0f}px">
      <div style="line-height:0">{leaf_engraved(int(h * 0.72), P['gold'], stroke=0.020)}</div>
      <div>
        {wordmark(h * 0.30, fg, 0.28)}
        <div style="margin-top:{h * 0.055:.0f}px">{gold_rule(f"{h * 0.55:.0f}px")}</div>
        <div class="ko-r" style="margin-top:{h * 0.055:.0f}px;font-size:{h * 0.105:.0f}px;
             color:{sub};letter-spacing:.16em">{BRAND_KO}</div>
      </div>
    </div>"""
    return page(f'<div class="stage" style="background:transparent">{inner}</div>',
                CSS, width, height)


def build_favicon(size: int) -> str:
    inner = (f'<div class="stage ink" style="display:flex;align-items:center;'
             f'justify-content:center">{leaf_solid(int(size * 0.74), P["gold_hi"], P["ink"])}</div>')
    return page(inner, CSS, size, size)


# ── 라인업 / 목록 ─────────────────────────────────────────────────────────
def build_index(width: int, height: int, items, *, kicker: str, heading: str,
                caption: str, dark: bool = True) -> str:
    u = width / 100  # 가로 1% 단위
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    line = "rgba(191,160,99,.30)" if dark else "rgba(22,38,31,.16)"
    rows = []
    for i, it in enumerate(items):
        rows.append(f"""<div style="display:flex;align-items:baseline;
          gap:{u * 3.4:.0f}px;padding:{u * 2.9:.0f}px 0;
          border-top:{'0' if i == 0 else f'1px solid {line}'}">
          <div class="num" style="flex:0 0 {u * 8:.0f}px;font-size:{u * 3.5:.0f}px;
               color:{P['gold']};letter-spacing:.06em">{it.no}</div>
          <div style="flex:1 1 auto">
            <div style="display:flex;align-items:baseline;gap:{u * 1.6:.0f}px">
              <div class="ko" style="font-size:{u * 4.2:.0f}px;color:{fg};
                   letter-spacing:.02em">{it.name}</div>
              <div class="wm" style="font-size:{u * 1.9:.0f}px;color:{P['gold']};
                   letter-spacing:.20em;text-transform:uppercase;opacity:.85">{it.en}</div>
            </div>
            <div class="sans" style="margin-top:{u * 1.3:.0f}px;font-size:{u * 2.15:.0f}px;
                 color:{sub};line-height:1.65;word-break:keep-all">{it.one_line}</div>
          </div>
        </div>""")
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      padding:{u * 9:.0f}px {u * 9:.0f}px {u * 7:.0f}px">
      <div>
        {small_caps(kicker, u * 1.9, P['gold'], 0.34)}
        <div class="ko" style="margin-top:{u * 2.4:.0f}px;font-size:{u * 6.4:.0f}px;
             color:{fg};letter-spacing:.02em">{heading}</div>
        <div class="sans" style="margin-top:{u * 2.0:.0f}px;font-size:{u * 2.2:.0f}px;
             color:{sub};line-height:1.7;word-break:keep-all">{caption}</div>
        <div style="margin-top:{u * 4.0:.0f}px">{gold_rule("100%", 1, .55)}</div>
      </div>
      <div style="flex:1 1 auto;display:flex;flex-direction:column;
           justify-content:center">{''.join(rows)}</div>
      <div style="display:flex;justify-content:center;padding-top:{u * 3:.0f}px">
        {signature(u * 3.4, dark)}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


# ── 상세페이지 ────────────────────────────────────────────────────────────
def build_hero(item, width: int, height: int, dark: bool = True) -> str:
    u = width / 100
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      justify-content:space-between;padding:{u * 9:.0f}px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        {small_caps(item.en, u * 1.9, P['gold'], 0.34)}
        <div class="num" style="font-size:{u * 2.4:.0f}px;color:{P['gold']};
             letter-spacing:.16em">{item.no}</div>
      </div>
      <div>
        <div style="line-height:0;margin-bottom:{u * 4:.0f}px">
          {leaf_engraved(int(u * 11), P['gold'], stroke=0.022)}</div>
        <div class="ko" style="font-size:{u * 9.2:.0f}px;color:{fg};line-height:1.22;
             letter-spacing:.01em;word-break:keep-all">{item.name}</div>
        <div style="margin:{u * 3.4:.0f}px 0">{gold_rule(f"{u * 14:.0f}px", 1, .8)}</div>
        <div class="ko-r" style="font-size:{u * 2.8:.0f}px;color:{sub};line-height:1.75;
             word-break:keep-all;max-width:{u * 76:.0f}px">{item.one_line}</div>
      </div>
      <div style="display:flex;align-items:flex-end;justify-content:space-between">
        {signature(u * 3.4, dark)}
        <div class="sans" style="font-size:{u * 1.7:.0f}px;color:{sub};
             letter-spacing:.18em">{TAGLINE}</div>
      </div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_points(item, width: int, height: int, dark: bool = False) -> str:
    u = width / 100
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    line = "rgba(191,160,99,.30)" if dark else "rgba(22,38,31,.14)"
    rows = []
    for i, (head, desc) in enumerate(item.points, 1):
        rows.append(f"""<div style="display:flex;gap:{u * 3:.0f}px;
          padding:{u * 2.6:.0f}px 0;border-top:1px solid {line}">
          <div class="num" style="flex:0 0 {u * 5:.0f}px;font-size:{u * 2.6:.0f}px;
               color:{P['gold']};padding-top:{u * .3:.0f}px">{i:02d}</div>
          <div style="flex:1 1 auto">
            <div class="ko" style="font-size:{u * 3.0:.0f}px;color:{fg};
                 letter-spacing:.01em">{head}</div>
            <div class="sans" style="margin-top:{u * 1.1:.0f}px;font-size:{u * 2.05:.0f}px;
                 color:{sub};line-height:1.72;word-break:keep-all">{desc}</div>
          </div>
        </div>""")
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      padding:{u * 8.5:.0f}px">
      <div>
        {small_caps("what's inside", u * 1.8, P['gold'], 0.32)}
        <div class="ko" style="margin-top:{u * 2.2:.0f}px;font-size:{u * 5.0:.0f}px;
             color:{fg};letter-spacing:.01em">{item.name} 구성</div>
        <div class="sans" style="margin-top:{u * 2.0:.0f}px;font-size:{u * 2.15:.0f}px;
             color:{sub};line-height:1.75;word-break:keep-all">{item.lead}</div>
      </div>
      <div style="flex:1 1 auto;display:flex;flex-direction:column;
           justify-content:center;margin-top:{u * 3:.0f}px">{''.join(rows)}</div>
      <div style="display:flex;justify-content:center">{signature(u * 3.2, dark)}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_spec(item, width: int, height: int, dark: bool = True) -> str:
    u = width / 100
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    line = "rgba(191,160,99,.30)" if dark else "rgba(22,38,31,.14)"
    specs = "".join(
        f"""<div style="display:flex;padding:{u * 2.2:.0f}px 0;border-top:1px solid {line}">
          <div class="sans" style="flex:0 0 {u * 22:.0f}px;font-size:{u * 2.0:.0f}px;
               color:{P['gold']};letter-spacing:.10em">{k}</div>
          <div class="ko-r" style="flex:1 1 auto;font-size:{u * 2.4:.0f}px;color:{fg}">{v}</div>
        </div>""" for k, v in item.spec
    )
    who = "".join(
        f"""<div class="sans" style="font-size:{u * 2.15:.0f}px;color:{sub};
          line-height:1.8;padding-left:{u * 3:.0f}px;position:relative;word-break:keep-all">
          <span style="position:absolute;left:0;color:{P['gold']}">—</span>{w}</div>"""
        for w in item.who
    )
    price_block = ""
    if item.price:
        price_block = f"""<div style="margin-top:{u * 4:.0f}px;padding-top:{u * 3.4:.0f}px;
          border-top:1px solid {line}">
          {small_caps("price", u * 1.7, P['gold'], 0.32)}
          <div class="wm" style="margin-top:{u * 1.4:.0f}px;font-size:{u * 5.4:.0f}px;
               color:{fg};letter-spacing:.02em">{item.price}</div>
          <div class="sans" style="margin-top:{u * 1.0:.0f}px;font-size:{u * 1.8:.0f}px;
               color:{sub};letter-spacing:.04em">{item.price_note}</div>
        </div>"""
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      padding:{u * 8.5:.0f}px">
      <div>
        {small_caps("details", u * 1.8, P['gold'], 0.32)}
        <div class="ko" style="margin-top:{u * 2.2:.0f}px;font-size:{u * 4.6:.0f}px;
             color:{fg}">자료 안내</div>
      </div>
      <div style="margin-top:{u * 4:.0f}px">{specs}</div>
      <div style="margin-top:{u * 5:.0f}px">
        {small_caps("for whom", u * 1.7, P['gold'], 0.32)}
        <div style="margin-top:{u * 2:.0f}px">{who}</div>
      </div>
      {price_block}
      <div style="flex:1 1 auto"></div>
      <div style="display:flex;justify-content:center">{signature(u * 3.2, dark)}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_pricetable(width: int, height: int, dark: bool = True) -> str:
    """자료·교재 가격표 한 장."""
    u = width / 100
    fg = P["paper"] if dark else P["forest"]
    sub = P["sage"] if dark else P["stone"]
    line = "rgba(191,160,99,.28)" if dark else "rgba(22,38,31,.14)"

    def block(title: str, items) -> str:
        rows = "".join(f"""<div style="display:flex;align-items:baseline;
          padding:{u * 1.9:.0f}px 0;border-top:1px solid {line}">
          <div class="ko" style="flex:0 0 {u * 30:.0f}px;font-size:{u * 2.5:.0f}px;
               color:{fg}">{it.name}</div>
          <div class="wm" style="flex:0 0 {u * 30:.0f}px;font-size:{u * 2.4:.0f}px;
               color:{P['gold_hi'] if dark else P['gold']}">{it.price}</div>
          <div class="sans" style="flex:1 1 auto;font-size:{u * 1.8:.0f}px;color:{sub};
               line-height:1.6;word-break:keep-all">{it.price_note}</div>
        </div>""" for it in items)
        return (f'<div style="margin-top:{u * 4:.0f}px">'
                f'{small_caps(title, u * 1.7, P["gold"], 0.30)}'
                f'<div style="margin-top:{u * 1.8:.0f}px">{rows}</div></div>')

    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      padding:{u * 8:.0f}px">
      <div>
        {small_caps("price", u * 1.8, P['gold'], 0.32)}
        <div class="ko" style="margin-top:{u * 2:.0f}px;font-size:{u * 5.0:.0f}px;
             color:{fg}">가격 안내</div>
        <div class="sans" style="margin-top:{u * 1.8:.0f}px;font-size:{u * 1.9:.0f}px;
             color:{sub};line-height:1.7">
          지문 단위로 낱개 구매하거나, 묶음으로 받으실 수 있습니다.</div>
      </div>
      {block("materials", MATERIALS)}
      {block("textbooks", BOOKS)}
      <div style="flex:1 1 auto"></div>
      <div style="display:flex;justify-content:center;padding-top:{u * 3:.0f}px">
        {signature(u * 3.2, dark)}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


# ── 포스트 썸네일 ─────────────────────────────────────────────────────────
def build_thumb(width: int, height: int, title: str, sub: str = "", tag: str = "",
                dark: bool = True, number: str = "") -> str:
    u = min(width, height) / 100
    fg = P["paper"] if dark else P["forest"]
    subc = P["sage"] if dark else P["stone"]
    rows = [r.strip() for r in re.split(r"<br\s*/?>", title) if r.strip()]
    longest = max((len(r) for r in rows), default=1)
    weight = max(len(rows), longest / 12)
    size = u * (9.6 if weight <= 2 else 8.4 if weight <= 3 else 7.2 if weight <= 4 else 6.2)

    top = []
    if tag:
        top.append(small_caps(tag, u * 2.0, P["gold"], 0.30))
    if number:
        top.append(f'<div class="num" style="font-size:{u * 2.3:.0f}px;color:{P["gold"]};'
                   f'letter-spacing:.14em">{number}</div>')
    top_el = (f'<div style="display:flex;align-items:center;gap:{u * 2.4:.0f}px">'
              f'{"".join(top)}</div>') if top else ""
    sub_el = (f'<div class="sans" style="margin-top:{u * 3:.0f}px;font-size:{u * 2.6:.0f}px;'
              f'color:{subc};line-height:1.7;word-break:keep-all">{sub}</div>') if sub else ""

    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      justify-content:space-between;padding:{u * 9:.0f}px">
      <div>{top_el}</div>
      <div>
        <div class="ko" style="font-size:{size:.0f}px;color:{fg};line-height:1.36;
             letter-spacing:-.005em;word-break:keep-all">{title}</div>
        {sub_el}
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        {signature(u * 3.4, dark)}
      </div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


# ── 실행 ──────────────────────────────────────────────────────────────────
def index_h(n: int) -> int:
    return 340 + n * 170


def points_h(item) -> int:
    return 560 + len(item.points) * 148


def spec_h(item) -> int:
    return 600 + len(item.spec) * 62 + len(item.who) * 58 + (170 if item.price else 0)


def emit(made: list[Path], name: str, html: str, w: int, h: int) -> None:
    made.append(html_to_png(html, OUT / name, w, h))
    print(f"  ✔ {name}  ({w}×{h})")


def build_all() -> list[Path]:
    made: list[Path] = []

    print("브랜드 기본")
    emit(made, "profile-naver-161.png", build_profile(161), 161, 161)
    emit(made, "profile-400.png", build_profile(400), 400, 400)
    emit(made, "profile-light-400.png", build_profile(400, dark=False), 400, 400)
    emit(made, "title-966x300-dark.png", build_title(966, 300, dark=True), 966, 300)
    emit(made, "title-966x300-light.png", build_title(966, 300, dark=False), 966, 300)
    emit(made, "title-966x200-dark.png", build_title(966, 200, dark=True), 966, 200)
    emit(made, "cover-mobile-1200x900.png", build_cover(1200, 900), 1200, 900)
    emit(made, "logo-horizontal-light-bg.png", build_logo_horizontal(1200, 300), 1200, 300)
    emit(made, "logo-horizontal-dark-bg.png",
         build_logo_horizontal(1200, 300, dark=True), 1200, 300)
    for n in (32, 180, 512):
        emit(made, f"favicon-{n}.png", build_favicon(n), n, n)

    print("라인업")
    h = index_h(len(MATERIALS))
    emit(made, "lineup-materials.png",
         build_index(DOC_W, h, MATERIALS, kicker="materials",
                     heading="자료 라인업",
                     caption="지문 한 장을 어디까지 쓸 수 있는지에 맞춰 여섯 갈래로 나눴습니다. "
                             "필요한 것만 골라 쓰셔도 되고, 순서대로 이어 쓰셔도 됩니다."),
         DOC_W, h)
    hb = index_h(len(BOOKS))
    emit(made, "lineup-books.png",
         build_index(DOC_W, hb, BOOKS, kicker="textbooks",
                     heading="제작 교재 · 고3",
                     caption="수업에서 직접 쓰면서 다듬은 교재입니다. 고3과 N수생을 기준으로 만들었습니다.",
                     dark=False),
         DOC_W, hb)

    ph = 480 + (len(MATERIALS) + len(BOOKS)) * 96
    emit(made, "price-table.png", build_pricetable(DOC_W, ph), DOC_W, ph)

    print("상세페이지")
    for it in MATERIALS + BOOKS:
        dark = it.key not in {"workbook", "voca", "syntax"}
        emit(made, f"detail-{it.key}-1-hero.png",
             build_hero(it, DOC_W, 1200, dark=dark), DOC_W, 1200)
        ph, sh = points_h(it), spec_h(it)
        emit(made, f"detail-{it.key}-2-points.png",
             build_points(it, DOC_W, ph, dark=not dark), DOC_W, ph)
        emit(made, f"detail-{it.key}-3-spec.png",
             build_spec(it, DOC_W, sh, dark=dark), DOC_W, sh)

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


# ── 블로그 원고 초안 ──────────────────────────────────────────────────────
POSTS = Path(__file__).resolve().parent / "posts"


def write_posts() -> list[Path]:
    """자료별 상세페이지 원고 초안을 마크다운으로 뽑는다.

    이미지 자리와 '직접 채울 곳'을 표시해 둔 뼈대다. 채우는 방법은 VOICE.md.
    """
    POSTS.mkdir(exist_ok=True)
    made = []

    def img(name: str) -> str:
        return f"![]({name})\n<!-- 이미지: brand/assets/{name} -->"

    for it in MATERIALS + BOOKS:
        pts = "\n\n".join(f"**{h}**\n\n{d}" for h, d in it.points)
        who = "\n".join(f"- {w}" for w in it.who)
        spec = "\n".join(f"- {k} — {v}" for k, v in it.spec)
        md = f"""# {it.name}

{img(f'detail-{it.key}-1-hero.png')}

{it.lead}

{img(f'detail-{it.key}-2-points.png')}

## 무엇이 들어 있나

{pts}

<!-- ▼ 직접 채울 곳 (VOICE.md §4) ─────────────────────────────
   · 이 자료를 만들게 된 계기가 된 구체적인 순간 한 문단
   · 수업에서 써 본 결과 — 학생 반응이나 바뀐 점
   · 만들면서 버린 버전 이야기
   · 자료 실물을 책상 위에 놓고 찍은 사진 1~2장
   이 자리를 비워 두면 아무리 문장을 고쳐도 AI 티가 남습니다.
────────────────────────────────────────────────────── -->

{img(f'detail-{it.key}-3-spec.png')}

## 구성

{spec}

## 이런 분께

{who}

## 가격

{it.price} — {it.price_note}

<!-- 구매 방법(링크·계좌·폼)을 여기에 넣으세요 -->
"""
        path = POSTS / f"{it.no.lower()}-{it.key}.md"
        path.write_text(md, encoding="utf-8")
        made.append(path)

    rows = "\n".join(
        f"**{it.no}. {it.name}** — {it.one_line}\n" for it in MATERIALS)
    brows = "\n".join(
        f"**{it.name}** — {it.one_line}\n" for it in BOOKS)
    index_md = f"""# 자료 라인업

{img('lineup-materials.png')}

{rows}

<!-- ▼ 직접 채울 곳: 왜 이 여섯으로 나눴는지, 어떤 순서로 쓰면 좋은지 -->

# 제작 교재 · 고3

{img('lineup-books.png')}

{brows}

# 가격

{img('price-table.png')}

<!-- 확정 전입니다. brand/PRICING.md 의 §4 를 채운 뒤 값을 고치세요. -->
"""
    path = POSTS / "00-lineup.md"
    path.write_text(index_md, encoding="utf-8")
    made.append(path)
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
        html = build_thumb(w, h, args.title, args.sub, args.tag,
                           dark=not args.light, number=args.number)
        html_to_png(html, out, w, h)
        print(f"✔ {out}  ({w}×{h})")
        return

    if args.cmd == "item":
        it = BY_KEY[args.key]
        made: list[Path] = []
        emit(made, f"detail-{it.key}-1-hero.png", build_hero(it, DOC_W, 1200), DOC_W, 1200)
        emit(made, f"detail-{it.key}-2-points.png",
             build_points(it, DOC_W, points_h(it), dark=False), DOC_W, points_h(it))
        emit(made, f"detail-{it.key}-3-spec.png",
             build_spec(it, DOC_W, spec_h(it)), DOC_W, spec_h(it))
        return

    if args.cmd == "posts":
        for f in write_posts():
            print(f"  ✔ {f.name}")
        return

    made = build_all()
    posts = write_posts()
    print(f"\n이미지 {len(made)}개 → {OUT}")
    print(f"원고 초안 {len(posts)}개 → {POSTS}")


if __name__ == "__main__":
    main()
