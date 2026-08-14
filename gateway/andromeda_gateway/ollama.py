from __future__ import annotations

from typing import Any

import httpx


class OllamaError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OllamaAdapter:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            if response.status_code >= 400:
                return {"ok": False, "detail": f"status {response.status_code}"}
            payload = response.json()
            models = [m.get("name") for m in payload.get("models", []) if isinstance(m, dict)]
            return {"ok": True, "models": models}
        except httpx.HTTPError as exc:
            return {"ok": False, "detail": str(exc)}

    async def generate(self, *, model: str, prompt: str) -> dict[str, Any]:
        body = {"model": model, "prompt": prompt, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=body)
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc

        if response.status_code >= 400:
            raise OllamaError(
                f"Ollama returned HTTP {response.status_code}: {response.text[:300]}",
                status_code=response.status_code,
            )

        payload = response.json()
        return {
            "model": payload.get("model", model),
            "response": payload.get("response", ""),
            "done": bool(payload.get("done", True)),
            "raw": payload,
        }
