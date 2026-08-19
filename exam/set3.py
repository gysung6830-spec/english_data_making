"""변형문제 3회 — 대의파악 집중(주제 1 + 제목 3 + 내용일치 3 + 함축의미 3 = 지문당 10문항).

1·2회와 별개 세트. 조판·검증은 renderer/validator 를 type_order 인자로 공용 사용한다.
유형키를 'base_i'(예: title_2) 로 합성해 문항 슬롯을 만든다(각 슬롯은 같은 base
생성기를 서로 다른 변형으로 호출). '함축의미'는 2회 B(함의추론) 를 그대로 재사용한다.
유형별 문항 수는 아래 _BASES 의 마지막 값으로 조절한다(주제=1, 나머지=3).
"""
from __future__ import annotations

TOPIC, TITLE, CONTENT, IMPLY = "topic", "title", "content", "imply"

# (base, 라벨, 발문, 문항수)
_BASES: tuple[tuple[str, str, str, int], ...] = (
    (TOPIC,   "주제",     "다음 글의 주제로 가장 적절한 것은?",                        1),
    (TITLE,   "제목",     "다음 글의 제목으로 가장 적절한 것은?",                       3),
    (CONTENT, "내용 일치", "위 글의 내용과 일치하는 것은?",                            3),
    (IMPLY,   "함축의미",  "밑줄 친 부분이 다음 글에서 의미하는 바로 가장 적절한 것은?", 3),
)


def _key(base: str, i: int) -> str:
    return f"{base}_{i}"


TYPE_ORDER3: tuple[str, ...] = tuple(
    _key(b, i) for b, _, _, n in _BASES for i in range(1, n + 1))
TYPE_LABELS3: dict[str, str] = {
    _key(b, i): lbl for b, lbl, _, n in _BASES for i in range(1, n + 1)}
TYPE_PROMPTS3: dict[str, str] = {
    _key(b, i): prompt for b, _, prompt, n in _BASES for i in range(1, n + 1)}
# 유형키 → (base, 변형번호)
BASE_OF: dict[str, str] = {_key(b, i): b for b, _, _, n in _BASES for i in range(1, n + 1)}
VARIANT_OF: dict[str, int] = {_key(b, i): i for b, _, _, n in _BASES for i in range(1, n + 1)}
# base → 문항 수
COUNT_OF: dict[str, int] = {b: n for b, _, _, n in _BASES}
