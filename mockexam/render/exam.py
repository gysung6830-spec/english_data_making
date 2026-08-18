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
_SERIF = ("'함초롬바탕','HCR Batang','Batang','바탕','Noto Serif CJK KR',"
          "'Noto Serif KR','NanumMyeongjo','Nanum Myeongjo','Times New Roman',serif")

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

/* 2단 흐름 배치. column-fill:auto → 왼쪽 단을 페이지 끝까지 채운 뒤 오른쪽 단,
   그다음 페이지로 넘어간다. 네이티브 페이지네이션이라 높이 추정 없이도
   문항이 페이지 경계에서 절대 겹치지(오버프린트) 않는다. */
.flow {{ column-count:2; column-gap:18px; column-rule:0.6px solid #cfcfcf;
         column-fill:auto; }}
.section-div {{ font-weight:700; margin:6px 0 8px; }}

.page {{ page-break-before: always; break-before: page; }}
.page:first-child {{ page-break-before: avoid; break-before: avoid; }}

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
.ans-rule {{ border:0; border-top:2px solid #000; margin:0 0 10px; }}
.ans-item {{ break-inside:avoid; margin-bottom:11px; padding-bottom:9px;
             border-bottom:0.6px dashed #cfcfcf; }}
.ans-head {{ margin-bottom:3px; }}
.ans-no {{ font-weight:800; font-size:9.4pt; }}
.badge {{ border:1px solid #888; border-radius:999px; padding:0 8px; font-size:8pt;
          color:#333; margin-left:6px; }}
.warn {{ border:1px solid #b00020; border-radius:999px; padding:0 8px; font-size:8pt;
         color:#b00020; font-weight:700; margin-left:6px; }}
.warn-note {{ color:#b00020; font-size:8.3pt; margin:3px 0 0; }}
.ans-line {{ margin:2px 0; }}
.ans-line .a {{ font-weight:800; color:#1d4ed8; }}
.ans-line .ansval {{ font-weight:800; }}
/* 해설 본문: 좌측정렬·넉넉한 줄간격, 구조화된 줄(라벨·선지) */
.exp {{ margin-top:3px; line-height:1.62; }}
.exp-line {{ margin:2.5px 0; padding-left:13px; text-indent:-13px; text-align:left; }}
.exp .lbl {{ font-weight:700; color:#0f5aa8; }}
.exp .lbl.trap {{ color:#b00020; }}
.exp .ci {{ font-weight:700; }}
.exp b {{ font-weight:800; }}

/* 섹션 구분 배너(학생용/교사용/빠른정답/해설) */
.sec-banner {{ text-align:center; font-size:13pt; font-weight:800; letter-spacing:3px;
               border:2px solid #000; border-radius:4px; padding:6px 8px; margin-bottom:10px; }}
/* 교사용: 문항 아래 정답+해설 */
.t-ans {{ margin-top:4px; font-size:8.6pt; }}
.t-ans b {{ color:#1d4ed8; font-weight:800; }}
.q .exp {{ margin:3px 0 2px; padding:5px 8px; background:#f6f8fc;
           border-left:2px solid #9db8e6; }}
/* 빠른 정답 */
.qa-sub {{ font-weight:800; margin:8px 0 4px; font-size:10pt; }}
.qa-table {{ border-collapse:collapse; margin:2px 0 4px; }}
.qa-table td {{ border:0.6px solid #999; padding:3px 7px; text-align:center;
                font-size:10pt; min-width:20px; }}
.qa-table td.qn {{ font-weight:800; background:#f0f2f5; }}
.qa-table td.qa {{ font-weight:700; }}
.qa-essay {{ font-size:9.2pt; line-height:1.6; }}
.qa-erow {{ margin:2px 0; padding-left:14px; text-indent:-14px; }}
/* 확인 권장 문항(맨 끝 별도 페이지) */
.rev-intro {{ font-size:9pt; color:#8a5a00; background:#fff8e1; border:1px solid #ffe08a;
              border-radius:6px; padding:8px 10px; margin-bottom:10px; }}
.rev-table {{ width:100%; border-collapse:collapse; font-size:9.2pt; }}
.rev-table th, .rev-table td {{ border:0.6px solid #bbb; padding:5px 8px; text-align:left;
              vertical-align:top; }}
.rev-table th {{ background:#f0f2f5; font-weight:800; }}
.rev-table td.rv-no {{ font-weight:800; white-space:nowrap; }}
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
    # 내용일치 개수형: 본문 + [보기] 진술 5개 박스(①~⑤ 줄바꿈)
    if q.type == "count_match" or "[보기]" in text:
        body, _, bogi = text.partition("[보기]")
        bogi_html = re.sub(r"^<br>", "",
                           re.sub(r"\s*([①②③④⑤])", r"<br>\1", _safe(bogi.strip())))
        out = []
        if body.strip():
            out.append(f'<div class="passage">{_safe(body.strip())}</div>')
        out.append(f'<div class="bogi"><div class="label">&lt; 보기 &gt;</div>{bogi_html}</div>')
        return "".join(out)
    # 문장삽입: [주어진 문장] 박스 + ①~⑤ 위치 본문
    if q.type == "insert" or "[주어진 문장]" in text:
        after = text.split("[주어진 문장]", 1)[1].strip() if "[주어진 문장]" in text else text
        if "\n" in after:
            given, body = after.split("\n", 1)
        else:
            m = re.search(r"[①②③④⑤]", after)
            given, body = (after[:m.start()], after[m.start():]) if m else (after, "")
        box = (f'<div class="bogi"><div class="label">&lt; 주어진 문장 &gt;</div>'
               f'{_safe(given.strip())}</div>')
        return box + f'<div class="passage">{_safe(body.strip())}</div>'
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


def _q_html(q: Question, teacher: bool = False) -> str:
    """문항 1개 HTML. teacher=True 면 정답을 볼드 표시하고 해설을 문항 아래에 붙인다."""
    correct = (q.answer or "").strip()
    parts = [f'<div class="q"><div class="q-head"><span class="no">{q.no}.</span> '
             f'{html.escape(q.stem)} '
             f'<span class="score">[{_fmt_score(q.score)}점]</span></div>']
    parts.append(_render_passage(q))
    if q.section == "essay":
        parts.append(_render_bogi(q))
    if q.choices:
        if q.meta.get("number_only"):
            # 어법·무관문장 등: 선지는 번호(①~⑤)만 한 줄로(교사용은 정답 번호 볼드).
            # 복수정답(어법 모두 고르기)은 정답이 '② ④'처럼 여러 개 → 집합으로 처리.
            correct_set = set(correct.split())
            labels = " ".join(
                (f'<b>{c.label}</b>' if teacher and c.label in correct_set else c.label)
                for c in q.choices)
            parts.append(f'<div class="choices numonly">{labels}</div>')
        else:
            parts.append('<div class="choices">')
            for c in q.choices:
                line = f'{c.label} {html.escape(c.text)}'
                if teacher and c.label == correct:
                    line = f'<b>{line}</b>'
                parts.append(f'<div>{line}</div>')
            parts.append('</div>')
    if teacher:
        parts.append(f'<div class="t-ans">정답 <b>{html.escape(_ko_normalize(q.answer))}</b></div>')
        if q.answer_notes:
            for n in q.answer_notes:
                parts.append(f'<div class="ans-line">· {html.escape(_ko_normalize(n))}</div>')
        if q.explanation:
            parts.append(f'<div class="exp">{_exp_html(q.explanation)}</div>')
    elif q.section == "essay":
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
    note = footer or "© 2026 Ortica영어. All rights reserved."
    return f"{note}  ·  {m.grade}학년 {m.subject or '공통영어1'}"


# ---------------------------------------------------------------------------
# 문제지 / 정답지
# ---------------------------------------------------------------------------
def _section_banner(text: str) -> str:
    return f'<div class="sec-banner">{html.escape(text)}</div>'


def _problem_body(exam: MockExam, info: dict, teacher: bool = False,
                  top: str = "") -> str:
    """문제지 본문(2단 흐름). teacher=True 면 정답 볼드+해설을 각 문항 아래 붙인다.

    top: 첫 페이지 상단에 넣을 블록(머리글 또는 섹션 배너).
    """
    choice_flow = "".join(_q_html(q, teacher) for q in exam.choice_questions)
    pages = [f'<div class="page">{top}'
             f'<div class="flow">{choice_flow}</div></div>']
    if exam.essay_questions:
        essay_flow = "".join(_q_html(q, teacher) for q in exam.essay_questions)
        pages.append('<div class="page">'
                     '<div class="section-div">&lt; 서 술 형 &gt;</div>'
                     f'<div class="flow">{essay_flow}</div></div>')
    return "".join(pages)


def build_problem_html(exam: MockExam, info: dict, footer: str = "") -> str:
    """학생용 문제지 단독 HTML(머리글+유의사항+2단 흐름)."""
    top = _header_block(exam, info) + _guidelines_block(exam, info)
    body = _problem_body(exam, info, teacher=False, top=top)
    title = info.get("exam_title") or f"{exam.blueprint.meta.name} 동형모의고사"
    return _wrap(title, body, footer_note=_footer_note(exam, footer))


def _quick_answer_body(exam: MockExam) -> str:
    """빠른 정답: 선택형은 번호-정답 격자, 서술형은 번호-정답 목록."""
    out = [f'<div class="page">{_section_banner("빠른 정답")}']
    # 선택형 격자(6칸씩)
    out.append('<div class="qa-sub">선택형</div><table class="qa-table"><tr>')
    per_row = 6
    for i, q in enumerate(exam.choice_questions):
        if i and i % per_row == 0:
            out.append('</tr><tr>')
        out.append(f'<td class="qn">{q.no}</td>'
                   f'<td class="qa">{html.escape(q.answer)}</td>')
    # 마지막 줄 빈칸 채우기
    rem = (-len(exam.choice_questions)) % per_row
    out.append('<td></td><td></td>' * rem)
    out.append('</tr></table>')
    # 서술형 목록
    if exam.essay_questions:
        out.append('<div class="qa-sub">서술형</div><div class="qa-essay">')
        for q in exam.essay_questions:
            out.append(f'<div class="qa-erow"><b>서술형 {q.no}.</b> '
                       f'{html.escape(q.answer)}</div>')
        out.append('</div>')
    out.append('</div>')
    return "".join(out)


def _answer_body(exam: MockExam) -> str:
    """정답해설지 본문(2단 흐름, 구조화 해설)."""
    body = [f'<div class="page">{_section_banner("정답 및 해설")}<div class="flow">']
    for q in exam.questions:
        label = TYPE_LABEL_KO.get(q.type, q.type)
        diff = DIFFICULTY_KO_REV.get(q.difficulty, "중")
        no = f"{q.no}번" if q.section == "choice" else f"서술형 {q.no}번"
        badge = f"{label} · {diff} · {_fmt_score(q.score)}점"
        body.append(f'<div class="ans-item"><div class="ans-head">'
                    f'<span class="ans-no">{no}</span>'
                    f'<span class="badge">{html.escape(badge)}</span></div>')
        body.append(f'<div class="ans-line"><span class="a">정답</span> '
                    f'<span class="ansval">{html.escape(_ko_normalize(q.answer))}</span></div>')
        if q.answer_notes:
            for n in q.answer_notes:
                body.append(f'<div class="ans-line">· {html.escape(_ko_normalize(n))}</div>')
        if q.explanation:
            body.append(f'<div class="exp">{_exp_html(q.explanation)}</div>')
        body.append('</div>')
    body.append('</div></div>')   # .flow, .page 닫기
    return "".join(body)


def build_answer_html(exam: MockExam, info: dict, footer: str = "") -> str:
    return _wrap("정답 및 해설", _answer_body(exam),
                 footer_note=_footer_note(exam, footer))


def _review_summary_body(exam: MockExam) -> str:
    """확인 권장 문항(⚠)만 PDF 맨 끝 별도 페이지에 모아 정리. 없으면 빈 문자열."""
    flagged = [q for q in exam.questions
               if isinstance(q.meta, dict) and q.meta.get("review_flag")]
    if not flagged:
        return ""
    rows = []
    for q in flagged:
        no = f"{q.no}번" if q.section == "choice" else f"서술형 {q.no}번"
        label = TYPE_LABEL_KO.get(q.type, q.type)
        reason = _ko_normalize(str(q.meta.get("review_flag", "")))
        rows.append(f'<tr><td class="rv-no">{no}</td><td>{html.escape(label)}</td>'
                    f'<td>{html.escape(reason)}</td></tr>')
    return (f'<div class="page">{_section_banner("검토 문항 (교사용)")}'
            '<div class="rev-intro">아래 문항은 정답·선지를 한 번 더 검토하시길 권장합니다. '
            '(교사용 참고 페이지 — 배부 시 제외)</div>'
            '<table class="rev-table"><tr><th>문항</th><th>유형</th><th>확인 사유</th></tr>'
            + "".join(rows) + '</table></div>')


# LLM 이 이따금 섞는 한자(漢字) → 한글 정규화(안전망). 시험지는 한글로만.
_HANJA = {
    "分析": "분석", "強調": "강조", "强調": "강조", "對照": "대조", "対照": "대조",
    "反對": "반대", "主張": "주장", "主語": "주어", "動詞": "동사", "名詞": "명사",
    "形容詞": "형용사", "副詞": "부사", "受動態": "수동태", "能動態": "능동태",
    "受動": "수동", "能動": "능동", "時制": "시제", "分詞": "분사",
    "過去分詞": "과거분사", "現在分詞": "현재분사", "關係詞": "관계사",
    "冠詞": "관사", "前置詞": "전치사", "接續詞": "접속사", "代名詞": "대명사",
    "複數": "복수", "單數": "단수", "一致": "일치", "語順": "어순", "態": "태",
    "文脈": "문맥", "論旨": "논지", "例示": "예시", "根據": "근거", "正答": "정답",
    "誤答": "오답", "文章": "문장", "單語": "단어", "語法": "어법", "解釋": "해석",
    "要旨": "요지", "主題": "주제", "比較": "비교", "省略": "생략", "強勢": "강세",
}
# 긴 항목이 먼저 매칭되도록 길이 내림차순으로 정렬
_HANJA_RE = re.compile("|".join(map(re.escape,
                                    sorted(_HANJA, key=len, reverse=True))))


def _ko_normalize(text: str) -> str:
    """한국어 텍스트에 섞인 흔한 한자를 한글로 치환."""
    return _HANJA_RE.sub(lambda m: _HANJA[m.group(0)], text or "")


# 해설을 줄 단위로 끊는 경계: (1) 라벨:, [오답 함정] 등, 문장 뒤 선지 시작 원문자
_EXP_LABEL = re.compile(r"(\[[^\]]{1,20}\]|\((?:\d)\)\s*[가-힣 ·]{0,14}[:：])")


def _exp_html(text: str) -> str:
    """긴 해설을 '정답근거 / 오답분석(선지별) / 핵심포인트'로 줄바꿈하고 라벨을 강조.

    LLM 해설의 '(1) 정답 근거:', '[오답 함정]', '[핵심 포인트]', 각 선지(①~⑤) 앞에서
    줄을 나눠 한 문단 벽글을 읽기 쉬운 목록형으로 만든다.
    """
    def esc(s: str) -> str:
        parts = []
        for seg in re.split(r"(<b>|</b>)", s):
            parts.append(seg if seg in ("<b>", "</b>") else html.escape(seg))
        return "".join(parts)

    t = _ko_normalize((text or "").strip())
    # 문장부호 뒤 '선지 시작' 원문자(뒤에 공백/따옴표가 오는 경우만) 앞에서 줄바꿈
    t = re.sub(r"(?<=[.。!?\]\)])\s+(?=[①②③④⑤][\s'\"“‘])", "\n", t)
    # 섹션 라벨 앞에서 줄바꿈
    t = re.sub(r"\s*(\[[^\]]{1,20}\]|\((?:\d)\)\s*[가-힣 ·]{0,14}[:：])", r"\n\1", t)

    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    out: list[str] = []
    for ln in lines:
        h = esc(ln)
        # 앞머리 라벨 강조([..] 는 오답 함정류=빨강, (N).. 는 파랑 헤더)
        m = _EXP_LABEL.match(ln)
        if m:
            lab = esc(m.group(1))
            cls = "lbl trap" if ln.startswith("[") and ("함정" in ln[:12] or "오답" in ln[:12]) else "lbl"
            rest = h[len(lab):]
            h = f'<span class="{cls}">{lab}</span>{rest}'
        else:
            # 선지 시작 원문자 강조
            h = re.sub(r"^([①②③④⑤])", r'<span class="ci">\1</span>', h)
        out.append(f'<div class="exp-line">{h}</div>')
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

    # 한 PDF에 4개 섹션: ① 학생용(문제) → ② 교사용(문제+해설, 정답 볼드)
    #                    → ③ 빠른 정답 → ④ 정답해설지
    student_top = _header_block(exam, info) + _guidelines_block(exam, info)
    teacher_top = _section_banner("교사용 · 문제 + 해설 (정답 볼드)")
    sections = [
        _problem_body(exam, info, teacher=False, top=student_top),
        _problem_body(exam, info, teacher=True, top=teacher_top),
        _quick_answer_body(exam),
        _answer_body(exam),
        _review_summary_body(exam),   # ⚠ 확인 권장 문항만 맨 끝 별도 페이지
    ]
    title = info.get("exam_title") or f"{exam.blueprint.meta.name} 동형모의고사"
    doc = _wrap(title, "".join(sections), footer_note=_footer_note(exam, footer))

    p_html = out / f"{stem}.html"
    p_html.write_text(doc, encoding="utf-8")
    result["problem_html"] = p_html
    # 재편집용 데이터(JSON) — 나중에 제목만 바꿔 재출력할 때 쓴다(API 재호출 없음).
    from .exam_io import save_exam_json
    result["exam_json"] = save_exam_json(exam, info, out / f"{stem}.exam.json")
    if to_pdf:
        _maybe_pdf(doc, out / f"{stem}.pdf", result, "problem_pdf")
    return result


def _maybe_pdf(html_str: str, path: Path, result: dict, key: str) -> None:
    try:
        from weasyprint import HTML
    except Exception:
        return
    HTML(string=html_str).write_pdf(str(path))
    result[key] = path
