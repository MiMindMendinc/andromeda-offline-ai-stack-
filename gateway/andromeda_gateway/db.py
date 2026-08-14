from __future__ import annotations

import sqlite3
import threading
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
    def __init__(self, path: str | Path, *, max_rows: int = 10_000) -> None:
        if max_rows < 1:
            raise ValueError("max_rows must be positive")
        self.max_rows = max_rows
        self._lock = threading.RLock()
        self._memory = str(path) == ":memory:"
        self.path = None if self._memory else Path(path).expanduser()
        self._memory_connection: sqlite3.Connection | None = None

        if self._memory:
            self._memory_connection = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            assert self.path is not None
            self.path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            if not self._memory:
                conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)

        if self.path is not None:
            try:
                self.path.chmod(0o600)
            except OSError:
                pass

    def _new_file_connection(self) -> sqlite3.Connection:
        assert self.path is not None
        conn = sqlite3.connect(self.path, timeout=5.0, check_same_thread=False)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = self._memory_connection if self._memory else self._new_file_connection()
            assert conn is not None
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                if not self._memory:
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
            conn.execute(
                "DELETE FROM events WHERE id <= (SELECT COALESCE(MAX(id), 0) FROM events) - ?",
                (self.max_rows,),
            )

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, self.max_rows))
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [dict(row) for row in rows]
