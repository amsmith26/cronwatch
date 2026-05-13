"""Retry policy for failed cron jobs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class RetryPolicy:
    """Defines how many times and how often to retry a failed job."""
    max_attempts: int = 3
    delay_seconds: float = 60.0
    backoff_factor: float = 1.0  # multiplied on each retry; 1.0 = constant delay
    max_delay_seconds: float = 3600.0

    def delay_for(self, attempt: int) -> float:
        """Return the delay (seconds) before *attempt* (0-indexed)."""
        if attempt <= 0:
            return 0.0
        raw = self.delay_seconds * (self.backoff_factor ** (attempt - 1))
        return min(raw, self.max_delay_seconds)


@dataclass
class RetryState:
    """Mutable per-job retry state."""
    attempts: int = 0
    last_attempt_at: Optional[float] = None
    succeeded: bool = False
    exhausted: bool = False


_Sleep = Callable[[float], None]


def run_with_retry(
    fn: Callable[[], bool],
    policy: RetryPolicy,
    *,
    sleep: _Sleep = time.sleep,
) -> RetryState:
    """Call *fn* repeatedly according to *policy*.

    *fn* must return ``True`` on success, ``False`` on failure.
    Returns the final :class:`RetryState`.
    """
    state = RetryState()
    for attempt in range(policy.max_attempts):
        delay = policy.delay_for(attempt)
        if delay > 0:
            sleep(delay)
        state.attempts += 1
        state.last_attempt_at = time.monotonic()
        ok = fn()
        if ok:
            state.succeeded = True
            return state
    state.exhausted = True
    return state
