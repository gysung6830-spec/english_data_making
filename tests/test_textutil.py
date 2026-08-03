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


if __name__ == "__main__":
    test_split_keeps_full_sentences()
    test_prompts_embed_verbatim_list()
    test_short_body_no_list()
    test_name_initials_not_split()
    test_file_tag_cleanup()
    test_dedup_placeholder()
    print("\n문장 분리/프롬프트 삽입 오프라인 테스트 통과 ✅")
