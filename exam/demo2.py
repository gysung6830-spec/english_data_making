"""변형문제 2회 데모 — DNA 지문 하나에서 7유형(A~G)을 파생(오프라인 미리보기용)."""
from __future__ import annotations

from . import build2 as B2
from .demo_data import DNA
from .set2 import A, B, C, D, E, F, G
from .types import Passage


def _passage_dna2() -> Passage:
    p = Passage(title=DNA.title)
    s = DNA.sentences

    # A · 어법·어휘 짝짓기 (오답 2개 = 어법 ⓐ + 반의어 ⓒ)
    p.set_qa(A, *B2.make_A(
        s,
        marks=[
            (1, "packs", "pack"),          # ⓐ 어법 오류(it packs)
            (2, "combined", "combined"),   # ⓑ 적절
            (3, "durable", "fragile"),     # ⓒ 반의어 오류
            (4, "encode", "encode"),       # ⓓ 적절
            (5, "preserved", "preserved"), # ⓔ 적절
        ],
        answer_no=2,
        reason=("ⓐ는 주어 it(단수)에 맞춰 pack→packs (수 일치 오류). ⓒ는 DNA가 수만 년 견딘다는 "
                "문맥이므로 fragile(부서지기 쉬운)이 아니라 durable(안정적인)이라야 한다(반의어 "
                "오류). 따라서 부적절한 것끼리 짝지으면 ⓐ, ⓒ."),
        choices=["ⓐ, ⓑ", "ⓐ, ⓒ", "ⓑ, ⓓ", "ⓒ, ⓔ", "ⓓ, ⓔ"],
    ))

    # B · 함의추론
    p.set_qa(B, *B2.make_B(
        s,
        phrase="nature's own hard drive",
        choices=[
            "DNA가 좁은 공간에 방대한 정보를 저장·보관하는, 자연이 만든 정보 저장 장치라는 뜻",
            "DNA가 실제로 컴퓨터 하드웨어의 한 부품으로 쓰인다는 뜻",
            "DNA는 정보를 거의 저장하지 못한다는 뜻",
            "자연이 인간의 저장 기술을 그대로 베꼈다는 뜻",
            "하드 드라이브가 DNA보다 저장 능력이 뛰어나다는 뜻",
        ],
        answer_no=1,
        reason=("'nature's own hard drive'는 DNA를 컴퓨터 저장장치에 빗댄 비유로, 아주 좁은 "
                "공간에 방대한 정보를 저장·보관하는 자연의 정보 저장 장치라는 의미다. 밑줄 주변 "
                "한 문장이 아니라 글 전체(밀도·내구성·응용)를 종합해야 도달한다."),
        wrong={
            2: "비유적 표현이므로 DNA가 '실제 하드웨어 부품'이라는 축자적 의미가 아니다.",
            3: "글은 DNA가 방대한 정보를 저장한다고 하므로 '거의 저장 못 한다'는 논지에 위배된다.",
            4: "자연이 인간 기술을 베꼈다는 내용은 글에 없다(무관).",
            5: "글은 DNA의 저장 효율을 예찬하므로 '하드 드라이브가 더 우수'는 반대다.",
        },
    ))

    # C · 어법 오류 판별(복수정답) — 1회 어법 빌더 재사용
    p.set_qa(C, *B2.make_C(
        s,
        marks=[
            (0, "which", "which"),
            (1, "packs", "pack"),           # 오류
            (2, "combined", "combined"),
            (3, "surviving", "surviving"),
            (4, "have", "has"),             # 오류
            (5, "allows", "allow"),         # 오류
            (5, "preserved", "preserved"),
            (6, "stored", "stored"),
        ],
        answer_nos=[2, 5, 6],
        reasons={
            2: "주어 it 은 단수이므로 pack → packs (수 일치).",
            5: "주어 researchers 는 복수이므로 has → have (수 일치).",
            6: "주어 it(the technique) 은 단수이므로 allow → allows (수 일치).",
        },
    ))

    # D · 어순 배열
    p.set_qa(D, *B2.make_D(
        tokens=["researchers", "begin", "to", "encode", "digital", "files",
                "into", "synthetic", "DNA"],
        cues=["begin"],
        answer_sentence="Researchers have begun to encode digital files into synthetic DNA.",
        reason="동사 begin 을 문맥(현재완료)에 맞춰 have begun 으로 변형하고 어순을 맞춘다.",
    ))

    # E · 요약문 빈칸(객관식)
    p.set_qa(E, *B2.make_E(
        before="DNA can ",
        mid=" a huge amount of information in a tiny space, so scientists are trying to ",
        after=" digital data inside it.",
        choice_pairs=[("store", "lose"), ("store", "preserve"), ("delete", "preserve"),
                      ("store", "delete"), ("hide", "reveal")],
        answer_no=2,
        reason=("지문은 DNA가 정보를 '저장(store)'하고, 과학자들이 그 안에 디지털 데이터를 "
                "'보존(preserve)'하려 한다는 내용이므로 (A) store, (B) preserve. 따라서 ②."),
    ))

    # F · 빈칸추론
    p.set_qa(F, *B2.make_F(
        before=("DNA is nature's own hard drive. What makes it remarkable is not only that it "
                "stores information, but that it packs an enormous amount into "),
        after=". A single gram could hold as much data as millions of ordinary hard drives.",
        choices=[
            "a vanishingly small space",
            "a brightly lit laboratory",
            "a widely shared network",
            "an expensive silicon chip",
            "a slowly fading memory",
        ],
        answer_no=1,
        reason=("빈칸 앞뒤는 방대한 정보를 '아주 좁은 공간'에 담는다는 밀도 이야기이므로 ①이 "
                "앞뒤 논리로 유일하게 복원된다."),
        wrong={
            2: "실험실 조명은 저장 밀도와 무관하다(무관).",
            3: "공유 네트워크는 '좁은 공간 저장'이라는 맥락과 맞지 않는다(무관).",
            4: "실리콘 칩은 DNA와 대비되는 대상일 뿐, 빈칸엔 '작은 공간'이 와야 한다(모순).",
            5: "'서서히 사라지는 기억'은 DNA의 내구성과 반대다(모순).",
        },
    ))

    # G · 내용일치 개수
    p.set_qa(G, *B2.make_G(
        s,
        statements=[
            "1그램의 DNA는 이론상 일반 하드 드라이브 수백만 개에 맞먹는 데이터를 담을 수 있다.",
            "DNA는 뼈와 얼음 속에서 수만 년 동안 보존될 수 있다.",
            "합성 DNA에 데이터를 저장하는 기술은 이미 빠르고 저렴하다.",
            "연구자들은 디지털 파일을 합성 DNA에 부호화하기 시작했다.",
            "DNA는 정보를 넓은 공간에 느슨하게 저장한다.",
        ],
        match_count=3,
        reason="일치하는 것은 (a),(b),(d) 세 개이므로 정답은 ③(3개).",
        per_stmt={
            1: "일치 — A single gram ~ millions of ordinary hard drives.",
            2: "일치 — durable, surviving for tens of thousands of years.",
            3: "불일치 — 지문은 '여전히 느리고 비싸다(still slow and expensive)'.",
            4: "일치 — researchers have begun to encode ~ synthetic DNA.",
            5: "불일치 — 지문은 '아주 작은 공간(vanishingly small space)'.",
        },
    ))
    return p


def demo_passages_2() -> list[Passage]:
    return [_passage_dna2()]
