"""Point-in-time snapshot of job health for dashboards and status endpoints."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.config import JobConfig
from cronwatch.metrics import MetricsRegistry
from cronwatch.scheduler import is_overdue, seconds_until_next
from cronwatch.tracker import JobTracker, RunStatus


@dataclass
class JobSnapshot:
    name: str
    schedule: str
    tags: List[str]
    total_runs: int
    success_rate: float          # 0.0 – 1.0
    avg_duration_seconds: float
    last_status: Optional[str]   # "success" | "failure" | None
    last_finished_at: Optional[datetime.datetime]
    is_overdue: bool
    seconds_until_next_run: float


@dataclass
class SystemSnapshot:
    captured_at: datetime.datetime
    jobs: List[JobSnapshot] = field(default_factory=list)

    @property
    def total_jobs(self) -> int:
        return len(self.jobs)

    @property
    def overdue_count(self) -> int:
        return sum(1 for j in self.jobs if j.is_overdue)

    @property
    def failing_count(self) -> int:
        return sum(1 for j in self.jobs if j.last_status == RunStatus.FAILURE.value)


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def build_job_snapshot(
    job: JobConfig,
    tracker: JobTracker,
    registry: MetricsRegistry,
    grace_seconds: int = 60,
    now: Optional[datetime.datetime] = None,
) -> JobSnapshot:
    now = now or _utcnow()
    records = tracker.get_records(job.name)
    metrics = registry.get(job.name)

    last_record = records[-1] if records else None
    last_status = last_record.status.value if last_record else None
    last_finished_at = last_record.finished_at if last_record else None

    overdue = is_overdue(job.schedule, grace_seconds, now)
    secs_next = seconds_until_next(job.schedule, now)

    return JobSnapshot(
        name=job.name,
        schedule=job.schedule,
        tags=list(job.tags or []),
        total_runs=metrics.total_runs,
        success_rate=registry.success_rate(job.name),
        avg_duration_seconds=registry.avg_duration(job.name),
        last_status=last_status,
        last_finished_at=last_finished_at,
        is_overdue=overdue,
        seconds_until_next_run=secs_next,
    )


def build_system_snapshot(
    jobs: List[JobConfig],
    tracker: JobTracker,
    registry: MetricsRegistry,
    grace_seconds: int = 60,
    now: Optional[datetime.datetime] = None,
) -> SystemSnapshot:
    now = now or _utcnow()
    snapshots = [
        build_job_snapshot(job, tracker, registry, grace_seconds, now)
        for job in jobs
    ]
    return SystemSnapshot(captured_at=now, jobs=snapshots)
