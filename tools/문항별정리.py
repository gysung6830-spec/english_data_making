#!/usr/bin/env python3
"""생성 결과를 '문항 번호 순' 한 장짜리 HTML 로 정리한다 (API 미사용).

시험지 PDF 는 학생·교사가 쓰는 물건이라 '몇 번이 어떤 유형이고 정답이 무엇인지'를
한눈에 훑기 어렵다. 이 도구는 같은 결과를 **문항별 점검표**로 다시 편다:
지문 한 번 → 16행 요약표(번호·유형·정답) → 문항별 상세(발문·선지·정답·해설).

사용:
    python tools/문항별정리.py                 # 데모 지문으로 샘플 만들기
    python tools/문항별정리.py 결과.json        # 웹앱이 저장한 분석 결과로 만들기
    python tools/문항별정리.py 결과.json -o 파일.html

내보낸 HTML 은 그대로 열어 봐도 되고, 인쇄해서 검토용으로 써도 된다.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exam.merged import (  # noqa: E402
    MERGED_LABELS,
    MERGED_ORDER,
    MERGED_PROMPTS,
    demo_passages_merged,
)

# 지문을 새로 써서 내거나 본문을 손대는 유형 — 상세에서 본문을 함께 보여 준다.
_SHOW_BODY = {
    "grammar": "이 문항에 쓰인 지문 (다시 쓴 것)",
    "grammar_count": "이 문항에 쓰인 지문 (다시 쓴 것)",
    "irrelevant": "이 문항에 쓰인 지문 (한 문장이 새로 끼워져 있음)",
    "pair_odd": "이 문항에 쓰인 지문 (ⓐ~ⓔ 밑줄)",
    "vocab": "이 문항에 쓰인 지문 (①~⑤ 밑줄)",
    "vocab_2": "이 문항에 쓰인 지문 (①~⑤ 밑줄)",
    "vocab_3": "이 문항에 쓰인 지문 (①~⑤ 밑줄)",
    "D": "제시된 낱말",
    "E": "요약문",
}


def _txt(h: str) -> str:
    """조판 HTML → 평문(태그 제거·공백 정리·엔티티 복원)."""
    h = re.sub(r"<br\s*/?>", " ", h or "")
    t = re.sub(r"<[^>]+>", " ", h)
    t = (t.replace("&#39;", "'").replace("&nbsp;", " ")
          .replace("&quot;", '"').replace("&amp;", "&")
          .replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", t).strip()


def collect(passage) -> list[dict]:
    """Passage → 문항 번호 순 항목 목록."""
    rows = []
    for no, t in enumerate(MERGED_ORDER, 1):
        if t not in passage.q:
            continue
        q, a = passage.q[t], passage.a[t]
        body = re.search(r'<div class="passage[^"]*">(.*?)</div>', q, re.S)
        given = re.search(r'<div class="given-sentence">(.*?)</div>', q, re.S)
        rows.append({
            "no": no, "key": t,
            "label": MERGED_LABELS[t], "prompt": MERGED_PROMPTS[t],
            "choices": [_txt(x) for x in re.findall(r"<li>(.*?)</li>", q, re.S)],
            "marks": re.findall(r'<span class="cnum">(.)</span>\s*<u>(.*?)</u>', q),
            "segs": [(L, _txt(s)) for L, s
                     in re.findall(r'seg-label">\((.)\)</span>(.*?)</div>', q, re.S)],
            "given": _txt(given.group(1)) if given else "",
            "body": _txt(body.group(1)) if body else "",
            "answer": _txt(re.search(r'answer-key">(.*?)</span>', a).group(1)),
            "reasons": [_txt(x) for x
                        in re.findall(r'<p class="(?:reason|wrong)">(.*?)</p>', a, re.S)],
            "flags": list(passage.flags.get(t, [])),
        })
    return rows


# ---------------------------------------------------------------------------
# 조판
# ---------------------------------------------------------------------------
_CIRC = "①②③④⑤⑥⑦⑧"
_E = html.escape


def _en(s: str) -> str:
    """영어 문항 내용 — 시험지 활자(세리프)로."""
    return f'<span class="en">{_E(s)}</span>'


def _has_hangul(s: str) -> bool:
    return bool(re.search(r"[가-힣]", s))


def _choice_list(row: dict) -> str:
    if not row["choices"]:
        return ""
    lis = []
    for i, c in enumerate(row["choices"], 1):
        c = re.sub(r"^[①-⑧]\s*", "", c)
        inner = _E(c) if _has_hangul(c) else _en(c)
        cls = " is-answer" if _CIRC[i - 1] in row["answer"] else ""
        lis.append(f'<li class="choice{cls}"><span class="cnum">{_CIRC[i - 1]}</span>'
                   f'<span class="ctext">{inner}</span></li>')
    return f'<ol class="choices">{"".join(lis)}</ol>'


def _mark_list(row: dict) -> str:
    if not row["marks"]:
        return ""
    chips = "".join(f'<span class="mark"><i>{_E(n)}</i>{_E(w)}</span>'
                    for n, w in row["marks"])
    return f'<div class="marks">{chips}</div>'


def _seg_list(row: dict) -> str:
    if not row["segs"]:
        return ""
    items = "".join(f'<div class="seg"><span class="seglabel">({_E(L)})</span>'
                    f'<p>{_en(s)}</p></div>' for L, s in row["segs"])
    return f'<div class="segs">{items}</div>'


def _detail_body(row: dict) -> str:
    cap = _SHOW_BODY.get(row["key"])
    if not cap or not row["body"]:
        return ""
    return (f'<details class="bodybox"><summary>{_E(cap)}</summary>'
            f'<p class="passage">{_en(row["body"])}</p></details>')


def _row_html(row: dict) -> str:
    parts = [f'<p class="prompt">{_E(row["prompt"])}</p>']
    if row["given"]:
        parts.append(f'<p class="given"><span class="glabel">주어진 문장</span>'
                     f'{_en(row["given"])}</p>')
    parts.append(_mark_list(row))
    parts.append(_seg_list(row))
    parts.append(_choice_list(row))
    parts.append(_detail_body(row))
    if row["flags"]:
        fl = "".join(f"<li>{_E(f)}</li>" for f in row["flags"])
        parts.append(f'<ul class="flags">{fl}</ul>')
    if row["reasons"]:
        rs = "".join(f"<li>{_E(r)}</li>" for r in row["reasons"])
        parts.append(f'<ul class="reasons">{rs}</ul>')
    return (
        f'<article class="item" id="q{row["no"]}">'
        f'<div class="gutter"><span class="qno">{row["no"]}</span></div>'
        f'<div class="detail">'
        f'<h3><span class="type">{_E(row["label"])}</span>'
        f'<span class="ans">{_E(row["answer"])}</span></h3>'
        f'{"".join(x for x in parts if x)}'
        f"</div></article>"
    )


_CSS = """
:root{
  --paper:#FDFDFB; --ink:#17212E; --muted:#5A6674; --rule:#E3E1DA;
  --tint:#F1F2EF; --mark:#C8352B; --markbg:#FBEDEB;
}
:root:not([data-theme="light"]){ }
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#14181D; --ink:#E7E9E6; --muted:#98A2AC; --rule:#282F37;
    --tint:#1A1F26; --mark:#F0796C; --markbg:#2B1E1E;
  }
}
:root[data-theme="dark"]{
  --paper:#14181D; --ink:#E7E9E6; --muted:#98A2AC; --rule:#282F37;
  --tint:#1A1F26; --mark:#F0796C; --markbg:#2B1E1E;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"Noto Sans KR","Apple SD Gothic Neo",system-ui,sans-serif;
  font-size:15px; line-height:1.7; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:820px; margin:0 auto; padding:48px 24px 96px}
.en{font-family:"Source Serif 4",Georgia,"Times New Roman",serif}

/* 머리말 */
header{border-bottom:2px solid var(--ink); padding-bottom:20px; margin-bottom:28px}
.eyebrow{font-size:12px; letter-spacing:.14em; color:var(--muted); margin:0 0 8px}
h1{font-family:"Noto Serif KR",serif; font-weight:600; font-size:30px;
   line-height:1.35; margin:0 0 10px; text-wrap:balance}
.sub{color:var(--muted); margin:0; font-size:14px}
.meta{display:flex; flex-wrap:wrap; gap:8px 18px; margin-top:14px;
      font-size:13px; color:var(--muted)}
.meta b{color:var(--ink); font-weight:700}

h2{font-family:"Noto Serif KR",serif; font-weight:600; font-size:19px;
   margin:44px 0 14px; padding-bottom:8px; border-bottom:1px solid var(--rule)}

/* 정본 지문 */
.source{background:var(--tint); border-radius:6px; padding:18px 20px; margin:0}
.source p{margin:0; font-family:"Source Serif 4",Georgia,serif; font-size:15.5px;
          line-height:1.85}

/* 요약표 */
.tablewrap{overflow-x:auto}
table{border-collapse:collapse; width:100%; font-size:14px}
th,td{text-align:left; padding:8px 10px; border-bottom:1px solid var(--rule);
      vertical-align:top}
th{font-size:12px; letter-spacing:.08em; color:var(--muted); font-weight:500;
   border-bottom:1px solid var(--ink); white-space:nowrap}
td.n{font-variant-numeric:tabular-nums; color:var(--muted); width:3.2em;
     text-align:right; padding-right:14px}
td.t{font-weight:700; white-space:nowrap}
td.a{color:var(--mark); font-weight:700; white-space:nowrap; width:5em}
td.d{color:var(--muted)}
tbody tr:hover{background:var(--tint)}
a.q{color:inherit; text-decoration:none}
a.q:hover{text-decoration:underline}

/* 문항 상세 */
.item{display:grid; grid-template-columns:64px 1fr; gap:0 18px;
      padding:26px 0; border-bottom:1px solid var(--rule)}
.item:last-child{border-bottom:none}
.qno{font-variant-numeric:tabular-nums; font-family:"Noto Serif KR",serif;
     font-size:30px; font-weight:600; color:var(--rule); line-height:1}
.detail h3{display:flex; align-items:baseline; gap:12px; margin:0 0 10px;
           font-size:16px; font-weight:700}
.type{font-family:"Noto Serif KR",serif; font-weight:600}
.ans{margin-left:auto; color:var(--mark); background:var(--markbg);
     border-radius:4px; padding:1px 9px; font-size:14px; font-weight:700;
     white-space:nowrap}
.prompt{margin:0 0 12px; color:var(--muted); font-size:14px}
.given{margin:0 0 12px; padding:10px 14px; background:var(--tint);
       border-radius:5px; font-size:14.5px}
.glabel{display:block; font-size:11px; letter-spacing:.1em; color:var(--muted);
        margin-bottom:4px}

.marks{display:flex; flex-wrap:wrap; gap:7px; margin:0 0 12px}
.mark{font-family:"Source Serif 4",Georgia,serif; font-size:14.5px;
      border:1px solid var(--rule); border-radius:4px; padding:2px 9px 2px 5px}
.mark i{font-style:normal; color:var(--muted); margin-right:5px}

.segs{display:flex; flex-direction:column; gap:8px; margin:0 0 12px}
.seg{display:grid; grid-template-columns:2.4em 1fr; gap:6px;
     background:var(--tint); border-radius:5px; padding:9px 12px}
.seglabel{font-weight:700; color:var(--muted)}
.seg p{margin:0; font-family:"Source Serif 4",Georgia,serif; font-size:14.5px}

.choices{list-style:none; margin:0 0 12px; padding:0;
         display:flex; flex-direction:column; gap:5px}
.choice{display:grid; grid-template-columns:1.7em 1fr; gap:4px; font-size:14.5px}
.choice .cnum{color:var(--muted)}
.choice.is-answer .ctext{color:var(--mark); font-weight:600}
.choice.is-answer .cnum{color:var(--mark)}

.bodybox{margin:0 0 12px; font-size:14px}
.bodybox summary{cursor:pointer; color:var(--muted); font-size:13px;
                 padding:4px 0}
.bodybox summary:hover{color:var(--ink)}
.bodybox .passage{margin:8px 0 0; background:var(--tint); border-radius:5px;
                  padding:12px 14px; line-height:1.8}

.reasons,.flags{margin:0; padding-left:18px; font-size:13.5px; color:var(--muted)}
.reasons li,.flags li{margin:3px 0}
.flags{color:var(--mark)}

footer{margin-top:48px; padding-top:18px; border-top:1px solid var(--rule);
       font-size:12.5px; color:var(--muted)}
:focus-visible{outline:2px solid var(--mark); outline-offset:2px}
@media (max-width:600px){
  .wrap{padding:32px 16px 64px}
  .item{grid-template-columns:44px 1fr; gap:0 12px}
  .qno{font-size:24px}
  h1{font-size:24px}
}
"""


def render(title: str, rows: list[dict], source: str, note: str = "") -> str:
    trs = "".join(
        f'<tr><td class="n">{r["no"]}</td>'
        f'<td class="t"><a class="q" href="#q{r["no"]}">{_E(r["label"])}</a></td>'
        f'<td class="a">{_E(r["answer"])}</td>'
        f'<td class="d">{_E(r["prompt"])}</td></tr>' for r in rows)
    items = "".join(_row_html(r) for r in rows)
    flagged = sum(1 for r in rows if r["flags"])
    return f"""<title>변형문제 문항별 점검표</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap">
<style>{_CSS}</style>
<div class="wrap">
<header>
  <p class="eyebrow">변형문제 통합본 · 문항별 점검표</p>
  <h1>{_E(title)}</h1>
  <p class="sub">{_E(note) if note else "지문 하나에서 뽑은 문항을 번호 순으로 폈습니다."}</p>
  <div class="meta">
    <span><b>{len(rows)}</b>문항</span>
    <span>배열 <b>수능 순서</b></span>
    <span>출제 수준 <b>수능 표준</b></span>
    <span>확인 권장 <b>{flagged}</b>건</span>
  </div>
</header>

<h2>정본 지문</h2>
<div class="source"><p>{_E(source)}</p></div>

<h2>한눈에 보기</h2>
<div class="tablewrap"><table>
<thead><tr><th class="n">번호</th><th>유형</th><th>정답</th><th>발문</th></tr></thead>
<tbody>{trs}</tbody>
</table></div>

<h2>문항별 상세</h2>
{items}

<footer>정답은 붉게 표시했습니다. ‘이 문항에 쓰인 지문’을 펼치면 밑줄·교체가 실제로
어떻게 들어갔는지 볼 수 있습니다. 어법 두 문항은 지문을 다시 써서 내므로 정본과 다릅니다.</footer>
</div>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="생성 결과를 문항별 HTML 로 정리")
    ap.add_argument("json", nargs="?", help="웹앱이 저장한 분석 결과(.json). 없으면 데모")
    ap.add_argument("-o", "--out", default="문항별정리.html")
    ap.add_argument("-i", "--index", type=int, default=0, help="여러 지문 중 몇 번째(0부터)")
    args = ap.parse_args()

    if args.json:
        from exam import serialize
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        parts, _ = serialize.load_parts(data)
        passages = parts[0]["passages"]
        note = parts[0].get("header_note", "")
    else:
        passages = demo_passages_merged()
        note = "무료 미리보기(데모 지문)로 만든 샘플입니다 — API 를 쓰지 않았습니다."

    if not passages:
        print("지문이 없습니다.", file=sys.stderr)
        return 1
    p = passages[min(args.index, len(passages) - 1)]
    rows = collect(p)
    src = _txt(p.q[MERGED_ORDER[0]].split("</div>")[0])   # 주제 문항의 본문 = 정본
    out = Path(args.out)
    out.write_text(render(p.title, rows, src, note), encoding="utf-8")
    print(f"{out}  ({len(rows)}문항)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
