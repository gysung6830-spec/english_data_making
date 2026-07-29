"""문장 분리 유틸 + 프롬프트 '문장 목록' 삽입 오프라인 테스트.

실행: python -m tests.test_textutil
"""
from __future__ import annotations

from src.textutil import split_sentences, sentence_list_block
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


if __name__ == "__main__":
    test_split_keeps_full_sentences()
    test_prompts_embed_verbatim_list()
    test_short_body_no_list()
    print("\n문장 분리/프롬프트 삽입 오프라인 테스트 통과 ✅")
