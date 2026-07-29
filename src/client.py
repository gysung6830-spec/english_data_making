"""Anthropic API 래퍼: 구조화된 JSON 응답 + 검증 + 재시도.

- 6개 섹션을 각각 독립 호출로 처리하기 위한 저수준 헬퍼.
- output_config.format(json_schema) 로 JSON 형식을 강제하고,
  pydantic 으로 다시 검증하여 개수/필드 오류 시 재요청한다.
"""
from __future__ import annotations

import base64
import copy
import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

DEFAULT_MAX_TOKENS = 8000


# ---------------------------------------------------------------------------
# pydantic 모델 -> 구조화 출력용 strict JSON 스키마
# ---------------------------------------------------------------------------
def _strictify(node: Any) -> None:
    """모든 object 노드에 additionalProperties:false 와 required(전체 키)를 설정."""
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            node["additionalProperties"] = False
            node["required"] = list(node["properties"].keys())
        for v in node.values():
            _strictify(v)
    elif isinstance(node, list):
        for v in node:
            _strictify(v)


def to_strict_schema(model_cls: type[BaseModel]) -> dict:
    schema = copy.deepcopy(model_cls.model_json_schema())
    _strictify(schema)
    return schema


def output_format(model_cls: type[BaseModel]) -> dict:
    return {"format": {"type": "json_schema", "schema": to_strict_schema(model_cls)}}


_MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
         ".gif": "image/gif", ".webp": "image/webp"}


def image_block(image_path: str | Path) -> dict:
    """이미지 파일 -> base64 이미지 content 블록 (비전 입력용)."""
    p = Path(image_path)
    b64 = base64.standard_b64encode(p.read_bytes()).decode("utf-8")
    media = _MEDIA.get(p.suffix.lower(), "image/jpeg")
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}}


def build_request(
    model: str,
    system: str,
    prompt: str,
    model_cls: type[BaseModel],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    image_path: str | Path | None = None,
    cache_prefix: str | None = None,
) -> dict:
    """messages.create 및 Batch API 에 그대로 쓸 요청 파라미터.

    image_path 가 주어지면 이미지 + 텍스트를 함께 보내는 비전 요청이 된다.
    cache_prefix 가 주어지면 '지문·분석'처럼 여러 호출이 공유하는 앞부분을
    system 블록으로 올리고 프롬프트 캐싱(cache_control)을 건다. 유형별로 다른
    지시문(prompt)만 뒤에 오므로, 같은 지문의 여러 유형 호출이 앞부분을 캐시에서
    읽어 입력 비용·지연을 크게 줄인다. (Opus 최소 캐시 길이 1024토큰 미만이면
    자동으로 캐시되지 않으니 무해하다.)
    """
    if cache_prefix:
        system_param: Any = [
            {"type": "text", "text": system},
            {"type": "text", "text": cache_prefix,
             "cache_control": {"type": "ephemeral"}},
        ]
        # 지문·분석이 프롬프트에도 그대로 들어 있으면 중복되어 캐시 효과가 사라진다.
        # system 으로 올렸으니 사용자 프롬프트에서는 제거한다(지시문만 남김).
        prompt = prompt.replace(cache_prefix, "").rstrip()
    else:
        system_param = system

    if image_path is not None:
        content: Any = [image_block(image_path), {"type": "text", "text": prompt}]
    else:
        content = prompt
    return {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_param,
        "messages": [{"role": "user", "content": content}],
        "output_config": output_format(model_cls),
    }


def parse_response_text(text: str, model_cls: type[T]) -> T:
    """응답 JSON 텍스트를 pydantic 모델로 검증/파싱."""
    data = json.loads(text)
    return model_cls.model_validate(data)


def extract_text(message: Any) -> str:
    for block in message.content:
        if getattr(block, "type", None) == "text":
            return block.text
    raise ValueError("응답에 텍스트 블록이 없습니다.")


class ClaudeClient:
    """동기 처리용 래퍼."""

    def __init__(self, api_key: str, model: str):
        import anthropic  # 지연 임포트 (mock 모드에서는 불필요)

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def structured(
        self,
        system: str,
        prompt: str,
        model_cls: type[T],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_retries: int = 1,
        extra_validate=None,
        image_path: str | Path | None = None,
        cache_prefix: str | None = None,
    ) -> T:
        """구조화 JSON 을 받아 검증. 실패 시 max_retries 만큼 재요청.

        image_path 가 주어지면 이미지를 함께 보내는 비전 요청으로 동작한다.
        cache_prefix 는 여러 호출이 공유하는 앞부분(지문·분석)으로, 프롬프트 캐싱에 쓴다.
        재시도 시 지시문(prompt)만 바뀌고 cache_prefix 는 그대로라 캐시가 계속 재사용된다.
        """
        last_err: Exception | None = None
        cur_prompt = prompt
        for attempt in range(max_retries + 1):
            req = build_request(self.model, system, cur_prompt, model_cls, max_tokens,
                                image_path=image_path, cache_prefix=cache_prefix)
            message = self._client.messages.create(**req)
            try:
                text = extract_text(message)
                obj = parse_response_text(text, model_cls)
                if extra_validate:
                    extra_validate(obj)
                return obj
            except (ValidationError, ValueError, json.JSONDecodeError) as e:
                last_err = e
                cur_prompt = (
                    prompt
                    + f"\n\n[주의] 직전 응답이 조건을 위반했습니다: {e}\n"
                    "이번에는 스키마와 개수 조건을 반드시 지켜 다시 작성하세요."
                )
        raise RuntimeError(f"검증 실패(재시도 소진): {last_err}")

    # Batch API -----------------------------------------------------------
    @property
    def raw(self):
        return self._client
