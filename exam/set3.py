"""변형문제 3회 — 지문당 4유형 × 3문항(주제·제목·내용일치·함축의미).

1·2회와 별개 세트. 조판·검증은 renderer/validator 를 type_order 인자로 공용 사용한다.
한 유형을 지문당 3번 출제하므로, 유형키를 'base_i'(예: topic_1) 로 합성해
12개의 문항 슬롯을 만든다(각 슬롯은 같은 base 생성기를 서로 다른 변형으로 호출).
'함축의미'는 2회 B(함의추론) 를 그대로 재사용한다.
"""
from __future__ import annotations

# base 유형(생성기 키)과 라벨·발문
TOPIC, TITLE, CONTENT, IMPLY = "topic", "title", "content", "imply"
PER = 3   # 유형당 문항 수

_BASES: tuple[tuple[str, str, str], ...] = (
    # (base, 라벨, 발문)
    (TOPIC,   "주제",     "다음 글의 주제로 가장 적절한 것은?"),
    (TITLE,   "제목",     "다음 글의 제목으로 가장 적절한 것은?"),
    (CONTENT, "내용 일치", "위 글의 내용과 일치하는 것은?"),
    (IMPLY,   "함축의미",  "밑줄 친 부분이 다음 글에서 의미하는 바로 가장 적절한 것은?"),
)


def _key(base: str, i: int) -> str:
    return f"{base}_{i}"


TYPE_ORDER3: tuple[str, ...] = tuple(
    _key(b, i) for b, _, _ in _BASES for i in range(1, PER + 1))
TYPE_LABELS3: dict[str, str] = {
    _key(b, i): lbl for b, lbl, _ in _BASES for i in range(1, PER + 1)}
TYPE_PROMPTS3: dict[str, str] = {
    _key(b, i): prompt for b, _, prompt in _BASES for i in range(1, PER + 1)}
# 유형키 → (base, 변형번호)
BASE_OF: dict[str, str] = {_key(b, i): b for b, _, _ in _BASES for i in range(1, PER + 1)}
VARIANT_OF: dict[str, int] = {_key(b, i): i for b, _, _ in _BASES for i in range(1, PER + 1)}
