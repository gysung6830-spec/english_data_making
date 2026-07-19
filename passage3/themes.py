"""디자인 테마 CSS 3종.

- modern   : 확정 테마. 무채색 포인트 + 문장마다 연한 구분선.
             페이지 규칙(break-before/inside)과 auto-fit 축소 클래스 포함.
- textbook : 대안(교재형).
- middle   : 대안(중등부형).

렌더러는 theme 문자열로 CSS를 선택한다. theme="" 이면 기본(modern과 동일한
페이지 규칙을 갖는 최소 CSS)을 쓴다.
"""
from __future__ import annotations

# 한글 폰트 스택 (설치 환경 대비 폭넓게 지정)
FONT_STACK = (
    "'Noto Sans CJK KR','Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo',"
    "'AppleGothic','Nanum Gothic',sans-serif"
)
SERIF_STACK = (
    "'Noto Serif CJK KR','Noto Serif KR','Batang','Apple SD Gothic Neo',serif"
)

# ── 페이지 배치 규칙 (모든 테마 공통으로 주입) ─────────────────
# .passage 자체엔 break-inside:avoid 를 걸지 않는다 → 큰 지문이 빈 페이지를
# 만드는 것을 방지. 대신 문장/표 행 단위로만 잘림을 막는다.
PAGE_RULES = """
@page { size: A4; margin: 20mm; }
html, body { margin: 0; padding: 0; }
.passage + .passage { break-before: page; }
.sent      { break-inside: avoid; }
tr.sent    { break-inside: avoid; }
.p-label   { break-after: avoid; }
.p-title   { break-after: avoid; }
"""

# ── auto-fit 축소 클래스 (본문/표 공통) ───────────────────────
AUTOFIT_RULES = """
/* 1단계 축소 */
.passage.compact  .en { font-size:12.7px; line-height:1.42; }
.passage.compact  .ko { font-size:11.2px; line-height:1.38; }
.passage.compact  .sent { margin-bottom:6px; padding-bottom:5px; }
.passage.compact  td { padding:5px 8px; font-size:12.7px; }
/* 2단계 축소 */
.passage.compact2 .en { font-size:12px;   line-height:1.34; }
.passage.compact2 .ko { font-size:10.6px; line-height:1.3; }
.passage.compact2 .sent { margin-bottom:4px; padding-bottom:3px; }
.passage.compact2 td { padding:3px 6px; font-size:12px; }
"""


def _modern_css() -> str:
    return f"""
{PAGE_RULES}
body {{
  font-family: {FONT_STACK};
  color: #1c1c1e;
  font-size: 13.5px;
  line-height: 1.55;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.doc-header {{
  text-align: right;
  font-size: 10.5px;
  color: #8a8a8e;
  letter-spacing: .2px;
  margin-bottom: 10px;
  border-bottom: 1px solid #ececee;
  padding-bottom: 4px;
}}
.passage {{ margin: 0; }}
.p-label {{
  display: inline-block;
  font-size: 10.5px;
  font-weight: 600;
  color: #6e6e73;
  background: #f2f2f4;
  border-radius: 4px;
  padding: 2px 8px;
  margin-bottom: 4px;
  letter-spacing: .2px;
}}
.p-title {{
  font-size: 15px;
  font-weight: 700;
  color: #1c1c1e;
  margin: 2px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #1c1c1e;
}}
/* 한줄해석 / 한줄영어 : 문장 블록 */
.sent {{
  margin-bottom: 10px;
  padding-bottom: 9px;
  border-bottom: 1px solid #f0f0f2;   /* 문장마다 연한 구분선 */
}}
.sent:last-child {{ border-bottom: none; }}
.sent .en {{
  font-size: 13.5px;
  line-height: 1.5;
  color: #1c1c1e;
}}
.sent .num {{
  color: #a1a1a6;
  font-weight: 600;
  margin-right: 5px;
}}
.sent .ko {{
  display: block;
  margin-top: 5px;
  font-size: 12px;
  line-height: 1.45;
  color: #48484a;
  background: #f5f5f7;               /* 회색박스 */
  border-radius: 5px;
  padding: 6px 9px;
}}
/* 좌지문 우해석 : 2단 표 */
table.two-col {{
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}}
table.two-col td {{
  vertical-align: top;
  padding: 8px 10px;
  border-bottom: 1px solid #f0f0f2;
  font-size: 13px;
  line-height: 1.5;
}}
table.two-col td.col-en {{ width: 55%; color: #1c1c1e; }}
table.two-col td.col-ko {{
  width: 45%;
  color: #48484a;
  background: #f8f8fa;
}}
table.two-col td .num {{ color: #a1a1a6; font-weight: 600; margin-right: 5px; }}
{AUTOFIT_RULES}
"""


def _textbook_css() -> str:
    return f"""
{PAGE_RULES}
body {{
  font-family: {SERIF_STACK};
  color: #20242c;
  font-size: 13.5px;
  line-height: 1.6;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.doc-header {{ text-align:right; font-size:10.5px; color:#7a8290; margin-bottom:10px; }}
.p-label {{
  font-size:10.5px; font-weight:700; color:#2a5db0;
  border:1px solid #2a5db0; border-radius:3px; padding:2px 8px;
}}
.p-title {{
  font-size:16px; font-weight:700; color:#20242c;
  margin:6px 0 12px 0; padding:6px 0; border-top:2px solid #2a5db0;
  border-bottom:2px solid #2a5db0;
}}
.sent {{ margin-bottom:10px; padding-bottom:9px; border-bottom:1px dotted #cfd6e0; }}
.sent:last-child {{ border-bottom:none; }}
.sent .num {{ color:#2a5db0; font-weight:700; margin-right:5px; }}
.sent .ko {{
  display:block; margin-top:5px; font-size:12px; color:#3a4048;
  background:#eef3fb; border-left:3px solid #2a5db0; padding:6px 9px;
}}
table.two-col {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
table.two-col td {{ vertical-align:top; padding:8px 10px; border:1px solid #cfd6e0; font-size:13px; }}
table.two-col td.col-en {{ width:55%; }}
table.two-col td.col-ko {{ width:45%; background:#eef3fb; }}
table.two-col td .num {{ color:#2a5db0; font-weight:700; margin-right:5px; }}
{AUTOFIT_RULES}
"""


def _middle_css() -> str:
    return f"""
{PAGE_RULES}
body {{
  font-family: {FONT_STACK};
  color: #2b2b2b;
  font-size: 14.5px;
  line-height: 1.7;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.doc-header {{ text-align:right; font-size:11px; color:#8a8a8a; margin-bottom:10px; }}
.p-label {{
  font-size:11px; font-weight:700; color:#fff;
  background:#ff8c42; border-radius:12px; padding:3px 10px;
}}
.p-title {{ font-size:17px; font-weight:800; color:#2b2b2b; margin:6px 0 14px 0; }}
.sent {{ margin-bottom:12px; padding-bottom:10px; border-bottom:2px dashed #ffe0c2; }}
.sent:last-child {{ border-bottom:none; }}
.sent .num {{
  display:inline-block; min-width:20px; text-align:center;
  color:#fff; background:#ff8c42; border-radius:50%;
  font-size:11px; font-weight:700; margin-right:6px; padding:1px 0;
}}
.sent .ko {{
  display:block; margin-top:6px; font-size:12.5px; color:#555;
  background:#fff6ee; border-radius:8px; padding:7px 10px;
}}
table.two-col {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
table.two-col td {{ vertical-align:top; padding:9px 11px; border-bottom:2px dashed #ffe0c2; font-size:14px; }}
table.two-col td.col-en {{ width:55%; }}
table.two-col td.col-ko {{ width:45%; background:#fff6ee; }}
table.two-col td .num {{ color:#ff8c42; font-weight:700; margin-right:5px; }}
{AUTOFIT_RULES}
"""


_THEMES = {
    "modern": _modern_css,
    "textbook": _textbook_css,
    "middle": _middle_css,
}


def get_css(theme: str = "") -> str:
    """theme 문자열 → CSS. 빈 문자열/미지원이면 modern."""
    key = (theme or "modern").strip().lower()
    builder = _THEMES.get(key, _modern_css)
    return builder()
