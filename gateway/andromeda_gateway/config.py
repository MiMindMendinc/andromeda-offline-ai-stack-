from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


MAX_PROMPT_LIMIT = 1_000_000
API_KEY_ENV = "ANDROMEDA_API_KEY"

DEFAULTS: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8000,
    "ollama_base_url": "http://127.0.0.1:11434",
    "default_model": "llama3.2:3b",
    "allowed_models": None,
    "request_timeout_seconds": 120.0,
    "sqlite_path": "andromeda-events.db",
    "event_log_max_rows": 10_000,
    "max_prompt_chars": 16_000,
    "allow_non_loopback_bind": False,
    "api_key": None,
}


def is_loopback_host(host: str) -> bool:
    if host.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _require_bool(name: str, value: Any) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _require_int(name: str, value: Any, *, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _require_number(name: str, value: Any, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    number = float(value)
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return number


def _require_nonempty_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    ollama_base_url: str
    default_model: str
    allowed_models: tuple[str, ...]
    request_timeout_seconds: float
    sqlite_path: str
    event_log_max_rows: int
    max_prompt_chars: int
    allow_non_loopback_bind: bool
    api_key: str | None

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "Settings":
        supplied = data or {}
        unknown = sorted(set(supplied) - set(DEFAULTS))
        if unknown:
            raise ValueError(f"Unknown config field(s): {', '.join(unknown)}")

        merged = dict(DEFAULTS)
        merged.update(supplied)

        host = _require_nonempty_string("host", merged["host"])
        port = _require_int("port", merged["port"], minimum=1, maximum=65_535)
        base_url = _require_nonempty_string("ollama_base_url", merged["ollama_base_url"]).rstrip("/")
        parsed_url = urlparse(base_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
            raise ValueError("ollama_base_url must be an absolute http(s) URL")

        default_model = _require_nonempty_string("default_model", merged["default_model"])
        raw_models = merged["allowed_models"]
        if raw_models is None:
            allowed_models = (default_model,)
        else:
            if not isinstance(raw_models, list) or not raw_models:
                raise ValueError("allowed_models must be a non-empty list of model names")
            allowed_models = tuple(
                _require_nonempty_string("allowed_models entry", model) for model in raw_models
            )
            if len(set(allowed_models)) != len(allowed_models):
                raise ValueError("allowed_models must not contain duplicates")
            if default_model not in allowed_models:
                raise ValueError("default_model must be present in allowed_models")

        api_key_value = merged["api_key"]
        if api_key_value is not None:
            api_key_value = _require_nonempty_string("api_key", api_key_value)
            if len(api_key_value) < 24:
                raise ValueError("api_key must contain at least 24 characters")

        settings = cls(
            host=host,
            port=port,
            ollama_base_url=base_url,
            default_model=default_model,
            allowed_models=allowed_models,
            request_timeout_seconds=_require_number(
                "request_timeout_seconds",
                merged["request_timeout_seconds"],
                minimum=0.1,
                maximum=3_600.0,
            ),
            sqlite_path=_require_nonempty_string("sqlite_path", merged["sqlite_path"]),
            event_log_max_rows=_require_int(
                "event_log_max_rows", merged["event_log_max_rows"], minimum=1, maximum=10_000_000
            ),
            max_prompt_chars=_require_int(
                "max_prompt_chars", merged["max_prompt_chars"], minimum=1, maximum=MAX_PROMPT_LIMIT
            ),
            allow_non_loopback_bind=_require_bool(
                "allow_non_loopback_bind", merged["allow_non_loopback_bind"]
            ),
            api_key=api_key_value,
        )
        settings.validate_bind_policy()
        return settings

    def validate_bind_policy(self) -> None:
        loopback = is_loopback_host(self.host)
        if not loopback and not self.allow_non_loopback_bind:
            raise ValueError(
                "Refusing non-loopback bind. Set allow_non_loopback_bind: true only on trusted LANs."
            )
        if not loopback and not self.api_key:
            raise ValueError("A 24+ character api_key is required for non-loopback binds")


def load_settings(path: str | Path | None = None) -> Settings:
    raw: dict[str, Any] = {}
    if path is not None:
        config_path = Path(path)
        if not config_path.is_file():
            raise FileNotFoundError(f"Config not found: {config_path}")
        with config_path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError("Config root must be a mapping")
        raw.update(loaded)

    env_api_key = os.environ.get(API_KEY_ENV)
    if env_api_key:
        raw["api_key"] = env_api_key
    return Settings.from_mapping(raw)
