"""Report -> HTML -> PDF (Jinja2 + WeasyPrint)."""
from __future__ import annotations

import random
from pathlib import Path

import re

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from . import schemas

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

# 특히 중요한 핵심 어법 키워드 (부각 표시용)
KEY_GRAMMAR = ["관계", "분사", "가정법", "비교", "도치", "강조", "5형식", "5 형식", "사역", "지각"]


def _is_key_grammar(text: str | None) -> bool:
    if not text:
        return False
    return any(k in text for k in KEY_GRAMMAR)


_env.filters["is_key_grammar"] = _is_key_grammar


def _highlight_words(text: str | None, words) -> Markup:
    """영어 요약문 안에서 핵심 단어(words)를 굵게 표시."""
    if not text:
        return Markup("")
    ws = sorted({w.strip() for w in (words or []) if w and w.strip()}, key=len, reverse=True)
    if not ws:
        return escape(text)
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in ws) + r")\b", re.IGNORECASE)
    out: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        out.append(str(escape(text[last:m.start()])))
        out.append('<b class="kw">' + str(escape(m.group(0))) + "</b>")
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


_env.filters["highlight_words"] = _highlight_words


# 매칭 시 무시할 기능어(내용어만 남겨 어구를 정확히 찾기 위함)
_STOP_WORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "is", "are", "was", "were",
    "be", "been", "being", "and", "or", "but", "it", "its", "this", "that",
    "these", "those", "for", "as", "so", "with", "by", "from", "not", "no",
    "does", "do", "did", "has", "have", "had", "will", "would", "can", "could",
    "we", "you", "they", "he", "she", "them", "us", "here", "there", "too",
    "also", "which", "who", "whom", "whose", "than", "then", "over", "again",
    "almost", "really", "very", "much", "more", "most", "only", "even", "just",
}


def _words(text) -> list[str]:
    return re.findall(r"[a-z']+", (text or "").lower())


def _chunk_color_index(example, chunks, point: str = "") -> int:
    """문법이 가리키는 어구(chunk)의 색 인덱스를 반환.

    직독직해 왼쪽 열의 문법 태그 색을 해당 어구(청크)의 색과 동일하게 맞추기 위함.
    청크 표시 색은 위치 index % 8 이므로 여기서도 같은 기준을 쓴다.

    1) 문법 포인트명에 든 '영어 표지어'(itself, that, much, although 등)가
       왼쪽부터 처음 등장하는 어구를 우선 선택 (가장 신뢰도 높음).
    2) 표지어가 없으면(과거분사·삽입구 등) 예문의 '내용어' 겹침이 가장 큰 어구.
    """
    if not chunks:
        return 0
    chunk_words = [set(_words(getattr(c, "english", ""))) for c in chunks]

    # 1) 포인트명의 표지어 우선 (기능어라도 문법 표지이므로 그대로 사용)
    for tok in _words(point):
        for i, cw in enumerate(chunk_words):
            if tok in cw:
                return i % 8

    # 2) 예문 내용어(기능어 제외) 최다 겹침
    ex = {w for w in _words(example) if w not in _STOP_WORDS}
    if ex:
        best_i, best_score = 0, -1
        for i, cw in enumerate(chunk_words):
            score = len(ex & cw)
            if score > best_score:
                best_score, best_i = score, i
        return best_i % 8
    return 0


_env.filters["chunk_color"] = _chunk_color_index


def _as_list(reports) -> list:
    if isinstance(reports, schemas.Report):
        return [reports]
    return list(reports)


def render_html(reports, footer_note: str = "", brand: str = "은아 T") -> str:
    """reports: 단일 Report 또는 여러 Report(list). 여러 지문이면 순서대로 출력.

    brand: 직독직해 'made by ~' 와 출제표 '~ tip' 에 넣을 이름. 빈 값이면 브랜드 문구 제거.
    (하단 저작권 footer_note 는 brand 와 무관하게 항상 그대로 표시)
    """
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(reports=_as_list(reports), footer_note=footer_note, brand=brand)


def _cap_report(report: schemas.Report, cap: int) -> schemas.Report:
    """어휘 개수를 cap 개로 줄인 사본 반환(원본은 건드리지 않음)."""
    if cap >= len(report.vocab.items):
        return report
    new_vocab = report.vocab.model_copy(update={"items": report.vocab.items[:cap]})
    return report.model_copy(update={"vocab": new_vocab})


def _fit_report(report, footer_note, css, min_vocab: int, brand: str = "은아 T"):
    """한 지문이 2페이지에 들어오도록 어휘 개수를 필요한 만큼만 줄인다."""
    from weasyprint import HTML

    def pages(cap):
        r = _cap_report(report, cap)
        html = render_html([r], footer_note, brand)
        doc = HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=[css])
        return len(doc.pages), r

    n = len(report.vocab.items)
    p, r = pages(n)
    if p <= 2:
        return report            # 이미 2페이지 이내면 그대로
    cap = n
    while cap > min_vocab:       # 최소 개수까지 한 개씩 줄이며 재시도
        cap -= 1
        p, r = pages(cap)
        if p <= 2:
            return r
    return r                     # 최소 개수까지 줄여도 넘치면 그 상태로


def render_pdf(reports, out_path: str | Path, footer_note: str = "",
               fit_pages: bool = True, min_vocab: int = 8,
               brand: str = "은아 T") -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트 (무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    rlist = _as_list(reports)

    def build(rs):
        html = render_html(rs, footer_note, brand)
        return HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=[css])

    doc = build(rlist)
    # 지문 1개당 2페이지(1p: 요약~어휘, 2p: 직독직해)를 넘기면 어휘를 줄여 다시 렌더
    if fit_pages and len(doc.pages) > 2 * len(rlist):
        rlist = [_fit_report(r, footer_note, css, min_vocab, brand) for r in rlist]
        doc = build(rlist)
    doc.write_pdf(str(out_path))
    return out_path


# ---------------------------------------------------------------------------
# 어휘 리스트 / 영단어 시험지 (직독직해 오른쪽 열 단어들 기반)
# ---------------------------------------------------------------------------
def collect_words(reports) -> list[dict]:
    """직독직해 각 chunk 의 words(핵심 단어)를 지문 순서대로 모으고 중복 제거."""
    seen: dict[str, dict] = {}
    order: list[str] = []
    for r in _as_list(reports):
        for s in r.literal.sentences:
            for c in s.chunks:
                for w in c.words:
                    word = (w.word or "").strip()
                    meaning = (w.meaning or "").strip()
                    if not word:
                        continue
                    key = word.lower()
                    if key not in seen:
                        seen[key] = {"word": word, "meaning": meaning}
                        order.append(key)
    return [{"no": i + 1, **seen[k]} for i, k in enumerate(order)]


def _pair_rows(words: list[dict]) -> list[tuple]:
    """단어 목록을 2열(왼쪽 위→아래, 오른쪽 위→아래)로 배치할 행 목록으로 변환."""
    half = (len(words) + 1) // 2
    left, right = words[:half], words[half:]
    rows = []
    for i in range(half):
        rows.append((left[i], right[i] if i < len(right) else None))
    return rows


def render_wordlist_pdf(reports, out_path: str | Path,
                        title: str = "핵심 어휘 리스트", footer_note: str = "") -> Path:
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    words = collect_words(reports)
    tmpl = _env.get_template("wordlist.html.j2")
    html = tmpl.render(title=title, words=words, rows=_pair_rows(words),
                       footer_note=footer_note)
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
    return out_path


def render_quiz_pdf(reports, out_path: str | Path,
                    title: str = "영단어 시험지", footer_note: str = "",
                    seed: int | None = None) -> Path:
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    words = collect_words(reports)
    shuffled = words[:]
    random.Random(seed).shuffle(shuffled)
    for i, w in enumerate(shuffled):   # 섞은 뒤 번호를 다시 매김
        w["no"] = i + 1
    tmpl = _env.get_template("quiz.html.j2")
    html = tmpl.render(title=title, words=shuffled, rows=_pair_rows(shuffled),
                       footer_note=footer_note)
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
    return out_path


def combine_pdfs(pdf_paths: list[Path], out_path: Path) -> Path:
    """여러 지문 PDF 를 하나로 합친다 (pypdf 사용, 없으면 개별 유지)."""
    try:
        from pypdf import PdfWriter
    except Exception:
        return out_path  # 병합 라이브러리 없으면 개별 파일 유지
    writer = PdfWriter()
    for p in pdf_paths:
        writer.append(str(p))
    with out_path.open("wb") as f:
        writer.write(f)
    return out_path
