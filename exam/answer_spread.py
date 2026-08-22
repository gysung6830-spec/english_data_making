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
SLOTS_MERGED = {"topic": 0, "title": 1, "content": 2, "B": 3, "E": 4, "F": 5,
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
