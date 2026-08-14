from __future__ import annotations

from andromeda_gateway.db import EventLog


def test_memory_database_persists_across_operations() -> None:
    log = EventLog(":memory:", max_rows=5)
    log.record(kind="test", status="ok")
    assert log.recent(limit=1)[0]["kind"] == "test"


def test_event_log_retention_is_bounded() -> None:
    log = EventLog(":memory:", max_rows=2)
    for index in range(4):
        log.record(kind=f"test-{index}", status="ok")
    rows = log.recent(limit=10)
    assert [row["kind"] for row in rows] == ["test-3", "test-2"]
