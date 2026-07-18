"""데모용 지문 데이터 (API 키 없이 파이프라인·조판을 검증한다).

명세서 부록의 샘플: 지문1(DNA)·지문2(star manager) 2지문.
format.py 의 빌더로 6종 문제/해설 HTML 을 만들어 Passage 를 구성한다.
"""
from __future__ import annotations

from . import format as F
from .types import (
    GRAMMAR,
    INSERT,
    ORDER,
    SHORT_ANSWER,
    TOPIC,
    VOCAB,
    Passage,
)


def _passage_dna() -> Passage:
    p = Passage(title="DNA, 자연의 정보 저장 장치")

    # ① 순서 배열 -----------------------------------------------------------
    p.set_qa(
        ORDER,
        F.order_q(
            given=("Every living cell carries a molecule called DNA, which works as "
                   "nature's own hard drive."),
            seg_a=("This density is astonishing: a single gram of DNA could, in theory, "
                   "hold as much data as millions of ordinary hard drives combined."),
            seg_b=("What makes it remarkable is not only that it stores information, but "
                   "that it packs an enormous amount into a vanishingly small space."),
            seg_c=("Inspired by such efficiency, researchers have begun to encode digital "
                   "files into synthetic DNA, hoping to preserve data for thousands of years."),
            orders=["(A)-(C)-(B)", "(B)-(A)-(C)", "(B)-(C)-(A)",
                    "(C)-(A)-(B)", "(C)-(B)-(A)"],
        ),
        F.order_a(
            2,
            "주어진 글에서 DNA를 '자연의 하드 드라이브'로 소개했다. (B)가 it stores "
            "information ~ small space로 그 특징(밀도)을 이어받고, (A)의 This density가 "
            "(B)의 small space를 가리키며 구체적 수치로 확장한다. 마지막으로 (C)가 such "
            "efficiency로 앞의 내용을 총괄하며 응용(디지털 저장)으로 마무리하므로 "
            "(B)-(A)-(C)가 자연스럽다.",
        ),
    )

    # ② 문장 삽입 -----------------------------------------------------------
    insert_body = (
        "Scientists have long admired the way nature stores information. "
        f"{F.pos(1)} DNA holds the instructions for building and running an organism, "
        "written in just four chemical letters. "
        f"{F.pos(2)} These letters are arranged in sequences so compact that a cell "
        "barely visible to the eye contains meters of coiled DNA. "
        f"{F.pos(3)} Engineers, by contrast, still struggle to shrink their storage "
        "devices below a certain size. "
        f"{F.pos(4)} They realized that a material perfected over billions of years "
        "might outperform anything built in a factory. "
        f"{F.pos(5)} As a result, several teams are now racing to turn DNA into a "
        "practical archive for the digital age."
    )
    p.set_qa(
        INSERT,
        F.insert_q(
            given_sentence=("Such a gap led them to look more closely at the molecule "
                            "itself for a solution."),
            marked_passage_html=insert_body,
        ),
        F.insert_a(
            4,
            "주어진 문장의 Such a gap은 앞 문장에서 언급된 '엔지니어들이 저장 장치를 "
            "일정 크기 이하로 줄이지 못하는 한계'를 가리킨다. 또 them ~ look more closely "
            "at the molecule은 뒤 문장의 They realized ~ material(=DNA)로 자연스럽게 "
            "이어지므로, 정답은 ④이다.",
        ),
    )

    # ③ 주제 (영어 선지) ----------------------------------------------------
    topic_passage = (
        "DNA is often described as the blueprint of life, but it is equally a masterpiece "
        "of data storage. In an almost invisible space, it keeps the full set of instructions "
        "an organism needs, and it does so with extraordinary stability, lasting far longer "
        "than the magnetic tapes or silicon chips people rely on today. Struck by this "
        "efficiency, scientists have started writing digital files into laboratory-made DNA. "
        "Though still slow and expensive, the approach hints at a future in which our libraries, "
        "photographs, and records could be preserved for millennia inside molecules."
    )
    p.set_qa(
        TOPIC,
        F.topic_q(
            topic_passage,
            choices=[
                # ① 무관 (지문 단어 blueprint, silicon 섞은 함정)
                "the reason silicon chips replaced paper blueprints in modern factories",
                # ② 정답 (유의어: data storage->compact preservation of information)
                "DNA's remarkable capacity to preserve information and its promise for data storage",
                # ③ 모순 (지문 단어 stability 섞되 반대로)
                "why DNA is too unstable to keep genetic instructions for very long",
                # ④ 무관 (지문 단어 organism 섞은 함정)
                "the process by which an organism digests and absorbs nutrients from food",
                # ⑤ 모순 (지문 단어 digital files 섞되 반대로)
                "the failure of scientists to store any digital files inside living cells",
            ],
        ),
        F.topic_a(
            2,
            "지문은 DNA가 좁은 공간에 방대한 정보를 안정적으로 오래 보관한다는 점(데이터 "
            "저장 매체로서의 가치)과 이를 디지털 저장에 응용하려는 시도를 다룬다. 정답 ②는 "
            "이를 핵심어의 유의어(preserve information, capacity)로 바꿔 표현했다.",
            {
                1: "blueprint·silicon 같은 지문 단어를 썼지만, 반도체가 청사진을 대체한 "
                   "이유는 글에 없다(무관).",
                3: "지문은 DNA가 매우 '안정적'이라고 했는데 선지는 '불안정'하다며 반대로 "
                   "말한다(모순).",
                4: "organism이라는 지문 단어만 빌려왔을 뿐, 소화·흡수 과정은 글과 관련이 "
                   "없다(무관).",
                5: "지문은 디지털 파일 저장을 이미 시작했다고 했는데 선지는 '실패했다'고 하여 "
                   "반대다(모순).",
            },
        ),
    )

    # ④ 어휘 (문맥상 부적절) ------------------------------------------------
    vocab_body = (
        "For decades, engineers have tried to make storage devices ever "
        f"{F.underline(1, 'smaller')} while holding more data. Nature solved this problem "
        f"long ago. DNA is astonishingly {F.underline(2, 'compact')}, fitting a huge library "
        f"of instructions into a microscopic cell. It is also highly "
        f"{F.underline(3, 'fragile')}, surviving in bone and ice for tens of thousands of "
        f"years. Because of these {F.underline(4, 'advantages')}, scientists now treat the "
        f"molecule as a promising medium, and they are actively "
        f"{F.underline(5, 'developing')} ways to store our digital data inside it."
    )
    p.set_qa(
        VOCAB,
        F.vocab_q(vocab_body),
        F.vocab_a(
            3,
            "밑줄 ③ 앞뒤에서 DNA가 뼈와 얼음 속에서 수만 년을 '견딘다(surviving)'고 했으므로 "
            "문맥상 '안정적인(durable/stable)' 의미라야 한다. 그런데 fragile(부서지기 쉬운)은 "
            "정반대이므로 부적절하다. 나머지 smaller·compact·advantages·developing은 모두 "
            "문맥에 맞는 유의어로 쓰였다.",
        ),
    )

    # ⑤ 어법 (복수정답) -----------------------------------------------------
    grammar_body = (
        "DNA is a molecule "
        f"{F.underline(1, 'that')} stores the instructions of life. "
        "The amount of information packed into a single cell "
        f"{F.underline(2, 'are')} truly enormous. "
        "Scientists, "
        f"{F.underline(3, 'fascinated')} by this efficiency, began to study it closely. "
        "They found that data could "
        f"{F.underline(4, 'be written')} into synthetic strands in the laboratory. "
        "The technique is still expensive, but it allows information "
        f"{F.underline(5, 'storing')} for thousands of years. "
        "Researchers who once doubted the idea "
        f"{F.underline(6, 'has')} now changed their minds, "
        "and they work hard "
        f"{F.underline(7, 'to improve')} the writing speed, "
        f"hoping that one day DNA will store the archives "
        f"{F.underline(8, 'which')} humanity wants to keep."
    )
    p.set_qa(
        GRAMMAR,
        F.grammar_q(grammar_body),
        F.grammar_a(
            [2, 5, 6],
            {
                2: "주어가 The amount(단수)이므로 are → is (수 일치).",
                5: "정보가 '저장되는' 대상이므로 능동 storing이 아니라 to be stored 같은 "
                   "수동형이 옳다 (태/준동사).",
                6: "주어가 Researchers(복수)이므로 has → have (수 일치).",
            },
        ),
    )

    # ⑥ 서술형 (세 소문항) --------------------------------------------------
    sa_passage = (
        "DNA has been quietly perfecting data storage for billions of years, and only "
        "recently have engineers, humbled by its efficiency, decided to borrow the idea. "
        "By translating ones and zeros into chemical letters, they can now write files into "
        "synthetic DNA that a laboratory carefully governs, so that the information it holds "
        "may survive far longer than any device we build today."
    )
    p.set_qa(
        SHORT_ANSWER,
        F.short_answer_q(
            passage=sa_passage,
            q1_prompt=("밑줄 친 borrow the idea가 구체적으로 무엇을 의미하는지 우리말로 "
                       "서술하시오."),
            q2_prompt=("다음 <보기>의 단어를 모두 배열하여, '엔지니어들은 정보를 화학 "
                       "문자로 번역하기로 결정했다'라는 뜻의 문장을 완성하시오. (동사는 원형 "
                       "제공, 어형 변화 가능)"),
            q2_tokens=["engineers", "decide", "to", "translate", "information",
                       "into", "chemical", "letters"],
            q2_cues=["decide", "translate"],
            q3_prompt="다음 요약문의 빈칸 (A), (B)에 제시어를 알맞은 형태로 바꿔 쓰시오.",
            q3_summary_html=(
                "Information " + F.blank("A", "accumulate") + " by nature over eons is now "
                "being copied by engineers, who write files into DNA that a lab "
                + F.blank("B", "govern") + "."
            ),
        ),
        F.short_answer_a(
            q1_answer=("DNA가 오랜 세월 동안 완성해 온 '정보를 좁은 공간에 저장하는 방식'을 "
                       "엔지니어들이 본떠, 디지털 데이터를 합성 DNA에 저장하려는 것을 말한다."),
            q2_answer="Engineers decided to translate information into chemical letters.",
            q3_answers={"A": "accumulated", "B": "governs"},
            q3_reason=("(A) 정보가 '축적되어 온' 대상이므로 과거분사 accumulated (수동·완료). "
                       "(B) 관계절의 주어 a lab이 3인칭 단수이고 현재 시제이므로 governs."),
        ),
    )

    return p


def _passage_star() -> Passage:
    p = Passage(title="The Star Manager Trap")

    # ① 순서 배열 -----------------------------------------------------------
    p.set_qa(
        ORDER,
        F.order_q(
            given=("Many companies promote their very best performer into a management "
                   "role, assuming that a star will naturally make a star boss."),
            seg_a=("The two jobs, however, demand almost opposite skills: one rewards "
                   "personal brilliance, while the other rewards the patience to develop "
                   "other people."),
            seg_b=("As a result, the company often loses a great performer and gains a "
                   "struggling manager at the very same time."),
            seg_c=("Placed in charge, the former star keeps chasing personal wins and "
                   "neglects the slow work of coaching the team."),
            orders=["(A)-(B)-(C)", "(A)-(C)-(B)", "(B)-(A)-(C)",
                    "(C)-(A)-(B)", "(C)-(B)-(A)"],
        ),
        F.order_a(
            2,
            "주어진 글은 최고 성과자를 관리자로 승진시키는 통념을 제시한다. (A)가 however로 "
            "두 역할이 정반대 능력을 요구한다고 반박하고, (C)가 그 결과 스타가 코칭을 "
            "소홀히 한다고 구체화하며, (B)가 As a result로 회사가 인재도 잃고 부실한 관리자를 "
            "얻는 결말을 맺는다. 따라서 (A)-(C)-(B)가 적절하다.",
        ),
    )

    # ② 문장 삽입 -----------------------------------------------------------
    insert_body2 = (
        "Being excellent at a task and helping others become excellent are not the same "
        "ability. "
        f"{F.pos(1)} A brilliant salesperson wins by closing deals personally. "
        f"{F.pos(2)} A good sales manager, on the other hand, wins by making an entire team "
        "close more deals. "
        f"{F.pos(3)} Yet firms routinely hand the manager's title to whoever sold the most "
        "last year. "
        f"{F.pos(4)} The new boss, trained only to shine alone, often keeps grabbing the best "
        "clients instead of coaching juniors. "
        f"{F.pos(5)} The team stalls, and the celebrated hire slowly turns into a "
        "disappointment."
    )
    p.set_qa(
        INSERT,
        F.insert_q(
            given_sentence=("This mismatch is exactly why the promotion so often backfires."),
            marked_passage_html=insert_body2,
        ),
        F.insert_a(
            4,
            "주어진 문장의 This mismatch는 ③ 뒤에서 드러난 '가장 많이 판 사람에게 관리자 "
            "직함을 주는 것'과 관리자에게 필요한 능력 사이의 불일치를 가리킨다. 또 backfires "
            "가 뒤 문장의 '혼자 빛나도록 훈련된 상사가 코칭을 소홀히 한다'는 부작용으로 "
            "이어지므로 정답은 ④이다.",
        ),
    )

    # ③ 주제 -----------------------------------------------------------------
    topic_passage2 = (
        "It feels natural to reward your top performer with a promotion into management, yet "
        "the logic is flawed. Excelling at a craft and guiding others to excel call for "
        "different talents; the first depends on individual skill, the second on the "
        "willingness to teach, listen, and wait. When a celebrated specialist is pushed into "
        "leading, they frequently keep competing with their own team instead of building it. "
        "The organization then suffers twice, losing an outstanding contributor and inheriting "
        "an unhappy, ineffective boss."
    )
    p.set_qa(
        TOPIC,
        F.topic_q(
            topic_passage2,
            choices=[
                # ① 모순 (지문 단어 promotion 섞되 반대 주장)
                "why promoting your best performer is always the smartest leadership choice",
                # ② 무관 (지문 단어 management 섞은 함정)
                "the history of management education in leading business schools",
                # ③ 정답 (유의어: top performer->skilled specialist, promotion->leadership move)
                "the hidden cost of turning a skilled specialist into a leader of others",
                # ④ 무관 (지문 단어 team 섞은 함정)
                "practical tips for organizing a company sports team after work",
                # ⑤ 모순 (지문 단어 skill 섞되 반대로)
                "how individual skill alone guarantees success as a team manager",
            ],
        ),
        F.topic_a(
            3,
            "지문은 뛰어난 전문가를 관리자로 올릴 때 두 역할이 요구하는 능력이 달라 회사가 "
            "'이중의 손해'를 본다는 점을 지적한다. 정답 ③은 top performer·promotion을 유의어 "
            "(skilled specialist, leader of others)로 바꿔 이 핵심을 담았다.",
            {
                1: "promotion이라는 지문 단어를 썼지만, 글은 승진이 '항상 최선'이라는 통념을 "
                   "'반박'한다(모순).",
                2: "management를 언급했을 뿐 경영 교육의 역사는 글과 무관하다(무관).",
                4: "team이라는 지문 단어만 빌려왔을 뿐, 사내 스포츠팀 구성은 주제가 아니다"
                   "(무관).",
                5: "지문은 개인 역량만으로는 좋은 관리자가 못 된다고 했는데 선지는 개인 역량이 "
                   "성공을 '보장'한다고 하여 반대다(모순).",
            },
        ),
    )

    # ④ 어휘 -----------------------------------------------------------------
    vocab_body2 = (
        "Companies love to reward a top performer, and the most common reward is a "
        f"{F.underline(1, 'promotion')} into management. The intention is good, but the logic "
        f"is often {F.underline(2, 'flawed')}. Doing a job brilliantly and helping others do "
        f"it well require {F.underline(3, 'identical')} skills. A star who is suddenly asked "
        f"to lead may keep {F.underline(4, 'competing')} with the very people they should be "
        f"coaching. In the end the firm may {F.underline(5, 'lose')} both a great specialist "
        f"and a capable manager."
    )
    p.set_qa(
        VOCAB,
        F.vocab_q(vocab_body2),
        F.vocab_a(
            3,
            "밑줄 ③의 뒤 내용은 '한 가지 일을 잘하는 것'과 '남을 돕는 것'이 서로 다르다는 "
            "취지이므로 문맥상 different(다른) 계열의 낱말이 와야 한다. 그런데 "
            "identical(동일한)은 정반대 의미라 부적절하다. 나머지 promotion·flawed·"
            "competing·lose는 모두 문맥에 맞는 유의어로 쓰였다.",
        ),
    )

    # ⑤ 어법 -----------------------------------------------------------------
    grammar_body2 = (
        "A company usually promotes the person "
        f"{F.underline(1, 'who')} sells the most. "
        "The skills that make a great seller "
        f"{F.underline(2, 'is')} not the skills that make a great boss. "
        f"{F.underline(3, 'Placed')} in charge of a team, the new manager feels lost. "
        "He keeps doing the work himself instead of "
        f"{F.underline(4, 'teaching')} others. "
        "The juniors, "
        f"{F.underline(5, 'whom')} need guidance, are left on their own. "
        "Their performance "
        f"{F.underline(6, 'begins')} to fall almost immediately. "
        "The star, once admired, is now "
        f"{F.underline(7, 'blaming')} for the team's slump, "
        "and the company wishes it "
        f"{F.underline(8, 'had kept')} him in his old role."
    )
    p.set_qa(
        GRAMMAR,
        F.grammar_q(grammar_body2),
        F.grammar_a(
            [2, 5, 7],
            {
                2: "주어가 The skills(복수)이므로 is → are (수 일치).",
                5: "관계절 안에서 주어 역할을 하므로 목적격 whom → 주격 who (관계사).",
                7: "스타가 팀 부진의 '책임을 지우는 대상'이므로 능동 blaming이 아니라 수동 "
                   "blamed가 옳다 (태).",
            },
        ),
    )

    # ⑥ 서술형 ---------------------------------------------------------------
    sa_passage2 = (
        "The best individual contributor is not automatically the best manager, because the "
        "role that once rewarded personal excellence now demands the patience to develop "
        "others. When firms ignore this, they decide to promote their star too quickly, and "
        "the talent that has been carefully built over years is wasted the moment a brilliant "
        "specialist governs a team they never learned to lead."
    )
    p.set_qa(
        SHORT_ANSWER,
        F.short_answer_q(
            passage=sa_passage2,
            q1_prompt=("밑줄 친 this가 가리키는 내용을 우리말로 구체적으로 서술하시오."),
            q2_prompt=("다음 <보기>의 단어를 모두 배열하여, '회사들은 그들의 스타를 너무 "
                       "빨리 승진시키기로 결정한다'라는 뜻의 문장을 완성하시오. (동사는 원형 "
                       "제공, 어형 변화 가능)"),
            q2_tokens=["firms", "decide", "to", "promote", "their", "star", "too", "quickly"],
            q2_cues=["decide", "promote"],
            q3_prompt="다음 요약문의 빈칸 (A), (B)에 제시어를 알맞은 형태로 바꿔 쓰시오.",
            q3_summary_html=(
                "Talent that has been " + F.blank("A", "accumulate") + " over years is lost "
                "when a specialist suddenly " + F.blank("B", "govern") + " a team without "
                "the skills to lead it."
            ),
        ),
        F.short_answer_a(
            q1_answer=("개인적으로 가장 뛰어난 사람이 곧바로 최고의 관리자가 되는 것은 "
                       "아니라는 사실(관리자 역할은 개인적 탁월함이 아니라 남을 키우는 인내를 "
                       "요구한다는 점)을 가리킨다."),
            q2_answer="Firms decide to promote their star too quickly.",
            q3_answers={"A": "accumulated", "B": "governs"},
            q3_reason=("(A) 재능이 여러 해에 걸쳐 '축적되어 온' 것이므로 현재완료 수동의 "
                       "과거분사 accumulated. (B) 주어 a specialist가 3인칭 단수 현재이므로 "
                       "governs."),
        ),
    )

    return p


def demo_passages() -> list[Passage]:
    """데모 2지문(DNA, star manager)을 돌려준다."""
    return [_passage_dna(), _passage_star()]
