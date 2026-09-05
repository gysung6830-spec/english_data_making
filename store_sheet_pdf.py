#!/usr/bin/env python3
"""단어 시험지를 **진짜 PDF** 로 만듭니다.

화면에서 A4 를 흉내 내고 인쇄 창에 맡기면, 브라우저마다 배율·여백이 달라
글씨 크기와 줄바꿈이 제각각으로 나옵니다. 그래서 지면을 여기서 직접 짭니다.

  - A4 세로, 여백 13mm(위아래) · 12mm(좌우) 로 고정입니다.
  - 내용이 한 장을 넘치면 **다음 장으로 이어집니다.** 문항 수를 줄이실 필요가 없습니다.
  - 화면에 보이는 것과 종이에 나오는 것이 같습니다. 같은 PDF 를 그림으로 바꿔 보여 줍니다.

글꼴은 사이트가 이미 갖고 있는 나눔스퀘어라운드(woff)를 한 번만 ttf 로 바꿔 씁니다.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "store_static" / "fonts"
CACHE_DIR = ROOT / "store_data" / ".cache"
FACES = {"R": ("NanumSquareRoundR.woff", "OrticaSheet"),
         "B": ("NanumSquareRoundB.woff", "OrticaSheet-B")}

try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    AVAILABLE = True
except ImportError:                                   # 라이브러리가 없으면 PDF 를 안 냅니다
    AVAILABLE = False

MM = 72 / 25.4
PW, PH = (210 * MM, 297 * MM) if AVAILABLE else (595.28, 841.89)
MARGIN_X, MARGIN_Y = 12 * MM, 13 * MM
BODY_W = PW - MARGIN_X * 2
TOP = PH - MARGIN_Y
BOTTOM = MARGIN_Y

INK = (0.086, 0.094, 0.110)          # #16181c
GRAY = (0.353, 0.380, 0.412)         # #5a6169
FAINT = (0.541, 0.565, 0.596)        # #8a9097
RULE = (0.878, 0.894, 0.910)         # #e0e4e8
GREEN = (0.078, 0.420, 0.290)        # #146b4a

_ready: bool | None = None


def _fonts() -> tuple[str, str]:
    """(보통, 굵게) 글꼴 이름. 준비가 안 되면 Helvetica 로 물러섭니다."""
    global _ready
    if _ready is False:
        return "Helvetica", "Helvetica-Bold"
    if _ready is True:
        return FACES["R"][1], FACES["B"][1]
    try:
        from fontTools.ttLib import TTFont as FTFont
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for woff, name in FACES.values():
            ttf = CACHE_DIR / (Path(woff).stem + ".ttf")
            if not ttf.exists():
                face = FTFont(str(FONT_DIR / woff))
                face.flavor = None
                face.save(str(ttf))
            pdfmetrics.registerFont(TTFont(name, str(ttf)))
        _ready = True
        return FACES["R"][1], FACES["B"][1]
    except Exception as exc:                          # 한글이 안 나와도 시험지는 나갑니다
        log.warning("시험지 글꼴을 준비하지 못했습니다: %s", exc)
        _ready = False
        return "Helvetica", "Helvetica-Bold"


# ---------------------------------------------------------------------------
# 지면 짜기
# ---------------------------------------------------------------------------
class Sheet:
    """A4 한 장씩 채워 나가는 도구. 자리가 모자라면 알아서 다음 장으로 넘깁니다."""

    def __init__(self, head: dict, subline: str, brand: str, year: int):
        self.reg, self.bold = _fonts()
        self.buf = io.BytesIO()
        self.c = rl_canvas.Canvas(self.buf, pagesize=(PW, PH))
        self.c.setTitle(head.get("title") or "어휘 TEST")
        self.head, self.subline, self.brand, self.year = head, subline, brand, year
        self.pages = 0
        self.y = TOP
        self.started = False
        # 지면마다 다시 그리는 머리말 정보 (문항 수·정답지 여부는 장마다 바뀝니다)
        self._title = ""
        self._score = 0
        self._answer = False

    # -- 낮은 층 -------------------------------------------------------------
    def _text(self, x, y, s, font, size, color=INK):
        self.c.setFont(font, size)
        self.c.setFillColorRGB(*color)
        self.c.drawString(x, y, s)

    def _w(self, s, font, size) -> float:
        return self.c.stringWidth(s, font, size)

    def _line(self, x1, y, x2, width=0.6, color=RULE, dash=None):
        self.c.setStrokeColorRGB(*color)
        self.c.setLineWidth(width)
        self.c.setDash(dash or [])
        self.c.line(x1, y, x2, y)
        self.c.setDash([])

    def _fit(self, s, font, size, width, floor=6.6) -> tuple[str, float]:
        """폭에 맞게 글씨를 줄이고, 그래도 넘치면 끝을 … 로 자릅니다."""
        s = (s or "").strip()
        if not s:
            return "", size
        while size > floor and self._w(s, font, size) > width:
            size -= 0.4
        if self._w(s, font, size) <= width:
            return s, size
        while s and self._w(s + "…", font, size) > width:
            s = s[:-1]
        return (s + "…") if s else "", size

    def _wrap(self, s, font, size, width) -> list[str]:
        """우리말이 섞여도 되도록 글자 단위로 접습니다. (띄어쓰기를 우선 봅니다)"""
        out, line = [], ""
        for word in (s or "").split(" "):
            trial = (line + " " + word).strip()
            if self._w(trial, font, size) <= width or not line:
                line = trial
                while self._w(line, font, size) > width and len(line) > 1:
                    cut = len(line)
                    while cut > 1 and self._w(line[:cut], font, size) > width:
                        cut -= 1
                    out.append(line[:cut])
                    line = line[cut:]
            else:
                out.append(line)
                line = word
        if line:
            out.append(line)
        return out or [""]

    # -- 지면 -----------------------------------------------------------------
    def new_page(self, title: str, score: int, answer: bool):
        """새 장을 열고 머리말을 그립니다."""
        if self.started:
            self.c.showPage()
        self.started = True
        self.pages += 1
        self._title, self._score, self._answer = title, score, answer
        self.y = TOP
        head = self.head

        if head.get("place"):
            self._text(MARGIN_X, self.y - 8.6, head["place"], self.bold, 8.6, GRAY)
            self.y -= 13

        top = self.y
        line = title + (" · 정답" if answer else "")
        # 오른쪽 칸(이름·점수)을 먼저 재고, 남는 폭에 제목을 맞춥니다
        right = self._fill_width(answer)
        text, size = self._fit(line, self.bold, 11.6, BODY_W - right - 14)
        self._text(MARGIN_X, top - 11.6, text, self.bold, size)
        self._fill_draw(top - 11.6, answer)
        self.y = top - 11.6 - 7
        self._line(MARGIN_X, self.y, PW - MARGIN_X, 1.2, INK)
        self.y -= 12

        if self.subline:
            self._text(MARGIN_X, self.y - 8.6, self.subline, self.reg, 8.6, GRAY)
            self.y -= 13
        self._footer()

    def _fill_width(self, answer: bool) -> float:
        if answer:
            return self._w("정답이 채워진 답지입니다", self.bold, 8.6) + 6
        w = 0.0
        if self.head.get("date"):
            w += self._w(self.head["date"], self.reg, 9) + 12
        elif self.head.get("dateblank"):
            w += self._w("날짜 ", self.reg, 9) + 57 + 12
        w += self._w("이름 ", self.reg, 9) + 57 + 12
        w += self._w("점수 ", self.reg, 9) + 26 + self._w(f" / {self._score}", self.reg, 9)
        return w

    def _fill_draw(self, y, answer: bool):
        """오른쪽 위 — 날짜 · 이름 · 점수 칸."""
        if answer:
            s = "정답이 채워진 답지입니다"
            self._text(PW - MARGIN_X - self._w(s, self.bold, 8.6), y, s, self.bold, 8.6, GREEN)
            return
        x = PW - MARGIN_X - self._fill_width(False)
        head = self.head
        if head.get("date"):
            self._text(x, y, head["date"], self.reg, 9, GRAY)
            x += self._w(head["date"], self.reg, 9) + 12
        elif head.get("dateblank"):
            self._text(x, y, "날짜", self.reg, 9, GRAY)
            x += self._w("날짜 ", self.reg, 9)
            self._line(x, y - 2, x + 57, 0.6, FAINT)
            x += 57 + 12
        self._text(x, y, "이름", self.reg, 9, GRAY)
        x += self._w("이름 ", self.reg, 9)
        self._line(x, y - 2, x + 57, 0.6, FAINT)
        x += 57 + 12
        self._text(x, y, "점수", self.reg, 9, GRAY)
        x += self._w("점수 ", self.reg, 9)
        self._line(x, y - 2, x + 26, 0.6, FAINT)
        x += 26
        self._text(x, y, f" / {self._score}", self.reg, 9, GRAY)

    def _footer(self):
        y = BOTTOM - 2
        self._line(MARGIN_X, y + 11, PW - MARGIN_X, 0.6, RULE)
        self._text(MARGIN_X, y, f"©{self.year}. {self.brand}. All rights reserved",
                   self.reg, 7.9, FAINT)
        no = str(self.pages)
        self._text(PW - MARGIN_X - self._w(no, self.reg, 7.9), y, no, self.reg, 7.9, FAINT)

    def room(self) -> float:
        """지금 장에 남은 높이."""
        return self.y - (BOTTOM + 16)

    def section_head(self, roman, title, guide, count, hinted, answer):
        self.y -= 4
        x = MARGIN_X
        self._text(x, self.y - 10.9, f"{roman}.", self.bold, 10.9)
        x += self._w(f"{roman}. ", self.bold, 10.9)
        self._text(x, self.y - 10.9, title, self.bold, 10.9)
        x += self._w(title + " ", self.bold, 10.9)
        note = "정답이 채워진 답지입니다." if answer else guide
        tail = f" (총 {count}문항{' · 첫 글자 힌트 제공' if hinted else ''})"
        text, size = self._fit(note + tail, self.reg, 8.6, PW - MARGIN_X - x)
        self._text(x, self.y - 10.6, text, self.reg, size, GRAY)
        self.y -= 10.9 + 6
        self._line(MARGIN_X, self.y, PW - MARGIN_X, 0.6, RULE)
        self.y -= 9

    def done(self) -> bytes:
        if self.started:
            self.c.showPage()
        self.c.save()
        return self.buf.getvalue()


# ---------------------------------------------------------------------------
# 문항 그리기
# ---------------------------------------------------------------------------
ROW = 15.5          # 쓰기형 한 줄 높이 (가장 빽빽할 때)
ROW_MAX = 30        # 문항이 적으면 여기까지 벌려 답 쓸 자리를 넓힙니다
GAP = 14.6          # 두 칸 사이


def _draw_write(sh: Sheet, x, y, w, item, kind, answer) -> None:
    """영→한 / 한→영 한 문항. 물음과 답 칸을 한 줄에 놓습니다."""
    no_w = 15
    sh._text(x, y, item["no"], sh.reg, 8.2, FAINT)
    left = x + no_w
    ask = item["en"] if kind == "en_ko" else item["ko"]
    ask_font = sh.bold if kind == "en_ko" else sh.reg
    ask_w = min(w * 0.5, w - 46)
    ask_text, ask_size = sh._fit(ask, ask_font, 9.4, ask_w)
    sh._text(left, y, ask_text, ask_font, ask_size)
    used = sh._w(ask_text, ask_font, ask_size)
    line_x = left + used + 7

    if kind == "ko_en" and not answer and item.get("hint"):
        sh._text(line_x, y, item["hint"], sh.bold, 9, GREEN)
        line_x += sh._w(item["hint"], sh.bold, 9) + 5

    right = x + w
    if answer:
        val = item["ko"] if kind == "en_ko" else item["en"]
        text, size = sh._fit(val, sh.bold, 9, right - line_x)
        sh._text(line_x, y, text, sh.bold, size, GREEN)
    else:
        sh._line(line_x, y - 2.5, right, 0.6, (0.776, 0.796, 0.816))
    sh._line(x, y - 6.5, right, 0.5, RULE, dash=[0.7, 1.7])


def _choice_lines(sh: Sheet, item, w) -> list[list[str]]:
    """보기 다섯 개를 폭에 맞춰 몇 줄로 나눌지 미리 재 둡니다."""
    cell = w - 22
    rows, line = [], []
    used = 0.0
    for i, ch in enumerate(item["choices"], 1):
        s = f"({i}) {ch}"
        need = sh._w(s, sh.reg, 8.6) + 16
        if line and used + need > cell:
            rows.append(line)
            line, used = [], 0.0
        line.append(s)
        used += need
    if line:
        rows.append(line)
    return rows


def _choice_height(sh: Sheet, item, w) -> float:
    return 13 + len(_choice_lines(sh, item, w)) * 12.4 + 6


def _draw_choice(sh: Sheet, x, y, w, item, answer) -> float:
    """객관식 한 문항. 물음 한 줄 아래에 보기를 깔아 놓습니다."""
    sh._text(x, y, item["no"], sh.reg, 8.2, FAINT)
    left = x + 15
    ask, size = sh._fit(item["en"], sh.bold, 9.4, w * 0.6)
    sh._text(left, y, ask, sh.bold, size)
    tag = f"( {item['answer_no']} )" if answer else "(     )"
    sh._text(x + w - sh._w(tag, sh.bold if answer else sh.reg, 9),
             y, tag, sh.bold if answer else sh.reg, 9, GREEN if answer else GRAY)

    yy = y - 13
    for row in _choice_lines(sh, item, w):
        xx = left + 7
        for s in row:
            no = int(s[1])
            right = answer and no == item["answer_no"]
            sh._text(xx, yy, s, sh.bold if right else sh.reg, 8.6,
                     GREEN if right else (0.290, 0.314, 0.341))
            xx += sh._w(s, sh.bold if right else sh.reg, 8.6) + 16
        yy -= 12.4
    bottom = yy + 6
    sh._line(x, bottom, x + w, 0.5, RULE, dash=[0.7, 1.7])
    return y - bottom + 6


def _render_section(sh: Sheet, sec: dict, title: str, answer: bool) -> None:
    """한 유형을 지면에 붓습니다. 넘치면 다음 장으로 이어집니다."""
    items = sec["items"]
    sh.new_page(title, len(items), answer)
    sh.section_head(sec["roman"], sec["title"], sec["guide"],
                    len(items), sec.get("hinted"), answer)

    if sec["kind"] == "choice":
        w = BODY_W
        i = 0
        while i < len(items):
            # 이 장에 몇 문항이 들어가는지 먼저 세어, 남는 자리를 고르게 나눠 줍니다
            room, fit, used = sh.room(), 0, 0.0
            while i + fit < len(items):
                need = _choice_height(sh, items[i + fit], w)
                if used + need > room:
                    break
                used += need
                fit += 1
            fit = max(1, fit)
            slack = min(9.0, max(0.0, (room - used) / fit))
            for item in items[i:i + fit]:
                sh.y -= _draw_choice(sh, MARGIN_X, sh.y - 9.4, w, item, answer) + slack
            i += fit
            if i < len(items):
                sh.new_page(title, len(items), answer)
                sh.section_head(sec["roman"], sec["title"], sec["guide"],
                                len(items), sec.get("hinted"), answer)
        return

    # 쓰기형 — 두 칸으로 흘려 담습니다
    col_w = (BODY_W - GAP) / 2
    i = 0
    while i < len(items):
        top = sh.y
        room = sh.room()
        rows = max(1, int(room // ROW))
        take = min(len(items) - i, rows * 2)
        # 한 장에 다 들어가면 두 칸에 반씩 나눠 담고 (신문처럼 균형을 맞춥니다),
        # 넘칠 때만 왼쪽 칸을 끝까지 채우고 오른쪽으로 넘깁니다.
        left_n = rows if take > rows else (take + 1) // 2
        # 문항이 적어 아래가 휑하면 줄 사이를 벌립니다. 답 쓸 자리가 넓어집니다.
        step = min(ROW_MAX, max(ROW, room / max(1, left_n)))
        for n, item in enumerate(items[i:i + left_n]):
            _draw_write(sh, MARGIN_X, top - 9.4 - n * step, col_w,
                        item, sec["kind"], answer)
        for n, item in enumerate(items[i + left_n:i + take]):
            _draw_write(sh, MARGIN_X + col_w + GAP, top - 9.4 - n * step, col_w,
                        item, sec["kind"], answer)
        i += take
        if i < len(items):
            sh.new_page(title, len(items), answer)
            sh.section_head(sec["roman"], sec["title"], sec["guide"],
                            len(items), sec.get("hinted"), answer)


def build(sections: list[dict], head: dict, book_name: str, scope: str,
          brand: str, year: int) -> bytes | None:
    """학생용 전부 → 정답지 전부 순서로 한 파일에 담습니다."""
    if not AVAILABLE or not sections:
        return None
    title = head.get("title") or f"어휘 TEST · {book_name} · {scope}"
    sub = f"{book_name} · {scope}" if head.get("title") and book_name not in head["title"] else ""
    try:
        sh = Sheet(head, sub, brand, year)
        for answer in (False, True):
            for sec in sections:
                _render_section(sh, sec, title, answer)
        return sh.done()
    except Exception as exc:                          # PDF 가 안 되면 화면으로 물러섭니다
        log.warning("시험지 PDF 를 만들지 못했습니다: %s", exc)
        return None


def page_count(sections: list[dict]) -> int:
    """몇 쪽짜리인지 — 만들어 봐야 정확합니다. 미리 보기 안내에 씁니다."""
    blob = build(sections, {}, "", "", "", 2026)
    if not blob:
        return 0
    try:
        import pymupdf
        with pymupdf.open(stream=blob, filetype="pdf") as doc:
            return doc.page_count
    except Exception:
        return 0
