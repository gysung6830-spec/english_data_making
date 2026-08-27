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
# 정답이 원 번호가 아닌 유형 — 빠른 정답에는 '서술형'으로 적는다.
SHORT_TYPES = {"short_answer", "D", "grammar_fix"}
_KEY_RE = re.compile(r'<span class="answer-key">(.*?)</span>', re.S)

# 번호(①·ⓑ)로 시작하는 근거 문단 — 오답 풀이처럼 번호를 내어쓰기 한다(CSS .reason.num).
_NUM_REASON = re.compile(r'<p class="reason">([①-⑧ⓐ-ⓔ])')


def hang_numbers(a_html: str) -> str:
    """해설 HTML 에서 '번호로 시작하는 근거 문단'에 내어쓰기 클래스를 붙인다.

    어법처럼 항목마다 한 줄씩 적는 유형은 번호가 왼쪽으로 나와야 목록으로 읽힌다.
    산문 근거(주제·요약 등)는 번호로 시작하지 않으므로 그대로 둔다.
    """
    return _NUM_REASON.sub(r'<p class="reason num">\1', a_html or "")


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


# 기본 편성 — 유형별(같은 유형을 몰아 풀며 그 유형의 감을 잡게 한다).
# 지문별로 묶고 싶으면 group_by="passage".
DEFAULT_GROUP_BY = "type"


def _blocks(passages: list[Passage], start: int,
            type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS,
            group_by: str = DEFAULT_GROUP_BY):
    """통합 블록 + 빠른 정답 목록을 만들며 문항 번호를 연속 부여한다.

    각 행(row)에 문제(q_body)·해설(a_body)·정답키(key)·출처(src)를 모두 담아,
    한 데이터로 학생용·교사용·빠른정답·해설지 4개 섹션을 조판한다.
    group_by="type"(기본): [주제: 지문1·2][제목: 지문1·2]… (문제유형별)
    group_by="passage": [지문1: 유형들][지문2: 유형들]… (지문별)
    번호는 어느 쪽이든 '조판에 나오는 순서 그대로' 1(또는 start)부터 연속 부여한다.
    """
    blocks: list[dict] = []
    quick: list[dict] = []       # 빠른정답: [{label, cells:[{no,key}]}] (label 빈값이면 머리 없이 평평)

    def _src(p: Passage, i: int) -> str:
        """문항에 붙일 출처 표기 — 원본 문항번호가 있으면 그것, 없으면 '지문 n'."""
        return (getattr(p, "source_label", "") or "").strip() or f"지문 {i}"

    def _row(no: int, t: str, p: Passage, i: int) -> tuple[dict, str]:
        a_html = hang_numbers(p.a[t])
        key = _answer_key(a_html, t in SHORT_TYPES)
        return ({
            "no": no, "type": t, "prompt": prompts[t],
            "q_body": Markup(p.q[t]), "label": labels[t],
            "a_body": Markup(a_html), "key": key,
            "src": _src(p, i), "title": p.title,
        }, key)

    def _has(p, t):     # 생성 실패로 빠진 슬롯은 건너뛴다(부분 생성 허용)
        return bool((p.q.get(t) or "").strip() and (p.a.get(t) or "").strip())

    if group_by == "type":
        # 유형별: 각 유형마다 번호를 1(start)부터 다시 매긴다. ([순서배열] 1·2 [문장삽입] 1·2 …)
        for t in type_order:
            rows: list[dict] = []
            items: list[dict] = []
            n = start
            for i, p in enumerate(passages, start=1):
                if not _has(p, t):
                    continue
                row, key = _row(n, t, p, i)
                rows.append(row)
                items.append({"no": n, "key": key})
                n += 1
            if not rows:       # 이 유형이 전 지문에서 다 빠졌으면 블록 생략
                continue
            blocks.append({"label": f"[{labels[t]}]", "chip": labels[t],
                           "prompt": prompts[t], "count": len(rows),
                           "title": "", "rows": rows})
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
                row, key = _row(n, t, p, i)
                rows.append(row)
                flat.append({"no": n, "key": key})
                n += 1
            disp = _src(p, i)
            blocks.append({"label": f"[{disp}]", "chip": disp, "prompt": "",
                           "count": len(rows), "title": p.title, "rows": rows})
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
                   part_label: str = "", group_by: str = DEFAULT_GROUP_BY) -> list[dict]:
    """'확인 권장'으로 표시된 문항을 문서 연속 번호와 함께 모은다.

    _blocks 와 '같은 순회 순서·같은 번호 부여 규칙'(group_by 포함)을 쓰므로 문항 번호가
    정확히 일치한다. part_label 은 합본에서 어느 파트인지 구분용.
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

    # 생성 실패로 '빠진 유형'도 알린다. 번호는 남은 문항으로 연속이라 PDF 만 봐서는
    # 어떤 유형이 누락됐는지 알 수 없으므로, 지문별로 모아 한 줄로 표시한다.
    for p in passages:
        missing = [labels[t] for t in type_order
                   if not ((p.q.get(t) or "").strip() and (p.a.get(t) or "").strip())]
        if missing:
            items.append({"no": "-", "label": "생성 누락", "title": p.title,
                          "part": part_label,
                          "reasons": [f"이 지문은 {len(missing)}개 유형이 빠졌습니다: "
                                      + ", ".join(missing)]})
    return items


def render_html(
    passages: list[Passage],
    header_note: str = "",
    doc_title: str = "영어 영역",
    start: int = 1,
    footer_note: str = DEFAULT_FOOTER,
    type_order=TYPE_ORDER, prompts=TYPE_PROMPTS, labels=TYPE_LABELS,
    sections=None, group_by: str = DEFAULT_GROUP_BY,
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
        # 유형별 편성에서는 유형마다 새 쪽에서 시작하고 큰 칩으로 유형 이름을 단다.
        by_type=(group_by == "type"),
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



# ---------------------------------------------------------------------------
# 유형 묶음의 2단 칸 높이 — 한 번 조판해 '재고' 나눈다
# ---------------------------------------------------------------------------
# WeasyPrint 는 column-fill: auto 에서 칸 높이로 '쪽에 남은 높이'를 쓴다. 그래서
# 한 쪽을 다 못 채우는 짧은 유형 묶음은 내용이 왼쪽 단에만 쌓이고 오른쪽 단이 통째로
# 빈다(지문 2~3개짜리 해설편이 늘 그렇다). column-fill: balance 로 조판기에게 맡기면
# 칸 높이를 이분 탐색하느라 해설편 한 섹션에 67초가 걸려 쓸 수 없었고, min-height 는
# 칸 높이에 아무 영향을 주지 않았다(직접 확인).
#
# 그래서 이렇게 한다: 1차로 한 번 조판해 묶음마다 '한 단에 쌓았을 때의 실제 높이'를
# 재고, 문항 경계 중 두 단이 가장 고르게 나뉘는 자리를 골라 그 높이를 height 로 준 뒤
# 2차 조판을 한다. 어림이 아니라 실측이라 빗나갈 일이 없다. 값은 CSS 픽셀.
_GROUP_ID = "tg-"
_COL_SLACK_PX = 4.0     # 칸 높이 여유(≈1mm)


def _box_id(box) -> str | None:
    el = getattr(box, "element", None)
    gid = el.get("id") if el is not None and hasattr(el, "get") else None
    return gid if (gid or "").startswith(_GROUP_ID) else None


def _group_fragments(doc) -> dict[str, list]:
    """조판된 문서에서 유형 묶음(2단 상자) 조각을 id 별로 모은다.

    다단 상자는 '바깥 상자 → 단 상자들'로 두 겹인데 둘 다 같은 element 를 물고 있다.
    바깥 상자만 잡아야 children 이 '단'이 된다(안쪽을 잡으면 children 이 문항이라
    단이 몇 개인지 알 수 없다). 그래서 만나는 즉시 그 아래는 더 보지 않는다.
    """
    out: dict[str, list] = {}

    def walk(box) -> None:
        gid = _box_id(box)
        if gid:
            out.setdefault(gid, []).append(box)
            return                       # 안쪽 겹은 건너뛴다
        for child in (getattr(box, "children", None) or []):
            walk(child)

    for page in doc.pages:
        walk(page._page_box)
    return out


def _even_split(heights: list[float]) -> float:
    """문항 경계 중 두 단이 가장 고르게 나뉘는 자리의 '큰 쪽' 높이."""
    total = sum(heights)
    best, acc = total, 0.0
    for h in heights[:-1]:
        acc += h
        best = min(best, max(acc, total - acc))
    return best


def _balance_css(doc) -> str:
    """1차 조판 실측 → 2차 조판에 줄 '묶음별 칸 높이' 스타일(없으면 빈 문자열)."""
    rules = []
    for gid, frags in _group_fragments(doc).items():
        if len(frags) != 1:          # 이미 여러 쪽에 걸친 묶음 — 손대지 않는다
            continue
        cols = list(getattr(frags[0], "children", None) or [])
        if len(cols) != 1:           # 이미 두 단을 쓰고 있다 — 그대로 둔다
            continue
        items = [c for c in (getattr(cols[0], "children", None) or [])
                 if hasattr(c, "margin_height")]
        if len(items) < 2:           # 문항이 하나뿐이면 나눌 수 없다
            continue
        # 딱 맞게 주면 반올림 한 톨에 첫 단이 넘쳐, 칩만 남고 본문이 다음 쪽으로
        # 밀린다(실제로 16쪽짜리가 26쪽이 됐다). 1mm 남짓 여유를 둔다.
        want = _even_split([c.margin_height() for c in items]) + _COL_SLACK_PX
        rules.append(f"#{gid}{{height:{want:.1f}px}}")
    return "".join(rules)


def _render_doc(html: str, css):
    """조판한다. 유형 묶음이 한 단에만 쌓였으면 칸 높이를 재서 다시 조판한다."""
    from weasyprint import CSS, HTML  # 지연 임포트(무거움)

    doc = HTML(string=html, base_url=str(TEMPLATE_DIR)).render(stylesheets=css)
    extra = _balance_css(doc)
    if not extra:
        return doc
    return HTML(string=html, base_url=str(TEMPLATE_DIR)).render(
        stylesheets=list(css) + [CSS(string=extra)])


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
    sections=None, group_by: str = DEFAULT_GROUP_BY,
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
    docs = [_render_doc(html, css)]

    # 교사용 산출물이면, '확인 권장 문항'을 맨 끝 별도 페이지로 덧붙인다.
    if active & _TEACHER_SECTIONS:
        items = collect_review(passages, start, type_order, labels, group_by=group_by)
        if items:
            rhtml = render_review_html(items, footer_note)
            docs.append(HTML(string=rhtml, base_url=str(TEMPLATE_DIR)).render(stylesheets=css))

    return _write_docs(docs, out_path)


def _collect_review_items(parts: list[dict]) -> list[dict]:
    """파트들에서 '확인 권장' 문항을 모은다(교사용 산출물이 있는 파트만)."""
    items: list[dict] = []
    for part in parts:
        active, _ = _resolve_sections(part.get("sections"))
        if active & _TEACHER_SECTIONS:
            items += collect_review(
                part["passages"], 1,
                part.get("type_order", TYPE_ORDER),
                part.get("labels", TYPE_LABELS),
                part_label=part.get("header_note", ""),
                group_by=part.get("group_by", DEFAULT_GROUP_BY))
    return items


def render_review_pdf(parts: list[dict], out_path: str | Path,
                      footer_note: str = DEFAULT_FOOTER) -> Path | None:
    """'검토 메모'만 별도 PDF 로 쓴다(본문 조판 없이).

    개별 파일만 뽑을 때처럼 합본을 만들지 않는 경우에도 검토 메모를 남기기 위해 쓴다.
    확인 권장 문항이 하나도 없으면 파일을 만들지 않고 None 을 돌려준다.
    """
    from weasyprint import HTML  # 지연 임포트(무거움)

    items = _collect_review_items(parts)
    if not items:
        return None
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=render_review_html(items, footer_note),
         base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=_stylesheets())
    return out_path


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
        group_by = part.get("group_by", DEFAULT_GROUP_BY)
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
        docs.append(_render_doc(html, css))
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
