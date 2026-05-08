"""Lightweight in-process metrics collector for cronwatch."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JobMetrics:
    job_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    missed_runs: int = 0
    total_duration_seconds: float = 0.0
    last_run_ts: Optional[float] = None
    last_success_ts: Optional[float] = None
    last_failure_ts: Optional[float] = None

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    @property
    def avg_duration(self) -> float:
        if self.successful_runs == 0:
            return 0.0
        return self.total_duration_seconds / self.successful_runs


class MetricsRegistry:
    """Thread-safe (GIL-level) store of per-job metrics."""

    def __init__(self) -> None:
        self._data: Dict[str, JobMetrics] = defaultdict(
            lambda: JobMetrics(job_name="")
        )

    def _get(self, job_name: str) -> JobMetrics:
        if job_name not in self._data:
            self._data[job_name] = JobMetrics(job_name=job_name)
        return self._data[job_name]

    def record_success(self, job_name: str, duration_seconds: float) -> None:
        m = self._get(job_name)
        now = time.time()
        m.total_runs += 1
        m.successful_runs += 1
        m.total_duration_seconds += duration_seconds
        m.last_run_ts = now
        m.last_success_ts = now

    def record_failure(self, job_name: str, duration_seconds: float) -> None:
        m = self._get(job_name)
        now = time.time()
        m.total_runs += 1
        m.failed_runs += 1
        m.total_duration_seconds += duration_seconds
        m.last_run_ts = now
        m.last_failure_ts = now

    def record_missed(self, job_name: str) -> None:
        m = self._get(job_name)
        m.missed_runs += 1

    def get(self, job_name: str) -> Optional[JobMetrics]:
        return self._data.get(job_name)

    def all_metrics(self) -> List[JobMetrics]:
        return list(self._data.values())

    def reset(self, job_name: str) -> None:
        if job_name in self._data:
            del self._data[job_name]


# Module-level singleton
registry = MetricsRegistry()
