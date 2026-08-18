"""변형문제 3회 데모 — DNA 지문 하나에서 주제3·제목3·내용일치3·함축의미3(오프라인 미리보기용)."""
from __future__ import annotations

from . import build as B
from . import build2 as B2
from .demo_data import DNA
from .set3 import TYPE_ORDER3
from .types import Passage

_S = DNA.sentences


def _topic(choices, ans, reason, wrong):
    return B.make_topic(_S, choices, ans, reason, wrong)


def _content(choices, ans, reason, wrong):
    return B.make_content(_S, choices, ans, reason, wrong)


def _imply(phrase, choices, ans, reason, wrong):
    return B2.make_B(_S, phrase, choices, ans, reason, wrong)


# ── 주제 3 ─────────────────────────────────────────────────────────────────
_TOPIC = [
    (["how DNA can hold vast data in a tiny, long-lasting form",
      "why hard drives will soon replace all natural molecules",
      "the danger of storing photographs inside living cells",
      "how ancient bone and ice were first discovered",
      "why digital files are cheaper than DNA today"], 1,
     "DNA가 방대한 정보를 아주 작고 오래가는 형태로 담는다는 밀도·내구성이 핵심.",
     {2: "하드 드라이브가 분자를 대체한다는 내용 없음(무관).",
      3: "저장의 위험을 다루지 않음(무관).", 4: "발견 경위는 지엽(무관).",
      5: "가격 비교가 주제가 아님(부분)."}),
    (["a mistake scientists made when encoding files",
      "the extraordinary storage density and durability of DNA",
      "the history of computer hard drives",
      "reasons DNA quickly loses information",
      "how libraries organize photographs"], 2,
     "글 전체가 DNA의 저장 밀도와 내구성을 예찬한다.",
     {1: "실수 사례 아님(무관).", 3: "하드 드라이브 역사 아님(무관).",
      4: "정보를 빨리 잃는다는 건 반대(모순).", 5: "도서관 정리와 무관."}),
    (["DNA as an ultra-compact, long-lived information store",
      "the failure of synthetic DNA experiments",
      "why molecules cannot hold any data",
      "a warning against reading old DNA",
      "the high speed and low cost of DNA storage"], 1,
     "아주 작고 오래가는 정보 저장체로서의 DNA.",
     {2: "실패를 논지로 삼지 않음(모순).", 3: "데이터를 못 담는다는 건 반대(모순).",
      4: "경고 글이 아님(무관).", 5: "지문은 '느리고 비싸다'고 함(모순)."}),
]

# ── 제목 3 ─────────────────────────────────────────────────────────────────
_TITLE = [
    (["DNA: Nature's Tiny Data Vault",
      "The End of the Hard Drive Era",
      "Why Ice Preserves Everything",
      "Photographs of the Distant Past",
      "A Cheap and Instant Storage Fix"], 1,
     "자연의 작은 데이터 금고 — 밀도·내구성을 함축한 제목.",
     {2: "하드드라이브 종말이 논지가 아님.", 3: "얼음 보존 일반론 아님.",
      4: "사진 자체가 주제 아님.", 5: "값싸고 즉각적이라는 건 반대(모순)."}),
    (["The Slow Death of Digital Files",
      "Molecules That Remember for Millennia",
      "How to Build a Faster Computer",
      "The Fragility of Modern Memory",
      "Ordinary Drives Beat DNA"], 2,
     "수천 년을 기억하는 분자 — 내구성·저장을 함축.",
     {1: "디지털 파일의 죽음이 아님.", 3: "컴퓨터 제작법 아님.",
      4: "취약성이 아니라 내구성이 논지(모순).", 5: "DNA가 더 우수(모순)."}),
    (["Storing a Library Inside a Molecule",
      "The Cost of Reading Old Bones",
      "Hard Drives Through History",
      "Why DNA Cannot Last Long",
      "Digital Data Is Always Safer"], 1,
     "분자 속에 도서관을 담다 — 밀도·응용을 함축.",
     {2: "옛 뼈 판독 비용이 주제 아님.", 3: "하드드라이브 역사 아님.",
      4: "오래 못 간다는 건 반대(모순).", 5: "디지털이 늘 안전하다는 건 무관·모순."}),
]

# ── 내용 일치 3(한글 선지) ──────────────────────────────────────────────────
_CONTENT = [
    (["1그램의 DNA가 이론상 일반 하드 드라이브 수백만 개 분량을 담을 수 있다.",
      "DNA는 정보를 넓은 공간에 느슨하게 저장한다.",
      "합성 DNA 저장 기술은 이미 빠르고 저렴하다.",
      "DNA는 며칠 만에 정보를 잃는다.",
      "연구자들은 DNA 연구를 최근에 포기했다."], 1,
     "일치 — A single gram ~ millions of ordinary hard drives.",
     {2: "'아주 작은 공간'과 반대(모순).", 3: "'여전히 느리고 비싸다'(모순).",
      4: "수만 년 보존된다(모순).", 5: "부호화를 시작했다(모순)."}),
    (["DNA는 뼈와 얼음 속에서 수만 년 동안 보존될 수 있다.",
      "DNA 저장 기술은 현재 매우 값싸다.",
      "DNA는 살아있는 세포에만 잠깐 존재한다.",
      "연구자들은 디지털 파일을 종이에 부호화한다.",
      "DNA는 정보를 거의 담지 못한다."], 1,
     "일치 — durable, surviving in bone and ice for tens of thousands of years.",
     {2: "'비싸다'(모순).", 3: "수만 년 보존(모순).",
      4: "종이가 아니라 합성 DNA(주체·대상 바꿔치기).", 5: "방대한 정보를 담음(모순)."}),
    (["연구자들은 디지털 파일을 합성 DNA에 부호화하기 시작했다.",
      "DNA 저장은 이미 빠르게 상용화되었다.",
      "DNA는 열과 빛에 매우 약하다.",
      "1그램의 DNA는 하드 드라이브 한 개 분량만 담는다.",
      "DNA는 정보를 오래 보존하지 못한다."], 1,
     "일치 — researchers have begun to encode digital files into synthetic DNA.",
     {2: "'여전히 느리고 비싸다'(모순).", 3: "내구성이 뛰어남(모순).",
      4: "수백만 개 분량(부분·수치 왜곡).", 5: "수천 년 보존(모순)."}),
]

# ── 함축의미 3(밑줄 어구 = 지문 실제 표현) ──────────────────────────────────
_IMPLY = [
    ("nature's own hard drive",
     ["a natural system that stores vast information in a tiny space",
      "a literal metal device found inside cells",
      "something that can hold almost no data",
      "a copy of human technology made by nature",
      "proof that drives outperform DNA"], 1,
     "DNA를 저장장치에 빗댄 비유 — 좁은 공간에 방대한 정보를 저장하는 자연의 장치.",
     {2: "실제 금속 장치라는 축자 오독.", 3: "거의 못 담는다는 건 반대.",
      4: "자연이 기술을 베꼈다는 내용 없음.", 5: "드라이브가 낫다는 건 반대."}),
    ("packs an enormous amount into a vanishingly small space",
     ["fits a huge quantity of data into an extremely tiny volume",
      "spreads data loosely across a large area",
      "needs a giant factory to operate",
      "loses data as it shrinks",
      "works only at very low temperatures"], 1,
     "방대한 정보를 아주 작은 공간에 담는다는 '밀도'의 함의.",
     {2: "넓게 흩는다는 건 반대.", 3: "공장 필요는 무관.",
      4: "줄면서 잃는다는 건 무관·모순.", 5: "저온 전용은 무관."}),
    ("astonishingly durable",
     ["able to survive intact for a very long time",
      "extremely easy to erase on purpose",
      "useful only for a single day",
      "impossible to store anywhere",
      "cheaper than every other method"], 1,
     "오랜 세월 온전히 견딘다는 '내구성'의 함의.",
     {2: "일부러 지우기 쉽다는 건 무관·반대.", 3: "하루만 쓸모는 반대.",
      4: "저장 불가는 반대.", 5: "가격 비교는 무관."}),
]


def _passage_dna3() -> Passage:
    p = Passage(title=DNA.title)
    for i, (ch, ans, r, w) in enumerate(_TOPIC, 1):
        p.set_qa(f"topic_{i}", *_topic(ch, ans, r, w))
    for i, (ch, ans, r, w) in enumerate(_TITLE, 1):
        p.set_qa(f"title_{i}", *_topic(ch, ans, r, w))     # 제목도 topic 렌더 구조 공유
    for i, (ch, ans, r, w) in enumerate(_CONTENT, 1):
        p.set_qa(f"content_{i}", *_content(ch, ans, r, w))
    for i, (ph, ch, ans, r, w) in enumerate(_IMPLY, 1):
        p.set_qa(f"imply_{i}", *_imply(ph, ch, ans, r, w))
    # 조판 순서(TYPE_ORDER3)와 키가 일치하는지 방어적 확인
    assert set(p.q) == set(TYPE_ORDER3)
    return p


def demo_passages_3() -> list[Passage]:
    return [_passage_dna3()]
