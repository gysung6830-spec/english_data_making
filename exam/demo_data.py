"""데모용 지문 데이터 — 지문마다 '정본 텍스트 하나'를 6종이 공유한다.

명세서 부록 샘플: 지문1(DNA)·지문2(star manager).
각 지문은 Source(문장 리스트) 하나이며, build.py 변형기로 6종을 파생하므로
"유형마다 지문이 다른" 문제가 없다(연결 텍스트는 모두 동일, 밑줄/치환 부분만 다름).
"""
from __future__ import annotations

from . import build as B
from .types import (
    CONTENT,
    GRAMMAR,
    INSERT,
    ORDER,
    SHORT_ANSWER,
    TOPIC,
    VOCAB,
    Passage,
    Source,
)

# ===========================================================================
# 지문 1 — DNA (정본 7문장)
# ===========================================================================
DNA = Source(
    title="DNA, 자연의 정보 저장 장치",
    sentences=[
        "Every living cell carries a molecule called DNA, which works as nature's own hard drive.",
        "What makes it remarkable is not only that it stores information, but that it packs an enormous amount into a vanishingly small space.",
        "A single gram of DNA could, in theory, hold as much data as millions of ordinary hard drives combined.",
        "It is also astonishingly durable, surviving in bone and ice for tens of thousands of years.",
        "Inspired by such efficiency, researchers have begun to encode digital files into synthetic DNA.",
        "The technique is still slow and expensive, but it allows information to be preserved for thousands of years.",
        "One day, our libraries and photographs may be stored safely inside molecules.",
    ],
)


def _passage_dna() -> Passage:
    p = Passage(title=DNA.title)
    s = DNA.sentences

    # ① 순서 — S0=주어진 글, 나머지 6문장을 3덩어리로 쪼개 라벨을 섞음
    p.set_qa(ORDER, *B.make_order(
        s, given_n=1, block_sizes=[2, 2, 2], display=[2, 1, 3],
        reason=("(B)=밀도(remarkable~small space)로 특징을 잇고, (A)의 It is also와 "
                "such efficiency가 (B)의 내용을 받아 durable·응용으로 확장하며, (C)의 "
                "The technique가 (A)의 encode를 이어받아 마무리한다. 따라서 (B)-(A)-(C)."),
    ))

    # ② 삽입 — 같은 글에서 S4 한 문장만 빼냄
    p.set_qa(INSERT, *B.make_insert(
        s, remove_idx=4,
        reason=("주어진 문장의 'such efficiency'는 앞의 밀도·내구성(①~③ 부근)을 가리키고, "
                "'researchers have begun to encode ~'는 뒤 문장 'The technique'로 자연스럽게 "
                "이어진다. 따라서 정답은 ④."),
    ))

    # ③ 주제 — 원본 그대로 + 영어 선지
    p.set_qa(TOPIC, *B.make_topic(
        s,
        choices=[
            "the reason silicon chips replaced paper blueprints in modern factories",
            "DNA's remarkable capacity to preserve information and its promise for data storage",
            "why DNA is too unstable to keep genetic instructions for very long",
            "the process by which an organism digests and absorbs nutrients from food",
            "the failure of scientists to store any digital files inside living cells",
        ],
        answer_no=2,
        reason=("지문은 DNA가 좁은 공간에 방대한 정보를 안정적으로 오래 보관한다는 점과 이를 "
                "디지털 저장에 응용하려는 시도를 다룬다. 정답 ②는 이를 핵심어의 유의어"
                "(preserve information, capacity)로 바꿔 표현했다."),
        wrong={
            1: "blueprint·silicon 같은 지문 단어를 썼지만 반도체가 청사진을 대체한 이유는 없다(무관).",
            3: "지문은 DNA가 매우 '안정적'이라 했는데 선지는 '불안정'하다며 반대로 말한다(모순).",
            4: "organism이라는 단어만 빌려왔을 뿐 소화·흡수 과정은 글과 무관하다(무관).",
            5: "지문은 디지털 파일 저장을 이미 시작했다는데 선지는 '실패했다'고 하여 반대다(모순).",
        },
    ))

    # ④ 어휘(방식1: 반의어) — 같은 글에서 밑줄 5개만 원본과 다름
    p.set_qa(VOCAB, *B.make_vocab(
        s,
        marks=[
            (1, "remarkable", "notable"),        # 유의어
            (1, "small", "tiny"),                # 유의어
            (3, "durable", "fragile"),           # 반의어 → 정답
            (4, "efficiency", "effectiveness"),  # 유의어
            (5, "expensive", "costly"),          # 유의어
        ],
        answer_no=3,
        reason=("[반의어형] ③ 문장은 DNA가 뼈·얼음 속에서 수만 년을 '견딘다'는 내용이므로 "
                "문맥상 durable(안정적인) 계열이라야 한다. 그런데 fragile(부서지기 쉬운)은 "
                "정반대라 부적절하다. 나머지 notable·tiny·effectiveness·costly는 원문 단어의 "
                "유의어로 문맥에 맞게 쓰였다."),
    ))

    # ⑤ 어법(복수정답) — 같은 글에서 밑줄 8개, 그중 3개만 오답형
    p.set_qa(GRAMMAR, *B.make_grammar(
        s,
        marks=[
            (0, "which", "which"),          # ① 관계사(적절)
            (1, "packs", "pack"),           # ② 수 일치 오류(it packs)
            (2, "combined", "combined"),    # ③ 분사(적절)
            (3, "surviving", "surviving"),  # ④ 분사구문(적절)
            (4, "have", "has"),             # ⑤ 수 일치 오류(researchers have)
            (5, "allows", "allow"),         # ⑥ 수 일치 오류(it allows)
            (5, "preserved", "preserved"),  # ⑦ 수동(적절)
            (6, "stored", "stored"),        # ⑧ 수동(적절)
        ],
        answer_nos=[2, 5, 6],
        reasons={
            2: "주어 it 은 단수이므로 pack → packs (수 일치).",
            5: "주어 researchers 는 복수이므로 has → have (수 일치).",
            6: "주어 it(the technique) 은 단수이므로 allow → allows (수 일치).",
        },
    ))

    # ⑥ 내용 일치 (한글 선지) — 서술형 앞
    p.set_qa(CONTENT, *B.make_content(
        s,
        choices=[
            "합성 DNA에 데이터를 저장하는 기술은 이미 빠르고 저렴하다.",
            "1그램의 DNA는 이론상 일반 하드 드라이브 수백만 개에 맞먹는 데이터를 담을 수 있다.",
            "DNA는 뼈나 얼음 속에서 몇 년밖에 보존되지 못한다.",
            "연구자들은 디지털 파일을 종이에 기록하기 시작했다.",
            "DNA는 정보를 넓은 공간에 느슨하게 저장한다.",
        ],
        answer_no=2,
        reason=("지문은 '1그램의 DNA가 이론상 일반 하드 드라이브 수백만 개와 맞먹는 데이터를 "
                "담을 수 있다(A single gram of DNA ~ millions of ordinary hard drives)'고 "
                "했으므로 ②가 글의 내용과 일치한다."),
        wrong={
            1: "지문은 그 기술이 '여전히 느리고 비싸다(still slow and expensive)'고 했으므로 "
               "'이미 빠르고 저렴하다'는 부분이 글과 정반대다.",
            3: "지문은 DNA가 뼈·얼음 속에서 '수만 년(tens of thousands of years)' 견딘다고 "
               "했으므로 '몇 년밖에'가 틀렸다.",
            4: "지문은 '합성 DNA(synthetic DNA)'에 부호화한다고 했으므로 '종이에 기록'이 "
               "틀렸다.",
            5: "지문은 정보를 '아주 작은 공간(vanishingly small space)'에 촘촘히 담는다고 "
               "했으므로 '넓은 공간에 느슨하게'가 틀렸다.",
        },
    ))

    # ⑦ 서술형 — 원본 + 파생 과제(영작·요약)
    p.set_qa(SHORT_ANSWER, *B.make_short(
        s,
        q1_prompt="본문에서 DNA를 'nature's own hard drive'라고 표현한 이유를 우리말로 서술하시오.",
        q1_answer=("DNA가 세포 안 아주 작은 공간에 생명체의 방대한 정보를 저장하고 오랫동안 "
                   "보관하는, 자연이 만든 정보 저장 장치와 같기 때문이다."),
        q2_prompt=("다음 <보기>의 단어를 모두 배열하여 '연구자들은 디지털 파일을 합성 DNA에 "
                   "저장(부호화)하기 시작했다'라는 뜻의 문장을 완성하시오. (동사는 원형 제공)"),
        q2_tokens=["researchers", "begin", "to", "encode", "digital", "files",
                   "into", "synthetic", "DNA"],
        q2_cues=["begin"],
        q2_answer="Researchers have begun to encode digital files into synthetic DNA.",
        q3_prompt="다음 요약문의 빈칸 (A), (B)에 제시어를 알맞은 형태로 바꿔 쓰시오.",
        q3_before="DNA ", q3_mid=(" vast amounts of information in a tiny space, so "
                                  "engineers are now "),
        q3_after=" to build archives inside it.",
        q3_cue_a="store", q3_cue_b="inspire", q3_ans_a="stores", q3_ans_b="inspired",
        q3_reason=("(A) 주어 DNA는 3인칭 단수 현재이므로 stores. (B) engineers are now ~ 로 "
                   "'영감을 받는' 수동이므로 inspired."),
    ))
    return p


# ===========================================================================
# 지문 2 — The Star Manager Trap (정본 7문장)
# ===========================================================================
STAR = Source(
    title="The Star Manager Trap",
    sentences=[
        "Many companies promote their very best performer into a management role.",
        "They assume that a star will naturally make a star boss.",
        "The two jobs, however, demand almost opposite skills.",
        "One rewards personal brilliance, while the other rewards the patience to develop other people.",
        "Placed in charge, the former star keeps chasing personal wins and neglects the slow work of coaching the team.",
        "The team stalls, and the celebrated hire slowly turns into a disappointment.",
        "In the end, the firm loses both an outstanding contributor and a capable manager.",
    ],
)


def _passage_star() -> Passage:
    p = Passage(title=STAR.title)
    s = STAR.sentences

    # ① 순서 — S0,S1=주어진 글, 나머지 5문장을 3덩어리로
    p.set_qa(ORDER, *B.make_order(
        s, given_n=2, block_sizes=[2, 2, 1], display=[2, 1, 3],
        reason=("(B)=however로 '두 역할이 정반대 능력을 요구한다'며 통념을 반박하고, (A)=Placed "
                "in charge로 그 결과(코칭 소홀·팀 정체)를 보이며, (C)=In the end로 '이중의 손해'를 "
                "맺는다. 따라서 (B)-(A)-(C)."),
    ))

    # ② 삽입 — S2(however 문장)만 빼냄
    p.set_qa(INSERT, *B.make_insert(
        s, remove_idx=2,
        reason=("주어진 문장은 however로 앞의 통념(스타=좋은 상사)을 뒤집고 'opposite skills'를 "
                "제시하며, 이는 뒤 문장 'One rewards ~ while the other ~'로 구체화된다. 따라서 "
                "정답은 ②."),
    ))

    # ③ 주제 — 원본 그대로
    p.set_qa(TOPIC, *B.make_topic(
        s,
        choices=[
            "why promoting your best performer is always the smartest leadership choice",
            "the history of management education in leading business schools",
            "the hidden cost of turning a skilled specialist into a leader of others",
            "practical tips for organizing a company sports team after work",
            "how individual skill alone guarantees success as a team manager",
        ],
        answer_no=3,
        reason=("지문은 뛰어난 전문가를 관리자로 올릴 때 두 역할이 요구하는 능력이 달라 회사가 "
                "'이중의 손해'를 본다고 지적한다. 정답 ③은 top performer·promotion을 유의어"
                "(skilled specialist, leader of others)로 바꿔 이 핵심을 담았다."),
        wrong={
            1: "promotion을 언급했지만 글은 승진이 '항상 최선'이라는 통념을 '반박'한다(모순).",
            2: "management를 언급했을 뿐 경영 교육의 역사는 글과 무관하다(무관).",
            4: "team이라는 단어만 빌려왔을 뿐 사내 스포츠팀 구성은 주제가 아니다(무관).",
            5: "지문은 개인 역량만으로는 좋은 관리자가 못 된다는데 선지는 성공을 '보장'한다며 반대다(모순).",
        },
    ))

    # ④ 어휘(방식2: 부정어 삽입) — 밑줄 단어는 원문 그대로, 정답 문장에만 부정어
    p.set_qa(VOCAB, *B.make_vocab(
        s,
        marks=[
            (0, "promote", "promote"),        # 원문 그대로
            (2, "opposite", "opposite"),      # 원문 그대로
            (3, "brilliance", "brilliance"),  # 원문 그대로
            (4, "neglects", "neglects"),      # 원문 그대로
            (6, "lose", "lose"),              # 원문 단어, 문장에 부정어 → 정답
        ],
        overrides={
            6: "In the end, the firm does not lose either an outstanding contributor or a capable manager.",
        },
        answer_no=5,
        reason=("[부정어 삽입형] 밑줄 단어는 모두 원문 그대로다. 글 전체는 회사가 뛰어난 실무자도 "
                "잃고 부실한 관리자도 얻는 '이중의 손해'를 본다고 한다. 그런데 ⑤ 문장에 부정어 "
                "'does not ~ either'가 들어가 '둘 다 잃지 않는다'는 뜻이 되어 글의 흐름과 모순된다. "
                "따라서 문맥상 부적절한 것은 ⑤이며, 나머지 promote·opposite·brilliance·neglects는 "
                "원문 그대로 문맥에 맞게 쓰였다."),
    ))

    # ⑤ 어법(복수정답) — 밑줄 8개, 그중 3개만 오답형
    p.set_qa(GRAMMAR, *B.make_grammar(
        s,
        marks=[
            (1, "make", "make"),          # ① 원형(적절)
            (2, "demand", "demands"),     # ② 수 일치 오류(two jobs demand)
            (3, "rewards", "rewards"),    # ③ 수 일치(One rewards, 적절)
            (4, "Placed", "Placing"),     # ④ 분사·태 오류(수동이어야)
            (4, "keeps", "keeps"),        # ⑤ 병렬(적절)
            (4, "neglects", "neglect"),   # ⑥ 병렬·수 일치 오류
            (5, "turns", "turns"),        # ⑦ 수 일치(적절)
            (6, "loses", "loses"),        # ⑧ 수 일치(적절)
        ],
        answer_nos=[2, 4, 6],
        reasons={
            2: "주어 The two jobs 는 복수이므로 demands → demand (수 일치).",
            4: "별은 '자리에 앉혀지는' 대상이므로 능동 Placing 이 아니라 과거분사 Placed (분사·태).",
            6: "앞의 keeps 와 병렬이고 주어가 3인칭 단수 현재이므로 neglect → neglects (병렬·수 일치).",
        },
    ))

    # ⑥ 내용 일치 (한글 선지) — 서술형 앞
    p.set_qa(CONTENT, *B.make_content(
        s,
        choices=[
            "관리자 역할과 실무 역할은 사실상 같은 능력을 요구한다.",
            "회사가 최고 성과자를 관리자로 올리면 대개 큰 이득을 본다.",
            "관리자로 승진한 스타는 팀을 코칭하기보다 개인적 성과를 계속 좇는 경향이 있다.",
            "실무에서의 개인적 탁월함은 관리자 역할이 보상하는 능력이다.",
            "승진한 스타 덕분에 팀 성과가 곧바로 향상된다.",
        ],
        answer_no=3,
        reason=("지문은 '자리에 앉은 former star가 개인적 성과를 좇고 팀 코칭의 더딘 일을 "
                "소홀히 한다(keeps chasing personal wins and neglects ~ coaching)'고 했으므로 "
                "③이 글의 내용과 일치한다."),
        wrong={
            1: "지문은 두 역할이 '거의 정반대 능력(opposite skills)'을 요구한다고 했으므로 "
               "'같은 능력'이 틀렸다.",
            2: "지문은 회사가 결국 뛰어난 실무자와 유능한 관리자를 '둘 다 잃는다(loses both)'고 "
               "했으므로 '큰 이득'이 정반대다.",
            4: "지문에서 개인적 탁월함(personal brilliance)을 보상하는 것은 '실무 역할'이고 "
               "관리자 역할은 '남을 키우는 인내'를 보상한다고 했으므로 주체가 뒤바뀌었다.",
            5: "지문은 스타가 관리자가 되면 '팀이 정체된다(The team stalls)'고 했으므로 "
               "'곧바로 향상된다'가 틀렸다.",
        },
    ))

    # ⑦ 서술형 — 원본 + 파생 과제
    p.set_qa(SHORT_ANSWER, *B.make_short(
        s,
        q1_prompt=("본문 마지막 문장의 'the firm loses both ~'가 구체적으로 무엇을 잃는다는 "
                   "뜻인지 우리말로 서술하시오."),
        q1_answer=("뛰어난 실무자(스타 성과자)를 관리자로 올리면서 그 실무 인재를 잃고, "
                   "동시에 팀을 제대로 이끌지 못하는 부실한 관리자를 떠안게 되는 것을 뜻한다."),
        q2_prompt=("다음 <보기>의 단어를 모두 배열하여 '회사는 뛰어난 실무자와 유능한 관리자를 "
                   "둘 다 잃는다'라는 뜻의 문장을 완성하시오. (동사는 원형 제공)"),
        q2_tokens=["the", "firm", "lose", "both", "an", "outstanding",
                   "contributor", "and", "a", "capable", "manager"],
        q2_cues=["lose"],
        q2_answer="The firm loses both an outstanding contributor and a capable manager.",
        q3_prompt="다음 요약문의 빈칸 (A), (B)에 제시어를 알맞은 형태로 바꿔 쓰시오.",
        q3_before="Promoting a star into management often ",
        q3_mid=", because the talent that has been ",
        q3_after=" over years is wasted.",
        q3_cue_a="backfire", q3_cue_b="build", q3_ans_a="backfires", q3_ans_b="built",
        q3_reason=("(A) 동명사구 주어(Promoting ~)는 단수 취급, 현재이므로 backfires. "
                   "(B) has been ~ 로 '쌓여 온' 수동·완료이므로 built."),
    ))
    return p


def demo_passages() -> list[Passage]:
    """데모 2지문(DNA, star manager)을 돌려준다."""
    return [_passage_dna(), _passage_star()]
