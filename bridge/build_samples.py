# -*- coding: utf-8 -*-
"""난이도별 '최종 샘플' 교재 5부 생성 (같은 지문, 레벨별 구성).

웹앱 생성기(src/bridge.py)의 실제 출력 형식으로, 모기 지문(PART 1, 문장 1~16)을
난이도 1~5 각각에 맞춰 렌더한다. (API 없이 볼 수 있는 완성 샘플)

    python -m bridge.build_samples
"""
from __future__ import annotations

from pathlib import Path
from src import bridge as B
from bridge.build_grammar_demo import GRAMMAR   # 병합 5단계 문법 카드(dict)
from bridge.lesson1_data import DAY1, DAY2, DAY3

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

# ---- 공통 지문(문장 1~16): 기존 데이터 재사용 ----
PASSAGE = DAY1["passage"] + DAY2["passage"] + [DAY3["passage"][0]]
LITERAL = DAY1["literal"] + DAY2["literal"] + [DAY3["literal"][0]]

# 어휘: 1~16 범위 통합 + 중복 제거
_vsrc = DAY1["vocab"] + DAY2["vocab"] + DAY3["vocab"][:2]
_seen, VOCAB = set(), []
for v in _vsrc:
    k = v["en"].lower()
    if k not in _seen:
        _seen.add(k); VOCAB.append(v)

SUMMARY_ONE = "작고 성가신 모기가, 사실은 인류 역사상 가장 많은 사람을 죽인 존재였다."
SUMMARY_BODY = ("모기가 어떻게 사람을 물고, 어떤 신호(이산화탄소·땀·체온)로 먹잇감을 찾는지 설명하는 글이에요. "
                "암컷 모기는 <b>알을 낳는 데 필요한 단백질</b> 때문에 우리 피를 빱니다.")
PART_HEADING = "PART 1  THE NUISANCE (성가신 존재)"

# ---- 레벨별 설정 ----
GOAL = {
    1: ("문장의 뼈대(주어+동사) + be동사·3인칭 -s", "누가/뭐했다부터! 오늘은 뼈대와 be동사만 잡아도 성공"),
    2: ("to부정사·원급·「the 비교급」", "동사를 아는 학생이 준동사·비교로 한 걸음 더"),
    3: ("관계대명사·분사구문·동격 that", "긴 문장 속 '설명 덩어리'를 괄호 치고 뼈대 찾기"),
    4: ("지문 핵심 문법 총정리(가정법·관계사·분사)", "내신 대비 — 핵심 문법을 정확히"),
    5: ("어법 함정·구문 비교·서술형", "상위권·서술형 대비 — 출제 포인트와 함정까지"),
}
VOCAB_N = {1: 26, 2: 20, 3: 17, 4: 15, 5: 13}

# ---- 레벨별 핵심 문법 연습문제 (지문 문장 기반) ----
def QG(point, question, answer, why):
    return B.BQuizGrammar(point=point, question=question, answer=answer, why=why)

QUIZ_GRAMMAR = {
    1: [
        QG("3인칭 -s", "A mosquito ( sneak / sneaks ) in and ( pierce / pierces ) your skin.",
           "sneaks, pierces", "주어 a mosquito=하나 → 동사에 -s"),
        QG("be동사", "You ( am / are / is ) on a camping trip.", "are", "주어 You → are"),
        QG("be동사", "This ( is / are ) a mild allergic reaction.", "is", "주어 This=하나 → is"),
        QG("의문문", "How ( do / does ) mosquitoes find their victims?", "do", "mosquitoes=여럿 → do"),
        QG("주어 찾기", "밑줄 친 진짜 주어에 ○: ( A mosquito ) sneaks in and pierces your skin.",
           "A mosquito", "동사(sneaks) 앞의 명사가 주어"),
    ],
    2: [
        QG("to부정사", "They need protein ( produce / to produce ) eggs.", "to produce", "~하기 위해(목적)"),
        QG("원급 as~as", "beating its wings as fast ( as / than ) 600 times per second", "as", "as + 원급 + as"),
        QG("the 비교급", "The more you scratch, ( more / the more ) it itches.", "the more", "the 비교급, the 비교급"),
        QG("to부정사 해석", "they need protein to produce eggs → 'to produce eggs'의 뜻은?", "알을 낳기 위해", "목적의 to부정사"),
    ],
    3: [
        QG("관계대명사", "Carbon dioxide, ( which / what ) humans and other animals breathe out, is a key signal.",
           "which", "선행사 Carbon dioxide(사물) → which"),
        QG("분사구문", "( Beat / Beating ) its wings as fast as 600 times per second, a mosquito sneaks in.",
           "Beating", "~하면서(능동) → -ing"),
        QG("분사구문", "it fills its belly and then escapes, ( leaving / left ) behind a bump.",
           "leaving", "혹을 남긴 채로(능동) → -ing"),
        QG("관계대명사", "you release certain chemicals ( that / what ) attract them.",
           "that", "선행사 chemicals → 주격 관계대명사 that"),
    ],
    4: [
        QG("관계사·뼈대", "Carbon dioxide, which humans breathe out, is a key signal. → 문장의 주어와 동사는?",
           "주어 Carbon dioxide / 동사 is", "삽입절(, which ~ ,)을 걷어내면 뼈대가 보임"),
        QG("분사구문", "( Beating / Beaten ) its wings, a mosquito sneaks in.", "Beating", "모기가 스스로 퍼덕임=능동"),
        QG("가정법 과거", "If our blood ( does not / did not ) contain protein, they would not bother us.",
           "did not", "가정법 과거: If + 과거, 주어 would + 원형"),
        QG("the 비교급", "( The more / More ) you scratch, the more it itches.", "The more", "the 비교급 ~, the 비교급 ~"),
        QG("동격 that", "a signal that a nice meal is near → 이 that의 이름은?", "동격 that", "뒤 절이 완전 → 동격"),
    ],
    5: [
        QG("계속적 용법", "어법상 틀린 곳 고치기: Carbon dioxide, ( that ) humans breathe out, is a signal.",
           "that → which", "콤마+관계사(계속적 용법)에는 that 불가"),
        QG("분사 능동/수동", "( Beating / Being beaten ) its wings, a mosquito sneaks in.", "Beating", "주어가 스스로 하는 능동 → -ing"),
        QG("동격 vs 관계사", "a signal that a nice meal is near / the only cue that they use — 각 that의 이름은?",
           "앞=동격 that, 뒤=관계대명사(목적격)", "뒤 절이 완전하면 동격, 빠진 자리 있으면 관계대명사"),
        QG("수 일치", "A mosquito ( sneak / sneaks ) in and pierces your skin.", "sneaks", "단수 주어 → -s (등위로 pierces도)"),
        QG("서술형", "삽입절을 빼고 주어·동사를 쓰시오: Carbon dioxide, which humans and other animals breathe out, is actually a key signal.",
           "주어 Carbon dioxide / 동사 is", "삽입·수식을 걷어내면 주어-동사"),
    ],
}


def _to_grammar(cards):
    out = []
    for c in cards:
        out.append(B.BGrammar(kind=c["kind"], tag=c["tag"], title=c["title"], rule=c["rule"],
                              examples=[B.BExample(en=e["en"], ko=e["ko"]) for e in c["examples"]]))
    return out


def build_one(level: int) -> B.BridgeGen:
    goal, goal_sub = GOAL[level]
    voc = VOCAB[:VOCAB_N[level]]
    qwords = [B.BQuizWord(en=v["en"], ko=v["ko"].split("(")[0].strip()) for v in voc[:10]]
    return B.BridgeGen(
        title="모기는 어떻게 무는가 (The Nuisance)",
        summary_oneline=SUMMARY_ONE,
        summary_body=SUMMARY_BODY,
        part_heading=PART_HEADING,
        goal_grammar=goal,
        goal_sub=goal_sub,
        passage=[B.BPassageLine(no=p["no"], en=p["en"]) for p in PASSAGE],
        vocab=[B.BVocab(en=v["en"], pron=v["pron"], pos=v["pos"], ko=v["ko"]) for v in voc],
        grammar=_to_grammar(GRAMMAR[level]),
        literal=[B.BLiteral(no=s["no"], en=s["en"], ko=s["ko"]) for s in LITERAL],
        quiz_word=qwords,
        quiz_grammar=QUIZ_GRAMMAR[level],
        quiz_translate=[
            B.BQuizTranslate(en="This is a mild allergic reaction to the mosquito's saliva.",
                             ko="이것은 모기의 침에 대한 가벼운 알레르기 반응이다."),
            B.BQuizTranslate(en="Carbon dioxide, which humans and other animals breathe out, is actually a key signal to mosquitoes.",
                             ko="이산화탄소는, 인간과 다른 동물들이 내쉬는 것인데, 사실 모기에게 핵심 신호이다."),
        ],
    )


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for lv in range(1, 6):
        key = B.level_meta(lv)["key"]
        gen = build_one(lv)
        out = OUT / f"브릿지최종샘플_{lv}_{key}.pdf"
        B.render_pdf(gen, out, lv, source="2022 개정 천재(강상구) 공통영어2 · Lesson 1 (모기)")
        paths.append(out)
        print(f"  난이도 {lv} · {key} → {out.name}")
    try:
        from pypdf import PdfWriter
        w = PdfWriter()
        for p in paths:
            w.append(str(p))
        combo = OUT / "브릿지최종샘플_난이도1-5_합본.pdf"
        with combo.open("wb") as f:
            w.write(f)
        print(f"  합본 → {combo.name}")
    except Exception as e:
        print(f"  (합본 생략: {e})")
    return paths


if __name__ == "__main__":
    print("난이도별 최종 샘플 생성 중...")
    build()
    print("완료. output/ 확인.")
