#!/usr/bin/env python3
"""Run the Andromeda local gateway with uvicorn."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from andromeda_gateway.config import load_settings
from andromeda_gateway.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Andromeda local FastAPI gateway")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to YAML config (defaults to built-in localhost settings)",
    )
    args = parser.parse_args()
    settings = load_settings(args.config)
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
