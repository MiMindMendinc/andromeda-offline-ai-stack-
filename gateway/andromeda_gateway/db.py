from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    model TEXT,
    prompt_chars INTEGER,
    response_chars INTEGER,
    status TEXT NOT NULL,
    detail TEXT
);
"""


class EventLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def record(
        self,
        *,
        kind: str,
        status: str,
        model: str | None = None,
        prompt_chars: int | None = None,
        response_chars: int | None = None,
        detail: str | None = None,
    ) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    created_at, kind, model, prompt_chars, response_chars, status, detail
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (created_at, kind, model, prompt_chars, response_chars, status, detail),
            )

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
