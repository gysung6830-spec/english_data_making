"""문장 분리 유틸 + 프롬프트 '문장 목록' 삽입 오프라인 테스트.

실행: python -m tests.test_textutil
"""
from __future__ import annotations

from src.textutil import split_sentences, sentence_list_block, file_tag, dedup_placeholder
from src import workbook_prompts as wp
from src import prose_prompts as pp
from src import blanks_prompts as bp

BODY = (
    "Conservation aims to keep an object in its present state, to protect it from change, "
    "usually for contemplation, research, display, and perhaps for use. "
    "Restoration involves restoring a historical instrument, e.g. a violin, or a painting. "
    "Conservators see themselves as protectors."
)


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def test_split_keeps_full_sentences():
    s = split_sentences(BODY)
    _check("문장 3개로 분리", len(s) == 3)
    _check("첫 문장 앞부분(주어) 보존",
           s[0].startswith("Conservation aims to keep an object in its present state"))
    _check("약어 e.g. 에서 분리하지 않음", "e.g. a violin" in s[1])
    _check("마지막 문장 온전", s[2] == "Conservators see themselves as protectors.")


def test_prompts_embed_verbatim_list():
    for name, text in [("workbook", wp.workbook_prompt("T", BODY)),
                       ("prose", pp.prose_prompt("T", BODY)),
                       ("blanks", bp.blanks_prompt("T", BODY))]:
        _check(f"{name} 프롬프트에 문장 목록 포함", "문장 목록" in text)
        _check(f"{name} 프롬프트에 첫 문장 전체 포함",
               "S1) Conservation aims to keep an object in" in text)


def test_short_body_no_list():
    _check("문장 1개면 목록 생략", sentence_list_block("Just one sentence.") == "")


def test_name_initials_not_split():
    # 이름 이니셜(Paul R. Ehrlich)에서 문장을 쪼개면 안 된다(과거 '앞 문장' 오류의 원인).
    body = ("The American biologist Paul R. Ehrlich wrote The Population Bomb. "
            "In 1970 he predicted disaster.")
    s = split_sentences(body)
    _check("이니셜에서 분리 안 함(2문장)", len(s) == 2)
    _check("Paul R. Ehrlich 한 문장 유지", s[0].startswith("The American biologist Paul R. Ehrlich"))
    # 문두 연속 이니셜도 보호
    _check("J. K. 연속 이니셜 보호", split_sentences("J. K. Rowling wrote it. She was famous.")[0]
           == "J. K. Rowling wrote it.")


def test_file_tag_cleanup():
    # 뱃지 파일명 태그: 번호 토큰 제거 후 남는 고아 '번'·쉼표를 정리해 깔끔하게.
    _check("고아 번·쉼표 정리", file_tag("1번올림포스 4강, 3.pdf") == "올림포스 4강 3")
    _check("이미 깨진 태그도 정리", file_tag("번올림포스 4강 , 3") == "올림포스 4강 3")
    _check("범위 번호 제거", file_tag("30~40번 워크북.pdf") == "워크북")


def test_dedup_placeholder():
    # 정답 어구가 자리표시자 옆에 남아 중복되면 제거(통합카드 배열/어형 오류 정리)
    _check("앞 중복 제거",
           dedup_placeholder("index {{Q5}} how long a resource {{Q6}}.", "{{Q6}}",
                             "how long a resource would last") == "index {{Q5}} {{Q6}}.")
    _check("뒤 중복 제거",
           dedup_placeholder("how it might {{Q6}} run", "{{Q6}}", "be run") == "how it might {{Q6}}")
    # 중복이 아니면 그대로(정상 문장 보존)
    _check("겹침 없으면 유지",
           dedup_placeholder("Forecasters {{Q1}} predict", "{{Q1}}", "who") == "Forecasters {{Q1}} predict")
    _check("어구 무관하면 유지",
           dedup_placeholder("We {{Q1}} the race", "{{Q1}}", "run") == "We {{Q1}} the race")
    # 부사(…ly) 하나가 낀 비인접 중복도 제거(통합카드/어형 실측: "(respond) usually respond")
    _check("부사 낀 비인접 중복 제거",
           dedup_placeholder("A bystander {{Q1}} usually respond, just", "{{Q1}}", "will respond")
           == "A bystander {{Q1}} usually just")
    _check("부사 낀 중복: comforted 제거",
           dedup_placeholder("the infant {{Q1}} sufficiently comforted and reassured", "{{Q1}}",
                             "has been comforted") == "the infant {{Q1}} sufficiently and reassured")
    # 정답과 무관하면 부사 뒤 단어는 건드리지 않음
    _check("부사 뒤 무관 단어 유지",
           dedup_placeholder("He {{Q1}} quickly ran home", "{{Q1}}", "had") == "He {{Q1}} quickly ran home")


def test_strip_form_leftover():
    from src.textutil import strip_form_leftover as s
    # 정답과 무관하게 '(원형)의 활용형' 중복 제거(복합수동 comforted 등)
    _check("복합수동 comforted 제거(부사 낀)",
           s("the infant {{P1}} sufficiently comforted and reassured.", "{{P1}}", "comfort")
           == "the infant {{P1}} sufficiently and reassured.")
    _check("인접 활용형 changed 제거",
           s("Concepts {{P1}} changed.", "{{P1}}", "change") == "Concepts {{P1}}")
    # 정상 문장(활용형 아님)은 유지
    _check("무관 단어 유지(our use)",
           s("We need to dramatically {{P1}} our use.", "{{P1}}", "reduce")
           == "We need to dramatically {{P1}} our use.")
    _check("무관 단어 유지(the picture)",
           s("They {{P1}} the picture.", "{{P1}}", "post") == "They {{P1}} the picture.")
    _check("짧은 원형(2자)은 미처리", s("It {{P1}} be.", "{{P1}}", "do") == "It {{P1}} be.")


def test_shuffle_choices():
    from src.textutil import shuffle_choices
    # 보기 집합·정답은 보존, 순서만 바뀔 수 있음
    out = shuffle_choices("[ a / b / c ]", "seed1")
    _check("보기 집합 보존", sorted(o.strip() for o in out[1:-1].split("/")) == ["a", "b", "c"])
    _check("[] 형식 유지", out.startswith("[ ") and out.endswith(" ]"))
    # 지칭 '= [ … ]' 은 prefix 유지
    r = shuffle_choices("= [ x / y / z ]", "s")
    _check("지칭 prefix 유지", r.startswith("= [ ") and set("xyz") == set(r) & set("xyz"))
    # 비[]선택형은 그대로
    _check("(원형) 그대로", shuffle_choices("(react)", "s") == "(react)")
    _check("〈 … 〉 그대로", shuffle_choices("〈 a / b 〉", "s") == "〈 a / b 〉")
    # 결정적: 같은 입력·시드는 같은 결과
    _check("결정적 재현", shuffle_choices("[ p / q / r ]", "k") == shuffle_choices("[ p / q / r ]", "k"))
    # 정답 위치 쏠림 제거: 첫 보기가 'a'인 문항이 전부는 아니어야 함(다양한 시드에서 분포)
    firsts = [shuffle_choices("[ a / b / c ]", f"s{i}")[2:3] for i in range(30)]
    _check("정답(첫 보기) 위치 분산", firsts.count("a") < 30 and len(set(firsts)) >= 2)
    # 보기 중복 제거: [ resolved / settled / dissolved / resolved ] → 3개 유니크
    dd = shuffle_choices("[ resolved / settled / dissolved / resolved ]", "k")
    opts = sorted(o.strip() for o in dd[1:-1].split("/"))
    _check("중복 보기 제거(4→3)", opts == ["dissolved", "resolved", "settled"])


def test_format_qno():
    from src.textutil import format_qno
    # '단원-문항' 형식: 10-A / 10-1 / 10-2 / 10-3, 서술형·논술형은 그대로
    _check("ANALYSIS → 10-A", format_qno("", "Ch. 04 Unit 10 - 수능 대비 ANALYSIS") == "10-A")
    _check("1번 + Unit 10 → 10-1", format_qno("1번", "Ch. 04 Unit 10") == "10-1")
    _check("2번 → 10-2", format_qno("2번", "Ch. 04 Unit 10") == "10-2")
    _check("3번 → 10-3", format_qno("3번", "Ch. 04 Unit 10") == "10-3")
    _check("서술형 유지", format_qno("서술형") == "서술형")
    _check("논술형 유지", format_qno("논술형") == "논술형")
    _check("이미 최종형식 유지(10-A)", format_qno("10-A") == "10-A")
    _check("이미 최종형식 유지(10-1)", format_qno("10-1") == "10-1")
    _check("Ch.04 는 단원 아님(Unit 10 사용)", format_qno("1번", "Ch. 04 Unit 10") == "10-1")
    _check("단원 없으면 문항만(1번)", format_qno("1번") == "1번")
    _check("판단 불가 시 빈 문자열", format_qno("", "그냥 제목") == "")
    _check("힌트의 서술형 감지", format_qno("", "Unit 10 - 서술형") == "서술형")


def test_source_prefix():
    from src.textutil import source_prefix
    # 교재명만 남기고 문항번호와 겹치는 단원/문항 토큰은 제거(뱃지 '교재명 10-1' 중복 방지)
    _check("Unit 토큰 제거", source_prefix("올림포스 독해 Unit 10") == "올림포스 독해")
    _check("Ch.·Unit 동시 제거", source_prefix("Ch. 04 Unit 10 올림포스") == "올림포스")
    _check("'출처:' 접두 제거", source_prefix("출처: EBS 수능특강") == "EBS 수능특강")
    _check("10-1 토큰 제거", source_prefix("자이스토리 10-1") == "자이스토리")
    _check("N과·N번 제거", source_prefix("리딩튜터 3과 30번") == "리딩튜터")
    _check("빈 출처 → 빈 문자열", source_prefix("") == "")
    _check("순수 교재명 유지", source_prefix("EBS 수능특강 영어독해") == "EBS 수능특강 영어독해")
    # 실제 조합: 교재명 + 문항번호 (교재명이 앞)
    from src.textutil import format_qno
    pref = source_prefix("올림포스 독해 Unit 10")
    qno = format_qno("1번", "Ch. 04 Unit 10")
    _check("교재명 + 문항번호 조합", f"{pref} {qno}".strip() == "올림포스 독해 10-1")


def test_shuffle_order_display():
    from src.textutil import shuffle_order_display
    # 정답 어순 그대로 들어와도 '정답과 다르게' 섞임(여러 번 반복해 확률적 실패 방지)
    for _ in range(50):
        d = shuffle_order_display("〈 It / was / not / until 〉", "It was not until")
        order = " ".join(p.strip() for p in d.strip("〈〉 ").split(" / "))
        _check("순서배열 ≠ 정답 어순", order != "It was not until")
        _check("조각 집합 보존", sorted(order.split()) == sorted(["It", "was", "not", "until"]))
    # 〈 〉 형식이 아니면 그대로
    _check("비〈〉 그대로", shuffle_order_display("[ a / b ]", "") == "[ a / b ]")
    _check("1조각 그대로", shuffle_order_display("〈 only 〉", "only") == "〈 only 〉")


if __name__ == "__main__":
    test_split_keeps_full_sentences()
    test_prompts_embed_verbatim_list()
    test_short_body_no_list()
    test_name_initials_not_split()
    test_file_tag_cleanup()
    test_dedup_placeholder()
    test_shuffle_choices()
    test_format_qno()
    test_shuffle_order_display()
    test_source_prefix()
    test_strip_form_leftover()
    print("\n문장 분리/프롬프트 삽입 오프라인 테스트 통과 ✅")
