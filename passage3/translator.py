"""해석 없는 문장만 Claude API로 번역(선택).

ANTHROPIC_API_KEY 가 없으면 아무 것도 하지 않고 그대로 반환한다(프로그램은
멈추지 않는다). 한줄영어 형식은 해석을 쓰지 않으므로 이 단계와 무관하다.
"""
from __future__ import annotations

import json
import os
from typing import List

try:
    from .parser import Passage, Sentence
except ImportError:
    from parser import Passage, Sentence

DEFAULT_MODEL = "claude-sonnet-5"

_SYSTEM = (
    "You are a professional Korean-English translator for a study handout. "
    "Translate each English sentence into natural, accurate Korean suitable "
    "for Korean high-school students. Keep it faithful; do not add commentary. "
    "Return ONLY a JSON object mapping the given id (string) to its Korean "
    "translation string."
)


def _collect_missing(passages: List[Passage]) -> List[tuple]:
    """(passage_index, sentence_index, en) 목록 — ko 가 비고 en 이 있는 것만."""
    missing = []
    for pi, p in enumerate(passages):
        for si, s in enumerate(p.sentences):
            if s.en and not s.ko.strip():
                missing.append((pi, si, s.en))
    return missing


def translate_missing(passages: List[Passage], model: str = DEFAULT_MODEL) -> List[Passage]:
    """해석 없는 문장만 골라 번역해 채운다."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    missing = _collect_missing(passages)
    if not api_key or not missing:
        return passages

    try:
        import anthropic
    except ImportError:
        return passages

    client = anthropic.Anthropic(api_key=api_key)

    # id → en 매핑 만들어 한 번(또는 배치)에 요청
    items = {str(i): en for i, (_, _, en) in enumerate(missing)}

    # 너무 많으면 분할 (한 요청당 최대 40문장)
    ids = list(items.keys())
    result: dict = {}
    BATCH = 40
    for start in range(0, len(ids), BATCH):
        batch_ids = ids[start:start + BATCH]
        payload = {k: items[k] for k in batch_ids}
        user_msg = (
            "Translate these English sentences to Korean. "
            "Return ONLY JSON {id: korean}.\n\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=4096,
                system=_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = "".join(
                block.text for block in resp.content if getattr(block, "type", "") == "text"
            )
            parsed = _extract_json(text)
            if isinstance(parsed, dict):
                result.update(parsed)
        except Exception:
            # 한 배치 실패해도 나머지는 진행
            continue

    # 결과 반영
    for i, (pi, si, _en) in enumerate(missing):
        ko = result.get(str(i))
        if ko:
            passages[pi].sentences[si].ko = str(ko).strip()

    return passages


def _extract_json(text: str):
    """모델 응답 문자열에서 JSON 객체를 추출."""
    text = text.strip()
    # 코드펜스 제거
    if text.startswith("```"):
        text = text.strip("`")
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 중괄호 구간만 잘라서 재시도
    a = text.find("{")
    b = text.rfind("}")
    if a != -1 and b != -1 and b > a:
        try:
            return json.loads(text[a:b + 1])
        except json.JSONDecodeError:
            return None
    return None
