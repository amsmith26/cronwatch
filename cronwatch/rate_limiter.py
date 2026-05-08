"""Token-bucket rate limiter for alert dispatching.

Prevents alert storms by capping the number of alerts sent per job
within a rolling time window.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class _Bucket:
    """Token-bucket state for a single job."""
    capacity: int
    refill_rate: float          # tokens per second
    tokens: float
    last_refill: float = field(default_factory=time.monotonic)

    def consume(self) -> bool:
        """Try to consume one token.  Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimiter:
    """Per-job token-bucket rate limiter.

    Parameters
    ----------
    max_alerts:  Maximum burst of alerts allowed before throttling.
    window_secs: Time window (seconds) over which *max_alerts* tokens refill.
    """

    def __init__(self, max_alerts: int = 5, window_secs: float = 3600.0) -> None:
        if max_alerts < 1:
            raise ValueError("max_alerts must be >= 1")
        if window_secs <= 0:
            raise ValueError("window_secs must be positive")
        self._max_alerts = max_alerts
        self._refill_rate = max_alerts / window_secs
        self._buckets: Dict[str, _Bucket] = {}

    # ------------------------------------------------------------------
    def _get_bucket(self, job_name: str) -> _Bucket:
        if job_name not in self._buckets:
            self._buckets[job_name] = _Bucket(
                capacity=self._max_alerts,
                refill_rate=self._refill_rate,
                tokens=float(self._max_alerts),
            )
        return self._buckets[job_name]

    def is_allowed(self, job_name: str) -> bool:
        """Return True if an alert for *job_name* should be sent right now."""
        return self._get_bucket(job_name).consume()

    def reset(self, job_name: str) -> None:
        """Fully refill the bucket for *job_name* (e.g. after a recovery)."""
        self._buckets.pop(job_name, None)

    def remaining(self, job_name: str) -> float:
        """Return the current token count for *job_name* (informational)."""
        return self._get_bucket(job_name).tokens
