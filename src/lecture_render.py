"""LecturePassage(필생보 스타일) -> HTML -> PDF.

- 학생용(teacher=False): ① 지문 · ② 해석 전 예측(빈칸) · ③ 한 문장씩 직접 풀기
- 강사용(teacher=True): 위 ①②③ + ④ 답지(끊어읽기·캐치) + ⑤ 해석 전 예측·정답
"""
from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from .lecture_schemas import STANCES, STRUCTURES, LecturePassage

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

# 어휘 리스트에서 제외할 '너무 쉬운(초등 수준)' 단어 — 숙어(여러 단어)는 걸러지지 않음
from .render import _is_easy_word as _too_easy


def _aggregate_vocab(sentences) -> list[dict]:
    """문장별 어휘를 지문 전체 어휘 리스트로 합침(단어 기준 중복 제거, 등장 순서 유지).

    - 각 어휘 앞에 '처음 나온 문장 번호(sid)'를 달아 어느 문장 어휘인지 표시한다.
    - 초등 수준의 너무 쉬운 '단일 단어'는 제외한다(중·고등 수준 + 숙어 위주).
    """
    seen: set[str] = set()
    out: list[dict] = []
    for s in sentences:
        for v in s.vocab:
            word = (v.word or "").strip()
            key = word.lower()
            if not key or key in seen:
                continue
            # 한 단어인데 너무 쉬우면 제외(숙어·구동사는 공백 포함이라 유지)
            if " " not in word and _too_easy(word):
                continue
            seen.add(key)
            out.append({"sid": s.id, "word": word, "meaning": (v.meaning or "").strip()})
    return out


_MARK = re.compile(r"\[\[(.+?)\]\]")


def _mark_en(text: str) -> Markup:
    """영어는 강조하지 않는다 — [[ ]] 표시만 떼고 원문 그대로.

    (어디가 빈칸인지 학생이 스스로 찾는 과정이 학습이므로 en 밑줄 없음)
    """
    return escape(_MARK.sub(lambda m: m.group(1), text or ""))


def _mark_tip(text: str) -> Markup:
    """오역 팁: 텍스트는 escape 하고 [[ ]] 부분만 <b>로 강조(en/ko 혼용 안전)."""
    esc = str(escape(text or ""))
    esc = _MARK.sub(lambda m: f"<b>{m.group(1)}</b>", esc)
    return Markup(esc)


def _mark_ko(text: str, teacher: bool) -> Markup:
    """[[...]] 부분을 학생용=빈칸 / 강사용=채워진 강조 로 표시(ko)."""
    out, last = [], 0
    for m in _MARK.finditer(text or ""):
        out.append(str(escape(text[last:m.start()])))
        inner = m.group(1)
        if teacher:
            out.append(f'<span class="ko-fill">{escape(inner)}</span>')
        else:
            w = max(min(len(inner) * 11 + 12, 200), 40)
            out.append(f'<span class="ko-blank" style="min-width:{w}px"></span>')
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


def _has_mark(text: str) -> bool:
    return bool(_MARK.search(text or ""))


def _highlight_passage(sentences, chains, first_expr_only: bool = False) -> Markup:
    """지문 텍스트에 각 재진술 사슬(소재)의 표현을 소재별 색 + '소재 번호'로 형광펜 표시.

    - 각 표현에 그 표현이 속한 '소재 번호'(1,2,…)를 위첨자로 붙인다
      (흑백 인쇄 시 형광펜 색이 구분 안 돼도 번호로 어느 소재인지 알 수 있게).
    - first_expr_only=True 면 '각 소재의 첫 표현'만 표시한다(학생용 예시 앵커).
    """
    text = str(escape(" ".join(s.text for s in sentences)))
    pairs = []  # (escaped_expr, color_class, chain_no)
    for ci, c in enumerate(chains):
        exprs = c.expressions[:1] if first_expr_only else c.expressions
        for expr in exprs:
            e = str(escape(expr)).strip()
            if e:
                pairs.append((e, f"hl{ci % 2}", ci + 1))
    tokens: dict[str, str] = {}
    # 긴 표현 먼저(짧은 표현이 긴 표현 안에서 잘리는 것 방지), 플레이스홀더로 치환
    for i, (e, color, cno) in enumerate(sorted(pairs, key=lambda p: -len(p[0]))):
        mm = re.search(re.escape(e), text, re.IGNORECASE)
        if not mm:
            continue
        tok = f"\x00{i}\x00"
        tokens[tok] = (f'<mark class="{color}"><sup class="hln">{cno}</sup>'
                       f'{text[mm.start():mm.end()]}</mark>')
        text = text[:mm.start()] + tok + text[mm.end():]
    for tok, html in tokens.items():
        text = text.replace(tok, html)
    return Markup(text)


def _match_sentence_no(src: str, sentences) -> int | None:
    """핵심 문법이 나온 원문 문장(source_sentence)이 지문 몇 번째 문장인지 찾음."""
    s = (src or "").strip().rstrip(".").lower()
    if not s:
        return None
    for sent in sentences:
        t = (sent.text or "").strip().rstrip(".").lower()
        if t and (s in t or t in s):
            return sent.id
    return None


def _build_view(p: LecturePassage, teacher: bool) -> dict:
    ov = p.overview

    chains = []
    for ci, c in enumerate(ov.restatement_chains):
        chains.append({
            "label": c.label,
            "variation": c.variation,
            "color": f"hl{ci % 2}",
        })
    passage_hl = _highlight_passage(p.sentences, ov.restatement_chains)
    # 학생용: 각 소재의 '첫 표현'만 예시로 형광펜 표시(나머지는 학생이 직접)
    passage_hl_student = _highlight_passage(p.sentences, ov.restatement_chains,
                                            first_expr_only=True)

    # ④ 글 내용 정리: 의미 블록 흐름(도입→전개→…)
    flow_blocks = []
    for b in ov.flow_blocks:
        flow_blocks.append({
            "stage": b.stage,
            "sentence_range": b.sentence_range,
            # ④ 글 내용 정리는 빈칸 없이 '전체 문장'을 보여준다([[ ]] 표시는 떼기만)
            "summary": _mark_en(b.summary),
            "easy_example": b.easy_example,
        })

    lines = []
    for s in p.analysis.sentences:
        chunks = []
        for c in s.chunks:
            chunks.append({
                "en": _mark_en(c.en),
                "ko": _mark_ko(c.ko, teacher),
            })
        lines.append({
            "id": s.id,
            "english": s.english,
            "grammar": [{"tag": g.tag, "note": g.note} for g in s.grammar],
            "chunks": chunks,
            "misreads": [{"statement": m.statement, "why": m.why} for m in s.misreads],
            "mistips": [_mark_tip(t) for t in getattr(s, "mistips", [])],
        })

    return {
        "item_no": (p.item_no or "").strip(),
        "theme_ko": p.theme_ko,
        "source": p.source,
        "key_grammar": {
            "point": ov.key_grammar.point,
            "source_sentence": ov.key_grammar.source_sentence,
            "source_no": _match_sentence_no(ov.key_grammar.source_sentence, p.sentences),
            "explanation": [{"chip": n.chip, "text": _mark_ko(n.text, teacher)}
                            for n in ov.key_grammar.explanation],
            "example": ov.key_grammar.example,
            "example_analysis": ov.key_grammar.example_analysis,
            "drills": [{"kind": d.kind, "question": d.question, "answer": d.answer,
                        "options": list(d.options), "words": list(d.words),
                        "from_passage": d.from_passage}
                       for d in ov.key_grammar.drills],
        },
        "sentences": p.sentences,
        "lines": lines,
        "vocab_list": _aggregate_vocab(p.analysis.sentences),
        "stances": STANCES,
        "structures": STRUCTURES,
        # ④ 글 정리
        "topic": ov.topic,
        "stance": ov.stance,
        "stance_reason": ov.stance_reason,
        "structure": ov.structure,
        "structure_reason": ov.structure_reason,
        "chains": chains,
        "passage_hl": passage_hl,
        "passage_hl_student": passage_hl_student,
        "flow_blocks": flow_blocks,
    }


def _as_list(passages) -> list[LecturePassage]:
    if isinstance(passages, LecturePassage):
        return [passages]
    return list(passages)


def render_lecture_html(passages, teacher: bool, footer_note: str = "") -> str:
    reps = _as_list(passages)
    views = []
    for i, p in enumerate(reps, 1):
        v = _build_view(p, teacher)
        v["no"] = i
        v["total"] = len(reps)
        views.append(v)
    tmpl = _env.get_template("lecture.html.j2")
    return tmpl.render(passages=views, teacher=teacher, footer_note=footer_note)


def _css_string(text: str) -> str:
    """CSS content 문자열용 이스케이프(따옴표·역슬래시·개행)."""
    return (text or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _inline_styles(html: str, footer_note: str = "") -> str:
    """폰트(@font-face base64)와 스타일을 문서 <head> 안에 직접 삽입한다.

    WeasyPrint(현재 버전)는 write_pdf(stylesheets=…) 로 넘긴 외부 CSS의 @font-face 를
    적용하지 않아 한글 폰트가 폴백된다. 문서 자체의 <style> 에 넣어야 나눔스퀘어라운드가
    확실히 임베드된다. 각주는 러닝 요소 대신 @bottom-center 문자열로 넣어(상단 잔상 방지).
    """
    fonts = (TEMPLATE_DIR / "lecture_fonts.css").read_text(encoding="utf-8")
    css = (TEMPLATE_DIR / "lecture.css").read_text(encoding="utf-8")
    # 하단 중앙: 저작권 문구 / 하단 우측: 페이지 번호(현재 / 전체)
    center = ""
    if footer_note:
        center = ('@bottom-center{ content:"%s"; font-size:8pt; color:#a7adb8; }'
                  % _css_string(footer_note))
    foot = ('@page{ %s @bottom-right{ content: counter(page) " / " counter(pages);'
            ' font-size:8pt; color:#a7adb8; } }' % center)
    return html.replace("</head>", f"<style>{fonts}\n{css}\n{foot}</style></head>", 1)


def render_lecture_pdf(passages, out_path: str | Path, teacher: bool,
                       footer_note: str = "") -> Path:
    from weasyprint import HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = _inline_styles(render_lecture_html(passages, teacher=teacher,
                                             footer_note=footer_note), footer_note)
    HTML(string=html, base_url=str(TEMPLATE_DIR) + "/").write_pdf(str(out_path))
    return out_path


def render_lecture_outputs(out_dir: str | Path, passages, stem: str,
                           footer_note: str = "", want_student: bool = True,
                           want_teacher: bool = True) -> list[dict]:
    """강의컨셉 교재 산출물(학생용/강사용)을 생성. pipeline.render_outputs 와 같은 rec 형식 반환."""
    out_dir = Path(out_dir)
    recs: list[dict] = []
    if want_student:
        p = out_dir / f"{stem}_강의교재_학생용.pdf"
        render_lecture_pdf(passages, p, teacher=False, footer_note=footer_note)
        recs.append({"kind": "lecture_student", "label": "🎓 강의교재(학생 문제지)", "path": p})
    if want_teacher:
        p = out_dir / f"{stem}_강의교재_강사용.pdf"
        render_lecture_pdf(passages, p, teacher=True, footer_note=footer_note)
        recs.append({"kind": "lecture_teacher", "label": "🗝️ 강의교재(강사용·답지 포함)", "path": p})
    return recs
