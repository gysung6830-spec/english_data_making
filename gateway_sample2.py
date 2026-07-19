#!/usr/bin/env python3
"""14강 Gateway 지문으로 만든 '변형문제 2회'(A~G) 샘플 — build2 + renderer.

실행: python gateway_sample2.py  → output/Gateway_2회_샘플.pdf
"""
from __future__ import annotations

from pathlib import Path

from exam import build2 as B2
from exam import renderer, validator
from exam.set2 import A, B, C, D, E, F, G, TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
from exam.types import Passage
from gateway_sample import GATEWAY  # 1회 샘플과 동일한 Gateway 정본 재사용

ROOT = Path(__file__).resolve().parent


def build_passage() -> Passage:
    p = Passage(title=GATEWAY.title)
    s = GATEWAY.sentences

    # A · 어법·어휘 짝짓기 (오답 2 = 반의어 ⓑ + 어법 ⓒ)
    p.set_qa(A, *B2.make_A(
        s,
        marks=[
            (0, "sufficient", "sufficient"),  # ⓐ 적절
            (1, "valuable", "worthless"),     # ⓑ 반의어 오류
            (3, "who", "whom"),               # ⓒ 관계사 오류
            (5, "produces", "produces"),      # ⓓ 적절
            (6, "satisfied", "satisfied"),    # ⓔ 적절
        ],
        answer_no=2,
        reason=("ⓑ는 '고객뿐 아니라 사용자를 참여시키는 것이 장기적으로 더 valuable(가치 있는)'"
                "이라는 문맥이므로 worthless(가치 없는)는 반의어 오류. ⓒ는 medical staff를 "
                "선행사로 받는 주격 관계대명사이므로 whom→who(어법 오류). 따라서 ⓑ, ⓒ."),
        choices=["ⓐ, ⓑ", "ⓑ, ⓒ", "ⓐ, ⓓ", "ⓒ, ⓔ", "ⓓ, ⓔ"],
    ))

    # B · 함의추론
    p.set_qa(B, *B2.make_B(
        s,
        phrase="a better building",
        choices=[
            "실제 사용자들의 서로 다른 요구와 경험을 이해해 그들에게 더 잘 맞게 만든 건물",
            "더 비싼 자재로 지은 고급 건물",
            "비용을 내는 고객의 요구만 충실히 반영한 건물",
            "규모가 더 크고 층수가 많은 건물",
            "공사 기간이 더 짧게 완성된 건물",
        ],
        answer_no=1,
        reason=("'a better building'은 글 전체 논지상 '각 사용자 집단이 공간을 어떻게 경험하는지 "
                "이해해 그들에게 더 잘 맞게 만든 건물'을 뜻한다. 밑줄 주변 한 문장이 아니라 "
                "사용자 참여→더 나은 건물이라는 전체 흐름을 종합해야 한다."),
        wrong={
            2: "'더 나은'은 자재 가격이 아니라 사용자 적합성을 뜻한다(축자적 오독).",
            3: "글은 고객뿐 아니라 '사용자'의 요구 반영을 강조하므로 '고객 요구만'은 논지에 위배(모순).",
            4: "건물의 크기·층수는 글과 무관하다(무관).",
            5: "공사 기간 단축은 글에 언급이 없다(무관).",
        },
    ))

    # C · 어법 오류 판별(복수정답)
    p.set_qa(C, *B2.make_C(
        s,
        marks=[
            (0, "is", "is"),
            (1, "involving", "involving"),
            (3, "who", "whom"),        # 오류
            (4, "are", "is"),          # 오류
            (5, "produces", "produce"),  # 오류
            (6, "consulted", "consulted"),
            (7, "reduced", "reduced"),
            (7, "lower", "lower"),
        ],
        answer_nos=[3, 4, 5],
        reasons={
            3: "medical staff를 선행사로 받는 주격 관계대명사이므로 whom → who (관계사).",
            4: "주어 the experiences 는 복수이므로 is → are (수 일치).",
            5: "주어가 동명사구 Understanding ~ 로 단수 취급이므로 produce → produces (수 일치).",
        },
    ))

    # D · 어순 배열
    p.set_qa(D, *B2.make_D(
        tokens=["involve", "users", "in", "the", "design", "process",
                "produce", "a", "better", "building"],
        cues=["involve", "produce"],
        answer_sentence="Involving users in the design process produces a better building.",
        reason="involve→Involving(동명사 주어), produce→produces(수 일치)로 변형해 어순을 맞춘다.",
    ))

    # E · 요약문 빈칸(객관식) — 지문도 함께 제시
    p.set_qa(E, *B2.make_E(
        s,
        before="When a building's real users are ",
        mid=" during design, the result is greater satisfaction and ",
        after=" costs for the institution.",
        choice_pairs=[("ignored", "higher"), ("consulted", "lower"), ("consulted", "higher"),
                      ("replaced", "lower"), ("ignored", "lower")],
        answer_no=2,
        reason=("지문은 사용자를 '자문(consult)'하면 만족이 커지고 비용이 '줄어든다(lower)'고 하므로 "
                "(A) consulted, (B) lower. 따라서 ②."),
    ))

    # F · 빈칸추론
    p.set_qa(F, *B2.make_F(
        before=("Understanding how each type of user experiences the current medical environment, "
                "as well as how each reacts to your prospective designs, inevitably produces "),
        after=". People are more satisfied with a new building if they have been consulted.",
        choices=[
            "a better building",
            "a cheaper contract",
            "a stricter regulation",
            "a larger profit margin",
            "a shorter waiting line",
        ],
        answer_no=1,
        reason=("빈칸 앞은 '각 사용자의 경험을 이해하면'이고 글 전체 논지가 '사용자 이해 → 더 나은 "
                "건물'이므로 ①이 앞뒤 논리로 유일하게 복원된다."),
        wrong={
            2: "계약 비용은 '사용자 이해→더 나은 결과' 맥락과 무관하다(무관).",
            3: "규제 강화는 글과 무관하다(무관).",
            4: "이윤 마진은 사용자 이해→건물 개선 논리와 어긋난다(무관).",
            5: "대기 줄 단축은 글에 언급이 없다(무관).",
        },
    ))

    # G · 내용일치 개수
    p.set_qa(G, *B2.make_G(
        s,
        statements=[
            "환자와 방문객은 대개 응급 상황 때문에 병원 건물을 비정기적으로 이용한다.",
            "행정 부서의 관점은 건물을 정기적으로 쓰는 의료진의 관점과 크게 다르다.",
            "설계 과정에서 자문을 받은 사람들은 새 건물에 오히려 덜 만족한다.",
            "대규모 기관에서 사용자 참여는 생산성 향상과 비용 절감으로 이어질 수 있다.",
            "뛰어난 설계는 비용을 내는 고객의 의견만 반영하면 충분하다.",
        ],
        match_count=3,
        reason="일치하는 것은 (a),(b),(d) 세 개이므로 정답은 ③(3개).",
        per_stmt={
            1: "일치 — patients and visitors ~ irregularly, often ~ life-threatening emergencies.",
            2: "일치 — perspectives ~ differ significantly from ~ medical staff who use it regularly.",
            3: "불일치 — 지문은 자문받은 사람이 '더 만족한다(more satisfied)'고 한다.",
            4: "일치 — this can translate into increased productivity ~ lower costs.",
            5: "불일치 — 지문은 고객뿐 아니라 '사용자'도 참여시켜야 한다고 한다.",
        },
    ))
    return p


def main() -> int:
    passages = [build_passage()]
    validator.validate_passages(passages, TYPE_ORDER2)
    nums = validator.validate_numbering(passages, 1, TYPE_ORDER2)
    print("검증 통과 — 문항 번호:", nums)
    out = ROOT / "output" / "Gateway_2회_샘플.pdf"
    renderer.render_pdf(passages, out, header_note="고3 영어 · 14강 Gateway (변형문제 2회)",
                        type_order=TYPE_ORDER2, prompts=TYPE_PROMPTS2, labels=TYPE_LABELS2)
    print("생성 완료:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
