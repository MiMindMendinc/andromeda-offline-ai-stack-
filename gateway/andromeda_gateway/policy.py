from __future__ import annotations

import hmac
from dataclasses import dataclass

from .config import Settings


@dataclass(frozen=True)
class PolicyViolation(ValueError):
    status_code: int
    detail: str

    def __str__(self) -> str:
        return self.detail


class PolicyGate:
    """Enforce local gateway access and resource-use policy before inference."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authorize(self, supplied_key: str | None) -> None:
        expected = self.settings.api_key
        if expected is None:
            return
        if supplied_key is None or not hmac.compare_digest(supplied_key, expected):
            raise PolicyViolation(status_code=401, detail="Invalid or missing API key")

    def validate_generate(
        self,
        *,
        prompt: str,
        requested_model: str | None,
        supplied_key: str | None,
    ) -> str:
        self.authorize(supplied_key)
        if not prompt.strip():
            raise PolicyViolation(status_code=422, detail="Prompt must contain non-whitespace text")
        if len(prompt) > self.settings.max_prompt_chars:
            raise PolicyViolation(
                status_code=413,
                detail=f"Prompt exceeds the {self.settings.max_prompt_chars}-character limit",
            )

        model = requested_model or self.settings.default_model
        if model not in self.settings.allowed_models:
            raise PolicyViolation(status_code=403, detail="Requested model is not allowed")
        return model
