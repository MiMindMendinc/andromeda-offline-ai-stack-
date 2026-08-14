from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from andromeda_gateway.config import Settings
from andromeda_gateway.main import create_app
from andromeda_gateway.ollama import OllamaError


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings.from_mapping(
        {
            "sqlite_path": str(tmp_path / "events.db"),
            "max_prompt_chars": 32,
        }
    )


@pytest.fixture
def app(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    async def fake_health() -> dict:
        return {"ok": True, "models": ["llama3.2:3b"]}

    async def fake_generate(*, model: str, prompt: str) -> dict:
        return {"model": model, "response": f"echo:{prompt}", "done": True}

    app = create_app(settings)
    monkeypatch.setattr(app.state.ollama, "health", fake_health)
    monkeypatch.setattr(app.state.ollama, "generate", fake_generate)
    return app


def request(app: FastAPI, method: str, path: str, **kwargs: object) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_health_ok(app: FastAPI) -> None:
    response = request(app, "GET", "/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["default_model"] == "llama3.2:3b"
    assert body["ollama"]["ok"] is True


def test_health_degraded_is_not_ready(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    async def degraded() -> dict:
        return {"ok": False, "detail": "offline"}

    monkeypatch.setattr(app.state.ollama, "health", degraded)
    response = request(app, "GET", "/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_generate_ok(app: FastAPI) -> None:
    response = request(app, "POST", "/api/generate", json={"prompt": "hello farm"})
    assert response.status_code == 200
    assert response.json() == {
        "model": "llama3.2:3b",
        "response": "echo:hello farm",
        "done": True,
    }
    events = app.state.event_log.recent(limit=5)
    assert "generate" in {event["kind"] for event in events}


@pytest.mark.parametrize("prompt", ["", "   "])
def test_generate_requires_meaningful_prompt(app: FastAPI, prompt: str) -> None:
    response = request(app, "POST", "/api/generate", json={"prompt": prompt})
    assert response.status_code == 422


def test_generate_enforces_configured_prompt_limit(app: FastAPI) -> None:
    response = request(app, "POST", "/api/generate", json={"prompt": "x" * 33})
    assert response.status_code == 413


def test_generate_rejects_unapproved_model(app: FastAPI) -> None:
    response = request(
        app,
        "POST",
        "/api/generate",
        json={"prompt": "hello", "model": "unapproved:latest"},
    )
    assert response.status_code == 403


def test_generate_maps_ollama_error_to_502(
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_generate(*, model: str, prompt: str) -> dict:
        raise OllamaError("Ollama request failed")

    monkeypatch.setattr(app.state.ollama, "generate", fail_generate)
    response = request(app, "POST", "/api/generate", json={"prompt": "hello"})
    assert response.status_code == 502


def test_configured_api_key_is_required(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key = "a-strong-local-key-1234567890"
    app = create_app(
        Settings.from_mapping(
            {
                "sqlite_path": str(tmp_path / "events.db"),
                "api_key": key,
            }
        )
    )

    async def fake_health() -> dict:
        return {"ok": True, "models": []}

    monkeypatch.setattr(app.state.ollama, "health", fake_health)
    assert request(app, "GET", "/health").status_code == 401
    assert request(
        app,
        "GET",
        "/health",
        headers={"X-Andromeda-Key": key},
    ).status_code == 200


def test_import_has_no_database_side_effect(tmp_path: Path) -> None:
    gateway_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(gateway_root)
    subprocess.run(
        [sys.executable, "-c", "import andromeda_gateway.main"],
        cwd=tmp_path,
        env=env,
        check=True,
    )
    assert not (tmp_path / "andromeda-events.db").exists()
