from __future__ import annotations

from typing import Any, Annotated

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import __version__
from .config import MAX_PROMPT_LIMIT, Settings, load_settings
from .db import EventLog
from .ollama import OllamaAdapter, OllamaError
from .policy import PolicyGate, PolicyViolation


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=MAX_PROMPT_LIMIT)
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$",
    )


class GenerateResponse(BaseModel):
    model: str
    response: str
    done: bool = True


ApiKeyHeader = Annotated[str | None, Header(alias="X-Andromeda-Key")]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    settings.validate_bind_policy()

    app = FastAPI(
        title="Andromeda Local Gateway",
        version=__version__,
        description="Offline-first local policy gateway for Andromeda.",
    )
    event_log = EventLog(settings.sqlite_path, max_rows=settings.event_log_max_rows)
    ollama = OllamaAdapter(settings.ollama_base_url, settings.request_timeout_seconds)
    policy = PolicyGate(settings)

    app.state.settings = settings
    app.state.event_log = event_log
    app.state.ollama = ollama
    app.state.policy = policy

    @app.get("/health")
    async def health(
        request: Request,
        x_andromeda_key: ApiKeyHeader = None,
    ) -> JSONResponse:
        try:
            request.app.state.policy.authorize(x_andromeda_key)
        except PolicyViolation as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

        cfg: Settings = request.app.state.settings
        backend = await request.app.state.ollama.health()
        status = "ok" if backend.get("ok") else "degraded"
        request.app.state.event_log.record(
            kind="health",
            status=status,
            detail=None if backend.get("ok") else str(backend.get("detail")),
        )
        body: dict[str, Any] = {
            "status": status,
            "version": __version__,
            "default_model": cfg.default_model,
            "ollama": backend,
        }
        return JSONResponse(status_code=200 if status == "ok" else 503, content=body)

    @app.post("/api/generate", response_model=GenerateResponse)
    async def generate(
        payload: GenerateRequest,
        request: Request,
        x_andromeda_key: ApiKeyHeader = None,
    ) -> GenerateResponse:
        log: EventLog = request.app.state.event_log
        try:
            model = request.app.state.policy.validate_generate(
                prompt=payload.prompt,
                requested_model=payload.model,
                supplied_key=x_andromeda_key,
            )
        except PolicyViolation as exc:
            log.record(
                kind="generate",
                status="denied",
                model=payload.model,
                prompt_chars=len(payload.prompt),
                detail=exc.detail,
            )
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

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

        text = result["response"]
        response_model = result["model"]
        log.record(
            kind="generate",
            status="ok",
            model=response_model,
            prompt_chars=len(payload.prompt),
            response_chars=len(text),
        )
        return GenerateResponse(
            model=response_model,
            response=text,
            done=result["done"],
        )

    return app
