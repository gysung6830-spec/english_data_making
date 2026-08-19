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
from render import html_to_png, measure_height, page  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets"
SAMPLES = OUT / "samples"

BRAND_EN = "Ortica"
BRAND_KO = "오르티카 영어"
PROFILE_EN = "Ortica 영어"   # 프로필에는 영문 이름 뒤에 '영어'를 붙인다
CONCEPT = "필자의 생각이 보이는 영어"
# 소개 문구는 글줄로 반복하지 않고 칩으로만 보여 준다.
KEYWORDS = ["고등 모의고사", "내신", "수능자료 제작"]

# 네이버 본문 폭에 맞춘 기본 가로.
DOC_W = 900

# 라인업 아래에 붙는 차별화 포인트. 자료 자체의 설명이 아니라
# "왜 다른 곳 자료가 아니라 이걸 쓰는가"에 대한 답만 적는다.
EDGE_READ = [
    ("무슨 글인지 알고 시작한다",
     "지문 위에 요지 한 줄이 먼저 옵니다. 영어만 덩그러니 있는 원문과 다릅니다."),
    ("끊어읽기와 해석이 1:1",
     "영어 끊어읽기와 한글 해석의 위치를 정확히 맞췄습니다. 대충 끊은 자료와 "
     "차원이 다릅니다."),
    ("시중에 없는 함축의미 카드",
     "직역하면 놓치는 맥락을 콕 집어 줍니다. 빈칸추론·함축추론을 정면으로 "
     "대비합니다."),
]

EDGE_SIGN = [
    ("손으로 푸는 훈련서",
     "끊어읽기 빈칸을 직접 채우고 '이렇게 읽으면 오답'으로 자기 오독을 잡습니다. "
     "눈으로 읽고 넘기는 자료가 아닙니다."),
    ("재진술을 눈으로 확인",
     "같은 개념이 어떻게 바뀌어 반복되는지 형광펜으로 시각화합니다. "
     "빈칸·함의·요지의 뿌리입니다."),
    ("강의용과 독학용을 따로",
     "앞에서 설명하며 쓰는 판과 혼자 앉아 보는 판은 지면부터 달라야 합니다. "
     "독학용에는 독해 원리 12쪽이 앞에 붙습니다."),
]

EDGE_EXAM = [
    ("남들이 안 다루는 대명사 지칭",
     "it·they·this 가 무엇을 가리키는지 짚는 문항을 넣었습니다. 독해력의 실제 "
     "승부처를 그냥 넘어가지 않습니다."),
    ("오답을 평가원식 5축으로 설계",
     "범위·방향·표면 어휘·근거 없음·초점 이동. 한 끗 차이 매력적 오답을 넣어 "
     "소거법이 통하지 않습니다."),
    ("우리 학교 동형",
     "시중 문제집의 남의 시험이 아닙니다. 실제 시험지의 유형·배점·난이도·"
     "레이아웃을 그대로 재현합니다."),
]

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


def autosize(make, width: int, pad: int, max_height: int = 6000) -> tuple[str, int]:
    """내용 높이를 브라우저에 재게 하고 그 높이로 다시 그린다.

    make(height, tail) 은 본문 맨 끝에 tail 을 붙인 HTML 을 돌려준다.
    """
    h = measure_height(lambda mark: make(max_height, mark), width, max_height) + pad
    return make(h, ""), h


# ── 브랜드 기본 ───────────────────────────────────────────────────────────
def build_profile(size: int, dark: bool = True, box_h: int = 0,
                  with_name: bool = True, name_text: str = "") -> str:
    """프로필.

    with_name=True  : 심볼 + 'Ortica 영어' + '오르티카 영어'
    with_name=False : 심볼만. 네이버 앱에서는 프로필이 지름 60px 남짓한 원으로
                      줄어드는데, 그 크기에서 두 줄짜리 글자는 뭉개진다.
                      글자를 빼고 잎을 키우면 작아져도 형태가 남는다.

    box_h 를 주면 세로가 긴 판(사이드바 스킨용)으로 만든다.
    name_text 로 윗줄 글자를 갈아 끼운다(기본 'Ortica 영어').
    """
    s, t = size, theme(dark)
    h = box_h or size
    title = name_text or PROFILE_EN
    if not with_name:
        inner = f"""<div style="height:100%;display:flex;align-items:center;
          justify-content:center">
          <div style="width:{s * 0.66:.0f}px;line-height:0">{mark(dark, int(s * 0.66))}</div>
        </div>"""
        return page(stage(inner, dark=dark, w=s, h=h, wm=False), CSS, s, h)

    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      align-items:center;justify-content:center">
      <div style="width:{s * 0.42:.0f}px;line-height:0">{mark(dark, int(s * 0.42))}</div>
      <div class="wm" style="margin-top:{s * 0.048:.0f}px;font-size:{s * 0.135:.0f}px;
           color:{t['fg']}">{title}</div>
      <div class="ko" style="margin-top:{s * 0.028:.0f}px;font-size:{s * 0.072:.0f}px;
           color:{t['accent']};letter-spacing:.08em">{BRAND_KO}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=s, h=h, wm=False), CSS, s, h)


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
        <div class="ko" style="font-size:{h * 0.082:.0f}px;color:{t['fg']}">{CONCEPT}</div>
        <div style="margin-top:{h * 0.060:.0f}px">{chips}</div>
      </div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_title_tall(width: int, height: int, dark: bool = True) -> str:
    """세로가 넉넉한 블로그 타이틀 (가로 966px, 세로 400~600px).

    네이버 타이틀 영역은 세로를 600px까지 늘릴 수 있다. 크게 쓰면 배너처럼
    보여서 브랜드가 먼저 읽힌다.
    """
    h, t = height, theme(dark)
    chips = "".join(chip(k, t, h * 0.032) for k in KEYWORDS)
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      align-items:center;justify-content:center;text-align:center">
      <div style="width:{h * 0.21:.0f}px;line-height:0">{mark(dark, int(h * 0.21))}</div>
      <div class="wm" style="margin-top:{h * 0.035:.0f}px;font-size:{h * 0.125:.0f}px;
           color:{t['fg']}">{PROFILE_EN}</div>
      <div class="ko" style="margin-top:{h * 0.022:.0f}px;font-size:{h * 0.042:.0f}px;
           color:{t['accent']};letter-spacing:.16em">{BRAND_KO}</div>
      <div style="width:{h * 0.10:.0f}px;height:2px;background:{P['gold']};
           margin:{h * 0.045:.0f}px auto"></div>
      <div class="ko" style="font-size:{h * 0.058:.0f}px;color:{t['fg']}">{CONCEPT}</div>
      <div style="margin-top:{h * 0.058:.0f}px">{chips}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_cover_backdrop(width: int, height: int, dark: bool = True) -> str:
    """네이버 모바일 홈 커버 — **글자 없는 배경**.

    네이버가 이 이미지 위에 블로그 제목·프로필·이웃수·홈편집 버튼을 직접
    그린다. 이미지에 글자를 넣으면 그 위에 또 글자가 얹혀 겹친다. 그래서
    여기서는 결만 깔고 글자는 네이버에 맡긴다.

    기기마다 잘리는 위치가 달라(아이패드는 가운데 가로 띠만 보인다) 특정
    자리에 그림을 몰지 않고 잎을 흩어 놓는다. 아래쪽은 흰 글자가 얹히므로
    한 겹 어둡게 눌러 둔다.
    """
    import random

    t = theme(dark)
    unit = min(width, height)
    rng = random.Random(7)          # 고정 시드 — 다시 돌려도 같은 그림이 나온다

    # 흔들린 격자 위에 작은 잎을 흩는다. 기기마다 잘리는 자리가 달라서
    # (아이패드는 가운데 가로 띠만 보인다) 한 곳에 그림을 몰지 않는다.
    cols, rows = 5, 4
    parts = []
    for r in range(rows):
        for c in range(cols):
            cx = (c + 0.5) / cols + rng.uniform(-0.07, 0.07)
            cy = (r + 0.5) / rows + rng.uniform(-0.09, 0.09)
            sc = rng.uniform(0.085, 0.165)
            tilt = rng.uniform(-40, 40)
            op = rng.uniform(0.045, 0.095)
            parts.append((cx, cy, sc, tilt, op))
    leaves = "".join(
        f'<path d="{leaf_path(width * cx, height * cy + unit * sc * 0.5, unit * sc, unit * sc * 0.62, teeth=11, depth=0.07, tilt=tilt)}" '
        f'fill="{t["wm"]}" fill-opacity="{op:.3f}"/>'
        for cx, cy, sc, tilt, op in parts
    )
    shade = ("linear-gradient(180deg, rgba(0,0,0,0) 45%, rgba(0,0,0,.30) 100%)"
             if dark else
             "linear-gradient(180deg, rgba(0,0,0,0) 45%, rgba(0,0,0,.10) 100%)")
    inner = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
      width="{width}" height="{height}" style="position:absolute;inset:0">{leaves}</svg>
      <div style="position:absolute;inset:0;background:{shade}"></div>"""
    return page(f'<div class="stage" style="background:{t["bg"]}">{inner}</div>',
                CSS, width, height)


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
      <div class="ko" style="font-size:{h * 0.050:.0f}px;color:{t['fg']}">{CONCEPT}</div>
      <div style="margin-top:{h * 0.050:.0f}px">{chips}</div>
    </div>"""
    return page(stage(inner, dark=dark, w=width, h=height), CSS, width, height)


def build_logo_horizontal(width: int, height: int, dark: bool = False,
                          transparent: bool = True) -> str:
    """가로형 로고.

    transparent=True 는 배경이 없는 판이라 다른 이미지 위에 얹을 때 쓴다.
    투명 PNG 는 보는 쪽 배경색에 따라 글자가 안 보이기도 해서, 그냥 올릴
    자리에는 transparent=False 로 배경이 깔린 판을 쓴다.
    """
    h, t = height, theme(dark)
    bg = "transparent" if transparent else t["bg"]
    inner = f"""<div style="width:100%;height:100%;display:flex;align-items:center;
      justify-content:center;gap:{h * 0.16:.0f}px;background:{bg}">
      <div style="width:{h * 0.78:.0f}px;line-height:0">{mark(dark, int(h * 0.78))}</div>
      <div>
        <div class="wm" style="font-size:{h * 0.44:.0f}px;color:{t['fg']}">{BRAND_EN}</div>
        <div class="ko" style="margin-top:{h * 0.06:.0f}px;font-size:{h * 0.135:.0f}px;
             color:{t['accent']}">{BRAND_KO}</div>
      </div>
    </div>"""
    return page(f'<div class="stage" style="background:{bg}">{inner}</div>',
                CSS, width, height)


def build_favicon(size: int) -> str:
    return page(f'<div class="stage">{logomark_svg(size, "dark")}</div>', CSS, size, size)


# ── 라인업 (실제 자료 예시 포함) ──────────────────────────────────────────
def build_lineup(width: int, items, *, heading: str, caption: str,
                 dark: bool = True, thumb_w: int = 320,
                 kicker: str = "", edge: list[tuple[str, str]] | None = None
                 ) -> tuple[str, int]:
    """자료 목록. 각 줄에 실제 산출물 썸네일을 함께 보여 준다.

    kicker : 제목 위 한 줄 (예: '01 - 03  ·  읽고 · 분석하고 · 훈련한다')
    edge   : 맨 아래 차별화 포인트 (소제목, 설명) 목록
    """
    u = width / 100
    t = theme(dark)
    rows = []

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

    kicker_el = ""
    if kicker:
        kicker_el = (f'<div class="ko" style="font-size:{u * 2.0:.0f}px;'
                     f'color:{t["accent"]};letter-spacing:.10em;'
                     f'margin-bottom:{u * 1.4:.0f}px">{kicker}</div>')

    edge_el = ""
    if edge:
        # 카드 세 장이 나란히 서므로 가장 긴 것에 높이를 맞춘다. 흘러넘쳐 잘리지
        # 않도록 줄 수를 세어 카드 높이를 직접 박는다.
        card_w = (width - u * 13 - u * 3.6) / 3
        head_px, desc_px = u * 2.1, u * 1.75
        head_lines = max(-(-len(h) * head_px // (card_w - u * 4.4)) for h, _ in edge)
        desc_lines = max(-(-len(d) * desc_px // (card_w - u * 4.4)) for _, d in edge)
        card_h = (u * 4.8 + head_lines * head_px * 1.42
                  + u * 1.0 + desc_lines * desc_px * 1.68)
        cards = "".join(f"""<div style="flex:1 1 0;background:{t['chip_bg']};
          border-radius:10px;padding:{u * 2.4:.0f}px {u * 2.2:.0f}px;
          height:{card_h:.0f}px">
          <div class="ko" style="font-size:{head_px:.0f}px;color:{t['accent']};
               line-height:1.42;word-break:keep-all">{head}</div>
          <div class="sans" style="margin-top:{u * 1.0:.0f}px;font-size:{desc_px:.0f}px;
               color:{t['muted']};line-height:1.68;word-break:keep-all">{desc}</div>
        </div>""" for head, desc in edge)
        edge_el = f"""<div style="margin-top:{u * 4:.0f}px;padding-top:{u * 3.4:.0f}px;
          border-top:1px solid {t['line']}">
          <div class="ko" style="font-size:{u * 2.5:.0f}px;color:{t['fg']};
               margin-bottom:{u * 2.0:.0f}px">{"이 셋이" if len(edge) == 3 else "이 자료가"} 다른 점</div>
          <div style="display:flex;gap:{u * 1.8:.0f}px">{cards}</div>
        </div>"""

    def make(h: int, tail: str = "") -> str:
        inner = f"""<div style="display:flex;flex-direction:column;
          padding:{u * 6.5:.0f}px {u * 6.5:.0f}px {u * 4.5:.0f}px">
          <div>
            {kicker_el}
            <div class="ko" style="font-size:{u * 5.4:.0f}px;color:{t['fg']}">{heading}</div>
            <div class="sans" style="margin-top:{u * 1.6:.0f}px;font-size:{u * 2.05:.0f}px;
                 color:{t['muted']};line-height:1.7;word-break:keep-all">{caption}</div>
          </div>
          <div>{''.join(rows)}</div>
          {edge_el}
          <div style="display:flex;justify-content:center;padding-top:{u * 4:.0f}px">
            {signature(u * 3.2, dark)}</div>
          {tail}
        </div>"""
        return page(stage(inner, dark=dark, w=width, h=h), CSS, width, h)

    return autosize(make, width, int(u * 4.5))


# ── 자료별 단독 소개 카드 ─────────────────────────────────────────────────
def build_card(item, width: int = DOC_W) -> tuple[str, int]:
    """자료 한 종을 한 장으로 소개한다.

    라인업을 한 장에 다 넣으면 목록으로만 읽힌다. 자료마다 한 장씩 두면
    글마다 그 자료 카드만 붙일 수 있다. 간판 자료(signature)는 어두운 판에
    배지를 달아 눈에 먼저 들어오게 한다.
    """
    u = width / 100
    dark = item.signature
    t = theme(dark)

    badge = ""
    if item.signature:
        badge = (f'<span class="chip" style="background:{P["gold"]};color:{P["green_900"]};'
                 f'padding:{u * 1.0:.0f}px {u * 2.0:.0f}px;font-size:{u * 1.8:.0f}px;'
                 f'letter-spacing:.14em">SIGNATURE · 간판 자료</span>')

    pts = "".join(
        f'<div class="sans" style="font-size:{u * 1.95:.0f}px;color:{t["muted"]};'
        f'line-height:1.7;padding-left:{u * 1.8:.0f}px;position:relative;'
        f'word-break:keep-all;margin-top:{u * 1.2:.0f}px">'
        f'<span style="position:absolute;left:0;color:{t["accent"]}">·</span>'
        f'<b style="color:{t["fg"]};font-weight:700">{head}</b> — {desc}</div>'
        for head, desc in item.points[: (6 if item.signature else 4)])

    edge_el = ""
    if item.edge:
        edge_el = f"""<div style="margin-top:{u * 3:.0f}px;background:{t['chip_bg']};
          border-left:3px solid {t['accent']};border-radius:0 8px 8px 0;
          padding:{u * 2.2:.0f}px {u * 2.6:.0f}px">
          <div class="ko" style="font-size:{u * 2.3:.0f}px;color:{t['fg']};
               line-height:1.5;word-break:keep-all">{item.edge}</div>
        </div>"""

    img = shot(item.sample)
    sample_el = ""
    if img:
        sample_el = f"""<div style="margin-top:{u * 3.4:.0f}px">{img}
          <div class="sans" style="margin-top:{u * 1.2:.0f}px;font-size:{u * 1.7:.0f}px;
               color:{t['muted']};line-height:1.6;word-break:keep-all">
            {item.sample_note}</div>
        </div>"""

    name_px = u * (7.0 if item.signature else 5.4)

    def make(h: int, tail: str = "") -> str:
        inner = f"""<div style="display:flex;flex-direction:column;
          padding:{u * 6.5:.0f}px {u * 6.5:.0f}px {u * 5:.0f}px">
          <div>{badge}</div>
          <div style="display:flex;align-items:baseline;gap:{u * 1.6:.0f}px;
               margin-top:{u * (2.6 if item.signature else 0):.0f}px">
            <div class="wm" style="font-size:{u * 2.2:.0f}px;color:{t['accent']}">{item.no}</div>
            <div class="ko" style="font-size:{name_px:.0f}px;color:{t['fg']}">{item.name}</div>
            <div class="sans" style="font-size:{u * 1.8:.0f}px;color:{t['muted']};
                 letter-spacing:.10em">{item.en}</div>
          </div>
          <div class="sans" style="margin-top:{u * 1.4:.0f}px;font-size:{u * 2.3:.0f}px;
               color:{t['fg']};line-height:1.6;word-break:keep-all;opacity:.92">
            {item.one_line}</div>
          {edge_el}
          {sample_el}
          <div style="margin-top:{u * 3.2:.0f}px">{pts}</div>
          <div style="display:flex;justify-content:center;padding-top:{u * 4:.0f}px">
            {signature(u * 3.0, dark)}</div>
          {tail}
        </div>"""
        return page(stage(inner, dark=dark, w=width, h=h), CSS, width, h)

    return autosize(make, width, int(u * 5))


# ── 상세페이지 ────────────────────────────────────────────────────────────
def build_hero(item, width: int, height: int, dark: bool = True) -> str:
    u = width / 100
    t = theme(dark)
    inner = f"""<div style="height:100%;display:flex;flex-direction:column;
      justify-content:space-between;padding:{u * 8:.0f}px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>{chip(item.no, t, u * 1.9)}</div>
        <div class="sans" style="font-size:{u * 1.7:.0f}px;color:{t['muted']};
             letter-spacing:.08em">{CONCEPT}</div>
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

    def figure(name: str, note: str, first: bool = False) -> str:
        img_el = shot(name)
        if not img_el:
            return ""
        head = (f'<div class="ko" style="font-size:{u * 2.4:.0f}px;color:{t["fg"]};'
                f'margin-bottom:{u * 1.5:.0f}px">실제 자료 예시</div>') if first else ""
        return f"""<div style="margin-top:{u * 4:.0f}px">{head}{img_el}
          <div class="sans" style="margin-top:{u * 1.3:.0f}px;font-size:{u * 1.75:.0f}px;
               color:{t['muted']};line-height:1.6;word-break:keep-all">{note}</div>
        </div>"""

    sample_block = figure(item.sample, item.sample_note, first=True)
    sample_block += "".join(figure(n, note) for n, note in item.extra)

    def make(h: int, tail: str = "") -> str:
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
          {tail}
        </div>"""
        return page(stage(inner, dark=dark, w=width, h=h), CSS, width, h)

    return autosize(make, width, int(u * 7.5))


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
    def make(h: int, tail: str = "") -> str:
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
          {tail}
        </div>"""
        return page(stage(inner, dark=dark, w=width, h=h), CSS, width, h)

    return autosize(make, width, int(u * 7.5))


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

    def rows_of(items):
        return "\n".join(f"**{it.no}. {it.name}** — {it.one_line}\n" for it in items)

    def edge_of(edge):
        return "\n".join(f"**{h}**\n\n{d}\n" for h, d in edge)

    (POSTS / "00-lineup.md").write_text(f"""# 자료 라인업

## 읽는 자료 (01 — 03)

{img('lineup-1-read.png')}

{rows_of(MATERIALS[:3])}

### 이 셋이 다른 점

{edge_of(EDGE_READ)}

## 간판 자료 — 필생보 (04 — 05)

{img('lineup-2-pilsaengbo.png')}

{rows_of(MATERIALS[3:5])}

### 이 셋이 다른 점

{edge_of(EDGE_SIGN)}

## 쓰는 자료 (06 — 09)

{img('lineup-3-write.png')}

{rows_of(MATERIALS[5:])}

### 이 셋이 다른 점

{edge_of(EDGE_EXAM)}

<!-- 가격은 brand/catalog.py 의 price 에 넣으면 상세페이지에 함께 나옵니다. -->
""", encoding="utf-8")
    made.append(POSTS / "00-lineup.md")
    return made


# ── 전체 목록표 ───────────────────────────────────────────────────────────
def build_index_sheet(width: int = 1200, cols: int = 4,
                      tile_h: int = 185) -> tuple[str, int]:
    """assets 안의 결과물을 파일명과 함께 한 장에 늘어놓는다.

    투명 PNG 는 흰 바탕 위에 얹어 보여 준다. 어느 파일이 안 보이는지
    바로 짚을 수 있게 하려는 목적이다.
    """
    from PIL import Image

    files = sorted(f for f in OUT.glob("*.png") if not f.name.startswith("_"))
    pad, gap = 24, 16
    cell = (width - pad * 2 - gap * (cols - 1)) // cols
    cards = []
    for f in files:
        with Image.open(f) as im:
            size = f"{im.width}×{im.height}"
        # 세로로 긴 장은 윗부분만 보여 준다. 목록에서는 어느 파일인지만 알면 된다.
        cards.append(f"""<div style="width:{cell}px">
          <div style="background:#fff;border:1px solid #DED9CC;border-radius:6px;
               overflow:hidden;height:{tile_h}px">
            <img src="{f.as_uri()}" style="display:block;width:100%;height:100%;
                 object-fit:cover;object-position:top">
          </div>
          <div style="margin-top:6px;font-size:12px;color:#5B6560;
               word-break:break-all;line-height:1.4">{f.name}<br>
            <span style="color:#8E958F">{size}</span></div>
        </div>""")
    rows = -(-len(files) // cols)
    height = pad * 2 + 44 + rows * (tile_h + 48 + gap)

    body = f"""<div style="background:#F2F0E9;padding:{pad}px;min-height:100%">
      <div style="font-weight:700;font-size:20px;color:{P['green_900']};
           margin-bottom:16px">Ortica 에셋 목록 — {len(files)}개</div>
      <div style="display:flex;flex-wrap:wrap;gap:{gap}px;align-items:flex-start">
        {''.join(cards)}</div>
    </div>"""
    return page(body, CSS, width, height), height


# ── 실행 ──────────────────────────────────────────────────────────────────
def emit(made: list[Path], name: str, html: str, w: int, h: int) -> None:
    made.append(html_to_png(html, OUT / name, w, h))
    print(f"  ✔ {name}  ({w}×{h})")


def build_all() -> list[Path]:
    made: list[Path] = []

    print("브랜드 기본")
    # 네이버 앱은 프로필을 작은 원으로 줄인다. 글자 없는 판을 기본으로 쓴다.
    emit(made, "profile-mark-800.png", build_profile(800, with_name=False), 800, 800)
    emit(made, "profile-mark-400.png", build_profile(400, with_name=False), 400, 400)
    emit(made, "profile-mark-light-800.png",
         build_profile(800, dark=False, with_name=False), 800, 800)
    # 크게 보이는 자리용 (이름이 함께 들어간 판)
    emit(made, "profile-name-800.png", build_profile(800), 800, 800)
    emit(made, "profile-name-400.png", build_profile(400), 400, 400)
    # 크림 바탕 판 — 가로형 로고와 같은 색·글자 구성
    emit(made, "profile-light-1200.png",
         build_profile(1200, dark=False, name_text=BRAND_EN), 1200, 1200)
    emit(made, "profile-light-800.png",
         build_profile(800, dark=False, name_text=BRAND_EN), 800, 800)
    emit(made, "profile-light-400.png",
         build_profile(400, dark=False, name_text=BRAND_EN), 400, 400)
    emit(made, "profile-portrait-400x480.png", build_profile(400, box_h=480), 400, 480)
    emit(made, "title-966x300-dark.png", build_title(966, 300), 966, 300)
    emit(made, "title-966x300-light.png", build_title(966, 300, dark=False), 966, 300)
    emit(made, "title-966x200-dark.png", build_title(966, 200), 966, 200)
    emit(made, "title-966x550-dark.png", build_title_tall(966, 550), 966, 550)
    emit(made, "title-966x550-light.png",
         build_title_tall(966, 550, dark=False), 966, 550)
    emit(made, "title-966x420-dark.png", build_title_tall(966, 420), 966, 420)
    # 네이버 모바일 커버 — 글자 없는 배경 (네이버가 제목·프로필을 위에 그린다)
    emit(made, "cover-backdrop-1600x1200.png",
         build_cover_backdrop(1600, 1200), 1600, 1200)
    emit(made, "cover-backdrop-1080x1080.png",
         build_cover_backdrop(1080, 1080), 1080, 1080)
    emit(made, "cover-backdrop-2400x1350.png",
         build_cover_backdrop(2400, 1350), 2400, 1350)
    # 글자가 들어간 판 — 배너·썸네일처럼 위에 아무것도 안 얹히는 자리용
    emit(made, "cover-branded-1200x900.png", build_cover(1200, 900), 1200, 900)
    # 배경이 깔린 판 — 그냥 올려도 어디서나 보인다
    emit(made, "logo-horizontal-solid-light.png",
         build_logo_horizontal(1200, 300, transparent=False), 1200, 300)
    emit(made, "logo-horizontal-solid-dark.png",
         build_logo_horizontal(1200, 300, dark=True, transparent=False), 1200, 300)
    # 투명 판 — 다른 이미지 위에 얹을 때만
    emit(made, "logo-horizontal-on-light.png", build_logo_horizontal(1200, 300), 1200, 300)
    emit(made, "logo-horizontal-on-dark.png",
         build_logo_horizontal(1200, 300, dark=True), 1200, 300)
    for n in (32, 180, 512):
        emit(made, f"favicon-{n}.png", build_favicon(n), n, n)

    print("자료별 소개 카드")
    for it in MATERIALS + BOOKS:
        html, h = build_card(it)
        emit(made, f"card-{it.no.lower()}-{it.key}.png", html, DOC_W, h)

    print("라인업")
    html, h = build_lineup(
        DOC_W, MATERIALS[:3],
        kicker="01 — 03  ·  읽는 자료",
        heading="같은 지문을 세 번 읽힙니다",
        caption="원문으로 한 번, 해석으로 한 번, 끊어읽기와 함축까지 뜯어서 또 한 번. "
                "세 자료가 같은 문장 번호를 씁니다.",
        edge=EDGE_READ, dark=False)
    emit(made, "lineup-1-read.png", html, DOC_W, h)

    html, h = build_lineup(
        DOC_W, MATERIALS[3:5],
        kicker="04 — 05  ·  간판 자료",
        heading="필생보 — 필자의 생각이 보이는 영어독해",
        caption="해석은 되는데 왜 틀릴까. 수능 독해는 문장 번역 시험이 아니라 "
                "필자의 생각을 읽는 시험입니다. 그 눈을 훈련하는 자료입니다.",
        edge=EDGE_SIGN)
    emit(made, "lineup-2-pilsaengbo.png", html, DOC_W, h)

    html, h = build_lineup(
        DOC_W, MATERIALS[5:],
        kicker="06 — 09  ·  쓰는 자료",
        heading="그 다음은 손으로 씁니다",
        caption="읽어서 안 것과 시험장에서 쓰는 것은 다릅니다. "
                "겹쳐서 묻고, 서술형으로 쓰게 하고, 변형해서 확인하고, "
                "우리 학교 시험지로 한 회차를 돌립니다.",
        edge=EDGE_EXAM, dark=False)
    emit(made, "lineup-3-write.png", html, DOC_W, h)

    html, h = build_lineup(
        DOC_W, BOOKS,
        kicker="교재",
        heading="제작 교재 · 고3",
        caption="아직 실물을 못 본 자료입니다. PDF 를 받으면 위 목록으로 옮깁니다.")
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
    sub.add_parser("index", help="전체 결과물 목록표 한 장 생성")

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

    if args.cmd == "index":
        html, h = build_index_sheet()
        html_to_png(html, OUT / "_index.png", 1200, h)
        print(f"✔ _index.png  (1200×{h})")
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
