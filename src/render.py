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

# @font-face(나눔스퀘어라운드)를 실제로 임베드하려면 FontConfiguration 이 필요하다.
_FONT_CONFIG = None


def _font_config():
    """WeasyPrint 용 FontConfiguration 싱글턴(지연 생성)."""
    global _FONT_CONFIG
    if _FONT_CONFIG is None:
        from weasyprint.text.fonts import FontConfiguration
        _FONT_CONFIG = FontConfiguration()
    return _FONT_CONFIG


def _stylesheet():
    """styles.css 를 FontConfiguration 과 함께 로드한 CSS 객체 반환."""
    from weasyprint import CSS
    return CSS(filename=str(TEMPLATE_DIR / "styles.css"), font_config=_font_config())


# 나눔스퀘어라운드를 base64 data URI 로 인라인 임베드한 @font-face CSS.
#   폰트 파일 경로/렌더 base_url 에 의존하지 않으므로 어떤 환경에서도 항상 적용된다.
_FONTS_DIR = TEMPLATE_DIR / "fonts"
_FONT_FACES = [
    (300, "NanumSquareRoundL.woff2"),
    (400, "NanumSquareRoundR.woff2"),
    (700, "NanumSquareRoundB.woff2"),
    (800, "NanumSquareRoundEB.woff2"),
]
_FONT_CSS_TEXT: str | None = None
_FONT_CSS_OBJ = None


def _font_face_css_text() -> str:
    """woff2 를 base64 로 인코딩한 @font-face 규칙 문자열(1회 생성 후 캐시)."""
    global _FONT_CSS_TEXT
    if _FONT_CSS_TEXT is None:
        import base64
        blocks = []
        for weight, fname in _FONT_FACES:
            data = base64.b64encode((_FONTS_DIR / fname).read_bytes()).decode()
            blocks.append(
                '@font-face{font-family:"NanumSquareRound";font-style:normal;'
                f'font-weight:{weight};'
                f'src:url("data:font/woff2;base64,{data}") format("woff2");}}'
            )
        _FONT_CSS_TEXT = "".join(blocks)
    return _FONT_CSS_TEXT


def _font_css():
    """base64 임베드 @font-face 를 담은 WeasyPrint CSS 객체(캐시)."""
    global _FONT_CSS_OBJ
    if _FONT_CSS_OBJ is None:
        from weasyprint import CSS
        _FONT_CSS_OBJ = CSS(string=_font_face_css_text(), font_config=_font_config())
    return _FONT_CSS_OBJ

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


# 서술형 교재 유형의 '표시 순서'(type-major 번호 매김에도 사용).
#   보기어휘 → 요약문 → 어법오류 → 조건영작 → 배열영작 → 문장변형 → 문답
WS_TYPE_ORDER = ["cloze", "summary", "error", "compose", "arrange", "paraphrase", "qa"]


# ---- 서술형 교재용 헬퍼 ---------------------------------------------------
_WS_LBL_RE = re.compile(r"\[\[([A-Za-z])\]\]")
_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


def _circled(n) -> str:
    """1→①, 2→② … 범위를 벗어나면 '(n)'."""
    try:
        i = int(n)
    except (TypeError, ValueError):
        return str(n)
    return _CIRCLED[i - 1] if 1 <= i <= len(_CIRCLED) else f"({i})"


_env.filters["circled"] = _circled


def _sub_labeled(text: str, answers_by_label: dict, reveal: bool) -> Markup:
    """문장 속 [[A]],[[B]] 를 '(A) 빈칸' 또는 '(A) 정답'으로 치환."""
    esc = str(escape(text or ""))

    def repl(m: "re.Match") -> str:
        lab = m.group(1).upper()
        if reveal:
            w = str(escape(answers_by_label.get(lab, "")))
            return f'<b class="ws-lab">({lab})</b> <u class="ws-fill">{w}</u>'
        return f'<b class="ws-lab">({lab})</b> <span class="ws-blank"></span>'

    return Markup(_WS_LBL_RE.sub(repl, esc))


_WS_UL_RE = re.compile(r"\{\{(\d+)\|([^}]*)\}\}")


def _sub_underlines(sentence: str, by_no: dict, reveal: bool) -> Markup:
    """유형6 문장의 {{n|표현}} 마커를 번호 밑줄로 치환(교사용은 오류 밑줄 강조)."""
    esc = str(escape(sentence or ""))

    def repl(m: "re.Match") -> str:
        no = int(m.group(1))
        txt = m.group(2)
        u = by_no.get(no)
        wrong = bool(reveal and u and u.get("wrong"))
        cls = "ul wrongword" if wrong else "ul"
        return f'<u class="{cls}">{txt}</u><sup class="uln">{no}</sup>'

    return Markup(_WS_UL_RE.sub(repl, esc))


def _underline_words(text: str, words) -> Markup:
    """지문(교사용) 안에서 정답 단어들을 밑줄로 표시."""
    if not text:
        return Markup("")
    ws = sorted({w.strip() for w in (words or []) if w and w.strip()},
                key=len, reverse=True)
    if not ws:
        return escape(text)
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in ws) + r")\b", re.IGNORECASE)
    out: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        out.append(str(escape(text[last:m.start()])))
        out.append('<u class="ws-key">' + str(escape(m.group(0))) + "</u>")
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


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


# ---- 출제 포인트(4번) 자동 분량 조절용 헬퍼 -------------------------------
_EXAM_REF_FLOOR = 3   # 지칭추론은 최소 이만큼은 남긴다
_EXAM_IMP_FLOOR = 1   # 함축의미 블록은 최소 이만큼은 남긴다


def _ref_line_count(report) -> int:
    for e in report.exam.items:
        if "지칭" in e.question_type:
            return len([ln for ln in e.content.split("\n") if ln.strip()])
    return 0


def _imp_block_count(report) -> int:
    for e in report.exam.items:
        if "함축" in e.question_type:
            return len([b for b in re.split(r"\n\s*\n", e.content.strip()) if b.strip()])
    return 0


def _trim_exam_report(report, ref_keep=None, imp_keep=None):
    """지칭추론 목록은 앞에서 ref_keep 줄, 함축의미는 앞에서 imp_keep 블록만 남긴 사본."""
    items = []
    for e in report.exam.items:
        if ref_keep is not None and "지칭" in e.question_type:
            lines = [ln for ln in e.content.split("\n") if ln.strip()][:ref_keep]
            items.append(e.model_copy(update={"content": "\n".join(lines)}))
        elif imp_keep is not None and "함축" in e.question_type:
            blocks = [b for b in re.split(r"\n\s*\n", e.content.strip()) if b.strip()][:imp_keep]
            items.append(e.model_copy(update={"content": "\n\n".join(blocks)}))
        else:
            items.append(e)
    return report.model_copy(update={"exam": report.exam.model_copy(update={"items": items})})


def _fit_report(report, footer_note, css, min_vocab: int, brand: str = "은아 T"):
    """한 지문이 2페이지에 들어오도록, 넘칠 때만 단계적으로 분량을 줄인다.

    순서(내용 손실이 적은 것부터):
      1) 어휘 개수를 full → min_vocab 까지 축소
      2) (어휘 최소 상태) 출제포인트 '지칭추론' 목록을 뒤에서부터 축소
      3) (지칭추론 최소 상태) 출제포인트 '함축의미' 블록을 뒤에서부터 축소
    """
    from weasyprint import HTML

    def pages(rep):
        html = render_html([rep], footer_note, brand)
        return len(HTML(string=html, base_url=str(TEMPLATE_DIR)).render(
            stylesheets=[_font_css(), css], font_config=_font_config()).pages)

    if pages(report) <= 2:
        return report

    # 1) 어휘 줄이기
    last = report
    for cap in range(len(report.vocab.items) - 1, min_vocab - 1, -1):
        last = _cap_report(report, cap)
        if pages(last) <= 2:
            return last

    # 2) 어휘 최소 상태에서 지칭추론 목록 줄이기
    base = _cap_report(report, min_vocab)
    for ref_keep in range(_ref_line_count(base) - 1, _EXAM_REF_FLOOR - 1, -1):
        last = _trim_exam_report(base, ref_keep=ref_keep)
        if pages(last) <= 2:
            return last

    # 3) 지칭추론 최소 상태에서 함축의미 블록 줄이기
    base2 = _trim_exam_report(base, ref_keep=_EXAM_REF_FLOOR)
    for imp_keep in range(_imp_block_count(base2) - 1, _EXAM_IMP_FLOOR - 1, -1):
        last = _trim_exam_report(base2, ref_keep=_EXAM_REF_FLOOR, imp_keep=imp_keep)
        if pages(last) <= 2:
            return last

    # 여기까지 못 맞췄다면 원인은 대개 '직독직해 자체가 길어서'이므로,
    # 어휘·출제를 괜히 깎지 말고 원본을 그대로 둔다.
    return report


def render_pdf(reports, out_path: str | Path, footer_note: str = "",
               fit_pages: bool = True, min_vocab: int = 8,
               brand: str = "은아 T") -> Path:
    from weasyprint import HTML  # 지연 임포트 (무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    css = _stylesheet()
    rlist = _as_list(reports)

    def build(rs):
        html = render_html(rs, footer_note, brand)
        return HTML(string=html, base_url=str(TEMPLATE_DIR)).render(
            stylesheets=[_font_css(), css], font_config=_font_config())

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
def _collect_words_one(report) -> list[dict]:
    """한 지문(report)의 직독직해 chunk words 를 순서대로 모으고 중복 제거."""
    seen: dict[str, dict] = {}
    order: list[str] = []
    for s in report.literal.sentences:
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


def collect_words(reports) -> list[dict]:
    """여러 지문의 어휘를 모두 합쳐 중복 제거(전체 합본용). 하위호환 유지."""
    seen: dict[str, dict] = {}
    order: list[str] = []
    for r in _as_list(reports):
        for item in _collect_words_one(r):
            key = item["word"].lower()
            if key not in seen:
                seen[key] = {"word": item["word"], "meaning": item["meaning"]}
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
    """PDF 1개 안에서 지문별로 페이지를 나눠 어휘 리스트를 만든다."""
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    reps = _as_list(reports)
    passages = []
    for i, rep in enumerate(reps, 1):
        words = _collect_words_one(rep)
        passages.append({"no": i, "total": len(reps), "title": rep.title,
                         "words": words, "rows": _pair_rows(words)})
    tmpl = _env.get_template("wordlist.html.j2")
    html = tmpl.render(title=title, passages=passages, footer_note=footer_note)
    css = _stylesheet()
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(
        str(out_path), stylesheets=[_font_css(), css], font_config=_font_config())
    return out_path


def render_quiz_pdf(reports, out_path: str | Path,
                    title: str = "영단어 시험지", footer_note: str = "",
                    seed: int | None = None) -> Path:
    """PDF 1개 안에서 지문별로 페이지를 나눠 영단어 시험지를 만든다(지문마다 정답 포함)."""
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    reps = _as_list(reports)
    rng = random.Random(seed)
    passages = []
    for i, rep in enumerate(reps, 1):
        words = _collect_words_one(rep)
        shuffled = words[:]
        rng.shuffle(shuffled)
        for j, w in enumerate(shuffled):   # 섞은 뒤 번호 재부여
            w["no"] = j + 1
        passages.append({"no": i, "total": len(reps), "title": rep.title,
                         "words": shuffled, "rows": _pair_rows(shuffled)})
    tmpl = _env.get_template("quiz.html.j2")
    html = tmpl.render(title=title, passages=passages, footer_note=footer_note)
    css = _stylesheet()
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(
        str(out_path), stylesheets=[_font_css(), css], font_config=_font_config())
    return out_path


# ---------------------------------------------------------------------------
# 내신 서술형 대비 교재 (6개 유형 · 4파트: 학생용/교사용/빠른정답/정답및해설)
# ---------------------------------------------------------------------------
def _hint(answer: str) -> str:
    """정답의 첫 글자만 노출하는 힌트(학생용 답란)."""
    a = (answer or "").strip()
    return a[0] if a else ""


def _ws_context(worksheets, start_no: int = 1, title: str = "",
                passage_start_no: int = 1) -> list[dict]:
    """Worksheet 목록 -> 템플릿용 컨텍스트(일련번호·힌트·빈칸 치환 완료).

    일련번호(qno)는 '표시 유형 순서(type-major)'로 매긴다:
      복수 지문이면 각 유형 안에서 지문1→지문2… 순으로 이어진다.
    start_no: 첫 문항 번호(사용자 지정 시작번호). 이후 자동 증가.
    title: 파일명(교재 제목). 지문 배지를 '파일명-지문번호'로 표시하는 데 쓴다.
    passage_start_no: 첫 지문 번호(사용자 지정). 지문이 여러 개면 여기서부터 1씩 증가.
    """
    reps = _as_list(worksheets)

    base = (title or "").strip()
    passages: list[dict] = []
    for i, ws in enumerate(reps, int(passage_start_no)):
        src = f"{base}-{i}" if base else f"지문 {i}"

        # 요약문 완성 ((A)(B) 빈칸)
        sum_items = []
        for it in (ws.summary.items if ws.summary else []):
            amap = {b.label.upper(): b.answer for b in it.blanks}
            sum_items.append({
                "src": src,
                "student": _sub_labeled(it.sentence, amap, False),
                "teacher": _sub_labeled(it.sentence, amap, True),
                "blanks": [{"label": b.label.upper(), "answer": b.answer,
                            "meaning": b.meaning, "hint": _hint(b.answer)}
                           for b in it.blanks],
            })

        # 문장 변형(유의어·구조 변환 후 빈칸 완성 · 보기 제공)
        para_items = []
        for q in (ws.paraphrase.questions if ws.paraphrase else []):
            amap = {b.label.upper(): b.answer for b in q.blanks}
            answers = [b.answer for b in q.blanks]
            bank = sorted(answers + list(q.distractors), key=str.lower)
            para_items.append({
                "src": src, "original": q.original, "choices": bank,
                "student": _sub_labeled(q.sentence, amap, False),
                "teacher": _sub_labeled(q.sentence, amap, True),
                "blanks": [{"label": b.label.upper(), "answer": b.answer,
                            "meaning": b.meaning, "hint": _hint(b.answer)}
                           for b in q.blanks],
                "explanation": q.explanation,
            })

        # 요지/제목 배열 영작
        def arrange(items):
            return [{
                "src": src, "korean": it.korean,
                "given_words": list(it.given_words), "word_count": it.word_count,
                "answer": it.answer, "explanation": it.explanation,
            } for it in items]
        idea_items = arrange(ws.arrange.ideas if ws.arrange else [])
        title_items = arrange(ws.arrange.titles if ws.arrange else [])

        # 조건 영작
        comp_items = [{
            "src": src, "korean": it.korean,
            "conditions": list(it.conditions), "given_words": list(it.given_words),
            "word_count": it.word_count, "answer": it.answer,
            "explanation": it.explanation,
        } for it in (ws.compose.items if ws.compose else [])]

        # 사용되지 않는 낱말 고르기
        cloze_sets = []
        for s in (ws.choice.sets if ws.choice else []):
            amap = {se.label.upper(): se.answer for se in s.sentences}
            lc = [c.lower() for c in s.choices]
            unused_idx = sorted(lc.index(u.lower()) + 1 for u in s.unused if u.lower() in lc)
            cloze_sets.append({
                "src": src, "choices": list(s.choices),
                "unused": list(s.unused), "unused_index": unused_idx,
                "explanation": s.explanation,
                "sentences": [{
                    "label": se.label.upper(), "answer": se.answer,
                    "student": _sub_labeled(se.text, amap, False),
                    "teacher": _sub_labeled(se.text, amap, True),
                } for se in s.sentences],
            })

        # 어법 오류 수정(밑줄 중 일부 오류)
        err_items = []
        for it in (ws.error.items if ws.error else []):
            by_no = {u.no: {"wrong": u.wrong} for u in it.underlines}
            wrong = [{"no": u.no, "text": u.text, "correction": u.correction,
                      "point": u.point} for u in it.underlines if u.wrong]
            err_items.append({
                "src": src,
                "student": _sub_underlines(it.sentence, by_no, False),
                "teacher": _sub_underlines(it.sentence, by_no, True),
                "wrong": sorted(wrong, key=lambda x: x["no"]),
                "explanation": it.explanation,
            })

        # 지문 기반 영어 문답
        qa_items = [{
            "src": src, "question": q.question, "answer": q.answer,
            "evidence": q.evidence, "answer_ko": q.answer_ko,
        } for q in (ws.qa.items if ws.qa else [])]

        passages.append({
            "no": i, "total": len(reps), "title": ws.title,
            "passage": ws.passage,
            "summary": sum_items,
            "paraphrase": para_items,
            "ideas": idea_items, "titles": title_items,
            "compose": comp_items,
            "cloze": cloze_sets,
            "error": err_items,
            "qa": qa_items,
        })

    # 일련번호: 표시 유형 순서(type-major)로 매긴다.
    #   유형5(배열영작)은 ideas + titles 를 한 유형으로 이어서 센다.
    n = int(start_no) - 1
    for key in WS_TYPE_ORDER:
        for pg in passages:
            seq = (pg["ideas"] + pg["titles"]) if key == "arrange" else pg[key]
            for item in seq:
                n += 1
                item["qno"] = n
    return passages


def render_worksheet_pdf(worksheets, out_path: str | Path,
                         title: str = "내신 서술형 대비 교재",
                         footer_note: str = "", brand: str = "은아 T",
                         start_no: int = 1, passage_start_no: int = 1) -> Path:
    """여러 지문의 Worksheet 를 한 PDF 로 만든다.

    구성(한 PDF): ① 학생용 → ② 교사용(정답 표시) → ③ 빠른 정답 → ④ 정답 및 해설.
    일련번호는 PDF 전체에 걸쳐 이어 붙고, 출처는 '지문 N' 배지로 표시한다.
    각 유형은 새 페이지에서 시작한다.
    start_no: 첫 문항 번호(사용자 지정). 지정하면 그 번호부터 자동 증가.
    """
    from weasyprint import HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    passages = _ws_context(worksheets, start_no=start_no, title=title,
                           passage_start_no=passage_start_no)
    # 유형별로 내용이 하나라도 있는지(부분 성공 시 빈 유형 블록은 건너뜀)
    has = {
        "cloze": any(p["cloze"] for p in passages),
        "summary": any(p["summary"] for p in passages),
        "error": any(p["error"] for p in passages),
        "compose": any(p["compose"] for p in passages),
        "arrange": any(p["ideas"] or p["titles"] for p in passages),
        "paraphrase": any(p["paraphrase"] for p in passages),
        "qa": any(p["qa"] for p in passages),
    }
    tmpl = _env.get_template("worksheet.html.j2")
    html = tmpl.render(title=title, passages=passages, has=has,
                       footer_note=footer_note, brand=brand)
    css = _stylesheet()
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(
        str(out_path), stylesheets=[_font_css(), css], font_config=_font_config())
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
