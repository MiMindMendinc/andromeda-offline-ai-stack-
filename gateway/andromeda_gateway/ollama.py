from __future__ import annotations

from typing import Any

import httpx


class OllamaError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _decode_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise OllamaError("Ollama returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise OllamaError("Ollama returned an invalid response object")
    return payload


class OllamaAdapter:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            if response.status_code >= 400:
                return {"ok": False, "detail": f"Ollama returned HTTP {response.status_code}"}
            payload = _decode_object(response)
            raw_models = payload.get("models", [])
            if not isinstance(raw_models, list):
                return {"ok": False, "detail": "Ollama returned an invalid models list"}
            models = [
                model["name"]
                for model in raw_models
                if isinstance(model, dict) and isinstance(model.get("name"), str)
            ]
            return {"ok": True, "models": models}
        except (httpx.HTTPError, OllamaError) as exc:
            return {"ok": False, "detail": str(exc)}

    async def generate(self, *, model: str, prompt: str) -> dict[str, Any]:
        body = {"model": model, "prompt": prompt, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=body)
        except httpx.HTTPError as exc:
            raise OllamaError("Ollama request failed") from exc

        if response.status_code >= 400:
            raise OllamaError(
                f"Ollama returned HTTP {response.status_code}",
                status_code=response.status_code,
            )

        payload = _decode_object(response)
        response_model = payload.get("model", model)
        response_text = payload.get("response")
        done = payload.get("done", True)
        if not isinstance(response_model, str) or not response_model:
            raise OllamaError("Ollama response is missing a valid model")
        if not isinstance(response_text, str):
            raise OllamaError("Ollama response is missing text")
        if type(done) is not bool:
            raise OllamaError("Ollama response contains an invalid done flag")
        return {"model": response_model, "response": response_text, "done": done}
