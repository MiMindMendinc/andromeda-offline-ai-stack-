from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8000,
    "ollama_base_url": "http://127.0.0.1:11434",
    "default_model": "llama3.2:3b",
    "request_timeout_seconds": 120,
    "sqlite_path": "andromeda-events.db",
    "allow_non_loopback_bind": False,
}


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    ollama_base_url: str
    default_model: str
    request_timeout_seconds: float
    sqlite_path: str
    allow_non_loopback_bind: bool

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "Settings":
        merged = dict(DEFAULTS)
        if data:
            merged.update({k: v for k, v in data.items() if k in DEFAULTS})
        return cls(
            host=str(merged["host"]),
            port=int(merged["port"]),
            ollama_base_url=str(merged["ollama_base_url"]).rstrip("/"),
            default_model=str(merged["default_model"]),
            request_timeout_seconds=float(merged["request_timeout_seconds"]),
            sqlite_path=str(merged["sqlite_path"]),
            allow_non_loopback_bind=bool(merged["allow_non_loopback_bind"]),
        )


def load_settings(path: str | Path | None = None) -> Settings:
    if path is None:
        return Settings.from_mapping()
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a mapping")
    return Settings.from_mapping(raw)
