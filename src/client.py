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
# 출력이 잘릴 때 자동으로 키우는 상한 (모델의 최대 출력 토큰 범위 내 안전값)
MAX_OUTPUT_TOKENS = 32000


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
) -> dict:
    """messages.create 및 Batch API 에 그대로 쓸 요청 파라미터.

    image_path 가 주어지면 이미지 + 텍스트를 함께 보내는 비전 요청이 된다.
    """
    if image_path is not None:
        content: Any = [image_block(image_path), {"type": "text", "text": prompt}]
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

    def _stream_message(self, req: dict):
        """스트리밍으로 최종 메시지를 받는다(긴 요청 대응). stream 이 없으면 create 로 대체.

        Anthropic SDK 는 max_tokens 가 커 응답이 10분을 넘길 수 있으면 비스트리밍 요청을
        거부한다(스트리밍 필수). messages.stream 컨텍스트로 끝까지 모아 최종 Message 를 반환한다.
        """
        msgs = self._client.messages
        if hasattr(msgs, "stream"):
            with msgs.stream(**req) as stream:
                return stream.get_final_message()
        return msgs.create(**req)   # 목/구버전 대체 경로

    def structured(
        self,
        system: str,
        prompt: str,
        model_cls: type[T],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_retries: int = 1,
        extra_validate=None,
        image_path: str | Path | None = None,
        model: str | None = None,
    ) -> T:
        """구조화 JSON 을 받아 검증. 실패 시 max_retries 만큼 재요청.

        image_path 가 주어지면 이미지를 함께 보내는 비전 요청으로 동작한다.
        model 을 주면 해당 호출만 다른 모델로 처리한다(예: 검증 패스는 저비용 Haiku).
        """
        use_model = model or self.model
        last_err: Exception | None = None
        cur_prompt = prompt
        cur_max = max_tokens
        attempt = 0
        # 출력이 잘려(max_tokens) 재시도할 때는 한도를 키우므로, 그런 재시도는 소진 횟수에서 제외해
        #   '길이 부족'과 '스키마 위반'을 각각 충분히 재시도하게 한다.
        truncation_retries = 0
        while attempt <= max_retries:
            req = build_request(use_model, system, cur_prompt, model_cls, cur_max,
                                image_path=image_path)
            # 스트리밍으로 받는다: max_tokens 가 커 응답이 10분을 넘길 수 있으면 SDK 가 비스트리밍
            #   요청을 거부하므로(긴 요청은 스트리밍 필수), stream 으로 최종 메시지를 모은다.
            message = self._stream_message(req)
            truncated = getattr(message, "stop_reason", None) == "max_tokens"
            try:
                text = extract_text(message)
                obj = parse_response_text(text, model_cls)
                if extra_validate:
                    extra_validate(obj)
                return obj
            except (ValidationError, ValueError, json.JSONDecodeError) as e:
                last_err = e
                if truncated and cur_max < MAX_OUTPUT_TOKENS and truncation_retries < 4:
                    # 응답이 잘렸다 → 토큰 한도를 키워 다시 시도(이 재시도는 소진에서 제외)
                    cur_max = min(int(cur_max * 1.7) + 1, MAX_OUTPUT_TOKENS)
                    truncation_retries += 1
                    cur_prompt = (
                        prompt
                        + "\n\n[주의] 직전 출력이 도중에 잘렸습니다. 같은 내용을 '더 간결하게'(불필요한 "
                        "군더더기 없이) 만들되, 반드시 '완결된 JSON'으로 끝까지 닫아서 응답하세요."
                    )
                    continue
                attempt += 1
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
