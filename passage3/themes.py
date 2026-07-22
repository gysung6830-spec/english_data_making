"""디자인 테마 CSS 3종.

- modern   : 확정 테마(참고 디자인 반영). 나눔명조 세리프, 우측 상단 머리글 +
             전체폭 구분선, 제목 왼쪽 세로 강조막대, 문장마다 연한 구분선.
             페이지 규칙(break-before/inside)과 auto-fit 축소 클래스 포함.
- textbook : 대안(교재형, 파란 포인트).
- middle   : 대안(중등부형, 주황 포인트).

렌더러는 theme 문자열로 CSS를 선택한다. theme="" 이면 modern.
"""
from __future__ import annotations

# 나눔명조 우선. 시스템에 없을 때를 대비해 Google Fonts @import도 함께 건다
# (오프라인이면 시스템 NanumMyeongjo / Noto Serif 로 폴백).
FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Nanum+Myeongjo:wght@400;700;800&display=swap');\n"
)
SERIF_STACK = (
    "'NanumMyeongjo','Nanum Myeongjo','나눔명조',"
    "'Noto Serif CJK KR','Noto Serif KR','Batang',serif"
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
.p-head    { break-after: avoid; }
"""

# ── auto-fit 축소 클래스 (본문/표 공통) ───────────────────────
AUTOFIT_RULES = """
/* 1단계 축소 */
.passage.compact  .en { font-size:12.7px; line-height:1.5; }
.passage.compact  .ko { font-size:10.5px; line-height:1.45; }
.passage.compact  .sent { margin-bottom:10px; padding-bottom:10px; }
.passage.compact  .ko-box { margin-top:6px; padding:6px 10px; }
.passage.compact  td { padding:8px 12px 8px 0; font-size:12.5px; }
.passage.compact  .p-head { margin-bottom:14px; }
/* 2단계 축소 */
.passage.compact2 .en { font-size:12px;   line-height:1.42; }
.passage.compact2 .ko { font-size:10px; line-height:1.38; }
.passage.compact2 .sent { margin-bottom:7px; padding-bottom:7px; }
.passage.compact2 .ko-box { margin-top:5px; padding:5px 9px; }
.passage.compact2 td { padding:6px 10px 6px 0; font-size:12px; }
.passage.compact2 .p-head { margin-bottom:11px; }
.passage.compact  .vocab { margin-top:12px; padding:8px 12px; }
.passage.compact  .vocab-item { font-size:10.5px; }
.passage.compact2 .vocab { margin-top:9px; padding:6px 10px; }
.passage.compact2 .vocab-item { font-size:10px; }
"""

# ── 하단 어휘 리스트 박스 (모든 테마 공통) ────────────────────
VOCAB_RULES = """
.vocab {
  margin-top: 18px;
  border: 1px solid #d9d9dd;
  border-radius: 6px;
  padding: 10px 14px;
  break-inside: avoid;
}
.vocab-title {
  font-size: 11.5px;
  font-weight: 700;
  color: #6e6e73;
  letter-spacing: .3px;
  margin-bottom: 8px;
}
.vocab-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px 22px;
}
.vocab-item {
  font-size: 11px;
  line-height: 1.45;
  break-inside: avoid;
  display: flex;
  gap: 7px;
  align-items: baseline;
}
.vocab-item .w { font-weight: 700; color: #1a1a1a; white-space: nowrap; }
.vocab-item .m { color: #555558; }
"""


def _modern_css() -> str:
    # 업로드 색상 #ecedf1(옅은 청회색) 기반 팔레트.
    # 배경·강조막대·구분선만 색을 쓰고, 글자는 모두 검은색.
    FILL = "#ecedf1"       # 해석·어휘 박스 배경
    INK = "#000000"        # 본문 글자(검정)
    KO = "#000000"         # 한글 해석 글자(검정)
    MUTED = "#000000"      # 라벨·머리글 글자(검정)
    LINE = "#dcdee7"       # 문장 구분선
    RULE = "#d3d6e1"       # 머리글 아래 굵은 선
    ACCENT = "#5b6377"     # 제목 왼쪽 강조막대(슬레이트, 글자 아님)
    NUM = "#000000"        # 원문자 번호(검정)
    return f"""{FONT_IMPORT}{PAGE_RULES}
body {{
  font-family: {SERIF_STACK};
  color: {INK};
  font-size: 13.5px;
  line-height: 1.6;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
/* 우측 상단 머리글 + 전체폭 구분선 */
.doc-header {{
  text-align: right;
  font-size: 11px;
  color: {MUTED};
  letter-spacing: .3px;
  padding-bottom: 8px;
  border-bottom: 1px solid {RULE};
  margin-bottom: 22px;
}}
.passage {{ margin: 0; }}
/* 제목: 라벨 + 제목 한 줄, 왼쪽 세로 강조막대 */
.p-head {{
  border-left: 4px solid {ACCENT};
  padding-left: 13px;
  margin: 0 0 20px 0;
  line-height: 1.45;
  color: {INK};
}}
.p-head .p-label {{ display: block; font-weight: 700; font-size: 13px; color: {MUTED}; margin-bottom: 3px; }}
.p-head .p-title {{ display: block; font-weight: 800; font-size: 15.5px; color: {INK}; }}
/* 한줄해석 / 한줄영어 : 문장 블록 */
.sent {{
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid {LINE};   /* 문장마다 연한 구분선 */
}}
.sent:last-child {{ border-bottom: none; padding-bottom: 0; }}
.en {{
  font-size: 13.5px;
  line-height: 1.62;
  color: {INK};
}}
.num {{
  color: {NUM};
  margin-right: 6px;
}}
/* 회색박스 한글해석 */
.ko-box {{
  margin-top: 8px;
  background: {FILL};
  border-radius: 5px;
  padding: 8px 12px;
}}
.ko-box .ko {{
  font-size: 11px;
  line-height: 1.5;
  color: {KO};
}}
/* 좌지문 우해석 : 2단 표(배경 없음, 가로 구분선만) */
table.two-col {{
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}}
table.two-col td {{
  vertical-align: top;
  padding: 11px 14px 11px 0;
  border-bottom: 1px solid {LINE};
  font-size: 13px;
  line-height: 1.62;
}}
table.two-col tr.sent:last-child td {{ border-bottom: none; }}
table.two-col td.col-en {{ width: 62%; color: {INK}; padding-right: 20px; }}
table.two-col td.col-ko {{ width: 38%; color: {KO}; font-size: 11px; }}
{AUTOFIT_RULES}{VOCAB_RULES}
/* 하단 어휘 박스도 같은 색 계열 (VOCAB_RULES 뒤에서 덮어씀) */
.vocab {{ border-color: #d7d9e3; background: {FILL}; }}
.vocab-title {{ color: {MUTED}; }}
.vocab-item .w {{ color: {INK}; }}
.vocab-item .m {{ color: {KO}; }}
"""


def _textbook_css() -> str:
    return f"""{FONT_IMPORT}{PAGE_RULES}
body {{
  font-family: {SERIF_STACK};
  color: #20242c;
  font-size: 13.5px;
  line-height: 1.62;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.doc-header {{
  text-align:right; font-size:11px; color:#7a8290;
  padding-bottom:8px; border-bottom:1px solid #c9d3e0; margin-bottom:22px;
}}
.p-head {{
  border-left:4px solid #2a5db0; padding-left:13px; margin:0 0 20px 0;
  line-height:1.45; color:#20242c;
}}
.p-head .p-label {{ display:block; font-weight:700; font-size:13px; color:#2a5db0; margin-bottom:3px; }}
.p-head .p-title {{ display:block; font-weight:800; font-size:15.5px; color:#20242c; }}
.sent {{ margin-bottom:14px; padding-bottom:13px; border-bottom:1px dotted #cfd6e0; }}
.sent:last-child {{ border-bottom:none; padding-bottom:0; }}
.en {{ font-size:13.5px; line-height:1.62; }}
.num {{ color:#2a5db0; margin-right:6px; }}
.ko-box {{ margin-top:8px; background:#eef3fb; border-left:3px solid #2a5db0; padding:8px 12px; }}
.ko-box .ko {{ font-size:11px; line-height:1.5; color:#3a4048; }}
table.two-col {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
table.two-col td {{ vertical-align:top; padding:11px 14px 11px 0; border-bottom:1px solid #cfd6e0; font-size:13px; line-height:1.62; }}
table.two-col td.col-en {{ width:62%; padding-right:20px; }}
table.two-col td.col-ko {{ width:38%; color:#3a4048; font-size:11px; }}
{AUTOFIT_RULES}{VOCAB_RULES}"""


def _middle_css() -> str:
    return f"""{FONT_IMPORT}{PAGE_RULES}
body {{
  font-family: {SERIF_STACK};
  color: #2b2b2b;
  font-size: 14.5px;
  line-height: 1.7;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.doc-header {{
  text-align:right; font-size:11.5px; color:#a58a6f;
  padding-bottom:8px; border-bottom:1px solid #ffe0c2; margin-bottom:22px;
}}
.p-head {{
  border-left:5px solid #ff8c42; padding-left:13px; margin:0 0 20px 0;
  line-height:1.45; color:#2b2b2b;
}}
.p-head .p-label {{ display:block; font-weight:700; font-size:13.5px; color:#ff8c42; margin-bottom:3px; }}
.p-head .p-title {{ display:block; font-weight:800; font-size:16px; color:#2b2b2b; }}
.sent {{ margin-bottom:16px; padding-bottom:14px; border-bottom:2px dashed #ffe0c2; }}
.sent:last-child {{ border-bottom:none; padding-bottom:0; }}
.en {{ font-size:14.5px; line-height:1.68; }}
.num {{ color:#ff8c42; font-weight:700; margin-right:6px; }}
.ko-box {{ margin-top:8px; background:#fff6ee; border-radius:8px; padding:9px 13px; }}
.ko-box .ko {{ font-size:11.5px; line-height:1.5; color:#555; }}
table.two-col {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
table.two-col td {{ vertical-align:top; padding:12px 14px 12px 0; border-bottom:2px dashed #ffe0c2; font-size:14px; line-height:1.68; }}
table.two-col td.col-en {{ width:60%; padding-right:20px; }}
table.two-col td.col-ko {{ width:40%; color:#555; font-size:11.5px; }}
{AUTOFIT_RULES}{VOCAB_RULES}"""


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
