"""Rate-limited notification suppression for cronwatch alerts."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class NotifierState:
    """Tracks per-job notification history."""
    last_notified_at: float = 0.0
    consecutive_failures: int = 0
    suppressed_count: int = 0


class Notifier:
    """Suppresses repeated alerts for the same job within a cooldown window.

    Args:
        cooldown_seconds: Minimum seconds between alerts for the same job.
        max_suppressed: After this many suppressed alerts, force-send regardless.
    """

    def __init__(self, cooldown_seconds: int = 3600, max_suppressed: int = 5) -> None:
        self.cooldown_seconds = cooldown_seconds
        self.max_suppressed = max_suppressed
        self._state: Dict[str, NotifierState] = {}

    def _get_state(self, job_name: str) -> NotifierState:
        if job_name not in self._state:
            self._state[job_name] = NotifierState()
        return self._state[job_name]

    def should_notify(self, job_name: str, *, _now: Optional[float] = None) -> bool:
        """Return True if an alert should be sent for *job_name* right now."""
        now = _now if _now is not None else time.time()
        state = self._get_state(job_name)
        elapsed = now - state.last_notified_at

        if elapsed >= self.cooldown_seconds:
            return True
        if state.suppressed_count >= self.max_suppressed:
            return True
        return False

    def record_notified(self, job_name: str, *, _now: Optional[float] = None) -> None:
        """Mark that a notification was just sent for *job_name*."""
        now = _now if _now is not None else time.time()
        state = self._get_state(job_name)
        state.last_notified_at = now
        state.suppressed_count = 0

    def record_suppressed(self, job_name: str) -> None:
        """Mark that a notification was suppressed for *job_name*."""
        state = self._get_state(job_name)
        state.suppressed_count += 1

    def record_failure(self, job_name: str) -> int:
        """Increment consecutive failure count; return new total."""
        state = self._get_state(job_name)
        state.consecutive_failures += 1
        return state.consecutive_failures

    def record_success(self, job_name: str) -> None:
        """Reset consecutive failure counter on success."""
        state = self._get_state(job_name)
        state.consecutive_failures = 0

    def consecutive_failures(self, job_name: str) -> int:
        """Return current consecutive failure count for *job_name*."""
        return self._get_state(job_name).consecutive_failures

    def reset(self, job_name: str) -> None:
        """Clear all state for *job_name*."""
        self._state.pop(job_name, None)
