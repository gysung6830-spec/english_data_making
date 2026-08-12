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
    """[[...]] 부분을 '오역 주의' 강조로 표시(en)."""
    out, last = [], 0
    for m in _MARK.finditer(text or ""):
        out.append(str(escape(text[last:m.start()])))
        out.append(f'<span class="en-trap">{escape(m.group(1))}</span>')
        last = m.end()
    out.append(str(escape(text[last:])))
    return Markup("".join(out))


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


def _highlight_passage(sentences, chains) -> Markup:
    """지문 텍스트에 각 재진술 사슬의 표현을 사슬별 형광펜 색으로 표시."""
    text = str(escape(" ".join(s.text for s in sentences)))
    pairs = []  # (escaped_expr, color_class)
    for ci, c in enumerate(chains):
        for expr in c.expressions:
            e = str(escape(expr)).strip()
            if e:
                pairs.append((e, f"hl{ci % 2}"))
    tokens: dict[str, str] = {}
    # 긴 표현 먼저(짧은 표현이 긴 표현 안에서 잘리는 것 방지), 플레이스홀더로 치환
    for i, (e, color) in enumerate(sorted(pairs, key=lambda p: -len(p[0]))):
        mm = re.search(re.escape(e), text, re.IGNORECASE)
        if not mm:
            continue
        tok = f"\x00{i}\x00"
        tokens[tok] = f'<mark class="{color}">{text[mm.start():mm.end()]}</mark>'
        text = text[:mm.start()] + tok + text[mm.end():]
    for tok, html in tokens.items():
        text = text.replace(tok, html)
    return Markup(text)


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

    # ④ 글 내용 정리: 의미 블록 흐름(도입→전개→…)
    flow_blocks = []
    for b in ov.flow_blocks:
        flow_blocks.append({
            "stage": b.stage,
            "sentence_range": b.sentence_range,
            "summary": _mark_ko(b.summary, teacher),
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
        })

    return {
        "item_no": (p.item_no or "").strip(),
        "theme_ko": p.theme_ko,
        "source": p.source,
        "key_grammar": {"point": ov.key_grammar.point,
                        "explanation": ov.key_grammar.explanation,
                        "example": ov.key_grammar.example},
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
    foot = ""
    if footer_note:
        foot = ('@page{ @bottom-center{ content:"%s"; font-size:8pt; color:#a7adb8; } }'
                % _css_string(footer_note))
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
