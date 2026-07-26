# -*- coding: utf-8 -*-
"""문법 섹션 난이도 **8단계** 비교 샘플 (검토용).

같은 지문(모기 PART 1)으로 8단계 문법 섹션을 나란히 렌더.
선생님이 보고 원하는 대로 단계를 합치기 위한 제안용.
    python -m bridge.build_grammar_demo8
"""
from __future__ import annotations

from pathlib import Path
from bridge.build_grammar_demo import CSS, C, E, _cards_html, PASSAGE

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "문법_난이도8단계_샘플.pdf"

# 8단계 라벨 (검토용)
LEVELS8 = {
    1: {"key": "입문", "desc": "단어만 겨우 아는 학생 · 문장 뼈대(주어+동사)부터"},
    2: {"key": "왕기초", "desc": "be동사가 뭔지 모름 · am/are/is·was/were"},
    3: {"key": "기초①", "desc": "3인칭 -s를 모름 · 일반동사 & -s"},
    4: {"key": "기초②", "desc": "과거·질문이 헷갈림 · 시제·의문/부정문"},
    5: {"key": "기본①", "desc": "to부정사를 모름 · 준동사 입문 + 원급/비교급"},
    6: {"key": "기본②", "desc": "관계사가 안 보임 · 관계대명사·분사 입문"},
    7: {"key": "표준", "desc": "고1 평균·내신 대비 · 지문 핵심 문법 전부"},
    8: {"key": "실전", "desc": "상위권·서술형 · 어법 함정·구문 비교·출제 포인트"},
}

GRAMMAR8 = {
    1: [
        C("core", "가장 먼저", "문장의 뼈대 — 누가(주어) + 뭐했다(동사)",
          "<b>누가(주어) + 뭐했다(동사)</b> 두 개만 먼저 찾으면 절반은 성공! 나머지는 다 꾸미는 살이라 몰라도 돼요.",
          [E("<b>A mosquito</b> <b>sneaks</b> in.", "모기가 몰래 들어온다 (누가=모기 / 뭐했다=들어온다)"),
           E("<b>It</b> <b>fills</b> its belly.", "그것이 채운다 (its belly=배를 → 살)")]),
        C("note", "지금은 몰라도 OK", "단어가 여러 개 붙어도 겁먹지 않기",
          "주어 앞뒤에 단어가 많아도 다 <b>살</b>이에요. &lsquo;진짜 누구?&rsquo;만 찾으면 돼요.",
          [E("Carbon dioxide … is a key signal.", "이산화탄소는 … 신호이다 (가운데는 다 살)")]),
    ],
    2: [
        C("core", "오늘의 핵심", "be동사 (am · are · is) = ~이다 / ~에 있다",
          "뜻이 거의 없는 <b>be동사</b>는 &lsquo;= (같다)&rsquo; 기호예요. I→am, You/We/They→are, He/She/It(하나)→is.",
          [E("You <b>are</b> on a camping trip.", "너는 캠핑 여행 중이다"),
           E("This <b>is</b> a reaction.", "이것은 반응이다 (This = a reaction)")]),
        C("normal", "문법 2", "be동사 과거 = was / were",
          "am·is의 과거는 <b>was</b>, are의 과거는 <b>were</b>. &lsquo;~였다&rsquo;.",
          [E("We <b>were</b> hungry.", "우리는 배고팠다")]),
        C("note", "지금은 몰라도 OK", "일반동사·관계사는 다음에", "be동사부터 확실히!", [E("It fills its belly.", "(참고) 이건 다음 단계에서")]),
    ],
    3: [
        C("core", "오늘의 핵심", "일반동사에 붙는 -s : 주어가 '하나'일 때",
          "움직임을 나타내는 <b>일반동사</b>는, 주어가 <b>하나(he/she/it)</b>이면 뒤에 <b>-s/-es</b>. 시험 단골!",
          [E("a mosquito <b>sneaks</b> in and <b>pierces</b>", "모기(하나)가 몰래 들어와 뚫는다"),
           E("it <b>fills</b> … it <b>itches</b>", "그것이 채운다 … 그것이 가렵다")]),
        C("normal", "문법 2", "be동사 vs 일반동사 구분",
          "&lsquo;~이다/있다&rsquo;면 <b>be동사</b>, 움직임이면 <b>일반동사</b>. 한 문장에 동사는 보통 하나!",
          [E("This is a reaction. / It fills its belly.", "이다(be) / 채운다(일반)")]),
    ],
    4: [
        C("core", "오늘의 핵심", "과거형 -ed = 이미 지나간 일",
          "일반동사 뒤에 <b>-ed</b>가 붙으면 <b>과거</b>(~했다). 불규칙도 있어요(go-went).",
          [E("She <b>studied</b> English.", "그녀는 영어를 공부했다")]),
        C("normal", "문법 2", "의문문 : 앞에 Do / Does",
          "일반동사로 물을 땐 문장 앞에 <b>Do/Does</b>, 뒤 동사는 원형.",
          [E("How <b>do</b> mosquitoes <b>find</b> their victims?", "모기는 어떻게 먹잇감을 찾을까?")]),
        C("normal", "문법 3", "부정문 : don't / doesn't",
          "&lsquo;~하지 않는다&rsquo;는 <b>don't/doesn't + 원형</b>.",
          [E("Mosquitoes <b>don't</b> sleep at day.", "(예) 모기는 낮에 자지 않는다")]),
    ],
    5: [
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
    6: [
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
    7: [
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
    8: [
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


def build():
    blocks = []
    for lv in range(1, 9):
        m = LEVELS8[lv]
        cards = GRAMMAR8[lv]
        blocks.append(
            f'<div class="lv"><div class="lvhead"><span class="lvbadge">난이도 {lv}</span>'
            f'<span class="lvkey">{m["key"]}</span><span class="lvdesc">{m["desc"]}</span>'
            f'<span class="cnt">문법 카드 {len(cards)}개</span></div>{_cards_html(cards)}</div>'
        )
    html = (f'<meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="head"><h1>③ 오늘의 기초 문법 — 난이도 <b>8단계</b> 비교 (검토용)</h1>'
            f'<div class="s">같은 지문(모기 PART 1)으로 8단계를 나란히. 보시고 원하는 단계를 합쳐 주세요.</div></div>'
            f'<div class="passage"><b>공통 지문</b> &nbsp;{PASSAGE}</div>'
            + "".join(blocks))
    from weasyprint import HTML
    OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(OUT))
    return OUT


if __name__ == "__main__":
    print("생성:", build())
