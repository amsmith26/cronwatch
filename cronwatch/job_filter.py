"""Filter and query jobs by status, schedule, or custom predicates."""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from cronwatch.config import JobConfig
from cronwatch.scheduler import is_overdue
from cronwatch.tracker import JobTracker, RunStatus


def jobs_by_name(
    jobs: Iterable[JobConfig],
    name: str,
    *,
    case_sensitive: bool = False,
) -> List[JobConfig]:
    """Return jobs whose name matches *name* (exact, optionally case-insensitive)."""
    if case_sensitive:
        return [j for j in jobs if j.name == name]
    needle = name.lower()
    return [j for j in jobs if j.name.lower() == needle]


def jobs_overdue(
    jobs: Iterable[JobConfig],
    tracker: JobTracker,
) -> List[JobConfig]:
    """Return jobs that are currently overdue according to the tracker."""
    result: List[JobConfig] = []
    for job in jobs:
        last = tracker.last_run(job.name)
        started_at = last.started_at if last is not None else None
        if is_overdue(job.schedule, job.grace_period, reference=started_at):
            result.append(job)
    return result


def jobs_with_last_status(
    jobs: Iterable[JobConfig],
    tracker: JobTracker,
    status: RunStatus,
) -> List[JobConfig]:
    """Return jobs whose most-recent run matches *status*."""
    result: List[JobConfig] = []
    for job in jobs:
        last = tracker.last_run(job.name)
        if last is not None and last.status == status:
            result.append(job)
    return result


def jobs_never_run(
    jobs: Iterable[JobConfig],
    tracker: JobTracker,
) -> List[JobConfig]:
    """Return jobs that have no recorded runs at all."""
    return [j for j in jobs if tracker.last_run(j.name) is None]


def jobs_matching(
    jobs: Iterable[JobConfig],
    predicate: Callable[[JobConfig], bool],
) -> List[JobConfig]:
    """Generic filter: return jobs for which *predicate* returns True."""
    return [j for j in jobs if predicate(j)]
