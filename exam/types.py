"""시험지 생성기의 핵심 데이터 구조.

명세서 §6-1 에 대응한다.

    TYPE_ORDER = [order, insert, topic, vocab, grammar, short_answer]  # 고정
    Passage = { title, q: {<type>: 문제 HTML}, a: {<type>: 해설 HTML} }

- 6종은 항상 이 순서로만 나온다(유형 누락·순서 변경 불가).
- 각 생성기는 Passage.q[type], Passage.a[type] 를 채운다.
- 조판기는 TYPE_ORDER 대로만 순회하므로 유형 순서가 자동 보장된다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 고정 출제 순서 (불변)
#   ① 순서 → ② 삽입 → ③ 주제 → ④ 어휘 → ⑤ 어법 → ⑥ 서술형
# ---------------------------------------------------------------------------
ORDER = "order"
INSERT = "insert"
TOPIC = "topic"
VOCAB = "vocab"
GRAMMAR = "grammar"
SHORT_ANSWER = "short_answer"

TYPE_ORDER: tuple[str, ...] = (ORDER, INSERT, TOPIC, VOCAB, GRAMMAR, SHORT_ANSWER)

# 발문(문제 지시문). 조판 시 문제 상단에 얇게 표기한다.
TYPE_PROMPTS: dict[str, str] = {
    ORDER: "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?",
    INSERT: "글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?",
    TOPIC: "다음 글의 주제로 가장 적절한 것은?",
    VOCAB: "밑줄 친 부분 중, 문맥상 낱말의 쓰임이 적절하지 않은 것은?",
    GRAMMAR: "밑줄 친 부분 중, 어법상 틀린 것을 모두 고르시오.",
    SHORT_ANSWER: "다음 글을 읽고 물음에 답하시오.",
}

# 유형 한글 라벨 (해설 등에서 참고용)
TYPE_LABELS: dict[str, str] = {
    ORDER: "순서 배열",
    INSERT: "문장 삽입",
    TOPIC: "주제",
    VOCAB: "어휘",
    GRAMMAR: "어법",
    SHORT_ANSWER: "서술형",
}


@dataclass
class Passage:
    """지문 1개에 대한 6종 문제/해설 묶음.

    q, a 는 유형(type) -> HTML 조각 딕셔너리이다.
    HTML 조각에는 문항 번호를 넣지 않는다 — 번호는 조판 단계에서
    문서 전체에 걸쳐 연속으로 부여된다.
    """

    title: str
    q: dict[str, str] = field(default_factory=dict)
    a: dict[str, str] = field(default_factory=dict)

    def set_qa(self, type_: str, question_html: str, answer_html: str) -> None:
        self.q[type_] = question_html
        self.a[type_] = answer_html

    @property
    def types(self) -> set[str]:
        return set(self.q.keys())
