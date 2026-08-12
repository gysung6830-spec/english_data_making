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

    # ④ 글 정리: 문장별 역할 흐름(1문장 역할 → 2문장 역할 → …)
    flow = [{"id": s.id, "role": s.role} for s in p.analysis.sentences]

    lines = []
    for s in p.analysis.sentences:
        chunks = [{"en": c.en, "ko": c.ko, "blank": c.blank,
                   "blank_w": _blank_width(c.ko)} for c in s.chunks]
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
        "sentences": p.sentences,
        "lines": lines,
        "vocab_list": _aggregate_vocab(p.analysis.sentences),
        "stances": STANCES,
        "structures": STRUCTURES,
        # ④ 글 정리 정답
        "topic": ov.topic,
        "stance": ov.stance,
        "stance_reason": ov.stance_reason,
        "structure": ov.structure,
        "structure_reason": ov.structure_reason,
        "chains": chains,
        "flow": flow,
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
