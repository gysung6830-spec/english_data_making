"""Analysis → HTML(레이아웃 A/B) → PDF (명세서 §5-5, §5-6).

- render_a_html / render_b_html : Analysis 목록을 HTML 문자열로.
- render_pdf                    : HTML → PDF. Playwright(Chromium) 우선, 없으면 WeasyPrint.

템플릿은 CSS 를 <style> 에 내장해 자체 완결형이므로 base_url·외부 폰트 로드가 필요 없다.
"""
from __future__ import annotations

import base64
import functools
import io
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Analysis

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = ROOT / "templates"
FONT_DIR = Path(__file__).resolve().parent / "fonts"

# ── 나눔스퀘어라운드 임베드(모든 환경에서 동일한 글꼴·자간 → 줄간격 일정) ──────────
# HTML 안에 폰트를 base64 로 심어 렌더 엔진(Chromium/WeasyPrint)이 시스템 글꼴 유무와
# 무관하게 '똑같은 글꼴 메트릭'으로 그린다. 매 렌더마다 실제 쓰인 문자만 서브셋하여
# 용량을 최소화(수십 KB)한다. 서브셋 결과는 문자 집합 기준으로 캐시(밀도 티어 반복 대비).
_FONT_FACES = [                      # (font-weight, 파일명)
    ("400", "NanumSquareRoundR.ttf"),
    ("700", "NanumSquareRoundB.ttf"),
    ("800", "NanumSquareRoundEB.ttf"),
]
# 항상 포함할 기본 문자: ASCII·원문자 ①~⑳·화살표·따옴표·대시 등
_BASE_UNI = (
    set(range(0x0020, 0x007F)) | set(range(0x2460, 0x2474))
    | {0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x2026, 0x00B7, 0x2013, 0x2014,
       0x2018, 0x2019, 0x201C, 0x201D, 0x2605, 0x2606, 0x00D7, 0x2192}
)
_subset_cache: dict[frozenset, str] = {}


@functools.lru_cache(maxsize=1)
def _font_raw() -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    for w, fn in _FONT_FACES:
        p = FONT_DIR / fn
        if p.exists():
            out.append((w, p.read_bytes()))
    return out


def _font_face_css(chars: frozenset) -> str:
    """주어진 문자 집합만 담은 @font-face(base64) <style> 블록. 실패 시 빈 문자열."""
    cached = _subset_cache.get(chars)
    if cached is not None:
        return cached
    raw = _font_raw()
    if not raw:
        _subset_cache[chars] = ""
        return ""
    try:
        from fontTools.subset import Options, Subsetter
        from fontTools.ttLib import TTFont
    except Exception:
        _subset_cache[chars] = ""
        return ""
    opt = Options()
    opt.name_IDs = ["*"]
    opt.notdef_outline = True
    opt.layout_features = []          # 학습지엔 OpenType 피처 불필요 → 용량 절감
    opt.drop_tables += ["GSUB", "GPOS"]
    faces: list[str] = []
    for w, data in raw:
        try:
            f = TTFont(io.BytesIO(data))
            ss = Subsetter(options=opt)
            ss.populate(unicodes=set(chars))
            ss.subset(f)
            buf = io.BytesIO()
            f.save(buf)
            f.close()
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception:
            continue
        faces.append(
            "@font-face{font-family:'NanumSquareRound';font-style:normal;"
            f"font-weight:{w};font-display:swap;"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}"
        )
    css = ("<style>" + "".join(faces) + "</style>") if faces else ""
    _subset_cache[chars] = css
    return css


_STYLE_RE = re.compile(r"<style>", re.IGNORECASE)


def _inject_fonts(html: str) -> str:
    """HTML 에 실제 쓰인 글자만 서브셋한 나눔스퀘어라운드 @font-face 를 앞에 삽입."""
    chars = frozenset(_BASE_UNI | {ord(c) for c in html if ord(c) > 0x7F})
    css = _font_face_css(chars)
    if not css:
        return html
    m = _STYLE_RE.search(html)          # 첫 <style> 앞(=head 안)에 폰트를 먼저 선언
    if not m:
        return html
    i = m.start()
    return html[:i] + css + html[i:]

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

# 원문자 ①~⑳ 변환 (레이아웃 B 번호용). 20 초과는 (n) 으로 폴백.
_CIRCLED = [chr(0x2460 + i) for i in range(20)]


def circled(n: int) -> str:
    return _CIRCLED[n - 1] if 1 <= n <= 20 else f"({n})"


_env.globals["circled"] = circled
# 매칭 문제 오른쪽 보기 라벨: 0→A, 1→B … (25 초과는 순환 방지용 숫자 폴백)
_env.globals["abc"] = lambda i: chr(65 + i) if 0 <= i < 26 else str(i + 1)


def _strip_ans_markers(text: str) -> str:
    """본문 표시용: 정답 표기 괄호만 제거하고 '정상 괄호'는 살린다.

    (X)·(O)·(A) 같은 '한 글자 정답/오답 표기'는 지우되, (Friday)·(2020)·(Country)
    처럼 내용이 든 괄호는 그대로 둔다. 예전에는 모든 '(' ')' 를 지워
    '12th (Friday)' 가 '12thFriday' 로 뭉치는 문제가 있었다.
    """
    import re
    s = re.sub(r"\(\s*[A-Za-z0-9]\s*\)", "", str(text))   # (X)·(1) 등 한 글자 표기만 제거
    return re.sub(r"\s{2,}", " ", s).strip()


_env.filters["ansclean"] = _strip_ans_markers


def _as_list(analyses) -> list[Analysis]:
    if isinstance(analyses, Analysis):
        return [analyses]
    return list(analyses)


def _ensure_vocab_test(a: Analysis) -> None:
    """단어 TEST 순서를 '결정적으로' 한 번만 섞어 a.vocab_test 에 채운다.

    지문 내용(제목+단어들)으로 시드를 만들어 매 렌더마다 같은 순서가 나오게 한다
    (측정 렌더와 최종 렌더, 교사/학생/정답 렌더가 모두 같은 순서를 써야 하기 때문).
    유의어/반의어는 테스트에서 제외하므로 여기선 단어·뜻만 쓰는 VocabEntry 를 그대로 담는다.
    """
    import hashlib
    import random

    if getattr(a, "vocab_test", None) or not getattr(a, "vocab", None):
        return
    seed_src = (a.title_en or "") + "|" + "|".join(v.word for v in a.vocab)
    seed = int.from_bytes(hashlib.md5(seed_src.encode("utf-8")).digest()[:4], "big")
    items = list(a.vocab)
    random.Random(seed).shuffle(items)
    a.vocab_test = items


def _ensure_vocab_match(a: Analysis) -> None:
    """유의어(=)·반의어(↔) '줄 잇기(매칭)' 문제 데이터를 결정적으로 만들어 붙인다.

    각 단어의 유의어/반의어(첫 항목)를 오른쪽 보기로 두고 '한 번만' 섞어(제목 시드),
    학생이 왼쪽 단어와 오른쪽 보기를 선으로 잇게 한다. 정답(왼쪽 i ↔ 오른쪽 위치)도 함께.
    match_syn / match_ant 는 렌더 전용 임시 속성(직렬화 대상 아님).
    """
    import hashlib
    import random

    if getattr(a, "match_syn", None) is not None:
        return
    _DASH = {"—", "-", ""}

    def build(kind: str) -> dict:
        pairs = []
        for v in (a.vocab or []):
            raw = (getattr(v, kind, "") or "").strip()
            first = raw.split(",")[0].strip() if raw else ""
            if first and first not in _DASH and v.word:
                pairs.append((v.word, first))
        if len(pairs) < 3:          # 매칭으로 내기엔 너무 적으면 생략
            return {}
        pairs = pairs[:6]           # 뜻쓰기와 한 페이지에 담기 위해 최대 6쌍
        seed = int.from_bytes(
            hashlib.md5(((a.title_en or "") + "|" + kind).encode("utf-8")).digest()[:4], "big")
        order = list(range(len(pairs)))
        random.Random(seed).shuffle(order)
        right = [pairs[i][1] for i in order]        # 섞인 보기(오른쪽)
        pos = {order[j]: j for j in range(len(order))}
        answer = [pos[i] for i in range(len(pairs))]  # 왼쪽 i → 오른쪽 위치
        return {"items": [p[0] for p in pairs], "right": right, "answer": answer}

    a.match_syn = build("syn")
    a.match_ant = build("ant")


def render_a_html(analyses, footer_note: str = "", footer_meta: str = "",
                  compact: bool = False, include_back: bool = True,
                  include_guide: bool = True, only_back: bool = False,
                  student: bool = False, slevel: str = "slash",
                  boxmode: str = "", include_test: bool = False,
                  only_answer: bool = False, only_test: bool = False,
                  only_guide: bool = False, only_front: bool = False,
                  only_source: bool = False, only_summary: bool = False,
                  toc: list | None = None) -> str:
    """레이아웃 A(분석 학습지형) HTML.

    footer_note   : 하단 우측 저작권 문구.
    footer_meta   : 하단 좌측 페이지 라벨(예: '2025년 06월 고2 모의고사 분석서').
    compact       : 압축 밀도(한 지문을 최대한 1페이지에).
    include_back  : 뒷페이지(어휘/흐름) 포함 여부(측정 시 False).
    include_guide : 맨 앞 '활용 가이드' 표지 페이지 포함 여부(측정 시 False).
    only_back     : 뒷면만 렌더(뒷면 페이지 수 측정용).
    only_guide/only_front/only_source/only_summary/only_test/only_answer :
                    특정 섹션만 렌더(합본 순서 재배치용). toc: 가이드 목차 항목.
    """
    alist = _as_list(analyses)
    for a in alist:
        _ensure_vocab_test(a)               # 단어 TEST 순서 결정(테스트/정답 동일 순서)
        _ensure_vocab_match(a)              # 유의어·반의어 줄잇기 매칭 데이터
    tmpl = _env.get_template("worksheet_a.html.j2")
    html = tmpl.render(analyses=alist, footer_note=footer_note,
                       footer_meta=footer_meta, compact=compact,
                       include_back=include_back, include_guide=include_guide,
                       only_back=only_back, student=student, slevel=slevel,
                       boxmode=boxmode, include_test=include_test,
                       only_answer=only_answer, only_test=only_test,
                       only_guide=only_guide, only_front=only_front,
                       only_source=only_source, only_summary=only_summary,
                       toc=toc or [])
    return _inject_fonts(html)


def render_b_html(analyses, footer_note: str = "", brand: str = "은아 T") -> str:
    """레이아웃 B(직독직해형) HTML.

    영어 원문을 의미 단위(청크)로 끊어 직독직해와 대응시키고, 문장별 핵심 문법 태그와
    핵심 단어를 함께 싣는다. brand 는 헤더 'made by …' 문구(빈 문자열이면 생략).
    """
    tmpl = _env.get_template("worksheet_b.html.j2")
    html = tmpl.render(analyses=_as_list(analyses), footer_note=footer_note, brand=brand)
    return _inject_fonts(html)


def render_html(analyses, layout: str = "A", footer_note: str = "",
                brand: str = "은아 T", footer_meta: str = "", compact: bool = False,
                include_guide: bool = True, student: bool = False,
                slevel: str = "slash", boxmode: str = "", include_test: bool = False,
                only_answer: bool = False, only_test: bool = False,
                include_back: bool = True, only_guide: bool = False,
                only_front: bool = False, only_source: bool = False,
                only_summary: bool = False, toc: list | None = None) -> str:
    if layout.upper() == "B":
        return render_b_html(analyses, footer_note=footer_note, brand=brand)
    return render_a_html(analyses, footer_note=footer_note, footer_meta=footer_meta,
                         compact=compact, include_guide=include_guide,
                         student=student, slevel=slevel, boxmode=boxmode,
                         include_test=include_test, only_answer=only_answer,
                         only_test=only_test, include_back=include_back,
                         only_guide=only_guide, only_front=only_front,
                         only_source=only_source, only_summary=only_summary,
                         toc=toc)


def _measure_pages_chromium(htmls: list[str]) -> list[int] | None:
    """여러 HTML 의 페이지 수를 '실제 렌더 엔진(Chromium)'으로 측정(브라우저 1회 재사용).

    최종 출력이 Chromium 이므로 측정도 같은 엔진으로 해야 1페이지 판정이 실제와
    일치한다(WeasyPrint 와는 경계에서 ±1 어긋날 수 있음). 불가하면 None.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    import tempfile

    import pypdfium2 as pdfium
    counts: list[int] = []
    try:
        with sync_playwright() as p:
            launch_kw: dict = {"args": ["--no-sandbox"]}
            exe = _find_chromium()
            if exe:
                launch_kw["executable_path"] = exe
            browser = p.chromium.launch(**launch_kw)
            page = browser.new_page(viewport=A4_VIEWPORT)
            for html in htmls:
                page.set_content(html, wait_until="networkidle")
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tf:
                    page.pdf(path=tf.name, format="A4", print_background=True,
                             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
                    counts.append(len(pdfium.PdfDocument(tf.name)))
            browser.close()
        return counts
    except Exception:
        return None


def _page_counts(htmls: list[str]) -> list[int]:
    """각 HTML 페이지 수. Chromium(최종 엔진) 우선, 안 되면 WeasyPrint 로 폴백."""
    counts = _measure_pages_chromium(htmls)
    if counts is not None:
        return counts
    from weasyprint import HTML  # dep
    return [len(HTML(string=h).render().pages) for h in htmls]


# 앞면 밀도 티어(큰→작): roomy=13px(짧은 지문은 크게 키워 페이지 채움) → normal=12px
# → compact=11px(빠듯할 때). 1페이지에 들어가는 '가장 큰' 티어를 골라 여백을 최소화한다.
_FRONT_TIERS = ["roomy", "normal", "compact"]


def _fit_pages(analyses, fit_front: bool = True,
               student: bool = False, slevel: str = "slash",
               boxmode: str = "") -> None:
    """앞면(분석)·뒷면(정리)을 지문마다 최대한 1페이지에 맞춘다(넘치는 장문은 2페이지).

    - 앞면: normal→compact→ultra 중 1페이지가 되는 가장 큰(덜 압축된) 단계.
    - 뒷면: 기본 압축으로 넘치면 btight 로 1페이지가 될 때만 적용.
    모든 후보를 모아 렌더 엔진 측정을 '한 번'에 수행(대량 처리 시 브라우저 1회).
    fit_front=False 면 앞면은 이미 정해진 밀도를 쓰고 뒷면만 맞춘다.
    학생용(student)은 빈칸 공간까지 반영해 측정한다.
    """
    lst = _as_list(analyses)
    jobs: list[tuple[int, str, object]] = []   # (지문 index, 'front'|'back', tier)
    htmls: list[str] = []
    for i, a in enumerate(lst):
        if fit_front:
            for t in _FRONT_TIERS:
                a.front_density = t
                jobs.append((i, "front", t))
                htmls.append(render_a_html([a], include_back=False, include_guide=False,
                                           student=student, slevel=slevel, boxmode=boxmode))
        # 뒷면(정리)은 고정 '읽기 좋은' 크기로 렌더(측정 불필요). 내용 많으면 자연 분할로 2쪽,
        # 첫 쪽을 꽉 채우고 남는 것만 넘긴다(원문블록·표 행·흐름 단계는 안 쪼개짐).
    if not htmls:
        return
    try:
        counts = _page_counts(htmls)
    except Exception:
        for a in lst:
            if fit_front:
                a.front_density = "compact"
        return

    for i, a in enumerate(lst):
        if fit_front:
            # 1페이지에 맞는 가장 큰(=가장 잘 보이는) 티어를 고른다.
            # normal(12px)이 1페이지에 들어가면 그걸로 '꽉 차게', 넘치면 compact(11px).
            # 둘 다 1페이지를 못 맞추는 장문이면 '기본' 크기(compact=11px)로 2페이지에 편다.
            chosen = "compact"
            for (j, kind, t), c in zip(jobs, counts):
                if j == i and kind == "front":
                    if c <= 1:
                        chosen = t
                        break
            a.front_density = chosen


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
# A4 96dpi 뷰포트(명세서 §11): 794×1123
A4_VIEWPORT = {"width": 794, "height": 1123}


def _find_chromium() -> str | None:
    """미리 설치된 Chromium 실행 파일 경로(있으면). 버전 불일치 시 이걸로 실행."""
    import glob
    import os

    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    for pat in ("chromium-*/chrome-linux/chrome",
                "chromium-*/chrome-linux64/chrome",
                "chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(os.path.join(base, pat)), reverse=True)
        for h in hits:
            if os.path.exists(h):
                return h
    return None


def _pdf_playwright(html: str, out_path: Path) -> bool:
    """Playwright(Chromium)로 HTML→PDF. 사용 불가하면 False.

    Chromium 은 CSS 를 정확히(특히 폭0 주석) 렌더하므로 단어 간격이 촘촘하다.
    번들 브라우저 버전이 안 맞으면 미리 설치된 Chromium 경로로 실행한다.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False
    try:
        with sync_playwright() as p:
            launch_kw: dict = {"args": ["--no-sandbox"]}
            exe = _find_chromium()
            if exe:
                launch_kw["executable_path"] = exe
            browser = p.chromium.launch(**launch_kw)
            page = browser.new_page(viewport=A4_VIEWPORT)
            page.set_content(html, wait_until="networkidle")
            page.pdf(path=str(out_path), format="A4", print_background=True,
                     margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            browser.close()
        return True
    except Exception:
        return False


def _pdf_weasyprint(html: str, out_path: Path) -> None:
    from weasyprint import HTML  # 지연 임포트(무거움)

    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path))


def render_pdf(analyses, out_path: str | Path, layout: str = "A",
               footer_note: str = "", brand: str = "은아 T",
               engine: str = "auto", footer_meta: str = "",
               density: str = "auto", student: bool = False,
               slevel: str = "slash", include_guide: bool = True,
               boxmode: str = "", include_test: bool = False,
               only_answer: bool = False, only_test: bool = False,
               include_back: bool = True, only_guide: bool = False,
               only_front: bool = False, only_source: bool = False,
               only_summary: bool = False, toc: list | None = None) -> Path:
    """Analysis → PDF.

    engine  : 'auto' | 'playwright' | 'weasyprint'.
    brand   : 레이아웃 B 헤더 'made by …' 문구.
    density : 'normal' | 'compact' | 'auto'. 'auto' 는 앞면이 지문당 1페이지를 넘으면
              자동으로 압축 밀도로 다시 맞춘다(레이아웃 A 한정).
    student : True 면 학생용(필기) — 정답/해석을 비워 빈칸으로.
    slevel  : 'slash'(끊어읽기만) | 'blank'(완전백지) | 'interp'(해석만 빈칸).
    include_guide : 맨 앞 '활용 가이드' 표지 포함 여부(합본 시 학생용은 False).
    include_test  : 지문마다 '단어 TEST' 페이지 포함.
    only_answer   : 단어 TEST '정답'만 렌더(밀도 측정 생략, 맨 뒤 합본용).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    compact = (density == "compact")
    # 밀도 자동맞춤은 앞면(분석) 렌더에만 필요 — 정답/테스트/가이드/원문/정리 단독 렌더는 생략.
    _skip_fit = only_answer or only_test or only_guide or only_source or only_summary
    if layout.upper() == "A" and not _skip_fit:
        if density == "auto":
            _fit_pages(analyses, fit_front=True, student=student, slevel=slevel,
                       boxmode=boxmode)
        else:                                        # 'normal' | 'compact' 고정
            for a in _as_list(analyses):
                a.front_density = density
            _fit_pages(analyses, fit_front=False, student=student, slevel=slevel,
                       boxmode=boxmode)
    html = render_html(analyses, layout=layout, footer_note=footer_note, brand=brand,
                       footer_meta=footer_meta, compact=compact,
                       student=student, slevel=slevel, include_guide=include_guide,
                       boxmode=boxmode, include_test=include_test,
                       only_answer=only_answer, only_test=only_test,
                       include_back=include_back, only_guide=only_guide,
                       only_front=only_front, only_source=only_source,
                       only_summary=only_summary, toc=toc)

    if engine in ("auto", "playwright"):
        if _pdf_playwright(html, out_path):
            return out_path
        if engine == "playwright":
            raise RuntimeError("Playwright(Chromium)를 사용할 수 없습니다.")
    _pdf_weasyprint(html, out_path)
    return out_path
