"""조판 (§6) — 원본 시험지 디자인 재현.

문제지: 테두리 머리글(제목·코드·반·과목·시간) → 좌우 2단 → <서술형> → 하단 쪽번호.
정답해설지: '정 답 및 해 설' 제목 → 문항별 배지(유형·난이도·배점) → 정답/해설.
- HTML 항상 생성(브라우저 미리보기). WeasyPrint 있으면 PDF 도 생성(쪽번호 포함).
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from ..core.models import DIFFICULTY_KO_REV, MockExam, Question

# 유형 → 정답지 배지용 한글 라벨
TYPE_LABEL_KO = {
    "grammar": "어법", "grammar_vocab_mix": "어법·어휘", "vocab_odd": "어휘",
    "vocab_3blank_abc": "어휘(빈칸)", "main_point": "요지", "title": "제목",
    "blank_single": "빈칸추론", "order": "순서", "irrelevant_sentence": "무관문장",
    "implied_meaning": "함축의미", "inference_mismatch": "내용일치",
    "dialogue_mismatch": "대화내용", "notice_match": "안내문", "summary_ab": "요약(A,B)",
    "prep_find_and_translate": "서술형·전치사/해석",
    "dialogue_arrange_inflect": "서술형·영작", "condition_write_inflect": "서술형·어형변형",
    "summary_fill_from_text": "서술형·요약빈칸", "word_arrange": "서술형·배열",
    "chart_fix_and_arrange": "서술형·도표", "arrange_and_translate": "서술형·배열/해석",
    "blank_choose_no_change": "서술형·어휘선택", "grammar_fix_and_answer": "서술형·어법교정",
}

# 서술형에서 <보기> 박스를 쓰는 유형
_BOGI_TYPES = {"dialogue_arrange_inflect", "condition_write_inflect", "word_arrange",
               "arrange_and_translate", "chart_fix_and_arrange", "blank_choose_no_change"}

# 한글 본문 글꼴: 학교 시험지(HWP) 기본 명조인 함초롬바탕을 1순위로,
# 미설치 환경을 위해 바탕/Batang → Noto Serif KR 순으로 대체.
_SERIF = ("'함초롬바탕','HCR Batang','Batang','바탕','Noto Serif KR',"
          "'Nanum Myeongjo','Times New Roman',serif")

_CSS = f"""
* {{ box-sizing: border-box; }}
@page {{ size: A4; margin: 11mm 12mm 10mm 12mm; }}
body {{ font-family: {_SERIF}; font-size: 8.2pt; line-height: 1.42; color:#000; margin:0; }}

/* 머리글 */
.exam-header {{ border:1.2px solid #000; padding:6px 12px 5px; margin-bottom:8px; }}
.exam-title {{ text-align:center; font-size:17pt; font-weight:700; letter-spacing:4px;
               margin-bottom:5px; }}
.hrow {{ display:flex; align-items:center; justify-content:space-between; font-size:10.5pt; }}
.hrow .center {{ font-weight:700; }}
.code-pill {{ border:1px solid #000; border-radius:999px; padding:1px 11px; font-size:9pt; }}
.exam-time {{ text-align:center; font-size:8.5pt; color:#333; margin-top:3px; }}

/* 유의사항(머리글 박스 아래) */
.guidelines {{ break-inside:avoid; font-size:8.4pt; line-height:1.4; margin-bottom:7px;
               padding-bottom:5px; border-bottom:0.6px solid #999; }}
.g-item {{ padding-left:12px; text-indent:-12px; margin:1px 0; }}
.g-item .cont {{ display:block; padding-left:12px; text-indent:0; }}

/* 2단. column-fill:auto → 각 페이지를 위→아래(왼쪽 단 먼저)로 꽉 채움 */
.columns {{ column-count:2; column-gap:18px; column-rule:0.6px solid #cfcfcf;
            column-fill:auto; }}
.section-div {{ column-span:all; font-weight:700; margin:6px 0 8px; }}

/* 페이지 단위 2단 배치(문항을 좌단부터 채움) */
.page {{ page-break-before: always; break-before: page; }}
.page:first-child {{ page-break-before: avoid; break-before: avoid; }}
.sheet {{ overflow: hidden; }}   /* clearfix */
.col {{ width: 48%; }}
.col.left {{ float: left; border-right: 0.6px solid #cfcfcf; padding-right: 15px; }}
.col.right {{ float: right; }}

/* 문항 */
.q {{ break-inside:avoid; margin-bottom:17px; }}
.q-head {{ font-weight:700; margin-bottom:4px; }}
.q-head .no {{ font-weight:800; }}
.q-head .score {{ font-weight:400; font-size:8.4pt; color:#333; }}
.passage {{ text-align:justify; margin:4px 0 5px; }}
.dialogue {{ margin:4px 0 5px; }}
.dialogue .turn {{ text-align:justify; margin:2px 0; padding-left:14px; text-indent:-14px; }}
.para {{ text-align:justify; margin:3px 0; }}
.box {{ border:1px solid #000; padding:5px 8px; margin:5px 0; text-align:justify; }}
.choices {{ margin:5px 0 0 2px; }}
.choices div {{ margin:1px 0; }}
.choices.numonly {{ margin-left:2px; letter-spacing:6px; }}
u {{ text-underline-offset:2px; }}

/* 보기/조건 박스 */
.bogi {{ border:1px solid #000; padding:5px 9px; margin:5px 0; text-align:center; }}
.bogi .label {{ font-weight:700; margin-bottom:2px; }}
.bogi.cond {{ text-align:left; }}
.bogi.cond .label {{ text-align:center; }}
.cond-list div {{ margin:1px 0; }}
.bogi.summary {{ text-align:left; }}
.bogi.summary .label {{ text-align:center; }}
.summary-text {{ text-align:justify; margin-top:2px; }}

/* 안내문 박스 */
.box.notice {{ text-align:left; }}
.notice-title {{ text-align:center; font-weight:700; margin-bottom:4px; }}
.notice-row {{ margin:2px 0; text-align:justify; }}
.blank-ko {{ margin:4px 0; }}
.answer-space {{ border-bottom:1px solid #000; height:26px; margin:6px 0 2px; }}

/* 하단 */
.footer {{ text-align:center; font-size:8.3pt; color:#555; margin-top:10px;
           padding-top:6px; }}

/* 정답해설지 */
.ans-title {{ text-align:center; font-size:16pt; font-weight:700; letter-spacing:8px;
              margin:2px 0 4px; }}
.ans-rule {{ border:0; border-top:2px solid #000; margin:0 0 12px; }}
.ans-item {{ break-inside:avoid; margin-bottom:12px; }}
.ans-no {{ font-weight:700; }}
.badge {{ border:1px solid #444; border-radius:999px; padding:1px 10px; font-size:8.6pt;
          color:#333; margin-left:6px; }}
.ans-line {{ margin:3px 0; }}
.ans-line .a {{ font-weight:700; }}
.exp {{ text-align:justify; }}
.trap {{ color:#b00020; }}
"""


# ---------------------------------------------------------------------------
# 지문 렌더 (밑줄/순서 도입문/보기 처리)
# ---------------------------------------------------------------------------
def _safe(text: str) -> str:
    """<u>..</u> 밑줄만 허용하고 나머지는 이스케이프."""
    out = []
    for t in re.split(r"(<u>|</u>)", text):
        out.append(t if t in ("<u>", "</u>") else html.escape(t))
    return "".join(out)


def _render_passage(q: Question) -> str:
    text = q.passage_text or ""
    if not text or text.startswith("(지문 부족") or text.startswith("(지문"):
        return ""
    # 순서(order): 도입문 박스 + (A)(B)(C) 문단
    if q.type == "order" and "(A)" in text and "(B)" in text:
        m = re.split(r"(?=\(A\))", text, maxsplit=1)
        intro = m[0].strip()
        rest = m[1] if len(m) > 1 else ""
        parts = [f'<div class="box">{_safe(intro)}</div>'] if intro else []
        for seg in re.split(r"(?=\((?:A|B|C)\))", rest):
            seg = seg.strip()
            if seg:
                parts.append(f'<div class="para">{_safe(seg)}</div>')
        return "".join(parts)
    # 안내문: 박스 + 구획별 줄나누기
    if q.type == "notice_match" or _looks_notice(text):
        return _render_notice_box(text)
    # 대화문: 화자별 줄나누기
    if q.type in ("dialogue_mismatch", "dialogue_arrange_inflect") or _looks_dialogue(text):
        turns = [t.strip() for t in _SPEAKER_SPLIT.split(text) if t.strip()]
        if len(turns) >= 2:
            return ('<div class="passage dialogue">'
                    + "".join(f'<div class="turn">{_safe(t)}</div>' for t in turns)
                    + '</div>')
    # 요약문([요약문] 마커) 분리 박스
    if "[요약문]" in text:
        body, _, summ = text.partition("[요약문]")
        out = []
        if body.strip():
            out.append(f'<div class="passage">{_safe(body.strip())}</div>')
        out.append(f'<div class="bogi summary"><div class="label">&lt; 요약문 &gt;</div>'
                   f'<div class="summary-text">{_safe(summ.strip())}</div></div>')
        return "".join(out)
    return f'<div class="passage">{_safe(text)}</div>'


# 안내문 구획 라벨
_NOTICE_LABEL = re.compile(
    r"(When\s*&\s*Where|When|Where|Date|Time|Location|Admission|Highlights|Notes|"
    r"Details|Registration|Price|Fee|Cost|Contact|Venue|Schedule|Hours|Deadline|"
    r"Eligibility|Prize|How to (?:Apply|Join|Register))\s*:", re.I)


def _looks_notice(text: str) -> bool:
    return len(_NOTICE_LABEL.findall(text)) >= 2


# 대화문 화자 라벨(줄 시작): 'Host:', 'Dr. Hill:', 'M:', 'W:', 'Woman:' 등
_SPEAKER_SPLIT = re.compile(
    r"(?=(?:[A-Z][a-zA-Z]*(?:\.\s*[A-Z][a-zA-Z]+)?|[MW]|Man|Woman|Boy|Girl)\s*:\s)")


def _looks_dialogue(text: str) -> bool:
    return len(_SPEAKER_SPLIT.findall(text)) >= 3


def _render_notice_box(text: str) -> str:
    """안내문을 박스에 넣고 제목·구획을 줄나누기."""
    segs = _NOTICE_LABEL.split(text)
    # split 은 [title, label1, tail1, label2, tail2, ...] 형태(캡처그룹 포함)
    title = segs[0].strip()
    lines = []
    i = 1
    while i < len(segs):
        label = segs[i].strip()
        content = segs[i + 1].strip() if i + 1 < len(segs) else ""
        lines.append(f'<div class="notice-row"><b>{html.escape(label)}:</b> '
                     f'{_safe(content)}</div>')
        i += 2
    head = f'<div class="notice-title">{_safe(title)}</div>' if title else ""
    return f'<div class="box notice">{head}{"".join(lines)}</div>'


def _render_bogi(q: Question) -> str:
    """서술형의 <조건>·<보기> 박스와 밑줄 우리말을 렌더."""
    out = []
    conditions = q.meta.get("conditions")
    if conditions:
        items = "".join(f'<div>· {html.escape(str(c))}</div>' for c in conditions)
        out.append(f'<div class="bogi cond"><div class="label">&lt; 조건 &gt;</div>'
                   f'<div class="cond-list">{items}</div></div>')
    blank_ko = q.meta.get("blank_ko")
    if blank_ko:
        out.append(f'<div class="blank-ko">밑줄: {html.escape(blank_ko)}</div>')
    bogi = q.meta.get("bogi")
    if bogi:
        words = " / ".join(html.escape(w) for w in bogi)
        out.append(f'<div class="bogi"><div class="label">&lt; 보기 &gt;</div>{words}</div>')
    return "".join(out)


def _q_html(q: Question) -> str:
    parts = [f'<div class="q"><div class="q-head"><span class="no">{q.no}.</span> '
             f'{html.escape(q.stem)} '
             f'<span class="score">[{_fmt_score(q.score)}점]</span></div>']
    parts.append(_render_passage(q))
    if q.section == "essay":
        parts.append(_render_bogi(q))
    if q.choices:
        if q.meta.get("number_only"):
            # 어법·무관문장 등: 선지는 번호(①~⑤)만 한 줄로
            labels = " ".join(c.label for c in q.choices)
            parts.append(f'<div class="choices numonly">{labels}</div>')
        else:
            parts.append('<div class="choices">')
            for c in q.choices:
                parts.append(f'<div>{c.label} {html.escape(c.text)}</div>')
            parts.append('</div>')
    if q.section == "essay":
        parts.append('<div class="answer-space"></div>')
    parts.append('</div>')
    return "".join(parts)


def _fmt_score(s: float) -> str:
    return str(int(s)) if float(s).is_integer() else f"{s:g}"


# ---------------------------------------------------------------------------
# 머리글 / 하단
# ---------------------------------------------------------------------------
def _header_block(exam: MockExam, info: dict) -> str:
    m = exam.blueprint.meta
    title = info.get("exam_title") or f"{m.grade}학년 영어 동형모의고사"
    code = info.get("code", "03")
    class_range = info.get("class_range", f"{m.grade}학년")
    subject = info.get("subject") or m.subject or "공통영어1"
    date = info.get("date", "")
    time_line = f"{date} ({m.time_min}분)" if date else f"({m.time_min}분)"
    return (
        '<div class="exam-header">'
        f'<div class="exam-title">{html.escape(title)}</div>'
        '<div class="hrow">'
        f'<span class="code-pill">코드: {html.escape(str(code))}</span>'
        f'<span class="center">{html.escape(class_range)}</span>'
        f'<span>과목명: {html.escape(subject)}</span>'
        '</div>'
        f'<div class="exam-time">{html.escape(time_line)}</div>'
        '</div>')


# 유의사항 기본 문구(원본 시험지 그대로). config header_info.guidelines 로 교체 가능.
DEFAULT_GUIDELINES = [
    "선다형은 반드시 컴퓨터용 사인펜을 사용하여 해당 답란에 정확히 마킹(●)하시오."
    "\n서술형은 서술형 답안지에 흑색 또는 청색 볼펜을 사용하여 정확히 서술하시오.",
    "각 문항마다 배점이 다르니 문항 끝에 표시된 배점을 참고하기 바랍니다.",
]


def _guidelines_block(exam: MockExam, info: dict) -> str:
    """머리글 박스 아래 유의사항. 마지막 줄은 blueprint 로 문항수·쪽수 자동 산정."""
    if info.get("guidelines") is False:      # 명시적으로 끄기
        return ""
    lines = info.get("guidelines") or DEFAULT_GUIDELINES
    m = exam.blueprint.meta
    n_c = len(exam.choice_questions)
    n_e = len(exam.essay_questions)
    summary = (f"지필평가: 총( {n_c + n_e} )문항"
               f"(선다형( {n_c} )문항, 서술형( {n_e} )문항), 총( {m.pages} )쪽")
    items = []
    for ln in lines:
        segs = str(ln).split("\n")
        head = html.escape(segs[0])
        cont = "".join(f'<span class="cont">{html.escape(s)}</span>' for s in segs[1:])
        items.append(f'<div class="g-item">○ {head}{cont}</div>')
    items.append(f'<div class="g-item">○ {html.escape(summary)}</div>')
    return f'<div class="guidelines">{"".join(items)}</div>'


def _footer_note(exam: MockExam, footer: str) -> str:
    """매 페이지 하단에 넣을 저작권 문구(쪽번호는 @page 카운터가 채움)."""
    m = exam.blueprint.meta
    note = footer or "이 시험문제는 은아T영어연구소의 저작물입니다."
    return f"{note}  ·  {m.grade}학년 {m.subject or '공통영어1'}"


# ---------------------------------------------------------------------------
# 문제지 / 정답지
# ---------------------------------------------------------------------------
# 한 단(컬럼)의 대략 가용 높이(mm). @page 여백 11/10mm 기준.
_COL_H = 262.0
_HEADER_H = 28.0
_GUIDE_H = 24.0
_SECTION_H = 9.0


def _est_height(q: Question) -> float:
    """문항의 대략 높이(mm) 추정 — 좌/우 단 배치용(8.8pt 기준)."""
    words = len((q.passage_text or "").split())
    h = 6.0                                   # 발문
    h += (words / 9.5) * 4.0                  # 지문(한 줄 ~9.5단어, 줄높이 ~4.0mm)
    if q.choices:
        h += len(q.choices) * 4.2             # 선지
    if q.section == "essay":
        h += 16.0                             # 답란
        if q.meta.get("bogi"):
            h += 14.0                         # <보기> 박스
        if q.meta.get("conditions"):
            h += 10.0 + len(q.meta["conditions"]) * 4.0   # <조건> 박스
        if q.meta.get("blank_ko"):
            h += 5.0
    h += 9.0                                  # 문항 간 여백
    return h


def _pack(questions: list[Question], first_left: float, first_right: float,
          col_h: float) -> list[tuple[list, list]]:
    """문항을 (좌단, 우단) 페이지 리스트로 배치. 좌단부터 채운다."""
    pages: list[tuple[list, list]] = []
    left: list = []
    right: list = []
    lh = rh = 0.0
    bl, br = first_left, first_right
    for q in questions:
        h = _est_height(q)
        if not left or lh + h <= bl:          # 좌단 우선(빈 좌단엔 무조건)
            left.append(q); lh += h
        elif rh + h <= br:                     # 좌단 다 차면 우단
            right.append(q); rh += h
        else:                                  # 둘 다 차면 새 페이지
            pages.append((left, right))
            left, right, lh, rh, bl, br = [q], [], h, 0.0, col_h, col_h
    if left or right:
        pages.append((left, right))
    return pages


def _render_sheet(left_html: str, right_html: str) -> str:
    return (f'<div class="sheet"><div class="col left">{left_html}</div>'
            f'<div class="col right">{right_html}</div></div>')


def build_problem_html(exam: MockExam, info: dict, footer: str = "") -> str:
    """실제 시험지 배치: 문항 높이를 추정해 좌/우 단·페이지로 직접 배치.

    선택형은 페이지당 ~5문항(좌단부터 채움), 서술형은 새 페이지에서 시작해 ~3문항.
    """
    guide = _guidelines_block(exam, info)
    # 선택형: 1쪽 좌단은 머리글+유의사항만큼 줄임
    c_pages = _pack(exam.choice_questions,
                    first_left=_COL_H - _HEADER_H - _GUIDE_H,
                    first_right=_COL_H - _HEADER_H, col_h=_COL_H)
    e_pages = _pack(exam.essay_questions,
                    first_left=_COL_H - _SECTION_H,
                    first_right=_COL_H - _SECTION_H, col_h=_COL_H) \
        if exam.essay_questions else []

    pages_html: list[str] = []
    for i, (left, right) in enumerate(c_pages):
        inner = _header_block(exam, info) if i == 0 else ""
        lh = (guide if i == 0 else "") + "".join(_q_html(q) for q in left)
        rh = "".join(_q_html(q) for q in right)
        pages_html.append(f'<div class="page">{inner}{_render_sheet(lh, rh)}</div>')
    for i, (left, right) in enumerate(e_pages):
        sec = '<div class="section-div">&lt; 서 술 형 &gt;</div>' if i == 0 else ""
        lh = "".join(_q_html(q) for q in left)
        rh = "".join(_q_html(q) for q in right)
        pages_html.append(f'<div class="page">{sec}{_render_sheet(lh, rh)}</div>')

    title = info.get("exam_title") or f"{exam.blueprint.meta.name} 동형모의고사"
    return _wrap(title, "".join(pages_html), footer_note=_footer_note(exam, footer))


def build_answer_html(exam: MockExam, info: dict, footer: str = "") -> str:
    body = ['<div class="ans-title">정 답 및 해 설</div><hr class="ans-rule">']
    for q in exam.questions:
        label = TYPE_LABEL_KO.get(q.type, q.type)
        diff = DIFFICULTY_KO_REV.get(q.difficulty, "중")
        no = f"{q.no}번" if q.section == "choice" else f"서술형 {q.no}번"
        badge = f"{label} · {diff} · {_fmt_score(q.score)}점"
        body.append(f'<div class="ans-item"><span class="ans-no">{no}</span>'
                    f'<span class="badge">{html.escape(badge)}</span>')
        if q.answer_notes:
            body.append(f'<div class="ans-line"><span class="a">정답.</span> '
                        f'{html.escape(q.answer)}</div>')
            for n in q.answer_notes:
                body.append(f'<div class="ans-line">· {html.escape(n)}</div>')
        else:
            body.append(f'<div class="ans-line"><span class="a">정답.</span> '
                        f'{html.escape(q.answer)}</div>')
        if q.explanation:
            body.append(f'<div class="exp"><b>해설.</b> {_exp_html(q.explanation)}</div>')
        body.append('</div>')
    return _wrap("정답 및 해설", "".join(body), footer_note=_footer_note(exam, footer))


def _exp_html(text: str) -> str:
    """[오답 함정] 대괄호 주석은 강조색으로, <b>..</b> 는 굵게 허용, 나머지는 이스케이프."""
    out = []
    for t in re.split(r"(<b>|</b>)", text):
        if t in ("<b>", "</b>"):
            out.append(t)
        else:
            out.append(re.sub(r"(\[[^\]]+\])", r'<span class="trap">\1</span>',
                              html.escape(t)))
    return "".join(out)


def _page_css(footer_note: str) -> str:
    """매 페이지 하단(@bottom)에 저작권 문구·쪽번호를 넣는 @page 규칙."""
    note = footer_note.replace('"', "'")
    return (
        "@page { "
        f'@bottom-center {{ content: "{note}"; font-family: {_SERIF}; '
        'font-size: 8pt; color: #555; } '
        '@bottom-right { content: "( " counter(page) " ) / ( " counter(pages) " )"; '
        'font-size: 8pt; color: #555; } }')


def _wrap(title: str, body: str, footer_note: str = "") -> str:
    page_css = _page_css(footer_note) if footer_note else ""
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<title>{html.escape(title)}</title>'
            f'<style>{_CSS}{page_css}</style></head>'
            f'<body>{body}</body></html>')


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------
def render_exam(exam: MockExam, out_dir: str | Path, form: str = "A",
                header_info: dict | None = None, footer: str = "",
                answer_key: str = "end", to_pdf: bool = True,
                basename: str | None = None) -> dict[str, Path]:
    """basename 을 주면 출력 파일명을 '{basename}.html/.pdf' 로 지정(웹앱 파일명 선택용)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    info = header_info or {}
    result: dict[str, Path] = {}
    stem = basename or f"mock_form_{form}"

    prob = build_problem_html(exam, info, footer)
    ans = build_answer_html(exam, info, footer)

    if answer_key == "end":
        prob = prob.replace("</body></html>",
                            '<div style="break-before:page"></div>'
                            + ans.split("<body>")[1].split("</body>")[0]
                            + "</body></html>")

    p_html = out / f"{stem}.html"
    p_html.write_text(prob, encoding="utf-8")
    result["problem_html"] = p_html

    if answer_key == "separate":
        a_html = out / f"{stem}_answers.html"
        a_html.write_text(ans, encoding="utf-8")
        result["answers_html"] = a_html

    if to_pdf:
        _maybe_pdf(prob, out / f"{stem}.pdf", result, "problem_pdf")
        if answer_key == "separate":
            _maybe_pdf(ans, out / f"{stem}_answers.pdf", result, "answers_pdf")
    return result


def _maybe_pdf(html_str: str, path: Path, result: dict, key: str) -> None:
    try:
        from weasyprint import HTML
    except Exception:
        return
    HTML(string=html_str).write_pdf(str(path))
    result[key] = path
