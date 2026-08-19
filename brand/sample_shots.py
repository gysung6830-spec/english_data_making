"""저장소의 자료 생성기로 **실제 산출물** 미리보기 이미지를 만든다.

블로그 라인업에 그림 대신 진짜 자료를 보여 주려면 실물이 필요하다. 여기서는
`src/render.py` 의 렌더 함수를 그대로 부르되, WeasyPrint 대신 HTML 을 가로채
헤드리스 크로미움으로 찍는다. 같은 코드 경로를 타므로 실제 PDF 와 내용이 같다.

    python brand/sample_shots.py        # brand/assets/samples/*.png
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

TEMPLATE_DIR = ROOT / "templates"
OUT = Path(__file__).resolve().parent / "assets" / "samples"

BRAND = "Ortica"
FOOTER = "© Ortica 오르티카 영어"


# ── WeasyPrint 자리에 HTML 가로채기 ───────────────────────────────────────
_captured: list[str] = []


def _install_html_capture() -> None:
    """`from weasyprint import CSS, HTML` 를 가로채는 가짜 모듈을 끼운다.

    src/render.py 를 고치지 않고도 각 자료의 HTML 을 그대로 얻을 수 있다.
    """
    if "weasyprint" in sys.modules and getattr(sys.modules["weasyprint"], "_ortica_stub", False):
        return

    class _HTML:
        def __init__(self, string: str = "", base_url: str | None = None):
            _captured.append(string)

        def write_pdf(self, *_a, **_k) -> None:
            pass

        def render(self, *_a, **_k):
            raise RuntimeError("미리보기에서는 페이지 계산을 쓰지 않습니다")

    class _CSS:
        def __init__(self, *_a, **_k):
            pass

    stub = types.ModuleType("weasyprint")
    stub.HTML = _HTML
    stub.CSS = _CSS
    stub._ortica_stub = True
    sys.modules["weasyprint"] = stub


def _capture(fn, *args, **kwargs) -> str:
    """렌더 함수를 부르고 그 안에서 만들어진 HTML 을 돌려준다."""
    _install_html_capture()
    _captured.clear()
    fn(*args, **kwargs)
    if not _captured:
        raise RuntimeError(f"{fn.__name__} 에서 HTML 을 잡지 못했습니다")
    return _captured[-1]


def _with_styles(html: str) -> str:
    """WeasyPrint 가 따로 붙이던 stylesheet 를 문서 안에 넣는다."""
    css = (TEMPLATE_DIR / "styles.css").read_text(encoding="utf-8")
    # 인쇄용 스타일이라 배경을 지정하지 않는다. 화면 촬영에서는 흰 종이를 깔아 준다.
    css += "\nhtml,body{background:#ffffff;}"
    head = f'<head><base href="{TEMPLATE_DIR.as_uri()}/"><style>{css}</style>'
    return html.replace("<head>", head, 1)


# ── 미리보기 만들기 ───────────────────────────────────────────────────────
def sample_reports(n: int = 1):
    from samples.sample_mock import mock_report
    titles = [("The Value of Curiosity", "2026학년도 6월 학평 31번", "31"),
              ("Why Cities Grow", "2026학년도 9월 학평 34번", "34")]
    return [mock_report(t, s, no) for t, s, no in titles[:n]]


def _trim_bottom(path: Path, pad: int = 24) -> None:
    """아래쪽 빈 여백을 잘라낸다. 자료마다 분량이 달라 높이를 미리 못 맞춘다."""
    from PIL import Image

    with Image.open(path) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        px = rgb.load()
        last = 0
        for y in range(h - 1, -1, -1):
            row_empty = all(px[x, y] == (255, 255, 255) for x in range(0, w, 7))
            if not row_empty:
                last = y
                break
        new_h = min(h, last + pad)
        if new_h < h - 4:
            rgb.crop((0, 0, w, new_h)).save(path)


def shoot_all(width: int = 860) -> list[Path]:
    from render import html_to_png
    from src import render as R

    OUT.mkdir(parents=True, exist_ok=True)
    reps = sample_reports(1)
    made: list[Path] = []

    def shoot(name: str, html: str, height: int, trim: bool = True) -> None:
        path = html_to_png(_with_styles(html), OUT / name, width, height)
        if trim:
            _trim_bottom(path)
        made.append(path)
        from PIL import Image
        with Image.open(path) as im:
            print(f"  ✔ samples/{name}  ({im.width}×{im.height})")

    # 1) 지문분석지 — 여섯 섹션이 한 화면에 들어오도록 넉넉히
    shoot("analysis.png",
          R.render_html(reps, footer_note=FOOTER, brand=BRAND), 1500)

    # 2) 한줄해석 — 문장 번호대로 원문과 해석이 나란히 붙는 앞부분
    shoot("one-line.png",
          R.render_html(reps, footer_note=FOOTER, brand=BRAND,
                        with_source=True), 330)

    # 3) 핵심 어휘 리스트
    shoot("vocablist.png",
          _capture(R.render_vocablist_pdf, reps, OUT / "_tmp.pdf",
                   footer_note=FOOTER), 1400)

    # 4) 핵심 어휘 시험지
    shoot("vocabtest.png",
          _capture(R.render_vocabtest_pdf, reps, OUT / "_tmp.pdf",
                   footer_note=FOOTER), 1800)

    (OUT / "_tmp.pdf").unlink(missing_ok=True)
    return made


if __name__ == "__main__":
    made = shoot_all()
    print(f"\n{len(made)}개 → {OUT}")
