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
    """문장별 어휘를 지문 전체 어휘 힌트로 합침(단어 기준 중복 제거, 등장 순서 유지)."""
    seen: set[str] = set()
    out: list[dict] = []
    for s in sentences:
        for v in s.vocab:
            key = (v.word or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append({"word": v.word.strip(), "meaning": (v.meaning or "").strip()})
    return out


def _problem_view(pr) -> dict:
    """오역 포인트 문제 1개 -> 렌더 뷰(객관식은 보기 순서를 결정론적으로 섞고 정답 기호 계산)."""
    view = {
        "no": pr.no, "sentence_id": pr.sentence_id, "focus": pr.focus,
        "kind": pr.kind, "question": pr.question,
        "explanation": pr.explanation, "answer_text": pr.answer_text,
        "options": [], "answer_sym": "",
    }
    if pr.kind == "객관식" and pr.options:
        idx = list(range(len(pr.options)))
        # 학생/강사 렌더가 같은 순서를 쓰도록 문제 고유값으로 시드 고정(정답이 항상 ①이 되지 않게)
        rng = random.Random(f"{pr.no}|{pr.sentence_id}|{pr.focus}")
        rng.shuffle(idx)
        for pos, oi in enumerate(idx):
            sym = _CIRCLED[pos] if pos < len(_CIRCLED) else f"({pos + 1})"
            view["options"].append({"sym": sym, "text": pr.options[oi],
                                    "correct": oi == pr.answer_index})
            if oi == pr.answer_index:
                view["answer_sym"] = sym
    return view


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

    items = []
    for s in p.analysis.sentences:
        items.append({
            "id": s.id,
            "english": s.english,
            "syntax_tag": s.syntax_tag,
            "en_chunked": " / ".join(c.en for c in s.chunks),
            "ko_chunked": " / ".join(c.ko for c in s.chunks),
            "catch": s.catch,
            "easy_example": s.easy_example,
        })

    problems = [_problem_view(pr) for pr in p.analysis.problems]

    return {
        "item_no": (p.item_no or "").strip(),
        "theme_ko": p.theme_ko,
        "source": p.source,
        "sentences": p.sentences,
        "lines": items,
        "vocab_hints": _aggregate_vocab(p.analysis.sentences),
        "problems": problems,
        "stances": STANCES,
        "structures": STRUCTURES,
        # ⑤ 정답
        "topic": ov.topic,
        "stance": ov.stance,
        "stance_reason": ov.stance_reason,
        "structure": ov.structure,
        "structure_reason": ov.structure_reason,
        "chains": chains,
        "analogy_name": ov.analogy_name,
        "analogy_desc": ov.analogy_desc,
        "gist": ov.gist,
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


def render_lecture_pdf(passages, out_path: str | Path, teacher: bool,
                       footer_note: str = "") -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_lecture_html(passages, teacher=teacher, footer_note=footer_note)
    css = CSS(filename=str(TEMPLATE_DIR / "lecture.css"))
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=[css])
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
