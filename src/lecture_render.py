"""LecturePassage -> HTML -> PDF (학생용 문제지 / 강사용 정답지).

명세 3장의 5개 섹션을 렌더링한다.
- 학생용: 문제만(먼저 스스로 시도 → 2지선다/라벨 채우기/줄잇기)
- 강사용: 정답·해설·근거 포함
학생용과 강사용이 '같은 보기 순서'를 공유하도록 뷰모델(선지 셔플 등)을 한 번만 만든 뒤
teacher 플래그만 바꿔 두 번 렌더한다.
"""
from __future__ import annotations

import random
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .lecture_schemas import ROLE_LABELS, LecturePassage

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)

_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
_KMARK = list("가나다라마바사아자차카타파하")


def _circ(i: int) -> str:
    return _CIRCLED[i] if i < len(_CIRCLED) else f"({i + 1})"


def _range_label(ids: list[int]) -> str:
    """[1,2,3] -> 'S1~S3', [4] -> 'S4', 비연속 -> 'S1, S3'."""
    ids = sorted(ids)
    if not ids:
        return ""
    if ids == list(range(ids[0], ids[-1] + 1)):
        return f"S{ids[0]}" if len(ids) == 1 else f"S{ids[0]}~S{ids[-1]}"
    return ", ".join(f"S{i}" for i in ids)


def _two_option_block(wrong: str, correct: str, rng: random.Random) -> dict:
    """2지선다(오답/정답)를 섞어 ①②로 배치하고 정답 기호를 표시."""
    opts = [{"text": wrong, "correct": False}, {"text": correct, "correct": True}]
    rng.shuffle(opts)
    for i, o in enumerate(opts):
        o["sym"] = _circ(i)
    correct_sym = next(o["sym"] for o in opts if o["correct"])
    return {"options": opts, "correct_sym": correct_sym}


def _build_view(passage: LecturePassage, rng: random.Random) -> dict:
    a = passage.analysis
    sent_text = {s.id: s.text for s in passage.sentences}

    traps = []
    for t in a.translation_traps:
        blk = _two_option_block(t.wrong_translation, t.correct_translation, rng)
        traps.append({
            "sentence_id": t.sentence_id,
            "sentence_text": sent_text.get(t.sentence_id, ""),
            "trap_type": t.trap_type,
            "reason": t.reason,
            "correct_translation": t.correct_translation,
            **blk,
        })

    blocks = []
    for b in a.role_blocks:
        ids = sorted(b.sentence_ids)
        text = " ".join(sent_text.get(i, "") for i in ids).strip()
        blocks.append({
            "range_label": _range_label(ids),
            "text": text,
            "correct_label": b.correct_label,
            "reason": b.reason,
        })

    tq = a.trap_question
    tq_view = {
        "type": tq.type,
        "sentence_id": tq.sentence_id,
        "sentence_text": sent_text.get(tq.sentence_id, ""),
        "question_text": tq.question_text,
        "explanation": tq.explanation,
        **_two_option_block(tq.option_wrong, tq.option_correct, rng),
    }

    # 패러프레이징 줄잇기: 좌(선지, 셔플) · 우(대응 문장 번호, 번호순)
    left = []
    for i, p in enumerate(a.paraphrase_items):
        left.append({"idx": i, "choice_text": p.choice_text,
                     "targets": sorted(p.matched_sentence_ids)})
    rng.shuffle(left)
    for i, item in enumerate(left):
        item["sym"] = _circ(i)
    right_ids = sorted({i for p in a.paraphrase_items for i in p.matched_sentence_ids})
    right = [{"kmark": _KMARK[k] if k < len(_KMARK) else str(k + 1),
              "sentence_id": sid, "text": sent_text.get(sid, "")}
             for k, sid in enumerate(right_ids)]
    kmark_of = {r["sentence_id"]: r["kmark"] for r in right}
    for item in left:
        item["answer_marks"] = [kmark_of[s] for s in item["targets"] if s in kmark_of]
    paraphrase = {"left": left, "right": right}

    return {
        "title": passage.title,
        "source": passage.source,
        "item_no": (passage.item_no or "").strip(),
        "sentences": passage.sentences,
        "vocab_hints": [{"word": v.word, "meaning": v.meaning} for v in a.vocab_hints],
        "traps": traps,
        "blocks": blocks,
        "role_labels": ROLE_LABELS,
        "trap_question": tq_view,
        "paraphrase": paraphrase,
    }


def _as_list(passages) -> list[LecturePassage]:
    if isinstance(passages, LecturePassage):
        return [passages]
    return list(passages)


def render_lecture_html(passages, teacher: bool, footer_note: str = "",
                        seed: int | None = None) -> str:
    reps = _as_list(passages)
    views = []
    for i, p in enumerate(reps, 1):
        rng = random.Random(seed if seed is not None else hash(p.title) & 0xFFFF)
        v = _build_view(p, rng)
        v["no"] = i
        v["total"] = len(reps)
        views.append(v)
    tmpl = _env.get_template("lecture.html.j2")
    return tmpl.render(passages=views, teacher=teacher, footer_note=footer_note)


def render_lecture_pdf(passages, out_path: str | Path, teacher: bool,
                       footer_note: str = "", seed: int | None = 12345) -> Path:
    from weasyprint import CSS, HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_lecture_html(passages, teacher=teacher, footer_note=footer_note, seed=seed)
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
        recs.append({"kind": "lecture_student", "label": "🎓 강의교재(학생 훈련용)", "path": p})
    if want_teacher:
        p = out_dir / f"{stem}_강의교재_강사용.pdf"
        render_lecture_pdf(passages, p, teacher=True, footer_note=footer_note)
        recs.append({"kind": "lecture_teacher", "label": "🗝️ 강의교재(강사용·정답)", "path": p})
    return recs
