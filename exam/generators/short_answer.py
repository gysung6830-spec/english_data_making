"""⑥ 서술형 생성기 (세 소문항) — 지문은 원본 그대로, 과제만 파생."""
from __future__ import annotations

from .. import build as B
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, ShortOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '서술형' 문제(세 소문항)를 만드세요. 지문은 원본 그대로 쓰입니다.

(1) 독해 이해 확인형: 특정 어구·사례가 뜻하는 바를 묻습니다. 답(q1_answer)은 반드시 '한국어'로.
(2) 문법 문장 영작(동사 원형, 낱개 배열):
    - 문법 요소가 많은 문장을 골라 단어를 '낱개로' 뒤섞어 q2_tokens 로 줍니다(구 묶음 금지).
    - q2_answer 는 반드시 '지문에 실제로 있는 문장 그대로'여야 한다(원래 배열이 정답).
      그 문장을 낱개로 뒤섞어 q2_tokens 로, 동사는 '원형'으로 제시하고 변형할 단어는 q2_cues 에.
(3) 영어 요약문 핵심어 빈칸(어형변화):
    - 지문 전체를 한 문장 요약문으로 만들고 (A),(B) 빈칸을 둡니다.
    - q3_before / q3_mid / q3_after 로 요약문을 세 조각(빈칸 기준)으로 나눕니다.
    - q3_cue_a/q3_cue_b 는 제시어 '원형', q3_ans_a/q3_ans_b 는 올바른 형태.
    - q3_reason 은 시제·수일치·태·품사 전환 근거(한국어).

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str]:
    out: ShortOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        model_cls=ShortOut,
        max_tokens=3500,
        max_retries=max_retries,
    )
    return B.make_short(
        analysis.sentences,
        q1_prompt=out.q1_prompt, q1_answer=out.q1_answer,
        q2_prompt=out.q2_prompt, q2_tokens=out.q2_tokens, q2_cues=out.q2_cues,
        q2_answer=out.q2_answer,
        q3_prompt=out.q3_prompt, q3_before=out.q3_before, q3_mid=out.q3_mid,
        q3_after=out.q3_after, q3_cue_a=out.q3_cue_a, q3_cue_b=out.q3_cue_b,
        q3_ans_a=out.q3_ans_a, q3_ans_b=out.q3_ans_b, q3_reason=out.q3_reason,
    )
