"""⑥ 서술형 생성기 (세 소문항) — 지문은 원본 그대로, 과제만 파생."""
from __future__ import annotations

import re

from .. import build as B
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, ShortOut
from .base import context

# (2) 어순 배열 표준 발문 — LLM 발문이 내부 용어를 흘리거나 뭉개졌을 때의 대체.
_Q2_FALLBACK = ("다음 단어들을 어법과 문맥에 맞게 배열하여 원래 문장을 완성하시오. "
                "(동사는 원형으로 제시되어 있으므로 알맞은 형태로 바꿔 쓸 것)")


def _clean_q2_prompt(p: str) -> str:
    """(2) 어순 배열 발문에서 '내부 지시 용어' 누출을 제거한다(학생용 정리).

    생성기 지시문의 '[문장] 목록'이라는 표현이 학생용 발문(q2_prompt)에 그대로
    복사되는 경우가 있어, 이를 걷어내고 자연스러운 발문으로 만든다. 지시가
    뭉개지면 표준 발문(_Q2_FALLBACK)으로 대체한다."""
    s = (p or "").strip()
    s = re.sub(r"\[?\s*문장\s*\]?\s*목록\s*(의|에서|을|를|에|은|이|)\s*", "", s)
    s = s.replace("[문장]", "문장").replace("[보기]", "<보기>")
    s = re.sub(r"\s{2,}", " ", s).strip()
    if len(s) < 12 or "배열" not in s:
        return _Q2_FALLBACK
    return s


_PROMPT = """아래 '정본 지문'으로 '서술형' 문제(세 소문항)를 만드세요. 지문은 원본 그대로 쓰입니다.

(1) 독해 이해 확인형: 특정 어구·사례가 뜻하는 바를 묻습니다. 답(q1_answer)은 반드시 '한국어'로.
(2) 문법 문장 영작(동사 원형, 낱개 배열):
    - 정본 지문의 여러 문장 중 문법 요소가 많은 문장 '하나'를 고릅니다.
    - q2_answer 는 그 문장을 '글자 그대로'(단어·축약형·구두점 포함, 요약·수정·의역 금지)
      복사한 것이어야 한다 → 원래 배열이 정답. 새로 쓰거나 바꾸지 마세요.
    - q2_tokens 는 그 문장의 단어만 '낱개로' 뒤섞은 것(구 묶음 금지). 동사는 '원형'으로
      제시하고, 원형으로 바꾼 단어만 q2_cues 에 넣습니다.
    - q2_prompt 는 '학생용 발문'입니다. 내부 표현('문장 목록' 등)을 쓰지 말고,
      "다음 단어들을 배열하여 완전한 문장을 완성하시오"처럼 자연스럽게 쓰세요.
(3) 영어 요약문 핵심어 빈칸(어형변화):
    - 지문 전체를 한 문장 요약문으로 만들고 (A),(B) 빈칸을 둡니다.
    - q3_before / q3_mid / q3_after 로 요약문을 세 조각(빈칸 기준)으로 나눕니다.
      (A)는 before와 mid 사이, (B)는 mid와 after 사이에 자동으로 들어갑니다. 조각
      '안에는' '(A)'·'(B)' 라벨을 절대 쓰지 마세요(라벨·빈칸은 조판기가 붙입니다).
    - q3_cue_a/q3_cue_b 는 제시어 '원형', q3_ans_a/q3_ans_b 는 올바른 형태.
    - q3_reason 은 시제·수일치·태·품사 전환 근거(한국어).

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    out: ShortOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=ShortOut,
        max_tokens=3500,
        max_retries=max_retries,
    )
    flags: list[str] = []
    q, a = B.make_short(
        analysis.sentences,
        q1_prompt=out.q1_prompt, q1_answer=out.q1_answer,
        q2_prompt=_clean_q2_prompt(out.q2_prompt), q2_tokens=out.q2_tokens, q2_cues=out.q2_cues,
        q2_answer=out.q2_answer,
        q3_prompt=out.q3_prompt, q3_before=out.q3_before, q3_mid=out.q3_mid,
        q3_after=out.q3_after, q3_cue_a=out.q3_cue_a, q3_cue_b=out.q3_cue_b,
        q3_ans_a=out.q3_ans_a, q3_ans_b=out.q3_ans_b, q3_reason=out.q3_reason,
        flags=flags,
    )
    return q, a, flags
