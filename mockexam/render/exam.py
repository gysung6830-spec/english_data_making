"""조판 (§6): 좌우 2단 문제지 + 정답·해설지.

- HTML 을 항상 만들고(브라우저 미리보기 가능), WeasyPrint 있으면 PDF 도 생성.
- 2단은 CSS column 기반(간단). 페이지 넘김이 크게 문제되면 table 2단으로 확장 가능.
"""
from __future__ import annotations

import html
from pathlib import Path

from ..core.models import MockExam, Question

_CSS = """
* { box-sizing: border-box; }
body { font-family: 'Malgun Gothic','Noto Sans KR','Nanum Gothic',sans-serif;
       font-size: 10.2pt; line-height: 1.5; color:#111; margin:0; }
.header { text-align:center; border-bottom:2px solid #222; padding:8px 0; margin-bottom:10px; }
.header .title { font-size:14pt; font-weight:700; }
.header .sub { font-size:9pt; color:#555; }
.columns { column-count:2; column-gap:22px; }
.q { break-inside: avoid; margin-bottom:12px; }
.q .no { font-weight:700; }
.q .stem { font-weight:600; }
.passage { border:1px solid #bbb; background:#fafafa; padding:6px 8px; margin:5px 0;
           white-space:pre-wrap; font-size:9.6pt; }
.choices { margin:3px 0 0 4px; }
.choices div { margin:1px 0; }
u { text-underline-offset:2px; }
.section-title { font-weight:700; font-size:11pt; border-left:4px solid #333;
                 padding-left:6px; margin:10px 0 6px; column-span:all; }
.footer { text-align:center; font-size:8.5pt; color:#666; margin-top:8px; }
.ans { break-inside:avoid; margin-bottom:8px; font-size:9.6pt; }
.ans .k { font-weight:700; color:#b00; }
.trap { color:#b00; }
"""


def _q_html(q: Question) -> str:
    parts = [f'<div class="q"><div><span class="no">{q.no}.</span> '
             f'<span class="stem">{html.escape(q.stem)}</span> '
             f'<span style="color:#888">[{q.score}점]</span></div>']
    if q.passage_text and not q.passage_text.startswith("(지문 부족"):
        # <u> 태그는 살리고 나머지는 이스케이프
        parts.append(f'<div class="passage">{_safe_passage(q.passage_text)}</div>')
    if q.choices:
        parts.append('<div class="choices">')
        for c in q.choices:
            parts.append(f'<div>{c.label} {html.escape(c.text)}</div>')
        parts.append('</div>')
    parts.append('</div>')
    return "".join(parts)


def _safe_passage(text: str) -> str:
    """<u>...</u> 밑줄과 ①~⑤ 마커만 허용하고 나머지는 이스케이프."""
    import re
    token = re.split(r'(<u>|</u>)', text)
    out = []
    for t in token:
        if t in ("<u>", "</u>"):
            out.append(t)
        else:
            out.append(html.escape(t))
    return "".join(out)


def build_problem_html(exam: MockExam, header: str = "", footer: str = "") -> str:
    bp = exam.blueprint
    title = header or f"{bp.meta.name} {bp.meta.grade}학년 영어 동형모의고사 ({exam.form}형)"
    sub = (f"{bp.meta.subject} · {bp.meta.time_min}분 · {bp.meta.total_score}점 · "
           f"선택형 {len(exam.choice_questions)} / 서술형 {len(exam.essay_questions)}"
           f"{' · 표준골격' if not bp.meta.learned else ''}")
    body = ['<div class="header">', f'<div class="title">{html.escape(title)}</div>',
            f'<div class="sub">{html.escape(sub)}</div></div>']
    body.append('<div class="columns">')
    body.append('<div class="section-title">[선택형]</div>')
    for q in exam.choice_questions:
        body.append(_q_html(q))
    body.append('<div class="section-title">[서술형]</div>')
    for q in exam.essay_questions:
        body.append(_q_html(q))
    body.append('</div>')
    if footer:
        body.append(f'<div class="footer">{html.escape(footer)}</div>')
    return _wrap(title, "".join(body))


def build_answer_html(exam: MockExam, header: str = "") -> str:
    bp = exam.blueprint
    title = (header or f"{bp.meta.name} {bp.meta.grade}학년 동형모의고사") + " — 정답·해설"
    body = ['<div class="header">', f'<div class="title">{html.escape(title)}</div></div>']
    for label, qs in (("선택형", exam.choice_questions), ("서술형", exam.essay_questions)):
        body.append(f'<div class="section-title">[{label} 정답·해설]</div>')
        for q in qs:
            ans = html.escape(q.answer)
            body.append(f'<div class="ans"><span class="k">{q.no}. 정답: {ans}</span>')
            if q.answer_notes:
                for n in q.answer_notes:
                    body.append(f'<div>· {html.escape(n)}</div>')
            if q.explanation:
                body.append(f'<div>{html.escape(q.explanation)}</div>')
            body.append('</div>')
    return _wrap(title, "".join(body))


def _wrap(title: str, body: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<title>{html.escape(title)}</title><style>{_CSS}</style></head>'
            f'<body>{body}</body></html>')


def render_exam(exam: MockExam, out_dir: str | Path, form: str = "A",
                header: str = "", footer: str = "",
                answer_key: str = "end", to_pdf: bool = True) -> dict[str, Path]:
    """문제지/정답지 HTML(+PDF) 생성. 반환: {'problem_html':..., 'problem_pdf':...}."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result: dict[str, Path] = {}

    prob = build_problem_html(exam, header, footer)
    ans = build_answer_html(exam, header)

    if answer_key == "end":
        # 정답을 문제지 맨 뒤에 붙인다.
        prob = prob.replace("</body></html>",
                            ans.split("<body>")[1].split("</body>")[0] + "</body></html>")

    p_html = out / f"mock_form_{form}.html"
    p_html.write_text(prob, encoding="utf-8")
    result["problem_html"] = p_html

    if answer_key == "separate":
        a_html = out / f"mock_form_{form}_answers.html"
        a_html.write_text(ans, encoding="utf-8")
        result["answers_html"] = a_html

    if to_pdf:
        _maybe_pdf(prob, out / f"mock_form_{form}.pdf", result, "problem_pdf")
        if answer_key == "separate":
            _maybe_pdf(ans, out / f"mock_form_{form}_answers.pdf", result, "answers_pdf")
    return result


def _maybe_pdf(html_str: str, path: Path, result: dict, key: str) -> None:
    try:
        from weasyprint import HTML
    except Exception:
        return  # WeasyPrint 미설치 → HTML 만 제공
    HTML(string=html_str).write_pdf(str(path))
    result[key] = path
