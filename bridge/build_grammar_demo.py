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


def C(kind, tag, title, rule, examples, form="", tip=""):
    return {"kind": kind, "tag": tag, "title": title, "rule": rule,
            "form": form, "examples": examples, "tip": tip}


def E(en, ko):
    return {"en": en, "ko": ko}


# ---------------------------------------------------------------------------
# 난이도별 문법 카드 (같은 지문 기준)
# ---------------------------------------------------------------------------
GRAMMAR = {
    # 1단계 = (구 1+2+3+4 합침): 기초 문법 한 번에
    1: [
        C("core", "가장 먼저", "문장의 뼈대 — 누가(주어) + 뭐했다(동사)",
          "영어 문장은 사람 몸처럼 <b>뼈대</b>가 있어요. 뼈대는 딱 두 가지, <b>누가(주어)</b>와 <b>뭐했다(동사)</b>예요. "
          "이 둘만 먼저 찾으면 아무리 긴 문장도 절반은 이해한 거예요. 나머지 단어(언제·어디서·무엇을)는 뼈대를 꾸며 주는 "
          "<b>&lsquo;살&rsquo;</b>이라, 처음엔 몰라도 괜찮아요. <b>동사부터</b> 찾고 그 앞의 명사를 주어로 잡는 게 요령이에요.",
          [E("<b>A mosquito</b> <b>sneaks</b> in.", "모기가(주어) 몰래 들어온다(동사)"),
           E("<b>It</b> <b>fills</b> its belly with blood.", "그것이(주어) 채운다(동사) — its belly·with blood는 살")],
          form="누가(주어) + 뭐했다(동사) + (나머지 = 살)",
          tip="동사(~하다/~이다)부터 찾고, 그 앞 명사가 주어!"),
        C("core", "오늘의 핵심", "be동사 (am · are · is / was · were) = ~이다 / ~에 있다",
          "동사에는 두 종류가 있어요. 움직임을 나타내는 <b>일반동사</b>(run, eat)와, 그냥 &lsquo;~이다/~에 있다&rsquo;만 뜻하는 "
          "<b>be동사</b>. be동사는 뜻이 거의 없어서 <b>&lsquo;=(같다)&rsquo; 기호</b>라고 생각하면 쉬워요. "
          "주어가 무엇이냐에 따라 모양만 바뀌어요.",
          [E("You <b>are</b> on a camping trip.", "너 = 캠핑 여행 중 (너는 캠핑 여행 중이다)"),
           E("This <b>is</b> a mild allergic reaction.", "이것 = 알레르기 반응 (이것은 알레르기 반응이다)")],
          form="I→am · You/We/They→are · He/She/It(하나)→is · (과거) was/were",
          tip="am/are/is/was/were가 보이면 무조건 &lsquo;~이다&rsquo;로 해석!"),
        C("normal", "문법 3", "일반동사에 붙는 -s : 주어가 '하나'일 때",
          "일반동사로 <b>지금(현재)</b>의 일을 말할 때, 주어가 <b>하나(he/she/it·단수)</b>이면 동사 뒤에 <b>-s/-es</b>를 붙여요. "
          "주어가 여럿(we/they·복수)이면 그냥 원형이에요. 사소해 보여도 시험에 정말 자주 나오는 &lsquo;수 일치&rsquo;예요.",
          [E("a mosquito <b>sneaks</b> in and <b>pierces</b> your skin", "모기(하나)가 몰래 들어와 뚫는다"),
           E("humans and other animals <b>breathe</b> out", "사람과 동물들이(여럿) 내쉰다 — 원형")],
          form="he/she/it(하나) + 동사-s   ↔   we/they(여럿) + 동사(원형)",
          tip="&lsquo;주어가 하나인가?&rsquo;부터 확인 → 하나면 -s."),
        C("normal", "문법 4", "과거형 -ed · 의문문 Do/Does · 부정문 don't",
          "지난 일은 동사에 <b>-ed</b>(또는 불규칙형)를 붙여 <b>과거</b>로 말해요. 일반동사로 <b>질문</b>할 땐 문장 앞에 "
          "<b>Do/Does</b>, <b>부정</b>은 <b>don't/doesn't</b>를 쓰는데, 그 <b>뒤 동사는 항상 원형</b>(-s·-ed 안 붙임)이에요.",
          [E("She <b>studied</b> English last night.", "그녀는 어젯밤 영어를 공부했다(과거)"),
           E("How <b>do</b> mosquitoes <b>find</b> their victims?", "모기는 어떻게 먹잇감을 찾을까?")],
          form="과거: 동사+ed · 의문: Do/Does+주어+원형? · 부정: don't/doesn't+원형",
          tip="Do/Does·don't 뒤 동사는 원형!"),
        C("note", "지금은 몰라도 OK", "관계사·분사·가정법은 나중에 배워요!",
          "이 지문엔 <b>which~(관계대명사), Beating~(분사구문), the 비교급</b> 같은 어려운 것도 섞여 있어요. "
          "<b>지금은 하나도 몰라도 됩니다.</b> 오늘은 위 기초(뼈대·be동사·-s·과거/의문)만 확실히 잡으면 대성공! "
          "어려운 건 난이도가 올라가면 하나씩 천천히 배워요.",
          [E("Carbon dioxide, which humans breathe out, is a signal.", "(참고) &lsquo;, which ~,&rsquo; 덩어리는 뒤 단계에서")]),
    ],
    # 2단계 = (구 5): 준동사 입문 + 비교
    2: [
        C("core", "오늘의 핵심", "to + 동사원형 = ~하기 위해 / ~하는 것 (to부정사)",
          "<b>to + 동사원형</b> 덩어리는 여러 뜻으로 쓰이는데, 가장 많이 나오는 건 <b>&lsquo;~하기 위해서&rsquo;(목적)</b>예요. "
          "&lsquo;왜 그렇게 했지?&rsquo;의 답이 되면 목적으로 해석해요. 문맥에 따라 &lsquo;~하는 것/~할&rsquo;로 해석되기도 해요.",
          [E("they need protein <b>to produce</b> eggs", "알을 낳기 위해 단백질이 필요하다"),
           E("We eat <b>to live</b>.", "우리는 살기 위해 먹는다")],
          form="동사 + to + 동사원형 = ~하기 위해 (목적)",
          tip="to 다음엔 반드시 <b>동사원형</b>(-s·-ed 안 붙임)."),
        C("normal", "문법 2", "원급 비교 as ~ as = ~만큼 …한/하게",
          "두 대상이 <b>비슷한 정도</b>일 때 <b>as + 형용사/부사 원급 + as</b> 로 &lsquo;~만큼 …한/하게&rsquo;라고 해요. "
          "as와 as 사이에는 꾸미지 않은 <b>원급</b>(fast, tall)이 들어가고, 뒤에 숫자·배수가 오면 그 정도를 나타내요.",
          [E("beating its wings <b>as fast as</b> 600 times per second", "초당 600번만큼 빠르게 날개를 퍼덕이며"),
           E("He is <b>as tall as</b> my dad.", "그는 우리 아빠만큼 키가 크다")],
          form="as + 원급 + as ~ = ~만큼 …한/하게",
          tip="as ~ as 사이는 비교급(-er) 말고 <b>원급</b>!"),
        C("normal", "문법 3", "「The 비교급 ~, the 비교급 ~」 = ~할수록 더 …하다",
          "<b>the + 비교급</b>이 두 번 짝을 이루면 &lsquo;<b>A 하면 할수록 더 B 하다</b>&rsquo;라는 뜻이에요. "
          "앞 절이 원인, 뒤 절이 결과처럼 이어져요. the가 두 번, 비교급이 두 번 보이면 바로 이 패턴이에요.",
          [E("<b>The more</b> you scratch, <b>the more</b> it itches.", "긁으면 긁을수록 더 가렵다"),
           E("<b>The higher</b> you go, <b>the colder</b> it gets.", "높이 갈수록 더 추워진다")],
          form="The 비교급 (A), the 비교급 (B) = A할수록 더 B",
          tip="&lsquo;the+비교급&rsquo;이 두 번이면 이 뜻!"),
    ],
    # 3단계 = (구 6): 관계사·분사 입문
    3: [
        C("core", "오늘의 핵심", "관계대명사 (who / which / that) — 명사를 뒤에서 설명",
          "명사 뒤에 붙어 그 명사가 <b>어떤 것인지 설명</b>해 주는 덩어리를 이끄는 말이 <b>관계대명사</b>예요. "
          "사람이면 <b>who</b>, 사물·동물이면 <b>which/that</b>. 특히 <b>명사, which ~,</b> 처럼 콤마로 끼어들면 "
          "&lsquo;그 명사에 대한 보충 설명&rsquo;이에요. 그 덩어리를 <b>괄호로 묶고</b> 읽으면 문장 뼈대가 드러나요.",
          [E("Carbon dioxide<b>, which humans breathe out,</b> is a signal.", "이산화탄소는(인간이 내쉬는 것인데) 신호이다"),
           E("certain chemicals <b>that attract them</b>", "그들을 유인하는 특정한 화학물질")],
          form="명사 + [who/which/that + (동사~)] = ~하는 (명사)",
          tip="관계사 덩어리를 괄호 치면 진짜 주어·동사가 보여요."),
        C("normal", "문법 2", "분사구문 (동사+ing) = ~하면서 / ~한 채로",
          "문장 앞이나 뒤에 <b>동사+ing</b>로 시작하는 덩어리가 콤마와 함께 오면, 주로 "
          "<b>&lsquo;~하면서 / ~한 채로 / ~해서&rsquo;</b>로 이어 읽어요. 이 -ing의 주인공(의미상 주어)은 보통 <b>문장의 주어</b>와 같아요.",
          [E("<b>Beating</b> its wings, a mosquito sneaks in.", "날개를 퍼덕이면서 모기가 몰래 들어온다"),
           E("…escapes, <b>leaving</b> behind a bump.", "…혹을 남긴 채 달아난다")],
          form="동사+ing ~, 주어 + 동사 … = ~하면서, 주어가 …하다",
          tip="-ing 덩어리의 주인공 = 문장 주어(모기)."),
        C("normal", "문법 3", "동격의 that = ~라는 (명사)",
          "명사 바로 뒤에 <b>that + 완전한 문장</b>이 오면, 그 that절은 <b>앞 명사의 내용을 그대로 풀어 주는 &lsquo;동격&rsquo;</b>이에요. "
          "&lsquo;~라는 (명사)&rsquo;로 해석해요. 관계대명사 that과 달리 <b>뒤 문장에 빠진 자리가 없어요</b>.",
          [E("a signal <b>that</b> a nice meal is near", "좋은 먹이가 가깝다<b>는</b> 신호"),
           E("the fact <b>that</b> he lied", "그가 거짓말했다<b>는</b> 사실")],
          form="명사 + that + 완전한 절 = ~라는 (명사)",
          tip="뒤 문장이 완전하면 동격, 빠진 자리 있으면 관계대명사."),
    ],
    # 4단계 = (구 7): 표준(내신) — 핵심 문법 전부
    4: [
        C("core", "핵심", "관계대명사 계속적 용법(삽입) — 삽입절 걷어내고 뼈대 찾기",
          "<b>명사, which ~,</b> (콤마 which)는 앞 명사를 <b>보충 설명</b>하는 &lsquo;계속적 용법&rsquo;이에요. "
          "문장을 읽을 땐 이 <b>삽입절을 괄호로 걷어내</b>고 남은 <b>주어–동사</b>부터 잡으면 아무리 길어도 해석돼요. "
          "계속적 용법에는 <b>that을 쓸 수 없다</b>는 게 중요한 포인트예요.",
          [E("Carbon dioxide, which humans and other animals breathe out, <b>is</b> a key signal.",
             "삽입절 제거 → <b>Carbon dioxide is a key signal</b>")],
          form="주어 [, which ~ ,] 동사 … → 삽입절 제거 = 주어 + 동사",
          tip="계속적 용법(,which)에는 that 불가! (시험 단골)"),
        C("normal", "문법 2", "분사구문 — 능동(-ing) vs 수동(p.p.)",
          "분사구문은 &lsquo;~하면서(동시)·~해서(이유)·~할 때(시간)&rsquo; 등 문맥에 맞게 해석해요. "
          "주어가 그 동작을 <b>스스로 하면 -ing(능동)</b>, <b>당하면 p.p.(수동)</b>이고, 의미상 주어는 문장 주어와 같아요.",
          [E("<b>Beating</b> its wings, a mosquito sneaks in.", "날개를 퍼덕이며(능동) 모기가 들어온다"),
           E("…escapes, <b>leaving</b> behind a bump.", "혹을 남긴 채 달아난다")],
          form="-ing(능동) / p.p.(수동) + …, 주어 + 동사",
          tip="주어가 하는 일이면 -ing, 받는 일이면 p.p."),
        C("normal", "문법 3", "가정법 과거 — If + 과거, 주어 would + 원형",
          "<b>If + 주어 + 과거동사 …, 주어 + would/could + 동사원형</b> 은 &lsquo;<b>(지금) 만약 ~라면 …할 텐데</b>&rsquo;로 "
          "<b>현재 사실의 반대</b>를 상상하는 표현이에요. If절 동사가 과거형이지만 <b>뜻은 현재</b>라는 게 핵심이에요.",
          [E("<b>If</b> our blood <b>did not</b> contain protein, they <b>would not</b> bother us.",
             "피에 단백질이 없다면 우리를 괴롭히지 않을 텐데 (→ 실제론 있음)")],
          form="If + 과거, 주어 would/could + 원형 = (지금) ~라면 …할 텐데",
          tip="&lsquo;사실의 반대&rsquo; → 실제로는 피에 단백질이 있다."),
        C("normal", "문법 4", "동격 that vs 관계대명사 that",
          "명사 + <b>that + 완전한 절</b> = &lsquo;~라는 (명사)&rsquo;(동격). 관계대명사 that과 헷갈리기 쉬운데, "
          "<b>뒤 절이 완전하면 동격</b>, 주어·목적어 자리가 비어 있으면 관계대명사예요.",
          [E("a signal <b>that</b> a nice meal is near", "좋은 먹이가 가깝다는 신호 (완전한 절 → 동격)"),
           E("the cue <b>that</b> they use", "그들이 이용하는 단서 (use의 목적어 빔 → 관계대명사)")],
          form="명사 + that + 완전한 절 = 동격 / 빠진 자리 있으면 관계대명사",
          tip="뒤 문장이 완전한지부터 확인!"),
        C("up", "참고", "지문 전체엔 가정법·완료·수동태도 나와요",
          "PART 2 등 지문 뒷부분에는 <b>수동태(be+p.p.), 현재완료(have p.p.), 과거완료(had p.p.)</b>도 나와요. "
          "표준 단계에선 지문에 실제로 나오는 것만 그때그때 정확히 짚어 줍니다.",
          [E("Rome <b>was surrounded</b> by wetland.", "로마는 습지로 둘러싸여 있었다 (수동태)")]),
    ],
    # 5단계 = (구 8): 실전(심화) — 함정·서술형
    5: [
        C("core", "출제 포인트", "관계대명사 which — 계속적 용법엔 that 불가",
          "<b>콤마+관계사(계속적 용법)</b>는 앞 명사(또는 앞 문장 전체)를 보충 설명하며, <b>that으로 바꿀 수 없어요.</b> "
          "해석의 열쇠는 <b>삽입절을 걷어내고 주어–동사</b>를 먼저 잡는 것. 어법 문제에서 &lsquo;,that&rsquo;은 대부분 오답이에요.",
          [E("Carbon dioxide, <b>which</b> humans breathe out, is a key signal.",
             "삽입절 제거 → CO2 is a key signal (,that ✗ / ,which ✓)")],
          form="선행사 , which ~ , (that 불가) → 걷어내면 주어+동사",
          tip="【함정】 ,that (✗) / ,which (✓)"),
        C("normal", "출제 포인트", "분사 — 능동(-ing) vs 수동(p.p.)",
          "분사가 꾸미는 대상이 그 동작을 <b>스스로 하면 -ing(능동)</b>, <b>당하면 p.p.(수동)</b>이에요. "
          "시험은 이 형태를 바꿔 놓고 맞는 것을 고르게 하니, &lsquo;누가 하는가/받는가&rsquo;를 따져야 해요.",
          [E("<b>Beating</b> its wings, a mosquito sneaks in.", "모기가 스스로 퍼덕임(능동) → Beating"),
           E("a bump <b>left</b> behind", "남겨진 혹(당함·수동) → left(p.p.)")],
          form="스스로 함 → V-ing / 당함 → p.p.",
          tip="【함정】의미상 주어가 &lsquo;하는지 받는지&rsquo;로 판단."),
        C("normal", "구분", "동격 that vs 관계대명사 that",
          "둘 다 that이지만 역할이 달라요. <b>뒤 절이 완전</b>하면 <b>동격</b>(~라는), 주어·목적어 자리가 <b>비어 있으면 관계대명사</b>예요. "
          "서술형·어법에서 자주 구분시켜요.",
          [E("a signal <b>that</b> a nice meal is near", "완전한 절 → 동격 that"),
           E("the cue <b>that</b> they use ▢", "use의 목적어 빔 → 관계대명사 that")],
          form="완전한 절 → 동격 / 빠진 자리 → 관계대명사",
          tip="that 뒤 문장이 완전한지부터 보기."),
        C("normal", "출제 포인트", "수 일치 · 부사 자리 · 어순",
          "긴 주어라도 <b>진짜 주어</b>에 동사를 맞춰요(수 일치). 부사(actually, quickly)는 문장 뼈대가 아니라 살이고, "
          "「the 비교급, the 비교급」의 <b>어순</b>도 자주 물어요.",
          [E("<b>A mosquito</b> sneaks in and pierces your skin.", "단수 주어 → sneaks/pierces (-s)"),
           E("<b>The more</b> you scratch, <b>the more</b> it itches.", "the+비교급 어순")],
          form="진짜 주어 ↔ 동사 수 일치 / the 비교급 어순 고정",
          tip="동사 앞 &lsquo;가짜 주어(수식어)&rsquo;에 속지 않기."),
        C("up", "서술형", "삽입절 제거 후 주어·동사 쓰기",
          "서술형 대비 연습이에요. 문장에서 <b>삽입절(, which ~,)·수식어(전치사구·분사)</b>를 모두 걷어내고 "
          "<b>진짜 주어와 동사</b>만 골라 쓰는 훈련을 해요. 이게 되면 어떤 긴 문장도 안 무너져요.",
          [E("Carbon dioxide, which humans and other animals breathe out, is actually a key signal.",
             "주어 <b>Carbon dioxide</b> / 동사 <b>is</b>")],
          form="삽입·수식 제거 → [주어] + [동사]",
          tip="괄호 치기 → 남는 것이 뼈대."),
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
.g-form{background:#fff;border:1px solid #d6cdf0;border-radius:6px;padding:4px 9px;margin:0 0 6px;font-size:9.2px;font-weight:700;color:#4a3a94;}
.g-form .lbl{display:inline-block;background:var(--purple);color:#fff;font-size:8px;font-weight:800;padding:0 6px;border-radius:7px;margin-right:6px;}
.gram-card.core .g-form{border-color:#eec6c3;} .gram-card.core .g-form .lbl{background:var(--red);}
.gram-card.up .g-form{border-color:#ecd9b6;} .gram-card.up .g-form .lbl{background:var(--amber);}
.g-tip{margin-top:6px;font-size:8.9px;color:#7a4a12;background:#fdf6ea;border-radius:6px;padding:4px 9px;}
.g-tip .lbl{font-weight:800;color:var(--amber);margin-right:4px;}
.note{font-size:8.8px;color:#7a4a12;background:#fdf6ea;border:1px solid #ecd9b6;border-radius:7px;padding:7px 11px;margin-bottom:14px;}
"""


def _cards_html(cards):
    out = []
    for g in cards:
        lvl = {"core": "core", "note": "up", "normal": ""}.get(g["kind"], "")
        ex = "<br>".join(f'<span class="en">{e["en"]}</span><span class="arrow">→</span>{e["ko"]}'
                         for e in g["examples"])
        form = (f'<div class="g-form"><span class="lbl">형태</span>{g["form"]}</div>'
                if g.get("form") else "")
        tip = (f'<div class="g-tip"><span class="lbl">✔ 이것만!</span>{g["tip"]}</div>'
               if g.get("tip") else "")
        out.append(f'<div class="gram-card {lvl}"><div><span class="g-tag">{g["tag"]}</span>'
                   f'<span class="g-title">{g["title"]}</span></div>'
                   f'<div class="g-rule">{g["rule"]}</div>{form}<div class="g-ex">{ex}</div>{tip}</div>')
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
