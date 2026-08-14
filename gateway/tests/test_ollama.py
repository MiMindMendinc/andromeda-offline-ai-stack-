from __future__ import annotations

import asyncio

import httpx
import pytest

from andromeda_gateway.ollama import OllamaAdapter, OllamaError


class FakeClient:
    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str) -> httpx.Response:
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response

    async def post(self, url: str, json: dict) -> httpx.Response:
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response


def test_health_handles_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient(httpx.Response(200, text="not-json"))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)
    result = asyncio.run(OllamaAdapter("http://127.0.0.1:11434", 5).health())
    assert result == {"ok": False, "detail": "Ollama returned invalid JSON"}


def test_generate_sanitizes_transport_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("POST", "http://127.0.0.1:11434/api/generate")
    fake = FakeClient(error=httpx.ReadTimeout("private upstream detail", request=request))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)
    with pytest.raises(OllamaError, match="^Ollama request failed$"):
        asyncio.run(
            OllamaAdapter("http://127.0.0.1:11434", 5).generate(
                model="llama3.2:3b",
                prompt="hello",
            )
        )


def test_generate_rejects_invalid_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient(httpx.Response(200, json={"model": "llama3.2:3b", "done": True}))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)
    with pytest.raises(OllamaError, match="missing text"):
        asyncio.run(
            OllamaAdapter("http://127.0.0.1:11434", 5).generate(
                model="llama3.2:3b",
                prompt="hello",
            )
        )
