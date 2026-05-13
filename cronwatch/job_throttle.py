"""Job execution throttling: prevent a job from running more frequently than allowed."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ThrottleRule:
    """Defines the minimum interval (in seconds) between runs for a job."""
    min_interval_seconds: int


@dataclass
class _ThrottleState:
    last_allowed_at: Optional[float] = None


class JobThrottle:
    """Tracks last-run timestamps and decides whether a job may run now."""

    def __init__(self) -> None:
        self._rules: Dict[str, ThrottleRule] = {}
        self._state: Dict[str, _ThrottleState] = {}

    def register(self, job_name: str, rule: ThrottleRule) -> None:
        """Register a throttle rule for a job."""
        self._rules[job_name] = rule
        self._state.setdefault(job_name, _ThrottleState())

    def is_throttled(self, job_name: str, now: Optional[float] = None) -> bool:
        """Return True if the job must be suppressed due to throttle."""
        if job_name not in self._rules:
            return False
        rule = self._rules[job_name]
        state = self._state[job_name]
        if state.last_allowed_at is None:
            return False
        ts = now if now is not None else time.time()
        elapsed = ts - state.last_allowed_at
        return elapsed < rule.min_interval_seconds

    def record_run(self, job_name: str, now: Optional[float] = None) -> None:
        """Record that a job was allowed to run at *now*."""
        if job_name not in self._state:
            self._state[job_name] = _ThrottleState()
        ts = now if now is not None else time.time()
        self._state[job_name].last_allowed_at = ts

    def seconds_until_allowed(self, job_name: str, now: Optional[float] = None) -> int:
        """Return seconds until the job may run again (0 if already allowed)."""
        if job_name not in self._rules:
            return 0
        rule = self._rules[job_name]
        state = self._state.get(job_name, _ThrottleState())
        if state.last_allowed_at is None:
            return 0
        ts = now if now is not None else time.time()
        remaining = rule.min_interval_seconds - (ts - state.last_allowed_at)
        return max(0, int(remaining))


def parse_throttle_rules(jobs_cfg: list) -> Dict[str, ThrottleRule]:
    """Build a {job_name: ThrottleRule} mapping from job config dicts."""
    rules: Dict[str, ThrottleRule] = {}
    for job in jobs_cfg:
        name = getattr(job, "name", None) or job.get("name", "")
        interval = None
        if hasattr(job, "min_interval_seconds"):
            interval = job.min_interval_seconds
        elif isinstance(job, dict):
            interval = job.get("min_interval_seconds")
        if interval is not None and int(interval) > 0:
            rules[name] = ThrottleRule(min_interval_seconds=int(interval))
    return rules
