"""Job run quota enforcement — limits how many times a job may run within a window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class QuotaRule:
    max_runs: int
    window_seconds: float


@dataclass
class _QuotaState:
    timestamps: List[float] = field(default_factory=list)

    def prune(self, window_seconds: float) -> None:
        cutoff = time.time() - window_seconds
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def count(self) -> int:
        return len(self.timestamps)

    def record(self) -> None:
        self.timestamps.append(time.time())


class JobQuota:
    """Track and enforce per-job run quotas within a rolling time window."""

    def __init__(self) -> None:
        self._rules: Dict[str, QuotaRule] = {}
        self._states: Dict[str, _QuotaState] = {}

    def register(self, job_name: str, rule: QuotaRule) -> None:
        self._rules[job_name] = rule
        self._states.setdefault(job_name, _QuotaState())

    def _get_state(self, job_name: str) -> _QuotaState:
        if job_name not in self._states:
            self._states[job_name] = _QuotaState()
        return self._states[job_name]

    def is_allowed(self, job_name: str) -> bool:
        """Return True if the job is within its quota, False if exceeded."""
        if job_name not in self._rules:
            return True
        rule = self._rules[job_name]
        state = self._get_state(job_name)
        state.prune(rule.window_seconds)
        return state.count() < rule.max_runs

    def record_run(self, job_name: str) -> None:
        """Record that a run has occurred for the given job."""
        state = self._get_state(job_name)
        if job_name in self._rules:
            state.prune(self._rules[job_name].window_seconds)
        state.record()

    def runs_in_window(self, job_name: str) -> int:
        """Return number of recorded runs within the current window."""
        if job_name not in self._rules:
            return self._get_state(job_name).count()
        rule = self._rules[job_name]
        state = self._get_state(job_name)
        state.prune(rule.window_seconds)
        return state.count()

    def remaining(self, job_name: str) -> int | None:
        """Return remaining allowed runs, or None if no quota registered."""
        if job_name not in self._rules:
            return None
        rule = self._rules[job_name]
        return max(0, rule.max_runs - self.runs_in_window(job_name))
