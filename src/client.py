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

DEFAULT_MAX_TOKENS = 16000
# 응답이 max_tokens 로 잘리면 재시도 시 이 상한까지 토큰 한도를 2배씩 키운다.
MAX_TOKENS_CAP = 32000


# ---------------------------------------------------------------------------
# pydantic 모델 -> 구조화 출력용 strict JSON 스키마
# ---------------------------------------------------------------------------
def _strictify(node: Any) -> None:
    """모든 object 노드에 additionalProperties:false 와 required(전체 키)를 설정.

    또한 배열의 minItems 를 0/1 로 클램프한다 — Anthropic 구조화 출력(output_config)은
    'minItems 값이 0 또는 1' 만 허용하므로, pydantic Field(min_length=N≥2)에서 나온
    minItems(예: drills 5, flow_blocks 2, explanation 3)를 1 로 낮춘다.
    (진짜 최소 개수 제약은 pydantic 파싱 단계에서 그대로 검증되고, 부족하면 재시도로 처리)
    """
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            node["additionalProperties"] = False
            node["required"] = list(node["properties"].keys())
        if "minItems" in node and isinstance(node["minItems"], int) and node["minItems"] > 1:
            node["minItems"] = 1
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
    image_path: str | Path | list | None = None,
) -> dict:
    """messages.create 및 Batch API 에 그대로 쓸 요청 파라미터.

    image_path 가 주어지면 이미지 + 텍스트를 함께 보내는 비전 요청이 된다.
    여러 장(list)을 주면 여러 이미지를 순서대로 함께 보낸다(예: PDF 여러 페이지).
    """
    if image_path is not None:
        paths = image_path if isinstance(image_path, (list, tuple)) else [image_path]
        content: Any = [image_block(p) for p in paths] + [{"type": "text", "text": prompt}]
    else:
        content = prompt
    return {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
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
        image_path: str | Path | list | None = None,
    ) -> T:
        """구조화 JSON 을 받아 검증. 실패 시 max_retries 만큼 재요청.

        image_path 가 주어지면 이미지를 함께 보내는 비전 요청으로 동작한다.
        """
        last_err: Exception | None = None
        cur_prompt = prompt
        cur_max = max_tokens
        for attempt in range(max_retries + 1):
            req = build_request(self.model, system, cur_prompt, model_cls, cur_max,
                                image_path=image_path)
            # max_tokens 가 크면 비스트리밍 요청은 SDK가 막는다(10분 초과 가능).
            # 스트리밍으로 받아 최종 메시지를 조립한다.
            with self._client.messages.stream(**req) as stream:
                message = stream.get_final_message()
            # 응답이 max_tokens 로 잘렸으면(JSON 미완성) 프롬프트가 아니라 한도가 문제.
            # 같은 한도로 재시도해봐야 또 잘리므로, 토큰 한도를 키워 다시 요청한다.
            if getattr(message, "stop_reason", None) == "max_tokens":
                last_err = ValueError(
                    f"응답이 최대 토큰({cur_max})에 걸려 잘렸습니다(지문이 길어 출력이 큼)."
                )
                if cur_max < MAX_TOKENS_CAP:
                    cur_max = min(cur_max * 2, MAX_TOKENS_CAP)
                cur_prompt = prompt  # 잘림은 내용 문제가 아니므로 프롬프트는 원본 유지
                continue
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
