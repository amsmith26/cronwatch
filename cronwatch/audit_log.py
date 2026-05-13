"""Append-only audit log for cronwatch events (alerts sent, jobs run, etc.)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


EVENT_ALERT_SENT = "alert_sent"
EVENT_JOB_STARTED = "job_started"
EVENT_JOB_FINISHED = "job_finished"
EVENT_JOB_MISSED = "job_missed"
EVENT_DIGEST_SENT = "digest_sent"
EVENT_WEBHOOK_SENT = "webhook_sent"


def _entry(event: str, job_name: str, detail: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = {
        "ts": _utcnow().isoformat(),
        "event": event,
        "job": job_name,
    }
    if detail:
        payload.update(detail)
    return json.dumps(payload)


class AuditLog:
    """Writes JSON-lines audit entries to a file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: str, job_name: str, detail: Optional[Dict[str, Any]] = None) -> None:
        line = _entry(event, job_name, detail)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def read_all(self) -> list[Dict[str, Any]]:
        """Return all entries as a list of dicts."""
        if not self.path.exists():
            return []
        entries: list[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if raw:
                    try:
                        entries.append(json.loads(raw))
                    except json.JSONDecodeError:
                        pass
        return entries

    def read_for_job(self, job_name: str) -> list[Dict[str, Any]]:
        """Return all entries for a specific job."""
        return [e for e in self.read_all() if e.get("job") == job_name]

    def tail(self, n: int = 20) -> list[Dict[str, Any]]:
        """Return the last *n* entries."""
        return self.read_all()[-n:]
