#!/usr/bin/env python3
"""업로드된 EBS 지문(2개)으로 만든 실제 샘플 — build.py + renderer 파이프라인.

지문1: 인간의 교제 욕구 / 지문2: 단일 재배와 잡초·해충
각 지문 정본에서 7종(순서·삽입·주제·어휘·어법·내용일치·서술형)을 파생한다.
실행: python sample_pdf.py  → output/PDF샘플_시험지.pdf
"""
from __future__ import annotations

from pathlib import Path

from exam import build as B
from exam import renderer, validator
from exam.types import (
    CONTENT, GRAMMAR, INSERT, ORDER, SHORT_ANSWER, TOPIC, VOCAB, Passage, Source,
)

ROOT = Path(__file__).resolve().parent

# ===========================================================================
# 지문 1 — 인간의 교제 욕구 (정본 6문장)
# ===========================================================================
P1 = Source(
    title="타인과의 교제를 향한 인간의 본성",
    sentences=[
        "Although the wish to be alone is often strong, its intensity varies from person to person.",
        "An equally impelling impulse, though, is to seek the company of others and to spend extended periods of time sharing activities.",
        "In these periods we exchange information and feelings in both conversational and non-verbal forms (facial expressions, eye contact, gestures, touching, and so on).",
        "We need other people to provide us with love, support, approval, bodily contact, reassurance, physical help and a myriad of other practical, physical and emotional needs.",
        "In a very basic sense we need others to confirm that we are there, that we exist and that we have an identity that is unique and separate from anyone else.",
        "Thus, we generally cannot exist for too long without seeking companionship.",
    ],
)


def _passage1() -> Passage:
    p = Passage(title=P1.title)
    s = P1.sentences

    p.set_qa(ORDER, *B.make_order(
        s, given_n=1, block_sizes=[2, 2, 1], display=[2, 1, 3],
        reason=("주어진 글은 혼자 있고 싶은 소망을 언급한다. (B)가 'though'로 그만큼 강한 "
                "'함께 있으려는 충동'을 대비하고 'In these periods'로 그 시간을 이어받으며, "
                "(A)가 우리가 타인을 필요로 하는 이유(필요 제공·정체성 확인)를 들고, (C)가 "
                "'Thus'로 결론짓는다. 따라서 (B)-(A)-(C)."),
    ))

    p.set_qa(INSERT, *B.make_insert(
        s, remove_idx=2,
        reason=("주어진 문장의 'In these periods'는 앞 문장의 '다른 사람과 함께 긴 시간을 "
                "보내며 활동을 공유하는' 그 시간을 가리키고, 이어 '우리는 다른 사람을 "
                "필요로 한다'로 연결된다. 따라서 정답은 ②."),
    ))

    p.set_qa(TOPIC, *B.make_topic(
        s,
        choices=[
            "why the desire to be alone always overpowers the need for others",
            "the deep human need for companionship and for others to confirm our identity",
            "effective non-verbal techniques for winning a business negotiation",
            "how facial expressions evolved differently across human cultures",
            "the idea that people can thrive for long periods in total isolation",
        ],
        answer_no=2,
        reason=("글은 혼자 있고 싶은 마음도 있지만 그만큼 강한, 타인과 함께하며 사랑·인정을 얻고 "
                "자신의 존재·정체성을 확인받으려는 '교제의 욕구'가 핵심이다. 정답 ②는 이를 "
                "유의어(companionship, confirm our identity)로 담았다."),
        wrong={
            1: "alone(혼자)이라는 지문 단어를 썼지만, 글은 함께 있으려는 충동을 강조하므로 "
               "'항상 압도한다'는 반대다(모순).",
            3: "non-verbal 같은 단어만 빌렸을 뿐 협상 기술은 글과 무관하다(무관).",
            4: "facial expressions 단어만 빌렸을 뿐 표정의 문화적 진화는 글과 무관하다(무관).",
            5: "글은 교제 없이는 오래 존재할 수 없다고 했으므로 '완전한 고립 속에서 잘 지낸다'는 "
               "반대다(모순).",
        },
    ))

    p.set_qa(VOCAB, *B.make_vocab(
        s,
        marks=[
            (0, "strong", "powerful"),          # 유의어
            (1, "extended", "prolonged"),       # 유의어
            (2, "exchange", "share"),           # 유의어
            (4, "unique", "identical"),         # 반의어 → 정답
            (5, "companionship", "fellowship"), # 유의어
        ],
        answer_no=4,
        reason=("[반의어형] ④ 문장은 '다른 누구와도 구별되는(separate)' 정체성이라는 맥락이므로 "
                "unique(고유한)라야 한다. 그런데 identical(동일한)은 정반대라 부적절하다. 나머지 "
                "powerful·prolonged·share·fellowship은 유의어로 문맥에 맞게 쓰였다."),
    ))

    p.set_qa(GRAMMAR, *B.make_grammar(
        s,
        marks=[
            (0, "varies", "vary"),          # ① 수 일치 오류(its intensity)
            (1, "impelling", "impelling"),  # ② 분사 형용사(적절)
            (1, "seek", "seek"),            # ③ 부정사 보어(적절)
            (2, "exchange", "exchange"),    # ④ 수 일치(we exchange, 적절)
            (3, "provide", "provide"),      # ⑤ to부정사(적절)
            (4, "exist", "exists"),         # ⑥ 수 일치 오류(we exist)
            (4, "have", "has"),             # ⑦ 수 일치 오류(we have)
            (5, "seeking", "seeking"),      # ⑧ 동명사(적절)
        ],
        answer_nos=[1, 6, 7],
        reasons={
            1: "주어 its intensity 는 단수이므로 vary → varies (수 일치).",
            6: "주어 we 는 복수이므로 exists → exist (수 일치).",
            7: "주어 we 는 복수이므로 has → have (수 일치).",
        },
    ))

    p.set_qa(CONTENT, *B.make_content(
        s,
        choices=[
            "우리는 사랑·지지·인정·신체적 접촉을 얻기 위해 타인이 필요하지만, 정서적 안심을 "
            "위해서는 타인이 필요하지 않다.",
            "우리는 다른 사람들의 존재와 정체성을 확인해 주기 위해 그들과 교제한다.",
            "사람들은 대화뿐 아니라 표정·눈 맞춤 같은 비언어적 방식으로도 정보와 감정을 "
            "주고받는다.",
            "우리가 비언어적 형태로 감정을 교환하는 것은 언어적 대화가 불가능하기 때문이다.",
            "혼자 있고 싶은 소망은 나이가 들수록 점점 더 강해진다.",
        ],
        answer_no=3,
        reason=("지문은 '이 시간 동안 우리는 대화적·비언어적 형태(표정, 눈 맞춤 등) 둘 다로 정보와 "
                "감정을 교환한다'고 했다. ③이 이를 유의어로 바꿔 표현한 일치 진술이다."),
        wrong={
            1: "지문은 사랑·지지·인정·신체 접촉과 함께 '안심(reassurance)·정서적 필요'까지 모두 "
               "타인이 필요하다고 했다. '정서적 안심을 위해서는 필요 없다'로 한 요소만 뒤집었다. "
               "(부분 일치 + 한 요소 왜곡)",
            2: "지문은 '다른 사람들이 우리의 존재·정체성을 확인해 준다'고 했는데, 선지는 우리가 "
               "그들의 것을 확인해 준다며 주체와 대상을 뒤바꿨다. (주체 바꿔치기)",
            4: "지문은 대화적·비언어적 형태 '둘 다'로 교환한다고 했을 뿐, '언어적 대화가 "
               "불가능해서'라는 인과는 없다. (인과 날조·역전)",
            5: "소망의 강도가 '사람마다 다르다'고는 했으나 '나이가 들수록 강해진다'는 언급은 "
               "지문에 없다. (미언급)",
        },
    ))

    p.set_qa(SHORT_ANSWER, *B.make_short(
        s,
        q1_prompt="본문에서 우리가 다른 사람들을 필요로 하는 이유를 두 가지 이상 우리말로 서술하시오.",
        q1_answer=("사랑·지지·인정·신체적 접촉·안심 같은 실질적·정서적 필요를 제공받기 위해서, "
                   "그리고 우리가 존재하며 고유한 정체성을 지녔음을 확인받기 위해서이다."),
        q2_prompt=("다음 <보기>의 단어를 모두 배열하여 '우리는 교제를 추구하지 않고는 오랫동안 "
                   "존재할 수 없다'라는 뜻의 문장을 완성하시오. (동사는 원형 제공)"),
        q2_tokens=["we", "cannot", "exist", "for", "long", "without", "seek",
                   "companionship"],
        q2_cues=["seek"],
        q2_answer="We cannot exist for long without seeking companionship.",
        q3_prompt="다음 요약문의 빈칸 (A), (B)에 제시어를 알맞은 형태로 바꿔 쓰시오.",
        q3_before="Although the wish to be alone ",
        q3_mid=" from person to person, humans still need the ",
        q3_after=" of their identity by others.",
        q3_cue_a="vary", q3_cue_b="confirm", q3_ans_a="varies", q3_ans_b="confirmation",
        q3_reason=("(A) 주어 the wish 는 단수 현재이므로 varies. (B) 'the ___ of ~' 구조로 "
                   "명사가 필요하므로 품사를 바꿔 confirmation."),
    ))
    return p


# ===========================================================================
# 지문 2 — 단일 재배와 원치 않는 종 (정본 9문장)
# ===========================================================================
P2 = Source(
    title="단일 재배가 부른 뜻밖의 생태적 결과",
    sentences=[
        "At one end of the spectrum of transformations was the forest gardening as practiced by the peoples of New Guinea and Amazonia that mimicked natural growth and left minimal traces on the land.",
        "At the other end was monoculture: cultivating only one species of plant or raising only one species of animal.",
        "The beginnings of monoculture can be seen in the wheat fields of the Middle East, the rice paddies of China, and the herds of sheep and goats on the Eurasian steppe.",
        "Biologically speaking, these species suddenly became very successful, measured by their rates of survival and reproduction.",
        "So did other, unwanted species.",
        "Crops that ripened or were stored after harvesting attracted rats, mice, sparrows, and roaches.",
        "Water pools provided habitats for mosquitoes.",
        "Garbage and human or animal waste attracted flies.",
        "Thanks to humans, weeds and pests were also biological winners.",
    ],
)


def _passage2() -> Passage:
    p = Passage(title=P2.title)
    s = P2.sentences

    p.set_qa(ORDER, *B.make_order(
        s, given_n=2, block_sizes=[3, 2, 2], display=[2, 1, 3],
        reason=("주어진 글은 변화의 두 끝(산림 정원 가꾸기 vs 단일 재배)을 제시한다. (B)가 단일 "
                "재배의 시작과 재배종의 성공, 'So did other, unwanted species'로 잇고, (A)가 그 "
                "구체적 예(농작물이 쥐를, 물웅덩이가 모기를 끌어들임)를 들며, (C)가 파리와 "
                "'인간 덕분에 잡초·해충도 승자'라는 결론으로 맺는다. 따라서 (B)-(A)-(C)."),
    ))

    p.set_qa(INSERT, *B.make_insert(
        s, remove_idx=4,
        reason=("주어진 문장 'So did other, unwanted species'는 앞 문장(재배종이 갑자기 성공적이 "
                "되었다)을 받아 '원치 않는 종들도 마찬가지였다'로 잇고, 뒤의 구체적 예(쥐·모기·"
                "파리)를 이끈다. 따라서 정답은 ③."),
    ))

    p.set_qa(TOPIC, *B.make_topic(
        s,
        choices=[
            "how single-species farming unintentionally helped weeds and pests flourish",
            "the best modern methods for keeping rats and mosquitoes out of homes",
            "why monoculture eliminated nearly all unwanted species from farmland",
            "the history of forest gardening techniques in New Guinea and Amazonia",
            "how growing many different species at once reduced crop success",
        ],
        answer_no=1,
        reason=("글은 단일 재배(monoculture)가 재배종뿐 아니라 잡초·해충 같은 원치 않는 종들까지 "
                "번성시켰다는 생태적 결과를 다룬다. 정답 ①은 이를 유의어(single-species farming, "
                "flourish)로 담았다."),
        wrong={
            2: "rats·mosquitoes 단어만 빌렸을 뿐, 해충을 집에서 막는 현대적 방법은 글과 "
               "무관하다(무관).",
            3: "글은 단일 재배가 원치 않는 종들을 오히려 번성시켰다고 했는데, 선지는 '거의 다 "
               "제거했다'며 정반대다(모순).",
            4: "forest gardening·New Guinea 같은 지문 단어를 썼지만, 그 기법의 역사는 글의 "
               "주제가 아니다(무관).",
            5: "성공한 종은 '단일 재배'로 인한 것인데, 선지는 '여러 종을 함께 길러 작물 성공이 "
               "줄었다'며 반대다(모순).",
        },
    ))

    p.set_qa(VOCAB, *B.make_vocab(
        s,
        marks=[
            (0, "minimal", "slight"),           # 유의어
            (1, "cultivating", "growing"),      # 유의어
            (3, "successful", "unsuccessful"),  # 반의어 → 정답
            (5, "attracted", "drew"),           # 유의어
            (8, "winners", "victors"),          # 유의어
        ],
        answer_no=3,
        reason=("[반의어형] ③ 문장은 이 종들이 생존율·번식률로 볼 때 '갑자기 매우 ~했다'는 "
                "맥락이고 뒤에 잡초·해충도 '승자'가 되었다고 하므로 successful(성공적인)이라야 "
                "한다. unsuccessful(실패한)은 정반대라 부적절하다. 나머지 slight·growing·drew·"
                "victors는 유의어이다."),
    ))

    p.set_qa(GRAMMAR, *B.make_grammar(
        s,
        marks=[
            (0, "left", "leaving"),       # ① 병렬 오류(mimicked ~ and left)
            (1, "raising", "raising"),    # ② 병렬(적절)
            (2, "seen", "seen"),          # ③ 수동(적절)
            (3, "measured", "measured"),  # ④ 분사(적절)
            (5, "ripened", "ripened"),    # ⑤ 관계절 동사(적절)
            (5, "attracted", "attract"),  # ⑥ 시제·수 일치 오류
            (6, "provided", "provided"),  # ⑦ 수 일치(적절)
            (8, "were", "was"),           # ⑧ 수 일치 오류(weeds and pests)
        ],
        answer_nos=[1, 6, 8],
        reasons={
            1: "앞의 mimicked 와 병렬을 이루는 과거동사여야 하므로 leaving → left (병렬).",
            6: "문맥이 과거이고 주어 Crops 에 맞춰야 하므로 attract → attracted (시제·수 일치).",
            8: "주어 weeds and pests 는 복수이므로 was → were (수 일치).",
        },
    ))

    p.set_qa(CONTENT, *B.make_content(
        s,
        choices=[
            "단일 재배의 시작은 중동의 밀밭, 중국의 논, 그리고 남아메리카의 양·염소 무리에서 "
            "볼 수 있다.",
            "한 종만 재배하거나 기르는 방식은 자연적 성장을 모방해 땅에 최소한의 흔적만 "
            "남겼다.",
            "익거나 수확 후 저장된 농작물은 쥐·참새 같은 동물들을 끌어들였다.",
            "잡초와 해충이 번성한 것은 인간이 그들을 일부러 길렀기 때문이다.",
            "농부들은 모기를 막기 위해 물웅덩이를 모두 없앴다.",
        ],
        answer_no=3,
        reason=("지문은 '익거나 수확 후 저장된 농작물이 쥐·생쥐·참새·바퀴벌레를 끌어들였다'고 "
                "했다. ③이 이를 유의어로 바꿔 표현한 일치 진술이다."),
        wrong={
            1: "밀밭(중동)·논(중국)까지는 맞지만, 지문은 양·염소 무리를 '유라시아 스텝(Eurasian "
               "steppe)'이라 했다. '남아메리카'로 한 요소만 바꿨다. (부분 일치 + 한 요소 왜곡)",
            2: "'자연적 성장을 모방해 땅에 최소한의 흔적만 남긴' 것은 '산림 정원 가꾸기'인데, "
               "선지는 이를 '단일 재배'의 특징으로 뒤바꿨다. (주체 바꿔치기)",
            4: "지문은 '인간 덕분에' 잡초·해충이 승자가 되었다고 했을 뿐, 인간이 그들을 '일부러 "
               "길렀다'는 인과는 없다. (인과 날조·역전)",
            5: "물웅덩이가 모기 서식지였다고는 했으나, 농부들이 그것을 없앴다는 내용은 지문에 "
               "없다. (미언급)",
        },
    ))

    p.set_qa(SHORT_ANSWER, *B.make_short(
        s,
        q1_prompt="본문에서 단일 재배가 가져온 '뜻밖의(원치 않은) 생태적 결과'가 무엇인지 우리말로 서술하시오.",
        q1_answer=("재배하려던 작물뿐 아니라 쥐·모기·파리 같은 해충과 잡초 등 원치 않는 종들까지 "
                   "함께 번성하게 된 것이다."),
        q2_prompt=("다음 <보기>의 단어를 모두 배열하여 '잡초와 해충도 생물학적 승자였다'라는 뜻의 "
                   "문장을 완성하시오. (동사는 원형 제공)"),
        q2_tokens=["weeds", "and", "pests", "be", "also", "biological", "winners"],
        q2_cues=["be"],
        q2_answer="Weeds and pests were also biological winners.",
        q3_prompt="다음 요약문의 빈칸 (A), (B)에 제시어를 알맞은 형태로 바꿔 쓰시오.",
        q3_before="As farmers ",
        q3_mid=" a single species, unwanted animals such as rats and insects also ",
        q3_after=".",
        q3_cue_a="cultivate", q3_cue_b="thrive", q3_ans_a="cultivated", q3_ans_b="thrived",
        q3_reason=("(A) 과거 시제 문맥이므로 cultivated. (B) 주어 unwanted animals 는 복수이고 "
                   "과거이므로 thrived."),
    ))
    return p


def main() -> int:
    passages = [_passage1(), _passage2()]
    validator.validate_passages(passages)
    nums = validator.validate_numbering(passages, start=1)
    print("검증 통과 — 문항 번호:", nums)
    out = ROOT / "output" / "PDF샘플_시험지.pdf"
    renderer.render_pdf(passages, out, header_note="고3 영어 · EBS 올림포스 변형")
    print("생성 완료:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
