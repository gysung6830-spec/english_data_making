#!/usr/bin/env python3
"""업로드된 EBS 올림포스 기본1 4개 지문으로 동형모의고사 한 세트를 저작·렌더.

API 키가 없어 LLM 파이프라인을 못 돌리는 환경에서, 확정된 출제원리
(정답=유의어 패러프레이즈 / 오답 2 주제무관 + 2 주제모순, 불일치=부정 비틀기,
 무관문장·어법=번호선지, 정답번호 분산)에 맞춰 손으로 문항을 구성한다.
"""
from pathlib import Path

from mockexam.core.models import (
    Blueprint, BlueprintMeta, Choice, MockExam, Question,
)
from mockexam.render.exam import render_exam

OUT = Path("output")
OUT.mkdir(exist_ok=True)


def C(*rows):
    labels = ["①", "②", "③", "④", "⑤"]
    return [Choice(labels[i], t) for i, t in enumerate(rows)]


def NUM5():
    return [Choice(l, "") for l in ["①", "②", "③", "④", "⑤"]]


# ─────────────────────────────────────────────────────────────────────
# 지문 1 · 인간의 교제·유대 본성 (Ch.04 Unit 10-2)
# ─────────────────────────────────────────────────────────────────────
P1 = ("Although the wish to be alone is often strong, its intensity varies from "
      "person to person. An equally impelling impulse, though, is to seek the company "
      "of others and to spend extended periods of time sharing activities. In these "
      "periods we exchange information and feelings in both conversational and "
      "non-verbal forms. We need other people to provide us with love, support, "
      "approval, bodily contact, reassurance, physical help and a myriad of other "
      "practical, physical and emotional needs. In a very basic sense we need others "
      "to confirm that we are there, that we exist and that we have an identity that "
      "is unique and separate from anyone else. Thus, we generally cannot exist for "
      "too long without seeking companionship.")

P1_BLANK = P1.replace("seeking companionship.", "seeking ____________.")

q1 = Question(
    no=1, section="choice", type="main_point", score=3,
    stem="다음 글의 요지로 가장 적절한 것은?",
    passage_text=P1,
    choices=C(
        "비언어적 의사소통은 언어적 대화보다 더 많은 양의 정보를 전달한다.",
        "혼자 있고 싶은 소망의 강도는 사람에 따라 큰 차이가 없다.",
        "인간은 타인과의 교류를 통해 사랑과 지지를 얻고 자신의 존재와 정체성을 확인한다.",
        "성숙한 사람은 타인의 인정에 의존하지 않고 홀로 정체성을 확립한다.",
        "인간은 타인의 도움 없이도 오랜 시간 자신의 존재를 유지할 수 있다.",
    ),
    answer="③",
    explanation=(
        "[핵심 포인트] 글은 사랑·지지·인정 등 여러 필요를 채워 주는 타인이 있어야 하고, "
        "아주 기본적으로 타인이 있어야 우리의 존재와 정체성이 확인된다고 말한다. 따라서 "
        "인간은 교제 없이 오래 지낼 수 없다는 것이 요지다.\n"
        "[오답 함정] ①② 지문의 표현(비언어적·소망)을 썼지만 글의 중심 주장이 아니다(주제 무관). "
        "④⑤ 마지막 문장 '교제 없이 오래 존재할 수 없다'와 정면으로 어긋난다(주제 모순)."
    ),
)

q1b = Question(
    no=0, section="choice", type="title", score=3,
    stem="다음 글의 제목으로 가장 적절한 것은?",
    passage_text=P1,
    choices=C(
        "The Strength of Wanting to Be Alone",
        "How Non-verbal Signals Replace Conversation",
        "Managing Your Time Between Work and Rest",
        "We Need Others to Know That We Exist",
        "Why Independence Defines a Mature Person",
    ),
    answer="④",
    explanation=(
        "[핵심 포인트] 글의 핵심은 '아주 기본적으로 타인이 있어야 우리가 존재하고 정체성을 "
        "가진다는 것을 확인받는다'이다. 이를 함축한 ④가 제목으로 알맞다.\n"
        "[오답 함정] ①⑤ '혼자'와 '독립'을 강조해 글의 결론과 반대다(주제 모순). ②③ 비언어적 "
        "신호·시간 관리는 글의 중심 소재가 아니다(주제 무관)."
    ),
)

q2 = Question(
    no=0, section="choice", type="blank_single", score=3,
    stem="다음 빈칸에 들어갈 말로 가장 적절한 것은?",
    passage_text=P1_BLANK,
    choices=C(
        "independence",
        "companionship",
        "solitude",
        "wealth",
        "silence",
    ),
    answer="②",
    explanation=(
        "[핵심 포인트] 앞에서 '타인과 함께 있으려는 충동', '타인이 있어야 존재·정체성이 확인된다'고 "
        "했으므로, 빈칸에는 '교제(함께함)'를 뜻하는 companionship이 와야 앞 내용과 같은 뜻으로 "
        "이어진다(유의어 재진술).\n"
        "[오답 함정] ①③⑤ independence·solitude·silence는 '혼자'를 뜻해 글의 결론과 반대다(주제 모순). "
        "④ wealth는 글에서 다루지 않는다(주제 무관)."
    ),
)

# ─────────────────────────────────────────────────────────────────────
# 지문 2 · 방관자 효과 (Ch.05 Unit 14) → 무관한 문장 유형
#   ③에 주제와 무관한 '체력 훈련' 문장을 삽입(지문 어휘 활용).
# ─────────────────────────────────────────────────────────────────────
P2_IRREL = (
    "① The problem with bystanders does not stem from defects in their character "
    "that prevent them from helping. "
    "② Rather, the situation that bystanders find themselves in constrains their "
    "behavior more than we realize. "
    "③ Developing a strong character through daily physical training helps people "
    "stay calm and remain fit when an emergency suddenly occurs. "
    "④ For example, the more bystanders there are, the less likely any one of them "
    "will intervene. "
    "⑤ When a number of bystanders witness an emergency, responsibility apparently "
    "diffuses among them, and no one feels enough personal responsibility to respond."
)

q3 = Question(
    no=3, section="choice", type="irrelevant_sentence", score=3,
    stem="다음 글에서 전체 흐름과 관계 없는 문장은?",
    passage_text=P2_IRREL,
    choices=NUM5(),
    answer="③",
    meta={"number_only": True},
    explanation=(
        "[핵심 포인트] 글은 '방관자의 문제는 성격 결함이 아니라 상황 때문'이라는 주장(①②)을, "
        "'사람이 많을수록 개입 가능성이 낮아지고 책임감이 분산된다'는 예시·근거(④⑤)로 뒷받침한다.\n"
        "[오답 함정] ③은 '꾸준한 체력 훈련이 위기 상황에서 침착함과 체력 유지에 도움이 된다'는 "
        "내용으로, 책임 분산(방관자 효과) 논지와 무관하다. emergency·character 같은 단어가 겹쳐 "
        "그럴듯해 보이지만 글의 흐름을 끊는다."
    ),
)

# 방관자 효과 원문(무관 문장 없이) — 요지 문항용
P2_ORIG = (
    "Social psychology tells us that bystanders in emergency situations are acting "
    "normally when they fail to respond. The problem with bystanders does not stem "
    "from defects in their character that prevent them from helping. Rather, the "
    "situation that bystanders find themselves in constrains their behavior more than "
    "we realize. For example, the more bystanders there are, the less likely any one "
    "of them will intervene. A single bystander at the scene of an emergency would "
    "usually respond. But when a number of bystanders witness an emergency, "
    "responsibility apparently diffuses among them, and no one feels enough personal "
    "responsibility to respond."
)

q3b = Question(
    no=0, section="choice", type="main_point", score=3,
    stem="다음 글의 요지로 가장 적절한 것은?",
    passage_text=P2_ORIG,
    choices=C(
        "위급 상황에서 방관자가 돕지 못하는 것은 성격 결함이 아니라, 사람이 많을수록 책임감이 "
        "분산되는 상황 때문이다.",
        "비언어적 의사소통에 능숙하면 위기 상황에서 오해를 줄일 수 있다.",
        "위급 상황에 대비해 평소에 응급 대처 훈련을 받아 두는 것이 중요하다.",
        "사람들은 대개 자신의 성격적 결함 때문에 위기 상황에서 남을 돕지 못한다.",
        "목격자의 수가 많을수록 그중 한 사람이 나서서 도울 가능성이 커진다.",
    ),
    answer="①",
    explanation=(
        "[핵심 포인트] 글은 방관자가 돕지 않는 원인을 '성격 결함'이 아니라 '상황'에서 찾으며, "
        "특히 사람이 많을수록 책임감이 분산되어 아무도 나서지 않는다고 설명한다.\n"
        "[오답 함정] ②③ 비언어적 소통·응급 훈련은 글에서 다루지 않는다(주제 무관). ④ 지문은 "
        "성격 결함이 원인이 아니라고 명시한다(주제 모순). ⑤ '사람이 많을수록 개입 가능성이 "
        "낮아진다'는 글과 정반대다(주제 모순)."
    ),
)

# ─────────────────────────────────────────────────────────────────────
# 지문 3 · 퍼스널 브랜딩 (Ch.05 Unit 14-1) → 제목 + 내용 불일치 + 빈칸
# ─────────────────────────────────────────────────────────────────────
P3 = ("Personal branding is not something that you have to do behind the scenes. "
      "For many it does not always feel comfortable to deliberately plan how we are "
      "going to promote ourselves and our accomplishments to others. Personal "
      "branding, however, is essential to achieving success. The key takeaway from "
      "this concept is awareness and anticipation. If you are not aware of the "
      "opportunities to brand yourself, you may not be directed to leave a favorable "
      "impression. So as you begin to think about what you want to be known for, begin "
      "to be more aware of what you want people to say about you when you are not in "
      "the room as an effective way to guide your personal brand.")

q4 = Question(
    no=4, section="choice", type="title", score=3,
    stem="다음 글의 제목으로 가장 적절한 것은?",
    passage_text=P3,
    choices=C(
        "Keep Your Achievements Behind the Scenes",
        "Manage the Reputation That Speaks When You're Away",
        "Success Comes Only From Natural Talent",
        "Why Self-Promotion Destroys Professional Trust",
        "The Art of Comfortable Small Talk",
    ),
    answer="②",
    explanation=(
        "[핵심 포인트] 글은 퍼스널 브랜딩이 성공에 필수이며, 핵심은 '인식과 예상'이고, "
        "'내가 그 자리에 없을 때 사람들이 나에 대해 말하는 것'을 관리하라고 조언한다. 이를 "
        "재진술한 ②가 제목으로 알맞다.\n"
        "[오답 함정] ① 첫 문장 '남몰래 뒤에서 하는 일이 아니다'와 정반대다(주제 모순). "
        "④ 자기 홍보가 신뢰를 무너뜨린다는 것도 글과 반대다(주제 모순). ③⑤ 타고난 재능·잡담 "
        "기술은 글에서 다루지 않는다(주제 무관)."
    ),
)

q5 = Question(
    no=5, section="choice", type="content_mismatch", score=3,
    stem="다음 글의 내용과 일치하지 않는 것은?",
    passage_text=P3,
    choices=C(
        "퍼스널 브랜딩은 남몰래 뒤에서만 해야 하는 일이 아니다.",
        "자기 홍보를 계획하는 일이 모든 사람에게 늘 편안하게 느껴지는 것은 아니다.",
        "퍼스널 브랜딩은 성공을 이루는 데 필수적이다.",
        "이 개념의 핵심은 인식(awareness)과 예상(anticipation)이다.",
        "브랜딩 기회를 인식하지 못하더라도 호의적인 인상을 남기는 데에는 지장이 없다.",
    ),
    answer="⑤",
    explanation=(
        "[핵심 포인트] ①~④는 각각 지문 문장과 그대로 일치한다.\n"
        "[오답 함정] ⑤ 지문은 '기회를 인식하지 못하면 호의적인 인상을 남기지 못할 수도 있다'고 "
        "했는데, 선지는 '지장이 없다'로 부정을 뒤집어 놓았다. 따라서 내용과 일치하지 않는다."
    ),
)

P3_BLANK = P3.replace("is essential to achieving success",
                      "is ____________ to achieving success")

q5b = Question(
    no=0, section="choice", type="blank_single", score=3,
    stem="다음 빈칸에 들어갈 말로 가장 적절한 것은?",
    passage_text=P3_BLANK,
    choices=C(
        "essential",
        "irrelevant",
        "harmful",
        "optional",
        "secondary",
    ),
    answer="①",
    explanation=(
        "[핵심 포인트] 뒤 문장들이 '퍼스널 브랜딩의 기회를 인식·예상하라'고 강조하며 그 중요성을 "
        "설명하므로, 빈칸에는 '필수적인(essential)'이 와야 흐름이 맞는다.\n"
        "[오답 함정] ② irrelevant ③ harmful ④ optional은 '중요하다'는 글의 논지와 반대다"
        "(주제 모순). ⑤ secondary(부차적) 역시 중요성을 낮춰 글과 어긋난다."
    ),
)

# ─────────────────────────────────────────────────────────────────────
# 지문 4 · 명왕성 발견 (Ch.05 Unit 14-2) → 어법 + 빈칸
# ─────────────────────────────────────────────────────────────────────
P4_GRAMMAR = (
    "The ability to detect visual movement ① <u>played</u> an interesting role in "
    "the history of astronomy. In 1930, Clyde Tombaugh was searching the skies for a "
    "possible undiscovered planet ② <u>lying</u> beyond Neptune. Stars essentially "
    "remain ③ <u>unmoving</u> in photos, while a planet moves from one photo to the "
    "next. He put each pair of photos on a machine ④ <u>what</u> would flip back and "
    "forth between one photo and the other. He identified that dot as Pluto, "
    "⑤ <u>which</u> astronomers now list as a dwarf planet."
)

q6 = Question(
    no=6, section="choice", type="grammar", score=4,
    stem="다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?",
    passage_text=P4_GRAMMAR,
    choices=NUM5(),
    answer="④",
    meta={"number_only": True},
    explanation=(
        "[핵심 포인트] ④ 앞에 선행사 a machine이 있고 뒤에는 주어가 빠진 불완전한 절이 오므로 "
        "관계대명사 that 또는 which가 와야 한다. what은 선행사를 포함하는 관계대명사여서 앞에 "
        "선행사가 있는 이 자리에는 쓸 수 없다. → what을 that(또는 which)으로 고쳐야 한다.\n"
        "[오답 함정] ① played: 주어 The ability에 대한 과거시제 동사로 적절. ② lying: planet을 "
        "꾸미는 현재분사로 적절. ③ unmoving: remain의 보어로 쓰인 형용사로 적절. ⑤ which: 앞의 "
        "Pluto를 선행사로 받는 계속적 용법의 관계대명사로 적절."
    ),
)

P4_BLANK = (
    "By flipping between two photographs of the same region taken several days apart, "
    "Tombaugh could spot the single dot that changed position while all the other dots "
    "stayed fixed. Stars remain in place, but a planet shifts from one image to the "
    "next. In other words, his discovery of Pluto ultimately depended on detecting "
    "____________ between the paired photographs."
)

q7 = Question(
    no=7, section="choice", type="blank_single", score=4,
    stem="다음 빈칸에 들어갈 말로 가장 적절한 것은?",
    passage_text=P4_BLANK,
    choices=C(
        "brightness",
        "color",
        "distance",
        "temperature",
        "movement",
    ),
    answer="⑤",
    explanation=(
        "[핵심 포인트] 앞에서 '점 하나가 위치를 바꾸었다(changed position)', '행성은 한 사진에서 "
        "다음 사진으로 이동한다(shifts)'고 했으므로, 빈칸에는 그 '움직임'을 뜻하는 movement가 와야 "
        "앞 내용과 같은 뜻으로 이어진다(유의어 재진술).\n"
        "[오답 함정] ① brightness ② color ④ temperature는 글에서 판단 근거로 삼지 않은 요소다"
        "(주제 무관). ③ distance는 '거리'로, 사진 사이의 '위치 변화(움직임)'를 포착했다는 논지와 "
        "어긋난다(주제 모순)."
    ),
)

# 읽기 순서(지문 1→4)대로 배열하고 문항 번호를 자동 부여.
ORDER = [q1, q1b, q2,          # 지문1: 요지·제목·빈칸
         q3, q3b,              # 지문2: 무관문장·요지
         q4, q5, q5b,          # 지문3: 제목·불일치·빈칸
         q6, q7]               # 지문4: 어법·빈칸
QUESTIONS = ORDER
for i, q in enumerate(QUESTIONS, 1):
    q.no = i
total = sum(q.score for q in QUESTIONS)

meta = BlueprintMeta(
    school_id="ebs_olympos", name="EBS 올림포스 기본1", level="high", grade=1,
    subject="영어독해", time_min=30, total_score=total, pages=4, learned=False,
)
exam = MockExam(blueprint=Blueprint(meta=meta, items=[]), questions=QUESTIONS)

info = {"exam_title": "동형모의고사 — EBS 올림포스 기본1 (4지문)",
        "subject": "영어독해"}

out = render_exam(exam, OUT, header_info=info,
                  footer="이 시험문제는 은아T영어연구소의 저작물입니다.",
                  answer_key="end", basename="EBS_올림포스_기본1_동형모의고사")

print("문항 수:", len(QUESTIONS), "총점:", total)
print("정답 분포:", [q.answer for q in QUESTIONS])
for k, p in sorted(out.items()):
    print(f"  {k}: {p}")
