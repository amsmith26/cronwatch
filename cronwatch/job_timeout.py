"""Job timeout enforcement: track running jobs and flag those exceeding max_runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.tracker import RunRecord, RunStatus


@dataclass
class TimeoutResult:
    job_name: str
    pid: Optional[int]
    started_at: float
    elapsed: float
    max_runtime: int  # seconds

    @property
    def exceeded_by(self) -> float:
        return max(0.0, self.elapsed - self.max_runtime)


def _utcnow() -> float:
    return time.time()


def check_timeout(record: RunRecord, max_runtime: int, now: Optional[float] = None) -> bool:
    """Return True if *record* is still running and has exceeded *max_runtime* seconds."""
    if record.status != RunStatus.RUNNING:
        return False
    if record.started_at is None:
        return False
    elapsed = (now if now is not None else _utcnow()) - record.started_at
    return elapsed > max_runtime


def find_timed_out_jobs(
    records: List[RunRecord],
    max_runtimes: Dict[str, int],
    now: Optional[float] = None,
) -> List[TimeoutResult]:
    """Scan *records* for running jobs that have exceeded their configured max_runtime.

    Args:
        records: list of RunRecord objects (typically the latest per job).
        max_runtimes: mapping of job_name -> max allowed seconds.
        now: override current time (for testing).

    Returns:
        List of TimeoutResult for each timed-out job.
    """
    ts = now if now is not None else _utcnow()
    results: List[TimeoutResult] = []
    for rec in records:
        limit = max_runtimes.get(rec.job_name)
        if limit is None:
            continue
        if rec.status != RunStatus.RUNNING or rec.started_at is None:
            continue
        elapsed = ts - rec.started_at
        if elapsed > limit:
            results.append(
                TimeoutResult(
                    job_name=rec.job_name,
                    pid=getattr(rec, "pid", None),
                    started_at=rec.started_at,
                    elapsed=elapsed,
                    max_runtime=limit,
                )
            )
    return results
