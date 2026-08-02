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


def _highlight_ko(text: str | None, keywords) -> Markup:
    """한국어 주제 문장 안에서 핵심 키워드(keywords)를 강조 표시.

    한국어는 \b(단어 경계)가 통하지 않으므로 '부분 문자열'로 매칭한다.
    긴 키워드를 먼저 매칭해 짧은 키워드에 잘리지 않도록 한다.
    """
    if not text:
        return Markup("")
    kws = sorted({k.strip() for k in (keywords or []) if k and k.strip()},
                 key=len, reverse=True)
    if not kws:
        return escape(text)
    pattern = re.compile("(" + "|".join(re.escape(k) for k in kws) + ")")
    out: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        out.append(str(escape(text[last:m.start()])))
        out.append('<b class="kw">' + str(escape(m.group(0))) + "</b>")
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


_env.filters["highlight_ko"] = _highlight_ko


def _blank_ko(text: str | None, keywords) -> Markup:
    """학생용: 주제 문장 속 핵심 키워드를 '빈칸'으로 바꿔 학생이 채우게 한다."""
    if not text:
        return Markup("")
    kws = sorted({k.strip() for k in (keywords or []) if k and k.strip()},
                 key=len, reverse=True)
    if not kws:
        return escape(text)
    pattern = re.compile("(" + "|".join(re.escape(k) for k in kws) + ")")
    out: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        out.append(str(escape(text[last:m.start()])))
        w = max(len(m.group(0)) * 12, 34)
        out.append(f'<span class="blank" style="min-width:{w}px"></span>')
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


_env.filters["blank_ko"] = _blank_ko


def _blank_words(text: str | None, words) -> Markup:
    """학생용: 영어 요약문 속 핵심 단어를 빈칸으로 바꿔 학생이 채우게 한다."""
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
        w = max(len(m.group(0)) * 8, 42)
        out.append(f'<span class="blank" style="min-width:{w}px"></span>')
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


_env.filters["blank_words"] = _blank_words


def _split_blocks(text: str | None) -> list[str]:
    """빈 줄로 구분된 텍스트를 블록 목록으로 나눈다(함축의미 표현별 묶음용)."""
    if not text:
        return []
    return [b for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]


_env.filters["split_blocks"] = _split_blocks


def _implicit_map(exam):
    """출제 포인트의 '함축의미' 블록을 {문장번호: [블록,...]} 로 정리(직독직해 표에 통합용)."""
    out: dict[int, list[str]] = {}
    if not exam:
        return out
    for e in exam.items:
        if "함축" in (e.question_type or ""):
            for block in re.split(r"\n\s*\n", (e.content or "").strip()):
                block = block.strip()
                if not block:
                    continue
                m = re.match(r"\s*(\d+)\s*문장", block)
                key = int(m.group(1)) if m else 0
                out.setdefault(key, []).append(block)
    return out


_env.filters["implicit_map"] = _implicit_map


def _ref_map(exam):
    """출제 포인트의 '지칭추론' 줄을 {문장번호: [줄,...]} 로 정리(직독직해 표에 통합용)."""
    out: dict[int, list[str]] = {}
    if not exam:
        return out
    for e in exam.items:
        if "지칭" in (e.question_type or ""):
            for line in (e.content or "").split("\n"):
                line = line.strip()
                if not line:
                    continue
                m = re.match(r"\s*(\d+)\s*문장", line)
                key = int(m.group(1)) if m else 0
                out.setdefault(key, []).append(line)
    return out


_env.filters["ref_map"] = _ref_map


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


def render_html(reports, footer_note: str = "", brand: str = "",
                with_source: bool = True, student: bool = False,
                source_label: str = "") -> str:
    """reports: 단일 Report 또는 여러 Report(list). 여러 지문이면 순서대로 출력.

    with_source=True 이면 앞부분에 '원문 + 전체 해석' 모음을 먼저 넣고, 그 뒤에 지문별 분석지.
    brand: 직독직해 'made by ~' 와 출제표 '~ tip' 에 넣을 이름. 빈 값이면 브랜드 문구 제거.
    source_label: 지문 번호 뱃지에 함께 표시할 '파일명(지문명)'.
    (하단 저작권 footer_note 는 brand 와 무관하게 항상 그대로 표시)
    """
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(reports=_as_list(reports), footer_note=footer_note,
                       brand=brand, with_source=with_source, student=student,
                       source_label=source_label)


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


def _fit_report(report, footer_note, css, min_vocab: int, brand: str = "",
                student: bool = False, source_label: str = ""):
    """한 지문이 2페이지에 들어오도록, 넘칠 때만 단계적으로 분량을 줄인다.

    순서(내용 손실이 적은 것부터):
      1) 어휘 개수를 full → min_vocab 까지 축소
      2) (어휘 최소 상태) 출제포인트 '지칭추론' 목록을 뒤에서부터 축소
      3) (지칭추론 최소 상태) 출제포인트 '함축의미' 블록을 뒤에서부터 축소
    """
    from weasyprint import HTML

    def pages(rep):
        # 분석지 부분만으로 판정(앞의 원문+해석 모음 제외)
        html = render_html([rep], footer_note, brand, with_source=False,
                           student=student, source_label=source_label)
        return len(HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=[css]).pages)

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


def _render_document(reports, footer_note, brand, student, fit_pages, min_vocab, css, HTML,
                     source_label=""):
    """분석지 한 버전(교사용 또는 학생용)을 렌더해 WeasyPrint Document 로 반환."""
    rlist = _as_list(reports)

    def build(rs, with_source):
        html = render_html(rs, footer_note, brand, with_source=with_source,
                           student=student, source_label=source_label)
        return HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=[css])

    # 분석지 부분만으로 페이지 판정(앞의 원문+해석 모음은 제외)
    if fit_pages:
        analysis = build(rlist, with_source=False)
        if len(analysis.pages) > 2 * len(rlist):
            rlist = [_fit_report(r, footer_note, css, min_vocab, brand, student, source_label)
                     for r in rlist]
    # 최종 출력은 원문+해석 모음 포함
    return build(rlist, with_source=True)


def render_pdf(reports, out_path: str | Path, footer_note: str = "",
               fit_pages: bool = True, min_vocab: int = 8,
               brand: str = "", student: bool = False, source_label: str = "") -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트 (무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    _render_document(reports, footer_note, brand, student, fit_pages,
                     min_vocab, css, HTML, source_label).write_pdf(str(out_path))
    return out_path


def render_analysis_pdf(reports, out_path: str | Path, footer_note: str = "",
                        min_vocab: int = 8, brand: str = "",
                        variants=(False,), source_label: str = "") -> Path:
    """분석지를 여러 버전 순서대로 '한 PDF'에 이어 붙인다.

    variants: 학생플래그 목록. 예) [False]=교사용만, [True]=학생용만,
              [False, True]=교사 전체 지문 → 학생 전체 지문 순서로 합본.
    """
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    docs = [_render_document(reports, footer_note, brand, s, True, min_vocab, css, HTML,
                             source_label)
            for s in variants]
    if len(docs) == 1:
        docs[0].write_pdf(str(out_path))
    else:
        all_pages = [pg for d in docs for pg in d.pages]
        docs[0].copy(all_pages).write_pdf(str(out_path))
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
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
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
    css = CSS(filename=str(TEMPLATE_DIR / "styles.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
    return out_path


# ---------------------------------------------------------------------------
# 단어 학습지 (같은 단어를 여러 방법으로 익히는 암기용 학습지)
#   유형① 소리 내어 읽으며 영어+뜻 두 번 쓰기
#   유형② 줄 잇기(영어-뜻 연결)
#   유형③ 뜻만 보고 영어 쓰기(첫 글자 힌트)
#   유형④ 영어 보고 뜻 쓰기(양방향 암기)
#   유형⑤ 철자 뒤섞기(Anagram) - 스펠링
# ---------------------------------------------------------------------------
def _hint_segments(word: str) -> list[dict]:
    """첫 글자 힌트용 조각 목록.

    첫 단어는 '첫 글자 노출 + 나머지 글자 수만큼 빈칸', 뒤 단어(구phrase)는 전부 빈칸.
    예) "mosquito" -> [{lead:'m', blanks:7}]
        "give up"  -> [{lead:'g', blanks:3}, {lead:'', blanks:2}]
    """
    segs: list[dict] = []
    for part in word.strip().split():
        if not part:
            continue
        if not segs:
            segs.append({"lead": part[0], "blanks": max(len(part) - 1, 0)})
        else:
            segs.append({"lead": "", "blanks": len(part)})
    if not segs:
        segs.append({"lead": "", "blanks": 0})
    return segs


def _scramble(word: str, rng: random.Random) -> str:
    """단어의 철자를 뒤섞는다(공백 단위로 토큰별). 원본과 같아지지 않게 시도."""
    def sc(tok: str) -> str:
        if len(tok) < 2:
            return tok
        for _ in range(8):
            chars = list(tok)
            rng.shuffle(chars)
            s = "".join(chars)
            if s.lower() != tok.lower():
                return s
        return "".join(sorted(tok))
    return " ".join(sc(t) for t in word.split())


def _worksheet_sets_one(report, size: int, rng: random.Random) -> list[dict]:
    """한 지문의 핵심 어휘(④)를 size개씩 묶어 학습지 '세트' 목록으로 만든다."""
    items = [{"word": (v.word or "").strip(), "meaning": (v.meaning or "").strip()}
             for v in report.vocab.items if (v.word or "").strip()]
    sets: list[dict] = []
    for start in range(0, len(items), size):
        group = items[start:start + size]
        words = [{"n": i + 1, "word": g["word"], "meaning": g["meaning"]}
                 for i, g in enumerate(group)]
        # ② 줄잇기: 오른쪽 '뜻'을 섞어 배치(선을 그어 연결하게). 2개 이상이면 원래 순서와
        # 완전히 같지 않도록 몇 번 시도한다.
        shuffled = words[:]
        for _ in range(5):
            rng.shuffle(shuffled)
            if len(words) < 2 or any(a["n"] != b["n"] for a, b in zip(words, shuffled)):
                break
        match = [{"left": w, "right": r} for w, r in zip(words, shuffled)]
        # ③ 뜻→영어 (첫 글자 힌트)
        type3 = [{"n": w["n"], "meaning": w["meaning"],
                  "segments": _hint_segments(w["word"])} for w in words]
        # ⑤ 철자 뒤섞기(Anagram): 흩어진 철자를 보고 단어를 완성
        anagram = [{"n": w["n"], "meaning": w["meaning"],
                    "scrambled": _scramble(w["word"], rng),
                    "blanks": len(w["word"].replace(" ", ""))} for w in words]
        sets.append({"words": words, "match": match, "type3": type3,
                     "anagram": anagram})
    return sets


def render_worksheet_pdf(reports, out_path: str | Path,
                         title: str = "단어 학습지", footer_note: str = "",
                         set_size: int = 10, seed: int | None = None) -> Path:
    """핵심 어휘를 10개씩 묶어, 세트마다 3가지 유형으로 익히는 학습지를 만든다.

    세트(10개)마다 한 페이지를 차지한다.
    """
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    reps = _as_list(reports)
    rng = random.Random(seed)
    sheets: list[dict] = []
    for i, rep in enumerate(reps, 1):
        sets = _worksheet_sets_one(rep, set_size, rng)
        for j, s in enumerate(sets, 1):
            sheets.append({"passage_no": i, "passage_total": len(reps),
                           "title": rep.title, "set_no": j, "set_total": len(sets), **s})
    tmpl = _env.get_template("worksheet.html.j2")
    html = tmpl.render(title=title, sheets=sheets, footer_note=footer_note)
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
