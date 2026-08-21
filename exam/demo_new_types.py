"""데모(무료 미리보기)용 — 통합본에 새로 들어온 유형의 예시 문항.

제목·무관한 문장·어휘(원문단어형·부정어형)·어법 개수는 기존 데모에 없던 유형이라
여기서 따로 만든다. 실제 생성과 똑같은 빌더(build.py)를 거치므로 조판 결과도 같다.

어법 두 유형(GRAMMAR·GRAMMAR_COUNT)은 여기 것이 demo_data 의 것을 대신한다 —
실제 생성과 같이 '다시 쓴 지문' 위에 서야 하기 때문이다(generators/grammar.py 참고).
두 문항은 서로 다른 다시쓰기를 쓰므로 같은 밑줄을 두 번 묻지 않는다.
"""
from __future__ import annotations

from . import build as B
from .demo_data import DNA, STAR
from . import build2 as B2
from .generators.pair_odd import build_pairs
from .types import (
    GRAMMAR, GRAMMAR_COUNT, IRRELEVANT, PAIR_ODD, TITLE, VOCAB_2, VOCAB_3, Passage,
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

    # 무관한 문장 — 도입 1문장 뒤 ①~⑤, ③자리에 '소재는 같고 논지는 벗어난' 문장을 끼움
    p.set_qa(IRRELEVANT, *B.make_irrelevant(
        s, start_no=2, answer_no=3,
        sentence=("Because living cells needed to store information, they gradually "
                  "shrank until they could survive in bone and ice."),
        reason=("글은 'DNA가 정보를 엄청난 밀도로 담고 오래 견디므로 저장 매체로 쓸 만하다'는 "
                "쪽으로 나아간다. 이 문장은 지문의 낱말(store information·bone and ice)을 그대로 "
                "쓰지만 인과를 뒤집었다 — 지문은 '작아서 많이 담는다'고 했지 '담아야 해서 작아졌다'고 "
                "한 적이 없다. 세포의 진화 원인은 필자의 논지가 아니다."),
        wrong={
            1: "①은 도입의 '정보를 저장한다'를 받아 '아주 작은 공간에 담는다'는 밀도로 나아간다.",
            2: "②는 ①의 밀도를 1그램이라는 구체적 수치로 뒷받침한다.",
            4: "④는 Inspired by such efficiency 로 앞의 효율을 받아 실제 연구로 이어 준다.",
            5: "⑤는 The technique 으로 ④의 연구를 받아 그 한계와 이점을 덧붙인다.",
        },
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
               (3, "astonishingly", "astonishingly"), (4, "researchers", "researchers"),
               (6, "stored", "stored")],
        answer_no=3,
        overrides={3: ("It is not astonishingly durable at all; it disappears from "
                       "bone and ice within a few short years.")},
        reason=("밑줄 다섯은 모두 원문 그대로라 낱말만 보면 흠이 없다. 그런데 ③ 이 든 문장이 "
                "'전혀 오래가지 못한다'로 바뀌어, 바로 뒤의 '그런 효율에 영감을 받아 연구가 "
                "시작됐다'와 정면으로 모순된다. 낱말이 아니라 문장이 흐름에서 어긋난 경우다."),
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

    # 어법 개수 — 또 다른 다시쓰기 위에. 밑줄을 하나하나 따져 '몇 개가 틀렸는지' 센다.
    r2 = [
        "Every cell that is alive contains a molecule known as DNA, which acts like nature's own hard drive.",
        "Its remarkable quality lies not only in storing information but also in squeezing an enormous amount into an extremely small space.",
        "Just one gram of DNA might, at least in theory, keep as much data as millions of everyday hard drives combined.",
        "Because it is so tough, it can survive within bone and ice for tens of thousands of years.",
        "Researchers, inspired by that efficiency, have begun to write digital files into synthetic DNA.",
        "The method is still slow and expensive, yet it allows information to be preserved for thousands of years.",
        "One day the libraries and photographs we treasure may sit safely inside molecules.",
    ]
    p.set_qa(GRAMMAR_COUNT, *B.make_grammar_count(
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

    p.set_qa(IRRELEVANT, *B.make_irrelevant(
        s, start_no=2, answer_no=4,
        sentence=("Companies promote their best performers precisely because coaching "
                  "a team always rewards personal brilliance."),
        reason=("글은 '두 자리가 정반대 능력을 요구한다'는 논지를 편다. 이 문장은 지문의 낱말"
                "(promote·performers·coaching·personal brilliance)을 그대로 쓰지만 인과를 날조했다 — "
                "지문은 코칭이 개인의 탁월함을 보상한다고 한 적이 없고, 오히려 그 둘을 정반대로 "
                "대비한다. 논지를 뒷받침하기는커녕 뒤집는다."),
        wrong={
            1: "①은 도입의 승진 관행을 받아 그 밑에 깔린 가정(스타가 스타 상사가 된다)을 드러낸다.",
            2: "②는 however 로 그 가정을 반박하며 '정반대 능력'이라는 논점을 세운다.",
            3: "③은 One ~ while the other ~ 로 그 정반대 능력이 무엇인지 풀어 준다.",
            5: "⑤는 The team stalls 로 두 능력이 어긋난 결과를 보여 준다.",
        },
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
               (4, "neglects", "neglects"), (5, "stalls", "stalls"),
               (6, "loses", "loses")],
        answer_no=3,
        overrides={4: ("Placed in charge, the former star no longer chases personal wins "
                       "and never neglects the slow work of coaching the team.")},
        reason=("글은 스타를 관리자로 앉히면 팀이 정체되고 결국 회사가 둘 다 잃는다는 쪽으로 간다. "
                "③ 문장이 '더는 개인 성과를 좇지 않고 코칭도 소홀히 하지 않는다'로 바뀌면 바로 뒤의 "
                "'팀이 정체된다'와 모순된다."),
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
    p.set_qa(GRAMMAR_COUNT, *B.make_grammar_count(
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
