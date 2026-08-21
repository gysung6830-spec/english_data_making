"""② 문장 삽입 생성기 — 정본에서 문장 하나만 빼낸다."""
from __future__ import annotations

from .. import build as B
from .. import shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, InsertOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '문장 삽입' 문제를 만드세요.
지문을 새로 쓰지 말고, 빼낼 문장 하나만 고르세요.

- remove_no: '주어진 문장'으로 빼낼 문장 번호(1-based). 넣을 위치가 확정되는 문장,
  즉 however/therefore/this/such 등 연결사·지시어로 시작하거나 앞뒤와 같은 소재로
  묶이는 '내부' 문장을 고르세요(첫 문장·마지막 문장 제외).
- reason: 지시어·연결 관계를 근거로 왜 그 위치인지 한국어로 설명.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1) -> tuple[str, str, list[str]]:
    def _chk(o: InsertOut) -> None:
        n = len(analysis.sentences)
        if not 2 <= o.remove_no <= n - 1:
            raise ValueError(f"빼낼 문장은 첫 문장·마지막 문장이 될 수 없습니다"
                             f"(1과 {n} 사이의 안쪽 문장에서 고르세요).")
        bad = shape.check_insert_cue(analysis.sentences[o.remove_no - 1])
        if bad:
            raise ValueError("삽입 문항 설계 결함 — " + " ".join(bad))

    out: InsertOut = client.structured(
        system=SYSTEM,
        prompt=_PROMPT.format(ctx=context(analysis)),
        cache_prefix=context(analysis),
        model_cls=InsertOut,
        max_tokens=1500,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    flags: list[str] = []
    q, a = B.make_insert(analysis.sentences, out.remove_no - 1, out.reason, flags=flags)
    return q, a, flags
