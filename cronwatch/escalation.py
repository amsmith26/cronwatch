"""Escalation policy: upgrade alert severity after repeated failures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
import time


@dataclass
class EscalationPolicy:
    """Configuration for a single job's escalation behaviour."""
    warn_after: int = 2      # failures before WARN
    critical_after: int = 5  # failures before CRITICAL
    reset_after: int = 1     # consecutive successes needed to reset


@dataclass
class _JobState:
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    level: str = "ok"          # ok | warn | critical
    last_updated: float = field(default_factory=time.time)


class EscalationTracker:
    """Tracks per-job failure streaks and derives the current severity level."""

    def __init__(self, policy: Optional[EscalationPolicy] = None) -> None:
        self._policy = policy or EscalationPolicy()
        self._states: Dict[str, _JobState] = {}

    def _get(self, job_name: str) -> _JobState:
        if job_name not in self._states:
            self._states[job_name] = _JobState()
        return self._states[job_name]

    def record_failure(self, job_name: str) -> str:
        """Record a failure; return the new severity level."""
        state = self._get(job_name)
        state.consecutive_failures += 1
        state.consecutive_successes = 0
        state.last_updated = time.time()
        state.level = self._compute_level(state)
        return state.level

    def record_success(self, job_name: str) -> str:
        """Record a success; return the (possibly reset) severity level."""
        state = self._get(job_name)
        state.consecutive_successes += 1
        state.last_updated = time.time()
        if state.consecutive_successes >= self._policy.reset_after:
            state.consecutive_failures = 0
            state.level = "ok"
        return state.level

    def current_level(self, job_name: str) -> str:
        return self._get(job_name).level

    def consecutive_failures(self, job_name: str) -> int:
        return self._get(job_name).consecutive_failures

    def _compute_level(self, state: _JobState) -> str:
        p = self._policy
        if state.consecutive_failures >= p.critical_after:
            return "critical"
        if state.consecutive_failures >= p.warn_after:
            return "warn"
        return "ok"

    def reset(self, job_name: str) -> None:
        """Unconditionally reset state for a job."""
        self._states.pop(job_name, None)
