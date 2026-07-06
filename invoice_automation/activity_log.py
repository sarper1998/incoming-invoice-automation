from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_LOG_PATH = Path("data/activity_log.jsonl")


def activity_log_path() -> Path:
    return Path(os.getenv("APP_LOG_PATH", DEFAULT_LOG_PATH))


def append_activity(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    event = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "type": event_type,
        **payload,
    }
    path = activity_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    return event


def list_activity(event_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    path = activity_log_path()
    if not path.exists():
        return []
    rows = [
        event
        for event in _read_events(path)
        if not event_type or event.get("type") == event_type
    ]
    return rows[-max(limit, 1):][::-1]


def clear_activity(event_type: str | None = None) -> int:
    path = activity_log_path()
    if not path.exists():
        return 0

    events = _read_events(path)
    if event_type is None:
        count = len(events)
        path.unlink()
        return count
    kept = [event for event in events if event.get("type") != event_type]
    removed = len(events) - len(kept)
    with path.open("w", encoding="utf-8") as handle:
        for event in kept:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    return removed


def _read_events(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows
