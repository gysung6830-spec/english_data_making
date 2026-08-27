"""정답 위치 분산 — 정답 번호가 한쪽(예: 늘 ③)에 몰리지 않게 고르게 흩뿌린다.

LLM 은 객관식 정답을 특정 번호(주로 가운데)에 몰아 배치하는 편향이 있다. 선지 순서가
'자유로운' 유형(주제·내용일치·2회 A·B·E·F)은 선지를 재배열해 정답을 목표 위치로 옮겨도
정오가 바뀌지 않으므로, 지문·유형별로 목표 위치를 정해 정답 번호를 고르게 분산한다.

(어휘·어법·순서·삽입·G 등은 정답 위치가 '읽는 순서/개수'로 구조적으로 정해지므로 건드리지
 않는다 — 이미 내용에 따라 자연히 달라진다.)
"""
from __future__ import annotations

import re
import zlib

# 1~5의 고정 스크램블(단조 증가 회피). 인덱스를 대면 목표 정답 위치가 나온다.
_ORDER = (3, 5, 2, 4, 1)

# 선지 순서가 자유로워 재배치 가능한 유형 → '지문 내 지역 슬롯'(분산 키)
SLOTS1 = {"topic": 0, "content": 1}                 # 변형문제 1회
SLOTS2 = {"A": 0, "B": 1, "E": 2, "F": 3}            # 변형문제 2회
# 통합본 — 선지 순서를 자유롭게 바꿔도 정오가 변하지 않는 유형만.
#   어휘·어법은 밑줄 읽는 순서가 번호를 정하고, 무관한 문장·순서·삽입은 본문 위치가
#   번호를 정하므로 재배치 대상이 아니다.
# 내용 O/X 는 다섯 진술을 각각 판정하므로 '정답 자리'가 없어 여기 들어가지 않는다.
SLOTS_MERGED = {"topic": 0, "title": 1, "linker": 2, "B": 3, "E": 4, "F": 5,
                "pair_odd": 6}


def seed_of(text: str) -> int:
    """지문 내용으로 안정적인(프로세스 무관) 시드를 만든다.

    같은 (지문 위치, 유형)이 시험지마다 늘 같은 번호가 되지 않도록 시작 위치를 지문
    내용에 따라 다르게 한다(파이썬 hash 는 실행마다 달라 사용하지 않는다).

    시드는 지문 내용에만 달렸다 — 같은 지문이면 항상 같은 정답 번호 배치가 나온다.
    """
    return zlib.crc32((text or "").encode("utf-8")) % len(_ORDER)


def pick(passage_index: int, slot: int, per_passage: int, seed: int = 0) -> int:
    """지문 index·유형 슬롯(+지문별 시드)으로 목표 정답 위치(1~5)를 정한다.

    passage_index 가 커질수록, 같은 유형도 지문마다 다른 위치를 받아 몰림을 막고,
    seed 로 시험지·지문마다 시작 위치를 달리해 '늘 같은 패턴'이 되지 않게 한다.
    """
    idx = seed + passage_index * per_passage + slot
    return _ORDER[idx % len(_ORDER)]


def place_answer(choices: list, answer_no: int, target_no: int,
                 extra_by_pos: dict[int, str] | None = None):
    """선지를 재배열해 정답을 target_no 위치로 옮긴다(정오 불변).

    - choices: 선지 목록(문자열 또는 (a,b) 쌍 등 무엇이든).
    - answer_no / target_no: 1-based. 나머지 선지는 원래 상대 순서를 유지한다.
    - extra_by_pos: 위치로 매긴 부가정보(예: 오답 근거 {번호: 설명}) — 새 위치로 재매핑.
    반환: (새 선지, 새 정답번호, 새 extra_by_pos|None)
    """
    n = len(choices)
    if n == 0:
        return choices, answer_no, extra_by_pos
    a = (answer_no - 1) % n
    t = (target_no - 1) % n
    perm = [i for i in range(n) if i != a]   # 나머지(상대 순서 유지)
    perm.insert(t, a)                         # 정답을 목표 슬롯에 끼워 넣음
    new_choices = [choices[i] for i in perm]
    new_answer = t + 1
    new_extra = None
    if extra_by_pos is not None:
        new_extra = {}
        for new_pos, old_i in enumerate(perm, 1):
            old_pos = old_i + 1
            if old_pos in extra_by_pos:
                new_extra[new_pos] = extra_by_pos[old_pos]
    return new_choices, new_answer, new_extra


def perm_map(n: int, answer_no: int, target_no: int) -> dict[int, int]:
    """place_answer 와 '똑같은' 재배열의 옛 번호 → 새 번호 대응표(1-based)."""
    if n <= 0:
        return {}
    a = (answer_no - 1) % n
    t = (target_no - 1) % n
    perm = [i for i in range(n) if i != a]
    perm.insert(t, a)
    return {old_i + 1: new_pos for new_pos, old_i in enumerate(perm, 1)}


def relabel_answer_ref(reason: str, old_no: int, new_no: int) -> str:
    """해설 본문이 정답 선지를 'N번'으로 지칭한 것을, 정답 위치 분산(재배열) 뒤의
    '실제 표시 번호'로 바꾼다.

    LLM 은 정답 근거(reason)에서 정답 선지를 자신이 정한 번호(재배열 전 answer_no)로
    지칭한다. place_answer 로 선지를 옮기면 표시 정답 번호가 달라지는데, 자유 서술인
    reason 은 자동으로 바뀌지 않아 '5번인데 본문은 1번이 정답'이라고 어긋난다.
    이 함수가 그 잔재를 표시 번호로 교정한다.

    '(N)번'·'N번 문장'·'N번째' 같은 '문장 번호/순서' 지칭은 정답 지칭이 아니므로
    건드리지 않는다(앞에 '('·숫자가 없고, 뒤에 '문장'·'째'가 없는 'N번'만 교체).
    """
    if not reason or old_no == new_no:
        return reason
    pat = re.compile(rf'(?<![(\d]){old_no}번(?!\s*문장|\s*째)')
    return pat.sub(f'{new_no}번', reason)


# 해설 본문이 선지·밑줄을 지칭하는 표기.
#   'N번' · '선지 N' · '선택지 N' · '첫/두/세/네/다섯 번째'
# '선택지 1' 을 빠뜨려 정답 ④를 '선택지 1'이라 부른 해설이 실제로 인쇄됐다.
_ORDINAL = {"첫": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "여섯": 6}
_ORD_BACK = {v: k for k, v in _ORDINAL.items()}
_REF = re.compile(
    r'(?<![(\d])(?:(\d)번(?!\s*문장|\s*째)'
    r'|선지\s*(\d)'
    r'|선택지\s*(\d)'
    r'|(첫|두|세|네|다섯|여섯)\s*번째)')


def relabel_choice_refs(text: str, mapping: dict[int, int]) -> str:
    """해설이 지칭한 '모든' 선지 번호를 재배열 뒤의 표시 번호로 한꺼번에 바꾼다.

    relabel_answer_ref 는 정답 번호 하나만 고쳤다. 그런데 해설이 오답까지 산문으로
    설명하는 유형(요약문 E)에서는 place_answer 가 선지를 옮기면 오답 번호도 전부
    어긋난다. 실제 결과물에서 '4번(정답)을 오답이라고 설명'하는 해설이 나왔고,
    두 지문 모두에서 같은 방식으로 밀렸다.

    치환은 '동시에' 이뤄져야 한다(1→2, 2→3 을 차례로 적용하면 1이 3이 된다).
    """
    if not text or not mapping:
        return text

    def _sub(m: re.Match) -> str:
        if m.group(4):                          # '세 번째' 같은 한글 서수
            old = _ORDINAL[m.group(4)]
            new = mapping.get(old, old)
            return f"{_ORD_BACK.get(new, m.group(4))} 번째"
        old = int(m.group(1) or m.group(2) or m.group(3))
        new = mapping.get(old, old)
        if m.group(1):
            return f"{new}번"
        return ("선지 " if m.group(2) else "선택지 ") + str(new)

    return _REF.sub(_sub, text)


# ---------------------------------------------------------------------------
# 내용 O/X — O 두 자리를 문항마다 다르게 흩어 놓는다
# ---------------------------------------------------------------------------
# 열 진술 중 O 는 늘 둘이다. 그 둘이 늘 같은 자리(예: ①과 ⑥)에 오면 학생이 지문을
# 읽지 않고 자리만 보고 찍는다. 그렇다고 모델에게 "적당히 섞어 주세요"라고 맡기면
# 앞쪽으로 몰리는 버릇이 나온다. 그래서 자리는 코드가 정한다.
#
# 고를 자리는 '두 O 가 서로 멀고, 앞뒤 어느 한쪽에 치우치지 않는' 짝만 모아 두었다.
# (간격 3 이상 · 둘이 같은 반쪽에 몰리지 않음)
_OX_SLOTS: tuple[tuple[int, int], ...] = (
    (2, 7), (4, 9), (1, 6), (3, 8), (5, 10), (2, 6),
    (3, 10), (1, 8), (4, 7), (5, 9), (2, 9), (3, 6),
)

# 짧은 지문의 영어판은 진술이 여덟이다(schemas.ox_sizes). 자리표도 따로 둔다 —
# 열 칸짜리 표를 그냥 쓰면 ⑨·⑩ 이 없는 문항에 없는 자리가 나온다.
_OX_SLOTS_8: tuple[tuple[int, int], ...] = (
    (2, 6), (4, 8), (1, 5), (3, 7), (2, 7), (1, 6),
    (3, 8), (4, 7), (2, 5), (1, 8), (3, 6), (2, 8),
)

_OX_TABLES: dict[int, tuple[tuple[int, int], ...]] = {8: _OX_SLOTS_8, 10: _OX_SLOTS}


def ox_positions(passage_index: int, version: int, seed: int = 0,
                 n: int = 10) -> tuple[int, int]:
    """이 문항에서 O 가 놓일 두 자리(1-based). n 은 그 문항의 진술 수(8 또는 10).

    passage_index(지문 순서)·version(한글판 0 · 영어판 1)·seed(지문 내용)로 정하므로
    ① 같은 시험지 안에서 문항마다 다르고, ② 같은 지문이면 늘 같은 결과가 나온다.
    """
    # 문항을 만들어지는 순서대로 세어 자리표를 한 칸씩 옮긴다 — 열두 문항까지는
    # 어느 둘도 같은 자리 짝을 쓰지 않는다(지문 6개 × 두 판).
    table = _OX_TABLES.get(n, _OX_SLOTS)
    idx = seed + passage_index * 2 + version
    return table[idx % len(table)]


def place_ox(items: list, positions: tuple[int, int]) -> list:
    """is_true 인 항목 둘을 positions 자리로 옮긴 새 목록.

    items 는 is_true 를 가진 객체들(순서는 모델이 준 그대로). 나머지는 남은 자리에
    원래 순서대로 채운다.
    """
    yes = [it for it in items if getattr(it, "is_true", False)]
    no = [it for it in items if not getattr(it, "is_true", False)]
    if len(yes) != len(positions):
        return list(items)          # 개수가 다르면 손대지 않는다(스키마가 이미 막는다)
    out: list = [None] * len(items)
    for pos, it in zip(sorted(positions), yes):
        out[pos - 1] = it
    rest = iter(no)
    for i in range(len(out)):
        if out[i] is None:
            out[i] = next(rest)
    return out
