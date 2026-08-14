from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from . import __version__
from .config import Settings, load_settings
from .db import EventLog
from .ollama import OllamaAdapter, OllamaError


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str | None = None


class GenerateResponse(BaseModel):
    model: str
    response: str
    done: bool = True


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    if not settings.allow_non_loopback_bind and settings.host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError(
            "Refusing non-loopback bind. Set allow_non_loopback_bind: true only on trusted LANs."
        )

    app = FastAPI(
        title="Andromeda Local Gateway",
        version=__version__,
        description="Offline-first local policy gateway for Andromeda.",
    )
    event_log = EventLog(settings.sqlite_path)
    ollama = OllamaAdapter(settings.ollama_base_url, settings.request_timeout_seconds)

    app.state.settings = settings
    app.state.event_log = event_log
    app.state.ollama = ollama

    @app.get("/health")
    async def health(request: Request) -> dict[str, Any]:
        cfg: Settings = request.app.state.settings
        backend = await request.app.state.ollama.health()
        status = "ok" if backend.get("ok") else "degraded"
        request.app.state.event_log.record(
            kind="health",
            status=status,
            detail=None if backend.get("ok") else str(backend.get("detail")),
        )
        return {
            "status": status,
            "version": __version__,
            "default_model": cfg.default_model,
            "ollama": backend,
        }

    @app.post("/api/generate", response_model=GenerateResponse)
    async def generate(payload: GenerateRequest, request: Request) -> GenerateResponse:
        cfg: Settings = request.app.state.settings
        model = payload.model or cfg.default_model
        log: EventLog = request.app.state.event_log
        try:
            result = await request.app.state.ollama.generate(model=model, prompt=payload.prompt)
        except OllamaError as exc:
            log.record(
                kind="generate",
                status="error",
                model=model,
                prompt_chars=len(payload.prompt),
                detail=str(exc),
            )
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        text = str(result.get("response", ""))
        log.record(
            kind="generate",
            status="ok",
            model=result.get("model", model),
            prompt_chars=len(payload.prompt),
            response_chars=len(text),
        )
        return GenerateResponse(
            model=str(result.get("model", model)),
            response=text,
            done=bool(result.get("done", True)),
        )

    return app


app = create_app()
