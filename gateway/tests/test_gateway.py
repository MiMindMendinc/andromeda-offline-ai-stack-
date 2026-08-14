from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from andromeda_gateway.config import Settings
from andromeda_gateway.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        host="127.0.0.1",
        port=8000,
        ollama_base_url="http://127.0.0.1:11434",
        default_model="llama3.2:3b",
        request_timeout_seconds=5.0,
        sqlite_path=str(tmp_path / "events.db"),
        allow_non_loopback_bind=False,
    )


@pytest.fixture
def client(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    async def fake_health() -> dict:
        return {"ok": True, "models": ["llama3.2:3b"]}

    async def fake_generate(*, model: str, prompt: str) -> dict:
        return {"model": model, "response": f"echo:{prompt}", "done": True, "raw": {}}

    app = create_app(settings)
    monkeypatch.setattr(app.state.ollama, "health", fake_health)
    monkeypatch.setattr(app.state.ollama, "generate", fake_generate)
    return TestClient(app)


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["default_model"] == "llama3.2:3b"
    assert body["ollama"]["ok"] is True


def test_generate_ok(client: TestClient, settings: Settings) -> None:
    response = client.post("/api/generate", json={"prompt": "hello farm"})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "llama3.2:3b"
    assert body["response"] == "echo:hello farm"
    assert body["done"] is True

    events = client.app.state.event_log.recent(limit=5)
    kinds = {event["kind"] for event in events}
    assert "generate" in kinds


def test_generate_requires_prompt(client: TestClient) -> None:
    response = client.post("/api/generate", json={"prompt": ""})
    assert response.status_code == 422


def test_refuses_non_loopback_bind_by_default() -> None:
    bad = Settings(
        host="0.0.0.0",
        port=8000,
        ollama_base_url="http://127.0.0.1:11434",
        default_model="llama3.2:3b",
        request_timeout_seconds=5.0,
        sqlite_path=":memory:",
        allow_non_loopback_bind=False,
    )
    with pytest.raises(ValueError, match="non-loopback"):
        create_app(bad)
