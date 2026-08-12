"""LecturePassage(필생보 스타일) -> HTML -> PDF.

- 학생용(teacher=False): ① 지문 · ② 해석 전 예측(빈칸) · ③ 한 문장씩 직접 풀기
- 강사용(teacher=True): 위 ①②③ + ④ 답지(끊어읽기·캐치) + ⑤ 해석 전 예측·정답
"""
from __future__ import annotations

import random
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .lecture_schemas import STANCES, STRUCTURES, LecturePassage

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

_CIRCLED = "①②③④⑤"


def _aggregate_vocab(sentences) -> list[dict]:
    """문장별 어휘를 지문 전체 어휘 리스트로 합침(단어 기준 중복 제거, 등장 순서 유지).

    각 어휘 앞에 '처음 나온 문장 번호(sid)'를 달아 어느 문장 어휘인지 표시한다.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for s in sentences:
        for v in s.vocab:
            key = (v.word or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append({"sid": s.id, "word": v.word.strip(), "meaning": (v.meaning or "").strip()})
    return out


def _content_view(s) -> dict:
    """'이 문장 내용' 객관식 -> 보기 순서를 결정론적으로 섞고 정답 기호 계산."""
    opts, answer_sym = [], ""
    idx = list(range(len(s.content_options)))
    # 학생/강사 렌더가 같은 순서를 쓰도록 문장 고유값으로 시드 고정(정답이 항상 ①이 되지 않게)
    rng = random.Random(f"{s.id}|{s.english[:40]}")
    rng.shuffle(idx)
    for pos, oi in enumerate(idx):
        sym = _CIRCLED[pos] if pos < len(_CIRCLED) else f"({pos + 1})"
        correct = oi == s.content_answer_index
        opts.append({"sym": sym, "text": s.content_options[oi], "correct": correct})
        if correct:
            answer_sym = sym
    return {"options": opts, "answer_sym": answer_sym}


def _blank_width(ko: str) -> int:
    """빈칸 폭(px): 가려질 한국어 길이에 비례(과도하게 길지 않게 상한)."""
    return max(min(len(ko) * 9 + 12, 300), 48)


def _build_view(p: LecturePassage) -> dict:
    ov = p.overview

    chains = []
    for c in ov.restatement_chains:
        chains.append({
            "label": c.label,
            "expressions": c.expressions,
            "first": c.expressions[0],
            "blanks": max(len(c.expressions) - 1, 1),
            "variation": c.variation,
        })

    lines = []
    for s in p.analysis.sentences:
        chunks = [{"en": c.en, "ko": c.ko, "blank": c.blank,
                   "blank_w": _blank_width(c.ko)} for c in s.chunks]
        cv = _content_view(s)
        lines.append({
            "id": s.id,
            "english": s.english,
            "grammar": [{"tag": g.tag, "note": g.note} for g in s.grammar],
            "chunks": chunks,
            "content_options": cv["options"],
            "content_answer_sym": cv["answer_sym"],
            "content_explanation": s.content_explanation,
        })

    return {
        "item_no": (p.item_no or "").strip(),
        "theme_ko": p.theme_ko,
        "source": p.source,
        "sentences": p.sentences,
        "lines": lines,
        "vocab_list": _aggregate_vocab(p.analysis.sentences),
        "stances": STANCES,
        "structures": STRUCTURES,
        # ③ 글 예측 정답
        "topic": ov.topic,
        "stance": ov.stance,
        "stance_reason": ov.stance_reason,
        "structure": ov.structure,
        "structure_reason": ov.structure_reason,
        "chains": chains,
    }


def _as_list(passages) -> list[LecturePassage]:
    if isinstance(passages, LecturePassage):
        return [passages]
    return list(passages)


def render_lecture_html(passages, teacher: bool, footer_note: str = "") -> str:
    reps = _as_list(passages)
    views = []
    for i, p in enumerate(reps, 1):
        v = _build_view(p)
        v["no"] = i
        v["total"] = len(reps)
        views.append(v)
    tmpl = _env.get_template("lecture.html.j2")
    return tmpl.render(passages=views, teacher=teacher, footer_note=footer_note)


def _inline_styles(html: str) -> str:
    """폰트(@font-face base64)와 스타일을 문서 <head> 안에 직접 삽입한다.

    WeasyPrint(현재 버전)는 write_pdf(stylesheets=…) 로 넘긴 외부 CSS의 @font-face 를
    적용하지 않아 한글 폰트가 폴백된다. 문서 자체의 <style> 에 넣어야 나눔스퀘어라운드가
    확실히 임베드된다.
    """
    fonts = (TEMPLATE_DIR / "lecture_fonts.css").read_text(encoding="utf-8")
    css = (TEMPLATE_DIR / "lecture.css").read_text(encoding="utf-8")
    return html.replace("</head>", f"<style>{fonts}\n{css}</style></head>", 1)


def render_lecture_pdf(passages, out_path: str | Path, teacher: bool,
                       footer_note: str = "") -> Path:
    from weasyprint import HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = _inline_styles(render_lecture_html(passages, teacher=teacher,
                                             footer_note=footer_note))
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
