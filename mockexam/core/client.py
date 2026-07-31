"""Anthropic API 래퍼: 구조화된 JSON 응답 + 검증 + 재시도.

- 문항 생성 시 유형별로 구조화 JSON 을 강제해 받기 위한 저수준 헬퍼.
- output_config.format(json_schema) 로 JSON 형식을 강제하고,
  pydantic 으로 다시 검증하여 스키마/개수 오류 시 재요청한다.
"""
from __future__ import annotations

import base64
import copy
import json
import re
import time
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

DEFAULT_MAX_TOKENS = 8000


# ---------------------------------------------------------------------------
# pydantic 모델 -> 구조화 출력용 strict JSON 스키마
# ---------------------------------------------------------------------------
# Anthropic strict JSON 스키마가 지원하지 않는 검증 키워드(개수·범위·길이 등).
# 이런 제약은 스키마에서 제거하고, 값 검증은 pydantic field_validator 로 대신한다.
_UNSUPPORTED_KEYS = (
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "minLength", "maxLength", "minItems", "maxItems", "minProperties", "maxProperties",
    "default", "title", "examples",   # Anthropic strict 가 거부(특히 default → 서술형 실패 원인)
)


def _strictify(node: Any) -> None:
    """object 노드에 additionalProperties:false·required 설정 + 미지원 키워드 제거.

    (Anthropic strict JSON 스키마는 minimum/maximum/minItems/minLength 등 제약을
     지원하지 않는다. 개수·범위 검증은 pydantic field_validator 로 처리한다.)
    """
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            node["additionalProperties"] = False
            node["required"] = list(node["properties"].keys())
        # minItems/maxItems 는 0·1 이면 허용, 그 외 및 나머지 제약은 제거
        for key in _UNSUPPORTED_KEYS:
            if key in ("minItems", "maxItems") and node.get(key) in (0, 1):
                continue
            node.pop(key, None)
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


def document_block(pdf_path: str | Path) -> dict:
    """PDF 파일 -> base64 document content 블록 (Claude 네이티브 PDF 비전)."""
    p = Path(pdf_path)
    b64 = base64.standard_b64encode(p.read_bytes()).decode("utf-8")
    return {"type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}


def media_block(path: str | Path) -> dict:
    """확장자로 PDF(document)·이미지(image) 블록을 자동 선택."""
    return document_block(path) if Path(path).suffix.lower() == ".pdf" else image_block(path)


def _field_type(spec: dict) -> str:
    t = spec.get("type")
    if t == "array":
        it = (spec.get("items") or {}).get("type", "string")
        return f"{it} 배열(예: [..])"
    return {"string": "문자열", "integer": "정수", "boolean": "true/false",
            "number": "숫자"}.get(t, t or "값")


def json_instructions(model_cls: type[BaseModel]) -> str:
    """모델 필드로부터 '이 JSON 형식으로만 답하라'는 프롬프트 지시를 만든다.

    strict output_config 대신 프롬프트로 형식을 안내 → 서버 스키마 거부(400) 회피.
    """
    props = model_cls.model_json_schema().get("properties", {})
    lines = []
    for name, spec in props.items():
        desc = spec.get("description", "")
        lines.append(f'  "{name}": <{_field_type(spec)}>'
                     + (f"   // {desc}" if desc else ""))
    body = ",\n".join(lines)
    return ("반드시 아래 형식의 JSON 객체 '하나만' 출력하라. 마크다운/설명/코드펜스 없이 "
            "순수 JSON 만:\n{\n" + body + "\n}")


def build_request(
    model: str,
    system: str,
    prompt: str,
    model_cls: type[BaseModel],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    image_path: str | Path | None = None,
) -> dict:
    """messages.create 요청 파라미터. 형식은 프롬프트로 안내(구조화 출력 미사용)."""
    full = f"{prompt}\n\n{json_instructions(model_cls)}"
    if image_path is not None:
        # PDF(document)·이미지(image) 자동 선택
        content: Any = [media_block(image_path), {"type": "text", "text": full}]
    else:
        content = full
    return {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": content}],
    }


def parse_response_text(text: str, model_cls: type[T]) -> T:
    """응답 텍스트에서 JSON 을 추출·파싱해 pydantic 모델로 검증(느슨한 파싱)."""
    return model_cls.model_validate(_extract_json(text))


def _extract_json(text: str) -> Any:
    """코드펜스/앞뒤 설명이 섞여 있어도 JSON 객체를 뽑아낸다."""
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(.+?)```", s, re.S)
    if m:
        s = m.group(1).strip()
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start:end + 1]
    return json.loads(s)


def extract_text(message: Any) -> str:
    """응답의 모든 text 블록을 이어붙여 반환(부분/다중 블록도 견고하게 처리)."""
    parts = [b.text for b in getattr(message, "content", [])
             if getattr(b, "type", None) == "text" and getattr(b, "text", "")]
    if parts:
        return "\n".join(parts)
    stop = getattr(message, "stop_reason", None)
    raise ValueError(f"응답에 텍스트 블록이 없습니다(stop_reason={stop}).")


# 일시적(재시도 가능) 오류로 볼 HTTP 상태 코드
_RETRY_STATUS = {408, 409, 429, 500, 502, 503, 529}
_RETRY_NAMES = {"RateLimitError", "InternalServerError", "APIConnectionError",
                "APITimeoutError", "OverloadedError", "ServiceUnavailableError",
                "APIConnectionTimeoutError"}


def _is_retryable(exc: Exception) -> bool:
    """rate limit(429)·과부하(529)·5xx·연결 오류면 재시도 대상."""
    status = getattr(exc, "status_code", None)
    if status in _RETRY_STATUS:
        return True
    return type(exc).__name__ in _RETRY_NAMES


def create_with_retry(client: Any, req: dict, max_attempts: int = 5,
                      base_delay: float = 2.0):
    """messages.create 를 지수 백오프로 재시도(2s·4s·8s·16s).

    rate limit/과부하/일시 오류에만 재시도하고, 그 외 오류는 즉시 전파한다.
    """
    last: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return client.messages.create(**req)
        except Exception as e:  # noqa: BLE001 - 상태코드로 재시도 여부 판단
            if not _is_retryable(e) or attempt == max_attempts - 1:
                raise
            last = e
            time.sleep(base_delay * (2 ** attempt))
    raise last  # 도달하지 않음


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
    ) -> T:
        """구조화 JSON 을 받아 검증. 실패 시 max_retries 만큼 재요청.

        image_path 가 주어지면 이미지를 함께 보내는 비전 요청으로 동작한다.
        """
        last_err: Exception | None = None
        cur_prompt = prompt
        for attempt in range(max_retries + 1):
            req = build_request(self.model, system, cur_prompt, model_cls, max_tokens,
                                image_path=image_path)
            message = create_with_retry(self._client, req)  # 429/529 등 백오프 재시도
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
