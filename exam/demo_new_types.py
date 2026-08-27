"""데모(무료 미리보기)용 — 통합본에 새로 들어온 유형의 예시 문항.

제목·연결어·내용 O/X 영어판·어휘(원문단어형·부정어형)·어법 서술형은 기존 데모에 없던
유형이라
여기서 따로 만든다. 실제 생성과 똑같은 빌더(build.py)를 거치므로 조판 결과도 같다.

어법 두 유형(GRAMMAR·GRAMMAR_FIX)은 여기 것이 demo_data 의 것을 대신한다 —
실제 생성과 같이 '다시 쓴 지문' 위에 서야 하기 때문이다(generators/grammar.py 참고).
두 문항은 서로 다른 다시쓰기를 쓰므로 같은 밑줄을 두 번 묻지 않는다.
"""
from __future__ import annotations

from . import build as B
from .demo_data import DNA, STAR
from . import build2 as B2
from .generators.pair_odd import build_pairs
from .types import (
    CONTENT_2, GRAMMAR, GRAMMAR_FIX, LINKER, PAIR_ODD, TITLE, VOCAB_2, VOCAB_3,
    Passage,
)

# 데모 지문 제목 -> 이 파일이 채워 줄 문항들
_BY_TITLE: dict[str, "Passage"] = {}


def _dna() -> Passage:
    p = Passage(title=DNA.title)
    s = DNA.sentences

    # 제목 — 명사구·대구·콜론형으로 통일
    p.set_qa(TITLE, *B.make_title(
        s,
        choices=[
            "Why Cold Storage Beats Every Other Archive",
            "The Molecule That Outlasts Our Machines",
            "Reading the Genes of Ancient Animals",
            "Cheaper Chips, Shorter Memories",
            "A Warning Against Trusting Digital Records",
        ],
        answer_no=2,
        reason=("글은 DNA가 ①엄청난 밀도로 정보를 담고 ②수만 년을 견디며 ③그래서 디지털 파일을 "
                "DNA에 새기는 연구가 시작됐다고 전개한다. '우리 기계보다 오래 남는 분자'가 밀도와 "
                "내구성, 그리고 저장 매체라는 논점을 한 줄로 압축한다."),
        wrong={
            1: "범위 비틀기 — 저온 보관은 지문에 없고, 글의 논점은 보관 환경이 아니라 DNA 자체다.",
            3: "초점 이동 — 고대 생물의 유전자 해독은 내구성의 예시일 뿐 글의 논점이 아니다.",
            4: "방향 반전 — 지문은 하드드라이브를 DNA와 대비하는 쪽이지 그 발전을 다루지 않는다.",
            5: "근거 없음 — 디지털 기록을 믿지 말라는 경고는 글에 없다(오히려 보존을 낙관한다).",
        },
    ))

    # 연결어 — (A) 4번 문장(부연·병렬) · (B) 6번 문장(대조). 원문에 연결어가 없는
    # 자리라 remove 는 비운다.
    p.set_qa(LINKER, *B2.make_linker(
        s, 4, 6, "", "",
        pairs=[("In addition", "However"), ("However", "Therefore"),
               ("For example", "Moreover"), ("In addition", "Similarly"),
               ("Nevertheless", "However")],
        answer_no=1,
        reason=("(A) 앞은 '아주 작은 공간에 엄청난 양을 담는다(밀도)', 뒤는 '뼈와 얼음 속에서 "
                "수만 년을 견딘다(내구성)'로, 서로 다른 장점을 하나 더 얹는 자리다 → In addition. "
                "(B) 앞은 '연구가 시작됐다'는 진전이고 뒤는 '아직 느리고 비싸다'는 한계라 뒤집는 "
                "자리다 → However. 실제로 원문도 그 문장 안에서 but 으로 뒤집는다."),
        wrong={
            2: "(A) 자리는 앞뒤가 대조가 아니라 장점을 더하는 관계라 However 가 맞지 않는다.",
            3: "(A) 뒤 문장은 앞의 예시가 아니라 별개의 장점이므로 For example 이 맞지 않는다.",
            4: "(A) 는 맞지만 (B) 자리는 앞의 진전을 뒤집는 자리라 Similarly 가 정반대다.",
            5: "(A) 자리에는 뒤집을 앞 진술이 없어 Nevertheless 가 성립하지 않는다.",
        },
    ))

    p.set_qa(CONTENT_2, *B.make_content_ox(
        s,
        statements=[
            "Every living cell contains DNA, which the passage compares to a hard drive.",
            "DNA loses its stored information within a few years unless it is frozen.",
            "Researchers write digital files into synthetic DNA because the molecule is "
            "remarkably efficient.",
            "The passage claims that synthetic DNA is already cheaper than magnetic tape.",
            "Only laboratory-made DNA, not natural DNA, can survive inside bone and ice.",
            "According to the passage, storing data in DNA is a fast process today.",
            "Ancient DNA has been read from bones, which proves it can be edited as well.",
            "The passage says that libraries will certainly be replaced by molecules.",
            "DNA can hold information in a space far smaller than any ordinary drive.",
            "Scientists began encoding files into DNA before they noticed how durable it was.",
        ],
        truths=[True, False, False, False, False,
                False, False, False, True, False],
        reasons=[
            "첫 문장 'Every living cell carries a molecule called DNA, which works as "
            "nature's own hard drive' 를 그대로 옮긴 일치 진술이다.",
            "지문은 정반대로 '뼈와 얼음 속에서 수만 년을 견딘다'고 했다. 얼리지 않으면 "
            "몇 년 만에 사라진다는 것은 지문과 어긋난다. (부분 일치 + 한 요소 왜곡)",
            "연구가 시작된 계기는 맞지만(Inspired by such efficiency), 지문은 이를 "
            "'영감을 받았다'고 했지 '효율적이기 때문에 쓴다'는 인과로 못 박지 않았다. "
            "덧붙여 진술은 원문에 없는 단정을 더한다. (인과 날조)",
            "자기 테이프와의 비용 비교는 지문에 없다. 오히려 지문은 그 기술이 아직 "
            "'비싸다'고 했다. (미언급인데 그럴듯)",
            "지문은 DNA 일반이 뼈와 얼음 속에서 견딘다고 했지, 실험실에서 만든 것만 "
            "그렇다고 한 적이 없다. (조건 삭제·왜곡)",
            "지문은 'The technique is still slow' 라고 했다. 정반대다. (정도·빈도 과장)",
            "고대 DNA를 읽어 낸다는 이야기는 내구성의 예시일 뿐, '편집할 수 있다'는 "
            "결론은 지문에 없다. (인과 날조)",
            "지문은 'may be stored' 라는 가능성을 말했을 뿐 '반드시 대체된다'고 하지 "
            "않았다. (정도·빈도 과장)",
            "지문은 '엄청난 양을 아주 좁은 공간에 담는다(packs an enormous amount into "
            "a vanishingly small space)'고 했다. 이를 바꿔 표현한 일치 진술이다.",
            "지문은 내구성을 먼저 말한 뒤 'Inspired by such efficiency' 로 연구를 "
            "잇는다. 순서가 뒤집혔다. (시점 뒤집기)",
        ],
    ))

    # 어휘 — 원문단어형(정답만 반의어, 나머지 4개는 원문 그대로)
    p.set_qa(VOCAB_2, *B.make_vocab(
        s,
        marks=[(1, "remarkable", "remarkable"), (1, "enormous", "tiny"),
               (2, "ordinary", "ordinary"), (4, "efficiency", "efficiency"),
               (5, "preserved", "preserved")],
        answer_no=2,
        reason=("② 그 문장은 DNA가 '아주 작은 공간에 엄청난 양을 밀어 넣는다'는 뜻이므로 "
                "tiny(적은)가 아니라 enormous(엄청난)여야 한다. 나머지 넷은 원문 그대로라 "
                "당연히 자연스럽다."),
    ))

    # 어휘 — 부정어형(밑줄은 원문 그대로, 정답 문장에 부정어를 넣어 흐름과 모순)
    p.set_qa(VOCAB_3, *B.make_vocab(
        s,
        marks=[(0, "carries", "carries"), (2, "hold", "hold"),
               (3, "never lasts", "never lasts"), (4, "researchers", "researchers"),
               (6, "stored", "stored")],
        answer_no=3,
        overrides={3: ("It never lasts in bone or ice, disappearing within a few "
                       "short years.")},
        reason=("나머지 넷은 원문 그대로라 흠이 없다. ③ 은 '전혀 오래가지 못한다'는 뜻이어서 "
                "바로 뒤의 '그런 효율에 영감을 받아 연구가 시작됐다'와 정면으로 모순된다. "
                "'오래 견딘다'는 뜻이어야 앞뒤가 이어진다."),
    ))
    # 어법 — 다시 쓴 지문 위에 낸다(원문 그대로면 외운 학생이 달라진 낱말만 찾는다)
    r1 = [
        "Inside every living cell sits a molecule called DNA, which serves as nature's own hard drive.",
        "What makes it extraordinary is not merely that it compresses information, but that it packs a huge quantity into a vanishingly small space.",
        "In theory, one single gram of DNA could carry as much data as millions of ordinary hard drives put together.",
        "It is remarkably tough as well, lasting inside bone and ice across tens of thousands of years.",
        "Impressed by such efficiency, researchers have started encoding digital files into synthetic DNA.",
        "Although the method remains slow and costly, it lets information be kept safe for thousands of years.",
        "Someday our libraries and photographs may rest safely within molecules.",
    ]
    p.set_qa(GRAMMAR, *B.make_grammar(
        r1,
        marks=[
            (0, "serves", "serves"),          # ① 관계사절 수 일치(적절)
            (1, "compresses", "compress"),    # ② 수 일치 오류(it compresses)
            (2, "put", "put"),                # ③ 과거분사(적절)
            (3, "lasting", "lasting"),        # ④ 분사구문(적절)
            (4, "have", "has"),               # ⑤ 수 일치 오류(researchers have)
            (5, "lets", "let"),               # ⑥ 수 일치 오류(it lets)
            (5, "kept", "kept"),              # ⑦ 수동(적절)
            (6, "rest", "rest"),              # ⑧ 조동사 뒤 원형(적절)
        ],
        answer_nos=[2, 5, 6],
        reasons={
            2: "선행하는 주어 it 은 단수이므로 compress → compresses (수 일치).",
            5: "주어 researchers 는 복수이므로 has → have (수 일치).",
            6: "주어 it(the method) 은 단수이므로 let → lets (수 일치).",
        },
    ))

    # 어법 서술형 — 또 다른 다시쓰기 위에. 틀린 넷을 찾아 바른 형태로 고쳐 쓴다.
    r2 = [
        "Every cell that is alive contains a molecule known as DNA, which acts like nature's own hard drive.",
        "Its remarkable quality lies not only in storing information but also in squeezing an enormous amount into an extremely small space.",
        "Just one gram of DNA might, at least in theory, keep as much data as millions of everyday hard drives combined.",
        "Because it is so tough, it can survive within bone and ice for tens of thousands of years.",
        "Researchers, inspired by that efficiency, have begun to write digital files into synthetic DNA.",
        "The method is still slow and expensive, yet it allows information to be preserved for thousands of years.",
        "One day the libraries and photographs we treasure may sit safely inside molecules.",
    ]
    p.set_qa(GRAMMAR_FIX, *B.make_grammar_fix(
        r2,
        marks=[
            (0, "known", "knowing"),          # ① 수동 관계 → 오류
            (1, "storing", "storing"),        # ② not only in ~ but also in ~ 병렬(적절)
            (2, "combined", "combining"),     # ③ 태 오류 → 오류
            (3, "survive", "survive"),        # ④ 조동사 뒤 원형(적절)
            (4, "have", "has"),               # ⑤ 수 일치 오류 → 오류
            (5, "preserved", "preserve"),     # ⑥ 태 오류 → 오류
        ],
        wrong_nos=[1, 3, 5, 6],
        reasons={
            1: "분자가 DNA라고 '불리는' 것이므로 능동 knowing 이 아니라 과거분사 known (태).",
            2: "not only in storing ~ but also in squeezing ~ 으로 동명사끼리 짝이 맞습니다(병렬·적절).",
            3: "hard drives 가 '합쳐진' 것이므로 combining → combined (태).",
            4: "조동사 can 뒤이므로 동사원형 survive 가 맞습니다(적절).",
            5: "주어 Researchers 는 복수이므로 has → have (수 일치).",
            6: "정보가 '보존되는' 것이므로 to be preserve → to be preserved (태).",
        },
        note="틀린 것은 ①③⑤⑥ 네 개, 옳은 것은 ②④ 두 개입니다.",
    ))
    # 어법·어휘 짝짓기 — ⓐ~ⓔ 중 정확히 2개(어법 1 + 어휘 1)만 부적절
    _ch, _no = build_pairs(2, 4, seed=0)          # ⓑ(어법) · ⓓ(어휘)
    p.set_qa(PAIR_ODD, *B2.make_A(
        s,
        marks=[
            (0, "works", "works"),          # ⓐ 관계절 수 일치(적절)
            (1, "packs", "pack"),           # ⓑ 어법 오류 — 주어 it 은 단수
            (2, "combined", "combined"),    # ⓒ 과거분사(적절)
            (3, "durable", "fragile"),      # ⓓ 어휘 오류 — 반의어 함정
            (5, "allows", "allows"),        # ⓔ 수 일치(적절)
        ],
        answer_no=_no,
        choices=_ch,
        reason=("부적절한 것은 ⓑ(어법)와 ⓓ(어휘) 둘입니다. / "
                "ⓐ 선행사 DNA(단수)를 받는 관계절 동사이므로 works 가 맞습니다(적절). / "
                "ⓑ pack → packs: 주어 it 이 단수이므로 단수동사여야 합니다 (어법). / "
                "ⓒ hard drives 가 '합쳐진' 것이므로 과거분사 combined 가 맞습니다(적절). / "
                "ⓓ fragile → durable: 뼈와 얼음 속에서 수만 년을 '견딘다'는 흐름이므로 "
                "'부서지기 쉬운'은 정반대입니다 (어휘·반의어 함정). / "
                "ⓔ 주어 it(the technique)이 단수이므로 allows 가 맞습니다(적절)."),
    ))
    return p


def _star() -> Passage:
    p = Passage(title=STAR.title)
    s = STAR.sentences

    p.set_qa(TITLE, *B.make_title(
        s,
        choices=[
            "How to Spot a Star Performer Early",
            "Rewarding Talent the Only Way We Know",
            "The Best Player Rarely Makes the Best Coach",
            "Why Teams Stall When Budgets Shrink",
            "Personal Brilliance Is All a Company Needs",
        ],
        answer_no=3,
        reason=("글은 최고 실무자를 관리자로 올리는 관행이 왜 실패하는지를 다룬다. 두 자리가 정반대 "
                "능력을 요구한다는 것이 논점이므로, '최고의 선수가 최고의 코치가 되는 일은 드물다'가 "
                "글 전체를 대구로 압축한다."),
        wrong={
            1: "초점 이동 — 인재를 어떻게 알아보느냐는 글이 다루지 않는다.",
            2: "방향 반전 — 글은 승진이 '올바른 보상'이라는 통념을 반박하는 쪽이다.",
            4: "근거 없음 — 예산 축소는 지문에 전혀 나오지 않는다.",
            5: "방향 반전 — 개인의 탁월함만으로는 부족하다는 것이 글의 요지다.",
        },
    ))

    # 연결어 — (A) 3번 문장은 원문이 'however' 를 문장 가운데 두므로 새로 빈칸을 놓고,
    # (B) 5번 문장은 앞의 대비를 실제 상황으로 옮기는 자리다.
    p.set_qa(LINKER, *B2.make_linker(
        s, 3, 5, "", "",
        pairs=[("However", "As a result"), ("Therefore", "However"),
               ("For example", "In contrast"), ("However", "Similarly"),
               ("Moreover", "As a result")],
        answer_no=1,
        reason=("(A) 앞은 '스타가 스타 상사가 될 것이라 여긴다'는 통념이고 뒤는 '두 자리는 거의 "
                "정반대 능력을 요구한다'는 반박이라 뒤집는 자리다 → However. (B) 앞은 그 정반대 "
                "능력이 무엇인지 밝힌 대목이고 뒤는 '스타를 앉혀 놓으니 개인 성과만 좇는다'는 "
                "귀결이므로 결과를 잇는 자리다 → As a result."),
        wrong={
            2: "(A) 는 앞의 통념을 뒤집는 자리라 결과를 잇는 Therefore 가 맞지 않는다.",
            3: "(A) 뒤 문장은 앞 진술의 예시가 아니라 반박이므로 For example 이 맞지 않는다.",
            4: "(A) 는 맞지만 (B) 자리는 결과를 잇는 자리라 Similarly 가 관계를 잘못 짚는다.",
            5: "(A) 자리에 Moreover 를 넣으면 통념을 오히려 더 밀어 주는 뜻이 되어 뒤집히지 않는다.",
        },
    ))

    p.set_qa(CONTENT_2, *B.make_content_ox(
        s,
        statements=[
            "The passage says that management rewards personal brilliance above all.",
            "Companies expect a top performer to become an equally good manager.",
            "The firm ends up keeping its outstanding contributor after the promotion.",
            "Coaching other people is described as quick and easy work.",
            "The passage recommends paying stars more instead of promoting them.",
            "Only small firms make the mistake of promoting their best performer.",
            "The team stalls because the new manager deliberately ignores it.",
            "A promoted star tends to keep chasing personal wins instead of coaching.",
            "The celebrated hire turns into a disappointment overnight.",
            "According to the passage, a star and a star boss need the same skills.",
        ],
        truths=[False, True, False, False, False,
                False, False, True, False, False],
        reasons=[
            "지문은 정반대다 — 개인적 탁월함을 보상하는 쪽은 실무 역할이고, 관리자 "
            "역할은 남을 키우는 인내를 보상한다. (주체 바꿔치기)",
            "두 번째 문장 'They assume that a star will naturally make a star boss' 를 "
            "바꿔 표현한 일치 진술이다.",
            "지문은 회사가 '뛰어난 실무자와 유능한 관리자를 둘 다 잃는다'고 했다. "
            "정반대다. (부분 일치 + 한 요소 왜곡)",
            "지문은 코칭을 'the slow work' 라고 불렀다. 빠르고 쉬운 일이라는 것은 "
            "어긋난다. (정도·빈도 과장)",
            "보수를 더 주라는 대안은 지문에 없다. 그럴듯하지만 언급되지 않았다. "
            "(미언급인데 그럴듯)",
            "지문은 'Many companies' 라고만 했고 회사 규모를 한정하지 않았다. "
            "(조건 삭제·왜곡)",
            "지문은 스타가 개인 성과를 좇느라 코칭을 소홀히 한다고 했지, '일부러 "
            "무시한다'고 하지 않았다. (인과 날조)",
            "다섯 번째 문장 'keeps chasing personal wins and neglects the slow work of "
            "coaching' 을 그대로 옮긴 일치 진술이다.",
            "지문은 'slowly turns into a disappointment' 라고 했다. 하룻밤 사이라는 "
            "것은 정반대다. (시점 뒤집기)",
            "지문의 논지는 두 자리가 '거의 정반대 능력'을 요구한다는 것이다. "
            "(인과·관계 역전)",
        ],
    ))

    p.set_qa(VOCAB_2, *B.make_vocab(
        s,
        marks=[(0, "promote", "promote"), (2, "opposite", "identical"),
               (3, "patience", "patience"), (4, "neglects", "neglects"),
               (6, "loses", "loses")],
        answer_no=2,
        reason=("뒤 문장이 '하나는 개인의 탁월함을, 다른 하나는 남을 키우는 인내를 보상한다'며 두 "
                "역할을 대비하므로, identical(동일한)이 아니라 opposite(정반대의)이어야 한다."),
    ))

    p.set_qa(VOCAB_3, *B.make_vocab(
        s,
        marks=[(1, "assume", "assume"), (2, "demand", "demand"),
               (4, "never neglects", "never neglects"), (5, "stalls", "stalls"),
               (6, "loses", "loses")],
        answer_no=3,
        overrides={4: ("Placed in charge, the former star keeps pursuing personal wins "
                       "and never neglects the slow work of coaching the team.")},
        reason=("글은 스타를 관리자로 앉히면 팀이 정체되고 결국 회사가 둘 다 잃는다는 쪽으로 간다. "
                "③ 이 '코칭을 결코 소홀히 하지 않는다'는 뜻이면 바로 뒤의 '팀이 정체된다'와 "
                "모순된다. '소홀히 한다'여야 앞뒤가 이어진다."),
    ))

    r1 = [
        "A great many firms move their strongest performer into a management role.",
        "They take for granted that a star will naturally become a star boss.",
        "The two roles, though, call for almost opposite skills.",
        "One prizes individual brilliance, whereas the other prizes the patience needed to develop other people.",
        "Put in charge, the former star keeps pursuing personal wins and neglects the slow work of coaching the team.",
        "The team stalls, and the celebrated hire gradually becomes a disappointment.",
        "In the end, the company loses both an outstanding contributor and a capable manager.",
    ]
    p.set_qa(GRAMMAR, *B.make_grammar(
        r1,
        marks=[
            (1, "become", "become"),      # ① 조동사 뒤 원형(적절)
            (2, "call", "calls"),         # ② 수 일치 오류(The two roles call)
            (3, "needed", "needed"),      # ③ 과거분사 수식(적절)
            (4, "Put", "Putting"),        # ④ 분사·태 오류(수동이어야)
            (4, "keeps", "keeps"),        # ⑤ 수 일치(적절)
            (4, "neglects", "neglect"),   # ⑥ 병렬·수 일치 오류
            (5, "becomes", "becomes"),    # ⑦ 수 일치(적절)
            (6, "loses", "loses"),        # ⑧ 수 일치(적절)
        ],
        answer_nos=[2, 4, 6],
        reasons={
            2: "주어 The two roles 는 복수이므로 calls → call (수 일치).",
            4: "별은 '자리에 앉혀지는' 대상이므로 능동 Putting 이 아니라 과거분사 Put (분사·태).",
            6: "앞의 keeps 와 병렬이고 주어가 3인칭 단수이므로 neglect → neglects (병렬·수 일치).",
        },
    ))

    r2 = [
        "Most large companies promote the very best performer they have into a management job.",
        "It is assumed that a brilliant worker will naturally turn into a brilliant boss.",
        "Yet the two positions demand nearly opposite abilities.",
        "The first rewards personal excellence, while the second rewards the patience to grow other people.",
        "Once placed in charge, the former star keeps chasing personal victories and ignores the slow labor of coaching.",
        "The team stops moving forward, and the celebrated hire slowly turns into a letdown.",
        "In the end, the firm loses an outstanding contributor as well as a capable manager.",
    ]
    p.set_qa(GRAMMAR_FIX, *B.make_grammar_fix(
        r2,
        marks=[
            (1, "assumed", "assuming"),   # ① 수동이어야 → 오류
            (2, "demand", "demand"),      # ② 수 일치(적절)
            (4, "placed", "placing"),     # ③ 수동 분사여야 → 오류
            (4, "ignores", "ignore"),     # ④ 병렬·수 일치 오류 → 오류
            (5, "turns", "turn"),         # ⑤ 수 일치 오류 → 오류
            (6, "loses", "loses"),        # ⑥ 수 일치(적절)
        ],
        wrong_nos=[1, 3, 4, 5],
        reasons={
            1: "'~라고 여겨진다'는 수동이므로 assuming → assumed (태).",
            2: "주어 the two positions 는 복수이므로 demand 가 맞습니다(수 일치·적절).",
            3: "별은 '앉혀지는' 대상이므로 능동 placing 이 아니라 과거분사 placed (분사·태).",
            4: "앞의 keeps 와 병렬이고 주어가 3인칭 단수이므로 ignore → ignores (병렬·수 일치).",
            5: "주어 the celebrated hire 는 단수이므로 turn → turns (수 일치).",
            6: "주어 the firm 은 단수이므로 loses 가 맞습니다(수 일치·적절).",
        },
        note="틀린 것은 ①③④⑤ 네 개, 옳은 것은 ②⑥ 두 개입니다.",
    ))

    _ch, _no = build_pairs(3, 5, seed=1)          # ⓒ(어법) · ⓔ(어휘)
    p.set_qa(PAIR_ODD, *B2.make_A(
        s,
        marks=[
            (0, "promote", "promote"),      # ⓐ 현재시제(적절)
            (1, "assume", "assume"),        # ⓑ 수 일치(적절)
            (2, "demand", "demands"),       # ⓒ 어법 오류 — The two jobs 는 복수
            (3, "rewards", "rewards"),      # ⓓ 수 일치(적절)
            (4, "neglects", "embraces"),    # ⓔ 어휘 오류 — 반의어 함정
        ],
        answer_no=_no,
        choices=_ch,
        reason=("부적절한 것은 ⓒ(어법)와 ⓔ(어휘) 둘입니다. / "
                "ⓐ 일반적 사실을 말하므로 현재시제 promote 가 맞습니다(적절). / "
                "ⓑ 주어 They 가 복수이므로 assume 이 맞습니다(적절). / "
                "ⓒ demands → demand: 주어 The two jobs 가 복수이므로 복수동사여야 합니다 (어법). / "
                "ⓓ 주어 One 이 단수이므로 rewards 가 맞습니다(적절). / "
                "ⓔ embraces → neglects: 스타가 코칭을 '소홀히 한다'는 흐름인데 '기꺼이 받아들인다'는 "
                "정반대입니다 (어휘·반의어 함정)."),
    ))
    return p


def supplement() -> dict[str, Passage]:
    """데모 지문 제목 -> 새 유형 문항이 담긴 Passage."""
    if not _BY_TITLE:
        for p in (_dna(), _star()):
            _BY_TITLE[p.title] = p
    return _BY_TITLE
