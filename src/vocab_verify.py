"""어휘 (상) 자동 교차검증 — 별도(저비용) LLM 이 '정답이 정확히 2개인지' 재검토.

어휘 (상) 유형은 '3개 보기 중 2개(원문·유의어) 고르기'라 구조상 출제오류 위험이 있다.
  - 오답 ③(형태 유사어)이 실제로는 유의어여서 '정답이 3개'가 되는 경우
  - 유의어라던 보기가 문맥상 어색해 '정답이 1개'뿐인 경우
이런 항목을 코드로는 잡을 수 없으므로, 생성이 끝난 뒤 어휘 (상) 문항만 모아
별도 LLM(기본 Haiku 4.5, 저비용)에게 '문맥상 정답 보기 개수'를 다시 세게 한다.
정확히 2개가 아니면 그 문항을 '제외'한다(문장은 그대로 남고 자리표시자만 렌더에서 제거).

비용: 어휘(상) 문항만 한 번에 묶어 1회 호출 → 지문당 수백~1천 토큰 수준(Haiku 기준 +1~2%).
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .client import ClaudeClient
from .config import Config
from .prose_render import LLMProsePack

# 검증용 저비용 모델 기본값 (판정 난이도가 낮아 Haiku 로 충분)
DEFAULT_VERIFY_MODEL = "claude-haiku-4-5"

SYSTEM = (
    "당신은 한국 고등학교 영어 어휘 문항의 '출제 오류' 검수관이다. "
    "각 문항은 한 영어 문장의 특정 위치에 보기 3개 '[ A / B / C ]'를 두고, "
    "그중 '문맥상 뜻이 통하는 보기'를 고르게 하는 유형이다(정상 문항은 정답이 정확히 2개). "
    "당신은 각 문항에 대해 '그 문장 문맥에서 뜻이 자연스럽게 통하는 보기'가 몇 개인지 냉정하게 센다. "
    "요청된 JSON 스키마에 정확히 맞는 JSON 으로만 응답한다."
)

_RULES = """[검수 기준]
- 각 item 은 key, sentence(원문 문장), options(보기 3개), intended_answers(출제자가 정답이라 표시한 2개), gloss(정답 뜻).
- 그 '문장 문맥'에 넣었을 때 '뜻이 자연스럽게 통하는(=정답이 될 수 있는)' 보기가 몇 개인지 세어 valid_count 에 넣는다.
  · 원문 단어와 '뜻이 통하는 유의어'는 정답으로 센다.
  · 철자만 비슷하고 뜻이 다르거나, 문맥에 넣으면 어색한 단어는 정답이 아니다.
- ok 판정:
  · valid_count 가 정확히 2 이고, 그 2개가 intended_answers 와 사실상 일치하면 ok=true.
  · valid_count 가 3 이상(오답이 사실은 유의어 → 정답 과다) 이거나 1 이하(유의어가 문맥상 어색 → 정답 부족)면 ok=false.
  · intended_answers 가 실제 정답 보기와 어긋나도 ok=false.
- reason 에는 한 줄로 근거(특히 ok=false 인 이유: 어떤 보기가 왜 문제인지)를 쓴다.
- 확신이 없으면 보수적으로 ok=false(문항 제외 쪽)로 판정한다. 애매한 문항을 남기는 것보다 빼는 게 낫다.

[출력 형식 — JSON]
{verdicts:[{key, ok, valid_count, reason}]}
- 모든 item 에 대해 하나씩, 입력과 같은 key 로 판정을 낸다. 다른 말 없이 JSON 만 출력한다."""


class VocabVerdict(BaseModel):
    key: str
    ok: bool = True
    valid_count: int = 2
    reason: str = ""


class VocabVerifyResult(BaseModel):
    verdicts: list[VocabVerdict] = Field(default_factory=list)


def _options_of(display: str) -> list[str]:
    """'[ A / B / C ]' → ['A','B','C'] (대괄호 안만 / 로 분리)."""
    inside = display.split("[", 1)[-1].rsplit("]", 1)[0] if "[" in display else display
    return [c.strip() for c in inside.split("/") if c.strip()]


def _collect_items(llm: LLMProsePack) -> list[dict]:
    """어휘 (상)=vocab_items 만 (key, 문장, 보기, 정답, 뜻)로 수집."""
    items: list[dict] = []
    for s in llm.sentences:
        for it in s.vocab_items:
            opts = _options_of(it.display)
            answers = [a.strip() for a in (it.answer or "").split("/") if a.strip()]
            items.append({
                "key": f"{s.no}:{it.id}",
                "sentence": s.en,
                "options": opts,
                "intended_answers": answers,
                "gloss": it.gloss or "",
            })
    return items


def _verify_prompt(items: list[dict]) -> str:
    import json

    lines = ["아래 어휘 (상) 문항들의 '문맥상 정답 보기 개수'를 검수하라.\n", _RULES,
             "\n[검수 대상 문항]"]
    for it in items:
        lines.append(json.dumps(it, ensure_ascii=False))
    return "\n".join(lines)


def verify_vocab_pack(client: ClaudeClient, cfg: Config, llm: LLMProsePack,
                      model: str | None = None) -> LLMProsePack:
    """어휘 (상) 문항을 별도 LLM 으로 교차검증해 '출제오류' 항목을 제거한 LLMProsePack 반환.

    - 검증 대상이 없으면 원본을 그대로 반환.
    - 검증 호출이 실패하면(네트워크/파싱 등) 원본을 그대로 반환한다(fail-open: 좋은 문항까지
      잃지 않도록). 판정이 없는 문항도 유지한다.
    """
    items = _collect_items(llm)
    if not items:
        return llm
    verify_model = model or getattr(cfg.processing, "verify_model", "") or DEFAULT_VERIFY_MODEL
    try:
        result = client.structured(
            system=SYSTEM,
            prompt=_verify_prompt(items),
            model_cls=VocabVerifyResult,
            max_tokens=4000,
            max_retries=1,
            model=verify_model,
        )
    except Exception:
        return llm  # 검증 실패 시 원본 유지(fail-open)

    # ok=False 또는 valid_count!=2 인 문항만 제외 대상으로 표시
    drop = {v.key for v in result.verdicts if (not v.ok) or v.valid_count != 2}
    if not drop:
        return llm
    for s in llm.sentences:
        s.vocab_items = [it for it in s.vocab_items if f"{s.no}:{it.id}" not in drop]
    return llm
