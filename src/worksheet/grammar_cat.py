"""어법 색상 카테고리 (IMG_0195 색상 체계).

어법 포인트 이름을 5개 카테고리 중 하나로 분류하고, 각 카테고리의 색을 준다.
학습지 상단 색상 범례 · 인라인 어법 번호 · 오른쪽 어법 Point 가 이 색을 쓴다.

  동사·준동사   (어형 변화)          → 남색  cverb
  형용사·부사   (원문·유의어·반의어) → 초록  cadj
  관계사·대명사 (어법·지칭 선택)     → 보라  crel
  연결사        (흐름 선택)          → 주황  cconn
  특수구문      (어순 배열)          → 빨강  cspec
"""
from __future__ import annotations

# (key, 이름, 부제, 글자색, 범례칩 배경)
CATEGORIES: list[tuple[str, str, str, str, str]] = [
    ("cverb", "동사·준동사", "어형 변화", "#2f3f97", "#eef1fb"),
    ("cadj", "형용사·부사", "원문·유의어·반의어", "#15803d", "#eaf6ee"),
    ("crel", "관계사·대명사", "어법·지칭 선택", "#7c3aed", "#f3edfc"),
    ("cconn", "연결사", "흐름 선택", "#d97706", "#fdf4e3"),
    ("cspec", "특수구문", "어순 배열", "#d23b3b", "#fdecec"),
]

COLOR: dict[str, str] = {k: color for k, _n, _s, color, _bg in CATEGORIES}

# 분류 규칙 — 위에서부터 먼저 걸리는 카테고리로 (키워드가 어법명에 들어있으면 매칭).
_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("crel", ("관계", "대명사", "지칭", "선행사", "재귀")),
    ("cconn", ("접속", "연결", "담화", "병렬", "상관", "등위")),
    ("cspec", ("도치", "강조", "가정법", "비교", "생략", "삽입", "어순", "형식", "동격", "물주")),
    ("cadj", ("형용사", "부사", "유의어", "반의어")),
    ("cverb", ("부정사", "동명사", "분사", "수동", "시제", "수일치", "일치",
               "조동", "사역", "지각", "준동사", "태", "동사")),
]

DEFAULT = "cverb"   # 어느 규칙에도 안 걸리면 동사·준동사로 (동사구문·관용구가 다수)


def classify(point_name: str) -> str:
    """어법 이름 → 카테고리 키(cverb/cadj/crel/cconn/cspec)."""
    name = point_name or ""
    for key, kws in _RULES:
        if any(kw in name for kw in kws):
            return key
    return DEFAULT
