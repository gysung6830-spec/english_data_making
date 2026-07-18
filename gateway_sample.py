#!/usr/bin/env python3
"""14강 Gateway 지문으로 만든 실제 샘플 (API 없이, build.py + renderer 파이프라인 사용).

정본 지문 하나(8문장)에서 7종을 파생한다:
  순서 → 삽입 → 주제 → 어휘 → 어법 → 내용일치 → 서술형
실행: python gateway_sample.py  → output/Gateway_샘플.pdf
"""
from __future__ import annotations

from pathlib import Path

from exam import build as B
from exam import renderer, validator
from exam.types import (
    CONTENT, GRAMMAR, INSERT, ORDER, SHORT_ANSWER, TOPIC, VOCAB, Passage, Source,
)

ROOT = Path(__file__).resolve().parent

GATEWAY = Source(
    title="Gateway — 설계에 사용자 피드백 반영하기",
    sentences=[
        "Giving clients sufficient opportunity to react to your designs while in progress is a key to professional success.",
        "Similarly, involving prospective building users as well as clients is even more valuable in the long run.",
        "Say your client is a large corporation, such as a health care provider.",
        "While the hospital administration may serve as your client, no doubt the perspectives of administration personnel will differ significantly from those of doctors, interns, residents, nurses, and other medical staff who use the building regularly.",
        "In addition, the experiences of patients and visitors who use the building irregularly, often as a result of life-threatening emergencies, are altogether different as well.",
        "Understanding how each type of user experiences the current medical environment as well as how each reacts to your prospective designs inevitably produces a better building.",
        "People are likely to be more satisfied with a new building or addition if they have been consulted in the design process.",
        "For a large institution, this can translate into increased productivity on the job, reduced absenteeism, less turnover, and lower costs.",
    ],
)


def build_passage() -> Passage:
    p = Passage(title=GATEWAY.title)
    s = GATEWAY.sentences

    # ① 순서 — S0,S1=주어진 글, 나머지 6문장을 3덩어리로
    p.set_qa(ORDER, *B.make_order(
        s, given_n=2, block_sizes=[2, 2, 2], display=[2, 1, 3],
        reason=("주어진 글은 고객뿐 아니라 '사용자'까지 참여시키는 것이 더 가치 있다고 한다. "
                "(B)=Say your client ~ While the hospital administration ~ differ 로 병원 예시를 "
                "꺼내 행정부서와 의료진의 관점 차이를 제시하고, (A)=In addition 으로 환자·방문객까지 "
                "더해 'a better building'으로 정리하며, (C)=People are ~ satisfied ~ For a large "
                "institution 으로 그 이점을 일반화한다. 따라서 (B)-(A)-(C).")
    ))

    # ② 삽입 — S4(In addition 문장)만 빼냄
    p.set_qa(INSERT, *B.make_insert(
        s, remove_idx=4,
        reason=("주어진 문장은 'In addition ~ as well'로, 앞 문장(행정부서와 의료진의 관점 차이, "
                "③ 위치 앞)에 환자·방문객이라는 사용자 집단을 '추가'하고, 뒤 문장 'Understanding "
                "how each type of user ~'로 이어진다. 따라서 정답은 ③.")
    ))

    # ③ 주제 (영어 선지)
    p.set_qa(TOPIC, *B.make_topic(
        s,
        choices=[
            "why architects should trust only the paying client's judgment",
            "the medical training hospital staff need to operate new equipment",
            "the value of consulting a building's real users, not just clients, for better design",
            "how hospitals prepare for life-threatening emergencies and disasters",
            "how involving users in design reduces satisfaction and raises costs",
        ],
        answer_no=3,
        reason=("지문은 비용을 내는 고객뿐 아니라 건물을 실제로 쓰는 다양한 사용자(의료진·환자·"
                "방문객)의 관점을 반영하면 더 나은 건물이 되고 만족·생산성 같은 이점이 따른다고 "
                "한다. 정답 ③은 clients·users를 유의어(real users, consulting)로 담아 이 핵심을 "
                "표현했다."),
        wrong={
            1: "client·judgment 같은 지문 단어를 썼지만, 글은 고객'만'이 아니라 사용자도 참여시켜야 "
               "한다고 하므로 '고객만 신뢰'는 모순이다.",
            2: "hospital staff라는 단어만 빌려왔을 뿐, 의료 장비 교육은 글과 무관하다(무관).",
            4: "emergencies라는 단어만 빌려왔을 뿐, 응급·재난 대비는 글의 주제가 아니다(무관).",
            5: "글은 사용자 참여가 만족·생산성을 '높인다'고 했는데 선지는 '낮춘다'고 하여 반대다(모순).",
        },
    ))

    # ④ 어휘 (방식1: 반의어) — 밑줄 5개 중 ④만 반의어
    p.set_qa(VOCAB, *B.make_vocab(
        s,
        marks=[
            (0, "sufficient", "ample"),          # 유의어
            (1, "valuable", "worthwhile"),       # 유의어
            (3, "significantly", "considerably"),# 유의어(부사)
            (5, "better", "worse"),              # 반의어 → 정답
            (6, "satisfied", "pleased"),         # 유의어
        ],
        answer_no=4,
        reason=("[반의어형] ④ 문장은 각 사용자를 이해하면 '더 나은(better)' 건물을 만든다는 맥락"
                "이므로 worse(더 나쁜)는 정반대라 부적절하다. 나머지 ample·worthwhile·"
                "considerably·pleased는 원문 단어의 유의어로 문맥에 맞게 쓰였다."),
    ))

    # ⑤ 어법 (복수정답) — 밑줄 8개, ③④⑤만 오답형
    p.set_qa(GRAMMAR, *B.make_grammar(
        s,
        marks=[
            (0, "is", "is"),                 # ① 동명사 주어 수일치(적절)
            (1, "involving", "involving"),   # ② 동명사(적절)
            (3, "who", "whom"),              # ③ 관계사 오류(주격이어야)
            (4, "are", "is"),                # ④ 수 일치 오류(experiences are)
            (5, "produces", "produce"),      # ⑤ 수 일치 오류(Understanding produces)
            (6, "consulted", "consulted"),   # ⑥ 수동(적절)
            (7, "reduced", "reduced"),       # ⑦ 병렬(적절)
            (7, "lower", "lower"),           # ⑧ 병렬(적절)
        ],
        answer_nos=[3, 4, 5],
        reasons={
            3: "medical staff를 선행사로 받는 주격 관계대명사이므로 whom → who (관계사).",
            4: "주어 the experiences 는 복수이므로 is → are (수 일치).",
            5: "주어가 동명사구 Understanding ~ 로 단수 취급이므로 produce → produces (수 일치).",
        },
    ))

    # ⑥ 내용 일치 (한글 선지, hard 모드: 헷갈리는 함정 오답) — 서술형 앞
    p.set_qa(CONTENT, *B.make_content(
        s,
        choices=[
            # ① 부분 일치 + 범위 과잉 한정(앞 절은 사실, '~에서만'이 없음)
            "설계 과정에서 자문을 받은 사람들은 새 건물에 더 만족하지만, 그런 만족은 대규모 "
            "기관에서만 나타난다.",
            # ② 주체 바꿔치기(정기/비정기 이용자 뒤바꿈)
            "병원 건물을 비정기적으로 이용하는 사람은 주로 의사와 간호사 같은 의료진이다.",
            # ③ 인과 날조(없던 because 를 끼움)
            "환자와 방문객의 경험이 서로 다른 것은 병원 행정 부서의 관점 때문이다.",
            # ④ 정답: 눈에 덜 띄는 세부 사실을 유의어로 위장(differ→'다르게 경험')
            "같은 병원 건물이라도 이용자 집단에 따라 그 공간을 경험하는 방식이 크게 달라진다.",
            # ⑤ 미언급인데 그럴듯(모순 아님, 지문에 없음)
            "설계자는 최종안을 확정하기 전에 모든 사용자에게서 서면 동의를 받아야 한다.",
        ],
        answer_no=4,
        reason=("지문은 같은 병원 건물이라도 행정 부서·의료진(정기 이용)·환자와 방문객(비정기 "
                "이용)이 그 공간을 '서로 크게 다르게' 경험한다고 했다(will differ significantly ~ / "
                "are altogether different). ④는 이를 원문 단어를 숨기고 유의어로 바꿔 표현한 "
                "일치 진술이다."),
        wrong={
            1: "앞 절(자문받은 사람이 더 만족)은 지문과 맞지만, 지문은 그 만족을 '대규모 "
               "기관에서만'으로 한정하지 않았다. 범위를 좁히는 '~에서만'이 지문에 없어 틀렸다. "
               "(부분 일치 + 범위 과장)",
            2: "지문에서 건물을 '비정기적으로(irregularly)' 이용하는 것은 환자·방문객이고, "
               "의료진(doctors·nurses 등)은 '정기적으로(regularly)' 이용한다고 했다. 주체가 "
               "뒤바뀌었다. (주체 바꿔치기)",
            3: "지문은 환자·방문객의 경험이 다른 이유를 '비정기적 이용·응급 상황'으로 설명할 뿐, "
               "'행정 부서의 관점 때문'이라는 인과는 지문에 없다. (인과 날조)",
            5: "사용자를 참여시키라는 취지와 '그럴듯'하지만, '서면 동의를 받아야 한다'는 내용은 "
               "지문에 전혀 언급되지 않았다. 반박할 문장이 없어 오히려 더 헷갈린다. (미언급)",
        },
    ))

    # ⑦ 서술형 — 원본 + 파생 과제
    p.set_qa(SHORT_ANSWER, *B.make_short(
        s,
        q1_prompt="본문 마지막 문장의 this가 가리키는 내용을 우리말로 구체적으로 서술하시오.",
        q1_answer=("설계 과정에서 건물을 실제로 사용할 사람들을 참여시키고 자문을 구하여, 그들이 "
                   "완성된 새 건물(또는 증축)에 더 만족하게 되는 것을 가리킨다."),
        q2_prompt=("다음 <보기>의 단어를 모두 배열하여 '설계 과정에 사용자를 참여시키는 것은 더 "
                   "나은 건물을 만든다'라는 뜻의 문장을 완성하시오. (동사는 원형 제공)"),
        q2_tokens=["involve", "users", "in", "the", "design", "process",
                   "produce", "a", "better", "building"],
        q2_cues=["involve", "produce"],
        q2_answer="Involving users in the design process produces a better building.",
        q3_prompt="다음 요약문의 빈칸 (A), (B)에 제시어를 알맞은 형태로 바꿔 쓰시오.",
        q3_before="When a building's real users, not just its clients, are ",
        q3_mid=" during design, the result is greater satisfaction and ",
        q3_after=" costs for the institution.",
        q3_cue_a="consult", q3_cue_b="reduce", q3_ans_a="consulted", q3_ans_b="reduced",
        q3_reason=("(A) users are ~ 로 '자문을 받는' 수동이므로 과거분사 consulted. "
                   "(B) '줄어든 비용'을 뜻하는 과거분사형 형용사이므로 reduced."),
    ))
    return p


def main() -> int:
    passages = [build_passage()]
    validator.validate_passages(passages)
    nums = validator.validate_numbering(passages, start=1)
    print("검증 통과 — 문항 번호:", nums)
    out = ROOT / "output" / "Gateway_샘플.pdf"
    renderer.render_pdf(passages, out, header_note="고3 영어 · 14강 Gateway")
    print("생성 완료:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
