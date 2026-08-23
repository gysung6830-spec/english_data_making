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

# 한 장에 넣을 실물 사진 수. 더 넣으면 스크롤만 길어지고 끝까지 안 읽힌다.
# 나머지 지면은 catalog 의 extra 에 남아 있으니 필요할 때 순서만 바꿔 쓰면 된다.
MAX_FIGURES = 2

# 특징 줄 수. 카드마다 분량이 들쭉날쭉하면 목록으로 늘어놨을 때 눈에 걸린다.
MAX_POINTS = 4

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


# 예시 지면을 뽑아낸 해상도(pdf_samples 의 기본 130dpi 에서 A4 가로).
# 잘라 낸 조각을 원래 지면에서 차지하던 비율대로 보여 주려고 기준으로 쓴다.
SAMPLE_PAGE_W = 1075

# 조각은 작아서 그대로 놓으면 안 읽힌다. 이만큼만 키운다. 더 키우면 흐려진다.
CROP_ZOOM = 1.5


def crop_img(name: str, doc_w: int, fill: bool = False) -> str:
    """부분 확대 조각. 원래 지면에서 차지하던 만큼만 키워서 보여 준다.

    좁은 조각을 본문 폭에 맞춰 늘리면 세 배로 확대되어 흐려지고, 지면에서
    작은 상자였다는 사실도 사라진다.
    """
    path = SAMPLES / name
    if not name or not path.exists():
        return ""
    from PIL import Image

    with Image.open(path) as im:
        w = im.width
    px = doc_w if fill else min(doc_w, round(w / SAMPLE_PAGE_W * doc_w * CROP_ZOOM))
    return (f'<img src="{path.as_uri()}" style="display:block;width:{px}px;'
            f'max-width:100%;border-radius:8px;'
            f'box-shadow:0 5px 18px rgba(14,31,26,.16)">')


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


def autosize(make, width: int, pad: int, max_height: int = 20000) -> tuple[str, int]:
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


# ── 라인업 (한 장) ────────────────────────────────────────────────────────
def first_sentence(text: str) -> str:
    """설명의 첫 문장만. 마침표 뒤에서만 자른다.

    '~합니다 그리고' 처럼 종결어미 뒤 공백에서 자르면 문장 가운데가 잘린다.
    """
    parts = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
    return parts[0]


def lineup_rows(items, t: dict[str, str], u: float, thumb_w: int = 320,
                points_n: int = 2) -> str:
    """자료 목록 줄. 왼쪽에 실물 썸네일, 오른쪽에 이름과 한 줄."""
    rows = []
    for it in items:
        thumb, caption = "", "예시 준비 중"
        src = it.thumb or it.sample
        if src:
            name = shot_crop(src, OUT / "thumbs" / f"t-{it.key}.png", thumb_w)
            if name:
                thumb = (f'<img src="{(OUT / "thumbs" / name).as_uri()}" '
                         f'style="width:100%;display:block;border-radius:8px;'
                         f'box-shadow:0 4px 16px rgba(14,31,26,.22)">')
                caption = "실제 자료 지면"
        if not thumb:
            thumb = (f'<div style="width:100%;aspect-ratio:4/3;border-radius:8px;'
                     f'border:1px dashed {t["line"]}"></div>')
        # 작은 사진은 글자가 안 읽히니 무슨 그림인지 한 줄로 알려 준다.
        thumb += (f'<div class="sans" style="margin-top:{u * .9:.0f}px;'
                  f'font-size:{u * 1.5:.0f}px;color:{t["muted"]};'
                  f'letter-spacing:.04em">{caption}</div>')

        badge = ""
        if it.signature:
            badge = (f'<span class="chip" style="background:{P["gold"]};'
                     f'color:{P["green_900"]};padding:{u * .40:.0f}px {u * .95:.0f}px;'
                     f'font-size:{u * 1.22:.0f}px;letter-spacing:.08em">SIGNATURE</span>')
        # 주문 제작은 배포 방식이 다르다. 눌러서 받는 자료와 섞이면 안 된다.
        if it.made_to_order:
            badge += (f'<span class="chip" style="border:1px solid {t["accent"]};'
                      f'color:{t["accent"]};padding:{u * .34:.0f}px {u * .9:.0f}px;'
                      f'font-size:{u * 1.22:.0f}px;margin-left:{u * .5:.0f}px">'
                      f'주문제작자료</span>')

        # 판형을 사진 라벨로 이미 보여 주는 자료는 그 판형 설명을 건너뛴다.
        # 사진 밑에 '원문만'이라 써 놓고 아래에 또 '원문만 —' 을 쓰면 같은 말이 두 번이다.
        src_pts = it.points[len(it.thumbs):] if it.thumbs else it.points
        n = it.lineup_points or points_n
        # 줄이 셋을 넘으면 설명을 첫 문장까지만 자른다. 생김새는 그대로 두어야
        # 목록에서 그 자료만 다른 모양으로 튀지 않는다.
        pts = "".join(
            f'<div class="sans" style="font-size:{u * 1.8:.0f}px;color:{t["muted"]};'
            f'line-height:1.68;padding-left:{u * 1.6:.0f}px;position:relative;'
            f'word-break:keep-all;margin-top:{u * .6:.0f}px">'
            f'<span style="position:absolute;left:0;color:{t["accent"]}">·</span>'
            f'<b style="color:{t["fg"]};font-weight:700">{head}</b> — '
            f'{first_sentence(desc) if n > 2 else desc}</div>'
            for head, desc, *_ in src_pts[:n])

        head_el = f"""<div style="display:flex;align-items:baseline;flex-wrap:wrap;
                 gap:{u * .8:.0f}px {u * 1.1:.0f}px">
              <div class="wm" style="font-size:{u * 2.0:.0f}px;color:{t['accent']}">{it.no}</div>
              <div class="ko" style="font-size:{u * 3.5:.0f}px;color:{t['fg']};
                   white-space:nowrap">{it.name}</div>
              {badge}
            </div>
            <div class="sans" style="margin-top:{u * 1.0:.0f}px;font-size:{u * 2.0:.0f}px;
                 color:{t['fg']};line-height:1.65;word-break:keep-all;opacity:.9">
              {it.one_line or it.edge}</div>
            <div style="margin-top:{u * 1.2:.0f}px">{pts}</div>"""

        if it.thumbs:
            # 판형이 여럿인 자료. 왼쪽에 한 장만 놓으면 '골라 쓰세요'라고 써 놓고
            # 한 가지만 보여 주는 꼴이라, 글 아래에 판형을 나란히 늘어놓는다.
            cells = []
            for name, label in it.thumbs:
                f = shot_crop(name, OUT / "thumbs" / f"t-{it.key}-{Path(name).stem}.png",
                              thumb_w, ratio=0.92)
                img = (f'<img src="{(OUT / "thumbs" / f).as_uri()}" '
                       f'style="width:100%;display:block;border-radius:6px;'
                       f'box-shadow:0 3px 12px rgba(14,31,26,.20)">') if f else ""
                cells.append(f"""<div style="flex:1 1 0">{img}
                  <div class="sans" style="margin-top:{u * .8:.0f}px;
                       font-size:{u * 1.6:.0f}px;color:{t['accent']};
                       font-weight:700">{label}</div></div>""")
            rows.append(f"""<div style="padding:{u * 3.4:.0f}px 0;
              border-top:1px solid {t['line']}">
              {head_el}
              <div style="display:flex;gap:{u * 1.8:.0f}px;margin-top:{u * 2.4:.0f}px">
                {''.join(cells)}</div>
            </div>""")
            continue

        rows.append(f"""<div style="display:flex;gap:{u * 3.2:.0f}px;
          padding:{u * 3.4:.0f}px 0;border-top:1px solid {t['line']}">
          <div style="flex:0 0 {u * 31:.0f}px">{thumb}</div>
          <div style="flex:1 1 auto">{head_el}</div>
        </div>""")
    return "".join(rows)


# 라인업 한 장을 이루는 묶음들. (머리말, 제목, 설명, 자료들, 어두운 판)
# 제작 교재는 아직 실물이 없어 목록에서 뺐다. catalog.BOOKS 는 그대로 두었으니
# PDF 를 받으면 여기 한 줄만 다시 넣으면 된다.
def lineup_sections():
    return [
        ("01 — 02  ·  지문 이해", "무슨 글인지부터 알게 합니다",
         "지문자료는 판형만 고르시면 되는 기본 자료입니다. 해석까지 붙여도 "
         "무슨 말인지 모르겠다는 학생에게는 지문분석지를 쓰시면 됩니다.",
         MATERIALS[:2], False),
        ("03 — 04  ·  시그니처 자료", "필생보 — 필자의 생각이 보이는 영어독해",
         "분석지는 아무리 잘 만들어도 학생이 눈으로 읽고 넘깁니다. 같은 내용을 "
         "손으로 채우면서 보게 만든 자료입니다. 수업에서 쓰실 강의용은 강사용과 "
         "학생용 두 판본으로 나오고, 학생이 혼자 볼 것은 독학용입니다.",
         MATERIALS[2:4], True),
        ("05 — 08  ·  시험 대비", "시험에 나오는 형태로 풀립니다",
         "아는 것과 시험장에서 맞히는 것은 다릅니다. 한 지문을 여러 각도로 묻고, "
         "서술형으로 대비하고, 변형문제로 확인한 뒤, 시험지 한 회차를 돌립니다.",
         MATERIALS[4:], False),
    ]


def build_lineup(width: int = DOC_W, part: int | None = None) -> tuple[str, int]:
    """자료 라인업.

    묶음마다 디자인을 새로 시작하면 어디까지가 한 목록인지 안 보인다. 그래서
    한 흐름으로 짜 놓고 **묶음 경계에서만** 자른다. 바탕색이 밝은 판과 어두운
    판으로 번갈아 가므로, 순서대로 올리면 이어진 한 장처럼 읽힌다.

    part=None : 전부 이어 붙인 한 장
    part=0..3 : 그 묶음만. 0 에는 머리말이, 마지막에는 꼬리말이 함께 붙는다.
    """
    u = width / 100
    secs = lineup_sections()
    chosen = list(enumerate(secs)) if part is None else [(part, secs[part])]
    with_head = part is None or part == 0
    with_foot = part is None or part == len(secs) - 1

    head_t = theme(True)
    bands = []
    if with_head:
        bands.append(f"""<div style="position:relative;background:{head_t['bg']};
          padding:{u * 7:.0f}px {u * 6.5:.0f}px {u * 6:.0f}px;overflow:hidden">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {u * 46:.0f}"
               width="{width}" height="{u * 46:.0f}"
               style="position:absolute;inset:0;pointer-events:none">
            <path d="{leaf_path(width * 0.86, u * 40, u * 62, u * 38, teeth=13, depth=0.055, tilt=18)}"
                  fill="{head_t['wm']}" fill-opacity="{head_t['wm_op']}"/></svg>
          <div style="position:relative">
            <div class="ko" style="font-size:{u * 2.0:.0f}px;color:{head_t['accent']};
                 letter-spacing:.12em">자료 라인업</div>
            <div class="ko" style="margin-top:{u * 1.4:.0f}px;font-size:{u * 5.6:.0f}px;
                 color:{head_t['fg']};line-height:1.32;word-break:keep-all">
              읽고 · 뜯어보고<br>시험에 나올 문제만 풉니다</div>
            <div class="sans" style="margin-top:{u * 2.0:.0f}px;font-size:{u * 2.05:.0f}px;
                 color:{head_t['muted']};line-height:1.75;word-break:keep-all">
              양질의 자료를 찾아 헤매던 시간, 이제는 수업에만 집중할 수 있습니다.
              압축 정리된 정리본부터 9개년 평가원분석을 통한 정교한 오답설계까지.
              <span style="color:{P['gold']}">SIGNATURE</span> 표시는 시그니처 자료입니다.</div>
          </div>
        </div>""")

    for i, (kicker, heading, caption, items, dark) in chosen:
        t = theme(dark)
        # 나눠 올린 조각도 몇 번째인지 보여야 순서가 안 흐트러진다.
        step = ("" if part is None else
                f'<span class="sans" style="float:right;font-size:{u * 1.7:.0f}px;'
                f'color:{t["muted"]};letter-spacing:.10em">'
                f'{i + 1} / {len(secs)}</span>')
        bands.append(f"""<div style="background:{t['bg']};
          padding:{u * 6:.0f}px {u * 6.5:.0f}px {u * 6:.0f}px">
          <div class="ko" style="font-size:{u * 2.0:.0f}px;color:{t['accent']};
               letter-spacing:.10em">{kicker}{step}</div>
          <div class="ko" style="margin-top:{u * 1.2:.0f}px;font-size:{u * 4.2:.0f}px;
               color:{t['fg']};line-height:1.36;word-break:keep-all">{heading}</div>
          <div class="sans" style="margin-top:{u * 1.4:.0f}px;font-size:{u * 2.0:.0f}px;
               color:{t['muted']};line-height:1.7;word-break:keep-all">{caption}</div>
          <div style="margin-top:{u * 1.6:.0f}px">{lineup_rows(items, t, u)}</div>
        </div>""")

    foot_t = theme(True)
    if with_foot:
        bands.append(f"""<div style="background:{foot_t['bg']};
          padding:{u * 4.5:.0f}px 0;display:flex;justify-content:center">
          {signature(u * 3.2, True)}</div>""")

    def make(h: int, tail: str = "") -> str:
        body = (f'<div style="display:flex;flex-direction:column;'
                f'background:{foot_t["bg"]}">{"".join(bands)}{tail}</div>')
        return page(body, CSS, width, h)

    return autosize(make, width, 0)


# 나눠 올릴 때 쓰는 파일 이름
LINEUP_PARTS = ["lineup-1-read.png", "lineup-2-pilsaengbo.png",
                "lineup-3-write.png"]


def grid_table(title: str, rows, t: dict[str, str], u: float, width: float) -> str:
    """항목이 많은 표를 두 칸으로 접는다.

    열여섯 줄을 세로로 세우면 그 표만 한 화면을 먹는다. 왼쪽에 유형, 오른쪽에
    대응 번호를 붙여 짧은 줄 열여섯 개로 만들면 훑어보기가 된다.
    """
    cells = "".join(f"""<div style="display:flex;justify-content:space-between;
      align-items:baseline;gap:{u * 1.2:.0f}px;padding:{u * 1.15:.0f}px 0;
      border-top:1px solid {t['line']};break-inside:avoid">
      <div class="sans" style="font-size:{u * 1.75:.0f}px;color:{t['fg']};
           line-height:1.4;word-break:keep-all">{k}</div>
      <div class="sans" style="flex:0 0 auto;font-size:{u * 1.5:.0f}px;
           color:{t['accent']};white-space:nowrap">{v}</div>
    </div>""" for k, v in rows)
    return f"""<div style="margin-top:{u * 3.4:.0f}px">
      <div class="ko" style="font-size:{u * 2.2:.0f}px;color:{t['fg']};
           margin-bottom:{u * .6:.0f}px;word-break:keep-all">{title}</div>
      <div style="column-count:2;column-gap:{u * 3.4:.0f}px">{cells}</div>
    </div>"""


def spec_table(title: str, rows, t: dict[str, str], u: float,
               label_w: float = 13) -> str:
    """제목 + (왼쪽 칸 / 오른쪽 설명) 표. 회차 구성·난이도 기준처럼
    줄글로 풀면 안 읽히는 것을 표로 보여 준다."""
    body = "".join(f"""<div style="display:flex;gap:{u * 2:.0f}px;
      padding:{u * 1.5:.0f}px 0;border-top:1px solid {t['line']}">
      <div class="ko" style="flex:0 0 {u * label_w:.0f}px;font-size:{u * 2.0:.0f}px;
           color:{t['accent']}">{k}</div>
      <div class="sans" style="flex:1 1 auto;font-size:{u * 1.9:.0f}px;color:{t['muted']};
           line-height:1.65;word-break:keep-all">{v}</div>
    </div>""" for k, v in rows)
    return f"""<div style="margin-top:{u * 3.4:.0f}px">
      <div class="ko" style="font-size:{u * 2.3:.0f}px;color:{t['fg']};
           margin-bottom:{u * 1.0:.0f}px">{title}</div>{body}
    </div>"""


# ── 자료별 상세페이지 ─────────────────────────────────────────────────────
def build_detail(item, width: int = DOC_W) -> tuple[str, int]:
    """자료 한 종의 상세페이지 한 장.

    한 자료를 표지·구성·안내 세 장으로 쪼개면 올릴 때마다 순서를 맞춰야 하고
    독자는 같은 이야기를 세 번 스크롤한다. 한 장에 이름 → 한 줄 → 차별점 →
    실물 → 구성 → 안내까지 세로로 세운다. 시그니처 자료(signature)는 어두운
    판에 배지를 달아 눈에 먼저 들어오게 한다.
    """
    u = width / 100
    dark = item.signature
    t = theme(dark)

    badge = ""
    if item.signature:
        badge = (f'<span class="chip" style="background:{P["gold"]};color:{P["green_900"]};'
                 f'padding:{u * 1.0:.0f}px {u * 2.0:.0f}px;font-size:{u * 1.8:.0f}px;'
                 f'letter-spacing:.14em">SIGNATURE · 시그니처 자료</span>')
    if item.made_to_order:
        badge += (f'<span class="chip" style="border:1px solid {t["accent"]};'
                  f'color:{t["accent"]};padding:{u * .9:.0f}px {u * 1.8:.0f}px;'
                  f'font-size:{u * 1.7:.0f}px;margin-left:{u * 1.0:.0f}px">'
                  f'주문제작자료</span>')

    def point_block(pt) -> str:
        """특징 한 줄 + 그 특징이 보이는 지면 조각.

        지면 전체를 넣으면 글자가 작아 아무것도 안 읽힌다. 말로 설명한 그 자리만
        잘라 바로 아래에 붙이면, 읽는 사람이 문장과 실물을 짝지어 본다.
        """
        head, desc, *rest = pt
        # 왼쪽에 지면, 오른쪽에 말. 눈이 사진에서 설명으로 바로 건너간다.
        col_w = int((width - u * 13 - u * 3) * 0.62)
        names = [c for c in (rest[0].split("|") if rest and rest[0] else [])]
        crops = "".join(
            f'<div style="margin-top:{u * 1.2 if i else 0:.0f}px">'
            f'{crop_img(c, col_w, fill=True)}</div>'
            for i, c in enumerate(names) if crop_img(c, col_w))
        # 사진을 키우려고 글자를 줄였다. 포인트는 짚어 주는 말이라 작아도 읽힌다.
        text = f"""<div class="ko" style="font-size:{u * 2.05:.0f}px;color:{t['fg']};
               line-height:1.42;word-break:keep-all">{head}</div>
          <div class="sans" style="margin-top:{u * .8:.0f}px;font-size:{u * 1.6:.0f}px;
               color:{t['muted']};line-height:1.68;word-break:keep-all">{desc}</div>"""
        if not crops:
            return f'<div style="margin-top:{u * 3.4:.0f}px">{text}</div>'
        return f"""<div style="margin-top:{u * 3.4:.0f}px;display:flex;
          gap:{u * 3:.0f}px;align-items:flex-start">
          <div style="flex:0 0 {col_w}px">{crops}</div>
          <div style="flex:1 1 auto">{text}</div>
        </div>"""

    # 특징 묶음 제목. '이게 다른 자료와 뭐가 다른데'를 묻고 있는 사람에게
    # 아래 줄들이 그 답이라고 먼저 알려 준다.
    pts_title = ""
    if item.points_title:
        pts_title = f"""<div style="margin-top:{u * 4.2:.0f}px;
          padding-bottom:{u * 1.0:.0f}px;border-bottom:2px solid {t['accent']}">
          <div class="ko" style="font-size:{u * 2.6:.0f}px;color:{t['fg']};
               word-break:keep-all">{item.points_title}</div>
        </div>"""

    n_pts = item.max_points or MAX_POINTS
    has_crops = any(len(pt) > 2 and pt[2] for pt in item.points)
    if has_crops:
        pts = "".join(point_block(pt) for pt in item.points[:n_pts])
    else:
        pts = "".join(
            f'<div class="sans" style="font-size:{u * 1.95:.0f}px;color:{t["muted"]};'
            f'line-height:1.7;padding-left:{u * 1.8:.0f}px;position:relative;'
            f'word-break:keep-all;margin-top:{u * 1.4:.0f}px">'
            f'<span style="position:absolute;left:0;color:{t["accent"]}">·</span>'
            f'<b style="color:{t["fg"]};font-weight:700">{head}</b> — {desc}</div>'
            for head, desc, *_ in item.points[:n_pts])

    edge_el = ""
    if item.edge:
        edge_el = f"""<div style="margin-top:{u * 3:.0f}px;background:{t['chip_bg']};
          border-left:3px solid {t['accent']};border-radius:0 8px 8px 0;
          padding:{u * 2.2:.0f}px {u * 2.6:.0f}px">
          <div class="ko" style="font-size:{u * 2.3:.0f}px;color:{t['fg']};
               line-height:1.5;word-break:keep-all">{item.edge}</div>
        </div>"""

    def figure(name: str, note: str) -> str:
        img_el = shot(name)
        if not img_el:
            return ""
        return f"""<div style="margin-top:{u * 3.4:.0f}px">{img_el}
          <div class="sans" style="margin-top:{u * 1.2:.0f}px;font-size:{u * 1.7:.0f}px;
               color:{t['muted']};line-height:1.6;word-break:keep-all">{note}</div>
        </div>"""

    n_fig = item.figures or (0 if has_crops else MAX_FIGURES)
    sample_el = ""
    if n_fig:
        sample_el = figure(item.sample, item.sample_note)
        sample_el += "".join(figure(n, note) for n, note in item.extra[:n_fig - 1])

    # 짧고 센 한 줄은 크게, 설명형 긴 한 줄은 작게. 같은 크기로 두면 센 문장이 죽는다.
    one_el = ""
    punchy = len(item.one_line) <= 30
    one_px = u * (3.4 if punchy else 2.3)
    one_cls = "ko" if punchy else "sans"
    one_op = ".95" if punchy else ".92"

    # 반 페이지 — 차별점 바로 아래. 무엇을 파는지 지면으로 한 번 보여 주고
    # 특징을 하나씩 뜯는 순서가 읽힌다.
    if item.one_line:
        one_el = (f'<div class="{one_cls}" style="margin-top:{u * 1.6:.0f}px;'
                  f'font-size:{one_px:.0f}px;color:{t["fg"]};line-height:1.5;'
                  f'word-break:keep-all;opacity:{one_op}">{item.one_line}</div>')

    tables_el = "".join(spec_table(title, rows, t, u) for title, rows in item.tables)
    tables_el += "".join(grid_table(title, rows, t, u, width - u * 13)
                         for title, rows in item.grids)
    name_px = u * (7.0 if item.signature else 5.4)

    # 형태·구성·배포는 이미지에 넣지 않는다. PDF·즉시 다운로드처럼 자료마다
    # 똑같은 줄이 장마다 반복되면 아래쪽이 안 읽힌다. catalog 의 spec 은 그대로
    # 두어 원고 초안(posts/*.md)에는 계속 들어간다.
    spec_el = ""

    who_el = ""
    if item.who:
        who_el = "".join(f"""<div class="sans" style="font-size:{u * 1.95:.0f}px;
          color:{t['muted']};line-height:1.8;padding-left:{u * 2.2:.0f}px;
          position:relative;word-break:keep-all">
          <span style="position:absolute;left:0;color:{t['accent']}">·</span>{w}</div>"""
          for w in item.who)
        who_el = f"""<div style="margin-top:{u * 3.4:.0f}px">
          <div class="ko" style="font-size:{u * 2.3:.0f}px;color:{t['accent']};
               margin-bottom:{u * 1.0:.0f}px">이런 분께</div>{who_el}
        </div>"""

    price_el = ""
    if item.price:
        price_el = f"""<div style="margin-top:{u * 3.4:.0f}px;padding-top:{u * 2.6:.0f}px;
          border-top:1px solid {t['line']}">
          <div class="ko" style="font-size:{u * 1.9:.0f}px;color:{t['accent']}">가격</div>
          <div class="wm" style="margin-top:{u * 1.0:.0f}px;font-size:{u * 4.2:.0f}px;
               color:{t['fg']}">{item.price}</div>
          <div class="sans" style="margin-top:{u * .8:.0f}px;font-size:{u * 1.75:.0f}px;
               color:{t['muted']}">{item.price_note}</div>
        </div>"""

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
          {one_el}
          {edge_el}
          {sample_el}
          {tables_el}
          {pts_title}
          <div style="margin-top:{u * 3.2:.0f}px">{pts}</div>
          {spec_el}
          {who_el}
          {price_el}
          <div style="display:flex;justify-content:center;padding-top:{u * 4:.0f}px">
            {signature(u * 3.0, dark)}</div>
          {tail}
        </div>"""
        return page(stage(inner, dark=dark, w=width, h=h), CSS, width, h)

    return autosize(make, width, int(u * 5))


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
        pts = "\n\n".join(f"**{h}**\n\n{d}" for h, d, *_ in it.points)
        who = "\n".join(f"- {w}" for w in it.who)
        spec = "\n".join(f"- {k} — {v}" for k, v in it.spec)
        tables = "".join(
            f"\n### {title}\n\n" + "\n".join(f"- **{k}** — {v}" for k, v in rows) + "\n"
            for title, rows in it.tables)
        sample = (f"\n{img('samples/' + it.sample)}\n\n{it.sample_note}\n" if it.sample
                  else "\n<!-- 실제 자료 화면 캡처를 여기에 넣으세요 -->\n")
        md = f"""# {it.name}

{img(f'detail-{it.no.lower()}-{it.key}.png')}

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
{tables}
## 이런 분께

{who}

<!-- 가격과 구매 방법(링크·계좌·폼)을 여기에 넣으세요 -->
"""
        (POSTS / f"{it.no.lower()}-{it.key}.md").write_text(md, encoding="utf-8")
        made.append(POSTS / f"{it.no.lower()}-{it.key}.md")

    def rows_of(items):
        return "\n".join(f"**{it.no}. {it.name}** — {it.one_line}\n" for it in items)

    (POSTS / "00-lineup.md").write_text(f"""# 자료 라인업

<!-- 이미지는 아래 순서대로 넣으면 이어진 한 장처럼 보입니다.
     한 장으로 올리려면 lineup.png 하나만 쓰세요. -->

{img('lineup-1-read.png')}

양질의 자료를 찾아 헤매던 시간, 이제는 수업에만 집중할 수 있습니다.
압축 정리된 정리본부터 9개년 평가원분석을 통한 정교한 오답설계까지.

자료 한 종씩 자세히 보시려면 각 상세페이지 글로 가시면 됩니다.

## 지문 이해 (01 — 02)

{rows_of(MATERIALS[:2])}

## 시그니처 자료 — 필생보 (03 — 04)

{img('lineup-2-pilsaengbo.png')}

{rows_of(MATERIALS[2:4])}

## 시험 대비 (05 — 08)

{img('lineup-3-write.png')}

{rows_of(MATERIALS[4:])}

<!-- 가격은 brand/catalog.py 의 price 에 넣으면 상세페이지에 함께 나옵니다. -->
""", encoding="utf-8")
    made.append(POSTS / "00-lineup.md")

    # 자료 번호나 키가 바뀌면 예전 이름의 초안이 남는다. 목록에 없는 것은 지운다.
    keep = {p.name for p in made}
    for old in POSTS.glob("*.md"):
        if old.name not in keep:
            old.unlink()
            print(f"  − {old.name} (지금 목록에 없는 초안)")
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

    print("자료별 상세페이지")
    for it in MATERIALS + BOOKS:
        html, h = build_detail(it)
        emit(made, f"detail-{it.no.lower()}-{it.key}.png", html, DOC_W, h)

    print("라인업")
    html, h = build_lineup()
    emit(made, "lineup.png", html, DOC_W, h)
    for i, name in enumerate(LINEUP_PARTS):
        html, h = build_lineup(part=i)
        emit(made, name, html, DOC_W, h)

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
    sub.add_parser("lineup", help="라인업(한 장 + 나눈 조각)만 다시 생성")

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

    if args.cmd == "lineup":
        made: list[Path] = []
        html, h = build_lineup()
        emit(made, "lineup.png", html, DOC_W, h)
        for i, name in enumerate(LINEUP_PARTS):
            html, h = build_lineup(part=i)
            emit(made, name, html, DOC_W, h)
        return

    if args.cmd == "item":
        it = BY_KEY[args.key]
        made: list[Path] = []
        html, h = build_detail(it)
        emit(made, f"detail-{it.no.lower()}-{it.key}.png", html, DOC_W, h)
        return

    made = build_all()
    posts = write_posts()
    print(f"\n이미지 {len(made)}개 → {OUT}")
    print(f"원고 초안 {len(posts)}개 → {POSTS}")


if __name__ == "__main__":
    main()
