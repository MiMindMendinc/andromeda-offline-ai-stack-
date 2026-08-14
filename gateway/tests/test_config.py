from __future__ import annotations

import pytest

from andromeda_gateway.config import Settings


def test_rejects_string_boolean_instead_of_bypassing_bind_guard() -> None:
    with pytest.raises(ValueError, match="allow_non_loopback_bind must be a boolean"):
        Settings.from_mapping(
            {
                "host": "0.0.0.0",
                "allow_non_loopback_bind": "false",
            }
        )


def test_non_loopback_bind_requires_explicit_flag_and_api_key() -> None:
    with pytest.raises(ValueError, match="Refusing non-loopback"):
        Settings.from_mapping({"host": "0.0.0.0"})

    with pytest.raises(ValueError, match="api_key"):
        Settings.from_mapping(
            {
                "host": "0.0.0.0",
                "allow_non_loopback_bind": True,
            }
        )

    settings = Settings.from_mapping(
        {
            "host": "0.0.0.0",
            "allow_non_loopback_bind": True,
            "api_key": "a-strong-local-key-1234567890",
        }
    )
    assert settings.host == "0.0.0.0"


def test_rejects_unknown_fields_and_invalid_ranges() -> None:
    with pytest.raises(ValueError, match="Unknown config"):
        Settings.from_mapping({"typo_port": 9000})
    with pytest.raises(ValueError, match="port"):
        Settings.from_mapping({"port": 70_000})
    with pytest.raises(ValueError, match="request_timeout_seconds"):
        Settings.from_mapping({"request_timeout_seconds": 0})


def test_default_model_must_be_allowed() -> None:
    with pytest.raises(ValueError, match="default_model"):
        Settings.from_mapping(
            {
                "default_model": "llama3.2:3b",
                "allowed_models": ["qwen3:4b"],
            }
        )
