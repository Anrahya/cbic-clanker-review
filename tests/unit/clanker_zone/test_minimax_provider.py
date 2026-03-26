import os
import socket
from pathlib import Path
from urllib.error import HTTPError

import pytest

from clanker_zone.provider.minimax import MiniMaxProvider, MiniMaxProviderConfig


def test_minimax_provider_builds_request_without_live_key():
    provider = MiniMaxProvider(MiniMaxProviderConfig())
    request = provider.build_request(
        system_prompt="System prefix",
        user_prompt="Review this dossier",
        metadata={"task": "demo"},
    )
    payload = provider.build_http_payload(request)
    assert payload["model"] == "MiniMax-M2.7"
    assert payload["system"] == "System prefix"
    assert payload["messages"][0]["content"][0]["text"] == "Review this dossier"


def test_minimax_provider_requires_key_only_for_live_resolution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    provider = MiniMaxProvider(MiniMaxProviderConfig())
    with pytest.raises(RuntimeError):
        provider.resolve_api_key()


def test_minimax_provider_retries_transient_timeout(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "demo")
    provider = MiniMaxProvider(
        MiniMaxProviderConfig(
            timeout_seconds=0.1,
            max_retries=1,
            retry_backoff_seconds=0.0,
        )
    )

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"model":"MiniMax-M2.7","content":[{"type":"text","text":"ok"}]}'

    calls = {"count": 0}

    def fake_urlopen(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise socket.timeout("timed out")
        return DummyResponse()

    monkeypatch.setattr("clanker_zone.provider.minimax.urlopen", fake_urlopen)
    response = provider.invoke(
        provider.build_request(system_prompt="system", user_prompt="user")
    )

    assert calls["count"] == 2
    assert response.blocks[0].text == "ok"


def test_minimax_provider_loads_api_key_from_local_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    (tmp_path / ".env").write_text("MINIMAX_API_KEY=from-dotenv\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    provider = MiniMaxProvider(MiniMaxProviderConfig())

    assert provider.resolve_api_key() == "from-dotenv"


def test_minimax_provider_retries_transient_http_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "demo")
    provider = MiniMaxProvider(
        MiniMaxProviderConfig(
            timeout_seconds=0.1,
            max_retries=1,
            retry_backoff_seconds=0.0,
        )
    )

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"model":"MiniMax-M2.7","content":[{"type":"text","text":"ok"}]}'

    calls = {"count": 0}

    def fake_urlopen(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise HTTPError(
                url="https://api.minimax.io/anthropic/v1/messages",
                code=429,
                msg="rate limited",
                hdrs={"Retry-After": "0"},
                fp=None,
            )
        return DummyResponse()

    monkeypatch.setattr("clanker_zone.provider.minimax.urlopen", fake_urlopen)
    response = provider.invoke(
        provider.build_request(system_prompt="system", user_prompt="user")
    )

    assert calls["count"] == 2
    assert response.blocks[0].text == "ok"
