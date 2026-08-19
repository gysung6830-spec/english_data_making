"""조판기 (명세서 §6, §4).

- TYPE_ORDER 대로만 순회하므로 유형 순서가 자동 보장된다.
- 문서 전체에 걸쳐 문항 번호를 연속으로 부여한다(지문2는 7번부터…).
- 배치: [모든 지문의 문제] → [모든 지문의 해설].
- 문제와 해설은 같은 번호로 대응한다.
- 2단(좌/우) 조판, 지문 라벨, 볼드 5곳, 쪽번호는 템플릿/CSS 가 담당한다.
"""
from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from .types import TYPE_LABELS, TYPE_ORDER, TYPE_PROMPTS, Passage

# 서술형 계열(단일 정답 번호가 없는 유형) — 빠른 정답에는 '서술형'으로 표기
SHORT_TYPES = {"short_answer", "D"}
_KEY_RE = re.compile(r'<span class="answer-key">(.*?)</span>', re.S)


def _answer_key(a_html: str, is_short: bool) -> str:
    """해설 HTML 에서 정답 키(①, '③, ④, ⑤' 등)만 뽑아 빠른 정답용으로 돌려준다."""
    if is_short:
        return "서술형"
    m = _KEY_RE.search(a_html)
    if not m:
        return "-"
    txt = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return txt or "-"

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=False,  # 생성기가 만든 HTML 조각을 그대로 삽입한다
)


def _blocks(passages: list[Passage], start: int,
            type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS,
            group_by: str = "passage"):
    """통합 블록 + 빠른 정답 목록을 만들며 문항 번호를 연속 부여한다.

    각 행(row)에 문제(q_body)·해설(a_body)·정답키(key)를 모두 담아,
    한 데이터로 학생용·교사용·빠른정답·해설지 4개 섹션을 조판한다.
    group_by="passage"(기본): [지문1: 유형들][지문2: 유형들]… (지문별)
    group_by="type": [순서배열: 지문1·2·3][문장삽입: …]… (문제유형별)
    번호는 어느 쪽이든 '조판에 나오는 순서 그대로' 1(또는 start)부터 연속 부여한다.
    """
    blocks: list[dict] = []
    quick: list[dict] = []       # 빠른정답: [{label, cells:[{no,key}]}] (label 빈값이면 머리 없이 평평)

    def _row(no: int, t: str, p: Passage) -> tuple[dict, str]:
        a_html = p.a[t]
        key = _answer_key(a_html, t in SHORT_TYPES)
        return ({
            "no": no, "type": t, "prompt": prompts[t],
            "q_body": Markup(p.q[t]), "label": labels[t],
            "a_body": Markup(a_html), "key": key,
        }, key)

    def _has(p, t):     # 생성 실패로 빠진 슬롯은 건너뛴다(부분 생성 허용)
        return bool((p.q.get(t) or "").strip() and (p.a.get(t) or "").strip())

    if group_by == "type":
        # 유형별: 각 유형마다 번호를 1(start)부터 다시 매긴다. ([순서배열] 1·2 [문장삽입] 1·2 …)
        for t in type_order:
            rows: list[dict] = []
            items: list[dict] = []
            n = start
            for p in passages:
                if not _has(p, t):
                    continue
                row, key = _row(n, t, p)
                rows.append(row)
                items.append({"no": n, "key": key})
                n += 1
            if not rows:       # 이 유형이 전 지문에서 다 빠졌으면 블록 생략
                continue
            blocks.append({"label": f"[{labels[t]}]", "title": "", "rows": rows})
            quick.append({"label": f"[{labels[t]}]", "cells": items})
    else:
        # 지문별: 문서 전체 연속 번호(1..N). 빠른정답은 머리 없는 한 묶음(평평).
        n = start
        flat: list[dict] = []
        for i, p in enumerate(passages, start=1):
            rows = []
            for t in type_order:
                if not _has(p, t):
                    continue
                row, key = _row(n, t, p)
                rows.append(row)
                flat.append({"no": n, "key": key})
                n += 1
            disp = getattr(p, "source_label", "") or f"지문 {i}"
            blocks.append({"label": f"[{disp}]", "title": p.title, "rows": rows})
        quick.append({"label": "", "cells": flat})
    return blocks, quick


# 자료 하단 저작권 문구 기본값(필요하면 render_pdf(footer_note=...) 로 교체)
DEFAULT_FOOTER = "ⓒ 2026. Ortica영어. All rights reserved."

# 출력 섹션 키(고정 순서). None 이면 4개 모두.
SECTION_KEYS = ["student", "teacher", "quick", "answers"]
# '확인 권장 문항' 페이지는 교사용 산출물일 때만 붙인다(학생용만 뽑으면 숨김).
_TEACHER_SECTIONS = {"teacher", "quick", "answers"}


def _resolve_sections(sections) -> tuple[set, str | None]:
    """선택 섹션을 정규화하고 '첫 섹션'(페이지 브레이크 억제용)을 찾는다."""
    if not sections:
        active = list(SECTION_KEYS)
    else:
        active = [k for k in SECTION_KEYS if k in sections]
        if not active:                      # 아무것도 안 고르면 전체
            active = list(SECTION_KEYS)
    return set(active), active[0]


def collect_review(passages: list[Passage], start: int = 1,
                   type_order=TYPE_ORDER, labels=TYPE_LABELS,
                   part_label: str = "", group_by: str = "passage") -> list[dict]:
    """'확인 권장'으로 표시된 문항을 문서 연속 번호와 함께 모은다.

    _blocks 와 '같은 순회 순서·같은 번호 부여 규칙'(group_by 포함)을 쓰므로 문항 번호가
    정확히 일치한다. part_label 은 합본에서 어느 파트(1회/2회·난이도)인지 구분용.
    """
    items: list[dict] = []
    n = start

    def _emit(t: str, p: Passage) -> None:
        nonlocal n
        # _blocks 와 동일하게, 생성 실패로 빠진 슬롯은 번호를 매기지 않는다(번호 일치).
        if not ((p.q.get(t) or "").strip() and (p.a.get(t) or "").strip()):
            return
        reasons = getattr(p, "flags", {}).get(t)
        if reasons:
            items.append({"no": n, "label": labels[t], "title": p.title,
                          "part": part_label, "reasons": list(reasons)})
        n += 1

    if group_by == "type":
        # 유형별: 각 유형마다 1(start)부터 — _blocks 와 동일한 번호 규칙(유형 라벨로 구분)
        for t in type_order:
            n = start
            for p in passages:
                _emit(t, p)
    else:
        for p in passages:
            for t in type_order:
                _emit(t, p)
    return items


def render_html(
    passages: list[Passage],
    header_note: str = "",
    doc_title: str = "영어 영역",
    start: int = 1,
    footer_note: str = DEFAULT_FOOTER,
    type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS,
    sections=None, group_by: str = "passage",
) -> str:
    blocks, quick = _blocks(passages, start, type_order, prompts, labels, group_by)
    active, first_section = _resolve_sections(sections)
    tmpl = _env.get_template("exam.html.j2")
    return tmpl.render(
        blocks=blocks,
        quick=quick,
        header_note=header_note,
        doc_title=doc_title,
        footer_note=footer_note,
        sections=active,
        first_section=first_section,
    )


def render_review_html(items: list[dict], footer_note: str = DEFAULT_FOOTER) -> str:
    """'확인 권장 문항'만 모은 마지막 페이지 HTML(독립 문서)."""
    tmpl = _env.get_template("review.html.j2")
    return tmpl.render(items=items, footer_note=footer_note)


def _stylesheets():
    """조판용 스타일시트: [임베드 폰트(fonts.css), 레이아웃(exam.css)] 순서.

    fonts.css 는 나눔스퀘어라운드를 base64 로 직접 담고 있어, 시스템에 폰트가 없거나
    경로가 달라도 항상 같은 폰트로 렌더된다(폰트가 exam.css 보다 먼저 정의돼야 함).
    """
    from weasyprint import CSS  # 지연 임포트(무거움)

    return [CSS(filename=str(TEMPLATE_DIR / "fonts.css")),
            CSS(filename=str(TEMPLATE_DIR / "exam.css"))]


def _write_docs(docs, out_path: Path) -> Path:
    """여러 WeasyPrint 문서의 페이지를 한 PDF로 병합해 쓴다."""
    all_pages = [pg for d in docs for pg in d.pages]
    docs[0].copy(all_pages).write_pdf(str(out_path))
    return out_path


def render_pdf(
    passages: list[Passage],
    out_path: str | Path,
    header_note: str = "",
    doc_title: str = "영어 영역",
    start: int = 1,
    footer_note: str = DEFAULT_FOOTER,
    type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS,
    sections=None, group_by: str = "passage",
) -> Path:
    from weasyprint import HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    active, _ = _resolve_sections(sections)
    html = render_html(passages, header_note=header_note, doc_title=doc_title,
                       start=start, footer_note=footer_note,
                       type_order=type_order, prompts=prompts, labels=labels,
                       sections=sections, group_by=group_by)
    css = _stylesheets()
    docs = [HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=css)]

    # 교사용 산출물이면, '확인 권장 문항'을 맨 끝 별도 페이지로 덧붙인다.
    if active & _TEACHER_SECTIONS:
        items = collect_review(passages, start, type_order, labels, group_by=group_by)
        if items:
            rhtml = render_review_html(items, footer_note)
            docs.append(HTML(string=rhtml, base_url=str(TEMPLATE_DIR)).render(stylesheets=css))

    return _write_docs(docs, out_path)


def render_pdf_multi(parts: list[dict], out_path: str | Path,
                     footer_note: str = DEFAULT_FOOTER,
                     review_out: str | Path | None = None) -> Path | None:
    """여러 '파트'를 한 PDF로 합본한다(WeasyPrint 페이지 병합, 외부 라이브러리 불필요).

    part = {passages, header_note, type_order, prompts, labels, sections}.
    각 파트는 자체 머리글로 시작하고, 파트 사이는 새 쪽에서 이어진다.
    '확인 권장(검토 메모)' 문항은 모아서:
      · review_out 이 None 이면 본문 PDF 맨 끝에 별도 페이지로 붙이고,
      · review_out 이 주어지면 그 경로에 '별도 파일'로 저장한다(본문에는 안 붙임).
    반환: 검토 메모를 별도 파일로 저장했으면 그 경로, 아니면 None.
    """
    from weasyprint import HTML  # 지연 임포트(무거움)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    css = _stylesheets()

    docs = []
    review_items: list[dict] = []
    for part in parts:
        type_order = part.get("type_order", TYPE_ORDER)
        labels = part.get("labels", TYPE_LABELS)
        sections = part.get("sections")
        group_by = part.get("group_by", "passage")
        html = render_html(
            part["passages"],
            header_note=part.get("header_note", ""),
            footer_note=footer_note,
            type_order=type_order,
            prompts=part.get("prompts", TYPE_PROMPTS),
            labels=labels,
            sections=sections,
            group_by=group_by,
        )
        docs.append(HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=css))
        # 각 파트의 확인 권장 문항을 파트 라벨과 함께 모은다(교사용 산출물일 때만).
        active, _ = _resolve_sections(sections)
        if active & _TEACHER_SECTIONS:
            review_items += collect_review(
                part["passages"], 1, type_order, labels,
                part_label=part.get("header_note", ""), group_by=group_by)

    review_path: Path | None = None
    if review_items:
        rhtml = render_review_html(review_items, footer_note)
        rdoc = HTML(string=rhtml, base_url=str(TEMPLATE_DIR)).render(stylesheets=css)
        if review_out is not None:          # 검토 메모를 '별도 파일'로 저장(본문엔 안 붙임)
            review_path = Path(review_out)
            review_path.parent.mkdir(parents=True, exist_ok=True)
            rdoc.write_pdf(str(review_path))
        else:                                # 기존 동작: 본문 맨 끝에 덧붙임
            docs.append(rdoc)

    _write_docs(docs, out_path)
    return review_path
