from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Optional

from pydantic import BaseModel, Field

from ..models import (
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    ProviderResponseBlock,
    ProviderUsage,
)
from .base import LLMProvider


class MiniMaxProviderConfig(BaseModel):
    model: str = "MiniMax-M2.7"
    base_url: str = "https://api.minimax.io/anthropic"
    api_key_env: str = "MINIMAX_API_KEY"
    explicit_api_key: Optional[str] = None
    temperature: float = Field(default=0.1, gt=0.0, le=1.0)
    max_tokens: int = 4096
    anthropic_version: str = "2023-06-01"
    timeout_seconds: float = 180.0
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0


class MiniMaxProvider(LLMProvider):
    def __init__(self, config: MiniMaxProviderConfig) -> None:
        self.config = config

    def resolve_api_key(self) -> str:
        api_key = self.config.explicit_api_key or os.getenv(self.config.api_key_env)
        if not api_key:
            api_key = _load_env_api_key(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"MiniMax API key is required. Set {self.config.api_key_env} or pass explicit_api_key when live execution is needed."
            )
        return api_key

    def build_request(self, *, system_prompt: str, user_prompt: str, metadata: Optional[dict] = None) -> ProviderRequest:
        return ProviderRequest(
            model=self.config.model,
            system_prompt=system_prompt,
            messages=[ProviderMessage(role="user", content=user_prompt)],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            metadata=metadata or {},
        )

    def build_http_payload(self, request: ProviderRequest) -> dict:
        return {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system_prompt,
            "messages": [
                {
                    "role": message.role,
                    "content": [{"type": "text", "text": message.content}],
                }
                for message in request.messages
            ],
        }

    def serialize_http_payload(self, request: ProviderRequest) -> str:
        return json.dumps(self.build_http_payload(request), ensure_ascii=False, indent=2)

    def build_headers(self) -> dict:
        return {
            "content-type": "application/json",
            "x-api-key": self.resolve_api_key(),
            "anthropic-version": self.config.anthropic_version,
        }

    def endpoint_url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/v1/messages"

    def normalize_response(self, raw_response: dict) -> ProviderResponse:
        blocks = []
        for block in raw_response.get("content", []):
            block_type = block.get("type", "unknown")
            text = block.get("text") or block.get("thinking")
            blocks.append(ProviderResponseBlock(kind=block_type, text=text, payload=block))
        usage = raw_response.get("usage", {}) or {}
        return ProviderResponse(
            model=raw_response.get("model", self.config.model),
            blocks=blocks,
            raw_response=raw_response,
            usage=ProviderUsage(
                input_tokens=int(usage.get("input_tokens", 0) or 0),
                output_tokens=int(usage.get("output_tokens", 0) or 0),
                cache_creation_input_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
                cache_read_input_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
            ),
            stop_reason=raw_response.get("stop_reason"),
            metadata=raw_response.get("metadata", {}) or {},
        )

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        payload = json.dumps(self.build_http_payload(request)).encode("utf-8")
        http_request = Request(
            self.endpoint_url(),
            data=payload,
            headers=self.build_headers(),
            method="POST",
        )
        attempts = self.config.max_retries + 1
        last_error: Optional[Exception] = None
        for attempt in range(attempts):
            try:
                with urlopen(http_request, timeout=self.config.timeout_seconds) as response:
                    raw = json.loads(response.read().decode("utf-8"))
                return self.normalize_response(raw)
            except HTTPError as exc:
                body = _read_http_error_body(exc)
                last_error = RuntimeError(f"MiniMax HTTP error {exc.code}: {body}")
                if not _is_retryable_http_error(exc) or attempt >= self.config.max_retries:
                    raise last_error from exc
                time.sleep(_retry_delay_for_http_error(exc, self.config.retry_backoff_seconds, attempt))
            except (URLError, socket.timeout, TimeoutError) as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                time.sleep(self.config.retry_backoff_seconds * (attempt + 1))
        raise RuntimeError(f"MiniMax network error after {attempts} attempt(s): {last_error}") from last_error


def _load_env_api_key(env_name: str) -> Optional[str]:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() != env_name:
            continue
        resolved = value.strip().strip("'").strip('"')
        if resolved:
            os.environ.setdefault(env_name, resolved)
            return resolved
    return None


def _is_retryable_http_error(error: HTTPError) -> bool:
    return error.code in {408, 409, 425, 429, 500, 502, 503, 504}


def _retry_delay_for_http_error(error: HTTPError, backoff_seconds: float, attempt: int) -> float:
    retry_after = error.headers.get("Retry-After") if error.headers else None
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass
    return backoff_seconds * (attempt + 1)


def _read_http_error_body(error: HTTPError) -> str:
    try:
        body = error.read()
    except Exception:
        body = b""
    if isinstance(body, bytes):
        decoded = body.decode("utf-8", errors="replace").strip()
        if decoded:
            return decoded
    return error.reason if getattr(error, "reason", None) else ""
