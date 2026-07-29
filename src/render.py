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
            stylesheets=[css], font_config=_font_config()).pages)

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
            stylesheets=[css], font_config=_font_config())

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
        str(out_path), stylesheets=[css], font_config=_font_config())
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
        str(out_path), stylesheets=[css], font_config=_font_config())
    return out_path


# ---------------------------------------------------------------------------
# 내신 서술형 대비 교재 (6개 유형 · 4파트: 학생용/교사용/빠른정답/정답및해설)
# ---------------------------------------------------------------------------
def _hint(answer: str) -> str:
    """정답의 첫 글자만 노출하는 힌트(학생용 답란)."""
    a = (answer or "").strip()
    return a[0] if a else ""


def _ws_context(worksheets) -> list[dict]:
    """Worksheet 목록 -> 템플릿용 컨텍스트(일련번호·힌트·빈칸 치환 완료)."""
    reps = _as_list(worksheets)
    counter = {"n": 0}

    def nxt() -> int:
        counter["n"] += 1
        return counter["n"]

    passages: list[dict] = []
    for i, ws in enumerate(reps, 1):
        src = f"지문 {i}"

        # 유형1: 요약문 완성 (지문 상단 노출 + (A)(B) 빈칸)
        sum_items = []
        all_answers = []
        for it in ws.summary.items:
            amap = {b.label.upper(): b.answer for b in it.blanks}
            all_answers += [b.answer for b in it.blanks]
            sum_items.append({
                "qno": nxt(), "src": src,
                "student": _sub_labeled(it.sentence, amap, False),
                "teacher": _sub_labeled(it.sentence, amap, True),
                "blanks": [{"label": b.label.upper(), "answer": b.answer,
                            "meaning": b.meaning, "hint": _hint(b.answer)}
                           for b in it.blanks],
            })

        # 유형2: 문장 변형
        para_items = [{
            "qno": nxt(), "src": src, "original": q.original,
            "options": list(q.options), "answer": q.answer,
            "explanation": q.explanation,
        } for q in ws.paraphrase.questions]

        # 유형3: 요지/제목 배열 영작
        def arrange(items):
            return [{
                "qno": nxt(), "src": src, "korean": it.korean,
                "given_words": list(it.given_words), "word_count": it.word_count,
                "answer": it.answer, "explanation": it.explanation,
            } for it in items]
        idea_items = arrange(ws.arrange.ideas)
        title_items = arrange(ws.arrange.titles)

        # 유형4: 조건 영작
        comp_items = [{
            "qno": nxt(), "src": src, "korean": it.korean,
            "conditions": list(it.conditions), "given_words": list(it.given_words),
            "word_count": it.word_count, "answer": it.answer,
            "explanation": it.explanation,
        } for it in ws.compose.items]

        # 유형5: 사용되지 않는 낱말 고르기
        cloze_sets = []
        for s in ws.choice.sets:
            amap = {se.label.upper(): se.answer for se in s.sentences}
            try:
                unused_idx = [c.lower() for c in s.choices].index((s.unused or "").lower()) + 1
            except ValueError:
                unused_idx = 0
            cloze_sets.append({
                "qno": nxt(), "src": src, "choices": list(s.choices),
                "unused": s.unused, "unused_index": unused_idx,
                "explanation": s.explanation,
                "sentences": [{
                    "label": se.label.upper(), "answer": se.answer,
                    "student": _sub_labeled(se.text, amap, False),
                    "teacher": _sub_labeled(se.text, amap, True),
                } for se in s.sentences],
            })

        # 유형6: 어법 오류 수정
        err_items = [{
            "qno": nxt(), "src": src, "text": it.text, "error": it.error,
            "correction": it.correction, "explanation": it.explanation,
        } for it in ws.error.items]

        passages.append({
            "no": i, "total": len(reps), "title": ws.title,
            "passage": ws.passage,
            "passage_teacher": _underline_words(ws.passage, all_answers),
            "summary": sum_items,
            "paraphrase": para_items,
            "ideas": idea_items, "titles": title_items,
            "compose": comp_items,
            "cloze": cloze_sets,
            "error": err_items,
        })
    return passages


# 유형별 '출제 원리' — 각 유형 시작 페이지에 상세 안내로 표시(정적 설명).
#   각 항목 = (소제목, 설명) 목록.
WS_PRINCIPLES = {
    1: [
        ("출제 의도", "지문 전체를 관통하는 핵심 정보를 한 문장으로 압축·재진술(paraphrase)한 "
                    "요약문을 제시하고, 내용 이해의 열쇠가 되는 단어를 빈칸으로 비워 둔다. "
                    "'내용 파악 + 어휘·어법·철자 정확도'를 동시에 측정한다."),
        ("문항 구성", "요약문은 원문 문장을 그대로 베끼지 않고 동의어·구문 변형으로 다시 쓴다. "
                    "한 문항에 빈칸 2개(A·B)를 두며, 정답은 반드시 지문 본문에 등장한 단어를 쓰되 "
                    "문맥에 맞게 어형(수·시제·품사)을 바꾸도록 설계한다."),
        ("함정·채점", "동의어를 써도 '원문에 실제로 있는 단어'가 아니면 오답 처리한다. "
                    "철자·어형 변화(예: nation→national, decide→decision)까지 정확해야 득점되므로 "
                    "부분 점수 기준을 미리 정해 둔다."),
        ("대비 포인트", "지문을 읽으며 주제문·핵심어를 표시하고, 요약문의 빈칸 앞뒤 품사·연어를 단서로 "
                    "정답 단어를 원문에서 되짚는 훈련을 반복한다."),
    ],
    2: [
        ("출제 의도", "지문의 한 문장을 여러 방식으로 변형(paraphrasing)한 뒤, 원문과 의미가 "
                    "'일치하는' 선지를 고르게 한다. 단어 표면이 아니라 문장 전체의 의미 관계를 "
                    "이해했는지 평가하며, 지문 변형이 잦은 학교 시험에 대비시킨다."),
        ("문항 구성", "정답 1개는 동의어 치환·태 변환·구문 재배열로 의미를 '보존'한다. "
                    "오답 4개는 반의어, 주객(주어-목적어) 전도, 부정/조건 왜곡, 과장·축소 등으로 "
                    "의미를 미세하게 비튼다. 선지 길이는 서로 비슷하게 맞춘다."),
        ("함정·채점", "가장 흔한 함정은 '핵심 단어가 그대로 보이는' 오답이다. 겹치는 단어에 현혹되지 "
                    "말고 인과·주체·정도의 방향이 원문과 같은지를 기준으로 판정한다."),
        ("대비 포인트", "동의어·반의어 세트를 정리하고, 능동↔수동·비교 구문의 의미 보존/왜곡 패턴을 "
                    "손으로 바꿔 써 보며 익힌다."),
    ],
    3: [
        ("출제 의도", "글의 요지와 제목을 영어로 직접 산출하게 하되, 정답 문장을 이루는 단어를 모두 "
                    "'보기'로 제공하고 어순만 배열하게 한다. 핵심 내용 파악과 어순·문장 구조 감각을 "
                    "함께 평가한다."),
        ("문항 구성", "요지는 완결된 문장, 제목은 명사구 형태로 낸다. 보기에는 관사·전치사 등 기능어까지 "
                    "포함하고, 학생이 어형을 바꿔야 하는 단어는 원형으로 준다. 제시된 단어 수를 함께 "
                    "명시해 답의 길이를 고정한다."),
        ("함정·채점", "보기 단어를 '모두, 한 번씩' 사용해야 하며 임의로 단어를 추가·생략하면 감점한다. "
                    "주어-동사 위치, 수식어구의 순서가 핵심 채점 포인트다."),
        ("대비 포인트", "요지=주제문 재진술, 제목=주제의 압축이라는 차이를 구분하고, 뼈대(주어+동사)를 "
                    "먼저 세운 뒤 수식어를 붙이는 순서로 배열하는 연습을 한다."),
    ],
    4: [
        ("출제 의도", "지문의 핵심 문장을 우리말로 제시하고, 그 문장에 실제로 쓰인 어법을 '조건'으로 "
                    "걸어 영작하게 한다. 단어 수와 어법 조건을 동시에 충족해야 하므로 정밀한 문장 "
                    "구성 능력을 평가한다."),
        ("문항 구성", "조건에는 관계사·분사구문·비교구문·가정법·도치 등 그 문장에서 실제로 쓰인 어법을 "
                    "제시한다. 반드시 써야 할 핵심 단어는 원형으로 주고, 어형 변화는 학생 몫으로 남긴다. "
                    "정답은 지문 원문 문장과 일치시키는 것을 원칙으로 한다."),
        ("함정·채점", "의미가 맞아도 지정된 어법(예: 관계대명사 who)을 쓰지 않으면 감점한다. "
                    "단어 수 초과·미달, 시제·수일치 오류도 감점 요소이므로 조건별 배점을 나눠 채점한다."),
        ("대비 포인트", "어법 조건을 '뼈대'로 삼아 먼저 구조를 잡고 단어를 채우는 훈련을 하고, "
                    "빈출 어법(관계사·분사·비교)의 정형화된 문형을 암기한다."),
    ],
    5: [
        ("출제 의도", "하나의 보기(5개)로 여러 문장의 빈칸을 채우게 한 뒤, 어디에도 들어갈 수 없어 "
                    "'사용되지 않는' 낱말 1개를 고르게 한다. 개별 단어 뜻을 넘어 문맥·연어·품사를 "
                    "종합 판단하는 어휘력을 평가한다."),
        ("문항 구성", "보기는 서로 헷갈릴 만한(같은 주제·품사 계열의) 고난도 단어로 구성한다. "
                    "각 문장은 보기 중 '딱 한 단어'만 자연스럽게 들어가도록 설계하고, 4개 문장에 4개가 "
                    "쓰이며 1개만 남게 만든다."),
        ("함정·채점", "남는 단어는 대개 뜻은 비슷하나 연어·품사·어법이 맞지 않는 단어다. 문장마다 "
                    "빈칸에 들어갈 단어를 확정한 뒤 소거법으로 남는 하나를 고르도록 유도한다."),
        ("대비 포인트", "단어를 뜻만 외우지 말고 자주 함께 쓰이는 연어(collocation)와 품사·문형까지 "
                    "묶어 익히며, 빈칸의 앞뒤 구조로 품사를 먼저 판단하는 습관을 들인다."),
    ],
    6: [
        ("출제 의도", "지문 문장에 어법상 틀린 부분을 한 곳만 심어 두고 찾아 고치게 한다. "
                    "내신 빈출 어법을 실제 문장 맥락에서 스스로 진단·수정하는 능력을 평가한다."),
        ("문항 구성", "오류는 수일치, 시제, 태(수동/능동), 관계사, 준동사(to부정사/동명사/분사), 병렬, "
                    "형용사↔부사 혼동 등 빈출 포인트에서 낸다. 한 문장에 명확한 오류를 '하나만' 둔다."),
        ("함정·채점", "정답은 원래 지문의 올바른 표현과 일치해야 하며, 틀린 부분을 '찾기'와 '바르게 "
                    "고치기'를 모두 요구한다. 어색하지만 어법상 맞는 표현을 오답으로 지목하지 않도록 "
                    "명확한 오류만 출제한다."),
        ("대비 포인트", "동사를 보면 주어와의 수·시제·태를, 명사구를 보면 관계사·준동사를 점검하는 "
                    "체크리스트를 만들어 문장을 스캔하는 훈련을 한다."),
    ],
}


def render_worksheet_pdf(worksheets, out_path: str | Path,
                         title: str = "내신 서술형 대비 교재",
                         footer_note: str = "", brand: str = "은아 T") -> Path:
    """여러 지문의 Worksheet 를 한 PDF 로 만든다.

    구성(한 PDF): ① 학생용 → ② 교사용(정답 표시) → ③ 빠른 정답 → ④ 정답 및 해설.
    일련번호는 PDF 전체에 걸쳐 이어 붙고, 출처는 '지문 N' 배지로 표시한다.
    각 유형은 새 페이지에서 시작하며, 유형 헤더에 '출제 원리'를 함께 안내한다.
    """
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    passages = _ws_context(worksheets)
    tmpl = _env.get_template("worksheet.html.j2")
    html = tmpl.render(title=title, passages=passages, principles=WS_PRINCIPLES,
                       footer_note=footer_note, brand=brand)
    css = _stylesheet()
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(
        str(out_path), stylesheets=[css], font_config=_font_config())
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
