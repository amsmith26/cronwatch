"""Blackout windows: suppress job execution or alerts during scheduled maintenance periods."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class BlackoutWindow:
    """A named time window during which matching jobs are blacked out."""

    name: str
    start: datetime  # timezone-aware UTC
    end: datetime    # timezone-aware UTC
    jobs: List[str] = field(default_factory=list)  # glob patterns; empty = all jobs

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if *now* falls within [start, end)."""
        if now is None:
            now = datetime.now(tz=timezone.utc)
        return self.start <= now < self.end

    def matches_job(self, job_name: str) -> bool:
        """Return True if this window applies to *job_name*."""
        if not self.jobs:
            return True
        return any(fnmatch.fnmatch(job_name, pattern) for pattern in self.jobs)

    def suppresses(self, job_name: str, now: Optional[datetime] = None) -> bool:
        """Return True when this window is active AND covers *job_name*."""
        return self.is_active(now) and self.matches_job(job_name)


class JobBlackout:
    """Collection of blackout windows; central query point."""

    def __init__(self, windows: Optional[List[BlackoutWindow]] = None) -> None:
        self._windows: List[BlackoutWindow] = list(windows or [])

    def add(self, window: BlackoutWindow) -> None:
        self._windows.append(window)

    def is_blacked_out(self, job_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if *any* window currently suppresses *job_name*."""
        return any(w.suppresses(job_name, now) for w in self._windows)

    def active_windows_for(self, job_name: str, now: Optional[datetime] = None) -> List[BlackoutWindow]:
        """Return all currently active windows that cover *job_name*."""
        return [w for w in self._windows if w.suppresses(job_name, now)]

    def all_windows(self) -> List[BlackoutWindow]:
        return list(self._windows)


def parse_blackout_windows(raw: object) -> List[BlackoutWindow]:
    """Parse a list of dicts (from YAML config) into BlackoutWindow objects."""
    if not raw:
        return []
    windows: List[BlackoutWindow] = []
    for item in raw:  # type: ignore[union-attr]
        start = _parse_dt(item["start"])
        end = _parse_dt(item["end"])
        windows.append(BlackoutWindow(
            name=item.get("name", "unnamed"),
            start=start,
            end=end,
            jobs=list(item.get("jobs") or []),
        ))
    return windows


def _parse_dt(value: object) -> datetime:
    """Accept a datetime object or an ISO-8601 string; always return UTC-aware."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    dt = datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
