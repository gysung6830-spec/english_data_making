"""자료 팩 — 라이브러리에 쌓인 지문들을 가로질러 만드는 산출물.

기존 파이프라인이 '지문 1편 → 자료 3종'이라면, 여기는 '지문 N편 → 누적 자료'다.
수업을 굴려 보면 실제로 손이 가는 건 이쪽이다.

    누적 어휘 리스트 / 누적 어휘 시험지   4주치 어휘를 한 장으로
    문법 누적 시트                       반복되는 문법 뼈대 정리
    숙제지(학생용 빈칸 분석지)            그날 배운 지문 복습
    개인 맞춤 시험지                     그 학생이 틀린 단어만 모아서

모두 저장된 report.json 을 재사용하므로 **API 비용이 0원**이다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from . import render
from .config import Config
from .library import Library
from .schemas import Report, VocabItem, VocabSection


# ---------------------------------------------------------------------------
# 여러 지문의 어휘를 한 덩어리로 합치기
# ---------------------------------------------------------------------------
def merge_vocab(reports: Sequence[Report]) -> list[VocabItem]:
    """중복 단어를 없애고 번호를 1부터 다시 매긴 어휘 목록."""
    seen: dict[str, VocabItem] = {}
    for rep in reports:
        for v in rep.vocab.items:
            word = (v.word or "").strip()
            if not word:
                continue
            key = word.lower()
            if key in seen:
                # 먼저 등록된 쪽에 유의어·반의어가 비어 있으면 채워 넣는다
                cur = seen[key]
                if not cur.synonyms and v.synonyms:
                    cur.synonyms = v.synonyms
                if not cur.antonyms and v.antonyms:
                    cur.antonyms = v.antonyms
                continue
            seen[key] = v.model_copy(deep=True)
    items = list(seen.values())
    for i, it in enumerate(items, start=1):
        it.no = i
        it.sentence_no = 0      # 합본에서는 원 지문의 문장 번호가 의미 없다
    return items


def merged_report(reports: Sequence[Report], title: str,
                  items: Iterable[VocabItem] | None = None) -> Report:
    """어휘 자료용 '합본 가짜 리포트'.

    어휘 리스트·시험지 렌더러는 report.vocab 과 제목만 쓰기 때문에,
    나머지 섹션은 첫 지문 것을 그대로 얹어도 출력에 영향이 없다.
    """
    if not reports:
        raise ValueError("합칠 지문이 없습니다.")
    base = reports[0]
    vocab_items = list(items) if items is not None else merge_vocab(reports)
    return base.model_copy(update={
        "title": title,
        "item_no": "",
        "summary": base.summary.model_copy(update={"theme_en": "", "theme_ko": ""}),
        "vocab": VocabSection(items=vocab_items, english_summary="",
                              english_summary_ko=""),
    })


def _out(cfg: Config, name: str) -> Path:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    return cfg.output_dir / name


def _safe(name: str) -> str:
    return "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "pack"


# ---------------------------------------------------------------------------
# 누적 복습 팩
# ---------------------------------------------------------------------------
def build_review_pack(cfg: Config, ids: Sequence[str], *, name: str = "누적복습",
                      lib: Library | None = None, want_list: bool = True,
                      want_test: bool = True, want_grammar: bool = True,
                      seed: int | None = None) -> list[dict]:
    """지문 여러 편을 묶어 누적 어휘 리스트 · 시험지 · 문법 시트를 만든다."""
    lib = lib or Library()
    ids = list(ids)
    if not ids:
        raise ValueError("자료 ID 를 하나 이상 지정하세요.")
    reports = lib.load_reports(ids)
    stem = _safe(name)
    fn = cfg.design.footer_note
    recs: list[dict] = []

    if want_list:
        merged = merged_report(reports, f"{name} — 누적 어휘")
        p = _out(cfg, f"{stem}_누적어휘리스트.pdf")
        render.render_vocablist_pdf([merged], p, title=f"{name} — 누적 어휘",
                                    footer_note=fn)
        recs.append({"kind": "vocablist", "label": "📚 누적 어휘 리스트", "path": p})

    if want_test:
        merged = merged_report(reports, f"{name} — 누적 어휘 시험")
        p = _out(cfg, f"{stem}_누적어휘test.pdf")
        render.render_vocabtest_pdf([merged], p, title=f"{name} — 누적 어휘 시험",
                                    footer_note=fn, seed=seed)
        recs.append({"kind": "vocabtest", "label": "🧩 누적 어휘 시험지", "path": p})

    if want_grammar:
        p = _out(cfg, f"{stem}_문법시트.pdf")
        render.render_grammar_sheet_pdf(reports, p, title=f"{name} — 문법 누적 시트",
                                        footer_note=fn)
        recs.append({"kind": "grammar", "label": "📐 문법 누적 시트", "path": p})

    return recs


# ---------------------------------------------------------------------------
# 숙제지 (학생용 빈칸 분석지)
# ---------------------------------------------------------------------------
def build_homework(cfg: Config, ids: Sequence[str], *, name: str = "숙제",
                   lib: Library | None = None) -> list[dict]:
    """그날 배운 지문의 학생용(정답 빈칸) 분석지를 숙제지로 뽑는다."""
    lib = lib or Library()
    reports = lib.load_reports(list(ids))
    p = _out(cfg, f"{_safe(name)}_숙제지.pdf")
    render.render_analysis_pdf(reports, p, footer_note=cfg.design.footer_note,
                               min_vocab=cfg.vocab.min, brand=cfg.design.brand,
                               variants=[True], source_label=name)
    return [{"kind": "homework", "label": "📝 숙제지(학생용 빈칸)", "path": p}]


# ---------------------------------------------------------------------------
# 개인 맞춤 시험지 — 그 학생이 틀린 단어만
# ---------------------------------------------------------------------------
def build_personal_test(cfg: Config, student_code: str, words: Sequence[str], *,
                        lib: Library | None = None, name: str = "",
                        seed: int | None = None) -> list[dict]:
    """오답 단어 목록으로 그 학생 전용 어휘 시험지를 만든다.

    단어의 뜻·유의어·반의어는 라이브러리에 이미 있는 분석 결과에서 끌어온다.
    (라이브러리에 없는 단어는 조용히 건너뛴다 — 만들 근거가 없기 때문)
    """
    lib = lib or Library()
    wanted = {w.strip().lower() for w in words if w and w.strip()}
    if not wanted:
        raise ValueError("시험지를 만들 단어가 없습니다.")

    idx = lib.vocab_index()
    picked: dict[str, VocabItem] = {}
    source_ids: list[str] = []
    for word in sorted(wanted):
        for mid in idx.get(word, []):
            try:
                rep = lib.load_report(mid)
            except FileNotFoundError:
                continue
            hit = next((v for v in rep.vocab.items
                        if v.word.strip().lower() == word), None)
            if hit:
                picked[word] = hit.model_copy(deep=True)
                if mid not in source_ids:
                    source_ids.append(mid)
                break

    if not picked:
        raise ValueError(
            "라이브러리에서 해당 단어들을 찾지 못했습니다. "
            "(먼저 그 지문을 `library add` 로 등록하세요)")

    items = list(picked.values())
    for i, it in enumerate(items, start=1):
        it.no = i
        it.sentence_no = 0

    label = name or f"{student_code} 오답 복습"
    base = lib.load_reports(source_ids[:1])
    merged = merged_report(base, label, items=items)
    p = _out(cfg, f"{_safe(student_code)}_오답복습test.pdf")
    render.render_vocabtest_pdf([merged], p, title=label,
                                footer_note=cfg.design.footer_note, seed=seed)
    missing = sorted(wanted - set(picked))
    return [{"kind": "personal", "label": "🎯 개인 오답 복습 시험지", "path": p,
             "words": len(items), "missing": missing}]
