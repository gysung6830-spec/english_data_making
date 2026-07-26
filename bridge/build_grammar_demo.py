# -*- coding: utf-8 -*-
"""문법 섹션 난이도 비교 샘플 — 같은 지문(모기 PART 1)으로 1~5단계 문법만 렌더.

실제 웹앱 생성물의 '③ 오늘의 기초 문법' 섹션이 난이도별로 어떻게 달라지는지 보여주는 데모.
    python -m bridge.build_grammar_demo
"""
from __future__ import annotations

from pathlib import Path
from src.bridge import LEVELS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "문법_난이도별_샘플.pdf"

# 공통 지문(참고): 모기 PART 1 문장 1~9
PASSAGE = ("① You are on a camping trip. ④ Beating its wings as fast as 600 times per second, "
           "a mosquito sneaks in and pierces your skin. ⑤ …it fills its belly with blood…, leaving behind a bump. "
           "⑥ This is a mild allergic reaction. ⑦ The more you scratch, the more it itches. "
           "⑧ How do mosquitoes find their victims? ⑨ Carbon dioxide, which humans breathe out, is a key signal…")


def C(kind, tag, title, rule, examples):
    return {"kind": kind, "tag": tag, "title": title, "rule": rule, "examples": examples}


def E(en, ko):
    return {"en": en, "ko": ko}


# ---------------------------------------------------------------------------
# 난이도별 문법 카드 (같은 지문 기준)
# ---------------------------------------------------------------------------
GRAMMAR = {
    # 1단계 = (구 1+2+3+4 합침): 기초 문법 한 번에
    1: [
        C("core", "가장 먼저", "문장의 뼈대 — 누가(주어) + 뭐했다(동사)",
          "<b>누가(주어) + 뭐했다(동사)</b> 두 개만 먼저 찾으면 절반은 성공! 나머지는 다 꾸미는 살이라 몰라도 돼요.",
          [E("<b>A mosquito</b> <b>sneaks</b> in.", "모기가 몰래 들어온다 (누가=모기 / 뭐했다=들어온다)")]),
        C("core", "오늘의 핵심", "be동사 (am · are · is / was · were) = ~이다 / ~에 있다",
          "뜻이 거의 없는 <b>be동사</b>는 &lsquo;= (같다)&rsquo; 기호. I→am, You/We/They→are, He/She/It(하나)→is. 과거는 was/were.",
          [E("You <b>are</b> on a camping trip.", "너는 캠핑 여행 중이다"),
           E("This <b>is</b> a reaction.", "이것은 반응이다 (This = a reaction)")]),
        C("normal", "문법 3", "일반동사에 붙는 -s : 주어가 '하나'일 때",
          "주어가 <b>하나(he/she/it)</b>이면 현재형 일반동사 뒤에 <b>-s/-es</b>. 시험 단골!",
          [E("a mosquito <b>sneaks</b> in and <b>pierces</b>", "모기(하나)가 몰래 들어와 뚫는다")]),
        C("normal", "문법 4", "과거형 -ed · 의문/부정문 do·does",
          "지난 일은 <b>-ed</b>(~했다). 일반동사 질문은 앞에 <b>Do/Does</b>, 부정은 <b>don't/doesn't</b>+원형.",
          [E("She <b>studied</b> English.", "그녀는 영어를 공부했다"),
           E("How <b>do</b> mosquitoes <b>find</b> …?", "모기는 어떻게 찾을까?")]),
        C("note", "지금은 몰라도 OK", "관계사·분사·가정법은 나중에!",
          "이 지문엔 <b>which~, Beating~, the 비교급</b> 같은 어려운 것도 있어요. <b>지금은 하나도 몰라도 됩니다.</b> 오늘은 위 기초만!",
          [E("Carbon dioxide, which humans breathe out, is a signal.", "(참고) which 부분은 뒤 단계에서")]),
    ],
    # 2단계 = (구 5): 준동사 입문 + 비교
    2: [
        C("core", "오늘의 핵심", "to + 동사원형 = ~하기 위해 / ~하는 것",
          "동사 뒤 <b>to + 동사원형</b>은 흔히 &lsquo;~하기 위해&rsquo;(목적).",
          [E("they need protein <b>to produce</b> eggs", "알을 낳기 위해 단백질이 필요하다")]),
        C("normal", "문법 2", "원급 비교 as ~ as = ~만큼 ~한",
          "<b>as + 원급 + as</b>, 뒤에 수치가 자주 와요.",
          [E("as fast <b>as</b> 600 times per second", "초당 600번만큼 빠르게")]),
        C("normal", "문법 3", "「the 비교급, the 비교급」",
          "&lsquo;the+비교급&rsquo; 두 번 = &ldquo;A 할수록 더 B 하다&rdquo;.",
          [E("<b>The more</b> you scratch, <b>the more</b> it itches.", "긁을수록 더 가렵다")]),
    ],
    # 3단계 = (구 6): 관계사·분사 입문
    3: [
        C("core", "오늘의 핵심", "관계대명사 which (앞 명사 설명)",
          "명사 뒤 <b>, which …,</b> 는 그 명사를 <b>추가 설명</b>. 괄호 치고 읽으면 뼈대가 보여요.",
          [E("Carbon dioxide<b>, which humans breathe out,</b> is a signal.", "이산화탄소는(인간이 내쉬는 것인데) 신호이다")]),
        C("normal", "문법 2", "분사구문 (-ing) = ~하면서 / ~한 채로",
          "문장 앞·뒤 <b>동사+ing</b> 덩어리. &lsquo;~하면서&rsquo;로 이어 읽기.",
          [E("<b>Beating</b> its wings…, a mosquito sneaks in", "날개를 퍼덕이면서, 모기가 들어온다")]),
        C("normal", "문법 3", "동격의 that",
          "명사 뒤 <b>that + 완전한 절</b>은 그 명사의 &lsquo;내용&rsquo;.",
          [E("a signal <b>that</b> a nice meal is near", "좋은 먹이가 가깝다는 신호")]),
    ],
    # 4단계 = (구 7): 표준(내신) — 핵심 문법 전부
    4: [
        C("core", "핵심", "관계대명사 계속적 용법(삽입) — 뼈대 찾기",
          "<b>, which ~ ,</b> 삽입절을 걷어내면 <b>주어-동사</b>가 드러나요.",
          [E("Carbon dioxide, which humans breathe out, <b>is</b> a key signal.", "뼈대: CO2 is a key signal")]),
        C("normal", "문법 2", "분사구문 (동시·시간)",
          "Beating/leaving의 의미상 주어 = 문장 주어(mosquito).",
          [E("…escapes, <b>leaving</b> behind a bump", "…달아난다, 혹을 남긴 채로")]),
        C("normal", "문법 3", "the 비교급·원급 as~as 정리",
          "병렬 구조·어순, as fast as + 배수.",
          [E("The more~, the more~ / as fast as 600 times", "~할수록 더~ / 600번만큼 빠르게")]),
        C("normal", "문법 4", "동격 that",
          "a signal that ~ (뒤 절이 완전 = 동격).",
          [E("a signal that a nice meal is near", "좋은 먹이가 가깝다는 신호")]),
        C("up", "참고", "지문 전체엔 가정법·완료·수동태도!",
          "PART 2 등에는 <b>가정법·현재완료·수동태</b>도 나와요. 표준 단계에선 그때그때 정확히 짚어줍니다.",
          [E("If our blood did not contain protein, they would not bother us.", "(가정법 과거) 뒤 지문에서")]),
    ],
    # 5단계 = (구 8): 실전(심화) — 함정·서술형
    5: [
        C("core", "출제 포인트", "관계대명사 which — that 불가 (계속적 용법)",
          "선행사 Carbon dioxide, 콤마 which. <b>【함정】</b> 계속적 용법엔 <b>that</b>을 못 써요.",
          [E("Carbon dioxide, which …, is a key signal.", "삽입절 제거 → CO2 is a key signal")]),
        C("normal", "출제 포인트", "분사 — 능동(-ing) vs 수동(p.p.)",
          "주체가 스스로 하면 <b>-ing</b>, 당하면 <b>p.p.</b>. <b>【함정】</b> 형태 바꿔 묻습니다.",
          [E("<b>Beating</b> its wings (능동)", "모기가 날개를 퍼덕이며 → Beating")]),
        C("normal", "구분", "동격 that vs 관계대명사 that",
          "뒤 절이 <b>완전</b>하면 동격, 빠진 자리가 있으면 관계대명사.",
          [E("a signal that a nice meal is near", "완전한 절 → 동격 that")]),
        C("normal", "출제 포인트", "수 일치 · 부사 자리 · 어순",
          "긴 주어라도 진짜 주어에 수 일치(<b>a mosquito sneaks</b>). the비교급 어순 주의.",
          [E("a mosquito sneaks in and pierces", "단수 주어 → -s")]),
        C("up", "서술형", "삽입절 제거 후 주어-동사 쓰기",
          "서술형 대비: 삽입·수식을 걷어내고 <b>주어/동사</b>를 정확히 찾아 쓰기.",
          [E("Carbon dioxide … is a key signal.", "주어 Carbon dioxide / 동사 is")]),
    ],
}

CSS = """
@page { size:A4; margin:12mm 12mm 14mm; @bottom-center{content:"ⓒ2026.김은아영어연구소.All rights reserved · " counter(page);
  font-family:"NanumGothic";font-size:8px;color:#9aa0a6;} }
*{box-sizing:border-box;} body{font-family:"NanumGothic","Malgun Gothic",sans-serif;color:#23272e;font-size:10.3px;margin:0;}
:root{--green-d:#1f7a48;--purple:#6a54b3;--purple-bg:#f1eefa;--amber:#cf8a2a;--red:#cd5049;--muted:#6b7280;--line:#e2e6ea;}
.head{border-bottom:3px solid var(--green-d);padding-bottom:7px;margin-bottom:10px;}
.head h1{font-size:19px;margin:0;color:var(--green-d);} .head .s{font-size:10px;color:var(--muted);margin-top:3px;}
.passage{background:#eef7f1;border:1px solid #cfe6d8;border-radius:8px;padding:9px 12px;font-size:9.3px;color:#33413a;margin-bottom:14px;line-height:1.6;}
.lv{break-inside:avoid;margin-bottom:16px;}
.lvhead{display:flex;align-items:center;gap:9px;margin-bottom:8px;}
.lvbadge{background:var(--green-d);color:#fff;font-weight:800;font-size:12px;padding:3px 12px;border-radius:16px;white-space:nowrap;}
.lvkey{font-weight:800;font-size:13px;color:var(--green-d);} .lvdesc{font-size:9.3px;color:var(--muted);}
.cnt{font-size:9px;color:var(--muted);margin-left:auto;}
.gram-card{border:1px solid var(--purple-bg);border-left:4px solid var(--purple);border-radius:0 7px 7px 0;padding:8px 11px;margin-bottom:8px;break-inside:avoid;}
.gram-card.core{border-left-width:5px;background:#faf9fe;} .gram-card.up{border-left-color:var(--amber);}
.g-tag{display:inline-block;background:var(--purple);color:#fff;font-size:8.5px;font-weight:800;padding:1px 8px;border-radius:9px;margin-right:6px;}
.gram-card.core .g-tag{background:var(--red);} .gram-card.up .g-tag{background:var(--amber);}
.g-title{font-weight:800;font-size:11px;}
.g-rule{margin:4px 0 5px;font-size:9.6px;line-height:1.55;} .g-rule b{background:#f1eefa;padding:0 2px;border-radius:3px;}
.gram-card.core .g-rule b{background:#fdeceb;} .gram-card.up .g-rule b{background:#f9f3e7;}
.g-ex{background:#faf9fd;border:1px dashed #d6cdf0;border-radius:6px;padding:5px 9px;font-size:9.3px;line-height:1.65;}
.gram-card.core .g-ex{background:#fdf7f6;border-color:#eec6c3;} .gram-card.up .g-ex{background:#fdfaf3;border-color:#ecd9b6;}
.g-ex .en{font-weight:700;color:#1f2937;} .g-ex .arrow{color:var(--purple);font-weight:800;padding:0 4px;}
.gram-card.core .g-ex .arrow{color:var(--red);} .gram-card.up .g-ex .arrow{color:var(--amber);}
.note{font-size:8.8px;color:#7a4a12;background:#fdf6ea;border:1px solid #ecd9b6;border-radius:7px;padding:7px 11px;margin-bottom:14px;}
"""


def _cards_html(cards):
    out = []
    for g in cards:
        lvl = {"core": "core", "note": "up", "normal": ""}.get(g["kind"], "")
        ex = "<br>".join(f'<span class="en">{e["en"]}</span><span class="arrow">→</span>{e["ko"]}'
                         for e in g["examples"])
        out.append(f'<div class="gram-card {lvl}"><div><span class="g-tag">{g["tag"]}</span>'
                   f'<span class="g-title">{g["title"]}</span></div>'
                   f'<div class="g-rule">{g["rule"]}</div><div class="g-ex">{ex}</div></div>')
    return "".join(out)


def build():
    blocks = []
    for lv in range(1, 6):
        m = LEVELS[lv]
        cards = GRAMMAR[lv]
        blocks.append(
            f'<div class="lv"><div class="lvhead"><span class="lvbadge">난이도 {lv}</span>'
            f'<span class="lvkey">{m["key"]}</span><span class="lvdesc">{m["desc"]}</span>'
            f'<span class="cnt">문법 카드 {len(cards)}개</span></div>{_cards_html(cards)}</div>'
        )
    html = (f'<meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="head"><h1>③ 오늘의 기초 문법 — 난이도 1~5 비교</h1>'
            f'<div class="s">같은 지문(모기 PART 1)으로, 난이도에 따라 문법 개수·난이도·설명이 어떻게 달라지는지</div></div>'
            f'<div class="passage"><b>공통 지문</b> &nbsp;{PASSAGE}</div>'
            + "".join(blocks))
    from weasyprint import HTML
    OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(OUT))
    return OUT


if __name__ == "__main__":
    p = build()
    print("생성:", p)
