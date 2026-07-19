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
@page {{ size: A4; margin: 15mm 14mm 16mm 14mm; }}
body {{ font-family: {_SERIF}; font-size: 10.3pt; line-height: 1.6; color:#000; margin:0; }}

/* 머리글 */
.exam-header {{ border:1.2px solid #000; padding:10px 14px 8px; margin-bottom:12px; }}
.exam-title {{ text-align:center; font-size:19pt; font-weight:700; letter-spacing:4px;
               margin-bottom:8px; }}
.hrow {{ display:flex; align-items:center; justify-content:space-between; font-size:11pt; }}
.hrow .center {{ font-weight:700; }}
.code-pill {{ border:1px solid #000; border-radius:999px; padding:2px 12px; font-size:9.5pt; }}
.exam-time {{ text-align:center; font-size:9pt; color:#333; margin-top:5px; }}

/* 유의사항(머리글 박스 아래) */
.guidelines {{ break-inside:avoid; font-size:9pt; line-height:1.5; margin-bottom:10px;
               padding-bottom:6px; border-bottom:0.6px solid #999; }}
.g-item {{ padding-left:13px; text-indent:-13px; margin:2px 0; }}
.g-item .cont {{ display:block; padding-left:13px; text-indent:0; }}

/* 2단 */
.columns {{ column-count:2; column-gap:24px; column-rule:0.6px solid #cfcfcf; }}
.section-div {{ column-span:all; font-weight:700; margin:6px 0 8px; }}

/* 문항 */
.q {{ break-inside:avoid; margin-bottom:14px; }}
.q-head {{ font-weight:700; }}
.q-head .score {{ font-weight:400; font-size:9pt; color:#333; }}
.passage {{ text-align:justify; margin:6px 0; }}
.para {{ text-align:justify; margin:5px 0; }}
.box {{ border:1px solid #000; padding:7px 10px; margin:6px 0; text-align:justify; }}
.choices {{ margin:5px 0 0 2px; }}
.choices div {{ margin:1.5px 0; }}
u {{ text-underline-offset:2px; }}

/* 보기 박스 */
.bogi {{ border:1px solid #000; padding:6px 10px; margin:6px 0; text-align:center; }}
.bogi .label {{ font-weight:700; margin-bottom:2px; }}
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
    return f'<div class="passage">{_safe(text)}</div>'


def _render_bogi(q: Question) -> str:
    bogi = q.meta.get("bogi")
    blank_ko = q.meta.get("blank_ko")
    out = []
    if blank_ko:
        out.append(f'<div class="blank-ko">밑줄: {html.escape(blank_ko)}</div>')
    if bogi:
        words = " / ".join(html.escape(w) for w in bogi)
        out.append(f'<div class="bogi"><div class="label">&lt; 보기 &gt;</div>{words}</div>')
    return "".join(out)


def _q_html(q: Question) -> str:
    parts = [f'<div class="q"><div class="q-head">{q.no}. {html.escape(q.stem)} '
             f'<span class="score">[{_fmt_score(q.score)}점]</span></div>']
    parts.append(_render_passage(q))
    if q.section == "essay":
        parts.append(_render_bogi(q))
    if q.choices:
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


def _footer_block(exam: MockExam, footer: str) -> str:
    note = footer or "이 시험문제는 은아T영어연구소의 저작물입니다."
    m = exam.blueprint.meta
    page_line = (f"{m.grade}학년 {m.subject or '공통영어1'} "
                 f"( 1 ) / ( {m.pages} ) 페이지 중")
    return (f'<div class="footer">{html.escape(note)}<br>{html.escape(page_line)}</div>')


# ---------------------------------------------------------------------------
# 문제지 / 정답지
# ---------------------------------------------------------------------------
def build_problem_html(exam: MockExam, info: dict, footer: str = "") -> str:
    # 유의사항은 2단 레이아웃의 '왼쪽 단(첫째 열)' 맨 위에만 배치
    body = [_header_block(exam, info), '<div class="columns">',
            _guidelines_block(exam, info)]
    for q in exam.choice_questions:
        body.append(_q_html(q))
    body.append('<div class="section-div">&lt; 서 술 형 &gt;</div>')
    for q in exam.essay_questions:
        body.append(_q_html(q))
    body.append('</div>')
    body.append(_footer_block(exam, footer))
    title = info.get("exam_title") or f"{exam.blueprint.meta.name} 동형모의고사"
    return _wrap(title, "".join(body))


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
    body.append(_footer_block(exam, footer))
    return _wrap("정답 및 해설", "".join(body))


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


def _wrap(title: str, body: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<title>{html.escape(title)}</title><style>{_CSS}</style></head>'
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
